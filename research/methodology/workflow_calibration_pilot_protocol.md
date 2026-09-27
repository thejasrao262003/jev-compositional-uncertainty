# Workflow Calibration Pilot — Standalone Preliminary Experiment

Status: **design only — no manifest built, no API calls made or
authorized.** This is the `n_calib = 30` calibration pilot specified in
`workflow_uncertainty_composition_protocol.md` §16.5 (Revision 5) — a
**separate, standalone preliminary experiment**, not part of Step 2's
main evaluation run. This document does not reopen or modify that
protocol's methodology in any way; it only specifies how the pilot
itself is built and executed.

## 1. Sole purpose (restated, binding)

Measure **two** empirical discordance rates, per §14 (Revision 7) of
`workflow_uncertainty_composition_protocol.md` — never one pooled
number:

- `d_hat(2v3)`: fraction of the 30 instances where Strategy 2's and
  Strategy 3's `Y_decision` disagree.
- `d_hat(2v4a)`: fraction of the 30 instances where Strategy 2's and
  Strategy 4a's `Y_decision` disagree.

Both are computed from the same 30 shared-response instances (§4 below).
These are the only two missing inputs to §14's McNemar-based power
calculation. Nothing else.

## 2. Exhaustive prohibited-use list (verbatim from §16.5 — not restated with any weakening)

```
This pilot's result feeds ONLY the sample-size formula (§14 of
workflow_uncertainty_composition_protocol.md). It must NOT be used to:
  - modify the generator or F (§16.2)
  - modify the cost matrix (§16.1)
  - modify Strategy 3's weights or conflict rule (§7.3)
  - modify any deployable trigger's threshold (§8)
  - change the policy-development/evaluation split ratio (§16.6)
  - exclude any instance as "too difficult" or otherwise
  - alter Y_decision, Y_resolved, Δ_marginal, Δ_seq, or any other
    primary/secondary estimand definition (§5)
```

The pilot's result is preserved and reported **regardless of whether it
matches any expectation** — it is an input to a pre-specified
calculation, not a go/no-go judged on convenience.

## 3. Instance construction — same generator design as §16.2, fresh content only

Reuses the frozen task (choice: subsystem routing; noul: customer-facing
yes/no/unclear; score: severity), the frozen `F` table, and the frozen
adapter templates from `workflow_uncertainty_composition_protocol.md`
§16.2 **exactly** — this pilot does not define a different task. Only
the specific sentence content is new (fresh, content-blind, checked for
zero overlap with every prior manifest's text in this project, including
`build_score_phase_b_manifest.py`'s 39 sentences and its own recorded
13 prior-manifest sentences).

**Schedule (deterministic, seeded, disclosed)**: the 18 reachable
`(c_1*, c_2*, c_3*)` combinations (2 routing values × 9 `(c_2*,c_3*)`
pairs) are each used once, then a seeded shuffle of those 18 combinations
supplies 12 more (with repetition) to reach exactly 30 instances. No
combination is selected because of any expected or observed Jev
behavior — the schedule is fixed before any sentence is written.

## 4. Chain execution — sequential, per instance (differs structurally from Phase B / presentation-sensitivity)

Unlike the `score`-track studies (single node, flat call plan), this
pilot's node 2 and node 3 inputs genuinely depend on the *live* upstream
decision (§1's chain-dependency property), not a pre-computed one. Per
instance:

```
1. Call node 1 (choice), 3 repeats -> reduce to modal decision (§2).
2. Build node 2's state = shared evidence + "Routing determination:
   {node_1's actual modal decision}." (§16.2's adapter, applied to the
   REAL observed decision, not c_1*).
3. Call node 2 (noul), 3 repeats -> reduce.
4. Build node 3's state = shared evidence + both upstream decision
   sentences (§16.2's adapter).
5. Call node 3 (score), 3 repeats -> reduce.
```

**Budget**: 30 instances × 3 nodes × 3 repeats = **270 calls, fixed
before execution**. This is meaningfully larger than any single prior
batch in this project (Phase B: 27; presentation-sensitivity: 36) because
it is the first study to execute a genuine multi-node dependent chain
rather than a single primitive — disclosed explicitly, not minimized.
Retries are handled by `JevClient` per every prior stage's convention and
are not additional planned calls.

## 5. What gets computed (per instance, after data collection only)

- `c_1*, c_2*, c_3*` (already fixed at manifest-build time) and
  `a* = F(c_2*, c_3*)`.
- Strategy 1's action: `F` applied to the two *observed* node
  decisions (node 2, node 3) in place of `(c_2*, c_3*)` — a decision-only
  analogue of `F`, reusing its structure rather than inventing a second
  table (disclosed, mechanical choice).
- Strategy 2's action: `conf_product` (§7.2) vs. a **provisional**
  threshold of `0.5` — round, disclosed, explicitly **not** the frozen
  Step 2 threshold (which still awaits derivation on a real policy-
  development set); binary mapping `accept` if `conf_product >= 0.5`
  else `escalate`, the simplest realization of "naive confidence
  composition," used here only to get a runnable comparator for
  discordance measurement.
- Strategy 3's action (§7.3, exactly as frozen — no modification).
- Strategy 4a's action (§7.4a, exactly as frozen).
- `Y_decision` per strategy; pairwise discordance for every strategy
  pair, with `Strategy 2 vs. Strategy 3` and `Strategy 2 vs. Strategy 4a`
  reported as the primary quantities feeding §14.

## 6. Artifacts — structurally separate from Step 2 (binding, per §16.5)

`workflow_calibration_pilot_manifest.json`, `workflow_calibration_pilot_
manifest_hashes.json`, its own raw/parsed response files, its own
execution manifest — never named, merged, or retroactively relabeled as
part of Step 2's eventual main-evaluation manifest.

## 7. Authorization status

**Design and manifest-build steps below require no API calls.** The 270
live calls (§4) are a **separate, explicit go/no-go**, distinct from and
prior to Step 2's main evaluation run, and are **not authorized by this
document**.
