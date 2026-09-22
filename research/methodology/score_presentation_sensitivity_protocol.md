# `score` Presentation-Sensitivity Protocol (Revision 4)

Status: **design only — no manifest built for this revision yet, no API
calls made or authorized.** This is Option B from the Phase B disposition
decision: a separately specified experiment, not an implicit extension of
Phase B. Submitted for review before any manifest is (re)built, per every
prior stage's practice in this project.

**Accurate one-line description of this study, stated up front per
review**: *a two-variant presentation-sensitivity study (`P2_full_reverse`,
`P3_severity_first`) with a canonical-equivalent replication control
(`P4_severity_last`), evaluated across three selected items* — not a
three-way non-canonical comparison. See the Revision 4 changelog for why.

## Changelog from Revision 3

Review's requested "final artifact review" (manifest integrity, plan
integrity, classification precedence, estimand scope, research
interpretation) caught a real, previously-undetected design flaw before
any live call was made:

**Finding**: `P1_canonical` and `P4_severity_last` are **byte-identical**
for all 3 selected items — and, checked structurally, for all 9 Phase B
items. Root cause: every composition in this track has always been
*written* as a non-decreasing tuple (e.g. `(0,0,1,2)`), and
`build_score_phase_b_manifest.py`'s `consume()` assigns strictly
increasing opaque IDs in exactly that iteration order. Sorting by ID
ascending (`P1_canonical`) and stable-sorting ascending by severity
(`P4_severity_last`) therefore always produce the same sequence — not a
coincidence of these 3 items, a structural property of how the whole
track's manifests have been built. Left uncorrected, `P4`'s "comparison"
to `P1` would trivially read as zero change for every item, silently
inflating apparent evidence for `NEGLIGIBLE` with a comparison that never
tested anything.

**Decision (Option B, approved)**: keep `P1`/`P2`/`P3` exactly as
Revision 3 defined them (no asymmetric tie-break hack to manufacture a
distinct `P4`, no new sentence construction, no budget change). Reclassify
`P4_severity_last`'s **role** from "third non-canonical permutation" to
**canonical-equivalent replication control** — its 3 calls remain in the
36-call plan, remain their own separately-recorded cell, and support a
separate P1-vs-P4 replication diagnostic (§6.3) — but are **structurally
excluded** from every primary sensitivity estimand (decision-change,
confidence-range, TV-distance) and from the classification procedure
(§7). Per review's explicit constraint: **P4's 3 raw responses are never
pooled into `P1_canonical`'s cell** — pooling would silently change the
sampling structure and give canonical presentation double weight relative
to `P2`/`P3`. `P1` and `P4` remain two distinct, separately-reported cells
that happen to share identical input content.

**Consequences, applied throughout this revision**:
- `NONCANONICAL_LABELS` (the set entering primary estimands) is now
  `{P2_full_reverse, P3_severity_first}` only — 2 permutations, not 3.
- The non-canonical comparison denominator is now **≤ 6** (3 items × 2
  permutations), not ≤ 9.
- A new §6.3 defines the P1-vs-P4 canonical-control diagnostic:
  descriptive only, reported separately, never entering §7's
  classification.
- The manifest builder now **asserts and would reject** any permutation
  claimed to be non-canonical (`P2`/`P3`) that turns out to be content-
  identical to `P1` — the exact class of error this revision exists to
  fix, now checked mechanically rather than trusted by construction.
- New self-tests added (§10) confirming `P4` cannot affect the decision-
  change denominator, confidence-range, TV-distance, or classification —
  including a positive-path test that a genuine `P2`/`P3` decision change
  still produces `MATERIAL`, and a test that a large, artificial P1-vs-P4
  difference does **not**.

## Changelog from Revision 1–2 (carried forward, unchanged by Revision 4)

- **A — Stable-cell eligibility for continuous estimands, made explicit.**
  A cell (item × permutation) is "eligible" for any canonical-referenced
  comparison only if both it and `P1_canonical` for that item reached a
  stable modal decision. An unstable canonical cell removes the *item*
  from canonical-referenced comparisons entirely (reported as
  unavailable, never as zero sensitivity).
