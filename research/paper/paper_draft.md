# Structured Outputs Do Not Imply Compatible Uncertainty: An Empirical Study of Confidence Signals in a Multi-Step Decision Workflow

*Working draft v0.1, 2026-10-16. Target: workshop paper or preprint
(option A in the session log). Every number is taken from a committed
result file, cited in brackets as [file]. `TBD-K` marks kernel
replication results to fill in after the full run. Citation keys refer to
`research/literature/literature_matrix.csv`; all must be re-verified
before submission (the literature pass was web-search only).*

---

## Abstract

Structured-output decision APIs return well-typed answers with numeric
confidence. It is tempting to treat those numbers as interchangeable
probabilities and compose them across the steps of a workflow. We test
that practice on a commercial API's three decision primitives:
- a categorical `choice`;
- a binary `noul`;
- an ordinal `score`.

The primitives are chained into a three-step triage workflow (route →
assess → rate severity). Data comes from three sources: controlled
constructed items, 202 human-triaged Mozilla bugs, and 240 reporter-labeled
Linux kernel bugs (`TBD-K`). Four findings:

1. **The primitives' uncertainty signals behave incompatibly.**
   - `choice` confidence is saturated (85% of real bugs at ≥ 0.90) but
     discriminative (AUROC 0.90).
   - `noul`'s confidence-like value is uninformative (AUROC 0.53) and
     underconfident.
   - `score`'s confidence is flat across true levels.
2. **Fixed confidence thresholds tuned on constructed data lost their
   intended selectivity on real text.** A cut that escalated 73% of
   constructed items (target 67%) escalated 88% of real bugs (target
   41%).
3. **`score` compresses real severity toward the middle.** It rates 79%
   of minor bugs higher than triage and 43% of serious bugs lower.
4. **Composed confidence added nothing beyond the decisions**
   (exploratory). Escalating the least-confident cases on top of
   decision composition never beat random escalation of the same size.

We also report a methodological lesson: a natural "confidence vs.
decisions" comparison is confounded when the target action is defined by
the decisions themselves. We give the corrected comparison, which is
pre-registered for a controlled follow-up study.

---

## 1. Introduction

**Motivation.** A structured response can be valid and still wrong.
Workflows built from several model decisions inherit each step's errors,
and a common hope is that each step's confidence can be composed into a
workflow-level signal for when to escalate to a human.

**Question.** When a workflow chains *heterogeneous* decision primitives,
can it rely on their uncertainty signals, and how should it combine them?

**Why heterogeneity matters.** The API we study exposes three primitives
whose uncertainty is structurally different:
- `choice` returns a distribution over labels plus a confidence scalar;
- `score` returns an ordinal distribution plus a confidence scalar;
- `noul` returns a single probability with no separate confidence.

Treating these as one kind of number is a modeling assumption. This
paper tests it.

**Contributions.**
- **C1. Characterization (§4).** Per-primitive behavior of confidence,
  on controlled and real data.
- **C2. Transfer (§5).** Fixed thresholds derived on constructed content
  fail to keep their selectivity on real text.
- **C3. Real-data validation (§6).** Two independent trackers with
  different labelers (triage vs. reporter).
- **C4. Composition (§7, exploratory).** Composed confidence adds
  nothing over the decisions here, and a confound in the obvious
  comparison is identified and corrected.
- **C5. Method (§8).** A pre-registration and audit process that caught
  five design or implementation defects before or alongside evaluation.

**Non-claims.** We make no claims about general calibration, other APIs
or model versions, domains beyond bug triage, or real-world operational
benefit.

---

## 2. Related work

- **Single-decision calibration:** Platt; Guo et al. 2017; Naeini et al.
  2015. LLM confidence surveys (KDD 2025, arXiv:2503.15850; NAACL 2024,
  arXiv:2311.08298).
- **Selective prediction and abstention:** El-Yaniv & Wiener; Geifman &
  El-Yaniv 2017; SelectiveNet 2019. **Learning to defer:** Madras et al.
  2018.
- **Conformal methods and composition:** Angelopoulos & Bates
  (arXiv:2107.07511); conformal risk control (arXiv:2208.02814);
  two-stage modular conformal (arXiv:2510.04406); pipeline-aware
  conformal with multiplicative per-stage compounding (PASC,
  arXiv:2605.18812, a single-author preprint, cited cautiously).
- **Cascades and escalation:**
  - early abstention (arXiv:2502.09054);
  - a decision-theoretic view of escalation (arXiv:2605.06350);
  - conformal cascades (arXiv:2607.25018);
  - LLM judges with escalation guarantees (ICLR 2025, arXiv:2407.18370).

  These route *one* decision through model tiers, not a workflow of
  different decision types.
- **Agents and trajectories:**
  - step-level calibration does not imply trajectory-level calibration
    (Lin et al., arXiv:2609.07395), the closest work;
  - agentic confidence calibration (arXiv:2601.15778);
  - uncertainty propagation in agents (SAUP, arXiv:2412.01033; UProp,
    arXiv:2506.17419).

