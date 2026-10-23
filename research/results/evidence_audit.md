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
