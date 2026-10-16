# Mozilla real-data validation — results (Part A)

Run 2026-10-16 under `mozilla_realistic_validation_proposal.md`
(Revision 3). Descriptive only: no hypothesis tests, as pre-registered.
Raw data is in `research/data/mozilla/mozilla_validation_raw_responses.jsonl`.
Every figure here is in `mozilla_validation_execution_manifest.json`.

**Run quality.** 202 bugs × 12 calls = 2,424 calls. All returned HTTP 200
and parsed against the schema. One transient retry recovered on its own.
`jev-1.13.0` throughout; mean latency 0.63 s. Every bug has all 3
repeats on all 4 arms. No failed nodes, so Strategy 1's undefined-`noul`
edge case never occurred. Repeat instability: `choice` 1/202, `score`
2/202, wording arm 9/202.

**How to read the numbers.**
- "Agreement" means agreement with Mozilla's triage labels, not
  accuracy.
- The sample is balanced at 40 per cell, so pooled figures describe
  this design, not real-world rates.
- Excluding bugs whose severity was revised biases agreement upward
  (proposal §2.3).
- Strategy scores are graded against `a* = F(regression, level)`, which
  is not externally validated.

## Per node

| Node | Agreement (Wilson 95%) | Trivial baseline | Read |
|---|---|---|---|
| `choice` (network vs storage) | 179/202 = **0.89** [0.83, 0.92] | always "network": 0.59 | Strong. On the 75 texts without subsystem cues: 0.84 |
| `noul` (regression?) | 162/202 = **0.80** [0.74, 0.85] | always "no": 0.74 | Only modestly above always "no" |
| `score` (severity) | 107/202 = **0.53** [0.46, 0.60] | always level 1: 0.40 | Weak; systematically compressed (RQ-A1) |
| `score`, Mozilla's wording | 113/202 = **0.56** [0.49, 0.63] | — | Different errors, similar total |

The subsets barely move these. The recent-12-months subset (n = 54)
scores 0.91 / 0.81 / 0.63, so there is no sign that older, possibly
memorized bugs inflate agreement. The cue-free subset costs `choice`
about 5 points, so keyword leakage is minor.

## RQ-A1 — does `score` over-rate minor bugs? **Yes, strongly. It also under-rates severe ones.**

| True level (Mozilla) | Rated higher than Mozilla | Confusion (modal Jev level) |
|---|---|---|
| 0 (S4, minor/cosmetic) | **42/53 = 0.79** [0.67, 0.88] | 11 at 0, **35 at 1**, 7 at 2, 1 unstable |
| 1 (S3, normal) | 15/79 = 0.19 [0.12, 0.29] | 7 at 0, 57 at 1, 15 at 2, 1 unstable |
| 2 (S1+S2, serious) | — (no higher level) | 1 at 0, **28 at 1**, 39 at 2 |

`score` pulls toward the middle level. 79% of minor bugs are rated
higher than triage, and 29/68 = 43% of serious bugs are rated *lower*. The
network S4 cell is the most extreme: 34 of 40 rated higher.

**Mozilla's own wording reduces the effect but doesn't remove it.** In
the wording arm, minor bugs are rated higher 66% of the time [0.52,
0.78] and serious bugs are now mostly placed correctly (54/66), but
normal bugs get pushed up (36% vs. 19%). So the lean is partly a
criteria-wording effect and partly a property of `score`.

**Synthetic vs. real.** On constructed items, `score` tracked the most
severe sentence (Phase B: 6/6) and never gave a cosmetic item level 0
(pilot). On real bug text it compresses toward the middle instead.

## RQ-A2 — are high-confidence `choice` errors real? **Not on real data.**

| `choice` confidence band | n | Mean confidence | Agreement |
|---|---:|---:|---:|
| [0.00, 0.25) | 7 | 0.10 | 0.29 |
| [0.25, 0.50) | 7 | 0.38 | 0.14 |
| [0.50, 0.75) | 9 | 0.57 | 0.67 |
| [0.75, 1.00] | 179 | 0.99 | **0.95** |

The ≥ 0.90 band covers 172 bugs, with mean confidence 0.995 and
agreement **0.96**. Stage 1's high-confidence/low-accuracy subgroup
(n = 6) doesn't recur. On real text, `choice` confidence is saturated
(it sits in the top band for 85% of bugs) and the rare low-confidence
answers are where its errors are. So it's informative, but only as a
"this one is shaky" flag on a small minority. ECE 0.05 (equal-width) and
0.03 (equal-mass).

## `noul` calibration

Agreement is flat across `noul`'s confidence-like bands (0.73, 0.83,
0.84, 0.71). How decisive `noul` sounds says almost nothing about
whether it is right. Its confidence-like value `2|noul − 0.5|` mostly
sits far *below* its agreement rate (mean 0.12 in a band agreeing 0.73).
So the ECE of 0.36 (equal-mass 0.34) reflects underconfidence plus a
flat curve, not overconfidence. Only 1 of 202 bugs reaches ≥ 0.90.

## RQ-A3 — strategies (descriptive; counts, not tests)

| Strategy | `P(Y_decision = 1)` | Not auto-accepted |
|---|---|---:|
| 1 — decision composition (`F`) | **131/202 = 0.65** [0.58, 0.71] | 86 |
| 4a (Rev 11) — `F` + repeat instability | **130/202 = 0.64** [0.58, 0.71] | 86 |
| 2 (Rev 11) — confidence product, escalate q = 0.41 | 97/202 = 0.48 [0.41, 0.55] | 83 |
| 5 (proposed) — per-primitive ranks, same q | 94/202 = 0.47 [0.40, 0.53] | 83 |
| 2 (Rev 10, fixed 0.5) | 75/202 = 0.37 | 177 |
| 4a (Rev 10, `choice ≥ 0.90`) | 81/202 = 0.40 | 183 |

- **Combining decisions beat combining confidences by about 17 points.**
  Of the bugs where Strategies 2 and 4a disagreed on correctness, 60
  went 4a's way and 27 went Strategy 2's. This isn't caused by Strategy
  2's inability to say "defer": only 15 bugs (7%) have "defer" as their
  target, so its ceiling is 0.93.
- **Per-primitive normalization (Strategy 5) didn't help here.** Its
  disagreements with Strategy 2 split 17 vs. 20. Strategy 5's rule
  excluded `choice` as saturated, so it ranked by `noul` and `score`
  only, and `noul`'s confidence carries no information (above).
- **The Revision 10 thresholds were much worse on real data** (0.37 and
  0.40), as the threshold-transfer finding predicted. Strategy 2 at 0.5
  escalated 88% of bugs, and 4a's trigger fired on 85%.

## What this does and doesn't establish

It **does** establish, on 202 human-triaged real bugs:
- `score` compresses severity toward the middle;
- `choice` is accurate, and its confidence is saturated but accurate at
  the top;
- `noul`'s confidence is uninformative;
- with these primitives, combining their decisions beat combining their
  confidences.

It **doesn't** establish general calibration, behavior outside Firefox
networking and storage bugs, or anything about Step 2. Step 2 uses
synthetic content, and this data sets no Step 2 constant, per proposal
§4. The strategy comparison is descriptive, not a test.
