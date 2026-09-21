# Stage 1 Execution Audit (descriptive, protocol-oriented)

**This is the corrected, authoritative report.** Executed
2026-09-21T17:40:31Z. 108/108 calls succeeded (HTTP 200), zero retries,
zero parse failures, single model version (`jev-1.13.0`) throughout.
Manifest hash matched the frozen baseline exactly (`2bf8c78d1f87dcfd...`).
No reserve/overflow items were used.

**Precise wording (per review):** the experimental execution had **zero
deviations** from the preregistered plan. The post-execution audit
separately identified and corrected an **analysis implementation
defect** — these are two different claims and are not conflated here.

**The defect, and the fix:** the first run of `analyze_stage1.py`'s
`compute_repeat_instability`/`compute_presentation_sensitivity` inferred
which items belonged to Layer 2/3 from "any item with a qualifying
record" — which matched all 60 primary items, since every item has a
`primary_canonical` row — rather than reading the manifest's actual
12-item `robustness_repeat_subset_ids`. That produced 48 false
"incomplete" reports and one false "deviation" entry. Fixed by having
both functions take `subset_item_ids` explicitly. **The superseded
output (sections 4 and 8 only, the only sections affected) is preserved
verbatim, clearly labeled, in
`stage1_execution_audit_SUPERSEDED.md`** — not deleted, not silently
replaced. This audit run (below) reflects the corrected code.

Raw/parsed data: `../data/characterization/stage1_{raw,parsed}_responses.jsonl`.
Run metadata: `../data/characterization/stage1_run_metadata.json`.

**Per the agreed protocol, nothing below is an H1/H2b conclusion.**
Section 7 states the exact per-primitive Brier-score probability mapping
and reliability-bin endpoint convention explicitly (per review Checks
A/B/C) before reporting any number, and section 6 states `D(x)`'s
direction explicitly (`D=1/3` means *stable*, one decision across three
presentations — not "33% stable"). The accuracy/Brier/reliability values
below are real, mechanically computed, descriptive results on this
constructed dataset — not yet characterized as evidence for or against
calibration; that interpretation is a separate, later step.

