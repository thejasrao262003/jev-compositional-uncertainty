# Step 0B Design Specification (Revision 3)

Status: **design only — not executed, not approved to execute.** Revision
3, responding point-by-point to a review of Revision 2 (which itself was
confirmed, on inspection, to already contain the near-majority condition,
opaque IDs, H2a/H2b gate, and three-stage budget the review asked to
verify — that review was working from a stale paste, not the actual file;
the full Revision 2 text is reproduced faithfully below with Revision 3's
additions layered in, not a silent rewrite). Nothing below should be run
without explicit sign-off.

## Changelog from Revision 2 (this revision)

- **Stage 0's scope formally limited to two of three possible questions**
  (construction feasibility, output feasibility — not hypothesis
  evidence), with an explicit prohibition on Stage 0 silently modifying
  Stage 1 item labels, inclusion criteria, hypotheses, estimands, or
  allocation after seeing outputs (§0).
- **Stage 0 pass/fail criteria rewritten from a fixed threshold
  (confidence < 0.95) to a responsiveness/feasibility criterion** (output
  varies across conditions at all) — avoids the failure mode of "forcing
  the API to behave according to the hypothesis" (§11).
- **Near-majority conditions' cross-primitive non-comparability stated
  explicitly** — 3:2 (`choice`/`noul`) and 2:1 (`score`) are not claimed
  equivalent manipulations (§11).
- **Small-sample interpretation rules added**, including the specific
  distinction between "not distinguishable from no relationship" and
  "evidence of no relationship," and a rule against generalizing an n≈30
  positive correlation into a calibration claim (§8A).
- **"No retroactive ground truth from observed decisions" added as its own
  explicit rule**, distinct from "no post-hoc reclassification" (§4).
- **Item-type × analysis-type eligibility table added** (§4), making
  explicit which item categories feed which analyses.
- **§15 (new): pre-flight static validation checklist**, plus an
  accompanying validator script
  (`../src/validate_step0b_manifest.py`) that checks a machine-readable
  item manifest against this checklist before any Stage 0 call is made.

## Changelog from Revision 1 (carried forward)

Fixes for all 7 critical issues and the "must fix" list from review,
**plus one new critical issue this revision surfaced while fixing #1 and
#3** (not something review named directly, but a direct consequence of
trying to satisfy both at once — flagged here rather than quietly patched):

- **New issue found: the ground-truth rule and the spread-producing ratio
  were mutually exclusive.** §4's original rule made *only* exactly-tied
  compositions (2:2 for `choice`, 1-sentence-vs-1-sentence mixes for
  `score`) "contested"/ground-truth-undefined — and Step 0A.1/0A.2 found
  that *only* those same tied compositions reliably produce non-saturated
  confidence (3:1 already saturates). That means, as originally designed,
  **every item with defined ground truth would have been expected to
  return confidence≈1.0**, making H1 nearly untestable by construction.
  Fixed in §3/§4 with a new "near-majority" condition (5-sentence items,
  3:2 ratio) that has a defined majority (so ground truth is valid) while
  being closer to the boundary than the 3:1 ratio already known to
  saturate — whether this actually produces spread is *itself* now an
  explicit Stage 0 validation question (§3, §11), not assumed.
- **Bug fixed: canonical-ordering keys were not content-blind.** Revision
  1's canonical rule ("sort sentence-pool keys lexicographically") used
  keys like `N1`/`D1` that encode the semantic category — lexicographic
  sort would then systematically order all `database`-labeled sentences
  before all `network`-labeled ones (`D` < `N`), confounding "canonical
  order" with content category. Fixed in §5: opaque, content-blind sentence
  IDs, assigned independently of semantic label.
- `noul`'s confidence analogue is no longer assumed — split into a gated
  **H2a (semantic/decision validation)** and **H2b (reliability
  hypothesis)**, with H2b only evaluated if H2a passes (§1, §11 Stage 0).
- Primitive-specific correctness/calibration targets defined explicitly
  (§8A) instead of treating `choice`/`score`/`noul` as interchangeable.
- H4 now has a prespecified, output-independent boundary formula, strata,
  and descriptive (not inferential) analysis plan (§8B).
- Complete-cell rules added: `m<3` and `k<3` cells are excluded from
  primary instability/sensitivity summaries and reported separately in a
  missingness report, never silently pooled with complete cells (§10).
- Budget restructured into three distinct stages — **Stage 0
  construction-validation pilot** (≈28 calls, own pass/fail gates, kept
  entirely out of the confirmatory sample), **Stage 1 main run**
  (provisional pending Stage 0), and a **narrowly-scoped operational
  reserve** (technical failures only, fixed replacement rule, no content
  or hypothesis changes) (§11).
