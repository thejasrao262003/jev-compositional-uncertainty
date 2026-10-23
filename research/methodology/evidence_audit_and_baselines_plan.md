# Evidence audit and baseline ablations (plan)

**Status:** written 2026-10-23, before any analysis below has been run.

**Label:** an audit plus exploratory analyses of existing data.
- No API or GPU calls are made.
- No pre-registered result is re-tested or replaced.
- The 500 held-out bugs have already been analysed several times, so
  every held-out number below is descriptive, not confirmatory.

**Motivation.** An external review asked whether the main result is more
than action-frequency prediction, whether it depends on the constructed
target, and whether every reported number reproduces from a clean
environment.

## A. Clean-environment reproduction

1. Export HEAD with `git archive` into an empty directory. It then holds
   no untracked files and no `.env`.
2. Regenerate every figure and table input (`make_figure_data.py`) and
   compare each output byte-for-byte with the committed files.
3. Run the number checks (`check_paper_numbers.py`, plain and `--acl`).

**Pass:** all outputs are identical and every number traces.

## B. Independent recomputation of the headline tests

Recompute HR1 and HR2, and the cross-model X1 and X2 AUROCs, with an
independent implementation:
- `sklearn.metrics.roc_auc_score` on scores rebuilt from the raw
  response files;
- the frozen estimator JSON, which is hash-checked before use.

**Pass:** every AUROC agrees with the paper to three decimals.

## C. Split integrity beyond text overlap

Already reported: no shared bug IDs, no exact text duplicates and no
near-duplicates.

Added here:
1. **Linked reports.** Fetch `dupe_of`, `duplicates`, `see_also`,
   `blocks`, `depends_on` and `regressed_by`/`regressions`, where
   available, from the public Bugzilla REST APIs. These are read-only
   tracker requests, not model calls.
2. **Count every held-out bug linked to a development bug.** The count
   and the bugs are reported.
3. **Re-run the HR1 contrast without those bugs** (descriptive).

## D. Contamination proxy (descriptive)

Report `E_dec` and final-step-confidence AUROC separately for held-out
bugs filed in the last 12 months and for older bugs, for each tracker
and model. Recent bugs are less likely to be in training data. Subsets
under 30 bugs are reported but not interpreted.

## E. Baseline ablations (the main analysis)

**Setup:**
- For each of the 5 models.
- Training: the model's own outputs on the 442 development bugs.
- Evaluation: the 500 held-out bugs.
- Target: wrong workflow action (`a ≠ a*`).

**Scores:**
1. **Constant** (AUROC 0.5 by construction; a reference only).
2. **Final-step confidence** (low = risky).
3. **Action-rule:** the historical error rate of the chosen action, from
   training counts with one pseudo-count, as in the intervention test.
4. **Action-only logistic:** one-hot workflow action only.
5. **`E_dec`:** the decision features, as pre-registered. For Jev this is
   the frozen estimator.
6. **`E_unc`:** the uncertainty features only (confidence-only
   estimator).
7. **`E_all`:** decision plus uncertainty features.

All logistic models use the project fitter (L2, λ = 1, standardized
features).

**Metrics:**
- AUROC with a 95% stratified bootstrap CI (B = 2,000);
- AUPRC;
- for scores that are probabilities (3–7): Brier score and ECE
  (10 equal-width bins).

**Paired contrasts** use a paired, tracker-stratified bootstrap of the
AUROC difference, 95% CI, on the same resampled bugs:
- `E_dec − action-rule` (does the estimator add anything beyond the
  action?);
- `E_all − E_dec` (does confidence add anything beyond the decisions?);
- `E_dec − final-step confidence`;
- `E_unc − final-step confidence`.

**Reading rule (fixed now):**
- A component "adds" ranking information only if the paired 95% CI of
  its contrast excludes 0.
- Otherwise the result is reported as no detectable gain, not as
  evidence of no gain.
- With 4 contrasts × 5 models = 20 intervals, about one could exclude 0
  by chance, so isolated exclusions are reported as such.

## F. Target robustness (constructed-target concern)

The target `a*` is a function `F` of the labels. Two alternative targets
do not pass through `F`:
1. **Severity wrong:** `score` decision ≠ reference level.
2. **Any node wrong:** any of `choice`, `noul` or `score` disagrees with
   its reference label.

For each target, refit the estimators on the development bugs and
compare these on the held-out bugs, with the same metrics and paired
contrasts as in E:
- the decision-only estimator;
- the action-rule recomputed for that target;
- final-step confidence;
- the confidence-only estimator;
- the combined estimator.

**Reading:** if decisions still beat confidence on targets that do not
pass through `F`, the finding is not an artifact of the constructed
target. If they do not, the paper's claim is narrowed to the constructed
target.

## G. Reference audit

Every bibliography entry not yet checked against its source is checked
now. The results go in `CITATION_VERIFICATION.md`.

## Outputs

- Code: `research/src/evidence_audit.py` and
  `research/src/baseline_ablations.py`.
- Results: `research/results/evidence_audit.{json,md}` and
  `research/results/baseline_ablations.{json,md}`.

## Addendum H (2026-10-23)

**Status:** written after sections E and F were computed, before H is
computed.

**Observation from F.** On the severity-wrong target, estimators fitted
on development bugs rank held-out errors *below* chance. A direct
tabulation explains why: P(severity wrong | `score` decision) inverts
between the quota-sampled development mix and the natural held-out mix.
For Jev, a level-1 answer is 60% wrong in development and 20% wrong
held out.

**Question.** Is the inversion a label-prior shift that re-weighting can
repair?

**Analysis:**
- Refit the action-rule and decision-only estimators on development bugs
  re-weighted to each tracker's natural (group × level) label mix.
- The mix comes from the held-out manifests' label counts, the same
  weights as the power simulation. No held-out model output is used.
- The weighted rule uses weighted error rates by action. The weighted
  estimator uses scikit-learn `LogisticRegression(C=1.0)` with
  standardized features and `sample_weight`.
- Evaluate on the held-out bugs for all three targets, for all 5 models,
  with the same AUROC and bootstrap CIs.

**Reading (fixed now):**
- If re-weighting restores above-chance ranking on severity-wrong, the
  inversion is attributed to prior shift.
- The paper then states that decision-conditioned error rates must be
  estimated under the deployment label mix.
- Either way the result is exploratory.
