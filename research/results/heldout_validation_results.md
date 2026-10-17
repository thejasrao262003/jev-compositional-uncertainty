# Held-out test of the frozen workflow-risk estimator — results

**Pre-registration:** `research/methodology/workflow_risk_heldout_preregistration.md`
(committed `1c93e74`). The estimator was frozen in `2e2500e`, before any
held-out data existed. The analysis is exactly as pre-registered; nothing
was changed after the smoke test.

**Data:**
- **500 new bugs:** 250 Mozilla and 250 kernel, sampled at each tracker's
  natural mix, with no overlap with the 442 training bugs.
- **4,500 calls:** all HTTP 200 and parsed, `jev-1.13.0` throughout, no
  retries. The smoke test (450 calls) was separate.
- **Files:** `research/data/heldout/heldout_raw_responses.jsonl`;
  analysis in `research/results/heldout_analysis.json`; calibration in
  `heldout_calibration_secondary.json`.

**Failure rate** of the decision-based workflow action: Mozilla 35.2%,
kernel 50.8%.

## Primary results: both supported (Holm, one-sided α = 0.05)

| Hypothesis | Estimate | One-sided 95% bound | Supported |
|---|---|---|---|
| **HR1:** `E_dec` AUROC > low final-step confidence (pooled, stratified) | 0.763 vs 0.549; difference **+0.214** | lower **+0.158** (p < 0.0005) | **Yes** |
| **HR2:** `E_dec` > 0.5 on Mozilla | **0.811** | lower 0.761 | **Yes** |
| **HR2:** `E_dec` > 0.5 on the kernel | **0.697** | lower 0.643 | **Yes** |

The smoke test's reversal (n = 50: 0.67 vs 0.73) did not hold at full
size. The decision to change nothing after it was correct.

## Secondary (descriptive)

**AUROC by estimator:**

| | Mozilla | Kernel | Pooled |
|---|---:|---:|---:|
| `E_dec` (decisions only, primary) | 0.811 | 0.697 | 0.763 |
| `E_all` (decisions + uncertainty signals) | 0.818 | 0.706 | 0.769 |
| Low final-step (`score`) confidence | 0.532 | 0.574 | 0.549 |
| Low minimum confidence | 0.561 | 0.485 | 0.503 |
| Low confidence product | 0.569 | 0.480 | 0.498 |

**Failure rate among the 80% judged safest:**

| | Overall failure rate | `E_dec` | Final-step confidence |
|---|---:|---:|---:|
| Mozilla | 35.2% | **25.5%** | 34.0% |
| Kernel | 50.8% | 47.5% | 46.0% |

**Calibration of `E_dec`'s predicted probability:**
- **The mean is right:** predicted 0.35 vs observed 0.35 on Mozilla, and
  0.51 vs 0.51 on the kernel.
- **The levels are miscalibrated:** ECE 0.20 (Mozilla) and 0.18
  (kernel). Expected, because it was trained on balanced data.
- **The output is coarse:** only 7–8 distinct risk levels, about one per
  decision pattern. Examples at Mozilla's natural mix:
  - the 132 bugs with predicted risk 0.24 fail 11% of the time;
  - bugs predicted at about 0.40 fail 77%;
  - the "defer" pattern, predicted 0.87, fails 62%.

## Reading

1. **Confirmed on new data.** A frozen estimator that knows Jev's
   systematic decision biases predicts when the workflow will be wrong
   (AUROC 0.70–0.81). Confidence aggregates stay at or near chance
   (0.48–0.57). That holds at each tracker's real bug mix, on 500 bugs
   it never saw.
2. **Uncertainty signals neither help nor hurt much on new data**
   (`E_all` − `E_dec` = +0.006 pooled). The probe's suggestion that they
   hurt under shift did not hold. They're simply nearly redundant with
   the decisions.
3. **It ranks better than it acts.** The ranking is strong, but with only
   7–8 risk levels and miscalibrated probabilities, operational gain
   depends on the tracker. Mozilla's failure rate among cases handled
   automatically drops from 35% to 26%; the kernel's barely moves (51% to
   48%), because most kernel risk sits in a few large tied groups.
   Finer-grained risk needs signals beyond the decision pattern, such as
   perturbation sensitivity.

## Limits

- **One model and one setup:** one Jev version (1.13.0), one prompt set,
  one workflow, one domain. Both trackers share them.
- **The target is constructed:** the target action is `F` applied to
  reference labels. Kernel labels are reporters' claims.
- **Prediction, not intervention:** this tests *prediction* only. Whether
  acting on it (verify, retry, escalate) reduces cost at a fixed budget
  is untested (the proposal's H2).
- **Robustness to a new Jev version or other prompts is untested** (H3).
