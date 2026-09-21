# Shortlist: papers most load-bearing for the gap analysis

Full details for all 28 reviewed papers are in `literature_matrix.csv`. This
file pulls out the ~10 papers that most directly bear on whether the
provisional research question is novel, and what they specifically do and do
not cover.

## Closest to "does individual calibration compose into workflow reliability"

**P26 — Lin et al., "Uncertainty Quantification for LLM Agents: A Taxonomy,
an Evaluation Protocol, and an Empirical Study" (arXiv:2609.07395, 2026)**
The single closest paper found to the first half of the research question.
Explicitly demonstrates, empirically, that step-level calibration does not
imply trajectory-level calibration, and introduces Trajectory-Checkpoint ECE
(TC-ECE) to measure the gap. Does **not** propose or evaluate an escalation
policy, and its workflows are LLM-agent reasoning trajectories specifically,
not general heterogeneous multi-step decision pipelines.

**P22 — Kotte, "PASC: Pipeline-Aware Conformal Prediction with Joint
Coverage Guarantees for Multi-Stage NLP and LLM Pipelines" (arXiv:2605.18812,
2026)** Closest paper to a *formal/mathematical* answer: shows independently
calibrated per-stage coverage compounds multiplicatively under independence
(≤72.9% joint coverage for K=3 stages at α=0.1) and proposes a method with
joint-coverage guarantees. Operates in the conformal-coverage framework
specifically (not general ECE-style calibration), is NLP/LLM-pipeline
specific, doesn't address human escalation. **Caveat: appears to be a
single-author, very recent preprint; peer-review status could not be
verified — treat cautiously until confirmed.**

**P10 — Zhang, Amin, Perakis, "Decomposition-Based Modular Conformal
Prediction for Two-Stage Modeling" (arXiv:2510.04406, 2025)** Formal
precedent for composing per-stage calibration, but restricted to exactly two
stages and regression-style residual decomposition.

**P28 — Zhang, Xiong, Wu, "Agentic Confidence Calibration" (arXiv:2601.15778,
2026)** Names "compounding errors along trajectories" explicitly as the
reason single-turn calibration fails for agents; proposes Holistic
Trajectory Calibration (HTC), a post-hoc trajectory-confidence detector —
not a formal theory linking per-step calibration to workflow reliability,
and not an escalation-policy study.

## Closest to "can a workflow-level uncertainty/escalation policy improve reliability at a target automation coverage"

**P23 — Dou, Lian, Li, "Conformal Cascade: Distribution-Free Accuracy
Guarantees for Multi-Tier LLM Inference" (arXiv:2607.25018, 2026)** A
provably-improving, conformal-set-based deferral rule for model cascades.
The "workflow" is a single query routed through model tiers, not a
multi-step software workflow of heterogeneous decision types.

**P18 — Zellinger, Liu, Thomson, "Cost-Saving LLM Cascades with Early
Abstention" (arXiv:2502.09054, 2025)** Early abstention reduces both cost and
error in cascades by exploiting correlated error patterns across stages —
an automation-coverage-like tradeoff, but again for repeated-same-decision
cascades, not heterogeneous workflows.

**P17 — Bouchard, "Is Escalation Worth It? A Decision-Theoretic
Characterization of LLM Cascades" (arXiv:2605.06350, 2026)** Cost-quality
tradeoff framework for cascades; useful for Phase 6 utility/cost metric
design.

**P16 — "Trust or Escalate: LLM Judges with Provable Guarantees for Human
Agreement" (ICLR 2025, arXiv:2407.18370)** Calibration-driven escalation with
provable human-agreement guarantees — but for a single judging decision, not
a workflow. *(Author list not independently verified — confirm before
citing.)*

## Existence proof that workflow-level policy can matter at all

**P13 — Meyerson et al., "Solving a Million-Step LLM Task with Zero Errors"
(MAKER, arXiv:2511.09030, 2025)** Strongest empirical demonstration that a
workflow-level policy (extreme decomposition + per-step voting/red-flagging)
can decouple end-to-end reliability from per-step accuracy, at >1M-step
scale. Mechanism is redundancy/voting, not calibration-driven escalation, and
it reports no automation-coverage/escalation-rate tradeoff curve.

## Machinery for aggregating per-step uncertainty into a workflow signal

**P21 — "SAUP: Situation Awareness Uncertainty Propagation on LLM Agent"
(ACL 2025, arXiv:2412.01033)** and **P27 — Duan et al., "UProp" (
arXiv:2506.17419, 2025)** both give mechanisms for propagating/aggregating
per-step uncertainty into a trajectory-level signal — necessary machinery for
a workflow-level escalation policy, but neither studies the
calibration-to-reliability relationship or evaluates an escalation policy
against automation coverage. *(P21 author list not independently
verified.)*

## Addendum after full-text read of PASC and Lin et al. (+ two new search areas)

**P22/PASC, full text:** confirmed to be a genuine joint-maximum-
nonconformity-score method (Prop. 4, Thm. 6) — exact finite-sample joint
coverage for a K-stage pipeline, but stages must each reduce to a single
scalar nonconformity score; no agentic chains tested; zero escalation
treatment. Single-author unreviewed preprint.

**P26/Lin et al., full text:** the step-vs-trajectory calibration gap is a
*proven* result (Prop. 1 counterexample, Prop. 2 exact formula
`P(Y₁=1,Y₂=1)=p₁p₂+ρ√(p₁(1−p₁)p₂(1−p₂))`), not just empirical — directly
validates this project's `conf_product`/`Δ` statistics in
`../methodology/compositional_reliability_baseline.md`. Escalation
discussed only as motivation, never implemented.

**New — P29, Babbar, Bhatt, Weller, "On the Utility of Prediction Sets in
Human-AI Teams" (IJCAI 2022, arXiv:2205.01411):** the nearest single-stage
precedent for combining calibrated/conformal uncertainty with a human
deferral policy, validated with a real n=120 human-subjects study
(Deferral Conformal Prediction). Not composed across a pipeline. This is
now the second paper (after PASC) that any paper draft must explicitly
differentiate from — PASC on the composition axis, Babbar et al. on the
escalation axis; the sharpened gap claim is that no paper does both
together for heterogeneous-representation stages. Full text not yet read
(abstract-level only) — should be read before the paper draft.

**New — classical reliability engineering (P32 Barlow & Proschan 1965;
P34, dependent-failure-propagation 2025):** confirms component-to-system
reliability composition (including relaxing independence) is a
60+-year-old solved problem for binary/point reliability — but not for
probabilistic calibration or heterogeneous ML uncertainty representations.
Rules out "composing reliability across stages" alone as a novelty claim;
does not touch the calibration/representation/escalation combination.

See `gap_analysis.md` §Full-text findings for the complete reasoning and
the resulting sharpened, more specific gap statement.

## What this shortlist implies

No single paper unifies (a) a general (not single-mechanism, not
single-domain) account of how per-decision calibration relates to end-to-end
multi-step workflow reliability, with (b) a workflow-level escalation policy
evaluated against an automation-coverage axis, across (c) a workflow of
heterogeneous decision types (not a repeated cascade of the same decision).
See `gap_analysis.md` for the full analysis and candidate gaps.
