"""Kubernetes workflow on the comparison models (research/methodology/k8s_crossmodel_preregistration.md).

  .venv/bin/python3 research/src/openjev/client_k8s.py --selftest                      no Modal
  .venv/bin/python3 research/src/openjev/client_k8s.py --model Qwen/Qwen2.5-7B-Instruct   dry run: builds every request
  ... --smoke --live --confirm-k8s-crossmodel-modal     30 development issues -> *_smoke_raw_responses.jsonl
  ... --full  --live --confirm-k8s-crossmodel-modal     500 development + 582 test issues
  --model openjev__openjev-27B uses the served shim (modal_openjev.OpenJevServer).

Questions and adapter are imported from run_k8s_workflow (frozen). Prompt templates and
confidence formulas are openjev/client.py's. Rows match k8s_raw_responses.jsonl's format.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE.parent
sys.path.insert(0, str(SRC))
sys.path.insert(0, str(HERE))
import run_k8s_workflow as kw  # noqa: E402  (frozen questions + adapter)
from client import choice_request, noul_request, score_request, choice_conf, score_conf  # noqa: E402
from run_workflow_calibration_pilot import reduce_choice_or_score_cell, reduce_noul_cell  # noqa: E402

ROOT = SRC.parents[1]
OUT_DIR = ROOT / "research" / "data" / "k8s" / "crossmodel"
SERVED = "openjev__openjev-27B"
MODELS = {"Qwen/Qwen2.5-7B-Instruct": "OpenJev", "microsoft/Phi-3.5-mini-instruct": "OpenJev",
          "allenai/OLMo-2-1124-7B-Instruct": "OpenJevT447", SERVED: None}
KEY = {arm: next(iter(kw.QUESTIONS[arm])) for arm in kw.ARMS}  # routing / bug / priority


def issues(smoke: bool):
    dev, test = kw.load()
    return kw.smoke_issues(dev) if smoke else dev + test


def request(arm, state):
    q = kw.QUESTIONS[arm][KEY[arm]]
    if arm == "choice":
        return choice_request(state, q)
    return (noul_request(state, q) if arm == "noul" else score_request(state, q)), None


def to_answer(arm, dist, letter_map):
    probs = dist["probs"]
    if arm == "choice":
        p = {letter_map[k]: v for k, v in probs.items()}
        return {KEY[arm]: {"type": "choice", "choice": max(p, key=p.get), "confidence": choice_conf(p), "probabilities": p}}
    if arm == "noul":
        return {KEY[arm]: {"type": "noul", "noul": probs["Yes"]}}
    pl = [probs[str(i)] for i in range(len(probs))]
    return {KEY[arm]: {"type": "score", "score": sum(i * v for i, v in enumerate(pl)), "confidence": score_conf(pl),
                       "probabilities": {str(i): v for i, v in enumerate(pl)}}}


def chain(model, iss, ask_arm):
    """Run choice -> noul -> score over all issues; ask_arm(arm, states) returns one call dict per issue."""
    d1 = {r["number"]: None for r in iss}
    d2 = dict(d1)
    rows = []
    for arm in kw.ARMS:
        states = [kw.node_state(r["text"], arm, d1[r["number"]], d2[r["number"]]) for r in iss]
        calls = ask_arm(arm, states)
        for r, call in zip(iss, calls):
            for k in range(1, kw.REPEATS + 1):
                rows.append({"number": r["number"], "split": r["split"], "arm": arm, "repeat": k,
                             "deterministic": True, "model": model, **call})
            if arm == "choice":
                d1[r["number"]] = reduce_choice_or_score_cell([call] * 3)["modal_decision"]
            elif arm == "noul":
                d2[r["number"]] = reduce_noul_cell([call] * 3)["decision"]
        print(f"{model}: {arm} done for {len(iss)} issues", flush=True)
    return rows


def open_model_asker(model):
    import modal
    engine = modal.Cls.from_name("openjev", MODELS[model])(model_id=model)

    def ask(arm, states):
        reqs, maps = zip(*(request(arm, s) for s in states))
        chunks = [list(reqs[s:s + 64]) for s in range(0, len(reqs), 64)]
        dists = [d for part in engine.distributions.map(chunks) for d in part]
        return [{"http_status": 200, "parsed_response": {"answers": to_answer(arm, d, m)}, "label_mass": d["label_mass"]}
                for d, m in zip(dists, maps)]
    return ask, None


def served_asker():
    import modal
    server = modal.Cls.from_name("openjev-serve", "OpenJevServer")()
    version = server.version.remote()

    def ask(arm, states):
        res = server.ask_many.remote([{"state": s, "model": "openjev", "questions": kw.QUESTIONS[arm]} for s in states])
        out = []
        for r in res:
            ok = r["http_status"] == 200 and r["json"] and "answers" in r["json"]
            out.append({"http_status": r["http_status"], "parsed_response": r["json"] if ok else None,
                        "raw_response": r["json"], "latency_ms": r.get("latency_ms"), "error": r.get("error")})
        return out
    return ask, version


def dry_run(model, smoke):
    iss = issues(smoke)
    n = 0
    for arm in kw.ARMS:
        for r in iss:
            req, mp = request(arm, kw.node_state(r["text"], arm, "node", 1))
            assert req["labels"] and (mp is None or set(mp.values()) == set(kw.QUESTIONS["choice"]["routing"]["criteria"]))
            n += 1
    return {"model": model, "issues": len(iss), "forward_passes": n,
            "dataset_sha256": hashlib.sha256(kw.DS.read_bytes()).hexdigest(), "out_dir": str(OUT_DIR.relative_to(ROOT))}


def selftest():
    assert KEY == {"choice": "routing", "noul": "bug", "score": "priority"}
    req, mp = request("choice", "T")
    assert req["labels"] == ["A", "B", "C"] and set(mp.values()) == {"network", "storage", "node"}
    a = to_answer("choice", {"probs": {"A": 0.1, "B": 0.2, "C": 0.7}}, mp)
    call = {"http_status": 200, "parsed_response": {"answers": a}}
    assert reduce_choice_or_score_cell([call] * 3)["modal_decision"] == mp["C"]
    n = {"http_status": 200, "parsed_response": {"answers": to_answer("noul", {"probs": {"Yes": 0.8, "No": 0.2}}, None)}}
    assert reduce_noul_cell([n] * 3)["decision"] == 1
    s = {"http_status": 200, "parsed_response": {"answers": to_answer("score", {"probs": {"0": 0.1, "1": 0.2, "2": 0.7}}, None)}}
    assert reduce_choice_or_score_cell([s] * 3)["modal_decision"] in (2, "2")
    fake = [{"number": i, "split": "development", "text": "x"} for i in range(3)]
    rows = chain("fake", fake, lambda arm, st: [{"http_status": 200, "parsed_response": {"answers": to_answer(
        arm, {"probs": {"choice": {"A": .8, "B": .1, "C": .1}, "noul": {"Yes": .9, "No": .1},
                        "score": {"0": .6, "1": .3, "2": .1}}[arm]}, request(arm, x)[1])}} for x in st])
    assert len(rows) == 3 * 3 * 3 and {r["arm"] for r in rows} == set(kw.ARMS)
    print("selftest OK")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--model", choices=list(MODELS))
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--full", action="store_true")
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--confirm-k8s-crossmodel-modal", dest="confirm", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not a.model:
        raise SystemExit("--model required")
    print(json.dumps(dry_run(a.model, a.smoke), indent=1))
    if not (a.smoke or a.full):
        print("Dry run only. No Modal calls were made.")
        return
    if not (a.live and a.confirm):
        raise SystemExit("Refusing: live runs need --live --confirm-k8s-crossmodel-modal")
    safe = a.model.replace("/", "__")
    out = OUT_DIR / f"{safe}{'_smoke' if a.smoke else ''}_raw_responses.jsonl"
    if out.exists():
        raise SystemExit(f"{out.name} exists; refusing to overwrite.")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ask, version = served_asker() if a.model == SERVED else open_model_asker(a.model)
    rows = chain(a.model, issues(a.smoke), ask)
    with out.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, default=str) + "\n")
    lm = sorted(r["label_mass"] for r in rows if r["repeat"] == 1 and "label_mass" in r)
    meta = {"model": a.model, "smoke": a.smoke, "issues": len(rows) // 9, "passes": len(rows) // 3,
            "failures": sum(r["http_status"] != 200 or not r.get("parsed_response") for r in rows if r["repeat"] == 1),
            "dataset_sha256": hashlib.sha256(kw.DS.read_bytes()).hexdigest(),
            "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), "server_version": version}
    if lm:
        meta.update(label_mass_min=lm[0], label_mass_median=lm[len(lm) // 2],
                    share_mass_below_0_5=round(sum(x < 0.5 for x in lm) / len(lm), 4))
    out.with_name(out.name.replace("_raw_responses.jsonl", "_run_meta.json")).write_text(json.dumps(meta, indent=1, default=str))
    print(json.dumps(meta, indent=1, default=str))


if __name__ == "__main__":
    main()
