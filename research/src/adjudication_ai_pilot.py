"""AI-judge pilot (human_target_validation_protocol.md, Amendment 1). Exploratory. No API calls.
  .venv/bin/python research/src/adjudication_ai_pilot.py"""
import csv, json, math, random, sys
from collections import Counter
from pathlib import Path
SRC = Path(__file__).resolve().parent
sys.path.insert(0, str(SRC))
import intervention_test as it  # noqa: E402
from build_workflow_calibration_pilot_manifest import F  # noqa: E402
ROOT = SRC.parents[1]
ADJ = ROOT / "research" / "data" / "adjudication"
OUT = ROOT / "research" / "results" / "adjudication_ai_pilot.json"


def wilson(k, n, z=1.96):
    if n == 0:
        return None
    p = k / n; d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [round(c - h, 3), round(c + h, 3)]


def kappa(a, b):
    n = len(a); po = sum(x == y for x, y in zip(a, b)) / n
    ca, cb = Counter(a), Counter(b)
    pe = sum(ca[k] * cb[k] for k in set(a) | set(b)) / (n * n)
    return (po - pe) / (1 - pe) if pe < 1 else float("nan")


key = json.loads((ADJ / "key_DO_NOT_OPEN_UNTIL_RATED.json").read_text())
labels = {}
for t in ("mozilla", "kernel"):
    for l in (ROOT / "research" / "data" / "heldout" / f"{t}_heldout.jsonl").open():
        b = json.loads(l); labels[(t, b["bug_id"])] = b
_, held, _ = it.load_model("Jev 1.13")
ai = {r["code"]: r["action"] for r in csv.DictReader((ADJ / "ratings_AI_pilot.tsv").open(), delimiter="\t")}
rows = []
for code, k in key.items():
    t, bid = k["tracker"], k["bug_id"]
    b = labels[(t, bid)]
    rows.append({"code": code, "tracker": t, "a_star": F(b["regression"], b["level"]), "ai": ai[code],
                 "jev": held[(t, bid)]["s1"], "level": b["level"], "regression": b["regression"]})
out = {"status": "EXPLORATORY AI-judge pilot (Amendment 1); not the pre-registered human validation",
       "n": len(rows), "cant_tell": sum(r["ai"] == "request_evidence" for r in rows),
       "target_mix": dict(Counter(r["a_star"] for r in rows))}
for name, dmap in (("R1_defer_as_defer", {"defer": "defer"}), ("R2_defer_as_accept", {"defer": "accept"})):
    R = [r for r in rows if r["ai"] != "request_evidence"]
    hum = [dmap.get(r["ai"], r["ai"]) for r in R]
    tgt = [r["a_star"] for r in R]
    k = sum(h == t for h, t in zip(hum, tgt))
    rng = random.Random(1); ks = []
    for _ in range(2000):
        idx = [rng.randrange(len(R)) for _ in R]
        v = kappa([hum[i] for i in idx], [tgt[i] for i in idx])
        if v == v:
            ks.append(v)
    ks.sort()
    conf = Counter(f"target={t} / ai={h}" for h, t in zip(hum, tgt))
    jev_wrong = [r["jev"] != r["a_star"] for r in R]
    jev_wrong_ai = [r["jev"] != h for r, h in zip(R, hum)]
    out[name] = {"n_rated": len(R), "agree_with_a_star": k, "agreement": round(k / len(R), 3), "wilson95": wilson(k, len(R)),
                 "kappa": round(kappa(hum, tgt), 3), "kappa_ci95": [round(ks[int(.025 * len(ks))], 3), round(ks[int(.975 * len(ks)) - 1], 3)],
                 "confusion": dict(sorted(conf.items())),
                 "jev_failure_label_agreement": round(sum(x == y for x, y in zip(jev_wrong, jev_wrong_ai)) / len(R), 3),
                 "jev_wrong_vs_a_star": sum(jev_wrong), "jev_wrong_vs_ai": sum(jev_wrong_ai)}
OUT.write_text(json.dumps(out, indent=2))
print(json.dumps(out, indent=1))
