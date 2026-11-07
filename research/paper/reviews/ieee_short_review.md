# Review of the short IEEE version (working draft)

**Manuscript:** "Jev in a Multi-Step Workflow: Predicting Failures Is Not
Knowing Which Reviews Pay", short IEEE version (7 pages,
`research/paper/jev_paper_IEEE_short.pdf`, sources in
`research/paper/ieee_short/`).

**Method:** the workflow of the `peer-review` skill from K-Dense-AI,
*Scientific Agent Skills* (MIT licence,
github.com/K-Dense-AI/scientific-agent-skills, `skills/peer-review`,
v2.4). It was applied by hand:
- scope;
- neutral map;
- reporting guidance;
- claim–evidence matrix;
- methods and statistics in the skill's order;
- reproducibility;
- ethics;
- figures, tables and citations;
- comments in the form Location / Observation / Evidence / Why it matters
  / Requested action.

The skill's bundled scripts only validate form declarations and were not
run.

**Status:** working draft for the authors. Not a decision. Per the skill,
an accountable human must verify every point before acting on it.

---

## 0. Scope, conflicts and limits

- **Material reviewed:** the short PDF and its LaTeX sources only. The
  full version, pre-registrations and code were consulted only to check
  whether something omitted here exists elsewhere; this is noted where it
  matters.
- **Conflict of interest, disclosed.** This review was produced by the AI
  assistant that ran the analyses and drafted this short version. It is a
  self-review, so it is not independent, and it is likely to miss
  problems the drafter could not see. Treat it as a pre-submission check.
  An independent human reviewer, or at least a separate model with no
  access to the project history, should review before submission.
- **Competence limits:** none for the statistics used (AUROC, paired
  bootstrap, Holm, label-shift estimation). No specialist review needed.
- **Target venue:** not chosen. Venue-specific requirements (page limits,
  double-blind rules, AI-use policy) are therefore checked only against
  general IEEE policy.

## 1. Neutral map

| Element | In this paper |
|---|---|
| Question | Which signals rank failures of a chained typed-decision workflow, and do they find the reviews that reduce cost? |
| System | Jev 1.13 (TypeSafe API) and four comparison models behind the same interface; a three-step triage workflow (`choice` → `noul` → `score`) plus an action rule *F* |
| Units | Bug or issue reports (442 development, 500 held-out Bugzilla bugs; 500 + 582 Kubernetes issues) |
| Design | Exploratory development phase, then pre-registered prediction tests (held-out, cross-model, Kubernetes) and a pre-registered cost test |
| Predictors compared | Final-step confidence vs. action-rule score *r(a)* and a decision-feature estimator *E*<sub>dec</sub> |
| Outcomes | AUROC for ranking failures (*a* ≠ *a*\*); total cost at a 10% review budget under a frozen matrix |
| Principal claims | (C1) decisions beat confidence for ranking failures; (C2) the signal is mostly the action error rate; (C3) the error rates depend on the label mix; (C4) it replicates on Kubernetes and across models; (C5) no review policy beat no review |

**Applicable reporting guidance:** TRIPOD+AI is the closest fit, since
the paper evaluates the discrimination of failure-prediction models. The
items most relevant here are:
- intended use and prediction time;
- leakage between development and evaluation;
- calibration as well as discrimination;
- uncertainty around performance;
- availability of model and code.

This is used as a prompt, not a score.

## 2. Claim–evidence matrix

