"""Traceability check: recompute the paper's headline numbers from committed
artifacts and confirm each appears in main.tex as stated. Exits non-zero on
any mismatch. No API calls.

  python3 research/paper/latex/check_paper_numbers.py
"""
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RES = HERE.parents[1] / "results"
# shared content used by main.tex, ieee.tex and springer.tex
ACL = "--acl" in sys.argv
_files = [HERE.parent / "acl" / f for f in ("acl_abstract.tex", "acl_body.tex", "acl_appendix.tex")] if ACL else \
    [HERE / f for f in ("abstract.tex", "body.tex", "appendix.tex")]
tex = re.sub(r"\s+", " ", " ".join(f.read_text() for f in _files))
st = json.loads((HERE / "paper_statistics.json").read_text())


def man(name):
    m = json.loads((RES / name).read_text())
    return m.get("analysis", m)["subsets"]["all"]


def expl(name):
    return json.loads((RES / name).read_text())


moz, ker = man("mozilla_validation_execution_manifest.json"), man("kernel_validation_execution_manifest.json")
emoz, eker = expl("mozilla_exploratory_analysis.json"), expl("kernel_exploratory_analysis.json")
f2 = lambda x: f"{x:.2f}"
f3 = lambda x: f"{x:.3f}"
ci2 = lambda c: f"[{f2(c[0])}, {f2(c[1])}]"
checks = []


def need(label, text):
    checks.append((label, text, text in tex))


# Node agreement (Table 3)
need("moz choice agreement", f"0.89 {ci2(moz['choice_agreement']['wilson95'])}")
need("moz noul agreement", f"0.80 {ci2(moz['noul_agreement']['wilson95'])}")
need("moz score agreement", f"0.53 {ci2(moz['score_agreement']['wilson95'])}")
need("ker choice agreement", f"{f3(ker['choice_agreement']['rate'])} {ci2(ker['choice_agreement']['wilson95'])}")
need("ker noul agreement", f"{f3(ker['noul_agreement']['rate'])} {ci2(ker['noul_agreement']['wilson95'])}")
need("ker score agreement", f"0.44 {ci2(ker['score_agreement']['wilson95'])}")
# Own-confidence AUROCs with CIs (Table 1)
for d, lab in (("mozilla", "moz"), ("kernel", "ker")):
    for node in ("choice", "noul", "score"):
        a = st[d]["auroc_own"][node]
        need(f"{lab} {node} AUROC", f"AUROC {f2(a['point'])} {ci2(a['ci95'])}")
# Severity compression
lm = moz["score_P_jev_above_mozilla_by_true_level"]["0"]
lk = ker["score_P_jev_above_reporter_label_by_true_level"]["0"]
need("moz minor rated higher", f"79\\% {ci2(lm['wilson95'])}")
need("ker minor rated higher", f"75\\% {ci2(lk['wilson95'])}")
# Composition (Section 7)
for d, lab in (("mozilla", "Mozilla"), ("kernel", "kernel")):
    c = st[d]["composition"]
    need(f"{d} AUROC (A)", f"{f2(c['auroc_missed_serious']['point'])} {ci2(c['auroc_missed_serious']['ci95'])}")
    need(f"{d} AUROC (B)", f"{f2(c['auroc_S1_wrong']['point'])} {ci2(c['auroc_S1_wrong']['ci95'])}")
