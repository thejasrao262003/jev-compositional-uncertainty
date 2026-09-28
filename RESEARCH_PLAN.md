> **Current status (2026-09-28):** the `choice`/`noul` characterization
> and both `score` studies are complete. The first workflow calibration
> pilot has run (270 calls). The Step 2 protocol is at Revision 10, with
> one primary comparison (2 vs 4a) and a provisional N. The template
> grammar is drafted, with one open decision. No Step 2 evaluation call
> has been made. The updates below run **oldest first**; the latest is
> "Where things stand (2026-09-28)", just before the session-1 plan.
> For a short overview, see `README.md`.

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

**Update (repository committed, 2 commits, 2026-09-22):** `f480613`
(62-file freeze of Stage 0/Stage 1 work) and `c8b6197` (provenance
correction to `analysis_freeze_manifest.json` — fixed the self-
referential-hash problem by renaming the field to `preceding_commit` with
an explicit note explaining why a file can't contain the hash of the
commit that carries its own current bytes; artifact hashes unchanged,
confirmed via `git diff --stat` before committing).

**Update (`score` semantic-validation specification written, 2026-09-22
— design only, not executed):**
`research/methodology/score_semantic_validation_specification.md`.
Recovers the documented `score` contract and isolates exactly what's
undocumented (how evidence aggregates into a probability distribution —
not the distribution-to-scalar formula, which was already confirmed).
Defines three candidate target semantics computable independently of any
Jev output (majority-count, highest-severity, severity-weighted-average;
a fourth, risk-sensitive, is explicitly deferred to the future workflow-
policy stage since it needs an externally supplied loss function this
study has no principled way to invent). Designs 10 three-sentence
compositions (3 unanimous-control anchors + 7 discriminative, chosen so
the three candidates predict different levels — including the exact
2:1 composition Stage 0 already tested once) and a pre-registered,
threshold-based gate (≥5/7 discriminative-item matches = semantic
clarity; otherwise ambiguity or failure) that is fixed *before* any data
exists, explicitly binding against picking whichever interpretation
happens to fit the data. Small budget (30 calls, feasibility-scale, no
robustness/repeat layer — that question is already answered in general
from Step 0A.2). All three gate outcomes (clarity/ambiguity/failure) are
mapped to what each would authorize next, none presumed.

**No API calls made.** This is a design document only, submitted for
review before any manifest is built or call is made.

**Update (Revision 2, 2026-09-22 — still no API calls):** fixed 3 major
protocol issues and 4 smaller ones. The gate denominators were
inconsistent (M's undefined cell on `(0,1,2)` meant M had 6 scorable
items while X/A had 7, under one shared "5 of 7" label) — fixed by
moving `(0,1,2)` entirely out of the primary gate onto a fixed 6-item set
where all three candidates are defined, reported only as a supplementary
X-vs-A comparison. The three gate outcomes (clarity/ambiguity/failure)
were not mutually exclusive as originally worded — a low-match-everywhere
case satisfied both "ambiguity" and "failure" simultaneously — fixed with
an explicit **ordered** decision procedure (clarity checked first, then
failure, everything else falls to ambiguity by construction; verified
exhaustive/mutually-exclusive by enumeration). The 5/7 threshold's status
was underspecified — now stated explicitly as a feasibility-stage design
heuristic, not statistical/inferential proof, with the candidates'
structural overlap (M=X on several compositions, etc.) named directly.
Also added: explicit repeat-aggregation and tie-handling rules (modal
decision across 3 repeats, a genuine "no consistent decision" category
that is never forced into a fake mode, full repeat-level data retained
regardless of the reduction); a hard separation between categorical
matching (argmax vs. M/X/A) and scalar proximity (`score` vs. unrounded
A) into two explicitly distinct analyses; and softened language on both
the single-domain scope and the presentation-order exclusion, framing
both as disclosed restrictions rather than implied generality claims.

Submitted for review before any manifest is built.

**Update (Revision 7, 2026-09-22 — still no API calls, moving from
implementation-audit to semantic-validation review):** froze the entire
verifier audit —
`research/data/characterization/score_verifier_freeze_manifest.json`
(exact script/spec hashes, full boundary matrix, every mutation operator
and result, independent fixture definitions, the `[1,9,9]→[1,9,1,9]`
test-construction history, documented limitations) — no semantic changes
follow this freeze; anything found later is a new, separately-tracked
issue. Added a **dedicated semantic fixture audit**
(`research/results/score_semantic_fixture_audit.md`), distinct from the
gate implementation audit: walks all 6 primary compositions individually
through an 8-point checklist (multiset size, M/X/A definedness and
derivation, no `M=X=A`, claimed class correctness, supplementary
exclusion) — all 6 independently verified.

