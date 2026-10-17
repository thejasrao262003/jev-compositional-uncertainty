# Workflow-risk probe: can Jev's outputs predict when the workflow will be wrong?

**Status: EXPLORATORY and post-hoc** (2026-10-17).
- It uses data the paper already reports, is not part of the paper, and
  sets no constant for any pre-registered study.
- No API calls.
- Every modeling choice was fixed before the first run and not tuned:
  - L2 logistic regression, λ = 1;
  - 5-fold CV × 20 repeats;
  - fixed feature sets;
  - fixed baselines.

**Code:**
- `research/src/workflow_risk_probe.py`, plain Python;
- `research/src/workflow_risk_probe_sklearn_check.py`, an independent
  scikit-learn re-implementation that agrees within 0.015 AUROC;
- `research/src/workflow_risk_probe_followup.py`, the coefficients and
  the population re-weighting.

**Numbers:** `workflow_risk_probe*.json`.

**Target.** The decision-based workflow action (`F` on the node decisions)
is wrong, i.e. differs from `a*`. The failure rate is 35% on Mozilla and
46% on the kernel.

**Inputs.** Only what one Jev run returns per bug: the three decisions
and confidences, the `score` distribution, `noul`'s probability, and
spread or stability across the 3 repeats. No labels or text features.

## Results

AUROC for ranking wrong actions first:

| Risk estimator | Mozilla (CV) | Kernel (CV) | Mozilla→Kernel | Kernel→Mozilla |
|---|---:|---:|---:|---:|
| Low final-step (`score`) confidence | 0.59 [0.50, 0.67] | 0.53 [0.46, 0.61] | — | — |
| Low minimum confidence | 0.53 | 0.46 | — | — |
| Low confidence product | 0.54 | 0.47 | — | — |
| Learned, **decisions only** | 0.67 | 0.80 | 0.81 [0.76, 0.87] | 0.69 [0.61, 0.76] |
| Learned, uncertainty signals only | 0.66 | 0.79 | 0.76 | 0.66 |
| Learned, decisions + uncertainty | 0.69 | 0.81 | 0.80 | 0.69 |

**Re-weighted to each tracker's real bug mix** (from the feasibility
counts; this guards against the balanced 40-per-cell design):

| Shift | Decisions only | Decisions + uncertainty | Best confidence baseline |
|---|---:|---:|---:|
| Mozilla→Kernel | **0.76** | 0.69 | 0.53 |
| Kernel→Mozilla | **0.83** | 0.76 | 0.58 |

**Failure rate among the 80% judged safest:**

| | Overall failure rate | Learned model | Confidence baselines |
|---|---:|---:|---:|
| Mozilla | 35% | 27% | 32–35% |
| Kernel | 46% | 36% | 45–47% |

## Reading

1. **Workflow failure is predictable from one Jev run, but not from its
   confidence.** Confidence aggregates sit at chance (0.46–0.59).
2. **Most of the signal is in the decisions.** A model that sees only
   what Jev decided reaches 0.67–0.83, including across trackers and
   under realistic label mixes. It mostly learns *which decision patterns
   are error-prone*. The largest weight on both trackers is on the
   workflow choosing **defer** (a regression plus a middle severity),
   which combines `noul`'s false alarms with `score`'s pull toward the
   middle. Those are the systematic biases documented in the paper.
3. **Uncertainty signals add little and transfer worse.** Within a
   tracker they add about 0.01–0.02. Under shift (cross-tracker,
   population-weighted) adding them *lowers* AUROC by 0.07. The
   decisions-only model is the more robust estimator.

## What this does and does not support (for the "when should an agent ask for help" idea)

**Supports, as a hypothesis for a new pre-registered study:** a risk
estimator that knows a model's *systematic decision biases* can predict
workflow failure where confidence composition cannot, and the knowledge
transfers between two trackers that share the model.

**Does not establish:**
- **Generality.** One model version, one workflow, one domain. The two
  trackers share Jev, the prompts and the sampling design.
- **Robustness when the bias changes.** A new Jev version or other
  prompts could move the error-prone patterns. That is H3 in the
  proposal, and it needs its own test.
- **Interventions.** Nothing here tests whether verify/retry/escalate
  actions chosen by this estimator reduce cost. That is H2.
- **Freedom from selection.** Post-hoc and computed on reported data.
  Small n: 202 and 240 bugs; most intervals are ±0.05–0.08.

**Next step if pursued:**
1. Pre-register the decisions-only estimator, trained on Mozilla + kernel
   as they stand.
2. Test it, frozen, on new data: a third tracker, a later Jev version,
   or perturbed prompts.
3. Add perturbation signals (order or paraphrase sensitivity), the one
   uncertainty family not yet tested.
4. Evaluate interventions at matched budgets.
