"""Intervention test (research/methodology/intervention_test_preregistration.md).
Fixed 10% review budget; strategies ranked from training data only; exact
expectation over ties; frozen cost table. No API or GPU calls.

  python3 research/src/intervention_test.py
"""
from __future__ import annotations

import json
import math
import random
import sys
from collections import defaultdict
from pathlib import Path

SRC = Path(__file__).resolve().parent
ROOT = SRC.parents[1]
sys.path.insert(0, str(SRC))
sys.path.insert(0, str(SRC / "openjev"))
sys.path.insert(0, str(ROOT / "research" / "paper" / "latex"))
import analyze_crossmodel as ac  # noqa: E402
import paper_statistics as ps  # noqa: E402
import run_heldout_validation as hv  # noqa: E402
import workflow_risk_probe as wp  # noqa: E402
from workflow_strategies_r12 import cost  # noqa: E402

BUDGET, B, SEED, ALPHA = 0.10, 2000, 20261017, 0.05
OUT_JSON = ROOT / "research" / "results" / "intervention_test.json"


def load_model(m):
    """(train list, held dict) of per-bug records with s1 / a_star / red / tracker."""
    if m == "Jev 1.13":
        train = []
        for d in ("mozilla", "kernel"):
            for bid, p in ps.load(d).items():
                train.append({"tracker": d, "red": p["red"], "s1": p["s1"], "a_star": p["a_star"], "bug": p["bug"]})
        data = hv.load_heldout()
        held = hv.per_bug(data, [json.loads(line) for line in hv.raw_path(False).open()])
        return train, held, hv.load_estimator()["estimators"]["DECISION"]
    raw = [json.loads(line) for line in (ac.DATA / f"{m.replace('/', '__')}_raw_responses.jsonl").open()]
    P = ac.per_bug(raw, ac.bugs_index())
    train = [p for p in P.values() if p["split"] == "train"]
    held = {k: p for k, p in P.items() if p["split"] == "heldout"}
    feats = [wp.vec({"dec": wp.features(p)[0], "unc": wp.features(p)[1]}, "DECISION") for p in train]
    est = {"features": sorted(wp.features(train[0])[0]),
           **wp.fit(feats, [int(p["s1"] != p["a_star"]) for p in train])}
    return train, held, est


def action_tables(train):
    """Smoothed per-action training means: expected net saving of review, and error rate."""
    sav, err = defaultdict(list), defaultdict(list)
    for p in train:
        a = p["s1"]
        sav[a].append(cost(a, p["a_star"]) - cost("escalate", p["a_star"]))
        err[a].append(int(a != p["a_star"]))
    allsav = [v for vs in sav.values() for v in vs]
    allerr = [v for vs in err.values() for v in vs]
    ms, me = sum(allsav) / len(allsav), sum(allerr) / len(allerr)
    sm = lambda vs, m: (sum(vs) + m) / (len(vs) + 1)
    return ({a: sm(v, ms) for a, v in sav.items()}, ms), ({a: sm(v, me) for a, v in err.items()}, me)


def rows_for(held, tables, est):
    (sav, ms), (err, me) = tables
    rows = []
    for key, p in held.items():
        dec, unc = wp.features(p)
        rows.append({"tracker": p["tracker"], "action": p["s1"], "a_star": p["a_star"],
                     "base_cost": cost(p["s1"], p["a_star"]),
                     "gain": cost(p["s1"], p["a_star"]) - cost("escalate", p["a_star"]),   # cost reduction if reviewed
                     "wrong_accept": int(p["s1"] == "accept" and p["a_star"] != "accept"),
                     "A1": sav.get(p["s1"], ms), "A2": err.get(p["s1"], me),
                     "E": hv.risk(est, p, "DECISION"),
                     "B": -unc["score_conf"],
                     "B2": -(unc["choice_conf"] * unc["noul_conf"] * unc["score_conf"])})
    return rows


def expected_total(rows, col):
    """Total cost after reviewing the top-k candidates by `col` (higher = review first);
    exact expectation over ties at the boundary. col=None -> random (exact)."""
    n = len(rows)
    k = math.ceil(BUDGET * n)
    cand = [r for r in rows if r["action"] != "escalate"]
    base = sum(r["base_cost"] for r in rows)
    k = min(k, len(cand))
    if col is None:
        g = sum(r["gain"] for r in cand) / len(cand) * k
        wa = sum(r["wrong_accept"] for r in cand) / len(cand) * k
        return base - g, wa
    cand = sorted(cand, key=lambda r: -r[col])
    gain = wa = 0.0
    i, taken = 0, 0
    while taken < k:
        j = i
        while j + 1 < len(cand) and cand[j + 1][col] == cand[i][col]:
            j += 1
        group = cand[i:j + 1]
        slots = min(k - taken, len(group))
        frac = slots / len(group)
        gain += frac * sum(r["gain"] for r in group)
        wa += frac * sum(r["wrong_accept"] for r in group)
        taken += slots
        i = j + 1
    return base - gain, wa


def boot_diff(rows, a, b):
    rng = random.Random(SEED)
    groups = defaultdict(list)
    for r in rows:
        groups[r["tracker"]].append(r)
    diffs = []
    for _ in range(B):
        s = [g[rng.randrange(len(g))] for g in groups.values() for _ in g]
        diffs.append(expected_total(s, a)[0] - expected_total(s, b)[0])
    diffs.sort()
    return diffs


def main():
    models = ["Jev 1.13"] + ac.MODELS
    out, pvals = {"status": "pre-registered analysis (intervention_test_preregistration.md)", "models": {}}, {}
    for m in models:
        train, held, est = load_model(m)
        rows = rows_for(held, action_tables(train), est)
        arms = {"A1": "A1", "A2": "A2", "E": "E", "B": "B", "B2": "B2", "C": None}
        res = {"n": len(rows), "k": math.ceil(BUDGET * len(rows)),
               "candidates": sum(r["action"] != "escalate" for r in rows),
               "base_total_cost": sum(r["base_cost"] for r in rows),
               "candidate_actions": {a: sum(1 for r in rows if r["action"] == a) for a in ("accept", "defer", "request_more_evidence")},
               "arms": {}}
        for name, col in arms.items():
            tot, wa = expected_total(rows, col)
            res["arms"][name] = {"total_cost": round(tot, 2), "wrong_accepts_caught": round(wa, 2)}
        for comp in ("C", "B"):
            d = boot_diff(rows, "A1", arms[comp])
            point = res["arms"]["A1"]["total_cost"] - res["arms"][comp]["total_cost"]
            p = sum(v >= 0 for v in d) / len(d)
            res[f"A1_minus_{comp}"] = {"point": round(point, 2), "ci95": [round(d[int(0.025 * B)], 2), round(d[int(0.975 * B) - 1], 2)],
                                       "bootstrap_p_one_sided": round(p, 4)}
            pvals[f"{m}:A1<{comp}"] = p
        out["models"][m] = res
        print(m, json.dumps({k: v for k, v in res.items() if k != "arms"}), {a: v["total_cost"] for a, v in res["arms"].items()})
    order = sorted(pvals, key=pvals.get)
    holm, ok = {}, True
    for i, key in enumerate(order):
        ok = ok and pvals[key] <= ALPHA / (len(order) - i)
        holm[key] = ok
    out["holm_supported"] = holm
    OUT_JSON.write_text(json.dumps(out, indent=2))
    print(json.dumps(holm, indent=1))


if __name__ == "__main__":
    main()
