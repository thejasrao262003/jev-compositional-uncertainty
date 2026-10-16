# Workflow Uncertainty Composition Protocol — Step 2, Specified (Revision 12)

Status (Revision 12, 2026-10-16): primary tests are now H1 (2h vs R)
and H2 (5h vs 2h) on cost (§11); N is void until the second pilot.

Status (Revision 10): **no Step 2 evaluation manifest exists and no
Step 2 call has been made or authorized.** The first calibration pilot
(30 instances, 270 calls, hand-written content) has run, and its result
is committed at `5c16f4c`. This document is **Step 2** of
`pilot_experiment_specification.md`. It operationalizes
`compositional_reliability_baseline.md`'s `Δ`/`conf_product` statistics.

**Current pipeline position:** Revision 10 (this file) → freeze the
deterministic template grammar (`workflow_template_grammar_spec.md`) →
independent grammar audit → a second 270-call calibration pilot on
templated content → `d_template` → recompute `N` → freeze `N` → build
the evaluation manifest → manifest audit and preflight → explicit Step 2
authorization. **`N = 733` is void as of Revision 11** (§14): it was
measured under strategy definitions Revision 11 replaced. The second
calibration pilot re-measures the disagreement rate under the Revision 11
definitions.

## Changelog from Revision 11 — the composition question asked on top of the decisions (Revision 12)

Adopted 2026-10-16. Sources:
- `research/methodology/revision12_strategy5_proposal.md` (§1–§8);
- `research/results/mozilla_exploratory_analysis.md` (E1–E3).

**What was wrong with Revision 11's primary comparison:**
- Strategy 2 never reads the node decisions, while `a* = F(c2*, c3*)`
  escalates on the severity level. So 2 vs 4a mostly measured which arm
  is given the information `F` needs.
- Under `Y_decision`, escalating a wrong decision earns nothing, even
  though §16.1's frozen cost matrix prices exactly that as a remedy.
- It was found by post-hoc review of the descriptive Mozilla
  comparison, not from any Step 2 data.

**What changed:**
- **New arms (§7.6):**
  - **2h:** `F(decisions)`, plus escalating the `k` least-confident
    instances by `conf_product`.
  - **5h:** the same, ranked by Strategy 5's per-primitive rank
    average.
  - **R:** `k` random overrides; a reference, not a policy.
  - `k = min(⌈0.10·n⌉, #candidates)`.
- **New primary tests (§11, §14):**
  - **H1:** 2h vs R.
  - **H2:** 5h vs 2h.
  - Both are on per-instance cost `C_action + C_human` (§6, §16.1),
    Holm-corrected, family-wise α = 0.05.
- **Why R and not Strategy 1 as H1's comparator:** under cost, any
  escalation of a wrongly accepted case pays off, so 2h vs 1 would
  partly measure "escalating is cheap", not "confidence is
  informative". Random overrides of the same budget hold that constant.
  (This refines proposal §8, which named 1 vs 2h.)
- **2 vs 4a becomes secondary and descriptive,** with the confound
  disclosed wherever it is reported. Strategy 5 standalone is
  descriptive.
- **The paper is led by the empirical findings**
  (`research/results/findings_synthesis.md`). Step 2 tests the
  composition question.

**Constants:**
- **New:** `R_OVERRIDE = 0.10`, a review-workload design constant
  fixed in the proposal addendum before any Revision 12 test was
  computed on any data. It is not taken from the Mozilla override
  curve.
- **Reused, already frozen:** the cost matrix; `C_human = 1`; the MDE,
  as its cost-unit form from §16.5 (0.05 × 9 ≈ 0.45 per instance).
- **Randomization:** 10,000 draws, seed 20261016.

Code: `research/src/workflow_strategies_r12.py`, with a self-test.

**Mozilla, descriptive and disclosed, not decisive.** Using the frozen
code on the 202 Mozilla bugs:
- 2h cost **more** than random overrides (390 vs. an expected 357;
  randomization p ≈ 0.05);
- 5h was at chance (360);
- 5h beat 2h (sign-flip p ≈ 0.05).

None of this sets a constant or changes a definition. It does say that
a null or negative H1 is a live outcome.

**What it costs:**
- **The effect is bounded.** Only `k` instances can change, so the
  achievable per-instance effect is at most about `0.10 × 11`.
- **Power is limited.** The MDE of 0.45 cost points is a large effect
  inside that bound, so H1 and H2 are powered for large effects only.
  Smaller ones are reported as not detected, never as absent.
- **N is still void.** It is recomputed from the second pilot's
  per-instance cost-difference SDs (§14).

