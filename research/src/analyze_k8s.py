"""Pre-registered analysis for research/methodology/independent_workflow_preregistration.md (v1).
No API or GPU calls.

  python3 research/src/analyze_k8s.py --selftest     synthetic end-to-end check
  python3 research/src/analyze_k8s.py                analysis of collected Jev outputs
"""
from __future__ import annotations

import argparse
import json
import math
import random
import sys
import zlib
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.preprocessing import StandardScaler

SRC = Path(__file__).resolve().parent
sys.path.insert(0, str(SRC))
import workflow_risk_probe as wp  # noqa: E402
from build_workflow_calibration_pilot_manifest import F  # noqa: E402
from run_workflow_calibration_pilot import (reduce_choice_or_score_cell, reduce_noul_cell,  # noqa: E402
                                            strategy_1_decision_only)
from workflow_strategies_r12 import cost  # noqa: E402

ROOT = SRC.parents[1]
DATA = ROOT / "research" / "data" / "k8s"
RES = ROOT / "research" / "results"
B, ALPHA = 2000, 0.05
SEED_K = zlib.crc32(b"k8s-K")
SEED_Q = zlib.crc32(b"k8s-quota")
COND_MAX = 100.0
ARMS = ("choice", "noul", "score")


# ------------------------------------------------------------ per-issue reduction
def per_issue(dataset, raw):
    by = defaultdict(lambda: defaultdict(list))
    for r in raw:
        by[r["number"]][r["arm"]].append(r)
    out, failed = [], []
    for d in dataset:
        if d["split"] == "calibration":
            continue
        arms = by.get(d["number"])
        if not arms or any(len(arms.get(a, [])) != 3 for a in ARMS):
            failed.append(d["number"])
            continue
        ch, nl, sc = reduce_choice_or_score_cell(arms["choice"]), reduce_noul_cell(arms["noul"]), reduce_choice_or_score_cell(arms["score"])
        if nl["decision"] is None or ch["n_valid_responses"] == 0 or sc["n_valid_responses"] == 0:
            failed.append(d["number"])
            continue
        a = strategy_1_decision_only(ch["modal_decision"], nl, sc)
        p = {**d, "red": {"choice": ch, "noul": nl, "score": sc}, "s1": a, "a_star": F(d["bug"], d["level"])}
        c3 = sc["modal_decision"]
        p["y_wrong_action"] = int(a != p["a_star"])
        p["y_priority_wrong"] = int(c3 is None or int(c3) != d["level"])
        p["y_any_node_wrong"] = int(ch["modal_decision"] != d["sig"] or nl["decision"] != d["bug"] or p["y_priority_wrong"])
        out.append(p)
    return out, failed


# ------------------------------------------------------------ scores
def rate_table(dev, y="y_wrong_action"):
    rbar = sum(p[y] for p in dev) / len(dev)
    g = defaultdict(list)
    for p in dev:
        g[p["s1"]].append(p[y])
    return {a: (sum(v) + rbar) / (len(v) + 1) for a, v in g.items()}, rbar


def conf_risk(p):
    c = p["red"]["score"]["mean_confidence"]
    return -(c if c is not None else 0.0)


def dec_vec(p):
    dec, unc = wp.features(p)
    return wp.vec({"dec": dec, "unc": unc}, "DECISION")


def all_vec(p):
    dec, unc = wp.features(p)
    return wp.vec({"dec": dec, "unc": unc}, "ALL")


def auc(y, s):
    return roc_auc_score(y, s) if 0 < sum(y) < len(y) else float("nan")


def paired_boot(y, s1, s0, seed):
    """one-sided p for AUROC(s1) - AUROC(s0) > 0 (s0=None -> vs 0.5), and 95% percentile CI."""
    rng = random.Random(seed)
    n = len(y)
    y, s1 = np.asarray(y), np.asarray(s1)
    s0 = None if s0 is None else np.asarray(s0)
    d = []
    for _ in range(B):
        i = np.array([rng.randrange(n) for _ in range(n)])
        yy = y[i]
        if 0 < yy.sum() < n:
            d.append(auc(yy, s1[i]) - (0.5 if s0 is None else auc(yy, s0[i])))
    d.sort()
    p = sum(x <= 0 for x in d) / len(d)
    return {"p_one_sided": round(p, 4), "ci95": [round(d[int(0.025 * len(d))], 4), round(d[int(0.975 * len(d)) - 1], 4)]}


