"""Runner for the Linux kernel Bugzilla replication
(research/methodology/kernel_replication_proposal.md).

A replication of run_mozilla_validation.py on a second tracker. It runs the
same 3-node chain (choice -> noul -> score), 3 repeats each, with the SAME
question objects, the SAME adapter and the SAME analysis code, all imported
from run_mozilla_validation.py (which in turn imports the frozen pilot,
Stage 1, Revision 11 and Strategy 5 modules). Nothing is copied and nothing
is fit to kernel data. Every imported module is pinned by hash.

What differs, and why (proposal §2, §4):
  * No label-wording arm. The kernel has no official severity definitions
    comparable to Mozilla's S1-S4 text, so there is nothing to pass as
    criteria. 9 calls per bug, not 12.
  * Mozilla's analyze() requires a wording arm. It is called unchanged
    with a SHADOW wording arm (a copy of the score arm, never sent to Jev)
    and every wording-derived output is then removed. A self-test proves
    the shadow cannot influence any reported number.
  * Labels are REPORTER-set; the lean key is renamed "..._above_reporter_
    label_..." so no output says "Mozilla" or "triage".
  * Subsets: Mozilla's lexicons reused unchanged; "recent" is created on or
    after 2018-01-01; one extra kernel-lexicon cue subset (secondary).

  --selftest                                    mutation and robustness tests; no network
  --mode dry-run                                preflight: hashes, plan; no network (default)
  --mode live --live --confirm-2160-kernel-calls  the real run (NOT authorized yet)
  --smoke-test --confirm-216-kernel-smoke-calls   first 10% of each cell (NOT authorized yet)
  --analyze-only                                re-run the analysis on existing raw responses
"""

from __future__ import annotations

import argparse
import contextlib
import copy
import hashlib
import json
import math
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SRC_DIR))

import run_mozilla_validation as moz  # noqa: E402  (questions, adapter, lexicons, analysis)
from build_workflow_calibration_pilot_manifest import F  # noqa: E402
from run_workflow_calibration_pilot import (  # noqa: E402
    reduce_choice_or_score_cell,
    reduce_noul_cell,
    strategy_1_decision_only,
    strategy_2_naive_confidence,
    strategy_4a_abstention_aware,
)
from workflow_strategies_r11 import strategy_2_r11, strategy_4a_r11  # noqa: E402
from workflow_strategy5_proposal import strategy_5  # noqa: E402

PreflightError = moz.PreflightError

REPO_ROOT = SRC_DIR.parent.parent
KERNEL_DIR = REPO_ROOT / "research" / "data" / "kernel"
RESULTS_DIR = REPO_ROOT / "research" / "results"
DATASET = KERNEL_DIR / "dataset.jsonl"
HASHES = KERNEL_DIR / "dataset_hashes.json"
RAW_OUT = KERNEL_DIR / "kernel_validation_raw_responses.jsonl"
EXEC_OUT = RESULTS_DIR / "kernel_validation_execution_manifest.json"
REPORT_OUT = RESULTS_DIR / "kernel_validation_report.md"
PREFLIGHT_OUT = RESULTS_DIR / "kernel_validation_preflight_report.json"
SMOKE_RAW_OUT = KERNEL_DIR / "kernel_smoketest_raw_responses.jsonl"
SMOKE_EXEC_OUT = RESULTS_DIR / "kernel_smoketest_execution_manifest.json"
SMOKE_REPORT_OUT = RESULTS_DIR / "kernel_smoketest_report.md"

EXPECTED_N = 240
REPEATS = moz.REPEATS                         # 3
ARMS = ("choice", "noul", "score")            # no wording arm (proposal §2.4)
CALLS_PER_BUG = len(ARMS) * REPEATS           # 9
EXPECTED_CALLS = EXPECTED_N * CALLS_PER_BUG   # 2,160
CONFIRM_FLAG = f"--confirm-{EXPECTED_CALLS}-kernel-calls"
EXPECTED_SMOKE_CALLS = 216                    # 6 cells x ceil(0.1 x 40) bugs x 9
SMOKE_CONFIRM_FLAG = f"--confirm-{EXPECTED_SMOKE_CALLS}-kernel-smoke-calls"