**Gap.** We found no work that studies *heterogeneous* primitives with
*structurally different* uncertainty representations inside one
workflow, measured against real labels. Caveat: classical
reliability-engineering composition and HCI escalation literature were
not searched systematically [research/literature/README.md].

---

## 3. Setting

**Primitives.** All runs use `jev-1.13.0`. Each node is called 3 times,
and the repeats are reduced to one decision:
- `choice` and `score`: the modal decision, with a tie tolerance of 0.02;
  a node with no majority of 2 of 3 is `repeat_unstable`;
- `noul`: the mean, thresholded at 0.5.

**Workflow.**
- Node 1, `choice`: network vs. storage routing.
- Node 2, `noul`: customer impact on constructed data; regression on
  real bugs.
- Node 3, `score`: 3-level severity.

Each node reads the evidence plus the upstream decisions (a fixed
adapter).

**Target action.** `a* = F(c2, c3)`:
- unclear impact → request more evidence;
- else severity 2 → escalate;
- else severity 1 and c2 = 1 → defer;
- else accept.

**Strategies:**
- **S1:** `F` on the node decisions.
- **S2:** escalate the `⌈q·n⌉` instances with the lowest product of
  confidences.
- **S4a:** `F` plus escalation on repeat instability.
- **S5:** per-primitive rank-normalized uncertainty.
- **2h / 5h:** `F(decisions)` plus confidence-ranked escalation of a
  fixed 10% budget.
- **R:** the same budget escalated at random.

**Scoring.** The frozen cost matrix [protocol §16.1]: wrongly accepting
costs 6–10, any other mismatch 1, plus 1 per escalation for the human.

---

## 4. Characterization: the primitives do not share uncertainty semantics

| Primitive | Constructed items | Real bugs (Mozilla, n = 202) |
|---|---|---|
| `choice` | A high-confidence error subgroup: mean confidence 0.915, accuracy 0.333, n = 6 [stage1_h1h2b_analysis.md] | Saturated: 85% at ≥ 0.90, agreeing 0.96. AUROC 0.90. ECE 0.05. The constructed failure subgroup does not recur |
| `noul` | 24/24 correct, but confidence below accuracy in every bin | Agreement flat across bands (0.71–0.84). AUROC 0.53. ECE 0.36 (underconfidence) |
| `score` | Tracks the most severe sentence (6/6). Confidence varies by 0.173 with sentence order alone, on 1 of 3 items | Confidence about 0.6 at every true level. AUROC 0.58 |

[mozilla_validation_results.md; mozilla_exploratory_analysis.md E4]

**Kernel replication:** `TBD-K`. The smoke test (n = 24) showed `choice`
at confidence 1.0 on 24/24 bugs [kernel_smoketest_execution_manifest.json].

**Reading.** On these primitives, a number labeled "confidence" ranges
from discriminative-but-saturated to uninformative. Whatever composition
rule is used, it inherits that mix.

---

## 5. Fixed thresholds lost their selectivity on real text

| Rule (designed on constructed data) | Constructed pilot | Mozilla (202) | Kernel |
|---|---|---|---|
| Escalate if `choice` confidence ≥ 0.90 | fires 27/30 | 85% | smoke 24/24; `TBD-K` |
| Accept iff confidence product ≥ 0.5 | escalates 73% (target 67%) | 88% (target 41%) | smoke 92%; `TBD-K` |

[threshold_transfer_finding.md]

**These are two different failures:**
- **The `choice` trigger is non-selective everywhere,** a design failure
  that only became visible once it was measured.
- **The product cut is distribution-sensitive.** Its selectivity was
  close to target on constructed data and far off on real data, because
  real text pulls `noul` toward 0.5.

**Lesson.** A fixed threshold carries the confidence scale of the data
it was set on. Constructed data was too clean to reveal this.

---

## 6. Real-data validation on two trackers

**Data.**
- **Mozilla:** 202 fixed Firefox networking and storage bugs, labeled by
  triage (S1–S4).
- **Linux kernel:** 240 fixed networking and storage bugs, labeled by
  the reporter (`TBD-K`).

Both trackers' keyword-free subsets are reported.

**Node agreement with the reference labels:**

| Node | Mozilla | Trivial baseline | Kernel |
|---|---|---|---|
| `choice` | 0.89 [0.83, 0.92] | 0.59 | `TBD-K` (smoke 24/24) |
| `noul` | 0.80 [0.74, 0.85] | 0.74 | `TBD-K` (smoke 15/24) |
| `score` | 0.53 [0.46, 0.60] | 0.40 | `TBD-K` (smoke 9/24) |

**Severity compression (`score`):**