```
======================================================================
1. Call success and schema validation
======================================================================
  total rows: 108
  http status counts: Counter({200: 108})
  rows with error set: 0
  rows with unparsed answer: 0

======================================================================
2. Model-version consistency
======================================================================
  models observed: {'jev-1.13.0': 108}

======================================================================
3. Missingness and replacement accounting
======================================================================
  distinct (item,purpose) cells with purpose != canonical_repeat: 84 (expect 60+12+12=84)
  canonical_repeat calls total: 24 (expect 24)
  overflow/replacement item calls made: 0 (expect 0)

======================================================================
4. Complete-cell eligibility (via analyze_stage1.py, H2a-gated)
======================================================================
  Stage 0 noul H2a recorded status: pass=True
  Layer 2/3 subset size (items designed to receive repeats/alt presentations): 12
  (NOTE: the other 48 primary items were only ever planned to get 1 canonical call each - they are correctly OUT OF SCOPE for this layer, not 'missing'. An earlier version of this audit conflated the two; fixed in analyze_stage1.py before this report was finalized.)
  repeat-instability: 12 complete items, 0 incomplete (expect 12, 0)
  presentation-sensitivity: 12 complete items, 0 incomplete (expect 12, 0)

======================================================================
5. Canonical output summaries (primary_canonical calls only, descriptive)
======================================================================
  [choice] n=30 (contested=6, non-contested=24)
    confidence-like: min=0.380 max=1.000 mean=0.867
    saturation rate (confidence-like >= 0.9): 21/30 = 70.00%
    items by condition: {'clear_5to0': 6, 'moderate_4to1': 6, 'near_majority_3to2': 12, 'contested_2to2': 6}
  [noul] n=30 (contested=6, non-contested=24)
    confidence-like: min=0.040 max=0.960 mean=0.694
    saturation rate (confidence-like >= 0.9): 6/30 = 20.00%
    items by condition: {'clear_5to0': 6, 'moderate_4to1': 6, 'near_majority_3to2': 12, 'contested_2to2': 6}

======================================================================
6. Repeat instability and presentation sensitivity (full results)
======================================================================
  Metric direction, stated explicitly: D(x) = (distinct selected decisions)/k.
  D=1/3=0.333 means ONE distinct decision across all 3 presentations (STABLE),
  not three distinct decisions. D=1.0 would mean maximal diversity (all 3 differed).
  Higher D = more diversity/instability, lower D = more stability. Stated here so
  it isn't misread as '33% stable' or similar.
  This subset is 12 items (of 60 primary items) per the preregistered design -
  results below characterize only this subset, not the full manifest or other pools.
  -- repeat instability (S, I) --
    choice_A_08_near_majority_3to2      S=1.000 I=0.000 flip=False decisions=['application', 'application', 'application']
    choice_A_10_near_majority_3to2      S=1.000 I=0.000 flip=False decisions=['application', 'application', 'application']
    choice_A_12_near_majority_3to2      S=1.000 I=0.000 flip=False decisions=['application', 'application', 'application']
    choice_B_11_near_majority_3to2      S=1.000 I=0.000 flip=False decisions=['billing', 'billing', 'billing']
    choice_B_14_contested_2to2          S=1.000 I=0.000 flip=False decisions=['billing', 'billing', 'billing']
    choice_B_15_contested_2to2          S=1.000 I=0.000 flip=False decisions=['billing', 'billing', 'billing']
    noul_A_01_clear_5to0                S=1.000 I=0.000 flip=False decisions=['yes', 'yes', 'yes']
    noul_A_07_near_majority_3to2        S=1.000 I=0.000 flip=False decisions=['yes', 'yes', 'yes']
    noul_A_14_contested_2to2            S=1.000 I=0.000 flip=False decisions=['yes', 'yes', 'yes']
    noul_B_01_clear_5to0                S=1.000 I=0.000 flip=False decisions=['yes', 'yes', 'yes']
    noul_B_06_moderate_4to1             S=1.000 I=0.000 flip=False decisions=['yes', 'yes', 'yes']
    noul_B_11_near_majority_3to2        S=1.000 I=0.000 flip=False decisions=['yes', 'yes', 'yes']
  -- presentation sensitivity (D) --
    choice_A_08_near_majority_3to2      D=0.333 top_prob_range=0.050 max_pairwise_diff=0.050 label_changes=False
    choice_A_10_near_majority_3to2      D=0.333 top_prob_range=0.010 max_pairwise_diff=0.010 label_changes=False
    choice_A_12_near_majority_3to2      D=0.333 top_prob_range=0.040 max_pairwise_diff=0.040 label_changes=False
    choice_B_11_near_majority_3to2      D=0.333 top_prob_range=0.120 max_pairwise_diff=0.120 label_changes=False
    choice_B_14_contested_2to2          D=0.333 top_prob_range=0.130 max_pairwise_diff=0.130 label_changes=False
    choice_B_15_contested_2to2          D=0.333 top_prob_range=0.150 max_pairwise_diff=0.150 label_changes=False
    noul_A_01_clear_5to0                D=0.333 top_prob_range=0.020 max_pairwise_diff=0.020 label_changes=False
    noul_A_07_near_majority_3to2        D=0.333 top_prob_range=0.080 max_pairwise_diff=0.080 label_changes=False
    noul_A_14_contested_2to2            D=0.333 top_prob_range=0.180 max_pairwise_diff=0.180 label_changes=False
    noul_B_01_clear_5to0                D=0.333 top_prob_range=0.000 max_pairwise_diff=0.000 label_changes=False
    noul_B_06_moderate_4to1             D=0.333 top_prob_range=0.080 max_pairwise_diff=0.080 label_changes=False
    noul_B_11_near_majority_3to2        D=0.333 top_prob_range=0.060 max_pairwise_diff=0.060 label_changes=False

======================================================================
7. Predefined primitive-specific metrics (mechanical computation only -
   NOT an H1/H2b interpretation; that is a separate, later step)
======================================================================
  Per-primitive quantity definitions, stated explicitly before the numbers (per review Check A/C):
  [choice] predicted event = 'the selected/canonical reference_label option is correct'.
           Brier input probability p_i = probabilities[reference_label] (the model's own
           probability mass on the reference option, NOT the top-two gap). y_i = 1 always,
           by construction, since we condition on the reference_label being the target event
           being scored -> Brier_i = (1 - p_i)^2. This is the single-term 'probability of the
           reference class' formulation, NOT summed across both classes (that variant would
           be exactly 2x these values for a 2-option choice) - stated so the two conventions
           are never confused.
  [noul]   predicted event = 'reference_label == yes'. Brier input probability p_i = the raw
           `noul` value directly (native primitive output, NOT a transform). y_i = 1 if
           reference_label=='yes' else 0 -> Brier_i = (y_i - p_i)^2. Standard textbook binary
           Brier score, no simplification needed (noul has only one probability field).
  The 'confidence-like' quantity (top-two gap for choice; 2*|noul-0.5| for noul) is used ONLY
  for the saturation-rate stat above and the reliability-table x-axis below - it is NEVER the
  input to the Brier calculation for either primitive. Pre-specified in step0b_design_specification.md
  §8B (g(x) definition) before this data was collected, not chosen after seeing results.
  Expected direction: higher confidence-like -> expected higher observed accuracy (this is H1/H2b's
  claim, tested here only as a plain bin table, not yet as a correlation statistic or verdict).
  [choice] non-contested n=24, selected-decision == reference_label: 18/24 = 75.00%
    Brier score (definition above, non-contested only): 0.2289 (n=24)
    reliability table (confidence-like -> observed accuracy; bins [0,.25),[.25,.5),[.5,.75),[.75,1.00],
    last bin closed at 1.00, bin counts shown):
      [0.00,0.25): n=0 (empty bin)
      [0.25,0.50): n=1 observed_accuracy=100.00%
      [0.50,0.75): n=3 observed_accuracy=66.67%
      [0.75,1.00]: n=20 observed_accuracy=75.00%
  [noul] non-contested n=24, selected-decision == reference_label: 24/24 = 100.00%
    Brier score (definition above, non-contested only): 0.0279 (n=24)
    reliability table (confidence-like -> observed accuracy; bins [0,.25),[.25,.5),[.5,.75),[.75,1.00],
    last bin closed at 1.00, bin counts shown):
      [0.00,0.25): n=2 observed_accuracy=100.00%
      [0.25,0.50): n=2 observed_accuracy=100.00%
      [0.50,0.75): n=4 observed_accuracy=100.00%
      [0.75,1.00]: n=16 observed_accuracy=100.00%

======================================================================
8. Deviations from the preregistered execution plan
======================================================================
  Deviations found: NONE
```
