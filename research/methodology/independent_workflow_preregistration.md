# Pre-registration: independent-workflow replication (Kubernetes issue triage)

**Status:** DRAFT for review, written 2026-10-23.
- No issue has been fetched for this study.
- No model call has been made.
- No outcome exists.

**Execution needs, in this order:**
1. review of this protocol;
2. explicit authorization of the dataset build (GitHub only);
3. separate explicit authorization of the Jev calls;
4. separate authorization of any GPU replication runs.

Feasibility counts below come from GitHub search totals (label counts
only). They were used to size the study, not to select issues.

## 1. Question

Does the chosen action's historical error rate rank workflow failures
better than final-step confidence in an independent software workflow?
And how does its usefulness change under label shift between development
and deployment?

**Scope.** This tests the paper's RQ1 and RQ2 in a new setting. A
negative result is a valid outcome and will be reported as the
replication result.

## 2. What is independent, and what is not

| | Original study | This study |
|---|---|---|
| Tracker and platform | Bugzilla (Mozilla, kernel) | GitHub (kubernetes/kubernetes) |
| Who labels | Mozilla triage; kernel reporters | Kubernetes triagers and SIG maintainers (prow labels) |
| Routing | 2-way (network / storage) | **3-way** (`sig/network`, `sig/storage`, `sig/node`) |
| Binary decision | Is it a regression? | **Is it a bug** (`kind/bug`), or a feature, support or cleanup item? |
| Ordinal decision | Severity (3 levels) | **Priority** (3 levels, from `priority/*`) |
| Split | Random development set, natural-mix held-out set | **Chronological**: develop on earlier issues, test on later ones |

**Unchanged on purpose:**
- the model (Jev; version recorded);
- the three-primitive chain with appended upstream decisions;
- 3 calls per node with modal reduction;
- the action rule F;
- the frozen cost table.

The reason is that this is a replication of the *finding*, not a new
method.

## 3. Population, labels and exclusions (fixed)

**Source.** Issues (not pull requests) in kubernetes/kubernetes,
fetched with the public GitHub REST API. Read-only.

**Eligible issues:**
1. **Routing:** exactly one of `sig/network`, `sig/storage` or
   `sig/node`.
2. **Kind:** exactly one of `kind/bug`, `kind/feature`, `kind/support`
   or `kind/cleanup`.
3. **Priority:** exactly one priority label.
   - Level 2 = `priority/critical-urgent`.
   - Level 1 = `priority/important-soon`.
   - Level 0 = `priority/important-longterm` or `priority/backlog`.
4. **Exclude test-infrastructure issues:** anything carrying
   `kind/flake`, `kind/failing-test` or `triage/duplicate`.
5. **Exclude bot-authored issues** (author type Bot).
6. **Created before 2026-10-01.**
7. **Length:** at least 100 characters of text after cleaning.

**Reference labels** are the labels at fetch time. They are triagers'
judgments, not ground truth, and this is stated as a limitation.

**Text and leakage control.**
- The model sees the issue title plus body only. No comments, no
  timeline, no labels.
- **Label leakage is removed:**
  - every line starting with `/` (prow commands such as `/sig network`,
    `/kind bug`, `/priority ...`);
  - every literal label string (`sig/...`, `kind/...`, `priority/...`,
    `triage/...`);
  - HTML comments, which hold issue-template instructions.
- **Privacy:** @-mentions and e-mail addresses are replaced.
- **Truncation:** to 2,000 characters at a sentence or paragraph
  boundary, using the existing builders' functions.
- **Audit:** an automated check fails the build if any label string or
  prow command survives cleaning.

## 4. Chronological split (fixed rule)

Eligible issues are sorted by `created_at`.
- **Test:** the most recent 500.
- **Calibration window:** the 150 issues immediately before the test
  set. Their *labels only* are used, as an alternative prior estimate.
  They get no model calls.
- **Development:** the 500 issues immediately before the calibration
  window. Earlier issues are unused.
- **Fewer than 1,150 eligible issues:** test = latest 40%, calibration =
  the preceding 10%, development = the preceding 50%. The resulting sizes
  are recorded.

