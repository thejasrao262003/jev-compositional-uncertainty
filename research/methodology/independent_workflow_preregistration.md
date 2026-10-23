# Pre-registration: independent-workflow replication (Kubernetes issue triage)

**Status:** APPROVED and frozen as v1, 2026-10-23.
- Approved by the authors on 2026-10-23 (Draft 2.4 text, unchanged).
- Any later change is a dated amendment (§10).
- Draft 1 (commit `7c692be`) is superseded; Draft 2 responds to its
  review, issues A–F plus the smaller items.
- **Draft 2.1** fixes four problems found in a line-by-line read of
  Draft 2 (`bc4ee9e`):
  1. an inconclusive-null rule that could never yield "not replicated";
  2. model-facing questions that were not pre-registered;
  3. no power statement for K2 and K3;
  4. an unspecified (human) blinded reader.
- **Draft 2.2:**
  - adds the reviewer's SIG-scope nuances to the routing criteria (CNI
    integration, not the specification; storage plugins; devices and
    images);
  - names the blinded reader.
- **Draft 2.3** answers the review of Draft 2.2:
  - consistent K3 interpretation (inconclusive, never "fails");
  - unstable answers handled identically in the BBSE C and μ;
  - a pre-committed stop rule for too-rare actions;
  - a qualified K2 power claim;
  - the exact model-facing input, traced to code and commits.
- **Draft 2.4** answers the review of Draft 2.3:
  - states the extra BBSE assumption (stable-answer mix re-weights all
    rows) and adds a per-label instability diagnostic;
  - removes the K1-derived equivalence threshold for K2 (a non-supported
    K2 is inconclusive).
- No issue has been fetched for this study.
- No model call has been made.
- No outcome exists.

**Gates, in order:**
1. approval of this draft (done 2026-10-23);
2. authorization of the GitHub-only dataset build (done 2026-10-23);
3. inspection of the build report (§9);
4. separate authorization of the Jev calls;
5. separate authorization of GPU replications.

Feasibility counts come from GitHub search totals and label metadata
only.

## 1. Question

Does the **historical error rate of the action the workflow chose**
(§6.1) rank workflow failures better than final-step confidence in an
independent workflow? And does a label-free label-shift correction
improve a deliberately mismatched development fit?

**Negative results are valid outcomes** and are reported as the
replication result.

## 2. What is independent, and what is not

| | Original study | This study |
|---|---|---|
| Platform and tracker | Bugzilla (Mozilla, kernel) | GitHub (kubernetes/kubernetes) |
| Routing labels | Component (triage / reporter) | `sig/*`, applied through prow commands by people |
| Binary labels | Regression flag | `kind/bug` vs `kind/feature`/`support`/`cleanup`; **reporter's template choice since Oct 2021** (§3) |
| Ordinal labels | Severity | `priority/*`, applied through prow commands by triagers |
| Routing | 2-way | **3-way** |
| Split | Random development set, natural held-out set | **Chronological** |

**Unchanged on purpose:**
- the model;
- the three-primitive chain with appended upstream decisions;
- 3 calls per node with modal reduction;
- the logic of the action rule (§4);
- the frozen cost table.

This is a replication of the finding, not a new method.

## 3. Population, labels and their semantics (fixed)

**Source.** Issues (not pull requests) in kubernetes/kubernetes, read
through the public GitHub REST API. The snapshot date is recorded.

**Eligible issues** must satisfy all of:
1. exactly one of `sig/network`, `sig/storage`, `sig/node`;
2. exactly one of `kind/bug`, `kind/feature`, `kind/support`,
   `kind/cleanup`;
3. exactly one of `priority/critical-urgent`, `priority/important-soon`,
   `priority/important-longterm`, `priority/backlog`.

**Excluded:**
- issues carrying `priority/awaiting-more-evidence`. Its description
  ("not yet enough support to actually get it done") records an
  evidence state, not an urgency level;
- issues carrying `kind/flake`, `kind/failing-test` or
  `triage/duplicate`;
- bot-authored issues;
- issues created on or after 2026-10-01;
- issues with fewer than 100 characters of model-visible text after
  cleaning (§3.3).

### 3.1 Priority semantics: an operational urgency scale, not severity

The label descriptions are quoted from the repository:

| Level | Labels | Description |
|---|---|---|
| **2** | `critical-urgent` | "Must be actively worked on as someone's top priority right now." |
| **1** | `important-soon` | "Must be staffed and worked on either currently, or very soon, ideally in time for the next release." |
| **0** | `important-longterm` | "May not be staffed and/or may need multiple releases to complete" |
| **0** | `backlog` | "Higher priority than awaiting-more-evidence" |

- **Why merge the two level-0 labels:** neither is committed for the
  next release. That is the distinction the action rule needs between
  scheduling now and not scheduling.
- **Reporting:** the two labels' counts are reported separately. A
  secondary analysis treats them as distinct.
- **No severity claim:** priority is a triage-urgency judgment, not a
  validated severity measure.

### 3.2 Label provenance and timing

