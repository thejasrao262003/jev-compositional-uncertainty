"""Designs and verifies a small M-vs-A supplementary composition set.

Per review: the frozen 6-item primary set (score_semantic_validation_
specification.md, Revision 7) is NOT modified. This is a separately
versioned extension, searched in a GENUINELY NEW composition space (n=5
sentences, not a replication of the exhausted n=4/3-level space - all 15
possible n=4/3-level multisets are already accounted for across the
primary/supplementary/control/non-discriminative categories, so there are
no new n=4 patterns left to add).

Pre-registered selection criteria (checked mechanically below, not by
inspection):
  1. M is defined and unique for the composition.
  2. A is defined under the EXISTING rounding rule (round-half-up),
     unchanged from the frozen spec.
  3. M != A (the item actually separates the target pair).
  4. The composition's discrimination class is computed and recorded
     (not assumed).
  5. Its relationship to X is recorded explicitly, not treated as
     irrelevant to the pair under study.
  6. Selection is by exhaustive search over n=5 compositions matching
     criteria 1-3, with a diversity rule (see below) - NOT by inspecting
     any Jev response (none exists; this script makes no API calls).
  7. Resulting combined (frozen 6 + supplement) pairwise coverage is
     computed and reported BEFORE any semantic evaluation.

No API calls. No modification to the frozen primary set or its artifacts.
"""

from __future__ import annotations

import json
import math
from collections import Counter
from itertools import combinations_with_replacement as cwr
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
OUT_PATH = REPO_ROOT / "research" / "results" / "score_mvsa_supplement_v1.json"

# The frozen primary 6 (unchanged, imported as data only - not re-derived
# differently here; source of truth remains score_semantic_composition_table.csv)
FROZEN_PRIMARY = {
    (0, 0, 0, 1): {"M": 0, "X": 1, "A": 0},
    (0, 0, 0, 2): {"M": 0, "X": 2, "A": 1},
    (0, 0, 1, 2): {"M": 0, "X": 2, "A": 1},
    (0, 1, 1, 2): {"M": 1, "X": 2, "A": 1},
    (0, 1, 2, 2): {"M": 2, "X": 2, "A": 1},
    (1, 1, 1, 2): {"M": 1, "X": 2, "A": 1},
}
PAIRS = [("M", "X"), ("M", "A"), ("X", "A")]
SUFFICIENCY_THRESHOLD = 6  # symmetric, per review: applies to ALL THREE pairs, not just M-vs-A
# Rationale for 6: matches the precedent set by X-vs-A's full 6/6 coverage in
# the original design - not an arbitrary number chosen to make M-vs-A pass.


def round_half_up(x: float) -> int:
    return math.floor(x + 0.5)


def analyze(comp: tuple[int, ...]) -> dict:
    counts = Counter(comp)
    most_common = counts.most_common()
    m = most_common[0][0] if (len(most_common) == 1 or most_common[0][1] > most_common[1][1]) else None
    x = max(comp)
    a_un = sum(comp) / len(comp)
    a = round_half_up(a_un)
    return {"M": m, "X": x, "A_unrounded": a_un, "A": a}


def search_n5_mvsa_candidates() -> list[dict]:
    """Exhaustive search, n=5 sentences, levels {0,1,2} - a genuinely new
    space, not a re-tread of the exhausted n=4 patterns."""
    found = []
    for comp in cwr([0, 1, 2], 5):
        r = analyze(comp)
        if r["M"] is None:
            continue  # criterion 1: M must be defined
        if r["M"] == r["A"]:
            continue  # criterion 3: must separate M from A
        distinct = len({r["M"], r["X"], r["A"]})
        disc_class = "THREE_WAY" if distinct == 3 else "TWO_WAY"  # criterion 4
        found.append({
            "composition": comp, "n_sentences": len(comp), "M": r["M"], "X": r["X"],
            "A_unrounded": round(r["A_unrounded"], 4), "A": r["A"],
            "discrimination_class": disc_class,
            "relationship_to_X": (  # criterion 5: recorded explicitly
                "M=X, separates from A only" if r["M"] == r["X"] else
                "M, X, A all distinct" if distinct == 3 else
                "X=A, separates from M only"  # not expected here given M!=A already filtered, kept for completeness
            ),
        })
    return found


