"""EXPLORATORY probe: can a learned workflow-risk estimator predict when the
decision-based workflow action is wrong, better than simple confidence
aggregates? No API calls; uses the committed Mozilla and kernel raw responses.

Status: exploratory and post-hoc on data the paper already reports. It is
NOT part of the paper and sets nothing for any pre-registered study. All
choices below were fixed before the first run and are not tuned:
  - target: S1's action (F on the node decisions) differs from a*;
  - model: L2-regularized logistic regression, lambda = 1.0, standardized
    features, plain gradient descent (no library);
  - within-tracker: stratified 5-fold CV repeated 20 times (seeded);
  - cross-tracker: train on one tracker, test on the other (H3-style shift);
  - feature sets: DECISION (what the nodes decided), UNCERTAINTY (confidence,
    distributions, repeat spread/stability), ALL;
  - baselines: low final-step (score) confidence, low minimum confidence,
    low product, random.

Caveat: both datasets are balanced by design (40 per cell), so a model that
learns P(error | decision) partly learns the sampling design. The
cross-tracker test is the guard against that.

  python3 research/src/workflow_risk_probe.py
"""
from __future__ import annotations

import json
import math
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "paper" / "latex"))
sys.path.insert(0, str(ROOT / "research" / "src"))
import paper_statistics as ps  # noqa: E402
from mozilla_exploratory_analysis import auroc  # noqa: E402

LAMBDA, LR, ITERS, FOLDS, REPEATS, SEED = 1.0, 0.1, 1500, 5, 20, 20261017
OUT = ROOT / "research" / "results" / "workflow_risk_probe.json"


def features(p) -> tuple[dict, dict]:
    r = p["red"]
    ch, nl, sc = r["choice"], r["noul"], r["score"]
    cprobs = list((ch["mean_probabilities"] or {}).values()) or [0.5, 0.5]
    sp = sc["mean_probabilities"] or {"0": 1 / 3, "1": 1 / 3, "2": 1 / 3}
    s = [sp.get(k, 0.0) for k in ("0", "1", "2")]
    ent = -sum(x * math.log(x) for x in s if x > 0)
    m = nl["mean_noul"] if nl["mean_noul"] is not None else 0.5
    sdec = sc["modal_decision"]
    dec = {"score_dec0": float(sdec == "0"), "score_dec2": float(sdec == "2"),
           "score_unstable": float(sdec is None), "noul_dec": float(nl["decision"] == 1),
           "act_escalate": float(p["s1"] == "escalate"), "act_defer": float(p["s1"] == "defer")}
    unc = {"choice_conf": ch["mean_confidence"] or 0.0, "choice_pmax": max(cprobs),
           "choice_unstable": float(not ch["stable"]),
           "noul_p": m, "noul_conf": 2 * abs(m - 0.5), "noul_spread": nl["spread"] or 0.0,
           "score_conf": sc["mean_confidence"] or 0.0, "score_p0": s[0], "score_p1": s[1], "score_p2": s[2],
           "score_entropy": ent, "score_expected": s[1] + 2 * s[2]}
    return dec, unc


def build(dataset):
    per = ps.load(dataset)
    rows = []
    for i, p in per.items():
        dec, unc = features(p)
        cp = (unc["choice_conf"] * unc["noul_conf"] * unc["score_conf"])
        rows.append({"id": i, "y": float(p["s1"] != p["a_star"]), "dec": dec, "unc": unc,
                     "base_score": -unc["score_conf"],
                     "base_min": -min(unc["choice_conf"], unc["noul_conf"], unc["score_conf"]),
                     "base_product": -cp})
    return rows


def vec(row, kind):
    if kind == "DECISION":
        d = row["dec"]
    elif kind == "UNCERTAINTY":
        d = row["unc"]
    else:
        d = {**row["dec"], **row["unc"]}
    return [d[k] for k in sorted(d)]


def fit(X, y):
    n, k = len(X), len(X[0])
    mu = [sum(x[j] for x in X) / n for j in range(k)]
    sd = [math.sqrt(sum((x[j] - mu[j]) ** 2 for x in X) / n) or 1.0 for j in range(k)]
    Z = [[(x[j] - mu[j]) / sd[j] for j in range(k)] for x in X]
    w, b = [0.0] * k, 0.0
    for _ in range(ITERS):
        gw, gb = [0.0] * k, 0.0
        for z, t in zip(Z, y):
            s = b + sum(wj * zj for wj, zj in zip(w, z))
            pr = 1 / (1 + math.exp(-max(-30, min(30, s))))
            e = pr - t
            gb += e
            for j in range(k):
                gw[j] += e * z[j]
        b -= LR * gb / n
        w = [wj - LR * (gwj / n + LAMBDA * wj / n) for wj, gwj in zip(w, gw)]
    return {"mu": mu, "sd": sd, "w": w, "b": b}


