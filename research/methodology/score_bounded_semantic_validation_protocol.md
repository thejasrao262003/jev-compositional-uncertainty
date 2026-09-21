# `score` Bounded Semantic-Validation Protocol

Status: **Phase A (freeze + candidate-completeness gate) complete below.
Phase B is a definition only — not executed, not authorized.** Approval
of this document authorizes drafting, not calling the API. Execution of
Phase B requires a separate, explicit sign-off, per every prior stage's
practice in this project.

## Phase A — Pre-execution semantic freeze

### A.1 Frozen inputs (referenced, not restated as new fact)

- **Composition set (9 items)**: 6 frozen n=4 items
  (`score_semantic_validation_specification.md` §3) + 3 supplement n=5
  items (`score_mvsa_supplement_manifest_spec.md`). Neither set is
  modified by this document.
- **Candidate definitions**: M (mode), X (max), A (rounded mean) — gate
  spec §2, unchanged.
- **Pairwise accounting**: M-X 7/9, M-A 6/9, X-A 9/9 —
  `score_mvsa_supplement_v1.json`, unchanged.
- **Allocation robustness result**: the 2-THREE_WAY+1-TWO_WAY selection
  is not uniquely load-bearing (the 1+2 alternative also clears
  threshold) — unchanged.
- **`≥6` threshold**: retained as a **provisional design criterion**,
  explicitly not an empirically validated sufficiency standard. This
  status does not change based on anything in this document.
- **Immutable identity of the 3 supplement compositions**: recorded
  separately from the (already-frozen, not retroactively touched)
  verifier audit — `research/data/characterization/
  score_supplement_hashes.json` locks the design script's and the
  supplement record's SHA-256 hashes plus the 3 compositions'
  identities (`(0,0,0,1,2)`, `(0,0,0,2,2)`, `(0,0,2,2,2)`), independently
  reproducible from `design_score_mvsa_supplement.py`'s pure-function
  search + selection rule alone (§3 of the manifest spec). Any future
  change to which 3 compositions are used requires a new version label
  (v2) and a new hash entry, never a silent overwrite of v1.

### A.2 Candidate-set adequacy gate (new, binding rule)

> **If a plausible alternative semantic family has not been considered or
> explicitly excluded by available contract evidence, the experiment may
> report discrimination among M, X, and A, but must not characterize the
> result as identifying `score`'s intended semantics.**

**Candidate families considered, and their status:**

| Family | Status |
|---|---|
| M, X, A (mode / max / mean) | Modeled, discriminable on this 9-item set (§A.1) |
| **Order/position-dependent aggregation** | **Not hypothetical — already observed, with confirmed controls (checked directly against the run script, not assumed).** `score_mix_L1_L2` vs. `score_mix_L1_L2_swapped` (`research/src/run_step0a2.py` lines 124/126, `step0a2_order_and_score_report.md` §2.2) use the **identical two sentences** (`L1a`, `L2b`) and the **identical instructions/criteria** (both draw from the single module-level `SCORE_INSTRUCTIONS`/`SCORE_CRITERIA`) — the state strings are `["L1a","L2b"]` vs. `["L2b","L1a"]` respectively, so **concatenation order is the only variable that differs**. Under that clean, single-variable comparison, confidence moved 0.73→0.86 and level-2 probability mass moved 0.18→0.09. Separately, `choice` showed a much larger, independently replicated order effect under the same single-variable-order-swap design (confidence 0.82→0.01, `step0a2_order_and_score_report.md` §1.2). **M, X, and A are all defined purely from the multiset of severity levels — every one of them is order-invariant by construction.** If `score`'s true aggregation is order-dependent (directly evidenced above, at least in part), *no* candidate in `{M, X, A}` can ever be the complete explanation, regardless of how much M-vs-X/M-vs-A/X-vs-A coverage exists. This is the single most concrete, evidence-backed gap in the current candidate set — not a generic hedge, and not an unverified assumption about what the prior experiment controlled. |
| A weighted (non-uniform) statistic | Not modeled, not excluded — plausible, untested |
| A transformation/normalization before aggregation | Not modeled, not excluded — plausible, untested |
| A probability-derived statistic not captured by M/X/A | Not modeled, not excluded — plausible, untested |
| A nonlinear aggregation / concentration effect | Not modeled, not excluded — plausible, untested |

**What the order-sensitivity finding does and does not establish, stated precisely (per review):**

| Claim | Status |
|---|---|
| M, X, A are order-invariant | Established, by their definitions |
| `score` has exhibited order sensitivity in prior observations | Reported as an existing experimental finding (confirmed controls, above) |
| M/X/A cannot fully represent order-dependent behavior | Follows from the invariant definitions |
| The exact mechanism causing `score`'s order sensitivity is known | **Not established** |
| The order effect necessarily represents `score`'s intended semantics | **Not established** |
| Canonical-presentation M/X/A comparisons can identify complete `score` semantics | **Not justified** |