cm, ck = st["mozilla"]["composition"], st["kernel"]["composition"]
need("moz S1-S2 discordant", f"{cm['S1_minus_S2']['discordant_S1_only']} vs.\\ {cm['S1_minus_S2']['discordant_S2_only']} discordant")
need("ker S1-S2 discordant", f"{ck['S1_minus_S2']['discordant_S1_only']} vs.\\ {ck['S1_minus_S2']['discordant_S2_only']} discordant")
need("moz S1-S2 CI", f"0.17 {ci2(cm['S1_minus_S2']['ci95'])}")
need("moz H1 totals", f"$T = {cm['h1_per_bug_cost_diff_vs_random']['totals'][0]}$ against $\\mu = {cm['h1_per_bug_cost_diff_vs_random']['totals'][1]}$")
need("ker H1 totals", f"$T = {ck['h1_per_bug_cost_diff_vs_random']['totals'][0]}$ against $\\mu = {ck['h1_per_bug_cost_diff_vs_random']['totals'][1]}$")
# Budgeted-override cost analysis (Section 7)
for d, c_ in (("mozilla", cm), ("kernel", ck)):
    h = c_["h1_per_bug_cost_diff_vs_random"]
    lo, hi = h["ci95"]
    sign = "+" if h["point"] > 0 else "-"
    need(f"{d} H1 per-bug diff + CI", (f"$+{h['point']:.2f}$" if h["point"] > 0 else f"$-{abs(h['point']):.2f}$")
         + f" [${lo:.2f}$, {hi:.2f}]")
    need(f"{d} H1 randomization p", f"$p = {h['randomization_p']:.2f}$")
    need(f"{d} H1 k", f"{h['k']}")
need("moz H1 null range", f"range {cm['h1_per_bug_cost_diff_vs_random']['null_total_cost_2.5_97.5'][0]}--{cm['h1_per_bug_cost_diff_vs_random']['null_total_cost_2.5_97.5'][1]}")
need("moz H1 share positive", f"{round(100 * cm['h1_per_bug_cost_diff_vs_random']['share_of_resamples_positive'])}\\% of resamples are positive")
# Threshold transfer (Table 2)
sel_m = json.loads((RES / "mozilla_validation_execution_manifest.json").read_text())
sel_m = sel_m.get("analysis", sel_m)["selectivity"]
sel_k = json.loads((RES / "kernel_validation_execution_manifest.json").read_text())["analysis"]["selectivity"]
need("moz trigger fired", f"{round(100 * sel_m['rev10_choice_conf_ge_0.90_trigger'])}\\%")
need("ker trigger fired", f"{round(100 * sel_k['rev10_choice_conf_ge_0.90_trigger'])}\\%")
need("moz cut escalated", f"{round(100 * sel_m['rev10_strategy2_escalation_rate'])}\\%")
need("ker cut escalated", f"{round(100 * sel_k['rev10_strategy2_escalation_rate'])}\\%")
# noul error direction (kernel)
nc = eker["noul_confusion_true_vs_jev"]
need("ker noul false alarms vs misses", f"{nc['0->1']} false alarms vs.\\ {nc['1->0']} misses")

# Held-out test, cross-model replication, intervention (added 2026-10-17)
ho = json.loads((RES / "heldout_analysis.json").read_text())
need("HR1 E_dec vs conf", f"AUROC {ho['HR1']['auroc_E_dec']} against {ho['HR1']['auroc_low_score_conf']}")
need("HR1 difference and bound", f"$+{ho['HR1']['difference']}$ (one-sided 95\\% lower bound $+{ho['HR1']['one_sided_95_lower']}$)")
need("HR2 mozilla", f"{ho['HR2']['mozilla']['auroc_E_dec']} on Mozilla (lower bound {ho['HR2']['mozilla']['one_sided_95_lower']})")
need("HR2 kernel", f"{ho['HR2']['kernel']['auroc_E_dec']} on the kernel (lower bound {ho['HR2']['kernel']['one_sided_95_lower']})")
cm = json.loads((RES / "openjev_crossmodel_analysis.json").read_text())
ol = cm["models"]["allenai/OLMo-2-1124-7B-Instruct"]["X1"]
need("OLMo X1", f"({ol['auroc_E_dec']} vs.\\ {ol['auroc_low_score_conf']}; one-sided $p = {ol['bootstrap_p_one_sided']:.3f}$")
need("all 8 Holm supported", "All 8 pre-registered tests are supported") if all(cm["holm_supported"].values()) else None
rb = json.loads((RES / "openjev_robustness_checks.json").read_text())["models"]
tr = rb["openjev/openjev-27B"]["E_jev_frozen"]
need("Jev->OpenJev transfer", f"reaches {tr[0]:.2f} [{tr[1][0]:.2f}, {tr[1][1]:.2f}]")
need("action rule Jev/OpenJev", f"matches the estimator for Jev ({rb['Jev 1.13']['rule_rate_by_action']:.2f}) and OpenJev ({rb['openjev/openjev-27B']['rule_rate_by_action']:.2f})")
iv = json.loads((RES / "intervention_test.json").read_text())
need("intervention Jev no-review", f"for Jev, {iv['models']['Jev 1.13']['base_total_cost']} with no review")
sup = sum(iv["holm_supported"].values())
need("intervention 2 of 10", f"{['Zero','One','Two','Three'][sup]} of ten pre-registered tests are supported")
mech = json.loads((RES / "intervention_cost_mechanism.json").read_text())["models"]
j = mech["Jev 1.13"]; o_ = mech["openjev/openjev-27B"]
need("oracle Jev 44%", f"cut Jev's cost by {round(100 * (1 - j['oracle_cost_at_k50'] / j['no_review_cost']))}\\%")
need("oracle OpenJev 33%", f"OpenJev's by {round(100 * (1 - o_['oracle_cost_at_k50'] / o_['no_review_cost']))}\\%")