def predict(model, X):
    out = []
    for x in X:
        z = [(xj - m) / s for xj, m, s in zip(x, model["mu"], model["sd"])]
        out.append(model["b"] + sum(wj * zj for wj, zj in zip(model["w"], z)))
    return out


def risk_at_coverage(scores, y, coverage=0.8):
    """Failure rate among the `coverage` share of instances judged safest."""
    order = sorted(range(len(y)), key=lambda i: scores[i])
    keep = order[: int(round(coverage * len(y)))]
    return sum(y[i] for i in keep) / len(keep)


def boot_ci(scores, y, rng, B=2000):
    vals = []
    n = len(y)
    for _ in range(B):
        idx = [rng.randrange(n) for _ in range(n)]
        a = auroc([scores[i] for i in idx], [bool(y[i]) for i in idx])
        if a is not None:
            vals.append(a)
    vals.sort()
    return [round(vals[int(0.025 * len(vals))], 3), round(vals[int(0.975 * len(vals)) - 1], 3)]


def cv_oof(rows, kind, rng):
    """Out-of-fold risk scores, stratified folds, one repeat."""
    pos = [i for i, r in enumerate(rows) if r["y"]]
    neg = [i for i, r in enumerate(rows) if not r["y"]]
    rng.shuffle(pos)
    rng.shuffle(neg)
    folds = [pos[f::FOLDS] + neg[f::FOLDS] for f in range(FOLDS)]
    oof = [0.0] * len(rows)
    for f in range(FOLDS):
        test = set(folds[f])
        tr = [i for i in range(len(rows)) if i not in test]
        model = fit([vec(rows[i], kind) for i in tr], [rows[i]["y"] for i in tr])
        for i, s in zip(sorted(test), predict(model, [vec(rows[i], kind) for i in sorted(test)])):
            oof[i] = s
    return oof


def main():
    data = {d: build(d) for d in ("mozilla", "kernel")}
    out = {"status": "EXPLORATORY / POST-HOC - not part of the paper; sets no pre-registered constant",
           "settings": {"lambda": LAMBDA, "folds": FOLDS, "repeats": REPEATS, "seed": SEED}}
    for d, rows in data.items():
        rng = random.Random(f"{SEED}:{d}")
        y = [r["y"] for r in rows]
        res = {"n": len(rows), "failure_rate": round(sum(y) / len(y), 3), "within_tracker_cv": {}, "baselines": {}}
        for base in ("base_score", "base_min", "base_product"):
            sc = [r[base] for r in rows]
            res["baselines"][base] = {"auroc": round(auroc(sc, [bool(t) for t in y]), 3), "ci95": boot_ci(sc, y, rng),
                                      "risk_at_80pct_coverage": round(risk_at_coverage(sc, y), 3)}
        for kind in ("DECISION", "UNCERTAINTY", "ALL"):
            aucs, risks, first = [], [], None
            for rep in range(REPEATS):
                oof = cv_oof(rows, kind, random.Random(f"{SEED}:{d}:{kind}:{rep}"))
                aucs.append(auroc(oof, [bool(t) for t in y]))
                risks.append(risk_at_coverage(oof, y))
                if first is None:
                    first = oof
            res["within_tracker_cv"][kind] = {"auroc_mean": round(sum(aucs) / len(aucs), 3),
                                              "auroc_range_over_repeats": [round(min(aucs), 3), round(max(aucs), 3)],
                                              "auroc_ci95_repeat0": boot_ci(first, y, rng),
                                              "risk_at_80pct_coverage_mean": round(sum(risks) / len(risks), 3)}
        out[d] = res
    # cross-tracker transfer
    out["cross_tracker"] = {}
    for tr, te in (("mozilla", "kernel"), ("kernel", "mozilla")):
        rng = random.Random(f"{SEED}:x:{tr}")
        y = [r["y"] for r in data[te]]
        out["cross_tracker"][f"train_{tr}_test_{te}"] = {}
        for kind in ("DECISION", "UNCERTAINTY", "ALL"):
            model = fit([vec(r, kind) for r in data[tr]], [r["y"] for r in data[tr]])
            sc = predict(model, [vec(r, kind) for r in data[te]])
            out["cross_tracker"][f"train_{tr}_test_{te}"][kind] = {
                "auroc": round(auroc(sc, [bool(t) for t in y]), 3), "ci95": boot_ci(sc, y, rng),
                "risk_at_80pct_coverage": round(risk_at_coverage(sc, y), 3)}
    OUT.write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
