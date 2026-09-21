# Literature Review

## Scope

This review supports the provisional research question:

> When individually probabilistic decisions are composed into a multi-step
> software workflow, how does the reliability of the overall workflow relate
> to the calibration of individual decisions, and can a workflow-level
> uncertainty or escalation policy improve reliability at a given automation
> coverage?

It covers 9 search areas: (1) classifier/confidence calibration, (2) selective
prediction / reject-option / risk-coverage, (3) conformal prediction and
conformal risk control, (4) uncertainty propagation in multi-stage systems,
(5) cascading errors in pipelines, (6) agent workflow reliability, (7)
cost-sensitive decision-making and human-in-the-loop escalation, (8)
calibration of LLM confidence, and (9) compositional decision systems
(the crux area for novelty assessment).

## Method and limitations (read before trusting this review)

- Conducted via general web search (WebSearch) plus targeted page fetches
  (WebFetch) against arXiv, ACL Anthology, ICML/NeurIPS proceedings pages,
  and AAAI/JMLR. **No Google Scholar, Semantic Scholar, or ACL Anthology API
  access was available** — this is a stated limitation, not an oversight.
- ~30 targeted queries were run, time-boxed to one session. This is a
  reasonable first pass, not an exhaustive systematic review.
- Every entry in `literature_matrix.csv` has a `review_status` field marking
  whether the abstract was independently fetched and confirmed ("Verified via
  WebFetch of abstract") or only seen at snippet level ("Snippet-level, not
  independently fetched"). Snippet-level entries should be re-confirmed
  before being cited in any paper draft.
- Author lists for a few entries could not be confirmed from the search
  results available; these are marked "Not verified" in the `authors`
  column. Do not cite these with invented author names.
- Two areas were initially **not** searched: (a) classical systems/
  reliability engineering literature on composing component reliabilities,
  and (b) HCI/decision-support literature on human-AI escalation. **Both
  have since been searched** (a follow-up pass, ~40 more queries, abstract-
  level for new finds) — see `gap_analysis.md` §Full-text findings and the
  added rows P29–P34 in `literature_matrix.csv`. Total search effort across
  both passes: ~70 queries, still general-web-search only (no Scholar/
  Semantic Scholar/ACM/IEEE Xplore access) — reliability-engineering and
  HCI venues specifically are likely underindexed by general web search,
  so this should not be treated as exhaustive for those two areas.
- PASC (P22) and Lin et al. (P26) — the two closest papers found — have
  since been read in **full text** (not abstract-only), via WebFetch of
  their arXiv HTML versions. Findings are folded into `literature_matrix.csv`
  and `gap_analysis.md`; both are now marked `review_status: VERIFIED FULL
  TEXT` in the matrix.
- A striking number of the closest-matching papers (P22, P26, P28, and
  several others) are dated 2025–2026, i.e. very recent preprints. Several
  have unverified peer-review status. This is a fast-moving area; the gap
  analysis below should be re-run closer to submission time.

## Files

- `literature_matrix.csv` — 28 papers reviewed, one row per paper, with the
  required structured columns (problem setting, decision type, uncertainty
  type, calibration method, workflow composition, escalation/abstention,
  evaluation metrics, contribution, limitations, relevance to Jev, novelty
  implication, review status).
- `shortlist.md` — the ~10 papers most load-bearing for the gap analysis,
  with a short note on why each matters.
- `gap_analysis.md` — the required gap-analysis writeup: what's known, what's
  missing, whether the gap is genuinely open, what evidence would address it,
  at least three candidate gaps ranked by fit/feasibility, and a
  recommendation.

## Next steps for the literature review itself

- Re-run key searches (area 9 especially) with Semantic Scholar/Google
  Scholar access if/when available, to reduce reliance on general web search.
- Independently fetch and confirm the remaining "snippet-level" entries
  before they appear in any paper draft.
- Do a dedicated pass on classical reliability engineering (series/parallel
  system reliability composition) — flagged above as unsearched.
- Re-check P16 and P21 author lists before citing.
