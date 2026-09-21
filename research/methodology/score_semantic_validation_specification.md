# `score` Semantic-Validation Specification (Revision 7)

Status: **design only — not executed, not approved to execute.** Now on
Revision 7 (full history in the changelog sections below, each labeled
with which revision it documents). Does not reopen or modify the frozen
`choice`/`noul` Stage 1 analysis (`stage1_h1h2b_analysis.md`, bound to
commit `f480613`) and does not authorize any new API call.

## Changelog from Revision 6 (this revision)

Closes out review's remaining requests before moving from implementation-
audit review to semantic-validation review:

- **Verifier audit frozen**: `research/data/characterization/
  score_verifier_freeze_manifest.json` — exact script/spec hashes, the
  full composition-table result, the 8-case boundary matrix, every
  mutation operator and its result (with the shipped-vs-hypothetical
  threshold distinction preserved, not collapsed), the independent
  fixture definitions, the `[1,9,9]→[1,9,1,9]` test-construction history,
  and the documented limitations — all as of this exact tested state. No
  semantic changes follow this freeze; a semantic concern found later is
  a new, separately recorded issue.
- **Dedicated semantic fixture audit added**, distinct from the gate
  implementation audit: `research/results/score_semantic_fixture_audit.md`
  walks all 6 primary compositions individually through an 8-point
  checklist (exactly 4 values; M defined; X from the intended domain; A's
  rounding rule; the M/X/A relationship independently derivable; no
  `M=X=A`; claimed class matches; supplementary item correctly excluded).
  All 6 verified.
- **§8 restructured around the explicit three-tier hierarchy** (verifier
  validity / semantic validity / research validity) rather than a single
  verifier-vs-semantic split — matching review's framing exactly, with a
  status table.
- **Mutation-testing wording split, not collapsed**: the shipped-
  threshold finding (branch is redundant, mathematically proven) and the
  hypothetical-threshold finding (branch matters, explicitly labeled as
  *outside the declared admissible configuration space*, a robustness
  probe, not evidence about production behavior) are now stated as two
  separate claims, per review's exact concern about collapsing them.
- **`[0,0,0,9]`'s scope stated explicitly**: proves the implementation
  distinguishes mode/max/mean from each other; does not and cannot
  establish which one is `score`'s correct semantic target.
- **Test-construction history preserved, not sanitized**: the original
  failing `[1,9,9]` fixture and why it failed are recorded in the freeze
  manifest, not silently replaced by only the corrected version.

## Changelog from Revision 2 (this revision)

**A real bug, not a stale render**: review caught that `(1,1,2)`'s table
row claimed "all three distinct" while its own rounded A value (1) equals
M (1) — only X (2) differs. Checking *all* Revision 2 rows the same way
(not just the one flagged) found this was worse than one mislabeled row:
**with 3-sentence/3-level compositions, only 4 of the 6 "primary gate"
items were even usable — `(0,1,1)` and `(1,2,2)` turned out to have
M=X=A after rounding (zero discrimination, mislabeled as discriminative
in both Rev. 1 and Rev. 2), and only `(0,0,2)` was a genuine 3-way split.**
This was a real design flaw, not a documentation slip — the n=3/3-level
composition space is too small (only 10 possible multisets total) to
supply 6 well-separated discriminative items without collisions.

**Fixed by moving to 4-sentence items** (re-deriving the full composition
table, not patching individual rows): the larger multiset space at n=4
yields 6 genuinely discriminative compositions with zero rounding
coincidences (2 three-way, 4 two-way splits — see §3), plus a cleaner
supplementary tie item. Controls also moved to n=4 for consistency (so
evidence *count* isn't itself a confound between control and
discriminative items — a possibility the n=3 design left unexamined).

**Also added, per review's two final checks**: an explicit, literal
gate pseudocode (§5.2) using integer counts on the fixed denominator=6,
not rates; an explicit unit-of-analysis statement (§5.0) — the primary
gate operates on 6 composition-level modal decisions, never the 18 raw
repeat-level observations directly; and an explicit, justified rule for
how `repeat_unstable` items are handled in the count (they contribute 0
to every candidate's numerator, denominator stays fixed at 6 — stated
rationale: this makes instability cost every candidate equally rather
than letting the denominator shrink to a cherry-picked stable subset).

## Changelog from Revision 3 (this revision)

- **The composition table is no longer hand-derived or hand-checked —
  it's script-generated and script-verified.**
  `research/src/verify_score_semantic_compositions.py` enumerates all 15
  possible 4-sentence/3-level multisets, computes `(M, X, A_unrounded,
  A_rounded)` for each independently, classifies each composition's
  discrimination class from the computed values alone, and asserts that
  classification against every claim this document makes (primary set
  size and composition, zero `M=X=A_rounded` items, 2 three-way + 4
  two-way split counts, supplementary item's M-undefined status and
  exclusion from the primary set). **Ran clean, all assertions pass** —
  output saved as artifacts: `research/results/
  score_semantic_composition_table.csv` (all 15 rows) and
  `score_semantic_composition_verification.json` (the pass/fail record).