- H5 downgraded to explicitly exploratory/descriptive only — no condition
  list implying a controlled test at n=30 (§1, §3, §9).
- Ground truth relabeled **"construction-defined reference label"**
  throughout, with an explicit equal-evidential-weight-by-construction
  statement (§4).
- Primary reporting language narrowed to avoid "Jev is calibrated"-style
  conclusions; a hedged reporting template is specified (§8A, §9).
- Cross-primitive comparison split into within-primitive and
  cross-primitive-descriptive categories; no combined "reliability score"
  (§8A, §9).
- §14 expanded with an explicit list of what the robustness-subset design
  can and cannot estimate (previously implicit).
- Per-primitive/per-domain allocation table added (§3).

## 0. Stage structure (new, read this first)

This revision runs in three stages, not one:

- **Stage 0 — construction-validation pilot** (§3, §11): validates (a)
  `noul`'s matched-pool method and confidence-analogue semantics (gates
  H2a), and (b) whether the new "near-majority" ratio condition actually
  produces non-saturated confidence for `choice`/`score` while keeping
  valid ground truth. Small, separate budget, own pass/fail criteria,
  **results never merged into the confirmatory Stage 1 sample.**
- **Stage 1 — main run** (§3, §6, §7, §11): the primary/robustness/repeat
  data collection, sized in §11 but **provisional on Stage 0's outcome** —
  if the near-majority condition fails validation, Stage 1's `choice`/
  `score` allocation is redesigned (not silently patched) before running,
  and if `noul`'s H2a fails, `noul` is characterized separately rather
  than folded into the H1/H2b comparative analysis.
- **Operational reserve** (§11): technical-failure replacement only,
  fixed rules, decided now, no content or hypothesis changes permitted.

**Stage 0's scope is strictly limited to two of three possible questions,
stated explicitly (Revision 3):**

1. **Construction feasibility** — does the item-generation procedure
   produce valid, non-degenerate items (well-formed requests, schema-valid
   responses, a defensible reference label where one is claimed)? *Stage 0
   checks this.*
2. **Output feasibility** — does Jev exhibit any measurable responsiveness
   to the manipulated variable in the near-majority/H2a conditions, as
   opposed to collapsing deterministically to the same saturated output
   regardless of composition? *Stage 0 checks this.*
3. **Hypothesis evidence** — whether confidence relates to correctness
   (H1/H2b). *Stage 0 does NOT check this — that is Stage 1's job, at a
   sample size actually intended to speak to it.*

> **Stage 0 may determine whether the preregistered construction is
> feasible. It may not modify Stage 1 item labels, inclusion criteria,
> hypotheses, primary estimands, or allocation after observing Jev
> outputs.** A failed feasibility check justifies *stopping* (reporting a
> primitive as not-testable-this-way, §0 changelog) or *redesigning before
> any further calls are made* (a new, separately-reviewed Stage 0 run) —
> never a silent in-flight patch followed immediately by Stage 1 execution
> on the same review cycle.

## 1. Research questions and hypotheses

**Primary RQ:** does Jev's reported confidence/probabilities relate to
empirical correctness across `choice`, `score`, and (contingent on H2a)
`noul`, under a fixed canonical presentation, and how does that
relationship differ across the three primitives?

**Secondary RQs:** (a) does presentation-sensitivity persist across
independently constructed evidence pools and across primitives? (b) is
decision instability concentrated near a prespecified decision boundary?

**Non-goals** (unchanged from Rev. 1): no workflow composition, no
escalation-policy design/evaluation, no value judgment about whether
Jev's calibration is "good."

**Hypotheses**, now explicitly tiered by confirmatory/exploratory status:

- **H1 (confirmatory, contingent on Stage 0):** for `choice` and `score`,
  on canonical-presentation, non-contested items, higher confidence is
  associated with higher empirical correctness. **Contingent**: this is
  only testable with meaningful confidence variance if Stage 0 confirms
  the near-majority condition (§3) produces non-saturated confidence on
  ground-truthed items. If Stage 0 shows it does not, H1 is reported as
  *not testable at this sample's achievable confidence range* rather than
  forced through on a near-degenerate confidence distribution — itself a
  reportable finding (§0 changelog).
- **H2a (confirmatory gate, `noul`, Stage 0 only):** before any reliability
  claim about `noul`, establish: (i) the returned value's documented
  interpretation ("probability the answer is yes," per
  `../jev_api_notes.md`) is consistent with observed behavior; (ii) 0.5 is
  used as the decision threshold **because it is the documented natural
  midpoint of a stated probability, not because it was fit to data**;
  (iii) the value moves in an interpretable direction under controlled
  evidence (more "yes"-supporting sentences → value closer to 1); (iv) a
  binary decision rule (`noul ≥ 0.5 → yes`) can be and is specified before
  seeing Stage 1 data. **All four must pass for H2b to proceed.**
