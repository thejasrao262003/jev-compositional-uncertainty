# Cross-model replication: Jev vs. four open models

**Pre-registration:** `research/methodology/openjev_crossmodel_preregistration.md`.
That file records three disclosed deviations:
- **Amendment 1:** OpenJev added before any of its outputs existed.
- **Amendment 2:** OLMo-2 run under `transformers` 4.47.1.
- **Amendment 3:** a readout bug fixed after interim results were seen.
  All general models were re-run under one corrected readout. The
  superseded outputs are archived.

**Data:** the same 942 bugs as the Jev studies (442 training + 500
held-out), the same questions and the same three-step adapter.

**Analysis:** `research/src/openjev/analyze_crossmodel.py` →
`openjev_crossmodel_analysis.json`.

**The models:**
- **Jev 1.13** (TypeSafe, hosted). The reference column uses its
  held-out study.
- **OpenJev 27B:** an independent *trained* Jev-style model, served
  exactly as its authors specify (vLLM 0.29 FP8 on H100 plus their
  calibrated helper). 2,826 requests, 0 failures.
- **Qwen2.5-7B-Instruct, OLMo-2-7B-Instruct, Phi-3.5-mini-instruct:**
  general instruct models behind our Jev-compatible logprob readout,
  using TypeSafe's documented confidence formulas.

## Primary result: decision patterns beat confidence for every model

The held-out AUROC for ranking wrong workflow actions first:

| Model | Held-out failure rate | `E_dec` (decisions) | Final-step confidence | X1 difference [one-sided 95% lower] | X2 lower bound |
|---|---:|---:|---:|---|---:|
| Jev 1.13 (reference) | 0.43 | 0.763 | 0.549 | +0.214 [+0.158] | 0.64–0.76 |
| **OpenJev 27B** | 0.47 | **0.748** | 0.575 | +0.173 [+0.120] | 0.713 |
| Qwen2.5-7B | 0.74 | **0.736** | 0.473 | +0.262 [+0.186] | 0.694 |
| Phi-3.5-mini | 0.72 | **0.677** | 0.401 | +0.276 [+0.193] | 0.633 |
| OLMo-2-7B | 0.80 | **0.637** | 0.551 | +0.086 [+0.007] | 0.589 |

**All 8 pre-registered tests are supported** (X1 and X2 for 4 models;
Holm, family-wise α = 0.05, one-sided). OLMo's X1 is the weakest
(p = 0.037) and passes at the last Holm step. For every model, an
estimator that knows the model's decision patterns predicts its workflow
failures, and the model's own final-step confidence does not (0.40–0.58).

## Secondary (descriptive)

**Jev's frozen estimator transfers to OpenJev** (X4): trained only on Jev
outputs, it reaches AUROC **0.76** on OpenJev's held-out outputs, as good
as OpenJev's own estimator. The two Jev-style models fail in the same
pattern. It also transfers to the general models (0.64–0.74).

**Uncertainty features** (X3, `E_all` − `E_dec`):

| Model | `E_all` − `E_dec` |
|---|---:|
| Jev | +0.006 |
| OpenJev | +0.004 |
| Qwen2.5-7B | +0.012 |
| Phi-3.5 | +0.054 |
| OLMo-2 | **+0.078** |

For the calibrated Jev-style models, uncertainty signals are redundant
with the decisions. For the weaker raw LLMs, exact token probabilities do
carry extra information.

**Severity bias depends on the model family:**

| Model | Minor bugs rated | Serious bugs rated | Pattern |
|---|---|---|---|
| Jev | mostly 1 (79% rated higher) | 43–56% rated lower | **pulled to the middle** |
| OpenJev | 1: 62–69% | 1: 27–32% | **pulled to the middle** (same as Jev) |
| Qwen2.5-7B | 2: 67–71% | 2: 91–94% | **pushed to "blocking"** |
| Phi-3.5 | 2: 72–76% | 2: 95–99% | **pushed to "blocking"** |
| OLMo-2 | 2: 91–94% | 2: 99–100% | **pushed to "blocking"** |

**Confidence per step** (AUROC for each step's own agreement, Mozilla /
kernel):

| Step | Jev-style models | General models | Reading |
|---|---|---|---|
| `choice` | 0.96–0.99 | 0.64–0.98 | Discriminative everywhere, and saturated (most bugs ≥ 0.90) |
| `noul` | 0.46–0.62 | 0.50–0.69 | Weak everywhere |
| `score` | 0.57–0.64 | 0.42–0.65 | Weak everywhere |

## What this means

- **The claim extends beyond Jev, with stated limits.** Across five
  *evaluated* models from four sources (not "every model"), decision
  features ranked incorrect workflow actions better than final-step
  confidence. The failure modes differed between Jev-style decision
  models and general instruct models.
  Across those five models:
  - workflow failure is predictable from the pattern of decisions;
  - final-step confidence is at or near chance;
  - routing confidence is the only step-level signal that consistently
    discriminates.
