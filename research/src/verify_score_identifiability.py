"""Pairwise identifiability analysis for the 6 primary-gate compositions.

New analysis, not previously computed: §3's "TWO_WAY"/"THREE_WAY" labels
say how many DISTINCT values appear among (M, X, A) on an item, but not
WHICH of the three candidate pairs (M-X, M-A, X-A) that item actually
separates. A "TWO_WAY" item separates exactly one pair while the other
two candidates coincide - it provides ZERO evidence for the coinciding
pair. This script computes, per pair, exactly how many of the 6 primary
items separate it - the identifiability question review's workstream 3
asks for, made concrete and counted rather than assumed uniform.

No API calls. Pure computation over the already-frozen composition table.
"""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
TABLE_CSV = REPO_ROOT / "research" / "results" / "score_semantic_composition_table.csv"
OUT_PATH = REPO_ROOT / "research" / "results" / "score_identifiability_analysis.json"

PRIMARY_COMPOSITIONS = [
    (0, 0, 0, 1), (0, 0, 0, 2), (0, 0, 1, 2),
    (0, 1, 1, 2), (0, 1, 2, 2), (1, 1, 1, 2),
]

PAIRS = [("M", "X"), ("M", "A"), ("X", "A")]


def load_table() -> dict:
    import csv
    rows = {}
    with TABLE_CSV.open() as f:
        for row in csv.DictReader(f):
            comp = eval(row["composition"])  # tuple literal, from our own trusted generator output
            rows[comp] = {
                "M": None if row["M"] == "" else int(row["M"]),
                "X": int(row["X"]),
                "A_rounded": int(row["A_rounded"]),
            }
    return rows


def main() -> None:
    table = load_table()

    print("=== Per-item pairwise separation (primary-gate compositions only) ===")
    per_item = {}
    for comp in PRIMARY_COMPOSITIONS:
        vals = {"M": table[comp]["M"], "X": table[comp]["X"], "A": table[comp]["A_rounded"]}
        assert vals["M"] is not None, f"{comp}: primary item must have M defined"
        separations = {f"{a}-{b}": vals[a] != vals[b] for a, b in PAIRS}
        per_item[str(comp)] = {"values": vals, "separates": separations}
        sep_str = ", ".join(f"{k}={'YES' if v else 'no'}" for k, v in separations.items())
        print(f"  {comp}  M={vals['M']} X={vals['X']} A={vals['A']}  ->  {sep_str}")

    print("\n=== Per-pair identifiability tally (out of 6 primary items) ===")
    pair_counts = {}
    for a, b in PAIRS:
        key = f"{a}-{b}"
        count = sum(1 for item in per_item.values() if item["separates"][key])
        pair_counts[key] = count
        print(f"  {key}: separated on {count}/6 items "
              f"({'FULL coverage' if count == 6 else 'PARTIAL coverage' if count > 0 else 'NO coverage'})")

    min_pair = min(pair_counts, key=pair_counts.get)
    max_pair = max(pair_counts, key=pair_counts.get)

    print(f"\n=== Finding ===")
    if pair_counts[min_pair] < pair_counts[max_pair]:
        print(f"  ASYMMETRIC IDENTIFIABILITY: {max_pair} is separated on {pair_counts[max_pair]}/6 items, "
              f"but {min_pair} is separated on only {pair_counts[min_pair]}/6 items.")
        print(f"  This design has WEAKER power to distinguish {min_pair} than to distinguish {max_pair} or the "
              f"remaining pair. A gate outcome driven mainly by {min_pair}-type disagreement rests on fewer "
              f"informative items than one driven by {max_pair}-type disagreement.")
    else:
        print(f"  All three pairs have equal identifiability ({pair_counts[min_pair]}/6 items each).")

    # Which items separate ONLY the weakest pair (i.e. are uniquely informative for it)?
    weak_pair_only_items = [
        comp for comp, item in per_item.items()
        if item["separates"][min_pair] and sum(item["separates"].values()) == 1
    ]

    record = {
        "primary_compositions": [str(c) for c in PRIMARY_COMPOSITIONS],
        "per_item_separation": per_item,
        "per_pair_identifiability_count": pair_counts,
        "weakest_pair": min_pair,
        "weakest_pair_count": pair_counts[min_pair],
        "strongest_pair": max_pair,
        "strongest_pair_count": pair_counts[max_pair],
        "asymmetric": pair_counts[min_pair] < pair_counts[max_pair],
        "items_uniquely_informative_for_weakest_pair": weak_pair_only_items,
    }
    OUT_PATH.write_text(json.dumps(record, indent=2))
    print(f"\nWritten to {OUT_PATH}")


if __name__ == "__main__":
    main()