- **H2b (confirmatory, gated on H2a):** among non-contested `noul` items,
  the value's distance from 0.5 is associated with empirical correctness,
  evaluated identically to H1's rank-correlation/reliability-diagram
  approach. Not evaluated at all if H2a fails; `noul` is then reported via
  characterization only (§9).
- **H3 (exploratory):** the presentation-sensitivity effect (Step 0A.2,
  one pool) recurs in ≥1 other independently constructed pool, for ≥1
  primitive. Reported as recurrence-or-not per pool, not pooled into a
  single effect size (small-sample descriptive, per review).
- **H4 (descriptive, not inferential — see §8B):** decision instability is
  higher in a prespecified near-boundary stratum than a prespecified
  saturated stratum. Reported as stratum-level descriptive statistics with
  uncertainty intervals, explicitly **not** claimed as a general
  boundary-instability law (sample size does not support that).
- **H5 (exploratory/descriptive only — downgraded from Rev. 1):** `score`
  may track the highest-severity sentence present rather than averaging.
  **This study cannot distinguish** maximum-dominance from threshold
  behavior, wording effects, or interaction effects (per review) — Step
  0B reports item-level `score`/`probabilities`/composition/order/repeat
  data descriptively (mean implied severity vs. max implied severity as
  competing summaries) and explicitly does **not** claim H5 as tested. A
  controlled follow-up (review's "Option 2") is deferred to a later,
  dedicated study.

## 2. Unit of analysis

Unchanged in structure from Rev. 1, with Stage 0 added as its own unit:

- **Stage 0 unit:** one *(condition, domain=1, repeat)* call, per
  primitive, evaluated against pass/fail criteria (§11), never entering
  the Stage 1 dataset.
- **Stage 1 primary layer:** one *item* = one canonical-presentation call.
- **Stage 1 robustness subset:** one *(item, presentation)* pair.
- **Stage 1 repeatability subset:** one *(item, repeat index)* triple.
- No call's outcome decides whether another call happens, at any stage or
  layer — all subset membership is fixed before data collection.

## 3. Evidence-pool construction procedure

**Content-blind opaque sentence IDs, mandatory** (fixes the lexicographic-
ordering bug in §0): every sentence in every pool gets an ID assigned
independently of its semantic label (e.g. a preregistered random
permutation over `s01, s02, ...`, not `N1`/`D1`-style category-encoding
keys). The mapping from opaque ID → (semantic label, sentence text) is
recorded in the item spec but never used to derive presentation order.

**Two independently constructed domains per primitive**, each with its
own sentence pool, per Stage 0's request for content-variability coverage.

**New "near-majority" condition, pending Stage 0 validation:**
`choice`/`noul` items use **5-sentence** pools (not 4), so that a 3:2 split
has a defined majority (valid ground truth, §4) while being numerically
closer to tied than the 3:1-out-of-4 ratio Step 0A.1 found already
saturates. `score`'s analogous condition: 2 sentences at one level + 1
sentence at an adjacent level (a 2:1 majority, same logic). **Whether 3:2
(or 2:1) actually produces non-saturated confidence is unknown and is
exactly what Stage 0 tests** — it is not assumed to work just because it
sounds closer to the boundary.

### Per-primitive, per-domain allocation (Stage 1, provisional pending Stage 0)

15 items per domain × 2 domains = 30 items/primitive, split as:

| Condition | Ratio/composition | n/domain | Ground truth | Purpose |
|---|---|---|---|---|
| Clear anchor | 5:0 (`choice`/`noul`) or pure-level ×2 sentences (`score`) | 3 | Defined | Sanity check; expected saturated, per Step 0A.1/0A.2 |
| Moderate anchor | 4:1 (`choice`/`noul`) or n/a for `score` | 3 | Defined | Confirms the known-saturating ratio still saturates here too |
| **Near-majority (key new condition)** | 3:2 (`choice`/`noul`) or 2:1 adjacent-level (`score`) | 6 | Defined | Tests whether a ground-truthed item can show non-saturated confidence — Stage 0-gated |
| Contested (tied) | 2:2 (`choice`/`noul`) or 1:1 cross-level mix (`score`) | 3 | **Undefined by rule (§4)** | Presentation-sensitivity/instability analysis only, never accuracy |

`score`'s "moderate anchor" row is not used (no natural 4:1 analogue at 3
severity levels); its 3 slots are redistributed to the near-majority row
(6→9 for `score` specifically), keeping totals at 15/domain. `score`'s
"clear anchor" spans all 3 pure levels across the 3 slots (1 item/level).