- **Two classes of model fail differently:**
  - trained Jev-style decision models pull severity to the middle and
    have well-behaved (unsaturated) confidence;
  - general instruct models push everything to "blocking", fail far more
    often, and carry some extra information in their raw token
    probabilities.

## Readout diagnostics and limits

- **Label mass** (the probability on the allowed answer labels) was below
  0.5 for 3/2,826 Qwen requests, **85/2,826 OLMo requests (3%)** and 0
  for Phi. On those, the model wanted to say something other than a bare
  label.
- **Ties:** exact 0.5 regression probabilities (bfloat16 ties) occurred
  in 3, 8 and 27 requests.
- **Library versions differ:** Qwen and Phi ran under `transformers`
  4.46.3, OLMo under 4.47.1.
- **No repeat variation for open models:** they are deterministic, so
  their repeat-variation features are constant.
- **The target is constructed;** kernel labels are reporters' claims.
- **One domain** (bug triage) and one workflow.


## Robustness checks requested in review (exploratory; `openjev_robustness_checks.json`)

1. **What transfers.** Jev's estimator is the hash-verified frozen file,
   applied unchanged to all four models and never refitted (code:
   `analyze_crossmodel.score_rows`). Its held-out AUROC:

   | Model | Frozen Jev estimator [95% CI] |
   |---|---|
   | OpenJev | 0.76 [0.72, 0.80] |
   | Qwen | 0.74 [0.68, 0.79] |
   | Phi | 0.70 [0.65, 0.75] |
   | OLMo | 0.64 [0.58, 0.70] |

2. **Uncertainty.** n = 500 held-out bugs per model; 95% bootstrap
   intervals stratified by tracker:

   | Model | `E_dec` | Final-step confidence | Intervals overlap? |
   |---|---|---|---|
   | Jev | 0.76 [0.72, 0.80] | 0.55 [0.50, 0.60] | No |
   | OpenJev | 0.75 [0.71, 0.79] | 0.58 [0.53, 0.63] | No |
   | Qwen | 0.74 [0.68, 0.79] | 0.47 [0.41, 0.54] | No |
   | Phi | 0.68 [0.63, 0.73] | 0.40 [0.34, 0.46] | No |
   | OLMo | 0.64 [0.58, 0.69] | 0.55 [0.48, 0.62] | **Yes** |

   The `E_dec` intervals of Jev, OpenJev and Qwen overlap, so **models
   cannot be ranked** against each other on this.

3. **Leakage.**
   - 0 bug-id overlap.
   - 0 exact text duplicates.
   - 0 near-duplicates (word 5-gram Jaccard ≥ 0.8). The highest similarity
     between any held-out and training bug is 0.58.
   - Real bugs only, so no template sharing.

4. **Fairer baselines** (held-out AUROC):

   | Baseline | AUROC |
   |---|---|
   | Low routing confidence alone | 0.48–0.52 |
   | Low regression confidence alone | 0.45–0.56 |
   | Severity-distribution entropy | 0.40–0.55 |
   | **Class-frequency rule: error rate by workflow action** (fit on each model's training bugs) | **Jev 0.76, OpenJev 0.75, Qwen 0.70, Phi 0.69, OLMo 0.58** |

   **This matches `E_dec`** for Jev and OpenJev (0.76/0.76, 0.75/0.75)
   and is close for the others. **The predictive information is almost
   entirely *which action the workflow chose* plus that action's
   historical error rate.** The logistic model adds little beyond that
   lookup (≤ 0.06, for OLMo).

   This sharpens the claim: *action-conditional error rates beat
   confidence.* It is simple and cheap, and it should be stated as
   such, not dressed up as a sophisticated estimator.

   By contrast, error rate by predicted *severity* alone is 0.40 for Jev
   (below chance), and 0.58–0.70 for the others.

5. **Different failure rates.** Partly model quality, but the interfaces
   differ:
   - the Jev-style models use their own trained question format and
     calibrated readout;
   - the general models use our prompt and constrained readout.

   So the absolute failure rates (43–80%) are **not** a clean model
   comparison. Only the within-model contrast (decisions vs confidence)
   is.

6. **Readout sensitivity.**
   - **Readout bug, before vs after the fix:** essentially unchanged for
     Qwen (0.732 → 0.736) and OLMo (0.637 → 0.637). For Phi, the
     estimator moved 0.566 → 0.677 and confidence 0.500 → 0.401, because
     the v1 severity readout was broken. Phi's X1 and X2 were supported
     under both versions.
   - **OLMo without its 39 held-out bugs that had a low-label-mass
     request:** `E_dec` 0.647 vs confidence 0.553. Same conclusion.
