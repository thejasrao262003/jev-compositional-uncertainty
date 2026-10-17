# Simulated ARR review: "Jev in a Multi-Step Workflow: Decisions Predict Failures, Not Which Reviews Pay"

**Reviewer stance.** Skeptical. Already knows the Jev single-request
audits (Deußer et al.; Meng; Denney & DiGiuseppe; Tang & Zheng) and
*Risk Is Not Review Value* (Park et al.).

**Written:** 2026-10-17 against `acl_main.pdf` (anonymous review build).
This is a self-review written to find weaknesses before submission. It is
not an external review and does not predict the real outcome.

## Summary

The paper chains Jev's three typed primitives into a bug-triage workflow
and asks two questions:
1. Which signals predict workflow failure?
2. Do those signals identify reviews worth paying for?

What it shows:
- **Prediction:** a frozen decision-feature estimator beats final-step
  confidence on 500 new bugs. The result replicates on four more models.
- **Intervention:** at a 10% review budget, no strategy beats no review.
  An oracle locates the value in wrongly accepted cases.
- **Stopped study:** a case-level score fails a pre-registered feasibility
  check, so the confirmatory study is stopped.

## Strengths

1. **Unusually disciplined methodology.**
   - Frozen estimators, hash-locked pre-registrations and Holm-corrected
     confirmatory tests.
   - Deviations are disclosed.
   - A binding stop rule is applied as written.
   - A traceability script regenerates every number.
2. **The prediction-vs-utility split is clearly operationalized** with a
   frozen cost matrix and an oracle bound. The oracle turns a negative
   result into a diagnosis: the value exists, identification fails.
3. **The cross-model design covers two kinds of model:** an independently
   trained Jev-style model and general models. The frozen-estimator
   transfer is a nice touch.
4. **The paper is honest about scope:** no priority claim, feasibility
   framed as non-confirmatory, models not ranked against each other.

## Weaknesses

**W1. The headline prediction result is close to structural (major).**
- The target `a*` and the action are both outputs of the same rule `F`.
  An estimator that knows the action, plus each action's historical error
  rate, will predict "action ≠ target" well, whatever the model's
  uncertainty quality.
- The paper's own finding that a class-frequency rule matches the
  estimator supports this reading.
- Final-step confidence is a different object, so "decisions beat
  confidence" is partly a comparison of unlike things.
- *Status:* now acknowledged in §6. A reviewer may still rate the
  contribution as modest.

**W2. The intervention result is largely arithmetic given the cost table
(major).**
- Break-even needs more than 18% of reviewed cases to be wrong accepts;
  about 14% of accepts are wrong under the natural mix. A weak ranker
  must lose.
- One budget and one author-chosen cost matrix. No sensitivity analysis
  shows whether the conclusion survives other reasonable cost ratios.
- *Status:* not addressed. Any sensitivity analysis would be new and
  exploratory, so it needs an explicit decision (see below).

**W3. Novelty against Park et al. is incremental (major for excitement).**
- "Risk is not review value" is already argued and shown.
- The paper's distinct angle is cost asymmetry *within* an action in a
  dependent typed workflow. That is a real but narrow addition.

**W4. The cross-model comparison is uneven (moderate).**
- The general models use the authors' readout and prompt.
- A readout bug was fixed after interim results were seen. It is
  disclosed and all models were re-run, but reviewers discount this.

**W5. The stopped study reads as unfinished work (moderate).**
- A reviewer may see §7's case-level analysis as a negative pilot rather
  than a result.
- The feasibility simulation reweights quota-sampled development bugs.
  Its assumption that Jev behaves within a (group, level) cell as it did
  on development bugs is untestable.

**W6. Pre-registration claims cannot be verified by a reviewer (moderate).**
- The registrations live in a private git repository, not a timestamped
  public registry.
- *Status:* the text now says the anonymized archive lists commit dates
  and hashes. A third-party timestamp would be stronger, but cannot be
  added retroactively.

**W7. Reference labels and the target are constructed (minor to
moderate).**
- Kernel severity is reporter-set, with "normal" as a default.
- `F` is the authors' rule.
- Disclosed in Limitations.

**W8. ACL fit (minor).**
- The work sits between NLP evaluation, software engineering and HCI
  deferral.
- It fits "LLM agents / evaluation", but some reviewers may send it to an
  SE or ML venue.

**W9. Proprietary-API reproducibility (minor).**
- Jev is hosted and versioned. Results may not hold for later versions.
- Raw responses are released, which mitigates this.

## Questions a reviewer would ask

1. Does the intervention conclusion hold under other cost ratios, for
   example a wrong accept costing 3–20 or review costing 0.5–2? (W2)
2. How does the decision estimator compare with an estimator given the
   *same* information plus per-step confidence? (Partly answered:
   `E_all − E_dec` is +0.004 to +0.078 in the results files, but this is
   not in the ACL text.)
3. Why not threshold the case-level score at zero expected saving, rather
   than spending a fixed budget? (Answer from the record: P > 0 covers
   about 194 cases per 500, so the cap binds and the outcome does not
   change.)
4. Can the pre-registration timestamps be independently verified? (W6)

## Likely scores (simulated)

| | Score |
|---|---|
| Soundness | 3.5 / 5. Strong process; W1 and W2 limit what the results mean. |
| Excitement | 2.5 / 5. Careful but narrow; a negative core result; incremental beyond Park et al. |
| Overall | Borderline main / likely Findings |

## Verdict on whether the contribution survives

**It partially survives.**
- **What survives a skeptical reading:**
  - a carefully pre-registered demonstration, replicated across models,
    that in a dependent typed-decision workflow the information that
    predicts failures does not identify the reviews worth paying for;
  - an oracle diagnosis of why.
- **What does not survive:** any reading of "decisions predict failures"
  as a strong standalone finding (W1).
- **What decides main track vs Findings:** most likely W2 (cost
  sensitivity) and W3 (positioning against Park et al.).

## Actions

**Done in the text, with no new analysis:**
- **W1:** a structural caveat added to §6.
- **W6:** a verification route for the pre-registrations stated in §1.

**Need your decision, because each would be new and exploratory:**
- **(a) Cost-sensitivity analysis (W2, Q1).** Recompute the frozen
  intervention arms under a pre-stated grid of cost ratios, on existing
  outputs only. It needs no API calls. It would be labelled exploratory
  and would not change the pre-registered result. This is the single most
  useful addition for reviewers.
- **(b) Report `E_all − E_dec` (Q2).** One sentence from existing,
  already-analysed results. It is low risk.
- **(c) A public timestamp for future work (W6).** This cannot be fixed
  retroactively for this paper.

**Release-side, still open:**
- Build the anonymized supplementary archive (scrubbed data, code, and a
  hash and commit-date manifest with no author identities).
- Remove identifying paths before packaging. Checked 2026-10-17: only
  two tracked files contain a local `/Users/...` path
  (`research/data/characterization/stage{0,1}_run_metadata.json`). Scrub
  them in the archive.