**Equal evidential weight, stated explicitly:** every included sentence is
treated as one equally-weighted "vote" toward its labeled target by
construction. This is a simplifying construction rule, **not a claim that
real-world evidence of this kind carries equal reliability** — stated here
so the reference label (§4) is never mistaken for a validated
ground-truth probability.

- **`noul`:** matched-pool construction is new (never tested, even
  narratively-informed, with this method) — built and validated in Stage 0
  before any Stage 1 `noul` item is run.
- **`score`:** reuses Step 0A.2's severity-labeled pool method, extended
  with the near-majority (2:1 adjacent-level) condition, content-blind IDs
  applied retroactively to future pools.

## 4. Ground-truth annotation protocol

Terminology, per review: every label below is a **construction-defined
reference label**, not independently validated real-world truth — stated
alongside "ground truth" throughout, never used alone.

- **Majority-supporting compositions** (5:0, 4:1, 3:2 for `choice`/`noul`;
  pure-level and 2:1-adjacent for `score`): reference label = the
  majority-supported option/level, under the equal-weight assumption
  (§3). A 3:2 composition's reference label reflects the *construction
  rule*, not a claim that the scenario is "75%… no — 60% likely true" in
  any calibrated sense.
- **Tied/contested compositions** (2:2 for `choice`/`noul`; 1:1 cross-level
  mixes for `score`): reference label is **explicitly undefined**.
  Excluded from §8A accuracy/ECE/H1/H2b metrics; retained for §8B/§8C
  instability/sensitivity analyses, where the target is decision
  consistency, not correctness.
- Single-annotator (constructor), not independently human-labeled —
  appropriate for construction-defined synthetic labels; a real limitation
  for generalizing beyond this synthetic setting (unchanged from Rev. 1,
  carried in `../literature/gap_analysis.md`).
- **No post-hoc reclassification.** An item's condition category and
  reference-label status are fixed in the item spec before any Stage 1
  call and never changed after seeing output (explicit rule, per review's
  "strongly recommended" list).
- **No retroactive ground truth from observed decisions (Revision 3,
  explicit rule).** A contested item's reference-label field remains
  `undefined` regardless of what Jev returns for it — Jev's own decision
  on a contested item is never written back into that item's reference
  label, even informally, even for a "let's see what it picked" sanity
  note. This is stated separately from "no post-hoc reclassification"
  above because it is a distinct, easy-to-make mistake: it is not about
  changing an item's *category*, it is about never treating the model's
  output as if it were the missing label for an item whose label was
  deliberately left undefined by construction.

**Item-type × analysis-type eligibility (Revision 3, made explicit per
review):**

| Item type | Correctness/calibration (§8A) | Stability/presentation (§8B-C) |
|---|---|---|
| Clear / moderate anchor (majority, saturated) | Eligible — reference label defined at construction | Eligible |
| Near-majority | Eligible **if** Stage 0 confirms it has a defensible, defined reference label (it does, by construction rule) — its *inclusion in H1/H2b specifically* is further contingent on Stage 0's output-feasibility check (§0, §11) | Eligible |
| Contested / tied | **Excluded** — no single reference label exists | Eligible |
| Failed/incomplete cell | Excluded from the relevant complete-cell analysis (§10) | Reported separately (§10, §13), not silently excluded |

## 5. Canonical presentation policy

- Canonical order = the item's **opaque sentence IDs sorted ascending**
  (content-blind by construction, §3 — fixes the Rev. 1 bug). Verified
  content-blind by construction: opaque IDs are assigned via a
  preregistered random permutation with no relationship to semantic label,
  recorded in the pool spec for audit.
- All Stage-1 primary-layer items are called once, at canonical order.
  §8A metrics use this layer only.

## 6. Robustness-subset sampling procedure (Layer 2)

Unchanged in mechanism from Rev. 1 (preregistered seed, 20% of primary
items, 2 alternate orderings: exact reverse + one seeded shuffle),
**with an explicit scope statement added** (per review item 12, moved from
implicit to stated): this subset estimates *whether* presentation changes
the output for a given item (1 call per alternate presentation) — it does
**not** estimate repeat variability *within* an alternate presentation,
does **not** estimate a presentation × repeat interaction, and **cannot**
say whether an observed alternate-presentation difference exceeds that
alternate presentation's own repeat noise (only canonical order gets
repeats, §7). See §14 for the complete list of what this design cannot
support.

## 7. Repeat allocation policy (Layer 3)

