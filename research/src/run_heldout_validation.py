"""Held-out test of the frozen workflow-risk estimator.
Pre-registration: research/methodology/workflow_risk_heldout_preregistration.md

Chain, questions, adapter and repeats are the kernel/Mozilla replication's,
imported unchanged (run_kernel_validation.py). The estimator is the frozen
file research/results/frozen_risk_estimator_v1.json; its sha256 is verified
before any scoring.

CLI:
  --selftest                                         no network, no Jev
  --mode dry-run                                     preflight only
  --smoke-test --live --confirm-450-heldout-smoke-calls   first 25 bugs per tracker
  --mode live  --live --confirm-4500-heldout-calls        all 500 bugs
  --analyze-only                                     pre-registered analysis of collected data
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent
sys.path.insert(0, str(SRC))
import run_kernel_validation as kv  # noqa: E402  (chain definition, unchanged)
import workflow_risk_probe as wp  # noqa: E402  (feature definitions, unchanged)
from build_workflow_calibration_pilot_manifest import F  # noqa: E402
from mozilla_exploratory_analysis import auroc  # noqa: E402
from run_workflow_calibration_pilot import (reduce_choice_or_score_cell, reduce_noul_cell,  # noqa: E402
                                            strategy_1_decision_only)

ROOT = SRC.parents[1]
HELD = ROOT / "research" / "data" / "heldout"
RES = ROOT / "research" / "results"
EST = RES / "frozen_risk_estimator_v1.json"
EST_SHA = "a7c1e2f1a3748cb54f91d14e50e15dc299d39a6b40f4b0f8d654c989945062ce"
TRACKERS = ("mozilla", "kernel")
N_PER_TRACKER = 250
SMOKE_PER_TRACKER = 25
CALLS_PER_BUG = len(kv.ARMS) * kv.REPEATS          # 9
EXPECTED_CALLS = 2 * N_PER_TRACKER * CALLS_PER_BUG  # 4,500
EXPECTED_SMOKE = 2 * SMOKE_PER_TRACKER * CALLS_PER_BUG  # 450
B, SEED, ALPHA = 2000, 20261017, 0.05


class PreflightError(RuntimeError):
    pass


def raw_path(smoke: bool) -> Path:
    return HELD / ("heldout_smoketest_raw_responses.jsonl" if smoke else "heldout_raw_responses.jsonl")


def load_heldout() -> dict[str, list[dict]]:
    out = {}
    for t in TRACKERS:
        ds = HELD / f"{t}_heldout.jsonl"
        man = json.loads((HELD / f"{t}_heldout_manifest.json").read_text())
        if hashlib.sha256(ds.read_bytes()).hexdigest() != man["sha256"]["dataset"]:
            raise PreflightError(f"{ds.name} does not match its manifest hash")
        out[t] = [json.loads(line) for line in ds.open()]
        if len(out[t]) != N_PER_TRACKER:
            raise PreflightError(f"{t}: {len(out[t])} bugs, expected {N_PER_TRACKER}")
        used = {json.loads(line)["bug_id"] for line in (ROOT / "research" / "data" / t / "dataset.jsonl").open()}
        if {b["bug_id"] for b in out[t]} & used:
            raise PreflightError(f"{t}: held-out set overlaps the training data")
    return out


def load_estimator() -> dict:
    if hashlib.sha256(EST.read_bytes()).hexdigest() != EST_SHA:
        raise PreflightError("frozen estimator file changed since pre-registration")
    return json.loads(EST.read_text())


def smoke_subset(data):
    return {t: bugs[:SMOKE_PER_TRACKER] for t, bugs in data.items()}


def run_live(data: dict[str, list[dict]], raw_out: Path) -> int:
    if raw_out.exists():
        raise PreflightError(f"{raw_out.name} exists; refusing to overwrite collected data or re-spend calls.")
    from jev_client import ClientConfig, JevClient  # imported only on the live path
    client = JevClient(config=ClientConfig())
    expected = sum(len(b) for b in data.values()) * CALLS_PER_BUG
    n = 0
    with raw_out.open("w", encoding="utf-8") as f:
        for t, bugs in data.items():
            for b in bugs:
                d1 = d2 = None
                for arm in kv.ARMS:
                    state = kv.node_state(b["text"], arm, d1, d2)
                    calls = []
                    for r in range(1, kv.REPEATS + 1):
                        n += 1
                        print(f"[{n}/{expected}] {t} bug {b['bug_id']} {arm} rep {r}", file=sys.stderr)
                        rec = client.ask(state=state, questions=kv.QUESTIONS[arm],
                                         test_group=f"heldout_risk:{t}:{b['bug_id']}:{arm}:{r}").to_json_dict()
                        f.write(json.dumps({"tracker": t, "bug_id": b["bug_id"], "arm": arm, "repeat": r, **rec},
                                           default=str) + "\n")
                        f.flush()
                        calls.append(rec)
                    if arm == "choice":
                        d1 = reduce_choice_or_score_cell(calls)["modal_decision"]
                    elif arm == "noul":
                        d2 = reduce_noul_cell(calls)["decision"]
    if n != expected:
        raise PreflightError(f"executed {n} calls, expected {expected}")
    return n


# --------------------------------------------------------------------------- analysis

def per_bug(data, rows):
    by = {}
    for r in rows:
        by.setdefault((r["tracker"], r["bug_id"]), {}).setdefault(r["arm"], []).append(r)
    out = {}
    for t, bugs in data.items():
        for b in bugs:
            arms = by.get((t, b["bug_id"]), {})
            if any(len(arms.get(a, [])) != kv.REPEATS for a in kv.ARMS):
                raise PreflightError(f"incomplete calls for {t} bug {b['bug_id']}; refusing to analyze")
            red = {"choice": reduce_choice_or_score_cell(arms["choice"]), "noul": reduce_noul_cell(arms["noul"]),
                   "score": reduce_choice_or_score_cell(arms["score"])}
            s1 = strategy_1_decision_only(red["choice"]["modal_decision"], red["noul"], red["score"])
            out[(t, b["bug_id"])] = {"tracker": t, "red": red, "s1": s1, "a_star": F(b["regression"], b["level"]),
                                     "bug": b}
    return out


def risk(est_entry, p, kind):
    dec, unc = wp.features(p)
    feats = dec if kind == "DECISION" else {**dec, **unc}
    x = [feats[k] for k in est_entry["features"]]
    return est_entry["b"] + sum(w * (xi - m) / s for w, xi, m, s in
                                zip(est_entry["w"], x, est_entry["mu"], est_entry["sd"]))


def scores(P, est):
    out = []
    for key, p in P.items():
        dec, unc = wp.features(p)
        out.append({"key": key, "tracker": p["tracker"], "y": int(p["s1"] != p["a_star"]),
                    "E_dec": risk(est["estimators"]["DECISION"], p, "DECISION"),
                    "E_all": risk(est["estimators"]["ALL"], p, "ALL"),
                    "low_score_conf": -unc["score_conf"],
                    "low_min_conf": -min(unc["choice_conf"], unc["noul_conf"], unc["score_conf"]),
                    "low_product": -(unc["choice_conf"] * unc["noul_conf"] * unc["score_conf"])})
    return out


def _auc(rows, col):
    return auroc([r[col] for r in rows], [bool(r["y"]) for r in rows])


def boot(rows, fn, strat=True, seed=SEED):
    rng = random.Random(seed)
    groups = {}
    for r in rows:
        groups.setdefault(r["tracker"] if strat else "all", []).append(r)
    vals = []
    for _ in range(B):
        sample = [g[rng.randrange(len(g))] for g in groups.values() for _ in g]
        v = fn(sample)
        if v is not None:
            vals.append(v)
    return sorted(vals)


def analyze(data, rows) -> dict:
    est = load_estimator()
    S = scores(per_bug(data, rows), est)
    res = {"n": len(S), "failure_rate": {t: round(sum(r["y"] for r in S if r["tracker"] == t) /
                                                  sum(1 for r in S if r["tracker"] == t), 3) for t in TRACKERS}}
    # HR1: E_dec - low_score_conf, pooled, stratified paired bootstrap, one-sided
    diff = lambda rs: (None if _auc(rs, "E_dec") is None else _auc(rs, "E_dec") - _auc(rs, "low_score_conf"))
    d = boot(S, diff)
    p1 = sum(v <= 0 for v in d) / len(d)
    res["HR1"] = {"auroc_E_dec": round(_auc(S, "E_dec"), 3), "auroc_low_score_conf": round(_auc(S, "low_score_conf"), 3),
                  "difference": round(diff(S), 3), "one_sided_95_lower": round(d[int(0.05 * len(d))], 3),
                  "bootstrap_p_one_sided": round(p1, 4)}
    # HR2: per tracker E_dec > 0.5
    res["HR2"] = {}
    pvals = {"HR1": p1}
    for t in TRACKERS:
        St = [r for r in S if r["tracker"] == t]
        bt = boot(St, lambda rs: _auc(rs, "E_dec"), strat=False, seed=SEED + hash(t) % 1000)
        p = sum(v <= 0.5 for v in bt) / len(bt)
        res["HR2"][t] = {"auroc_E_dec": round(_auc(St, "E_dec"), 3), "one_sided_95_lower": round(bt[int(0.05 * len(bt))], 3),
                         "bootstrap_p_one_sided": round(p, 4)}
        pvals[f"HR2_{t}"] = p
    order = sorted(pvals, key=pvals.get)
    holm, ok = {}, True
    for i, k in enumerate(order):
        ok = ok and pvals[k] <= ALPHA / (len(order) - i)
        holm[k] = ok
    res["holm_supported"] = holm
    # secondary, descriptive
    sec = {}
    for t in (*TRACKERS, "pooled"):
        St = S if t == "pooled" else [r for r in S if r["tracker"] == t]
        sec[t] = {c: round(_auc(St, c), 3) for c in ("E_dec", "E_all", "low_score_conf", "low_min_conf", "low_product")}
        for c in ("E_dec", "E_all", "low_score_conf"):
            o = sorted(St, key=lambda r: r[c])[: int(round(0.8 * len(St)))]
            sec[t][f"risk_at_80pct_coverage_{c}"] = round(sum(r["y"] for r in o) / len(o), 3)
    res["secondary_descriptive"] = sec
    return res


# --------------------------------------------------------------------------- CLI

def preflight() -> dict:
    data = load_heldout()
    load_estimator()
    return {"status": "PREFLIGHT PASSED", "bugs": {t: len(b) for t, b in data.items()},
            "calls_full": EXPECTED_CALLS, "calls_smoke": EXPECTED_SMOKE,
            "estimator_sha256": EST_SHA, "chain": "run_kernel_validation (unchanged)"}


def selftest() -> None:
    est = load_estimator()
    assert "jev_client" not in sys.modules
    fake_red = {"choice": {"modal_decision": "network", "stable": True, "mean_confidence": 1.0,
                           "mean_probabilities": {"network": 1.0, "storage": 0.0}},
                "noul": {"mean_noul": 0.8, "spread": 0.0, "decision": 1},
                "score": {"modal_decision": "1", "stable": True, "mean_confidence": 0.6,
                          "mean_probabilities": {"0": 0.1, "1": 0.7, "2": 0.2}}}
    p_defer = {"red": fake_red, "s1": "defer"}
    p_accept = {"red": {**fake_red, "noul": {"mean_noul": 0.1, "spread": 0.0, "decision": 0}}, "s1": "accept"}
    assert risk(est["estimators"]["DECISION"], p_defer, "DECISION") > risk(est["estimators"]["DECISION"], p_accept, "DECISION")
    # analysis runs end to end on synthetic rows and refuses partial data
    rng = random.Random(1)
    data = {t: [{"bug_id": i, "regression": rng.randint(0, 1), "level": rng.randint(0, 2), "text": "x"}
                for i in range(30)] for t in TRACKERS}
    rows = []
    for t in TRACKERS:
        for b in data[t]:
            for arm in kv.ARMS:
                for r in range(1, kv.REPEATS + 1):
                    if arm == "noul":
                        ans = {"regression": {"type": "noul", "noul": rng.random()}}
                    else:
                        q = "routing" if arm == "choice" else "severity"
                        if arm == "choice":
                            ans = {q: {"type": "choice", "choice": "network", "confidence": 0.9,
                                       "probabilities": {"network": 0.95, "storage": 0.05}}}
                        else:
                            lv = rng.randint(0, 2)
                            ans = {q: {"type": "score", "score": float(lv), "confidence": rng.random(),
                                       "probabilities": {str(k): (0.8 if k == lv else 0.1) for k in range(3)}}}
                    rows.append({"tracker": t, "bug_id": b["bug_id"], "arm": arm, "repeat": r, "http_status": 200,
                                 "parsed_response": {"answers": ans}})
    global B
    saved, B = B, 200
    try:
        res = analyze(data, rows)
        assert set(res["holm_supported"]) == {"HR1", "HR2_mozilla", "HR2_kernel"}
        try:
            analyze(data, rows[:-1])
            raise AssertionError("partial data was analyzed")
        except PreflightError:
            pass
    finally:
        B = saved
    assert "jev_client" not in sys.modules
    print("=== HELD-OUT RUNNER SELF-TESTS PASSED ===")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["dry-run", "live"], default="dry-run")
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--confirm-4500-heldout-calls", dest="confirm", action="store_true")
    ap.add_argument("--smoke-test", action="store_true")
    ap.add_argument("--confirm-450-heldout-smoke-calls", dest="confirm_smoke", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--analyze-only", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if a.analyze_only:
        data = load_heldout()
        smoke = not raw_path(False).exists()
        if smoke:
            data = smoke_subset(data)
        rows = [json.loads(line) for line in raw_path(smoke).open()]
        res = analyze(data, rows)
        name = "heldout_smoketest_analysis.json" if smoke else "heldout_analysis.json"
        (RES / name).write_text(json.dumps(res, indent=2))
        print(json.dumps(res, indent=1))
        return
    info = preflight()
    print(json.dumps(info, indent=1))
    if a.smoke_test:
        if not (a.live and a.confirm_smoke):
            raise SystemExit("Refusing: smoke test needs --live and --confirm-450-heldout-smoke-calls")
        run_live(smoke_subset(load_heldout()), raw_path(True))
        return
    if a.mode == "live":
        if not (a.live and a.confirm):
            raise SystemExit("Refusing: live run needs --live and --confirm-4500-heldout-calls")
        run_live(load_heldout(), raw_path(False))
        return
    print("Dry-run only. No Jev calls were made.")


if __name__ == "__main__":
    main()
