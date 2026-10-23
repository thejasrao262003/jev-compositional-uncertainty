# Kubernetes replication: build report and feasibility outcome

**Protocol:** `independent_workflow_preregistration.md` v1 plus
Amendment 1 (cleaning fix).

**Snapshot:** 2026-10-23T17:51:00.031112+00:00

**Calls:** none. This was a GitHub-only build; no Jev call was made.

## Counts

- **Fetched:** 12,535 candidate items (issues and pull requests).
- **Eligible:** 1,320.
- **Exclusions:** {"not_exactly_one_kind": 2093, "not_exactly_one_sig": 187, "too_short_after_cleaning": 30, "pull_request": 8738, "not_exactly_one_priority": 36, "excluded_label": 120, "after_cutoff": 11}.

**Splits (chronological):**

| Split | Issues | Created | Filed through issue forms |
|---|---:|---|---:|
| Development | 500 | 2016-02-03 – 2020-08-13 | 0% |
| Calibration | 150 | 2020-08-17 – 2022-04-21 | 22% |
| Test | 483 (after removing 17 linked) | 2022-05-09 – 2026-09-30 | 80% |

## Target-action prevalence under F

| Split | accept | defer | escalate |
|---|---:|---:|---:|
| Development | 237 | 153 | 110 |
| Calibration | 87 | 48 | 15 |
| Test | 380 | 87 | **16** |

## Gates

- **Leakage, hard checks: PASS** (after Amendment 1).
  - **First build:** 24 issues kept quoted prow commands, and old-template
    kind answers leaked.
  - **Fixed** by Amendment 1. The rebuild has 0 hard failures.
- **Feasibility: FAIL.** The rule needs n ≥ 20 for each action in both the
  development and test sets. The test set has **16 escalate**.
  **By the pre-committed rule, the study stops as infeasible under the
  pre-registered design. No model call is made.**

## Why the gate fails

The project changed between the two periods:

| | Development (2016–2020) | Test (2022–2026) |
|---|---|---|
| `critical-urgent` issues | 22% | 3% |
| Issues filed through forms | 0% | 80% |

This is itself a large, natural label-prior shift. It is exactly the
situation the paper's label-shift finding concerns, so it is
informative. But the frozen design cannot be run on it.

## Other diagnostics

- **Priority-label lag:** median 4 days, 90th percentile 443 days.
- **Early-triage subset:** 729 issues.
- **Dataset SHA-256:** `ed30cb7119cc3530f6f5066e452be283b6938ddbe32c36c6e09b793e8f2bc9bd`.