def holm(pvals):
    order = sorted(pvals, key=pvals.get)
    ok, res = True, {}
    for i, k in enumerate(order):
        ok = ok and pvals[k] <= ALPHA / (len(order) - i)
        res[k] = ok
    return res


# ------------------------------------------------------------ K3 arms
def quota_subsample(dev):
    rng = random.Random(SEED_Q)
    g = defaultdict(list)
    for p in sorted(dev, key=lambda p: p["number"]):
        g[p["level"]].append(p)
    m = min(len(v) for v in g.values())
    out = []
    for lvl in sorted(g):
        out += rng.sample(g[lvl], m)
    return out


def bbse(quota, test):
    qs = [p for p in quota if p["red"]["score"]["modal_decision"] is not None]
    ts = [p for p in test if p["red"]["score"]["modal_decision"] is not None]
    C = np.zeros((3, 3))
    for p in qs:
        C[int(p["red"]["score"]["modal_decision"]), p["level"]] += 1
    C /= len(qs)
    mu = np.array([sum(int(p["red"]["score"]["modal_decision"]) == i for p in ts) for i in range(3)], float) / len(ts)
    cond = float(np.linalg.cond(C))
    info = {"cond": cond, "evaluable": cond <= COND_MAX}
    try:
        v = np.linalg.solve(C, mu)
    except np.linalg.LinAlgError:
        info.update(evaluable=False, solve_failed=True)
        return None, info
    info["negative_before_clip"] = bool((v < 0).any())
    v = np.clip(v, 0, None)
    p_q = np.array([sum(p["level"] == l for p in qs) for l in range(3)], float) / len(qs)
    est = v * p_q
    info["estimated_test_mix_stable"] = [round(float(x), 3) for x in (est / est.sum() if est.sum() else est)]
    info["v"] = [round(float(x), 3) for x in v]
    return {l: float(v[l]) for l in range(3)}, info


def fit_arm(quota, weights_by_level, test, y="y_priority_wrong"):
    X = [dec_vec(p) for p in quota]
    w = np.array([weights_by_level[p["level"]] for p in quota]) if weights_by_level else np.ones(len(quota))
    w = w / w.mean() if w.mean() > 0 else w
    sc = StandardScaler().fit(X)
    lr = LogisticRegression(C=1.0, solver="lbfgs", max_iter=2000).fit(sc.transform(X), [p[y] for p in quota], sample_weight=w)
    return lr.predict_proba(sc.transform([dec_vec(p) for p in test]))[:, 1]


# ------------------------------------------------------------ analysis
def d_star(n):
    f = RES / "k8s_power_realized.json"
    if f.exists():
        return json.loads(f.read_text())["d_star"]
    return 0.10 if n >= 500 else 0.20


