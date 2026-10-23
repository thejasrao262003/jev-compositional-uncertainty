"""Addendum J5 follow-up: bootstrap CIs and paired contrasts for the within-accepted-case AUROCs.
Exploratory; no API calls.   .venv/bin/python research/src/audit_j5_intervals.py"""
import json, random, sys
from collections import defaultdict
from pathlib import Path
from sklearn.metrics import roc_auc_score
SRC = Path(__file__).resolve().parent
sys.path.insert(0, str(SRC))
import audit_second_pass as asp  # noqa: E402
import intervention_test as it  # noqa: E402
import workflow_risk_probe as wp  # noqa: E402
OUT = it.ROOT / "research" / "results" / "audit_j5_intervals.json"
B = 2000
res = {}
for m in ("Jev 1.13", "openjev/openjev-27B", "Qwen/Qwen2.5-7B-Instruct"):
    train, held, _ = it.load_model(m)
    H = list(held.values())
    yfn = lambda p: int(p["s1"] != p["a_star"])
    rows = asp.score_rows(train, H, [yfn(p) for p in train], yfn)
    acc = [{"tracker": p["tracker"], "y": int(p["a_star"] != "accept"), "E_dec": r["E_dec"], "conf": r["conf"],
            "p2": wp.features(p)[1]["score_p2"]} for p, r in zip(H, rows) if p["s1"] == "accept"]
    rng = random.Random(5)
    g = defaultdict(list)
    for r in acc:
        g[r["tracker"]].append(r)
    bs = defaultdict(list)
    for _ in range(B):
        s = [x[rng.randrange(len(x))] for x in g.values() for _ in x]
        y = [r["y"] for r in s]
        if not 0 < sum(y) < len(y):
            continue
        a = {c: roc_auc_score(y, [r[c] for r in s]) for c in ("E_dec", "conf", "p2")}
        for c in a:
            bs[c].append(a[c])
        bs["p2-conf"].append(a["p2"] - a["conf"])
        bs["E_dec-conf"].append(a["E_dec"] - a["conf"])
    q = lambda v: [round(sorted(v)[int(0.025 * len(v))], 3), round(sorted(v)[int(0.975 * len(v)) - 1], 3)]
    y = [r["y"] for r in acc]
    res[m] = {"n_accepted": len(acc), "wrong_accepts": sum(y),
              **{c: {"auroc": round(roc_auc_score(y, [r[c] for r in acc]), 3), "ci95": q(bs[c])} for c in ("E_dec", "conf", "p2")},
              "p2_minus_conf": {"ci95": q(bs["p2-conf"])}, "E_dec_minus_conf": {"ci95": q(bs["E_dec-conf"])}}
    print(m, json.dumps(res[m]))
OUT.write_text(json.dumps(res, indent=2))
