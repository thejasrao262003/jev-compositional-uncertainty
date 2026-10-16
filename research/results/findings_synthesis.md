# Findings synthesis — what the project has established (C)

Status as of 2026-10-16, **revision 2** (after two external reviews and
the exploratory analysis in `mozilla_exploratory_analysis.md`). This
document pulls together the empirical findings the paper would lead
with. Each finding is stated with its scope: it holds **for the tested
primitives (`jev-1.13.0`), the tested conditions and these datasets**.
No Step 2 evaluation data exists, so nothing here is a Step 2 result.

**The argument in three layers:**

1. **Characterization (F1, F3).** Structured, well-typed output doesn't
   mean the uncertainty values mean the same thing. Each primitive has
   its own confidence behavior and its own failure mode.
2. **Composition (F2, F4).** How signals are combined matters. Here,
   composed confidence added nothing beyond the decisions, and the one
   informative confidence signal never reached the action.
3. **Validation (Step 2).** Reliability at the workflow level needs its
   own controlled test. Agreement or calibration at the primitive level
   doesn't establish it.

**What this is not:** a general theory of compositional uncertainty. It
is an empirical characterization of how uncertainty representations and
composition rules behave on controlled and real data, plus a method for
catching failure modes before a workflow is evaluated.

## Replication on a second tracker (2026-10-16)

The Linux kernel Bugzilla replication: 240 bugs, reporter-set labels,
2,160 calls, all clean (`kernel_validation_results.md`).

**Replicates:**
- **F1:** `choice` saturated but discriminative (AUROC 0.98); `noul`
  uninformative (AUROC 0.41); `score` flat across levels.
- **F2:** the trigger fired on 96%; the 0.5 cut escalated 78% vs a
  target of 42%.
- **F3, more strongly:** minor bugs rated higher 0.75; serious rated
  lower 0.56.
- **The restated F4:** composed confidence was at chance for choosing
  overrides (AUROC 0.50–0.51), and the sign of 2h vs random flipped
  between trackers, which is consistent with no information.

**Doesn't replicate:** the strength of "decisions beat confidences"
(Mozilla p = 0.0005; kernel p = 0.20; recent kernel bugs reverse it).

**New:** `noul`'s error direction is dataset-dependent. It misses
regressions on Mozilla and over-flags them on the kernel.

## F1. The three primitives behave incompatibly as uncertainty signals

| Primitive | Synthetic (Stages 0–1, pilot) | Real data (Mozilla, n = 202) |
|---|---|---|
| `choice` | High-confidence errors on constructed ambiguity: mean confidence 0.915, accuracy 0.333, n = 6 | Saturated (85% of bugs at ≥ 0.90, agreeing 0.96), but **discriminative**: AUROC 0.90 for its own agreement. ECE 0.05 |
| `noul` | Correct 24/24, but confidence below accuracy in every bin | Agreement flat across bands. AUROC 0.53. Underconfident. ECE 0.36 |
| `score` | Confidence moves with sentence order alone (0.173 range on 1 of 3 items) | Confidence about 0.6 at every true level. AUROC 0.58. Plus a level bias (F3) |

**Claim:** in the observed behavior, these values can't be treated as
interchangeable probabilities. That is not an impossibility result: no
transformation was tried that might make them comparable.

**What replicates from synthetic to real:**
- `noul`'s underconfidence replicates.
- `choice`'s high-confidence error subgroup does **not**. It stands as a
  boundary condition on constructed ambiguous items (n = 6), not a
  general property. Real text still has 7 `choice` errors at
  confidence ≥ 0.90, so such errors are rare, not absent.

## F2. The tested fixed-threshold rules didn't give the selectivity they were designed for

Full account: `threshold_transfer_finding.md`.

| Revision 10 rule | Synthetic pilot | Mozilla smoke (21) | Mozilla full (202) |
|---|---|---|---|
| 4a trigger `choice ≥ 0.90` fires | 27/30 | 19/21 | 85% |
| Strategy 2 (0.5 cut) escalates | 73% (ideal 67%) | 90% (ideal 38%) | 88% (ideal 41%) |

**These are two different failures:**
- **4a's trigger is persistently non-selective.** It fired on 85–90% of
  inputs in *every* setting. That is a design failure, caught only once
  it was measured, not a change between distributions.
- **Strategy 2 is the distribution-sensitivity evidence.** Its fixed
  cut came close to the ideal rate on synthetic data (73% vs 67%) and
  far from it on real data (88% vs 41%).

