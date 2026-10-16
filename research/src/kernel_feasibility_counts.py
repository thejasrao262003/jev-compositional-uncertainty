"""Feasibility counts for the proposed Linux kernel Bugzilla replication
(research/methodology/kernel_replication_proposal.md). Mirrors
mozilla_feasibility_counts.py.

Queries the public bugzilla.kernel.org REST API (read-only; User-Agent
set, 0.5 s between requests, limit/offset paging). The kernel's Bugzilla
5.1.1 ignores `count_only`, so counts are taken from paged id lists. No Jev
API call is made. No bug text, e-mail address or personal name is written
to disk: the description sample records lengths and a log-line share only,
and the history sample records only whether severity changed.

Groups, severities, resolutions and the HTTP helper are imported from
build_kernel_dataset.py so the two cannot drift apart.

Output: research/results/kernel_feasibility_counts.json
"""

from __future__ import annotations

import json
import random
import statistics
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SRC_DIR))

import build_kernel_dataset as kb  # noqa: E402

SEVERITIES = ["blocking", "high", "normal", "low", "enhancement"]
FIELDS = "id,severity,cf_regression,creation_time,product,component"
SAMPLE_PER_CELL = 8
SAMPLE_SEED = "kernel-feasibility-sample-v1"

OUT = SRC_DIR.parent / "results" / "kernel_feasibility_counts.json"


def fetch_group(group: str) -> list[dict]:
    bugs = {}
    for product, comps in kb.GROUPS[group]:
        for b in kb.search(kb.group_query(product, comps, SEVERITIES, FIELDS)):
            bugs[b["id"]] = b
    return [bugs[i] for i in sorted(bugs)]


def main():
    rng = random.Random(SAMPLE_SEED)
    record = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "source": kb.BZ,
        "status": "counts only; no Jev call made",
        "filters": {"resolution": kb.FIXED_RESOLUTIONS, "created_from": None,
                    "recent_from": kb.RECENT_FROM},
        "groups": {g: [f"{p} :: {', '.join(c) if c else '(all components)'}" for p, c in v]
                   for g, v in kb.GROUPS.items()},
        "severity_to_level": kb.LEVELS,
        "counts_by_severity": {}, "counts_by_level": {}, "cf_regression_values": {},
        "regression_yes_by_level": {}, "recent_since_2018_by_level": {},
        "recent_since_2018_regression_yes_by_level": {}, "components": {},
        "description_sample": {}, "severity_history_sample": {},
    }
    for group in kb.GROUPS:
        bugs = fetch_group(group)
        record["counts_by_severity"][group] = dict(Counter(b["severity"] for b in bugs))
        record["cf_regression_values"][group] = dict(Counter(str(b.get("cf_regression")) for b in bugs))
        record["components"][group] = dict(Counter(f"{b['product']} :: {b['component']}" for b in bugs))
        by_level = {lv: [b for b in bugs if kb.LEVELS.get(b["severity"]) == lv] for lv in (2, 1, 0)}
        record["counts_by_level"][group] = {f"level{lv}": len(v) for lv, v in by_level.items()}
        record["regression_yes_by_level"][group] = {
            f"level{lv}": sum(b.get("cf_regression") == "Yes" for b in v) for lv, v in by_level.items()}
        recent = {lv: [b for b in v if b["creation_time"][:10] >= kb.RECENT_FROM] for lv, v in by_level.items()}
        record["recent_since_2018_by_level"][group] = {f"level{lv}": len(v) for lv, v in recent.items()}
        record["recent_since_2018_regression_yes_by_level"][group] = {
            f"level{lv}": sum(b.get("cf_regression") == "Yes" for b in v) for lv, v in recent.items()}
        # Seeded random sample per cell: description length, log-line share,
        # and whether severity was ever changed after filing.
        lengths, shares, changed, sampled = [], [], 0, 0
        for lv in (2, 1, 0):
            pool = sorted(b["id"] for b in by_level[lv])
            for bug_id in rng.sample(pool, min(SAMPLE_PER_CELL, len(pool))):
                text = kb.first_comment(bug_id)
                lengths.append(len(text))
                lines = [ln for ln in text.splitlines() if ln.strip()]
                shares.append(sum(bool(kb.LOG_LINE_RE.match(ln)) for ln in lines) / len(lines) if lines else 0.0)
                changed += int(kb.severity_history(bug_id)[1])
                sampled += 1
        record["description_sample"][group] = {
            "n": len(lengths), "median_chars": statistics.median(lengths), "max_chars": max(lengths),
            "share_over_2000_chars": round(sum(n > kb.MAX_CHARS for n in lengths) / len(lengths), 3),
            "median_log_line_share": round(statistics.median(shares), 3)}
        record["severity_history_sample"][group] = {"n": sampled, "severity_changed_after_filing": changed}
        print(group, record["counts_by_level"][group], flush=True)
    OUT.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(record, indent=2))


if __name__ == "__main__":
    main()
