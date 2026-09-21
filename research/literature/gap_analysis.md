# Gap Analysis

Status: **based on a one-session, ~30-query general-web-search literature
pass (see `README.md` for method and limitations). Treat conclusions here as
provisional until the flagged snippet-level entries are independently
confirmed and the unsearched areas (classical reliability engineering, HCI
escalation literature) are checked.**

**Update after collaborator review:** the review confirmed the general
"nobody studies composed workflows" framing was too broad — PASC
(arXiv:2605.18812) and Lin et al. (arXiv:2609.07395) are closer to the
mathematical/empirical core than the abstract-only read below gives credit
for. Candidates 2 and 3 below have also been reframed per the
collaborator's specific feedback (characterization, not presumed failure;
a sharper heterogeneous-representation question).

**Update after full-text read (complete):** both papers, plus a targeted
search of the two previously unsearched areas (classical reliability
engineering, HCI human-AI escalation literature), have now been read/
searched in full (not abstract-only) — see §Full-text findings below. Net
effect: the novelty claim narrows further and becomes more specific, but a
defensible gap remains. **PASC is now confirmed, via full text, to genuinely
be a joint-maximum-nonconformity-score method** (Proposition 4 + Theorem 6)
giving exact finite-sample joint coverage for a K-stage pipeline — this
specific sub-problem (joint coverage for a homogeneous-scalar pipeline) is
solved and should not be re-claimed as open. **Lin et al. is now confirmed
to formally prove** (Propositions 1–2, not just empirically show) that
naive multiplicative composition of per-step confidence is wrong whenever
step correctness is correlated — this directly validates this project's own
`conf_product` statistic in `compositional_reliability_baseline.md` as
measuring a real, proven phenomenon, not a speculative one. Neither paper,
nor anything found in the two new search areas, addresses **composing
uncertainty across stages with structurally different representations**
(a bare scalar vs. a full distribution + separate confidence field) **or**
deriving an escalation policy *from* a composed, heterogeneous joint
uncertainty (as opposed to treating composition and escalation as separate
concerns, which is how every paper found here treats them). See
§Recommendation for the resulting sharpened claim.

## What is already established (not in dispute)

- Individual-model/individual-decision calibration is a mature area
  (Platt scaling, temperature scaling, Bayesian binning, ECE, reliability
  diagrams — P01–P03) and extends reasonably well to LLM outputs specifically
  (surveys P19, P20).
- Selective prediction / reject-option classification has a solid formal
  foundation (risk-coverage tradeoffs, P04–P06) — but only for a single
  decision point.
- Conformal prediction and conformal risk control (P07, P08) give
  distribution-free guarantees for a single stage, and recent work (2025–26)
  has begun extending this to two-stage settings (P10, P24) and to
  multi-stage NLP/LLM pipelines specifically (P22/PASC).
- Calibration-driven escalation/deferral for a *single* decision or a
  *cascade of the same decision repeated across model tiers* is an active
  and fairly well-developed area as of 2025–2026 (P16, P17, P18, P23, P25).
- For LLM *agents* specifically, very recent work (2025–2026) has begun
  directly studying whether step-level calibration composes into
  trajectory-level reliability, and the answer found so far is **no, it does
  not compose automatically** (P26, P28), and mechanisms exist for
  aggregating per-step uncertainty into a trajectory signal (P21, P27).
- A workflow-level *structural* policy (not calibration-based) can decouple
  end-to-end reliability from per-step accuracy at extreme scale (P13/MAKER).

## What is missing

1. **No paper found studies a heterogeneous multi-step workflow** — i.e. a
   workflow whose steps are different *kinds* of decisions (a routing
   choice, a numeric score, a binary check), each with potentially different
   uncertainty representations — as opposed to (a) a cascade of the same
   decision repeated across model tiers, or (b) an LLM agent's trajectory of
   structurally similar free-text-derived steps.
