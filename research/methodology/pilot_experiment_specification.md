# Concrete experiment specification (revised after collaborator review)

Revision note: this replaces the original single "Step 0 / Step 1" draft.
The collaborator review approved Step 0A, Step 0B (as exploratory), and
Step 1 (as plumbing only, not scientific evidence), and explicitly did
**not** approve treating a 50-instance workflow run as scientific evidence,
or locking the heterogeneous-uncertainty method / main research question yet.
Step 2 (the actual research pilot) is deferred until Step 0's findings and
the literature full-text review (PASC, Lin et al.) are in.

## Target research direction (see `../literature/gap_analysis.md`)

Provisional, to be refined after this pilot and the pending full-text
literature review: a scoped study of calibration-to-reliability composition
and escalation-policy design in a **heterogeneous** multi-step workflow
(mixed `choice`/`score`/`noul` decision types), gated on Step 0's
characterization and calibration findings.

**Sharper framing of the heterogeneous-representation question** (replacing
the earlier, looser "noul has one number, choice has a distribution"
framing): *does the representation of a decision's uncertainty — a bare
scalar probability (`noul`) vs. a full distribution plus a separately
derived concentration statistic (`choice`/`score`) — affect the quality of
a common workflow-level risk estimate or escalation policy, after
controlling for the underlying decision's correctness and the information
actually available?* This leaves open, and the experiment must be able to
show, any of: the representations turn out equivalent for binary decisions;
a derived scalar is sufficient for some policies; the richer distribution
matters only in multi-class settings; naively combining heterogeneous
signals introduces its own calibration error; or downstream cost
information matters more than representation type. No outcome should be
assumed going in.

## Step 0A — API characterization (approved; run first, small)

**Purpose:** establish ground truth about the live API before any
calibration or workflow claim is built on top of assumed behavior.
Documentation and live behavior can diverge; this step checks that.

**What it must establish, per primitive (`choice`, `score`, `noul`) —
using the collaborator's requested quantity table:**

