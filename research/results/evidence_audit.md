# Evidence audit (2026-10-23)

**Plan:** `research/methodology/evidence_audit_and_baselines_plan.md`
(committed `39f944d` before any analysis).

**Code:** `research/src/evidence_audit.py`.

**Numbers:** `evidence_audit.json`.

No API or GPU calls were made. The baseline ablations (sections E, F and
H) are reported separately in `baseline_ablations.md`.

## A. Clean-environment reproduction — PASS, with one defect found

1. **Clean export.** `git archive` of HEAD went into an empty directory,
   with no `.env` and no untracked files.
2. **Figures and tables.** Re-running `make_figure_data.py` gave 19 of 19
   figure and table inputs byte-identical to the committed files. Every
   reported number traces in both the plain and the ACL check.
3. **Full re-run from raw API responses.** Every analysis script was run
   in the clean export: paper statistics, workflow-risk probe, held-out
   validation, cross-model, robustness, intervention, cost mechanism,
   case-level development, power, budget check and sensitivity.
   - 10 of 12 result files were byte-identical.
   - The other 2 differed in a single value, the kernel HR2 one-sided
     lower bound (0.642 vs 0.643).
4. **Diagnosis.** The pre-registered held-out analysis seeded its
   per-tracker bootstrap with `SEED + hash(t) % 1000`. Python's built-in
   string hash is salted per process, so the seed changed between runs.
   Across four hash seeds the HR2 lower bounds were:

   | Bound | Range across hash seeds |
   |---|---|
   | Kernel | 0.640–0.644 |
   | Mozilla | 0.759–0.763 |

   HR1, all point estimates and all test outcomes never changed.
5. **Fix.** The seed is now `zlib.crc32`, which is deterministic. The
   bounds are now 0.762 (Mozilla) and 0.648 (kernel), and the paper is
   updated. Seven other analyses were re-run under a different hash seed,
   and all were byte-identical. No other `hash()` use exists in the
   analysis code.

## B. Independent recomputation — PASS

The baseline-ablation script recomputes the AUROCs with
`sklearn.metrics.roc_auc_score`, not the project's Mann–Whitney code.
`E_dec` and final-step confidence on the pre-registered target match the
paper to three decimals for all five models:

| | Jev | OpenJev | Qwen | Phi | OLMo |
|---|---|---|---|---|---|
| `E_dec` / confidence | 0.763 / 0.549 | 0.748 / 0.575 | 0.736 / 0.473 | 0.677 / 0.401 | 0.637 / 0.551 |

The frozen estimator's hash is verified before use.

## C. Split integrity beyond text overlap — PASS

**Tracker links fetched:** `dupe_of`, `duplicates`, `see_also`,
`blocks`, `depends_on` and `regressed_by`/`regressions` (Mozilla only for
the last two), for all 942 bugs, from the public Bugzilla REST APIs.
These were read-only requests. The cache holds IDs and link fields only.

| Tracker | Held-out bugs linked to a development bug |
|---|---:|
| Mozilla | 8 of 250 |
| Kernel | 1 of 250 |

Without those 9 bugs, HR1 still holds: `E_dec` reaches 0.770 against
0.551 for final-step confidence (n = 491).

## D. Contamination proxy (descriptive)

**Recent** means filed in the 12 months before the held-out sample was
drawn, on or after 2025-10-17.

| Model | Mozilla recent (n = 70): `E_dec` / conf. | Mozilla older (n = 180): `E_dec` / conf. |
|---|---|---|
| Jev | 0.847 / 0.519 | 0.793 / 0.528 |
| OpenJev | 0.870 / 0.546 | 0.817 / 0.566 |
| Qwen2.5 | 0.713 / 0.670 | 0.830 / 0.374 |
| Phi-3.5 | 0.889 / 0.373 | 0.828 / 0.257 |
| OLMo-2 | 0.765 / 0.410 | 0.721 / 0.447 |

**Reading:**
- On recently filed bugs, which are less likely to be in any model's
  training data, the decisions-over-confidence gap persists for every
  model. It is smallest for Qwen2.5 (0.71 vs 0.67).
- The kernel held-out set has only 3 recent bugs, so it is not
  interpreted.
- This is a proxy. Filing date does not guarantee absence from training
  data.

## G. Reference audit — PASS, with one correction

All 40 bibliography entries are now checked against a source. The nine
not checked before were verified against proceedings, publisher or arXiv
pages.

**Correction:** Platt (1999) was cited as a Microsoft Research tech
report. It is now the canonical chapter in *Advances in Large Margin
Classifiers* (MIT Press, pp. 61–74). Missing pages and volumes were also
added (see `CITATION_VERIFICATION.md`).

## Second external audit (addendum J, 2026-10-23)

**Plan:** committed `715883f` before computing.

**Results:** `audit_independent_recompute.json` and
`audit_second_pass.json`.

