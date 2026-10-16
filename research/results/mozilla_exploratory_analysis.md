# Mozilla full run — exploratory analysis (POST-HOC)

**Status: exploratory, not pre-registered.** Everything here was
computed after the descriptive results had been seen, in response to
review questions. It doesn't revise `mozilla_validation_results.md`. It
isn't confirmatory evidence, and it sets no Step 2 constant. No API
calls were made: it uses the same 2,424 raw responses.

- Code: `research/src/mozilla_exploratory_analysis.py`
- Numbers: `mozilla_exploratory_analysis.json`

## E1. Strategy 2 was never a fair test of confidence composition

`a* = F(regression, level)`. `F` escalates exactly when severity is
level 2 (S1/S2), defers on a level-1 regression, and accepts otherwise.

**The confound:**
- Strategies 1 and 4a apply `F` to the *predicted* labels, so they
  estimate `a*` directly.
- Strategy 2 (Revision 11) **ignores the node decisions entirely**. It
  accepts or escalates from the confidence product alone.
- So to be right on a serious bug, Strategy 2 needs low confidence to
  *mean* high severity. Nothing in the design says it should.
- The 60-vs-27 split therefore mostly compares severity decisions with
  confidence used as a stand-in for severity.

**The size of the gap isn't the inability to defer.** 4a also wins
within both of the other classes:

| Target class | n | S1 | S4a | S2 | S5 |
|---|---:|---:|---:|---:|---:|
| accept | 119 | 89 | 89 | 69 | 68 |
| escalate (serious) | 68 | 39 | 39 | 28 | 26 |
| defer | 15 | 3 | 2 | 0 | 0 |

Exact McNemar tests, exploratory, two-sided:

| Comparison | Discordant pairs | p |
|---|---|---|
| 4a vs 2 | 60 vs 27 | 0.0005 |
| 1 vs 2 | 61 vs 27 | 0.0004 |
| 5 vs 2 | 17 vs 20 | 0.74 |
| 1 vs 4a | 1 vs 0 | 1.0 |

Because of the confound, the 4a-vs-2 p-value says Strategy 2 is a poor
severity detector. It does **not** say that composing confidences is
worse at managing uncertainty.

## E2. The fair question: does confidence add anything *beyond* the decisions?

**Setup:** start from `F(decisions)` (131/202 correct). Among the 139
bugs it didn't escalate, also escalate the `k` least confident ones.
This is reported for **every** `k`, so no `k` is chosen, and compared
with the exact expectation for random overrides.

| k | Confidence product | Strategy 5 U | Random |
|---:|---:|---:|---:|
| 0 | 131 | 131 | 131.0 |
| 5 | 128 | 128 | 128.7 |
| 10 | 124 | 128 | 126.5 |
| 20 | 117 | 124 | 121.9 |
| 30 | 114 | 122 | 117.4 |
| 50 | 114 | 109 | 108.3 |

**Overrides never help.** No `k` beats the decisions alone. Confidence
product or Strategy 5 U ranks the missed serious bugs almost exactly at
random (AUROC 0.49 and 0.50 among the candidates).

**Reading:** on this data, the composed confidence carries no
information about which bugs need escalating beyond what the decisions
already carry.

## E3. Does low confidence flag the bugs where the decisions are wrong?

`a*` doesn't ask this operational question, because it treats "escalate"
as the correct action for a serious bug, not as a remedy for an
uncertain one. `F(decisions)` is wrong on 71/202 bugs.

| Signal | AUROC for flagging an `F` error |
|---|---:|
| Confidence product (low) | 0.54 |
| Strategy 5 U (high) | 0.55 |
| `score` confidence (low) | 0.59 |

Weak on every signal.

## E4. Discrimination vs. calibration, per node

| Node | Own-confidence AUROC for own agreement | Errors | ECE |
|---|---:|---:|---:|
| `choice` | **0.90** | 23 (7 at confidence ≥ 0.90) | 0.05 |
| `noul` | 0.53 | 40 | 0.36 |
| `score` | 0.58 | 95 | — |

**The finding that ties E1–E4 together:**
- **`choice` is the only primitive whose confidence discriminates**,
  and `F` doesn't use `choice` at all.
- So the one informative uncertainty signal in the chain never reaches
  the action, while the two signals that do reach it are close to
  uninformative.
- That is a structural reason, specific to this chain, why confidence
  composition can't help here.

`noul` misses regressions more than it invents them: 23 missed, 17
false alarms.

## E5. `score` error audit (project criteria arm)

**Serious bugs (level 2) rated lower, 29/68:**
- non-crash 22/34 vs crash 7/34. Crash bugs are recognized as serious;
  other S2s mostly aren't.
- network 20/40, storage 9/28.
- long texts (≥ 400 chars) 24/49, short 5/19.
- recent 5/22, older 24/46.
- Level 2 is effectively S2: only 1 bug is S1, so the S1+S2 merge
  doesn't drive this.

**Minor bugs (S4) rated higher, 42/54:**
- network 34/40 (0.85), storage 8/14 (0.57).
- Close to uniform on regression and length.

**`score`'s confidence doesn't vary with the true level:** means 0.65,
0.62, 0.61. Its confidence gives no warning of the compression.

**Not possible:** Jev returns no explanations, so the error audit can't
compare reasoning with labels. A text-level read of the 71 over- and
under-rated bugs would be the next step. It is a manual qualitative pass, not
a statistic.

## Consequences

1. **F4 must be restated (see `findings_synthesis.md`).** The supported
   statements are:
   - a confidence-only gate is a poor severity detector;
   - composed confidence adds nothing beyond the decisions on this data
     (E2), and barely flags decision errors (E3).

   "Decision composition beats confidence composition" overstates what
   the comparison can show.
2. **The same confound is in the Step 2 protocol.** Step 2 uses the same
   `F` and the same Strategy 2, so its primary comparison 2 vs 4a
   inherits the confound. See the Revision 12 addendum (§8): the fair
   comparator is a hybrid arm, `F` plus confidence overrides at a fixed
   rate.

## E6. Revision 12's primary tests, applied descriptively

Revision 12 was adopted after E1–E5. Its constant (`R_OVERRIDE = 0.10`)
was fixed in the proposal addendum before this was computed, and
Mozilla sets no constant. These p-values are **not confirmatory**.

| Quantity | Value |
|---|---|
| `k` overrides (of 139 candidates) | 21 |
| Total cost: `F(decisions)` alone | 361 |
| Total cost: random overrides, exact expectation | 357.2 |
| Total cost: 2h (`conf_product`) | **390** (H1 randomization p ≈ 0.050) |
| Total cost: 5h (Strategy 5 U) | 360 (vs random p ≈ 0.87) |
| 5h vs 2h, paired | 5h lower by 30 total (sign-flip p ≈ 0.046) |

**Reading:**
- `conf_product` ranked *toward* bugs the decisions already got right,
  so it did worse than chance.
- Strategy 5's normalization removed that harm but added no
  information.
- Random escalation itself slightly lowers cost (361 → 357.2). That is
  why H1 compares against R, not against decisions alone.