| ID | Claim (location) | Evidence | Alignment | Issue |
|---|---|---|---|---|
| C1 | The decision estimator ranks failures better than final-step confidence (Abstract; §V; Fig. 4) | HR1: 0.763 vs. 0.549, +0.214, one-sided lower bound +0.158; 8/8 cross-model tests | Strong for the stated target | The comparator is weak and partly favoured by construction (M2). "Failure" means disagreement with a constructed target (M1) |
| C2 | Most of the signal is the action's error rate (Abstract; §VI) | For Jev the estimator adds +0.000 [−0.012, +0.011] over *r(a)*; *r(a)* matches the estimator for Jev and OpenJev | Supported for Jev-style models | "Most" is fair for those models; Qwen2.5 and OLMo-2 gain +0.035 and +0.057 |
| C3 | Error rates do not transfer across label mixes (Abstract; §VI; Table IV) | Dev-fit AUROC 0.28 on severity errors; re-weighting repairs it | Directionally supported | Exploratory, no intervals in the text, and not labelled exploratory in the prose (M6) |
| C4 | Replicates on Kubernetes and for three of four further models (Abstract; §VII; Table V) | Jev 0.776 vs. 0.628, +0.148 [+0.091, +0.207]; Table V | Supported for Jev and OpenJev | Two of the three "supporting" comparison models are below chance on a step; the competence criterion is post hoc and **not labelled as such in this version** (M4) |
| C5 | Better ranking did not reduce cost; no 10% policy beat no review (Abstract; §VIII; Fig. 5) | Jev 658 no review vs. 681–714 with review; 2/10 tests supported | Supported under one frozen cost matrix | Reverses at m = 2 or h = 0.5 (Table VI); no intervals on cost differences; the title generalises beyond one matrix (M5) |
| C6 | Novelty: "We found no prior work that tests…" (§II, last paragraph) | None in this version | **Not supported as written** | The search method and its limits, disclosed in the full version, were dropped here (M3) |
| C7 | "Practitioners often assume" confidence can be combined (§I, ¶1) | No citation | **Not supported** | Vague attribution (m1) |

## 3. Major comments

