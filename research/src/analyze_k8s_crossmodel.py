"""Analysis for research/methodology/k8s_crossmodel_preregistration.md. No API or GPU calls.

  .venv/bin/python research/src/analyze_k8s_crossmodel.py --selftest
  .venv/bin/python research/src/analyze_k8s_crossmodel.py
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

SRC = Path(__file__).resolve().parent
sys.path.insert(0, str(SRC))
import analyze_k8s as ak  # noqa: E402  (frozen per-model analysis)

ROOT = SRC.parents[1]
CM = ROOT / "research" / "data" / "k8s" / "crossmodel"
OUT = ROOT / "research" / "results" / "k8s_crossmodel_analysis.json"
MODELS = ["Qwen/Qwen2.5-7B-Instruct", "microsoft/Phi-3.5-mini-instruct", "allenai/OLMo-2-1124-7B-Instruct",
          "openjev__openjev-27B"]


def combine(per_model):
    """Holm across the 8 primary tests; status per model; overall reading (protocol section 3)."""
    pv = {}
    for m, r in per_model.items():
        if r is None:
            continue
        pv[(m, "XK1")] = r["primary"]["K1"]["p_one_sided"]
        pv[(m, "XK2")] = r["primary"]["K2"]["p_one_sided"]
    H = ak.holm(pv)
    out = {}
    for m, r in per_model.items():
        if r is None:
            out[m] = {"status": "run failed"}
            continue
        k1, k2 = r["primary"]["K1"], r["primary"]["K2"]
        x1 = ("supported" if H[(m, "XK1")] else "not replicated" if k1["ci95"][1] < k1["d_star"] else "inconclusive")
        out[m] = {"n_test": r["n"]["test"], "failed_issues": len(r["n"]["failed"]),
                  "auroc_rule": k1["auroc_rule"], "auroc_conf": k1["auroc_conf"],
                  "diff": round(k1["auroc_rule"] - k1["auroc_conf"], 4), "ci95": k1["ci95"],
                  "p_XK1": k1["p_one_sided"], "XK1": x1, "p_XK2": k2["p_one_sided"],
                  "XK2": "supported" if H[(m, "XK2")] else "inconclusive",
                  "K3_exploratory": r["primary"]["K3"]["status"], **r.get("descriptive", {}), "rate_table": r["primary"]["rate_table"]}
    st = [v.get("XK1") for v in out.values()]
    overall = ("holds on Kubernetes" if st.count("supported") >= 3 else
               "does not generalise" if st.count("not replicated") >= 2 else "mixed")
    return {"per_model": out, "overall": overall, "holm_family_size": len(pv)}


def low_mass_sensitivity(ds, raw, r):
    lm = [x["label_mass"] for x in raw if x["repeat"] == 1 and "label_mass" in x]
    if not lm or sum(v < 0.5 for v in lm) / len(lm) <= 0.02:
        return None
    bad = {x["number"] for x in raw if x.get("label_mass", 1) < 0.5}
    s = ak.analyze(ds, [x for x in raw if x["number"] not in bad])["primary"]["K1"]
    return {"excluded_issues": len(bad), "auroc_rule": s["auroc_rule"], "auroc_conf": s["auroc_conf"],
            "ci95": s["ci95"], "p_one_sided": s["p_one_sided"]}


def main():
    ds = [json.loads(l) for l in (ak.DATA / "k8s_dataset.jsonl").open()]
    per, full, sens = {}, {}, {}
    for m in MODELS:
        f = CM / f"{m.replace('/', '__')}_raw_responses.jsonl"
        if not f.exists():
            per[m] = None
            continue
        raw = [json.loads(l) for l in f.open()]
        r = ak.analyze(ds, raw)
        P, _ = ak.per_issue(ds, raw)  # descriptive, added after results were seen
        T = [p for p in P if p["split"] == "test"]
        r["descriptive"] = {"test_action_mix": dict(Counter(p["s1"] for p in T)),
                            "test_wrong_action_rate": round(sum(p["y_wrong_action"] for p in T) / len(T), 4),
                            "test_wrong_action_rate_exact": sum(p["y_wrong_action"] for p in T) / len(T)}
        per[m], full[m], sens[m] = r, r, low_mass_sensitivity(ds, raw, r)
    res = combine(per)
    # Amendment 1 (post hoc): competence = above chance on every step, applied to every model incl. Jev 1.13
    jev_raw = [json.loads(l) for l in (ak.DATA / "k8s_raw_responses.jsonl").open()]
    jev = json.loads((ak.RES / "k8s_analysis.json").read_text())["primary"]["K1"]
    comp = {}
    for m, raw in [("Jev 1.13", jev_raw)] + [(m, [json.loads(l) for l in (CM / f"{m.replace('/', '__')}_raw_responses.jsonl").open()])
                                              for m in MODELS if per[m] is not None]:
        P, _ = ak.per_issue(ds, raw)
        T = [p for p in P if p["split"] == "test"]
        a = {"routing": sum(p["red"]["choice"]["modal_decision"] == p["sig"] for p in T) / len(T),
             "bug": sum(p["red"]["noul"]["decision"] == p["bug"] for p in T) / len(T),
             "priority": sum(1 - p["y_priority_wrong"] for p in T) / len(T)}
        ok = a["routing"] > 1 / 3 and a["bug"] > 1 / 2 and a["priority"] > 1 / 3
        x1 = jev["status"] if m == "Jev 1.13" else res["per_model"][m]["XK1"]
        comp[m] = {"accuracy": {k: round(v, 4) for k, v in a.items()}, "competent": ok, "XK1": x1}
    res["amendment1_competence"] = {"criterion": "test accuracy above chance on every step (1/3, 1/2, 1/3)",
                                    "models": comp,
                                    "competent_supported": [m for m, v in comp.items() if v["competent"] and v["XK1"] == "supported"],
                                    "competent": [m for m, v in comp.items() if v["competent"]]}
    res["low_mass_sensitivity"] = sens
    res["exploratory"] = {m: {"secondary": r["secondary"], "K3": r["primary"]["K3"]} for m, r in full.items()}
    OUT.write_text(json.dumps(res, indent=2, default=str))
    print(json.dumps({k: res[k] for k in ("per_model", "overall")}, indent=1))


def selftest():
    fake = {}
    for i, m in enumerate(MODELS):
        p = [0.001, 0.004, 0.2, 0.0][i]
        fake[m] = {"n": {"test": 582, "failed": []},
                   "primary": {"K1": {"auroc_rule": 0.7, "auroc_conf": 0.6, "ci95": [0.02 if p < .05 else -.02, 0.15],
                                      "p_one_sided": p, "d_star": 0.10},
                               "K2": {"p_one_sided": p / 2}, "K3": {"status": "x"}, "rate_table": {}}}
    fake[MODELS[3]] = None
    r = combine(fake)
    assert r["per_model"][MODELS[0]]["XK1"] == "supported"
    assert r["per_model"][MODELS[2]]["XK1"] == "inconclusive"
    assert r["per_model"][MODELS[3]]["status"] == "run failed"
    assert r["overall"] == "mixed" and r["holm_family_size"] == 6
    print("selftest OK")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    selftest() if a.selftest else main()
