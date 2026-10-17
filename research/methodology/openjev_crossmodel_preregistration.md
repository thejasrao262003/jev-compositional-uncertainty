# Pre-registration: cross-model replication with open-weight "open-Jev" models

**Status:** pre-registered 2026-10-17, before any open-model output exists.
No TypeSafe API calls are involved; the runs use open-weight models on
Modal GPUs.

## 1. Why

Every result so far comes from one model, Jev 1.13. There is no
open-source Jev: TypeSafe has not released weights or architecture. To
test whether the findings are about *Jev* or about *structured decision
primitives in general*, we build a Jev-compatible decision layer
("open-Jev") over open-weight LLMs and run the identical study.

## 2. Open-Jev (fixed before any run)

**Same inputs as Jev:** for each step (`choice`, `noul`, `score`) the
model sees the same evidence text, the same question instructions and
criteria (`run_kernel_validation.QUESTIONS`), and the same three-step
adapter (`node_state`).

**Prompt.** A fixed template asks for a single label:
- an option letter for `choice`;
- a level digit 0/1/2 for `score`;
- Yes/No for `noul`.

The template is in `research/src/openjev/client.py`.

**Probabilities.**
- The next-token probability of each allowed label is read from the model
  at the answer position.
- Leading-space and case variants are summed.
- The result is renormalized over the allowed labels, which is equivalent
  to constrained decoding.
- Greedy and deterministic: no sampling.

**Outputs, in Jev's documented schema (docs.typesafe.ai/confidence):**
- choice: `confidence = (p_max − 1/n)/(1 − 1/n)`;
- score: `confidence = max(0, 1 − Σ p_i |i − m| / MAD_unif)` and
  `score = Σ i·p_i`;
- noul: `noul = P(Yes)`.

**Repeats.** Inference is deterministic, so each step's single output is
recorded 3 times and flagged `deterministic`. The repeat-instability and
spread features are therefore constant for open models. That is
disclosed, and it means `E_dec`/`E_all` lose those inputs.

**Models** (ungated open weights, three families and sizes, chosen
before any run):
- `Qwen/Qwen2.5-7B-Instruct`;
- `allenai/OLMo-2-1124-7B-Instruct` (fully open data);
- `microsoft/Phi-3.5-mini-instruct`.

If a model fails to load, it is replaced by `Qwen/Qwen2.5-14B-Instruct`,
and the replacement is reported.

## 3. Data

- **Training split:** the 442 bugs of the original Mozilla (202) and
  kernel (240) studies.
- **Held-out split:** the 500 held-out bugs (250 + 250, natural mix).

These are identical to the Jev studies, so results are paired by bug
across models.

## 4. Hypotheses (per model)

For each open model *M*:

**C1 (characterization, descriptive):** report, as for Jev,
- agreement with reference labels for each step;
- confidence AUROC for each step's own agreement;
- severity confusion (is there middle compression?);
- the fixed-threshold selectivity.

**X1 (primary):** a decisions-only risk estimator trained on *M*'s outputs
for the 442 training bugs predicts *M*'s workflow failures on the 500
held-out bugs better than *M*'s low final-step confidence.
- **Same as HR1:** features, λ = 1, target and test.
- **Supported** if the one-sided 95% lower bound of the AUROC difference
  is above 0.

**X2 (primary):** the same estimator's held-out AUROC is above 0.5.
- **Supported** if the one-sided 95% lower bound is above 0.5.

**Multiplicity:** Holm across the 3 models × 2 tests (6 tests),
family-wise α = 0.05.

**X3 (descriptive):** does `E_all` beat `E_dec` for *M*? For open models,
`E_all` includes the logprob-based confidence and distribution features.
These are exact model probabilities, unlike Jev's.

**X4 (descriptive):** apply the *Jev-trained* frozen estimator to each
open model's outputs. Do Jev's error-prone decision patterns transfer to
other models?

## 5. What would change the paper's claims

- **X1/X2 hold for open models:** "decision patterns predict failure,
  confidence doesn't" becomes a cross-model finding.
- **X1 fails, but `E_all` or confidence works for open models:** the
  confidence failure is specific to Jev's confidence construction, not to
  structured primitives. The paper must say so.
- **Severity compression appears or not:** that tells whether it is
  model-specific.

## 6. Cost

About 942 bugs × 3 steps = 2,826 forward passes per model, single GPU
(L4/A10G), roughly $1–3 per model on Modal.
