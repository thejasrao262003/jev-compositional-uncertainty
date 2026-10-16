# Grammar Draft 3 — independent review (2026-10-16)

**Reviewer:** a separate agent instance with no access to the author's
reasoning, working read-only (no edits, no API calls). It reviewed the
spec, the generator, the units file and the audit JSON at the Draft 3
commit `c0b3d9e`. **Verdict: not ready.** Verbatim findings are
summarized below. The author's responses are pending Draft 4.

## Critical

- **C1. Capacity depends on fine paraphrase distinctions.**
  - Merges the reviewer judges defensible under §5.1 drop pools below
    `N_MAX = 1,260`: impact:0 to 288–360, impact:unclear to 370, routing
    to 504/588, severity:2 to 268. The needs are 430 and 645.
  - In both impact:0 and impact:unclear, each component carries 6 reasons
    for one conclusion. That is only 72–74 independent subjects against
    about 430 instances.
  - **Fix:** add subjects rather than predicate variants, or lower
    `N_MAX`. Either way, promote the subject-blocked analysis.
- **C2. Most blocking sentences don't state "no workaround".**
  - Only 112/448 (25%) do. The rest say "retrying does not help", "the
    previous version cannot be restored" or "cannot be completed
    manually".
  - §4's claim that every blocking sentence states no workaround exists
    is false.
- **C3. Customer-facing evidence still leaks through meaning.**
  - The three sentences have no referential link: the impact sentence's
    component is unrelated to the routing component and the severity
    function.
  - Some routing subjects are commerce-coded (product catalog,
    shipping, inventory, session state: 192 units), as are some severity
    functions (email delivery, form submission).
  - About 20 of the 74 impact:unclear components are customer-coded
    (gift cards, coupons, loyalty points, receipts…).
  - **Fix:** link the sentences (an instance-level "the only affected
    service is {c}"), make the subjects neutral, and have a human label
    about 50 composed instances before freezing.

## Moderate

- **M1.** Severity cues inside impact:1 ("urgent pages", "escalations",
  and "surge/wave/burst" in all 448). They are seen only when c2 = 1,
  which biases the c2 = 1, c3 = 1 defer cell.
- **M2.** Some frames belong to a single value ("A design review found
  that…" is cosmetic only; "Testing shows that…" is degraded only).
  These imply internal or pre-production, and bias `noul`. A10 misses
  "narrow mobile screens" and "desktop app".
- **M3.** Network cues in 187/448 blocking sentences ("request",
  "responds", "path", "route") are missed by A5.
- **M4.** `_contains` misses inflections ("fail" doesn't match
  "failures"). 74 impact:unclear units mention failures and a fallback.
- **M5. Labels are recoverable from surface form.**
  - c3: `" but " → 1; ", and " → 2; else 0` is **100%** accurate.
  - c2: one keyword regex is **98.4%** accurate.
  - Length alone gets about 60%.
  - Some opening words belong to a single value.
  - So the second pilot's `d` measures detection of templated
    patterns. Disclose that as a scope limit, and share frames across
    values.
- **M6.** A11 is tautological. It re-applies the same filters, so it can
  only check coverage. The fit tables themselves are unaudited.
- **M7.** The spec is stale or overclaims:
  - "magnitudes balanced across instances" is not implemented;
  - §7 still names seed v1, and §10 still shows Draft 1 counts;
  - "next: review Draft 2" is stale;
  - "impact sentences assert no severity" is contradicted by M1 and M4.

## Minor

- **Implausible combinations:** free-tier customers with "account
  managers"; "synthetic test fixtures" on every component; "disk I/O
  wait at the connection pool"; "link flaps" on DNS resolvers.
- **Weak entailment:** "excluded from every customer-facing SLA" doesn't
  entail "not customer-facing".
- **A12 gaps:** the plural check isn't applied to every pool, and there
  is dead code.
- **Pilot vs. main:** 100% of pilot subjects reappear in main. They are
  disjoint by proposition and text, but this should be disclosed.

## Verified correct

- Seeding is deterministic.
- IDs are content-blind.
- Stored proposition keys match a fresh recomputation.
- The fail-closed declarations work.
- A2, A3 and A4 hold.
- Magnitude classes are balanced within each routing pool.