**Linked-issue leakage.** Drop any test issue whose body references a
development issue number (`#NNNN` or an issue URL), or that a
development issue body references. Do the same between calibration and
test. Counts are reported.

**Feasibility.** GitHub search totals for the three SIGs give about
1,300 bug issues with a priority label and about 580 non-bug issues with
a priority label, before exclusions. The natural mix is dominated by
`sig/node` (about 85%). That mix is kept and reported, not rebalanced.

## 5. Calls and budget (fixed)

**Jev:**
- 3 nodes × 3 repeats = 9 calls per issue.
- Development and test sets only: about 1,000 issues, so about 9,000
  calls.
- A smoke test of 30 development issues (270 calls) runs first.
- **Model version:** `jev-latest`, with the resolved version recorded.
  If it is not `jev-1.13.0`, stop after the smoke test and report before
  any full run.
- **Failure handling:**
  - retry up to 2 times;
  - if more than 1% of calls fail after retries, stop and report;
  - no topping-up of samples after any outcome is seen.
- **Cap:** 9,500 Jev calls in total.

**Replications:** OpenJev (same commit and serving as before) and the
three open models, on the same issues and prompts. **Separately
authorized**, Modal GPU only.

## 6. Analyses (fixed)

**Target.** As in the paper: wrong workflow action (a ≠ a\* with
a\* = F(reference labels)). The secondary targets are "priority wrong"
and "any node wrong".

**Development fit.** All rules and estimators are fitted on the
development set only (natural mix):
- the action rule (one pseudo-count);
- `E_dec` and `E_all` (L2 logistic, λ = 1, the project fitter).

**Label-shift arm.** No new calls are made for it.
- **Quota subsample:** from the development set, draw a subsample
  balanced across the three priority levels: the largest equal-count
  subsample, with a fixed seed.
- **Three fits on it:**
  - (a) unweighted;
  - (b) BBSE weights, from the subsample's confusion matrix of the
    `score` answer against priority, and the test set's `score`-answer
    mix (no test labels);
  - (c) calibration-window label-count weights.
- **Evaluation:** on the test set.

**Primary hypotheses (Jev).** Each uses a one-sided paired bootstrap
(B = 2,000, fixed seed `zlib.crc32`-derived), with Holm correction
across K1–K3 at family-wise α = 0.05.
- **K1:** the action rule ranks test-set wrong actions better than
  final-step confidence (paired AUROC difference > 0).
- **K2:** the action rule's test AUROC exceeds 0.5.
- **K3:** on the priority-wrong target, the quota-subsample estimator
  with BBSE weights (b) has a higher test AUROC than without weights (a).

**Secondary (reported whatever the outcome; no multiplicity claims):**
- paired CIs for `E_dec` − action rule and `E_all` − `E_dec`;
- the any-node target;
- weights (c) vs (b);
- a natural development fit vs the quota-subsample fit;
- cost at a 10% review budget under the frozen table, with the oracle
  bound;
- per-SIG results where n ≥ 50.

**Replication models.** The same K1 and K2, Holm within each model,
reported as replications.

**Interpretation (fixed now):**
- **K1 supported:** the main predictive finding replicates in an
  independent workflow.
- **K1 not supported:** it does not replicate, and the paper says so in
  its abstract.
- **K3 not supported:** the label-free correction does not transfer to
  this workflow.
- **Power.** For a single-tracker paired AUROC contrast on 500 issues,
  the standard error is about 0.03. The minimum detectable difference is
  therefore about 0.06 at 80% power, against the 0.21 observed in the
  original study. A smaller true effect may be missed, and that is
  stated.

## 7. Deviations

Any change after authorization is recorded as a dated amendment before
the data it affects exist. Interim outcomes are not inspected between the
smoke test and the full run, beyond call-failure counts and the version
check.

## 8. Artifacts

- `research/src/build_k8s_dataset.py` (dataset build and leakage audit);
- `research/src/run_k8s_workflow.py` (calls, with the same safeguards
  as earlier runners: dry run, explicit confirm flags, resume);
- `research/src/analyze_k8s.py`;
- results in `research/results/k8s_*`.