Unchanged in mechanism (same 18-item subset, 2 additional canonical
repeats, output-independent selection). **Complete-cell rule added:**
primary repeat-instability summary statistics (§8B) require all `m=3`
canonical-order calls to have succeeded; any item with `m<3` is excluded
from that summary and reported in a separate missingness table (§10, §13)
rather than having its `S`/`I` computed on a different, incomparable
denominator.

## 8. Exact estimands and formulas

### A. Primary decision quality and calibration — primitive-specific targets (per review item 1 and 10)

| Primitive | Correctness target | Probabilistic-forecast field | Valid metrics |
|---|---|---|---|
| `choice` | Correct discrete option | Selected-class probability `probabilities[choice]`; full distribution available | Accuracy, per-class precision/recall, confusion matrix, multiclass Brier score, classwise reliability diagram, ECE (2 binnings) |
| `score` | Correct severity level | Full `probabilities` distribution over levels (a genuine categorical distribution — validated schema, §Step 0A) | Exact-level accuracy, within-1-level accuracy, multiclass Brier score on the level distribution, level-wise reliability diagram, ECE (2 binnings). **The scalar `score` field (weighted mean) is evaluated separately, via MAE against the reference level — it is a point estimate, not itself treated as a probability.** |
| `noul` | Correct binary proposition | The raw `noul` value, **only if H2a passes** | If H2a passes: accuracy after thresholding at 0.5, MAE against {0,1}, reliability diagram/ECE treating `noul` as a Bernoulli probability, Brier score. If H2a fails: none of these — `noul` is reported via §9's characterization-only path. |

Jev's `confidence` (or, for `noul`, the raw value) is never used as a
ground-truth proxy anywhere — always the thing evaluated, never the label.

**Reporting template (replaces Rev. 1's unqualified "primary outcome"
framing), per primitive, per review item 10:**

1. Total items in the primitive's Stage-1 sample.
2. Non-contested items (§4) — this is the effective n for §8A.
3. Correctly classified count, out of non-contested items.
4. Accuracy with an uncertainty interval (e.g. Wilson/Clopper-Pearson
   given the small n).
5. Output/confidence distribution and saturation rate (fraction at or near
   1.0), reported regardless of H1's testability outcome.
6. Full item-level prediction/correctness table (an appendix, not just a
   summary statistic).
7. Brier score, only where a valid probability interpretation exists per
   the table above.
8. Reliability diagram **with bin counts shown** (per review — a diagram
   with unlabeled tiny bins is visually persuasive but not informative).
9. ECE, both binning schemes, reported as **secondary** descriptive
   evidence alongside the diagram — never the sole calibration conclusion.
10. Rank correlation (confidence vs. correctness), computed **only** if
    the confidence distribution (item 5) shows enough spread to make a
    correlation meaningful — otherwise reported as "not computed,
    insufficient confidence variance" rather than a misleading near-zero
    or undefined correlation.

**Language rule:** conclusions are stated as *"under the construction-
defined benchmark and canonical presentation used in this study, the
observed relationship between the reported uncertainty signal and
correctness was [result]"* — never as "Jev is calibrated" or equivalent
unqualified claims.

**Small-sample interpretation rules (Revision 3, per review item 4),
apply to every metric in this section and in §9:**

- Every reliability diagram, ECE value, Brier score, and rank correlation
  is reported with its item count (and, where computed, bin counts) and
  labeled **descriptive/exploratory** — not a stable population-level
  calibration estimate, given n≈30/primitive split across 2 domains and
  up to 4 conditions.
- **A non-significant or near-zero rank correlation is reported as "not
  distinguishable from no relationship at this sample size," never as
  "evidence of no relationship."** The two are not the same claim, and
  this study is not powered to support the stronger one.
- **A positive rank correlation found at n≈30 synthetic items is reported
  as consistent with H1/H2b at this sample size and in this construction**
  — never generalized to "Jev is calibrated" or extrapolated to
  naturalistic inputs, per the language rule above.
- Two-bin (or any coarse) ECE estimates are never presented as a
  standalone conclusion — always alongside the underlying reliability
  diagram and its bin counts, so a reader can judge how much the ECE
  number is actually resting on.

### B. Repeat instability (Layer 3, `m=3`, complete cells only)

Unchanged formulas: `S(x,p) = max_d [n_d(x,p)/m]`, `I(x,p) = 1-S(x,p)`,
plus flip indicator, distinct-decision count, min/max top probability,
top-two gap per call, fraction disagreeing with the modal decision — all
reported together, never the flip indicator alone (per Rev. 1, retained).

**H4's boundary measure, defined before any Stage 1 data is collected:**

- `choice`/`score`: `g(x) = p_(1)(x) - p_(2)(x)` — the gap between the
  top-two option/level probabilities, computed **from the canonical-
  presentation call only** (not from any repeat or alternate-presentation
  output, so the stratification itself doesn't leak repeat-noise
  information into the grouping variable).