**Revision 12 disclosure: an audience leak in the first pilot's
content (2026-10-16).**
- **What leaked:** each node reads all three evidence sentences.
  Several of the first pilot's hand-written severity sentences signal
  customer impact on their own (e.g. "The billing service is rejecting
  all payment methods"), including in instances whose `c2*` is
  not-customer-facing.
- **What it affects:** the pilot's `noul` agreement, and through `F`
  its target actions in the level-1 cells. So its measured disagreement
  rate partly reflects contradictory evidence. It sets no current
  constant: N = 733 is already void, and Revision 12 re-sizes from the
  second pilot.
- **The fix:** the template grammar's Draft 3 makes routing and
  severity sentences audience-neutral and enforces it (audit A10).

## Changelog from Revision 10 — thresholds that did not transfer (Revision 11)

Full account, with every number: `research/results/threshold_transfer_finding.md`.

**What was found.** A 10% smoke test of the Mozilla real-data study (21
bugs, 252 calls) showed Strategies 2 and 4a escalating almost every
case. The first calibration pilot showed the same, milder and unnoticed,
because it was only used to estimate a disagreement rate. Diagnosed from
the strategies' **input signals only**, never labels or results:
- **4a's `choice ≥ 0.90` trigger fired on 90% of inputs in both
  datasets** (27/30 synthetic, 19/21 real). `choice` confidence is
  saturated, with a median of exactly 1.0 on both and only 4 distinct
  values on real text, so no cut-off on it can select a minority.
- **Strategy 2's fixed `conf_product ≥ 0.5` cut escalated 73% of
  synthetic instances** (close to the 67% a perfect accept/escalate
  policy would) **but 90% of real ones** (against 38%). Real text pulls
  `noul` toward the middle, which pulls the product down. A fixed cut in
  confidence units carries one content distribution's scale with it.
- **So Revision 10's only main comparison set two escalate-almost-
  always policies against each other.** On the smoke test both scored
  7/21, the share of bugs whose correct action is "escalate".

**What changed:**
- **Strategy 2** (§7.2) now escalates exactly `⌈q·n⌉` instances with the
  lowest `conf_product`. `q` is the share of target actions that aren't
  "accept": 6/9 by construction for this design, never fit to model
  output.
- **4a** (§7.4a) loses the `choice` trigger. It escalates on repeat
  instability, otherwise returns `F`.

Implemented in `research/src/workflow_strategies_r11.py`. The frozen
Revision 10 functions stay unchanged in `run_workflow_calibration_pilot.py`
as the record of what the first pilot ran.

**Why this isn't post-hoc tuning.** Neither change was chosen by
comparing strategy results, and neither was iterated. The trigger is
removed because of saturation alone, which needs no labels to show.
`q` comes from the design. The rank-based rule doesn't depend on the
confidence scale, which is what changed between synthetic and real
text.

**What it costs:**
1. **4a is no longer primitive-aware.** It is `F` plus repeat-
   instability escalation, almost the same as Strategy 1 (instability
   is rare: 2/30 and 0/21). The main comparison now tests **naive
   confidence composition at a matched escalation rate against decision-
   based composition** (§13).
2. **`N = 733` is void** (§14).
3. **Strategy 2 is batch-relative.** It ranks within the evaluated set.

The first calibration pilot's prohibited-use list is respected: the
change comes from the signals' saturation and transfer behavior, not
from the pilot's disagreement counts or outcomes. Whether that
distinction holds up is for review to judge; it is disclosed here so
review doesn't have to go looking for it.

## Revision 10 audit addendum — content generator changes, so N is provisional again

The independent audit of the Revision 10 file accepted the B(ii) change
and chose **Option 1** for the evaluation content:

- **Why.** §16.2's no-reuse rule requires about 2,199 unique evidence
  sentences for the main run. The existing generator is a fixed pool of
  90 hand-written sentences with no grammar, so any way of reaching
  that number is a new generation mechanism. The audit chose a
  deterministic template grammar. It rejected hand-writing about 2,199
  sentences, relaxing no-reuse, and any Jev-authored text.
- **Consequence for N.** `d(2v4a) = 7/30` was measured on hand-written
  content. The main run will use templated content, which is a
  different distribution, so carrying `7/30` over would be an untested
  transportability assumption at exactly the point where it sets N. A
  second 30-instance calibration pilot on templated content will
  measure `d_template`, and `N` is recomputed from that.
- **What makes N provisional.** Only the change of content generator.
  No Step 2 outcome exists or was observed. Strategy 2 (threshold 0.5),
  4a (triggers as in §7.4a), the cost matrix, `F`, MDE, α and power are
  unchanged and stay frozen through the second pilot.
- **Sequencing.** The grammar is frozen and independently audited
  **before** the second pilot runs. That pilot measures `d_template`
  for sizing only; it cannot be used to judge or revise the grammar.
- **Document cleanup the audit found.** §16.5, §16.6's status line and
  §17 still described the first pilot as not yet run and still used the
  two-comparison design. They now carry Revision 10 status notes, with
  the old text kept as a marked superseded record rather than deleted.

## Changelog from Revision 9 — design correction (B(ii)), not a post-hoc reduction of N

**Causal sequence, stated so it cannot be misread**: protocol inspection →
structural equivalence → design correction. *Not*: pilot result →
undesirable result → reduce N.

**The finding.** §7.3 zeroes `w_score` only when a *deployable*
presentation-risk trigger fires, but §8 defines no such trigger — its
only `score` flag is the diagnostic-only construction-class flag, walled
off from every real strategy. So `w_score = 1` on every instance, and
Strategy 3 computes `F(noul decision, score decision)`, which is Strategy
1's rule. The two differ only in the degenerate case where every `noul`
call fails (Strategy 3 escalates; Strategy 1 would pass an undefined
input to `F`), which did not occur in the pilot. The pilot's `1 vs 3 =
0/30` is consistent with this, but it is not the reason for the change;
the protocol text alone establishes the equivalence.

**The decision.** Strategy 3 was removed from the primary comparison set
because, under the pre-specified deployable-trigger configuration, its
presentation-risk suppression condition is never activated; consequently
its computation is identical to Strategy 1 over the evaluation domain.
Retaining 2-vs-3 as a primary comparison would duplicate an existing arm
rather than evaluate a distinct composition strategy. Strategy 3 is kept
only as a descriptive implementation-equivalence arm (§7.3).

**Propagated consequences:**

1. **One primary comparison, 2 vs 4a** (§11–§14). `N_final = 733`
   (§14), reusing the already-computed `n_required(2v4a)`; the `942`
   figure is superseded, not reinterpreted.
2. **Multiplicity — a latent gap, now moot, disclosed rather than left
   to vanish silently.** Revisions 7–9 had two primary comparisons, each
   at α = 0.05, with no multiplicity rule stated (family-wise error up to
   ≈0.10). With one primary comparison, α = 0.05 applies directly and no
   correction is needed.
3. **Strategy 2 and 4a pinned to exactly the definitions `d(2v4a)` was
   measured under.** `d(2v4a) = 7/30` came from the pilot's Strategy 2
   with threshold `0.5` and the pilot's 4a with no cross-node-
   disagreement rule. The main run must use those same two definitions,
   or the power calculation no longer describes the comparison it sizes.
   Both values were fixed before the pilot ran (pilot protocol §5; the
   runner's `cross_node_disagreement = False`), so this matches the main
   run to what was measured; it doesn't choose values after seeing
   results. Strategy 2's threshold is now frozen at `0.5` (§7.2, was "fit
   on a policy-development set"), and the cross-node rule is frozen as
   *none* for this task (§8).
4. **The policy-development split is removed** (§8, §9, §16.6). After
   item 3, nothing is left to fit: Strategy 3's constants, 4a's triggers
   (the `0.90` boundary comes from Step 0B), and Strategy 2's threshold
   are all fixed. So all 733 instances are evaluation instances. This
   also resolves an ambiguity §16.6 never addressed: under a 30/70 split,
   733 evaluation instances would have needed `ceil(733/0.7) = 1048` in
   total. Per §8's own fallback rule, the deployable triggers are
   reported as pre-specified exploratory rules, not calibrated ones.
5. **The claims matrix is re-scoped** (§13). The "primitive-aware"
   wording now refers to 4a, described precisely as `F`-composition plus
   the deployable escalation triggers (one of which, `choice` confidence
   ≥ 0.90, is primitive-specific). Strategy 3 appears in no claim.

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

**Shared-response design (frozen)**: all four strategies (1, 2, 3, 4a;
since Revision 10, 2 vs 4a is the sole primary comparison, and 1 and 3
are computed descriptively only —
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
π_2 (REVISION 11, binding): escalate exactly ceil(q * n) instances with
  the lowest conf_product in the evaluated set (undefined conf_product
  ranks lowest; ties broken by instance id); accept the rest.
  q = share of target actions != accept = 6/9 for this design (by
  construction from F and the balanced schedule; never fit to output).
  Code: workflow_strategies_r11.strategy_2_r11.
π_2 (Revision 10, SUPERSEDED - kept as the record of the first pilot):
  accept if conf_product >= 0.5, else escalate.
  Threshold FROZEN at 0.5 (Revision 10) - the exact value the
  calibration pilot used when it measured d(2v4a), fixed before that
  pilot ran. No longer fit on a policy-development set (removed, §8).
  Missing confidence on choice or score -> escalate.
```

**Disclosed reversal (Revision 10).** Before the pilot ran, its own
documents described `0.5` as *provisional* and "explicitly NOT the
frozen Step 2 threshold" (`workflow_calibration_pilot_protocol.md` §5;
the `STRATEGY2_PROVISIONAL_THRESHOLD` comment in
`run_workflow_calibration_pilot.py`). Revision 10 adopts that same value
as Step 2's frozen threshold. This reverses a pre-pilot statement, so it
is recorded here. The adoption doesn't depend on any pilot outcome
(`b`, `c`, `d`, any action): `d(2v4a)` describes Strategy 2 at `0.5`,
and sizing the main run with it while running Strategy 2 at any other
threshold would detach the power calculation from the comparison it
sizes. The pilot files are left unedited because they record what ran.
The main-run runner, when written, must define this constant as frozen
rather than provisional.

