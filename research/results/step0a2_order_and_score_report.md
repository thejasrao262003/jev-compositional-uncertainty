# Step 0A.2 — Order/Repeat Factorial (`choice`) + Matched-Pool Characterization (`score`)

Run: 2026-09-21, 26 live calls (18 + 8). Raw/parsed data:
`../data/characterization/step0a2_order_*`, `step0a2_score_*`. Script:
`../src/run_step0a2.py`. Still strictly observational — no ground truth
attached to any item, no calibration claim made anywhere below.

## 0. Scope and deliberate omission

Per review, this follow-up is narrowly scoped to the two specific questions
raised: (A) is the order effect found in Step 0A.1 a real, reproducible
effect, and can it be decomposed from repeat noise? (B) does the
matched-evidence-pool method (which worked for `choice`) also work for
`score`? **One thing was deliberately not tested here**: a second 2:2
evidence pool for part (A), which would let *content* variability be
estimated alongside permutation and repeat variability. That's a real gap
(see §1.4) and is flagged as still open rather than silently assumed away.

## Part A — `choice` order/repeat factorial

### 1.1 Design

One fixed evidence pool — the exact same four sentences as Step 0A.1's
`symmetric_a`/`symmetric_b` (2 network-flavored, 2 database-flavored,
matched register). 6 prespecified permutations, chosen to *probe* (not
isolate — position, adjacency, pairing, and starting sentence all change
together across these 6 orderings, so no individual mechanism is
separable from this design; see §1.4) a few candidate hypotheses about
*what* in the ordering might matter:

| Permutation | Order | Hypothesis it was intended to probe (not isolated) |
|---|---|---|
| P1 | N1,D1,N2,D2 | pair-adjacent, network-sentence-first in each pair (= Step 0A.1 `symmetric_a`) |
| P2 | D1,N1,D2,N2 | pair-adjacent, database-sentence-first (= Step 0A.1 `symmetric_b`) |
| P3 | N1,N2,D1,D2 | block ordering, all-network-then-database (= Step 0A.1 `high_overlap_a`) |
| P4 | D1,D2,N1,N2 | block ordering, reversed |
| P5 | N1,D2,N2,D1 | cross-interleaved, breaks the pairing structure |
| P6 | D2,N1,D1,N2 | cross-interleaved, different starting sentence |

3 repeats per permutation = 18 calls. All HTTP 200, schema-valid.

### 1.2 Results

| Permutation | `database` probability, 3 repeats | mean | repeat range | selected label(s) |
|---|---|---|---|---|
| P1 | 0.91, 0.92, 0.89 | **0.907** | 0.030 | database, database, database |
| P2 | 0.56, 0.47, 0.45 | **0.493** | 0.110 | database, **network, network** — label flips |
| P3 | 0.69, 0.66, 0.71 | **0.687** | 0.050 | database ×3 |
| P4 | 0.60, 0.54, 0.55 | **0.563** | 0.060 | database ×3 |
| P5 | 0.49, 0.53, 0.45 | **0.490** | 0.080 | **network, database, network** — label flips |
| P6 | 0.80, 0.79, 0.78 | **0.790** | 0.020 | database ×3 |

The **observed permutation range** (max permutation-mean − min
permutation-mean, on the `database`-probability scale; a descriptive
statistic, not a formal effect-size or variance-decomposition estimate) =
**0.417** — a very large spread for changing only the arrangement of four
fixed sentences. Mean within-permutation repeat range across all 6
permutations = **0.058** (range 0.020–0.110) — **the observed permutation
range was approximately 7.2× the mean within-permutation repeat range**
(0.417/0.058 ≈ 7.2; not "an order of magnitude," corrected per review),
confirming Step 0A.1's qualitative read: **permutation variability
dominates repeat variability** for this evidence pool.

P1 (0.907) replicates Step 0A.1's `symmetric_a` (0.91) closely; P3 (0.687)
replicates `high_overlap_a` (0.71) closely — good internal consistency
across the two runs, one day apart, same client/model version.

### 1.3 The sharper finding: near-50/50 permutations flip the selected label under repeat noise alone

P2 and P5 both landed with permutation-mean `database` probability within
0.01 of exactly 0.5 — and in both cases, **the actual selected `choice`
label changed between repeats of the identical request** (P2: database,
network, network; P5: network, database, network).

**Precise claim (per review, stated at the scope this evidence actually
supports):** in the tested evidence pool, repeated evaluations of
presentations whose mean `database` probability was near 0.5 produced
categorical decision flips. This indicates that downstream policies
treating `choice` as a deterministic discrete decision should account for
repeat-level instability near the observed boundary. **This is not a
claim that Jev is generally nondeterministic, nor an estimate of a
population-wide flip rate** — 6 permutations with 3 repeats each (2 of
them near-boundary) is sufficient to characterize that the phenomenon
exists, not to estimate how often it occurs across the input space.

