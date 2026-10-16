# Citation verification record (2026-10-16)

For each citation: the claim the paper makes, what it was checked against,
and the outcome. "Abstract" means the arXiv abstract page or proceedings
record. Full texts were **not** read, so claims beyond the abstract
remain unverified.

| Key | Claim in the paper | Checked against | Outcome |
|---|---|---|---|
| xia2026propagation | Uncertainty must be studied across the compound system: intra-model, system-level, socio-technical propagation | Abstract (arXiv 2604.23505) | Consistent. Wording aligned to the abstract's three levels |
| zhang2026centraltendency | LLM raters compress ordinal scores toward the middle; prompt changes didn't remove it (clinical scoring) | Abstract (2605.16386) | Consistent |
| wang2026cordial | Few-label calibration of ordinal LLM outputs modelling flattening | Abstract (2609.29807) | Consistent |
| alves2024defer | Cost-sensitive deferral to multiple experts under workload limits | Abstract (2403.06906); venue per mlanthology (TMLR 2024) | Consistent. Softened from "formalizes our setting" to "closely related" |
| kittler1998combining | Classical fixed combination rules incl. the product rule; the product rule's justification assumes conditional independence | Bibliographic record (TPAMI 20(3):226–239, DOI 10.1109/34.667881) | Record verified. The conditional-independence statement is the standard reading of the paper's derivation, **not re-read in full text** |
| lin2026uqagents | Step-level calibration need not imply trajectory-level calibration | Abstract (2609.07395) | **Corrected.** Shown by counterexample (not empirically); experiments show step errors are coupled |
| kotte2026pasc | Errors compound across stages; independently calibrated stages lack joint coverage | Abstract (2605.18812) | **Corrected.** The earlier "compounds multiplicatively" isn't stated in the abstract |
| zhang2025modular | Composition across two stages | Abstract (2510.04406) | Consistent (two-stage sequential models) |
| chowdhury2019error | Error propagation through pipeline steps quantified | Abstract (1903.00405) | Consistent |
| zellinger2025early | Early abstention in LLM cascades | Abstract (2502.09054) | Consistent |
| bouchard2026escalation | Depth and deferral thresholds of cascades | Abstract v2 (2605.06350) | **Corrected.** Title changed in v2; the bib now cites v2 and notes v1's title |
| dou2026conformalcascade | Conformal cascades with distribution-free guarantees | Abstract (2607.25018) | Consistent |
| rabanser2025gatekeeper | Confidence tuning for cascades | Abstract (2502.19335) | Consistent |
| jung2025trust | LLM judges with escalation and provable human-agreement guarantees | Abstract; ICLR 2025 proceedings | Consistent. Authors and venue verified |
| zhang2026agentic | Calibrating agent trajectories | Abstract (2601.15778) | Consistent |
| duan2025uprop | Uncertainty propagation in multi-step agentic decisions | Abstract (2506.17419) | Consistent |
| geng2024survey | Survey of LLM confidence estimation and calibration | ACL Anthology 2024.naacl-long.366 | Consistent; pages added |
| babbar2022predsets | Prediction sets in human–AI teams | Abstract (IJCAI 2022 per arXiv comment) | Consistent |
| madras2018predict | Learning to defer | NeurIPS 2018 proceedings | Consistent. Title is the NeurIPS one ("Improving Fairness and Accuracy …") |
| typesafe2026confidence | Jev's `confidence` summarizes the output distribution (1 = all mass on one outcome, 0 = even); "one reasonable way to summarize a distribution, not the only one"; set thresholds on your own data; `noul` returns a single probability with no separate confidence | docs.typesafe.ai/confidence, fetched 2026-10-16 | Consistent. The page doesn't use the name "Jev"; the model name `jev-*` comes from the TypeSafe API (`jev-latest` → `jev-1.13.0`) |
| angelopoulos2021gentle, angelopoulos2024crc | Conformal prediction; conformal risk control | Literature-matrix abstract fetches | Not re-checked this pass |
| platt1999probabilistic, guo2017calibration, naeini2015bbq, elyaniv2010selective, geifman2017selective, geifman2019selectivenet, barlow1965reliability | Standard background | Literature matrix | Not re-checked this pass (classical, widely cited) |

**Not established by this record:**
- that the literature review is exhaustive;
- any claim that would require reading a cited paper's full text.
