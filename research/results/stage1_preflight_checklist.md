# Stage 1 (`choice` + `noul`) Preflight Checklist

Status: **manifest generated and fully validated; zero Stage 1 API calls
made.** This document closes out the 8-item pre-execution checklist from
review. Execution itself is a separate, subsequent authorization.

## 1. Item accounting (resolves the 60 vs. 64 discrepancy)

| Manifest component | Count |
|---|---|
| Primary `choice` items (2 domains × 15) | 30 |
| Primary `noul` items (2 domains × 15) | 30 |
| **Primary items, total** | **60** |
| Preregistered reserve/overflow replacements (1 per primitive per domain) | 4 |
| **Total manifest entries** | **64** |

The 4 overflow items are **not** part of the core call plan (`run_stage1.py`'s
`build_plan()` explicitly skips any `item_id` containing `"overflow"`) —
confirmed by the dry-run count below. They exist only as preregistered,
structurally-matched substitutes (§11) for manual, reviewed use if a
primary cell fails irrecoverably — never auto-substituted, never counted
in the primary denominator.

## 2. Exact call allocation (confirmed by dry run, zero API calls)

`build_plan()` was called directly against the real manifest — no network
call — and produced exactly:

| Call purpose | Count |
|---|---|
| `primary_canonical` (60 items × 1) | 60 |
| `canonical_repeat` (12-item subset × 2 additional repeats) | 24 |
| `alt_presentation_reverse` (12-item subset × 1) | 12 |
| `alt_presentation_seeded_shuffle` (12-item subset × 1) | 12 |
| **Core total** | **108** |

Matches §11's Stage 1 budget for two primitives exactly. Reserve capacity
(4 overflow items) is tracked separately, not folded into this total.

## 3. Runner audited for `JevClient`-only access — done

`../src/run_stage1.py` imports and calls `JevClient` for every request; no
raw HTTP call exists in the script. Confirmed both by direct inspection
and by the validator (check #9: PASS, `JevClient referenced in:
['research/src/run_stage1.py']`).

## 4. Subset/manifest seed re-derivation — done, strengthened beyond the request

`../src/verify_stage1_rederivation.py` re-runs the **entire** manifest
construction from scratch (fresh process, recorded seeds only) and
confirms the regenerated manifest is content-identical to the one on disk
— not just the 12-item subset, but also the 308 sentences, all opaque
IDs, and the frozen `alternate_orders`. Output saved:
`stage1_rederivation_check.txt`. This is strictly stronger evidence than
re-deriving the subset alone, since every seeded component is proven
reproducible from the two recorded seeds
(`opaque_id_permutation_seed`, `subset_selection_seed`), not just one.

## 5. H2a gate persisted before any `noul` analysis — done, enforced in code

`../data/characterization/stage0_gate_outcomes.json` is the machine-
readable persistence of `stage0_report.md`'s gate table.
`../src/analyze_stage1.py`'s `require_h2a_passed()` reads this file and
**raises `H2aNotPassedError`** if any `noul` metric is requested while the
recorded status isn't `"pass"` — not a comment, an enforced guard,
confirmed by the script's self-test (`H2aNotPassedError` correctly raised
against a synthetic "gate failed" record) and by the validator (check
#10: PASS).

## 6. Complete-cell filtering implemented before aggregation — done, enforced in code

`analyze_stage1.py`'s `compute_repeat_instability`/
`compute_presentation_sensitivity` require exactly `m==3`/`k==3` records
per item before computing `S`/`I`/`D(x)`; anything less is routed to a
separate `missingness` list and excluded from `results`, never pooled.
Confirmed by the script's self-test (a synthetic 2-call "incomplete" item
is correctly excluded and appears only in `missingness`) and by the
validator (check #11: PASS).

## 7. Manifest, metadata, and code revision frozen

- Manifest: `../data/characterization/stage1_manifest_choice_noul.json`,
  content hash `2bf8c78d1f87dcfd...`, recorded as the tracked baseline in
  `../data/characterization/stage0_manifest_hashes.json` (with an explicit
  changelog note explaining the one deliberate re-baseline that occurred
  — adding frozen `alternate_orders` — and confirming it happened before
  any Stage 1 API call, not after).
- Validated: `stage1_choice_noul_manifest_validation.txt` — **all 11
  checks pass**, none N/A (checks 9-11 now genuinely exercised against
  real code, not placeholders).
- Code: `build_stage1_manifest.py`, `run_stage1.py`, `analyze_stage1.py`,
  `verify_stage1_rederivation.py`, `validate_step0b_manifest.py` — current
  state as of this checklist; any further change to any of these before
  execution should trigger a re-run of this full checklist, not a partial
  one.

## 8. Final expected call budget and reserve policy

- **Core planned calls: 108** (§2 above).
- **Reserve capacity: 4 preregistered overflow items** (§1), structurally
  matched to specific primary cells, substituted only manually and only
  on irrecoverable failure — never automated, never selected post hoc.
- **Actual calls executed: 0.** This document is a preflight artifact;
  execution counts will be reported separately, after the fact, from
  `run_stage1.py`'s own `stage1_run_metadata.json` once (if) it runs.
- **Replacement calls**, if any occur: will be attributed explicitly to
  the original failed cell's `item_id` in the eventual run report, per
  §10's missing-call handling rule — never silently merged into the
  primary count.

## Outstanding before execution sign-off

Everything above is a **generation/validation** deliverable, now complete
for `choice`+`noul`. Per the gate table, **execution of the 108 live calls
still requires separate, explicit authorization** — nothing in this
checklist self-authorizes it. `score` remains fully blocked (no Stage 1
manifest exists for it), pending the semantic-validation follow-up
sequence in `stage0_report.md`'s flagged-concern section.