- **Reference labels** are the labels at snapshot time.
- **Label timing:** for each target label, the time it was added is
  recorded from the issue-events API. The lag from creation is reported.
- **Early-triage secondary analysis:** restricted to issues whose `sig`,
  `kind` and `priority` labels were all applied within 30 days of
  creation.
- **`kind` provenance.** The bug-report and enhancement issue forms have
  existed since 2021-10-05 (verified at commit `fbd477a8bfe5`). They
  auto-apply `kind/bug` and `kind/feature`. For issues filed through
  them, the binary label is the **reporter's** classification, possibly
  corrected later. This parallels the kernel's reporter-set severity and
  is stated as a limitation.
- **`sig` and `priority`** are applied through prow commands, which
  people issue.

### 3.3 Model-visible text and leakage control

**Title plus the free-text answers only.**
- **Kept:** for issue-form issues, the answers to the free-text fields,
  with their headings removed:
  - bug form: "What happened?", "What did you expect to happen?",
    "How can we reproduce it…?", "Anything else we need to know?";
  - enhancement form: "What would you like to be added?", "Why is this
    needed?".
- **Dropped:** the structured environment fields that exist only in the
  bug form (Kubernetes version, Cloud provider, OS version, Install
  tools, Container runtime, Related plugins). Their presence alone would
  reveal the form.
- **Free-form issues** (pre-2021 or without a form): the body is kept,
  and any markdown heading matching a form heading is removed.
- **Not shown:** comments, timeline and labels.

**Removed before any model sees the text:**
- lines starting with `/` (prow commands);
- literal label strings (`sig/`, `kind/`, `priority/`, `triage/`,
  `area/`);
- team mentions `@kubernetes/sig-*` (routing cues);
- HTML comments;
- other @-mentions and e-mail addresses (privacy).

**Truncation:** to 2,000 characters at a sentence or paragraph
boundary, using the existing builders' functions.

**Leakage audit** (part of the build report):
- **Hard fail:** any surviving prow command, label string, form heading
  or team mention fails the build.
- **Soft flags (reported, not removed):** cue phrases such as "feature
  request", "is a bug", "regression", "P0", "P1", "priority",
  "severity", "critical", "urgent" and "SIG Network/Storage/Node". The
  flag rate is reported per split and per label.
