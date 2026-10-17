"""Write pgfplots coordinate files for the paper's figures from committed
result files, so every plotted number traces to an artifact. No API calls.

  python3 research/paper/latex/make_figure_data.py
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
RES = HERE.parents[1] / "results"


def override(name):
    e = json.loads((RES / f"{name}_exploratory_analysis.json").read_text())
    pts = e["override_curve"]["points"]
    n = e["n"]
    with open(HERE / f"fig_override_{name}.dat", "w") as f:
        f.write("k conf u5 rand\n")
        for p in pts:
            if p["k"] <= 80:
                f.write(f"{p['k']} {p['conf_product'] / n:.4f} {p['strategy5_U'] / n:.4f} {p['random_expected'] / n:.4f}\n")


def lean(name, manifest, key):
    a = json.loads((RES / manifest).read_text())
    a = a.get("analysis", a)
    conf = a["subsets"]["all"][key]
    with open(HERE / f"fig_confusion_{name}.dat", "w") as f:
        f.write("true pred0 pred1 pred2\n")
        for t in ("0", "1", "2"):
            row = conf[t]
            tot = sum(v for k, v in row.items() if k != "unstable")
            f.write(f"{t} " + " ".join(f"{row.get(p, 0) / tot:.3f}" for p in ("0", "1", "2")) + "\n")


override("mozilla")
override("kernel")
lean("mozilla", "mozilla_validation_execution_manifest.json", "score_confusion")
lean("kernel", "kernel_validation_execution_manifest.json", "score_confusion")
print("wrote", sorted(p.name for p in HERE.glob("fig_*.dat")))


# ---------------------------------------------------------------------------
# Additional figures (added for the IEEE version; used by all versions).
# ---------------------------------------------------------------------------
import sys as _sys
_sys.path.insert(0, str(HERE))
import paper_statistics as ps  # noqa: E402

BIN_EDGES = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0001]


def reliability(name):
    per = ps.load(name)
    sig = ps.node_signals(per, list(per))
    for node in ("choice", "noul"):
        conf, ok = sig[node]
        with open(HERE / f"fig_rel_{name}_{node}.dat", "w") as f:
            f.write("conf acc n\n")
            for lo, hi in zip(BIN_EDGES, BIN_EDGES[1:]):
                idx = [i for i, c in enumerate(conf) if lo <= c < hi]
                if len(idx) >= 5:
                    f.write(f"{sum(conf[i] for i in idx) / len(idx):.3f} "
                            f"{sum(ok[i] for i in idx) / len(idx):.3f} {len(idx)}\n")


def heatmap(name, manifest):
    a = json.loads((RES / manifest).read_text())
    conf = a.get("analysis", a)["subsets"]["all"]["score_confusion"]
    with open(HERE / f"fig_heat_{name}.dat", "w") as f:
        f.write("x y v\n")
        for t in ("0", "1", "2"):
            row = conf[t]
            tot = sum(v for k, v in row.items() if k != "unstable")
            for p in ("0", "1", "2"):
                f.write(f"{p} {t} {row.get(p, 0) / tot:.2f}\n")
            f.write("\n")


def transfer():
    def sel(m):
        a = json.loads((RES / m).read_text())
        return a.get("analysis", a)["selectivity"]
    mz, kn = sel("mozilla_validation_execution_manifest.json"), sel("kernel_validation_execution_manifest.json")
    # Constructed pilot values from threshold_transfer_finding.md (27/30 fired; 73% escalated; target 6/9).
    rows = [("Pilot", 100 * 27 / 30, 73, 100 * 6 / 9),
            ("Mozilla", 100 * mz["rev10_choice_conf_ge_0.90_trigger"], 100 * mz["rev10_strategy2_escalation_rate"], 100 * mz["rev11_strategy2_q"]),
            ("Kernel", 100 * kn["rev10_choice_conf_ge_0.90_trigger"], 100 * kn["rev10_strategy2_escalation_rate"], 100 * kn["rev11_strategy2_q"])]
    with open(HERE / "fig_transfer.dat", "w") as f:
        f.write("set trigger cut target\n")
        for r in rows:
            f.write(f"{r[0]} {r[1]:.1f} {r[2]:.1f} {r[3]:.1f}\n")


def forest():
    st = json.loads((HERE / "paper_statistics.json").read_text())
    items = [("choice", lambda d: st[d]["auroc_own"]["choice"]),
             ("noul", lambda d: st[d]["auroc_own"]["noul"]),
             ("score", lambda d: st[d]["auroc_own"]["score"]),
             ("compA", lambda d: st[d]["composition"]["auroc_missed_serious"]),
             ("compB", lambda d: st[d]["composition"]["auroc_S1_wrong"])]
    for d, off in (("mozilla", 0.15), ("kernel", -0.15)):
        with open(HERE / f"fig_forest_{d}.dat", "w") as f:
            f.write("x y lo hi\n")
            for k, (_, get) in enumerate(items):
                v = get(d)
                y = len(items) - k + off
                f.write(f"{v['point']} {y:.2f} {v['point'] - v['ci95'][0]:.3f} {v['ci95'][1] - v['point']:.3f}\n")


reliability("mozilla")
reliability("kernel")
heatmap("mozilla", "mozilla_validation_execution_manifest.json")
heatmap("kernel", "kernel_validation_execution_manifest.json")
transfer()
forest()
print("wrote additional figure data")


# ---------------------------------------------------------------------------
# Cross-model and intervention figures (added 2026-10-17)
# ---------------------------------------------------------------------------
def crossmodel():
    rb = json.loads((RES / "openjev_robustness_checks.json").read_text())["models"]
    names = [("Jev 1.13", "Jev"), ("openjev/openjev-27B", "OpenJev"), ("Qwen/Qwen2.5-7B-Instruct", "Qwen2.5"),
             ("microsoft/Phi-3.5-mini-instruct", "Phi-3.5"), ("allenai/OLMo-2-1124-7B-Instruct", "OLMo-2")]
    with open(HERE / "fig_crossmodel.dat", "w") as f:
        f.write("model y dec declo dechi conf conflo confhi\n")
        for i, (key, short) in enumerate(names):
            v = rb[key]
            d, c = v["E_dec"], v["final_step_conf"]
            y = len(names) - i
            f.write(f"{short} {y} {d[0]} {d[0] - d[1][0]:.3f} {d[1][1] - d[0]:.3f} "
                    f"{c[0]} {c[0] - c[1][0]:.3f} {c[1][1] - c[0]:.3f}\n")


def intervention():
    it = json.loads((RES / "intervention_test.json").read_text())["models"]
    mech = json.loads((RES / "intervention_cost_mechanism.json").read_text())["models"]
    with open(HERE / "fig_intervention.dat", "w") as f:
        f.write("model noreview A1 B C oracle\n")
        for key, short in MODELS5:
            a = it[key]["arms"]
            f.write(f"{short} {it[key]['base_total_cost']} {a['A1']['total_cost']} {a['B']['total_cost']} "
                    f"{a['C']['total_cost']} {mech[key]['oracle_cost_at_k50']}\n")


MODELS5 = (("Jev 1.13", "Jev"), ("openjev/openjev-27B", "OpenJev"), ("Qwen/Qwen2.5-7B-Instruct", "Qwen2.5"),
           ("microsoft/Phi-3.5-mini-instruct", "Phi-3.5"), ("allenai/OLMo-2-1124-7B-Instruct", "OLMo-2"))
ARM_NAMES = {"A1": "action rule", "A2": "error rate", "E": "estimator", "B": "confidence", "B2": "conf.\\ product", "C": "random"}


def crossmodel_table():
    """Per-model summary table (table_crossmodel.tex), generated from committed results."""
    rb = json.loads((RES / "openjev_robustness_checks.json").read_text())["models"]
    cm = json.loads((RES / "openjev_crossmodel_analysis.json").read_text())["models"]
    ho = json.loads((RES / "heldout_analysis.json").read_text())   # 250 bugs per tracker: overall rate = mean
    it = json.loads((RES / "intervention_test.json").read_text())["models"]
    mech = json.loads((RES / "intervention_cost_mechanism.json").read_text())["models"]
    kind = {"Jev": "TypeSafe, hosted", "OpenJev": "Jev-style, 27B", "Qwen2.5": "general, 7B",
            "Phi-3.5": "general, 3.8B", "OLMo-2": "general, 7B"}
    ci = lambda v: f"{v[0]:.2f} [{v[1][0]:.2f}, {v[1][1]:.2f}]"
    lines = []
    for key, short in MODELS5:
        r = rb[key]
        fail = sum(ho["failure_rate"].values()) / 2 if key == "Jev 1.13" else float(cm[key]["heldout_failure_rate"])
        transfer = "---" if key == "Jev 1.13" else f"{r['E_jev_frozen'][0]:.2f}"
        arms = it[key]["arms"]
        best = min(arms, key=lambda a: arms[a]["total_cost"])
        m = mech[key]
        lines.append(f"{short} & {kind[short]} & {fail:.2f} & {ci(r['E_dec'])} & {ci(r['final_step_conf'])} & "
                     f"{r['rule_rate_by_action']:.2f} & {transfer} & {it[key]['base_total_cost']} & "
                     f"{arms[best]['total_cost']:.0f} ({'all arms tie' if len({v['total_cost'] for v in arms.values()}) == 1 else ARM_NAMES[best]}) & {m['oracle_cost_at_k50']} & "
                     f"{round(100 * m['share_of_cost_from_wrong_accepts'])}\\% \\\\")
    (HERE / "table_crossmodel.tex").write_text(
        "% Generated by make_figure_data.py from research/results/*.json. Do not edit by hand.\n"
        "\\begin{tabular}{llcccccrrrr}\n\\toprule\n"
        " & & & \\multicolumn{4}{c}{Held-out AUROC for wrong actions} & \\multicolumn{4}{c}{Cost at 10\\% review budget} \\\\\n"
        "\\cmidrule(lr){4-7}\\cmidrule(lr){8-11}\n"
        "Model & Type & Fail rate & Decision est. & Final-step conf. & Action rule & Jev est. & No review & Best review arm & Oracle & Wrong accepts \\\\\n"
        "\\midrule\n" + "\n".join(lines) + "\n\\bottomrule\n\\end{tabular}\n")


def budget_table():
    """Budget-feasibility grid (table_budget.tex), generated from committed results."""
    bc = json.loads((RES / "case_level_review_budget_check.json").read_text())
    rows = []
    for n, r in bc["results"].items():
        for i, (b, v) in enumerate(r.items()):
            lead = f"{int(n):,}".replace(",", "{,}") if i == 0 else ""
            rows.append(f"{lead} & {float(b) * 100:g}\\% & {v['k']} & {v['power']:.2f} & ${v['median_cost_change_vs_no_review']:+.0f}$ & "
                        f"$[{v['central_80pct'][0]:+.0f}, {v['central_80pct'][1]:+.0f}]$ \\\\")
        rows.append("\\addlinespace")
    (HERE / "table_budget.tex").write_text(
        "% Generated by make_figure_data.py from research/results/case_level_review_budget_check.json. Do not edit by hand.\n"
        "\\begin{tabular}{rrrrrr}\n\\toprule\n"
        "Fresh bugs & Budget & $k$ & Power & Median $\\Delta$cost & 80\\% range \\\\\n\\midrule\n"
        + "\n".join(rows[:-1]) + "\n\\bottomrule\n\\end{tabular}\n")


def intervention_tests_table():
    """Pre-registered intervention tests (table_intervention_tests.tex), from intervention_test.json."""
    it = json.loads((RES / "intervention_test.json").read_text())
    rows = []
    for key, short in MODELS5:
        m = it["models"][key]
        cells = []
        for comp, sym in (("C", "<C"), ("B", "<B")):
            d = m[f"A1_minus_{comp}"]
            ok = it["holm_supported"][f"{key}:A1{sym}"]
            cells.append(f"${d['point']:+.1f}$ [${d['ci95'][0]:+.1f}$, ${d['ci95'][1]:+.1f}$]{'$^{*}$' if ok else ''}")
        rows.append(f"{short} & {cells[0]} & {cells[1]} \\\\")
    (HERE / "table_intervention_tests.tex").write_text(
        "% Generated by make_figure_data.py from research/results/intervention_test.json. Do not edit by hand.\n"
        "\\begin{tabular}{lcc}\n\\toprule\n"
        "Model & A1 $-$ random & A1 $-$ confidence \\\\\n\\midrule\n"
        + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}\n")


crossmodel()
intervention()
crossmodel_table()
budget_table()
intervention_tests_table()
print("wrote cross-model and intervention figure data")