- **B — Aggregation rule for confidence/probability, made explicit.**
  Within a *stable* cell, mean confidence and mean probability vector are
  computed over **all 3 valid raw responses** (tied calls included),
  never restricted to repeats whose individual `jev_level` matched the
  cell's modal decision.
- **C — `MATERIAL_CONF` framed explicitly as conservative** relative to
  Step 0A.2's ~0.13 confidence shift.
- **D — `P3`/`P4` made fully executable, and explicitly NOT reverses of
  each other** — still true and still relevant even though `P4` is now a
  control rather than a comparison arm (its content is still independently
  defined, just structurally coincident with `P1` here).
- **E — Pooled decision-change rate** given an explicit formula and
  denominator-reporting requirement (now over `{P2,P3}` only, §6.1).
- **F — Analysis split into primary and secondary descriptive** (M/X/A
  alignment) — unaffected by this revision; the P1/P4 control diagnostic
  (§6.3) is a *third*, also-separate category, neither primary nor the
  M/X/A alignment analysis.
- **Item-coverage guard for `NEGLIGIBLE` (P0)** — unchanged in mechanism,
  now operating over a 2-permutation non-canonical set instead of 3 (§7).
- **Classification precedence** (`UNCLASSIFIABLE`, `INCONCLUSIVE_BY_
  INSTABILITY`) — unchanged in mechanism (§7).

Selected items (§2) and the 36-call budget (§5) are unchanged. The four
permutation *definitions* (§3) are unchanged — only `P4`'s **role** in the
analysis changes.

## 0. Why this exists, and what it is not

Phase B (`score_bounded_semantic_validation_protocol.md`, executed
2026-09-22) found that under **canonical, fixed presentation**, `score`'s
output discriminated among M/X/A with X (Highest-severity) as the leader
on the frozen six-item gate (matches M=1, X=6, A=0 → CLARITY, stability
6/6 — `score_phase_b_execution_manifest.json`) and on 2 of 3 pairwise
comparisons (M-X, X-A). Phase B's own protocol (§A.2) states it **cannot**
investigate whether this holds under a different sentence order, because
canonical-only presentation means every item was called at exactly one
fixed order.

Separately, Step 0A.2 already found `score` order-sensitive on a
different (2-sentence) construction: `score_mix_L1_L2` vs. `_swapped`
moved confidence 0.73→0.86 and level-2 probability mass 0.18→0.09 under
an identical-content, order-only swap.

**This study's objective**: determine whether the X-alignment observed in
Phase B is robust to presentation order, on the *same* n=4 items Phase B
already used — **without** treating this as another "which candidate
wins" test. The order-sensitivity *signal itself* (does the underlying
probability distribution move, independent of whether the argmax
changes) is the primary quantity of interest, because that is what a
workflow-level escalation policy that thresholds on `confidence` or
`probabilities` — not just the top-line decision — would actually be
exposed to.

**Explicit non-goals**:
- Not a re-run or re-scoring of Phase B's frozen six-item gate.
- Not a test of `choice`'s or `noul`'s order sensitivity.
- Not a semantic-identification claim for `score` under any outcome.
- Not a proposal or test of an escalation policy.
- Not a claim that 3 items in 1 domain characterize order sensitivity for
  `score` in general.
- **Not, as of Revision 4, a three-way non-canonical comparison** — it is
  a two-variant comparison (`P2`, `P3`) plus a canonical-equivalent
  replication control (`P4`). Described accurately as such in any
  write-up.

## 1. Frozen research question

> Within the single domain and n=4 severity-level compositions already
> used in Phase B, does varying the presentation order of otherwise-
> identical, already-fixed sentences materially change `score`'s modal
> decision, confidence, or probability distribution — and separately,
> does the previously observed X-alignment survive that variation, or is
> it an artifact of the one order Phase B happened to use?

Restated in the form that matters for the project's actual research
question: **how sensitive is `score`'s uncertainty signal to presentation
order, and what does that imply for using it as an input to a reliable
escalation policy** — not merely "does X win again."

## 2. Item selection — mechanical, pre-registered, no Jev output involved

Reuses 3 of Phase B's 6 frozen n=4 items (identical sentence content,
identical severity-level assignment — no new content authored). Selected
by the same deterministic rule already established for the M-vs-A
supplement (2 THREE_WAY + 1 TWO_WAY, ascending composition-tuple sort):