| Quantity | What Step 0A checks |
|---|---|
| Output probability | Does the live response's `probabilities` (or `noul` value) match the documented shape and always sum to 1.0 (for `choice`/`score`)? |
| Confidence | Is `confidence` present exactly when documented (absent for `noul`), and does it match the documented concentration formula given the returned `probabilities`? |
| Repeated-call behavior | For an identical request repeated 3×, how much do `choice`/`score`/`noul`/`probabilities`/`confidence` vary? (Needed to know if experiments are reproducible at whatever sampling settings we don't control.) |
| Model version | Does the response's `model` field resolve `"jev-latest"` to a concrete version string, and is it stable across calls within one session? |
| Usage/latency | Do `usage.input_tokens`/`usage.output_tokens` behave sensibly (roughly track input length), and what is per-call latency? |
| Mixed-question behavior | When `choice`, `score`, and `noul` questions are sent together in one request, are they answered independently of each other (as documented — "in parallel and in isolation")? |

**Design:** a small, fixed set of hand-written (not yet synthetic-generator)
probes — a few `choice` questions, a few `score` questions, a few `noul`
questions, one repeated 3× identical, one mixed multi-question request.
Target: on the order of 15-25 total API calls. This is deliberately much
smaller than the previously planned 540-call audit — characterization comes
first, at minimum spend, before deciding the calibration audit is even
worth running at scale.

**Output:** a characterization report (raw responses persisted, schema
validated against a pydantic model derived from the docs, any discrepancies
between documented and observed behavior flagged explicitly) — see
`../../results/reports/` once generated.

## Step 0B — Individual-decision calibration audit (approved, exploratory only)

**Reframed question** (per collaborator review — this is a characterization
study, not a presumed finding): *does Jev's reported confidence behave as an
empirically useful predictor of correctness, and how (if at all) does that
behavior differ across `choice`, `score`, and `noul`?* Do not presuppose the
blog/docs tension resolves toward "not calibrated" — that is exactly what
this step tests.

For each primitive, Step 0B must distinguish, not conflate:

| Quantity | Meaning being verified |
|---|---|
| Output probability | The model's returned distribution/scalar |
| Confidence | The separately returned or derived concentration measure |
| Correctness | Whether the selected/implied output matches ground truth |
| Calibration | Whether predicted probabilities track empirical correctness |
| Ranking quality | Whether higher confidence identifies more reliable cases (a weaker, still-useful property even if literal calibration fails — e.g. AUROC of confidence vs. correctness) |

**Decision gates — all must pass before any calibration claim is treated as
meaningful, and before scaling up beyond the pilot's item count:**

- **Gate A — Semantic validity:** we can state, precisely and in writing,
  what each returned probability/confidence value is claimed to represent
  for each primitive (done in `../jev_api_notes.md`; Step 0A must confirm
  this against live responses, not just docs).
- **Gate B — Ground truth:** every test item has a defensible,
  non-circular correctness label (synthetic-generator items must not be
  constructed in a way the model could trivially exploit or that makes the
  "ground truth" itself ambiguous by the label-generation process).
- **Gate C — Identifiability:** enough items are spread across the observed
  probability/confidence range (not clustered at 0 or 1) to make a
  reliability diagram informative — if Jev is near-deterministic and always
  reports confidence ≈1.0 on these items, ECE is not measurable and the
  item design must change before proceeding.
- **Gate D — Comparability:** for each primitive, we can state exactly
  which uncertainty signal is being evaluated and why (e.g., for `noul`,
  whether we test the raw value, or a symmetrized transform like
  `2*|noul-0.5|`, and why).
- **Gate E — Reproducibility:** the same item set and code can be re-run and
  produce auditable, comparable output (raw responses persisted with
  experiment ID, config, and model version, per Step 0A).

If any gate fails, **stop and fix the experimental design** — do not
proceed to a workflow-level (Step 2) conclusion on top of a failed gate.

**Design:** the previously specified ~540-call design (3 primitive types ×
3 ambiguity levels × ~20 items × 3 repeats) remains the target *design* for
Step 0B, but it should not be run until Step 0A confirms the gates above are
plausibly satisfiable (e.g., that confidence values are not degenerate).
Treat Step 0B's own results as **exploratory** — sized to check the gates
and get a first read on calibration behavior, not to produce a publishable
calibration claim on its own.

**Update after Step 0A.1 (controlled ambiguity follow-up, see
`../results/step0a1_controlled_ambiguity_report.md`) — this design must
change before Step 0B runs:**

- Items cannot be generated by "write text that sounds ambiguous" — that
  reliably saturates to confidence 1.0 for `choice` (and, on the one
  untested attempt so far, for `score` too). Items must instead be built
  from **explicit, matched evidence pools** (fixed-register sentences,
  each pre-labeled as supporting one option/level), mixed in controlled
  counts, the way Step 0A.1 did for `choice`. `score` needs its own version
  of this construction (not yet built).
- **Evidence/sentence order must be an explicit, randomized variable for
  every near-balanced item**, not a single fixed arrangement — Step 0A.1
  found a 0.82→0.01 confidence swing from reordering the same four
  sentences. Each "balanced" item should be run in ≥2-3 random orders.
- **Items with intermediate confidence need repeat sampling** (Step 0A.1
  saw ~±0.03-0.04 confidence jitter across 3 identical calls when
  confidence was intermediate, vs. bit-identical repeats when confidence
  was saturated) — budget 2-3x repeats for non-saturated items specifically,
  not uniformly across the whole item set. This will raise the effective
  call count above the original ~540 estimate; the revised total should be
  computed once the matched-evidence-pool method is extended to `score`
  and `noul`.

## Step 1 — Workflow plumbing only (approved; explicitly not scientific evidence)

Purpose: validate orchestration, ground-truth generation, logging, schema
handling, and escalation routing code end-to-end. **Results from this step
must not be cited as evidence about compositional reliability or escalation
policy quality** — the sample size and item design are for engineering
validation only.

Design unchanged from the original draft: a 3-stage chain (`choice` routing
→ `noul` validation → `score` severity, conditioned on upstream outputs, no
oracle correction between stages), 50 synthetic instances, two trivial
policies compared (no escalation vs. a fixed 0.7 confidence threshold, not
tuned). See git history of this file for the original full description if
needed; the design itself is unchanged, only its evidentiary status.

## Step 2 — Research pilot (deferred — to be designed after Step 0 + literature review)

**Not yet specified in detail.** Per collaborator review, the topology,
benchmark size, comparison methods, and escalation intervention for the
actual research pilot must be selected *based on* Step 0A/0B findings and
the pending full-text comparison against PASC (arXiv:2605.18812) and Lin et
al. (arXiv:2609.07395) — not designed in advance of that evidence. When
specified, Step 2 must be sized to make the `Δ` statistic and workflow-level
reliability diagram in `compositional_reliability_baseline.md` estimable
with a defensible sample size (to be computed via a power analysis once
Step 0B gives a first estimate of per-node accuracy/variance — not just
picked arbitrarily as 50 was for the plumbing step).

## Decision rule: does the pilot justify the larger paper?

Explicit go/no-go criteria, to be evaluated after Step 0A + Step 0B
(exploratory) + the literature full-text review are complete, **before**
Step 2 is designed or run:

- **Go, with the heterogeneous-representation framing (Candidate 3):** if
  Step 0B shows `noul`'s calibration/ranking-quality behavior measurably
  differs from `choice`/`score` (e.g., markedly different ECE, or the
  `2*|noul-0.5|` transform is a poor proxy for concentration relative to how
  `confidence` behaves for the other two), AND the full-text review confirms
  PASC/Lin et al. do not already cover heterogeneous-representation
  composition.
- **Go, with the general composition framing (Candidate 1), representation
  angle dropped:** if Step 0B shows no meaningful representational
  difference, but a non-trivial composition gap `Δ` is still plausible from
  Step 1's plumbing run (even though not statistically meaningful at n=50,
  a large qualitative effect is worth a properly powered Step 2) — and the
  full-text review confirms PASC's formalism doesn't already fully cover the
  escalation-policy question.
