# Stage 0 Report — Construction-Validation Pilot

Executed 2026-09-21. 26/26 calls succeeded (HTTP 200), zero retries, zero
schema mismatches. Per `step0b_design_specification.md` §0: this report
establishes **construction feasibility** and **output feasibility**
only — it draws **no conclusion about H1/H2** (hypothesis evidence is out
of scope for Stage 0 by design).

## Protocol identity

- Manifest: `../data/characterization/stage0_manifest.json`, content hash
  recorded in `../data/characterization/stage0_run_metadata.json` and
  independently in `../data/characterization/stage0_manifest_hashes.json`
  (validator-tracked baseline).
- Manifest validated **before** any call was made:
  `../results/stage0_manifest_validation.txt` (all applicable checks
  PASS — see that file; checks 9-11 correctly N/A, no analysis code
  exists yet).
- Client: `../src/jev_client/` (unchanged since Step 0A). Model resolved
  to the same version observed throughout this project
  (`jev-1.13.0` — recorded per-call in the raw response log, consistent
  across all 26 calls, no drift).
- Code: `../src/build_stage0_manifest.py` (manifest generation, no network
  calls) → `../src/validate_step0b_manifest.py` (validation) →
  `../src/run_stage0.py` (execution, `JevClient`-only). Raw/parsed data:
  `../data/characterization/stage0_{raw,parsed}_responses.jsonl`.
- Timestamp: run metadata records `run_timestamp_utc`; all 26 calls
  completed within one session.

## Construction feasibility

All 10 items (4 `noul`, 3 `choice`, 3 `score`) were schema-valid on every
call. Reference labels were present for all majority-condition items and
`null` for the one contested item, matching `is_contested` in every case
(validator check #4). **One construction-feasibility concern surfaced by
the data itself, requiring review before Stage 1** — see §"Flagged
concern" below. This is reported as a feasibility finding, not acted on
unilaterally (per §0's rule that Stage 0 may not silently redesign Stage
1).

## Output feasibility

**noul (H2a):** value across conditions: 5:0 → 0.970, 4:1 → 0.880, 3:2 →
0.740 (mean), 2:2 → 0.400 (mean) — monotonically decreasing as the
yes:no evidence ratio decreases, and clearly non-identical across
conditions. Repeat range: 0.00 (saturated conditions) to 0.02
(near-majority/contested) — bounded, comparable in magnitude to `choice`'s
previously observed repeat jitter (Step 0A.2: 0.02-0.11).

- H2a(i) direction: **PASS** — monotonic, correct direction (more
  "yes"-supporting evidence → value closer to 1).
- H2a(ii) bounded repeats: **PASS** — observed repeat ranges were
  0.00–0.02 in this pilot, reported descriptively; this is **not** a
  formal cross-primitive statistical comparison against `choice`'s
  previously observed repeat jitter (Step 0A.2) — different primitive,
  different evidence pool, different conditions, mentioned only as
  informal context, not as part of the pass criterion itself.
- H2a(iii) consistent with documented interpretation: **PASS** — all
  values in [0,1], no anomalies.
- **H2a: PASS overall.** Under the tested construction conditions, `noul`
  produced values consistent with its documented directional
  interpretation and showed usable variation with bounded repeat
  differences. **This authorizes H2b to be evaluated in Stage 1; it does
  not establish H2b, and does not validate that `noul` is a calibrated
  confidence measure** — that remains exactly what H2b's Stage 1
  evaluation is for.

**choice (near-majority 3:2), output feasibility:** `g(x)` (top-two
probability gap, mean of 3 repeats) per item: 0.980, 0.793, 0.140 — **not
identical across items** (criterion met), and more than that: a genuine
spread from near-saturated to near-tied. All three items' selected label
matched the majority-sentence-count reference label (`regression`),
including the near-tied item (barely, at ~57%). Repeat ranges: 0.000,
0.020, 0.040 — small and bounded.

- **Output feasibility: PASS.** Unlike the 4-sentence 3:1 ratio
  characterized in Step 0A.1 (which always saturated), the 5-sentence 3:2
  ratio produces real, graded variation — including at least one item
  (`choice_nm_003`) landing near the decision boundary while still
  technically agreeing with its constructed reference label.

**score (near-majority 2:1 adjacent), output feasibility:** `g(x)` per
item: 0.947, 0.893, 0.780 — technically not identical (criterion
narrowly met), but the range (0.78-0.95) is much narrower than `choice`'s
(0.14-0.98), and **all three items' implied level (argmax of
`probabilities`, always level 2) disagreed with the majority-sentence-
count reference label (level 1) in every single case.** This is not
random noise — it is a consistent, one-directional disagreement across 3
independently constructed items.

- **Output feasibility (narrow criterion): PASS** (values are not
  identical).
