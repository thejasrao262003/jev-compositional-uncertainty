"""Held-out datasets for research/methodology/workflow_risk_heldout_preregistration.md.

Natural-mix sampling: N bugs drawn at random from each tracker's FULL
eligible pool (all subsystem groups x all severity levels), excluding every
bug in the existing datasets. Fetching, text cleaning, privacy scrubbing and
every exclusion rule are the original builders' functions, called unchanged
(build_mozilla_dataset.py, build_kernel_dataset.py); only the sampling loop
differs (no per-cell quota). No Jev calls.

  python3 research/src/build_heldout_datasets.py --tracker mozilla
  KERNEL_BZ_CACHE_DIR=<scratch cache> python3 research/src/build_heldout_datasets.py --tracker kernel
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

SRC = Path(__file__).resolve().parent
sys.path.insert(0, str(SRC))
import build_kernel_dataset as kb  # noqa: E402
import build_mozilla_dataset as moz  # noqa: E402

ROOT = SRC.parents[1]
OUT_DIR = ROOT / "research" / "data" / "heldout"
SEED = "heldout-risk-v1"
N_PER_TRACKER = 250


def existing_ids(tracker: str) -> set[int]:
    p = ROOT / "research" / "data" / tracker / "dataset.jsonl"
    return {json.loads(line)["bug_id"] for line in p.open()}


def pool(module, tracker: str) -> list[dict]:
    seen, out = set(), []
    for group in module.GROUPS:
        for level in (2, 1, 0):
            for bug in module.candidates(group, module.CELL_SEVERITIES[level]):
                if bug["id"] not in seen:
                    seen.add(bug["id"])
                    out.append({**bug, "_group": group, "_level": level})
    return out


def build_mozilla(n: int):
    used = existing_ids("mozilla")
    cands = [b for b in pool(moz, "mozilla") if b["id"] not in used]
    eligible = len(cands)
    random.Random(f"{SEED}:mozilla").shuffle(cands)
    recent_cutoff = datetime.now(timezone.utc) - timedelta(days=365)
    stats = {"eligible_after_removing_used": eligible, "used_excluded": len(used), "inspected": 0,
             "excluded_intermittent": 0, "excluded_fuzzing": 0, "excluded_too_short": 0,
             "excluded_severity_retriaged": 0}
    recs = []
    for bug in cands:
        if len(recs) == n:
            break
        stats["inspected"] += 1
        if moz.is_intermittent(bug):
            stats["excluded_intermittent"] += 1
            continue
        raw = moz.first_comment(bug["id"])
        if any(m in raw.lower() for m in moz.INTERMITTENT_MARKERS):
            stats["excluded_intermittent"] += 1
            continue
        if any(m in raw.lower() for m in moz.FUZZING_MARKERS):
            stats["excluded_fuzzing"] += 1
            continue
        text = moz.clean(bug["summary"], raw)
        if len(text) - len(bug["summary"]) < moz.MIN_CHARS:
            stats["excluded_too_short"] += 1
            continue
        if moz.severity_retriaged(bug["id"]):
            stats["excluded_severity_retriaged"] += 1
            continue
        created = datetime.fromisoformat(bug["creation_time"].replace("Z", "+00:00"))
        recs.append({"bug_id": bug["id"], "url": f"https://bugzilla.mozilla.org/show_bug.cgi?id={bug['id']}",
                     "tracker": "mozilla", "group": bug["_group"],
                     "component": f"{bug['product']} :: {bug['component']}", "severity": bug["severity"],
                     "level": bug["_level"], "regression": int("regression" in bug["keywords"]),
                     "creation_time": bug["creation_time"], "recent_12_months": created >= recent_cutoff,
                     "text": text, "text_sha256": hashlib.sha256(text.encode()).hexdigest()})
        if len(recs) % 25 == 0:
            print(f"mozilla: {len(recs)}/{n}", flush=True)
    return recs, stats


def build_kernel(n: int):
    used = existing_ids("kernel")
    cands = [b for b in pool(kb, "kernel") if b["id"] not in used]
    eligible = len(cands)
    random.Random(f"{SEED}:kernel").shuffle(cands)
    stats = {"eligible_after_removing_used": eligible, "used_excluded": len(used), "inspected": 0,
             "excluded_intermittent": 0, "excluded_fuzzing": 0, "excluded_too_short": 0,
             "excluded_severity_retriaged": 0, "privacy_name_occurrences_scrubbed": 0}
    recs = []
    for bug in cands:
        if len(recs) == n:
            break
        stats["inspected"] += 1
        if kb.is_intermittent(bug):
            stats["excluded_intermittent"] += 1
            continue
        raw = kb.first_comment(bug["id"])
        if any(m in raw.lower() for m in moz.INTERMITTENT_MARKERS):
            stats["excluded_intermittent"] += 1
            continue
        if any(m in raw.lower() for m in kb.FUZZING_MARKERS) or \
                any(m in bug["summary"].lower() for m in kb.KERNEL_FUZZING_MARKERS):
            stats["excluded_fuzzing"] += 1
            continue
        summary, body, _n_tr, n_nm = kb.prepare(bug["summary"], raw, bug.pop("_names"))
        text, trunc = kb.clean_with_truncation(summary, body)
        if "@" in text:
            text = re.sub(r"\S*@\S*", "[email]", text)
        if len(text) - len(summary) < kb.MIN_CHARS:
            stats["excluded_too_short"] += 1
            continue
        retriaged, changed = kb.severity_history(bug["id"])
        if retriaged:
            stats["excluded_severity_retriaged"] += 1
            continue
        assert not kb.leak_check(text), (bug["id"], kb.leak_check(text))
        stats["privacy_name_occurrences_scrubbed"] += n_nm
        recs.append({"bug_id": bug["id"], "url": f"https://bugzilla.kernel.org/show_bug.cgi?id={bug['id']}",
                     "tracker": "kernel", "group": bug["_group"],
                     "component": f"{bug['product']} :: {bug['component']}", "severity": bug["severity"],
                     "level": bug["_level"], "regression": int(bug.get("cf_regression") == "Yes"),
                     "cf_regression": bug.get("cf_regression"), "creation_time": bug["creation_time"],
                     "severity_changed_after_filing": changed, **trunc,
                     "text": text, "text_sha256": hashlib.sha256(text.encode()).hexdigest()})
        if len(recs) % 25 == 0:
            print(f"kernel: {len(recs)}/{n}", flush=True)
    return recs, stats


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tracker", choices=["mozilla", "kernel"], required=True)
    ap.add_argument("--n", type=int, default=N_PER_TRACKER)
    a = ap.parse_args()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f"{a.tracker}_heldout.jsonl"
    if out.exists():
        raise SystemExit(f"{out.name} exists; refusing to overwrite a held-out set.")
    recs, stats = (build_mozilla if a.tracker == "mozilla" else build_kernel)(a.n)
    if len(recs) < a.n:
        raise SystemExit(f"only {len(recs)} eligible held-out bugs; expected {a.n}")
    overlap = {r["bug_id"] for r in recs} & existing_ids(a.tracker)
    assert not overlap, overlap
    with out.open("w", encoding="utf-8") as f:
        for r in recs:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    from collections import Counter
    manifest = {"tracker": a.tracker, "seed": SEED, "n": len(recs), "sampling": "natural mix, random from full pool",
                "stats": stats, "mix": {f"{g}:level{l}": c for (g, l), c in
                                        sorted(Counter((r["group"], r["level"]) for r in recs).items())},
                "regression_share": round(sum(r["regression"] for r in recs) / len(recs), 3),
                "built_utc": datetime.now(timezone.utc).isoformat(),
                "sha256": {"dataset": hashlib.sha256(out.read_bytes()).hexdigest(),
                           "builder": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}}
    (OUT_DIR / f"{a.tracker}_heldout_manifest.json").write_text(json.dumps(manifest, indent=2))
    print(json.dumps(manifest, indent=1))


if __name__ == "__main__":
    main()