# Every local module this runner executes, pinned to the bytes committed at
# b6094d0. The first three carry the same pins as the Mozilla runner.
DEPENDENCIES = {
    "run_workflow_calibration_pilot.py": "ff080cbff22b0071aed95ec8cc39e89c74a942999fa33ddfc2b1ffb85e14db12",
    "build_workflow_calibration_pilot_manifest.py": "284eab7215e7d40f62b197cdff5400aa250184ea258806266d6d4f5e7a1934de",
    "stage1_h1h2b_analysis.py": "6d6b5ef36d32033b0319326bcd104662fc864ff31c05f781f12d84c778a48faa",
    "run_mozilla_validation.py": "c34a26610ba96326d69b41d7596b1cc6ac4832c3ff4637149a902669fcaceb70",
    "build_mozilla_dataset.py": "64d71a61f1e169ba179fd5e3976f1751e610a89090b455b21cfaf50526c3d913",
    "workflow_strategies_r11.py": "e0f81ed17355e0433f9f45b1f427fc3aa76422e2a9e872f9f6054cdf6fc87dff",
    "workflow_strategy5_proposal.py": "7d4a16452b94cab1659aa910bf09187469c3cc9c85454cad98b37b1d1359edba",
    "analyze_stage1.py": "4f13e31f43cf5e62c906242ac4616dfd8773496d2d134f74f0dd82874332d10b",
    "build_score_phase_b_manifest.py": "9fd4e489cde48b8b8751c8e636541d45241708013a8c842ee7a496c0854e9873",
}

# ---------------------------------------------------------------------------
# Questions and adapter: the Mozilla objects themselves (identity, not copies)
# ---------------------------------------------------------------------------

CHOICE_Q = moz.CHOICE_Q
NOUL_Q = moz.NOUL_Q
SCORE_Q = moz.SCORE_Q
QUESTIONS = {"choice": CHOICE_Q, "noul": NOUL_Q, "score": SCORE_Q}
node_state = moz.node_state

# ---------------------------------------------------------------------------
# Pre-registered subsets (proposal §5). Mozilla lexicons reused unchanged.
# ---------------------------------------------------------------------------

# Kernel-specific cue lexicon, frozen before any call. Deliberately broad;
# used ONLY for the extra secondary subset `no_routing_cue_extended`.
KERNEL_NETWORK_CUE_RE = re.compile(
    r"\b(ethernet|eth\d+|wlan\d*|wi-?fi|wireless|802\.11\w*|iwl\w*|ath\d+\w*|rtl\w+|r8169|e1000\w*|igb|"
    r"ixgbe|tg3|bnx\w*|mlx\w*|nic|ipv[46]|tcp|udp|icmp|ip|netfilter|iptables|nftables|conntrack|"
    r"packets?|mtu|vlan|router|bonding|netdev\w*|skb\w*)\b", re.I)
KERNEL_STORAGE_CUE_RE = re.compile(
    r"\b(ext[234]|btrfs|xfs|file ?systems?|fs|disks?|ssd|hdd|nvme\w*|scsi|sata|ata\d*|ahci|ide|raid\d*|"
    r"md\d*|lvm\d?|dm-\w+|device-mapper|blk\w*|block|i/o|partitions?|mount(ed|ing)?|fsck|journal\w*|"
    r"sd[a-z]\d*|inodes?)\b", re.I)


def has_kernel_routing_cue(bug: dict) -> bool:
    return bool(KERNEL_NETWORK_CUE_RE.search(bug["text"]) or KERNEL_STORAGE_CUE_RE.search(bug["text"]))


