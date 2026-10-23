"""Addendum H of evidence_audit_and_baselines_plan.md: does re-weighting the
development bugs to the natural label mix repair the decision-conditioned
error estimators? Exploratory. No API or GPU calls. Weights use only label
counts from the held-out manifests (same as the power simulation).

  .venv/bin/python research/src/prior_shift_reweighting.py
"""
from __future__ import annotations

import json
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.preprocessing import StandardScaler

SRC = Path(__file__).resolve().parent
sys.path.insert(0, str(SRC))
import baseline_ablations as ba  # noqa: E402
import case_level_review_power as pw  # noqa: E402
import intervention_test as it  # noqa: E402
import workflow_risk_probe as wp  # noqa: E402

OUT = it.ROOT / "research" / "results" / "prior_shift_reweighting.json"


def cell(p):
    return (p["bug"]["group"], str(p["bug"]["level"]))


def weights(train):
    nat = {t: pw.natural_mix(t) for t in ("mozilla", "kernel")}
    cnt = Counter((p["tracker"], cell(p)) for p in train)
    w = [nat[p["tracker"]].get(cell(p), 0.0) / cnt[(p["tracker"], cell(p))] for p in train]
    m = sum(w) / len(w)
    return [x / m for x in w]


def dec_vec(p):
    dec, unc = wp.features(p)
    return wp.vec({"dec": dec, "unc": unc}, "DECISION")


def boot_auc(rows, col, rng):
    groups = defaultdict(list)
    for r in rows:
        groups[r["tracker"]].append(r)
    v = []
    for _ in range(ba.B):
        s = [g[rng.randrange(len(g))] for g in groups.values() for _ in g]
        y = [r["y"] for r in s]
        v.append(roc_auc_score(y, [r[col] for r in s]))
    v.sort()
    return [round(v[int(0.025 * ba.B)], 3), round(v[int(0.975 * ba.B) - 1], 3)]


def main():
    prev = json.loads(ba.OUT.read_text())["models"]
    out = {"status": "EXPLORATORY (addendum H)", "models": {}}
    for mname in ["Jev 1.13"] + it.ac.MODELS:
        train, held, _ = it.load_model(mname)
        w = weights(train)
        out["models"][mname] = {}
        for target, fn in ba.TARGETS.items():
            ytr = [fn(p) for p in train]
            sw, sy = defaultdict(float), defaultdict(float)
            for p, yi, wi in zip(train, ytr, w):
                sw[p["s1"]] += wi
                sy[p["s1"]] += wi * yi
            overall = sum(wi * yi for wi, yi in zip(w, ytr)) / sum(w)
            rule = {a: (sy[a] + overall) / (sw[a] + 1) for a in sw}
            sc = StandardScaler().fit([dec_vec(p) for p in train])
            lr = LogisticRegression(C=1.0, max_iter=2000).fit(sc.transform([dec_vec(p) for p in train]), ytr, sample_weight=w)
            rows = [{"tracker": p["tracker"], "y": fn(p),
                     "rule_w": rule.get(p["s1"], overall),
                     "E_dec_w": lr.predict_proba(sc.transform([dec_vec(p)]))[0][1],
                     "conf": -wp.features(p)[1]["score_conf"]} for p in held.values()]
            rng = random.Random(ba.SEED)
            y = [r["y"] for r in rows]
            res = {}
            for col in ("rule_w", "E_dec_w", "conf"):
                res[col] = {"auroc": round(roc_auc_score(y, [r[col] for r in rows]), 3), "ci95": boot_auc(rows, col, rng)}
            p0 = prev[mname][target]["scores"]
            res["unweighted"] = {"action_rule": p0["action_rule"]["auroc"], "E_dec": p0["E_dec"]["auroc"]}
            out["models"][mname][target] = res
            print(mname, target, {k: (v["auroc"] if isinstance(v, dict) and "auroc" in v else v) for k, v in res.items()}, flush=True)
    OUT.write_text(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
