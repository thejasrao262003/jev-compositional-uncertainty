# Kubernetes replication: build report (Amendment 2)

**Protocol:** `independent_workflow_preregistration.md` v1 plus
Amendment 1 (cleaning) and Amendment 2 (test widened to 600, one-time).

**History.** The pre-registered 500-issue test window failed the
feasibility gate (16 escalate). That result is kept in git at commit
`09ae38a`. This report is the amended build.

**Snapshot:** 2026-10-23T17:54:37.382680+00:00

**Calls:** none (GitHub-only build).

## Splits

| Split | Issues | Created | Issue-form share | accept | defer | escalate |
|---|---:|---|---:|---:|---:|---:|
| Development | 500 | 2015-06-02 – 2019-07-18 | 0% | 248 | 149 | 103 |
| Calibration | 150 | 2019-07-19 – 2021-04-09 | 0% | 81 | 49 | 20 |
| Test | 582 (600 minus 18 linked) | 2021-04-16 – 2026-09-30 | 72% | 441 | 116 | 25 |

## Gates

1. **Feasibility: PASS.** Every action has n ≥ 20 in both the
   development and test sets, after linked-issue removal.
2. **Leakage, hard checks: PASS** (0 failures).
3. **Power at the realized n = 582:** recomputed before any call
   (`k8s_power_realized.json`). d\* is fixed from it.
4. **Not authorized by passing these gates:** the 270-call smoke test and
   the 40-issue blinded human read. Each is a separate decision.

## Binding framing

Development and test differ at once in:
- **label prevalence:** 21% vs 4% escalate;
- **input format:** 0% vs 72% issue forms;
- **period:** 2015–2019 vs 2021–2026.

So this is a **combined temporal and distribution-shift test**, not an
isolated label-shift test. It is a transfer test, not a guaranteed
replication.

## Other diagnostics

- **Priority-label lag:** median 4 days, 90th percentile 468 days.
- **Early-triage subset:** 732 issues.
- **Dataset SHA-256:** `60aa4120c2e51b3c5bbc0554cf8b4833df6905e763c655606693fb69089372ba`.
