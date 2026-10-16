"""Strategy definitions and primary tests for
workflow_uncertainty_composition_protocol.md, Revision 12.

Why Revision 12 exists (full account:
research/results/mozilla_exploratory_analysis.md E1-E3):
Strategy 2 never reads the node decisions, while a* = F(c2*, c3*) escalates
on the severity level. So "2 vs 4a" mostly measured which arm is given the
information F needs, not whether composing uncertainty helps. And under
Y_decision an escalation is right only when a* = escalate, so escalating a
wrong decision to a human earns nothing, although the frozen cost matrix
(§16.1) prices exactly that as a remedy (1 + C_human vs 6-10).

Revision 12 asks the composition question on top of the decisions:
  2h: F(decisions) [Strategy 1], then also escalate the k least-confident
      instances by conf_product among those F did not already escalate.
  5h: the same, ranked by Strategy 5's per-primitive rank average U.
  R : the same number k of overrides chosen uniformly at random among the
      same candidates. A reference distribution, not a policy.
  k = min(ceil(R_OVERRIDE * n), #candidates), R_OVERRIDE = 0.10, a design
      constant set for human-review workload before any Step 2 data, and
      NOT chosen from the Mozilla override curve.
Primary tests, on per-instance cost C_action + C_human (§6, §16.1):
  H1: 2h vs R - does confidence pick better overrides than chance?
  H2: 5h vs 2h - does per-primitive normalization pick better ones?
  Holm across {H1, H2}, family-wise alpha = 0.05.
"""

from __future__ import annotations

import math
import random

from workflow_strategies_r11 import conf_product
from workflow_strategy5_proposal import strategy_5

R_OVERRIDE = 0.10
N_RANDOMIZATIONS = 10_000
SEED = 20261016
C_HUMAN_PER_ESCALATION = 1  # §6 placeholder

# §16.1, frozen; rows = action taken, columns = a*
COST = {
    "accept": {"accept": 0, "escalate": 10, "request_more_evidence": 6, "defer": 8},
    "escalate": {"accept": 1, "escalate": 0, "request_more_evidence": 1, "defer": 1},
    "request_more_evidence": {"accept": 1, "escalate": 1, "request_more_evidence": 0, "defer": 1},
    "defer": {"accept": 1, "escalate": 1, "request_more_evidence": 1, "defer": 0},
}


def cost(action: str, a_star: str) -> int:
    """C_action + C_human for one instance."""
    return COST[action][a_star] + (C_HUMAN_PER_ESCALATION if action == "escalate" else 0)


def n_overrides(n: int, n_candidates: int) -> int:
    return min(math.ceil(R_OVERRIDE * n), n_candidates)


def _override(base: dict, order: list) -> dict:
    cand = [i for i in order if base[i] != "escalate"]
    k = n_overrides(len(base), len(cand))
    flip = set(cand[:k])
    return {i: ("escalate" if i in flip else a) for i, a in base.items()}


def strategy_2h(base: dict, instances: list[tuple]) -> dict:
    """base: {id: Strategy 1 action}. instances: (id, node1, node2, node3).
    Undefined conf_product ranks least confident; ties by id."""
    cp = {inst[0]: conf_product(*inst[1:]) for inst in instances}
    order = sorted(cp, key=lambda i: (-1.0 if cp[i] is None else cp[i], str(i)))
    return _override(base, order)


def strategy_5h(base: dict, instances: list[tuple]) -> dict | None:
    """None if Strategy 5 is NOT COMPUTABLE (no admissible signal)."""
    s5 = strategy_5(instances, q=0.0)  # q unused here; only U and admissibility
    if s5["actions"] is None:
        return None
    order = sorted(s5["U"], key=lambda i: (-s5["U"][i], str(i)))
    return _override(base, order)


def h1_randomization_test(base: dict, hybrid: dict, a_star: dict,
                          n_draws: int = N_RANDOMIZATIONS, seed: int = SEED) -> dict:
    """H1: total cost of `hybrid` vs the distribution of total cost under k
    random overrides of the same candidates. Two-sided, centred on the exact
    random expectation; p = (1 + #extreme) / (1 + n_draws)."""
    cand = sorted((i for i in base if base[i] != "escalate"), key=str)
    k = n_overrides(len(base), len(cand))
    base_total = sum(cost(base[i], a_star[i]) for i in base)
    gain = {i: cost("escalate", a_star[i]) - cost(base[i], a_star[i]) for i in cand}
    expected = base_total + (k * sum(gain.values()) / len(cand) if cand else 0.0)
    observed = sum(cost(hybrid[i], a_star[i]) for i in hybrid)
    rng = random.Random(seed)
    dev = abs(observed - expected)
    extreme = sum(abs(base_total + sum(gain[i] for i in rng.sample(cand, k)) - expected) >= dev - 1e-9
                  for _ in range(n_draws))
    return {"k": k, "n_candidates": len(cand), "base_total_cost": base_total,
            "hybrid_total_cost": observed, "random_expected_total_cost": expected,
            "per_instance_difference_vs_random": (observed - expected) / len(base),
            "p_two_sided": (1 + extreme) / (1 + n_draws)}


