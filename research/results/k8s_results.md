# Independent-workflow replication (Kubernetes): results

**Protocol:** `research/methodology/independent_workflow_preregistration.md`
v1 plus Amendments 1–7. All amendments were written before any model
output existed.

**Analysis:** `research/src/analyze_k8s.py`, run once as frozen.

**Numbers:** `k8s_analysis.json`.

**Run.**
- **Calls:** 9,738 on pinned `jev-1.13.0` (development 500 issues, test
  582).
- **All** HTTP 200, all parsed, 0 retries, 0 failed issues.
- **The raw outputs were committed before analysis** (`693d1eb`).

**Framing (binding).** Development (2015–2019) and test (2021–2026)
differ at once in:
- period;
- issue-form use (0% vs 73%);
- label prevalence (escalate 21% vs 4%).

This is a **combined temporal and distribution-shift transfer test**,
not an isolated label-shift test.

## Pre-registered tests (Holm across K1–K3)

| | Estimate | 95% CI (paired) | Verdict |
|---|---|---|---|
| **K1:** action error rate vs final-step confidence | 0.776 vs 0.628, **+0.148** | [+0.091, +0.207] | **Supported. The finding replicates.** |
| **K2:** action error rate vs chance | 0.776 | [+0.241, +0.312] above 0.5 | **Supported** |
| **K3:** BBSE-weighted vs unweighted quota fit (priority-wrong target) | 0.348 vs 0.699, **−0.350** | [−0.428, −0.271] | **Inconclusive (negative estimate)**, by the frozen rule |

**About K3.**
- **Why the label is "inconclusive":** the frozen rule calls a
  non-supported K3 inconclusive and never evidence that the correction
  fails, because K3's power was not simulated. That label stands.
- **Descriptively, the whole interval is far below zero.** The mechanism
  is visible:
  - BBSE was numerically stable (condition number 39) and estimated the
    test mix as **[0, 1, 0]**, all middle level;
  - the true mix among stable answers was **[0.69, 0.26, 0.05]**, mostly
    level 0;
  - the weighting therefore pushed the fit toward the wrong level.
- **This answers the open question** from the original study, whether
  the BBSE ranking gain needs a dominant middle level: here it did not
  hold.
- **The calibration-window weights** (arm c, labels from the preceding
  150 issues) gave 0.663, also below the unweighted 0.699.

## Secondary (no multiplicity claims)

**Estimators:**
- **`E_dec` vs action rule:** `E_dec` is 0.787; difference +0.004 to
  +0.017 (CI). A small gain, as for Qwen and OLMo in the original study.
- **`E_all` vs `E_dec`:** −0.046 to +0.010. Confidence adds nothing.

**Robustness of the K1 contrast:**

| Subset or target | Action rule | Confidence |
|---|---|---|
| Any node wrong | 0.721 | 0.648 |
| SIG node, the only SIG with n ≥ 50 (n = 521) | 0.822 | 0.621 |
| Early-triage subset (labels within 30 days; n = 442) | 0.760 | 0.632 |

**Shift with a natural development set:** the action rule fit on the
2015–2019 *natural* development set ranks 2021–2026 priority errors at
0.740. A chronological natural development fit did not invert, unlike
the quota fit.

**Level-0 sublabels:** the priority-wrong rate is 0.76 for
important-longterm and 0.71 for backlog.

**Instability by label:**
- quota subsample: 0.000 / 0.029 / 0.039 (levels 0 / 1 / 2);
- test overall: 0.012.

Low and similar across levels, so the extra BBSE assumption is roughly
plausible. It was not the cause of the failure.

**Hypothetical cost** (frozen table, not validated for Kubernetes): no
review 460, oracle at 10% (k = 59) 418.

## What this adds to the paper

1. **The main predictive finding transfers.** In an independent
   workflow on a different platform, with three-way routing, a different
   binary question and triager priority, it holds across a five-year
   chronological shift. The action's historical error rate ranks
   failures better than final-step confidence, by +0.148.
2. **It again comes almost entirely from the action rule;** the
   estimator adds little.
3. **The label-free correction did not transfer.** Its estimate
   collapsed onto the middle level again, and here the true mix was
   elsewhere, so it hurt. The paper's BBSE claim must be restricted
   accordingly.