| True level | Mozilla: rated higher | Mozilla: rated lower | Kernel |
|---|---|---|---|
| minor | 42/53 = 0.79 [0.67, 0.88] | — | `TBD-K` (smoke 7/8) |
| serious | — | 29/68 = 0.43 | `TBD-K` (smoke 5/8) |

**Wording.** With Mozilla's own severity definitions, serious bugs
improve but normal bugs are pushed up (overall 0.56). The criteria matter,
but the bias persists.

**Why two trackers.** Mozilla labels come from triage and kernel labels
from reporters. If compression appears against both, it is less likely to
be an artifact of one labeling process.

---

## 7. Composition (exploratory, Mozilla; kernel `TBD-K`)

**7.1 The naive comparison is confounded.**
- S1/S4a beat S2: 0.65 vs 0.48, discordant pairs 60 vs 27, exact p =
  0.0005 (exploratory).
- But S2 never reads the decisions, while `a*` escalates on severity. So
  this mostly measures that *confidence is a poor severity detector*.

**7.2 The fair question: does confidence add anything beyond the
decisions?**
- Starting from `F(decisions)`, also escalate the `k` least-confident
  instances, for every `k`. The result never beats the decisions alone,
  and ranks the missed serious bugs at chance (AUROC 0.49–0.50).
- At a fixed 10% budget scored by cost, confidence-ranked overrides cost
  *more* than random ones: 390 vs 357, p ≈ 0.05.
- Per-primitive normalization (5h) was at chance: 360.
- Composed confidence barely flags decision errors (AUROC 0.54–0.59).

[mozilla_exploratory_analysis.md E1–E6]

**7.3 A structural reason in this chain.** The only discriminative
confidence (`choice`, AUROC 0.90) belongs to the one node `F` doesn't
use. The informative signal never reaches the action.

**Kernel:** `TBD-K`. In the smoke test the naive strategy ranking reversed
(S2 12/24, S5 14/24 vs S1 9/24). At n = 24 this is noise-level, but it is
reported whichever way the full run goes.

**Status.** Everything in §7 is post hoc and hypothesis-generating. The
confirmatory test is pre-registered (§10).

---

## 8. Method: audits that caught defects

| Defect | Detected by | When |
|---|---|---|
| A "primitive-aware" arm structurally identical to the baseline | Inspecting the action rule | Before evaluation |
| A trigger firing on about 90% of inputs | Selectivity on input signals only | Before evaluation |
| A threshold sensitive to the data distribution | Smoke test vs. pilot | Before the full run |
| Four silent runner defects (e.g. "None" shown to the model, partial data analyzed) | Adversarial probing | Before the live run |
| Confidence-vs-decisions confound | Post-hoc review | After the Mozilla result |
| Template content: labels recoverable from punctuation; evidence leaking across labels | Independent reviewer agent | Before the controlled study |

**Recommendation.** For each arm, ask "can this arm be right on each
target class, and through what information?" before any result exists.

---

## 9. Limitations

- **Generality:** one API at one model version, in one domain.
- **References aren't truth:**
  - Mozilla triage labels exclude re-triaged bugs (a selection bias);
  - kernel labels are reporters' claims;
  - kernel "normal" is a default value.
- **Small constructed samples.** The `choice` subgroup is 6 items;
  `noul` was 24/24.
- **The target is constructed.** `a* = F(...)` is a target we built,
  not a measured outcome. Strategy results are conditional on it.
- **Memorization:** possible for old bugs. The recent subsets are small
  (Mozilla 54, kernel 35).
- **Twelve protocol revisions.** All are dated, disclosed and made before
  the relevant data existed, but they are numerous.

---

## 10. Pre-registered follow-up (not yet run)

Protocol Revision 12.1, on deterministic template content (grammar Draft
4, 3,103 audited units):
- **H1:** 2h vs. random overrides at a 10% budget, scored by cost.
- **H2:** 5h vs. 2h, with sign-flip randomization clustered by service.

Both are Holm-corrected. N is sized from a second calibration pilot, with
a ceiling of 720. A null H1 is a live outcome, and it would be reported
as the answer to the composition question.

---

## Appendix (to assemble)

- A. Full cost matrix and `F` table.
- B. Strategy definitions and code pointers.
- C. Dataset construction for both trackers (filters, cells, truncation,
  privacy scrubbing).
- D. Mozilla per-cell tables; kernel per-cell tables (`TBD-K`).
- E. Protocol revision log (summary of 12 revisions).
- F. Reproducibility: hashes, model version, call counts (Mozilla 2,424;
  kernel 2,160 + 216 smoke).

## Open items before submission

- [ ] Fill in `TBD-K` from the kernel full run.
- [ ] Verify every citation, and search classical reliability and HCI
  escalation work.
- [ ] Confirm that TypeSafe's terms allow publishing a benchmark of Jev.
- [ ] Prepare the public repository per `research/PUBLICATION_CHECKLIST.md`.
- [ ] Figures: reliability diagrams, the severity confusion matrices, the
  override curve.