| Composition | Discrimination class | Selected because |
|---|---|---|
| `(0,0,0,2)` | THREE_WAY (first, sorted) | M, X, A all distinct |
| `(0,0,1,2)` | THREE_WAY (second, sorted) | M, X, A all distinct |
| `(0,0,0,1)` | TWO_WAY (first, sorted) | {M,A}=0 vs. X=1 |

**The non-circularity property comes from the selection rule itself**, a
pure function of each item's composition-level discrimination class,
fixed before any Jev call in this whole track — it takes no coverage
count, match count, or Jev output as input.

The other 3 frozen items and all 3 supplement items are **not** part of
this study — a deliberate scope restriction (§5), not a claim that
order-sensitivity is absent there.

## 3. Permutation design — content-blind, structurally defined, fully executable

Each selected item has exactly 4 sentences, each already assigned to a
severity level. Four permutations, defined **structurally**, identically
across all 3 items:

| Label | Definition | Role (Revision 4) | In primary sensitivity estimands? |
|---|---|---|---|
| `P1_canonical` | Opaque sentence IDs sorted ascending — Phase B's own canonical order, re-collected fresh (§4) | Primary canonical reference | Reference point |
| `P2_full_reverse` | Exact reverse of `P1_canonical`'s sentence sequence | Non-canonical order | **Yes** |
| `P3_severity_first` | `stable_sort(canonical_sentences, key=severity_level, reverse=True)` | Non-canonical order | **Yes** |
| `P4_severity_last` | `stable_sort(canonical_sentences, key=severity_level, reverse=False)` | **Canonical-equivalent replication control** | **No** — see §4, §6.3 |

`P3` and `P4` remain independently-defined stable sorts (descending /
ascending by severity, ties broken by canonical relative order) — `P4` is
still not defined as "reverse of `P3`." What changed in Revision 4 is not
`P4`'s definition but its **role**: for every item in this track, `P4`
happens to reproduce `P1_canonical` exactly (proven in §4), so it cannot
function as a genuine order variant here. It is retained as a control
cell rather than discarded, because its 3 raw calls still provide a
useful (if content-identical) replication check on `P1_canonical`'s
result (§6.3) — just not as evidence about order sensitivity.

Worked example for `(0,0,1,2)`, still illustrating why `P4` must be its
own independently-defined sort rather than "reverse `P3`" (unaffected by
the role change above): `P3 = [s_d, s_c, s_a, s_b]`, `P4 = [s_a, s_b, s_c,
s_d]`, `reverse(P3) = [s_b, s_a, s_c, s_d]` — all three differ.

**Why not exhaustive 4! = 24 permutations per item**: a small number of
*structurally meaningful* orderings targets the presentation-order
mechanisms most plausible to matter, without an exhaustive, budget-
blowing sweep — a disclosed scope restriction.

## 4. Data-collection design — fresh data, explicit aggregation rule, content-equivalence check

**All 4 permutations, including `P1_canonical`, are collected fresh in
this study's own run**, rather than reusing Phase B's already-collected
canonical-order data — avoiding a between-session confound.

**Separate diagnostic (not part of the sensitivity analysis)**: this
study's own `P1_canonical` results may be compared against Phase B's
stored canonical results for the same 3 items, as an external check for
temporal drift — never blended into §7's classification.

**Content-equivalence check, added (Revision 4, binding on the manifest
builder)**: before any call plan is built, the builder **must** verify,
per item, that `P2_full_reverse` and `P3_severity_first`'s sentence-ID
sequences are **not** identical to `P1_canonical`'s — and must abort
(raise, not warn) if either is. This is the mechanical safeguard against
the exact failure mode Revision 4 exists to fix: a permutation *labeled*
non-canonical that is *actually* content-identical to canonical.
`P4_severity_last`'s equivalence to `P1_canonical` is, conversely,
**expected and asserted** (not treated as an error) — the builder records
this explicitly as `permutation_distinct_from_P1: false` for `P4`, rather
than silently relying on the predefined role label.

**Repeat structure, per (item × permutation) cell**: 3 calls, tie
tolerance `0.02`. A near-tied call is excluded from `jev_level`
extraction but its `confidence`/`probabilities` remain valid for the
cell's continuous aggregates.

