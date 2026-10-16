# Proposed Revision 12 — Strategy 5 and the paper's framing

Status: **ADOPTED 2026-10-16** into the protocol as Revision 12, with §8's hybrid arms, refined on adoption: the primary H1 compares 2h with random overrides (R) rather than with Strategy 1, and both tests use cost. See the protocol's Revision 12 changelog. Original status line: proposal for review, not frozen. Written and committed before
the full Mozilla run's results were examined. The run itself was already
in progress, so this proposal is on record ahead of any result from it.
No Step 2 evaluation data exists.

## 1. The framing decision (recommendation: C, with A and B as its experiments)

After Revision 11, none of the protocol's primitive-aware signals had
held up: Strategy 3 was structurally identical to Strategy 1 (Revision
10), and 4a's trigger was saturated (Revision 11). Three options were
considered:

- **A.** Run Step 2 as Revision 11 left it: confidence composition vs.
  decision composition.
- **B.** Design a genuine primitive-aware rule.
- **C.** Make the empirical findings the contribution.

**Recommended:** the paper leads with **C**. Its findings are saturated
`choice` confidence; fixed thresholds that don't carry over from
synthetic to real text; a structurally empty primitive-aware arm caught
by inspection; and the real-data validation. Step 2 then tests C's
practical claim with two pre-registered comparisons:

| Comparison | Question | Origin |
|---|---|---|
| **2 vs 4a** | Does combining decisions beat combining confidences, at matched escalation rates? | A (Revision 11) |
| **2 vs 5** | Does putting each primitive's signal on its own scale beat multiplying raw confidences? | B, derived from C's own lesson |

## 2. Strategy 5 (B)

Code: `research/src/workflow_strategy5_proposal.py`.

1. **Per-primitive uncertainty:** `u_choice = 1 − conf`, `u_noul = 1 −
   2|noul − 0.5|`, `u_score = 1 − conf`. An undefined signal is treated
   as maximal uncertainty.
2. **Admissibility, judged on the evaluated inputs only:** a signal is
   excluded if one value covers more than half the instances, because a
   signal tied on a majority can't order them.
3. **Normalization:** each admissible signal becomes its rank percentile
   within the set, and they are averaged.
4. **Action:** escalate the `⌈q·n⌉` instances with the highest average
   and accept the rest. Same `q` and action space as Strategy 2.
5. **No admissible signal:** NOT COMPUTABLE, reported as such, never a
   silent fallback.

**Why it counts as primitive-aware:** each primitive's signal is judged
against its own distribution before anything is combined. Strategy 2
multiplies raw numbers on incompatible scales.

**Why 2 vs 5 is a clean test:** same `q`, same inputs, same action
space. The only difference is how the signals are combined.

## 3. Honest provenance

The admissibility rule is **motivated by** having seen `choice`'s
saturation in the smoke test and the synthetic pilot. That is
disclosed, not hidden. What keeps it from being post-hoc fitting:
- it is stated generally (any signal, one threshold, half the
  instances), not as "drop `choice`";
- it uses inputs only, never labels or outcomes;
- it was frozen before the full Mozilla results were examined;
- Step 2's evaluation data, the synthetic content from the template
  grammar, doesn't exist yet.

Whether `choice` is excluded on Step 2 data will be decided by the rule
on that data, not assumed.

## 4. Consequences if adopted

- **Multiplicity:** two primary comparisons. Holm–Bonferroni across the
  pair, family-wise α = 0.05.
- **Sizing:** each comparison's disagreement rate is measured in the
  second calibration pilot (templated content, Revision 11 and 12
  definitions). `N = max(n_required(2v4a), n_required(2v5))` at
  α = 0.025, the conservative Holm first step.
- **Claims:**
  - **2 vs 5 significant:** per-primitive normalization beats raw
    multiplication, on this benchmark.
  - **2 vs 4a significant:** decisions beat confidences at matched
    rates.
  - Neither result establishes external validity. The Mozilla
    descriptive arm (§5) is the only real-data evidence.