- **Blinded manual inspection.** This is required before the Jev calls
  are authorized.
  - **Sample:** 40 cleaned issues (seed `zlib.crc32("k8s-blind")`),
    stratified 20 development and 20 test.
  - **Reader:** Tushar M (a human author who did not design the cleaning
    rules), or Thejas P Rao if Tushar is unavailable. Not an AI
    assistant.
    - The reader receives the cleaned text only, without reference
      labels, model outputs, or any marker of development or test.
    - The reader records the label-cue judgment for each issue before
      seeing any label metadata.
  - **What the reader records**, per issue:
    1. Is any of the three labels stated or recoverable from an explicit
       cue (a prow command, label text, form heading, SIG team mention,
       or a sentence such as "this is a feature request" or "P0")?
    2. Did cleaning damage the text (truncated mid-word, empty after
       stripping, a template remnant)?
    3. Free notes.
  - **Handling:**
    - **A cue class found in the sample is cleaning-rule-shaped** (for
      example, a template phrase the rules missed). The cleaning rule is
      amended as a dated amendment, the whole dataset is rebuilt, and the
      audit is repeated on a new seed. This is allowed only before any
      model call.
    - **The cue is natural reporter language** (for example, "feature
      request"). It is left in, as task-legitimate content, and its rate
      is reported. Removing it would make the task unnatural.
    - **Two or more of 40 show damaged text.** The cleaning is fixed and
      the dataset rebuilt, as above.
  - **Release:** the inspection log is committed. The texts stay
    private.

## 4. The action rule and target (frozen truth tables)

**The logic is unchanged.** `F(c2, c3)`, where `c3 = 2` means escalate,
and `c3 = 1` with `c2 = 1` means defer. The semantics in this workflow:
- **escalate** = assign now (top priority);
- **defer** = a bug scheduled for the next release;
- **accept** = normal SIG queue handling.

`F` ignores routing (`c1`), as in the original study.

### 4.1 Model-facing questions (frozen at approval)

The questions use the original study's format and adapter.
- **Routing criteria** summarize each SIG's official scope. They were
  checked against the Kubernetes community SIG descriptions in review
  (2026-10-23). Network covers the Kubernetes side of network-plugin
  integration, not the CNI specification itself. Node's charter
  excludes network and persistent-storage management.
- **The charters establish scope, not that every label is correct,**
  which is consistent with the operational target (§4.2). Priority
criteria quote the label descriptions (§3.1). **No wording may change
after approval**, including after the smoke test.

```json
{"routing": {"type": "choice",
  "instructions": "Which Kubernetes special interest group (SIG) should own this issue?",
  "criteria": {
    "network": "Cluster networking: Services, kube-proxy, DNS, Ingress and Gateway, NetworkPolicy, endpoints, and the Kubernetes side of network-plugin (CNI) integration",
    "storage": "Persistent storage: volumes, PersistentVolumes and claims, StorageClasses, storage plugins and CSI, snapshots, attach and mount",
    "node": "The node and kubelet: pod lifecycle on the node, container runtime (CRI), node-level resource management, devices and images, node status and reliability"}}}
```
```json
{"bug": {"type": "noul",
  "instructions": "Does this issue report a bug (behaviour that is incorrect or broken), as opposed to a feature request, a support question, or a cleanup task?"}}
```
```json
{"priority": {"type": "score",
  "instructions": "How urgently must this issue be worked on?",
  "criteria": [
    "Important over the long term or backlog; not needed for the next release",
    "Must be staffed and worked on soon, ideally in time for the next release",
    "Must be actively worked on as someone's top priority right now"]}}
```

**Exact model-facing input.**
- **The request body** is exactly `{"state": <state>, "model":
  "jev-latest", "questions": <one of the three JSON objects above>}`.
- **It is sent by** `research/src/jev_client/client.py`, unchanged since
  commit `f480613`. There are no wrapper or system instructions. The
  JSON objects above are the exact `questions` values.
- **The state** is built by the original adapter, `node_state` in
  `research/src/run_mozilla_validation.py` at commit `7c15bd7`. Only its
  two strings are relabelled for this workflow:
  - **node 1:** `state` = cleaned issue text.
  - **node 2:** `state` = `<text>\n\nRouting determination: <sig>.`
  - **node 3:** `state` = `<text>\n\nRouting determination: <sig>. Bug
    assessment: <a bug | not a bug>.`
  - **A missing upstream decision** is written `undetermined`, never
    `None`, as in the original.
- **Recorded in the runner's manifest:** the new runner's code hash, and
  a unit test asserting these exact strings.

### 4.2 Truth tables

**Reference (target) side.** `c2*` = 1 if `kind/bug`, else 0. `c3*` is
the priority level (§3.1). `c2*` is never unclear.

| `c2*` \ `c3*` | 0 | 1 | 2 |
|---|---|---|---|
| 1 (bug) | accept | **defer** | escalate |
| 0 (feature, support, cleanup) | accept | accept | escalate |

**Model (action) side, same function:**
- `c2` is the `noul` decision: mean probability ≥ 0.5 means 1, else 0.
  It is never unclear.
- `c3` is the modal `score` level.
- If `score` has no two-of-three majority, the action is **escalate**
  (fail-safe, as in the original study).
- A node with zero valid responses after retries is a failed issue. It
  is excluded, counted, and counts toward the failure stop rule (§5).

**Complete model-side table.** `c2` ∈ {0, 1}; `c3` ∈ {0, 1, 2, unstable}.

| `c2` \ `c3` | 0 | 1 | 2 | unstable |
|---|---|---|---|---|
| 1 | accept | defer | escalate | escalate |
| 0 | accept | accept | escalate | escalate |
| missing (0 valid responses) | failed issue (excluded and counted) | | | |

**Reference side.** Every eligible issue has exactly one valid label per
dimension (§3), so the reference table has no invalid cells.

The action set is therefore {accept, defer, escalate}. Request-evidence
cannot occur, as in the original real-data runs.

**What "failure" means here.** The target is disagreement with an
*operational* classification:
- triagers' urgency for priority;
- the reporter's (possibly later-corrected) template choice for bug-ness;
- SIG assignment for routing.

It is not objective bug truth. The paper must say this wherever the
result is stated.

**Targets:**
- **Primary:** a ≠ a\*.
- **Secondary:**
  - priority wrong (`c3 ≠ c3*`, with an unstable `c3` counted as wrong);
  - any node wrong (routing, bug-ness or priority).

## 5. Split, linkage, snapshot and budget (fixed)

**Chronological split.** Sort eligible issues by `created_at`.
- **Test:** the latest 500.
- **Calibration window:** the preceding 150. Labels only; no model calls.
- **Development:** the preceding 500. Earlier issues are unused.
- **Fewer than 1,150 eligible issues:** test 40%, calibration 10%,
  development 50% of what exists. The test stays confirmatory if the
  test set has ≥ 300 issues, with the power implications in §7.
  Below 300 it is reported as exploratory.
- **The rule is applied mechanically.** The resulting sizes are fixed at
  build time, before any model call.

**Linked-issue removal (frozen algorithm).** Within title and body:
- the regexes `#(\d+)` and `github.com/kubernetes/kubernetes/(issues|pull)/(\d+)`;
- plus `cross-referenced` timeline events between issues;
- plus `state_reason == "duplicate"` with its target.

Any test issue linked to a development or calibration issue, either way,
is removed. Linked pairs within a split are kept. Counts are reported.

**Snapshot integrity.** The build records:
- issue numbers;
- `created_at`;
- the full label set and the label-event times;
- the API endpoints, query parameters and page counts;
- the snapshot time;
- the cleaned-text SHA-256;
- the dataset SHA-256;
- the template commit `fbd477a8bfe5`.

Texts are kept private, as in the original study's release policy.

**Jev budget.**
- 9 calls per issue on the development and test sets.
- **Smoke test:** 30 development issues (270 calls). It is included in
  the cap, its outputs are reused as part of the development set, and
  it is not used to change prompts.
- **Retries:** up to 2 per call, counted toward the cap.
- **Cap:** 9,500 calls including smoke test and retries.
- **Stop rules:**
  - stop if the resolved model is not `jev-1.13.0` (checked at the smoke
    test);
  - stop if more than 1% of issues fail after retries;
  - stop at the cap.
- No sample top-ups after any outcome is seen.

**Replications** (OpenJev at commit `b4a89f5`, Qwen2.5, Phi-3.5,
OLMo-2) are secondary, run only after the Jev analysis is frozen, need
separate authorization, and are reported whatever they show.

## 6. Scores and estimators (frozen)

### 6.1 The primary score: the chosen action's historical error rate

For each action a, estimated on the **development set only**:

r(a) = (e(a) + r̄) / (n(a) + 1)

- e(a) is the number of development issues with action a whose action
  is wrong.
- n(a) is the number of development issues with action a.
- r̄ is the overall development error rate.
- An action unseen in development gets r̄.

Each test issue's score is r(its action). A higher score means riskier.
Ties are handled by AUROC's half-credit.

### 6.2 The comparator: final-step confidence

The score is −(mean `score` confidence over the 3 calls). A higher score
means riskier. An unstable or missing confidence counts as 0, giving risk
0, the highest possible. The direction is frozen.

### 6.3 Secondary estimators

`E_dec` and `E_all` use the project L2 logistic fitter (λ = 1) on the
decision features and on decision plus uncertainty features, fitted on
the development set.

### 6.4 The label-shift arm (K3), with a controlled comparison

**Quota subsample.** From the development set, take the largest
subsample with equal counts per priority level (seed fixed,
`zlib.crc32("k8s-quota")`). It gets no new calls.

**One estimator for all three arms.**
- Features: `DECISION`.
- Model: `StandardScaler` then `LogisticRegression(C=1.0, lbfgs,
  max_iter=2000)`.
- Target: priority wrong.
- Evaluation: the same test rows.

**Only the weights differ:**
- **(a) Unweighted:** w = 1.
- **(b) BBSE** (Lipton et al., 2018).
  - Classes: priority levels {0, 1, 2}. Predictor: the model's modal
    `score` answer, excluding unstable answers.
  - Confusion matrix: C[i, j] = share of quota-subsample issues with
    answer i and label j.
  - Answer mix: μ[i] = share of **test** issues with answer i, among
    test issues with a **stable** `score` answer. Unstable answers are
    excluded from both C and μ, so both are defined on the same event,
    a stable answer, and each sums to 1. No test labels are used.
  - **Estimand.** The correction estimates the test label mix
    *conditional on a stable `score` answer*. It assumes instability is
    unrelated to the label. The unstable-answer fraction is reported for
    the quota subsample and for the test set.
  - **Weights apply to all quota-subsample issues by label,** including
    those with an unstable answer. Those issues stay in the fit, with the
    weight of their label, so all three arms use the same training rows
    and the comparison stays controlled.
  - **Additional assumption (stated, not tested as a gate):** the label
    mix estimated among stable-answer issues is used to re-weight *all*
    quota-subsample issues. That requires the stable-answer conditional
    label mix to represent the full sample's label mix, which holds if
    instability is unrelated to the priority label.
  - **Diagnostic (reported, not used to select a method):**
    - the unstable-answer rate **by true priority label** in the quota
      subsample and in the development set;
    - the overall unstable-answer rate in the test set (test labels are
      not used for weighting).
    - Whatever these rates show, the method is not changed.
  - Solve C v = μ. If cond(C) > 100 or the solve fails, K3 is
    **"not evaluable"** and counted as not supported. Negative v are
    clipped to 0.
  - **Why 100:** in the original study, BBSE worked at condition
    numbers 13–37 (Jev, OpenJev, Qwen2.5) and failed at 371–905
    (Phi-3.5) and ~10^16 (OLMo-2).
  - Weight for a quota-subsample issue with label j: v[j], normalized to
    mean 1.
- **(c) Calibration window:** v[j] = q_cal[j] / p_quota[j]. Here q_cal
  is the calibration window's label proportions with add-one smoothing,
  and p_quota is the subsample's proportions (equal by construction).
  Normalized the same way. q_cal's 95% multinomial CIs are reported. (c)
  is a practical baseline, not an oracle.

## 7. Hypotheses, tests and power (fixed)

**Tests.** One-sided paired bootstrap, B = 2,000, seed
`zlib.crc32("k8s-K")`, resampling test issues. Holm correction across
K1–K3, family-wise α = 0.05.

- **K1:** AUROC(r(a)) − AUROC(final-step confidence) > 0, on the test
  set, target a ≠ a\*.
- **K2:** AUROC(r(a)) > 0.5 on the test set.
- **K3:** AUROC(arm b) − AUROC(arm a) > 0, on the priority-wrong target.

**Power (simulation: `research/src/k8s_power_simulation.py`, results in
`k8s_power_simulation.json`).**
- **Generative model:** a paired-AUROC test on simulated data. The
  action-rule score has 3 tied levels; confidence AUROC is 0.55.
- **Varied:** effect +0.03 / +0.06 / +0.10 / +0.20, failure prevalence
  0.25 / 0.45, correlation between the rankings 0.2 / 0.5, and n = 500 /
  300.
- **Reported** both at α = 0.05 and at the Holm worst case α = 0.05/3.

**Power for K1.**
- **Ranges** are across the four (prevalence, correlation) settings:
  prevalence 0.25 / 0.45 × correlation 0.2 / 0.5.
- **Settings:** 300 simulated studies per cell; B = 400 inside each.
- **Baseline:** confidence AUROC 0.55; the action-rule score has 3 tied
  levels (60/25/15%).

| AUROC difference | n = 500, α = 0.05 | n = 500, Holm worst (α/3) | n = 300, α = 0.05 | n = 300, Holm worst (α/3) |
|---|---|---|---|---|
| +0.03 | 0.19–0.32 | 0.11–0.19 | 0.15–0.24 | 0.08–0.11 |
| +0.06 | 0.46–0.76 | 0.31–0.59 | 0.35–0.59 | 0.18–0.42 |
| +0.10 | 0.86–0.98 | 0.73–0.94 | 0.61–0.92 | 0.45–0.78 |
| +0.20 | 1.00–1.00 | 1.00–1.00 | 1.00–1.00 | 0.99–1.00 |

**What the design can detect:**
- **+0.10 or more** at n = 500 (power 0.86–0.98 nominal, 0.73–0.94 at
  the Holm worst case).
- **The original study's effect, +0.21,** is detected with power
  ≈ 1.00 at either size.
- **+0.06 is not reliably detectable:** power 0.46–0.76 at n = 500.
- **+0.03 is undetectable:** power ≤ 0.32.
- **Correction of Draft 1:** Draft 1's "minimum detectable difference
  about 0.06" was wrong. It is about 0.10.
- **d\* (used by the interpretation rule below)** is the smallest
  simulated effect with power ≥ 0.80 in every setting at nominal α.
  - **n = 500:** d\* = +0.10.
  - **n = 300:** +0.10 is not reliably detected (power 0.61–0.92), so
    d\* = +0.20. The grid does not resolve it more finely.
- **If fewer than 500 test issues survive,** the table for the realized
  n is recomputed with the same script before any model call. The
  realized-n power is reported.

**K2 and K3:**
- **K2** (above chance) is a one-sample contrast against 0.5.
  - **Not simulated.** Under the simulation's assumptions the action-rule
    score's own AUROC (0.58–0.75 for the K1 effects simulated) is
    expected to be easier to distinguish from 0.5 than the paired
    difference is from 0.
  - **The power of K2 was not directly evaluated.** K2 measures one
    AUROC's distance above 0.5, a different effect size from K1's paired
    difference, so K1's d\* does not apply to it.
  - **A non-supported K2 is reported as inconclusive,** with its 95% CI,
    and no equivalence claim is made.
- **K3 was not simulated.** Its effect size cannot be planned from the
  original study, because that study had no quota-vs-natural mismatch on
  a priority target. A non-supported K3 is therefore always reported as
  **inconclusive about the correction**, never as evidence that it does
  not work.

**Interpretation (fixed):**
- **The 300-test-issue floor is a protocol decision, not a power
  guarantee.**
- **K1 supported:** the finding replicates in an independent workflow.
- **K1 not supported.** Read the two-sided 95% percentile CI of the
  paired difference, from the same bootstrap, against d\*. Here d\* is
  the smallest effect the design reliably detects (§7: +0.10 at n = 500,
  +0.20 at n = 300; recomputed for the realized n).
  - **Upper bound < d\*:** reported as **not replicated**. Effects the
    design could detect are excluded.
  - **Upper bound ≥ d\*:** reported as **inconclusive**. An effect of
    detectable size remains compatible with the data.
  - Either way, this is stated in the paper's abstract.
- **K3 supported:** the pre-registered test supports the label-free
  correction in this workflow.
- **K3 not supported: inconclusive about the correction.** It is never
  reported as evidence that the correction fails, because K3's power was
  not simulated. The report says which case applies:
  - (i) **a negative point estimate** (arm b below arm a);
  - (ii) **a positive but non-significant estimate**;
  - (iii) **not evaluable**: the stability check failed (cond(C) > 100)
    or the solve failed.
- **Stability is not accuracy.** Passing the condition-number check
  shows only that the BBSE inversion is numerically stable, not that the
  estimated mix is correct. The estimated mix is reported against the
  true test mix *after* the test.
- **No method change on failure.** If BBSE fails its check, that is
  reported, and no alternative estimator is substituted.
- **Calibration-window weights** are reported with their uncertainty and
  their temporal distance from the test set.

## 8. Secondary analyses (reported whatever the outcome)

**No multiplicity claims:**
- paired CIs for `E_dec` − r(a) and `E_all` − `E_dec`;
- the any-node target;
- arm (c) vs arm (b);
- the natural development fit vs the quota fit;
- separate level-0 labels;
- the early-triage subset;
- per-SIG results where n ≥ 50.

**A hypothetical cost analysis:** the frozen cost table at a 10% review
budget, with the oracle bound. These costs have not been validated for
Kubernetes triage and are reported as such.

**Replication models:** K1 and K2 with Holm within each model.

## 9. Build report, required before the Jev-call decision

1. Eligible counts after each exclusion, with the snapshot time.
2. Counts by routing, kind and priority, and their joint distributions,
   per split.
3. Target-action prevalence under F, per split.
   - **Feasibility rule (pre-committed, no rebalancing):** each target
     action (accept, defer, escalate) must have n ≥ 20 in the development
     set **and** n ≥ 20 in the test set.
   - **If any count is below 20, the study stops.** It is reported as
     infeasible under the pre-registered design. No model call is made.
   - **Any alternative design** (for example, merging actions or another
     population) requires a new dated amendment, written and approved
     before any model call. It is reported as a deviation.
4. Split sizes, linked-issue removals and the label-lag distribution.
5. The leakage audit: hard checks, soft-flag rates, and the 40-issue
   blinded sample, ready for an author to read.
6. Dataset, text and manifest hashes.

## 10. Deviations

Any change after approval is a dated amendment, written before the data
it affects exist. Between the smoke test and the full run, only failure
counts and the version check are inspected.

---

## Amendment 1 (2026-10-23), written after the first build and before any model call

**What the first build found** (`k8s_build_report.json`):
- **Leakage hard check failed for 24 issues.** Pre-2021 issue templates
  wrote prow commands as block quotes (`> /kind bug`). The pre-step
  removed command lines *before* `moz.clean` stripped the `> ` prefix,
  so the commands survived. The same old template asks "Is this a BUG
  REPORT or FEATURE REQUEST?", and the reporter's answer reveals `kind`.
- **The feasibility rule (§9) failed.** The test set has 16 *escalate*
  target actions, below the floor of 20.

**Cleaning fix (applies the §3.3 rule as intended; no other change):**
- **Prow commands** are also removed when quoted (`^\s*>?\s*/command`).
- **The old-template kind question is removed:** the line "Is this a BUG
  REPORT or FEATURE REQUEST?", the line "Uncomment only one, leave it on
  its own line", and every line between them and the next `**What`
  heading.
- **Two new hard checks:** the leakage audit now also fails on "BUG
  REPORT or FEATURE REQUEST" and "Uncomment only one".
- **The rebuild uses the cached API responses** (same snapshot).

**Feasibility.** The §9 rule is binding.
- **If the rebuilt test set still has fewer than 20 escalate actions,
  the study stops** as infeasible under the pre-registered design.
- **No Jev call is made.**
- Any redesign is a new amendment needing explicit approval before
  calls.

## Amendment 2 (2026-10-23), written after the Amendment 1 rebuild and before any model call

**Why.** The rebuilt test set (the latest 500 eligible issues) failed the
§9 feasibility gate with 16 *escalate* target actions. The original
design and its failure remain recorded (`k8s_build_report.md`, commit
`09ae38a`).

**Change (one-time; chosen by the authors on 2026-10-23).**
- **Test:** the latest **600** eligible issues, not 500.
- **Calibration:** the preceding 150.
- **Development:** the preceding 500.
- **Everything else is unchanged:** eligibility, cleaning (Amendment 1),
  linked-issue removal, the action rule, the questions, the scores, the
  hypotheses, the tests and the interpretation rules.

**How 600 was chosen.** From label counts of the eligible pool only (no
model output exists). It is the smallest of the sizes examined (500,
600, 650, 700, 750) that gives at least 20 escalate actions before
linked-issue removal (28).

**Gates (binding):**
1. **Feasibility.** After linked-issue removal, the test set must still
   have ≥ 20 of each action, and the development set too. **If it fails,
   the study stops for good.** The window is not widened or adjusted
   again.
2. **Leakage.** The hard checks must pass.
3. **Power.** If the final test n differs from 500, the K1 power table
   is recomputed for that n before any model call, and d\* is set from
   it.
4. **Separate approvals.** Passing these gates authorizes neither model
   calls nor human annotation. The 270-call smoke test and the 40-issue
   blinded read are separate decisions, and the read needs an available
   human author.

**Framing (binding on the paper).** Development and test differ at once
in label prevalence (22% vs about 3–5% escalate) and in input format
(0% vs about 80% filed through issue forms). The study is therefore a
**combined test of temporal and distribution shift**, not an isolated
test of label shift. Any change in performance cannot be attributed to
label prevalence alone. It is a test of whether the findings transfer
to a different workflow and period, not a guaranteed replication.

## Amendment 3 (APPROVED 2026-10-23, budget only)

**Finding.** The runner's dry run shows the Amendment 2 design needs
(500 + 582) × 9 = **9,738** Jev calls before retries. That exceeds the
frozen cap of 9,500, which was sized for 1,000 issues. Amendment 2 did
not update the cap; that was an oversight. The runner refuses to plan
past the cap, so no call can start.

**Proposed change.**
- **New cap:** 10,300 calls, including the smoke test and retries
  (9,738 planned plus about 5% for retries).
- **Unchanged:** everything else, including the stop rules (model
  version, > 1% failed issues, cap) and the separate approval of the
  270-call smoke test.

**Status: approved by the authors on 2026-10-23, for the budget only.**
- **Cap:** 10,300 calls. That is 9,738 planned plus about 5% for
  retries, about 10,225, leaving about 75 calls of headroom.
- **Unchanged:** the test window, the hypotheses, the analysis and the
  stop rules.
- **This approval does not authorize any model call.**

**Power gate at the realized n = 582** (`k8s_power_realized.json`,
recorded before any call):
- **The frozen rule** (§7: "smallest simulated effect with power ≥ 0.80
  in every setting at nominal α") gives **d\* = +0.10**. Power at
  +0.10 is 0.92–0.99 at nominal α.
- **No Holm-adjusted floor was pre-specified.** The Holm worst-case
  power at +0.10, 0.78–0.97, is reported as such and is not a gate.
- **The criterion is not revisited after outputs exist.**

## Amendment 4 (2026-10-23), written after the first blinded read and before any model call

**Finding** (first blinded read, `blind_log_first_read.csv`):
- **Leaked kind cues in 12 of 40 cleaned issues.** Pre-form Kubernetes
  issues used older *markdown* templates whose bold headings survived
  cleaning: `**What happened**:`, `**What you expected to happen**:`,
  `**How to reproduce it…**:`, `**Anything else we need to know?**:`,
  `**Environment**:` with its sub-fields, `**What would you like to be
  added**:`, `**Why is this needed**:` and `**How to categorize this
  issue?**`. Failing-test remnants (`### Relevant SIG(s)`, empty `###`
  lines) also survived.
- **These reveal `kind`,** just as the form headings do. The cue class is
  cleaning-rule-shaped, so by §3.3 the rule is amended, the dataset is
  rebuilt and the read is repeated on a new seed.
- **Provenance of the read.** The protocol requires the reader to be a
  human author. The authors must confirm who produced
  `blind_log_first_read.csv`. Either way, its findings were checked
  against the texts by script, and they hold.

**Cleaning change (same principle as §3.3, extended to the older
templates):**
- **Bold template headings** listed above are removed, and their content
  is kept.
- **The `**Environment**:` block** is dropped up to the next bold
  heading, like the form's environment fields.
- **`### Relevant SIG(s)` sections** are dropped, and so are empty
  `###` lines.
- **Hard checks** now also fail on any of these headings.

**Not changed:** fenced code blocks are still removed. That is
`moz.clean`, shared with the Mozilla and kernel datasets.
- In the read, three issues (B03, B15, B39) show an "Example:" whose
  code block was removed. That follows from this by-design rule and is
  not counted as cleaning damage. Its rate is reported.

**The new blinded sample** uses seed `zlib.crc32("k8s-blind-2")` and
must be read by a human author before any model call.

## Amendment 5 (2026-10-23), the authors' decision on the blinded read

**Change.** The authors accepted an **AI assistant's** read of the
blinded sample as the blinded read, in place of a human author's
(§3.3). This is a deviation from the frozen protocol.

**The first read:**
- **File:** `blind_log_first_read.tsv`.
- **It found** the old-template leakage handled by Amendment 4.
- **It was checked** against the cleaned texts by script, and its
  template-heading findings were confirmed.

**The repeated read** on the rebuilt dataset (new seed, Amendment 4) is
done the same way, by an AI assistant, with the same packet and log
format.
- It must not be done by the assistant that wrote the cleaning rules.
- Its findings are checked by script.

**Disclosure.** The paper states that the leakage read was performed by
an AI assistant at the authors' direction, not by a human author as
pre-registered. It is listed as a protocol deviation.

## Amendment 6 (2026-10-24), written after the second blinded read and before any model call

**Second read** (`blind_log_second_read.tsv`, AI assistant per
Amendment 5):
- **No template remnants.**
- **17 of 40 natural reporter cues** ("we found a bug", "Remove …",
  "[SIG NODE Discussion]"). These stay in, as task-legitimate content,
  and their rate is reported.
- **1 possibly damaged text** (B15, orphaned "N/A" answers), below the
  threshold of 2.
- **`@user` and `[team]` placeholders** are the intended replacements
  (§3.3).

**Cleaning-rule gap found.** The read found `@user/goog-node` in B35.
- A script found **20 of 1,232 issues** with surviving team names after
  `@org/`, for example `goog-node`, `rh-storage` and `goog-image`. The
  team-mention rule removed only `@kubernetes/sig-*`, and the generic
  mention rule replaced only the `@org` part.
- Team names can reveal routing, so this cue class is
  cleaning-rule-shaped.

**Fix.**
- **Every `@org/team` mention** is replaced by `[team]` before the
  generic mention rule runs.
- **New hard check:** the build fails on any `@org/team` or `@user/`
  remnant.

**Then:** the dataset is rebuilt, and the read is repeated on a new seed
(`zlib.crc32("k8s-blind-3")`) under Amendment 5.

**Amendment 6b**, same date, before the third read and before any model
call.
- **Why:** a script sweep of the whole dataset, run after the team-mention
  fix, found 5 more issues with old template headings in other markdown
  formats: `#### What you expected to happen:`, and `**What happened?**`
  with the `?` inside the bold markers.
- **Fix:** template headings are now matched after normalization, so any
  `#` level, bold or not, with or without a trailing `:` or `?`, in any
  case, against one list of all known form and markdown-template
  headings. Environment sections are dropped in either format.
- **The hard check uses the same normalization.** The rebuild has 0
  template headings in any format, 0 `@org/team` remnants and 0 hard
  failures.
- **The sweep also found** natural reporter cues, which stay in and are
  reported:
  - "[sig-node]"-style title prefixes (5);
  - one old-era "P0" label mentioned in prose;
  - "priority: 0" as a YAML field.

**Third read, rejected** (2026-10-24).
- **Why:** the AI-assistant log for the third packet quoted cues that do
  not appear in the issues they were attributed to. 14 of 26 quoted cues
  matched the second packet's issues under the same B codes. The log
  therefore does not describe the third packet.
- **Kept as:** `blind_log_third_read_REJECTED_cues.tsv` (the extracted
  quotes and the check).
- **Fix:** the same sample (seed `k8s-blind-3`) is relabelled K01–K40,
  so its codes cannot collide with earlier packets. The packet asks for
  verbatim quotes, and those quotes are checked by script against the
  K-coded texts before the read is accepted.

**Third read, K01–K40: accepted** (2026-10-24; `blind_log_third_read_K.tsv`).
- **Verbatim cues:** all 22 quoted cues appear in their own K-coded text
  (script check).
- **"No cue" notes:** 13 of 13 spot-checked notes describe the correct
  issue.
- **Damaged texts:** 0.
- **The 22 cues are natural reporter language** and stay in. Their rate
  is reported.
  - One SIG cue is `[sig-node]` inside a pasted e2e test name. Such
    test-name tags occur in 17 of 1,232 issues and are reported as a
    natural cue rate.
- **No cleaning-rule gap was found.**
- **Disclosure.** The AI assistant stated that it could not certify it
  ran in a fresh conversation. Isolation was meant to prevent judging
  the wrong packet's text, and that is verified directly by the
  verbatim-quote check. The read is accepted on that basis, under
  Amendment 5.

**Gate status before the smoke test:**
- feasibility: pass;
- leakage hard checks: pass;
- power at n = 582: d\* = +0.10;
- cap: 10,300 (Amendment 3);
- blinded read: accepted.

**The 270-call smoke test still needs its own explicit authorization.**

## Smoke test, stopped by the version rule (2026-10-24)

**Authorization:** the authors authorized the 270-call smoke test on
2026-10-24.

**What happened:**
- **Calls made: 9** (1 issue × 3 nodes × 3 repeats).
- **All HTTP 200 and parsed; no retries.**
- **`jev-latest` resolved to `jev-1.14.0`.** By the §5 stop rule
  ("stop if the resolved model is not `jev-1.13.0`"), the runner stopped.
- **No model output was inspected** beyond version, HTTP status and
  parse status.

**Status:** stopped. No further call is made until the authors decide
how to treat the model version. That decision will be a new amendment.

## Amendment 7 (2026-10-24, approved by the authors): pin `jev-1.13.0`

**Change.**
- **Requests:** `"model": "jev-1.13.0"` replaces `"model": "jev-latest"`
  (§4.1). Everything else in the request body is unchanged.
- **Why:** the replication tests the finding with the same model as the
  original study, which used `jev-1.13.0`.
- **The stop rule is unchanged:** any resolved model other than
  `jev-1.13.0` stops the run.

**The 9 earlier calls** resolved to `jev-1.14.0`.
- They are moved to `research/data/k8s/superseded_jev_1_14_0/` and are
  never analysed.
- They count toward the overall budget, so the runner's cap is 10,291
  (10,300 − 9).

**Before the smoke test:** one probe call checks that the pinned version
is served. It counts toward the budget, and the cap becomes 10,290. If
the version is not served, nothing more runs, and the authors choose
between running on `jev-1.14.0` (disclosed) and stopping.

**Smoke test on the pinned `jev-1.13.0`: PASS** (2026-10-24).
- **Calls:** 270 (30 development issues × 9).
- **Results:** all HTTP 200; all parsed; all resolved to `jev-1.13.0`;
  0 retries; 0 failed issues.
- **Only these criteria were inspected.**
- **The smoke outputs are reused as part of the development set** (§5).
- **The full run needs separate authorization.**

## Results recorded (2026-10-24)

**Run:** 9,738 calls, all valid. **Analysis:** run once as frozen
(`k8s_results.md`).

| | Verdict |
|---|---|
| K1 | Supported (+0.149 [+0.091, +0.207]) |
| K2 | Supported |
| K3 | Inconclusive (negative estimate; −0.350 [−0.428, −0.271]; BBSE estimate [0, 1, 0] vs true [0.69, 0.26, 0.05]) |
