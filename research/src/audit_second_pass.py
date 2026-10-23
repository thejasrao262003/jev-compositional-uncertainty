"""Addendum J3-J7 of evidence_audit_and_baselines_plan.md. Exploratory; no API or GPU calls.

  .venv/bin/python research/src/audit_second_pass.py
"""
from __future__ import annotations

import json
import random
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
from sklearn.metrics import roc_auc_score

SRC = Path(__file__).resolve().parent
sys.path.insert(0, str(SRC))
import evidence_audit as ea  # noqa: E402
import intervention_cost_sensitivity as ics  # noqa: E402
import intervention_test as it  # noqa: E402
import run_heldout_validation as hv  # noqa: E402
import workflow_risk_probe as wp  # noqa: E402
from build_workflow_calibration_pilot_manifest import F  # noqa: E402

OUT = it.ROOT / "research" / "results" / "audit_second_pass.json"
MODELS = ["Jev 1.13"] + it.ac.MODELS
B = 2000


def bid(p):
    return (p["tracker"], int(p["bug"]["bug_id"]))


def dec_vec(p):
    d, u = wp.features(p)
    return wp.vec({"dec": d, "unc": u}, "DECISION")


def conf(p):
    return -wp.features(p)[1]["score_conf"]


def paired(rows, a, b, seed=7):
    rng = random.Random(seed)
    g = defaultdict(list)
    for r in rows:
        g[r["tracker"]].append(r)
    v = []
    for _ in range(B):
        s = [x[rng.randrange(len(x))] for x in g.values() for _ in x]
        y = [r["y"] for r in s]
        if 0 < sum(y) < len(y):
            v.append(roc_auc_score(y, [r[a] for r in s]) - roc_auc_score(y, [r[b] for r in s]))
    v.sort()
    y = [r["y"] for r in rows]
    return {"auroc_" + a: round(roc_auc_score(y, [r[a] for r in rows]), 3),
            "auroc_" + b: round(roc_auc_score(y, [r[b] for r in rows]), 3),
            "diff": round(roc_auc_score(y, [r[a] for r in rows]) - roc_auc_score(y, [r[b] for r in rows]), 3),
            "ci95": [round(v[int(0.025 * len(v))], 3), round(v[int(0.975 * len(v)) - 1], 3)]}


def score_rows(train, held, ytr, yfn):
    m = wp.fit([dec_vec(p) for p in train], ytr)
    rate = defaultdict(list)
    for p, y in zip(train, ytr):
        rate[p["s1"]].append(y)
    rb = sum(ytr) / len(ytr)
    rr = {a: (sum(v) + rb) / (len(v) + 1) for a, v in rate.items()}
    return [{"tracker": p["tracker"], "y": yfn(p), "E_dec": wp.predict(m, [dec_vec(p)])[0],
             "rule": rr.get(p["s1"], rb), "conf": conf(p)} for p in held]


# ---------- J3 grouped refit
def components():
    links = json.loads(ea.CACHE.read_text())
    ids = ea.ids()
    nodes = {(t, b) for t, d in ids.items() for b in d["dev"] + d["held"]}
    parent = {n: n for n in nodes}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    for t in ids:
        for b, rec in links[t].items():
            for x in ea.linked_ids(rec, t):
                a, c = (t, int(b)), (t, x)
                if a in nodes and c in nodes:
                    parent[find(a)] = find(c)
    held = {(t, b) for t, d in ids.items() for b in d["held"]}
    dev = {(t, b) for t, d in ids.items() for b in d["dev"]}
    comp_h = {find(n) for n in held}
    comp_d = {find(n) for n in dev}
    mixed = comp_h & comp_d
    return {n for n in dev if find(n) in mixed}, {n for n in held if find(n) in mixed}


# ---------- J4 mappings
def remap(p, mapping):
    b = dict(p["bug"])
    t = p["tracker"]
    if mapping == "m1" and t == "mozilla":
        b["level"] = {"S1": 2, "S2": 1, "S3": 1, "S4": 0}[b["severity"]]
    if mapping == "m2" and t == "kernel" and b["severity"] == "normal":
        return None
    if mapping == "m3" and t == "kernel" and b.get("cf_regression") == "---":
        return None
    q = dict(p)
    q["bug"] = b
    q["a_star"] = F(b["regression"], b["level"])
    return q


