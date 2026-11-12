# Pre-registration: the full study on Gemini Decision 1

**Status:** written 2026-11-12, before any study data has been sent to the
model. A single synthetic, keyless request on 2026-11-12 returned HTTP
403 ("unregistered callers"); it carried no study data.

**Parents.** Everything not stated here is inherited unchanged:
- `openjev_crossmodel_preregistration.md` (Bugzilla workflow,
  hypotheses X1–X4);
- `independent_workflow_preregistration.md` (Kubernetes, K1–K3);
- `k8s_crossmodel_preregistration.md` (comparison models on Kubernetes,
  competence check as amended);
- the intervention (cost) test protocol.

## 1. Model and interface

**Model:** `gemini-decision-1` (Google), through the Decisions API, `POST
https://generativelanguage.googleapis.com/v1beta/decisions`.
- It answers typed `choice`, `noul` and `score` questions with
  probabilities and a confidence, which is Jev's interface.
- No dated version identifier is documented, so every response is
  stored with the request date and any version the API reports.

**Requests:**
- the body is `{model, input, questions}`;
- `input` is the exact state text the Jev runs used (same adapter,
  `node_state`);
- `questions` is the exact frozen question object, imported from
  `run_kernel_validation.QUESTIONS` (Bugzilla) and
  `run_k8s_workflow.QUESTIONS` (Kubernetes).

**Answer mapping:**
- Answers are stored unchanged.
- If `score` probabilities are keyed by level text rather than by index,
  they are mapped to indices 0, 1, 2 in criteria order, with the mapping
  recorded.
- Confidence is the API's own value.

**Access and data use:**
- **API key:** the authors' key, read from the environment and never
  logged.
- **Free tier:** Google may use submitted content to improve its
  products. Only public bug and issue texts are sent; they have already
  been privacy-scrubbed.

## 2. Repeats (decided by the smoke test, rule fixed now)

**The smoke test** sends 30 Bugzilla development bugs through the
workflow, with three real calls per node (270 calls).

**The rule:**
- **Deterministic:** if every set of three repeats returns identical
  probabilities (to 1e-6), the model is treated as deterministic. The
  full runs then make one call per node, recorded three times and
  flagged, as for the open models.
- **Otherwise:** three real calls per node, as for Jev.

## 3. Data

The same items as every other model, so results are paired by item:
- the 442 development and 500 held-out Bugzilla bugs;
- the 500 development and 582 test Kubernetes issues.

## 4. Primary hypotheses (Holm across all four, α = 0.05)

- **G-X1:** on the 500 held-out bugs, `E_dec`, fitted on Gemini's
  outputs for the 442 development bugs, ranks wrong actions better than
  Gemini's final-step confidence (as X1).
- **G-X2:** that AUROC exceeds 0.5 (as X2).
- **G-K1:** on the 582 Kubernetes test issues, the action-rule score
  beats final-step confidence (as K1, with d\* = 0.10).
- **G-K2:** the Kubernetes action-rule AUROC exceeds 0.5 (as K2).

**Pre-registered cost tests (a separate Holm family of two):** A1
against random review, and A1 against confidence-ranked review, at a 10%
budget on the held-out bugs, under the frozen cost matrix.

## 5. Exploratory, all reported

- **Characterization:** node agreement, confidence AUROC per node,
  severity confusion, fixed-threshold selectivity.
- **Estimator comparisons:** `E_all` against `E_dec`; Jev's frozen
  estimator applied to Gemini's outputs; action-rule ablations.
- **The implied-probability baseline.**
- **Label-shift analyses:** re-weighting, BBSE, and K3.
- **Cost:** cost sensitivity and the oracle decomposition.
- **The competence check:** above chance on every step.

## 6. Data quality and safeguards

**Failures:**
- A request that fails (HTTP error, including safety blocks) is retried
  at most twice, and every attempt is logged.
- An item with a failed node is dropped for Gemini and counted.
- The run stops if more than 1% of items fail.

**Running safely:**
- **Pacing:** at most 150 requests per minute, below the free tier's
  200, and at most 9,500 calls per run, below 10,000 per day. Runs are
  resumable.
- **Before any study data is sent:** a selftest and a dry run, with no
  calls.
- **Each live stage needs explicit flags,** and output files are never
  overwritten.

## 7. What would change the paper

**If G-X1/G-K1 hold,** the finding extends to a fifth decision model from
a third provider.

**If they fail** for a competent model, the paper must say that decision
patterns are not a general predictor across decision APIs.

**Every result is reported.**
