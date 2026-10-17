"""DESCRIPTIVE / EXPLORATORY follow-up to the pre-registered intervention test.
Not a test; computes no new strategy. No API or GPU calls.

Per model, on the 500 held-out bugs:
  - cost decomposition of the no-review workflow by (action, target) cell;
  - how much of the total cost is avoidable by escalation at all;
  - per-action break-even: a review of action a pays off only if
    P(target makes escalation cheaper) is high enough;
  - ORACLE bound: total cost if the 50 reviews went to the 50 candidates with
    the largest true saving (uses held-out outcomes; an upper bound on what
    any ranking could achieve, NOT a strategy).

  python3 research/src/intervention_cost_mechanism.py
"""
from __future__ import annotations

import json
import math
import sys
from collections import Counter
from pathlib import Path

SRC = Path(__file__).resolve().parent
sys.path.insert(0, str(SRC))
import intervention_test as it  # noqa: E402

OUT = it.ROOT / "research" / "results" / "intervention_cost_mechanism.json"


def main():
    out = {"status": "DESCRIPTIVE / EXPLORATORY; oracle uses held-out outcomes and is an upper bound, not a strategy",
           "models": {}}
    pre = json.loads(it.OUT_JSON.read_text())["models"]
    for m in ["Jev 1.13"] + it.ac.MODELS:
        train, held, est = it.load_model(m)
        rows = it.rows_for(held, it.action_tables(train), est)
        base = sum(r["base_cost"] for r in rows)
        cells = Counter()
        for r in rows:
            cells[(r["action"], r["a_star"])] += r["base_cost"]
        cand = [r for r in rows if r["action"] != "escalate"]
        k = min(math.ceil(it.BUDGET * len(rows)), len(cand))
        gains = sorted((r["gain"] for r in cand), reverse=True)
        oracle = base - sum(gains[:k])
        positive = [g for g in gains if g > 0]
        per_action = {}
        for a in ("accept", "defer"):
            ra = [r for r in cand if r["action"] == a]
            if ra:
                per_action[a] = {"n": len(ra), "mean_saving_if_reviewed": round(sum(r["gain"] for r in ra) / len(ra), 3),
                                 "share_where_review_saves": round(sum(r["gain"] > 0 for r in ra) / len(ra), 3)}
        out["models"][m] = {
            "no_review_cost": base,
            "cost_by_cell_(action->target)": {f"{a}->{t}": c for (a, t), c in sorted(cells.items(), key=lambda x: -x[1]) if c},
            "share_of_cost_from_wrong_accepts": round(sum(c for (a, t), c in cells.items() if a == "accept") / base, 3),
            "candidates": len(cand), "candidates_where_review_saves": len(positive),
            "max_total_saving_any_budget": sum(positive),
            "oracle_cost_at_k50": oracle, "best_preregistered_arm_cost": min(v["total_cost"] for v in pre[m]["arms"].values()),
            "per_action": per_action}
        print(m, json.dumps({k2: v for k2, v in out["models"][m].items() if k2 != "cost_by_cell_(action->target)"}))
    OUT.write_text(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
