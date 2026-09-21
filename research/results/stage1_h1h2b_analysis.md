# Stage 1 H1/H2b Formal Statistical Write-up (`choice` + `noul`)

`score` excluded (blocked). Confirmatory analysis on frozen, already-
collected Stage 1 data — no new API calls, no manifest/label changes.
Follows the collaborator-authorized 7-step order, plus a Step 8
supplementary item-level audit table added per review
(`stage1_h1h2b_item_level_audit.csv`, all 48 non-contested items, full
verifiability trail). Full per-step output below.

**Artifact freeze**: `../data/characterization/analysis_freeze_manifest.json`
locks the exact raw-response, manifest, Stage 0 gate, analysis-script, and
item-level-audit-CSV hashes this report rests on, plus the runtime
version and a change-discipline rule (editorial vs. numerical/logic
changes must be distinguished, and any numerical/logic change requires
re-hashing and re-noting this freeze record — never a silent update). No
git commit exists yet to bind these to a source snapshot (repo has no
commits); the artifact hashes are the only binding available until one is
made.

**Terminology, stated once here and repeated in Step 7:** accuracy, rank
association, and calibration (`P(correct|confidence=c) ≈ c`) are three
different properties. Nothing below tests calibration directly — Steps
3–6 produce reliability/confidence-correctness evidence *relevant to* it,
not a calibration test.

- **`choice`**: 18/24 (75%, 95% CI [0.55, 0.88]) accuracy on non-contested
  items. Weak positive rank association (Spearman ρ=0.25, n=24) —
  directionally consistent with H1, but weak. Equal-mass binning surfaces
  a high-confidence subgroup (mean confidence 0.915, observed accuracy
  0.333, n=6) that is also part of the dominant high-confidence region
  under equal-width binning — reflected under both tested partitions *on
  this sample*, but that does not establish the pattern is independent of
  binning choice in general (equal-mass groups are data-dependent, n=6 is
  small). The 6 underlying items are in the audit CSV for independent
  verification. **Hypothesis stance**: descriptive, directionally
  consistent with H1, but confidence ordering and reliability were not
  uniformly aligned in this sample — not general calibration, not a
  dependably useful confidence-based ranking.
- **`noul`**: 24/24 (100%, 95% CI [0.86, 1.00]) accuracy on non-contested
  items. Rank correlation **not computed** — precise stated cause:
  correctness was constant (y=1 for all 24 observations), zero outcome
  variance, undefined correlation (not ρ=0). Every reliability bin shows
  100% observed accuracy while mean confidence was *below* 1.0 in every
  bin (0.19–0.87) — i.e. confidence values were systematically
  **underconfident** relative to the accuracy actually observed, not
  overconfident, and ECE is nonzero (0.2542) despite perfect accuracy.
  **Hypothesis stance, corrected per review**: this establishes perfect
  observed correctness in this sample. It does **not** establish
  calibration (nonzero gaps in every bin) or a positive
  confidence-correctness relationship (undefined here) — accuracy,
  calibration, and discrimination are different properties, and only the
  first is demonstrated.
- **Cross-primitive Brier, unified convention** (`2·(1-p_ref)²`, both
  primitives): `choice` 0.458, `noul` 0.056. **Metric comparability ≠
  experimental comparability** (stated explicitly in Step 5): same formal
  scoring rule, but different item sets, domains, and primitive semantics
  — this gap is descriptive, not evidence that one primitive is
  "better," and is not used to rank the primitives. One-term/native
  values (0.229, 0.028) preserved as audit artifacts only.
- Repeat/presentation subset (12 items): mean S=1.000, mean D=0.333, zero
  flips, zero label changes — stable within this specific 12-item
  subset; not extrapolated further.