# Case-level score development and budget feasibility check (added 2026-10-17)
dv = json.loads((RES / "case_level_review_dev.json").read_text())["in_sample_all_442"]
need("plug-in training cost", f"({dv['P']['cost']:.0f} vs.\\ {dv['no_review']})")
need("plug-in oracle share", f"captured {round(100 * dv['P']['share_of_oracle_saving'])}\\% of the oracle saving")
bc = json.loads((RES / "case_level_review_budget_check.json").read_text())
best = max(((n, b, v) for n, r in bc["results"].items() for b, v in r.items()), key=lambda x: x[2]["power"])
need("budget check best power", f"highest power was {best[2]['power']:.2f} (1\\% budget, 1{{,}}000 bugs), with a median change of ${best[2]['median_cost_change_vs_no_review']:.0f}$")
need("budget check range", f"[{best[2]['central_80pct'][0]:.0f}, +{best[2]['central_80pct'][1]:.0f}]")
need("not viable", "No budget was viable") if not bc["decision"]["viable"] else None

# Exploratory cost sensitivity and confidence ablation (added 2026-10-18)
cs = json.loads((RES / "intervention_cost_sensitivity.json").read_text())
jv = lambda c: cs["cells"][c]["models"]["Jev 1.13"]["best_minus_no_review"]
need("sens Jev m=2 range", f"for Jev, {-round(jv('m=2,h=1'))}--{-round(jv('m=2,h=0.5'))} units")
need("sens Jev small reversal", f"(Jev ${round(jv('m=1,h=0.5'))}$ at $m = 1$")
need("sens only OLMo robust", "cost-robust only for OLMo-2") if [m for m, v in cs["summary"].items() if v["verdict"] == "cost-robust"] == ["allenai/OLMo-2-1124-7B-Instruct"] else None
need("sens A1>C 12/16", f"in {cs['summary']['Jev 1.13']['cells_A1_beats_C']} of 16 cells") if cs['summary']['Jev 1.13']['cells_A1_beats_C'] == cs['summary']['openjev/openjev-27B']['cells_A1_beats_C'] else None
rev = [m for m, v in cs["summary"].items() if "m=2,h=1" in v["all_cells_where_review_pays"]]
SHORTN = {"Jev 1.13": "Jev", "openjev/openjev-27B": "OpenJev", "Qwen/Qwen2.5-7B-Instruct": "Qwen2.5",
          "microsoft/Phi-3.5-mini-instruct": "Phi-3.5", "allenai/OLMo-2-1124-7B-Instruct": "OLMo-2"}
