# Pre-registration: the Kubernetes workflow on the four comparison models

**Status:** written 2026-10-24, before any comparison-model output on
Kubernetes exists. **No TypeSafe API calls are involved;** the runs use
open-weight models on Modal GPUs.

**Parents:**
- `independent_workflow_preregistration.md` (v1 plus Amendments 1–7): the
  dataset, questions, adapter, analysis, K1–K3 and d\*.
- `openjev_crossmodel_preregistration.md`: the open-Jev decision layer, the
  three open models and the served OpenJev-27B.

Everything not stated here is inherited from them unchanged.

## 1. Why

The Kubernetes replication supported K1 and K2 for Jev 1.13 only. This
study tests whether the same predictive finding holds for the four
comparison models on an independent workflow. If it does, the claim is
about chained typed decisions in general, not about one vendor model.

## 2. Fixed elements

**Data.**
- `research/data/k8s/k8s_dataset.jsonl`, unchanged (sha256 recorded by the
  runner).
- 500 development and 582 test issues. The 150 calibration issues get no
  model calls, as in the Jev run.

**Questions and adapter.** `run_k8s_workflow.QUESTIONS` and
`run_k8s_workflow.node_state`, imported, not copied.

**Models (fixed now):**
- `Qwen/Qwen2.5-7B-Instruct`, `microsoft/Phi-3.5-mini-instruct` (Modal
  class `OpenJev`);
- `allenai/OLMo-2-1124-7B-Instruct` (class `OpenJevT447`);
- OpenJev-27B through the served shim (`openjev-serve`), with the server
  version and shim hash recorded.

**Decision layer.**
- **Open models:** `openjev/client.py`'s prompt templates and TypeSafe's
  documented confidence formulas.
- **OpenJev-27B:** the shim's own outputs.
- **Determinism:** inference is deterministic, so each call is recorded
  three times and flagged, as in the parent study.
- **Disclosed consequences:**
  - repeat-instability features are constant;
  - an "unstable score" can never occur, so the escalate-on-instability
    route of F is inactive.

**Analysis.** `analyze_k8s.analyze`, unchanged, run separately on each
model's outputs. Each model's rate table comes from its own development
outputs.

## 3. Hypotheses, per model M

**XK1 (primary).** On the test issues, the action-rule score r(a) ranks
M's wrong actions (a ≠ a\*) better than M's final-step confidence. This
is the paired one-sided bootstrap of K1.

**XK2 (primary).** The action-rule score's AUROC exceeds 0.5. This is K2.

**Multiplicity.** Holm correction across all 8 primary tests (4 models ×
XK1, XK2), at α = 0.05. This is stricter than the parent's per-model
family.

**Status per model,** with the parent's rules:
- **XK1 supported:** it survives Holm.
- **Not replicated:** the upper 95% bound is below d\* = 0.10, from
  `k8s_power_realized.json`.
- **Otherwise inconclusive.**

**Overall reading, fixed now:**
- **The cross-model finding "holds on Kubernetes"** if XK1 is supported
  for at least 3 of the 4 models.
- **It "does not generalise"** if XK1 is not replicated for 2 or more.
- **Otherwise the result is mixed.**

All four models are reported whatever the outcome.

## 4. Exploratory (reported, no claim)

- **K3** (the prior-shift repair) per model, with the BBSE diagnostics.
- **E_dec and E_all** vs the rule. Repeat features are constant here.
- **Per-node agreement** with reference labels.
- **The any-node target.**
- **Per-SIG results.**
- **The hypothetical cost** at a 10% review budget, using the frozen
  table, not validated for Kubernetes.

## 5. Data-quality rules (fixed now)

- **Label mass.** The share of next-token probability on the allowed
  labels is recorded for every pass.
- **Low-mass sensitivity.** If more than 2% of a model's passes have mass
  below 0.5, XK1 is also reported with those issues excluded. The primary
  result is unchanged by this.
- **Failure handling,** for runs or issues that fail technically, without
  looking at outputs:
  - a model that fails to load is reported as failed and **not replaced**,
    since its Mozilla and kernel results already exist;
  - an issue with a failed pass is dropped for that model and counted.

## 6. Run safeguards

- **Selftest and dry run,** with no Modal calls. The dry run builds every
  request and checks its labels.
- **Smoke run:** 30 development issues per open model, which must
  complete without errors.
- **The full run,** after explicit user authorization of the Modal spend.
- **Output** goes to `research/data/k8s/crossmodel/<model>_raw_responses.jsonl`.
  The runner refuses to overwrite an existing file.

## Amendment 1 (2026-10-24, after results were seen): competence sensitivity

**Not part of the frozen primary analysis.** The primary result and the
overall reading ("holds on Kubernetes") are unchanged.

**Request.** After the results were seen, the authors asked that models
which cannot do the task not carry the cross-model claim. Dropping only
the model that failed XK1 would be selective reporting, so one criterion
is applied to every model, Jev 1.13 included.

**Criterion.** A model is **competent** if its test-set accuracy beats
chance on every step:
- routing above 1/3;
- bug or not above 1/2;
- priority above 1/3.

**Reported:**
- XK1 status for the competent models, with Jev's from the parent study;
- every model's per-step accuracy.

**The primary table stays complete and is reported in full.** The paper
leads with the competent models and summarises the others.