SUBSETS = {
    "all": lambda b: True,                                                          # PRIMARY
    "no_routing_cue": lambda b: not moz.has_routing_cue(b),                         # Mozilla lexicons
    "no_routing_cue_extended": lambda b: not (moz.has_routing_cue(b) or has_kernel_routing_cue(b)),
    "no_regression_wording": lambda b: not moz.REGRESSION_WORD_RE.search(b["text"]),
    "recent_since_2018": lambda b: bool(b["recent_since_2018"]),
}

# Record fields allowed in dataset.jsonl. Anything else (e.g. a reporter or
# assignee field) fails the preflight.
ALLOWED_FIELDS = {"bug_id", "url", "group", "component", "severity", "level", "regression", "cf_regression",
                  "creation_time", "recent_since_2018", "severity_changed_after_filing",
                  "chars_before_truncation", "truncation", "log_line_share", "text", "text_sha256"}
EMAIL_LIKE_RE = re.compile(r"@|[\w.+-]+\s?(\[at\]|\(at\))\s?[\w-]+", re.I)

# ---------------------------------------------------------------------------
# Inputs and plan
# ---------------------------------------------------------------------------


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def load_dataset(path: Path | None = None) -> list[dict]:
    return [json.loads(line) for line in (path or DATASET).open(encoding="utf-8")]


def verify_inputs(dataset: Path | None = None) -> dict:
    dataset = dataset or DATASET
    rec = json.loads(HASHES.read_text())
    checks = {"dataset.jsonl": (_sha(dataset), rec["dataset.jsonl"]),
              "build_kernel_dataset.py": (_sha(SRC_DIR / "build_kernel_dataset.py"),
                                          rec["build_kernel_dataset.py"])}
    for name, (actual, expected) in checks.items():
        if actual != expected:
            raise PreflightError(f"{name}: sha256 {actual} != recorded {expected}")
    bugs = load_dataset(dataset)
    if len(bugs) != EXPECTED_N:
        raise PreflightError(f"expected {EXPECTED_N} bugs, got {len(bugs)}")
    if len({b["bug_id"] for b in bugs}) != EXPECTED_N:
        raise PreflightError("duplicate bug_id")
    for b in bugs:
        if b["group"] not in ("network", "storage") or b["level"] not in (0, 1, 2) \
                or b["regression"] not in (0, 1):
            raise PreflightError(f"bad label on bug {b['bug_id']}")
        if hashlib.sha256(b["text"].encode("utf-8")).hexdigest() != b["text_sha256"]:
            raise PreflightError(f"text_sha256 mismatch on bug {b['bug_id']}")
        if set(b) - ALLOWED_FIELDS:
            raise PreflightError(f"unexpected field(s) {sorted(set(b) - ALLOWED_FIELDS)} on bug {b['bug_id']}")
        if EMAIL_LIKE_RE.search(b["text"]):
            raise PreflightError(f"email-like string in text of bug {b['bug_id']}")
    out = {k: {"sha256": a, "match": True} for k, (a, _) in checks.items()}
    for dep, pinned in DEPENDENCIES.items():
        actual = _sha(SRC_DIR / dep)
        if actual != pinned:
            raise PreflightError(f"frozen dependency {dep} changed: {actual} != pinned {pinned}")
    out["dependencies"] = {d: {"sha256": h, "match": True} for d, h in DEPENDENCIES.items()}
    return out


def build_plan(bugs: list[dict]) -> list[tuple]:
    return [(b["bug_id"], arm, r) for b in bugs for arm in ARMS for r in range(1, REPEATS + 1)]


def validate_plan(plan: list[tuple], bugs: list[dict]) -> None:
    if len(plan) != len(bugs) * CALLS_PER_BUG:
        raise PreflightError(f"plan has {len(plan)} calls, expected {len(bugs) * CALLS_PER_BUG}")
    if len(set(plan)) != len(plan):
        raise PreflightError("duplicate plan cell")
    if any(p[1] not in ARMS for p in plan):
        raise PreflightError("plan contains an arm outside ARMS")
    if Counter(p[0] for p in plan) != Counter({b["bug_id"]: CALLS_PER_BUG for b in bugs}):
        raise PreflightError("plan does not cover every bug exactly CALLS_PER_BUG times")