**Claim:** the tested fixed rules didn't transfer as intended. Revision
11's outcome-independent rules avoid this particular failure. They are
not thereby shown to be robust in general. Not claimed: that fixed
thresholds never transfer.

## F3. `score` disagrees with Mozilla triage in a middle-seeking direction

Mozilla, 202 bugs, project criteria:
- 79% of minor (S4) bugs are rated higher than triage [0.67, 0.88];
- 43% of serious (S1/S2) bugs are rated lower;
- overall agreement is 0.53, against 0.40 for always choosing level 1.

The exploratory audit (E5) adds:
- serious bugs that are crashes are mostly recognized (7/34
  underrated), while non-crash ones mostly aren't (22/34);
- network S4 bugs are overrated more than storage S4 bugs (0.85 vs
  0.57);
- `score`'s confidence doesn't vary with true level, so it gives no
  warning of the bias.

**Wording arm.** Mozilla's own criteria help serious bugs but push
normal bugs up; overall agreement 0.56. The criteria influence the
behavior, but the mechanism isn't isolated.

**Scope:**
- This is systematic disagreement with one project's human triage, not
  ground-truth severity error.
- Triage labels contain judgment calls.
- **Selection limitation:** bugs whose severity was revised were
  excluded, which biases agreement upward and removes exactly the
  contested cases.
- Level 2 is effectively S2 (S1 n = 1), so the S1+S2 merge isn't
  driving the result.
- Under-rating serious bugs and over-rating minor ones have different
  costs in practice. No cost function was evaluated.

## F4. Composed confidence added nothing beyond the decisions (exploratory)

**Superseded statement (revision 1, kept for the record):** *"Combining
decisions beat combining confidences on real data … Strategies 1/4a
0.65/0.64 vs Strategy 2 0.48; disagreements 60 vs 27."* The numbers are
correct but the claim overstates them:
- Strategy 2 ignores the node decisions and uses confidence as a
  stand-in for severity.
- `a*` escalates on severity, so most of the gap is built into the
  comparison (E1).

**Restated, on Mozilla, graded against the constructed `a*`; all
exploratory:**
- **A confidence-only gate is a poor severity detector.** 4a beats 2,
  60 vs 27, with an exploratory exact p of 0.0005. 4a also wins within
  the accept and escalate classes, not only on defer.
- **Confidence adds nothing on top of the decisions.** Escalating the
  `k` least-confident bugs on top of `F(decisions)` never beats the
  decisions alone, at any `k`. It ranks the missed serious bugs at
  random (AUROC 0.49–0.50) (E2).
- **It barely flags decision errors.** AUROC 0.54–0.59 (E3).
- **Structural reason, specific to this chain:** the only discriminative
  confidence (`choice`, 0.90) belongs to the one node `F` doesn't use
  (E4).

- **Under Revision 12's frozen tests (applied descriptively):**
  `conf_product` overrides cost *more* than random ones (390 vs 357),
  and Strategy 5's were at chance (E6).

**Evidential status:** hypothesis-generating. It doesn't share F1–F3's
standing because it came from the same data and the target is
constructed. **It also changes Step 2:** Step 2's 2-vs-4a comparison had
the same confound. Revision 12, now adopted, replaces it with H1 (2h vs
random overrides) and H2 (5h vs 2h) on cost. Confirmation is reserved for Step 2 under the frozen
protocol, whichever way it comes out.

## F5. Method: audits that caught defects before evaluation

| Defect | How detected | Change made |
|---|---|---|
| Strategy 3 structurally identical to Strategy 1 | Inspection of the action rule | Revision 10 |
| 4a trigger non-selective (fires on about 90%) | Selectivity on input signals only, before evaluation data | Revision 11: trigger removed |
| Strategy 2 threshold distribution-sensitive | Same check, smoke test vs pilot | Revision 11: fixed-rate `q` |
| Runner: "None" shown to the model, partial data analyzed, biased upward-lean rate, uncounted failures | Adversarial input probing | Fixed, with tests, before the live run |
| Strategy 2 ignores decisions while `a*` is severity-defined | Post-hoc review of the Mozilla comparison | Revision 12 (adopted): H1/H2 on cost |

These are methodological lessons, not evidence that any composition
method works. The last row is a cautionary case: the audit happened
*after* a result was in. It would have been caught earlier by asking,
for each arm, "can this arm be right on each target class, and through
what information?"
