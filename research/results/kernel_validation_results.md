# Linux kernel replication — results

**Run.** 2026-10-16, under `kernel_replication_proposal.md` Revision 1.
- **Descriptive only,** like Mozilla. §E's tests are exploratory, not
  confirmatory.
- **Data:** 240 bugs × 9 calls = **2,160 calls**. All returned HTTP 200
  and parsed; 1 transient retry recovered; `jev-1.13.0` throughout;
  mean latency 0.85 s. Plus a 216-call smoke test.
- **Sources:**
  - `research/data/kernel/kernel_validation_raw_responses.jsonl`
  - `kernel_validation_execution_manifest.json`
  - `kernel_exploratory_analysis.json`

**How to read it:**
- **Labels are reporters' claims, not triage.** Severity is the
  reporter's own claim, and the regression field is unset ("---", coded
  0) on 94/240 bugs.
- **The sample is balanced at 40 per cell,** so pooled figures describe
  this design, not real-world rates.
- **Strategy scores** are graded against the constructed
  `a* = F(regression, level)`.

## Per node

| Node | Kernel agreement (Wilson 95%) | Trivial baseline | Mozilla (for comparison) |
|---|---|---|---|
| `choice` (network vs storage) | **234/240 = 0.975** [0.95, 0.99] | 0.50 | 0.89 |
| `noul` (regression) | **174/240 = 0.725** [0.67, 0.78] | always "no": 0.808 | 0.80 (baseline 0.74) |
| `score` (severity) | **106/240 = 0.44** [0.38, 0.50] | always level 1: 0.33 | 0.53 (baseline 0.40) |

**`choice`:**
- Subset with no subsystem cues (extended lexicon, n = 26): 21/26.
- Log-dominated texts (n = 41): 41/41.

**`noul`:**
- **Below the always-"no" baseline overall.** It over-flags: 63 false
  alarms vs 3 misses. Recall on true regressions is 43/46. Mozilla was
  the opposite (23 misses vs 17 false alarms).
- **The unset field doesn't explain it** (K3 subset). The false-alarm
  rate is the same on explicit "No" (33/100) as on unset (30/94). On
  bugs with the field set, `noul` beats its baseline: 110/146 vs
  100/146.

## K-A1 — severity compression replicates, more strongly

| True level (reporter) | Rated higher | Rated lower | Confusion (modal Jev level) |
|---|---|---|---|
| 0 (low) | **60/80 = 0.75** [0.65, 0.83] | — | 20 at 0, **54 at 1**, 6 at 2 |
| 1 (normal) | 23/79 = 0.29 [0.20, 0.40] | 5/79 | 5 at 0, 51 at 1, 23 at 2, 1 unstable |
| 2 (blocking/high) | — | **45/80 = 0.56** | 1 at 0, **44 at 1**, 35 at 2 |

**Mozilla:** minor rated higher 0.79, serious rated lower 0.43.

