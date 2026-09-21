**Update (post collaborator review):** the sections below reflect the
original session-1 state. A collaborator review then (1) approved Step 0A/
0B/Step 1 of the pilot but not treating a 50-instance run as scientific
evidence, (2) requested full-text reads of PASC and Lin et al. plus two new
literature-search areas, (3) requested a sharper heterogeneous-uncertainty
research question, an explicit compositional-reliability baseline, and a
go/no-go decision rule. All of that is now done — see
`research/literature/gap_analysis.md` §Full-text findings for the
sharpened, narrower gap statement, `research/methodology/
compositional_reliability_baseline.md` for the formal `Δ`/`conf_product`
statistics (now cross-validated against Lin et al.'s Proposition 2), and
`research/methodology/pilot_experiment_specification.md` for the revised
Step 0A/0B/Step 1/Step 2 structure with explicit decision gates and a
go/no-go rule. `docs.typesafe.ai/patterns` has also been checked — no
calibration or escalation guidance found there either.

**Update (Step 0A complete, live API, 2026-09-21):** built a minimal client
(`research/src/jev_client/`, `.venv` + `requirements.txt` for
reproducibility) and ran the approved 21-call coverage matrix (basic
choice/score/noul, 4 repeated-identical, edge/invalid inputs, one mixed
multi-primitive call). Full writeup: `research/results/characterization_report.md`;
raw/parsed data and run metadata in `research/data/characterization/`.
**No calibration or reliability claims were made** — this was strictly
observational, per the approved scope.

Headline results: the documented API contract, all three primitives'
output shapes, and the model-version-resolution mechanism (`jev-latest` →
`jev-1.13.0`) are all confirmed live with zero schema mismatches across 19
successful calls. Determinism was perfect on the one item tested 4x. Two
new, previously-undocumented behaviors were discovered (empty `state`
accepted rather than rejected; single-option `choice` accepted). Gate
verdicts: **A (semantic validity) PASS, D (reproducibility) PASS with
caveats, B (output comparability) open by design** (this is the research
question, not a gate to resolve here). **C (identifiability) and E
(experimental viability) are marked NEEDS INVESTIGATION / CONDITIONAL** —
hand-picked "ambiguous" `choice` inputs did not reliably elicit
intermediate confidence in this small sample (they came back ≈1.0
confidence instead), while the empty-state edge case and both `noul` items
did show genuine spread. This is an item-design finding, not a Jev
calibration finding, but it means the full ~540-call Step 0B audit should
not be launched yet.

**Update (Step 0A.1 complete, live API, 2026-09-21):** ran the approved
12-call controlled-ambiguity follow-up. Full report:
`research/results/step0a1_controlled_ambiguity_report.md`. Two headline,
previously-unknown findings: (1) intermediate `choice` confidence **is**
reachable — down to an exact 50/50 tie — but not via the manipulated
variable the pilot targeted (evidence-sentence-count ratio saturates to
confidence 1.0 at anything ≥3:1); it appeared unpredictably within the 2:2
tier instead. (2) **Sentence order alone** — same 4 sentences, same
content, positions swapped within pairs — swung confidence from 0.82 to
0.01, the single largest effect in the whole matrix, and was not something
this pilot set out to test. A third finding: repeated identical calls are
bit-identical when confidence is saturated but show real numerical jitter
(~±0.03-0.04) when confidence is intermediate — determinism is not uniform
across Jev's output range.

Applying the agreed 5-criterion gate honestly: 3 clear passes, 1 partial
(reproducible in direction, not magnitude), 1 fail-as-originally-specified
(the manipulated variable doesn't explain the within-tier variation — order
and content do, and weren't controlled for). Net verdict: not a failed
pilot — intermediate confidence is confirmed reachable and the actual
controlling factors are now identified, but Step 0B's design needs three
concrete changes before it can run (see
`research/methodology/pilot_experiment_specification.md` §Step 0B, updated
accordingly): matched-evidence-pool item construction (also still needed
for `score`, not yet built), explicit order-randomization for near-balanced
items, and a repeat-sampling budget for intermediate-confidence items
(raises the ~540-call estimate, not yet recomputed).

**Update (Step 0A.2 complete, live API, 2026-09-21):** ran the two
requested follow-ups (26 calls total). Full report:
`research/results/step0a2_order_and_score_report.md`. (A) A proper
6-permutation × 3-repeat factorial on one fixed `choice` evidence set
confirms the order effect is real and decomposes it from repeat noise:
permutation variability (`R_perm`=0.417) is an order of magnitude larger
than repeat variability (mean range 0.058) — but at the 2 permutations
whose mean sat near the 50/50 boundary, that same repeat noise **flipped
the selected label** across identical repeated calls, not just the
confidence number. The mechanism behind the order effect itself remains
unidentified (position/adjacency/content-pairing are confounded in this
design) and content variability (a second evidence pool) was deliberately
not tested, both flagged as open rather than resolved. (B) The
matched-evidence-pool method now also works for `score` — resolving Step
0A.1's inconclusive result — and surfaced a secondary, single-item
observation that `score` may track the worst symptom rather than average
conflicting severity evidence (flagged, not claimed).

**Update (Step 0B Design Specification written, 2026-09-21 — not
executed):** per collaborator review, wrote the required 14-section design
spec: `research/methodology/step0b_design_specification.md`. Covers
research questions/pre-registered hypotheses (H1-H5), unit of analysis, a
generalized evidence-pool construction procedure (≥2 independent domains
per primitive, including a new matched-pool method for `noul`, which had
never been deliberately tested this way), a ground-truth protocol that
explicitly excludes deliberately-contested/balanced items from accuracy
metrics, a deterministic (lexicographic) canonical presentation policy, a
three-layer sampling design (primary / presentation-robustness /
repeatability, with the latter two combined onto one preregistered ~20%
subset for budget efficiency), exact estimands (decision quality; `S`/`I`
repeat-instability; `D`(x) + range/max-diff presentation-sensitivity;
escalation-metric definitions reserved for Phase 9), missing-data
handling, a proposed ≈190-call budget with reserve, exclusion/stopping
rules (fixed design, no adaptive stopping, explicit pause triggers), a
figure/table plan, and limitations (no formal power analysis yet;
content-variability still only partially addressed; order-effect mechanism
still unidentified by design, deferred to a separate later study).

Also corrected two imprecisions in the Step 0A.2 report per review: "order
of magnitude" restated as the precise ratio (≈7.2×), and `R_perm`
relabeled as a descriptive "observed permutation range," not a formal
effect-size/variance-decomposition estimate.

**Update (Step 0B Design Specification, Revision 2, 2026-09-21 — not
executed):** a rigorous section-by-section review of Revision 1 found 7
critical issues; all are addressed in Revision 2
(`research/methodology/step0b_design_specification.md`), which also
surfaces **one new critical issue found while fixing the review's #1 and
#3**: the original ground-truth rule and the ratio known to produce
non-saturated confidence were mutually exclusive — every item with a
valid reference label would have been expected to saturate to
confidence≈1.0, making H1 nearly untestable by construction. Revision 2
fixes this with a new "near-majority" condition (5-sentence 3:2 items for
`choice`/`noul`; 2:1 adjacent-level items for `score`) whose ability to
produce non-saturated confidence *while keeping valid ground truth* is
itself now a Stage 0 validation question, not assumed. A second bug was
also caught and fixed: the original canonical-ordering rule (sort by
sentence key) used semantically-prefixed keys (`N1`/`D1`), which would
have systematically confounded "canonical order" with content category —
fixed with content-blind opaque sentence IDs.

Revision 2 restructures execution into three stages: **Stage 0** (≈26-28
calls, its own pass/fail gates, validates `noul`'s never-before-tested
matched-pool method via a gated H2a/H2b split, and validates the new
near-majority ratio for `choice`/`score` — kept entirely out of the
confirmatory sample), **Stage 1** (162 calls core, provisional on Stage 0's
outcome), and a narrowly-scoped **operational reserve** (~24 calls,
technical-failure replacement only, fixed preregistered rules, explicitly
prohibited from being used to adjust content or hypotheses). Grand total
if Stage 0 passes cleanly: ≈212 calls. Also added: primitive-specific
correctness/calibration targets (choice/score/noul are no longer treated
as interchangeable), a prespecified output-independent boundary formula
and descriptive-only analysis plan for H4, complete-cell rules so
instability statistics computed on fewer than the planned repeats/
presentations are never pooled with complete ones, H5 downgraded to
explicitly exploratory, "construction-defined reference label"
terminology, a hedged reporting template that avoids "Jev is calibrated"-
style conclusions, and cross-primitive reporting split so no combined
"reliability score" masks the primitives' representational differences.

**Update (Revision 3, 2026-09-21 — not executed):** addressed a further
review of Revision 2 (which noted — correctly, per a stale paste on the
reviewer's side, since confirmed the live file already had it — that
Stage 0 gates, near-majority conditions, and the H2a/H2b split needed to
be verifiably present). Revision 3 adds: an explicit 3-way scope limit for
Stage 0 (construction feasibility / output feasibility / hypothesis
evidence — Stage 0 only checks the first two, with a hard prohibition on
silently modifying Stage 1 after seeing outputs); Stage 0's pass/fail
criteria rewritten from a fixed confidence threshold to a pure
responsiveness check (does output vary at all across conditions), so
Stage 0 cannot be read as "forcing the API to confirm the hypothesis";
explicit non-comparability of the `choice`/`noul` (3:2) vs `score` (2:1)
near-majority conditions; small-sample interpretation language rules
(non-significant ≠ evidence of no relationship; n≈30 positive correlation
≠ a calibration claim); a standalone "no retroactive ground truth from
observed decisions" rule; an item-type × analysis-type eligibility table;
and new §15, a pre-flight static validation checklist.

**§15 is backed by a real, runnable validator** —
`research/src/validate_step0b_manifest.py` — implementing all 11 checks
against a machine-readable item manifest (checks 1-8) and, once an
analysis script exists, against that code (checks 9-11, currently N/A
since that script isn't written yet). Self-tested against a dummy manifest
(both a clean case, all manifest-level checks pass, and a deliberately
broken case with a duplicate opaque ID, which correctly fails) — this
is real, tested code, not just a described checklist. **It has not yet
been run against an actual Step 0B item manifest, because that manifest
does not exist yet** — generating the real Stage 0/Stage 1 manifests
(sentence pools, opaque IDs, reference labels, per the §3 allocation
table) is the next concrete step, separate from this design review.

**Update (Stage 0 EXECUTED, live API, 2026-09-21):** generated the real
Stage 0 manifest (`research/src/build_stage0_manifest.py`, no network
calls), ran the validator against it — first pass genuinely **failed**
(#1 unique-opaque-IDs) because the manifest reused identical sentences
across items to save writing effort; fixed by rewriting every item with
fully independent sentences (43 unique, zero reuse), not by relaxing the
check — then re-validated clean (all applicable checks PASS, artifact
saved: `research/results/stage0_manifest_validation.txt`) before making
any API call, per the required order of operations. Executed all 26
calls via `research/src/run_stage0.py` (`JevClient`-only, satisfying
validator check #9): **26/26 succeeded, zero failures, zero schema
mismatches.**

Full report: `research/results/stage0_report.md`. Headline results:
**`noul` H2a passes cleanly** (value moves monotonically with evidence
ratio: 0.97→0.88→0.74→0.40 across 5:0/4:1/3:2/2:2; repeat range ≤0.02) —
`noul` is authorized for Stage 1. **`choice`'s near-majority (3:2, 5
sentences) condition passes output feasibility strongly** — `g(x)` ranges
0.98→0.79→0.14 across 3 items, real graded variation (unlike the
4-sentence 3:1 ratio, which Step 0A.1 found always saturates) — `choice`
is authorized for Stage 1. **`score`'s near-majority (2:1 adjacent-level)
condition is flagged, not authorized:** all 3 independently constructed
items showed Jev's output concentrating on the single higher-severity
sentence's level, directly contradicting the majority-sentence-count
reference label, every time — a systematic disagreement, not noise. This
echoes Step 0A.2's exploratory H5 observation now recurring across 3 items
instead of 1, but per Stage 0's non-evidence rule this is reported as a
**construction-feasibility concern about the reference-label rule**, not
as H5 evidence, and `score`'s Stage 1 design is held pending a review
decision among three disclosed, not-yet-chosen options (reweight the
rule / treat these as contested / a separate small follow-up).

**Update (Stage 0 report revised; Stage 1 manifest generated for `choice`/
`noul`, 2026-09-22 — no new API calls):** applied both requested wording
corrections to `stage0_report.md` (H2a's pass no longer implies calibration
is established; the repeat-jitter comparison to `choice` is now explicit
descriptive context, not a formal cross-primitive comparison), added the
explicit narrow-pass-vs-substantive-feasibility sentence for `score`,
softened the flagged-concern heading, and replaced the open-ended options
list with the chosen path: **modified Option 3** (freeze this result;
mark mixed-severity `score` items contested-pending-review; define the
semantic target independently of Jev's output; run a separately-authorized
semantic-validation follow-up; submit a revised `score` Stage 1 spec for
its own approval).

Built and validated the real Stage 1 manifest for `choice`+`noul`
(`research/src/build_stage1_manifest.py` → 60 primary items across 2
independent domains per primitive, 30/primitive, per §3's allocation
table, plus 4 preregistered overflow spares and a 12-item seeded
robustness+repeat subset — `score` excluded entirely, per the block
above). All 308 sentences are template-generated with jittered numeric
slots specifically to guarantee manifest-wide uniqueness (the exhaustion
of a first, too-small template pool was caught and fixed before any
validation run, the same discipline Stage 0 established). **Validated
clean**: `research/results/stage1_choice_noul_manifest_validation.txt` —
all 8 applicable checks pass (checks 9-11 correctly N/A, no Stage 1
analysis code exists yet).

**Update (Stage 1 preflight checklist complete, 2026-09-22 — still zero
API calls):** closed out all 8 items from the pre-execution checklist —
`research/results/stage1_preflight_checklist.md`. Item accounting
resolved explicitly (60 primary = 30 `choice` + 30 `noul`, plus 4
preregistered reserve items = 64 manifest entries; reserve confirmed
excluded from the core call plan by a zero-API-call dry run of
`build_plan()`). Wrote and validated the actual Stage 1 runner
(`run_stage1.py`, `JevClient`-only) and analysis code
(`analyze_stage1.py`, with the H2a gate and complete-cell filtering
**enforced in code and proven by a passing self-test**, not just
documented). Wrote `stage0_gate_outcomes.json` as the machine-readable
persistence of Stage 0's gate table, which `analyze_stage1.py` now reads
and refuses to proceed past for any `noul` metric unless it says "pass".
Built `verify_stage1_rederivation.py`, which re-runs manifest
construction from scratch and confirms the **entire** manifest (not just
the subset) re-derives byte-identical from its two recorded seeds — a
strictly stronger check than the one requested.

Along the way, updating the manifest to freeze `alternate_orders` (so
presentation order is never generated at runtime, closing a design gap
review flagged only implicitly) legitimately changed its content hash;
this was deliberately re-baselined with a disclosed changelog note in
`stage0_manifest_hashes.json`, not silently overwritten. **Full 11-check
validator audit now passes with zero N/A results** — checks 9-11 are
genuinely exercised against real runner/analysis code, not placeholders.

**Update (Stage 1 EXECUTED + audited, live API, 2026-09-21/22):** ran the
frozen 108-call plan (`run_stage1.py`) — **108/108 succeeded**, zero
retries, zero parse failures, single model version throughout, manifest
hash matched the frozen baseline exactly, zero reserve items used.

Ran the requested 8-point descriptive/protocol audit
(`research/src/stage1_audit.py` → `research/results/stage1_execution_audit.md`).
**Found and fixed a real bug in the analysis code itself**, not the data:
`analyze_stage1.py`'s repeat-instability/presentation-sensitivity
functions were scoping to "any item with a qualifying record" instead of
the manifest's actual 12-item Layer 2/3 subset, so they wrongly flagged
48 items as "incomplete" (those items were only ever designed to get 1
canonical call — not missing data, out of scope by design). Fixed by
passing the subset explicitly; re-confirmed 12/12 complete, 0 incomplete,
in both layers. This is precisely the "does the executed dataset show the
safeguards were applied correctly" gap the preflight self-tests (built on
synthetic fixtures) couldn't have caught on their own.

Headline descriptive numbers (reported per the audit's own rule: **not**
an H1/H2b interpretation, that's a separate later step): `choice`
non-contested accuracy 18/24 (75%), Brier 0.229; `noul` non-contested
accuracy 24/24 (100%), Brier 0.028; `choice` saturation rate 70%, `noul`
saturation rate 20% (using confidence-like ≥0.9). Zero deviations from
the preregistered plan.

**Update (audit corrected + annotated per review, 2026-09-22 — no new API
calls):** preserved the superseded (buggy) audit output as its own
labeled artifact (`stage1_execution_audit_SUPERSEDED.md`, sections 4/8
only, the affected ones) rather than silently discarding it, with the
precise wording distinction review required: zero execution deviations
vs. one post-execution analysis implementation defect (found and fixed).
Added, before any number is reported: the exact per-primitive Brier-score
probability mapping (`choice` uses `probabilities[reference_label]`,
single-term "probability of the reference class" form; `noul` uses the
raw native value, standard binary Brier — explicitly documented as
different conventions, not a shared formula) and an explicit reliability-
bin endpoint convention (last bin closed at 1.00). Added an explicit
`D(x)` direction statement (`D=1/3` = stable/one decision across three
presentations, not "33% stable"). The corrected `stage1_execution_audit.md`
is now the authoritative report.

**Update (formal H1/H2b write-up complete, 2026-09-22 — no new API
calls):** fixed the Brier terminology issue first — added a unified,
explicitly-defined cross-primitive metric (standard 2-term binary Brier,
`2·(1-p_ref)²`, same formula for both primitives) rather than comparing
`choice`'s one-term value to `noul`'s native value; both originals are
preserved as labeled audit artifacts, not deleted. Then ran the full
7-step authorized analysis
(`research/src/stage1_h1h2b_analysis.py` → `research/results/stage1_h1h2b_analysis.md`):
frozen-input hashes recorded; Spearman rank correlation (`choice` ρ=0.25;
`noul` correctly reported as "not computed" — zero outcome variance at
n=24, not ρ=0); two reliability binning schemes with bin counts and ECE
for both; Wilson confidence intervals on accuracy (`choice` 18/24 [0.55,
0.88]; `noul` 24/24 [0.86, 1.00]); repeat/presentation subset summary
scoped to its 12 items only; and the full hedged reporting template
(descriptive observation / statistical association / uncertainty /
hypothesis stance) applied to both primitives.

**One genuinely interesting finding surfaced by the equal-mass binning
specifically:** `choice`'s second rank-quartile (mean confidence 0.92)
had only 33% observed accuracy — a real overconfidence signal that the
equal-width table's coarser bins partially masked. Reported as an
observation, not a calibration verdict, per the hedging rule.

**Update (5 wording/substance corrections applied per review, 2026-09-22
— no new API calls):** (1) unified Brier now explicitly labeled "metric
comparability ≠ experimental comparability," with the 5 specific reasons
listed; (2) `choice`'s overconfidence subgroup finding softened from
"not an artifact of binning" to "reflected under both tested partitions
on this sample, does not establish general binning-independence" —
plus a new Step 8 supplementary item-level audit CSV (all 48 non-
contested items, `stage1_h1h2b_item_level_audit.csv`) so the 6
underlying items are independently checkable; (3) **`noul`'s "consistent
with calibration" language removed entirely** — corrected to state
plainly that 100%-accuracy-in-every-bin does not imply calibration when
ECE is nonzero (0.2542), and that the pattern is *underconfidence*
relative to observed accuracy, not evidence of calibration; (4)
`choice`'s hypothesis stance now integrates the overconfidence subgroup
into the same conclusion rather than treating it as a footnote; (5) a
terminology sweep distinguishing accuracy/rank-association/calibration
as three different properties throughout, plus the exact stated cause
for `noul`'s undefined Spearman correlation (constant y=1, not generic
"insufficient data").

**Per the agreed protocol, this is now a completed, precisely-worded,
non-causal statistical write-up** — not a claim that `choice` or `noul`
is "calibrated," and not a controlled comparison between the two
primitives (different item sets/domains). `score` remains fully blocked.

**Update (analysis freeze record + closing sections, 2026-09-22 — no new
API calls):** wrote
`research/data/characterization/analysis_freeze_manifest.json` — locks
the raw-response, manifest, Stage 0 gate, analysis-script, and item-
level-audit-CSV hashes (all 5 requested fields, plus runtime version and
timestamp) with an explicit change-discipline rule distinguishing
editorial from numerical/logic changes; no git commit exists to bind
these to a source snapshot, noted explicitly rather than glossed over.
Added the reviewer-drafted overall conclusion paragraph verbatim to
`stage1_h1h2b_analysis.md`, plus a scoped "research implication" closing
section that names the motivating questions (high confidence with
observed error patterns; high accuracy with underconfident scores;
differing native uncertainty semantics; untested presentation/instability
conditions) while explicitly stating this experiment does not establish
and is not presented as establishing a workflow-level escalation policy —
preserving the primitive-characterization/workflow-policy separation
review asked to keep intact.

**This closes out the `choice`/`noul` Stage 1 formal analysis.** `score`
remains independently blocked, not folded into any of these conclusions.
Next open items, per the accumulated record: (a) the `score` semantic-
validation follow-up sequence (`stage0_report.md`'s flagged concern,
still unresolved), and (b) any future workflow-policy experiment, which
per this section should be separately specified and reviewed, not
derived directly from these aggregate results.

# Research plan — session 1 (Phase 0 + Phase 1)

Research theme: *From Calibrated Decisions to Reliable Workflows: Evaluating
Compositional Uncertainty in Structured AI Decision Models*, using
TypeSafe's Jev API.

## 1. Repository status report (Phase 0)

- Directory was empty except a `.env` file containing one variable,
  `JEV_API_KEY` (value not read or printed by this session — only the
  variable name was checked). Not exported into the shell environment.
- No git repository existed — **now initialized** (`git init`), with a
  `.gitignore` added that excludes `.env` and standard Python/Node/OS
  artifacts. Nothing has been committed yet.
- Python 3.14.5, pip 26.1.1, Node v26.0.0, npm 11.12.1 available.
- No existing virtualenv, `pyproject.toml`, or Jev client code/docs found
  anywhere in the directory.
- Created so far (documents and structure only — **no dependencies
  installed, no code written, no API calls made**):
  - `research/literature/` — `README.md`, `literature_matrix.csv` (28
    papers), `shortlist.md`, `gap_analysis.md`
  - `research/jev_api_notes.md` — grounding notes from TypeSafe's public
    docs (blog + `docs.typesafe.ai`), not from the live API
  - `research/methodology/pilot_experiment_specification.md` — concrete,
    small-scale pilot spec, gated on your approval
  - This file

## 2. Literature review plan and findings (Phase 1)

Full detail in `research/literature/`. Summary: a one-session, ~30-query
general-web-search literature pass (no Scholar/Semantic Scholar API access —
stated as a limitation, not hidden) across 9 areas found:

- Mature, separate literatures for (a) individual-decision calibration, (b)
  selective prediction/risk-coverage, (c) conformal prediction/risk control,
  and (d) calibration-driven escalation for a *single* decision or a
  *cascade of the same decision* repeated across model tiers.
- Very recent (2025–2026) work specifically on LLM-agent trajectories
  showing **step-level calibration does not imply trajectory-level
  calibration** (closest: Lin et al., arXiv:2609.07395), and a formal
  result that independently-calibrated per-stage conformal coverage
  compounds multiplicatively across stages in NLP/LLM pipelines (closest:
  Kotte, "PASC," arXiv:2605.18812 — single-author preprint, peer-review
  status unverified, treat cautiously).
- **No paper found combines** (a) a heterogeneous multi-step workflow (mixed
  decision types, not a repeated cascade or homogeneous agent trajectory),
  (b) a general account of how per-decision calibration relates to composed
  workflow reliability, and (c) a workflow-level escalation policy evaluated
  against an automation-coverage axis. Full reasoning and caveats in
  `research/literature/gap_analysis.md`.

**Read `research/literature/README.md` for what was and wasn't searched
before trusting the novelty claim above** — two areas (classical
reliability-engineering composition math, and HCI escalation literature)
were not searched and could plausibly surface adjacent work.

## 3. Candidate gaps and recommendation (Phase 1)

Three candidates were developed and ranked in
`research/literature/gap_analysis.md`:

1. **Calibration-to-reliability composition + escalation policy in
   heterogeneous multi-step workflows** (generalized version of the
   original research question). Highest novelty per this search, highest
   effort/risk.
2. **Empirical audit of whether Jev's `confidence` field is itself
   calibrated**, motivated by a genuine, quotable tension: TypeSafe's blog
   claims "Calibrated: higher confidence means higher accuracy," while the
   technical docs (`docs.typesafe.ai/confidence`) describe `confidence` only
   as a distribution-concentration statistic with no accuracy guarantee
   stated. Highest feasibility, lowest standalone novelty (well-trodden
   method, just not yet applied to Jev).
3. **Workflow-level escalation under structurally heterogeneous uncertainty
   representations** — motivated by a real, documented fact about Jev: the
   `noul` primitive returns a single continuous probability with **no
   separate `confidence` field** (by design — a two-outcome distribution
   needs only one number), while `choice`/`score` expose a full distribution
   *plus* a separate derived `confidence` scalar. No reviewed paper
   addresses combining structurally different uncertainty representations
   within one workflow.

**Recommendation:** run Candidate 2 first as mandatory Phase 2 groundwork
(it gates interpretation of everything else), then pursue a scoped merge of
Candidates 1 and 3 as the main paper direction — studying the
composition/escalation question specifically on a heterogeneous workflow
that includes a real `noul` node, rather than a hypothetical heterogeneity.
Full justification and the conditions under which this recommendation should
be revisited (e.g., if `noul` turns out to behave like a thresholded
`choice`/`score` output once characterized empirically) are in
`gap_analysis.md`'s final two sections.

## 4. Concrete experiment specification (Phase 1 deliverable, pre-approval)

`research/methodology/pilot_experiment_specification.md` specifies a small,
two-step pilot:

- **Step 0:** individual-decision calibration audit across all three
  primitives (~540 API calls) — addresses Candidate 2.
- **Step 1:** a minimal 3-stage heterogeneous chain workflow (choice →
  noul → score) over 50 synthetic instances, with ground truth known by
  construction, comparing "no escalation" vs. a naive fixed-threshold
  escalation baseline — a plumbing/validation pass for Candidates 1+3, not
  a result to interpret substantively.

Explicitly out of scope for the pilot: non-Jev baselines, distribution
shift, branching topologies, any non-trivial escalation policy, and
statistical significance testing — all deferred to the main experiment.

## 5. Assumptions that still need validation

- That the blog's "calibrated" claim and the docs' concentration-statistic
  definition of `confidence` are genuinely in tension rather than
  reconcilable — needs the empirical Step 0 audit, and a check of
  `docs.typesafe.ai/patterns` (not yet fetched).
- That `noul`'s lack of a separate `confidence` field actually creates a
  meaningful policy-design problem, versus being trivially resolved by a
  simple transform like `2*|noul - 0.5|` — this is exactly what Candidate
  3 needs to test, not assume.
- That documentation matches live API behavior — nothing above has been
  confirmed against an actual API response (see `research/jev_api_notes.md`
  "still unchecked" section: error format, rate limits, model-version
  pinning behavior, whether `probabilities` can ever be sparse or null).
- That a synthetic-benchmark-first approach (Step 1) will generalize enough
  to support paper-level claims — the plan already requires at least one
  realistic/externally-validated task before the final paper (per the
  original Phase 3 instructions); which task that should be is not yet
  decided.
- That the literature search was thorough enough — two areas (classical
  reliability engineering, HCI escalation literature) were not searched.
- Several literature entries are marked "snippet-level, not independently
  fetched" or have unverified author lists in
  `research/literature/literature_matrix.csv` — these need confirmation
  before appearing in any paper draft.
- P22 (PASC) in particular should get a full-text read (not just abstract)
  before finalizing scope, since it's the closest single paper to
  Candidate 1's mathematical core and its peer-review status is unverified.

## 6. Prioritized next-step checklist

1. **You review and approve (or redirect) the recommended direction** in
   `research/literature/gap_analysis.md` §Recommendation, and the pilot
   spec in `research/methodology/pilot_experiment_specification.md`, before
   any code is written or the Jev API is called.
2. Fetch and check `docs.typesafe.ai/patterns` (cheap, no API key needed) to
   close the "still unchecked" gap on the calibration-claim tension.
3. Full-text read of P22/PASC (arXiv:2605.18812) to confirm it doesn't
   already answer Candidate 1, and to check its peer-review status.
4. Re-run or extend the literature search for areas 3–6 and 9 with
   Scholar/Semantic Scholar access if/when available; do the unsearched
   classical-reliability-engineering pass.
5. Once approved: scaffold `pyproject.toml` + `src/` layout, build the Jev
   API adapter (`src/jev_research/models/jev_client.py` etc. per the
   original spec), and run Step 0 of the pilot (individual-decision
   calibration audit) before touching Step 1.
6. Only after Step 0 passes its validation criteria: run Step 1 (3-stage
   pilot workflow), write the pilot report, and only then decide on the main
   experiment design (Phase 8) and the specific escalation-policy
   intervention (Phase 9).
7. Make an initial git commit once you're satisfied with this plan (nothing
   has been committed yet — you may want to review file contents first).

**Nothing beyond what's listed above has been done.** No packages are
installed, no `pyproject.toml` exists yet, and the Jev API has not been
called. Awaiting your review before proceeding to implementation.