Permutations away from the boundary (P1, P3, P4, P6) never flipped labels
across their 3 repeats, and their repeat ranges (0.02–0.06) were
comparable in magnitude to P2/P5's repeat range (0.08–0.11) — **the noise
magnitude itself doesn't look dramatically larger near the boundary; the
*consequence* of that noise (a label flip) is what differs**, because
only near-boundary permutation-means are close enough to 0.5 for ordinary
jitter to cross it.

### 1.4 Order effect: observed association versus identified mechanism

Per review, this section is deliberately conservative. What this follow-up
establishes: **changing the order of a fixed four-sentence evidence set
was associated with large, reproducible-in-direction differences in
Jev's output** (permutation means ranging 0.49–0.91 on the `database`-
probability scale, each mean itself estimated from 3 repeats so it isn't
just single-call noise). What it does **not** establish: *why*. Candidate
mechanisms — position/primacy, recency, adjacency/local-pairing effects,
or something about how specific sentence pairs interact — are not
distinguishable from these 6 permutations of one fixed pool, because
permutation and "which sentences are adjacent to which" are confounded
here by construction (changing order necessarily changes adjacency too).
**Content variability was not measured in this follow-up** (only one
evidence pool was tested, per the scoping decision in §0) — so it's also
not yet possible to say whether this magnitude of order-sensitivity is
typical for 2:2-balanced items generally, or specific to this pool's
content. Both remain open questions, explicitly, rather than resolved.

## Part B — `score` matched-evidence-pool characterization

### 2.1 Design

A 9-sentence pool, 3 sentences pre-labeled per severity level (0 =
cosmetic, 1 = degraded-with-workaround, 2 = blocking), matched register,
same "cosmetic/blocking" rubric as Step 0A.1's `score` items. Explicit
design decisions, stated before running (per review's 5 points):

1. **Intended level of each sentence**: fixed by construction (see script).
2. **Independence vs. reinforcement**: sentences are written as independent
   symptom observations, not phrased to reinforce or reference each other.
3. **Contradictory evidence**: deliberately permitted — several items mix a
   low-severity and a high-severity sentence in the same `state`, which is
   the whole point (testing how `score` aggregates conflicting evidence).
4. **Aggregation relationship**: no assumption made in advance (not assumed
   linear/weighted-mean over sentence *labels* — only the documented
   formula for how `score` aggregates the *returned* per-level
   probabilities was assumed, per `../jev_api_notes.md`).
5. **Output properties tracked**: `score`, `probabilities`, `confidence`,
   all three, for every item.

8 items: 2 "clear" (pure level-0, pure level-2), 3 mixed pairs (0v2
contradictory, 1v2 boundary, 0v1 boundary), 1 order-swap of the 1v2 pair,
2 repeats of the 1v2 pair.

### 2.2 Results

| item | condition | score | confidence | probabilities |
|---|---|---|---|---|
| score_clear_L0 | pure level 0 | 0.03 | 0.96 | {0: 0.97, 1: 0.03, 2: 0.0} |
| score_clear_L2 | pure level 2 | 1.99 | 0.99 | {0: 0.0, 1: 0.01, 2: 0.99} |
| score_mix_L0_L2 | contradictory 0+2 | 1.95 | 0.93 | {0: 0.0, 1: 0.05, 2: 0.95} |
| score_mix_L1_L2 | boundary 1+2 | **1.18** | **0.73** | {0: 0.0, 1: 0.82, 2: 0.18} |
| score_mix_L0_L1 | boundary 0+1 | 0.90 | 0.85 | {0: 0.1, 1: 0.9, 2: 0.0} |
| score_mix_L1_L2_swapped | boundary 1+2, order-reversed | 1.09 | 0.86 | {0: 0.0, 1: 0.91, 2: 0.09} |
| score_mix_L1_L2_repeat1 | boundary 1+2, repeat | 1.17 | 0.75 | {0: 0.0, 1: 0.83, 2: 0.17} |
| score_mix_L1_L2_repeat2 | boundary 1+2, repeat | 1.12 | 0.81 | {0: 0.0, 1: 0.88, 2: 0.12} |

### 2.3 Findings

**The matched-pool method works for `score` — Step 0A.1's inconclusive
result is resolved.** `score_mix_L1_L2` (confidence 0.73, meaningful
probability mass on both level 1 and level 2) is genuinely intermediate,
unlike Step 0A.1's narrative-built boundary item (which saturated to
confidence 1.0). The earlier null result was a construction-method
limitation, not a property of `score`.