2. **No paper combines a general calibration-composition account with an
   escalation policy evaluated against an automation-coverage axis.** The
   calibration-composition papers (P22, P26, P28) are diagnostic — they show
   composition fails or characterize how — but do not then design and
   evaluate a workflow-level escalation policy. The escalation papers (P16,
   P17, P18, P23, P25) design and evaluate escalation policies, but for a
   single decision or homogeneous cascade, not a general composed workflow,
   and none plot reliability against an automation-coverage curve the way
   selective-prediction work (P04, P05) does for single decisions.
3. **No paper evaluates any of this on a structured, typed decision API**
   (Jev's `choice` / `score` / `noul` primitives, which return
   qualitatively different output shapes — a full categorical distribution,
   a numeric score with a distribution, and a bare 0.0/1.0 with no
   documented distribution, respectively). All reviewed agent/LLM papers
   operate on free-text or single-scalar LLM confidence: none address how a
   workflow-level policy should combine calibration signals across
   *structurally different* uncertainty representations within one workflow.
4. **TypeSafe's own documentation is internally in tension** on the central
   empirical premise: the product blog claims "Calibrated: higher confidence
   means higher accuracy," while the docs' `/confidence` page explicitly
   states confidence is "a statistic computed from the probability
   distribution the answer already gives you" (i.e., a concentration
   statistic) and makes no accuracy/calibration guarantee. No independent
   evaluation of this claim exists yet (Jev is a new product), and the
   claim itself is worth testing before anything built on top of it.

## Why the missing part matters

If per-decision calibration does not compose into workflow-level reliability
(as P26 and P28 suggest for LLM agents, and as P22 shows formally for
conformal coverage), then any system — including one built on Jev — that
sets automation thresholds per-decision using per-decision confidence is
likely to under- or over-estimate true end-to-end reliability, silently. This
is a practical risk for anyone using Jev (or any structured-decision API) to
automate multi-step software workflows, not just a theoretical curiosity.
Nobody has yet shown *how much* this matters when the workflow is
heterogeneous (mixed decision types), nor whether a workflow-level escalation
policy can recover most of the lost reliability at a tolerable automation
cost — which is exactly the second half of the original research question
and is unanswered for this setting by any paper found.

## Full-text findings (PASC, Lin et al.) and two new search areas

Full detail in `literature_matrix.csv` (rows P22, P26 updated; P29–P34
added). Summary:

- **PASC, full text:** genuinely a joint-max-nonconformity-score method
  (Prop. 4: ⋂ₖ{sₖ≤q} = {maxₖ sₖ≤q}; Thm. 6: joint coverage in
  [1−α, 1−α+1/(n+1)]). Tested on a static NER→NED→Entity-Typing pipeline
  with real distribution shift (CoNLL-2003 → WNUT-17/WikiNEuRal), against
  independent-CP/Bonferroni/tuned-Bonferroni/MC-Dropout baselines.
  **Explicitly does not test agentic/LLM-agent chains** (named as future
  work), **has no escalation/abstention treatment at all**, and
  **structurally assumes every stage can be reduced to one scalar
  nonconformity score in [0,1]** — it does not handle a stage whose native
  output is a full distribution plus a separately meaningful confidence
  field differently from a stage whose native output is a bare scalar.
  Single-author independent-researcher preprint, no venue, unreviewed as of
  v1 (2026-05-12) — treat citation weight accordingly.
- **Lin et al., full text:** the step-vs-trajectory calibration gap is a
  **proven result**, not just an empirical observation — Proposition 1 gives
  a two-step correlated-coin-flip counterexample, and Proposition 2 gives
  the exact formula `P(Y₁=1,Y₂=1) = p₁p₂ + ρ√(p₁(1−p₁)p₂(1−p₂))`, showing
  naive multiplicative composition *underestimates* joint success under
  positive correlation. TC-ECE requires per-checkpoint (not pooled)
  calibration assessment. Escalation is discussed only as motivation
  (§8.2), never implemented or evaluated. Their "heterogeneity" is about
  *where* in a pipeline uncertainty arises (planning vs. tool-use vs.
  retrieval, etc. — a taxonomic axis), not about formally composing stages
  whose uncertainty *representations* differ in type.
