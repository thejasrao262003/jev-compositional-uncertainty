# Case-level review targeting: development and power planning

**Plan:** `research/methodology/case_level_review_development_plan.md`
(committed `82afcf2` before any score was computed).

**Code:** `research/src/case_level_review_dev.py` and
`research/src/case_level_review_power.py`.

**Numbers:** `case_level_review_dev.json` and
`case_level_review_power.json`.

**Data:** the 442 training bugs only. The 500 held-out bugs' Jev outputs
were never loaded. No API or GPU calls were made.

## Development result (training data, quota-sampled mix)

At a 10% budget, total cost (lower is better):

| Evaluation | No review | **P (plug-in)** | L (logistic) | A1 (action rule) | B (low confidence) | Random | Oracle |
|---|---:|---:|---:|---:|---:|---:|---:|
| All 442 (P has no parameters) | 713 | **630** | 608 (in-sample) | 704 | 694 | 716 | 332 |
| Fit on Mozilla, evaluate on kernel | 352 | **312** | 334 | 351 | 363 | 359 | 178 |
| Fit on kernel, evaluate on Mozilla | 361 | **318** | 373 | 354 | 319 | 357 | 178 |
| Repeated 5-fold (mean of 20) | 713 | **630** | 639 | 741 | 694 | 716 | 332 |

**Selection by the pre-stated rule: P.** L did not beat P in either
cross-tracker direction. The file
`frozen_case_review_score_v1.json` (sha256 `82d93045…`) holds P's
definition, frozen.

**Performance on the training mix:**
- P cuts cost by about 12% against no review.
- It captures about 22% of the oracle saving.
- Its AUROC for wrong accepts among accepted cases is 0.69, against 0.57
  for confidence.
- This is the first strategy in the project for which review pays, but
  only on the training mix.

## Power planning: the study as specified is projected to fail

The training bugs were quota-sampled, with many serious bugs. A fresh
batch would be a **natural mix**:
- Mozilla is 8% level 2;
- the kernel is 25% level 2.

The planning simulation:
- reweights the training bugs to each tracker's natural label mix (label
  counts from the held-out manifests; no held-out Jev output is read);
- applies the frozen P unchanged;
- runs the planned paired, tracker-stratified bootstrap with Holm across
  three comparators;
- uses 300 simulated studies per size.

| Fresh bugs (Jev calls) | P − no review | P − A1 | P − B (confidence) | Power, P < no review | Power, P < A1 |
|---|---:|---:|---:|---:|---:|
| 500 (4,500) | +22.9 | −8.1 | +11.9 | 0.00 | 0.02 |
| 750 (6,750) | +30.1 | −15.8 | +16.3 | 0.00 | 0.02 |
| 1,000 (9,000) | +39.2 | −21.3 | +17.3 | 0.00 | 0.03 |

**Mechanism:**
- **Wrong accepts are rare in the natural mix.** There are about 35 wrong
  accepts per 500 bugs (Mozilla about 15 per 250, kernel about 20 per
  250). That agrees with the 38 seen in the held-out oracle analysis, so
  the reweighting looks credible.
- **The precision needed is out of reach.** Under the frozen table, a
  review of an accepted case pays only if more than 2/11 ≈ 18% of the
  reviewed cases are wrong. A score with AUROC about 0.69 does not reach
  that precision when it must spend 50 reviews on a pool where about 14%
  of accepts are wrong.
- **P's advantage over A1 remains** (−8 to −21). Even so, power to show
  it is negligible, and P is projected to lose to confidence.

**Assumption.** Jev behaves within a (group, level) cell as it did on the
training bugs. That cannot be checked without new data.

## Consequence

Spending about 4,500 Jev calls on the confirmatory study **as currently
specified** (10% budget fully spent, frozen cost table, natural mix)
would almost certainly produce a negative result that this simulation
already predicts. **This finding was reached before any fresh data
existed.** Any change to the design (budget, population or stopping
rule) is a design decision that must be made and pre-registered *before*
data collection. It must not be tuned against this simulation.

## Outcome (2026-10-17)

A bounded, pre-registered budget check that varied only the review budget
found no viable design. By its binding stop rule the confirmatory study
was not run (`case_level_review_budget_check.md`).