def cell_sizes(bugs: list[dict]) -> dict:
    return {f"{g}:level{lv}": sum(1 for b in bugs if b["group"] == g and b["level"] == lv)
            for g in ("network", "storage") for lv in (2, 1, 0)}


def preflight() -> dict:
    inputs = verify_inputs()
    bugs = load_dataset()
    plan = build_plan(bugs)
    validate_plan(plan, bugs)
    if len(plan) != EXPECTED_CALLS:
        raise PreflightError(f"plan has {len(plan)} calls, expected {EXPECTED_CALLS}")
    smoke = smoke_subset(bugs)
    return {"status": "dry-run; no Jev call made", "inputs": inputs, "n_bugs": len(bugs),
            "cells": cell_sizes(bugs), "arms": list(ARMS), "planned_calls": len(plan),
            "calls_per_bug": CALLS_PER_BUG, "live_confirm_flag": CONFIRM_FLAG,
            "smoke_test": {"bugs": len(smoke), "calls": len(smoke) * CALLS_PER_BUG,
                           "confirm_flag": SMOKE_CONFIRM_FLAG},
            "subset_sizes": {k: sum(f(b) for b in bugs) for k, f in SUBSETS.items()},
            "questions": QUESTIONS}

# ---------------------------------------------------------------------------
# Live execution (never called by dry-run or self-tests)
# ---------------------------------------------------------------------------


def smoke_subset(bugs: list[dict]) -> list[dict]:
    cells = defaultdict(list)
    for b in bugs:
        cells[(b["group"], b["level"])].append(b)
    return [b for v in cells.values() for b in v[: math.ceil(moz.SMOKE_FRACTION * len(v))]]


def run_live(bugs: list[dict], raw_out: Path | None = None) -> list[dict]:
    raw_out = raw_out or RAW_OUT
    # Refuse BEFORE importing or instantiating the client.
    if raw_out.exists():
        raise PreflightError(f"{raw_out.name} already exists; refusing to overwrite collected data or "
                             f"re-spend calls. Move it aside deliberately to re-run.")
    from jev_client import ClientConfig, JevClient  # imported only on the live path

    expected = len(bugs) * CALLS_PER_BUG
    client = JevClient(config=ClientConfig())
    rows, n = [], 0
    with raw_out.open("w", encoding="utf-8") as f:
        for b in bugs:
            d1 = d2 = None
            for arm in ARMS:
                state = node_state(b["text"], arm, d1, d2)
                calls = []
                for r in range(1, REPEATS + 1):
                    n += 1
                    print(f"[{n}/{expected}] bug {b['bug_id']} {arm} rep {r}", file=sys.stderr)
                    rec = client.ask(state=state, questions=QUESTIONS[arm],
                                     test_group=f"kernel_validation:{b['bug_id']}:{arm}:{r}").to_json_dict()
                    row = {"bug_id": b["bug_id"], "arm": arm, "repeat": r, **rec}
                    f.write(json.dumps(row, default=str) + "\n")
                    f.flush()
                    calls.append(rec)
                    rows.append(row)
                if arm == "choice":
                    d1 = reduce_choice_or_score_cell(calls)["modal_decision"]
                elif arm == "noul":
                    d2 = reduce_noul_cell(calls)["decision"]
    if len(rows) != expected:
        raise PreflightError(f"executed {len(rows)} calls, expected {expected}")
    return rows

# ---------------------------------------------------------------------------
# Analysis: Mozilla's analyze(), unchanged, wrapped
# ---------------------------------------------------------------------------

LEAN_KEY_MOZ = "score_P_jev_above_mozilla_by_true_level"
LEAN_KEY = "score_P_jev_above_reporter_label_by_true_level"


