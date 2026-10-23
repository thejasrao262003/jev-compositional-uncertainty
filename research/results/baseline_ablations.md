# Baseline ablations, target robustness and prior-shift re-weighting

**Plan:** `research/methodology/evidence_audit_and_baselines_plan.md`.
- Sections E and F were committed `39f944d`, before running.
- Addendum H was committed `a9d6186`, after E and F but before H.

**Code:** `research/src/baseline_ablations.py` and
`research/src/prior_shift_reweighting.py`.

**Numbers:** `baseline_ablations.json` and `prior_shift_reweighting.json`.

**Status:** exploratory. The held-out bugs have been analysed before. No
API or GPU calls were made.

**Self-check:** on the pre-registered target, `E_dec` and final-step
confidence reproduce the paper exactly for all 5 models:

| | Jev | OpenJev | Qwen | Phi | OLMo |
|---|---|---|---|---|---|
| `E_dec` / confidence | 0.763 / 0.549 | 0.748 / 0.575 | 0.736 / 0.473 | 0.677 / 0.401 | 0.637 / 0.551 |

## E. What does the estimator add? (target: wrong workflow action)

Paired AUROC differences, with 95% CIs from a paired, tracker-stratified
bootstrap (B = 2,000). **Bold** marks a CI that excludes 0.

| Model | `E_dec` − action-rule | `E_all` − `E_dec` (adding confidence) | `E_dec` − final-step conf. | `E_unc` − final-step conf. |
|---|---|---|---|---|
| Jev | 0.000 [−0.012, +0.011] | +0.006 [−0.016, +0.030] | **+0.214** [+0.147, +0.286] | **+0.159** [+0.097, +0.225] |
| OpenJev | +0.002 [−0.007, +0.011] | +0.004 [−0.019, +0.025] | **+0.173** [+0.110, +0.238] | **+0.076** [+0.025, +0.128] |
| Qwen2.5 | **+0.035** [+0.003, +0.069] | +0.012 [−0.009, +0.032] | **+0.262** [+0.176, +0.356] | **+0.262** [+0.179, +0.353] |
| Phi-3.5 | −0.012 [−0.039, +0.019] | **+0.055** [+0.009, +0.101] | **+0.276** [+0.179, +0.379] | **+0.332** [+0.241, +0.428] |
| OLMo-2 | **+0.057** [+0.010, +0.103] | **+0.078** [+0.030, +0.124] | +0.086 [−0.011, +0.181] | **+0.069** [+0.020, +0.119] |

The action-only logistic model equals the action-rule in every case,
because both are monotone in the action.

**Reading, by the pre-stated rule:**
1. **For the Jev-style models, the estimator adds nothing beyond the
   action.** The difference is 0.000 and +0.002, with tight CIs. For Qwen
   and OLMo it adds a little (+0.035 and +0.057). For Phi there is no
   detectable gain.
2. **Confidence adds nothing beyond the decisions for Jev, OpenJev and
   Qwen.** It adds a little for Phi and OLMo (+0.055 and +0.078).
3. **A confidence-only estimator beats raw final-step confidence for
   every model** (+0.07 to +0.33). So the uncertainty fields carry
   information that the final-step confidence alone does not.
4. **Chance.** 20 intervals were computed and 13 exclude 0. These are
   consistent effects, not isolated chance exclusions.

## F. Targets that do not pass through the constructed rule `F`

The two alternative targets are "severity wrong" (`score` ≠ reference
level) and "any node wrong". Estimators are refitted on development bugs
for each target. Held-out AUROC (unweighted fit):

| Model | Severity wrong: `E_dec` / action-rule / conf. | Any node wrong: `E_dec` / action-rule / conf. |
|---|---|---|
| Jev | **0.282** / 0.303 / 0.613 | 0.559 / 0.414 / 0.560 |
| OpenJev | **0.277** / 0.233 / 0.627 | 0.619 / 0.712 / 0.564 |
| Qwen2.5 | 0.620 / 0.707 / 0.460 | 0.755 / 0.743 / 0.401 |
| Phi-3.5 | **0.307** / 0.320 / 0.415 | 0.668 / 0.725 / 0.289 |
| OLMo-2 | 0.498 / 0.437 / 0.570 | 0.425 / 0.415 / 0.488 |

**Several decision-based estimators rank held-out severity errors far
below chance.** Taken at face value, "decisions beat confidence" fails
on targets that do not go through `F`.

**Diagnosis.** A direct tabulation shows P(severity wrong | `score`
decision) inverts between the two samples:

| | Development (quota mix) | Held-out (natural mix) |
|---|---|---|
| Jev, level-1 answers | 60% wrong | 20% wrong |
| Jev, level-0 and level-2 answers | | 82% and 73% wrong |
| Label mix | many serious and minor bugs | 390 of 500 bugs are level 1 |

A decision's error rate depends on the label prior. Development and
held-out priors differ by design.

## H. Re-weighting development bugs to the natural label mix (addendum H)

**Weights** match each tracker's natural (group × level) label mix. They
use the held-out manifests' label counts (no held-out model output),
which is optimistic, because a deployer must estimate the mix. Held-out
AUROC, decision-only estimator:

| Model | Severity wrong: unweighted → weighted [95% CI] (conf.) | Any node wrong: unweighted → weighted [95% CI] (conf.) | Wrong action: unweighted → weighted (conf.) |
|---|---|---|---|
| Jev | 0.282 → **0.793** (0.613) | 0.559 → **0.758** (0.560) | 0.763 → 0.770 (0.549) |
| OpenJev | 0.277 → **0.794** (0.627) | 0.619 → **0.805** (0.564) | 0.748 → 0.757 (0.575) |
| Qwen2.5 | 0.620 → **0.740** (0.460) | 0.755 → 0.731 (0.401) | 0.736 → 0.731 (0.473) |
| Phi-3.5 | 0.307 → **0.673** (0.415) | 0.668 → **0.772** (0.289) | 0.677 → 0.698 (0.401) |
| OLMo-2 | 0.498 → **0.621** (0.570) | 0.425 → 0.425 (0.488) | 0.637 → 0.637 (0.551) |

Bootstrap CIs for each cell are in `prior_shift_reweighting.json`.

**Reading, by the pre-stated rule:**
1. **Re-weighting restores above-chance ranking** on severity-wrong for
   every model, and on any-node-wrong for every model except OLMo-2. The
   inversion is attributed to label-prior shift.
2. **Under the deployment label mix, decisions beat final-step confidence
   on all three targets for 4 of 5 models.** The exception is OLMo-2 on
   any-node-wrong. So the finding does not depend on the constructed
   target. What it does depend on is estimating decision-conditioned
   error rates under the deployment label distribution.
3. **The pre-registered result was not affected by this.** On the
   wrong-action target, re-weighting changes AUROC by at most ±0.02.

## What this changes in the paper

- **The estimator adds nothing beyond "historical error rate of the
  chosen action"** for the Jev-style models, and little elsewhere. The
  paper already said "mostly". It now gives the paired CIs and says
  "nothing detectable" for Jev and OpenJev.
- **New finding:** decision-conditioned error estimators are not
  portable across label distributions. Fitted on a quota-sampled
  development set, they can be anti-predictive on a natural-mix
  deployment set. Re-weighting to the deployment mix repairs them.
- **Target robustness:** with matched label mix, the decisions-beat-
  confidence result extends to two targets independent of `F`, with one
  exception (OLMo-2, any node).