def analyze(dataset, raw):
    P, failed = per_issue(dataset, raw)
    dev = [p for p in P if p["split"] == "development"]
    test = [p for p in P if p["split"] == "test"]
    cal = [d for d in dataset if d["split"] == "calibration"]
    out = {"n": {"development": len(dev), "test": len(test), "failed": failed}}

    rt, rbar = rate_table(dev)
    y = [p["y_wrong_action"] for p in test]
    s_rule = [rt.get(p["s1"], rbar) for p in test]
    s_conf = [conf_risk(p) for p in test]
    k1 = paired_boot(y, s_rule, s_conf, SEED_K)
    k2 = paired_boot(y, s_rule, None, SEED_K + 1)

    # K3
    quota = quota_subsample(dev)
    yq = [p["y_priority_wrong"] for p in test]
    w_b, info_b = bbse(quota, test)
    s_a = fit_arm(quota, None, test)
    k3 = None
    if w_b is not None and info_b["evaluable"]:
        s_b = fit_arm(quota, w_b, test)
        k3 = paired_boot(yq, s_b, s_a, SEED_K + 2)
    qcal = np.array([sum(d["level"] == l for d in cal) + 1 for l in range(3)], float)
    qcal /= qcal.sum()
    pq = np.array([sum(p["level"] == l for p in quota) for l in range(3)], float) / len(quota)
    w_c = {l: float(qcal[l] / pq[l]) for l in range(3)}
    s_c = fit_arm(quota, w_c, test)

    pv = {"K1": k1["p_one_sided"], "K2": k2["p_one_sided"]}
    if k3 is not None:
        pv["K3"] = k3["p_one_sided"]
    H = holm(pv)
    ds = d_star(len(test))
    k1_status = "supported" if H["K1"] else ("not replicated" if k1["ci95"][1] < ds else "inconclusive")
    k3_status = ("not evaluable" if k3 is None else
                 "supported" if H.get("K3") else
                 ("inconclusive (negative estimate)" if auc(yq, fit_arm(quota, w_b, test)) < auc(yq, s_a) else
                  "inconclusive (positive, non-significant)"))
    true_mix = [round(sum(p["level"] == l for p in test if p["red"]["score"]["modal_decision"] is not None) /
                      max(1, sum(1 for p in test if p["red"]["score"]["modal_decision"] is not None)), 3) for l in range(3)]
    out["primary"] = {
        "K1": {"auroc_rule": round(auc(y, s_rule), 4), "auroc_conf": round(auc(y, s_conf), 4), **k1,
               "holm": H["K1"], "d_star": ds, "status": k1_status},
        "K2": {"auroc_rule": round(auc(y, s_rule), 4), **k2, "holm": H["K2"],
               "status": "supported" if H["K2"] else "inconclusive"},
        "K3": {"bbse": info_b, "auroc_arm_a": round(auc(yq, s_a), 4),
               "auroc_arm_b": None if k3 is None else round(auc(yq, fit_arm(quota, w_b, test)), 4),
               **(k3 or {}), "holm": H.get("K3", False), "status": k3_status,
               "true_test_mix_stable_reported_after": true_mix},
        "rate_table": {a: round(v, 4) for a, v in rt.items()}, "overall_dev_error_rate": round(rbar, 4),
    }
    # secondary
    m_dec = wp.fit([dec_vec(p) for p in dev], [p["y_wrong_action"] for p in dev])
    m_all = wp.fit([all_vec(p) for p in dev], [p["y_wrong_action"] for p in dev])
    s_dec = wp.predict(m_dec, [dec_vec(p) for p in test])
    s_all = wp.predict(m_all, [all_vec(p) for p in test])
    sec = {"E_dec_minus_rule": paired_boot(y, s_dec, s_rule, SEED_K + 3),
           "E_all_minus_E_dec": paired_boot(y, s_all, s_dec, SEED_K + 4),
           "auroc_E_dec": round(auc(y, s_dec), 4), "auroc_E_all": round(auc(y, s_all), 4),
           "arm_c_calibration_weights": {"q_cal": [round(float(x), 3) for x in qcal], "auroc": round(auc(yq, s_c), 4)}}
    rt_any, rb_any = rate_table(dev, "y_any_node_wrong")
    ya = [p["y_any_node_wrong"] for p in test]
    sec["any_node"] = {"auroc_rule": round(auc(ya, [rt_any.get(p["s1"], rb_any) for p in test]), 4),
                       "auroc_conf": round(auc(ya, s_conf), 4)}
    rt_nat, rb_nat = rate_table(dev, "y_priority_wrong")
    sec["priority_wrong_natural_dev_rule_auroc"] = round(auc(yq, [rt_nat.get(p["s1"], rb_nat) for p in test]), 4)
    sec["instability_by_label"] = {
        s: {l: round(sum(p["red"]["score"]["modal_decision"] is None for p in S if p["level"] == l) /
                     max(1, sum(1 for p in S if p["level"] == l)), 3) for l in range(3)}
        for s, S in (("quota", quota), ("development", dev))}
    sec["instability_test_overall"] = round(sum(p["red"]["score"]["modal_decision"] is None for p in test) / len(test), 3)
    sec["per_sig"] = {}
    for sig in ("network", "storage", "node"):
        T = [p for p in test if p["sig"] == sig]
        if len(T) >= 50:
            yy = [p["y_wrong_action"] for p in T]
            sec["per_sig"][sig] = {"n": len(T), "auroc_rule": round(auc(yy, [rt.get(p["s1"], rbar) for p in T]), 4),
                                   "auroc_conf": round(auc(yy, [conf_risk(p) for p in T]), 4)}
    early = [p for p in test if all(p["label_times"].get(k) for k in ("sig", "kind", "priority")) and
             max((np.datetime64(p["label_times"][k][:19]) - np.datetime64(p["created_at"][:19])).astype("timedelta64[D]").astype(int)
                 for k in ("sig", "kind", "priority")) <= 30]
    if len(early) >= 30:
        yy = [p["y_wrong_action"] for p in early]
        sec["early_triage"] = {"n": len(early), "auroc_rule": round(auc(yy, [rt.get(p["s1"], rbar) for p in early]), 4),
                               "auroc_conf": round(auc(yy, [conf_risk(p) for p in early]), 4)}
    sec["level0_sublabels"] = {lab: {"n": sum(1 for p in test if p["priority_label"] == lab),
                                     "priority_wrong_rate": round(sum(p["y_priority_wrong"] for p in test if p["priority_label"] == lab) /
                                                                  max(1, sum(1 for p in test if p["priority_label"] == lab)), 3)}
                               for lab in ("important-longterm", "backlog")}
    # hypothetical cost at a 10% budget (frozen table), oracle bound
    base = sum(cost(p["s1"], p["a_star"]) for p in test)
    cand = [p for p in test if p["s1"] != "escalate"]
    k = min(math.ceil(0.10 * len(test)), len(cand))
    gains = sorted((cost(p["s1"], p["a_star"]) - cost("escalate", p["a_star"]) for p in cand), reverse=True)
    sec["hypothetical_cost"] = {"no_review": base, "oracle_at_10pct": base - sum(gains[:k]), "k": k,
                                "note": "frozen cost table, not validated for Kubernetes triage"}
    out["secondary"] = sec
    return out


