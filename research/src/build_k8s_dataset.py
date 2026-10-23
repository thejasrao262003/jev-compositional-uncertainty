"""Dataset build for research/methodology/independent_workflow_preregistration.md
(v1, frozen 2026-10-23). GitHub REST API only, read-only. NO model calls.

  python3 research/src/build_k8s_dataset.py --selftest
  python3 research/src/build_k8s_dataset.py --build      # fetch (cached) + build + report

Outputs (research/data/k8s/, texts private like the other datasets):
  raw/                 cached API responses
  k8s_dataset.jsonl    one record per split issue (development / calibration / test)
  k8s_manifest.json    counts, hashes, snapshot provenance
  blind_sample.jsonl   40 cleaned texts with opaque codes (for the human reader)
  blind_key.json       code -> issue mapping (NOT given to the reader)
  blind_log_TEMPLATE.csv
and research/results/k8s_build_report.{json,md}.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
import subprocess
import sys
import time
import urllib.parse
import urllib.request
import zlib
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

SRC = Path(__file__).resolve().parent
sys.path.insert(0, str(SRC))
import build_mozilla_dataset as moz  # noqa: E402  (clean() reused unchanged)
from build_workflow_calibration_pilot_manifest import F  # noqa: E402  (frozen action rule)

ROOT = SRC.parents[1]
DATA = ROOT / "research" / "data" / "k8s"
RAW = DATA / "raw"
RES = ROOT / "research" / "results"
REPO = "kubernetes/kubernetes"
API = "https://api.github.com"
TEMPLATE_COMMIT = "fbd477a8bfe5631a43293b59aa4f8d0f941ca480"
CUTOFF = "2026-10-01T00:00:00Z"
N_TEST, N_CAL, N_DEV = 600, 150, 500  # Amendment 2: test widened from 500 to 600 (one-time)
MIN_CHARS = 100

SIGS = ["network", "storage", "node"]
KINDS = ["bug", "feature", "support", "cleanup"]
PRIORITY_LEVEL = {"critical-urgent": 2, "important-soon": 1, "important-longterm": 0, "backlog": 0}
EXCLUDE_LABELS = {"priority/awaiting-more-evidence", "kind/flake", "kind/failing-test", "triage/duplicate"}

FORM_KEEP = ["What happened?", "What did you expect to happen?",
             "How can we reproduce it (as minimally and precisely as possible)?", "Anything else we need to know?",
             "What would you like to be added?", "Why is this needed?"]
FORM_DROP = ["Kubernetes version", "Cloud provider", "OS version", "Install tools",
             "Container runtime (CRI) and version (if applicable)",
             "Related plugins (CNI, CSI, ...) and versions (if applicable)"]
FORM_HEADINGS = FORM_KEEP + FORM_DROP

PROW_LINE = re.compile(r"^\s*>?\s*/[a-z][\w-]*(\s.*)?$", re.I | re.M)  # Amendment 1: quoted commands too
OLD_KIND_Q = re.compile(r"^.*Is this a BUG REPORT or FEATURE REQUEST\?.*?(?=^\s*\*\*What|\Z)", re.I | re.M | re.S)
OLD_BOLD_HEADS = ["What happened", "What you expected to happen", "How to reproduce it (as minimally and precisely as possible)",
                  "How to reproduce it", "Anything else we need to know?", "Anything else we need to know",
                  "What would you like to be added", "Why is this needed", "How to categorize this issue?",
                  "How to categorize this issue"]  # Amendment 4: pre-form markdown templates
OLD_BOLD_RE = re.compile(r"^\s*\*\*(" + "|".join(re.escape(h) for h in OLD_BOLD_HEADS) + r")\*\*\s*:?\s*", re.I | re.M)
OLD_ENV_BLOCK = re.compile(r"^\s*\*\*Environment\*\*\s*:?.*?(?=^\s*\*\*[^*\n]+\*\*|\Z)", re.I | re.M | re.S)
RELEVANT_SIG_BLOCK = re.compile(r"^\s*#+\s*Relevant SIG\(s\).*?(?=^\s*#+\s*\S|\Z)", re.I | re.M | re.S)
EMPTY_HASH = re.compile(r"^\s*#+\s*$", re.M)
# Amendment 6b: one normalized matcher for template headings in ANY markdown format (#..., **...**, trailing ':' or '?')
def _norm_head(h):
    return re.sub(r"[\s:?*#]+$", "", re.sub(r"^[\s#*]+", "", h)).strip().lower()
TEMPLATE_HEADS = {_norm_head(h) for h in FORM_KEEP + FORM_DROP + OLD_BOLD_HEADS + ["Environment"]}
HASH_HEAD = re.compile(r"^\s*#{1,6}\s*(.+?)\s*$")
BOLD_HEAD = re.compile(r"^\s*\*\*([^*\n]+?)\*\*\s*:?\s*(.*)$")
ENV_HEAD = {"environment"} | {_norm_head(h) for h in FORM_DROP}


def _heading(ln):
    """(normalized heading text, remainder on the same line) for a markdown heading line, else None."""
    m = HASH_HEAD.match(ln)
    if m:
        return _norm_head(m.group(1)), ""
    m = BOLD_HEAD.match(ln)
    if m:
        return _norm_head(m.group(1)), m.group(2).strip()
    return None


def template_heads_in(text):
    return [h for ln in text.splitlines() if (hd := _heading(ln)) and (h := hd[0]) in TEMPLATE_HEADS]


def strip_template_headings(text):
    """Remove known template headings in any format; drop environment sections up to the next heading."""
    out, skipping = [], False
    for ln in text.splitlines():
        hd = _heading(ln)
        if hd and hd[0] in TEMPLATE_HEADS:
            skipping = hd[0] in ENV_HEAD
            if hd[1] and not skipping:
                out.append(hd[1])
            continue
        if hd and skipping:          # another (non-template) heading ends an environment section
            skipping = False
        if not skipping:
            out.append(ln)
    return "\n".join(out)
OLD_UNCOMMENT = re.compile(r"^.*Uncomment only one, leave it on its own line.*$", re.I | re.M)
LABEL_STR = re.compile(r"\b(sig|kind|priority|triage|area)/[\w.-]+", re.I)
TEAM_MENTION = re.compile(r"@kubernetes/sig-[\w-]+", re.I)
HTML_COMMENT = re.compile(r"<!--.*?-->", re.S)
TEAM_ANY = re.compile(r"(?<![\w.])@[A-Za-z0-9][\w-]*/[\w.-]+")  # Amendment 6: any @org/team mention
MENTION = re.compile(r"(?<![\w.])@[A-Za-z0-9][A-Za-z0-9-]{0,38}")
NO_RESPONSE = re.compile(r"^\s*_No response_\s*$", re.M)
LINK_NUM = re.compile(r"(?<![\w/&])#(\d{3,6})\b")
LINK_URL = re.compile(r"github\.com/kubernetes/kubernetes/(?:issues|pull)/(\d+)")
SOFT_CUES = ["feature request", "is a bug", "regression", "p0", "p1", "priority", "severity", "critical",
             "urgent", "sig network", "sig storage", "sig node", "sig-network", "sig-storage", "sig-node"]


# ---------------------------------------------------------------- API
def token():
    return subprocess.run(["gh", "auth", "token"], check=True, capture_output=True, text=True).stdout.strip()


def get(path, params=None, cache=None, tok=None):
    if cache and cache.exists():
        return json.loads(cache.read_text())
    url = f"{API}{path}" + ("?" + urllib.parse.urlencode(params) if params else "")
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {tok}", "Accept": "application/vnd.github+json",
                                               "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "research-build"})
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                data = json.loads(r.read().decode())
            break
        except Exception:  # noqa: BLE001
            if attempt == 4:
                raise
            time.sleep(5 * (attempt + 1))
    if cache:
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps(data))
    return data


def paged(path, params, cache_prefix, tok, log):
    out, page = [], 1
    while True:
        d = get(path, {**params, "per_page": 100, "page": page}, RAW / f"{cache_prefix}_p{page}.json", tok)
        log.append({"endpoint": path, "params": {**params, "page": page}, "items": len(d)})
        out += d
        if len(d) < 100:
            return out
        page += 1


# ---------------------------------------------------------------- cleaning
def extract_form(body: str) -> tuple[str, bool]:
    """Issue-form bodies render as '### <heading>' sections. Keep free-text answers
    (headings removed), drop environment fields. Returns (text, was_form)."""
    lines = (body or "").splitlines()
    heads = [i for i, ln in enumerate(lines) if ln.startswith("### ") and ln[4:].strip() in FORM_HEADINGS]
    if not heads:
        return body or "", False
    kept = []
    for k, i in enumerate(heads):
        end = heads[k + 1] if k + 1 < len(heads) else len(lines)
        if lines[i][4:].strip() in FORM_KEEP:
            kept.append("\n".join(lines[i + 1:end]).strip())
    return "\n\n".join(x for x in kept if x), True


def strip_form_headings(text: str) -> str:
    out = []
    for ln in text.splitlines():
        h = re.sub(r"^\s*#+\s*", "", ln).strip().rstrip(":")
        if ln.lstrip().startswith("#") and (h in FORM_HEADINGS or h + "?" in FORM_HEADINGS):
            continue
        out.append(ln)
    return "\n".join(out)


def prestep(text: str) -> str:
    text = HTML_COMMENT.sub(" ", text)
    text = OLD_KIND_Q.sub("", text)
    text = OLD_ENV_BLOCK.sub("", text)
    text = RELEVANT_SIG_BLOCK.sub("", text)
    text = OLD_BOLD_RE.sub("", text)
    text = strip_template_headings(text)
    text = EMPTY_HASH.sub("", text)
    text = OLD_UNCOMMENT.sub("", text)
    text = NO_RESPONSE.sub("", text)
    text = PROW_LINE.sub("", text)
    text = TEAM_MENTION.sub("[team]", text)
    text = TEAM_ANY.sub("[team]", text)
    text = LABEL_STR.sub("[label]", text)
    text = MENTION.sub("@user", text)
    return text


def model_text(title: str, body: str) -> tuple[str, bool]:
    b, was_form = extract_form(body)
    if not was_form:
        b = strip_form_headings(b)
    return moz.clean(prestep(title), prestep(b)), was_form


def hard_leaks(text: str) -> list[str]:
    p = []
    if PROW_LINE.search(text):
        p.append("prow_command")
    if LABEL_STR.search(text):
        p.append("label_string")
    if TEAM_MENTION.search(text) or TEAM_ANY.search(text) or "@user/" in text:
        p.append("team_mention")
    if any(re.search(rf"(?im)^\s*#*\s*{re.escape(h)}\s*$", text) for h in FORM_HEADINGS):
        p.append("form_heading")
    if re.search(r"(?i)bug report or feature request|uncomment only one", text):
        p.append("old_template_kind_question")
    if OLD_BOLD_RE.search(text) or re.search(r"(?im)^\s*\*\*Environment\*\*", text) or re.search(r"(?i)relevant sig\(s\)", text) \
            or template_heads_in(text):
        p.append("old_markdown_template")
    return p


def soft_flags(text: str) -> list[str]:
    low = text.lower()
    return [c for c in SOFT_CUES if re.search(rf"(?<![a-z0-9]){re.escape(c)}(?![a-z0-9])", low)]


# ---------------------------------------------------------------- eligibility
def label_names(issue):
    return {l["name"] for l in issue["labels"]}


def eligibility(issue) -> tuple[dict | None, str | None]:
    if "pull_request" in issue:
        return None, "pull_request"
    L = label_names(issue)
    sig = [s for s in SIGS if f"sig/{s}" in L]
    kind = [k for k in KINDS if f"kind/{k}" in L]
    pri = [p for p in PRIORITY_LEVEL if f"priority/{p}" in L]
    if len(sig) != 1:
        return None, "not_exactly_one_sig"
    if len(kind) != 1:
        return None, "not_exactly_one_kind"
    if len(pri) != 1:
        return None, "not_exactly_one_priority"
    if L & EXCLUDE_LABELS:
        return None, "excluded_label"
    if (issue.get("user") or {}).get("type") == "Bot":
        return None, "bot_author"
    if issue["created_at"] >= CUTOFF:
        return None, "after_cutoff"
    return {"sig": sig[0], "kind": kind[0], "priority_label": pri[0], "level": PRIORITY_LEVEL[pri[0]],
            "bug": int(kind[0] == "bug")}, None


def a_star(rec):
    return F(rec["bug"], rec["level"])


# ---------------------------------------------------------------- build
def build():
    tok = token()
    snapshot = datetime.now(timezone.utc).isoformat()
    log, cand, seen = [], {}, set()
    for s in SIGS:
        for p in PRIORITY_LEVEL:
            for it in paged(f"/repos/{REPO}/issues", {"labels": f"sig/{s},priority/{p}", "state": "all"},
                            f"list_{s}_{p}", tok, log):
                if it["number"] not in seen:
                    seen.add(it["number"])
                    cand[it["number"]] = it
    drop = Counter()
    elig = []
    for n, it in sorted(cand.items()):
        info, why = eligibility(it)
        if why:
            drop[why] += 1
            continue
        text, was_form = model_text(it["title"], it.get("body") or "")
        if len(text) < MIN_CHARS:
            drop["too_short_after_cleaning"] += 1
            continue
        elig.append({"number": n, "created_at": it["created_at"], "state_reason": it.get("state_reason"),
                     **info, "was_form": was_form, "text": text,
                     "raw_refs": sorted({int(x) for x in LINK_NUM.findall((it["title"] or "") + "\n" + (it.get("body") or ""))}
                                        | {int(x) for x in LINK_URL.findall(it.get("body") or "")})})
    elig.sort(key=lambda r: (r["created_at"], r["number"]))
    N = len(elig)
    if N >= N_TEST + N_CAL + N_DEV:
        nt, nc, nd = N_TEST, N_CAL, N_DEV
    else:
        nt, nc = int(0.4 * N), int(0.1 * N)
        nd = N - nt - nc if int(0.5 * N) > N - nt - nc else int(0.5 * N)
    test = elig[N - nt:]
    cal = elig[N - nt - nc:N - nt]
    dev = elig[N - nt - nc - nd:N - nt - nc]
    for split, rows in (("development", dev), ("calibration", cal), ("test", test)):
        for r in rows:
            r["split"] = split

    # timelines for split issues: label times, cross-references, duplicate marks
    split_rows = dev + cal + test
    for r in split_rows:
        tl = paged(f"/repos/{REPO}/issues/{r['number']}/timeline", {}, f"timeline_{r['number']}", tok, log)
        ltimes, xrefs, dupes = {}, set(), set()
        for ev in tl:
            e = ev.get("event")
            if e == "labeled":
                name = (ev.get("label") or {}).get("name", "")
                ltimes.setdefault(name, ev.get("created_at"))
            elif e == "cross-referenced":
                src = (ev.get("source") or {}).get("issue") or {}
                if src.get("number") and "pull_request" not in src:
                    xrefs.add(src["number"])
            elif e == "marked_as_duplicate":
                d = (ev.get("dupe") or ev.get("canonical") or {})
                if d.get("number"):
                    dupes.add(d["number"])
        lab = {"sig": f"sig/{r['sig']}", "kind": f"kind/{r['kind']}", "priority": f"priority/{r['priority_label']}"}
        r["label_times"] = {k: ltimes.get(v) for k, v in lab.items()}
        r["links"] = sorted(set(r["raw_refs"]) | xrefs | dupes)

    # linked-issue removal: test issues linked (either direction) to development or calibration
    split_of = {r["number"]: r["split"] for r in split_rows}
    linked = set()
    for r in split_rows:
        for x in r["links"]:
            if x in split_of and split_of[x] != r["split"]:
                a, b = (r["number"], x)
                if split_of[a] == "test" and split_of[b] in ("development", "calibration"):
                    linked.add(a)
                if split_of[b] == "test" and split_of[a] in ("development", "calibration"):
                    linked.add(b)
    removed = sorted(linked)
    test = [r for r in test if r["number"] not in linked]
    final = dev + cal + test

    # leakage audit
    hard = {r["number"]: hard_leaks(r["text"]) for r in final}
    hard_fail = {k: v for k, v in hard.items() if v}
    soft = Counter()
    soft_by = {}
    for r in final:
        f = soft_flags(r["text"])
        r["soft_flags"] = f
        for c in f:
            soft[(r["split"], c)] += 1
    # feasibility: target-action prevalence
    for r in final:
        r["a_star"] = a_star(r)
        r["text_sha256"] = hashlib.sha256(r["text"].encode()).hexdigest()
    acts = {s: Counter(r["a_star"] for r in final if r["split"] == s) for s in ("development", "calibration", "test")}
    feasible = all(acts[s].get(a, 0) >= 20 for s in ("development", "test") for a in ("accept", "defer", "escalate"))

    # write dataset
    DATA.mkdir(parents=True, exist_ok=True)
    keep = ["number", "split", "created_at", "sig", "kind", "priority_label", "level", "bug", "a_star", "was_form",
            "label_times", "state_reason", "soft_flags", "text", "text_sha256"]
    ds = DATA / "k8s_dataset.jsonl"
    ds.write_text("".join(json.dumps({k: r[k] for k in keep}) + "\n" for r in final))
    ds_hash = hashlib.sha256(ds.read_bytes()).hexdigest()

    # blinded sample: 20 development + 20 test, opaque codes, text only
    rng = random.Random(zlib.crc32(b"k8s-blind-3"))  # Amendment 6: new seed for the repeated read
    pick = rng.sample([r for r in final if r["split"] == "development"], 20) + \
        rng.sample([r for r in final if r["split"] == "test"], 20)
    rng.shuffle(pick)
    codes = {f"B{i + 1:02d}": r["number"] for i, r in enumerate(pick)}
    (DATA / "blind_sample.jsonl").write_text("".join(json.dumps({"code": c, "text": r["text"]}) + "\n"
                                                     for c, r in zip(codes, pick)))
    (DATA / "blind_key.json").write_text(json.dumps(codes, indent=1))
    (DATA / "blind_log_TEMPLATE.csv").write_text(
        "code,label_recoverable_from_explicit_cue(yes/no),which_label_and_cue,text_damaged(yes/no),damage_type,notes\n"
        + "".join(f"{c},,,,,\n" for c in codes))

    def dist(rows, key):
        return dict(sorted(Counter(r[key] for r in rows).items(), key=lambda x: str(x[0])))

    lags = []
    for r in final:
        t = r["label_times"].get("priority")
        if t:
            lags.append((datetime.fromisoformat(t.replace("Z", "+00:00")) -
                         datetime.fromisoformat(r["created_at"].replace("Z", "+00:00"))).days)
    lags.sort()
    early = sum(1 for r in final if all(r["label_times"].get(k) and
                (datetime.fromisoformat(r["label_times"][k].replace("Z", "+00:00")) -
                 datetime.fromisoformat(r["created_at"].replace("Z", "+00:00"))).days <= 30 for k in ("sig", "kind", "priority")))
    report = {
        "protocol": "independent_workflow_preregistration.md v1 (frozen 2026-10-23)",
        "snapshot_utc": snapshot, "template_commit": TEMPLATE_COMMIT, "cutoff": CUTOFF,
        "candidates_fetched": len(cand), "exclusions": dict(drop), "eligible": N,
        "split_sizes_before_link_removal": {"development": len(dev), "calibration": len(cal), "test": nt},
        "linked_test_issues_removed": len(removed), "linked_removed_numbers": removed,
        "split_sizes_final": {s: sum(1 for r in final if r["split"] == s) for s in ("development", "calibration", "test")},
        "date_ranges": {s: [min(r["created_at"] for r in final if r["split"] == s), max(r["created_at"] for r in final if r["split"] == s)]
                        for s in ("development", "calibration", "test")},
        "distributions": {s: {k: dist([r for r in final if r["split"] == s], k) for k in ("sig", "kind", "priority_label", "level")}
                          for s in ("development", "calibration", "test")},
        "joint_bug_by_level": {s: dict(Counter(f"bug={r['bug']},level={r['level']}" for r in final if r["split"] == s))
                               for s in ("development", "calibration", "test")},
        "target_action_prevalence": {s: dict(v) for s, v in acts.items()},
        "feasibility_rule": "each of accept/defer/escalate n>=20 in development AND test",
        "feasible": feasible,
        "form_share": {s: round(sum(r["was_form"] for r in final if r["split"] == s) / max(1, sum(1 for r in final if r["split"] == s)), 3)
                       for s in ("development", "calibration", "test")},
        "priority_label_lag_days": {"n": len(lags), "median": lags[len(lags) // 2] if lags else None,
                                    "p90": lags[int(0.9 * len(lags))] if lags else None},
        "early_triage_subset_n": early,
        "leakage_hard_failures": hard_fail, "leakage_hard_pass": not hard_fail,
        "soft_flag_counts": {f"{s}:{c}": n for (s, c), n in sorted(soft.items())},
        "blind_sample": {"n": len(codes), "seed": "zlib.crc32('k8s-blind')", "file": "research/data/k8s/blind_sample.jsonl"},
        "api_log_pages": len(log),
        "hashes": {"dataset_sha256": ds_hash},
    }
    (DATA / "k8s_manifest.json").write_text(json.dumps({**report, "api_log": log}, indent=1))
    RES.mkdir(exist_ok=True)
    (RES / "k8s_build_report.json").write_text(json.dumps(report, indent=2))
    print(json.dumps({k: report[k] for k in ("candidates_fetched", "exclusions", "eligible", "split_sizes_final",
                                             "linked_test_issues_removed", "target_action_prevalence", "feasible",
                                             "leakage_hard_pass", "form_share", "priority_label_lag_days",
                                             "early_triage_subset_n", "date_ranges")}, indent=1))
    return report


# ---------------------------------------------------------------- selftest
def selftest():
    form = ("### What happened?\n\nkubelet crashes on start\n\n### What did you expect to happen?\n\nno crash\n\n"
            "### Kubernetes version\n\n1.30\n\n### Cloud provider\n\n_No response_\n")
    t, was = model_text("kubelet crash /sig node", form)
    assert was and "kubelet crashes" in t and "1.30" not in t and "Kubernetes version" not in t and "What happened" not in t
    raw = "Some text\n/kind bug\n/priority critical-urgent\n<!-- template -->\ncc @kubernetes/sig-network-bugs @alice\nsee sig/network"
    t2, was2 = model_text("Title", raw)
    assert not was2
    assert "/kind" not in t2 and "critical-urgent" not in t2 and "template" not in t2
    assert "sig-network-bugs" not in t2 and "alice" not in t2 and "sig/network" not in t2
    assert hard_leaks(t2) == [], hard_leaks(t2)
    assert hard_leaks("x\n/sig node") == ["prow_command"]
    assert soft_flags("This is a feature request with P0 priority") == ["feature request", "p0", "priority"]
    assert F(1, 1) == "defer" and F(0, 1) == "accept" and F(1, 2) == "escalate" and F(0, 0) == "accept"
    e, why = eligibility({"labels": [{"name": "sig/node"}, {"name": "kind/bug"}, {"name": "priority/backlog"}],
                          "user": {"type": "User"}, "created_at": "2025-01-01T00:00:00Z"})
    assert why is None and e["level"] == 0 and e["bug"] == 1
    _, why = eligibility({"labels": [{"name": "sig/node"}, {"name": "sig/network"}, {"name": "kind/bug"},
                                     {"name": "priority/backlog"}], "user": {"type": "User"}, "created_at": "2025-01-01T00:00:00Z"})
    assert why == "not_exactly_one_sig"
    _, why = eligibility({"labels": [{"name": "sig/node"}, {"name": "kind/bug"}, {"name": "priority/backlog"},
                                     {"name": "priority/awaiting-more-evidence"}], "user": {"type": "User"},
                          "created_at": "2025-01-01T00:00:00Z"})
    assert why == "excluded_label"
    assert LINK_NUM.findall("fixes #12345 and see #9") == ["12345"]
    old = ("Title\n\n**Is this a BUG REPORT or FEATURE REQUEST?**:\n\nUncomment only one, leave it on its own line:\n\n"
           "> /kind bug\n> /kind feature\n\nBUG REPORT\n\n**What happened**:\nthe kubelet panics when the pod starts up")
    t3, _ = model_text("Title", old)
    assert "BUG REPORT" not in t3 and "/kind" not in t3 and "kubelet panics" in t3, t3
    assert hard_leaks(t3) == [], hard_leaks(t3)
    old2 = ("Svc invalid\n\n**What happened**:\nexport adds fields.\n\n**What you expected to happen**:\nno error\n\n"
            "**Environment**:\n- Kubernetes version: 1.9\n- OS: ubuntu\n\n**Anything else we need to know?**:\nclusterIP breaks it")
    t4, _ = model_text("Svc invalid", old2)
    assert "What happened" not in t4 and "Environment" not in t4 and "1.9" not in t4 and "export adds fields" in t4 and "clusterIP breaks it" in t4, t4
    t5, _ = model_text("Crash", "PoC here\n\n###\n\n### Relevant SIG(s)\n\nsig-node\n")
    assert "Relevant SIG" not in t5 and "sig-node" not in t5, t5
    assert hard_leaks(t4) == [] and hard_leaks(t5) == []
    t7, _ = model_text("x", "lead text\n\n#### What you expected to happen:\n\nDon't panic!\n\n#### Environment:\n- Kubernetes version: 1.20\n\n#### Notes\nkeep me")
    assert "What you expected" not in t7 and "1.20" not in t7 and "Don't panic!" in t7 and "keep me" in t7, t7
    t8, _ = model_text("x", "**What happened?**\n\nIt broke.\n\n**Possibly related?**\n- other")
    assert "What happened" not in t8 and "It broke." in t8 and "Possibly related" in t8, t8
    assert hard_leaks(t7) == [] and hard_leaks(t8) == []
    t6, _ = model_text("x", "cc @kubernetes/goog-node @alice and @rh-team/rh-storage please look")
    assert "goog-node" not in t6 and "rh-storage" not in t6 and "@user/" not in t6, t6
    assert hard_leaks(t6) == []
    print("selftest OK")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--build", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        selftest()
    if a.build:
        build()