def select_diverse_three(candidates: list[dict], n_three_way: int = 2, n_two_way: int = 1) -> list[dict]:
    """Diversity rule (pre-registered, not post-hoc): take the first
    `n_three_way` THREE_WAY and first `n_two_way` TWO_WAY items by
    deterministic sort order (composition tuple, ascending) - no
    randomness, no data-dependence, and critically: this rule NEVER
    inspects pairwise coverage counts when choosing, so it cannot have
    been reverse-engineered to hit a coverage target. Parametrized so the
    alternative allocation (1 three-way + 2 two-way) can be run as an
    explicit robustness check (see run_selection_robustness_check)."""
    candidates = sorted(candidates, key=lambda c: c["composition"])
    three_way = [c for c in candidates if c["discrimination_class"] == "THREE_WAY"]
    two_way = [c for c in candidates if c["discrimination_class"] == "TWO_WAY"]
    selected = three_way[:n_three_way] + two_way[:n_two_way]
    excluded = [c for c in candidates if c not in selected]
    assert len(selected) == n_three_way + n_two_way, f"selection rule did not yield the expected count: {selected}"
    return selected, excluded


def run_selection_robustness_check(candidates: list[dict]) -> None:
    """Confirms the PRIMARY selection rule (2 three-way + 1 two-way) is
    not the only allocation that would have cleared the sufficiency
    threshold - i.e. the diversity rule wasn't implicitly reverse-
    engineered to hit the target. Tests the alternative (1 three-way + 2
    two-way) allocation and confirms IT ALSO clears >=6 on every pair."""
    print("\n=== Selection-rule robustness check (per review) ===")
    alt_selected, _ = select_diverse_three(candidates, n_three_way=1, n_two_way=2)
    alt_items = {c["composition"]: {"M": c["M"], "X": c["X"], "A": c["A"]} for c in alt_selected}
    alt_combined = {**FROZEN_PRIMARY, **alt_items}
    alt_coverage = compute_pairwise_coverage(alt_combined)
    alt_all_sufficient = all(v >= SUFFICIENCY_THRESHOLD for v in alt_coverage.values())
    print(f"  Alternative allocation (1 THREE_WAY + 2 TWO_WAY): {[c['composition'] for c in alt_selected]}")
    print(f"  Alternative coverage: {alt_coverage}")
    print(f"  Alternative also meets sufficiency on all 3 pairs: {alt_all_sufficient}")
    assert alt_all_sufficient, (
        "the alternative allocation does NOT clear the threshold - this means the primary rule's "
        "2-three-way/1-two-way choice may have been load-bearing for the result, which would need disclosure"
    )
    print("  CONFIRMED: both the primary (2+1) and alternative (1+2) allocations independently clear the "
          "sufficiency threshold on all 3 pairs - the specific 2:1 ratio chosen was not necessary for this "
          "result, supporting that the selection rule was not reverse-engineered to hit the target.")


def compute_pairwise_coverage(items: dict) -> dict:
    coverage = {f"{a}-{b}": 0 for a, b in PAIRS}
    for comp, vals in items.items():
        for a, b in PAIRS:
            if vals[a] != vals[b]:
                coverage[f"{a}-{b}"] += 1
    return coverage


