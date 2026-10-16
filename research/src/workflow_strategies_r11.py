"""Strategy definitions for workflow_uncertainty_composition_protocol.md, Revision 11.

Why these replace Revision 10's Strategy 2 and 4a, in one paragraph (the
full account is research/results/threshold_transfer_finding.md):
Revision 10 used fixed numeric thresholds: Strategy 2 accepted when
conf_product >= 0.5, and 4a escalated when choice confidence >= 0.90.
Measured on the strategies' own input signals, with no labels involved,
neither threshold transferred between content distributions. choice
confidence is saturated (median 1.0 on synthetic AND real text), so the
0.90 trigger fired on 27/30 synthetic and 19/21 real inputs and cannot
select a minority on any threshold. Strategy 2's 0.5 cut escalated 73% of
synthetic inputs (close to the 67% a perfect binary policy would) but 90%
of real ones (against about 41%).

Revision 11 rules, neither tuned on outcomes:
  Strategy 2: escalate exactly ceil(q * n) instances with the lowest
    conf_product in the evaluated set (ties broken by instance id), accept
    the rest. q is the share of instances whose target action is not
    "accept": fixed by construction for designed data (6/9 for Step 2's
    balanced design), the label marginal for externally labeled data.
  Strategy 4a: the choice-confidence trigger is removed. 4a escalates on
    repeat instability (choice or score node), otherwise returns F(noul
    decision, score decision), escalating on an undefined input.

The frozen Revision 10 functions in run_workflow_calibration_pilot.py are
not modified; they stay the record of what the first pilot ran.
"""

from __future__ import annotations

import math

from build_workflow_calibration_pilot_manifest import F

STEP2_DESIGN_Q = 6 / 9  # share of the 9 (c2*, c3*) cells whose F(.) != "accept"


def conf_product(node1: dict, node2: dict, node3: dict) -> float | None:
    """Revision 10's composed confidence-like statistic, unchanged."""
    if node1["mean_confidence"] is None or node3["mean_confidence"] is None or node2["mean_noul"] is None:
        return None
    return node1["mean_confidence"] * 2 * abs(node2["mean_noul"] - 0.5) * node3["mean_confidence"]


def prevalence_q(a_stars: list[str]) -> float:
    """Share of target actions that are not "accept". Uses only the target
    marginal, never which instance has which target or any model output."""
    return sum(a != "accept" for a in a_stars) / len(a_stars)


def strategy_2_r11(instances: list[tuple], q: float) -> dict:
    """instances: (instance_id, node1, node2, node3). Returns {id: action}.
    Escalates exactly ceil(q * n) instances by ascending conf_product; an
    instance with undefined conf_product is ranked lowest (escalated
    first). Ties are broken by instance id, so the result is deterministic."""
    if not 0.0 <= q <= 1.0:
        raise ValueError(f"q must be in [0, 1], got {q}")
    n_escalate = math.ceil(q * len(instances))

    def key(inst):
        cp = conf_product(*inst[1:])
        return (-1.0 if cp is None else cp, str(inst[0]))
    ranked = sorted(instances, key=key)
    escalate = {inst[0] for inst in ranked[:n_escalate]}
    return {inst[0]: ("escalate" if inst[0] in escalate else "accept") for inst in instances}


def strategy_4a_r11(node1: dict, node2: dict, node3: dict) -> str:
    if not node1["stable"] or not node3["stable"]:
        return "escalate"  # repeat-instability trigger: deployable, unchanged from Revision 10
    if node2["decision"] is None or node3["modal_decision"] is None:
        return "escalate"
    return F(node2["decision"], int(node3["modal_decision"]))


def selectivity(fired: list[bool]) -> float:
    """Share of inputs on which a trigger fires. A trigger that fires on
    nearly every input carries almost no information about WHICH input
    to escalate. This is computed from inputs only, never labels."""
    return sum(fired) / len(fired) if fired else float("nan")
