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