- **Classical reliability engineering** (Barlow & Proschan 1965 onward,
  P32; modern dependent-failure-propagation extensions, P34): gives
  60+-year-old closed-form component→system composition math, including
  extensions that relax the independence assumption — but for binary/point
  pass-fail reliability, not probabilistic calibration, and not escalation
  policy. Confirms component-to-system composition per se is not a novel
  mathematical object; this project's contribution must rest on the
  calibration/heterogeneous-representation/escalation combination, not on
  "composing reliability across stages" alone.
- **HCI/learning-to-defer literature**: an active field (Chow 1970 reject
  option onward; Madras, Pitassi, Zemel 2018 "Learning to Defer," P33) with
  one directly adjacent paper — **Babbar, Bhatt, Weller, "On the Utility of
  Prediction Sets in Human-AI Teams," IJCAI 2022 (P29)** — which combines
  conformal-prediction-style uncertainty with human deferral and validates
  it with a real n=120 human-subjects study. This is the nearest single
  precedent for "escalation policy derived from calibrated uncertainty,"
  but it is single-stage, not composed across a pipeline. Also newly found:
  an operations-research framing of escalation thresholds under reviewer
  capacity constraints (Wang & Rachev 2026, P31) and a pre-deployment
  diagnostic for whether abstention will help at all (Doku 2026, P30) —
  both single-decision, different framings than ML calibration composition.

**Sharpened, defensible gap statement** (replacing the earlier, broader
claim): a project that (a) formally or empirically composes uncertainty
across pipeline stages with **structurally different representations**
(a bare scalar with no separate confidence field vs. a full distribution
with one) — which PASC's uniform-scalarization assumption and Lin et al.'s
location-taxonomy do not cover — **and** (b) derives an escalation/
human-review policy **as a function of that composed, heterogeneous joint
uncertainty**, rather than treating composition and escalation as separate
concerns (every paper found here does one or the other, never both
together) — is not preempted by anything found across ~70 total search
queries in this and the follow-up pass. This is a narrower, more specific
claim than the original "heterogeneous multi-step workflow reliability"
framing, and should be stated this precisely in any paper draft, with PASC
and Babbar et al. cited as the two nearest neighbors and the exact axis
each falls short on named explicitly.

**Caveats on this claim, stated plainly:** this remains a general-web-search
pass (~70 queries total across both rounds), with no Scholar/Semantic
Scholar/ACM/IEEE Xplore access — reliability-engineering and HCI venues
specifically are likely underindexed by general web search. PASC is a
single-author, unreviewed, very recent (2026-05) preprint in a fast-moving
area and may already have follow-up work by the time this is read. Absence
of a preempting paper in this search is evidence of "not found," which is
intrinsically weaker than evidence of "does not exist."

## Candidate gaps (ranked by research fit and feasibility, not by unverified novelty)

### Candidate 1 — Calibration-to-reliability composition + escalation policy in heterogeneous multi-step workflows (generalized version of the original RQ)

- **What's already known:** Composition fails to preserve calibration in
  LLM-agent trajectories (P26, P28) and in conformal-coverage NLP pipelines
  (P22); single-decision/homogeneous-cascade escalation policies work well
  (P16–P18, P23, P25).
- **What's missing:** A workflow-level escalation/abstention policy
  *designed and evaluated* for a *heterogeneous* multi-step workflow, plotted
  against an automation-coverage axis, with an explicit account of how
  per-decision calibration quality relates to the resulting workflow
  reliability.
- **Why it matters:** This is the practically relevant setting for anyone
  building software automation (routing → validation → retry → escalation
  style workflows), not just LLM-agent trajectories or repeated-model
  cascades.
- **Is it genuinely open:** Yes, per this search — the closest papers (P22,
  P26) each cover one half; none cover both halves together in a
  heterogeneous-decision-type workflow.
