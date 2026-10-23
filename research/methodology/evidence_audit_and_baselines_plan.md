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

## Addendum I (2026-10-23)

**Status:** written before I is computed. This addendum answers an
external review point: the re-weighting in H uses the held-out label
counts, so it is not deployment-feasible.

**Question.** Can the label-mix correction be done without any test
labels?

**Method: black-box shift estimation (BBSE; Lipton et al., 2018).** Per
model and tracker, the label is the reference severity level (3 classes)
and the predictor is the model's `score` decision.
- **Confusion matrix:** C[i, j] = P_dev(ŷ = i, y = j), estimated on the
  development bugs. These have labels.
- **Target prediction mix:** μ = P_held(ŷ = i), the share of held-out
  bugs given each `score` answer. This uses held-out *predictions* only,
  never held-out labels.
- **Weights:** solve C w = μ, clip w at 0, and normalise so the
  development bugs keep their total weight. If C is singular or a
  weight goes negative before clipping, that is reported.
- **Unstable answers:** bugs with a repeat-unstable `score` answer
  (ŷ = None) are excluded from C and μ, on the assumption that the
  instability is unrelated to the label.
- **Applying the weights:** the development bugs are re-weighted by
  w[level]. The group dimension is not corrected; that is disclosed.

**Comparison** on the held-out bugs, all three targets, all 5 models:

| | Weighting | Uses test labels? |
|---|---|---|
| (i) | Unweighted development fit | No |
| (ii) | Oracle weights (section H) | Label counts |
| (iii) | BBSE weights | No |

Also reported: the estimated vs true held-out level mix.

**Reading (fixed now):**
- BBSE "recovers" the correction for a model and target if its AUROC is
  at least halfway from (i) to (ii).
- Exploratory either way.

## Addendum J (2026-10-23): second external audit

**Status:** written before any item below is computed. Everything here
is exploratory on previously analysed data, and no API calls are made.
None of it replaces a pre-registered result.

### J1. Independent re-implementation of the primary result

A new script imports no project analysis code. It works directly from
the raw response files, the dataset files and the frozen estimator JSON.
It re-implements:
- modal reduction (tie tolerance 0.02);
- the `noul` threshold;
- the action rule F;
- the targets;
- the frozen estimator's features from its stored feature names.

It then recomputes:
- HR1 (AUROC of `E_dec` and of final-step confidence, and their paired
  difference with a one-sided 95% lower bound, using a tracker-stratified
  bootstrap with B = 2,000);
- HR2.

**Pass:** every number matches the paper to three decimals, or the
discrepancy is reported and traced.

### J2. Per-tracker headline contrast

The `E_dec` − final-step-confidence paired difference with its 95% CI,
computed within Mozilla and within the kernel separately.

### J3. Grouped split refit

- **Groups:** connected components of the tracker-link graph (C), over
  development and held-out bugs.
- **Refit:** remove every development bug in a component that contains
  a held-out bug, refit `E_dec` (project fitter) on the remaining
  development bugs, and evaluate on held-out bugs outside those
  components.
- **Reported for:** all five models.

### J4. Alternative label mappings (target sensitivity)

Each mapping recomputes the target. The action-rule score and `E_dec`
are refit on development bugs under the same mapping, then compared with
final-step confidence on the held-out bugs:
- **(m1)** Mozilla S2 mapped to level 1 instead of 2 (S1 → 2; S2, S3 →
  1; S4 → 0);
- **(m2)** kernel bugs whose severity is the default "normal" excluded
  from both sets;
- **(m3)** kernel bugs with `cf_regression` unset ("---") excluded from
  both sets.

**Reading:** if decisions beat confidence under every mapping (paired
95% CI above 0), the result is not fragile to these choices. Otherwise,
the mappings where it fails are reported.

### J5. Within-action identification of costly errors

Among held-out *accepted* cases, compute the AUROC for "wrongly
accepted" (target escalate or defer) of:
- `E_dec`;
- the action rule (constant within an action, so 0.5);
- final-step confidence;
- `score` P(level 2).

This is for all five models. It tests directly whether any score
separates the expensive errors within an action.

### J6. BBSE under synthetic, known label shift

- **Setup:** for Jev and OpenJev, resample the held-out bugs (with
  replacement, 500 per draw) to target severity mixes on a grid: level-2
  share 5% / 10% / 20% / 35% / 50%, with the rest split 1 : 0.3 between
  levels 1 and 0.
- **Estimate:** apply BBSE with the development confusion matrix, 200
  draws per mix.
- **Report:** the estimation error of the level-2 share (bias and RMSE)
  and the share of draws with cond(C) ≤ 100.
- **Repeat** with the confusion matrix degraded toward uninformative by
  mixing it with a uniform matrix (λ = 0 / 0.25 / 0.5 / 0.75).

### J7. Reviewer accuracy

Re-score the frozen intervention rankings with reviewer accuracy
ρ ∈ {1.0, 0.9, 0.8}:
- a reviewed case reaches the correct target action with probability ρ;
- otherwise it keeps the workflow's action;
- human cost is charged either way;
- expected cost is computed exactly.

This is at the frozen cost table and at the m = 2 cell, for all five
models.