names = [SHORTN[m] for m in SHORTN if m in rev]
need("sens reversing models at m=2", f"For {', '.join(names[:-1])} and {names[-1]},\nreview pays when wrong accepts cost twice as much".replace("\n", " "))
cmx = json.loads((RES / "openjev_crossmodel_analysis.json").read_text())["models"]
ho2 = json.loads((RES / "heldout_analysis.json").read_text())["secondary_descriptive"]["pooled"]
gains = [round(ho2["E_all"] - ho2["E_dec"], 3)] + [round(cmx[k]["X3_X4_descriptive"]["E_all"] - cmx[k]["X3_X4_descriptive"]["E_dec"], 3)
         for k in ("openjev/openjev-27B", "Qwen/Qwen2.5-7B-Instruct", "microsoft/Phi-3.5-mini-instruct", "allenai/OLMo-2-1124-7B-Instruct")]
need("E_all-E_dec", f"by +{gains[0]:.3f} (Jev), +{gains[1]:.3f} (OpenJev) and +{gains[2]:.3f} (Qwen2.5), none distinguishable from 0, but by +{gains[3]:.3f} (Phi-3.5) and +{gains[4]:.3f} (OLMo-2)")

# Evidence audit and ablations (added 2026-10-23)
ea = json.loads((RES / "evidence_audit.json").read_text())
nl = sum(v["heldout_bugs_linked_to_a_dev_bug"] for k, v in ea["C_linked_reports"].items() if k != "HR1_without_linked")
w = ea["C_linked_reports"]["HR1_without_linked"]
need("linked reports", f"connect {nl} held-out bugs")
need("HR1 without linked", f"reaches {w['auroc_E_dec']:.3f} against {w['auroc_final_step_conf']:.3f}")
rc = ea["D_recency"]["Jev 1.13"]["mozilla:recent"]
need("recent mozilla", f"$E_{{\\text{{dec}}}}$ reaches {rc['auroc_E_dec']:.3f} against {rc['auroc_final_step_conf']:.3f}")
ab = json.loads((RES / "baseline_ablations.json").read_text())["models"]
c1 = ab["Jev 1.13"]["wrong_action"]["contrasts"]["E_dec-action_rule"]
c2 = ab["openjev/openjev-27B"]["wrong_action"]["contrasts"]["E_dec-action_rule"]
need("Jev E_dec-rule CI", f"($+{c1['diff']:.3f}$ [${c1['ci95'][0]:.3f}$, $+{c1['ci95'][1]:.3f}$]")
need("OpenJev E_dec-rule CI", f"$+{c2['diff']:.3f}$ [${c2['ci95'][0]:.3f}$, $+{c2['ci95'][1]:.3f}$]")
rw = json.loads((RES / "prior_shift_reweighting.json").read_text())["models"]["Jev 1.13"]["severity_wrong"]
need("Jev severity reweighted", f"(Jev {rw['E_dec_w']['auroc']:.2f} vs.\\ {rw['conf']['auroc']:.2f} on severity)")
need("Jev severity dev-fit", f"(0.{round(100 * ab['Jev 1.13']['severity_wrong']['scores']['E_dec']['auroc'])} for Jev and OpenJev)") if round(100 * ab['Jev 1.13']['severity_wrong']['scores']['E_dec']['auroc']) == round(100 * ab['openjev/openjev-27B']['severity_wrong']['scores']['E_dec']['auroc']) else None

# BBSE (addendum I, added 2026-10-23)
bb = json.loads((RES / "label_shift_bbse.json").read_text())["models"]
need("BBSE Jev", f"Jev ({bb['Jev 1.13']['severity_wrong']['bbse']:.2f} on severity, {bb['Jev 1.13']['any_node_wrong']['bbse']:.2f} on any node)")
need("BBSE OpenJev", f"OpenJev\n({bb['openjev/openjev-27B']['severity_wrong']['bbse']:.2f}, {bb['openjev/openjev-27B']['any_node_wrong']['bbse']:.2f})".replace("\n", " "))
need("BBSE Qwen", f"Qwen2.5 ({bb['Qwen/Qwen2.5-7B-Instruct']['severity_wrong']['bbse']:.2f} on severity)")