- **Narrow scope further, or reconsider Candidate 2 as the primary
  contribution:** if Step 0B shows Jev's confidence is poorly related to
  correctness *at the individual-decision level already* (regardless of
  composition) — in that case, the individual-decision audit itself
  (Candidate 2), done rigorously across primitive types and possibly
  compared against other structured-decision APIs, may be the more
  defensible and self-contained contribution, and the composition question
  becomes a secondary finding rather than the main claim.
- **No-go on the current framing entirely:** *(resolved — does not apply)*.
  The full-text review is complete: PASC solves joint coverage for
  homogeneous-scalar pipelines only (no heterogeneous representations, no
  escalation policy); Lin et al. proves step-vs-trajectory miscalibration
  but never attempts joint composition or an escalation policy; Babbar et
  al. (P29) combines calibrated uncertainty with human deferral but only
  for a single-stage decision. None directly answers the sharpened
  combination (heterogeneous-representation composition + escalation
  policy derived from that composition) — see
  `../literature/gap_analysis.md` §Full-text findings for the complete
  reasoning. This condition should still be re-checked if a newer preprint
  surfaces before the paper is finalized, given how recent (2025-2026) the
  closest work is.

This decision should be made explicitly and in writing (an update to
`gap_analysis.md`'s recommendation section) — not implicitly by just
proceeding to Step 2.

## Budget

- Step 0A: ~15-25 API calls (small, deliberately).
- Step 0B: up to ~540 API calls if gates A-E pass — actual cost to be
  measured from Step 0A's `usage` fields before committing to the full run.
- Step 1: as specified in the original draft (~50-150 calls depending on
  whether stages can be batched or must be sequential — confirmed by
  Step 0A's mixed-question-behavior check).
- Step 2: not yet budgeted — depends on the power analysis referenced above.
- **No step beyond Step 0A should be run without checking in, given Step 0B
  and Step 1 both involve nontrivial API spend even if individually cheap.**

## Explicitly out of scope until Step 2 is designed

- Non-Jev baselines (Phase 4).
- Distribution-shift conditions (Phase 8).
- Branching topology, workflow depth variation (Phase 8).
- Any escalation policy beyond the two trivial Step 1 baselines (Phase 9).
- Statistical significance testing (Phase 10) — Step 1's n=50 is not
  powered for this; Step 2 will be, once designed.
- The realistic/externally-validated task required for the final paper
  (Phase 3 requirement).