**M1. The failure label is a constructed target, and the abstract and
conclusion do not say how weak its validation is.**
- **Location:** Abstract; §XI Conclusion; §III ("Action, target and
  failure"); §X.
- **Observation:** every result depends on *a*\* = *F*(reference labels).
  The only validity check is an AI-judge pilot at about chance (κ between
  −0.157 and +0.015, §X). The Conclusion nonetheless says the workflow's
  decisions "predicted its failures far better", with no qualifier.
- **Evidence or criterion:** claim–evidence alignment. Abstract and
  conclusion claims should carry material caveats.
- **Why it matters:** a reader will take "failure" to mean a wrong
  decision. The paper has not shown that it is one.
- **Requested action:** in the abstract and the first Conclusion
  sentence, say "disagreement with a label-derived target action". Add
  one sentence to the abstract noting that the target is unvalidated.
  Running the pre-registered two-human validation would turn the paper's
  largest weakness into evidence.

**M2. The main comparator is weak, and the comparison partly favours the
action-rule score by construction.**
- **Location:** §III ("Failure signals"); §V; §VI (paragraph beginning
  "Most of this signal…"); Fig. 4.
- **Observation:** the action and the target are produced by the same
  rule *F*. *r(a)* is therefore close to a per-class error rate on the
  model's own predicted class. Final-step confidence is the confidence of
  one node only. The paper itself says "part of this is built in".
- **Evidence or criterion:** analysis–question alignment. A comparison
  between signals should give each a fair representation of the quantity
  being predicted.
- **Why it matters:** "decisions beat confidence" may reflect the choice
  of comparator rather than a property of the models. Reviewers in
  calibration and selective prediction will raise this first.
- **Requested action:** add at least one stronger confidence-based
  baseline, namely the model-implied probability that the chosen action
  is correct. It can be computed from the `score` distribution and the
  `noul` probability through *F*. Also report AUROC within each action
  (§VIII already shows about 0.49 within accepts for Jev). If decisions
  still win, the claim becomes much harder to dismiss. If not, narrow the
  claim to "single-node confidence".

**M3. The novelty claim is broader than the evidence given in this
version.**
- **Location:** §II, last paragraph; §I ("The contribution is
  methodological"); Table I.
- **Observation:** "We found no prior work that tests…" appears with no
  description of the search. The full version states that the search was
  web-based and did not systematically cover reliability engineering or
  HCI; that caveat was cut. Each element in Table I (pre-registration,
  budgeted cost evaluation, label-shift correction) is standard on its
  own, and Park et al. [14] already argue that error risk and review value
  differ.
- **Evidence or criterion:** a novelty claim must not be broader than the
  search and cited literature support.
- **Why it matters:** an unqualified priority claim invites a reviewer to
  name one counterexample and discount the paper.
- **Requested action:** restore one sentence on the search and its
  limits. Frame the novelty as the combination and the empirical test
  ("to our knowledge, this combination has not been tested on…"), and
  state plainly that the risk-versus-value distinction itself comes from
  [14].

**M4. The Kubernetes cross-model result relies on a post hoc competence
check that this version does not label as post hoc.**
- **Location:** §VII, second paragraph; Table V; Abstract ("including the
  only other one competent at every step").
- **Observation:** the pre-registered rule (at least 3 of 4 models)
  passes, but two of the three supporting comparison models are below
  chance on priority (Table V: 0.082 and 0.270 against 0.33). The
  "competent at every step" criterion was introduced after the results
  were seen. The full version and the protocol amendment say so; this
  version does not.
- **Evidence or criterion:** transparent labelling of confirmatory and
  exploratory analyses.
- **Why it matters:** without the label, a reader may assume the
  competence split was planned. Unlabelled post hoc analyses are a common
  ground for rejection.
- **Requested action:** add "(defined after the results were seen and
  applied to every model)" where competence is introduced. In Table V,
  separate Jev's row, which comes from a different pre-registration, from
  the four comparison models. Consider stating that the evidence from
  competent models is two related systems (OpenJev is trained to Jev's
  interface).

**M5. The cost conclusion is fragile, and the title generalises it.**
- **Location:** Title; Abstract (last two sentences); §VIII; Fig. 5;
  Table VI.
- **Observation:** "no 10% review policy beat no review" holds under one
  constructed cost matrix with perfect reviewers. Table VI shows review
  paying for three models at m = 2 or h = 0.5. No uncertainty is reported
  for the cost differences in the text or in Fig. 5. The cost test was
  also pre-registered after the prediction results on the same bugs were
  known (§X).
- **Evidence or criterion:** effect estimates need uncertainty, and
  conclusions should not extrapolate beyond the analysed conditions.
- **Why it matters:** the title states a general truth ("Predicting
  failures is not knowing which reviews pay"). The evidence supports a
  conditional one.
- **Requested action:** report intervals for the main cost contrasts (the
  full version has them for the pre-registered tests). In the abstract,
  say "under the pre-registered cost matrix" and "with perfect
  reviewers". Consider a less absolute title, or a subtitle naming the
  setting.

**M6. Uncertainty and exploratory status are reported unevenly.**
- **Location:** §IV (all AUROCs); §V (HR2 values without lower bounds);
  §VI (0.64–0.76, 0.28, 0.79, 0.74 without intervals); Table V (no CIs);
  Fig. 5 (no uncertainty).
- **Observation:** many headline numbers are point estimates. The
  label-shift results in §VI are exploratory, but the prose presents them
  next to confirmatory results without saying so; only the Table IV
  caption does.
- **Evidence or criterion:** estimates should carry intervals, and
  exploratory analyses should be labelled where they are reported.
- **Why it matters:** readers cannot judge precision, and the RQ2 answer
  reads as confirmed when it is not.
- **Requested action:** add intervals at least to Table V and to the key
  §VI numbers. Open the RQ2 paragraph with "In exploratory analyses…".
  State that the one pre-registered RQ2 test, the Kubernetes BBSE test,
  was inconclusive with a negative estimate.

**M7. There is no data, code or pre-registration availability
statement.**
- **Location:** whole paper. The appendices, including Reproducibility
  and Data provenance, were removed in this version.
- **Observation:** the paper says that estimators were "hash-frozen" and
  protocols pre-registered, but gives no repository, commit, DOI or
  timestamps. It also omits serving details for the open models and
  states no funding or conflict-of-interest information.
- **Evidence or criterion:** reproducibility and transparency, and the
  TRIPOD+AI availability items.
- **Why it matters:** the pre-registration is the paper's main
  methodological strength, and readers cannot check it. Reliance on a
  proprietary API (jev-1.13.0) also limits replication.
- **Requested action:** add a short "Data and code availability"
  paragraph with the repository URL and commit, where the
  pre-registrations live and how their dates can be verified, the open
  model versions, and the API-dependence caveat. Add a funding and
  conflicts sentence, for example who paid for API and GPU use, and
  whether any author is affiliated with TypeSafe.

## 4. Minor comments

- **m1.** §I, ¶1: "Practitioners often assume…" has no source. Cite one,
  or rephrase as "A natural design is to combine…".
- **m2.** §VI, first paragraph: "We picked small open models because they
  … make more mistakes" reads as choosing models to suit the result.
  Rephrase: weaker models produce more failures, which gives the
  predictors more positives to rank.
- **m3.** §III: the development set was quota-sampled by severity while
  the held-out set used the natural mix. This is central to RQ2 but first
  appears in §VI. Move it to "Data and workflow".
- **m4.** Fig. 4 caption: "For all five models" omits that the intervals
  overlap for OLMo-2, as the full version says. Add it.
- **m5.** §V: give the HR2 one-sided lower bounds (0.762 and 0.648), as
  for HR1.
- **m6.** §III: for the open models the three repeats are identical
  (deterministic inference), so repeat-instability plays no role for
  them. State this once, since it means the workflow is not identical
  across models.
- **m7.** Table V: define "Priority acc." and the chance level in the
  caption (it is there), and note that it is a test-set accuracy.
- **m8.** The action-rule score takes only 3–4 distinct values, so AUROC
  involves heavy ties. Note this, and how ties are broken when ranking a
  fixed review budget.
- **m9.** §II: most cited Jev papers are 2026 preprints. One sentence
  noting that this literature is new and largely un-refereed sets
  expectations, as the full version did.
- **m10.** §IX: the audit lessons are useful but read as process
  narrative. In a short version, consider cutting this section to one
  sentence in §X, to make room for M2 and M7.

## 5. Strengths, to keep

- Clear separation of the two questions, ranking failures and finding the
  reviews that pay, with an oracle bound that shows where the value lies.
- Pre-registered, hash-frozen confirmatory tests, with an independent
  recomputation of the held-out result.
- A genuinely independent replication: different platform and labelling
  process, chronological split, label-leak removal.
- Candid reporting of negative and inconclusive results: the BBSE failure
  on Kubernetes, the stopped case-level study, and the near-chance AI-judge
  pilot.
- A good architecture figure (Fig. 1) and a compact novelty table.

## 6. Ethics and integrity

- AI assistance is disclosed in the acknowledgment, consistent with IEEE
  policy. Keep it.
- Data are public bug reports, privacy-scrubbed as stated. Confirm that
  redistributing report text, if planned, is permitted by the trackers'
  terms; the full version says texts are regenerated, not redistributed.
- No integrity concerns found.

## 7. Priority order for revision

1. M1 and M5: qualify the abstract, conclusion and title.
2. M4 and M6: label the post hoc and exploratory analyses; add intervals.
3. M7: add the availability, funding and conflicts statement.
4. M2: add the model-implied action-probability baseline. This is the
   one new analysis; it needs no new model calls.
5. M3 and the minor comments.

M1, M3 to M7 and the minor comments are wording or reporting changes.
M2 needs a small re-analysis of existing outputs.

---

## 8. Resolution log (2026-11-08)

| Comment | What was done |
|---|---|
| M1 | Abstract says the target is not validated against human judgment. The intro summary and Conclusion say "measured against / disagreement with a label-derived target" |
| M2 | New exploratory baseline (plan `cfb686d`, committed before computing; results in `research/results/implied_probability_baseline.*`): the model's own probabilities passed through *F*. The rule beats it for 4/5 models (Jev +0.228 [+0.158, +0.297]; not OLMo-2), and it adds nothing over final-step confidence. Reported in §VI. Within accepts it is a weak post hoc signal (Jev 0.596 [0.508, 0.682]), reported in §VIII |
| M3 | Contribution reframed as a combination; Park et al. credited; search method and limits restored before the novelty sentence |
| M4 | Competence check labelled "defined after seeing the results, applied to every model"; OpenJev noted as related to Jev; Jev's row separated in Table V, whose caption names both pre-registrations |
| M5 | Abstract and §VIII state "pre-registered cost matrix, with reviewers assumed correct". Pre-registered cost contrasts given with intervals; the review-vs-no-review comparison marked descriptive. **Title left unchanged:** this is the authors' call, and the full version shares it |
| M6 | Intervals added in §IV, §V (HR2 lower bounds), Table V (differences with CIs) and the Kubernetes BBSE test. RQ2 marked exploratory, and the pre-registered RQ2 test reported as inconclusive with a negative estimate |
| M7 | "Data and code availability" section added. **Funding and competing interests left as a red placeholder:** the authors must supply them (not known to the drafter) |
| m1–m9 | Done (m1 rephrased; m2 rephrased; m3 quota sampling in §III; m4 OLMo-2 overlap in Fig. 4 caption; m5 HR2 bounds; m6 deterministic repeats; m7 caption; m8 ties; m9 2026 preprints) |
| m10 | §IX removed; its key sentence moved into Threats to validity |

**Checks:** 7 pages, no overflowing lines or broken references. All 241
numbers in the short version trace to the full paper or a committed
results file.
