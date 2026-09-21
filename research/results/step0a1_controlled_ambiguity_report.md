# Step 0A.1 — Controlled Ambiguity Characterization

Run: 2026-09-21, 12 live calls. Raw/parsed data:
`../data/characterization/step0a1_*`. Client unchanged from Step 0A
(`../src/jev_client/`). Script: `../src/run_step0a1.py` (contains the full
pre-registered criterion-satisfaction matrix, defined before any prompt
text was written, per the agreed design discipline).

**Scope discipline, unchanged from Step 0A:** still strictly observational
— no ground truth is attached to any item, so nothing here is a calibration
claim. The question is narrower and more mechanical: *does the API produce
a measurable, non-degenerate response to a controlled manipulation?*

## 1. Design recap

Two-option `choice` task ("which subsystem is responsible for this
incident: network or database?") built from a fixed pool of 8 matched-
register symptom sentences (4 network-flavored, 4 database-flavored,
~90-110 characters each, same grammatical pattern). Every item uses
identical `instructions`/`criteria` and exactly 4 sentences concatenated
as `state` — **only which 4 sentences, and in what order, varies.** 8
conditions: 2 baseline (4:0 / 0:4), 2 moderate (3:1 / 1:3), 2 high-overlap
(2:2, two different sentence pairs), 2 symmetric (2:2, same two mirrored
pairs, order swapped between the two items). Plus 2 `score` items (one
clear, one intended-boundary) and 2 repeats of one 2:2 item.

## 2. Observed facts

| item | sentence keys (order) | ratio | choice | confidence | probabilities |
|---|---|---|---|---|---|
| baseline_network | N1,N2,N3,N4 | 4:0 | network | 1.00 | network 1.0 / database 0.0 |
| baseline_database | D1,D2,D3,D4 | 0:4 | database | 1.00 | database 1.0 / network 0.0 |
| moderate_network | N1,N2,N3,D1 | 3:1 | network | 1.00 | network 1.0 / database 0.0 |
| moderate_database | N1,D1,D2,D3 | 1:3 | database | 1.00 | database 1.0 / network 0.0 |
| high_overlap_a | N1,N2,D1,D2 | 2:2 | **database** | **0.42** | database 0.71 / network 0.29 |
| high_overlap_b | D3,D4,N3,N4 | 2:2 | network | 0.94 | network 0.97 / database 0.03 |
| symmetric_a | N1,D1,N2,D2 | 2:2 | database | 0.82 | database 0.91 / network 0.09 |
| symmetric_b | D1,N1,D2,N2 | 2:2 | **network** | **0.01** | network 0.50 / database 0.50 (exact tie) |
| symmetric_a repeat 1 | (identical to symmetric_a) | 2:2 | database | 0.85 | database 0.93 / network 0.07 |
| symmetric_a repeat 2 | (identical to symmetric_a) | 2:2 | database | 0.78 | database 0.89 / network 0.11 |
| score_clear_level2 | n/a (narrative) | n/a | score=2.0 | 1.00 | level2 1.0 |
| score_boundary_1_vs_2 | n/a (narrative) | n/a | score=1.0 | 1.00 | level1 1.0 |

All 12 calls returned HTTP 200, matched the documented schema, no errors.

## 3. Findings, most important first

### 3.1 Intermediate confidence is reachable for `choice` — but not the way the "ratio" manipulation predicted

**4:0 and 0:4 saturate to confidence 1.0, as expected. But so do 3:1 and
1:3** — one contradicting sentence out of four was not enough to move
confidence at all in either moderate item. Confidence only became
non-extreme at exactly 2:2 evidence count, **and even then, not
reliably**: `high_overlap_b` (2:2) still came back at confidence 0.94,
barely different from the 3:1/1:3 saturation. **The intended independent
variable (sentence-count ratio) does not cleanly predict confidence** —
it predicts *only the two saturated extremes*; within the 2:2 tier,
something else is doing the work.

### 3.2 Sentence order, not just content, has a large and previously unanticipated effect

`symmetric_a` (order: N1, D1, N2, D2) and `symmetric_b` (order: D1, N1,
D2, N2) use **the exact same four sentences and the exact same mirrored
pairing** — only the position of the first sentence in each pair was
swapped. Result: confidence dropped from **0.82 → 0.01**, and the
probability distribution went from a 91/9 split to an **exact 50/50 tie**.
This is not a small effect — it is the single largest confidence swing in
the entire matrix, produced by the smallest possible input change. This
was not the manipulated variable this pilot set out to test, but it is
the most consequential finding: **any future item-generation method for
Step 0B/Step 2 must treat sentence/evidence order as a controlled
(ideally randomized) variable, not an incidental one.**

### 3.3 Repeated identical calls are NOT bit-identical when confidence is intermediate

Step 0A found 4/4 bit-identical repeats — but that test item had
confidence 1.0. Here, `symmetric_a` repeated 3 times total (original +
2 repeats) gave confidence **0.82, 0.85, 0.78** and database-probability
**0.91, 0.93, 0.89** — the *selected option* was stable (database, all 3
times) but the *magnitude* was not. **Determinism at Jev appears to depend
on how saturated the answer is**: near-certain answers are bit-stable;
genuinely intermediate answers carry real call-to-call numerical noise
(here, roughly ±0.03-0.04 on confidence across 3 samples — not
characterized precisely enough to call a variance estimate, just an
observed range). This has a direct downstream consequence: **Step 0B/Step
2 cannot treat a single call's confidence value as a noise-free
measurement** for items in the intermediate range; some form of repeated
sampling or explicit noise modeling is needed for those items specifically
(saturated items may not need it).

### 3.4 `score`'s one boundary attempt did not elicit spread — but it wasn't given the same construction method as `choice`

Both `score` items came back confidence 1.0. Unlike the `choice` matrix,
the `score` items were built narratively ("about half of requests fail,
most retry successfully") rather than from an explicit matched-sentence
pool the way `choice`'s 2:2 conditions were. **This is inconclusive, not
negative** — it shows narrative-only construction doesn't reliably elicit
intermediate `score` confidence (consistent with §3.1's finding that
narrative "ambiguous-sounding" text doesn't work reliably for `choice`
either), not that `score` is incapable of intermediate confidence. A
proper test needs the same explicit-evidence-pool method used for `choice`,
adapted to a severity rubric (e.g., a fixed pool of symptom sentences each
pre-labeled as supporting level 0/1/2, mixed in controlled ratios).

## 4. Decision-outcome classification (per the agreed 4-outcome framework)

**Outcome 4 applies most precisely, with a correction:** different
primitives *do* behave differently, but the evidence base is currently
asymmetric — `choice` was tested with a strong (explicit evidence-pool)
method and `score` was not. Before this can be reported as a genuine
primitive-level difference, `score` needs the same construction method.
`noul` (from Step 0A) showed intermediate values under plain narrative
construction alone (0.47, 0.42) without needing an explicit evidence pool
— if that holds up, it would suggest `noul` is *easier* to elicit
intermediate uncertainty from than `choice`, which is itself an
interesting, reportable asymmetry, but is based on only 2 `noul` items so
far and needs its own controlled follow-up before being stated as a
finding.

**Outcome 2 also applies:** intermediate confidence for `choice` is
reachable only under a specific, narrow construction (near-even evidence
count, and evidently something about order/content within that count) —
not under general "this sounds ambiguous" prompt-writing, and not under a
1-sentence-out-of-4 imbalance. Step 0B's item-generation method must be
built around the construction that actually works, which is now
identified (matched-count, matched-register evidence pools with order as
an explicit variable) rather than assumed.

## 5. The five-criterion gate, applied honestly

1. **At least one controlled condition produces non-extreme uncertainty —
   PASS.** (`high_overlap_a`: conf 0.42; `symmetric_b`: exact 50/50 tie.)
2. **A meaningful difference between at least two controlled conditions —
   PASS.** (1.00 at baseline/moderate vs. 0.01-0.94 at 2:2 — a large,
   unambiguous difference, though not the difference originally predicted.)
3. **Reproducible behavior under repeated calls — PARTIAL PASS.** Direction
   (which option wins) was stable across 3 repeats; magnitude was not
   (§3.3). Should be stated precisely as "qualitatively reproducible,
   quantitatively noisy," not a clean pass.
4. **An interpretable relationship between the manipulated condition and
   the output — FAILS as originally specified.** The manipulated variable
   (sentence-count ratio) only explains the two saturated extremes; it does
   not explain the variation *within* the 2:2 tier, where order (§3.2) and
   presumably specific sentence content dominate instead. The relationship
   is interpretable only after adding order/content as variables that this
   pilot did not control for.
5. **No evidence the result is an artifact of malformed/edge-case inputs —
   PASS.** All 12 calls were well-formed, HTTP 200, schema-valid.

**Net: 3 clear passes, 1 partial, 1 fail-as-specified but fixable.** This
is not a failed pilot — it succeeded at its actual job (a feasibility
check), which was to find out *whether and how* intermediate confidence is
reachable, and it found a concrete, fixable answer: yes, reachable, but not
via the variable this pilot set out to manipulate, and with previously
unknown order-sensitivity and intermediate-value noise that must now be
designed around.

## 6. What this changes about the Step 0B / Step 2 design (not yet implemented — for review)

- **Item generation must use explicit, matched evidence pools** (as done
  here for `choice`), not narrative "write something that sounds
  ambiguous" prompts — the latter reliably saturates to confidence 1.0.
- **Sentence/evidence order must be an explicit, controlled or randomized
  variable**, not incidental — §3.2 shows it can dominate over evidence
  count. Any Step 0B item at a "balanced" evidence ratio should be run in
  more than one order (ideally several random orders) rather than a single
  fixed arrangement.
- **Repeated calls per item are needed for items in the intermediate
  confidence range**, to characterize (not just assume away) call-to-call
  noise before computing ECE/reliability diagrams — a single call per item
  is likely sufficient for saturated items but not for intermediate ones,
  per §3.3. This changes the ~540-call Step 0B budget estimate: some
  fraction of items will need 2-3x repeat sampling, which was not costed
  in the original design.
- **`score` needs its own matched-evidence-pool construction method**
  before any claim (positive or negative) is made about whether it can
  produce intermediate confidence — the one attempt here used a weaker
  (narrative) method than `choice` got, so the two primitives are not yet
  fairly compared.
- **This does not change Gate A, D from Step 0A** (still pass) and does
  not resolve Gate B (still open by design — the research question).

## 7. Recommendation

**Do not launch the full ~540-call Step 0B design yet.** Two things should
happen first, both small: (a) build and run a matched-evidence-pool
version of the `score` item-generation method (a handful of calls,
mirroring what was done here for `choice`), and (b) decide explicitly how
Step 0B will handle order-randomization and repeat-sampling for
intermediate-confidence items, since both are now confirmed to matter and
neither was budgeted for in the original ~540-call estimate in
`../methodology/pilot_experiment_specification.md`. Once those two design
questions are settled, Step 0B's design can be finalized with a revised
(likely somewhat larger, to afford repeats) call budget and submitted for
approval before running it.
