"""Development stage for case-level review targeting
(research/methodology/case_level_review_development_plan.md).

Training bugs only (Mozilla 202 + kernel 240), Jev's existing outputs. The
500 held-out bugs are never loaded. No API or GPU calls.

  .venv/bin/python research/src/case_level_review_dev.py
"""
from __future__ import annotations

import hashlib
import json
import math
import random
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent
sys.path.insert(0, str(SRC))
import intervention_test as it  # noqa: E402
import workflow_risk_probe as wp  # noqa: E402
from workflow_strategies_r12 import cost  # noqa: E402

ps = it.ps
RES = it.ROOT / "research" / "results"
OUT_JSON = RES / "case_level_review_dev.json"
FROZEN = RES / "frozen_case_review_score_v1.json"
L_FEATURES = ["score_p0", "score_p1", "score_p2", "score_conf", "noul_p", "noul_conf", "choice_conf", "score_unstable"]
REPEATS, FOLDS, SEED = 20, 5, 20261017
LOW = -1e9   # rank for non-accepted candidates under P and L


def plug_in(unc):
    """Expected saving of reviewing an accepted case, Jev's probabilities taken as calibrated."""
    p2, p1, q = unc["score_p2"], unc["score_p1"], unc["noul_p"]
    pe, pd = p2, p1 * q
    return 9 * pe + 6 * pd - 2 * (1 - pe - pd)


def l_vector(p):
    dec, unc = wp.features(p)
    f = {**dec, **unc}
    return [f[k] for k in L_FEATURES]


def train_records():
    recs = []
    for d in ("mozilla", "kernel"):
        for bid, p in ps.load(d).items():
            recs.append({"tracker": d, "bug_id": bid, "red": p["red"], "s1": p["s1"], "a_star": p["a_star"], "bug": p["bug"]})
    return recs


def fit_L(recs):
    acc = [p for p in recs if p["s1"] == "accept"]
    return wp.fit([l_vector(p) for p in acc], [int(p["a_star"] != "accept") for p in acc])


def rows(recs, fit_recs, model):
    """Evaluation rows; A1 and L use only `fit_recs`."""
    (sav, ms), _ = it.action_tables(fit_recs)
    out = []
    for p in recs:
        dec, unc = wp.features(p)
        acc = p["s1"] == "accept"
        out.append({"tracker": p["tracker"], "action": p["s1"], "a_star": p["a_star"],
                    "base_cost": cost(p["s1"], p["a_star"]),
                    "gain": cost(p["s1"], p["a_star"]) - cost("escalate", p["a_star"]),
                    "wrong_accept": int(acc and p["a_star"] != "accept"),
                    "A1": sav.get(p["s1"], ms), "B": -unc["score_conf"],
                    "P": plug_in(unc) if acc else LOW,
                    "L": wp.predict(model, [l_vector(p)])[0] if (acc and model) else LOW})
    return out


def auc_wrong_accept(rs, col):
    acc = [r for r in rs if r["action"] == "accept"]
    pos = [r[col] for r in acc if r["wrong_accept"]]
    neg = [r[col] for r in acc if not r["wrong_accept"]]
    s = sum((x > y) + 0.5 * (x == y) for x in pos for y in neg)
    return s / (len(pos) * len(neg))


def summary(rs):
    base = sum(r["base_cost"] for r in rs)
    cand = [r for r in rs if r["action"] != "escalate"]
    k = min(math.ceil(it.BUDGET * len(rs)), len(cand))
    oracle = base - sum(sorted((r["gain"] for r in cand), reverse=True)[:k])
    out = {"n": len(rs), "k": k, "no_review": base, "oracle": oracle}
    for col in ("P", "L", "A1", "B", None):
        tot, wa = it.expected_total(rs, col)
        name = col or "C"
        out[name] = {"cost": round(tot, 2), "wrong_accepts_caught": round(wa, 2),
                     "share_of_oracle_saving": round((base - tot) / (base - oracle), 3) if base > oracle else None}
    for col in ("P", "L", "B"):
        out[col]["auroc_wrong_accept_among_accepts"] = round(auc_wrong_accept(rs, col), 3)
    return out


def main():
    recs = train_records()
    assert len(recs) == 442
    out = {"status": "DEVELOPMENT (training bugs only; held-out 500 never loaded)",
           "plan": "research/methodology/case_level_review_development_plan.md"}

    # In-sample: P has no parameters; L in-sample is shown for reference only.
    out["in_sample_all_442"] = summary(rows(recs, recs, fit_L(recs)))

    # Cross-tracker.
    out["cross_tracker"] = {}
    for test, train in (("kernel", "mozilla"), ("mozilla", "kernel")):
        te = [p for p in recs if p["tracker"] == test]
        tr = [p for p in recs if p["tracker"] == train]
        out["cross_tracker"][f"fit_{train}_eval_{test}"] = summary(rows(te, tr, fit_L(tr)))

    # Repeated stratified 5-fold, pooled out-of-fold scores.
    rng = random.Random(SEED)
    rep = []
    for _ in range(REPEATS):
        fold_of = {}
        for t in ("mozilla", "kernel"):
            ids = [p["bug_id"] for p in recs if p["tracker"] == t]
            rng.shuffle(ids)
            for i, b in enumerate(ids):
                fold_of[(t, b)] = i % FOLDS
        oof = []
        for f in range(FOLDS):
            te = [p for p in recs if fold_of[(p["tracker"], p["bug_id"])] == f]
            tr = [p for p in recs if fold_of[(p["tracker"], p["bug_id"])] != f]
            oof += rows(te, tr, fit_L(tr))
        rep.append(summary(oof))
    out["repeated_5fold"] = {
        name: {"mean_cost": round(sum(r[name]["cost"] for r in rep) / REPEATS, 2),
               "min_cost": min(r[name]["cost"] for r in rep), "max_cost": max(r[name]["cost"] for r in rep)}
        for name in ("P", "L", "A1", "B", "C")}
    out["repeated_5fold"]["no_review"] = rep[0]["no_review"]
    out["repeated_5fold"]["oracle"] = rep[0]["oracle"]

    # Selection rule (plan): L replaces P only if lower cost in both cross-tracker
    # directions AND in the repeated 5-fold mean.
    ct = out["cross_tracker"].values()
    l_wins = all(s["L"]["cost"] < s["P"]["cost"] for s in ct) and \
        out["repeated_5fold"]["L"]["mean_cost"] < out["repeated_5fold"]["P"]["mean_cost"]
    chosen = "L" if l_wins else "P"
    out["selection"] = {"chosen": chosen, "rule": "L only if better than P in both cross-tracker directions and 5-fold mean"}
    frozen = {"score": chosen, "applies_to": "accepted cases only; every non-accepted candidate ranks below every accepted case",
              "budget": it.BUDGET, "frozen_on": "2026-10-17, 442 training bugs, before any fresh bug exists"}
    if chosen == "P":
        frozen["definition"] = "9*p2 + 6*p1*q - 2*(1 - p2 - p1*q); p2/p1 = score mean_probabilities['2']/['1'], q = noul mean_noul"
    else:
        frozen.update({"features": L_FEATURES, **fit_L(recs)})
    FROZEN.write_text(json.dumps(frozen, indent=2))
    h = hashlib.sha256(FROZEN.read_bytes()).hexdigest()
    FROZEN.with_suffix(".json.sha256").write_text(f"{h}  {FROZEN.name}\n")
    out["selection"]["frozen_file"] = str(FROZEN.relative_to(it.ROOT))
    out["selection"]["sha256"] = h
    OUT_JSON.write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
