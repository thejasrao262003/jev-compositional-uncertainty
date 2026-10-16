# Workflow Template Grammar — Specification (Draft 3, for independent audit)

Status: **draft for audit, not frozen.** No sentence from this grammar has
been assigned to any pilot or evaluation instance, and no API call has
been made. This spec replaces hand-written content for the second
calibration pilot and the Step 2 main run
(`workflow_uncertainty_composition_protocol.md`, Revision 10 audit
addendum). The executable form is `research/src/build_workflow_template_
grammar.py`. Its full expansion (4,235 units, Draft 3) is in `research/data/
characterization/workflow_template_grammar_units.json`, and its audit
results are in `research/results/workflow_template_grammar_audit.json`.

**Draft 3 (2026-10-16): fixes from a full review of Draft 2.** All
audits pass, including three new ones: 4,235 units, with every pool
covering `N_MAX = 1,260` at the proposition level.

1. **Audience leak, the critical fix.** Every node reads all three
   sentences. Draft 2's severity sentences said who was affected:
   "Users report that…" (151), "A user noticed that…" (143), "…for every
   user" (55), plus customer-coded subjects such as checkout, login,
   billing and shopping cart. Some routing names did too: user-accounts
   and billing databases, and "internal DNS resolvers". So in impact:0
   and impact:unclear instances the evidence contradicted `c2*`,
   especially in the level-1 cells, where `c2*` decides accept vs.
   defer.
   - **Fix:** routing and severity sentences are now audience-neutral.
     Only impact sentences say whether customers are affected.
   - **New audit A10** fails the build on any of about 40 audience
     words outside the impact pool.
2. **Capacity overclaim, corrected.** Draft 2 split total blocking
   failure into 4 classes, one of them distinct only by a time phrase.
   §5.2 calls that non-content, so under the spec's own rule Draft 2 had
   216–324 propositions, not the 432 it reported.
   - **Fix:** regrouped into 3 consistent classes: no service; every
     attempt errors; runs but the output is unusable. Functions were
     added to restore capacity.
3. **Routing-cue lexicon widened.** A5 now also covers region, traffic,
   endpoint, request path, webhook, API, URL, HTTP, upload and
   dispatcher (network), and cache, CSV, storage, records, archive,
   repository and logs (database). It caught 12 impact sentences, plus
   108 "region" mentions in blocking sentences. All fixed.