**Cell stability**: a cell is stable if ≥2 of its 3 non-tied calls agree
on `jev_level`.

**Continuous aggregation within a cell**: mean confidence and mean
probability vector are computed over **all 3 valid raw responses**,
regardless of stability or individual `jev_level`/tie status — never
filtered to modal-matching repeats.

**`P1` and `P4` remain two distinct, separately-recorded cells (Revision
4, binding)**: each of `modal_level`, `stable`, the 3 raw responses, mean
confidence, and mean probability vector is computed and stored
independently for `P1_canonical` and `P4_severity_last`. **They are never
pooled** into a single 6-response cell — doing so would silently change
`P1`'s sampling structure and give the canonical presentation twice the
repeat weight of `P2`/`P3`.

**Cell eligibility for cross-permutation comparisons**: a canonical-
referenced comparison between `P1_canonical` and `P2` or `P3` requires
both cells to be stable. If `P1_canonical` for an item is itself
unstable, that item is excluded from all canonical-referenced
comparisons (reported as unavailable, never as zero). `P4` participates
in **no** eligibility computation for the primary estimands — only in its
own separate diagnostic (§6.3).

## 5. Budget — fixed before execution, broken out by role (Revision 4)

3 items × 4 permutations × 3 repeats = **36 calls, fixed before
execution.** Broken out by role, per review's request:

| Role | Permutations | Calls |
|---|---|---|
| Primary sensitivity comparisons | `P2`, `P3` (3 items × 2 × 3 repeats) | 18 |
| Canonical reference + replication control | `P1`, `P4` (3 items × 2 × 3 repeats) | 18 |
| **Total** | | **36** |

Transient-error retries are not additional planned calls. Not executed.
Not authorized by this document.

## 6. Estimands — defined before any data exists

### 6.1 Primary analysis — `NONCANONICAL_LABELS = {P2, P3}` only

1. **Per-cell modal decision and stability**, computed independently for
   all 4 cells per item (`P1`, `P2`, `P3`, `P4`) — `P4`'s cell is
   computed and stored like any other, it simply never enters the
   estimands below.
2. **Decision-change rate**:

   ```
   numerator   = count of eligible (item, p in {P2,P3}) pairs where
                 modal_level(p) != modal_level(P1_canonical)
   denominator = count of eligible (item, p) pairs, p in {P2,P3}
                 (both P1_canonical and p stable)

   n_noncanonical_comparisons_planned = 6   # 3 items x {P2,P3}, before exclusions
   R_change = numerator / denominator      # undefined if denominator == 0
   ```

   Reported alongside: numerator, denominator, `R_change`,
   `n_noncanonical_comparisons_planned` (= 6, fixed), the count of
   excluded comparisons (out of 6) and each one's reason (canonical
   unstable / this permutation unstable). `R_change` is **descriptive**,
   not the classification's primary trigger.
3. **Confidence range**: per item, over `[P1_canonical] + [p for p in
   (P2, P3) if canonical_stable and p.stable]` — `P1` counted exactly
   once, `P4` never included. Undefined if this set has fewer than 2
   cells.
4. **Distributional change**: per item, per eligible `p in {P2, P3}`,
   total variation distance between `p`'s mean probability vector and
   `P1_canonical`'s — reported per item as the maximum across eligible
   `P2`/`P3` comparisons. Undefined if `P1_canonical` is unstable.