def main() -> None:
    print("=== Pre-registered search: n=5 compositions separating M from A ===")
    candidates = search_n5_mvsa_candidates()
    for c in candidates:
        print(f"  {c['composition']}: M={c['M']} X={c['X']} A_unrounded={c['A_unrounded']} A={c['A']} "
              f"-> {c['discrimination_class']}, relationship_to_X: {c['relationship_to_X']}")
    print(f"  Found {len(candidates)} candidates satisfying criteria 1-3 (M defined, A defined, M!=A)")

    selected, excluded = select_diverse_three(candidates)
    print(f"\n=== Selected 3, per the pre-registered diversity rule (2 THREE_WAY + 1 TWO_WAY, sorted, no Jev data involved) ===")
    for c in selected:
        print(f"  {c['composition']}: M={c['M']} X={c['X']} A={c['A']} -> {c['discrimination_class']} "
              f"({c['relationship_to_X']})")
    print(f"\n=== Excluded, and why ===")
    for c in excluded:
        print(f"  {c['composition']}: excluded - the rule takes the first 1 TWO_WAY candidate by ascending "
              f"composition-tuple sort; this candidate sorts after the one that was selected within its class.")

    run_selection_robustness_check(candidates)

    supplement_items = {c["composition"]: {"M": c["M"], "X": c["X"], "A": c["A"]} for c in selected}

    print("\n=== Combined pairwise coverage: frozen 6 + supplementary 3 = 9 items ===")
    combined = {**FROZEN_PRIMARY, **supplement_items}
    assert len(combined) == 9, "expected 9 combined items (6 frozen + 3 new, all distinct compositions)"
    frozen_coverage = compute_pairwise_coverage(FROZEN_PRIMARY)
    combined_coverage = compute_pairwise_coverage(combined)

    print(f"  {'pair':8s} {'frozen (of 6)':15s} {'combined (of 9)':17s} {'meets sufficiency (>=6)?'}")
    all_sufficient = True
    for a, b in PAIRS:
        key = f"{a}-{b}"
        sufficient = combined_coverage[key] >= SUFFICIENCY_THRESHOLD
        all_sufficient = all_sufficient and sufficient
        print(f"  {key:8s} {frozen_coverage[key]}/6{'':11s} {combined_coverage[key]}/9{'':13s} "
              f"{'YES' if sufficient else 'NO'}")

    assert combined_coverage["M-A"] > frozen_coverage["M-A"], "supplement did not improve M-vs-A coverage at all"
    print(f"\nM-vs-A coverage improved from {frozen_coverage['M-A']}/6 to {combined_coverage['M-A']}/9 "
          f"({'meets' if combined_coverage['M-A'] >= SUFFICIENCY_THRESHOLD else 'still does not meet'} "
          f"the symmetric sufficiency threshold of >={SUFFICIENCY_THRESHOLD} separating items)")

    record = {
        "status": "DESIGN ONLY - not executed, not approved for execution. Separately versioned from the frozen primary 6.",
        "frozen_primary_compositions": {str(c): {**v, "n_sentences": 4} for c, v in FROZEN_PRIMARY.items()},
        "all_4_qualifying_n5_candidates": [
            {"composition": str(c["composition"]), "n_sentences": c["n_sentences"], "M": c["M"], "X": c["X"],
             "A_unrounded": c["A_unrounded"], "A": c["A"], "discrimination_class": c["discrimination_class"],
             "relationship_to_X": c["relationship_to_X"]}
            for c in sorted(candidates, key=lambda c: c["composition"])
        ],
        "supplement_v1_selected": [
            {"composition": str(c["composition"]), "n_sentences": c["n_sentences"], "M": c["M"], "X": c["X"], "A": c["A"],
             "discrimination_class": c["discrimination_class"], "relationship_to_X": c["relationship_to_X"]}
            for c in selected
        ],
        "excluded_candidate": {
            "composition": str(excluded[0]["composition"]) if excluded else None,
            "reason": "Deterministic diversity rule (2 THREE_WAY + 1 TWO_WAY by ascending composition-tuple "
                "sort) selects only 1 of the 2 qualifying TWO_WAY candidates; this one sorts second within "
                "its class and was not selected. Not excluded for any coverage-outcome reason.",
        },
        "selection_rule_reproducibility": "select_diverse_three(candidates, n_three_way=2, n_two_way=1): "
            "sort all qualifying candidates by composition tuple ascending; partition by discrimination_class; "
            "take the first n_three_way THREE_WAY and first n_two_way TWO_WAY items. Fully mechanical - takes "
            "no coverage counts, no Jev output, and no outcome preference as input. Reproducible by anyone "
            "given only the candidate list and the two integer parameters.",
        "selection_rule_robustness_check": "the alternative allocation (1 THREE_WAY + 2 TWO_WAY) was also "
            "tested and independently clears the >=6 sufficiency threshold on all 3 pairs (see console output) "
            "- the specific 2:1 ratio was not necessary for the result, evidence against the rule having been "
            "reverse-engineered to hit the target.",
        "selection_criteria": [
            "M defined and unique", "A defined under the existing round-half-up rule",
            "M != A (separates the target pair)", "discrimination class computed and recorded",
            "relationship to X recorded explicitly", "selected by exhaustive search + a pre-registered "
            "diversity rule (2 THREE_WAY + 1 TWO_WAY, sorted deterministically) - not by inspecting any "
            "Jev response, since none exists",
        ],
        "sentence_count_metadata": {
            "frozen_primary_n_sentences": 4,
            "supplement_v1_n_sentences": 5,
            "flagged_confound": "Composition-level pairwise separation (the mathematical M/X/A relationship) "
                "is unaffected by sentence count and has been verified independently of it. However, input "
                "LENGTH itself is a separate variable this supplement introduces: whether Jev's actual "
                "aggregation behavior differs between 4-sentence and 5-sentence inputs is untested and "
                "unrelated to which severity levels are present. Any eventual results report must keep three "
                "things separate: (1) composition-level pairwise separation [verified, this document], (2) "
                "input-length effects [NOT tested - no n=5 control exists yet to isolate this], (3) actual "
                "Jev semantic evidence [not yet collected]. This is a documented, unresolved limitation, not "
                "a claim that n=4 and n=5 items are equivalent.",
        },
        "no_selection_based_on_jev_output": "Confirmed structurally: this entire script makes zero API calls "
            "and reads no Jev response data; candidate discovery and selection are pure functions of the "
            "composition math (mode/max/mean) defined before this document existed.",
        "sufficiency_threshold": SUFFICIENCY_THRESHOLD,
        "sufficiency_threshold_rationale": "matches the precedent set by X-vs-A's full 6/6 coverage in the "
            "original 6-item design - applied symmetrically to all three pairs. This is a MATCHED PRECEDENT, "
            "explicitly NOT a validated sufficiency threshold - whether >=6 is scientifically adequate remains "
            "open (see score_semantic_identification_protocol.md's decision gate).",
        "frozen_coverage": frozen_coverage,
        "combined_coverage": combined_coverage,
        "all_three_pairs_meet_sufficiency_after_supplement": all_sufficient,
        "decision_gate": "Per score_semantic_validation_specification.md §8's three-tier hierarchy: this "
            "document addresses verifier/design-level coverage only. Semantic validity (is M/X/A correct?) "
            "and research validity (is this design scientifically adequate?) remain OPEN and are not advanced "
            "by clearing this numeric threshold.",
        "note": "This supplement improves pairwise coverage counts. It does NOT establish that M, X, or A is "
            "correct, that these items are representative of real score inputs, that each item has equal "
            "evidentiary value, or that meeting this numeric threshold is scientifically sufficient - see "
            "score_semantic_validation_specification.md §8's three-tier validity hierarchy, unchanged by this document.",
    }
    OUT_PATH.write_text(json.dumps(record, indent=2))
    print(f"\nWritten to {OUT_PATH}")
    print("\n=== DESIGN COMPLETE. No API calls made. No frozen artifact modified. Submitted for review. ===")


if __name__ == "__main__":
    main()
