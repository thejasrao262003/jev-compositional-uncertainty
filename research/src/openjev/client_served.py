"""Run the three-step chain against OpenJev served by modal_openjev.OpenJevServer
(Jev-format request bodies; the shim's own probabilities and confidence).
Same bugs, questions and adapter as every other run. Output rows match the Jev
raw-response format the analysis reads. Pre-registration Amendment 1.

  .venv/bin/python3 research/src/openjev/client_served.py --label openjev__openjev-27B
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))
import run_kernel_validation as kv  # noqa: E402
from client import load_bugs, OUT_DIR  # noqa: E402


def run(label: str, limit: int | None = None) -> None:
    import modal
    from run_workflow_calibration_pilot import reduce_choice_or_score_cell, reduce_noul_cell
    out = OUT_DIR / f"{label}_raw_responses.jsonl"
    if out.exists():
        raise SystemExit(f"{out.name} exists; refusing to overwrite.")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    bugs = load_bugs()[:limit] if limit else load_bugs()
    server = modal.Cls.from_name("openjev-serve", "OpenJevServer")()
    version = server.version.remote()
    state = {i: {"d1": None, "d2": None} for i in range(len(bugs))}
    rows = {i: [] for i in range(len(bugs))}
    failures = 0
    for arm in kv.ARMS:
        bodies = [{"state": kv.node_state(b["text"], arm, state[i]["d1"], state[i]["d2"]), "model": "openjev",
                   "questions": kv.QUESTIONS[arm]} for i, (_, _, b) in enumerate(bugs)]
        res = server.ask_many.remote(bodies)
        for i, r in enumerate(res):
            ok = r["http_status"] == 200 and r["json"] and "answers" in r["json"]
            failures += int(not ok)
            call = {"http_status": r["http_status"], "parsed_response": r["json"] if ok else None,
                    "raw_response": r["json"], "latency_ms": r.get("latency_ms"), "error": r.get("error")}
            for k in range(1, kv.REPEATS + 1):
                rows[i].append({"split": bugs[i][0], "tracker": bugs[i][1], "bug_id": bugs[i][2]["bug_id"], "arm": arm,
                                "repeat": k, "deterministic": True, "model": label, **call})
            if arm == "choice":
                state[i]["d1"] = reduce_choice_or_score_cell([call] * 3)["modal_decision"]
            elif arm == "noul":
                state[i]["d2"] = reduce_noul_cell([call] * 3)["decision"]
        print(f"{label}: {arm} done for {len(bugs)} bugs (failures so far {failures})", flush=True)
    with out.open("w", encoding="utf-8") as f:
        for i in range(len(bugs)):
            for row in rows[i]:
                f.write(json.dumps(row) + "\n")
    (OUT_DIR / f"{label}_run_meta.json").write_text(json.dumps(
        {"label": label, "bugs": len(bugs), "requests": len(bugs) * len(kv.ARMS), "failures": failures,
         "server_version": version}, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True)
    ap.add_argument("--limit", type=int)
    a = ap.parse_args()
    run(a.label, a.limit)
