"""Power / sample-size planning for the confirmatory case-level review study.

Simulated fresh batches: training bugs (with Jev's existing outputs) resampled
per tracker with importance weights that move the quota-sampled training mix to
each tracker's NATURAL label mix (group x level), as recorded in the held-out
manifests (label counts only; no held-out Jev output is read). The frozen
score P is applied unchanged. Each simulated study runs the planned paired,
tracker-stratified bootstrap (reduced B) and the planned Holm family.

Assumes Jev behaves within a cell as it did on training bugs. That is an
assumption, stated in the pre-registration. No API or GPU calls.

  .venv/bin/python research/src/case_level_review_power.py
"""
from __future__ import annotations

import json
import random
import sys
from collections import Counter
from pathlib import Path

SRC = Path(__file__).resolve().parent
sys.path.insert(0, str(SRC))
import case_level_review_dev as dev  # noqa: E402
import intervention_test as it  # noqa: E402

HELD = it.ROOT / "research" / "data" / "heldout"
OUT = it.ROOT / "research" / "results" / "case_level_review_power.json"
SIZES = [250, 375, 500]          # per tracker
SIMS, B_INNER, ALPHA = 300, 300, 0.05
COMPARATORS = ["no_review", "A1", "B"]


def natural_mix(tracker):
    m = json.loads((HELD / f"{tracker}_heldout_manifest.json").read_text())["mix"]
    tot = sum(m.values())
    return {tuple(k.replace("level", "").split(":")): v / tot for k, v in m.items()}


def cost_of(rs, arm):
    if arm == "no_review":
        return sum(r["base_cost"] for r in rs)
    return it.expected_total(rs, None if arm == "C" else arm)[0]


def one_study(pools, weights, n, rng):
    sample = []
    for t in pools:
        sample += rng.choices(pools[t], weights=weights[t], k=n)
    point = {c: cost_of(sample, "P") - cost_of(sample, c) for c in COMPARATORS}
    groups = {t: [r for r in sample if r["tracker"] == t] for t in pools}
    ge = {c: 0 for c in COMPARATORS}
    for _ in range(B_INNER):
        s = [g[rng.randrange(len(g))] for g in groups.values() for _ in g]
        p = cost_of(s, "P")
        for c in COMPARATORS:
            ge[c] += (p - cost_of(s, c)) >= 0
    pv = {c: ge[c] / B_INNER for c in COMPARATORS}
    order = sorted(pv, key=pv.get)
    ok, holm = True, {}
    for i, c in enumerate(order):
        ok = ok and pv[c] <= ALPHA / (len(order) - i)
        holm[c] = ok
    return point, holm


def main():
    recs = dev.train_records()
    rs = dev.rows(recs, recs, None)
    pools, weights, mix_report = {}, {}, {}
    for t in ("mozilla", "kernel"):
        idx = [i for i, p in enumerate(recs) if p["tracker"] == t]
        cells = Counter((recs[i]["bug"]["group"], str(recs[i]["bug"]["level"])) for i in idx)
        nat = natural_mix(t)
        missing = [c for c in nat if c not in cells]
        assert not missing, (t, missing)
        pools[t] = [rs[i] for i in idx]
        weights[t] = [nat.get((recs[i]["bug"]["group"], str(recs[i]["bug"]["level"])), 0.0) /
                      cells[(recs[i]["bug"]["group"], str(recs[i]["bug"]["level"]))] for i in idx]
        mix_report[t] = {"training_cells": {f"{g}:{l}": c for (g, l), c in sorted(cells.items())},
                         "natural_share": {f"{g}:{l}": round(v, 3) for (g, l), v in sorted(nat.items())}}
    rng = random.Random(dev.SEED)
    out = {"status": "PLANNING ONLY (training bugs reweighted to natural mix)", "mix": mix_report, "sizes": {}}
    for n in SIZES:
        pts, wins = {c: [] for c in COMPARATORS}, Counter()
        for _ in range(SIMS):
            point, holm = one_study(pools, weights, n, rng)
            for c in COMPARATORS:
                pts[c].append(point[c])
                wins[c] += holm[c]
        out["sizes"][f"{2 * n}_bugs ({18 * n} Jev calls)"] = {
            c: {"mean_P_minus_comparator": round(sum(pts[c]) / SIMS, 1),
                "power_holm": round(wins[c] / SIMS, 2)} for c in COMPARATORS}
        print(n, json.dumps(out["sizes"][f"{2 * n}_bugs ({18 * n} Jev calls)"]), flush=True)
    OUT.write_text(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