def check_complete(bugs: list[dict], rows: list[dict]) -> None:
    have = Counter((r["bug_id"], r["arm"]) for r in rows)
    want = Counter({(b["bug_id"], arm): REPEATS for b in bugs for arm in ARMS})
    if have != want:
        bad = [k for k in set(want) | set(have) if have[k] != want[k]][:5]
        raise PreflightError(f"incomplete or extra raw data, e.g. {bad}; refusing to analyze")


@contextlib.contextmanager
def _mozilla_subsets_replaced():
    saved = moz.SUBSETS
    moz.SUBSETS = SUBSETS
    try:
        yield
    finally:
        moz.SUBSETS = saved


def _strip_wording(summary: dict) -> dict:
    out = {k: v for k, v in summary.items() if not k.startswith("wording_")}
    out["repeat_unstable_rate"] = {k: v for k, v in summary["repeat_unstable_rate"].items() if k != "wording"}
    out[LEAN_KEY] = out.pop(LEAN_KEY_MOZ)
    return out


def analyze(bugs: list[dict], rows: list[dict], shadow_rows: list[dict] | None = None) -> dict:
    """Mozilla's analyze() on the 3 real arms plus a shadow wording arm
    (default: a copy of the score arm; never sent to Jev), then every
    wording-derived output is removed. `shadow_rows` exists for the
    self-test that proves the shadow cannot change any reported number."""
    check_complete(bugs, rows)
    if shadow_rows is None:
        shadow_rows = [dict(copy.deepcopy(r), arm="wording") for r in rows if r["arm"] == "score"]
    with _mozilla_subsets_replaced():
        res = moz.analyze(bugs, list(rows) + shadow_rows)
    for d in ("failed_calls_by_arm", "bugs_with_all_calls_failed_by_arm"):
        res["data_quality"][d].pop("wording")
    res["subsets"] = {k: _strip_wording(v) for k, v in res["subsets"].items()}
    res["cells"] = {k: _strip_wording(v) for k, v in res["cells"].items()}
    res["notes"] = ["Agreement is with REPORTER-set kernel Bugzilla labels (component, severity, cf_regression), "
                    "not with triage and not accuracy.",
                    "No label-wording arm (kernel has no official severity definitions).",
                    "a* = F(regression, level) applied to reporter labels; strategy figures are not externally "
                    "validated and set no Step 2 constant."]
    return res


def write_report(analysis: dict, path: Path) -> None:
    L = ["# Kernel replication - results (descriptive)", "",
         "Agreement is with REPORTER-set kernel Bugzilla labels, not with triage and not accuracy. The sample is",
         "balanced by severity cell, so pooled figures describe this design, not real-world rates. Per-cell",
         "figures are in the JSON. Strategy figures score against `a* = F(regression, level)`: only the node",
         "labels are external, not the target action. No wording arm (proposal §2.4).", ""]
    for name, S in analysis["subsets"].items():
        L.append(f"## Subset `{name}` (n={S['n']}){' - PRIMARY' if name == 'all' else ''}")
        L.append(f"- choice agreement {S['choice_agreement']['rate']}, noul agreement {S['noul_agreement']['rate']}, "
                 f"score agreement {S['score_agreement']['rate']}")
        lean = S[LEAN_KEY][0]
        L.append(f"- RQ-K1, level-0 (reporter 'low') row: P(Jev level > reporter level) = {lean['rate']} "
                 f"(k={lean['k']}/{lean['n']}, unstable {lean['unstable']})")
        L.append(f"- RQ-K2, choice >=0.90 band: {S['choice_bands']['band_ge_0.90']}")
        L.append("")
    path.write_text("\n".join(L) + "\n")

# ---------------------------------------------------------------------------
# Self-tests (no network)
# ---------------------------------------------------------------------------


def _synthetic_rows(bugs, perfect=True):
    """Mozilla's synthetic generator, minus its wording rows."""
    return [r for r in moz._synthetic_rows(bugs, perfect=perfect) if r["arm"] != "wording"]