- **Evidence that would address it:** A synthetic benchmark with controlled
  ground truth (Phase 3) across chain/branching topologies, individual
  calibration metrics per decision node (Phase 6), workflow-level reliability
  measured end-to-end, and at least one escalation policy (fixed threshold
  as baseline, plus one uncertainty-aware alternative) evaluated on a
  risk–coverage-style curve at the workflow level.
- **How it differs from existing methods:** Extends P26's diagnostic
  (step-vs-trajectory calibration gap) and P22's formal coverage-composition
  result into (a) a heterogeneous-decision-type setting and (b) a policy
  design/evaluation, which neither paper does.
- **Feasibility:** Highest effort/risk of the three. Requires the full
  benchmark + escalation-policy design + statistical analysis pipeline
  (Phases 3, 6, 9, 10) to be built and validated before results are
  meaningful. Real risk that with a synthetic benchmark only, findings won't
  transfer to claims about "software workflows" broadly — the plan already
  requires at least one non-synthetic task (Phase 3) to mitigate this.

### Candidate 2 — Characterization study: how does Jev's reported confidence relate to correctness, across primitive types?

**Reframed per collaborator review.** This is a characterization study with
an open outcome, not a search for a presumed calibration failure. The
hypothesis under test is: *does Jev's reported confidence behave as an
empirically useful predictor of correctness, and how (if at all) does that
behavior differ across `choice`, `score`, and `noul`?* — not "Jev claims to
be calibrated but the docs prove it isn't" (that would be premature; the
blog/docs wording difference is a motivation to check, not a conclusion).

- **What's already known:** General methodology for testing LLM confidence
  calibration is mature (P02, P03, P19, P20). TypeSafe's own docs
  (`docs.typesafe.ai/confidence`) describe `confidence` as a
  distribution-concentration statistic without stating an accuracy
  guarantee, while the product blog claims "Calibrated: higher confidence
  means higher accuracy." This wording difference is directly quotable and
  is the motivation for testing, not evidence of a finding.
- **What's missing:** Any independent empirical evaluation of Jev
  specifically (it is a new product; nothing in the literature search
  concerns it), including whether the relationship between confidence and
  correctness differs across the three primitive types (choice/score/noul),
  across input rewordings, across ambiguous vs. clear inputs, and under
  repeated identical queries. Also missing: separating *calibration*
  (probabilities track empirical correctness) from the weaker *ranking
  quality* (higher confidence merely correlates with correctness, e.g. via
  AUROC) — a system can have poor calibration but still-useful ranking, and
  the two have different implications for escalation-policy design.
- **Why it matters:** This is a necessary premise-check before any
  composition claim can be trusted — if individual Jev decisions are
  *already* poorly related to correctness, that alone could explain
  workflow-level unreliability without needing a composition-specific
  mechanism, which would change the interpretation of any Candidate-1-style
  result. Equally, if individual decisions turn out well-calibrated, that is
  itself a useful, reportable finding, not a null result to bury.
- **Is it genuinely open:** Yes for Jev specifically, but the *methodology*
  is well-trodden (P02, P03) — this is novel-in-application, not
  novel-in-method. See `../methodology/pilot_experiment_specification.md`
  §Step 0B for the decision gates (A–E) this study must pass before its
  results are treated as meaningful.
- **Evidence that would address it:** Phase 2 characterization experiments
  already specified (repeated inputs, wording perturbations, ambiguous vs.
  clear, per-primitive-type ECE/reliability diagrams).
- **How it differs from existing methods:** Applies established calibration
  auditing methodology to a novel commercial API and a novel primitive
  design (typed choice/score/noul rather than free-text-derived confidence).
- **Feasibility:** Highest feasibility of the three — directly buildable
  from the Phase 2 client + characterization experiments already scoped, and
  low statistical/engineering risk. **Weakest as a standalone paper
  contribution** (an audit of one commercial product, using known methods),
  but necessary regardless of which candidate is chosen, and could stand as
  a workshop paper or as Section 1 of a larger paper built on Candidate 1
  or 3.

### Candidate 3 — Workflow-level escalation under structurally heterogeneous uncertainty representations