**Status:** exploratory; no API calls.

### J1. Independent re-implementation — PASS

The re-implementation imports no project analysis code: reduction,
action rule, features, AUROC and bootstrap are all written afresh, from
the raw responses and the frozen estimator's stored numbers.
- **Point estimates match exactly:** HR1 0.763 vs 0.549 (difference
  +0.214), HR2 0.811 and 0.697.
- **Bootstrap bounds differ by 0.001–0.009.** That is Monte Carlo noise
  from a different random-number stream, consistent with the earlier
  hash-seed sweep.

### J2. Per-tracker contrast

`E_dec` − final-step confidence:

| Tracker | Difference [95% CI] |
|---|---|
| Mozilla | +0.279 [+0.191, +0.374] |
| Kernel | +0.124 [+0.023, +0.225] |

Both exclude 0. The kernel effect is weaker.

### J3. Grouped split refit

Development and held-out bugs in shared link components (9 each) were
dropped, and `E_dec` was refit on the remaining 433 development bugs and
evaluated on 491 held-out bugs:

| Model | `E_dec` − confidence [95% CI] |
|---|---|
| Jev | +0.221 [0.154, 0.288] |
| OpenJev | +0.182 [0.118, 0.244] |
| Qwen2.5 | +0.270 [0.179, 0.358] |
| Phi-3.5 | +0.274 [0.175, 0.373] |
| OLMo-2 | +0.088 [−0.013, +0.183] (includes 0) |

### J4. Alternative label mappings

The mappings were: (m1) Mozilla S2 to level 1; (m2) kernel default
"normal" bugs dropped; (m3) kernel unset-regression bugs dropped.
- **Decisions beat confidence under every mapping for every model**
  (paired CI above 0).
- **The one exception is OLMo-2 under m2:** +0.020 [−0.067, +0.111].
- **The result is not fragile to these mapping choices.**

### J5. Within accepted cases: can any score find the costly errors?

AUROC for "wrongly accepted" among accepted held-out cases:

| Model | Accepts (wrong) | `E_dec` | Final-step conf. | `score` P(level 2) |
|---|---|---|---|---|
| Jev | 245 (38) | 0.461 | 0.487 | 0.491 |
| OpenJev | 198 (29) | 0.519 | 0.540 | 0.676 |
| Qwen2.5 | 71 (14) | 0.526 | 0.509 | 0.550 |
| Phi-3.5 | 59 (4) | 0.509 | 0.686 | 0.645 |
| OLMo-2 | 17 (1) | — | — | — |

- **For Jev, no score separates wrong accepts from correct ones.** This
  confirms "the value exists; the identification fails".
- **The case-level score's ingredients fall away on held-out data.**
  The full plug-in score, which combines P(level 2) and the regression
  probability, had AUROC 0.69 on development bugs for Jev. Its main
  ingredient, P(level 2), alone reaches only 0.49 on held-out bugs. That
  independently supports the stopped feasibility decision.
  - **Not computed here:** the full plug-in score on held-out bugs. That
    analysis was deliberately not run when the study stopped.
- **OpenJev** has a weak within-action signal (0.68).
- **Phi-3.5 and OLMo-2** have too few wrong accepts to interpret.

### J6. BBSE under known synthetic label shift — the paper's claim is narrowed

**Setup.** Held-out bugs were resampled to known severity mixes, and
BBSE was given the development confusion matrix.

**Result.** The estimated level-2 share is **biased toward the
development mix**:
- for Jev, bias −0.06 at a true share of 0.20, and −0.21 at 0.50;
- RMSE up to 0.24;
- similar for OpenJev (bias −0.15 at 0.20).

**Conditioning is not the issue.** The condition number stayed at 9–30
in every setting, so the bias is not ill-conditioning. It indicates that
the model's answer-given-label behaviour differs between development and
held-out bugs, which breaks BBSE's pure-label-shift assumption.

**Reading.**
- The label-free correction *did* repair the ranking (addendum I), but
  it does **not** recover the deployment label mix accurately.
- The repair should be described as **directional**, not as an accurate
  estimate of the mix.

### J7. Reviewer accuracy

With reviewer accuracy ρ, a reviewed case resolves correctly with
probability ρ. Otherwise the workflow's action stands and the human cost
is still paid. ρ = 1 reproduces the pre-registered table.

| | At the frozen costs | At 2× wrong-accept cost |
|---|---|---|
| Effect of lower accuracy | Review loses more (Jev +23 → +28 at ρ = 0.8) | Savings shrink (Jev −44 → −26; OpenJev −58 → −36) |

The sign does not change for any model in either cell.

### Human adjudication

**Not done; it requires people.**
- **Proposed:** an independent author adjudicates a random 50-bug
  held-out sample for "correct action", blind to labels and model
  outputs, and the agreement with the constructed target `a*` is
  reported.
