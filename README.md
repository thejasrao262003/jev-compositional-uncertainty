# Compositional Uncertainty in Multi-Step AI Decision Workflows

This is a research project on one question: when a workflow chains
several AI decision primitives together, can it rely on their
uncertainty signals, and how should it combine them? The subject is
TypeSafe's Jev API, whose three primitives (`choice`, `score`, `noul`)
report confidence in structurally different ways.

## What's been found so far

- **The primitives fail in different ways.** `choice` has a
  high-confidence, low-accuracy subgroup (mean confidence 0.915,
  observed accuracy 0.333, n=6). `noul` was correct 24/24 times but
  reported confidence below its observed accuracy in every bin.
- **What `score` is meant to measure is not identified.** Under a fixed
  sentence order, its output tracked the highest severity present more
  than the majority or the average. That is discrimination among three
  candidate rules, not identification of what `score` intends.
- **`score`'s confidence moves when only the sentence order changes.** On
  one of three items, confidence varied by 0.173 across orderings, while
  the chosen severity stayed the same on all six comparisons.

Together these mean a workflow can't treat every primitive's
"confidence" as the same kind of probability. The current phase tests
ways of composing these signals across a three-step chain.

## Status

| Track | State |
|---|---|
| `choice` / `noul` characterization | Complete, frozen (`f480613`) |
| What `score` measures: validation study | Complete (`18e000b`) |
| `score` sensitivity to sentence order | Complete (`def7da7`) |
| Workflow composition, first calibration pilot | Run: 270 calls, 0 deviations (`5c16f4c`) |
| Workflow composition, template grammar | Draft 4 (after an independent review found Draft 3 not ready): one incident about one service per instance, value-neutral frames, every blocking sentence denies a workaround, N_MAX = 720. All 13 audits pass. Awaiting a 54-item human pass before freeze |
| Mozilla real-data validation (Tushar) | Full run complete: 2,424 calls, all clean; see `research/results/mozilla_validation_results.md` |
| Linux kernel replication | Full run complete: 2,160 calls, all clean. F1–F3 and the restated F4 replicate; the strength of "decisions beat confidences" does not. See `research/results/kernel_validation_results.md` |
| Findings synthesis | `research/results/findings_synthesis.md` (revision 2, after review); exploratory follow-up: `research/results/mozilla_exploratory_analysis.md` |
| Step 2 protocol | **Revision 12 adopted:** primary tests H1 (confidence overrides vs random) and H2 (per-primitive vs raw product) on cost |
| Threshold transfer finding → Revision 11 | Fixed thresholds didn't carry over from synthetic to real text; see `research/results/threshold_transfer_finding.md` |
| Main Step 2 evaluation | **Not built, not run.** Sample size void until the second calibration pilot |

## How the work is done

Every study follows the same sequence: write the protocol, have it
reviewed independently, freeze it, build and hash-lock the manifest,
run a dry-run preflight and self-tests, then get explicit authorization
before any live API call. Findings are scoped strictly to what the data
support. Superseded text is kept and marked as superseded, not deleted.

## Layout

```
RESEARCH_PLAN.md            running project log (every stage, in order)
research/
  methodology/              protocols and specifications
                            (current: workflow_uncertainty_composition_protocol.md)
  src/                      manifest builders, runners, verifiers, jev_client/
  data/characterization/    manifests, hash locks, raw/parsed API responses
  results/                  analyses, execution manifests, audit outputs
  literature/               literature matrix and gap analysis
```

## Reproducing

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# Everything below runs offline: no API key needed, no calls made.
python research/src/build_workflow_template_grammar.py              # expand and audit the grammar
python research/src/run_workflow_calibration_pilot.py --selftest    # runner self-tests
python research/src/run_workflow_calibration_pilot.py --mode dry-run
```

Live runs need `JEV_API_KEY` in a local `.env` file, which git ignores.
Each runner also requires explicit confirmation flags, for example
`--live --confirm-270-calibration-calls`.

## Scope

This is a construction-defined methodology study: the correct answers
come from how each item was built, not from independent human labels.
Nothing here claims general calibration, a validated escalation policy,
or behavior beyond the tested domain.