**Sharper framing per collaborator review** (the original "noul has one
number, choice has a distribution" framing was an API observation, not yet
a research question): *does the representation of a decision's uncertainty
— a bare scalar probability (`noul`) vs. a full distribution plus a
separately derived concentration statistic (`choice`/`score`) — affect the
quality of a common workflow-level risk estimate or escalation policy, after
controlling for the underlying decision's correctness and the information
actually available?* This must be left open to several possible answers,
not designed to find one: the representations could turn out equivalent for
binary decisions; a derived scalar could be sufficient for some policies;
the richer distribution could matter only in multi-class settings; naively
combining heterogeneous signals could itself introduce calibration error;
or downstream cost information could matter more than representation type.

- **What's already known:** Escalation policies exist for homogeneous
  uncertainty signals (a single confidence scalar per step, or a single
  conformal set per step — P16–P18, P21, P23, P25, P27).
- **What's missing:** Every reviewed workflow/cascade/agent paper assumes
  each step emits the *same kind* of uncertainty signal. Jev's own primitive
  design breaks this: `choice` and `score` return a full probability
  distribution (over options or over levels, respectively) plus a
  *separate, derived* `confidence` scalar (a concentration statistic of that
  distribution), while `noul` returns a single continuous value in [0,1]
  documented as "the probability that the answer is yes" and has **no
  separate `confidence` field at all** — per the docs, "a Noul's probability
  distribution has only two outcomes, yes and no, so the single `noul` value
  describes it completely." So the heterogeneity is not "some nodes have
  uncertainty info and some don't" (all three primitives are fully
  probabilistic) — it is that `noul`'s single number conflates what
  `choice`/`score` keep separate (the answer's direction/value vs. how
  concentrated the model is about it), which a workflow-level policy
  designed around a `confidence`-like scalar cannot directly consume for
  `noul` nodes without an explicit transformation (e.g. `2*|noul - 0.5|` as
  an analogous concentration statistic — itself an assumption to test, not
  a given). A workflow mixing all three (as the candidate 5-stage workflow
  in Phase 3 does) has no established way to combine these structurally
  different representations into one workflow-level escalation decision.
- **Why it matters:** This is not a hypothetical — it is a direct
  consequence of how Jev (and plausibly other structured-decision APIs) are
  actually designed. An escalation policy that only knows how to use
  scalar confidence will silently ignore or mishandle `noul` nodes.
- **Is it genuinely open:** Yes per this search — no paper reviewed
  addresses heterogeneous uncertainty *representations* within one workflow,
  as distinct from heterogeneous *decision content* with homogeneous
  representation (which is what LLM-agent-trajectory papers have).
- **Evidence that would address it:** Requires the Phase 3 heterogeneous
  workflow with at least one `noul`-type node, and an ablation comparing a
  representation-aware escalation policy against one that treats all nodes
  identically (e.g. by forcing `noul` outputs through the same threshold
  logic as `choice`/`score` confidence).
- **How it differs from existing methods:** No existing escalation-policy
  paper reasons about representation heterogeneity; this would be a novel
  mechanism-level contribution, but a narrower one than Candidate 1.
- **Feasibility:** Medium — narrower in scope than Candidate 1 (a specific
  mechanism question rather than a general theory), but still requires the
  full workflow benchmark and escalation-policy infrastructure. Somewhat
  dependent on `noul`'s actual behavior once characterized in Phase 2 (e.g.,
  if `noul` turns out to expose more granular information than the docs
  suggest, this gap narrows).

## Recommendation