- **Supplementary item explicitly tagged `supplementary_contested_tie`**
  in the item spec's `membership` field (§3) — not swept into the primary
  set by a generic "all compositions except controls" filter; the
  verification script asserts this membership tag structurally, not just
  in prose.
- **Gate pseudocode restructured** (§5.2) with an explicit
  `number_of_candidates_at_max_count` check, so "no unique leader" is its
  own visible branch rather than an implicit consequence of the count
  comparison (the underlying logic is unchanged — Revision 3's version
  already handled this correctly by construction — but review asked for
  it to be visible in the code, not just provable by inspection).
- **Failure threshold restated as an explicit integer** ("at least 4 of
  6" spelled out, not left as "majority").
- **`repeat_unstable` reporting requirement added** (§5.0): a fixed table
  of 6 quantities (total primary compositions, stable modal decisions,
  unstable count, per-candidate match counts, per-candidate rates,
  stability rate) that must be reported alongside the gate outcome, so a
  reader cannot confuse semantic mismatch with measurement instability —
  per review's distinction that an unstable item is evidence the
  *experiment* failed to reach a stable decision, not evidence against
  any candidate's semantics specifically.
- **n=4 vs. n=3 non-comparability caution added** (§3): this revision's
  results are not directly comparable to a hypothetical n=3 run except
  for the one deliberately-noted thematic (not literal) link to Stage 0.

## Changelog from Revision 1 (carried forward)

- **Fixed inconsistent gate denominators** (review §1): the primary gate
  now scores all three candidates on the **same fixed 6-item set** where
  M, X, and A are all defined — `(0,1,2)` (M undefined) is moved out of
  the primary gate entirely and reported only as a supplementary,
  two-candidate (X vs. A) comparison. No more mixing 6-item and 7-item
  denominators under one shared "5 of 7" phrase.
- **Made gate outcomes mutually exclusive** (review §2) via an explicit
  **ordered** decision procedure (§5): clarity checked first, then
  failure, everything else falls to ambiguity by construction — no
  match-count combination can satisfy two outcomes.
- **Reframed the 5/6-vs-3/6 threshold as a feasibility-stage design
  heuristic**, not inferential/statistical evidence of a "true" semantics,
  with the candidates' structural overlap (M=X on several compositions,
  etc.) stated explicitly (§5).
- **Defined repeat aggregation and tie handling explicitly** (review §4,
  §5.1): modal `jev_level` across 3 repeats per item, with an explicit
  no-consistent-decision category (not a forced fake mode) and full
  repeat-level data retained and reported, not discarded by the
  reduction.
- **Separated categorical matching (argmax vs. M/X/A) from scalar
  proximity (`score` vs. unrounded A)** (review §5.2) into two explicitly
  distinct analyses — the second is a supplementary diagnostic with its
  own pre-specified distance metric, never substituted into the primary
  gate.
- **Softened the presentation-robustness and single-domain scope
  language** (review §5.3, §5.4) from implied generality to explicit,
  bounded scope restrictions.

## Changelog from Revision 4 (this revision) — genuine implementation audit

Per review's request for an implementation audit rather than another
conceptual pass, both verification scripts were substantially upgraded
and re-run:

- **Independent primitive unit tests added** (`run_primitive_unit_tests`
  in the composition verifier): `round_half_up` and `mode_with_tie_
  detection` are checked against textbook values that have nothing to do
  with score compositions (e.g. `round_half_up(1.5)==2`,
  `mode([9,9,1,1])==None`) *before* those functions are trusted to
  analyze any composition — so a bug in the primitives isn't silently
  "baked into" both the computed table and the hand-transcribed
  `SPEC_CLAIMS` at once, which was a real gap in Revision 4 (the claims
  were transcribed by reading the script's own printed output, not
  independently authored).
- **Real mutation tests added to both scripts**, not asserted in prose:
  the composition verifier deliberately corrupts a claimed discrimination
  class, relabels the supplementary item as primary, breaks the rounding
  rule, and breaks tie-detection — all four corruptions are confirmed
  caught. The gate-logic verifier deliberately disables the tie-check
  branch and perturbs both threshold constants — see §5.2 below for the
  one genuinely interesting finding this turned up (the tie-branch is
  currently outcome-redundant under the shipped constants, proven
  mathematically, not just asserted).
- **A real bug was caught and fixed while building the mutation tests**:
  the first draft of the composition verifier's own "no network
  dependency" check used substring search over its own source file,
  which trivially matched its own forbidden-word list literal (the check
  failed against itself on first run). Fixed with an AST-based import
  check instead of substring search — this bug and fix are reported
  here, not silently corrected.
