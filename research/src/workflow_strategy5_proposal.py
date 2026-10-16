"""Strategy 5, primitive-aware composition by per-primitive rank. PROPOSED
for Revision 12; not yet part of the frozen protocol.

Motivation (research/results/threshold_transfer_finding.md): each
primitive's confidence lives on its own scale. choice is saturated at 1.0,
noul's 2|noul-0.5| shifts with the content distribution, and score's
confidence sits near 0.6. Strategy 2 multiplies these raw numbers, so
whichever scale happens to be smallest dominates, and a fixed cut-off
carries one content distribution's scale with it. Strategy 5 treats each
primitive's signal on its own terms first. That's the sense in which it
is primitive-aware.

Rule, fixed here before the full Mozilla run's results were examined, and
using no labels and no outcomes:
  1. Per-primitive uncertainty per instance:
       u_choice = 1 - choice mean_confidence
       u_noul   = 1 - 2|mean_noul - 0.5|
       u_score  = 1 - score mean_confidence
     An undefined signal (all calls failed) is treated as maximal
     uncertainty, 1.0.
  2. Admissibility, judged on the evaluated set's inputs only: a signal is
     admissible iff its single most common value (rounded to 3 decimals)
     covers at most half the instances. A signal tied on a majority of
     instances can't order them, which is exactly what made Revision
     10's choice trigger useless.
  3. Each admissible signal becomes its within-set rank percentile in
     [0, 1] (average ranks for ties).
  4. U = mean of the admissible percentiles. If no signal is admissible,
     Strategy 5 is reported as NOT COMPUTABLE; it never silently falls
     back.
  5. Escalate the ceil(q * n) instances with the highest U (ties by
     instance id) and accept the rest. q and the accept/escalate action
     space are exactly Strategy 2's (Revision 11), so Strategy 2 vs. 5
     differs ONLY in how the signals are combined.
"""

from __future__ import annotations

import math
from collections import Counter

MAX_MODAL_SHARE = 0.5


def uncertainties(node1: dict, node2: dict, node3: dict) -> dict:
    c, m, s = node1["mean_confidence"], node2["mean_noul"], node3["mean_confidence"]
    return {"choice": 1.0 if c is None else 1 - c,
            "noul": 1.0 if m is None else 1 - 2 * abs(m - 0.5),
            "score": 1.0 if s is None else 1 - s}


def admissible(values: list[float]) -> bool:
    if not values:
        return False
    top = Counter(round(v, 3) for v in values).most_common(1)[0][1]
    return top / len(values) <= MAX_MODAL_SHARE


def rank_percentiles(values: list[float]) -> list[float]:
    n = len(values)
    if n == 1:
        return [0.5]
    order = sorted(range(n), key=lambda i: values[i])
    ranks = [0.0] * n
    i = 0
    while i < n:
        j = i
        while j + 1 < n and values[order[j + 1]] == values[order[i]]:
            j += 1
        for k in range(i, j + 1):
            ranks[order[k]] = (i + j) / 2
        i = j + 1
    return [r / (n - 1) for r in ranks]


def strategy_5(instances: list[tuple], q: float) -> dict:
    """instances: (instance_id, node1, node2, node3). Returns
    {"actions": {id: action} or None, "admissible": [...], "excluded": [...]}."""
    ids = [inst[0] for inst in instances]
    us = [uncertainties(*inst[1:]) for inst in instances]
    signals = ("choice", "noul", "score")
    adm = [s for s in signals if admissible([u[s] for u in us])]
    result = {"admissible": adm, "excluded": [s for s in signals if s not in adm]}
    if not adm:
        result["actions"] = None  # NOT COMPUTABLE - reported, never silently replaced
        return result
    pct = {s: rank_percentiles([u[s] for u in us]) for s in adm}
    U = {ids[i]: sum(pct[s][i] for s in adm) / len(adm) for i in range(len(ids))}
    n_escalate = math.ceil(q * len(ids))
    ranked = sorted(ids, key=lambda i: (-U[i], str(i)))
    esc = set(ranked[:n_escalate])
    result["actions"] = {i: ("escalate" if i in esc else "accept") for i in ids}
    result["U"] = U
    return result