**Status: full-text review complete (see §Full-text findings above).** The
structure below (Candidate 2 first, then a scoped Candidate 1+3 merge) is
confirmed as the working plan, **narrowed to the sharpened gap statement**
above: composing heterogeneous-representation uncertainty *and* deriving an
escalation policy from that composition, together — not composition alone
(PASC's territory) and not escalation-from-uncertainty alone (Babbar et
al./P29's territory). Any paper draft must cite and differentiate from PASC
and Babbar et al. specifically, on the exact axis each falls short. The
explicit go/no-go decision rule in
`../methodology/pilot_experiment_specification.md` §Decision rule still
governs whether to proceed to Step 2 once Step 0 results are in — full-text
review clears one of that rule's gating conditions but does not replace the
Step 0 empirical check.

**Pursue Candidate 2 first, as mandatory Phase 2 groundwork (not a
standalone paper direction) — it is already scoped as part of the API
characterization phase and gates everything downstream: if Jev's
`confidence` field is not usefully related to correctness at the individual
level, that changes how Candidates 1 and 3 should be framed and interpreted.**

**For the main paper contribution, pursue a scoped-down merge of Candidates 1
and 3**: study calibration-to-reliability composition and a workflow-level
escalation policy (Candidate 1's core question) specifically in a
heterogeneous-decision-type workflow that includes at least one structurally
different uncertainty representation (Candidate 3's specific mechanism,
using a real `noul` node). This is recommended over pursuing Candidate 1 or
3 alone because:

- It targets the specific combination that the shortlist shows is
  genuinely unaddressed (heterogeneous decision types + composition theory +
  escalation policy + automation-coverage evaluation), rather than
  re-deriving a result (P22, P26) or narrowly re-deriving a mechanism
  (P23, P27) that already exists in an adjacent setting.
- It is grounded in Jev's actual, documented primitive design rather than a
  hypothetical — the heterogeneity is not manufactured for novelty's sake.
- It reuses Phase 3's already-planned 5-stage candidate workflow, so no
  separate infrastructure is needed for Candidate 3's mechanism question —
  it is naturally exercised by testing Candidate 1's general question on
  that workflow.

This recommendation should be revisited after Phase 2 characterization
(Candidate 2) is complete: if Jev's `noul` primitive turns out (empirically)
to behave like a thresholded version of `choice`/`score` rather than a
genuinely different representation, the Candidate-3 component of this
recommendation weakens and the project should fall back to a pure
Candidate-1 framing (still a defensible, if less distinctively Jev-specific,
contribution). This should also be revisited if further literature search
(Scholar/Semantic Scholar access, or the unsearched classical-reliability
and HCI areas) surfaces a paper that already covers this combination.

## Assumptions still needing validation before this becomes a confirmed plan

- `/primitives/choice`, `/primitives/score`, and `/primitives/noul` have now
  been fetched (see `../jev_api_notes.md`) and confirm: `noul` is a
  continuous probability in [0,1] with no separate `confidence` field (by
  design, not an omission — a two-outcome distribution is fully described by
  one number), while `choice`/`score` expose a full distribution plus a
  separate `confidence` concentration statistic. **This still needs
  re-verification against live API responses once the Phase 2 client is
  built** — documentation and actual API behavior can diverge, and the docs
  give only one worked example per primitive.
- That the blog-vs-docs tension on "calibrated" is not resolved elsewhere in
  the docs (`/confidence`, `/introduction/quickstart`, and all three
  `/primitives/*` pages were checked; `/patterns` was not yet fetched, and
  none of the checked pages define calibration or give an accuracy
  guarantee — so the tension stands as described, but `/patterns` should
  still be checked before this is treated as final).
- ~~That P22 (PASC) is not simply the paper that already answers Candidate 1~~
  — **resolved via full-text read**: PASC solves joint coverage for
  homogeneous-scalar pipelines only; it does not address heterogeneous
  representations or escalation policy. Peer-review status remains
  unverified (single-author preprint, no venue) — still worth periodically
  re-checking for a published/reviewed version before final citation.
- New: Babbar, Bhatt, Weller (P29, IJCAI 2022) is the nearest single-stage
  precedent for escalation-from-calibrated-uncertainty and should be read
  in full (currently abstract-level only) before the paper draft, since any
  reviewer familiar with the deferral literature will expect it addressed.
- That a synthetic benchmark plus one realistic task (per the existing Phase
  3 plan) will be convincing enough for peer review — this is a standard
  concern for synthetic-first workflow-reliability work and should be
  discussed explicitly in the paper's limitations section regardless of
  which candidate is chosen.