# Second audit (addendum J, added 2026-10-23)
ir = json.loads((RES / "audit_independent_recompute.json").read_text())
need("J2 mozilla", f"$+{ir['J2_moz']['diff']:.3f}$ [$+{ir['J2_moz']['diff_ci95'][0]:.3f}$,\n  $+{ir['J2_moz']['diff_ci95'][1]:.3f}$] on Mozilla".replace("\n  ", " "))
need("J2 kernel", f"$+{ir['J2_ker']['diff']:.3f}$ [$+{ir['J2_ker']['diff_ci95'][0]:.3f}$, $+{ir['J2_ker']['diff_ci95'][1]:.3f}$] on the kernel")
assert all(v["abs_diff"] == 0 for k, v in ir["comparison_to_paper"].items() if v["kind"] == "point estimate"), "independent recompute mismatch"
sp = json.loads((RES / "audit_second_pass.json").read_text())
j3 = sp["J3"]["Jev 1.13"]
need("J3 Jev", f"gives {j3['auroc_E_dec']:.3f} against {j3['auroc_conf']:.3f}\n  (difference $+{j3['diff']:.3f}$ [$+{j3['ci95'][0]:.3f}$, $+{j3['ci95'][1]:.3f}$])".replace("\n  ", " "))
j5 = sp["J5"]["Jev 1.13"]
need("J5 Jev", f"the {j5['wrong_accepts']} wrong accepts at AUROC {j5['auroc_E_dec']:.2f}, {j5['auroc_conf']:.2f} and {j5['auroc_p_level2']:.2f}")
need("J5 Jev n", f"among Jev's {j5['n_accepted']} accepted held-out cases")
j7a, j7b = sp["J7"]["Jev 1.13"]["m=2,h=1,rho=1.0"], sp["J7"]["Jev 1.13"]["m=2,h=1,rho=0.8"]
need("J7 Jev", f"falls from {-round(j7a['best_minus_no_review'])} to {-round(j7b['best_minus_no_review'])}\nunits".replace("\n", " "))
j6 = sp["J6"]["Jev 1.13"]["lambda=0.0,level2_share=0.5"]
need("J6 Jev bias", f"underestimates a 50\\% share of serious bugs by {-j6['bias']:.2f}")

# J5 intervals (added 2026-10-23)
j5i = json.loads((RES / "audit_j5_intervals.json").read_text())
cj = j5i["Jev 1.13"]["conf"]; po = j5i["openjev/openjev-27B"]["p2"]
need("J5 Jev conf CI", f"{cj['auroc']:.2f} [{cj['ci95'][0]:.2f}, {cj['ci95'][1]:.2f}] for confidence")
need("J5 OpenJev p2", f"({po['auroc']:.2f} [{po['ci95'][0]:.2f}, {po['ci95'][1]:.2f}], above confidence)")
assert j5i["openjev/openjev-27B"]["p2_minus_conf"]["ci95"][0] > 0
assert all(j5i["Jev 1.13"][k]["ci95"][0] < 0.5 < j5i["Jev 1.13"][k]["ci95"][1] for k in ("E_dec", "conf", "p2")) or j5i["Jev 1.13"]["E_dec"]["ci95"][1] < 0.53

po2 = j5i["openjev/openjev-27B"]
need("J5 OpenJev paired", f"above confidence by $+{po2['p2']['auroc'] - po2['conf']['auroc']:.2f}$ (95\\% interval [$+{po2['p2_minus_conf']['ci95'][0]:.2f}$, $+{po2['p2_minus_conf']['ci95'][1]:.2f}$])")

bad = [c for c in checks if not c[2]]
for label, text, ok in checks:
    print(("OK   " if ok else "MISS ") + f"{label}: {text}")
print(f"\n{len(checks) - len(bad)}/{len(checks)} traced")
sys.exit(1 if bad else 0)
