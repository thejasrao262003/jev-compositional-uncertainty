# Intervention test — results

**Pre-registration:** `research/methodology/intervention_test_preregistration.md`
(committed `751176c`, before any cost outcome was computed).
**Code:** `research/src/intervention_test.py`. **Numbers:**
`intervention_test.json`.

**Setting:**
- 500 held-out bugs per model;
- 50 reviews (10% budget);
- a review = escalation to a human;
- the frozen cost table plus 1 unit of human cost per escalation;
- rankings from training data or the case itself;
- exact expectation over ties.

## Total cost (lower is better)

| Model | No review | A1: cost-aware action rule | A2: raw action error rate | E: `E_dec` | B: low confidence | B2: low product | C: random | Candidates (non-escalated) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Jev 1.13 | 658 | **683.7** | 713.9 | 713.9 | 688.0 | 681.0 | 693.5 | 363 |
| OpenJev 27B | 660 | 688.5 | 721.6 | 721.6 | **674.0** | 701.0 | 700.8 | 314 |
| Qwen2.5-7B | 903 | 913.5 | 913.5 | 910.0 | 912.0 | 911.0 | 911.1 | 80 |
| Phi-3.5 | 831 | 898.4 | 898.4 | 897.9 | **890.0** | 890.0 | 898.5 | 63 |
| OLMo-2-7B | 893 | 916 | 916 | 916 | 916 | 916 | 916 | 17 |

## Pre-registered tests (Holm across 10, one-sided α = 0.05)

| Model | I1: A1 beats random | I2: A1 beats confidence |
|---|---|---|
| Jev | **−9.8 [−17.4, −2.6], supported** | −4.3 [−39.6, +36.9], not supported |
| OpenJev | **−12.2 [−22.2, −3.6], supported** | +14.5 [−30.9, +55.2], not supported (confidence did better) |
| Qwen | +2.3 [−0.9, +7.0], not supported | +1.5, not supported |
| Phi | −0.1, not supported | +8.4 [0.0, +22.7], not supported (confidence did better) |
| OLMo | 0, not supported | 0, not supported |

**2 of 10 tests are supported.** Both are I1 (beats random), for the two
Jev-style models. **I2 is supported for no model.**

## What it means

1. **At this budget and cost table, reviewing never paid for itself.**
   - Every review arm, for every model, cost *more* than no review at
     all (Jev: 658 with no review vs 681–714 with review). A review costs
     2 units unless it catches a wrongly accepted case. Under this table,
     most of the workflow's errors are cheap (defers and escalations,
     cost 1), so 50 reviews mostly pay 2 to fix nothing.
   - The useful question is therefore *which strategy loses least*. Even
     "loses least" is a policy no one should adopt.
2. **The predictive signal did not become an operational advantage over
   confidence.**
   - The action-level rule beat random selection for Jev and OpenJev
     (about 10–12 cost units, about 1.5–2%).
   - It did not beat confidence for any model. For OpenJev and Phi,
     confidence-ranked review lost the least.
   - Ranking *which actions are wrong* (AUROC) is not the same as finding
     *which reviews save money*. That depends on the cost of each error
     type, not its frequency.
3. **Raw error rate is the worst way to spend a review budget here.**
   - A2 and `E_dec` (both "defer first") lost the most, as reasoned in
     the pre-registration before any outcome was computed.
   - The most error-prone action is a cheap one. The predictive finding,
     taken literally, points reviewers at the wrong cases.
4. **The general instruct models leave nothing to review.** They escalate
   most cases themselves (OLMo: only 17 of 500 not escalated), so a
   review budget barely matters. Their failure is over-escalation, which
   is costly in human time and is not fixed by more review.

## Consequence for the paper

The cross-model *prediction* result stands: actions plus history rank
errors better than confidence. But **it does not translate into lower
cost at a 10% review budget under the frozen cost table.** A deployable
intervention would need to target *expensive* errors, i.e. wrongly
accepted cases, and possibly a different budget or cost structure.
Those are new hypotheses, not this test.

## Limits

- One budget (10%) and one cost table, both frozen in advance. Other cost
  structures (e.g. cheaper review, or costlier wrong defers) could change
  the picture. That is untested, and must not be tuned post hoc on these
  results.
- Reviews are assumed correct.
- The target action is constructed.
- The general models use our prompt/readout, so their candidate sets
  differ structurally.


## Correction after a descriptive follow-up (2026-10-17; `intervention_cost_mechanism.json`, exploratory)

"What it means", point 1, explained the result as "most of the workflow's
errors are cheap". **For the Jev-style models that is wrong.** The text
above is left unchanged; the correction is below.

An **oracle**, which knows held-out outcomes and so is an upper bound, not
a strategy, shows how much a perfect choice of 50 reviews could save:

| Model | No review | Best pre-registered arm | Oracle (perfect 50) | Share of no-review cost from wrong *accepts* | Candidates where review saves |
|---|---:|---:|---:|---:|---:|
| Jev 1.13 | 658 | 681 | **370** (−44%) | 52% | 38 of 363 |
| OpenJev | 660 | 674 | **441** (−33%) | 40% | 29 of 314 |
| Qwen | 903 | 910 | 856 (−5%) | 14% | 14 of 80 |
| Phi | 831 | 890 | 890 | 4% | 4 of 63 |
| OLMo | 893 | 916 | 916 | 1% | 1 of 17 |

**Corrected reading:**
- **Jev-style models: the value exists, the identification fails.** About
  half the cost is wrongly accepted serious or regression bugs, and a
  perfect reviewer could remove a third to almost half of total cost.
  They are 15–16% of accepted cases.
  - The action rule cannot separate them (every accept looks alike).
  - Confidence could not either.
  - So the failure is in *finding the expensive errors within an
    action*, not in the cost structure.
- **General models: the explanation is structural.** Their cost is
  dominated by over-escalation (`escalate → accept`, 518–610 units),
  which more review cannot reduce. Even the oracle saves little.

**This gives the next hypothesis** (new, to be pre-registered and tested
on fresh data): a per-case estimator of *P(wrong accept)*, which bugs
were wrongly accepted, built only from training data. For example, from
the `score` distribution's mass on "blocking" and `noul`'s probability.
Can it capture a meaningful part of the oracle's saving at a 10% budget?