- **The `score` output-feasibility criterion passed in its narrow
  operational sense because the observed outputs were non-identical. This
  does not establish that the current 2:1 construction, its
  reference-label rule, or its resulting item set is suitable for Stage 1
  evaluation. Construction feasibility remains blocked pending semantic
  review** (below) — the two gates are separate, and a technical pass on
  one does not carry over to the other.

## Flagged concern: the majority-sentence-count reference-label rule is not currently justified for mixed-severity `score` compositions

All three `score` near-majority items were constructed as "2 sentences at
one level + 1 sentence at an adjacent, higher level," with the reference
label set to the **majority-count** level (level 1, per §4's equal-
weight-by-construction rule). In all three items, Jev's returned
distribution instead concentrated heavily on the **single higher-severity
sentence's level** (level 2: 0.97, 0.95, 0.90 probability respectively) —
the opposite of the constructed majority, every time.

This directly echoes Step 0A.2's exploratory H5 observation (`score` may
track the highest-severity sentence present rather than averaging), now
recurring across 3 independently constructed items instead of 1. **This
report does not treat that as confirming H5** — H5 remains explicitly
exploratory (§0/§9) and Stage 0 is not evidence for or against it.

**Supported by this pilot:**

- The three independently constructed items used a majority-count
  reference label of level 1.
- Jev assigned the highest probability to level 2 in every item.
- The level-2 probability was high in all three cases: 0.97, 0.95, 0.90.
- The disagreement was directionally consistent across all three
  constructions.
- The current majority-count rule therefore produces reference labels
  that conflict with the primitive's observed behavior under this task
  formulation.

**Not established by this pilot:**

- That Jev's intended `score` semantics are "maximum severity."
- That majority-count aggregation is universally invalid.
- That `score` implements a formal max-pooling function.
- H5 (which remains exploratory, unaffected by this finding either way).
- That level 2 is the operationally "correct" answer for these items.
- That the higher-severity sentence is always the operationally relevant
  target, in general.

**Decision (per review): Option 3, modified — chosen, not unilaterally.**
Immediate procedural action:

1. **Freeze this Stage 0 result.** The original majority-count labels,
   outputs, manifest hash, and this report are preserved as-is, not
   overwritten by whatever the follow-up below finds.
2. **Mark the mixed-severity `score` items as contested-pending-review** —
   not counted as valid or invalid examples in any Stage 1 accuracy
   calculation until a target rule is established.
3. **Define the semantic target independently of Jev's output** —
   documented task semantics, an explicit operational rubric, independent
   annotation, or a prespecified multi-target analysis. The rule is not
   chosen merely because it matches what Jev returned.
4. **Run a bounded `score` semantic-validation follow-up** (separately
   authorized, not run as part of this report): pure severity anchors,
   mixed adjacent levels, extreme-level mixtures, repeated constructions,
   and order controls — investigating the target construct itself, not
   confirming H5.
5. **Submit a revised `score` Stage 1 specification for separate
   approval**, stating target semantics, contested-item treatment,
   eligibility rules, and whether the resulting analysis is confirmatory,
   descriptive, or exploratory.

Per §0's prohibition, Stage 1's `score` design is **not** finalized until
this sequence completes and is reviewed.

## Failure accounting

Zero failures. 26/26 calls returned HTTP 200 and parsed against the
documented schema with no `parse_notes` (no undocumented fields, no
schema mismatches). No retries were triggered. Nothing to report in a
missingness table this time.

## Gate decision

| Gate | Verdict |
|---|---|
| `noul` H2a (semantic/decision validation) | **PASS** |
| `noul` matched-pool construction feasibility | **PASS** |
| `choice` near-majority (3:2) output feasibility | **PASS** |
| `choice` near-majority construction feasibility | **PASS** |
| `score` near-majority (2:1) output feasibility (narrow criterion) | **PASS**, but see flagged concern |
| `score` near-majority construction feasibility | **FLAGGED — requires review before Stage 1** |

## Non-evidence statement

**Nothing in this report supports or contradicts H1 or H2b.** Stage 0 was
scoped to construction and output feasibility only (§0). The `score`
finding above is reported as a *construction-feasibility* concern (is the
reference-label rule defensible), explicitly not as evidence toward H5 or
any other hypothesis, consistent with H5's exploratory-only status.

## Stage 1 authorization

- **`noul`:** authorized to proceed to Stage 1 as designed — H2a passed
  cleanly on all three sub-criteria.
- **`choice`:** authorized to proceed to Stage 1 as designed — the 3:2
  near-majority condition demonstrably produces graded, non-saturated
  output while remaining consistent with its constructed reference label.
- **`score`:** **not yet authorized.** The near-majority construction
  rule needs a review decision (one of the three options above, or
  another) before Stage 1's `score` item set is generated. Proceeding to
  generate and run `score`'s Stage 1 items on the current rule would risk
  building 30 items around a reference-label rule this pilot has direct
  evidence may not be defensible.

**Recommendation:** proceed to generate and validate Stage 1 manifests for
`choice` and `noul` now; hold `score`'s Stage 1 manifest generation for a
decision on the flagged concern.
