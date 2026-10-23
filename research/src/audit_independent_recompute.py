"""Addendum J1: independent re-implementation of the primary held-out result (HR1, HR2)
and the per-tracker contrast (J2). Imports NO project analysis code: only the raw
API responses, the held-out dataset files and the frozen estimator's stored numbers.
Reduction, noul threshold, action rule, targets, features, AUROC and bootstrap are
re-implemented here from the protocol text.

  python3 research/src/audit_independent_recompute.py
"""
from __future__ import annotations

import hashlib
import json
import random
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
HELD = ROOT / "research" / "data" / "heldout"
EST = ROOT / "research" / "results" / "frozen_risk_estimator_v1.json"
EST_SHA = "a7c1e2f1a3748cb54f91d14e50e15dc299d39a6b40f4b0f8d654c989945062ce"
OUT = ROOT / "research" / "results" / "audit_independent_recompute.json"
TIE = 0.02
PAPER = {"HR1_E_dec": 0.763, "HR1_conf": 0.549, "HR1_diff": 0.214, "HR1_lower": 0.158,
         "HR2_moz": 0.811, "HR2_moz_lower": 0.762, "HR2_ker": 0.697, "HR2_ker_lower": 0.648}


def modal(responses):
    """Top-probability label per valid response, skipping responses whose top two probs are within TIE;
    decision = a label chosen by >= 2 of 3. Also returns mean confidence over valid responses."""
    tops, confs = [], []
    for r in responses:
        if r.get("http_status") != 200 or not r.get("parsed_response"):
            continue
        ans = next(iter(r["parsed_response"]["answers"].values()))
        confs.append(ans["confidence"])
        pr = sorted(ans["probabilities"].items(), key=lambda kv: -kv[1])
        if len(pr) >= 2 and abs(pr[0][1] - pr[1][1]) <= TIE:
            continue
        tops.append(pr[0][0])
    best = max(set(tops), key=tops.count) if tops else None
    dec = best if best is not None and tops.count(best) >= 2 else None
    return dec, (sum(confs) / len(confs) if confs else None)


def noul_decision(responses):
    vals = [next(iter(r["parsed_response"]["answers"].values()))["noul"] for r in responses
            if r.get("http_status") == 200 and r.get("parsed_response")]
    return (1 if sum(vals) / len(vals) >= 0.5 else 0) if vals else None


def action(c2, c3):
    """Action rule (protocol §16.2): unstable severity -> escalate (fail-safe); 2 -> escalate;
    1 with regression -> defer; otherwise accept."""
    if c3 is None:
        return "escalate"
    if c3 == 2:
        return "escalate"
    if c3 == 1 and c2 == 1:
        return "defer"
    return "accept"


def auroc(y, s):
    y, s = np.asarray(y), np.asarray(s, float)
    pos, neg = s[y == 1], s[y == 0]
    gt = (pos[:, None] > neg[None, :]).sum()
    eq = (pos[:, None] == neg[None, :]).sum()
    return (gt + 0.5 * eq) / (len(pos) * len(neg))


def main():
    assert hashlib.sha256(EST.read_bytes()).hexdigest() == EST_SHA, "frozen estimator hash mismatch"
    est = json.loads(EST.read_text())["estimators"]["DECISION"]
    labels = {}
    for t in ("mozilla", "kernel"):
        for l in (HELD / f"{t}_heldout.jsonl").open():
            b = json.loads(l)
            labels[(t, b["bug_id"])] = b
    by = defaultdict(lambda: defaultdict(list))
    for l in (HELD / "heldout_raw_responses.jsonl").open():
        r = json.loads(l)
        by[(r["tracker"], r["bug_id"])][r["arm"]].append(r)
    rows = []
    for key, b in labels.items():
        arms = by[key]
        c2 = noul_decision(arms["noul"])
        sdec, sconf = modal(arms["score"])
        c3 = int(sdec) if sdec is not None else None
        a = action(c2, c3)
        target = action(b["regression"], b["level"])
        feat = {"act_defer": float(a == "defer"), "act_escalate": float(a == "escalate"), "noul_dec": float(c2 == 1),
                "score_dec0": float(c3 == 0), "score_dec2": float(c3 == 2), "score_unstable": float(c3 is None)}
        x = [feat[f] for f in est["features"]]
        risk = est["b"] + sum(w * (xi - m) / s for w, xi, m, s in zip(est["w"], x, est["mu"], est["sd"]))
        rows.append({"tracker": key[0], "y": int(a != target), "E_dec": risk, "conf": -(sconf if sconf is not None else 0.0)})

    def boot(R, fn, seed):
        rng = random.Random(seed)
        g = defaultdict(list)
        for r in R:
            g[r["tracker"]].append(r)
        v = []
        for _ in range(2000):
            s = [x[rng.randrange(len(x))] for x in g.values() for _ in x]
            v.append(fn(s))
        return sorted(v)

    A = lambda R, c: auroc([r["y"] for r in R], [r[c] for r in R])
    out = {"n": len(rows), "failure_rate": round(sum(r["y"] for r in rows) / len(rows), 3)}
    d = boot(rows, lambda s: A(s, "E_dec") - A(s, "conf"), 11)
    out["HR1"] = {"E_dec": round(A(rows, "E_dec"), 3), "conf": round(A(rows, "conf"), 3),
                  "diff": round(A(rows, "E_dec") - A(rows, "conf"), 3), "one_sided_95_lower": round(d[int(0.05 * len(d))], 3)}
    for t, k in (("mozilla", "moz"), ("kernel", "ker")):
        R = [r for r in rows if r["tracker"] == t]
        v = boot(R, lambda s: A(s, "E_dec"), 12)
        dd = boot(R, lambda s: A(s, "E_dec") - A(s, "conf"), 13)
        out[f"HR2_{k}"] = {"E_dec": round(A(R, "E_dec"), 3), "one_sided_95_lower": round(v[int(0.05 * len(v))], 3)}
        out[f"J2_{k}"] = {"E_dec": round(A(R, "E_dec"), 3), "conf": round(A(R, "conf"), 3),
                          "diff": round(A(R, "E_dec") - A(R, "conf"), 3),
                          "diff_ci95": [round(dd[int(0.025 * len(dd))], 3), round(dd[int(0.975 * len(dd)) - 1], 3)]}
    comp = {"HR1_E_dec": out["HR1"]["E_dec"], "HR1_conf": out["HR1"]["conf"], "HR1_diff": out["HR1"]["diff"],
            "HR1_lower": out["HR1"]["one_sided_95_lower"], "HR2_moz": out["HR2_moz"]["E_dec"],
            "HR2_moz_lower": out["HR2_moz"]["one_sided_95_lower"], "HR2_ker": out["HR2_ker"]["E_dec"],
            "HR2_ker_lower": out["HR2_ker"]["one_sided_95_lower"]}
    out["comparison_to_paper"] = {k: {"paper": PAPER[k], "independent": v, "abs_diff": round(abs(PAPER[k] - v), 3),
                                      "kind": "bootstrap bound (Monte Carlo; different RNG stream)" if "lower" in k else "point estimate"}
                                  for k, v in comp.items()}
    OUT.write_text(json.dumps(out, indent=2))
    print(json.dumps(out["comparison_to_paper"], indent=1))
    print(json.dumps({k: out[k] for k in ("J2_moz", "J2_ker")}, indent=1))


if __name__ == "__main__":
    main()