def main():
    out = {"status": "EXPLORATORY (addendum J)", "J3": {}, "J4": {}, "J5": {}, "J6": {}, "J7": {}}
    drop_dev, drop_held = components()
    out["J3_dropped"] = {"development": len(drop_dev), "held_out": len(drop_held)}
    for m in MODELS:
        train, held, _ = it.load_model(m)
        H = list(held.values())
        yfn = lambda p: int(p["s1"] != p["a_star"])
        # J3
        tr = [p for p in train if bid(p) not in drop_dev]
        he = [p for p in H if bid(p) not in drop_held]
        out["J3"][m] = {"n_train": len(tr), "n_held": len(he),
                        **paired(score_rows(tr, he, [yfn(p) for p in tr], yfn), "E_dec", "conf")}
        # J4
        out["J4"][m] = {}
        for mp in ("m1", "m2", "m3"):
            tr2 = [q for q in (remap(p, mp) for p in train) if q]
            he2 = [q for q in (remap(p, mp) for p in H) if q]
            rows = score_rows(tr2, he2, [yfn(p) for p in tr2], yfn)
            out["J4"][m][mp] = {"n_train": len(tr2), "n_held": len(he2), "E_dec_vs_conf": paired(rows, "E_dec", "conf"),
                                "rule_vs_conf": paired(rows, "rule", "conf")}
        # J5 within accepted cases
        rows = score_rows(train, H, [yfn(p) for p in train], yfn)
        acc = [(p, r) for p, r in zip(H, rows) if p["s1"] == "accept"]
        y = [int(p["a_star"] != "accept") for p, _ in acc]
        if 0 < sum(y) < len(y):
            out["J5"][m] = {"n_accepted": len(acc), "wrong_accepts": sum(y),
                            "auroc_E_dec": round(roc_auc_score(y, [r["E_dec"] for _, r in acc]), 3),
                            "auroc_rule": round(roc_auc_score(y, [r["rule"] for _, r in acc]), 3),
                            "auroc_conf": round(roc_auc_score(y, [r["conf"] for _, r in acc]), 3),
                            "auroc_p_level2": round(roc_auc_score(y, [wp.features(p)[1]["score_p2"] for p, _ in acc]), 3)}
        # J7 reviewer accuracy (frozen rankings); rho=1 reproduces the pre-registered table
        base_rows = it.rows_for(held, it.action_tables(train), it.load_model(m)[2])
        out["J7"][m] = {}
        for (mm, hh) in ((1, 1), (2, 1)):
            rs = ics.rescore(base_rows, mm, hh)
            for rho in (1.0, 0.9, 0.8):
                rr = [dict(r, gain=rho * r["gain"] - (1 - rho) * hh) for r in rs]
                base = sum(r["base_cost"] for r in rr)
                arms = {a: it.expected_total(rr, None if a == "C" else a)[0] for a in ics.ARMS}
                best = min(arms, key=arms.get)
                out["J7"][m][f"m={mm},h={hh},rho={rho}"] = {"best_arm": best, "best_minus_no_review": round(arms[best] - base, 1)}
    # J6 synthetic BBSE (Jev, OpenJev)
    rng = np.random.default_rng(20261023)
    for m in ("Jev 1.13", "openjev/openjev-27B"):
        train, held, _ = it.load_model(m)
        dv = [(int(p["red"]["score"]["modal_decision"]), p["bug"]["level"]) for p in train if p["red"]["score"]["modal_decision"] is not None]
        hv_ = [(int(p["red"]["score"]["modal_decision"]), p["bug"]["level"]) for p in held.values() if p["red"]["score"]["modal_decision"] is not None]
        by_lvl = {l: [x for x in hv_ if x[1] == l] for l in range(3)}
        res = {}
        for lam in (0.0, 0.25, 0.5, 0.75):
            def noisy(pairs):
                return [(int(rng.integers(3)) if rng.random() < lam else a, y) for a, y in pairs]
            dvn = noisy(dv)
            C = np.zeros((3, 3))
            for a, y in dvn:
                C[a, y] += 1
            C /= len(dvn)
            p_dev = C.sum(axis=0)
            cond = float(np.linalg.cond(C))
            for s2 in (0.05, 0.10, 0.20, 0.35, 0.50):
                mix = [0.3 * (1 - s2) / 1.3, (1 - s2) / 1.3, s2]
                errs = []
                for _ in range(200):
                    cnt = rng.multinomial(500, mix)
                    samp = [by_lvl[l][i] for l in range(3) for i in rng.integers(0, len(by_lvl[l]), cnt[l])]
                    samp = noisy(samp)
                    mu = np.bincount([a for a, _ in samp], minlength=3) / len(samp)
                    try:
                        v = np.clip(np.linalg.solve(C, mu), 0, None)
                    except np.linalg.LinAlgError:
                        continue
                    q = v * p_dev
                    q = q / q.sum() if q.sum() > 0 else q
                    errs.append(q[2] - s2)
                e = np.array(errs)
                res[f"lambda={lam},level2_share={s2}"] = {"cond": round(cond, 1), "evaluable_cond_le_100": cond <= 100,
                                                          "bias": round(float(e.mean()), 3), "rmse": round(float(np.sqrt((e ** 2).mean())), 3)}
        out["J6"][m] = res
    OUT.write_text(json.dumps(out, indent=2))
    for k in ("J3", "J5"):
        print(k, json.dumps(out[k], indent=0)[:1500])
    print("J4", {m: {mp: (v["E_dec_vs_conf"]["diff"], v["E_dec_vs_conf"]["ci95"]) for mp, v in d.items()} for m, d in out["J4"].items()})
    print("J7", {m: d for m, d in out["J7"].items()})
    print("J6", {m: {k: (v["bias"], v["rmse"], v["cond"]) for k, v in d.items()} for m, d in out["J6"].items()})


if __name__ == "__main__":
    main()