```
# Step 1. Frozen analysis input
- raw responses: stage1_raw_responses.jsonl sha256=fca3adcc98b9a9be...
- manifest: stage1_manifest_choice_noul.json sha256=a91700a8e1c62285...
- Stage 0 gate outcomes: stage0_gate_outcomes.json sha256=d219a7d8972c33ed...
- this analysis script: stage1_h1h2b_analysis.py sha256=6d6b5ef36d32033b...
- noul H2a recorded status: pass=True

# Step 2. Scoring-rule definitions (resolved per review)
- `choice` one-term metric (AUDIT ARTIFACT, preserved, NOT used for cross-primitive
  comparison): Brier_1term_i = (1 - probabilities[reference_label])^2, y=1 constant.
- `noul` native metric (AUDIT ARTIFACT, preserved, NOT used for cross-primitive
  comparison): Brier_native_i = (y_i - noul_value)^2, y_i = 1[reference_label=='yes'].
- **NEW, unified, cross-primitive-comparable metric**: for BOTH primitives, define
  p_ref = P(primitive assigns to the reference/correct outcome) - for `choice`,
  probabilities[reference_label]; for `noul`, noul_value if reference=='yes' else
  1-noul_value. Then Brier_unified_i = 2 * (1 - p_ref)^2 (the standard 2-term binary
  Brier score (p-1)^2+(1-p)^2, since y=1 by construction on non-contested items).
  THIS is the only metric compared across primitives below.

# Step 3. Rank correlation (Spearman, confidence-like vs. correctness)
  [choice] n=24, quantity correlated: confidence-like (top-two probability gap) vs. binary correctness (1=selected-decision matches reference_label).
    expected direction (H1/H2b): positive (higher confidence -> higher correctness)
    Spearman rho: 0.252 (n=24 non-contested items out of 30 primary items for this primitive; this measures RANK ASSOCIATION between confidence-like and correctness, NOT a calibration test - P(correct|confidence=c)~=c is a stronger, separate claim this statistic does not address; no significance test performed, n too small for a reliable p-value)
  [noul] n=24, quantity correlated: confidence-like (2*|noul-0.5|) vs. binary correctness (1=selected-decision matches reference_label).
    expected direction (H1/H2b): positive (higher confidence -> higher correctness)
    Spearman rho: NOT COMPUTED - correctness was constant (y_i=1 for all 24 observations, 24/24 correct), producing zero variance and an undefined correlation. This is a precise, stated cause, not a generic 'insufficient data' note.

# Step 4. Reliability summaries (two binning schemes, both with counts, per §8A)
  [choice] n=24
    -- equal-width binning (4 bins) --
      [0.00,0.25)    n=0 (empty bin)
      [0.25,0.50)    n=  1 mean_conf=0.380 obs_acc=1.000 |gap|=0.620
      [0.50,0.75)    n=  3 mean_conf=0.657 obs_acc=0.667 |gap|=0.010
      [0.75,1.00]    n= 20 mean_conf=0.949 obs_acc=0.750 |gap|=0.199
    ECE (equal-width): 0.1933
    -- equal-mass binning (4 rank-groups; ties may straddle a group boundary,
       disclosed limitation at this n) --
      rank-group 1/4 (conf 0.38-0.85)    n=  6 mean_conf=0.672 obs_acc=0.833 |gap|=0.162
      rank-group 2/4 (conf 0.90-0.94)    n=  6 mean_conf=0.915 obs_acc=0.333 |gap|=0.582
      rank-group 3/4 (conf 0.94-0.99)    n=  6 mean_conf=0.972 obs_acc=0.833 |gap|=0.138
      rank-group 4/4 (conf 0.99-1.00)    n=  6 mean_conf=0.998 obs_acc=1.000 |gap|=0.002
    ECE (equal-mass): 0.2208
  [noul] n=24
    -- equal-width binning (4 bins) --
      [0.00,0.25)    n=  2 mean_conf=0.190 obs_acc=1.000 |gap|=0.810
      [0.25,0.50)    n=  2 mean_conf=0.450 obs_acc=1.000 |gap|=0.550
      [0.50,0.75)    n=  4 mean_conf=0.680 obs_acc=1.000 |gap|=0.320
      [0.75,1.00]    n= 16 mean_conf=0.869 obs_acc=1.000 |gap|=0.131
    ECE (equal-width): 0.2542
    -- equal-mass binning (4 rank-groups; ties may straddle a group boundary,
       disclosed limitation at this n) --
      rank-group 1/4 (conf 0.16-0.68)    n=  6 mean_conf=0.437 obs_acc=1.000 |gap|=0.563
      rank-group 2/4 (conf 0.68-0.82)    n=  6 mean_conf=0.753 obs_acc=1.000 |gap|=0.247
      rank-group 3/4 (conf 0.82-0.90)    n=  6 mean_conf=0.853 obs_acc=1.000 |gap|=0.147
      rank-group 4/4 (conf 0.92-0.96)    n=  6 mean_conf=0.940 obs_acc=1.000 |gap|=0.060
    ECE (equal-mass): 0.2542

# Step 5. Scoring metrics (accuracy w/ Wilson CI, all three Brier variants)
  [choice] accuracy: 18/24 = 0.750, 95% Wilson CI [0.551, 0.880] (n=24, small-sample - wide interval expected)
    Brier (unified, cross-primitive-comparable): 0.4577
    Brier (one-term, audit artifact only): 0.2289
  [noul] accuracy: 24/24 = 1.000, 95% Wilson CI [0.862, 1.000] (n=24, small-sample - wide interval expected)
    Brier (unified, cross-primitive-comparable): 0.0557
    Brier (native, audit artifact only): 0.0279

  Metric comparability vs. experimental comparability (per review, stated explicitly):
  the unified Brier score places both primitives on the same formal binary scoring
  convention - that is a mathematical fact. It does NOT make the two numbers evidence
  of one primitive being 'more reliable' than the other, because: (1) different
  primitive semantics (choice vs. noul), (2) different constructed item sets and
  domains, (3) different native uncertainty representations, (4) construction-defined
  (not independently validated) reference labels, and (5) no controlled assignment of
  the same inputs to both primitives. Metric comparability is not experimental
  comparability - the gap between 0.458 and 0.056 below is descriptive, not causal.

# Step 6. Repeat and presentation subsets (12-item subset, NOT extrapolated to full sample)
  repeat instability: 12/12 complete, mean S=1.000, items with any flip: 0/12
  presentation sensitivity: 12/12 complete, mean D=0.333 (D=1/3 per item = stable, see §prior report), items with any label change: 0/12
  This subset (12 of 60 primary items, ~20% per the preregistered sampling rate) is the
  ONLY basis for these two statistics - not generalized to the other 48 items or to
  other evidence pools/domains not tested.

# Step 7. Hedged summary (descriptive observation / statistical association / uncertainty / hypothesis stance)
  Terminology note (per review): 'calibration' below means the formal property
  P(correct|confidence=c) ~= c. Accuracy, rank association, and calibration are three
  DIFFERENT properties - a primitive can show one without the others. None of Step 3-6's
  statistics directly test calibration; they are reliability/confidence-correctness
  evidence relevant to it, not a calibration test.

  [choice]
    Descriptive observation: under the construction-defined benchmark and canonical
    presentation used in this study, choice matched its reference label on 18/24
    non-contested items (95% CI [0.55,0.88]).
    Statistical association: weak positive rank association (Spearman rho=0.25, n=24,
    no significance test performed) - directionally consistent with H1's claimed
    relationship, but weak.
    Reliability pattern: equal-mass binning identified a high-confidence subgroup (rank-
    group 2/4: mean confidence 0.915, observed accuracy 0.333, n=6) with a large gap; this
    subgroup is also part of the dominant high-confidence region under equal-width binning,
    so the pattern is reflected under both tested partitions on THIS sample. This does NOT
    establish the pattern is independent of binning choice in general - equal-mass groups
    are data-dependent, ties can straddle group boundaries, and n=6 in that subgroup is
    small. See stage1_h1h2b_item_level_audit.csv for the underlying 6 items.
    Uncertainty: n=24 is small; Wilson interval is wide; several reliability bins have
    n<=6.
    Hypothesis stance: the positive rank association is directionally consistent with
    H1, but it is weak, uncorrected for multiple comparisons, and co-occurs with a
    high-confidence/low-accuracy subgroup in the same sample - confidence ordering and
    reliability were not uniformly aligned here. The findings are descriptive; they do
    not establish general calibration or a dependably useful confidence-based ranking.

  [noul]
    Descriptive observation: noul matched its reference label on all 24/24 non-contested
    items (95% CI [0.86,1.00]). All four reliability bins (both binning schemes) show
    100% observed accuracy, while mean confidence-like was below 1.0 in every bin
    (0.19-0.87 across bins) - i.e., confidence values were systematically below the
    accuracy actually observed in every bin (underconfidence relative to this sample,
    not overconfidence).
    Statistical association: NOT COMPUTED - correctness was constant (y_i=1 for all 24
    observations), producing zero outcome variance and an undefined correlation.
    Uncertainty: n=24 is small; perfect observed accuracy in a sample of 24 does not
    establish the primitive's general error rate (the Wilson interval's lower bound is
    0.86, not 1.00). The nonzero ECE (0.2542, both binning schemes - identical here
    because the outcome is constant) means confidence-like values did not numerically
    match observed accuracy in any bin, even though every decision was correct.
    Hypothesis stance: the results establish perfect observed correctness within this
    non-contested sample. They do NOT establish calibration (nonzero reliability gaps in
    every bin) or a positive confidence-correctness relationship (undefined at this
    sample's zero outcome variance) - accuracy, calibration, and discrimination are
    different properties, and only the first is demonstrated here.

# Step 8. Supplementary item-level audit table (verifiability, per review)
  Wrote 48 rows (all 48 non-contested choice+noul items, full audit
  trail: item_id, confidence-like, predicted decision, reference label, correctness,
  equal-mass rank-group assignment) to stage1_h1h2b_item_level_audit.csv
```

