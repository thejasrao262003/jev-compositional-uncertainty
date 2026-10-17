# Pre-registration: does action-level history improve review decisions at a fixed budget?

**Status:** specified 2026-10-17, before any intervention outcome has been
computed.

**Disclosure.** The model outputs this analysis uses already exist: the
held-out runs of Jev, OpenJev, Qwen, Phi and OLMo. Their *ranking*
results (AUROC) have been seen. **No cost or intervention outcome has
been computed for any strategy below.** This is an analysis-blind
specification on existing data, not a new data collection, and it must
be read that way.

## Setting

**Units.** The 500 held-out bugs per model; the same bugs for every
model.

**Base workflow.** S1: action = `F(model's decisions)`.

**Review = escalation to a human.** A reviewed case's action becomes
*escalate*.

**Cost.** The frozen cost table (protocol §16.1) plus 1 unit of human
cost per escalation (`workflow_strategies_r12.cost`).

**Candidates.** Bugs whose base action is not already *escalate*.

**Budget.** `k = ⌈0.10·n⌉ = 50` reviews per model.

**Outcome.** Total cost over the 500 bugs. Lower is better.

## Why the primary strategy is cost-aware (reasoned before any outcome)

Under the frozen table:
- reviewing a wrongly **accepted** case saves 6–10 at a review cost of 2;
- reviewing a **deferred** case never saves anything. A wrong defer costs
  1, and escalating it costs 1 + 1.

Ranking by raw historical error rate would therefore spend the budget on
defers, the most error-prone action, and could lose to random selection.
So the primary strategy ranks by *expected net saving*, not error rate.
The raw error-rate rule is kept as a secondary arm.

## Strategies (all rankings from TRAINING data or the case itself; never from held-out outcomes)

| Arm | Ranks candidates by | Role |
|---|---|---|
| **A1** | Action-level expected net saving from review: the training-set mean of `cost(action, a*) − cost(escalate, a*)` for that action | **Primary** |
| A2 | Action-level historical error rate (training) | Secondary |
| E | `E_dec` risk (logistic on decisions, trained on the model's training split; for Jev, the frozen estimator) | Secondary |
| **B** | Low final-step (`score`) confidence | **Primary comparator** |
| B2 | Low confidence product | Secondary |
| **C** | Random selection | **Primary comparator** |

**Ties.** When rank ties straddle the budget boundary, the **exact
expected** cost over a uniformly random choice within the tied group is
used. No seed-dependent tie-breaking. C is computed as an exact
expectation.

**Sparse actions.** Training estimates use additive smoothing toward the
overall training mean (one pseudo-count). An action never seen in
training gets that mean.

## Hypotheses and tests

Per model *M* (5 models):

- **I1:** A1 has lower total cost than C (random).
- **I2:** A1 has lower total cost than B (confidence).

**Test.** The paired difference in total cost (A1 − comparator) per
bug. 95% percentile bootstrap over bugs (B = 2,000, stratified by
tracker, fixed seed). Training-derived rankings stay fixed and are not
re-estimated. The bootstrap p-value is one-sided (A1 is better).

**Multiplicity.** Holm across 5 models × 2 = 10 tests, family-wise
α = 0.05.

**Reporting.**
- Every arm's total cost, per model and per tracker.
- The number of wrongly accepted cases each arm catches.
- Results reported **whatever their direction**. If A1 does not beat C,
  the predictive signal does not translate into lower cost at this
  budget, and that is the finding.

**Not tested.**
- Other budgets.
- Reviewer error: reviews are assumed correct, which is the cost
  table's assumption.
- Latency.

## Artifact

`research/src/intervention_test.py`. Results in
`research/results/intervention_test.json` and `intervention_test.md`.