- **Explicit precedence case** added and tested (review's item B4).
- **Artifact-integrity checks added**: CSV row count and duplicate-key
  checks, a credential-shaped-string scan of both artifacts, and the
  verifier script's own SHA-256 recorded inside the JSON verification
  record (so a later change to the verifier is itself detectable).

All of the above ran clean except the two bugs named above, which were
caught by the very checks being added and then fixed — the intended
purpose of building them.

## Changelog from Revision 5 (this revision)

Four remaining checks from review, all addressed with real code, run, and
re-verified:

1. **Space definition confirmed, not assumed**: `verify_score_gate_logic.
   py` now has an explicit `run_space_definition_check()` — asserts the
   achievable per-candidate match-count range is exactly `{0,...,6}` (7
   values, never `{0,...,7}` which would wrongly include an impossible
   "matched 7 of 6 items" value), and that `7³=343` is therefore the
   *exact* set of logically possible outcome triples for a real 6-item
   primary-gate run, not padded space. Ran clean.
2. **Named boundary matrix added**, 8 individually visible, individually
   asserted cases (leader at `CLARITY_MIN−1`/`CLARITY_MIN`; other
   candidate at `CLARITY_OTHERS_MAX`/`CLARITY_OTHERS_MAX+1`; two
   candidates tied at `CLARITY_MIN`; all three tied at the max; all three
   at/below `FAILURE_MAX`) — not just silently covered by the exhaustive
   sweep. All 8 pass.
3. **Primitive-test independence strengthened, with the provenance issue
   named explicitly**: this project's n=4/3-level domain only ever
   produces quarter-fraction means (`k/4` for `k=0..8`), so *no*
   quarter-fraction round-half-up test is truly independent of the
   domain — stated in the script's own docstring, not glossed over. Fixed
   by adding 7 genuinely out-of-domain values (negative, large,
   non-quarter-fraction) alongside 5 in-domain boundary values now
   explicitly labeled "coincidental, not cherry-picked." Added the exact
   mode-detection cases review named: two-way tie, three-way tie,
   order-invariance (same multiset, different order), and — the one that
   matters most for this whole study — **"max level is not the mode"**
   (`[0,0,0,9] → mode=0`, confirmed in the abstract before ever touching
   a real composition, directly exercising the M≠X property the entire
   candidate-target design depends on). **Building this caught a real bug
   in my own test list**: an order-invariance case I wrote as `[1,9,9]`
   wasn't actually the same multiset as the tie case it was meant to
   re-test (missing a `1`) — caught by running it, not by inspection,
   fixed to `[1,9,1,9]`.
4. **Verifier validity vs. semantic validity, made explicit** — new §9.

## 0. Why this exists, and what it is not

Stage 0 found that `score`'s output, under a 2-sentence-level-1 +
1-sentence-level-2 composition, concentrated heavily on level 2 (0.97,
0.95, 0.90 probability across three independently constructed items) —
directly contradicting the majority-sentence-count reference label used
everywhere else in this project. That finding was correctly reported as a
**construction-feasibility concern**, not evidence for or against H5
("`score` tracks the worst symptom"), because the reference-label rule
itself was never validated for `score` — it was inherited from `choice`/
`noul` without checking whether it fits `score`'s different (ordinal,
not nominal) output space.

**This document's objective**: determine what target semantics `score`
is intended to represent, and whether its output can be evaluated against
a pre-specified reference target — **without assuming the result of H5**,
and without choosing whichever interpretation happens to match Jev's
observed output most closely (that would be circular: fitting the label
to the data, then claiming the data validates the label).

**Explicit non-goals**: this is not an accuracy study, not a calibration
study, not a test of H5, and does not by itself authorize `score`'s
return to a Stage-1-style formal analysis. It produces a gate decision
(§8) — one of several possible outcomes, not a predetermined "yes."

## 1. Recovered documented contract (what's known vs. what's not)

From `research/jev_api_notes.md` / `docs.typesafe.ai`, confirmed live in
Step 0A (bit-exact match):

- **Documented and confirmed**: `score` = the probability-weighted mean of
  level indices, computed *from* the returned `probabilities` distribution
  (e.g. `0×0.0 + 1×0.57 + 2×0.43 = 1.43`). `confidence` = a concentration
  statistic of that same distribution. `legend` maps level index → the
  caller-supplied description. `probabilities` sums to 1.0 across the 2-10
  caller-defined levels.
- **NOT documented anywhere**: *how the model's `probabilities`
  distribution itself is formed from multiple pieces of evidence in the
  input `state`.* This is the entire crux. TypeSafe's docs specify the
  scalar-from-distribution formula (stage (b) below) but say nothing about
  the evidence-to-distribution mapping (stage (a)):
  - **(a) evidence → probability distribution over levels** — undocumented,
    unknown, exactly what this study probes.
  - **(b) probability distribution → scalar `score`** — documented,
    already confirmed (weighted mean).
  Stage 0's finding is about (a), not (b) — the weighted-mean formula
  (b) was never in question; what's unresolved is what (a) is even
  *supposed* to represent when evidence conflicts.

## 2. Candidate target semantics (defined independently of any Jev output)