### 7.3 Strategy 3 — descriptive implementation-equivalence arm only (Revision 10; not a primary comparison)

**Status (Revision 10)**: Strategy 3 is **not** a primary comparison arm
and appears in no claim (§13). Under this protocol's deployable-trigger
set (§8), `w_score` is never zeroed, so the rule below computes
`F(noul decision, score decision)`, which is Strategy 1's rule. The only
difference arises when every `noul` call fails. Strategy 3 is still
computed and reported descriptively, as a record that the specified
primitive-aware arm is empty under this configuration. It does not stand
for primitive-aware composition as such. Making it distinct would
require a *deployable* `score` presentation-risk signal, which this
protocol does not have and which is out of scope for this pass. The text
below is kept as the Revision 6 record of how the rule was resolved.

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

### 7.4a Strategy 4a — Abstention-aware composition (deployable; the sole primary comparator, Revision 10)

```
π_4a (REVISION 11, binding):
  1. if the choice node OR the score node is repeat_unstable -> ESCALATE
  2. else -> F(noul decision, score decision), ESCALATE on undefined input.
  The choice-confidence trigger is REMOVED: choice confidence is
  saturated (median 1.0 on synthetic and real text) and the >= 0.90
  trigger fired on 90% of both, so it cannot select (Revision 11
  changelog). Code: workflow_strategies_r11.strategy_4a_r11.

π_4a (Revision 10, SUPERSEDED - the record of what the first pilot ran):
  1. if the choice node OR the score node is repeat_unstable (§2)
       -> ESCALATE    (noul has no modal-stability concept, §2, so it
                       does not enter this check)
  2. elif choice mean_confidence >= 0.90
       -> ESCALATE    (primitive-specific trigger, Step 0B boundary)
  3. elif cross-node disagreement
       -> ESCALATE    (rule frozen as NONE for this task, §8 - so this
                       branch never fires; kept for contract completeness)
  4. else -> Strategy 3's rule (§7.3), which here equals
       F(noul decision, score decision), ESCALATE on undefined input.
Uses only information a real deployed system observes at decision time.
```

