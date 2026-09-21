# `score` Semantic Identification Protocol

Status: **design/analysis only — not executed, not approved for any API
call.** This document sits one level above
`score_semantic_validation_specification.md` (Revision 7, "the gate
spec") — that document defines and verifies the *mechanics* of comparing
M/X/A against Jev output; this document asks the prior question of
whether the existing design can actually **identify** among them without
circularity, and reports one substantive new finding it turned up.
Nothing here modifies the frozen verifier audit
(`score_verifier_freeze_manifest.json`) or the gate spec's mechanics —
where content already exists there, this document references it rather
than duplicating or restating it differently.

## Scope

**Central question**: which independently defined target, if any, best
represents the intended semantics of Jev's `score` primitive — evaluated
without assuming the answer is M, X, or A merely because one aligns with
observed output, and without treating a composition's result as evidence
for a candidate it doesn't actually distinguish from the others.

This document does not answer that question (no data exists yet). It
establishes whether the *existing* design is capable of answering it, and
where it currently is not.

## Workstream 1 — Contract and semantic evidence inventory

**Already addressed, referenced not duplicated**: the gate spec's §1
separates documented behavior (the distribution→scalar formula) from
undocumented behavior (the evidence→distribution mapping — the actual
unknown). Stage 0's controlled observations (the 2:1 adjacent-level
finding) are the only *observed behavior* on record; everything else
about `score`'s aggregation is, correctly, still a hypothesis, not
evidence — see `stage0_report.md`'s "Flagged concern" for the full
account of what was and wasn't established there.

**Nothing new added here.** This inventory was already done correctly;
re-stating it in different words would not improve it.

## Workstream 2 — Candidate-target definition

**Already addressed, referenced not duplicated**: gate spec §2 defines M
(mode, undefined on ties), X (max, always defined), A (mean, rounded via
a stated deterministic rule, reported both rounded and unrounded), and
explicitly defers a fourth candidate (risk-sensitive) as not definable
without an externally supplied loss function. Tie handling, undefined
cases, and the categorical-vs-scalar distinction (§5.2 of that document)
are all already specified there.

## Workstream 3 — Identifiability analysis (the new contribution of this document)

**This is the one workstream not previously computed anywhere in this
project.** "Discriminative" in the gate spec's §3 only ever meant "at
least two of the three candidates differ on this item" — it does not say
*which* pair differs. A composition where M and A coincide but X differs
provides **zero** evidence for choosing between M and A specifically,
even though it's correctly labeled "discriminative" in the aggregate
sense.

`research/src/verify_score_identifiability.py` computes, for each of the
3 candidate pairs (M-X, M-A, X-A), exactly how many of the 6 primary
items actually separate that pair — script-verified, not hand-counted.
Result, saved to `research/results/score_identifiability_analysis.json`:

| Pair | Items separating it (of 6) | Coverage |
|---|---|---|
| M vs. X | 5 | Near-full |
| **M vs. A** | **3** | **Half** |
| X vs. A | 6 | Full |

**Finding: the current 6-item design has asymmetric identifiability.**
X-vs-A is fully powered (every primary item informs it); M-vs-X is
near-fully powered; **M-vs-A is powered by only half the item set** —
`(0,0,0,2)`, `(0,0,1,2)`, and `(0,1,2,2)` are the only three items where
M and A actually differ (the other three — `(0,0,0,1)`, `(0,1,1,2)`,
`(1,1,1,2)` — all happen to have `A_rounded == M`, so they're silent on
this specific comparison, however "discriminative" they look overall).

**Consequence, stated plainly**: if a future run's gate outcome is driven
mainly by items where M and A disagree specifically, that conclusion
rests on a smaller, less redundant evidence base (3 items, no repeats
factored in yet) than a conclusion driven by X-vs-A disagreement (6
items). This is not disqualifying, but it should be weighed explicitly
before treating any CLARITY outcome as equally well-supported regardless
of which pair drove it — see Workstream 5.

**Resolved by review: augment, don't modify.** Per review, the frozen
6-item set stays exactly as it is — no retroactive edits — and a
**separately versioned supplementary set** closes the M-vs-A gap instead.

### Supplement v1 — pre-registered, searched, and verified

`research/src/design_score_mvsa_supplement.py` searches a **genuinely
new** composition space (n=5 sentences, not a re-tread of n=4 — every one
of the 15 possible n=4/3-level multisets is already accounted for across
the primary/supplementary/control/non-discriminative categories, so no
new n=4 pattern exists to add). Pre-registered selection criteria (all
checked mechanically, before selection, none dependent on any Jev
output — none exists):