# ------------------------------------------------------------ selftest
def selftest():
    rng = random.Random(1)
    ds, raw = [], []
    lv_p = [0.5, 0.35, 0.15]
    for i in range(1, 801):
        split = "development" if i <= 350 else ("calibration" if i <= 450 else "test")
        level = rng.choices([0, 1, 2], lv_p)[0]
        bug = int(rng.random() < 0.7)
        sig = rng.choice(["network", "storage", "node"])
        d = {"number": i, "split": split, "sig": sig, "kind": "bug" if bug else "feature", "bug": bug, "level": level,
             "priority_label": "backlog" if level == 0 else "x", "created_at": "2025-01-01T00:00:00Z",
             "label_times": {"sig": "2025-01-02T00:00:00Z", "kind": "2025-01-02T00:00:00Z", "priority": "2025-01-03T00:00:00Z"},
             "text": "t"}
        ds.append(d)
        if split == "calibration":
            continue
        for arm in ARMS:
            for r in (1, 2, 3):
                if arm == "choice":
                    pick = sig if rng.random() < 0.8 else rng.choice(["network", "storage", "node"])
                    ans = {"type": "choice", "choice": pick, "confidence": 0.9,
                           "probabilities": {s: (0.9 if s == pick else 0.05) for s in ("network", "storage", "node")}}
                elif arm == "noul":
                    ans = {"type": "noul", "noul": min(1, max(0, (0.8 if bug else 0.3) + rng.gauss(0, 0.15)))}
                else:
                    sl = level if rng.random() < 0.55 else rng.choice([0, 1, 2])
                    probs = {str(k): (0.7 if k == sl else 0.15) for k in range(3)}
                    ans = {"type": "score", "score": sl, "confidence": rng.uniform(0.4, 0.8), "probabilities": probs}
                raw.append({"number": i, "split": split, "arm": arm, "repeat": r, "http_status": 200,
                            "parsed_response": {"answers": {"q": ans}}})
    res = analyze(ds, raw)
    assert res["n"]["development"] == 350 and res["n"]["test"] == 350
    for k in ("K1", "K2", "K3"):
        assert "status" in res["primary"][k], k
    assert 0 <= res["primary"]["K1"]["auroc_rule"] <= 1
    print("selftest OK", json.dumps({k: res["primary"][k].get("status") for k in ("K1", "K2", "K3")}),
          "K1 auroc rule/conf", res["primary"]["K1"]["auroc_rule"], res["primary"]["K1"]["auroc_conf"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    ds = [json.loads(l) for l in (DATA / "k8s_dataset.jsonl").open()]
    raw = [json.loads(l) for l in (DATA / "k8s_raw_responses.jsonl").open()]
    res = analyze(ds, raw)
    (RES / "k8s_analysis.json").write_text(json.dumps(res, indent=2))
    print(json.dumps(res["primary"], indent=1))


if __name__ == "__main__":
    main()