**Revision 11:** with the `choice` trigger removed, 4a is no longer
primitive-aware. It is `F` plus repeat-instability escalation, almost
the same as Strategy 1. The paragraph below describes Revision 10.

What made 4a "primitive-aware" (Revision 10) was **only** its triggers. The
`choice`-confidence trigger is primitive-specific, and the repeat-
instability check reflects §2's measurement layer, which differs by
primitive. The composition step itself is `F`. That is the scope in
which §13's claims use the term.

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

### 7.6 Revision 12 arms — overrides on top of the decisions (binding)

```
Base: Strategy 1's action for every instance (F on the decisions).
Candidates: instances whose base action is not escalate.
k = min(ceil(R_OVERRIDE * n), #candidates), R_OVERRIDE = 0.10 (frozen).
2h: escalate the k candidates with the lowest conf_product (undefined
    ranks lowest; ties by instance id). Code: strategy_2h.
5h: escalate the k candidates with the highest Strategy 5 U (per-
    primitive uncertainty, admissibility rule MAX_MODAL_SHARE = 0.5,
    within-set rank percentiles; workflow_strategy5_proposal.py). If no
    signal is admissible, 5h is NOT COMPUTABLE and H2 is reported as
    such - never silently replaced. Code: strategy_5h.
R:  k candidates drawn uniformly at random. A reference distribution
    for H1, not a policy; its expectation is computed exactly.
Strategy 5 standalone (escalate ceil(q*n) by U, accept the rest):
    descriptive only.
```

All Revision 12 arms see exactly the inputs Strategies 1 and 2 already
use: single-call decisions and confidences, with no repeats beyond §2
and no labels. `R_OVERRIDE` sets the human-review budget and is
identical across 2h, 5h and R. That is the matched-budget property
Revision 11 got from `q`.

### 7.5 Information budget per strategy

