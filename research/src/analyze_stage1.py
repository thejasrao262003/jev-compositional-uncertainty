"""Stage 1 analysis: repeat-instability (S/I) and presentation-sensitivity
(D(x)) statistics, per step0b_design_specification.md §8B/§8C.

Implements, and enforces at the code level (not just by convention):
  - the H2a gate: any `noul` metric requires stage0_gate_outcomes.json's
    recorded verdict to be "pass" before it is computed at all (§15 check
    #10) - this is not a comment, it's a guard that raises if violated.
  - complete-cell filtering: S/I require exactly the 3 canonical-order
    records (m==3); D(x) requires exactly the 3 presentations (k==3) -
    incomplete cells are routed to a separate missingness list, never
    silently aggregated with complete ones (§15 check #11).

Self-tested below against synthetic fixture records shaped like
run_stage1.py's raw_responses.jsonl rows - this has NOT been run against
real Stage 1 data because Stage 1 has not been executed yet.
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
GATE_OUTCOMES_PATH = REPO_ROOT / "research" / "data" / "characterization" / "stage0_gate_outcomes.json"


class H2aNotPassedError(Exception):
    """Raised if noul metrics are requested but H2a's recorded gate isn't a pass."""


def load_gate_outcomes(path: Path = GATE_OUTCOMES_PATH) -> dict:
    return json.loads(path.read_text())


def noul_h2a_passed(gate_outcomes: dict) -> bool:
    return gate_outcomes.get("gates", {}).get("noul_h2a", {}).get("status") == "pass"


def require_h2a_passed(gate_outcomes: dict) -> None:
    if not noul_h2a_passed(gate_outcomes):
        raise H2aNotPassedError(
            "noul H2a gate is not recorded as 'pass' in stage0_gate_outcomes.json - "
            "no noul confidence/accuracy/ECE/Brier metric may be computed. "
            "See step0b_design_specification.md §8A: noul is reported via "
            "characterization-only path when H2a fails."
        )


def top_two_gap(probabilities: dict[str, float]) -> float:
    vals = sorted(probabilities.values(), reverse=True)
    return vals[0] - (vals[1] if len(vals) > 1 else 0.0)


def selected_decision(answer: dict) -> Any:
    if answer["type"] == "choice":
        return answer["choice"]
    if answer["type"] == "score":
        return answer["score"]
    if answer["type"] == "noul":
        return "yes" if answer["noul"] >= 0.5 else "no"
    raise ValueError(f"unknown answer type: {answer['type']}")


def compute_repeat_instability(records: list[dict], gate_outcomes: dict,
                                subset_item_ids: set[str] | None = None) -> tuple[dict[str, dict], list[dict]]:
    """§8B: S(x,p), I(x,p) etc. Requires exactly m==3 canonical-order
    records per item (primary_canonical + 2x canonical_repeat). Items with
    m<3 go to the missingness list, never into the results dict.

    IMPORTANT: only items in `subset_item_ids` (the manifest's
    robustness_repeat_subset_ids, i.e. items DESIGNED to receive repeats)
    are considered at all. An item outside that subset was only ever
    planned to get 1 canonical call - it is not "missing" data, it's simply
    not part of this layer by design, and must not appear in either
    `results` or `missingness`. Passing None disables this filter (checks
    every item that has any qualifying record) - only appropriate for
    fixture/self-test data that doesn't distinguish subset membership.
    """
    by_item = defaultdict(list)
    for r in records:
        if r["call_purpose"] in ("primary_canonical", "canonical_repeat"):
            if subset_item_ids is not None and r["item_id"] not in subset_item_ids:
                continue  # out of scope for this layer by design, not missing data
            by_item[r["item_id"]].append(r)

    results: dict[str, dict] = {}
    missingness: list[dict] = []
    for item_id, recs in by_item.items():
        primitive = recs[0]["primitive"]
        if primitive == "noul":
            require_h2a_passed(gate_outcomes)  # raises if H2a hasn't passed - enforced, not optional
        m = len(recs)
        if m != 3:  # complete-cell rule (§7, §10) - enforced here, not just documented
            missingness.append({"item_id": item_id, "layer": "repeat_instability", "m_observed": m, "m_required": 3})
            continue
        decisions = [selected_decision(r["answer"]) for r in recs]
        counts = {d: decisions.count(d) for d in set(decisions)}
        modal_count = max(counts.values())
        s = modal_count / m
        results[item_id] = {
            "S": s, "I": 1 - s,
            "any_flip": len(set(decisions)) > 1,
            "n_distinct_decisions": len(set(decisions)),
            "decisions": decisions,
        }
    return results, missingness


def compute_presentation_sensitivity(records: list[dict], gate_outcomes: dict,
                                      subset_item_ids: set[str] | None = None) -> tuple[dict[str, dict], list[dict]]:
    """§8C: D(x) etc. Requires exactly k==3 presentations per item
    (primary_canonical + alt_presentation_reverse + alt_presentation_seeded_shuffle).
    Items with k<3 go to the missingness list.

    IMPORTANT: same subset-scoping as compute_repeat_instability - an item
    outside `subset_item_ids` was never planned to get alternate
    presentations at all; it is out of scope for this layer, not missing.
    """
    by_item = defaultdict(list)
    for r in records:
        if r["call_purpose"] in ("primary_canonical", "alt_presentation_reverse", "alt_presentation_seeded_shuffle"):
            if subset_item_ids is not None and r["item_id"] not in subset_item_ids:
                continue
            by_item[r["item_id"]].append(r)

    results: dict[str, dict] = {}
    missingness: list[dict] = []
    for item_id, recs in by_item.items():
        primitive = recs[0]["primitive"]
        if primitive == "noul":
            require_h2a_passed(gate_outcomes)
        k = len(recs)
        if k != 3:  # complete-cell rule - enforced
            missingness.append({"item_id": item_id, "layer": "presentation_sensitivity", "k_observed": k, "k_required": 3})
            continue
        decisions = [selected_decision(r["answer"]) for r in recs]
        top_probs = [max(r["answer"]["probabilities"].values()) if "probabilities" in r["answer"]
                     else r["answer"]["noul"] for r in recs]
        results[item_id] = {
            "D": len(set(decisions)) / k,
            "top_prob_range": max(top_probs) - min(top_probs),
            "max_pairwise_diff": max(abs(a - b) for a in top_probs for b in top_probs),
            "label_changes": len(set(decisions)) > 1,
        }
    return results, missingness


# --- Self-test: synthetic records, shaped like run_stage1.py's output ----

def _fixture_records() -> list[dict]:
    def rec(item_id, primitive, call_purpose, choice, p_choice, p_other):
        return {
            "item_id": item_id, "primitive": primitive, "call_purpose": call_purpose,
            "answer": {"type": "choice", "choice": choice,
                       "probabilities": {"a": p_choice if choice == "a" else p_other,
                                          "b": p_choice if choice == "b" else p_other}},
        }

    records = []
    # complete item (m=3, all agree) -> S=1.0, I=0.0
    for cp in ("primary_canonical", "canonical_repeat", "canonical_repeat"):
        records.append(rec("choice_complete_agree", "choice", cp, "a", 0.9, 0.1))
    # complete item (m=3, split 2:1) -> S=2/3, I=1/3, flip
    records.append(rec("choice_complete_split", "choice", "primary_canonical", "a", 0.55, 0.45))
    records.append(rec("choice_complete_split", "choice", "canonical_repeat", "b", 0.51, 0.49))
    records.append(rec("choice_complete_split", "choice", "canonical_repeat", "a", 0.52, 0.48))
    # incomplete item (m=2, one call missing) -> must go to missingness, not results
    records.append(rec("choice_incomplete", "choice", "primary_canonical", "a", 0.8, 0.2))
    records.append(rec("choice_incomplete", "choice", "canonical_repeat", "a", 0.8, 0.2))
    return records


def run_self_test() -> None:
    records = _fixture_records()

    print("=== Self-test: H2a gate enforcement ===")
    gate_fail = {"gates": {"noul_h2a": {"status": "flagged_blocked"}}}
    gate_pass = {"gates": {"noul_h2a": {"status": "pass"}}}
    noul_rec = {"item_id": "noul_x", "primitive": "noul", "call_purpose": "primary_canonical",
                "answer": {"type": "noul", "noul": 0.7}}
    try:
        compute_repeat_instability([noul_rec, noul_rec, noul_rec], gate_fail)
        raise AssertionError("expected H2aNotPassedError to be raised")
    except H2aNotPassedError:
        print("PASS: noul metric correctly BLOCKED when H2a gate is not 'pass'")

    # choice-only records should compute fine regardless of the noul gate
    results, missing = compute_repeat_instability(records, gate_fail)
    assert "choice_complete_agree" in results and "choice_complete_split" in results
    assert "choice_incomplete" not in results
    print("PASS: choice metrics computed even when noul gate is blocked (gate is per-primitive)")

    print("\n=== Self-test: repeat instability (S/I) ===")
    print(json.dumps(results, indent=2))
    assert results["choice_complete_agree"]["S"] == 1.0 and results["choice_complete_agree"]["I"] == 0.0
    assert abs(results["choice_complete_split"]["S"] - 2 / 3) < 1e-9
    assert results["choice_complete_split"]["any_flip"] is True
    print("PASS: S/I values match hand-computed expectations")

    print("\n=== Self-test: complete-cell filtering ===")
    print("missingness:", json.dumps(missing, indent=2))
    assert len(missing) == 1 and missing[0]["item_id"] == "choice_incomplete" and missing[0]["m_observed"] == 2
    print("PASS: incomplete cell (m=2) correctly excluded from results and routed to missingness")

    print("\nAll self-test assertions passed.")


if __name__ == "__main__":
    run_self_test()
