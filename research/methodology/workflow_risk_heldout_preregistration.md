# Pre-registration: does a frozen bias-aware risk estimator predict workflow failure on new bugs?

**Status:** pre-registered 2026-10-17, before any held-out data was
collected. No Jev call for this study has been made. Live calls need
separate, explicit authorization.

**Origin.** The exploratory probe (`research/results/workflow_risk_probe.md`)
found that a model trained on *what Jev decided* predicted when the
decision-based workflow action was wrong (AUROC 0.67–0.83, including
across trackers), while confidence aggregates sat at chance. That was
post-hoc. This study tests it on bugs the estimator has never seen.

## 1. The estimator (frozen)

`research/results/frozen_risk_estimator_v1.json`, sha256 `a7c1e2f1a3748cb54f91d14e50e15dc299d39a6b40f4b0f8d654c989945062ce`,
committed in `2e2500e` before any held-out data existed.

- **Training:** all 442 previously collected bugs (202 Mozilla + 240
  kernel). L2 logistic regression, λ = 1, standardized features, with
  the settings fixed in the probe. Trained once; never retrained.
- **Primary, `E_dec`:** decision features only. These are `score`'s modal
  level (0 / 2 / unstable), `noul`'s decision, and the workflow action
  (escalate / defer).
- **Secondary, `E_all`:** decision features plus uncertainty signals
  (confidences, `score` distribution and entropy, `noul` probability and
  spread, stability flags).
- **Risk score:** the linear predictor. The runner verifies the file's
  sha256 before scoring.

## 2. Held-out data (new bugs, natural mix)

- **Sources:** Mozilla and Linux kernel Bugzilla, with the same products,
  components, resolution filters, label mappings and exclusion rules as
  the original studies (§2 of each proposal).
- **No overlap:** every bug in the existing datasets (442) is excluded.
- **Sampling.** **250 bugs per tracker, drawn at random from the full
  eligible pool, at its natural mix of severities and subsystems.** It is
  not balanced per cell. This removes the balanced-design artifact by
  construction: performance is measured at the real bug mix. The seed is
  `heldout-risk-v1`.
- **Unchanged from the original studies:**
  - text cleaning, privacy scrubbing and truncation;
  - the three-step chain, questions, adapter and 3 repeats per step;
  - model `jev-latest`, whose resolution is recorded;
  - no label-wording arm.
- **Calls:** 500 bugs × 3 steps × 3 repeats = **4,500**, preceded by a
  10% smoke test (50 bugs, 450 calls).

## 3. Hypotheses and tests

**Target.** The decision-based action (`F` on the node decisions) differs
from `a* = F(true regression, true level)`.

**HR1 (primary), better than final-step confidence.**
- **Claim:** `E_dec`'s AUROC exceeds the AUROC of *low final-step
  (`score`) confidence*. That is the proposal's main baseline, and the
  strongest confidence baseline in the probe.
- **Statistic:** pooled over both held-out sets, stratified by tracker.
- **Test:** paired bootstrap of the AUROC difference (2,000 resamples of
  bugs within tracker, seed fixed), one-sided.
- **Supported** if the one-sided 95% lower bound of the difference is
  above 0.

**HR2 (primary), better than chance on each tracker.**
- **Claim:** `E_dec`'s AUROC exceeds 0.5 on the Mozilla held-out set and
  on the kernel held-out set, separately.
- **Supported** if each one-sided 95% bootstrap lower bound is above 0.5.

**Multiplicity:** Holm across the three primary tests (HR1 and the two
per-tracker HR2 tests), family-wise α = 0.05, one-sided.

**Secondary (descriptive, no claims):**
- `E_dec` vs low minimum confidence and vs low confidence product;
- `E_all` vs `E_dec`: does adding uncertainty signals help or hurt on new
  data?;
- failure rate among the 80% judged safest, and risk–coverage curves;
- calibration of `E_dec`'s predicted probability: reliability diagram and
  ECE. Note that the training prevalence came from balanced data, so
  miscalibration is expected and is reported, not corrected;
- results per tracker and per severity level.

## 4. Power

- **Probe effect:** differences between `E_dec` and score confidence of
  0.08–0.29 AUROC, with an expected failure rate of about 35–50%.
- **Precision at n = 250 per tracker:** about ±0.06 for AUROC and about
  ±0.07 for a paired difference.
- **Sizing:** HR1 at n = 500 pooled is powered for a difference of about
  0.06 or more.
- **If the real effect is near the low end of the probe's range,** HR1
  may fail. That would be reported as a null, not re-analyzed.

## 5. What would count against the idea

- **HR1 fails:** knowing Jev's decision biases does not beat final-step
  confidence on new bugs. The probe's result would then be attributed to
  in-sample fitting.
- **HR2 fails on one tracker:** the estimator does not transfer to that
  tracker's natural mix.
- **`E_all` < `E_dec` again:** this would support the probe's finding
  that Jev's uncertainty signals hurt under shift.

## 6. Not tested here

- **Interventions (proposal H2):** whether verify, retry or escalate
  actions chosen by `E_dec` reduce cost.
- **Robustness to a new Jev version, other prompts or other domains**
  (proposal H3).
- **Perturbation signals** (order or paraphrase sensitivity).

These would follow as separate pre-registrations if HR1 and HR2 hold.

## 7. Artifacts

| Artifact | Purpose |
|---|---|
| `research/src/freeze_risk_estimator.py` | Freezes the estimator (done) |
| `research/src/build_heldout_datasets.py` | Natural-mix sampler. It reuses each builder's fetch, clean, scrub and exclusion functions unchanged |
| `research/data/heldout/{mozilla,kernel}_heldout.jsonl` | The held-out datasets, plus hashes and a manifest |
| `research/src/run_heldout_validation.py` | Dry-run, smoke test, live run and the pre-registered analysis |