1. M is defined and unique.
2. A is defined under the *existing, unchanged* rounding rule.
3. `M ≠ A` (the item actually separates the target pair).
4. Discrimination class computed and recorded, not assumed.
5. Relationship to X recorded explicitly, never treated as irrelevant.
6. Selected by exhaustive search + a pre-registered diversity rule (2
   THREE_WAY + 1 TWO_WAY, deterministic sort — no randomness, no
   data-dependence), not by inspecting any output.
7. Resulting combined coverage computed and reported *before* any
   semantic evaluation (immediately below).

**Search result**: 4 candidate n=5 compositions satisfy criteria 1-3;
the diversity rule selects 3: `(0,0,0,1,2)` and `(0,0,0,2,2)`
(THREE_WAY — M, X, A all distinct) and `(0,0,2,2,2)` (TWO_WAY — M=X,
separates from A only).

**Combined pairwise coverage, frozen 6 + supplement 3 = 9 items,
script-verified**:

| Pair | Frozen (of 6) | Combined (of 9) | Meets symmetric sufficiency (≥6)? |
|---|---|---|---|
| M vs. X | 5 | 7 | YES |
| **M vs. A** | **3** | **6** | **YES** |
| X vs. A | 6 | 9 | YES |

**All three pairs now meet the same ≥6-separating-item bar** — the
threshold set by X-vs-A's original full coverage, applied symmetrically,
not chosen to make M-vs-A pass. Full record:
`research/results/score_mvsa_supplement_v1.json`.

**What this supplement does and does not establish, restated per its own
output**: it improves the *count* of items separating each pair. It does
**not** establish that M/X/A are the only competing interpretations, that
these new items are representative of real `score` inputs, that every
item carries equal evidentiary weight, or that meeting this numeric
threshold is scientifically sufficient — those remain exactly as open as
before (§8 of the gate spec, unchanged).

**Full design record (all 4 candidates, exclusion reasoning, selection-
rule robustness check, sentence-count confound)**: see
`research/methodology/score_mvsa_supplement_manifest_spec.md`.

**Not yet built**: full manifest-level items (content-blind opaque IDs,
canonical presentation order, validator pass) for the 3 supplement
compositions — that is the next concrete step *if* this design is
approved, following the identical build → validate → review → execute
pipeline every other stage in this project has used. No sentences have
been written and no API budget estimated yet for this specific
supplement.

## Workstream 4 — Evidence-to-target mapping, and the central methodological constraint

**Already substantially addressed** by the gate spec's pre-registered,
ordered gate (§5.2 — thresholds fixed before any data collection) and its
§8 three-tier hierarchy (explicitly: agreement with Jev's output
establishes *observational* agreement for that item, never *intended
semantics*). Restated here as a single binding rule, since review named
it as the central constraint for this whole workstream:

> **Agreement with Jev's output on a given composition is evidence about
> that composition only. It is never treated as proof of intended
> semantics, regardless of how many compositions agree** — the gate's
> CLARITY threshold (§5.2 of the gate spec) is a pre-registered
> feasibility criterion for *whether a pattern is visible*, not a
> statistical proof that the winning candidate is correct. This document
> adds nothing to that rule; it only re-states it as explicitly
> binding on this workstream, per review's request.

**Also restated as a binding rule** (implicit in the existing design,
made explicit per review): **non-discriminating items are never counted
as evidence for any candidate.** The 3 control compositions
(`(0,0,0,0)`, `(1,1,1,1)`, `(2,2,2,2)`) are excluded from the gate
entirely (gate spec §3); this document's identifiability analysis
confirms the mechanism generalizes correctly — an item that happens not
to separate a *specific pair* (e.g. `(0,0,0,1)` for M-vs-A) must likewise
never be counted as evidence for that pair's outcome, even though it
remains valid evidence for the pairs it does separate. **No code change
is required for this** — the gate already only tallies matches for the
candidate a modal decision actually equals (gate spec §5.1); this
workstream's contribution is confirming, via the identifiability
computation above, that the "silent on this pair" cases are correctly
identified as such rather than silently miscounted.

## Workstream 5 — Decision and stopping rules

**Extends, does not replace, the gate spec's existing outcome table**
(§9 there: CLARITY/FAILURE/AMBIGUITY → what each authorizes). Per review,
the rule below is stated **symmetrically across all three pairs** — the
M-vs-A asymmetry made the issue *visible*, but the principle applies
identically to M-vs-X and X-vs-A if either ever becomes the
under-evidenced pair in a future design change.

### Pair-specific evidence accounting (formalized, per review)

For every candidate pair `P` and item set of size `N`:

```
n_P = sum over items i of  1{item i separates pair P}
```