5. **Repeat-instability rate**: fraction of all 12 (item × permutation)
   cells that are `repeat_unstable` — **`P4`'s cells are included in this
   denominator** (it is still a real measurement whose stability matters,
   even though it doesn't enter the sensitivity comparisons), so this
   remains "of 12," not "of 9."

**Required study-level output fields**: `n_stable_cells` (of 12),
`n_noncanonical_comparisons_planned` (= 6), `n_eligible_decision_
comparisons` (of 6), `n_eligible_distribution_comparisons` (of 6),
per-item `canonical_cell_stable` (bool), `n_items_with_eligible_
comparisons` (of 3), `n_items_without_eligible_comparisons` (of 3),
`item_coverage_complete` (bool), and `n_excluded_canonical_equivalent_
controls` (= 3, one per item, fixed — since all 3 `P4` cells are
structurally excluded from the primary estimands by role, not by data-
dependent eligibility).

### 6.2 Secondary descriptive analysis (M/X/A alignment — unchanged)

6. **Alignment with M/X/A**, all three, no candidate assumed correct —
   reported per permutation (including `P4`, for completeness of the
   descriptive record), never used to argue for or against any
   candidate's correctness, never merged into §6.1.

### 6.3 Canonical-control diagnostic (`P1` vs. `P4`) — new, Revision 4, descriptive only, never feeds §7

Because `P4_severity_last` is content-identical to `P1_canonical` for
every item in this study, the pair provides a **replication diagnostic**
for `P1_canonical`'s own measurement, computed and reported entirely
separately from §6.1–6.2:

- **Modal-decision agreement**: does `P1`'s modal decision equal `P4`'s,
  per item (both, one, or neither may be `repeat_unstable`)?
- **Confidence difference**: `P4.mean_confidence - P1.mean_confidence`,
  per item.
- **Probability-distribution difference**: total variation distance
  between `P1` and `P4`'s mean probability vectors, per item.
- **Joint stability**: whether both `P1` and `P4` independently reached a
  stable modal decision.

**Binding interpretive rule**: this diagnostic answers "how much does
`score` vary across two independent 3-call samples of the *same* input,"
i.e. baseline repeat/session noise — it is **not** evidence about order
sensitivity (no order varied) and **must not** be presented as such.
A large `P1`/`P4` difference does not make the run `MATERIAL`; a small
one does not make it `NEGLIGIBLE` or add to `item_coverage_complete`.
It is reported for context (e.g., to help interpret whether a `P2`/`P3`
difference is large relative to the same-input baseline noise), never as
an input to §7's classification.

## 7. Stopping / classification criteria — pre-registered, ordered, over `{P2,P3}` only

```
MATERIAL_CONF = 0.15      # conservative relative to Step 0A.2's ~0.13 shift
MATERIAL_DIST = 0.20
NEGLIGIBLE_CONF = 0.10
NEGLIGIBLE_DIST = 0.10
HIGH_INSTABILITY = 1/3    # >=4 of 12 cells repeat_unstable (P4's cells count
                          # toward this denominator; they never count toward
                          # decision/confidence/distribution comparisons)
NONCANONICAL_LABELS = {P2_full_reverse, P3_severity_first}   # NOT P4

# Step 1 - unclassifiable check
if every item's P1_canonical cell is unstable:
    final_classification = "UNCLASSIFIABLE"
else:
    # Step 2 - raw classification, computed ONLY over eligible {P2,P3} comparisons
    n_items_with_eligible_comparisons = count(
        item for item in items
        if item.n_eligible_comparisons_over_P2_P3 >= 1
    )
    item_coverage_complete = (n_items_with_eligible_comparisons == 3)

    if any eligible P2/P3 comparison shows a decision change:
        raw = "MATERIAL"
    elif any item's eligible confidence range >= MATERIAL_CONF
         or any item's eligible max TV distance >= MATERIAL_DIST:
        raw = "MATERIAL"
    elif (item_coverage_complete
          and every item's eligible confidence range < NEGLIGIBLE_CONF
          and every item's eligible max TV distance < NEGLIGIBLE_DIST):
        raw = "NEGLIGIBLE"
    else:
        raw = "INCONCLUSIVE"

    # Step 3 - instability precedence
    instability_rate = n_unstable_cells / 12    # over all 12 cells, P4 included
    if raw == "NEGLIGIBLE" and instability_rate >= HIGH_INSTABILITY:
        final_classification = "INCONCLUSIVE_BY_INSTABILITY"
    elif instability_rate >= HIGH_INSTABILITY:
        final_classification = raw + " (unstable underlying data)"
    else:
        final_classification = raw
```

`P4`'s cells never appear in any branch above except via the overall
instability-rate denominator (Step 3) — a design choice, not an
oversight: `P4`'s own repeat consistency is still informative about
`score`'s general measurement noise, even though its content-equivalence
to `P1` disqualifies it from the sensitivity comparisons themselves.

**Thresholds remain a pre-registered design choice, not a validated
statistical standard.**

## 8. Outcome-interpretation matrix (unchanged in structure; denominators now over `{P2,P3}`)

| Final classification | Required interpretation |
|---|---|
| `UNCLASSIFIABLE` | Every item's canonical cell was itself unstable; order sensitivity cannot be assessed. Report as a measurement-reliability finding, not evidence about order |
| `MATERIAL` | Presentation order materially affects `score`'s output on this item set (via `P2`/`P3`); any semantic-alignment claim (Phase B's X-lead included) must be qualified as order-dependent |
| `MATERIAL (unstable underlying data)` | A material effect was observed, but instability was also high — report both facts |
| `NEGLIGIBLE` | (Only reachable at low instability.) On this item set, `score`'s output is stable across the two tested non-canonical orderings — narrows, but does not close, the order-sensitivity question |
| `INCONCLUSIVE` | Genuinely between thresholds, or item coverage over `{P2,P3}` is incomplete — report raw values and denominators |
| `INCONCLUSIVE (unstable underlying data)` | Neither question resolves cleanly |
| `INCONCLUSIVE_BY_INSTABILITY` | Eligible data looked negligible, but instability was too high to say so |

