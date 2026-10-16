"""Runner for Part A of research/methodology/mozilla_realistic_validation_proposal.md.

Runs the 3-node chain (choice -> noul -> score) on the frozen 202-bug
Mozilla dataset, plus the label-wording arm, and produces the descriptive
analysis fixed in proposal §2.5.

Reuses, unmodified, the frozen calibration-pilot code for per-node
reduction and for Strategies 1, 2 and 4a (run_workflow_calibration_pilot.py),
and the Stage 1 conventions for Wilson intervals and ECE
(stage1_h1h2b_analysis.py). Nothing here is fit to Mozilla data.

  --selftest            mutation and robustness tests; no network
  --mode dry-run        preflight: hashes, plan; no network (default)
  --mode live --live --confirm-2424-mozilla-calls   the real run
  --analyze-only        re-run the analysis on existing raw responses
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SRC_DIR))

from build_workflow_calibration_pilot_manifest import F  # noqa: E402  (frozen, §16.2)
from run_workflow_calibration_pilot import (  # noqa: E402  (frozen pilot code, unmodified)
    reduce_choice_or_score_cell,
    reduce_noul_cell,
    strategy_1_decision_only,
    strategy_2_naive_confidence,
    strategy_4a_abstention_aware,
)
from stage1_h1h2b_analysis import wilson_interval  # noqa: E402

REPO_ROOT = SRC_DIR.parent.parent
MOZ_DIR = REPO_ROOT / "research" / "data" / "mozilla"
RESULTS_DIR = REPO_ROOT / "research" / "results"
DATASET = MOZ_DIR / "dataset.jsonl"
HASHES = MOZ_DIR / "dataset_hashes.json"
RAW_OUT = MOZ_DIR / "mozilla_validation_raw_responses.jsonl"
EXEC_OUT = RESULTS_DIR / "mozilla_validation_execution_manifest.json"
REPORT_OUT = RESULTS_DIR / "mozilla_validation_report.md"
SMOKE_RAW_OUT = MOZ_DIR / "mozilla_smoketest_raw_responses.jsonl"
SMOKE_EXEC_OUT = RESULTS_DIR / "mozilla_smoketest_execution_manifest.json"
SMOKE_REPORT_OUT = RESULTS_DIR / "mozilla_smoketest_report.md"
SMOKE_FRACTION = 0.10

EXPECTED_N = 202
REPEATS = 3
CALLS_PER_BUG = 3 * REPEATS + REPEATS        # 3 chain nodes + wording arm, 3 repeats each
EXPECTED_CALLS = EXPECTED_N * CALLS_PER_BUG  # 2,424
CONFIRM_FLAG = "--confirm-2424-mozilla-calls"

# Frozen code this runner depends on, pinned to the bytes committed at
# 5c16f4c (pilot) and f480613 (Stage 1). The preflight refuses to run if
# any of them has changed.
DEPENDENCIES = {
    "run_workflow_calibration_pilot.py": "ff080cbff22b0071aed95ec8cc39e89c74a942999fa33ddfc2b1ffb85e14db12",
    "build_workflow_calibration_pilot_manifest.py": "284eab7215e7d40f62b197cdff5400aa250184ea258806266d6d4f5e7a1934de",
    "stage1_h1h2b_analysis.py": "6d6b5ef36d32033b0319326bcd104662fc864ff31c05f781f12d84c778a48faa",
}

# ---------------------------------------------------------------------------
# Questions (proposal §2.2). Wording identical to the pilot unless noted.
# ---------------------------------------------------------------------------

CHOICE_Q = {"routing": {
    "type": "choice",
    "instructions": "Which subsystem is most likely responsible for this incident?",
    "criteria": {
        "network": "Issues with connectivity, latency, routing, DNS, or packet loss between systems",
        "storage": "Issues with local data storage: databases, IndexedDB, quota, caches, or persistence",
    }}}
NOUL_Q = {"regression": {"type": "noul",
                         "instructions": "Is this bug a regression (something that used to work and broke)?"}}
SEVERITY_CRITERIA = ["Cosmetic; no impact to functionality",
                     "Broken or degraded feature, but a workaround exists",
                     "Blocking issue; no workaround exists"]
SCORE_Q = {"severity": {"type": "score", "instructions": "How severe is this incident?",
                        "criteria": SEVERITY_CRITERIA}}
# Label-wording arm: Mozilla's verbatim definitions. ORDER MATTERS: score's
# index 0 is the least severe level, so the list runs S4 -> S1, the reverse
# of Mozilla's own numbering. Passing S1 first would invert the scale.
MOZILLA_DEFINITIONS_LEAST_TO_MOST = [
    "(Small/Trivial) minor significance, cosmetic issues, low or no impact to users",      # S4 -> idx 0
    "(Normal) Blocks non-critical functionality or a work around exists",                   # S3 -> idx 1
    "(Serious) Major functionality/product severely impaired or a high impact issue and a "
    "satisfactory workaround does not exist",                                               # S2 -> idx 2
    "(Catastrophic) Blocks development/testing, may impact more than 25% of users, causes "
    "data loss, likely dot release driver, and no workaround available",                    # S1 -> idx 3
]
WORDING_Q = {"severity": {"type": "score", "instructions": "How severe is this incident?",
                          "criteria": MOZILLA_DEFINITIONS_LEAST_TO_MOST}}


def node_state(text: str, node: str, d1: str | None, d2: int | None) -> str:
    """The adapter (proposal §2.2): each node's input is the bug text plus
    the upstream modal decisions, in a fixed template."""
    # An upstream node with no modal decision is shown as "undetermined",
    # never as Python's "None", and a failed noul node is never silently
    # shown as "not a regression".
    route = d1 if d1 is not None else "undetermined"
    if node == "choice":
        return text
    if node == "noul":
        return f"{text}\n\nRouting determination: {route}."
    reg = {1: "regression", 0: "not a regression"}.get(d2, "undetermined")
    return f"{text}\n\nRouting determination: {route}. Regression assessment: {reg}."


def collapse_wording_call(call: dict) -> dict:
    """Map a 4-level wording-arm response onto the 3-level scale BEFORE
    reduction, by summing the S2 and S1 probabilities (idx 2 + idx 3).
    This is the same S1+S2 merge the labels use, and it lets the wording
    arm go through the identical reduction as the primary score node."""
    out = json.loads(json.dumps(call))
    parsed = out.get("parsed_response")
    if parsed and out.get("http_status") == 200:
        ans = list(parsed["answers"].values())[0]
        p = ans["probabilities"]
        ans["probabilities"] = {"0": p.get("0", 0.0), "1": p.get("1", 0.0),
                                "2": p.get("2", 0.0) + p.get("3", 0.0)}
    return out

# ---------------------------------------------------------------------------
# Pre-registered subsets (proposal §2.5). Lexicons frozen here.
# ---------------------------------------------------------------------------

NETWORK_CUE_RE = re.compile(r"\b(https?|dns|cookies?|sockets?|tls|ssl|prox(y|ies)|necko|network(ing)?|"
                            r"h2|h3|quic|websockets?)\b", re.I)
STORAGE_CUE_RE = re.compile(r"\b(indexeddb|idb|sqlite|quota|localstorage|sessionstorage|cache api|storage|"
                            r"databases?|mozstorage)\b", re.I)
REGRESSION_WORD_RE = re.compile(r"regress", re.I)


def has_routing_cue(bug: dict) -> bool:
    return bool(NETWORK_CUE_RE.search(bug["text"]) or STORAGE_CUE_RE.search(bug["text"]))


SUBSETS = {
    "all": lambda b: True,                                                   # PRIMARY
    "no_routing_cue": lambda b: not has_routing_cue(b),
    "no_regression_wording": lambda b: not REGRESSION_WORD_RE.search(b["text"]),
    "recent_12_months": lambda b: bool(b["recent_12_months"]),
}

# ---------------------------------------------------------------------------
# Inputs and plan
# ---------------------------------------------------------------------------


class PreflightError(Exception):
    pass


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def load_dataset() -> list[dict]:
    return [json.loads(line) for line in DATASET.open(encoding="utf-8")]


def verify_inputs() -> dict:
    rec = json.loads(HASHES.read_text())
    checks = {"dataset.jsonl": (_sha(DATASET), rec["dataset.jsonl"]),
              "build_mozilla_dataset.py": (_sha(SRC_DIR / "build_mozilla_dataset.py"),
                                           rec["build_mozilla_dataset.py"])}
    for name, (actual, expected) in checks.items():
        if actual != expected:
            raise PreflightError(f"{name}: sha256 {actual} != recorded {expected}")
    bugs = load_dataset()
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
    out = {k: {"sha256": a, "match": True} for k, (a, _) in checks.items()}
    for dep, pinned in DEPENDENCIES.items():
        actual = _sha(SRC_DIR / dep)
        if actual != pinned:
            raise PreflightError(f"frozen dependency {dep} changed: {actual} != pinned {pinned}")
    out["dependencies"] = {d: {"sha256": h, "match": True} for d, h in DEPENDENCIES.items()}
    return out


def build_plan(bugs: list[dict]) -> list[tuple]:
    """(bug_id, arm, repeat). Node 2/3 inputs depend on live upstream
    decisions, so the plan fixes the call cells, not the input strings."""
    return [(b["bug_id"], arm, r) for b in bugs
            for arm in ("choice", "noul", "score", "wording") for r in range(1, REPEATS + 1)]


def validate_plan(plan: list[tuple], bugs: list[dict]) -> None:
    if len(plan) != EXPECTED_CALLS:
        raise PreflightError(f"plan has {len(plan)} calls, expected {EXPECTED_CALLS}")
    if len(set(plan)) != len(plan):
        raise PreflightError("duplicate plan cell")
    if Counter(p[0] for p in plan) != Counter({b["bug_id"]: CALLS_PER_BUG for b in bugs}):
        raise PreflightError("plan does not cover every bug exactly CALLS_PER_BUG times")


def preflight() -> dict:
    inputs = verify_inputs()
    bugs = load_dataset()
    plan = build_plan(bugs)
    validate_plan(plan, bugs)
    return {"inputs": inputs, "n_bugs": len(bugs), "planned_calls": len(plan),
            "calls_per_bug": CALLS_PER_BUG,
            "subset_sizes": {k: sum(f(b) for b in bugs) for k, f in SUBSETS.items()}}

# ---------------------------------------------------------------------------
# Live execution (never called by dry-run or self-tests)
# ---------------------------------------------------------------------------


def smoke_subset(bugs: list[dict]) -> list[dict]:
    """First ceil(10%) of each cell, in dataset order - deterministic, no
    sampling choice, and every cell (incl. the S4 row) is represented."""
    import math
    cells = defaultdict(list)
    for b in bugs:
        cells[(b["group"], b["level"])].append(b)
    return [b for v in cells.values() for b in v[: math.ceil(SMOKE_FRACTION * len(v))]]


def run_live(bugs: list[dict], raw_out: Path | None = None) -> list[dict]:
    from jev_client import ClientConfig, JevClient  # imported only on the live path

    raw_out = raw_out or RAW_OUT
    expected = len(bugs) * CALLS_PER_BUG
    if raw_out.exists():
        raise PreflightError(f"{raw_out.name} already exists; refusing to overwrite collected data or "
                             f"re-spend calls. Move it aside deliberately to re-run.")
    client = JevClient(config=ClientConfig())
    rows, n = [], 0
    with raw_out.open("w", encoding="utf-8") as f:
        for b in bugs:
            d1 = d2 = None
            state3 = None
            for arm, q in (("choice", CHOICE_Q), ("noul", NOUL_Q), ("score", SCORE_Q), ("wording", WORDING_Q)):
                state = state3 if arm == "wording" else node_state(b["text"], arm, d1, d2)
                if arm == "score":
                    state3 = state  # wording arm gets the identical input: only criteria differ
                calls = []
                for r in range(1, REPEATS + 1):
                    n += 1
                    print(f"[{n}/{expected}] bug {b['bug_id']} {arm} rep {r}", file=sys.stderr)
                    rec = client.ask(state=state, questions=q,
                                     test_group=f"mozilla_validation:{b['bug_id']}:{arm}:{r}").to_json_dict()
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
# Analysis (proposal §2.5) - descriptive only
# ---------------------------------------------------------------------------


def reduce_bug(calls_by_arm: dict) -> dict:
    return {"choice": reduce_choice_or_score_cell(calls_by_arm["choice"]),
            "noul": reduce_noul_cell(calls_by_arm["noul"]),
            "score": reduce_choice_or_score_cell(calls_by_arm["score"]),
            "wording": reduce_choice_or_score_cell([collapse_wording_call(c) for c in calls_by_arm["wording"]])}


def _rate(k: int, n: int) -> dict:
    lo, hi = wilson_interval(k, n)
    return {"k": k, "n": n, "rate": (k / n) if n else None, "wilson95": [lo, hi] if n else None}


def _bands(items: list[tuple[float, bool]]) -> dict:
    """Equal-width (4) and equal-mass (4) bands plus the >=0.90 band, with
    ECE, using the Stage 1 conventions. items: (confidence_like, correct)."""
    def row(chunk, label):
        if not chunk:
            return {"band": label, "n": 0}
        mc = sum(c for c, _ in chunk) / len(chunk)
        acc = sum(k for _, k in chunk) / len(chunk)
        return {"band": label, "n": len(chunk), "mean_confidence": mc, "agreement": acc, "gap": abs(mc - acc)}
    width = [[] for _ in range(4)]
    for c, k in items:
        width[min(int(c * 4), 3)].append((c, k))
    ew = [row(b, f"[{i/4:.2f},{(i+1)/4:.2f}{']' if i == 3 else ')'}") for i, b in enumerate(width)]
    s = sorted(items)
    n = len(s)
    sizes = [n // 4 + (1 if i < n % 4 else 0) for i in range(4)]
    em, idx = [], 0
    for i, size in enumerate(sizes):
        em.append(row(s[idx: idx + size], f"rank-group {i+1}/4"))
        idx += size

    def ece(t):
        return sum(r["n"] / n * r["gap"] for r in t if r["n"]) if n else None
    hi = [x for x in items if x[0] >= 0.90]
    return {"equal_width": ew, "ece_equal_width": ece(ew), "equal_mass": em, "ece_equal_mass": ece(em),
            "band_ge_0.90": row(hi, ">=0.90")}


def check_complete(bugs: list[dict], rows: list[dict]) -> None:
    """Refuse to analyze partial data: every bug needs exactly REPEATS
    calls per arm. A crash mid-run must not silently shrink the data."""
    have = Counter((r["bug_id"], r["arm"]) for r in rows)
    want = {(b["bug_id"], arm): REPEATS for b in bugs for arm in ("choice", "noul", "score", "wording")}
    if have != Counter(want):
        missing = [k for k in want if have[k] != REPEATS][:5]
        raise PreflightError(f"incomplete or extra raw data, e.g. {missing}; refusing to analyze")


def _ok(call: dict) -> bool:
    return call.get("http_status") == 200 and bool(call.get("parsed_response"))


def analyze(bugs: list[dict], rows: list[dict]) -> dict:
    check_complete(bugs, rows)
    by = defaultdict(lambda: defaultdict(list))
    for r in rows:
        by[r["bug_id"]][r["arm"]].append(r)
    per = {}
    for b in bugs:
        red = reduce_bug(by[b["bug_id"]])
        a_star = F(b["regression"], b["level"])
        actions = {
            "1": strategy_1_decision_only(red["choice"]["modal_decision"], red["noul"], red["score"]),
            "2": strategy_2_naive_confidence(red["choice"], red["noul"], red["score"]),
            "4a": strategy_4a_abstention_aware(red["choice"], red["noul"], red["score"],
                                               score_presentation_risk_active=False,
                                               cross_node_disagreement=False),
        }
        per[b["bug_id"]] = {"bug": b, "red": red, "a_star": a_star, "actions": actions}

    def summarize(ids: list[int]) -> dict:
        P = [per[i] for i in ids]
        out = {"n": len(P)}
        # choice: agreement with Mozilla component group (unstable counts as no agreement)
        ch = [(p["red"]["choice"]["mean_confidence"] or 0.0, p["red"]["choice"]["modal_decision"] == p["bug"]["group"])
              for p in P]
        out["choice_agreement"] = _rate(sum(k for _, k in ch), len(ch))
        out["choice_bands"] = _bands(ch)
        briers = [2 * (1 - (p["red"]["choice"]["mean_probabilities"] or {}).get(p["bug"]["group"], 0.0)) ** 2
                  for p in P]
        out["choice_unified_brier"] = sum(briers) / len(briers) if briers else None
        # noul: agreement with the `regression` keyword
        nl = []
        nb = []
        for p in P:
            m = p["red"]["noul"]["mean_noul"]
            y = p["bug"]["regression"]
            nl.append((abs(m - 0.5) * 2 if m is not None else 0.0, p["red"]["noul"]["decision"] == y))
            pref = (m if y == 1 else 1 - m) if m is not None else 0.0
            nb.append(2 * (1 - pref) ** 2)
        out["noul_agreement"] = _rate(sum(k for _, k in nl), len(nl))
        out["noul_bands"] = _bands(nl)
        out["noul_unified_brier"] = sum(nb) / len(nb) if nb else None
        # score + wording arm: confusion matrices and upward lean per true level
        for arm in ("score", "wording"):
            conf = {t: Counter() for t in (0, 1, 2)}
            for p in P:
                d = p["red"][arm]["modal_decision"]
                conf[p["bug"]["level"]]["unstable" if d is None else int(d)] += 1
            # Upward lean is estimated over STABLE decisions (an unstable
            # node is neither above nor below); the unstable count is
            # reported next to it, never folded in as "not above".
            lean = {}
            for t in (0, 1, 2):
                stable_n = sum(v for k, v in conf[t].items() if k != "unstable")
                up = sum(v for k, v in conf[t].items() if k != "unstable" and k > t)
                lean[t] = {**_rate(up, stable_n), "unstable": conf[t]["unstable"]}
            agree = sum(conf[t][t] for t in (0, 1, 2))
            out[f"{arm}_confusion"] = {t: dict(conf[t]) for t in conf}
            out[f"{arm}_agreement"] = _rate(agree, len(P))
            out[f"{arm}_P_jev_above_mozilla_by_true_level"] = lean
        # strategies (descriptive; a* comes from F applied to Mozilla labels, not externally validated)
        out["strategies"] = {}
        for s in ("1", "2", "4a"):
            y = [p["actions"][s] == p["a_star"] for p in P]
            resolved = [p["actions"][s] not in ("escalate", "defer") for p in P]
            out["strategies"][s] = {"P_Y_decision": _rate(sum(y), len(y)), "coverage": _rate(sum(resolved), len(P))}
        for s in ("1", "4a"):
            t = Counter()
            for p in P:
                y2 = p["actions"]["2"] == p["a_star"]
                ys = p["actions"][s] == p["a_star"]
                t[("2_right" if y2 else "2_wrong") + "/" + (s + "_right" if ys else s + "_wrong")] += 1
            out["strategies"][f"discordance_2_vs_{s}"] = dict(t)
        out["repeat_unstable_rate"] = {arm: _rate(sum(1 for p in P if not p["red"][arm]["stable"]), len(P))
                                       for arm in ("choice", "score", "wording")}
        spreads = [p["red"]["noul"]["spread"] for p in P if p["red"]["noul"]["spread"] is not None]
        out["noul_repeat_spread_mean"] = sum(spreads) / len(spreads) if spreads else None
        return out

    # Data quality. The frozen Strategy 1 passes an undefined noul decision
    # into F, which then reads it as "not a regression" (a disclosed
    # Revision 10 edge case, not patched here because the code is frozen).
    # Count how often that case occurs so it is visible, not silent.
    quality = {"failed_calls_by_arm": {arm: sum(1 for r in rows if r["arm"] == arm and not _ok(r))
                                       for arm in ("choice", "noul", "score", "wording")},
               "bugs_with_all_calls_failed_by_arm": {
                   arm: sum(1 for b in bugs if not any(_ok(c) for c in by[b["bug_id"]][arm]))
                   for arm in ("choice", "noul", "score", "wording")},
               "bugs_where_strategy1_saw_undefined_noul": sum(
                   1 for p in per.values() if p["red"]["noul"]["decision"] is None)}
    result = {"data_quality": quality, "subsets": {}, "cells": {}}
    for name, f in SUBSETS.items():
        result["subsets"][name] = summarize([b["bug_id"] for b in bugs if f(b)])
    for g in ("network", "storage"):
        for lv in (2, 1, 0):
            ids = [b["bug_id"] for b in bugs if b["group"] == g and b["level"] == lv]
            result["cells"][f"{g}:level{lv}"] = summarize(ids)
    return result


def write_report(analysis: dict, path: Path) -> None:
    A = analysis["subsets"]["all"]
    L = ["# Mozilla validation — results (descriptive)", "",
         "Agreement is with Mozilla triage labels, not accuracy. The sample is balanced by severity cell, so",
         "pooled figures describe this design, not real-world rates. Per-cell figures are in the JSON.",
         "Strategy figures score against `a* = F(regression, level)`: only the node labels are",
         "externally validated, not the target action.", ""]
    for name, S in analysis["subsets"].items():
        L.append(f"## Subset `{name}` (n={S['n']}){' — PRIMARY' if name == 'all' else ''}")
        L.append(f"- choice agreement {S['choice_agreement']['rate']}, noul agreement {S['noul_agreement']['rate']}, "
                 f"score agreement {S['score_agreement']['rate']}, wording-arm agreement {S['wording_agreement']['rate']}")
        lean = S["score_P_jev_above_mozilla_by_true_level"][0]
        lean_w = S["wording_P_jev_above_mozilla_by_true_level"][0]
        L.append(f"- RQ-A1, S4 row: P(Jev level > Mozilla) = {lean['rate']} (k={lean['k']}/{lean['n']}); "
                 f"wording arm {lean_w['rate']} (k={lean_w['k']}/{lean_w['n']})")
        L.append(f"- RQ-A2, choice >=0.90 band: {S['choice_bands']['band_ge_0.90']}")
        L.append("")
    path.write_text("\n".join(L) + "\n")

# ---------------------------------------------------------------------------
# Self-tests
# ---------------------------------------------------------------------------


def _resp(answer: dict) -> dict:
    return {"http_status": 200, "parsed_response": {"answers": {"q": answer}}}


def _choice(label, conf=0.9):
    other = "storage" if label == "network" else "network"
    return _resp({"type": "choice", "choice": label, "confidence": conf,
                  "probabilities": {label: conf, other: round(1 - conf, 6)}})


def _score(level, conf=0.9, n_levels=3):
    p = {str(i): 0.0 for i in range(n_levels)}
    p[str(level)] = conf
    p[str((level + 1) % n_levels)] = round(1 - conf, 6)
    return _resp({"type": "score", "score": float(level), "confidence": conf, "probabilities": p})


def _noul(v):
    return _resp({"type": "noul", "noul": v})


def _synthetic_rows(bugs, perfect=True):
    rows = []
    for b in bugs:
        lab = b["group"] if perfect else ("storage" if b["group"] == "network" else "network")
        lvl = b["level"] if perfect else (b["level"] + 1) % 3
        reg = b["regression"] if perfect else 1 - b["regression"]
        w_idx = {0: 0, 1: 1, 2: 2}[lvl]
        for r in range(1, REPEATS + 1):
            rows.append({"bug_id": b["bug_id"], "arm": "choice", "repeat": r, **_choice(lab, 0.95)})
            rows.append({"bug_id": b["bug_id"], "arm": "noul", "repeat": r, **_noul(0.9 if reg else 0.1)})
            rows.append({"bug_id": b["bug_id"], "arm": "score", "repeat": r, **_score(lvl)})
            rows.append({"bug_id": b["bug_id"], "arm": "wording", "repeat": r, **_score(w_idx, n_levels=4)})
    return rows


def run_selftest() -> None:
    print("=== Self-tests (no network) ===")
    bugs = load_dataset()

    # 1. hash tamper is caught, then restored
    orig = DATASET.read_bytes()
    try:
        DATASET.write_bytes(orig + b" ")
        try:
            verify_inputs()
            raise AssertionError("tampered dataset passed verify_inputs")
        except PreflightError:
            pass
    finally:
        DATASET.write_bytes(orig)
    verify_inputs()
    print("  PASS: dataset tamper caught; restored file verifies")

    # 1b. a changed frozen dependency is caught (pin, not just a record)
    saved = dict(DEPENDENCIES)
    try:
        DEPENDENCIES["run_workflow_calibration_pilot.py"] = "0" * 64
        try:
            verify_inputs()
            raise AssertionError("changed dependency passed verify_inputs")
        except PreflightError:
            pass
    finally:
        DEPENDENCIES.clear()
        DEPENDENCIES.update(saved)
    print("  PASS: a changed frozen dependency blocks the preflight")

    # 2. plan validation rejects extra, missing and duplicate cells
    plan = build_plan(bugs)
    validate_plan(plan, bugs)
    for bad, why in ((plan + [(bugs[0]["bug_id"], "choice", 9)], "extra"), (plan[:-1], "missing"),
                     (plan + [plan[0]], "duplicate")):
        try:
            validate_plan(bad, bugs)
            raise AssertionError(f"{why} cell passed validate_plan")
        except PreflightError:
            pass
    print(f"  PASS: plan = {len(plan)} calls; extra/missing/duplicate cells rejected")

    # 3. wording-arm scale direction: index 0 must be Mozilla's least severe (S4)
    assert "cosmetic" in MOZILLA_DEFINITIONS_LEAST_TO_MOST[0].lower()
    assert "catastrophic" in MOZILLA_DEFINITIONS_LEAST_TO_MOST[3].lower()
    c = collapse_wording_call(_resp({"type": "score", "score": 3.0, "confidence": 0.6,
                                     "probabilities": {"0": 0.0, "1": 0.1, "2": 0.3, "3": 0.6}}))
    p = list(c["parsed_response"]["answers"].values())[0]["probabilities"]
    assert p == {"0": 0.0, "1": 0.1, "2": 0.3 + 0.6}, p
    print("  PASS: wording criteria run S4->S1 (not inverted); S1+S2 probabilities merge to level 2")

    # 4. adapter template is exact and the wording arm shares node 3's input
    assert node_state("T", "noul", "network", None) == "T\n\nRouting determination: network."
    assert node_state("T", "score", "storage", 1) == \
        "T\n\nRouting determination: storage. Regression assessment: regression."
    print("  PASS: adapter templates exact")

    # 5. end-to-end analysis on synthetic perfect / perfectly-wrong responses
    good = analyze(bugs, _synthetic_rows(bugs, perfect=True))["subsets"]["all"]
    bad = analyze(bugs, _synthetic_rows(bugs, perfect=False))["subsets"]["all"]
    for k in ("choice_agreement", "noul_agreement", "score_agreement", "wording_agreement"):
        assert good[k]["rate"] == 1.0, (k, good[k])
        assert bad[k]["rate"] == 0.0, (k, bad[k])
    assert good["score_P_jev_above_mozilla_by_true_level"][0]["rate"] == 0.0
    assert bad["score_P_jev_above_mozilla_by_true_level"][0]["rate"] == 1.0  # level 0 shifted to 1
    print("  PASS: analysis gives agreement 1.0 on perfect and 0.0 on perfectly-wrong synthetic data; "
          "upward lean detected exactly")

    # 6. a* is F applied to labels; strategies take no label argument
    import inspect
    assert F(1, 1) == "defer" and F(0, 1) == "accept" and F(1, 2) == "escalate" and F(0, 0) == "accept"
    for fn in (strategy_1_decision_only, strategy_2_naive_confidence, strategy_4a_abstention_aware):
        assert not ({"a_star", "label", "bug"} & set(inspect.signature(fn).parameters)), fn.__name__
    print("  PASS: a* = F(regression, level); no strategy sees a label")

    # 7. subsets are pre-registered and non-empty; primary is 'all'
    sizes = {k: sum(f(b) for b in bugs) for k, f in SUBSETS.items()}
    assert sizes["all"] == EXPECTED_N and all(v > 0 for v in sizes.values()), sizes
    print(f"  PASS: subset sizes {sizes}")

    # 9. probe-found defects stay fixed
    #  9a. an undetermined upstream node is never shown as "None" or as "not a regression"
    assert node_state("T", "noul", None, None) == "T\n\nRouting determination: undetermined."
    assert node_state("T", "score", None, None) == \
        "T\n\nRouting determination: undetermined. Regression assessment: undetermined."
    #  9b. partial raw data is refused, not silently analyzed
    one = [b for b in bugs[:1]]
    full = _synthetic_rows(one)
    try:
        analyze(one, full[:-1])
        raise AssertionError("analyze accepted a missing call")
    except PreflightError:
        pass
    #  9c. upward lean excludes unstable decisions instead of counting them as "not above"
    b0 = dict(one[0], level=0)
    rows = []
    for r, lvl in zip((1, 2, 3), (0, 1, 2)):
        rows += [{"bug_id": b0["bug_id"], "arm": "choice", "repeat": r, **_choice(b0["group"])},
                 {"bug_id": b0["bug_id"], "arm": "noul", "repeat": r, **_noul(0.1)},
                 {"bug_id": b0["bug_id"], "arm": "score", "repeat": r, **_score(lvl)},
                 {"bug_id": b0["bug_id"], "arm": "wording", "repeat": r, **_score(0, n_levels=4)}]
    lean = analyze([b0], rows)["subsets"]["all"]["score_P_jev_above_mozilla_by_true_level"][0]
    assert lean["n"] == 0 and lean["unstable"] == 1 and lean["rate"] is None, lean
    #  9d. a node whose calls all failed is counted in data_quality
    dead = [dict(r, http_status=500, parsed_response=None) if r["arm"] == "noul" else r for r in full]
    q = analyze(one, dead)["data_quality"]
    assert q["bugs_with_all_calls_failed_by_arm"]["noul"] == 1 and q["bugs_where_strategy1_saw_undefined_noul"] == 1, q
    #  9e. the live path refuses to overwrite existing raw data
    import tempfile
    global RAW_OUT
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
    print("  PASS: 'undetermined' adapter wording; partial data refused; lean excludes unstable; "
          "all-failed nodes counted; existing raw data never overwritten")

    # 8. dry-run never touches the network
    import requests

    def boom(*a, **k):
        raise AssertionError("network used during dry-run")
    saved = requests.post
    requests.post = boom
    try:
        preflight()
    finally:
        requests.post = saved
    print("  PASS: preflight makes zero network calls")
    print("\n=== ALL SELF-TESTS PASSED ===")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["dry-run", "live"], default="dry-run")
    ap.add_argument("--live", action="store_true")
    ap.add_argument(CONFIRM_FLAG, dest="confirm", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--analyze-only", action="store_true")
    ap.add_argument("--smoke-test", action="store_true", help="first 10%% of each cell, separate artifacts")
    ap.add_argument("--confirm-252-smoke-calls", dest="confirm_smoke", action="store_true")
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
            if len(sub) * CALLS_PER_BUG != 252 or not a.confirm_smoke:
                sys.exit("Refusing: smoke test needs --confirm-252-smoke-calls (21 bugs x 12 calls)")
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
        (RESULTS_DIR / "mozilla_validation_preflight_report.json").write_text(json.dumps(report, indent=2))
        print(json.dumps(report, indent=2))
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
