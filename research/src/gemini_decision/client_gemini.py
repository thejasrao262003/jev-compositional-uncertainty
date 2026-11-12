"""Gemini Decision 1 runner (research/methodology/gemini_decision_preregistration.md).

  .venv/bin/python research/src/gemini_decision/client_gemini.py --selftest
  .venv/bin/python research/src/gemini_decision/client_gemini.py --target bugzilla          dry run (no calls)
  ... --target bugzilla --smoke --live --confirm-gemini-calls      30 dev bugs, 3 real calls per node
  ... --target bugzilla --full  --live --confirm-gemini-calls [--repeats 1|3] [--max-calls 9500]
  ... --target k8s      --full  --live --confirm-gemini-calls [--repeats 1|3]

Key: GEMINI_API_KEY from the environment or .env (never printed or logged). Standard library only.
Questions and adapters are imported from the frozen Jev runners. Rows match the existing raw formats
(Bugzilla: research/data/openjev/*_raw_responses.jsonl; Kubernetes: research/data/k8s/crossmodel/).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import sys
import threading
import time
import urllib.error
import urllib.request
import zlib
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE.parent
sys.path.insert(0, str(SRC))
import run_kernel_validation as kv  # noqa: E402  (Bugzilla questions + adapter)
import run_k8s_workflow as kw  # noqa: E402  (Kubernetes questions + adapter)
from run_workflow_calibration_pilot import reduce_choice_or_score_cell, reduce_noul_cell  # noqa: E402

ROOT = SRC.parents[1]
MODEL = "gemini-decision-1"
LABEL = "gemini__gemini-decision-1"
URL = "https://generativelanguage.googleapis.com/v1beta/decisions"
OUT = {"bugzilla": ROOT / "research" / "data" / "openjev", "k8s": ROOT / "research" / "data" / "k8s" / "crossmodel"}
MAX_RPM, RETRIES, WORKERS = 150, 2, 4
ARMS = ("choice", "noul", "score")


def api_key():
    k = os.environ.get("GEMINI_API_KEY")
    if not k and (ROOT / ".env").exists():
        for line in (ROOT / ".env").read_text().splitlines():
            if line.startswith("GEMINI_API_KEY="):
                k = line.split("=", 1)[1].strip().strip('"').strip("'")
    if not k:
        raise SystemExit("GEMINI_API_KEY not set (environment or .env). Get a key at aistudio.google.com.")
    return k


# ------------------------------------------------------------------ items
def bugzilla_items(smoke):
    out = []
    for t in ("mozilla", "kernel"):
        for line in (ROOT / "research" / "data" / t / "dataset.jsonl").open():
            b = json.loads(line); out.append({"split": "train", "tracker": t, "bug_id": b["bug_id"], "text": b["text"]})
        for line in (ROOT / "research" / "data" / "heldout" / f"{t}_heldout.jsonl").open():
            b = json.loads(line); out.append({"split": "heldout", "tracker": t, "bug_id": b["bug_id"], "text": b["text"]})
    if smoke:
        train = [x for x in out if x["split"] == "train"]
        out = sorted(random.Random(zlib.crc32(b"gemini-smoke")).sample(train, 30), key=lambda x: (x["tracker"], x["bug_id"]))
    return out


def k8s_items(smoke):
    dev, test = kw.load()
    items = [{"number": r["number"], "split": r["split"], "text": r["text"]} for r in dev + test]
    return items[:30] if smoke else items


TARGET = {"bugzilla": (bugzilla_items, kv.QUESTIONS, kv.node_state, lambda it: (it["split"], it["tracker"], it["bug_id"]),
                       lambda it: {"split": it["split"], "tracker": it["tracker"], "bug_id": it["bug_id"]}),
          "k8s": (k8s_items, kw.QUESTIONS, kw.node_state, lambda it: (it["number"],),
                  lambda it: {"number": it["number"], "split": it["split"]})}


# ------------------------------------------------------------------ answers
def normalise(answers, questions):
    """Map score probabilities keyed by level text to level indices (recorded); leave others unchanged."""
    out, mapped = {}, False
    for k, a in answers.items():
        a = dict(a)
        q = questions.get(k, {})
        if a.get("type") == "score" and isinstance(a.get("probabilities"), dict):
            keys = list(a["probabilities"])
            if not all(str(x).isdigit() for x in keys):
                crit = q.get("criteria", [])
                a["probabilities"] = {str(crit.index(x)): v for x, v in a["probabilities"].items() if x in crit}
                mapped = True
        out[k] = a
    return out, mapped


# ------------------------------------------------------------------ http
class Pacer:
    def __init__(self, rpm):
        self.gap, self.lock, self.next = 60.0 / rpm, threading.Lock(), 0.0

    def wait(self):
        with self.lock:
            now = time.monotonic()
            t = max(now, self.next)
            self.next = t + self.gap
        time.sleep(max(0.0, t - now))


def call(key, body, pacer):
    attempts = []
    for attempt in range(1, RETRIES + 2):
        pacer.wait()
        t0 = time.time()
        req = urllib.request.Request(URL, data=json.dumps(body).encode(), method="POST",
                                     headers={"Content-Type": "application/json", "x-goog-api-key": key})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                data = json.loads(r.read().decode())
            return {"http_status": 200, "raw_response": data, "attempt": attempt, "latency_ms": int(1000 * (time.time() - t0)),
                    "errors": attempts}
        except urllib.error.HTTPError as e:
            msg = e.read().decode()[:500]
            attempts.append({"status": e.code, "body": msg})
            if e.code in (400, 403):     # safety block or auth: do not retry
                return {"http_status": e.code, "raw_response": None, "attempt": attempt, "errors": attempts}
            time.sleep(min(30, 2 ** attempt))
        except Exception as e:  # network
            attempts.append({"status": None, "body": f"{type(e).__name__}: {str(e)[:200]}"})
            time.sleep(min(30, 2 ** attempt))
    return {"http_status": attempts[-1]["status"] or 0, "raw_response": None, "attempt": RETRIES + 1, "errors": attempts}


# ------------------------------------------------------------------ run
def run(target, smoke, repeats, max_calls, key):
    items_fn, Q, node_state, keyf, idf = TARGET[target]
    items = items_fn(smoke)
    out = OUT[target] / f"{LABEL}{'_smoke' if smoke else ''}_raw_responses.jsonl"
    done = {}
    if out.exists():
        for line in out.open():
            r = json.loads(line)
            done[(*keyf(r), r["arm"], r["repeat"])] = r
    calls = {"n": 0}
    lock = threading.Lock()
    pacer = Pacer(MAX_RPM)
    f = out.open("a", encoding="utf-8")
    real_repeats = 3 if smoke else repeats

    def one_item(it):
        d1 = d2 = None
        for arm in ARMS:
            q = Q[arm]
            body = {"model": MODEL, "input": node_state(it["text"], arm, d1, d2), "questions": q}
            recs = []
            for r in range(1, 4):
                k = (*keyf(it), arm, r)
                if k in done:
                    recs.append(done[k]); continue
                if r > real_repeats:            # deterministic: record the first call three times, flagged
                    base = dict(recs[0]); base.update(repeat=r, deterministic=True)
                    rec = base
                else:
                    with lock:
                        if calls["n"] >= max_calls:
                            raise SystemExit(f"STOP: per-run call cap {max_calls} reached; resume later")
                        calls["n"] += 1
                    res = call(key, body, pacer)
                    ans = (res["raw_response"] or {}).get("answers")
                    norm, mapped = normalise(ans, q) if ans else (None, False)
                    rec = {**idf(it), "arm": arm, "repeat": r, "deterministic": real_repeats == 1, "model": LABEL,
                           "http_status": res["http_status"], "parsed_response": {"answers": norm} if norm else None,
                           "raw_response": res["raw_response"], "score_keys_mapped": mapped, "attempt": res["attempt"],
                           "errors": res["errors"], "latency_ms": res.get("latency_ms"),
                           "request_utc": datetime.now(timezone.utc).isoformat()}
                with lock:
                    f.write(json.dumps(rec) + "\n"); f.flush()
                    done[k] = rec
                recs.append(rec)
            if arm == "choice":
                d1 = reduce_choice_or_score_cell(recs)["modal_decision"]
            elif arm == "noul":
                d2 = reduce_noul_cell(recs)["decision"]
        return all(r["http_status"] == 200 for r in recs)

    ok = []
    try:
        with ThreadPoolExecutor(WORKERS) as ex:
            for i, res in enumerate(ex.map(one_item, items), 1):
                ok.append(res)
                if i % 25 == 0 or i == len(items):
                    print(f"[{target}] {i}/{len(items)} items, calls this run {calls['n']}, failed items {ok.count(False)}",
                          file=sys.stderr, flush=True)
                if ok.count(False) > max(1, 0.01 * len(items)):
                    raise SystemExit(f"STOP: {ok.count(False)} failed items exceeds 1% of {len(items)}")
    finally:
        f.close()
    meta = {"target": target, "smoke": smoke, "items": len(items), "repeats_real": real_repeats, "calls_this_run": calls["n"],
            "failed_items": ok.count(False), "model": MODEL, "finished_utc": datetime.now(timezone.utc).isoformat(),
            "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    out.with_name(out.name.replace("_raw_responses.jsonl", "_run_meta.json")).write_text(json.dumps(meta, indent=1))
    print(json.dumps(meta, indent=1))


def determinism_report(path):
    """Smoke check: identical probabilities (1e-6) across the three repeats of every node?"""
    rows = [json.loads(l) for l in open(path)]
    by = {}
    for r in rows:
        if r["http_status"] == 200:
            by.setdefault((r.get("tracker"), r.get("bug_id"), r.get("number"), r["arm"]), []).append(r)
    diffs = []
    for k, rs in by.items():
        ps = []
        for r in rs:
            a = next(iter(r["parsed_response"]["answers"].values()))
            ps.append([a["noul"]] if "noul" in a else [a["probabilities"][x] for x in sorted(a["probabilities"])])
        diffs.append(max(abs(x - y) for p in ps for x, y in zip(p, ps[0])) if len(ps) > 1 else 0.0)
    return {"cells": len(diffs), "max_abs_diff": max(diffs) if diffs else None,
            "deterministic": bool(diffs) and max(diffs) <= 1e-6}


def selftest():
    assert set(kv.QUESTIONS) == set(ARMS) and set(kw.QUESTIONS) == set(ARMS)
    q = {"severity": {"type": "score", "criteria": ["low", "mid", "high"]}}
    n, m = normalise({"severity": {"type": "score", "probabilities": {"low": .2, "mid": .5, "high": .3}}}, q)
    assert m and n["severity"]["probabilities"] == {"0": .2, "1": .5, "2": .3}
    n, m = normalise({"severity": {"type": "score", "probabilities": {"0": .2, "1": .5, "2": .3}}}, q)
    assert not m
    rec = {"http_status": 200, "parsed_response": {"answers": {"x": {"type": "score", "probabilities": {"0": .1, "1": .2, "2": .7},
                                                                "confidence": .5, "score": 1.6}}}}
    assert reduce_choice_or_score_cell([rec] * 3)["modal_decision"] in (2, "2")
    for t, (fn, Q, ns, kf, idf) in TARGET.items():
        it = fn(False)[0]
        body = {"model": MODEL, "input": ns(it["text"], "score", None, None), "questions": Q["score"]}
        assert body["input"] and len(json.dumps(body)) < 2_000_000
    assert len(bugzilla_items(True)) == 30
    print("selftest OK")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--target", choices=list(TARGET))
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--full", action="store_true")
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--confirm-gemini-calls", dest="confirm", action="store_true")
    ap.add_argument("--repeats", type=int, choices=(1, 3), default=3)
    ap.add_argument("--max-calls", type=int, default=9500)
    ap.add_argument("--determinism", metavar="SMOKE_JSONL")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if a.determinism:
        return print(json.dumps(determinism_report(a.determinism), indent=1))
    if not a.target:
        raise SystemExit("--target required")
    items = TARGET[a.target][0](a.smoke)
    per_item = 9 if a.smoke else 3 * a.repeats
    print(json.dumps({"target": a.target, "items": len(items), "planned_calls": len(items) * per_item,
                      "max_calls_per_run": a.max_calls, "max_rpm": MAX_RPM}, indent=1))
    if not (a.smoke or a.full):
        print("Dry run only. No calls were made.")
        return
    if not (a.live and a.confirm):
        raise SystemExit("Refusing: live runs need --live --confirm-gemini-calls")
    run(a.target, a.smoke, a.repeats, a.max_calls, api_key())


if __name__ == "__main__":
    main()