| Strategy | Single evaluation? | Repeats accessed? | Native distribution? | Offline calibration data? | Can escalate? |
|---|---|---|---|---|---|
| 1 — Decision-only | Yes | No | No | No | Structural rule only |
| 2 — Naive confidence | Yes | No | Confidence scalar only | No | Threshold-based |
| 3 — Descriptive equivalence arm (Rev. 10) | Yes | No | Yes | No — fixed constants only | Fallback only |
| 4a — Abstention-aware (deployable, sole primary comparator) | Yes (base) | Yes — same repeats every node already has (§2), no extra calls | Yes | No — trigger thresholds fixed from prior findings (Step 0B), not fit to Step 2 data | Yes, primary role |
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
| `choice` confidence ≥ 0.90 | **REMOVED in Revision 11.** Fired on 27/30 synthetic and 19/21 real inputs; the signal is saturated at 1.0, so no cut-off on it selects a minority (`threshold_transfer_finding.md`) | Deployable in form, non-selective in fact | none (was 4a) |
| Cross-node disagreement | Task-specific joint-inconsistency rule. **Frozen as NONE for this task (Revision 10)**, matching the calibration pilot under which `d(2v4a)` was measured. For this generator, "inconsistent" would have to be defined over `choice`'s routing label, which `F` doesn't use (§7.3), so no principled rule exists | **Deployable** in form; inert here | 4a (never fires) |
| `score` construction-class flag | Item's *true* construction matches the presentation-sensitivity study's `MATERIAL`-flagged composition class | **Diagnostic-only** — requires generator-side knowledge no deployed system has | 4b (oracle) **only** |

**Data separation (Revision 10 — policy-development set removed)**:

```
Discovery set:            prior findings (Step 0B, the score track) -
                           already spent, not re-derived from Step 2 data.
Calibration pilot:         the 30-instance pilot - supplies d(2v4a) for
                           sizing ONLY (§14, §16.5 prohibited-use list);
                           its instances never enter the evaluation set.
Policy-development set:   REMOVED (Revision 10). Every threshold and
                           weight is now fixed before Step 2 data exists
                           (Strategy 2: 0.5; 4a: 0.90 from Step 0B, cross-
                           node rule = none; Strategy 3: fixed constants),
                           so a held-out fitting set would fit nothing.
Evaluation set:            all N_final instances (733 void, Rev 11) - scores the frozen
                           rules only, no post-hoc adjustment.
External validation set:   later, separate, out of scope here (§4.1).
```

Because no trigger is calibrated on Step 2 data, every deployable
trigger is reported as a **pre-specified exploratory rule**, not a
calibrated one, as §8's original fallback clause requires. The `score`
construction-class flag is reported **only** through 4b's oracle-ceiling
framing. Its diagnostic-only status is structural, not a matter of data
volume.

## 9. Risk–coverage–cost reporting — full frontier, no post-hoc threshold selection

No strategy's threshold is chosen after seeing evaluation-set outcomes.
As of Revision 10, every threshold is fixed before Step 2 data exists
(§7.2, §7.4a, §8); none is fit on any Step 2 subset.