Restructured spec §8 around the explicit **three-tier hierarchy**
(verifier validity: addressed; semantic validity: open; research
validity: open) rather than a binary split. Split the mutation-testing
claim that was at risk of being collapsed: the shipped-threshold finding
(branch mathematically redundant) and the hypothetical-threshold finding
(branch matters, but that configuration is explicitly labeled *outside
the declared admissible space*, a robustness probe only) are now two
separate, clearly-scoped claims. Stated explicitly that `[0,0,0,9]`
proves the implementation distinguishes mode/max/mean from each
other and nothing about which one `score` actually uses.

**Per review: implementation audit is done. Semantic validity and
research adequacy are both still fully open — that is the explicit
handoff point to the next phase, not a gap to paper over.**

**Update (semantic-validation handoff, 2026-09-22 — still no API calls):**
wrote `research/methodology/score_semantic_identification_protocol.md`,
sitting one level above the gate spec — references rather than duplicates
existing content (contract inventory, candidate definitions already
covered; nothing restated in different words for its own sake).

**Its actual new contribution**: workstream 3 ("identifiability
analysis") computes something never previously checked —
`research/src/verify_score_identifiability.py` finds that the 6 primary
items' pairwise discriminating power is **asymmetric**: X-vs-A is
separated on all 6 items, M-vs-X on 5 of 6, but **M-vs-A on only 3 of
6** (`(0,0,0,1)`, `(0,1,1,2)`, `(1,1,1,2)` all happen to have
`A_rounded == M`, silently uninformative for that specific comparison
despite being labeled "discriminative" overall). Consequence: a future
CLARITY outcome driven mainly by M-vs-A disagreement would rest on half
the evidence base a X-vs-A-driven outcome would. This is now a required
disclosure in workstream 5's extended decision rules, and a new stopping
condition ("evidence insufficient for Stage 1") triggers if CLARITY is
reached only via the low-coverage pair.

Also formalized as explicit binding rules (both already true in the
existing implementation, now named rather than merely implicit): (1)
agreement with Jev's output is never proof of intended semantics,
regardless of how many items agree; (2) an item non-discriminating for a
*specific pair* must never be counted as evidence for that pair, even
when it remains valid evidence for the pairs it does separate.

**One open question submitted to review, not resolved unilaterally**:
whether to proceed with the current 6-item design (disclosing the M-vs-A
limitation) or add supplementary items to close that specific gap before
any further work.

**Update (Supplement v1 designed, 2026-09-22 — still no API calls, frozen
6 unmodified):** per review's decision to augment rather than modify,
built `research/src/design_score_mvsa_supplement.py` — searched a
genuinely new composition space (n=5 sentences; every one of the 15
possible n=4/3-level multisets was already exhausted across the existing
categories, so no new n=4 pattern was available) under 7 pre-registered
criteria (M defined+unique, A defined under the unchanged rounding rule,
`M≠A`, discrimination class recorded, relationship-to-X recorded,
selection by exhaustive search + a deterministic diversity rule with zero
dependence on any Jev output, combined coverage reported before any
semantic evaluation). Found 4 qualifying compositions, selected 3 (2
THREE_WAY + 1 TWO_WAY, per the diversity rule) — `(0,0,0,1,2)`,
`(0,0,0,2,2)`, `(0,0,2,2,2)`.

**Result, script-verified**: combined with the frozen 6, M-vs-A coverage
rises from 3/6 to 6/9 — and applying the *same* `≥6` threshold
symmetrically (per review's explicit request, not just to M-vs-A) shows
**all three pairs now clear it**: M-X 7/9, M-A 6/9, X-A 9/9. Full record:
`score_mvsa_supplement_v1.json`.

Generalized the stopping rule in the identification protocol to be
symmetric across all three pairs (formalized as `n_P` = pair-specific
separating-item count, with an explicit rule that only those items may
ever count as evidence for that pair), and added the explicit
frozen-vs-newly-open list review requested. **Nothing here builds actual
manifest items, estimates a budget, or authorizes any API call** — that
remains the next, separate step if this design is approved.

**Update (supplement manifest spec + sentence-count confound named,
2026-09-22 — still no API calls):** wrote
`research/methodology/score_mvsa_supplement_manifest_spec.md`, the
requested next artifact, containing all 10 required elements. Two
substantive additions beyond restating prior results: (1) a **selection-
rule robustness check** — ran the alternative allocation (1 THREE_WAY + 2
TWO_WAY instead of 2+1) and confirmed it *also* independently clears the
≥6 threshold on all 3 pairs (M-X 6/9, M-A 6/9, X-A 9/9), which is direct
evidence the 2:1 ratio wasn't reverse-engineered to hit the target — a
different reasonable rule gets there too. (2) **The n=4-vs-n=5
sentence-count confound review flagged is now named as its own tracked
limitation**, not folded into the composition-level math: the frozen 6
use 4 sentences, the supplement uses 5 (because the n=4 space is fully
exhausted — no larger n=4 M-vs-A set exists to build instead), and no
n=5 control exists yet to isolate whether input length itself changes
Jev's behavior independent of severity content. Documented as a binding
rule for any future write-up: composition-level separation (verified),
input-length effects (untested), and actual semantic evidence
(uncollected) must never be blended into one conclusion.

Also recorded, per the design script's output: the full 4-candidate table
(not just the 3 selected), the excluded candidate (`(0,1,2,2,2)`) with
its purely mechanical exclusion reason, and an explicit decision-gate
restatement that none of this advances semantic or research validity —
only design-level coverage.

**Update (bounded semantic-validation protocol, 2026-09-22 — Phase A
complete, Phase B defined but NOT executed):** wrote
`research/methodology/score_bounded_semantic_validation_protocol.md`.
**The most important addition**: M, X, and A are all defined purely from
the *multiset* of severity levels — every one is order-invariant by
construction. Step 0A.2 already found real, replicated order-sensitivity
for `choice` (confidence 0.82→0.01 from a two-sentence swap) *and* a
smaller but real order effect on `score` itself (the same 1+2 boundary
composition, order-reversed, moved confidence 0.73→0.86 and level-2 mass
0.18→0.09). This means order-dependence isn't a generic hypothetical
alternative semantic family to list alongside the others — it's already
evidenced, and it's a structural blind spot no candidate in `{M,X,A}` can
ever cover. Built this into a formal candidate-set adequacy gate: any
Phase B result must be reported as "discrimination among M/X/A under
canonical presentation," never as "`score`'s semantics identified,"
until order-dependence (and four other unexcluded families: weighted
statistics, transformations, probability-derived statistics, nonlinear/
concentration effects) are separately addressed.

Also resolved, as an explicit design decision open to override: rather
than invent and re-verify new 3-way gate thresholds for 9 items, the
already-audited N=6 gate runs unchanged on the frozen 6 only; the
supplement's 3 items feed exclusively into pair-specific `n_P`
accounting. Phase B is fully specified (9 items, canonical-only, 3
repeats/item, 27 calls) but **not executed** — Phase C's review criteria
(stability check, frozen-6 gate outcome, pair-specific cross-check,
candidate-adequacy re-application, "underidentified" as an acceptable
outcome, no automatic Stage 1 expansion) are defined for data that
doesn't exist yet. All 6 of review's binding conditions are satisfied by
the design; none of them authorizes running it.

**Update (artifact-level preflight, 2026-09-22 — still no API calls),
addressing review's 6-point preflight review of the protocol document
itself:**

1. **Order-sensitivity citation verified against the actual run script**,
   not assumed: `run_step0a2.py` lines 124/126 confirm `score_mix_L1_L2`
   vs. `score_mix_L1_L2_swapped` use the identical two sentences and
   identical instructions/criteria — concatenation order is the *only*
   variable that differs. The "assuming the prior comparison controlled
   for composition" caveat is now resolved, not carried forward as an
   assumption. Added the exact do/don't-establish table (mechanism
   unknown; order effect doesn't necessarily equal intended semantics).
2. **Phase B's inability to investigate order-sensitivity is now its own
   named, explicit exclusion** (previously implied by "canonical
   presentation only") — stated as a rule that Phase B's own data may
   never be used as evidence about order-invariance either way.
3. **N=6-gate/N=9-accounting separation made concrete**: added a
   quantities table (gate input/denominator vs. pairwise-accounting
   denominator, explicitly different), a prohibited-phrasing rule ("the
   nine-item gate passed" — banned, no such gate exists) plus the
   required replacement phrasing verbatim, and a code-level requirement
   that any future Phase B analysis script call the frozen `gate()`
   function unmodified on the 6-item data and compute `n_P` via a
   *separate* function on the 9-item data — never one merged function.
4. **Immutable identity for the 3 supplement compositions**: new
   `research/data/characterization/score_supplement_hashes.json` (design
   script + supplement record SHA-256, the 3 compositions' identities) —
   kept separate from the already-frozen verifier audit rather than
   retroactively editing it.
5. **27-call budget confirmed fixed**, with retry-accounting stated
   explicitly (client-level retries don't add to the planned count, per
   established convention).
6. **Full outcome-interpretation matrix added to Phase C** — every
   combination of {frozen-6 gate outcome} × {stability} × {pair-specific
   sufficiency} now has a required report phrase, including the
   previously-undefined "CLARITY but unstable" and "AMBIGUITY but
   inconclusive due to instability" cells, not just the favorable
   combinations.

**Protocol design is now at the preflight-complete stage the review
described.** No execution has occurred; none is authorized by this
update.

**Update (Revision 6, 2026-09-22 — still no API calls, all four remaining
checks closed with real code):** (1) space-definition confirmed rather
than assumed — the gate verifier now asserts the achievable per-candidate
match range is exactly `{0..6}` (7 values, never a padded `{0..7}`), so
343 = 7³ is provably the exact logically-possible space, not oversized.
(2) An 8-case named boundary matrix added (leader at `CLARITY_MIN±1`,
other candidate at `CLARITY_OTHERS_MAX`/`+1`, ties at the floor, all tied
high, all at/below `FAILURE_MAX`) — each individually visible and
asserted, not just silently swept up by the exhaustive sweep. (3)
Primitive-test independence strengthened with the actual limitation named
in the script's docstring: this n=4/3-level domain only ever produces
quarter-fraction means, so no quarter-fraction test is *truly*
independent of it — fixed with 7 genuinely out-of-domain values
(negative, large, non-quarter-fraction) plus the specific mode-detection
cases requested (two-way tie, three-way tie, order-invariance, and the
one that matters most — "max level is not the mode," `[0,0,0,9]→mode=0`,
directly exercising the M≠X property this whole study depends on).
**Building this caught a real bug**: an order-invariance test case,
`[1,9,9]`, wasn't actually the same multiset as the tie case it was
meant to re-test (missing a `1`) — caught by running it, not by
inspection, fixed to `[1,9,1,9]`. (4) A new §8, "Verifier validity vs.
semantic validity," makes explicit what passing every script does *not*
establish: that M/X/A is correct, that 6 items are sufficient, that the
thresholds are optimal, that a future Stage 1 experiment would have valid
ground truth, or that any of this generalizes past the tested domain.

Both verifiers re-ran clean end-to-end after the fix.

**Update (Revision 5, 2026-09-22 — still no API calls, genuine
implementation audit):** upgraded both verification scripts with real
mutation testing, not just prose claims of protectiveness. Composition
verifier: added independent primitive unit tests (textbook values,
unrelated to any composition) for `round_half_up`/`mode_with_tie_
detection` before trusting them on real data; added 4 mutation tests
(corrupt a discrimination-class claim, relabel the supplementary item as
primary, break rounding, break tie-detection) — all 4 confirmed caught;
added CSV/JSON artifact-integrity checks (row count, duplicate keys,
credential-string scan, verifier script hash recorded in the JSON). A
real bug surfaced building this: the "no network dependency" check's
first draft used substring search on its own source and matched its own
forbidden-word list literal — fixed with an AST-based import check
instead, reported not silently patched.

Gate-logic verifier: added the explicit precedence case from review's
item B4 (`M=5,X=4,A=0` → AMBIGUITY, confirmed never CLARITY/FAILURE), and
3 mutation tests. **The most interesting result**: disabling the tie-
check branch changes **0 of 343** outcomes under the shipped thresholds —
proven mathematically (any tie-at-max necessarily puts a co-tied,
above-threshold candidate into the "others" check, which alone already
blocks CLARITY), not a test gap. A second mutation, using a hypothetical
threshold configuration where the branch *would* matter, confirmed 16
wrongful CLARITY cases appear without it — proving the mutation
methodology itself is sound rather than the branch being dead weight or
the tests being vacuous. `FAILURE_MAX`/`CLARITY_MIN` separately confirmed
load-bearing (perturbing either measurably shifts the outcome
distribution).

Both scripts re-ran clean end-to-end after fixes.

**Update (Revision 4, 2026-09-22 — still no API calls):** the composition
table is no longer hand-derived or hand-checked. Two new verification
scripts, both run and both clean:
`research/src/verify_score_semantic_compositions.py` enumerates all 15
possible 4-sentence/3-level multisets, computes `(M, X, A_unrounded,
A_rounded)` independently for each, and asserts the spec's every claim
against that computed table (primary-set size/composition, zero
`M=X=A_rounded` items, the 2-three-way/4-two-way split count, the
supplementary item's M-undefined status and its exclusion from the
primary set) — output saved to `score_semantic_composition_table.csv`
and `score_semantic_composition_verification.json`.
`research/src/verify_score_gate_logic.py` exhaustively runs the gate
pseudocode over all 343 possible `(matches_M, matches_X, matches_A)`
combinations (not just spot-checked tie cases), confirming a tied leader
can never produce CLARITY and that the three outcomes are exhaustive and
mutually exclusive across the *entire* space, not just by construction
argument — output saved to `score_gate_logic_verification.txt`.

Also: the supplementary item now carries an explicit
`"supplementary_contested_tie"` membership tag (asserted structurally by
the verification script, not just described in prose) so it can't be
accidentally swept into the primary set by a generic filter; a mandatory
6-quantity reporting table added so `repeat_unstable` counts are never
confused with semantic mismatch in the eventual write-up; the gate
pseudocode restructured with an explicit tie-branch and the failure
threshold spelled out as a literal integer constant; and an explicit
caution that this n=4 design's results won't be directly comparable to a
hypothetical n=3 run.

**Update (Revision 3, 2026-09-22 — still no API calls):** review caught
that `(1,1,2)`'s "all three distinct" label was mathematically wrong
(rounded A=1=M, only X=2 differs) — checking every Revision 2 row the
same way (not just the flagged one) found this was a real design flaw,
not a typo: **with 3-sentence/3-level compositions, only 4 of the 6
"primary gate" items were actually usable** — `(0,1,1)` and `(1,2,2)`
have M=X=A after rounding (zero discrimination), mislabeled as
discriminative since Revision 1. Root cause: only 10 possible 3-sentence/
3-level multisets exist, too few to supply 6 well-separated items without
collisions. Fixed by moving to **4-sentence items** (re-deriving the full
table by direct enumeration, script-verified, not hand-computed) — yields
6 genuinely discriminative compositions with zero rounding coincidences
(2 three-way, 4 two-way splits) plus a cleaner supplementary tie item
`(0,0,2,2)`; controls also moved to n=4 for internal consistency. Budget
unchanged (still 10 compositions × 3 calls = 30).

Also addressed review's two final checks: an explicit unit-of-analysis
statement (the gate operates on 6 composition-level modal decisions,
never the 18 raw repeat-level observations, with a stated, justified rule
for why `repeat_unstable` items contribute 0 to every candidate's count
rather than shrinking the denominator — shrinking it would let a
candidate's rate rise just by excluding its own hard cases); and literal,
executable pseudocode for the ordered gate, including a by-construction
proof that a tie at the top can never produce a CLARITY outcome (no
special-case branch needed).

Submitted for review before any manifest is built.

**Update (Phase B runner built, self-tested, and EXECUTED — 27 live API
calls, 2026-09-22):** review's blocking finding on `score_bounded_
semantic_validation_protocol.md` was that no executable Phase B runner
existed to enforce the protocol's requirements, only prose describing
them. Addressed with two new scripts, both self-tested before any call:

- `research/src/build_score_phase_b_manifest.py` — closed a real gap
  surfaced by trying to make the protocol executable: the frozen 6 items
  (`score_semantic_validation_specification.md` §3) and the 3 supplement
  items (`score_mvsa_supplement_v1.json`) had only ever been defined as
  abstract level-multisets, e.g. `(0,0,0,1)` — no actual sentence text
  existed to send to the API. This script authors 39 fresh, single-domain
  sentences (18 cosmetic / 9 degraded / 12 blocking), checked at runtime
  for zero overlap with any prior manifest's text, assigns them via a
  seeded deterministic shuffle (seed `1729`, no Jev output involved), and
  independently re-derives M/X/A from each item's level multiset before
  writing anything — asserting agreement with the pre-registered expected
  values. Output: `research/data/characterization/score_phase_b_manifest.json`
  + `score_phase_b_manifest_hashes.json` (same immutability discipline as
  `score_supplement_hashes.json`).
- `research/src/run_score_phase_b.py` — hash-verifies all four upstream
  inputs (design script, supplement record, the new manifest + its
  builder, the frozen `verify_score_gate_logic.py`) before touching
  anything; validates the exact 9-item identity set and the exact 27-call
  plan (rejects extra/missing/duplicate cells); imports `gate()` directly
  from `verify_score_gate_logic` rather than reimplementing it; keeps
  `compute_pairwise_np` structurally separate, operating on all 9 items;
  implements the §5.0 modal-reduction rule (0.02 tie tolerance, ≥2/3
  agreement); maps outcomes through the full 12-cell (gate × stability ×
  sufficiency) interpretation matrix; gates live execution behind two
  independent flags (`--live` + `--confirm-27-calls`) on top of
  `--mode live`.
- **7-case self-test suite, run and passing**: hash-tamper detection
  fires and un-fires correctly; an injected 10th item, a truncated
  26-call plan, and a duplicate cell are each rejected; `gate.__module__`
  confirms no local reimplementation; the 9-item pairwise scope is
  confirmed structurally distinct from the 6-item-only gate call site;
  `requests.post` was monkeypatched to raise and the dry-run preflight
  completed without triggering it. **A real bug was caught by the first
  self-test run, not glossed over**: `compute_pairwise_np` initially
  assumed an `"A"` key where the manifest correctly stores
  `"A_unrounded"`/`"A_rounded"` separately (per §2's rounding-rule
  distinction) — fixed with one `normalize_expected()` function rather
  than scattered ad hoc fixes.

**Executed, per explicit approval ("Approved: proceed with the 27 Phase B
calls")**: rebuild → hash match, self-tests → 7/7, dry-run preflight →
clean, then all 27 calls ran. Result: 27/27 HTTP 200, zero retries, zero
deviations. Full record: `research/results/score_phase_b_execution_manifest.json`;
raw/parsed data in `research/data/characterization/score_phase_b_{raw,parsed}_responses.jsonl`.

**Frozen six-item gate (denominator 6, unmodified)**: matches M=1, X=6,
A=0 → **CLARITY, leader X (Highest-severity)**, stability 6/6. **Nine-item
pairwise n_P (separate accounting)**: M-X 7 designed/6 favor X; M-A 6
designed/2 favor M, 1 favor A, 3 unstable-or-neither; X-A 9 designed/8
favor X, 1 favor A. Classification: `CLARITY/low-instability/sufficient`.

**Required report phrasing, per §A.2/§A.3 (binding, not optional)**:
*"discrimination among M, X, and A under canonical (fixed) presentation
only"* — never "score's intended semantics identified," "score implements
a maximum operator," or any claim that this generalizes across
presentation order. Order-dependence was already evidenced for `score`
(Step 0A.2, `score_mix_L1_L2` vs. `_swapped`) before this run and remains
completely untouched by it — Phase B's canonical-only design structurally
cannot speak to it either way. The four other unmodeled candidate families
(weighted statistic, transformation/normalization, probability-derived
statistic, nonlinear/concentration effect) remain unexcluded.

**No automatic Stage 1 expansion** (Phase C criterion 6) — two disposition
options are on the table and neither has been chosen yet: (A) close the
`score`-semantic investigation at this bounded result, or (B) a
separately designed, separately approved presentation-sensitivity study
(explicitly not an implicit extension of Phase B). Awaiting a decision on
which to pursue, if either, before any further `score` API calls.

**Update (Option B — presentation-sensitivity study designed, revised
4x, and EXECUTED — 36 live API calls, 2026-09-22):** Option B was chosen.
`research/methodology/score_presentation_sensitivity_protocol.md` went
through 4 review-driven revisions before any manifest was built:

- **Rev 1→2**: stable-cell eligibility made explicit (an unstable
  canonical cell excludes the item from comparisons, never zeroes it);
  continuous aggregation defined to use all 3 raw responses per cell, not
  just modal-matching ones; `MATERIAL_CONF=0.15` disclosed as conservative
  relative to Step 0A.2's ~0.13 prior shift; `P3`/`P4` given fully
  executable, independent stable-sort definitions (proven NOT reverses of
  each other via a worked `(0,0,1,2)` example); decision-change given an
  explicit formula/denominator; primary vs. secondary (M/X/A) analysis
  split; `UNCLASSIFIABLE`/`INCONCLUSIVE_BY_INSTABILITY` outcomes added so
  a high-instability run could never surface as a negligible-sensitivity
  finding.
- **Rev 2→3**: closed a P0 loophole — the raw classification could reach
  `NEGLIGIBLE` even when 2 of 3 items had **zero** eligible non-canonical
  comparisons, silently ignoring missing coverage. Fixed with an
  `item_coverage_complete` guard (all 3 items must have ≥1 eligible
  comparison) required for `NEGLIGIBLE`, mutation-tested.
- **Rev 3→4 — a real design flaw caught by literal artifact inspection,
  not structural review alone**: `P1_canonical` and `P4_severity_last`
  turned out to be **byte-identical** for all 3 selected items, and
  structurally for all 9 Phase B items — every composition in this track
  has always been written as a non-decreasing tuple, and sentence IDs are
  assigned in that same iteration order, so ascending-ID canonical order
  always already equals ascending-severity order. Caught only by
  comparing actual manifest contents cell-by-cell, not by reviewing the
  permutation *definitions* (which were individually correct). Fixed via
  **Option B**: `P4` reclassified from "third non-canonical permutation"
  to **canonical-equivalent replication control** — its 3 calls stay in
  the 36-call budget and remain their own separately-recorded cell (never
  pooled into `P1`), feeding only a separate P1-vs-P4 replication
  diagnostic (§6.3), structurally excluded from the decision-change/
  confidence-range/TV-distance estimands and from `classify()`. The
  manifest builder now asserts and would abort if `P2`/`P3` were ever
  content-identical to `P1` (mutation-tested).

**Self-tests: 15/15 passing** (runner) + 2 (builder's verbatim-reuse and
content-equivalence mutation tests), including explicit fixtures for
every precedence rule named across all 4 revisions.

**Executed, per explicit approval**: 36/36 calls, all HTTP 200, 0
retries, 0 deviations. **Result: `MATERIAL`.** Decomposed, precisely (per
review's phrasing corrections, adopted here):

- **No modal decision changes were observed** across the 6 eligible
  `P2`/`P3` comparisons (0/6) — this is an observation about the tested
  sample, not a claim of order invariance as a property of the model.
- **Confidence-range sensitivity exceeded the pre-registered `MATERIAL_
  CONF=0.15` threshold on 1 of 3 items** (`(0,0,1,2)`: canonical 0.723,
  full-reverse 0.613, severity-first 0.550, control 0.740 — range
  0.173). TV distance for that item (0.117) stayed below `MATERIAL_
  DIST=0.20` — the confidence-range criterion alone drove the `MATERIAL`
  classification, not a decision flip and not TV distance.
- **P1/P4 canonical-control diagnostic** (baseline same-content
  replication noise, one 3-call sample per item, not a general noise
  bound): confidence differences of 0.003/0.017/0.000 across the 3 items
  — an order of magnitude smaller than `(0,0,1,2)`'s 0.173 range,
  supporting (not proving) that the observed variation there is
  presentation-associated rather than pure sampling noise.
- **All tested presentations retained the descriptive X-alignment** for
  all 3 items across all 4 permutations (`X=true`, `M=A=false`
  everywhere) — Phase B's categorical result did not change in this
  sample; what changed was the confidence signal, not the decision.

**Established**: presentation-associated variation in `score`'s
confidence output, material on 1 of 3 tested items, coexisting with
decision stability across the same comparisons. **Not established**:
`score`'s intended semantics; order-sensitivity generalizing beyond this
domain/item-set/permutation-set; miscalibration; that this signal should
inform any specific escalation policy. No Stage 1 manifest or escalation
policy is authorized by this result (per protocol §9).

**Open next-question framing (not yet designed or authorized)**, per
review: any workflow-relevance follow-up should separately distinguish
(1) decision stability, (2) confidence sensitivity — both addressed here
— from (3) operational consequence and (4) reliability/error-risk
correspondence, neither of which this study touches.

All artifacts (protocol, manifest, hash-locks, builder/runner scripts,
raw/parsed responses, execution manifest) were committed at `def7da7`.

**Update (pivot to workflow-level composition — Step 2 protocol,
Revisions 1–9, 2026-09-22/27, no Step 2 calls):** the `score` sub-track
was closed at its bounded findings and kept as motivating evidence.
Work moved to the paper's actual question: how a multi-step workflow
should combine, or decline to combine, uncertainty signals from
heterogeneous primitives. This is Step 2 of
`pilot_experiment_specification.md`, specified in
`research/methodology/workflow_uncertainty_composition_protocol.md`,
and it builds on `compositional_reliability_baseline.md`'s `Δ` and
`conf_product` statistics. The protocol went through nine review-driven
revisions before any evaluation manifest existed:

- **Rev 1–2**: a fixed `K=3` chain (`choice → noul → score`) with a
  frozen workflow outcome contract. `Y_decision` counts escalated
  instances, so escalating everything can't look reliable. `Y_resolved`
  (coverage) is reported separately. `Δ` has one fixed population.
  Marginal and sequential baselines are both defined. Every strategy
  gets an information budget and a replication unit, and the cost model
  separates action, measurement, human and latency costs.
- **Rev 3 — a real leak caught.** The `score` escalation trigger relied
  on each item's *true construction class*, which no deployed system
  could observe. Triggers were split into deployable ones and
  diagnostic-only ones. Strategy 4 became 4a, the real policy, and 4b, an
  oracle ceiling that is never compared as a policy. Target coherence
  was formalized as `a* = F(c_1*, c_2*, c_3*)`, with required properties.
- **Rev 4–5 — §16 frozen.** This fixed the cost matrix, the task
  generator and the `F` table, the ordering, the adapter, and the power
  procedure. A "no degrees of freedom" audit followed. Three locks were
  written into the document: the cost matrix is only a post-hoc score,
  `F` is independent of strategy outputs, and there is an exhaustive list
  of what the calibration pilot must never be used for.
- **Rev 6 — three defects found by implementing, not reviewing.**
  `F`'s code diverged from its own table on `(unclear, blocking)`, and the
  protocol's prose verification was wrong at the same cell. §7.3's
  "weighted majority vote" was undefined, because `choice`'s decision
  has no counterpart in `F`'s input space. A random schedule could
  exceed a sentence pool's capacity, and did.
- **Rev 7** made the discordance estimand explicit: which comparisons,
  never pooled, `Y_decision` disagreement only, and a `1/30` floor
  applied only at sizing time. **Rev 8** named α = 0.05 and power = 0.80,
  which had never been frozen. **Rev 9** confirmed that the `(d, MDE)`
  sample-size formula is valid without the directional `b`/`c` counts,
  and withdrew a claim that `942` was "conservative".

**Update (first calibration pilot EXECUTED — 270 live calls,
2026-09-27):** 30 instances with fresh hand-written content (90
sentences, zero overlap with any prior manifest), run as a sequential
3-node chain in which node 2's and node 3's inputs depend on the live
upstream decisions. 270/270 calls, HTTP 200, 0 retries, 0 deviations.
Discordance: `2 vs 3` = 9/30 (`b=1, c=8`), `2 vs 4a` = 7/30 (`b=2,
c=5`). Resulting sizing: `N_final = max(942, 733) = 942`, about 8,478
calls. Committed as a checkpoint at `5c16f4c`.

**Update (Revision 10 — design correction B(ii), 2026-09-27/28, no
Step 2 calls):** reading the protocol against the pilot showed that
Strategy 3 was **structurally identical to Strategy 1**. §7.3 suppresses
`score` only when a *deployable* presentation-risk trigger fires, and
§8 defines none. So the binding `2 vs 3` comparison was really
`2 vs 1`. The sequence was protocol inspection → structural equivalence
→ design correction, not pilot result → reduce N. The pilot's `1 vs 3 =
0/30` is consistent with this but was not the reason. What changed:

- `2 vs 4a` became the **sole primary comparison**, giving N = 733
  (6,597 calls). A multiplicity gap from Revisions 7–9, two primary
  comparisons with no correction, was disclosed and is now moot.
  Strategy 3 was demoted to a descriptive arm that appears in no claim.
- Strategy 2's threshold was pinned at `0.5`, and 4a's cross-node rule as
  *none*: exactly the definitions `d(2v4a)` was measured under. This
  reverses the pilot's own pre-run description of `0.5` as
  "provisional", and the reversal is recorded in §7.2.
- The policy-development split was removed, since nothing is left to
  fit. §16.6 argues why this doesn't breach the pilot's prohibited-use
  list.
- Mechanical audits of the Revision 10 text and code found no leftover
  2-vs-3 or multiplicity language, and nothing fit from evaluation data.
- The sizing was recomputed from the 270 raw responses and written to
  `workflow_step2_power_analysis_rev10.json`. The Revision 9 file is
  kept unmodified.

**Update (content generator changes, so N is provisional again —
template grammar drafted, 2026-09-28, no API calls):** the no-reuse
rule needs about 2,199 unique evidence sentences for the main run.
The independent audit chose a **deterministic template grammar**, plus a
**second 270-call calibration pilot on templated content**, since
`d = 7/30` was measured on hand-written text and may not carry over.
Stale text in Revision 10 (§16.5, §16.6, §17 and the header) was
updated, and the old wording kept, marked as superseded. The grammar
(`workflow_template_grammar_spec.md` and
`build_workflow_template_grammar.py`) expands a finite, fully listed
vocabulary into 4,128 sentences, with pilot and main keys reserved
separately. All eight gating audits pass after fixes:
- 3 real cross-node cue leaks: "ad-hoc **query** tool", "footer
  **link** text", and "query **latency**".
- 1 severity leak: "**crash** reports" inside a customer-impact
  sentence.
- A plural-matching bug in the audit itself.
- A subject–verb agreement bug, and a workaround that didn't fit its
  feature. The checks passed both; only reading the output caught them.

**Open decision: how to define reuse.** Many vocabulary fillers are
synonyms. At the proposition level, two impact pools have only 32
distinct propositions and the blocking pool only 160, against 256
needed at N ≈ 738. Repeated propositions would correlate instances and
reduce effective power. The recommendation is to make proposition-level
uniqueness a gating check and enlarge the content vocabularies. A
proposed balanced allocation rule, `N_eval = 18·ceil(n_required/18)`,
also awaits sign-off.

**Where things stand (2026-09-28).** No evaluation manifest exists. No
Step 2 call has been made or authorized. The second pilot is not
authorized, and is gated on freezing the grammar and on an independent
grammar audit. Everything since `5c16f4c` is uncommitted: Revision 10,
the sizing record, the grammar, this log, and a new `README.md`. Next:
decide the reuse definition → revise the vocabulary → freeze and audit
the grammar → second calibration pilot → recompute N → build the
manifest → preflight → explicit Step 2 authorization.

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