**Only the `n_P` items separating pair `P` may contribute evidence to a
conclusion about that pair** — the other `N − n_P` items are silent on it
and must never be counted for or against it, regardless of how the
overall gate resolves. Any results write-up must report, per pair: total
item count, `n_P` (separating), `N − n_P` (non-separating), any
unstable/undefined cases among the separating items specifically, and
**whether `n_P` meets the pre-registered sufficiency threshold**
(`≥6`, per Workstream 3's supplement, applied identically to all three
pairs) — never just the aggregate `N`, which would let a thin
pair-specific evidence base hide behind a healthy-looking total.

### Outcome-level rules

- **Candidate separation (CLARITY)**: as defined in the gate spec, **plus**
  a required disclosure — *which pairwise comparisons actually drove the
  winning candidate's lead*, with that pair's `n_P` reported alongside the
  gate outcome. A CLARITY outcome driven by a pair at `n_P≥6` and one
  driven by a pair below threshold are not equally well-evidenced, even
  if both clear the same numeric gate.
- **Candidate equivalence**: two or more candidates coincide on enough
  items that neither can be favored — already the AMBIGUITY outcome's
  natural interpretation when the leader's gap fails; no new rule needed.
- **Ambiguous or underidentified semantics**: if the eventual data lands
  in AMBIGUITY *and* the deciding items are concentrated on a pair below
  the sufficiency threshold, that should be reported as **underidentified
  by design** for that pair specifically, not merely "ambiguous" — a
  diagnosis that points at the composition set, not at `score`'s
  behavior, as the limiting factor.
- **Evidence insufficient for a Stage 1 design**: applies, **symmetrically
  for any of the three pairs**, if either (a) the gate spec's own FAILURE
  outcome triggers, or (b) CLARITY triggers but the deciding pair's `n_P`
  is below the sufficiency threshold — in which case Stage 1 should not
  proceed on that candidate without first closing that pair's
  identifiability gap. With Supplement v1 (above), all three pairs
  currently meet `n_P≥6` — this condition is not presently triggered, but
  remains binding if a future design change reintroduces an imbalance.
  this document introduces, not previously stated.

## What this document explicitly does not do (binding non-goals, restated per review)

- Does not create a `score` Stage 1 manifest.
- Does not make any live Jev call.
- Does not select M, X, or A based on any preliminary fit — none exists;
  no data has been collected under either this document or the gate spec.
- Does not treat the frozen verifier audit as validating this design's
  research sufficiency — verifier validity and research validity remain
  the separate tiers the gate spec's §8 already establishes.
- Does not claim the candidate space (M, X, A) exhausts all plausible
  `score` semantics — a materially different candidate (e.g. a genuine
  risk-sensitive target, once a loss function exists) remains possible
  and out of scope here, per the gate spec's §2.
- Does not infer a ground-truth target from any observed Jev output —
  none has been observed under this design.
- Does not optimize thresholds before a semantic target is justified —
  the gate spec's thresholds are feasibility heuristics (its §5.2),
  unchanged by this document.

## What stays frozen, and what's newly open (per review, stated explicitly)

**Kept frozen — nothing below was touched by this update:**

- Implementation-audit artifacts and hashes
  (`score_verifier_freeze_manifest.json`).
- The original 6-item composition set and its results
  (`score_semantic_composition_table.csv`, unchanged).
- Existing verifier results (composition, gate-logic, fixture audits).
- The pairwise identifiability findings themselves (Workstream 3's
  3/6, 5/6, 6/6 counts — a historical record of the frozen 6-item set's
  properties, not revised even though a supplement now exists alongside).
- The rule that pair-silent items cannot count as evidence.
- The three-tier validity hierarchy (gate spec §8) distinguishing
  verifier / semantic / research validity.

**Newly open, separately tracked — not yet resolved, not yet approved:**

- Whether Supplement v1's 3 compositions should be built into full
  manifest-level items (opaque IDs, canonical order, validator pass) and
  submitted for the same review pipeline as everything else.
- The pair-specific sufficiency threshold (`≥6`) itself — proposed here
  by precedent (matching X-vs-A's original coverage), not yet
  independently justified as the *right* number.
- Whether Supplement v1's specific 3 items (or any 3 items) are
  representative enough of real `score` inputs to count as adequate
  evidence, beyond just meeting the numeric threshold.
- Whether the M/X/A candidate set is complete, or whether a materially
  different candidate should be considered before any of this proceeds
  further.
- Whether semantic validation, even with Supplement v1 closing the
  numeric gap, can actually support a Stage 1 design — the three-tier
  hierarchy's "semantic validity" and "research validity" rows remain
  open regardless of how this specific coverage question resolves.

**No API call, manifest, or Stage 1 authorization follows from this
document.** The next step, if this design is approved, is building
Supplement v1 into real manifest items and running it through the same
build → validate → review → execute pipeline as every prior stage.
