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

---

# Second pass (2026-10-18), after the cost-sensitivity analysis

**State reviewed:** `acl_main.pdf`.
- **Length:** Limitations starts on page 7, so the content is within the
  8-page limit.
- **Anonymity:** no identifying text in the PDF and no author metadata.
- **Numbers:** 59 of 59 trace to result files.
- **Supplement:** builds, and its self-audit passes.

## Status of the first-pass weaknesses

| | First-pass issue | Now |
|---|---|---|
| W1 | Prediction result close to structural | Acknowledged in §6. The confidence ablation is now reported (+0.004 to +0.078). Confidence is redundant with the decisions for the Jev-style models and adds a little for the weaker general models. **Resolved as far as text can resolve it.** |
| W2 | Single cost table | Exploratory grid added (Table 4). **The answer is not reassuring for the headline.** Within a factor of 2 of the frozen costs, review pays for Jev, OpenJev and Qwen2.5 (and marginally for Phi-3.5). Only OLMo-2 is cost-robust. The paper now says this in the abstract, intro, §7, conclusion and Limitations. |
| W3 | Incremental on Park et al. | Unchanged. The sensitivity result *strengthens* the link: review value is governed by the cost ratio relative to achievable precision, which is Park et al.'s point made quantitatively for a typed workflow. |
| W4–W9 | | Unchanged; all disclosed. |
| W6 | Pre-registration not verifiable | The supplement now carries a manifest. It lists the commit and date of each protocol, verifies both `.sha256` locks, and shows that each protocol precedes its results and the first held-out API call. |

## New issue found in this pass

**N1. The title now overstates (major).**
- "Decisions Predict Failures, **Not Which Reviews Pay**" reads as a
  general claim.
- In the sensitivity grid at m = 2, the decision-based action rule is the
  *best* arm for Jev and saves 44–69 units against no review. There, the
  decisions *do* identify reviews that pay.
- Under the pre-registered costs the title is true. Across reasonable
  costs it is not.
- A reviewer who reads Table 4 will flag the mismatch.

Options:
- **(a, recommended)** "Jev in a Multi-Step Workflow: Predicting Failures
  Is Not the Same as Knowing Which Reviews Pay". This states the
  conceptual distinction the evidence supports, since error-rate rankings
  were the worst way to spend reviews.
- **(b)** Keep the title and rely on the qualified abstract. This carries
  more reviewer risk.

**N2. Small reversals could be over-read (minor).** Some grid cells
reverse by only a few units, for example Jev −2. The text says these lie
inside the original intervals. No change is needed.

**N3. The intervention section is now the densest part of the paper
(minor).** It holds three tables and a figure. If space is needed later,
the per-test table (Table 3) could move to the appendix. It is not needed
at the current length.

## Verdict, second pass

- **Soundness:** 3.5 → 4 out of 5. The sensitivity analysis and the
  manifest answer the two most likely soundness objections, even though
  one of the answers is unfavorable to the original framing.
- **Excitement:** about 2.5 out of 5, unchanged. The paper is now more
  honest, but no more surprising.
- **Overall:** borderline main track. Findings remains the most likely
  outcome.

The contribution that survives is this:
- in a dependent typed-decision workflow, the signals that predict
  failure rank errors by frequency, not cost;
- under the pre-registered economics they did not make review pay;
- whether review pays at all is set by the cost ratio relative to the
  precision those signals can reach.

That is coherent and defensible, provided the title stops implying that
review *never* pays.

## Remaining actions before submission

1. **Title decision (N1).** This is the only open content decision.
2. **Responsible NLP checklist.** Filled in on the submission form.
   Answers are available from the paper: models and versions, data
   licenses (public trackers), compute (one H100; API calls), AI-assistant
   use (declared under Ethical considerations), and the supplement.
3. **Upload the two supplementary zips.** Rebuild them from the final
   commit first.
4. **The ACL 2027 call page did not load.** Confirm the exact ARR deadline
   from the official site.

---

# Third pass (2026-10-18): changes made for rc2

- **N1, resolved.** The new title is "Jev in a Multi-Step Workflow:
  Predicting Failures Is Not Knowing Which Reviews Pay", applied in all
  versions. It states the distinction the evidence supports and no longer
  implies that review never pays.
- **Overclaims removed.** These statements contradicted the sensitivity
  grid:
  - the section title is now "Does prediction make review pay?" (it was
    "Prediction is not intervention utility");
  - the Fig. 5 caption, "every review arm costs more", the case-level
    conclusion and the Discussion are each qualified to the
    pre-registered costs or to the signals tested.
- **New limitation: reuse of the held-out set.** The intervention test was
  pre-registered after the held-out prediction results were known, and the
  sensitivity analysis is post hoc on the same 500 bugs. Neither is an
  independent confirmation.
- **Prose.** Contribution 2 and the conclusion are rewritten.
  Limitations is split into labelled paragraphs.
- **Checks.** 59 of 59 numbers trace. All four builds are clean.
  Limitations starts on page 7.

No open content decisions remain. Before submission:
- fill in the Responsible NLP checklist;
- upload the supplementary zips;
- confirm the ARR deadline.
