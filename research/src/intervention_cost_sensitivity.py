"""Exploratory cost-sensitivity analysis of the intervention test
(research/methodology/intervention_cost_sensitivity_plan.md).

Rankings are frozen as computed under the original cost table; only the
costs used to score them vary. No API or GPU calls.

  .venv/bin/python research/src/intervention_cost_sensitivity.py
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent
sys.path.insert(0, str(SRC))
import intervention_test as it  # noqa: E402
from workflow_strategies_r12 import COST  # noqa: E402

M_GRID = [0.5, 1, 2, 4]
H_GRID = [0.25, 0.5, 1, 2]
ARMS = ["A1", "A2", "E", "B", "B2", "C"]
OUT = it.ROOT / "research" / "results" / "intervention_cost_sensitivity.json"


def cost_mh(action, a_star, m, h):
    c = COST[action][a_star] * (m if action == "accept" else 1)
    return c + (h if action == "escalate" else 0)


def rescore(rows, m, h):
    return [dict(r, base_cost=cost_mh(r["action"], r["a_star"], m, h),
                 gain=cost_mh(r["action"], r["a_star"], m, h) - cost_mh("escalate", r["a_star"], m, h))
            for r in rows]


def main():
    frozen_rows = {}
    for mname in ["Jev 1.13"] + it.ac.MODELS:
        train, held, est = it.load_model(mname)
        frozen_rows[mname] = it.rows_for(held, it.action_tables(train), est)   # rankings under the original table

    # Self-check: the (1, 1) cell must reproduce the pre-registered numbers exactly.
    pre = json.loads(it.OUT_JSON.read_text())["models"]
    for mname, rows in frozen_rows.items():
        rs = rescore(rows, 1, 1)
        assert sum(r["base_cost"] for r in rs) == pre[mname]["base_total_cost"], mname
        for a in ARMS:
            got = round(it.expected_total(rs, None if a == "C" else a)[0], 2)
            assert abs(got - pre[mname]["arms"][a]["total_cost"]) < 0.01, (mname, a, got)

    out = {"status": "EXPLORATORY / POST HOC; rankings frozen under the original table; point estimates only",
           "grid": {"m_accept_error_multiplier": M_GRID, "h_human_cost_per_escalation": H_GRID},
           "cells": {}, "summary": {}}
    for m in M_GRID:
        for h in H_GRID:
            cell = {}
            for mname, rows in frozen_rows.items():
                rs = rescore(rows, m, h)
                base = sum(r["base_cost"] for r in rs)
                arms = {a: round(it.expected_total(rs, None if a == "C" else a)[0], 2) for a in ARMS}
                cand = [r for r in rs if r["action"] != "escalate"]
                k = min(math.ceil(it.BUDGET * len(rs)), len(cand))
                oracle = base - sum(g for g in sorted((r["gain"] for r in cand), reverse=True)[:k] if True)
                best = min(arms, key=arms.get)
                cell[mname] = {"no_review": round(base, 2), "arms": arms, "best_arm": best,
                               "best_minus_no_review": round(arms[best] - base, 2),
                               "A1_minus_C": round(arms["A1"] - arms["C"], 2),
                               "A1_minus_B": round(arms["A1"] - arms["B"], 2),
                               "oracle": round(oracle, 2)}
            out["cells"][f"m={m},h={h}"] = {"break_even_precision_escalate_target": round((1 + h) / (10 * m + 1), 3),
                                            "models": cell}
    near = [f"m={m},h={h}" for m in (0.5, 1, 2) for h in (0.5, 1, 2)]
    for mname in frozen_rows:
        rev_near = [c for c in near if out["cells"][c]["models"][mname]["best_minus_no_review"] < 0]
        rev_all = [c for c in out["cells"] if out["cells"][c]["models"][mname]["best_minus_no_review"] < 0]
        out["summary"][mname] = {
            "verdict": "cost-robust" if not rev_near else "cost-dependent",
            "near_cells_where_review_pays": rev_near,
            "all_cells_where_review_pays": rev_all,
            "cells_A1_beats_C": sum(out["cells"][c]["models"][mname]["A1_minus_C"] < 0 for c in out["cells"]),
            "cells_A1_beats_B": sum(out["cells"][c]["models"][mname]["A1_minus_B"] < 0 for c in out["cells"]),
            "n_cells": len(out["cells"])}
    OUT.write_text(json.dumps(out, indent=2))
    print(json.dumps(out["summary"], indent=1))


if __name__ == "__main__":
    main()
