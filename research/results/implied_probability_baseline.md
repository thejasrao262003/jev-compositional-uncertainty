# Model-implied action probability baseline (exploratory, post hoc)

**Plan:** `research/methodology/implied_probability_baseline_plan.md`,
committed `cfb686d` before computing.
**Code:** `research/src/implied_probability_baseline.py`.
**Numbers:** `implied_probability_baseline.json`.

**What it tests.** A fairer confidence baseline that passes through the
action rule: 1 − P(chosen action), using the model's own `score`
distribution and `noul` probability. The data are the 500 held-out bugs,
and the target is a wrong action.

| Model | Action rule | Implied risk | Final-step conf. | Rule − implied [95% CI] | Implied − conf. [95% CI] |
|---|---|---|---|---|---|
| Jev 1.13 | 0.762 | 0.535 | 0.549 | +0.228 [+0.158, +0.297] | −0.014 [−0.060, +0.033] |
| OpenJev-27B | 0.746 | 0.535 | 0.575 | +0.211 [+0.143, +0.283] | −0.040 [−0.090, +0.008] |
| Qwen2.5-7B | 0.701 | 0.466 | 0.473 | +0.235 [+0.145, +0.331] | −0.008 [−0.022, +0.005] |
| Phi-3.5-mini | 0.688 | 0.396 | 0.401 | +0.293 [+0.203, +0.387] | −0.005 [−0.015, +0.005] |
| OLMo-2-7B | 0.580 | 0.556 | 0.551 | +0.024 [−0.073, +0.123] | +0.005 [−0.001, +0.012] |

**Reading, by the plan's fixed rule.** The action rule exceeds the
implied risk, with intervals excluding 0, for 4 of 5 models (not
OLMo-2). The paper may therefore say that the decisions beat the model's
own probabilities passed through *F*. The implied risk adds nothing over
final-step confidence.

**Within-action (secondary).** Within accepted cases, the implied risk
ranks wrong accepts above chance, where final-step confidence did not:
- Jev: 0.596 [0.508, 0.682], against 0.487 [0.374, 0.605] for
  confidence (38 failures out of 245);
- OpenJev: 0.681 [0.589, 0.773], against 0.540 [0.407, 0.671] (29 out
  of 198).

This is a weak, post hoc signal from many comparisons. It points to
where a within-action selector could come from. It does not show that
review would pay.
