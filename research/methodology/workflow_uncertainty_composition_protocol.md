# Workflow Uncertainty Composition Protocol — Step 2, Specified (Revision 9)

Status: **design only — no manifest built, no API calls made or
authorized (with one narrow, disclosed exception noted in §16.5).** This
document is **Step 2** of `pilot_experiment_specification.md`, now
specified after Step 0A, Step 0B (`stage1_h1h2b_analysis.md`), and the
entire `score` track. It operationalizes `compositional_reliability_
baseline.md`'s `Δ`/`conf_product` statistics. Per review's own verdict on
Revision 4: **methodology is not being reopened** — Revision 5 makes
three already-agreed guarantees explicit *in the artifact itself* rather
than leaving them as conversational claims, since review correctly noted
it could only audit a summary, not the file. Pipeline: §16 frozen
(Revision 4) → these three locks made explicit (Revision 5) → the
30-instance calibration pilot (its own separate go/no-go) → power
calculation → manifest generation → hash lock → preflight/self-tests →
main evaluation run.

## Changelog from Revision 8

Review asked, correctly, whether the `942`/`733` sample sizes actually
used the McNemar test's directional discordant-pair counts (`b`, `c`) or
only their sum. Verified against the raw pilot data: `2v3` had `b=1,
c=8`; `2v4a` had `b=2, c=5` (both satisfy `b+c` = the already-reported
discordance count, confirmed by direct assertion, not by argument). The
formula used is the standard `(d, MDE)`-parameterized McNemar sample-size
formula, mathematically equivalent to a `(b,c)`-parameterized one — `b`
and `c` individually aren't required as *inputs* because `MDE` is the
pre-specified design target from §16.1's cost matrix, never estimated
from the pilot's own split. `N_final` is unchanged. The directional
breakdown is now recorded in `workflow_step2_power_analysis.json` for
audit. The pilot's own raw directional imbalance (`b−c`: −0.233 and
−0.100) happens to exceed the `0.05` target in magnitude, but this does
**not** by itself make `942` "conservative" — an earlier draft of this
line claimed so, and review correctly rejected it: a 30-instance
estimate of `b−c` is noisy, and `n` also depends on `d`, which could
differ under a larger true effect. The only claim this supports is the
procedural one: the design calculation never substituted the observed
imbalance for the pre-specified `0.05` target.

## Changelog from Revision 7

The 30-instance, 270-call calibration pilot executed cleanly (270/270,
HTTP 200, 0 retries, 0 deviations — `workflow_calibration_pilot_
execution_manifest.json`). Computing the actual power analysis (§14)
surfaced one more disclosed gap, closed here rather than left implicit:
**significance level and target power were never named as frozen
constants.** Fixed with the standard, universally-conventional values
`α = 0.05` (two-sided) and `power = 0.80` — the same class of disclosed-
convention constant as the Wilson-CI 95% level already used throughout
this project, not a value chosen to hit any particular result.

## Changelog from Revision 6

Review confirmed the four implementation-discovered fixes and asked for
one last thing before authorizing the 270 calls: make the discordance-
rate estimand feeding §14's power analysis completely explicit — which
comparison(s), pooled or separate, which outcome, and the small-cell
rule. Not a new methodology decision; §14 previously left all four
ambiguous ("a candidate strategy (3, 4a)" implied one comparison could
stand in for both). §14 now specifies: two separate, never-pooled
comparisons (`2v3`, `2v4a`), both estimated from the same 30 pilot
instances; `Y_decision` disagreement as the only paired outcome;
`N_final = max(n_required(2v3), n_required(2v4a))` as the sizing rule for
a single shared evaluation set; and a disclosed `1/30` discordance floor
applied only at power-*calculation* time (never altering the pilot's own
reported raw counts) if either comparison observes zero discordant pairs.

## Changelog from Revision 5

Discovered while *implementing* the calibration pilot (building
`build_workflow_calibration_pilot_manifest.py` / `run_workflow_
calibration_pilot.py`), not by further methodology review — this is
execution work surfacing a real defect, the same category of finding as
the `P1≡P4` catch, not a reopened design choice:

1. **`F`'s own implementation initially diverged from its frozen
   table** — code checked `c3==2` before `c2=="unclear"`, silently
   turning `(unclear, 2)` into `escalate` instead of the table's
   `request_more_evidence`. Caught by `verify_F_totality_and_properties`,
   fixed in code. This also exposed that **§16.2's own prose verification
   of property 3 was itself wrong** ("every `c_3*=2` row resolves to
   `escalate`... regardless of `c_2*`" contradicts the table one line
   later) — fixed to state the actual, weaker property correctly
   (property 3 forbids `accept`, not any specific non-accept action).
2. **§7.3's "weighted majority vote" is inapplicable to the concrete
   generator** — `choice`'s decision has no counterpart in `F`'s
   `(c_2*, c_3*)` input space, so a vote including it is undefined, not
   merely underspecified. Resolved: Strategy 3's action rule is `F`
   applied to `noul`/`score`'s decisions only, for this generator;
   `w_choice` is retained as a named constant for a future generator
   where it would apply, disclosed as unused rather than silently
   dropped. Zero new tunable parameters introduced.
3. **A schedule-construction bug**, also caught by execution: a random
   shuffle for the calibration pilot's 12 "extra" instances could exceed
   a sentence pool's fixed capacity (and did, on the first run). Fixed
   with an exact deterministic (off-diagonal) construction, verified
   against the claimed per-value counts directly, not merely by
   construction argument.

## Changelog from Revision 4