Each candidate below is a fully specified decision rule computable from
an item's *construction* (the severity levels its constituent sentences
were pre-labeled with) alone — none of them reference what Jev actually
returns.

Let an item be built from sentences with pre-labeled levels
`l_1, ..., l_n` (e.g. a `(0,0,2)` item has two level-0 sentences and one
level-2 sentence).

| Interpretation | Target definition | Decision rule / tie handling |
|---|---|---|
| **Majority-count (M)** | The level receiving the most sentence-votes | `mode(l_1..l_n)`; if no unique mode, **M is undefined for that item — excluded from M's scorable set entirely**, not just from that item's tally |
| **Highest-severity (X)** | The level of the single most severe sentence present | `max(l_1..l_n)`; always unique-valued, never undefined |
| **Severity-weighted-average (A)** | The unweighted mean of sentence-implied levels | `round_half_up(mean(l_1..l_n))` for categorical matching; the unrounded mean is kept separately for the scalar-proximity diagnostic (§5.2) |
| **Risk-sensitive (R)** | A policy-defined loss-minimizing level under an explicit asymmetric cost | Requires an externally supplied loss function — **not definable a priori**; explicitly deferred to the future workflow-policy stage |
| **Contested** | No single target is defensible from current evidence | Fallback if the gate (§5) resolves to ambiguity or failure |

**R stays explicitly out of scope.** This study only adjudicates among M,
X, A (and the fallback "contested").

**Structural overlap, acknowledged explicitly (per review §3B)**: M, X,
and A are not independent candidate models — several compositions make
M=X (any composition with a majority level that is also the maximum,
e.g. `(0,2,2)`), and rounding can make A coincide with M or X on others.
The test-cell design (§3) is built specifically to include compositions
where all three diverge, but the *possibility* of coincidental agreement
on other compositions is a structural fact about these three candidates,
not a flaw introduced by this study — restated at the gate (§5) so the
threshold isn't read as stronger evidence than it is.

**Pre-registered rule, binding on the eventual results write-up**: this
study will **not** select a single winning interpretation because it best
matches observed Jev output. §5 defines the gate mechanically, in
advance — the interpretation(s) that pass are whichever the pre-stated
procedure selects, not whichever "looks right" after seeing the data.

## 3. Independent semantic test-cell design

**4 sentences per item throughout** (controls included) — changed from
Revision 1/2's 3-sentence design after re-deriving the full composition
table found several 3-sentence "discriminative" items were actually
non-discriminative once rounding was checked (§ changelog). Verified by
direct enumeration of all 15 possible 4-sentence, 3-level multisets
(script-checked, not hand-computed):

**Primary gate set — 6 compositions, all three candidates defined and
genuinely distinct-or-partially-distinct on all six (zero rounding
coincidences, verified):**

| Composition `(l_1..l_4)` | M | X | A (unrounded → rounded) | Discriminates |
|---|---|---|---|---|
| `(0,0,0,1)` | 0 | 1 | 0.25 → 0 | {M,A}=0 vs. X=1 |
| `(0,0,0,2)` | 0 | 2 | 0.50 → 1 | M=0, X=2, A=1 — **all three distinct** |
| `(0,0,1,2)` | 0 | 2 | 0.75 → 1 | M=0, X=2, A=1 — **all three distinct** |
| `(0,1,1,2)` | 1 | 2 | 1.00 → 1 | {M,A}=1 vs. X=2 |
| `(0,1,2,2)` | 2 | 2 | 1.25 → 1 | {M,X}=2 vs. A=1 |
| `(1,1,1,2)` | 1 | 2 | 1.25 → 1 | {M,A}=1 vs. X=2 — the closest n=4 analogue of Stage 0's tested composition (Stage 0 used n=3, ratio 2:1; this is the n=4, ratio 3:1 version — **not claimed identical**, thematically related only |

2 genuine three-way splits, 4 two-way splits, **no item where M=X=A**
(the exact defect that made `(0,1,1)`/`(1,2,2)` useless in the n=3
design).

**Supplementary item (not part of the primary gate) — `(0,0,2,2)`**,
`membership: "supplementary_contested_tie"` (an explicit tag in the item
spec, per review — this item is excluded from the primary set structurally,
not by a generic "everything except controls" filter that could
accidentally sweep it in): M is undefined (`0` and `2` both appear
twice, no unique mode) — the n=4, tied-count analogue of every other
primitive's "contested/2:2" condition elsewhere in this project. Reported
separately as an X-vs-A comparison (X=2, A=1.00→1): checks whether Jev
produces a stable decision at all under a symmetric tie, not which
candidate wins.

**Comparability caution (per review)**: this revision's results, once
collected, are **not directly comparable** to what an n=3 run would have
produced — moving from 3 to 4 sentences changes the entire distribution
of possible compositions, ties, and the M/X/A relationship, not just item
length. The one exception is `(1,1,1,2)`, deliberately retained as the
closest *thematic* (not literal) analogue of Stage 0's tested 2:1
composition — stated as thematic only, never as an equivalent replication.