def h2_sign_flip_test(x: dict, y: dict, a_star: dict,
                      n_draws: int = N_RANDOMIZATIONS, seed: int = SEED) -> dict:
    """H2: paired per-instance cost difference x - y, two-sided sign-flip
    randomization test on the sum. Instances with zero difference carry no
    information and are kept (they contribute 0 under every flip)."""
    d = [cost(x[i], a_star[i]) - cost(y[i], a_star[i]) for i in x]
    obs = sum(d)
    nz = [v for v in d if v != 0]
    rng = random.Random(seed)
    extreme = sum(abs(sum(v if rng.random() < 0.5 else -v for v in nz)) >= abs(obs) - 1e-9
                  for _ in range(n_draws))
    return {"total_difference": obs, "per_instance_difference": obs / len(d), "n_nonzero": len(nz),
            "p_two_sided": (1 + extreme) / (1 + n_draws)}


def holm(pvals: dict, alpha: float = 0.05) -> dict:
    """Holm-Bonferroni step-down. Returns {name: reject?}."""
    order = sorted(pvals, key=pvals.get)
    out, still = {}, True
    for rank, name in enumerate(order):
        still = still and pvals[name] <= alpha / (len(order) - rank)
        out[name] = still
    return out


def n_required_cost(sigma: float, mde_cost: float, alpha: float = 0.025, power: float = 0.80) -> int:
    """Normal-approximation sizing for a paired per-instance cost difference."""
    z = {0.025: 2.241402728, 0.05: 1.959963985}[alpha]  # two-sided z_{alpha/2}
    zp = {0.80: 0.8416212336}[power]
    return math.ceil(((z + zp) * sigma / mde_cost) ** 2)


def run_selftest() -> None:
    def node(conf=None, noul=None, stable=True, decision=None, modal=None):
        return {"mean_confidence": conf, "mean_noul": noul, "stable": stable, "decision": decision,
                "modal_decision": modal, "mean_probabilities": None}
    # 20 instances; F said accept for all; least confident 2 are the escalate targets
    ids = list(range(20))
    inst = [(i, node(conf=1.0), node(noul=0.1 if i > 1 else 0.45, decision=0), node(conf=0.6 + 0.01 * i, modal=1))
            for i in ids]
    base = {i: "accept" for i in ids}
    a_star = {i: ("escalate" if i < 2 else "accept") for i in ids}
    h = strategy_2h(base, inst)
    assert [i for i in ids if h[i] == "escalate"] == [0, 1], h  # k = ceil(0.1*20) = 2
    assert cost("accept", "escalate") == 10 and cost("escalate", "accept") == 2
    t = h1_randomization_test(base, h, a_star, n_draws=2000)
    assert t["hybrid_total_cost"] == 2 and t["base_total_cost"] == 20 and t["p_two_sided"] < 0.05, t
    # already-escalated instances are never candidates; k capped by candidates
    base2 = {i: ("escalate" if i < 19 else "accept") for i in ids}
    h2 = strategy_2h(base2, inst)
    assert sum(a == "escalate" for a in h2.values()) == 20
    # sign-flip: identical arms -> p = 1
    assert h2_sign_flip_test(h, h, a_star, n_draws=200)["p_two_sided"] == 1.0
    # Holm
    assert holm({"H1": 0.01, "H2": 0.04}) == {"H1": True, "H2": True}
    assert holm({"H1": 0.03, "H2": 0.04}) == {"H1": False, "H2": False}
    assert holm({"H1": 0.001, "H2": 0.30}) == {"H1": True, "H2": False}
    # 5h: noul spread makes it admissible; choice saturated is excluded
    h5 = strategy_5h(base, inst)
    assert h5 is not None and sum(a == "escalate" for a in h5.values()) == 2
    assert n_required_cost(1.0, 0.45) == math.ceil(((2.241402728 + 0.8416212336) / 0.45) ** 2)
    print("workflow_strategies_r12 selftest: all passed")


if __name__ == "__main__":
    run_selftest()