## 5. Mozilla's role (and the prohibited-use rule)

Strategy 5 is reported on the Mozilla data **descriptively**, alongside
Strategies 1, 2 and 4a. Mozilla sets no Step 2 constant: Strategy 5's
rule and `q` come from the design, not from Mozilla outcomes. That
respects Tushar's proposal §4.

## 6. Decision requested

Adopt Revision 12 (Strategy 5 added, two primary comparisons with Holm
correction, the paper led by C)? If yes, it is folded into the protocol
before the grammar freeze and the second calibration pilot.

## 7. Addendum after the full Mozilla run (2026-10-16) — not decisive

Added after the run. The text above is unchanged from commit `7c15bd7`.

On Mozilla (descriptive, n = 202):
- Strategy 5 scored 94/202 = 0.47 and Strategy 2 scored 97/202 = 0.48.
- Their disagreements split 17 (5 right) vs 20 (2 right).
- The admissibility rule excluded `choice`, as expected from its
  saturation, so Strategy 5 ranked on `noul` and `score`.
- `noul`'s confidence turned out to be uninformative on this data:
  agreement is flat across bands.

**This must not decide adoption.** Under Tushar's proposal §4, Mozilla
outcomes set no Step 2 design choice. Changing the recommendation
because Strategy 5 did no better here would be exactly the post-hoc
tuning the protocol forbids.

It is still disclosed because it lowers the prior that 2 vs 5 will
show a difference. The likely Step 2 outcome for 2 vs 5 is therefore a
non-significant result. N is sized for an MDE of 0.05, so a true
difference below that would most likely be missed. The paper should be
ready to report that null honestly. The
recommendation in §1 stands as written. Adopt or reject is the
reviewer's decision.

## 8. Addendum: Strategy 2 can't test confidence composition against an `F`-defined target (2026-10-16)

Found in post-hoc review of the Mozilla comparison; details in
`research/results/mozilla_exploratory_analysis.md` E1–E2.

**The problem:**
- `a* = F(c2*, c3*)` escalates on the severity *level*.
- Strategy 2 (and Strategy 5) output accept or escalate from confidence
  alone and never read the decisions. To be right on an escalate
  target, low confidence would have to *mean* high severity.
- Strategies 1 and 4a apply `F` to the decisions, so they estimate
  `a*` directly.

So 2 vs 4a (and 5 vs 4a) mostly measures the information each arm is
given, not the value of composing uncertainty. This holds for Step 2's
designed content as much as for Mozilla, because the same `F` and the
same Strategy 2 are used.

**Proposed fix (for review, not adopted).** Add a hybrid arm, **2h**:
- apply `F(decisions)` as Strategy 1 does;
- then escalate the `⌈r·n⌉` least-confident instances, by
  `conf_product`, that `F` didn't already escalate;
- **fix `r` before any data:** suggested `r = 0.10`. It is a design
  constant chosen for review workload. It must not be chosen from the
  Mozilla curve, which was flat-to-negative at every `r`.

**Primary comparison:** 1 vs 2h. It isolates the question "does
composed confidence add information beyond the decisions?" The 2h
variant using Strategy 5's U in place of `conf_product` (5h) gives
"does per-primitive normalization help?"

**What changes if adopted:**
- 2 vs 4a and 2 vs 5 become secondary and descriptive.
- Holm applies to 1 vs 2h and 2h vs 5h.

**What it costs:**
- The second pilot must measure the discordance rate for 1 vs 2h. At a
  low `r` that rate is small, which keeps N moderate.
- The effect is bounded by `r`. At most `r` of the instances can
  change, so the MDE must be ≤ `r`. With MDE 0.05 and `r` 0.10 that is
  feasible but tight.

**Mozilla prior, disclosed and non-decisive:** confidence overrides
didn't beat random on Mozilla (E2). A null result for 1 vs 2h is the
likely Step 2 outcome. The paper should present it as the test of the
composition question, whichever way it comes out.