Review audited Revision 4 from a summary (correctly declining to claim
line-by-line verification of a file it couldn't retrieve) and asked for
three things to be locked down **in the document**, not just described:

1. **Cost matrix isolation from strategy construction** — new binding
   rule at the top of §7: `cost(a,a*)` is a post-hoc scoring function
   only, never an input to any strategy's decision rule, extended into
   the bundle-isolation self-test (§2).
2. **`F`'s input-independence from strategy outputs** — a new, explicit
   property in §4.3 (`F`'s only arguments are the construction-defined
   `c_i*` values, never any strategy's output or any live API result),
   verified as property 0 in §16.2's per-property checklist.
3. **The calibration pilot's boundary, exhaustively enumerated** — §16.5
   now lists, verbatim, the seven things the pilot's result must never
   be used for (modifying the generator, costs, Strategy 3, thresholds,
   the split ratio, excluding instances, or altering any estimand), and
   requires the pilot to produce its **own** separate manifest/hash-lock/
   results artifacts, never merged into Step 2's main dataset. §16.5 also
   now states explicitly that the cost-matrix-derived MDE (operational
   relevance) and the pilot-derived discordance rate (statistical power)
   are two different kinds of quantity, never substituted for each
   other, per review's specific ask.

## Changelog from Revision 3

Per review's explicit instruction — "§16 execution only, no further
methodology review" — every item in Revision 3's §16 checklist is now
frozen as a concrete, disclosed decision (§16.1–§16.6), not left as a
generic placeholder. A **"no degrees of freedom remain" audit** was then
run against the entire document (§17) — every occurrence of
choose/select/tune/optimize/threshold/weight/"depending on results" was
checked and is either pinned to a specific pre-registered value/rule or
explicitly labeled descriptive/diagnostic-only. One genuine exception
survived that audit and is disclosed rather than papered over: §16.5's
power analysis cannot produce a final sample size from paperwork alone —
it requires a small (~30-instance), separately-scoped **calibration
pilot** whose only purpose is measuring a discordance rate, walled off
from policy-development and evaluation data, **not yet authorized**, and
not counted as this document authorizing any of Step 2's actual 36+
evaluation calls.

**Handoff test (per review's framing)**: after this revision, every
section below is a complete, unambiguous specification **except** the six
items in §16 — and those six are now generic-content gaps (the actual
task domain, its numeric costs, its ordering choice), not open
methodological questions. Someone else should be able to read this
document and build §16's six deliverables without making a single
further methodological decision.

## Changelog from Revision 2

Review laid out a 7-step resolution order. Items 1–5 are resolved as
frozen decisions below (not deferred prose); item 6 (power analysis) gets
its exact procedure specified in §14, not computed (it structurally
cannot be, until §16's generator-dependent items exist); item 7 (build
manifest, run) remains gated on §16.

1. **Measurement layer frozen** (§2, new) — exactly what every node
   records, how repeats are generated and reduced, and a binding
   invariant (checked by self-test, not assumed) that no strategy's
   decision can depend on information outside its declared budget.
2. **Strategy 3 finished** (§7.3) — an actual weighted-vote rule with
   exactly two named constants (`w_noul=0.5`, `noul` binarization cutoff
   `=0.5`) and one control-flow rule, all fixed before any Step 2 data
   exists. No free parameter remains to be fit after results are seen.
3. **Target coherence resolved** (§4.3, new) — `a* = F(c_1*, c_2*, c_3*)`
   is now a required, contractually-constrained function (totality,
   nominal-default, non-silent-escalation-suppression), closing the gap
   where node-level targets and the final-action target were defined
   independently with no stated relationship.
4. **Escalation triggers split into deployable vs. diagnostic-only**
   (§8, restructured) — **this caught a real leak in Revision 2**: the
   `score` presentation-risk trigger relied on knowing an item's *true
   construction class*, information no deployed policy could ever
   observe. Strategy 4 is now split into 4a (deployable-only, the actual
   evaluated policy) and 4b (an oracle ceiling using the diagnostic-only
   signal, reported only as a mechanism-level upper bound, never as a
   real strategy).
5. **Estimands/costs given explicit small-cell rules** (§5.4, §6) — a
   minimum conditioning-population size for `Δ_seq`'s conditional terms,
   explicit "not estimable" handling for empty cost-matrix cells and
   low-`n` frontier bins, rather than silently computing a noisy point
   estimate.
6. **Power-analysis procedure specified** (§14, new) — the exact test
   (paired McNemar / paired bootstrap CI, matching §2's shared-response
   paired design) and its required inputs, without fabricating a sample
   size from data that doesn't exist yet.
7. Manifest/preflight/live calls remain **not authorized**, gated on §16.

## 0. Why now, and what's already decided (unchanged)

Per `pilot_experiment_specification.md`'s decision rule: **"Go, with the
heterogeneous-representation framing (Candidate 3)"** — confirmed, not
reopened here. Motivating evidence, unchanged: Step 0B's two distinct
`choice`/`noul` failure modes (`choice`'s high-confidence/low-accuracy
subgroup, mean confidence 0.915, observed accuracy 0.333, n=6; `noul`'s
systematic underconfidence despite 24/24 accuracy) plus the `score`
track's two further findings (Phase B's non-identified X-lead; the
presentation-sensitivity study's confidence-material/decision-stable
split, 0.173 confidence range on 1/3 items, 0/6 decision changes).

## 1. The workflow abstraction — tightened scope

```
x -> P_1(x) -> P_2(x|P_1) -> ... -> P_K(x|P_1..P_{K-1}) -> a

Fixed for this pass:
K = 3, exactly. Primitive multiset = {choice, score, noul}, each once.
Chain ordering FIXED: choice -> noul -> score, frozen in §16.3.
  No branching. No silent node-skipping - only via a strategy's own
  escalation action (§7).
Upstream-to-downstream input transformation via the deterministic
  adapter frozen in §16.2/§16.4, not improvised per instance.
Every strategy's declared input state is logged BEFORE its policy
  function executes (§2's binding invariant).
```

Proposed abstraction for this pass only — not a claim about every real
Jev workflow, nor that ordering/branching are unimportant (out of scope
here, explicitly).

## 2. Measurement layer — frozen

**Per-node measurement bundle**, recorded once per input, before any
strategy's policy function runs, immutable thereafter:

```
For node i (primitive in {choice, score, noul}):
  - 3 raw API responses (repeats): full raw JSON, http_status, parsed
    decision/level, confidence (choice/score) or noul scalar,
    probabilities/legend where applicable, timestamp, usage tokens.
  - choice/score: modal reduction per score_semantic_validation_
    specification.md §5.0 (reused verbatim) - tie tolerance 0.02 on the
    top-two probabilities, modal decision requires >=2/3 non-tied
    agreement, else `stable=False` (repeat_unstable).
  - noul: no distribution, so "tie" doesn't apply. mean_noul = mean of
    the 3 raw scalars. The 3 raw values' own spread (max-min) is recorded
    as noul's repeat-variability diagnostic - the closest analogue to
    repeat_unstable this primitive supports, reported but not gating
    "stable" the same way (noul has no natural near-tie concept).
  - mean_confidence / mean_probabilities (choice/score): computed over
    ALL 3 raw responses (not filtered to modal-matching repeats), per
    the score track's established rule (Revision B of the presentation-
    sensitivity protocol).

Bundle_i = {raw_responses[3], modal_decision_or_mean_noul, stable,
            mean_confidence, mean_probabilities}
```

**Canonical `noul`-decision extraction (Revision 4, stated once, reused
everywhere)**: `noul` has no native categorical decision. Wherever a
binary decision is needed from a `noul` node — for node-level correctness
`C_i` (§5), for `F`'s inputs (§4.3, §16.2), and for Strategy 3/4a's vote
(§7.3) — it is extracted identically, by the single frozen rule
`noul_decision = 1 if mean_noul >= 0.5 else 0`. This rule is defined once
here and never redefined or re-tuned at any other point in this document.

**Binding invariant (checked, not assumed)**: every strategy's action is
a pure function of the bundles for the nodes it is declared to access
per §7.5's information-budget table — nothing else. Verified by a
self-test mirroring `run_score_phase_b.py`'s pattern: re-run a strategy's
policy function against a copy of the bundle with every *undeclared*
field corrupted or removed; the strategy's output action must not
change. A strategy whose output changes under this mutation is a defect
in that strategy's implementation, caught before any live call.

**Shared-response design (frozen)**: all four strategies (1, 2, 3, 4a —
§7) are evaluated on the **same** measurement bundles per input. Raw
calls are made **once** per input (3 repeats × 3 nodes = 9 calls/input,
per §6's `C_measurement`), and every strategy's policy runs over that one
recorded dataset. This is a deliberate **paired** design; the paired
dependency is reflected downstream in every comparison (§14's power
analysis, §12's policy-level analyses) — never treated as four
independent samples.

**Replication units**:

| Unit | Definition | Role |
|---|---|---|
| Raw response | One API response | Measurement-level record |
| Node replicate | One node's `Bundle_i` (3 raw responses, reduced) | Per-node stability/decision estimate |
| Workflow replicate | One complete `K=3` chain, built from its 3 nodes' bundles | Primary outcome unit — `Y_decision`/`Y_resolved` computed here |
| Input | One fixed constructed instance `x` | Sampling unit |
| Strategy evaluation | One input, evaluated under one policy (§7) | Comparison unit |

## 3. What each primitive can expose, and what's comparable

Unchanged from Revision 2 (grounded in Step 0B and the `score` track):

| Primitive | Native output | Established behavior | Comparable across primitives? |
|---|---|---|---|
| `choice` | categorical decision + `probabilities` dict + `confidence` | Step 0B: 18/24 (75%) accuracy, Spearman ρ=0.25 (weak), high-confidence/low-accuracy subgroup (0.915 conf, 0.333 acc, n=6) | `probabilities[reference_label]` well-defined; `confidence` a documented concentration statistic |
| `noul` | single scalar `noul ∈ [0,1]`, no separate `confidence` field | Step 0B: 24/24 (100%) accuracy, correlation undefined, underconfident in every bin | Requires the `2·|noul−0.5|` transform to get a confidence-like scalar at all — **transform validity untested** |
| `score` | ordinal `score` + `confidence` + `probabilities` over levels | Phase B: X-lead, not semantic identification. Presentation-sensitivity: 0.173 confidence range on 1/3 items, 0/6 decision changes | `confidence`/`probabilities` exist natively, but **the target the distribution represents is unresolved** |

**Terminology discipline (unchanged)**: any composed statistic
(`conf_product` or similar) is a **composed confidence-like statistic**,
never a common probability estimate. **Binding rule (unchanged)**:
*metric comparability is not experimental comparability* (Step 0B §5).

## 4. Workflow outcome contract — frozen, including target coherence

### 4.1 Ground-truth mechanism (unchanged)

Step 2 runs first on **construction-defined ground truth** as an
explicit **methodology-validation pass**, not the paper's externally-
validated evidence (that remains a separate, later decision, §16).

### 4.2 Outcome contract — required fields (unchanged from Revision 2)

```
Input:                    a constructed instance x (content-blind,
                           seeded, no-reuse discipline).
Reference outcome (a*):   known by construction - see §4.3 for how it
                           relates to node-level targets.
Intermediate node target: each node i has its own construction-defined
                           reference decision c_i* - node-level
                           correctness measured against c_i* directly.
Final workflow action:    one of {accept, escalate, request_more_evidence,
                           defer}.
Y_decision:                1[a == a*] - defined for EVERY instance,
                           including escalated/deferred ones. If a*
                           itself is "escalate" for a genuinely
                           ambiguous-by-construction instance,
                           Y_decision correctly rewards escalating on
                           exactly those instances (see §4.3's property
                           3 for why this is guaranteed, not assumed).
Y_resolved:                1[a != escalate AND a != defer].
Treatment of escalation
  and defer:               scored via Y_decision/Y_resolved as above -
                           never automatic success or failure.
Treatment of unresolved
  cases:                   excluded from an estimand's population ONLY
                           if a node produced no reading at all
                           (repeat_unstable, §2) - never conflated with
                           a deliberate escalation.
```

`W=1` (from `compositional_reliability_baseline.md`) is disambiguated as
`Y_decision=1` for the remainder of this document.

### 4.3 Target coherence — how node-level targets compose into `a*` (Revision 3, new — closes the gap review named)

Revision 2 defined `c_i*` and `a*` as each construction-defined, but never
specified their relationship — a real gap: without it, a generator could
assign them inconsistently, silently invalidating `Δ_seq`'s conditional-
accuracy interpretation and the claim (§4.2) that `Y_decision` rewards
escalating on genuinely ambiguous instances.

**Frozen contract**: `a* = F(c_1*, c_2*, c_3*)`, where `F` is a
deterministic function fixed at manifest-build time. **This document
specifies the properties `F` must satisfy** — the actual table, frozen
in §16.2, is verified against these three properties there.

**Input-independence property, made explicit (Revision 4, per audit —
stated ahead of the three properties below, since it constrains `F`'s
inputs rather than its outputs)**: `F`'s *only* arguments are the
construction-defined targets
`c_1*, c_2*, c_3*` — values fixed by the generator at manifest-build
time, before any Jev call exists. `F` has no access to, and never
depends on, any strategy's actual output `a`, any node's live decision,
confidence, or probability, or any Step 2 evaluation-set result. This
guarantees `a*` is computed once, by the generator alone, and can never
be fitted or adjusted to match — or to disadvantage — any strategy's
behavior. `F` must additionally satisfy:

1. **Totality**: defined for every `(c_1*, c_2*, c_3*)` combination the
   generator can actually produce — no combination left with an
   undefined `a*`.
2. **Nominal default**: if every `c_i*` indicates the unambiguous/nominal
   case for its node, `F(...) = accept`.
3. **Non-silent-escalation-suppression**: if any `c_i*` indicates a
   construction-flagged edge case, `F` must not resolve to `accept`
   unless the generator explicitly documents that specific combination
   as a genuine, disclosed exception — never a silent default. This is
   what makes §4.2's "rewards escalating on genuinely ambiguous
   instances" claim true by construction, not by assumption.
4. **`c_i*` independence from `a*` is definitional, not a claim of
   statistical independence**: each `c_i*` is measured against its own
   node-level target regardless of `a*`'s value, but `c_i*`'s *value* can
   still cascade into `c_{i+1}*`'s construction (node `i+1`'s input
   depends on node `i`'s output, per §1) — `F` maps the resulting tuple
   to `a*`; it is not a claim that the `c_i*` are drawn independently of
   each other.

## 5. Estimand definitions and populations

### 5.1 Primary outcome and population (unchanged)

`P(Y_decision=1)`, over the full, pre-specified instance population — no
strategy-dependent exclusion, never conditioned on `Y_resolved=1`.

### 5.2 Secondary quantities (unchanged)

`P(Y_decision=1 | Y_resolved=1)`; coverage `P(Y_resolved=1)`;
escalation/defer rate.

### 5.3 `Δ` — two baselines (unchanged)

```
P̂_marginal = Π_{i=1}^{K} P(C_i=1)                    # marginal product
P̂_seq = P(C_1=1) * Π_{i=2}^{K} P(C_i=1 | C_1=1,...,C_{i-1}=1)  # sequential

Δ_marginal = P_observed(Y_decision=1) - P̂_marginal   # PRIMARY
Δ_seq      = P_observed(Y_decision=1) - P̂_seq        # SECONDARY, reference diagnostic
```

`Δ_marginal` primary for continuity with `compositional_reliability_
baseline.md`'s already-reconciled Lin et al. Proposition 2 sign guidance.
`n_i^reached` reported per node per strategy.

### 5.4 Undefined and small-cell handling (Revision 3, new — closes the "silent noisy estimate" gap)

```
MIN_CONDITIONING_N = 5   # frozen, disclosed, not tuned post-hoc
MIN_BIN_N = 5
```

- `P̂_seq`'s conditional term `P(C_i=1 | C_1=1,...,C_{i-1}=1)` is
  **UNDEFINED** (not computed as a point estimate) if that conditioning
  population has fewer than `MIN_CONDITIONING_N` instances. If undefined,
  `Δ_seq` itself is reported UNDEFINED for that comparison — never
  silently computed from a noisy conditional estimate.
- `Δ_marginal` is **UNDEFINED** if any `n_i^reached = 0` for a strategy —
  never treated as `P(C_i=1) ∈ {0,1}` by convention.
- Any `(a, a*)` cost-matrix cell (§6) with zero observed evaluation-set
  instances is reported **"not estimable from this pass"** — never
  imputed as zero-cost.
- Risk-coverage frontier bins (§10) with fewer than `MIN_BIN_N` instances
  are reported but flagged **low-n**, not suppressed, not given the same
  interpretive weight as larger bins.

## 6. Cost model

```
C_total = C_action + C_measurement + C_human + C_latency
```

| Component | Included this pass? | Definition |
|---|---|---|
| `C_action` | Yes | `cost(a, a*)` — full numeric matrix frozen in §16.1 |
| `C_measurement` | Yes, simplified | fixed per-call unit × raw calls used (§2: 9 calls/input, shared across strategies — no strategy pays more in calls, only strategy 4a's *use* of the repeat data differs, §7.5) |
| `C_human` | Placeholder = 1 fixed unit/escalation | avoids silently pretending escalation is free |
| `C_latency` | Not modeled | disclosed as unmeasured, not assumed zero |

Undefined-cell handling per §5.4. Cost-sensitive comparisons only use
components marked "included," with `C_latency`'s absence disclosed in
every such comparison.

## 7. Composition strategies — executable contracts

**Binding rule, checked against every strategy below (Revision 4, per
audit)**: `cost(a, a*)` (§6/§16.1) is a **post-hoc scoring function
only**. It is applied *after* a strategy produces its action `a`, to
compute `C_action` for reporting (§9, §11) — it never appears as an
input to, or is referenced by, any strategy's decision rule `π_1..π_4a`
below. No strategy chooses an action by minimizing expected cost; each
decides via its own fixed decision/confidence/vote/trigger logic, and
the cost matrix only scores the result afterward. This is checked, not
merely asserted: none of §7.1–§7.4a's decision rules take `a*` or
`cost(·,·)` as an argument, and the bundle-isolation self-test (§2)
extends to confirming this — a strategy's action must not change if
`cost(·,·)`'s values are corrupted in a mutated copy of the environment
it runs in.

### 7.1 Strategy 1 — Decision-only

```
Feature contract: primitive identities, node positions, native
  DECISION only, upstream decision sequence. EXCLUDED: confidence,
  probabilities, noul's raw scalar beyond its binarized decision, any
  repeat statistic, any offline risk label.
π_1: (decisions_1..K) -> action, fixed lookup rule (per manifest).
```

### 7.2 Strategy 2 — Naive confidence composition

```
conf_i = confidence (choice, score) or 2*|noul-0.5| (noul).
conf_product = Π conf_i
π_2: threshold(conf_product) -> action, threshold frozen on the
  policy-development set (§8), never on the evaluation set.
```

### 7.3 Strategy 3 — Primitive-aware composition (Revision 6 — resolved against the concrete generator)

**Finding, disclosed (Revision 6)**: attempting to actually implement
this section against §16.2's concrete generator surfaced a real
incompatibility, not a stylistic gap — `weighted_majority(decisions,
weights=[w_choice, w_score, w_noul])` presumes all three nodes' decisions
live in one comparable, votable space. In the frozen generator they do
not: `choice` picks a subsystem (`network`/`database`), which `F` never
takes as an input at all — only `noul`'s and `score`'s decisions
determine `a*` (§16.2). A "vote" that includes `choice`'s decision
against the other two is not merely awkward, it is undefined — `choice`'s
value has no counterpart to agree or disagree with. This was invisible
until someone tried to compute it, exactly analogous to the `P1≡P4`
degeneracy caught in the presentation-sensitivity track — caught by
attempted implementation, not by re-reading the prose.

**Resolution, generator-consistent**: for this generator specifically,
`choice`'s decision plays no role in *which action* Strategy 3 selects
(it remains fully scored on its own, via `C_1`/`Δ`, per §5 — this only
changes what feeds the *action*, not what feeds the mechanism-level
per-node correctness statistics). The combination reduces to `F` applied
to the two decisions `F` actually accepts:

```
Fixed constants (frozen now, never tuned on Step 2 data):
  w_noul   = 0.5   # disclosed, deliberately round discount reflecting
                    # the untested-transform gap (§3) - not fit to data
  w_score  = 1.0, forced to 0.0 (full suppression, not partial
             downweighting) when the DEPLOYABLE presentation-risk
             trigger (§8) is active for this node
  # w_choice is retained as a named constant (=1.0) for a future
  # generator where choice's decision IS actionable, but is not
  # consulted by THIS generator's combination rule - disclosed, not
  # silently dropped.

Per-node binarized decision:
  score: native ordinal decision. noul: the canonical noul_decision
  rule (§2).

Combination rule (deterministic):
  if w_score == 0.0:
      -> ESCALATE          # score suppressed, and F structurally
                            # requires a c3-equivalent input - no
                            # resolution is possible without it
  elif noul's decision is undefined OR score's decision is undefined:
      -> ESCALATE           # missing input, fail safe
  else:
      -> F(noul's decision, score's decision)   # F, §16.2, unmodified
```

This is deterministic, has the same two named constants (`w_noul`,
`noul`'s binarization cutoff) as before, and adds zero new free
parameters — it resolves an implementation impossibility, it does not
introduce a tunable choice. `w_choice` is unused by this generator's
action rule and is disclosed as such rather than silently dropped from
the constant list.

### 7.4a Strategy 4a — Abstention-aware composition (deployable; the actual evaluated policy)

```
π_4a: as Strategy 3 (§7.3), PLUS escalate if any DEPLOYABLE trigger
  (§8) fires: repeat instability, choice confidence >= 0.90, or
  cross-node disagreement. Uses only information a real deployed system
  observes at decision time.
```

### 7.4b Strategy 4b — Diagnostic ceiling (NOT a policy; never compared as one)

```
As 4a, PLUS also escalates on the score construction-class flag (§8's
DIAGNOSTIC-ONLY trigger) - information only the GENERATOR possesses
(the item's true construction class), never available to a deployed
system. Computed and reported ONLY in §11's mechanism-level analysis, as
an oracle upper-bound answering "how much would Y_decision improve if
this diagnostic-only signal were somehow made deployable." Labeled
"oracle ceiling" in every table it appears in. NEVER included in §12's
policy comparison or §13's outcome/claims matrix as a real strategy.
```

### 7.5 Information budget per strategy

| Strategy | Single evaluation? | Repeats accessed? | Native distribution? | Offline calibration data? | Can escalate? |
|---|---|---|---|---|---|
| 1 — Decision-only | Yes | No | No | No | Structural rule only |
| 2 — Naive confidence | Yes | No | Confidence scalar only | No | Threshold-based |
| 3 — Primitive-aware | Yes | No | Yes | Weights from policy-development set only | Fallback only |
| 4a — Abstention-aware (deployable) | Yes (base) | Yes — same repeats every node already has (§2), no extra calls | Yes | Yes, deployable-trigger thresholds only | Yes, primary role |
| 4b — Diagnostic ceiling (oracle, NOT a policy) | Yes (base) | Yes | Yes | Yes, **plus** generator-side construction-class knowledge | Yes, oracle only |

**Binding rule**: strategies 1–3 receive exactly the same single-call
inputs. 4a's additional access is limited to repeat-stability status
every node already generates (§2) — no extra API calls. 4b's oracle
access is explicitly disclosed and walled off from every policy-level
comparison.

## 8. Trigger contract — deployable vs. diagnostic-only (Revision 3, closes the leak review found)

Revision 2's `score` presentation-risk trigger relied on "a known
construction class" — the item's *true* generative construction, which a
real deployed system cannot observe (it only sees API responses). Fixed:
every trigger is now explicitly classified, and only **deployable**
triggers feed Strategy 4a.

| Trigger | Definition | Deployable or diagnostic-only? | Used in |
|---|---|---|---|
| Repeat instability | A node's 3-call modal reduction (§2) produced no modal decision | **Deployable** — the repeat calls are always made, their outcome is directly observed | 4a |
| `choice` confidence ≥ 0.90 | Exact boundary of Step 0B's observed subgroup (n=6), frozen | **Deployable** — confidence is a real, observed API field | 4a |
| Cross-node disagreement | Task-specific joint-inconsistency rule, frozen at manifest-build time | **Deployable** — decisions are observed at decision time | 4a |
| `score` construction-class flag | Item's *true* construction matches the presentation-sensitivity study's `MATERIAL`-flagged composition class | **Diagnostic-only** — requires generator-side knowledge no deployed system has | 4b (oracle) **only** |

**Discovery/policy-development/evaluation separation, unchanged for
every deployable trigger's threshold**:

```
Discovery set:            prior findings (Step 0B, the score track) -
                           already spent, not re-derived from Step 2 data.
Policy-development set:   a held-out portion of Step 2's instances,
                           used to fix any threshold/weight as a frozen
                           constant BEFORE evaluation.
Evaluation set:            scores the frozen triggers/weights only - no
                           post-hoc adjustment.
External validation set:   later, separate, out of scope here (§4.1).
```

If Step 2's sample is too small for a real split, every deployable
trigger is reported as a **pre-specified exploratory rule**, not a
calibrated one — and the `score` construction-class flag is reported
**only** via 4b's oracle-ceiling framing regardless of sample size, since
its diagnostic-only status is structural, not a data-volume problem.

## 9. Risk–coverage–cost reporting — full frontier, no post-hoc threshold selection

No strategy's threshold is chosen after seeing evaluation-set outcomes —
fixed on the policy-development set (§8).

**Required reporting per strategy, on the evaluation set**: full
empirical risk–coverage frontier (headline point = policy-development-
set-derived threshold; frontier itself is context, not license to
cherry-pick post hoc); `P(Y_decision=1)`, `P(Y_decision=1|Y_resolved=1)`,
coverage, escalation rate (§5); mean/tail `C_total` by component (§6);
`n_i^reached` per node; the threshold-selection procedure actually used.

## 10. Mechanism-level analyses (kept separate from policy evaluation)

Diagnose *how the primitives behave in composition* — never read as
policy validation alone: per-node and conditional correctness;
`Δ_marginal`, `Δ_seq` (§5.4's undefined-cell rules apply); `conf_product`
reliability diagram, reported per chain composition, not pooled; repeat-
instability rate per node type; **Strategy 4b's oracle ceiling** (§7.4b).

## 11. Policy-level analyses (kept separate from mechanism diagnosis)

Evaluate whether a strategy improves operational outcomes — strategies
1, 2, 3, 4a **only** (never 4b): `P(Y_decision=1)` per strategy
(primary); coverage, escalation rate, `C_total` (§9); risk–coverage–cost
frontier (§9); paired differences (§2's shared-response design).

**A favorable mechanism-level finding is never, by itself, evidence that
any specific strategy in §7 fixes it** — that is this section's separate
comparison.

## 12. Evidence required before any escalation policy is considered validated

| Tier | Question | What would establish it |
|---|---|---|
| Verifier validity | Does the strategy code correctly implement its own frozen contract (§7)? | Exhaustive/mutation-tested unit verification, same discipline as `verify_score_gate_logic.py`, plus §2's bundle-isolation self-test |
| Strategy validity | Does 3 or 4a improve `P(Y_decision=1)`, coverage, or cost vs. §7's baselines, on the construction-defined evaluation set, using only policy-development-derived thresholds? | A properly powered Step 2 run (§14) |
| External validity | Does that improvement hold on independently-validated ground truth? | The separate, later externally-validated task (§4.1) — not addressed here |

## 13. Outcome/claims matrix

| Result | Supports | Does not support |
|---|---|---|
| `Δ_marginal ≈ 0` and `Δ_seq ≈ 0`, strategies 1–4a similar `P(Y_decision=1)` | Per-node thresholds approximate this benchmark reasonably | Generalization beyond this construction-defined task |
| `Δ_marginal < 0` (Lin-et-al.-corrected) | Cascading failure, motivating a workflow-level policy | That any strategy in §7 fixes it |
| 3 or 4a beats 2 on `P(Y_decision=1)`/frontier at matched/disclosed cost | Primitive-aware/abstention-aware beats naive confidence, on this benchmark/evaluation set | External validity (§12); that deployable triggers (§8) transfer beyond their disclosed scope |
| No strategy beats 1 | Confidence-like signals may not add value here | Confidence signals are worthless in general |
| 4b's ceiling ≫ 4a | The diagnostic-only signal is workflow-relevant *if it could be made deployable* | That 4a (the real policy) captures that value — it structurally cannot, by design |
| High instability/abstention rates | `score`/`noul`'s representation-validity gaps are workflow-relevant | The deployable triggers are well-calibrated in general |

## 14. Power analysis — procedure specified, number pending §16.5 (Revision 7 — discordance estimand made explicit)

```
Primary comparisons: TWO, computed and sized SEPARATELY, never pooled:
  (a) Strategy 2 vs. Strategy 3
  (b) Strategy 2 vs. Strategy 4a
  - both are pre-specified strategy pairs from §7; there is no third
    "combined" comparison and no comparison against Strategy 1 or 4b in
    this power analysis (4b is never a policy comparison, per §11/§13).

Paired outcome: for each evaluation instance i, and for a given
  comparison (a) or (b), the pair is DISCORDANT iff
  Y_decision(Strategy 2, i) != Y_decision(comparator, i) - i.e. the two
  strategies' correctness against a* differs on that instance. This is
  the ONLY outcome paired; confidence, coverage, and cost are not part
  of this estimand.

Discordance rate, per comparison:
  d_hat(2v3)  = (# discordant pairs under comparison (a)) / n_calib
  d_hat(2v4a) = (# discordant pairs under comparison (b)) / n_calib
  Both are estimated from the SAME 30 calibration-pilot instances
  (shared-response design, §2) - not two disjoint sub-samples.

Test: McNemar's exact test (paired binary outcomes), run separately for
  (a) and (b). Paired bootstrap CI on the difference in P(Y_decision=1),
  also separate per comparison, reported alongside.

Significance level and power (Revision 8, disclosed convention, not
  tuned to any result): alpha = 0.05 (two-sided), power = 0.80 - the
  same class of standard, universally-conventional constant as this
  project's existing 95% Wilson intervals, chosen before either
  discordance rate was known.

Sample size, once both d_hat values exist - standard normal-
  approximation formula for McNemar-test sample sizing (the paired-
  difference estimator's variance is approximately d_hat/n when the MDE
  is small relative to the discordance rate):
    n_required = ceil( (z_{alpha/2} + z_power)^2 * d_hat / MDE^2 )
    z_{0.025} = 1.959963985, z_{0.80 power} = 0.8416212336
  n_required(a) = using d_hat(2v3) and MDE=0.05 (§16.5).
  n_required(b) = using d_hat(2v4a) and MDE=0.05.
  N_final = max(n_required(a), n_required(b))   # the LARGER of the two,
    never averaged or pooled - a single shared evaluation set (§2's
    paired design) must be adequately powered for BOTH comparisons
    simultaneously, so the more conservative (larger) requirement
    governs. Reported alongside both individual n_required values, not
    replacing them.

**Parameterization note (Revision 9, per audit)**: this formula requires
only `d` (total discordance), not the directional counts `b`
(Strategy-2-right/comparator-wrong) and `c` (Strategy-2-wrong/comparator-
right) individually, because it is parameterized by `(d, MDE)` rather
than `(b, c)` — an equivalent parameterization of the same family
(`b = n(d+MDE)/2`, `c = n(d-MDE)/2`), valid specifically because `MDE` is
a pre-specified design target (§16.1), never estimated from the pilot's
own `b`/`c` split. The actual `(b, c)` breakdown from the executed pilot
is recorded in `workflow_step2_power_analysis.json` for audit.

**Computed, 2026-09-27, from the executed 30-instance calibration
pilot** (`workflow_calibration_pilot_execution_manifest.json`,
270/270 calls, 0 deviations): `d_hat(2v3) = 9/30 = 0.300` (`b=1, c=8`, no
floor needed), `d_hat(2v4a) = 7/30 ≈ 0.233` (`b=2, c=5`, no floor needed)
→ `n_required(2v3) = 942`, `n_required(2v4a) = 733` →
**`N_final = 942`**. At `K=3` nodes × 3 repeats/node, this implies
**≈8,478 calls** for Step 2's main evaluation run — an order of
magnitude larger than any prior batch in this project (Phase B: 27;
presentation-sensitivity: 36; this pilot: 270) and disclosed here
explicitly as its own, separate, much larger authorization question,
not implied or minimized.

Degenerate-estimate floor (frozen now, applied only at power-calculation
time, never by the pilot itself - the pilot reports raw counts
unmodified, per its own §2 prohibited-use list):
  MIN_DISCORDANCE_FLOOR = 1 / n_calib = 1/30 ≈ 0.033
  If a comparison's raw d_hat = 0 (zero discordant pairs observed in 30
  instances), the required-n calculation uses MIN_DISCORDANCE_FLOOR in
  place of 0, rather than treating "0 observed" as "the true rate is
  exactly 0" (which would make the McNemar-based n calculation degenerate
  or undefined). This floor is a sizing convention, disclosed here before
  the pilot runs - it does NOT alter the pilot's own reported d_hat value,
  which is always the raw, unfloored observed rate.
```

**Both required inputs are now resolved, per §16.5**: the minimum
detectable effect is fixed at **0.05**, derived explicitly from §16.1's
cost matrix — see §16.5 for the derivation. The discordance rate has **no
prior data to draw on**: `pilot_experiment_specification.md`'s Step 1
plumbing run was never executed (confirmed by direct repository search).
§16.5's 30-instance calibration pilot is the only legitimate source, and
now supplies exactly two named quantities (`d_hat(2v3)`, `d_hat(2v4a)`),
never a single pooled number.

**No sample size is fixed by this document** — only the test, the MDE,
the two named comparisons, the floor convention, and the mechanism for
obtaining the two missing inputs (§16.5's calibration pilot, not yet
authorized).

## 15. Explicit non-goals and scope restrictions

- Not a claim that §1's fixed `K=3`, single-ordering scope covers all
  Jev workflows.
- Not a resolution of `score`'s intended semantics.
- Not, on its own, an externally-validated escalation policy.
- Not a ranking of strategies 1–4a in advance of running the comparison.
- Not an authorization for any API call.
- The `2·|noul−0.5|` transform's validity remains untested.
- Strategy 4b is not a policy candidate under any circumstance — its
  presence in this document is solely to bound how much value a
  currently-non-deployable signal *could* have, never to imply it should
  be deployed as-is.

## 16. §16 execution — every item frozen (Revision 4)

### 16.1 Numeric `cost(a, a*)` matrix

```
                  a*=accept   a*=escalate   a*=req_more_evidence   a*=defer
a=accept              0           10                6                 8
a=escalate            1            0                1                 1
a=req_more_evidence   1            1                0                 1
a=defer               1            1                1                 0
```

**Rationale, disclosed, not derived from data**: the diagonal is 0
(correct action, no cost). Off-diagonal costs are asymmetric by design —
silently **accepting** when the correct action was something else is
scored far worse (6–10) than any other mismatch (uniformly 1), because
that is the one failure mode with no downstream safeguard: an unnecessary
escalation/defer/evidence-request still gets caught by a human or a later
step, but a wrongly-accepted instance does not. Within the "accepted when
shouldn't have" row, severity is ordered `escalate`(10) > `defer`(8) >
`request_more_evidence`(6) — a disclosed judgment that missing a case
needing immediate human escalation is worse than missing a case needing
only a scheduled deferral, which is worse than missing a case that merely
needed more evidence gathered. Every mismatch among the three non-accept
actions is a uniform 1 — a deliberate simplification (no claim that these
three process errors are equally costly in reality; treating them
asymmetrically would be a second, unmotivated free parameter). `C_human`
(§6, placeholder +1/escalation) is added on top of this table, not
folded into it — `C_action` measures correctness only.

### 16.2 Task generator and `F`

**Domain**: extends the project's established software/ops-incident
domain (same family as `build_score_phase_b_manifest.py`'s severity
pool and Step 0A.2's subsystem-routing task) — a single, disclosed
domain, not a new one invented for this pass.

```
Node 1 (choice): "Which subsystem is most likely responsible for this
  incident?" - categories {network, database}. c_1* in {network,
  database}, always resolvable (no contested-routing case in this first
  pass - a disclosed scope restriction, not a claim that routing is
  never ambiguous).
Node 2 (noul): "Is this incident customer-facing?" - ground truth
  c_2* in {0, 1, unclear}. "unclear" is a construction-flagged
  indeterminate case (mirroring the score track's supplementary-
  contested-tie treatment) - items with c_2*="unclear" are excluded from
  noul's own C_2/marginal-accuracy computation (structurally non-
  scorable, not a noul failure), exactly as M-undefined items were
  excluded from score's primary gate.
Node 3 (score): "How severe is this incident?" - reuses the existing
  3-level criteria verbatim (cosmetic / degraded-with-workaround /
  blocking-no-workaround). c_3* in {0, 1, 2}.
```

**`F` table** (depends on `(c_2*, c_3*)` only — `c_1*`'s two values map
identically, since routing correctness is scored via `C_1` but does not
change which final action is correct):

```
c_3*=0 (cosmetic):
  c_2*=0          -> accept
  c_2*=1          -> accept
  c_2*=unclear    -> request_more_evidence
c_3*=1 (degraded):
  c_2*=0          -> accept
  c_2*=1          -> defer
  c_2*=unclear    -> request_more_evidence
c_3*=2 (blocking):
  c_2*=0          -> escalate
  c_2*=1          -> escalate
  c_2*=unclear    -> request_more_evidence
```

**Verification against §4.3's properties**:
0. *Input-independence*: the table above is a lookup over `(c_1*, c_2*,
   c_3*)` alone — no cell references, or could reference, any strategy's
   output, any node's live decision/confidence, or any evaluation-set
   result. It was written before §7's strategies were finalized and
   would not change if they were rewritten ✓.
1. *Totality*: all 9 `(c_2*, c_3*)` pairs (× 2 `c_1*` values = 18 total
   reachable combinations) are defined above — none missing.
2. *Nominal default*: `(c_1*=either, c_2*=0, c_3*=0) -> accept` ✓.
3. *Non-silent-escalation-suppression*: property 3 (§4.3) only forbids
   resolving to `accept` — it does not require any specific non-accept
   action. Every `c_2*=unclear` row resolves to `request_more_evidence`,
   never `accept`, regardless of `c_3*` ✓ (this takes precedence over
   `c_3*` at their intersection: `(c_2*=unclear, c_3*=2)` resolves to
   `request_more_evidence`, **not** `escalate` — a Revision 5 correction;
   an earlier draft of this line incorrectly claimed "every `c_3*=2` row
   resolves to `escalate` regardless of `c_2*`," which the table itself
   already contradicted, caught only when `F` was implemented and
   independently re-verified in code, not by re-reading the prose alone).
   Every remaining `c_3*=2` row (`c_2*∈{0,1}`) resolves to `escalate`,
   never `accept` ✓.

**Content-authoring rules for the actual sentence pool (specification
only — authoring itself is manifest-generation's job, per the agreed
pipeline, not this freeze)**: content-blind opaque sentence IDs (never
semantically prefixed, per every prior manifest's rule), seeded
deterministic assignment, zero reuse of any sentence from any prior
manifest in this project (checked by the same string-overlap method
`build_score_phase_b_manifest.py` used), one sentence pool per node type
sized to cover every `(c_1*, c_2*, c_3*)` combination the evaluation
population needs without reuse across items.

**Adapter (§1, §16.4)**: node 2's input state = the shared incident
evidence sentences + one appended, fixed-template sentence: `"Routing
determination: {node_1_decision}."` Node 3's input state = the same
evidence + `"Routing determination: {node_1_decision}. Customer impact
assessment: {'customer-facing' if node_2_decision==1 else 'not
customer-facing'}."` A fixed, disclosed string template — not
improvised per instance, and not re-derived from any live response
beyond substituting the upstream node's own already-computed decision.

### 16.3 Chain ordering

**`choice -> noul -> score`** — alphabetical order of primitive type
names. Disclosed as a deliberately arbitrary-but-mechanical rule
(lexicographic), chosen specifically *because* it carries no interpretive
bias about which primitive "should" go first — not chosen after seeing
any output, and not chosen to match this project's own historical
narrative order (Stage 0/1 characterized `choice`/`noul` before `score`,
which this ordering only coincidentally matches).

### 16.4 Deterministic adapter

Specified in full in §16.2 above (the two fixed sentence templates) —
not restated separately.

### 16.5 Power analysis — frozen procedure, one disclosed gap remaining

**Minimum detectable effect, derived from §16.1's cost matrix (not
guessed)**: a disclosed threshold of **0.05** (5 percentage points)
absolute improvement in `P(Y_decision=1)`. Rationale: given the cost
matrix's magnitudes (0–10), a 5-point shift in the rate of the *worst*
mismatch class (accepting when `escalate`/`defer` was correct, cost
8–10) moves expected `C_action` by roughly `0.05 × 9 ≈ 0.45` cost-points
per instance on average — a magnitude large relative to the matrix's own
scale (comparable to a full unit of the uniform-mismatch cost), and
therefore treated as the smallest effect worth the evaluation-set budget
to detect. This is a disclosed judgment call tied explicitly to §16.1's
numbers, not an unmotivated round number.

**Two conceptually distinct roles, kept explicit (Revision 4, per
audit)**: the cost matrix determines **what improvement matters
operationally** (the `0.05` MDE above is a practical-relevance judgment,
not a statistical quantity) — it does **not**, and cannot, determine the
discordance rate below, which is a separate, purely empirical input to
**statistical power/sample size**. These two numbers answer different
questions and are never substituted for each other:
`cost matrix -> operationally-relevant MDE`;
`calibration pilot -> empirical discordance rate -> required n, given
that MDE`.

**Test**: paired McNemar's exact test on `Y_decision` between a
candidate strategy (3 or 4a) and Strategy 2, over the shared-response
inputs (§2). Paired bootstrap CI on the difference in `P(Y_decision=1)`
reported alongside.

**The one genuine gap**: computing McNemar's required `n` needs the
paired **discordance rate** (fraction of instances where the two
strategies' `Y_decision` disagree) — and no prior data exists to supply
it. `pilot_experiment_specification.md`'s Step 1 plumbing run (which
would have been the natural source) was **never executed** — confirmed
by direct search of the repository; no Step 1 data of any kind exists.
Inventing a discordance rate here would be exactly the fabricated-effect-
size error review told me to avoid.

**Resolution — a scoped calibration pilot, not a guess**: a dedicated
`n_calib = 30` instance pilot (reusing Step 1's originally-specified
size as a disclosed, round starting constant — not as previously-
collected data, since none exists), whose **sole purpose** is measuring
the Strategy-2-vs-{3,4a} discordance rate.

**Exhaustive list of what the calibration pilot's output may NOT be used
for (Revision 4, per audit — stated explicitly, not left to inference)**:

```
The calibration pilot's result feeds ONLY the sample-size formula
(§14). It must NOT be used to:
  - modify the generator or F (§16.2)
  - modify the cost matrix (§16.1)
  - modify Strategy 3's weights or conflict rule (§7.3)
  - modify any deployable trigger's threshold (§8)
  - change the policy-development/evaluation split ratio (§16.6)
  - exclude any instance as "too difficult" or otherwise
  - alter Y_decision, Y_resolved, Δ_marginal, Δ_seq, or any other
    primary/secondary estimand definition (§5)
```

Any of the above, if done after the pilot, converts it into an
undisclosed additional development set and invalidates this protocol's
"no free parameters after seeing results" guarantee (§17) — this list
exists precisely so that boundary cannot be crossed by omission.

**Structurally separate artifacts, not folded into Step 2's dataset**:
the calibration pilot gets its **own** manifest, its own raw/parsed
response files, its own results file, and its own hash-lock — mirroring
`score_phase_b_manifest_hashes.json`'s pattern — named distinctly (e.g.
`workflow_calibration_pilot_manifest.json`, never merged into or
retroactively relabeled as part of the main Step 2 evaluation manifest,
even after both exist.

**This pilot has not been run, is not authorized by this document, and
is a separate, small, explicit go/no-go decision** — distinct from, and
prior to, authorizing Step 2's full evaluation run.

### 16.6 Policy-development/evaluation split

**30% policy-development / 70% evaluation**, a disclosed, standard
round-number convention (not tuned on any data) — applied to whatever
total evaluation-population size §16.5's calibration pilot ultimately
yields. If the calibration pilot itself is never run or the resulting
population is too small to support this split meaningfully, every
deployable trigger (§8) is reported as exploratory-only, per §8's own
fallback rule — restated here as the binding default if 16.5 is not
completed before a manifest is built.

**Status**: items 16.1–16.4 and 16.6 are fully frozen — no further
methodological decision remains in them. Item 16.5's *procedure* is
frozen; its *number* requires the disclosed 30-instance calibration
pilot, not yet authorized. **No manifest exists yet, and no evaluation-
run API call is authorized by this document.**

## 17. "No degrees of freedom remain" audit (Revision 4, new)

Per review's explicit request: every occurrence of *choose, select,
tune, optimize, threshold, weight, depending on results* (and close
variants) in this document was checked. Result:

| Term found | Location | Status |
|---|---|---|
| "threshold" (Strategy 2's `conf_product` cutoff) | §7.2 | Pinned: fixed on the policy-development set, never the evaluation set — value itself is a §16.6-scoped deliverable, not a live free parameter |
| "weight"/`w_choice`/`w_noul`/`w_score` | §7.3 | Pinned: `w_choice=1.0`, `w_noul=0.5`, `w_score∈{1.0,0.0}` — all named constants, fixed before any Step 2 data, none tuned |
| "threshold-selection procedure" | §9 | Descriptive reporting requirement (states what must be *disclosed* about a already-fixed threshold), not an open choice |
| "choose"/"chosen" (ordering, cost severity, MDE) | §16.1, §16.3, §16.5 | Each is a disclosed, rationale-attached constant, fixed in this revision — not left open, not tuned post-hoc |
| "select"/"selected" (composition strategies) | §0, §7 | Refers to which of 4 pre-registered strategies is *reported on*, not a strategy chosen after seeing results — §15 already bars ranking in advance and using observed data to pick a winner |
| "optimize"/"tune" | (none found as live instructions) | — |
| "depending on results"/"post hoc" | §7.2, §9, §14 | Every instance is a **prohibition** ("no post-hoc tuning," "no post-hoc threshold selection"), not a permission |

**One item flagged by this audit and already disclosed, not newly
found**: §16.5's calibration-pilot discordance rate is data that does
not exist yet — correctly a gap requiring a small, separately-authorized
pilot, not a free parameter smuggled into the strategy-comparison logic
itself. It cannot affect any strategy's action rule (§7) or any
threshold used in the actual evaluation (§8, §9) — it only sizes the
evaluation set.

**Audit conclusion**: no other free parameter remains. Per review's own
stated rule, **changing this protocol's methodology after observing any
Jev output — from the calibration pilot or otherwise — is a violation,
not an improvement**, and is not authorized by anything in this
document.

**No manifest exists yet, and no evaluation-run API call is authorized
by this document. The 30-instance calibration pilot (§16.5) remains a
separate, explicit, not-yet-requested go/no-go decision.**
