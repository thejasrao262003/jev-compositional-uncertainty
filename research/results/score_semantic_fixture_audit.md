# Semantic Fixture Audit — the 6 Primary Compositions

**Distinct from the gate/verifier implementation audit** (per review):
that audit asked "does the code correctly execute the declared rules?"
This document asks a narrower, prior question for each of the 6 primary
compositions specifically: "is the composition's own claimed
classification mathematically correct, checked item by item against the
8-point checklist below?" A correct implementation could still be pointed
at a wrong or insufficient set of fixtures — this is the check that it
isn't, item by item, not just in aggregate.

Source data: `score_semantic_composition_table.csv` (script-generated,
`verify_score_semantic_compositions.py`, sha256 `ffb86c3f...` — see
`score_verifier_freeze_manifest.json`). Every value below is read from
that frozen table, not recomputed by hand for this document.

## Per-item audit, 8-point checklist

| # | Check | Applies to |
|---|---|---|
| 1 | Multiset contains exactly 4 values | all 6 |
| 2 | M is defined | all 6 (by design — undefined-M items are excluded from primary, §3) |
| 3 | X computed from the intended level domain `{0,1,2}` | all 6 |
| 4 | A uses the specified deterministic rounding rule (round-half-up) | all 6 |
| 5 | The claimed M/X/A relationship is independently derivable from the composition alone | all 6 |
| 6 | No primary item has `M = X = A_rounded` | all 6 |
| 7 | Claimed discrimination class matches the mathematical relationship | all 6 |
| 8 | Supplementary tie item excluded from this set | checked once, at the end |

| Composition | 1 | 2 | 3 | 4 | 5 | 6 | 7 | Claimed class | Verified? |
|---|---|---|---|---|---|---|---|---|---|
| `(0,0,0,1)` | ✓ (4 values) | ✓ M=0 | ✓ X=1∈{0,1,2} | ✓ 0.25→0 | ✓ 3 zeros+1 one → mode 0, max 1, mean 0.25 | ✓ 0≠1 | ✓ {M,A}=0 vs X=1 → TWO_WAY | TWO_WAY | **YES** |
| `(0,0,0,2)` | ✓ | ✓ M=0 | ✓ X=2 | ✓ 0.5→1 | ✓ 3 zeros+1 two → mode 0, max 2, mean 0.5 | ✓ 0≠2≠1 | ✓ M=0,X=2,A=1 all distinct → THREE_WAY | THREE_WAY | **YES** |
| `(0,0,1,2)` | ✓ | ✓ M=0 | ✓ X=2 | ✓ 0.75→1 | ✓ 2 zeros+1 one+1 two → mode 0 (2 of 4, unique), max 2, mean 0.75 | ✓ 0≠2≠1 | ✓ M=0,X=2,A=1 all distinct → THREE_WAY | THREE_WAY | **YES** |
| `(0,1,1,2)` | ✓ | ✓ M=1 | ✓ X=2 | ✓ 1.0→1 | ✓ 1 zero+2 ones+1 two → mode 1 (2 of 4, unique), max 2, mean 1.0 | ✓ 1≠2 (A=1=M) | ✓ {M,A}=1 vs X=2 → TWO_WAY | TWO_WAY | **YES** |
| `(0,1,2,2)` | ✓ | ✓ M=2 | ✓ X=2 | ✓ 1.25→1 | ✓ 1 zero+1 one+2 twos → mode 2 (2 of 4, unique), max 2, mean 1.25 | ✓ 2≠1 (M=X) | ✓ {M,X}=2 vs A=1 → TWO_WAY | TWO_WAY | **YES** |
| `(1,1,1,2)` | ✓ | ✓ M=1 | ✓ X=2 | ✓ 1.25→1 | ✓ 3 ones+1 two → mode 1 (3 of 4, unique), max 2, mean 1.25 | ✓ 1≠2 (A=1=M) | ✓ {M,A}=1 vs X=2 → TWO_WAY | TWO_WAY | **YES** |

**All 6 primary items: verified.** 2 genuine three-way splits
(`(0,0,0,2)`, `(0,0,1,2)`), 4 two-way splits, zero items with
`M=X=A_rounded` (the exact defect that invalidated 2 of Revision
1-3's items).

**Check 8 — supplementary exclusion**: `(0,0,2,2)` has 2 zeros + 2 twos —
a genuine count-tie at the top (2=2), so no unique mode exists by the
stated rule; `M` is correctly undefined, and the composition is
correctly excluded from the primary 6-item set (tagged
`supplementary_contested_tie`, not swept in by a generic filter — see
`verify_score_semantic_compositions.py`'s explicit assertion).

## What this audit does and does not establish (per the three-tier hierarchy, spec §8)

- **Verifier validity** (does the code correctly execute the declared
  rules?) — addressed separately, by the implementation/mutation audit.
- **This document's contribution — one layer of semantic validity**:
  confirms the *specific 6 fixtures* chosen for the primary gate are
  themselves mathematically sound relative to the *declared* M/X/A
  definitions (§2) — not that those definitions are the right ones to
  test `score` against, and not that 6 fixtures are *enough*.
- **Still open, not addressed here or anywhere yet**: whether M, X, or A
  is the construct Jev's `score` primitive is actually built around
  (semantic validity, full sense), and whether 6 compositions in one
  domain can adequately characterize that behavior (research validity).
  Both remain exactly as open as before this document — this audit
  narrows "is the fixture set internally sound" to a checked yes, nothing
  more.
