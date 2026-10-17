# Budget check: result and stopping decision

**Specification:** `research/methodology/case_level_review_budget_check.md`
(committed `6b6d470` before any budget other than 10% was evaluated).

**Code:** `research/src/case_level_review_budget_check.py`.

**Numbers:** `case_level_review_budget_check.json`.

**Setting:**
- the frozen score P;
- the frozen cost table;
- each tracker's natural label mix;
- 442 training bugs, with population resampling in each simulated study;
- 400 simulated studies per cell, each with a paired, tracker-stratified
  bootstrap (B = 300) and a one-sided α of 0.05.

No API or GPU calls were made. The held-out Jev outputs were not loaded.

## Full grid

The cost change is cost(P) − cost(no review). Negative means review pays.

| Fresh bugs | Budget | Reviews k | Power | Median cost change | 80% range | Share of simulations where review pays |
|---|---|---:|---:|---:|---|---:|
| 500 | 1% | 5 | 0.13 | -1 | [-23, +10] | 0.59 |
| 500 | 2% | 10 | 0.07 | -2 | [-24, +20] | 0.52 |
| 500 | 3% | 15 | 0.05 | +8 | [-25, +30] | 0.40 |
| 500 | 5% | 25 | 0.03 | +17 | [-16, +42] | 0.23 |
| 500 | 7.5% | 38 | 0.03 | +24 | [-23, +65] | 0.28 |
| 500 | 10% | 50 | 0.01 | +26 | [-32, +78] | 0.26 |
| 750 | 1% | 8 | 0.12 | -6 | [-39, +16] | 0.55 |
| 750 | 2% | 15 | 0.10 | +8 | [-36, +30] | 0.49 |
| 750 | 3% | 23 | 0.03 | +13 | [-31, +46] | 0.30 |
| 750 | 5% | 38 | 0.04 | +32 | [-23, +65] | 0.27 |
| 750 | 7.5% | 57 | 0.02 | +43 | [-29, +92] | 0.21 |
| 750 | 10% | 75 | 0.01 | +43 | [-26, +106] | 0.23 |
| 1000 | 1% | 10 | 0.20 | -2 | [-46, +20] | 0.56 |
| 1000 | 2% | 20 | 0.14 | +7 | [-59, +40] | 0.49 |
| 1000 | 3% | 30 | 0.08 | +16 | [-50, +60] | 0.35 |
| 1000 | 5% | 50 | 0.03 | +38 | [-32, +100] | 0.20 |
| 1000 | 7.5% | 75 | 0.03 | +57 | [-39, +120] | 0.22 |
| 1000 | 10% | 100 | 0.04 | +52 | [-52, +145] | 0.26 |

## Decision (mechanical application of the pre-stated rule)

**No budget is viable.**
- **Power:** viability required ≥ 0.80 at ≤ 1,000 fresh bugs. The
  highest power anywhere on the grid is 0.20, at a 1% budget with 1,000
  bugs. Its median change there is −2, with an 80% range of −46 to +20.
- **Median cost change:** at every budget of 2% or more, the median is
  positive, so review is projected to cost more than no review.

**By the binding stop rule:**
- the confirmatory study is **not run**;
- **no** fresh bugs are built and **no** Jev or GPU calls are made;
- **no** further designs are searched. That includes smaller budgets, a
  different cost table, a modified score and an enriched population.

## What this does and does not show

- **It is a feasibility assessment on training data, not confirmatory
  evidence.** It does not show that review cannot reduce cost.
- **Value exists.** The oracle analysis shows a good selector would save
  33–44% for the Jev-style models.
- **The signal cannot isolate the cases.** The available signals cannot
  identify wrong accepts precisely enough under the natural mix to pay
  for the reviews (break-even precision is about 18%).
- **Paper claim:** the training-derived review-ranking approach did not
  meet the pre-registered power and economic-viability criteria under the
  natural bug mix at the tested sample sizes.
