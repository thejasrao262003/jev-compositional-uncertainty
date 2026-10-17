"""open-Jev client: Jev-compatible choice / noul / score answers from an
open-weight model served by modal_app.OpenJev, run through the identical
three-step chain on the 442 training + 500 held-out bugs.
Pre-registration: research/methodology/openjev_crossmodel_preregistration.md

Confidence formulas are TypeSafe's documented ones (docs.typesafe.ai/confidence).
Output rows match the Jev raw-response format the analysis code reads
(tracker, bug_id, arm, repeat, http_status, parsed_response.answers), with
each deterministic call recorded 3 times and flagged.

  .venv/bin/python3 research/src/openjev/client.py --model Qwen/Qwen2.5-7B-Instruct
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE.parent
sys.path.insert(0, str(SRC))
sys.path.insert(0, str(HERE))
import run_kernel_validation as kv  # noqa: E402  (questions + adapter, unchanged)

ROOT = SRC.parents[1]
OUT_DIR = ROOT / "research" / "data" / "openjev"
SYSTEM = "You are a decision model. Read the evidence and answer the structured question with a single label."
LETTERS = "ABCDEFGH"


def choice_request(state: str, q: dict) -> tuple[dict, dict]:
    opts = list(q["criteria"])
    lines = [f"{LETTERS[i]}. {o} — {q['criteria'][o]}" for i, o in enumerate(opts)]
    user = (f"Evidence:\n{state}\n\nQuestion: {q['instructions']}\n\nOptions:\n" + "\n".join(lines) +
            "\n\nRespond with the letter of the best option only.")
    return ({"messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": user}],
             "labels": [LETTERS[i] for i in range(len(opts))]}, {LETTERS[i]: o for i, o in enumerate(opts)})


def score_request(state: str, q: dict) -> dict:
    lines = [f"{i} — {c}" for i, c in enumerate(q["criteria"])]
    user = (f"Evidence:\n{state}\n\nQuestion: {q['instructions']}\n\nScale:\n" + "\n".join(lines) +
            "\n\nRespond with the single digit of the best level only.")
    return {"messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": user}],
            "labels": [str(i) for i in range(len(q["criteria"]))]}


def noul_request(state: str, q: dict) -> dict:
    user = f"Evidence:\n{state}\n\nQuestion: {q['instructions']}\n\nRespond with Yes or No only."
    return {"messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": user}],
            "labels": ["Yes", "No"]}


# TypeSafe's documented confidence formulas
def choice_conf(p: dict) -> float:
    n = len(p)
    return (max(p.values()) - 1 / n) / (1 - 1 / n)


def score_conf(p: list[float]) -> float:
    n = len(p)
    m = max(range(n), key=lambda i: p[i])
    mad_unif = sum(abs(i - (n - 1) / 2) for i in range(n)) / n
    return max(0.0, 1 - sum(pi * abs(i - m) for i, pi in enumerate(p)) / mad_unif)


def to_answer(arm: str, dist: dict, letter_map: dict | None = None) -> dict:
    probs = dist["probs"]
    if arm == "choice":
        p = {letter_map[k]: v for k, v in probs.items()}
        top = max(p, key=p.get)
        return {"routing": {"type": "choice", "choice": top, "confidence": choice_conf(p), "probabilities": p}}
    if arm == "noul":
        return {"regression": {"type": "noul", "noul": probs["Yes"]}}
    pl = [probs[str(i)] for i in range(len(probs))]
    return {"severity": {"type": "score", "score": sum(i * v for i, v in enumerate(pl)), "confidence": score_conf(pl),
                         "probabilities": {str(i): v for i, v in enumerate(pl)}}}


def load_bugs() -> list[tuple[str, str, dict]]:
    out = []
    for t in ("mozilla", "kernel"):
        for line in (ROOT / "research" / "data" / t / "dataset.jsonl").open():
            out.append(("train", t, json.loads(line)))
        for line in (ROOT / "research" / "data" / "heldout" / f"{t}_heldout.jsonl").open():
            out.append(("heldout", t, json.loads(line)))
    return out


def run(model_id: str, limit: int | None = None, cls_name: str = "OpenJev") -> Path:
    import modal
    from run_workflow_calibration_pilot import reduce_choice_or_score_cell, reduce_noul_cell
    safe = model_id.replace("/", "__")
    out = OUT_DIR / f"{safe}_raw_responses.jsonl"
    if out.exists():
        raise SystemExit(f"{out.name} exists; refusing to overwrite.")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    bugs = load_bugs()[:limit] if limit else load_bugs()
    OpenJev = modal.Cls.from_name("openjev", cls_name)
    engine = OpenJev(model_id=model_id)
    state = {i: {"d1": None, "d2": None} for i in range(len(bugs))}
    rows = {i: [] for i in range(len(bugs))}
    meta = {"model": model_id, "label_mass": []}
    for arm in kv.ARMS:
        reqs, maps = [], []
        for i, (_, _, b) in enumerate(bugs):
            st = kv.node_state(b["text"], arm, state[i]["d1"], state[i]["d2"])
            q = next(iter(kv.QUESTIONS[arm].values()))
            if arm == "choice":
                r, mp = choice_request(st, q)
            else:
                r, mp = (noul_request(st, q) if arm == "noul" else score_request(st, q)), None
            reqs.append(r)
            maps.append(mp)
        chunks = [reqs[s:s + 64] for s in range(0, len(reqs), 64)]
        dists = [d for part in engine.distributions.map(chunks) for d in part]
        for i, (d, mp) in enumerate(zip(dists, maps)):
            ans = to_answer(arm, d, mp)
            meta["label_mass"].append(d["label_mass"])
            call = {"http_status": 200, "parsed_response": {"answers": ans}, "label_mass": d["label_mass"]}
            for r in range(1, kv.REPEATS + 1):
                rows[i].append({"split": bugs[i][0], "tracker": bugs[i][1], "bug_id": bugs[i][2]["bug_id"], "arm": arm,
                                "repeat": r, "deterministic": True, "model": model_id, **call})
            if arm == "choice":
                state[i]["d1"] = reduce_choice_or_score_cell([call] * 3)["modal_decision"]
            elif arm == "noul":
                state[i]["d2"] = reduce_noul_cell([call] * 3)["decision"]
        print(f"{model_id}: {arm} done for {len(bugs)} bugs", flush=True)
    with out.open("w", encoding="utf-8") as f:
        for i in range(len(bugs)):
            for row in rows[i]:
                f.write(json.dumps(row) + "\n")
    lm = sorted(meta["label_mass"])
    (OUT_DIR / f"{safe}_run_meta.json").write_text(json.dumps(
        {"model": model_id, "bugs": len(bugs), "forward_passes": len(lm),
         "label_mass_min": lm[0], "label_mass_median": lm[len(lm) // 2]}, indent=2))
    print(f"wrote {out}")
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--limit", type=int)
    ap.add_argument("--cls", default="OpenJev", help="OpenJevT447 for models needing transformers 4.47 (OLMo-2)")
    a = ap.parse_args()
    run(a.model, a.limit, a.cls)