## Overall conclusion

Across the evaluated construction-defined benchmark, `choice` achieved
18/24 correctness on non-contested items and exhibited a weak positive
association between confidence-like values and correctness. Its
reliability summaries also exposed a high-confidence subgroup with
substantially lower observed accuracy, indicating that confidence
ordering and empirical reliability were not uniformly aligned in this
sample. `noul` achieved 24/24 correctness, but its confidence-like values
remained below observed accuracy across all reliability bins; this
demonstrates sample accuracy rather than calibration. The unified Brier
scores were computed under a common formal binary scoring convention, but
their cross-primitive comparison remains descriptive because the
primitives were evaluated on different constructed item sets and domains.
**None of these findings establishes general calibration, generalization,
or primitive-level superiority.**

## Research implication (scoped)

A workflow cannot safely treat every high-confidence value as
interchangeable evidence of reliability — `choice`'s high-confidence
subgroup with 33% observed accuracy and `noul`'s uniformly-below-accuracy
confidence values are two different, primitive-specific ways that a naive
"trust high confidence" rule would fail here. This motivates, but does
**not** by itself justify, workflow-level questions this study was not
designed to answer: how a workflow should treat high confidence
co-occurring with observed error patterns (`choice`), high accuracy
co-occurring with underconfident scores (`noul`), genuinely different
native uncertainty semantics across primitives, and potentially unstable
or presentation-sensitive outputs outside the 12-item subset tested here.

**This experiment does not establish a workflow-level escalation policy,
and is not presented as doing so.** Per review, the separation between
primitive characterization (this document) and workflow-policy evaluation
(a separately-specified future experiment) is preserved deliberately — no
escalation rule should be derived directly from these small-sample
aggregate results without its own, separately reviewed policy experiment.
