# Exploratory cost-sensitivity analysis of the intervention test (plan)

**Status:** written 2026-10-17, before any grid cell other than the
frozen table has been computed.

**Label:** exploratory and post hoc. The pre-registered intervention
result (frozen cost table, `intervention_test_preregistration.md`)
remains the primary result and is not re-tested.

## Question

Does the pre-registered conclusion depend on the particular cost matrix?
The conclusion is that, at a 10% review budget, no feasible strategy
costs less than no review.

## Fixed (unchanged from the pre-registered test)

- The 500 held-out bugs and every model's existing outputs. No API or
  GPU calls are made.
- The budget: k = 50 reviews. A review turns the action into
  *escalate*.
- **Every ranking is frozen as computed under the original table:**
  - A1, the action-level expected saving;
  - A2, the action-level error rate;
  - E, the risk estimator;
  - B, low confidence;
  - B2, low confidence product;
  - C, random (exact expectation).

  Rankings are **not** re-derived for each cost cell. That isolates the
  question "does the same policy still lose under other economics?"
- Exact expectation over ties, as in the original analysis.

## Grid (fixed now)

Costs are parameterized as follows. Mismatches by non-accept actions
cost 1, as in the frozen table.
- **m**, the multiplier on wrong-accept costs (accept row 10 / 6 / 8):
  0.5, 1, 2 or 4.
- **h**, the human cost per escalation: 0.25, 0.5, 1 or 2.

That gives 16 cells. The frozen table is (m = 1, h = 1).

For reference, the break-even precision for reviewing an accepted case
whose target is *escalate* is (1 + h) / (10m + 1). Under the frozen
table it is 2/11 ≈ 18%.

## What is reported

For each model and cell:
- the no-review cost;
- each arm's cost;
- the best feasible arm's cost minus the no-review cost;
- A1 − C and A1 − B;
- the oracle cost.

These are point estimates only. No tests are run, so there is no
multiplicity to manage, and no cell is selected as "the" result.

## Reading rule (fixed now)

- **Near cells:** the 9 cells with m ∈ {0.5, 1, 2} and h ∈ {0.5, 1, 2},
  that is, within a factor of 2 of the frozen values on both axes.
- **Far cells:** the 7 cells with m = 4 or h = 0.25.
- **Cost-robust.** The negative conclusion is called cost-robust for a
  model if no feasible arm costs less than no review in any near cell.
- **Cost-dependent.** If some near cell reverses it, the conclusion is
  called cost-dependent for that model. The reversing cells are reported
  with the break-even precision that explains them.
- **Far cells are descriptive only.**
- **Ordering.** Whether the ordering A1 < C and A1 < B changes across
  the grid is reported as counts of cells.

## Outputs

- Code: `research/src/intervention_cost_sensitivity.py`.
- Results: `research/results/intervention_cost_sensitivity.json` and
  `.md`.
