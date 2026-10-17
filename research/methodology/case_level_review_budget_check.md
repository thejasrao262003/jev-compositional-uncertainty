# Budget check: one bounded training-only design check, with a stop rule

**Status:** written 2026-10-17, before any budget other than 10% has been
evaluated. This follows the power-planning result in
`research/results/case_level_review_dev.md`: at a 10% budget, the frozen
score P is projected to cost more than no review under the natural mix.

## What is fixed, and may not change

- **The score:** P, frozen in `frozen_case_review_score_v1.json`
  (sha256 `82d93045…`). No new features, no refit, no threshold.
- **The cost table:** the frozen table plus 1 unit of human cost per
  escalation.
- **The population:** each tracker's **natural** label mix, from the
  held-out manifests' label counts. There is no enrichment with serious
  bugs.
- **The data:** the 442 training bugs only. The held-out 500 bugs' Jev
  outputs are not loaded.
- **The only thing varied:** the review budget.

## Budget grid (fixed now)

Review budgets of **1%, 2%, 3%, 5%, 7.5% and 10%** of bugs, with
k = ⌈budget·n⌉. A smaller budget concentrates reviews on the cases P is
most confident are wrong accepts. That is the only route to the
18%-precision break-even.

## Simulation: uncertainty included

Each simulated study runs these steps:

1. **Population uncertainty.** Resample the training bugs with
   replacement within each tracker. This propagates uncertainty in the
   error distribution and in P's ranking performance.
2. **Natural-mix draw.** From that resampled set, draw n/2 bugs per
   tracker with importance weights toward the natural mix.
3. **Test.** Run the planned test: a paired, tracker-stratified bootstrap
   of `cost(P) − cost(no review)` with B = 300, one-sided α = 0.05.

The simulation uses 400 studies per (budget, n), for fresh sample sizes
n ∈ {500, 750, 1,000}. The largest is about 9,000 Jev calls, which is
the resource cap.

## Viability criterion and selection (fixed now)

A budget is **viable** if, at some n ≤ 1,000:
- the simulated **power** to show `cost(P) < cost(no review)` is
  **≥ 0.80**; and
- the **median** projected saving is negative (review pays), with the
  80% central interval of projected savings across simulations reported.

**Selection:**
- If more than one budget is viable, choose the one that reaches power
  0.80 at the **smallest n**. Ties go to the **larger** budget, because
  it is more useful in practice.
- n is then the smallest grid size at which that budget reaches 0.80.

## Stop rule (binding)

**If no budget on the grid is viable, stop.** No further designs are
searched, no Jev calls are made, and the paper reports the training
result, the 10% power analysis and this check (Option 1).

**If a budget is viable,** it selects a *candidate* design only. The
training analysis cannot show the intervention works. A separate
pre-registration then freezes the following:
- the budget and n;
- the selection rule;
- the comparators: no review (primary), A1 and B (secondary);
- the estimand and tests;
- the exclusions and stopping rules;
- Jev as primary, and OpenJev and the open models as pre-specified
  replications.

That pre-registration must be committed before any fresh bug is built or
any API call is made.

## Outputs

- Code: `research/src/case_level_review_budget_check.py`.
- Results: `research/results/case_level_review_budget_check.json` and
  `.md`.