**Consequence, binding on Phase B and C**: because order-dependence is
independently evidenced (not merely hypothetical), any Phase B result —
even a clean CLARITY outcome among M/X/A — must be reported as
*"discrimination among M, X, and A under canonical (fixed) presentation
only"*, never as *"identification of `score`'s intended semantics."* A
dedicated order-dependence characterization for `score` (analogous to
Step 0A.2's `choice` study) is a **separate, later, explicitly out-of-
scope study** for this protocol — folding it into Phase B would confound
"which of M/X/A" with "is `score` order-dependent at all" in one dataset,
making neither question answerable cleanly.

### A.3 Gate-mechanics resolution for 9 items (a design decision, made now)

The existing 3-way CLARITY/FAILURE/AMBIGUITY gate (`score_semantic_
validation_specification.md` §5.2) was exhaustively verified for **N=6**
(`CLARITY_MIN=5`, `CLARITY_OTHERS_MAX=3`, `FAILURE_MAX=3`). Rather than
invent and re-verify a new set of thresholds for N=9 (which would need
its own exhaustive/mutation-tested audit before being trusted), this
protocol resolves the question as follows:

- **The primary 3-way gate runs unchanged, on the frozen 6 items only** —
  reusing the already-verified `verify_score_gate_logic.py` procedure
  exactly as audited, no new thresholds.
- **The supplement's 3 items are used exclusively for pair-specific `n_P`
  accounting** (`score_semantic_identification_protocol.md` Workstream 5)
  — i.e. they inform whether a given pair has *enough separating
  evidence*, not a re-scaled version of the 3-way CLARITY decision.

This avoids inventing unverified new gate mechanics while still using all
9 items for the purpose they were actually designed for. **This is a
resolved design decision, open to being overridden by review**, not a
deferred question.

**Quantities kept visually and mathematically distinct, in both code and
reporting (per review's accounting safeguard)** — any future analysis
script MUST keep these as separate variables/columns, never merged:

| Quantity | Denominator | Source |
|---|---|---|
| Gate input | 6 (frozen) | `gate()` from `verify_score_gate_logic.py`, unmodified |
| Gate decision denominator | 6 (frozen) | same, unmodified |
| Supplementary pairwise accounting | 3 (new) | `design_score_mvsa_supplement.py` |
| Pairwise coverage denominator | up to 9, per-pair `n_P` | combined, pair-specific only |

**Required phrasing, prohibited phrasing, stated explicitly:**

> **Prohibited**: "the nine-item gate passed" — no nine-item gate exists.
> **Required**: "the frozen six-item gate remains unchanged; the three
> supplementary compositions extend pair-specific identifiability
> accounting only."

Any future analysis code implementing Phase B must call the frozen
`gate()` function on the 6-item data exactly as-is, and compute pairwise
`n_P` counts via a **separate** function operating on the combined 9-item
data — never a single function that takes 9 items as input to a
redefined gate.

## Phase B — Bounded semantic-validation pilot (definition only)

**Purpose, stated narrowly**: characterize *observed agreement and
disagreement* among M, X, and A on the 9-item set. **Not** to select a
target, not to establish generalization, not to authorize Stage 1.

- **Items**: all 9 (6 frozen + 3 supplement), canonical presentation only
  (no alternate-order layer — see §A.2's scoping decision).
- **Repeat structure**: identical to the gate spec's §5.0 — 3 calls per
  item (1 canonical + 2 repeats), modal-decision reduction, an explicit
  `repeat_unstable` category for items without a consistent modal
  decision (never forced into a fake mode).
- **Budget**: 9 × 3 = **27 calls, fixed before execution**. This is the
  complete planned-call count; transient-error retries (already handled
  inside `JevClient`, per every prior stage's convention) are not
  additional planned calls and do not change this number. Not executed.
  Not authorized by this document.
- **Computed, after data collection (not before)**:
  - Per-item modal `jev_level`, compared against M/X/A (categorical
    matching, gate spec §5.1).
  - The frozen-6 3-way gate outcome (CLARITY/FAILURE/AMBIGUITY),
    unchanged mechanics (§A.3).
  - Pair-specific `n_P` **observed** match counts (not just designed
    coverage) — e.g., of the 6 items separating M-vs-A, how many actually
    favored M vs. A vs. neither (repeat-unstable)?
  - Repeat-instability rate across all 9 items.
- **Explicit non-claims, restated**: no target selection, no Stage 1
  authorization, no candidate-completeness resolution, no order-
  dependence characterization for `score`.

### Explicit scope exclusion (per review, stated as its own rule, not implied)

> **Phase B cannot investigate the already-observed order-sensitivity
> gap.** Canonical-only presentation means every item is called at
> exactly one fixed sentence order. Phase B can characterize Jev's
> response *at that one order* and compare it to M/X/A; it **cannot**
> establish whether that response would hold at a different order, and it
> **cannot** explain the order effects already observed for `score` and
> `choice` elsewhere in this project. Any Phase B/C report that discusses
> order-sensitivity may only cite the *prior* Step 0A.2 findings — it may
> not present Phase B's own (canonical-only) data as evidence about
> order-invariance one way or the other.

## Phase C — Post-pilot authorization review (criteria, not a verdict)

Evaluated only after Phase B data exists (none does yet):

1. **Stability check**: is the `repeat_unstable` rate low enough that the
   modal decisions are themselves trustworthy? No pre-set numeric bar is
   fixed here — Phase C must set one *before* looking at the Phase B
   data, not after.
2. **Frozen-6 gate outcome**, taken at face value per its own verified
   mechanics (§A.3) — CLARITY, FAILURE, or AMBIGUITY.
3. **Cross-check against pair-specific evidence**: if the frozen-6 gate
   resolves to CLARITY for a candidate whose winning margin depended on a
   pair *not* meeting `n_P≥6` even with the supplement folded in, that is
   a red flag requiring explicit disclosure, not a clean pass.
4. **Candidate-set adequacy gate reapplied** (§A.2): even a clean,
   well-evidenced CLARITY outcome is reported as *"discrimination among
   M/X/A under canonical presentation"* — never as *"`score`'s intended
   semantics identified"* — until order-dependence and the other
   unexcluded families are separately addressed.
5. **"Underidentified" is an explicitly acceptable outcome** — if results
   depend on an underrepresented or unmodeled semantic family (most
   plausibly: if the modal decisions look sensitive to which specific
   sentence order happened to be used as "canonical" for a given item),
   the correct report is "insufficient for identification," not a forced
   candidate selection.
6. **No automatic Stage 1 expansion.** Whatever Phase C concludes, it
   does not by itself authorize a `score` Stage 1 manifest, a larger item
   set, or any change to the semantic target — that remains a fully
   separate, later decision.

### Outcome-interpretation matrix (per review — every combination must have a defined interpretation, not just the favorable ones)

| Frozen-6 gate | Stability | Pair-specific check | Required interpretation |
|---|---|---|---|
| CLARITY | Low instability | Winning pair meets `n_P≥6` | Strongest available outcome: report as "discrimination among M/X/A, canonical presentation only" (§A.2) — still not semantic identification |
| CLARITY | Low instability | Winning pair **below** `n_P≥6` | Red flag (criterion 3) — report the CLARITY outcome alongside its evidentiary weakness explicitly, not as an unqualified pass |
| CLARITY | **High** instability | (either) | Instability undermines trust in the modal decisions the gate itself was computed from — report as "CLARITY reached, but on unstable underlying data" — not a clean result regardless of pair coverage |
| FAILURE | (either) | — | No candidate reached a majority — report plainly; this is a legitimate, informative outcome about `score`, not a defect in the pilot |
| AMBIGUITY | Low instability | Deciding items concentrated on a `n_P`-sufficient pair | "Genuinely ambiguous" — candidates are stably indistinguishable on well-evidenced comparisons |
| AMBIGUITY | Low instability | Deciding items concentrated on a `n_P`-insufficient pair | **"Underidentified by design"** (criterion 5) — the composition set, not `score`'s behavior, is the limiting factor |
| AMBIGUITY | **High** instability | (either) | Cannot distinguish "genuinely ambiguous" from "underidentified" from "too unstable to tell" — report as "inconclusive," the weakest but still explicitly defined outcome |

Every cell above has a required report phrase — Phase C is not permitted
to reach a combination not listed here without first extending this
table, reviewed, before interpreting that data.

## Six binding conditions before Phase B may execute (restated as gates, not just noted)

| # | Condition | Status |
|---|---|---|
| 1 | Input-length confounding (n=4 vs. n=5) retained as a limitation, never treated as behaviorally equivalent without a control | **Bound** — stated in `score_mvsa_supplement_manifest_spec.md` §8, unchanged here |
| 2 | `≥6` threshold remains provisional; passing it cannot auto-trigger semantic acceptance | **Bound** — §A.1 |
| 3 | Pair-specific evidence (`n_P`) is the accounting unit; pair-silent items excluded from that pair's evidence | **Bound** — §A.3, Phase B's computed outputs |
| 4 | Alternative semantics documented, including which are excluded and why | **Bound** — §A.2's table; order-dependence flagged as evidenced, not hypothetical; four other families remain unexcluded |
| 5 | A stopping rule exists; "insufficient for identification" is an acceptable outcome | **Bound** — Phase C item 5 |
| 6 | No automatic Stage 1 expansion from a pilot result | **Bound** — Phase C item 6 |

All six are satisfied by this document's design. **None of them being
satisfied authorizes execution** — that is a separate decision, still
pending.
