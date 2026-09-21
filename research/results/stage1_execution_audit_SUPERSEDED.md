# Stage 1 Execution Audit — SUPERSEDED (analysis implementation defect)

**This file is preserved for the audit trail only. Do not cite its
section 4 or section 8 conclusions.** It is the raw output of the first
run of `stage1_audit.py`, before `analyze_stage1.py`'s
`compute_repeat_instability`/`compute_presentation_sensitivity` were
fixed to scope to the manifest's actual `robustness_repeat_subset_ids`
(12 items) instead of inferring scope from "any item with a qualifying
record" (which matched all 60 primary items, since every item has a
`primary_canonical` row).

**Precise wording, per review**: the experimental execution had zero
deviations from the preregistered plan — 108/108 calls succeeded exactly
as planned, against the frozen manifest. What follows is a **post-
execution analysis implementation defect**, found and fixed before this
run's results were finalized, not an execution deviation and not missing
experimental data. See `stage1_execution_audit.md` (the corrected,
authoritative report) for the fix and the correct results.

## Superseded output (section 4 and section 8 only — the affected sections)

```
======================================================================
4. Complete-cell eligibility (via analyze_stage1.py, H2a-gated)
======================================================================
  Stage 0 noul H2a recorded status: pass=True
  repeat-instability: 12 complete items, 48 incomplete (expect 12, 0)
  presentation-sensitivity: 12 complete items, 48 incomplete (expect 12, 0)
  INCOMPLETE (repeat): [48 entries, one per primary item outside the
  Layer 2/3 subset, each showing m_observed=1, m_required=3 - WRONG:
  these 48 items were never designed to have m=3; they only ever had 1
  planned canonical call. The check should not have applied to them at
  all. See analyze_stage1.py's fix: both functions now take
  `subset_item_ids` explicitly and skip any item outside it, rather than
  inferring scope from which records exist.]
  INCOMPLETE (presentation): [same 48 items, k_observed=1, k_required=3 -
  same root cause.]

======================================================================
8. Deviations from the preregistered execution plan
======================================================================
  Deviations found: ['incomplete cells present']
  WRONG: this was the analysis-scope defect above being misread as an
  execution deviation. Corrected report (stage1_execution_audit.md)
  shows: Deviations found: NONE.
```

Sections 1, 2, 3, 5, 6, and 7 were unaffected by this defect (they don't
depend on the repeat-instability/presentation-sensitivity subset-scoping
logic) and their superseded values match the corrected report's values
exactly.

**Code revision that produced this superseded output**: the version of
`analyze_stage1.py`'s `compute_repeat_instability`/
`compute_presentation_sensitivity` functions before the
`subset_item_ids` parameter was added (see git-free hash trail: this
project has no commits yet, so the fix is documented here by description
rather than by commit SHA — the corrected functions are the ones
currently on disk).