**Evidence for a "worst symptom dominates" aggregation pattern, not
averaging.** `score_mix_L0_L2` (one trivial cosmetic sentence + one
blocking sentence, in the same input) scored 1.95 with 0.93 confidence —
essentially as if the trivial sentence weren't there at all. If aggregation
were closer to a simple average of the two implied severities (0 and 2),
one would expect something nearer the middle; instead the output tracked
the *more severe* symptom almost completely. This is a single item, one
data point — stated as an observed pattern worth a dedicated follow-up if
it becomes relevant to the paper, not a general claim about `score`'s
aggregation function.

**Order sensitivity also appears in `score`, same direction, smaller
magnitude (in this one pair).** Swapping the two sentences in the 1v2
boundary item moved confidence from 0.73 to 0.86 and the level-2
probability mass from 0.18 to 0.09 — real, but a smaller shift than the
`choice` order effect (§1.2 showed swings across the *entire* 0.49–0.91
range). Only one swapped pair was tested for `score`; this should not be
treated as a precise magnitude comparison against `choice`'s effect, only
as confirmation the same *qualitative* phenomenon exists.

**Repeat variability for the boundary item is modest and did not flip
anything.** `score_mix_L1_L2` and its two repeats: score 1.18/1.17/1.12,
confidence 0.73/0.75/0.81, level-2 mass 0.18/0.17/0.12. Ranges (score:
0.06, confidence: 0.08) are comparable in magnitude to the `choice` study's
repeat noise (§1.2: 0.02–0.11), and this item's point estimate was not
close enough to any decision boundary for the noise to change a
downstream categorical outcome — consistent with §1.3's finding that the
*consequence* of repeat noise, not just its magnitude, is what depends on
proximity to a boundary.

## 3. Descriptive variability breakdown (as requested)

**Terminology note per review:** the quantities below are descriptive
range statistics from one small run, not formal effect sizes or a variance
decomposition (e.g. no ANOVA was fit) — treated and named as such
throughout, not as population-level estimates.

For the `choice` order/repeat factorial specifically (the only part of
this run with a proper repeated-measures structure):

- **Observed permutation range** = 0.417 (database-probability scale) —
  the dominant source of variation observed in this study.
- **Observed repeat range**, mean within-permutation = 0.058 (range
  0.020–0.110 across the 6 permutations) — **≈7.2× smaller** than the
  observed permutation range, but large enough to flip the selected label
  at 2 of 6 permutations whose means sat near the 0.5 boundary.
- **Content variability**: **not estimated** — would require a second,
  independently-constructed 2:2 evidence pool run through the same
  permutation × repeat design, deliberately deferred here (§0) to keep
  this follow-up small. Recommended as a next step only if Step 0B's
  design needs a precise content-variability estimate; not required to
  answer the two questions this follow-up was scoped to answer.

Pooling permutation and repeat variation into one number was deliberately
avoided, per review — they are reported separately above and should stay
separate in any later analysis (e.g. an ANOVA-style variance decomposition
once a properly powered design is run, with content pool as a third
factor).

## 4. Revised Step 0B gate checklist

| Requirement | Status |
|---|---|
| Matched `score` construction tested | **Done** (§2) — works, resolves Step 0A.1's open item |
| Order protocol decided | **Not yet decided** — this run shows order must be either (a) explicitly randomized per item, or (b) treated as its own measured factor (a subset of items run at ≥2 orders). A blanket "pick one arbitrary order per item" policy is now confirmed unsafe. |
| Repeat protocol decided | **Not yet decided** — candidates from review: (A) fixed repeats for every item [simplest, most expensive, no selection bias], (B) two-stage with a preregistered (not confidence-triggered) subset getting repeats, (C) full permutation×repeat for a subset [best for the robustness question specifically, most expensive]. This run used (C) for `choice` and single-call for `score` (aside from one preregistered repeat triplet) — a deliberate, disclosed asymmetry, not yet a policy for Step 0B. |
| Revised budget | **Not yet computed** — needs the order/repeat protocol decision first; must include permutations, repeats, and a pilot reserve for failed/invalid calls. |
| Predefined estimands | **Not yet written** — Step 0B's primary calibration/reliability metrics should be specified in writing before running it, independent of what these follow-ups happened to find. |

## 5. Recommendation

Both requested follow-ups are complete and both resolved their targeted
question: the order effect is real, reproducible in direction, and now
decomposed from repeat noise (though its mechanism remains unidentified,
§1.4); the `score` matched-pool method works and surfaced a possibly
useful secondary finding (worst-symptom-dominates aggregation) worth
keeping in mind for Phase 9's escalation-policy design. **Step 0B should
still not be launched yet** — per §4, the order and repeat protocols need
an explicit decision (not just evidence that they matter), and the
estimands should be written down before, not after, the audit runs. These
are design decisions for review, not further characterization calls.
