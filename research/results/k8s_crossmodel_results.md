# Kubernetes workflow on the four comparison models

**Protocol:** `research/methodology/k8s_crossmodel_preregistration.md`,
committed in `fc08d51` before any output.
**Raw outputs:** committed before analysis.
**Code:** `research/src/openjev/client_k8s.py` and
`research/src/analyze_k8s_crossmodel.py`.
**Numbers:** `k8s_crossmodel_analysis.json`.

**Runs:** 1,082 issues per model (500 development + 582 test), with zero
technical failures. No model had more than 2% of passes with label mass
below 0.5, so the low-mass sensitivity analysis was not triggered.

## Primary (Holm over 8 tests)

| Model | AUROC rule | AUROC confidence | Difference [95%] | XK1 | XK2 |
|---|---|---|---|---|---|
| Qwen2.5-7B | 0.710 | 0.555 | +0.155 [+0.095, +0.217] | supported | supported |
| Phi-3.5-mini | 0.519 | 0.674 | −0.155 [−0.284, −0.009] | not replicated | inconclusive |
| OLMo-2-7B | 0.850 | 0.255 | +0.595 [+0.487, +0.700] | supported | supported |
| OpenJev-27B | 0.796 | 0.569 | +0.227 [+0.174, +0.285] | supported | supported |

**Overall, by the pre-registered rule: "holds on Kubernetes"** (3 of 4
models).

## Descriptive context (added after the results were seen)

| Model | Test actions (accept / defer / escalate) | Wrong-action rate |
|---|---|---|
| Qwen2.5-7B | 87 / 494 / 1 | 0.662 |
| Phi-3.5-mini | 1 / 1 / 580 | 0.954 |
| OLMo-2-7B | 73 / 2 / 507 | 0.847 |
| OpenJev-27B | 180 / 388 / 14 | 0.555 |

- **The small open models are poor at this task.** Each collapses onto
  one action.
- **Where the rule wins, much of its signal is "this is the dominant
  action, which is usually wrong".**
- **Phi-3.5 escalates 580 of 582 issues.** Its rule score is therefore
  nearly constant and cannot rank, and confidence is the only signal left.
  The failure is a model that has collapsed onto one action, not evidence
  against the rule where actions vary.
- **OLMo-2's confidence is inversely related to correctness** (AUROC
  0.255): it is most confident when wrong.

## Exploratory

- **E_dec over the rule:** between −0.000 and +0.029 across models. The
  decision estimator again adds little.
- **K3 (BBSE) was evaluable only for OpenJev-27B,** where the estimate was
  negative. The others failed the condition-number gate.