**Control anchors** — `(0,0,0,0)`, `(1,1,1,1)`, `(2,2,2,2)`: all three
candidates trivially agree; confirms the pipeline still produces
saturated, unambiguous output where there is nothing to discriminate.
Not part of the discriminative gate; reported as a sanity check.

**10 compositions total**: 3 control + 6 primary-gate + 1 supplementary —
same total as Revision 1/2, only the specific compositions changed.

**Content-blind construction, applied from the start** (lesson from
Stage 0/Stage 1's caught bugs): one domain, opaque sentence IDs assigned
via a seeded random permutation, zero sentence reuse across items or
across this project's prior manifests — verified by the same
`validate_step0b_manifest.py`-style uniqueness check before any call.

## 4. Evidence-pool construction procedure

- **One domain — an explicit, bounded scope restriction, not a claim of
  generality** (per review §5.4): this study resolves *which target
  interpretation* to test against, not content-variability robustness.
  Stage 0/Stage 1 observed the general order/composition-sensitivity
  phenomenon recur across domains for `choice`/`noul`, but that does
  **not** establish that a single domain is sufficient to characterize
  `score`'s semantic-aggregation behavior in general — the resulting
  interpretation from this pass should be treated as scoped to this
  domain until validated elsewhere, not generalized.
- 4 sentences per item (uniform across controls and discriminative items
  alike — see §3), each independently authored (no reuse, no
  template-duplication) per the 10 compositions in §3.
- Canonical presentation: opaque IDs sorted ascending (same content-blind
  rule as `step0b_design_specification.md` §5).
- **Presentation-order sensitivity is deliberately excluded from this
  pass** — an explicit scope restriction to isolate the evidence-
  aggregation question (per review §5.3), **not** an implication that
  `score` is presentation-invariant. That question remains open and
  would need its own dedicated design if it becomes relevant here.
- Reference labels: **none of M, X, A is written into the item as "the"
  reference_label.** All three (plus A-unrounded) are computed and stored
  as separate, parallel fields in the item spec.

## 5. Pre-registered interpretation gate (ordered, mutually exclusive)

### 5.0 Unit of analysis, stated explicitly (per review's "final check 1")

**The primary gate (§5.2) operates on 6 composition-level modal
decisions — never on the 18 raw repeat-level observations directly.**
The 18 repeat-level observations (6 primary-gate items × 3 repeats) are
first reduced, one item at a time, to at most one modal `jev_level` per
item (procedure below); the gate's denominator is **6** (the number of
primary-gate compositions), not 18 and not a shrinking count of "eligible"
items — see the `repeat_unstable` handling below for why the denominator
does not shrink.

**Per-call extraction**: for each of the 3 repeat calls per item, take
Jev's returned `probabilities`, compute `jev_level = argmax(probabilities)`.

**Tie handling**: if the top two probabilities are within `0.02` of each
other (a priori tolerance, catches only near-exact ties), the call is
marked `jev_tied` — excluded from that call's `jev_level`, reported
separately, never resolved by dictionary/insertion order.

**Repeat aggregation, per item**: take the 3 calls' `jev_level` values
(excluding `jev_tied` calls).
- If ≥2 of the non-tied repeats agree: that value is the item's **modal
  `jev_level`**.
- Otherwise (all 3 differ, or fewer than 2 non-tied calls remain): the
  item has **no modal decision**, flagged `repeat_unstable`.
- **Denominator handling for `repeat_unstable` items (per review's ask
  not to leave this implicit)**: an unstable item contributes **zero
  matches to every candidate's numerator** (M, X, and A alike) — it is
  *not* removed from the denominator. The primary-gate denominator stays
  fixed at 6 regardless of how many items are unstable. **Rationale,
  stated explicitly**: shrinking the denominator to "compositions with a
  stable decision" would let a candidate's apparent match *rate* rise
  simply because the hard/unstable cases were excluded from its own
  count — fixing the denominator at 6 makes instability cost every
  candidate equally, rather than being erasable by narrowing the base.
- Full repeat-level data (all 3 raw `jev_level`/`jev_tied` values per
  item, and each individual repeat's own candidate-match outcome, not
  just the modal one) is retained and reported regardless, so the
  composition-level reduction never conceals repeat-to-repeat
  disagreement.

**Required reporting table (per review — mandatory alongside any gate
outcome, so semantic mismatch is never confused with measurement
instability)**: an unstable composition is evidence that *the experiment*
failed to reach a stable composition-level decision, not evidence against
any candidate's semantics specifically — that distinction must be visible
in the results write-up, not just in this design document:

| Quantity | Value to report |
|---|---|
| Total primary compositions | 6 (fixed) |
| Stable modal decisions | count, `0`-`6` |
| `repeat_unstable` compositions | count, `0`-`6` (= 6 − stable) |
| Candidate match counts | `matches_M`, `matches_X`, `matches_A`, each `0`-`6` |
| Candidate rates | each match count `/ 6` |
| Stability rate | stable compositions `/ 6` |

