# Finding: fixed confidence thresholds did not transfer from synthetic to real text

Date: 2026-10-16. This finding led to Revision 11 of
`research/methodology/workflow_uncertainty_composition_protocol.md`.

## What happened

Revision 10 compared two strategies that both rely on a fixed numeric
confidence threshold:

- **Strategy 2** accepts an instance when `conf_product ≥ 0.5`, where
  `conf_product = choice confidence × 2|noul − 0.5| × score confidence`,
  and escalates it otherwise.
- **Strategy 4a** escalates whenever `choice` confidence is `≥ 0.90`.
  That boundary came from Stage 1's 6-item high-confidence/low-accuracy
  subgroup.

A 10% smoke test of the Mozilla study (21 real Firefox bugs, 252 calls)
showed both strategies escalating nearly every bug. Rechecking the first
calibration pilot (30 synthetic instances) showed the same problem,
milder and unnoticed, because that pilot was used only to estimate a
disagreement rate, never to look at what each strategy actually did.

## The numbers

Everything below uses only the strategies' **input signals**. No label,
correctness score or comparison result was used to diagnose the problem
or to choose the fix.

| Signal | Synthetic pilot (n = 30) | Real Mozilla bugs (n = 21) |
|---|---|---|
| `choice` confidence, median | **1.000** | **1.000** |
| `choice` confidence ≥ 0.90 (4a's trigger fires) | **27/30 = 90%** | **19/21 = 90%** |
| `choice` confidence ≥ 0.98 | 22/30 | 19/21 |
| Distinct `choice` confidence values | 12 | **4** |
| `noul` confidence-like `2|noul − 0.5|`, median | 0.753 | 0.520 |
| `score` confidence, median | 0.625 | 0.607 |
| `conf_product`, median | 0.327 | 0.217 |
| Strategy 2 (Rev 10) escalation rate | 22/30 = **73%** | 19/21 = **90%** |
| Share a perfect accept/escalate policy would escalate (`a* ≠ accept`) | 67% (design: 6 of 9 cells) | 38% (8/21; 41% on the full 202) |

## Why each threshold failed

**4a's `choice ≥ 0.90` trigger was broken on both kinds of data.**
`choice` confidence is saturated: its median is exactly 1.0 on synthetic
and real text alike, and real text produced only 4 distinct values. A
trigger that fires on 90% of inputs carries almost no information about
*which* inputs to escalate. No other cut-off on this signal can fix that,
because the inputs it would need to separate share the value 1.0. The
Stage 1 subgroup the threshold came from (mean confidence 0.915, n = 6)
sat inside a spread of confidences. In this workflow there is no spread
left to sit inside.

**Strategy 2's 0.5 cut-off happened to fit the synthetic data and didn't
fit real data.** On synthetic data it escalated 73% of instances, close
to the 67% a perfect binary policy would. On real bugs it escalated 90%
against 38%. The cause is the inputs, not the rule: real bug text pulls
`noul` toward the middle (median `2|noul − 0.5|` falls from 0.75 to
0.52), which pulls the product down. An absolute cut-off in confidence
units bakes in one content distribution's scale.

**The consequence for Revision 10's only main comparison.** With both
strategies escalating nearly everything, "Strategy 2 vs. 4a" compared two
escalate-almost-always policies. On the smoke test both scored exactly
7/21, the share of bugs whose correct action is "escalate". That would
have been the experiment that sets N = 733 (about 6,600 calls).

## The fix (Revision 11), and why it isn't tuning

| Strategy | Revision 10 | Revision 11 |
|---|---|---|
| 2 | accept iff `conf_product ≥ 0.5` | escalate exactly `⌈q·n⌉` instances with the lowest `conf_product`; accept the rest |
| 4a | escalate if repeat-unstable **or** `choice ≥ 0.90`, else `F` | escalate if repeat-unstable, else `F`. The `choice` trigger is removed |

- **`q` isn't fit to model output.** It is the share of instances whose
  target action isn't "accept": 6/9 by construction for Step 2's
  balanced design, and the label base rate for Mozilla. It makes
  Strategy 2 escalate as often as a perfect accept/escalate policy
  would, so a comparison measures *which* instances each strategy
  escalates rather than *how many*. For Mozilla this uses the
  evaluation labels' marginal (not which bug has which label), which is
  disclosed as such.
- **A rank-based rule carries over by construction.** It doesn't depend
  on the confidence scale, which is exactly what changed between
  synthetic and real text.
- **Removing the 4a trigger follows from saturation alone.** The trigger
  fired on 90% of both datasets, which needs no labels to establish.
- **Neither change was chosen by comparing strategy results**, and none
  was iterated. The Revision 11 results below were computed once,
  afterwards.

## What Revision 11 does on the same smoke-test data (no new calls)

| | Rev 10 S2 | Rev 10 S4a | Rev 11 S2 | Rev 11 S4a | S1 (unchanged) |
|---|---:|---:|---:|---:|---:|
| Not auto-accepted (escalate or defer) | 19/21 (90%) | 20/21 (95%) | **8/21 (38%)** (= q) | 9/21 (43%) | 9/21 (43%) |
| …of which escalated | 19 | 19 | 8 | 3 | 3 |
| `P(Y_decision = 1)` | 7/21 | 7/21 | 7/21 | 14/21 | 14/21 |

Read these as a check that the rules behave as specified, **not** as
results. n = 21, and the main Step 2 experiment uses synthetic content,
not this data.

## Costs of the fix, stated plainly

1. **4a is no longer primitive-aware.** With the `choice` trigger gone,
   4a is `F` plus repeat-instability escalation. Repeat instability is
   rare (2/30 synthetic, 0/21 real), so 4a is almost identical to
   Strategy 1, and both scored 14/21 here. The main comparison, 2 vs. 4a,
   now tests **naive confidence composition at a matched escalation rate
   against decision-based composition**. That's a real question, but
   not "does a primitive-aware trigger help". Each trigger this protocol
   has tried for primitive awareness has failed on inspection: Strategy
   3's (Revision 10) and now 4a's.
2. **Strategy 2 still can't produce "defer" or "request more evidence".**
   Its accuracy is capped by the share of instances whose target is one
   of those. That cap existed in Revision 10 too.
3. **The Revision 10 sample size (N = 733) is void.** It came from a
   disagreement rate measured under the old strategy definitions. The
   planned second calibration pilot will measure it again under the
   Revision 11 definitions.
4. **Strategy 2 is now batch-relative.** It ranks within the evaluated
   set, which suits a fixed-escalation-rate evaluation. A deployed
   version would need a calibration batch.

## Lesson for the paper

A numeric confidence threshold is a statement about one content
distribution's confidence scale. Here it carried over from synthetic to
real text only by coincidence (Strategy 2) or not at all (4a). Composition
rules for heterogeneous primitives should be defined by rank or matched
escalation rate, or checked for selectivity on the target distribution,
before they are compared. The project's own constructed data was too
clean to show this. Real data showed it in 21 bugs.
