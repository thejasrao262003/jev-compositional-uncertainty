"""Addendum I of evidence_audit_and_baselines_plan.md: deployment-feasible
label-shift correction by black-box shift estimation (BBSE; Lipton et al.
2018). Held-out LABELS are never used to build the weights: only development
labels + development predictions (confusion matrix) and held-out PREDICTIONS
(prediction mix). Exploratory. No API or GPU calls.

  .venv/bin/python research/src/label_shift_bbse.py
"""
from __future__ import annotations

import json
import random
import sys
from collections import Counter
from pathlib import Path

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.preprocessing import StandardScaler

SRC = Path(__file__).resolve().parent
sys.path.insert(0, str(SRC))
import baseline_ablations as ba  # noqa: E402
import intervention_test as it  # noqa: E402
import prior_shift_reweighting as pr  # noqa: E402

OUT = it.ROOT / "research" / "results" / "label_shift_bbse.json"
LEVELS = [0, 1, 2]


def bbse_weights(train, held, tracker):
    dev = [p for p in train if p["tracker"] == tracker and p["red"]["score"]["modal_decision"] is not None]
    tgt = [p for p in held if p["tracker"] == tracker and p["red"]["score"]["modal_decision"] is not None]
    C = np.zeros((3, 3))
    for p in dev:
        C[int(p["red"]["score"]["modal_decision"]), p["bug"]["level"]] += 1
    C /= len(dev)
    mu = np.array([sum(int(p["red"]["score"]["modal_decision"]) == i for p in tgt) for i in LEVELS], float) / len(tgt)
    info = {"cond": float(np.linalg.cond(C))}
    try:
        w = np.linalg.solve(C, mu)
    except np.linalg.LinAlgError:
        w, *_ = np.linalg.lstsq(C, mu, rcond=None)
        info["singular"] = True
    info["negative_before_clip"] = bool((w < 0).any())
    w = np.clip(w, 0, None)
    p_dev = np.array([sum(p["bug"]["level"] == l for p in dev) for l in LEVELS], float) / len(dev)
    q_est = w * p_dev
    q_est = q_est / q_est.sum() if q_est.sum() > 0 else q_est
    q_true = np.array([sum(p["bug"]["level"] == l for p in tgt) for l in LEVELS], float) / len(tgt)  # reported only
    info.update({"w": [round(float(x), 3) for x in w], "est_level_mix": [round(float(x), 3) for x in q_est],
                 "true_level_mix_reported_only": [round(float(x), 3) for x in q_true]})
    return {l: float(w[l]) for l in LEVELS}, info


def main():
    out = {"status": "EXPLORATORY (addendum I); weights use no held-out labels", "models": {}}
    rw_prev = json.loads(pr.OUT.read_text())["models"]
    ab_prev = json.loads(ba.OUT.read_text())["models"]
    for mname in ["Jev 1.13"] + it.ac.MODELS:
        train, held, _ = it.load_model(mname)
        H = list(held.values())
        wts, info = {}, {}
        for t in ("mozilla", "kernel"):
            wts[t], info[t] = bbse_weights(train, H, t)
        w = [wts[p["tracker"]][p["bug"]["level"]] for p in train]
        m = sum(w) / len(w)
        w = [x / m for x in w]
        res = {"bbse": info}
        for target, fn in ba.TARGETS.items():
            ytr = [fn(p) for p in train]
            sc = StandardScaler().fit([pr.dec_vec(p) for p in train])
            lr = LogisticRegression(C=1.0, max_iter=2000).fit(sc.transform([pr.dec_vec(p) for p in train]), ytr, sample_weight=w)
            rows = [{"tracker": p["tracker"], "y": fn(p), "E_dec_bbse": lr.predict_proba(sc.transform([pr.dec_vec(p)]))[0][1]}
                    for p in H]
            y = [r["y"] for r in rows]
            a_bbse = round(roc_auc_score(y, [r["E_dec_bbse"] for r in rows]), 3)
            a_unw = ab_prev[mname][target]["scores"]["E_dec"]["auroc"]
            a_orc = rw_prev[mname][target]["E_dec_w"]["auroc"]
            conf = rw_prev[mname][target]["conf"]["auroc"]
            gap = a_orc - a_unw
            res[target] = {"unweighted": a_unw, "oracle_weights": a_orc, "bbse": a_bbse,
                           "bbse_ci95": pr.boot_auc(rows, "E_dec_bbse", random.Random(ba.SEED)),
                           "final_step_conf": conf,
                           "recovered": (a_bbse - a_unw) >= 0.5 * gap if gap > 0.02 else None}
        out["models"][mname] = res
        print(mname, {k: (v if k == "bbse" else (v["unweighted"], v["oracle_weights"], v["bbse"], v["recovered"]))
                      for k, v in res.items() if k != "bbse"},
              {t: (i["est_level_mix"], i["true_level_mix_reported_only"], round(i["cond"], 1), i["negative_before_clip"]) for t, i in info.items()},
              flush=True)
    OUT.write_text(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
