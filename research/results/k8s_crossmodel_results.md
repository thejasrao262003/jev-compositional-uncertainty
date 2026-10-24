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

## Amendment 1 (post hoc, disclosed): competence sensitivity

**Criterion:** test accuracy above chance on every step (routing above
1/3, bug above 1/2, priority above 1/3). It is applied to every model,
Jev included.

| Model | Routing | Bug | Priority | Competent | XK1 / K1 |
|---|---|---|---|---|---|
| Jev 1.13 | 0.952 | 0.916 | 0.371 | yes | supported |
| OpenJev-27B | 0.912 | 0.907 | 0.404 | yes | supported |
| Qwen2.5-7B | 0.890 | 0.868 | 0.270 | no | supported |
| OLMo-2-7B | 0.923 | 0.832 | 0.082 | no | supported |
| Phi-3.5-mini | 0.924 | 0.761 | 0.046 | no | not replicated |

**Both competent models support the finding.**
- **The split matches the paper's model classes:** the two models trained
  for typed decisions pass, and all three general instruct models fail on
  priority, as they push severity to "blocking" on Mozilla and kernel.
- **The primary result and overall reading are unchanged.** The paper
  leads with the competent models and summarises the others.
