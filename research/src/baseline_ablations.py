"""Baseline ablations and target robustness
(research/methodology/evidence_audit_and_baselines_plan.md, sections E and F).

Exploratory: the 500 held-out bugs have been analysed before. No API or GPU
calls. Training = each model's own outputs on the 442 development bugs.

  .venv/bin/python research/src/baseline_ablations.py
"""
from __future__ import annotations

import json
import math
import random
import sys
from collections import defaultdict
from pathlib import Path

from sklearn.metrics import average_precision_score, roc_auc_score

SRC = Path(__file__).resolve().parent
sys.path.insert(0, str(SRC))
import intervention_test as it  # noqa: E402
import run_heldout_validation as hv  # noqa: E402
import workflow_risk_probe as wp  # noqa: E402

OUT = it.ROOT / "research" / "results" / "baseline_ablations.json"
B, SEED = 2000, 20261023
ACTIONS = ["accept", "escalate", "defer", "request_more_evidence"]
SCORES = ["final_step_conf", "action_rule", "action_only", "E_dec", "E_unc", "E_all"]
PROB = {"action_rule", "action_only", "E_dec", "E_unc", "E_all"}
CONTRASTS = [("E_dec", "action_rule"), ("E_all", "E_dec"), ("E_dec", "final_step_conf"), ("E_unc", "final_step_conf")]


def sev_wrong(p):
    d = p["red"]["score"]["modal_decision"]
    return int(d is None or int(d) != p["bug"]["level"])


TARGETS = {
    "wrong_action": lambda p: int(p["s1"] != p["a_star"]),
    "severity_wrong": sev_wrong,
    "any_node_wrong": lambda p: int(p["red"]["choice"]["modal_decision"] != p["bug"]["group"]
                                    or p["red"]["noul"]["decision"] != p["bug"]["regression"]
                                    or sev_wrong(p)),
}


def sig(x):
    return 1 / (1 + math.exp(-max(-30, min(30, x))))


def onehot(p):
    return [float(p["s1"] == a) for a in ACTIONS]


def fit_vec(train, y, fn):
    return wp.fit([fn(p) for p in train], y)


def score_table(mname, train, held, frozen_est, target):
    ytr = [TARGETS[target](p) for p in train]
    rate = defaultdict(list)
    for p, t in zip(train, ytr):
        rate[p["s1"]].append(t)
    overall = sum(ytr) / len(ytr)
    rule = {a: (sum(v) + overall) / (len(v) + 1) for a, v in rate.items()}   # one pseudo-count, as in the intervention test
    feat = lambda kind: (lambda p: wp.vec({"dec": wp.features(p)[0], "unc": wp.features(p)[1]}, kind))
    m_act = fit_vec(train, ytr, onehot)
    m_unc = fit_vec(train, ytr, feat("UNCERTAINTY"))
    m_all = fit_vec(train, ytr, feat("ALL"))
    if target == "wrong_action" and frozen_est is not None:
        e_dec = lambda p: sig(hv.risk(frozen_est, p, "DECISION"))       # pre-registered estimator (frozen for Jev)
    else:
        m_dec = fit_vec(train, ytr, feat("DECISION"))
        e_dec = lambda p: sig(wp.predict(m_dec, [feat("DECISION")(p)])[0])
    rows = []
    for p in held.values():
        dec, unc = wp.features(p)
        rows.append({"tracker": p["tracker"], "y": TARGETS[target](p),
                     "final_step_conf": -unc["score_conf"],
                     "action_rule": rule.get(p["s1"], overall),
                     "action_only": sig(wp.predict(m_act, [onehot(p)])[0]),
                     "E_dec": e_dec(p),
                     "E_unc": sig(wp.predict(m_unc, [feat("UNCERTAINTY")(p)])[0]),
                     "E_all": sig(wp.predict(m_all, [feat("ALL")(p)])[0])})
    return rows


def auc(rows, col):
    y = [r["y"] for r in rows]
    return roc_auc_score(y, [r[col] for r in rows]) if 0 < sum(y) < len(y) else float("nan")


def ece(rows, col, bins=10):
    tot, n = 0.0, len(rows)
    for b in range(bins):
        lo, hi = b / bins, (b + 1) / bins
        g = [r for r in rows if lo <= r[col] < hi or (b == bins - 1 and r[col] == 1.0)]
        if g:
            tot += len(g) / n * abs(sum(r[col] for r in g) / len(g) - sum(r["y"] for r in g) / len(g))
    return tot


def analyse(rows):
    rng = random.Random(SEED)
    groups = defaultdict(list)
    for r in rows:
        groups[r["tracker"]].append(r)
    boots = []
    for _ in range(B):
        s = [g[rng.randrange(len(g))] for g in groups.values() for _ in g]
        boots.append({c: auc(s, c) for c in SCORES})
    q = lambda v: [round(v[int(0.025 * len(v))], 3), round(v[int(0.975 * len(v)) - 1], 3)]
    out = {"n": len(rows), "positives": sum(r["y"] for r in rows), "scores": {}, "contrasts": {}}
    y = [r["y"] for r in rows]
    for c in SCORES:
        v = sorted(b[c] for b in boots)
        e = {"auroc": round(auc(rows, c), 3), "auroc_ci95": q(v),
             "auprc": round(average_precision_score(y, [r[c] for r in rows]), 3)}
        if c in PROB:
            e["brier"] = round(sum((r[c] - r["y"]) ** 2 for r in rows) / len(rows), 3)
            e["ece10"] = round(ece(rows, c), 3)
        out["scores"][c] = e
    for a, b in CONTRASTS:
        d = sorted(bt[a] - bt[b] for bt in boots)
        ci = q(d)
        out["contrasts"][f"{a}-{b}"] = {"diff": round(auc(rows, a) - auc(rows, b), 3), "ci95": ci,
                                        "excludes_0": ci[0] > 0 or ci[1] < 0}
    return out


def main():
    res = {"status": "EXPLORATORY (held-out set previously analysed); plan: evidence_audit_and_baselines_plan.md",
           "models": {}}
    for mname in ["Jev 1.13"] + it.ac.MODELS:
        train, held, est = it.load_model(mname)
        res["models"][mname] = {}
        for target in TARGETS:
            rows = score_table(mname, train, held, est, target)
            res["models"][mname][target] = analyse(rows)
            r = res["models"][mname][target]
            print(mname, target, r["positives"], {c: r["scores"][c]["auroc"] for c in SCORES},
                  {k: (v["diff"], v["ci95"]) for k, v in r["contrasts"].items()}, flush=True)
    OUT.write_text(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