**Against both references** (triage, and the reporter's own claim),
`score` pulls toward the middle level, and on kernel text it under-rates
serious bugs even more. Its confidence is flat across true levels (0.65,
0.62, 0.61), so it gives no warning.

## K-A2 — `choice` confidence: saturated and accurate

| Measure | Kernel |
|---|---|
| Bugs at confidence ≥ 0.90 | 230/240 |
| Agreement in that band | 0.991 |
| ECE | 0.023 |
| AUROC for its own agreement | 0.98 |

Only 2 of its 6 errors are high-confidence. The constructed-data
high-confidence error subgroup doesn't recur, as on Mozilla.

**`noul`:** its confidence-like value is non-monotonic in agreement
(0.69 / 0.93 / 0.67 / 0.58 across bands). AUROC is **0.41**, below
chance, and ECE 0.36. Uninformative, as on Mozilla (0.53).

## K-A3 — fixed thresholds: the transfer failure replicates

| Revision 10 rule | Synthetic pilot | Mozilla | **Kernel** |
|---|---|---|---|
| `choice ≥ 0.90` trigger fires | 27/30 | 85% | **96%** |
| Strategy 2 (cut at 0.5) escalates | 73% (target 67%) | 88% (target 41%) | **78% (target 42%)** |

## K-A4 — strategies (descriptive)

| Strategy | Kernel `P(Y_decision)` | Mozilla |
|---|---|---|
| 1 — `F` on decisions | 129/240 = 0.54 [0.47, 0.60] | 0.65 |
| 4a — + repeat instability | 129/240 = 0.54 | 0.64 |
| 2 — confidence product, q = 0.42 | 114/240 = 0.475 [0.41, 0.54] | 0.48 |
| 5 — per-primitive ranks | 119/240 = 0.50 | 0.47 |
| Rev 10 thresholds (2 / 4a) | 0.37 / 0.34 | 0.37 / 0.40 |

**4a vs 2:**
- 66 vs 51 discordant pairs; exact p = 0.20 (exploratory). Mozilla's
  60 vs 27 had p = 0.0005.
- The kernel gap comes from the accept class (85 vs 78) and defer (9 vs
  0). Escalate is a tie (35 vs 36).

**Recent bugs reverse the ranking:** since 2018 (n = 35), S2 gets 21 and
S1 gets 11. This is a small, post-hoc-looking subset, reported because
it was pre-registered.

## E — exploratory: does confidence add anything beyond the decisions?

**Override curve:**
- **The setup:** start from `F(decisions)` (129 correct), then also
  escalate the `k` least-confident of 175 candidates.
- **The result:** it tracks the random expectation at every `k` (e.g.
  `k` = 20: 124 vs 123.4). AUROC for finding the missed serious bugs is
  0.50 (product) and 0.51 (Strategy 5).

**Flagging decision errors:**
- AUROC 0.47 (product), 0.47 (Strategy 5), 0.53 (`score` confidence).
- These are at or below chance. Mozilla's were 0.54–0.59.

**Revision 12 tests, applied descriptively** (`k` = 24):

| Arm | Total cost | vs. random overrides (358.6) |
|---|---|---|
| `F(decisions)` alone | 352 | — |
| 2h (product-ranked) | **338** | randomization p = 0.18 |
| 5h (Strategy 5-ranked) | 360 | p = 0.95 |

- 2h vs 5h: 5h is higher by 22 (p = 0.07).
- On Mozilla, 2h was *worse* than random (390 vs 357, p ≈ 0.05).

## What replicates and what doesn't

| Finding | Mozilla | Kernel | Status |
|---|---|---|---|
| F1. `choice` confidence saturated but discriminative | yes (0.90) | yes (0.98) | **Replicates** |
| F1. `noul` confidence uninformative | AUROC 0.53 | AUROC 0.41 | **Replicates** |
| F1. `score` confidence flat across levels | yes | yes | **Replicates** |
| F2. Fixed thresholds lose selectivity on real text | yes | yes | **Replicates** |
| F3. `score` compresses severity toward the middle | 0.79 / 0.43 | 0.75 / 0.56 | **Replicates, stronger** |
| F4. Composed confidence ≈ no information about where to escalate | override AUROC 0.49–0.50 | 0.50–0.51 | **Replicates** (≈ chance on both) |
| Naive "decisions beat confidences" (4a vs 2) | 60 vs 27, p = 0.0005 | 66 vs 51, p = 0.20 | **Weaker; not robust** |
| Sign of the 2h-vs-random difference | worse | better | **Inconsistent.** Consistent with chance |
| `noul` error direction | misses | false alarms | **Dataset-dependent** |

**Bottom line:**
- **The characterization findings replicate on an independent tracker
  with a different labeling process.** F1–F3, and the core of F4
  ("composed confidence carries ≈ no information about which cases to
  escalate"), hold on both.
- **The strength of "decisions beat confidences" does not replicate.**
  That claim was already flagged as confounded, so this supports
  stating F4 the restated way, not the original way.
