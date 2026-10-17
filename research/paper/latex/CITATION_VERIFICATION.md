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
| qwen2024qwen25 | Qwen2.5 model family (Qwen2.5-7B-Instruct used in the cross-model replication) | arXiv abstract page 2412.15115, fetched 2026-10-17 | Consistent. **Corrected** byline: group author "Qwen" precedes An Yang |
| olmo2024olmo2 | OLMo 2 model family (OLMo-2-7B-Instruct) | arXiv abstract page 2501.00656 (v1 31 Dec 2024), fetched 2026-10-17 | Consistent (title "2 OLMo 2 Furious"; Team OLMo, Walsh, Soldaini) |
| abdin2024phi3 | Phi-3 family (Phi-3.5-mini-instruct) | arXiv abstract page 2404.14219, fetched 2026-10-17 | Consistent |
| openjev2026 | Independent trained Jev-style open-weights model, served per its authors' instructions | Hugging Face model card (huggingface.co/openjev/openjev), read 2026-10-17 when deploying | Consistent. Cited only as the model's source; no performance claims taken from the card |
| gomez2026openjev | Unofficial architectural reconstruction of Jev with no trained weights | GitHub README (github.com/kyegomez/open-jev), read 2026-10-17 | Consistent. Cited only to explain why it was not evaluated |
| deusser2026jev | Jev 1.13.0 benchmarked zero-shot on 37 datasets, 346,009 requests; choice probabilities well calibrated, support selective prediction; binary probabilities rank well but sit poorly vs 0.5; training-tuned thresholds raised UNFAIR-ToS micro-F1 0.50→0.75; compared with two open models; single requests, no workflows or review costs | arXiv abstract 2609.37647, fetched 2026-10-17 | Consistent |
| meng2026jevaudit | Pre-registered calibration/accuracy audit of jev-1.13.0 vs DeBERTa zero-shot and two small OpenAI models on SST-2 and AG News | Zenodo record 10.5281/zenodo.22935043 (v1.0.0, 2026-09-24), fetched 2026-10-17 | **Full paper read 2026-10-17** (archive md5 21b3b8ef… matches Zenodo; `paper/JEV_PAPER.md`, read only, no code run). Claims cited: question form changes calibration (yes/no underconfident, ECE 0.091; choice 0.020); 71.6% of AG News answers at exactly 1.00 → 53 operating points; temperature scaling removes most miscalibration; no 5% automatic tier certified for Jev on AG News (0/2,000 splits). **Corrected:** our earlier text called it pre-registered; its Limitations state the analysis is exploratory, despite hashed protocol files in the archive |
| denney2026jev | Jev vs human coders, a commercial LLM and an open model on seven political-science replications; calibration better than the commercial LLM's token probabilities but not consistently better than the open model's | arXiv abstract 2610.06625 (v2), fetched 2026-10-17 | Consistent. Author order per arXiv (Denney, DiGiuseppe) |
| tang2026typed | Early evidence audit of 28 papers on typed decision models; no independent accuracy advantage yet for the typed readout; 14-item checklist | arXiv abstract 2609.32160, fetched 2026-10-17 | Consistent |
| geuter2026innerjev | Open instruction-tuned models give Jev-like decisions by reading answer-letter logits in one forward pass; LoRA recipe; OpenDecisions | arXiv abstract 2610.17205, fetched 2026-10-17 | Consistent. **Not** the source of the OpenJev checkpoint we ran (that model card links no paper) |
| park2026riskreview | Error risk is not review value under bounded review budgets; review-value ranking left less post-repair residual exposure than risk ranking at a 20% budget (TAT-QA/SciFact) | arXiv abstract 2609.07095 (SeT-LLM @ KDD 2026), fetched 2026-10-17 | Consistent |
| openjev2026 (updated) | Checkpoint provenance | HF download metadata on our Modal volume: commit b4a89f5884f3482a5e894b2e7ff01db8ea033726 for all files; model card read 2026-10-17 (org `openjev`, Apache-2.0 base, CC BY-NC weights, no paper, states independence from TypeSafe) | Pinned. Distinct from other projects named OpenJev |

**Not established by this record:**
- that the literature review is exhaustive;
- any claim that would require reading a cited paper's full text.