**Required reporting per strategy, on the evaluation set**: full
empirical risk–coverage frontier (headline point = the frozen threshold,
e.g. Strategy 2's `0.5`; frontier itself is context, not license to
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

**Primary tests (Revision 12, binding).** Both use the per-instance
cost `C_action + C_human` (§6, §16.1). Holm–Bonferroni across the two,
family-wise α = 0.05.
- **H1, 2h vs R:** total cost of 2h against the distribution of total
  cost under `k` random overrides of the same candidates. Two-sided
  randomization test centred on the exact random expectation, 10,000
  draws, seed 20261016. It asks: does composed confidence pick better
  overrides than chance?
- **H2, 5h vs 2h:** paired per-instance cost differences. Two-sided
  sign-flip randomization test, same draws and seed. It asks: does
  per-primitive normalization pick better overrides than the raw
  product?

**Secondary, descriptive:**
- `Y_decision` for every arm;
- 2 vs 4a, with its information-access confound disclosed wherever
  reported;
- Strategy 5 standalone.

*Superseded (Revisions 10–11):* "Sole primary, powered comparison:
Strategy 2 vs. Strategy 4a, paired McNemar test on `Y_decision` at
α = 0.05."

**Reported descriptively, not as hypothesis tests**: Strategy 1 (decision-
only baseline) and Strategy 3 (implementation-equivalence arm, §7.3),
with the same metrics. Their comparisons carry no significance claim and
no power guarantee. Never 4b.

Metrics per strategy: `P(Y_decision=1)`; coverage, escalation rate,
`C_total` (§9); risk–coverage–cost frontier (§9); paired differences (§2's
shared-response design).

**A favorable mechanism-level finding is never, by itself, evidence that
any specific strategy in §7 fixes it** — that is this section's separate
comparison.

## 12. Evidence required before any escalation policy is considered validated

| Tier | Question | What would establish it |
|---|---|---|
| Verifier validity | Does the strategy code correctly implement its own frozen contract (§7)? | Exhaustive/mutation-tested unit verification, same discipline as `verify_score_gate_logic.py`, plus §2's bundle-isolation self-test |
| Strategy validity | Does 4a improve `P(Y_decision=1)` over Strategy 2 on the construction-defined evaluation set, using only thresholds fixed before Step 2 data existed? (Revision 10: 4a is the sole primary comparator; Strategy 3 is not tested.) | A properly powered Step 2 run (§14; `N` to be recomputed under Revision 11, since 733 is void) |
| External validity | Does that improvement hold on independently-validated ground truth? | The separate, later externally-validated task (§4.1) — not addressed here |

## 13. Outcome/claims matrix

| Result | Supports | Does not support |
|---|---|---|
| `Δ_marginal ≈ 0` and `Δ_seq ≈ 0`, strategies 1, 2, 4a similar `P(Y_decision=1)` | Per-node thresholds approximate this benchmark reasonably | Generalization beyond this construction-defined task |
| `Δ_marginal < 0` (Lin-et-al.-corrected) | Cascading failure, motivating a workflow-level policy | That any strategy in §7 fixes it |
| **H1: 2h beats R** (Revision 12 primary, Holm) | Composed confidence picks better overrides than chance, at a 10% review budget, on this benchmark | External validity; other budgets; other compositions of the signals |
| H1: 2h not different from R | No evidence that `conf_product` carries override-relevant information beyond the decisions, for effects ≥ 0.45 cost points | That it carries none. Smaller effects aren't ruled out |
| H1: 2h worse than R | `conf_product` ranks *away* from errors on this benchmark (anti-informative) | That confidence signals are harmful in general |
| **H2: 5h beats 2h** (Revision 12 primary, Holm) | Per-primitive normalization picks better overrides than the raw product | That 5h beats chance (that is H1's question for 5h, reported descriptively) |
| *(Revision 11, now secondary)* 4a beats 2 on `P(Y_decision=1)` (McNemar) | **Revision 11:** decision-based composition (`F` plus repeat-instability escalation) beats naive confidence-product composition **when both escalate at matched rates**, on this benchmark/evaluation set | External validity (§12); **anything about primitive-aware composition**, since 4a has no primitive-specific signal left (Revision 11); that confidence signals are useless, since only one composition of them (the product) is tested |
| 4a vs. 2 not significant | No evidence at this N that these deployable triggers improve on naive confidence composition, for MDE = 0.05 | That no escalation rule helps, or that effects smaller than 0.05 are absent |
| Strategy 3 ≡ Strategy 1 (descriptive) | That the specified primitive-aware arm is empty under this trigger configuration (§7.3) | Anything about primitive-aware composition's value. This is a statement about the protocol, not about the primitives |
| No strategy beats 1 | Confidence-like signals may not add value here | Confidence signals are worthless in general |
| 4b's ceiling ≫ 4a | The diagnostic-only signal is workflow-relevant *if it could be made deployable* | That 4a (the real policy) captures that value — it structurally cannot, by design |
| High instability/abstention rates | `score`/`noul`'s representation-validity gaps are workflow-relevant | The deployable triggers are well-calibrated in general |

## 14. Power analysis — binding sizing (Revision 10)

**Revision 12 sizing (binding; supersedes the 2-vs-4a procedure
below).**

```
Inputs from the second calibration pilot (templated content, 30
  instances), computed with the Revision 12 code:
  sigma_H1 = SD over instances of [cost(2h, i) - E_R cost(i)]
  sigma_H2 = SD over instances of [cost(5h, i) - cost(2h, i)]
MDE_cost = 0.45 per instance (§16.5's derivation, in cost units).
alpha = 0.025 per test (Holm's first step, conservative), power = 0.80.
n_required(H) = ceil(((z_{0.0125} + z_{0.80}) * sigma_H / MDE_cost)^2)
N_final = max(n_required(H1), n_required(H2)).
Floor: if a pilot sigma is 0, use sqrt(1/30 - 1/900) ~ 0.180, the SD
  of 30 values with exactly one |difference| = 1 (one discordant
  instance treated as observed, as MIN_DISCORDANCE_FLOOR did). Disclosed
  at sizing time; never used to judge outcomes.
Feasibility: if N_final x 9 calls exceeds what is authorized, report
  and stop for a decision. The MDE is never loosened to fit.
Prohibited: Mozilla's figures (any) as sizing inputs.
```


**Revision 11 (superseded by the Revision 12 sizing above): `N = 733` below is VOID.** It came from `d(2v4a)`
measured under the Revision 10 strategy definitions, which Revision 11
replaced (§7.2, §7.4a). The procedure stays binding. `N` is recomputed
from the disagreement rate the second calibration pilot measures under
the Revision 11 definitions.

**Binding, Revision 10 — the procedure below is binding; the `N = 733`
it produces is PROVISIONAL.** That figure was computed from `d` measured
on hand-written content, and the main run will use templated content
(see the Revision 10 audit addendum). `N` will be recomputed by this
same procedure from `d_template`, the second calibration pilot's
estimate. Everything else in this block stays frozen.

```
Primary comparison: ONE - Strategy 2 vs. Strategy 4a (§11). Strategy
  2 vs. 3 is no longer a primary comparison (§7.3, Revision 10
  changelog): structural equivalence of Strategy 3 to Strategy 1, not
  a pilot result.
Paired outcome: DISCORDANT iff Y_decision(2, i) != Y_decision(4a, i).
Test: McNemar's exact test, alpha = 0.05 two-sided, power = 0.80.
  One primary comparison, so no multiplicity correction applies (the
  two-comparison design in Revisions 7-9 never specified one - a
  latent gap, now moot).
Sizing input: d_hat(2v4a) = 7/30 = 0.2333 (b=2, c=5), from the executed
  calibration pilot, measured under exactly the Strategy 2 (threshold
  0.5) and 4a (cross-node rule = none) definitions the main run uses
  (§7.2, §7.4a).
MDE = 0.05 (§16.5, cost-matrix-derived design target - unchanged).
n_required(2v4a) = ceil(7.8489 * 0.2333 / 0.0025) = 733
N_final = 733 evaluation instances - all of them evaluation (no policy-
  development split, §8). Superseded: N_final = 942 (Revision 9), which
  was set by the now-dropped 2v3 comparison.
Implied main-run budget: 733 x 3 nodes x 3 repeats = 6,597 calls.
Record: research/results/workflow_step2_power_analysis_rev10.json
  (supersedes workflow_step2_power_analysis.json, which is preserved
  unmodified as the Revision 9 record).
```

**Superseded record (Revisions 7–9), kept for provenance, not binding:**

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

*(End of superseded Revisions 7–9 record. The binding sizing is the
Revision 10 block at the top of this section: `N_final = 733`, one
primary comparison. The 733-instance manifest does not yet exist, and no
Step 2 call is authorized by this document.)*

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

**Revision 10 note:** for the main run and the second calibration
pilot, the sentence content comes from the deterministic template
grammar in `workflow_template_grammar_spec.md`, which is pending its own
independent audit. The rules below still bind (content-blind IDs, seeded
assignment, zero reuse against every prior manifest), but that spec
makes "reuse" more precise. The first pilot's 90 hand-written sentences
were authored under the original rules below.

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

**Revision 10 status (binding):**

- **First calibration pilot: completed.** 30 instances of hand-written
  content, 270/270 calls, 0 retries or deviations; committed at
  `5c16f4c`.
- **Its sizing result:** `d(2v4a) = 7/30` (`b=2, c=5`). Under the single
  primary comparison (§14), that gave `N = 733` for the hand-written-
  content design.
- **N is provisional again, only because the evaluation content
  generator is changing** from hand-written sentences to the
  deterministic template grammar (Revision 10 audit addendum). No Step 2
  outcome exists or has been observed.
- **Second calibration pilot: planned, not run, not authorized.** It
  will use 30 templated instances (270 calls), be generated only after
  the grammar is frozen and independently audited, and follow the same
  prohibited-use list and separate-artifact rules as the first pilot
  (both reproduced below). It measures `d_template` for sizing only and
  cannot be used to judge or revise the grammar.

**Superseded record (Revisions 4–9), kept for provenance, not binding.**
Where the text below says the pilot "has not been run", or refers to
"Strategy 3 or 4a" or a two-comparison design, it describes the state
before Revision 10. The MDE derivation, the prohibited-use list and the
separate-artifact rule in it **remain binding**, and apply equally to the
second pilot.

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

~~**This pilot has not been run, is not authorized by this document, and
is a separate, small, explicit go/no-go decision**~~ *(superseded: the
first pilot ran, per the Revision 10 status above)*. The principle still
binds, and now applies to the second, templated pilot: each calibration
pilot is a separate, small, explicit go/no-go decision, distinct from
and prior to authorizing Step 2's full evaluation run.

*(End of superseded Revisions 4–9 record for §16.5.)*

### 16.6 Policy-development/evaluation split — REMOVED (Revision 10)

**Binding, Revision 10 (still binding in Revision 11): no split. All
`N_final` instances are evaluation instances** (733 at Revision 10, now
void; recomputed under Revision 11). Revision 11 keeps this: Strategy 2's
`q` comes from the design, so nothing is fit on a held-out set. There is nothing left to fit: every threshold and
weight is fixed before Step 2 data exists (§8's data-separation block).

**Why this does not violate the pilot's prohibited-use list (§16.5),
stated because that list explicitly forbids using the pilot to "change
the policy-development/evaluation split ratio"**: none of the pilot's
*outputs* (`b`, `c`, `d`, any `Y_decision`, any action) drove this
change. It follows from two things that don't depend on pilot outcomes.
(1) The structural finding that Strategy 3 ≡ Strategy 1, which the
protocol text alone establishes. (2) The requirement that the main run
use the *definitions* the pilot was built with — Strategy 2 threshold
`0.5` and cross-node rule *none*. Both were fixed before the pilot ran,
and were fixed so that `d(2v4a)` would describe the comparison it sizes.
Once Strategy 2's threshold is pinned, the split has no remaining
purpose. Whether this reasoning is sound is for the independent
Revision 10 audit to judge; it is disclosed here so the audit doesn't
have to go looking for it.

**Superseded (Revisions 4–9), kept for provenance**: **30% policy-development / 70% evaluation**, a disclosed, standard
round-number convention (not tuned on any data) — applied to whatever
total evaluation-population size §16.5's calibration pilot ultimately
yields. If the calibration pilot itself is never run or the resulting
population is too small to support this split meaningfully, every
deployable trigger (§8) is reported as exploratory-only, per §8's own
fallback rule — restated here as the binding default if 16.5 is not
completed before a manifest is built.

**Status (Revision 10)**: 16.1, 16.3, 16.4 and 16.6 are frozen. 16.2's
task, `F` and adapter are frozen; its sentence *content* now comes from
the template grammar, which is pending audit. 16.5's procedure is
frozen; its number (`N = 733`) is provisional until the second, templated
calibration pilot measures `d_template`. **No evaluation manifest exists,
and no Step 2 call is authorized by this document.** *(Superseded wording,
Revisions 4–9: "Item 16.5's number requires the disclosed 30-instance
calibration pilot, not yet authorized.")*

## 17. "No degrees of freedom remain" audit (Revision 4, new)

Per review's explicit request: every occurrence of *choose, select,
tune, optimize, threshold, weight, depending on results* (and close
variants) in this document was checked. Result:

| Term found | Location | Status |
|---|---|---|
| "threshold" (Strategy 2) | §7.2 | **Revision 11:** no numeric cutoff. A fixed escalation rate `q = 6/9`, taken from the design. (Revision 10's `0.5` is superseded.) |
| "threshold" (4a's `choice`-confidence trigger) | §7.4a, §8 | **Revision 11: removed** (saturated signal). Cross-node rule pinned as *none* |
| "weight"/`w_choice`/`w_noul`/`w_score` | §7.3 | Pinned: `w_choice=1.0`, `w_noul=0.5`, `w_score∈{1.0,0.0}` — all named constants, fixed before any Step 2 data, none tuned |
| "threshold-selection procedure" | §9 | Descriptive reporting requirement (states what must be *disclosed* about a already-fixed threshold), not an open choice |
| "choose"/"chosen" (ordering, cost severity, MDE) | §16.1, §16.3, §16.5 | Each is a disclosed, rationale-attached constant, fixed in this revision — not left open, not tuned post-hoc |
| "select"/"selected" (composition strategies) | §0, §7 | Refers to which of 4 pre-registered strategies is *reported on*, not a strategy chosen after seeing results — §15 already bars ranking in advance and using observed data to pick a winner |
| "optimize"/"tune" | (none found as live instructions) | — |
| "depending on results"/"post hoc" | §7.2, §9, §14 | Every instance is a **prohibition** ("no post-hoc tuning," "no post-hoc threshold selection"), not a permission |

**One item flagged by this audit and already disclosed, not newly
found (Revision 10 status)**: the discordance rate that sizes the
evaluation set. The first pilot measured it on hand-written content
(`7/30`). Because the main run will use templated content, the value
that will actually size N is `d_template`, from a second pilot not yet
run. Either way it is a sizing input, not a free parameter: it cannot
affect any strategy's action rule (§7) or any threshold used in the
evaluation (§8, §9). *(Superseded wording, Revisions 4–9: "data that
does not exist yet".)*

**Audit conclusion**: no other free parameter remains. Per review's own
stated rule, **changing this protocol's methodology after observing any
Jev output — from the calibration pilot or otherwise — is a violation,
not an improvement**, and is not authorized by anything in this
document.

**No evaluation manifest exists, and no Step 2 call is authorized by
this document. The first calibration pilot has run (`5c16f4c`). The
second, templated calibration pilot (§16.5) is a separate, explicit go/
no-go decision, not yet requested, and is gated on the template
grammar's independent audit.**
