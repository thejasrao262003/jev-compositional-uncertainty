"""EXPLORATORY follow-up to workflow_risk_probe.py (no API calls):
(1) coefficients of the ALL model fit per tracker (what it learns);
(2) cross-tracker AUROC re-weighted to each tracker's REAL population mix of
    (subsystem, level) cells, from the committed feasibility counts, to test
    whether the balanced 40-per-cell design drives the result.

  .venv/bin/python3 research/src/workflow_risk_probe_followup.py
"""
import json
import sys
from pathlib import Path

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import workflow_risk_probe as wp  # noqa: E402

RES = ROOT / "research" / "results"
moz_f = json.loads((RES / "mozilla_feasibility_counts.json").read_text())["counts_by_severity"]
ker_f = json.loads((RES / "kernel_feasibility_counts.json").read_text())["counts_by_level"]
pop = {"mozilla": {(g, {"S1": 2, "S2": 2, "S3": 1, "S4": 0}[s]): 0 for g in moz_f for s in moz_f[g]},
       "kernel": {}}
for g, d in moz_f.items():
    for s, n in d.items():
        pop["mozilla"][(g, {"S1": 2, "S2": 2, "S3": 1, "S4": 0}[s])] += n
for g, d in ker_f.items():
    for lv, n in d.items():
        pop["kernel"][(g, int(lv[-1]))] = n


def weighted_auroc(scores, y, w):
    pos = [(s, wi) for s, t, wi in zip(scores, y, w) if t]
    neg = [(s, wi) for s, t, wi in zip(scores, y, w) if not t]
    num = sum(wp_ * wn * ((sp > sn) + 0.5 * (sp == sn)) for sp, wp_ in pos for sn, wn in neg)
    return num / (sum(w_ for _, w_ in pos) * sum(w_ for _, w_ in neg))


data = {d: wp.build(d) for d in ("mozilla", "kernel")}
per = {d: wp.ps.load(d) for d in data}
model = lambda: make_pipeline(StandardScaler(), LogisticRegression(C=1.0 / wp.LAMBDA, max_iter=5000))
out = {"coefficients_ALL": {}, "population_weighted_cross_tracker": {}}
names = {k: sorted({**data["mozilla"][0]["dec"], **data["mozilla"][0]["unc"]}) for k in ["ALL"]}["ALL"]
for d, rows in data.items():
    m = model().fit(np.array([wp.vec(r, "ALL") for r in rows]), [r["y"] for r in rows])
    coef = m.named_steps["logisticregression"].coef_[0]
    out["coefficients_ALL"][d] = {n: round(float(c), 2) for n, c in sorted(zip(names, coef), key=lambda t: -abs(t[1]))[:8]}
for tr, te in (("mozilla", "kernel"), ("kernel", "mozilla")):
    rows = data[te]
    cells = [(per[te][r["id"]]["bug"]["group"], per[te][r["id"]]["bug"]["level"]) for r in rows]
    n_sample = {c: cells.count(c) for c in set(cells)}
    w = [pop[te][c] / n_sample[c] for c in cells]     # inverse sampling fraction
    y = [r["y"] for r in rows]
    res = {"population_failure_rate": round(sum(wi * t for wi, t in zip(w, y)) / sum(w), 3)}
    for kind in ("DECISION", "ALL"):
        m = model().fit(np.array([wp.vec(r, kind) for r in data[tr]]), [r["y"] for r in data[tr]])
        res[kind] = round(weighted_auroc(list(m.decision_function(np.array([wp.vec(r, kind) for r in rows]))), y, w), 3)
    for base in ("base_score", "base_min", "base_product"):
        res[base] = round(weighted_auroc([r[base] for r in rows], y, w), 3)
    out["population_weighted_cross_tracker"][f"{tr}->{te}"] = res
print(json.dumps(out, indent=1))
(RES / "workflow_risk_probe_followup.json").write_text(json.dumps(out, indent=2))
