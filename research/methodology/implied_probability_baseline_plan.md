# Plan: a stronger confidence baseline (model-implied action probability)

**Status:** written 2026-11-08, before computing. Exploratory and post
hoc: the 500 held-out bugs have been analysed before. It responds to
comment M2 of `research/paper/reviews/ieee_short_review.md`.

**No API or GPU calls;** existing outputs only.

## Why

The main comparison sets the action-rule score *r(a)* against final-step
confidence, the `score` node's confidence alone. The action and the target
both come from the rule *F*, so a fairer confidence-based baseline should
also pass through *F*.

## Baseline (fixed now)

**Model-implied action probability.** From the model's own mean
distributions, with *p*<sub>k</sub> the `score` probability of level *k*
and *q* the mean `noul` probability, treating the two nodes as
independent:
- P(escalate) = *p*<sub>2</sub>;
- P(defer) = *p*<sub>1</sub>·*q*;
- P(accept) = *p*<sub>0</sub> + *p*<sub>1</sub>·(1 − *q*).

The risk score is 1 − P(chosen action). Any other action (request
evidence) gets risk 0.5, and its count is reported.

## Analyses (fixed now)

**Models:** Jev 1.13, OpenJev-27B, Qwen2.5-7B, Phi-3.5-mini and
OLMo-2-7B. Each is evaluated on its own 500 held-out bugs. The target is
a wrong action (*a* ≠ *a*\*).

**Scores compared:**
- final-step confidence (low confidence ranks first);
- the action-rule score *r(a)*, as in `baseline_ablations.py`;
- the model-implied risk.

**Statistics:** AUROC, with tracker-stratified bootstrap 95% intervals
(B = 2000, seed 20261023, the same as `baseline_ablations.py`).

**Contrasts:**
- *r(a)* minus implied risk;
- implied risk minus final-step confidence.

**Within-action AUROC.** For every action with at least 10 failures and
10 non-failures, the AUROC of final-step confidence and of implied risk
for failure within that action. *r(a)* is constant within an action,
so its within-action AUROC is 0.5 by construction.

## Reading (fixed now)

**If *r(a)* still exceeds the implied risk,** with an interval excluding
0, for most models, the paper may say that decisions beat the model's
own probabilities passed through *F*.

**Otherwise,** the paper narrows the claim to "single-node confidence"
and reports the result.

**Either way, the result is reported as exploratory.**