class _NoNetwork(contextlib.ContextDecorator):
    def __enter__(self):
        import socket

        import requests
        self._saved = (requests.post, requests.get, socket.socket.connect)

        def boom(*a, **k):
            raise AssertionError("network used")
        requests.post = requests.get = boom
        socket.socket.connect = boom
        return self

    def __exit__(self, *exc):
        import socket

        import requests
        requests.post, requests.get, socket.socket.connect = self._saved
        return False


def run_selftest() -> None:
    import inspect
    import shutil
    import tempfile

    global RAW_OUT
    print("=== Self-tests (no network) ===")
    with _NoNetwork():
        bugs = load_dataset()

        # 1. tampering with a COPY of the dataset is caught (the real file is never written)
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td) / "dataset.jsonl"
            shutil.copyfile(DATASET, tmp)
            verify_inputs(tmp)
            tmp.write_bytes(tmp.read_bytes() + b" ")
            try:
                verify_inputs(tmp)
                raise AssertionError("tampered dataset passed verify_inputs")
            except PreflightError:
                pass
        verify_inputs()
        print("  PASS: dataset tamper caught (on a temp copy); real file verifies")

        # 1b. every pinned dependency blocks the preflight when changed
        for dep in DEPENDENCIES:
            saved = DEPENDENCIES[dep]
            DEPENDENCIES[dep] = "0" * 64
            try:
                try:
                    verify_inputs()
                    raise AssertionError(f"changed {dep} passed verify_inputs")
                except PreflightError:
                    pass
            finally:
                DEPENDENCIES[dep] = saved
        print(f"  PASS: each of the {len(DEPENDENCIES)} pinned modules blocks the preflight if changed")

        # 2. plan: exact count, no wording arm; extra/missing/duplicate/foreign-arm rejected
        plan = build_plan(bugs)
        validate_plan(plan, bugs)
        assert len(plan) == EXPECTED_CALLS == EXPECTED_N * 9 and CALLS_PER_BUG == 9
        assert not any(p[1] == "wording" for p in plan)
        for bad, why in ((plan + [(bugs[0]["bug_id"], "choice", 9)], "extra"), (plan[:-1], "missing"),
                         (plan + [plan[0]], "duplicate"),
                         (plan[:-1] + [(plan[-1][0], "wording", plan[-1][2])], "wording arm")):
            try:
                validate_plan(bad, bugs)
                raise AssertionError(f"{why} cell passed validate_plan")
            except PreflightError:
                pass
        print(f"  PASS: plan = {len(plan)} calls ({EXPECTED_N} bugs x 3 nodes x 3 repeats); "
              "extra/missing/duplicate/wording cells rejected")

        # 3. questions and adapter are Mozilla's own objects; templates exact
        assert CHOICE_Q is moz.CHOICE_Q and NOUL_Q is moz.NOUL_Q and SCORE_Q is moz.SCORE_Q
        assert node_state is moz.node_state
        assert SCORE_Q["severity"]["criteria"] == moz.SEVERITY_CRITERIA
        assert node_state("T", "noul", "network", None) == "T\n\nRouting determination: network."
        assert node_state("T", "score", "storage", 1) == \
            "T\n\nRouting determination: storage. Regression assessment: regression."
        assert node_state("T", "score", None, None) == \
            "T\n\nRouting determination: undetermined. Regression assessment: undetermined."
        print("  PASS: questions/adapter are the Mozilla objects (identity); templates exact")

        # 4. end-to-end on synthetic perfect / perfectly-wrong responses
        good = analyze(bugs, _synthetic_rows(bugs, True))
        bad = analyze(bugs, _synthetic_rows(bugs, False))
        for k in ("choice_agreement", "noul_agreement", "score_agreement"):
            assert good["subsets"]["all"][k]["rate"] == 1.0, (k, good["subsets"]["all"][k])
            assert bad["subsets"]["all"][k]["rate"] == 0.0, (k, bad["subsets"]["all"][k])
        assert good["subsets"]["all"][LEAN_KEY][0]["rate"] == 0.0
        assert bad["subsets"]["all"][LEAN_KEY][0]["rate"] == 1.0
        print("  PASS: agreement 1.0 on perfect and 0.0 on perfectly-wrong synthetic data; lean detected exactly")

        # 5. the shadow wording arm cannot change any reported number, and leaves no trace
        rows = _synthetic_rows(bugs, True)
        wrong_shadow = [dict(r, arm="wording") for r in _synthetic_rows(bugs, False) if r["arm"] == "score"]
        dead_shadow = [dict(r, arm="wording", http_status=500, parsed_response=None)
                       for r in rows if r["arm"] == "score"]
        a0 = json.dumps(analyze(bugs, rows), sort_keys=True, default=str)
        for sh in (wrong_shadow, dead_shadow):
            assert json.dumps(analyze(bugs, rows, sh), sort_keys=True, default=str) == a0
        def _keys(o):
            if isinstance(o, dict):
                for kk, vv in o.items():
                    yield str(kk)
                    yield from _keys(vv)
            elif isinstance(o, list):
                for vv in o:
                    yield from _keys(vv)
        keys = set(_keys(json.loads(a0))) - {"no_regression_wording"}
        assert not [kk for kk in keys if "wording" in kk or "mozilla" in kk.lower()], keys
        assert moz.SUBSETS is not SUBSETS  # Mozilla's module state restored
        print("  PASS: shadow wording arm (correct, wrong or failed) gives byte-identical output; "
              "no 'wording'/'mozilla' key survives; Mozilla module state restored")

        # 6. a* = F(labels); no strategy sees a label
        assert F(1, 1) == "defer" and F(0, 1) == "accept" and F(1, 2) == "escalate" and F(0, 0) == "accept"
        for fn in (strategy_1_decision_only, strategy_2_naive_confidence, strategy_4a_abstention_aware,
                   strategy_2_r11, strategy_4a_r11, strategy_5):
            assert not ({"a_star", "label", "bug"} & set(inspect.signature(fn).parameters)), fn.__name__
        print("  PASS: a* = F(regression, level); no strategy sees a label")

        # 7. subsets pre-registered, primary is 'all', all non-empty
        sizes = {k: sum(f(b) for b in bugs) for k, f in SUBSETS.items()}
        assert sizes["all"] == EXPECTED_N and all(v > 0 for v in sizes.values()), sizes
        assert sizes["no_routing_cue_extended"] <= sizes["no_routing_cue"]
        print(f"  PASS: subset sizes {sizes}")

        # 8. probe-found defects stay fixed (as in the Mozilla runner)
        one = bugs[:1]
        full = _synthetic_rows(one)
        for broken, why in ((full[:-1], "missing call"),
                            (full + [dict(full[0], arm="wording")], "wording row in real data")):
            try:
                analyze(one, broken)
                raise AssertionError(f"analyze accepted {why}")
            except PreflightError:
                pass
        b0 = dict(one[0], level=0)
        rws = []
        for r, lvl in zip((1, 2, 3), (0, 1, 2)):
            rws += [{"bug_id": b0["bug_id"], "arm": "choice", "repeat": r, **moz._choice(b0["group"])},
                    {"bug_id": b0["bug_id"], "arm": "noul", "repeat": r, **moz._noul(0.1)},
                    {"bug_id": b0["bug_id"], "arm": "score", "repeat": r, **moz._score(lvl)}]
        lean = analyze([b0], rws)["subsets"]["all"][LEAN_KEY][0]
        assert lean["n"] == 0 and lean["unstable"] == 1 and lean["rate"] is None, lean
        dead = [dict(r, http_status=500, parsed_response=None) if r["arm"] == "noul" else r for r in full]
        q = analyze(one, dead)["data_quality"]
        assert q["bugs_with_all_calls_failed_by_arm"]["noul"] == 1 and \
            q["bugs_where_strategy1_saw_undefined_noul"] == 1 and "wording" not in q["failed_calls_by_arm"], q
        saved_raw = RAW_OUT
        with tempfile.NamedTemporaryFile() as tmp:
            RAW_OUT = Path(tmp.name)
            try:
                run_live([])
                raise AssertionError("run_live would overwrite existing raw data")
            except PreflightError:
                pass
            finally:
                RAW_OUT = saved_raw
        assert "jev_client" not in sys.modules, "jev_client was imported during self-tests"
        print("  PASS: partial/foreign data refused; lean excludes unstable; all-failed nodes counted; "
              "existing raw data never overwritten, refused before the client is imported")

        # 9. privacy: only whitelisted fields, no email-like strings, no '@'
        for b in bugs:
            assert not (set(b) - ALLOWED_FIELDS), b["bug_id"]
            assert not EMAIL_LIKE_RE.search(b["text"]), b["bug_id"]
        print("  PASS: dataset has only whitelisted fields and no email-like strings")

        # 10. preflight makes zero network calls (requests and raw sockets patched to raise)
        report = preflight()
        assert report["planned_calls"] == EXPECTED_CALLS
        assert report["smoke_test"]["calls"] == EXPECTED_SMOKE_CALLS, report["smoke_test"]
        print("  PASS: preflight makes zero network calls; smoke subset = "
              f"{report['smoke_test']['bugs']} bugs / {report['smoke_test']['calls']} calls")
    assert "jev_client" not in sys.modules
    print("\n=== ALL SELF-TESTS PASSED ===")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["dry-run", "live"], default="dry-run")
    ap.add_argument("--live", action="store_true")
    ap.add_argument(CONFIRM_FLAG, dest="confirm", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--analyze-only", action="store_true")
    ap.add_argument("--smoke-test", action="store_true", help="first 10%% of each cell, separate artifacts")
    ap.add_argument(SMOKE_CONFIRM_FLAG, dest="confirm_smoke", action="store_true")
    a = ap.parse_args()

    if a.selftest:
        run_selftest()
        return
    report = preflight()
    if a.smoke_test:
        sub = smoke_subset(load_dataset())
        if a.analyze_only:
            rows = [json.loads(line) for line in SMOKE_RAW_OUT.open()]
        else:
            if len(sub) * CALLS_PER_BUG != EXPECTED_SMOKE_CALLS or not (a.live and a.confirm_smoke):
                sys.exit(f"Refusing: smoke test needs --live and {SMOKE_CONFIRM_FLAG}")
            rows = run_live(sub, SMOKE_RAW_OUT)
        analysis = analyze(sub, rows)
        SMOKE_EXEC_OUT.write_text(json.dumps({"status": "SMOKE TEST - pipeline check, NOT study results",
                                              "bugs": [b["bug_id"] for b in sub], "calls": len(rows),
                                              "retries": sum(1 for r in rows if r.get("is_retry")),
                                              "analysis": analysis}, indent=2, default=str))
        write_report(analysis, SMOKE_REPORT_OUT)
        print(f"Wrote {SMOKE_EXEC_OUT.relative_to(REPO_ROOT)}")
        return
    if a.analyze_only:
        rows = [json.loads(line) for line in RAW_OUT.open()]
        analysis = analyze(load_dataset(), rows)
    elif a.mode == "dry-run":
        PREFLIGHT_OUT.write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps({k: v for k, v in report.items() if k != "questions"}, indent=2))
        print("\nDry-run only. No Jev calls were made.")
        return
    else:
        if not (a.live and a.confirm):
            sys.exit(f"Refusing: live mode needs --live and {CONFIRM_FLAG}")
        rows = run_live(load_dataset())
        analysis = analyze(load_dataset(), rows)
    retries = sum(1 for r in rows if r.get("is_retry"))
    EXEC_OUT.write_text(json.dumps({"preflight": report, "calls": len(rows), "retries": retries,
                                    "analysis": analysis}, indent=2, default=str))
    write_report(analysis, REPORT_OUT)
    print(f"Wrote {EXEC_OUT.relative_to(REPO_ROOT)} and {REPORT_OUT.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
