# Findings synthesis — what the project has established (C)

Status as of 2026-10-16. This document pulls together the empirical
findings the paper would lead with. Each item gives the evidence, its
source, and how far it can be pushed. No Step 2 evaluation data exists,
so nothing here is a Step 2 result.

## F1. The three primitives report uncertainty in incompatible ways

| Primitive | Synthetic (Stages 0–1, pilot) | Real data (Mozilla, n = 202) |
|---|---|---|
| `choice` | High-confidence errors on constructed ambiguity: mean confidence 0.915, accuracy 0.333, n = 6 | Saturated: 85% of bugs in the ≥ 0.90 band, which agrees 0.96. Its errors sit in the rare low-confidence answers. ECE 0.05 |
| `noul` | Correct 24/24, but confidence below accuracy in every bin | Agreement flat across confidence bands (0.73–0.84). Confidence far below agreement. ECE 0.36 |
| `score` | Confidence moves with sentence order alone (0.173 range on 1 of 3 items) | Confidence ≈ 0.6 everywhere, plus a systematic level bias (F3) |

**Claim:** a workflow can't treat these numbers as one kind of
probability. `noul`'s underconfidence replicates from synthetic to real
data. `choice`'s high-confidence error subgroup does **not** replicate
on real text. The Stage 1 result stands as a property of the
constructed ambiguous items (n = 6), not of `choice` in general.

## F2. Fixed confidence thresholds don't carry over from synthetic to real text

Full account: `threshold_transfer_finding.md`.

| Revision 10 rule | Synthetic pilot | Mozilla smoke (21) | Mozilla full (202) |
|---|---|---|---|
| 4a trigger `choice ≥ 0.90` fires | 27/30 | 19/21 | 85% |
| Strategy 2 (0.5 cut) escalates | 73% (ideal 67%) | 90% (ideal 38%) | 88% (ideal 41%) |

The full run confirmed the smoke-test diagnosis at 10× the sample.
Revision 11 replaced the fixed thresholds with rules that don't depend
on outcomes. **Lesson:** a fixed threshold carries one content
distribution's confidence scale with it. The project's constructed
data was too clean to show this, and only real text did.

## F3. `score` compresses real severity toward the middle

Mozilla, 202 bugs, project criteria:
- 79% of minor (S4) bugs are rated higher than triage [0.67, 0.88];
- 43% of serious (S1/S2) bugs are rated lower;
- overall agreement is 0.53, against 0.40 for always choosing level 1.

Mozilla's own criteria wording helps serious bugs but pushes normal
bugs up; overall 0.56. On constructed items, `score` instead tracked
the most severe sentence. **Scope:** this is agreement with one
project's human triage, which is itself noisy and biased by excluding
re-triaged bugs. It is not "accuracy". It is still a large, consistent
directional bias in both criteria wordings.

## F4. Combining decisions beat combining confidences on real data (descriptive)

On Mozilla, graded against the unvalidated `a* = F(regression, level)`:

| Strategy | P(Y_decision) |
|---|---|
| Decision composition (Strategies 1 and 4a) | 0.65 and 0.64 |
| Confidence product at the same escalation rate (Strategy 2) | 0.48 |
| Per-primitive rank composition (Strategy 5) | 0.47 |

Disagreements between Strategies 2 and 4a split 60 vs 27.
This is **descriptive**: no test was pre-registered on Mozilla, and the
graded target is constructed. Step 2 is where it gets tested (2 vs. 4a
under Revision 11/12). The Mozilla figure sets no Step 2 constant.

## F5. Review process findings worth reporting as method

- A primitive-aware arm (Strategy 3) turned out to be structurally
  identical to Strategy 1, and was caught by inspection (Revision 10).
- A saturated trigger was caught by checking input signals only, before
  any evaluation data existed (Revision 11).
- Probing the runner with adversarial inputs found four silent defects
  before the live run.

These argue for checking how selective each strategy's signal is on
pilot inputs before freezing it.

## How the paper would use these

- **F1–F3** are the contribution and are already supported.
- **F4** is the practical question Step 2 tests under a controlled
  design with real power, using two Holm-corrected comparisons if
  Revision 12 is adopted. Mozilla gives it real-data plausibility, not
  confirmation.

What stays out of scope:
- general calibration claims;
- other domains;
- any statement that `score` is "wrong" rather than in disagreement
  with Mozilla's triage.