### 5.1 Candidate matching (primary gate, categorical)

For each of the 6 primary-gate items with a modal `jev_level` (items
without one contribute 0 to every count, per §5.0), compare the modal
`jev_level` against M, X, and A(rounded) for that item. A match is
recorded independently per candidate (not mutually exclusive at the item
level — M/X/A can coincide by construction on some items, per §3's
table).

`matches_M`, `matches_X`, `matches_A` — each an integer **0 to 6**,
counted against the **fixed denominator 6**.

### 5.2 Ordered gate decision — literal pseudocode (per review's "final check 2")

```
matches = {"M": matches_M, "X": matches_X, "A": matches_A}   # each an integer in [0, 6]
DENOM = 6
CLARITY_MIN = 5          # leading candidate must match >= 5 of 6
CLARITY_OTHERS_MAX = 3   # every other candidate must match <= 3 of 6
FAILURE_MAX = 3          # "majority" on a denominator of 6 means >= 4;
                          # FAILURE requires every candidate to stay at <= 3
                          # (i.e. no candidate reaches even a bare majority)

max_count = max(matches.values())
candidates_at_max = [name for name, count in matches.items() if count == max_count]

if max_count < CLARITY_MIN:
    # No candidate even reaches the clarity floor - skip straight to
    # failure/ambiguity logic without considering uniqueness of the leader.
    if max_count <= FAILURE_MAX:
        outcome = "FAILURE"          # no candidate reached a majority (>=4 of 6)
    else:
        outcome = "AMBIGUITY"        # some candidate reached 4/6 (a majority) but not the 5/6 clarity floor
elif len(candidates_at_max) != 1:
    # Explicit tie-at-the-top branch (per review - made visible, not just
    # provable by inspection): two or more candidates share the highest
    # count, so there is no unique leader. Clarity requires a unique
    # leader by definition, so this can never be CLARITY.
    outcome = "AMBIGUITY"
else:
    leader_name = candidates_at_max[0]
    other_counts = [c for name, c in matches.items() if name != leader_name]
    if max(other_counts) <= CLARITY_OTHERS_MAX:
        outcome = "CLARITY"
        primary_candidate = leader_name
    else:
        outcome = "AMBIGUITY"        # leader cleared 5/6 but another candidate also exceeded 3/6
```

**Failure threshold, stated as an explicit integer** (per review — not
left as "majority"): with `DENOM = 6`, a majority is `>= 4`. `FAILURE`
requires every candidate's count to be `<= 3` — i.e. **no** candidate
reaches even a bare majority of 4. This is spelled out in the constant
`FAILURE_MAX = 3` above, not inferred from the word "majority."

**Tie-at-the-top is now its own visible branch** (`len(candidates_at_max)
!= 1`), rather than an implicit consequence of the arithmetic (Revision
3's version already produced the correct result by construction — this
restructuring makes that provable-by-inspection rather than requiring the
reader to trace through the comparison).

**Exhaustively verified, not spot-checked**:
`research/src/verify_score_gate_logic.py` runs this exact pseudocode over
**all 343** possible `(matches_M, matches_X, matches_A)` combinations in
`[0,6]³` (not just the 8 tie cases discussed above), asserts every
CLARITY outcome has a unique leader at `≥5` with all others `≤3`, every
FAILURE outcome has every candidate `≤3`, and the three outcome counts
sum to 343 (confirming exhaustiveness/mutual-exclusivity over the full
space, not just by construction argument). Ran clean — output saved to
`research/results/score_gate_logic_verification.txt`.

