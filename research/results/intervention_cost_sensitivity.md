# Exploratory cost sensitivity of the intervention test

**Plan:** `research/methodology/intervention_cost_sensitivity_plan.md`
(committed `ca92a3c` before any cell other than the frozen table was
computed).

**Code:** `research/src/intervention_cost_sensitivity.py`.

**Numbers:** `intervention_cost_sensitivity.json`.

**Status:** exploratory and post hoc.
- The pre-registered result (frozen table, m = 1 and h = 1) is the
  primary result and is unchanged.
- Rankings are frozen as computed under the original table.
- The results are point estimates only, with no tests.
- **Self-check:** the (1, 1) cell reproduces every pre-registered arm cost
  exactly.

## Best feasible arm minus no review, near cells

Negative means review pays. Here m is the multiplier on wrong-accept
costs, h is the human cost per escalation, and p* is the break-even
precision for reviewing an accepted case whose target is *escalate*.

| m | h | p* | Jev | OpenJev | Qwen2.5 | Phi-3.5 | OLMo-2 |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0.5 | 0.5 | 25% | +29 | +25 | +21 | +52 | +20 |
| 0.5 | 1 | 33% | +54 | +50 | +46 | +77 | +28 |
| 0.5 | 2 | 50% | +104 | +100 | +96 | +127 | +45 |
| 1 | 0.5 | 14% | **−2** | **−11** | **−18** | +34 | +14 |
| **1** | **1** (frozen) | 18% | +23 | +14 | +7 | +59 | +23 |
| 1 | 2 | 27% | +73 | +64 | +57 | +109 | +40 |
| 2 | 0.5 | 7% | **−69** | **−83** | **−97** | **−2** | +4 |
| 2 | 1 | 10% | **−44** | **−58** | **−72** | +23 | +13 |
| 2 | 2 | 14% | +6 | **−8** | **−22** | +73 | +30 |

## Reading, applied by the pre-stated rule

| Model | Verdict | Near cells where review pays | Cells where A1 beats random | Cells where A1 beats confidence |
|---|---|---|---:|---:|
| Jev | **cost-dependent** | 3 of 9 | 12 of 16 | 12 of 16 |
| OpenJev | **cost-dependent** | 4 of 9 | 12 of 16 | 0 of 16 |
| Qwen2.5 | **cost-dependent** | 4 of 9 | 4 of 16 | 4 of 16 |
| Phi-3.5 | **cost-dependent** | 1 of 9 | 8 of 16 | 0 of 16 |
| OLMo-2 | **cost-robust** | 0 of 9 | 0 of 16 | 0 of 16 |

**What this means:**
1. **The headline intervention conclusion depends on the frozen cost
   table.** The conclusion is that at a 10% budget no feasible strategy
   beats no review. It holds at the frozen table, at all cheaper
   wrong-accept costs (m = 0.5), and at h = 2 for most models.
   - **Where it reverses:** for Jev, OpenJev and Qwen2.5 it reverses when
     wrong accepts cost twice as much (m = 2, h ≤ 1), or when review
     costs half as much (h = 0.5, m = 1).
   - **The mechanism** is the break-even precision. Review pays once p*
     falls to about 14% or below, which is near the share of wrongly
     accepted cases (about 14–16%).
2. **The size of a reversal matters.** Some reversals are a few units,
   for example Jev −2 at (1, 0.5). That is far inside the ±40-unit
   intervals of the original paired tests, so it is not evidence that
   review pays. The m = 2 reversals for the Jev-style models and Qwen
   (−44 to −97) are larger.
3. **The ordering result is more stable than the sign of the
   saving.**
   - The action rule beats random for both Jev-style models in every cell
     except m = 0.5 (12 of 16).
   - It beats confidence for Jev in the same 12 cells, but never for
     OpenJev or Phi-3.5.
4. **The over-escalating general model is unaffected.** OLMo-2 has too
   few reviewable cases (17 candidates) for review to matter, except at
   m = 4.
5. **The case-level feasibility check is not reopened.** Its stopping
   decision was made under the frozen table. By its binding rule it is
   not re-run under other costs.

**What this does not show:**
- Real operational costs are unknown.
- The target action is constructed.
- Reviewers are assumed correct.
- No cell is a validated deployment estimate.

**The defensible statement:** prediction quality did not translate into
a cost benefit under the pre-registered economics. Whether review pays is
governed by the ratio of wrong-accept cost to review cost, relative to
the precision the signals can reach.
