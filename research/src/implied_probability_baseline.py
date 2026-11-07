"""Model-implied action probability baseline
(research/methodology/implied_probability_baseline_plan.md). Exploratory, post hoc.
No API or GPU calls.

  .venv/bin/python research/src/implied_probability_baseline.py
"""
from __future__ import annotations

import json
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

SRC = Path(__file__).resolve().parent
sys.path.insert(0, str(SRC))
import intervention_test as it  # noqa: E402
import workflow_risk_probe as wp  # noqa: E402
from baseline_ablations import B, SEED, auc  # noqa: E402

OUT = it.ROOT / "research" / "results" / "implied_probability_baseline.json"
SCORES = ["final_step_conf", "action_rule", "implied"]
CONTRASTS = [("action_rule", "implied"), ("implied", "final_step_conf")]
MIN_CLASS = 10


def implied_action_prob(p):
    """P(F(c2, c3) = chosen action) under the model's own mean distributions, nodes independent."""
    probs = p["red"]["score"]["mean_probabilities"] or {}
    pk = [float(probs.get(str(k), 0.0)) for k in range(3)]
    tot = sum(pk)
    pk = [v / tot for v in pk] if tot > 0 else [1 / 3] * 3
    q = p["red"]["noul"]["mean_noul"]
    q = 0.5 if q is None else q
    table = {"escalate": pk[2], "defer": pk[1] * q, "accept": pk[0] + pk[1] * (1 - q)}
    return table.get(p["s1"])


def rows_for(train, held):
    rate = defaultdict(list)
    for p in train:
        rate[p["s1"]].append(int(p["s1"] != p["a_star"]))
    overall = sum(v for vs in rate.values() for v in vs) / sum(len(vs) for vs in rate.values())
    rule = {a: (sum(v) + overall) / (len(v) + 1) for a, v in rate.items()}
    rows, other = [], 0
    for p in held.values():
        _, unc = wp.features(p)
        pa = implied_action_prob(p)
        if pa is None:
            other += 1
        rows.append({"tracker": p["tracker"], "action": p["s1"], "y": int(p["s1"] != p["a_star"]),
                     "final_step_conf": -unc["score_conf"], "action_rule": rule.get(p["s1"], overall),
                     "implied": 0.5 if pa is None else 1 - pa})
    return rows, other


def boot(rows, cols, rng):
    groups = defaultdict(list)
    for r in rows:
        groups[r["tracker"]].append(r)
    out = []
    for _ in range(B):
        s = [g[rng.randrange(len(g))] for g in groups.values() for _ in g]
        out.append({c: auc(s, c) for c in cols})
    return out


def q95(v):
    v = sorted(x for x in v if x == x)
    return [round(v[int(0.025 * len(v))], 3), round(v[int(0.975 * len(v)) - 1], 3)]


def analyse(rows):
    rng = random.Random(SEED)
    bt = boot(rows, SCORES, rng)
    res = {"n": len(rows), "failures": sum(r["y"] for r in rows), "scores": {}, "contrasts": {}, "within_action": {}}
    for c in SCORES:
        res["scores"][c] = {"auroc": round(auc(rows, c), 3), "ci95": q95([b[c] for b in bt])}
    for a, b in CONTRASTS:
        ci = q95([x[a] - x[b] for x in bt])
        res["contrasts"][f"{a}-{b}"] = {"diff": round(auc(rows, a) - auc(rows, b), 3), "ci95": ci,
                                        "excludes_0": ci[0] > 0 or ci[1] < 0}
    for act, n in Counter(r["action"] for r in rows).items():
        sub = [r for r in rows if r["action"] == act]
        pos = sum(r["y"] for r in sub)
        if pos >= MIN_CLASS and len(sub) - pos >= MIN_CLASS:
            bw = boot(sub, ["final_step_conf", "implied"], random.Random(SEED + 1))
            res["within_action"][act] = {"n": n, "failures": pos,
                                         **{c: {"auroc": round(auc(sub, c), 3), "ci95": q95([b[c] for b in bw])}
                                            for c in ("final_step_conf", "implied")}}
    return res


def main():
    out = {"status": "EXPLORATORY, post hoc (plan committed cfb686d before computing); held-out set analysed before",
           "models": {}}
    for m in ["Jev 1.13"] + it.ac.MODELS:
        train, held, _ = it.load_model(m)
        rows, other = rows_for(train, held)
        r = analyse(rows)
        r["actions_without_implied_probability"] = other
        out["models"][m] = r
        print(m, {c: r["scores"][c] for c in SCORES}, {k: (v["diff"], v["ci95"]) for k, v in r["contrasts"].items()},
              {a: (v["n"], v["failures"], v["final_step_conf"]["auroc"], v["implied"]["auroc"])
               for a, v in r["within_action"].items()}, flush=True)
    OUT.write_text(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