**Explicit precedence case** (review's item B4 — leader clears the
clarity floor while another candidate exceeds `FAILURE_MAX`): tested at
`(M=5, X=4, A=0)`. Result: **AMBIGUITY** — never CLARITY (X=4 exceeds
`CLARITY_OTHERS_MAX=3`) and never FAILURE (the maximum, 5, already
exceeds `FAILURE_MAX=3`, so FAILURE's own precondition is never reached).
This resolves the precedence question directly: a leader clearing the
clarity floor while another candidate is "merely" majority-but-not-clear
always falls to AMBIGUITY, by construction of the ordered checks, not by
a separate rule.

**Mutation-tested, with one genuinely interesting finding**: disabling
the explicit tie-at-the-top branch changes **0 of 343** final outcomes
under the shipped constants (`CLARITY_MIN=5 > CLARITY_OTHERS_MAX=3`,
3 candidates) — this is **mathematically provable, not a test gap**: any
tie at the maximum necessarily puts a co-tied candidate (value `≥5`) into
the arbitrarily-chosen "leader"'s `other_counts`, which alone already
exceeds `CLARITY_OTHERS_MAX=3` regardless of which tied candidate is
picked. **The explicit tie-branch is currently outcome-redundant** —
kept for defensive clarity (code readability, and protection against
*future* threshold changes) rather than because it changes any result
today. A second mutation, using a hypothetical `CLARITY_OTHERS_MAX =
CLARITY_MIN` configuration (not the shipped value), confirms the branch
*would* matter under different thresholds (16 wrongful CLARITY cases
appear without it) — proving the mutation-testing methodology itself is
sound, not just that the shipped version happens to pass. `FAILURE_MAX`
and `CLARITY_MIN` were separately confirmed load-bearing (changing either
measurably shifts the outcome distribution).

**Exhaustive and mutually exclusive by construction**: every possible
`(matches_M, matches_X, matches_A)` triple with each value in `[0,6]`
falls into exactly one of the three branches above, in this fixed order —
confirmed by enumeration for all boundary cases (both candidates at the
clarity threshold, leader at exactly 4, leader at 5 with a second
candidate at 4, etc.).

**Threshold status, stated explicitly (per review §3)**: the `5/6` vs.
`≤3/6` split is a **feasibility-stage design heuristic** selected to
require a visible (≥2-item) separation between candidates given their
structural overlap (§2) — it is **not** a statistically validated
threshold and is not offered as inferential proof that any candidate is
the "true" intended semantics. It is a pre-registered, mechanical
decision rule, chosen for operational interpretability, nothing more.

### 5.3 Supplementary analyses (never feed into §5.2's gate)

- **`(0,0,2,2)`** (M undefined — tied count, per §3): X-vs-A comparison
  reported separately, not pooled into the 6-item primary tally.
- **Scalar-proximity diagnostic (review §5.2)**: for the 6 primary-gate
  items, `e_A = |score - A_unrounded|` (Jev's own returned `score` field
  vs. the unrounded severity-weighted-average). Reported as a separate,
  pre-specified diagnostic with its own stated tolerance bands (e.g.
  `e_A < 0.25` = "close," `≥0.25` = "not close" — chosen now, before data,
  not fit after). **This tests scalar proximity, not categorical
  semantic match, and is never used to declare "semantic alignment" on
  its own** — a small `e_A` can occur even when the underlying
  probability distribution has a different shape than A implies.
- **Repeat-instability rate**: fraction of the 6 primary items with no
  modal decision (`repeat_unstable`), reported regardless of gate outcome
  — high instability here would qualify *any* gate outcome's confidence,
  clarity included.

## 6. Budget (small, feasibility-scale — not an accuracy study)

- 10 compositions × 3 calls (canonical, + 2 repeats for the modal-
  decision procedure in §5.0) = **30 calls**. Unchanged from Revision 1;
  the repeat-aggregation fix (§5.0) uses this same budget, it does not
  require more calls, just a precisely defined reduction.
- No presentation-order layer (§4) and single domain (§4) — both now
  stated as explicit, disclosed scope restrictions, not claims of
  established generality.
- No `score` items from this study feed into Stage 1's frozen analysis or
  any existing item pool. Entirely new, cleanly separated data.

## 7. Explicit non-goals (restated)

- Not a test of H5 (worst-symptom-dominance) — H5 remains exploratory,
  unaffected by this study's outcome either way.
- Not an authorization to run `score`'s Stage 1 manifest — a **separate**
  decision, made only after this gate resolves (§8).
- Not a calibration or accuracy claim about `score` under any candidate
  target — this study establishes *which target(s) to evaluate against*,
  not *how well `score` performs* against them.
- Not a claim that presentation-order is irrelevant to `score` (§4), and
  not a claim that one domain characterizes `score`'s semantics generally
  (§4) — both are disclosed scope restrictions, not findings.
- No API call is authorized by this document. Build manifest → validate
  (content-blind IDs, uniqueness, reference-field-free-of-circularity,
  same checks as every prior stage) → submit for review → execute only
  after separate sign-off.

## 8. Three-tier validity hierarchy (read before citing this document's "verified" status)

**This is the single most important interpretive boundary in the whole
document, and it must not blur.** Per review, three genuinely different
questions are in play, and progress on one says nothing about the others:

| Tier | Question | Status as of Revision 6 |
|---|---|---|
| **Verifier validity** | Does the implementation correctly execute the declared rules over the declared input space? | **Addressed** — see below |
| **Semantic validity** | Do M, X, and A represent the intended interpretation of the Jev `score` primitive? | **Open** — this whole study exists to investigate it, not settle it in advance |
| **Research validity** | Are 6 compositions, the chosen thresholds, and the constructed targets sufficient to support the intended scientific conclusion? | **Open** — a feasibility-scale probe (§6), not a completeness claim |

### What's addressed (verifier validity)

- The composition table is computed correctly, matches what this
  document claims, and the claims were checked against independently-
  derived primitive behavior (not copied from the domain, where
  avoidable — see the provenance note below on where full independence
  isn't achievable). A **dedicated semantic fixture audit**,
  `research/results/score_semantic_fixture_audit.md`, separately confirms
  each of the 6 primary compositions individually against an 8-point
  checklist — a check that the *fixtures*, not just the *code*, are
  internally sound.
- The gate decision procedure is exhaustive, mutually exclusive, and
  behaves as specified at every tested boundary (8-case named matrix,
  full 343-case sweep, an explicit precedence case).
- The verification code itself is free of the specific corruption classes
  tested (wrong classification, wrong membership, wrong rounding, wrong
  tie-detection, wrong thresholds) and has no network/credential
  dependency.
- **A frozen record of this entire audit** — exact script hashes, the
  full boundary matrix, every mutation operator and its result, the
  independent fixture definitions, and the documented limitations below —
  is preserved in `research/data/characterization/
  score_verifier_freeze_manifest.json`. No semantic changes are made
  after this freeze; a semantic concern discovered later becomes a new,
  separately recorded issue, never a silent edit to the frozen record.

### Mutation-testing precision, stated per review (avoiding a collapsed claim)

Two separate findings, kept separate:

1. Under the **shipped** thresholds (`CLARITY_MIN=5`, `CLARITY_OTHERS_MAX=3`),
   the tie-at-top branch is mathematically subsumed by the competing-
   candidate constraint and does not alter the exhaustive outcome table
   (0 of 343 outcomes change if it's disabled).
2. A **hypothetical** threshold configuration (`CLARITY_OTHERS_MAX` raised
   to equal `CLARITY_MIN`) — explicitly **outside the declared admissible
   configuration space** (§5.2's constants are fixed at 5/3/3; this is a
   robustness probe, not a configuration this study would ever run under)
   — shows the branch *would* matter (16 wrongful CLARITY cases without
   it). This is a defensive-robustness result, not evidence about current
   production behavior.

### Test-construction history preserved, not sanitized

Per review: an initial order-invariance fixture, `[1, 9, 9]`, was meant to
re-test the tie case `[9,9,1,1]` under a different element order, but
accidentally dropped one occurrence of `1` — not the same multiset at
all. Execution raised the assertion failure on first run; the fixture was
corrected to `[1, 9, 1, 9]` without touching the implementation under
test (`mode_with_tie_detection` was never at fault). Full detail
preserved in the freeze manifest's `test_construction_history_note`, not
just summarized here — this is evidence the test construction itself is
executed and checked, not merely inspected.

### The `[0,0,0,9]` fixture: what it proves and what it doesn't

This fixture (mode=0, max=9, mean=2.25) confirms the **implementation**
does not collapse mode, maximum, and arithmetic mean into the same
result — a necessary property for M/X/A to ever be distinguishable at
all. **It does not establish which of the three statistics best
represents `score`'s intended semantic target.** That question is
untouched by this fixture, by design.

### What none of this establishes (semantic + research validity, still fully open)

- That M, X, or A is the *correct* semantic interpretation of `score`.
- That these 6 primary compositions are *sufficient* to characterize
  `score`'s evidence-aggregation behavior in general.
- That the chosen thresholds are empirically optimal — the mutation tests
  confirm they're *load-bearing* (changing them changes results), which
  is a different claim from them being *correct*.
- That a future Stage 1 `score` experiment, even if this gate resolves to
  CLARITY, will have a valid external ground truth — the resulting
  "primary candidate" is still a construction-defined reference label
  (§2), with all the same limitations already documented for `choice`/
  `noul`'s reference labels.
- That Jev's `score` output semantics generalize beyond this controlled,
  single-domain, n=4 composition space (§4's disclosed scope
  restrictions still apply in full).

**In short: the implementation audit can establish that the pre-
registered procedure is faithfully and defensibly implemented, and that
its fixtures are internally sound. It cannot, by itself, establish the
truth of any semantic hypothesis about `score`, or that this design is
scientifically adequate.** Both remain fully open, per the table above —
the next pass is semantic validation, not another implementation pass.

## 9. Gate decision and what each outcome authorizes

| Outcome | What it authorizes |
|---|---|
| **CLARITY** (one candidate ≥5/6, others ≤3/6, checked first) | A `score` Stage 1 manifest may be designed, modeled on `choice`/`noul`'s (`step0b_design_specification.md` §3), using the identified primary candidate as the foregrounded reference-label rule (M, X, A all still reported in parallel, per §2's binding rule). Still requires its own construction-feasibility/output-feasibility Stage-0-style check before any Stage 1 budget is committed. |
| **FAILURE** (max candidate ≤3/6, checked second) | `score` is reported as not currently evaluable against any of M/X/A. Stays excluded from any accuracy-style analysis until a materially different interpretation framework is proposed and separately reviewed. Characterization-only findings (distribution shape, saturation) remain reportable regardless. |
| **AMBIGUITY** (everything else, the default) | `score` may still get a Stage 1-style characterization, framed explicitly as multi-target from the outset — accuracy/Brier/reliability reported against M, X, and A in parallel, with no primary designation. A legitimate, if less crisp, path forward, not a block. |

None of these three outcomes is presumed. The manifest, the ordered
comparison procedure, the tie/repeat-aggregation rules, and the
thresholds above are complete and fixed; only the data is missing, and no
data exists yet.