- `noul` (only if H2a passes): `g(x) = |noul_value - 0.5| * 2`, mapped to
  the same [0,1] concentration scale as `g(x)` above.
- **Strata, fixed before data collection**, informed by Step 0A.1/0A.2's
  observed distribution (heavily saturated): **near-boundary** =
  `g(x) < 0.3`; **saturated** = `g(x) > 0.8`; items in between are
  reported but not used for the stratum contrast (avoids an arbitrary
  binary split swallowing a continuous middle).
- **Analysis: descriptive only**, per review — mean and median `I(x,p)`
  per stratum, with a bootstrap confidence interval (appropriate given
  `m=3`'s coarse possible values: 0, 1/3, 2/3), and an explicit statement
  that this is **not** a general boundary-instability law, given the
  sample size. No formal hypothesis test (e.g. no t-test on 3-valued
  discrete data) is performed or implied.

### C. Presentation sensitivity (Layer 2, `k=3`: canonical + 2 alternates, complete cells only)

Unchanged formulas (`D(x)`, top-probability range, max pairwise
difference, label-change flag, modal-decision-consistency check),
**with the complete-cell rule**: primary `D(x)` comparisons require all
`k=3` presentations to have succeeded; incomplete sets are retained as raw
data and reported in a clearly separate "partial presentation sets" table
(§13), not silently combined with complete sets.

### D. Escalation-related metrics (definitions only, unchanged from Rev. 1 — reserved for Phase 9, not computed here)

Risk, coverage, escalation rate, cost, instability capture, missed-
instability rate — same definitions as Rev. 1 §8D.

## 9. Primary and secondary outcomes, tiered by status

- **Confirmatory (contingent on Stage 0 gates):** H1 (`choice`/`score`),
  H2b (`noul`, only if H2a passes).
- **Descriptive, prespecified strata/formulas, not inferential:** H4.
- **Exploratory, recurrence-checking only:** H3.
- **Exploratory/descriptive, explicitly not a controlled test:** H5.
- **Characterization-only (no hypothesis, reported regardless of other
  outcomes):** cross-primitive comparison — split per review item 11 into
  (a) **within-primitive** metrics (accuracy, primitive-appropriate
  calibration, primitive-specific error, primitive-specific instability —
  §8A/§8B, not compared across primitives) and (b) **cross-primitive
  descriptive properties only** (output range, saturation frequency under
  a common `g(x)`-based definition, presentation-sensitivity recurrence,
  repeat-induced decision changes where a comparable decision rule
  exists). **No combined cross-primitive "reliability score" or ranking is
  computed or reported** — preserving the primitives' representational
  differences is part of the scientific contribution
  (`../literature/gap_analysis.md` Candidate 3), not a limitation to
  paper over with a single number.

## 10. Missing-call and invalid-response handling

Unchanged retry/logging mechanism from Rev. 1, with the complete-cell
distinction now explicit:

- Failed calls excluded from all metrics for that specific cell, logged in
  `failed_calls`, never imputed (unchanged).
- **Complete-cell requirement, new:** `m<3` (Layer 3) or `k<3` (Layer 2)
  cells are **excluded from the primary §8B/§8C summaries** and instead
  populate a **separate missingness and execution-quality report** (§13)
  — an instability statistic computed on 2 calls is not comparable to one
  computed on 3 (per review item 5's worked example), so they are never
  pooled.
- If an item's canonical call fails irrecoverably, the item is excluded
  from Layer 1 entirely and counted in the missingness report.

## 11. Budget, in three separated stages (per review item 6)

### Stage 0 — construction-validation pilot (≈28 calls, own gate, excluded from confirmatory sample)

**Pass/fail criteria, revised (per review item 1) to test feasibility and
responsiveness, not a specific expected mean/variance** — the point is
whether the design is informative and interpretable at all, not whether
the API confirms H1/H2 in advance:

| Component | Calls | Construction feasibility (must pass) | Output feasibility (must pass) |
|---|---|---|---|
| `noul` matched-pool + H2a | 8 | All requests schema-valid; reference labels well-defined for 5:0/4:1/3:2 (majority conditions); documented "probability of yes" interpretation not contradicted by any response (e.g. no value outside [0,1], no response inconsistent with the stated direction on the two unambiguous 5:0 anchors). | The returned value is **not identical across all four conditions** (5:0, 4:1, 3:2, 2:2) — i.e. Jev's `noul` output responds *at all* to composition changes. No specific target value or gap size is required to pass. |
| `choice` near-majority (3:2) check | 9 (3 items × 3 repeats) | All requests schema-valid; majority reference label well-defined for each of the 3 items. | **Across the 3 items' canonical-call outputs, the top-two probability gap `g(x)` (§8B) is not identical for all three** — i.e. the API is demonstrably responsive to *which* specific 3:2 composition is presented, not collapsing to one fixed saturated output regardless of content. (A finding that all 3 items independently saturate to `g(x)≈1.0` is a construction-feasibility **pass** but an output-feasibility **fail** — a legitimate, reportable result, not grounds to keep trying ratios post hoc.) |
| `score` near-majority (2:1 adjacent) check | 9 | Same structure as `choice`, applied to `score`'s reference-level assignment. | Same responsiveness criterion, applied to `score`'s top-two-level probability gap. |
| **Stage 0 total** | **≈26** | | |

This reframing directly addresses review's caution: a pass here means
"the API is measurably responsive to this manipulation, so a properly
powered Stage 1 could in principle detect a confidence-correctness
relationship" — **not** "the API already shows the relationship we're
hoping to find." Hypothesis evidence (whether that relationship favors
H1/H2) is deliberately out of scope for Stage 0 (§0).

**Cross-primitive comparability, stated explicitly (per review item 3):**
3:2 (`choice`/`noul`, 5 sentences) and 2:1 adjacent-level (`score`, 3
sentences, different severity semantics and level-spacing) are **not**
claimed to be equivalent manipulations of "closeness to the boundary."
Each is held constant only *within* its own primitive's condition set
(same sentence-count/composition logic across that primitive's own
clear/moderate/near-majority/contested rows, §3's allocation table) — never
normalized or compared *across* primitives as if they measured the same
underlying quantity. This is the same reason §9 computes no combined
cross-primitive "reliability score": it would require exactly the kind of
cross-primitive equivalence this design does not establish.

### Stage 1 — main run (provisional, per the allocation table in §3; recomputed if any Stage 0 gate fails)

| Component | Calls | Detail |
|---|---|---|
| Primary layer | 90 | 30 items × 3 primitives, canonical order, 1 call/item |
| Robustness — alternate presentations | 36 | 18 items (20% of 90) × 2 alternate presentations |
| Robustness — canonical repeats | 36 | same 18 items × 2 additional canonical repeats |
| **Stage 1 core total** | **162** | |

### Operational reserve (technical failures only — no content or hypothesis changes, per review item 6)

- ~15% of Stage 1 core (~24 calls), used **exclusively** to replace calls
  that failed irrecoverably (§10) with a **preregistered, fixed
  replacement rule**: the next unused item from the same domain and
  condition category in a preregistered overflow list (generated
  alongside the main item set, before Stage 1 begins) — never a
  freely-chosen substitute, never selected after inspecting any output.
- **Explicitly prohibited uses of reserve calls**, per review: inspecting
  results and modifying item composition, changing canonical ordering,
  adjusting hypotheses, selectively replacing "inconvenient" items, or
  deciding which analyses to retain. Any of these would convert this from
  a preregistered to an adaptive design.

**Grand total, if all Stage 0 gates pass without redesign:** 26 (Stage 0)
+ 162 (Stage 1 core) + 24 (reserve) ≈ **212 calls.** If a Stage 0 gate
fails and a primitive's Stage 1 design is revised, this total changes and
must be resubmitted for review before Stage 1 runs — not silently
recomputed and executed.

## 12. Analysis exclusions and stopping rules

Unchanged core rules from Rev. 1 (contested items excluded from §8A by
rule; no early stopping/adaptive design; pause-and-report triggers for
>20% failure rate, model-version drift, or novel schema mismatches), with
two additions:

- **Stage 0 gates control Stage 1 design, not Stage 1 execution
  mid-stream.** Stage 0 completes and is reviewed in full before any
  Stage 1 call is made — there is no scenario where Stage 1 starts before
  Stage 0's results are known.
- **No post-hoc reclassification of any item's condition category or
  reference-label status** (§4), reiterated here as a stopping-rule-
  adjacent prohibition, not just a labeling convention.

## 13. Planned tables and figures

Unchanged list from Rev. 1, **plus**:

- Missingness and execution-quality report (§10): failed calls, `m<3`/
  `k<3` cells, and incomplete presentation sets, reported separately from
  complete-cell summaries.
- Per-primitive/per-domain allocation table (§3), populated with actual
  vs. planned counts after Stage 0/Stage 1.
- Stage 0 gate-outcome table: pass/fail per primitive/condition, with the
  raw data that produced each verdict.
- Reliability diagrams now specified to include bin counts (§8A item 8).

## 14. Limitations and scope of generalization

Unchanged from Rev. 1 (synthetic/construction-defined reference labels
only; single-annotator; content-variability only partially addressed via
2 domains; order-effect mechanism unidentified; no formal power analysis;
model-version currency caveat), **plus, per review item 12, made explicit
rather than implicit:**

- **What the robustness-subset design cannot estimate:** repeat
  variability within an alternate (non-canonical) presentation;
  presentation × repeat interaction; whether an observed alternate-
  presentation difference exceeds that presentation's own repeat noise (no
  repeats are collected at alternate presentations, only at canonical). A
  full presentation × repeat factorial, as run for one item in Step 0A.2,
  remains a separate, later, mechanism-oriented study, not part of Step
  0B's scope.
- **H1/H2b's testability is contingent, not assumed** (§0, §1) — this
  design does not guarantee a measurable confidence-correctness
  relationship can be estimated; Stage 0 exists specifically to find out
  before committing the Stage 1 budget, and a Stage 0 fail is reported as
  a substantive finding about Jev's decision saturation, not hidden or
  redesigned around silently.
- Reliability diagrams and ECE at this sample size should be read as
  descriptive, not final calibration verdicts — restated here because it
  governs how §9's outcomes should be written up, not just how they're
  computed.

## 15. Pre-flight static validation (Revision 3, new — required before Stage 0)

Per review: verification of the *implementation*, not just the
specification, before a single API call is made. This checklist is
implemented as an automated validator,
`../src/validate_step0b_manifest.py`, which checks a machine-readable item
manifest (one JSON file per stage, generated by a separate, not-yet-built
item-generation script) and produces a pass/fail report. **The validator
exists now and is self-tested against a small dummy manifest (see below);
it has not yet been run against a real Stage 0/Stage 1 manifest, because
those manifests have not been generated yet** — generating them is the
next concrete step, separate from and after this design review.

Checks performed (each maps to one review requirement):

1. Every item has a **unique** opaque ID.
2. Opaque IDs are **not correlated with semantic label** — checked by
   confirming the ID-assignment field in the manifest records a random
   permutation seed (not a deterministic function of label/category
   string), and by confirming no substring of any semantic label appears
   in its corresponding opaque ID.
3. **Canonical order is derivable from opaque IDs alone** — recomputing
   canonical order from the manifest's opaque IDs must match the
   manifest's stored canonical order exactly, with no dependency on any
   other field.
4. **Reference labels are present exactly where the condition category
   requires them** — defined for clear/moderate/near-majority items,
   explicitly `null`/`undefined` for contested items (never silently
   missing, never accidentally populated for a contested item).
5. **Manifests are immutable after creation** — the validator computes and
   records a content hash of each stage's manifest; a later validator run
   against a changed manifest with the same stage ID fails loudly rather
   than silently re-validating a modified file.
6. **Random seeds are recorded** — subset-selection seed (§6/§7) and
   opaque-ID-permutation seed (§3/§5) must both be present in the
   manifest's metadata block.
7. **Robustness/repeat subset membership is fixed** — the selected item
   IDs for Layer 2/3 are stored in the manifest before any Stage 1 call
   and the validator confirms this list's hash matches what a fresh
   re-derivation from the recorded seed would produce (catches manual
   edits to the subset list).
8. **Reserve-call rules are structural, not discretionary** — the
   validator confirms the manifest's overflow-replacement list (§11) is
   itself prespecified (same domain/condition per slot as the item it
   would replace), not an empty placeholder to be filled in during
   execution.
9. Every response-recording code path uses the existing
   `../src/jev_client/` client (which already records the resolved `model`
   field per call, per Step 0A) — checked by confirming the runner script
   imports `JevClient` rather than issuing raw requests.
10. **`noul` thresholding/H2b metrics are code-gated on H2a**: the
    validator checks that the analysis code path computing any `noul`
    accuracy/ECE/Brier metric is conditioned on an explicit `h2a_passed`
    flag read from the Stage 0 gate-outcome record (§13), not hardcoded to
    run unconditionally.
11. **Incomplete cells cannot enter complete-cell aggregates** — the
    validator confirms the analysis code's complete-cell filter
    (`m==3`/`k==3`) is applied before any `S`/`I`/`D(x)` aggregation
    function, by checking that these functions' inputs are pre-filtered
    record sets, not the raw response log.

Checks 9-11 are checks on **analysis code that does not exist yet**
(Step 0B's metrics/analysis scripts are a downstream deliverable, not yet
written) — included here so the checklist is complete and the analysis
code can be validated against it once written, not to claim they are
satisfied today. Checks 1-8 are checks on the **item manifest**, which is
also not yet generated. The validator script below is real and runnable
today against its self-test fixture; it is not yet runnable against real
Step 0B data because that data doesn't exist yet.
