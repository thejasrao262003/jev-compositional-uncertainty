# A mathematically explicit compositional-reliability baseline

Requested addition: a formal baseline against which "does calibration
compose across a workflow" can be measured quantitatively, rather than
argued qualitatively. This is a draft of Phase 5 material, pulled forward
because the pilot needs a concrete target statistic to compute, not just a
narrative claim. **This must be reconciled against PASC's actual formal
setup once its full text is read (in progress) — see the open question at
the end.**

## Setup

- Workflow = a sequence of decision nodes `i = 1..K` (chain topology first;
  branching is a later extension, not handled here).
- Node `i` receives input state `S_i`, which may depend on the outputs of
  nodes `1..i-1` (i.e., nodes are not independent by construction — this is
  what makes it a workflow and not K unrelated evaluations).
- Ground truth action `a_i*` is known by construction (synthetic generator).
- Jev's decision at node `i` is a random variable `A_i = A_i(S_i)`.
- **Local correctness:** `C_i = 1[A_i = a_i*]`.
- **Local accuracy:** `p_i = P(C_i = 1)` (marginal, over the input
  distribution).
- **Local confidence signal:** `conf_i` — the `confidence` field for
  `choice`/`score` nodes, or the `noul` value itself (or a transform of it,
  e.g. `2*|noul - 0.5|`, to be determined empirically in Step 0 — see
  `pilot_experiment_specification.md`) for `noul` nodes.
- **Local calibration:** node `i` is locally calibrated if
  `E[C_i | conf_i = c] ≈ c` for all `c` in the observed range. Measured via
  ECE/reliability diagrams per node (Step 0B).
- **Workflow success (strict version):**
  `W = 1[C_1 = 1 ∧ C_2 = 1 ∧ ... ∧ C_K = 1]`.
  A weaker, task-specific success predicate (e.g., tolerating a correctable
  error at one node) is a documented alternative to test later, not used in
  the pilot — the strict version is the more conservative, easier-to-reason-
  about default.

## The chain rule always holds — that is not the claim being tested

By the chain rule of probability, exactly:

```
P(W = 1) = Π_{i=1}^{K} P(C_i = 1 | C_1 = 1, ..., C_{i-1} = 1)
```

This is a tautology, not a finding — it holds regardless of whether
anything "composes well" or not. **The actual empirical question is whether
the conditional accuracy `P(C_i = 1 | C_1=1,...,C_{i-1}=1)` is well
approximated by the unconditional, marginal accuracy `p_i`** — i.e., whether
node `i`'s correctness is (approximately) independent of whether upstream
nodes were correct.

## The naive-independence baseline

Define the **naive-independence predicted workflow reliability**:

```
P̂_naive(W = 1) = Π_{i=1}^{K} p_i
```

This is exactly what a policy that sets a *per-node* confidence/accuracy
threshold *without accounting for cross-node dependence* implicitly assumes
about the resulting workflow-level reliability. It is directly measurable:
`p_i` comes from Step 0B's per-primitive accuracy estimates, and
`P̂_naive(W=1)` is just their product.

Define the **composition gap**:

```
Δ = P_observed(W = 1) - P̂_naive(W = 1)
```

measured directly from the Step 1/Step 2 workflow benchmark (empirical
fraction of instances with `W=1`, versus the product of the Step 0B
per-primitive accuracies for the same three primitive types used in the
workflow).

- `Δ ≈ 0`: node correctness is approximately independent across the
  workflow — per-node accuracy composes as naively expected. A per-node
  threshold policy is probably a reasonable approximation of a workflow-level
  policy.
- `Δ < 0` (observed reliability worse than the naive product predicts):
  errors are positively correlated across nodes — evidence of cascading
  failure (a wrong upstream decision makes downstream decisions more likely
  to also be wrong, beyond what independent per-node error rates would
  predict). This is the quantitative version of "calibration/accuracy does
  not compose," and is exactly what would justify a workflow-level (not
  per-node) escalation policy.
- `Δ > 0`: errors are negatively correlated (self-correcting) — would argue
  *against* needing a workflow-level policy beyond per-node thresholds, and
  is worth reporting honestly if observed rather than only looking for `Δ<0`.

## The confidence-weighted analogue (for the escalation-policy question specifically)

The accuracy-based `Δ` above tests whether *correctness* composes. A second,
related statistic tests whether the *confidence signals themselves*, if
naively multiplied, predict workflow-level reliability — this is the
statistic most directly comparable to PASC's coverage-compounding result
(pending confirmation of PASC's exact formalism):

```
conf_product = Π_{i=1}^{K} conf_i        (per workflow instance)
```

Bin workflow instances by `conf_product` and compare the empirical `P(W=1)`
within each bin to the bin's mean `conf_product` — a workflow-level
reliability diagram, directly analogous to the per-node reliability diagram
in Step 0B, but for the composed signal. Systematic overconfidence here
(empirical `P(W=1)` below the diagonal) is the direct workflow-level analogue
of PASC's joint-coverage degradation result, but computed in the
ECE/accuracy framing rather than the conformal-coverage framing — this is
the intended point of methodological differentiation from PASC, pending the
full-text comparison.

## Decision rule tie-in

`Δ` and the workflow-level reliability diagram above are the two statistics
that Step 2 (research pilot, not yet run) is designed to estimate with
enough sample size to be meaningful. See
`pilot_experiment_specification.md` §Decision rule for how these feed into
whether the larger paper is justified.

## Resolved: relationship to PASC and Lin et al. (full text now read)

- **Lin et al. (arXiv:2609.07395) directly validates the `conf_product`
  statistic above, formally.** Their Proposition 2 gives the exact
  correlated-coin-flip formula
  `P(C₁=1,C₂=1) = p₁p₂ + ρ√(p₁(1−p₁)p₂(1−p₂))` for two steps, which is
  precisely the accuracy-side version of the deviation `Δ` measures for a
  chain: under positive correlation between node correctness (the expected
  direction for cascading failure), the naive product `Π pᵢ` *underestimates*
  true joint success — so `Δ` should be interpreted with this correction in
  mind: a positive `Δ` (observed reliability *above* the naive product) is
  the expected sign under positive correctness-correlation per Lin et al.'s
  formula, not necessarily evidence of "self-correction." **This changes
  the interpretation guidance in the main body above** — re-derive the
  expected-sign reasoning from Prop. 2 before interpreting Step 2 results,
  rather than treating `Δ<0`/`Δ>0` as simply "bad"/"good."
- **PASC's method is not the same mathematical object as `Δ` or
  `conf_product`**, confirmed by full text: PASC takes a *max* over
  per-stage nonconformity scores (`max_k s_k`), not a *product* of
  per-stage confidences/probabilities. It targets joint *coverage*
  (a conformal-set guarantee) rather than joint *accuracy/success
  probability*. So this document's accuracy/ECE-framed statistics are a
  genuinely different (not merely re-framed) quantity from PASC's
  coverage-compounding result — the methodological differentiation from
  PASC holds up under full-text scrutiny, not just as a framing choice.
- Neither paper's method handles the case where different `i` in the chain
  have structurally different uncertainty representations (PASC assumes a
  uniform per-stage scalarization; Lin et al.'s formula is stated for
  homogeneous step-confidence scalars) — the `conf_product` statistic as
  defined above inherits this same limitation for `noul` nodes (whose
  `conf_i` must first be defined via a transform — see
  `pilot_experiment_specification.md` Gate D) and should be computed
  separately for chains with and without a `noul` node until Step 0B
  determines whether the transform is a reasonable proxy.