**Incomplete item coverage**: if any of the 3 items has zero eligible
`{P2,P3}` comparisons, `NEGLIGIBLE` is unreachable regardless of how clean
the available data looks — falls to `INCONCLUSIVE` (or its instability
variant) unless `UNCLASSIFIABLE` applies.

**The `P1`/`P4` canonical-control diagnostic (§6.3) never appears in this
table** — it has no classification outcome of its own; it is reported
alongside the table's result as context, not as a row within it.

## 9. What this study does and does not authorize

| Outcome | Authorizes |
|---|---|
| `MATERIAL` (either variant) | Phase B's X-alignment must be reported as order-dependent going forward; does **not** authorize a full order×composition factorial |
| `NEGLIGIBLE` | Some additional confidence that X's Phase B lead is not solely a canonical-order artifact on this item set; does **not** establish general order-invariance or semantic identification |
| `INCONCLUSIVE` (either variant) | No update to Phase B's interpretation |
| `INCONCLUSIVE_BY_INSTABILITY` | No update to Phase B's interpretation; flags `score`'s repeat-level reliability as a separate concern |
| `UNCLASSIFIABLE` | No update to Phase B's interpretation; flags a measurement-viability concern |

**No outcome authorizes**: a `score` Stage 1 manifest, a workflow-level
escalation policy, or a semantics claim for any of M/X/A. The P1/P4
control diagnostic, regardless of its own result, authorizes nothing on
its own — it is contextual, not a gate.

## 10. Next step

The next artifacts, per Option B: a rebuilt `build_score_presentation_
sensitivity_manifest.py` (same 3 items, same 4 permutation definitions,
now additionally recording each permutation's `role` and
`permutation_distinct_from_P1` fields, and asserting/aborting on the
content-equivalence check in §4) and a rebuilt runner restricting
`NONCANONICAL_LABELS` to `{P2, P3}`, adding the §6.3 diagnostic as a
separate computation, and updating the required output fields per §6.1.

**Self-tests required before this revision may be considered re-reviewed
(all listed explicitly, per review)**:
1. `P4` is rejected from the non-canonical comparison set (structural
   membership check on `NONCANONICAL_LABELS`).
2. `P4` is not included in the decision-change numerator/denominator.
3. `P4` is not included in confidence-range or TV-distance calculations.
4. `P1` and `P4` results remain separately recorded (never pooled into
   one 6-response cell).
5. An artificially large `P1`/`P4` difference does **not** produce
   `MATERIAL` and does **not** affect `item_coverage_complete`.
6. A genuine `P2` or `P3` decision change still produces `MATERIAL`
   (positive-path check, so the fix isn't over-broad).
7. A clean `P1`/`P2`/`P3` result cannot become `NEGLIGIBLE` merely
   because `P4`'s cell is present and stable — nor prevented from being
   `NEGLIGIBLE` by an unstable `P4` cell (`P4`'s stability is fully
   inert to classification).
8. The manifest builder rejects (raises on) a supposedly non-canonical
   (`P2`/`P3`) permutation whose contents are byte-identical to `P1` —
   with a mutation test proving this check actually fires, not merely
   documented.

**Not built yet, and no API call is authorized by this document.**
