# Development plan: case-level review targeting (training data only)

**Status:** written 2026-10-17, before any score below has been computed
on any data. This is the *development* stage. The confirmatory test is a
separate pre-registration on a fresh batch of bugs, written after this
stage finishes.

## Question

The intervention test (`intervention_test_preregistration.md`) found that
no feasible review strategy beat "no review" at a 10% budget. The
descriptive oracle follow-up showed that, for Jev, the saving exists
(about 44% of cost) and sits almost entirely in **wrongly accepted**
cases. The action-level rule cannot find them, because every accepted
case gets the same rank.

**Can a per-case score, computed from Jev's own outputs, rank accepted
cases by how likely review is to save money, well enough to make review
pay at a 10% budget?**

## Data rules

- **Development uses only the 442 training bugs** (Mozilla 202, kernel
  240) and Jev's existing outputs on them.
- **The 500 held-out bugs are not used in development.** Their cost
  structure (the oracle) has already been seen, so they cannot serve as
  a confirmatory test. After the score is frozen they may be reported as
  a clearly labelled *previously seen* secondary check, never as
  evidence.
- No new API or GPU calls in this stage.

## Why only accepted cases (reasoned from the frozen cost table)

- Review turns the action into *escalate*, which costs 1 unit of human
  time, plus 1 if escalation was not the target.
- **Accept:** review saves 9 if the target was *escalate*, saves 6 if it
  was *defer*, and loses 2 if it was *accept*.
- **Defer** and **request evidence:** review never saves (a mismatch
  costs 1 either way, plus the human unit).

So any useful score must rank **accepted** cases, and the quantity to
rank by is the expected saving
`9·P(target = escalate) + 6·P(target = defer) − 2·P(target = accept)`.

## Candidate scores (fixed now; no others will be tried)

Defined on accepted cases. Non-accepted candidates always rank below
every accepted case.

| Id | Score | Fitted? |
|---|---|---|
| **P (plug-in)** | Expected saving, treating Jev's probabilities as calibrated: with `p2` = `score` mass on level 2, `p1` = mass on level 1 and `q` = `noul` P(regression), target ≈ escalate with prob `p2` and defer with prob `p1·q`. Score = `9·p2 + 6·p1·q − 2·(1 − p2 − p1·q)` | No (no parameters) |
| **L (small model)** | L2 logistic regression (λ = 1, standardized features, the same fitter as the frozen risk estimator) predicting *wrong accept* among accepted training cases. Features: `score_p0`, `score_p1`, `score_p2`, `score_conf`, `noul_p`, `noul_conf`, `choice_conf`, `score_unstable`. | Yes, on training accepts |

Comparators (the same as the intervention test):
- **A1:** the action-level cost-aware rule. Ties every accepted case.
- **B:** low `score` confidence.
- **C:** random (exact expectation).
- **No review.**
- **Oracle** (upper bound only).

## How development performance is measured

All on training data, and never on the held-out 500:

1. **Cross-tracker:** fit on Mozilla and evaluate on the kernel, then the
   reverse. P needs no fitting, so this only matters for L.
2. **Repeated 5-fold cross-validation**, stratified by tracker (20
   repeats), for L.
3. **Metrics** at a 10% budget (k = ⌈0.10·n⌉):
   - total cost against no review, A1 and B;
   - the share of the oracle saving captured;
   - AUROC for wrong accept among accepted cases (secondary).

## Selection rule (fixed now)

- **P is the default primary score.** It has no parameters, so it
  cannot overfit 442 bugs.
- **L replaces P only if** its out-of-fold cost at k is lower than P's in
  **both** cross-tracker directions **and** in the repeated 5-fold
  average.
- **The chosen score is then frozen as-is.** For L, that means refitting
  on all 442 training bugs, writing the coefficients to a JSON file and
  hash-locking it before any fresh data exists.
- **If neither score beats no review in development,** that is reported.
  The confirmatory study still runs if it is authorized, because the
  development estimate is noisy (about 45 reviews). A negative
  development result will be stated in the pre-registration.

## Outputs

- Code: `research/src/case_level_review_dev.py`.
- Results: `research/results/case_level_review_dev.json` and `.md`.
- If L is selected: a frozen file
  `research/results/frozen_case_review_score_v1.json`, plus its
  `.sha256`.