4. **Slot fit, new audit A11.** Combinations are now built only when
   they make sense together:
   - a workaround must address its failure (Draft 2 had at least 70
     misfits, such as "fail on large inputs, but a page refresh
     restores normal behavior");
   - a failure mode must fit its feature;
   - text defects apply only to elements that carry text;
   - "unusable output" applies only to functions that produce output.
5. **Surface form, new audit A12.** Fixed: plural subjects with
   singular verbs (13), "There has been escalations" (49), a doubled
   "from" (128), "the issue on" + a non-page surface (168), and doubled
   time references.
6. **Disclosed, not fixed:**
   - **Length differs by label.** Means: cosmetic 79 chars, degraded
     107, blocking 98; impact:0 108, impact:1 122, unclear 142. A model
     could use length as a shallow cue. Allocation balance doesn't
     remove it.
   - **Plausibility is improved, not guaranteed.** Some combinations
     are still stilted.

The audience leak was **also present in the first pilot's hand-written
sentences** (for example, "The billing service is rejecting all payment
methods" paired with not-customer-facing impact). It is disclosed in the
protocol.

**Draft 2 (2026-10-16): §5 is settled. Option A, proposition-level
uniqueness, is adopted and gating.**
- The generator now emits one sentence per proposition and fails closed
  on any undeclared signature slot or unmapped filler.
- The vocabulary was expanded so every pool covers `N_MAX = 1,260` at
  the proposition level.
- All audits pass: 3,987 units.

The grammar is a **freeze candidate**. It is frozen only after
independent review of this spec, the generator, and
`workflow_template_grammar_audit.json`.

*Draft 1 status line (superseded):* "One item is not ready to freeze:
§5, the definition of reuse … three of the eight pools can't supply
even `N = 738`."

## 1. Grammar dimensions

Each evidence sentence belongs to one pool and one construction value,
and is built from three **semantic slots** plus **surface slots**:

| Pool : value | Semantic slots (the key) | Surface slots |
|---|---|---|
| routing : network / database | component × metric × change | frame (3), time phrase (6) |
| impact : 1 (customer-facing) | source channel × customer segment × product surface | frame (3) |
| impact : 0 (not customer-facing) | component × isolation evidence × who confirmed | frame (3) |
| impact : unclear | component × unknown aspect × who could not confirm | frame (3) |
| severity : 0 (cosmetic) | UI element × defect × display context | frame (3) |
| severity : 1 (degraded, workaround) | feature × failure mode × workaround | frame (3) |
| severity : 2 (blocking, none) | function × failure × no-workaround scope | frame (3) |

An instance's evidence is three sentences, one each from routing, impact
and severity, joined in that order, as in the first pilot. §16.2's
adapter is unchanged.

## 2. Vocabulary

Every slot has a finite, fully listed vocabulary, given verbatim in the
generator. Nothing is sampled from a model at build time.

**Provenance, disclosed.** The vocabulary lists (about 250 short
phrases) were written by the assistant that is also implementing this
protocol, which is a language model, but **not Jev**. That's the same
provenance as the first pilot's 90 hand-written sentences. What differs
is the scale of authorship: the grammar's author writes a small list you
can review in full, and turning it into sentences is purely mechanical.
**Jev authored or rewrote no evaluation text, and must not** (audit
item 9).

## 3. How construction variables map to `c_1*`, `c_2*`, `c_3*`

`c_1*`, `c_2*` and `c_3*` are the pool values themselves: `routing:network`
means `c_1* = network`, `impact:unclear` means `c_2* = unclear`, and
`severity:2` means `c_3* = 2`. An instance draws one unit per pool for
its scheduled `(c_1*, c_2*, c_3*)`, and `a* = F(c_2*, c_3*)` (§16.2).

## 4. Semantic equivalence across variants, and its limits

**Within a pool and value, every combination entails that value's label
by construction.** Every network sentence names a network component and
metric. Every blocking sentence states total failure and that no
workaround exists. Every degraded sentence states a partial failure and
a workaround.

**What's not guaranteed: plausibility.** Combinatorial expansion yields
some combinations a person wouldn't write. For example, "SMS two-factor
codes … but an admin can still trigger them manually" is grammatical and
correctly labeled, but awkward. The label stays valid while realism
varies. This is one reason the first pilot's `d` doesn't transfer to
templated content, and why the second pilot measures `d_template`.

**Leakage audits (A5, A6), both passing.**
- Routing sentences contain cues from their own class only, and impact
  and severity sentences contain no routing cues. The first run caught 3
  real leaks, all fixed in the vocabulary: "ad-hoc **query** tool" in
  impact, "footer **link** text" in severity, and "query **latency**" (a
  network cue inside database sentences). It also exposed a bug in the
  audit itself: plurals such as "switches" and "proxies" didn't match.
  That is fixed too.
- Impact sentences assert no functional severity. The first run caught
  "end-user **crash** reports", now fixed. Customer-facing sentences now
  say customers reported "the issue on the checkout page" rather than
  "checkout failing". The latter would contradict a cosmetic severity
  label on the same instance, as some of the first pilot's hand-written
  sentences did.

**A residual, disclosed confound.** Routing sentences describe symptoms
with magnitudes ("an approximately tenfold increase in packet loss").
Those could push the `score` node's severity judgment upward regardless
of the severity sentence. This isn't eliminated, but the magnitude
classes are balanced by construction across instances (§6), so the
effect falls equally on all severity levels.

## 5. Definition of reuse — **SETTLED: Option A, proposition-level (Draft 2; classes regrouped in Draft 3)**

### 5.1 The rule

Two sentences **reuse a proposition** when they state the same atomic
claim: the same subject, predicate, arguments and conditions, with the
same polarity, even in different words. Sharing words or a template
frame doesn't count as reuse. Only sharing a proposition does, and
within a pool and value no proposition may appear twice.

In this grammar the claim is the tuple of a unit's **content slots**,
after paraphrases are merged into classes. Polarity and label are fixed
by `(pool, value)`, so a proposition is identified by `(pool, value,
signature)`. Propositions in different pools are distinct by
construction.

| Pool : value | Canonical signature (key order) | Dropped as non-content |
|---|---|---|
| routing | component (subject) · metric (predicate) · magnitude/shape class | frame, time phrase |
| impact : 1 | evidence channel · customer segment · product surface (subject) | frame |
| impact : 0 | component (subject) · evidence class | frame, who confirmed |
| impact : unclear | component (subject) · unknown-aspect class | frame, who could not confirm |
| severity : 0 | UI element (subject) · defect class · display context (condition) | frame |
| severity : 1 | feature (subject) · failure-mode class · workaround | frame |
| severity : 2 | function (subject) · failure class · no-workaround scope class | frame |

The paraphrase classes are listed verbatim in the generator's `SYN`.
Merges include:
- "a sharp spike" = "an abrupt jump";
- "is misaligned by a few pixels" = "sits one pixel off its grid";
- "stall after a long session" = "stop updating after a while";
- the three "no workaround" phrasings.

### 5.2 Edge cases, decided

| Case | Decision |
|---|---|
| Same claim, different wording | Reuse. One class |
| Opposite polarity | Not reuse. It can't occur within a pool, because the label fixes polarity |
| Different subject (component, function, element) | Not reuse |
| Same subject and predicate, different condition (e.g. display context) | Not reuse. The condition is a signature slot |
| Time phrase ("since the last deploy" vs "over the past hour") | Non-content. It changes neither label nor subject/predicate, so it is a surface slot |
| Who confirmed / who could not confirm | Non-content (nuisance). Attribution isn't a different claim (rejects Option B) |
| Same vocabulary, different claim | Not reuse. Classes are defined on slot meaning, not shared words |
| Fillers differing only by a time phrase ("has been down since the last deploy" vs "has stopped working") | Same class. Time phrases are non-content (Draft 3 regrouping) |
| A filler whose class is unclear | **Blocks the build** until it is declared (§5.3) |

### 5.3 Fail-closed enforcement

Every slot of every pool is declared exactly once:
- **SYN:** paraphrase classes, with every filler mapped;
- **IDENTITY:** each filler is its own proposition, reviewed as such;
- **NUISANCE:** dropped.

`check_signature_declarations()` stops expansion on any of: an
undeclared slot, a filler missing from its SYN map, or a stale map
entry. Both failure modes were probed and both block.

**Expansion.** All filler keys are shuffled with the fixed seed
(`workflow-template-grammar-v3` since Draft 3). The first key of each proposition is
kept, so paraphrases are spread across different propositions.

### 5.4 Capacity (Draft 3)

| Pool : value | Proposition keys (= units) | Needed at N = 1,260 (pilot quota + 6k or 9k) |
|---|---:|---:|
| routing : network / database | 672 / 672 | 645 |
| impact : 0 | 432 | 430 |
| impact : 1 | 448 | 430 |
| impact : unclear | 444 | 430 |
| severity : 0 | 648 | 430 |
| severity : 1 | 471 | 430 |
| severity : 2 | 448 | 430 |

**Blocking classes (Draft 3):**
- failure: {no service}, {every attempt errors}, {runs, output
  unusable; output-producing functions only};
- scope: {no workaround / fallback / alternative}, {can't be done
  manually}, {retrying doesn't help}, {previous version can't be
  restored}.

Capacity comes from 45 audience-neutral functions, 28 degraded features
(each with a failure-fit set) and 23 cosmetic elements (13 of them
text-bearing).

*Draft 2 table (superseded, and overstated for severity:2; see the
Draft 3 changelog):* 672 / 432 / 448 / 444 / 432 / 455 / 432.

### 5.5 Required at manifest time (not testable here)

1. **Whole-plan audit:** across the complete evaluation manifest and
   the second pilot, no `(pool, value, proposition key)` is used twice
   and none is shared between pilot and main. The build stops on
   violation.
2. **Residual correlation, disclosed:** distinct propositions still
   share subjects. For example, one impact:0 component appears with 6
   evidence classes. The Step 2 analysis must report H1/H2 again as a
   pre-specified **sensitivity analysis**, with randomization blocked
   by the severity subject and the impact component. Pre-specified
   rule: if a conclusion changes, that is reported, and the primary
   result stands as computed.
3. **Ceiling:** if Revision 12's sizing gives `N_eval > 1,260`, the
   build stops for a decision. The vocabulary isn't expanded after the
   pilot.

### Draft 1 record (superseded): the open decision as it was posed

What the generator currently enforces:
- **Exact-string uniqueness:** normalized for case, punctuation and
  whitespace, across all 4,128 units and against all 142 prior project
  sentences (A2). Passing.
- **Filler-level semantic-key uniqueness** within each pool and value
  (A3). Passing. Surface slots (frame, time phrase) don't count toward
  distinctness.

**Why that's not enough, as you said in audit item 5.** Many fillers are
synonyms: "a sharp spike" and "an abrupt jump"; "no workaround exists",
"there is no fallback path" and "no alternative route is available". Two
filler-distinct keys can state the same proposition. A9 therefore
recounts capacity at the **proposition level**: synonyms are merged into
classes, and "who confirmed" is dropped as nuisance.

| Pool : value | Filler keys | **Proposition keys** | Needed at N = 738 | Needed at N = 1,260 |
|---|---:|---:|---:|---:|
| routing : network | 672 | 576 | 384 | 645 |
| routing : database | 672 | 576 | 384 | 645 |
| impact : 0 | 448 | **32** | 256 | 430 |
| impact : 1 | 448 | 448 | 256 | 430 |
| impact : unclear | 448 | **32** | 256 | 430 |
| severity : 0 | 480 | 360 | 256 | 430 |
| severity : 1 | 480 | 480 | 256 | 430 |
| severity : 2 | 480 | **160** | 256 | 430 |

(`N = 738` is what `d = 7/30` would give under §6's rule. The real N
comes from `d_template`.)

At the proposition level, "not customer-facing" and "unclear" collapse
to 32 distinct propositions (8 components × 4 evidence classes), and
"blocking" to 160. The binding content in those pools is the
*component* or *function*, and there are too few of them. The larger
counts come from paraphrases and attributions.

**Why it matters statistically, not just stylistically.** Instances
are McNemar's sampling unit. If many instances carry the same
proposition in different words, their outcomes are correlated, the
effective sample size falls below N, and the test becomes anti-
conservative. So the reuse definition determines whether N actually
buys the power §14 claims.

**Options:**

| Option | Definition | What it requires | Risk |
|---|---|---|---|
| **A (recommended)** | Proposition-level uniqueness (A9 becomes gating) | Expand the *content* vocabularies: about 64 components each for impact:0 and impact:unclear, and about 16 functions for blocking, at N ≈ 738 (about 108 and 27 at N = 1,260) | More authoring, but still a finite, reviewable list, not free generation |
| B | Filler-level, but "who confirmed" counts as content | Impact:0/unclear reach 256, just enough at N ≈ 738; fails at larger N | Treats a weak distinction (who attested) as independence |
| C | Filler-level, as now | Nothing | The duplication your item 5 flagged; effective N below nominal |

## 6. Balanced allocation — exact integer rule (proposed; changes how §14's N is rounded)

*Revision 12 note:* `n_required` now comes from §14's cost-based sizing (`max(n(H1), n(H2))`), not from `d`. The rounding rule and the ceiling below apply unchanged.

**Proposed rule:** `N_eval = 18 · ceil(n_required / 18)`, which puts
exactly `N_eval / 18` instances in each of the 18 `(c_1*, c_2*, c_3*)`
cells. `N_eval` is never below `n_required`: at `d = 7/30`, `n_required =
733` becomes `N_eval = 738`. Per-value needs are then exact: `9k` routing
units per `c_1*` value and `6k` units per `c_2*` and per `c_3*` value,
where `k = N_eval / 18`.

This rounds §14's `N_final = n_required` *up* to the next exact-balance
point. It's a change to how N is set, so it's up to the audit to accept
or reject.

**Capacity ceiling:** `N_MAX = 1,260` (`k = 70`), which covers
`d_template` up to about 0.40. If `d_template` gives `n_required > N_MAX`,
the build **stops** and escalates as a decision. It does not silently
expand the vocabulary after the pilot.

**Second pilot schedule:** identical to the first pilot's (all 18 cells
once, plus 12 off-diagonal cells, for 30 instances). That needs 15
routing units per `c_1*` value and 10 per `c_2*` / `c_3*` value.

## 7. Separating the second pilot from the main run

The generator shuffles each pool-and-value's keys with a fixed,
disclosed seed (`workflow-template-grammar-v1`). The first 15 or 10 keys
are **reserved for the second pilot**, and the rest are the main-run
reserve. This is checked (A4): **zero** shared semantic keys and **zero**
shared texts between the two reserves. The second pilot will get its own
manifest, hash-lock and results files, per the protocol's
separate-artifact rule.

## 8. Independent label derivation

Each unit's label is the `(pool, value)` of the expansion loop that
built it, set *before* rendering. No code path reads a label back out of
the text (A8). For the first pilot, `F` was re-verified independently of
the protocol prose; the same verification applies here.

## 9. No Jev-generated text

See §2. Prohibited, and not used anywhere.

## 10. Distributional audit (A7)

*Draft 2:* the table below is the Draft 1 record. The current per-pool counts, frame balance and slot spread are in `workflow_template_grammar_audit.json` (A7), regenerated for Draft 2.

Main-reserve counts per pool and value, frame balance, and the spread
of each slot filler's counts:

| Pool : value | Units | Frame counts | Slot-filler count ranges (min–max per slot) |
|---|---:|---|---|
| routing : network | 657 | 219 / 219 / 219 | 53–56, 80–83, 90–96 |
| routing : database | 657 | 219 / 219 / 219 | 52–56, 80–84, 92–96 |
| impact : 0 | 438 | 146 / 146 / 146 | 53–56, 61–64, 52–56 |
| impact : 1 | 438 | 146 / 146 / 146 | 60–64, 53–56, 52–56 |
| impact : unclear | 438 | 146 / 146 / 146 | 53–56, 61–64, 54–56 |
| severity : 0 | 470 | 157 / 157 / 156 | 38–40, 58–60, 93–95 |
| severity : 1 | 470 | 157 / 157 / 156 | 38–40, 57–60, 91–95 |
| severity : 2 | 470 | 157 / 157 / 156 | 45–48, 56–60, 77–79 |

Balance is near-exact within every pool and value. The full per-cell
distribution of the *instances actually drawn* (subsystem × impact ×
severity × frame) can only be audited once allocation (§6) is applied,
so it is part of the manifest audit, not this one.

## What this draft does not authorize

It doesn't freeze the grammar (Draft 3 awaits independent review), assign any unit to an
instance, build a pilot or evaluation manifest, or authorize any API
call. **Next:**
1. Independent review of Draft 2.
2. Freeze, hash-locking the generator and the units file.
3. Build the second-pilot manifest with the §5.5 whole-plan audit.
4. Preflight.
5. Explicit authorization for its 270 calls.
