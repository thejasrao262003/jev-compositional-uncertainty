"""Pre-registered cross-model analysis (research/methodology/openjev_crossmodel_preregistration.md).
No API calls. Reads research/data/openjev/*_raw_responses.jsonl.

Per open model M:
  C1  characterization (descriptive): node agreement, own-confidence AUROC,
      severity confusion, fixed-threshold selectivity;
  X1  E_dec trained on M's 442 training bugs vs M's low final-step confidence,
      on M's 500 held-out bugs (paired, stratified bootstrap, one-sided);
  X2  E_dec held-out AUROC > 0.5 (one-sided bootstrap);
  Holm across all models x {X1, X2};
  X3  E_all vs E_dec (descriptive);
  X4  Jev's FROZEN estimator applied to M's outputs (descriptive).
The same functions as the Jev held-out analysis are used (features, fit,
bootstrap); Jev's own held-out numbers are included for comparison.

  python3 research/src/openjev/analyze_crossmodel.py
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE.parent
sys.path.insert(0, str(SRC))
import run_heldout_validation as hv  # noqa: E402
import workflow_risk_probe as wp  # noqa: E402
from build_workflow_calibration_pilot_manifest import F  # noqa: E402
from run_workflow_calibration_pilot import (reduce_choice_or_score_cell, reduce_noul_cell,  # noqa: E402
                                            strategy_1_decision_only)

ROOT = SRC.parents[1]
DATA = ROOT / "research" / "data" / "openjev"
OUT = ROOT / "research" / "results" / "openjev_crossmodel_analysis.json"
MODELS = ["Qwen/Qwen2.5-7B-Instruct", "allenai/OLMo-2-1124-7B-Instruct", "microsoft/Phi-3.5-mini-instruct",
          "openjev/openjev-27B"]  # Amendment 1: OpenJev served via its shim (file label openjev__openjev-27B)
ALPHA = 0.05


def bugs_index():
    idx = {}
    for t in ("mozilla", "kernel"):
        for line in (ROOT / "research" / "data" / t / "dataset.jsonl").open():
            b = json.loads(line)
            idx[("train", t, b["bug_id"])] = b
        for line in (ROOT / "research" / "data" / "heldout" / f"{t}_heldout.jsonl").open():
            b = json.loads(line)
            idx[("heldout", t, b["bug_id"])] = b
    return idx


def per_bug(rows, idx):
    by = {}
    for r in rows:
        by.setdefault((r["split"], r["tracker"], r["bug_id"]), {}).setdefault(r["arm"], []).append(r)
    P = {}
    for key, arms in by.items():
        b = idx[key]
        red = {"choice": reduce_choice_or_score_cell(arms["choice"]), "noul": reduce_noul_cell(arms["noul"]),
               "score": reduce_choice_or_score_cell(arms["score"])}
        s1 = strategy_1_decision_only(red["choice"]["modal_decision"], red["noul"], red["score"])
        P[key] = {"split": key[0], "tracker": key[1], "red": red, "s1": s1, "a_star": F(b["regression"], b["level"]),
                  "bug": b}
    if len(P) != len(idx):
        raise SystemExit(f"incomplete model output: {len(P)} of {len(idx)} bugs")
    return P


def characterization(P):
    out = {}
    for t in ("mozilla", "kernel"):
        Q = [p for p in P.values() if p["tracker"] == t]
        ch = [(p["red"]["choice"]["mean_confidence"] or 0, p["red"]["choice"]["modal_decision"] == p["bug"]["group"]) for p in Q]
        nl = [(2 * abs(p["red"]["noul"]["mean_noul"] - 0.5), p["red"]["noul"]["decision"] == p["bug"]["regression"]) for p in Q]
        sc = [(p["red"]["score"]["mean_confidence"] or 0,
               p["red"]["score"]["modal_decision"] is not None and int(p["red"]["score"]["modal_decision"]) == p["bug"]["level"]) for p in Q]
        conf = {lv: Counter() for lv in (0, 1, 2)}
        for p in Q:
            d = p["red"]["score"]["modal_decision"]
            conf[p["bug"]["level"]]["unstable" if d is None else int(d)] += 1
        trig = sum(1 for p in Q if (p["red"]["choice"]["mean_confidence"] or 0) >= 0.90) / len(Q)
        prod_esc = sum(1 for p in Q if ((p["red"]["choice"]["mean_confidence"] or 0) * 2 * abs(p["red"]["noul"]["mean_noul"] - 0.5)
                                        * (p["red"]["score"]["mean_confidence"] or 0)) < 0.5) / len(Q)
        out[t] = {"n": len(Q),
                  "agreement": {"choice": round(sum(k for _, k in ch) / len(Q), 3), "noul": round(sum(k for _, k in nl) / len(Q), 3),
                                "score": round(sum(k for _, k in sc) / len(Q), 3)},
                  "own_conf_auroc": {"choice": hv.auroc(*map(list, zip(*ch))), "noul": hv.auroc(*map(list, zip(*nl))),
                                     "score": hv.auroc(*map(list, zip(*sc)))},
                  "share_choice_conf_ge_0.90": round(trig, 3), "share_product_below_0.5": round(prod_esc, 3),
                  "score_confusion_row_normalized": {lv: {k: round(v / sum(c.values()), 3) for k, v in sorted(c.items(), key=str)}
                                                     for lv, c in conf.items() if sum(c.values())}}
        for k, v in out[t]["own_conf_auroc"].items():
            out[t]["own_conf_auroc"][k] = None if v is None else round(v, 3)
    return out


def score_rows(Ps, models, jev_est):
    rows = []
    for key, p in Ps.items():
        dec, unc = wp.features(p)
        rows.append({"key": key, "tracker": p["tracker"], "y": int(p["s1"] != p["a_star"]),
                     "E_dec": hv.risk(models["DECISION"], p, "DECISION") if models else None,
                     "E_all": hv.risk(models["ALL"], p, "ALL") if models else None,
                     "E_jev_frozen": hv.risk(jev_est["estimators"]["DECISION"], p, "DECISION"),
                     "low_score_conf": -unc["score_conf"],
                     "low_min_conf": -min(unc["choice_conf"], unc["noul_conf"], unc["score_conf"]),
                     "low_product": -(unc["choice_conf"] * unc["noul_conf"] * unc["score_conf"])})
    return rows


def main():
    idx = bugs_index()
    jev_est = hv.load_estimator()
    res = {"models": {}, "jev_heldout_reference": json.loads((ROOT / "research" / "results" / "heldout_analysis.json").read_text())}
    pvals = {}
    for m in MODELS:
        f = DATA / f"{m.replace('/', '__')}_raw_responses.jsonl"
        if not f.exists():
            res["models"][m] = "NOT RUN"
            continue
        P = per_bug([json.loads(line) for line in f.open()], idx)
        train = [p for p in P.values() if p["split"] == "train"]
        held = {k: p for k, p in P.items() if p["split"] == "heldout"}
        fitted = {}
        for kind in ("DECISION", "ALL"):
            feats = [wp.vec({"dec": wp.features(p)[0], "unc": wp.features(p)[1]}, kind) for p in train]
            names = sorted(wp.features(train[0])[0]) if kind == "DECISION" else sorted({**wp.features(train[0])[0], **wp.features(train[0])[1]})
            mdl = wp.fit(feats, [int(p["s1"] != p["a_star"]) for p in train])
            fitted[kind] = {"features": names, **mdl}
        S = score_rows(held, fitted, jev_est)
        diff = lambda rs: (None if hv._auc(rs, "E_dec") is None else hv._auc(rs, "E_dec") - hv._auc(rs, "low_score_conf"))
        d = hv.boot(S, diff)
        px1 = sum(v <= 0 for v in d) / len(d)
        bt = hv.boot(S, lambda rs: hv._auc(rs, "E_dec"))
        px2 = sum(v <= 0.5 for v in bt) / len(bt)
        pvals[f"{m}:X1"], pvals[f"{m}:X2"] = px1, px2
        res["models"][m] = {
            "characterization_all_bugs": characterization(P),
            "heldout_failure_rate": round(sum(r["y"] for r in S) / len(S), 3),
            "X1": {"auroc_E_dec": round(hv._auc(S, "E_dec"), 3), "auroc_low_score_conf": round(hv._auc(S, "low_score_conf"), 3),
                   "difference": round(diff(S), 3), "one_sided_95_lower": round(d[int(0.05 * len(d))], 3),
                   "bootstrap_p_one_sided": round(px1, 4)},
            "X2": {"auroc_E_dec": round(hv._auc(S, "E_dec"), 3), "one_sided_95_lower": round(bt[int(0.05 * len(bt))], 3),
                   "bootstrap_p_one_sided": round(px2, 4)},
            "X3_X4_descriptive": {c: round(hv._auc(S, c), 3) for c in
                                  ("E_dec", "E_all", "E_jev_frozen", "low_score_conf", "low_min_conf", "low_product")},
        }
    order = sorted(pvals, key=pvals.get)
    holm, ok = {}, True
    for i, k in enumerate(order):
        ok = ok and pvals[k] <= ALPHA / (len(order) - i)
        holm[k] = ok
    res["holm_supported"] = holm
    OUT.write_text(json.dumps(res, indent=2, default=str))
    print(json.dumps({m: (v if isinstance(v, str) else {k: v[k] for k in ("X1", "X2", "X3_X4_descriptive", "heldout_failure_rate")})
                      for m, v in res["models"].items()}, indent=1))
    print("holm:", holm)


if __name__ == "__main__":
    main()
