"""Bounded training-only budget check
(research/methodology/case_level_review_budget_check.md).

Frozen score P, frozen cost table, natural mix; only the review budget varies.
Outer resampling of the training bugs propagates uncertainty in the error
distribution and in P's ranking. No API or GPU calls; held-out outputs not loaded.

  .venv/bin/python research/src/case_level_review_budget_check.py
"""
from __future__ import annotations

import json
import math
import random
import sys
from collections import Counter
from pathlib import Path

SRC = Path(__file__).resolve().parent
sys.path.insert(0, str(SRC))
import case_level_review_dev as dev  # noqa: E402
import case_level_review_power as pw  # noqa: E402

OUT = dev.it.ROOT / "research" / "results" / "case_level_review_budget_check.json"
BUDGETS = [0.01, 0.02, 0.03, 0.05, 0.075, 0.10]
SIZES = [500, 750, 1000]          # total fresh bugs (half per tracker)
SIMS, B_INNER, ALPHA, POWER = 400, 300, 0.05, 0.80


def savings(rows, ks):
    """{k: expected total gain from reviewing the top-k candidates by P}, exact over ties."""
    cand = sorted((r for r in rows if r["action"] != "escalate"), key=lambda r: -r["P"])
    out, gain, taken, i = {}, 0.0, 0, 0
    todo = sorted(set(ks))
    while todo:
        if i >= len(cand):
            for k in todo:
                out[k] = gain
            break
        j = i
        while j + 1 < len(cand) and cand[j + 1]["P"] == cand[i]["P"]:
            j += 1
        g, size = sum(r["gain"] for r in cand[i:j + 1]), j - i + 1
        while todo and todo[0] <= taken + size:
            k = todo.pop(0)
            out[k] = gain + g * (k - taken) / size
        gain, taken, i = gain + g, taken + size, j + 1
    return out


def main():
    recs = dev.train_records()
    rs = dev.rows(recs, recs, None)
    by_t = {t: [(i, rs[i]) for i, p in enumerate(recs) if p["tracker"] == t] for t in ("mozilla", "kernel")}
    nat = {t: pw.natural_mix(t) for t in by_t}
    cell = lambda i: (recs[i]["bug"]["group"], str(recs[i]["bug"]["level"]))
    rng = random.Random(dev.SEED + 1)
    out = {"status": "TRAINING-ONLY DESIGN CHECK (see methodology/case_level_review_budget_check.md)",
           "budgets": BUDGETS, "results": {}}
    for n in SIZES:
        ks = {b: math.ceil(b * n) for b in BUDGETS}
        sav_pts = {b: [] for b in BUDGETS}
        wins = Counter()
        for _ in range(SIMS):
            sample = []
            for t, items in by_t.items():
                pop = [items[rng.randrange(len(items))] for _ in items]          # population uncertainty
                cnt = Counter(cell(i) for i, _ in pop)
                w = [nat[t].get(cell(i), 0.0) / cnt[cell(i)] for i, _ in pop]
                sample += [r for _, r in rng.choices(pop, weights=w, k=n // 2)]
            pt = savings(sample, ks.values())
            for b in BUDGETS:
                sav_pts[b].append(-pt[ks[b]])                                      # cost(P) - cost(no review)
            groups = [[r for r in sample if r["tracker"] == t] for t in by_t]
            ge = Counter()
            for _ in range(B_INNER):
                s = [g[rng.randrange(len(g))] for g in groups for _ in g]
                bs = savings(s, ks.values())
                for b in BUDGETS:
                    ge[b] += (-bs[ks[b]]) >= 0
            for b in BUDGETS:
                wins[b] += ge[b] / B_INNER <= ALPHA
        res = {}
        for b in BUDGETS:
            v = sorted(sav_pts[b])
            res[f"{b:.3f}"] = {"k": ks[b], "power": round(wins[b] / SIMS, 3),
                               "median_cost_change_vs_no_review": round(v[len(v) // 2], 1),
                               "central_80pct": [round(v[int(0.1 * len(v))], 1), round(v[int(0.9 * len(v)) - 1], 1)],
                               "share_of_sims_where_review_pays": round(sum(x < 0 for x in v) / len(v), 3)}
        out["results"][str(n)] = res
        print(n, json.dumps(res), flush=True)

    viable = []
    for b in BUDGETS:
        for n in SIZES:
            r = out["results"][str(n)][f"{b:.3f}"]
            if r["power"] >= POWER and r["median_cost_change_vs_no_review"] < 0:
                viable.append((n, -b))
                break
    if viable:
        n, nb = min(viable)
        out["decision"] = {"viable": True, "budget": -nb, "n": n,
                           "next": "write a confirmatory pre-registration; no calls until it is committed"}
    else:
        out["decision"] = {"viable": False, "next": "STOP (binding): report findings; no further designs, no API calls"}
    print(json.dumps(out["decision"]))
    OUT.write_text(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
