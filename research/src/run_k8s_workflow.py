"""Jev runner for research/methodology/independent_workflow_preregistration.md (v1).

  python3 research/src/run_k8s_workflow.py --selftest              no network, no Jev
  python3 research/src/run_k8s_workflow.py                         dry run: preflight + call plan only
  python3 research/src/run_k8s_workflow.py --smoke --live --confirm-270-k8s-smoke-calls
  python3 research/src/run_k8s_workflow.py --full  --live --confirm-k8s-full-calls

Frozen elements (protocol §4.1, §5):
- questions: QUESTIONS below are the exact `questions` values;
- state: the original adapter's structure (run_mozilla_validation.node_state @ 7c15bd7),
  relabelled: "Routing determination: <sig>." / "Bug assessment: <a bug|not a bug>.";
- 3 repeats per node, modal reduction (frozen reducers), noul threshold 0.5;
- client: research/src/jev_client/client.py with max_retries=2; every attempt counts toward the cap.
Safeguards: refuses without explicit flags; resumable (skips completed calls); smoke issues are
reused in the full run; stops on model-version mismatch, on >1% failed issues, or at the cap.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
import zlib
from pathlib import Path

SRC = Path(__file__).resolve().parent
sys.path.insert(0, str(SRC))
from build_workflow_calibration_pilot_manifest import F  # noqa: E402
from run_workflow_calibration_pilot import reduce_choice_or_score_cell, reduce_noul_cell  # noqa: E402

ROOT = SRC.parents[1]
DATA = ROOT / "research" / "data" / "k8s"
DS = DATA / "k8s_dataset.jsonl"
RAW = DATA / "k8s_raw_responses.jsonl"
META = DATA / "k8s_run_meta.json"
ARMS = ("choice", "noul", "score")
REPEATS = 3
CAP = 10300  # Amendment 3 (approved 2026-10-23, budget only)
SMOKE_N = 30
EXPECTED_MODEL = "jev-1.13.0"
FAIL_RATE_STOP = 0.01

QUESTIONS = {
    "choice": {"routing": {"type": "choice",
                           "instructions": "Which Kubernetes special interest group (SIG) should own this issue?",
                           "criteria": {
                               "network": "Cluster networking: Services, kube-proxy, DNS, Ingress and Gateway, NetworkPolicy, endpoints, and the Kubernetes side of network-plugin (CNI) integration",
                               "storage": "Persistent storage: volumes, PersistentVolumes and claims, StorageClasses, storage plugins and CSI, snapshots, attach and mount",
                               "node": "The node and kubelet: pod lifecycle on the node, container runtime (CRI), node-level resource management, devices and images, node status and reliability"}}},
    "noul": {"bug": {"type": "noul",
                     "instructions": "Does this issue report a bug (behaviour that is incorrect or broken), as opposed to a feature request, a support question, or a cleanup task?"}},
    "score": {"priority": {"type": "score",
                           "instructions": "How urgently must this issue be worked on?",
                           "criteria": ["Important over the long term or backlog; not needed for the next release",
                                        "Must be staffed and worked on soon, ideally in time for the next release",
                                        "Must be actively worked on as someone's top priority right now"]}},
}


def node_state(text: str, node: str, d1: str | None, d2: int | None) -> str:
    """Original adapter structure; a missing upstream decision is 'undetermined'."""
    route = d1 if d1 is not None else "undetermined"
    if node == "choice":
        return text
    if node == "noul":
        return f"{text}\n\nRouting determination: {route}."
    bug = {1: "a bug", 0: "not a bug"}.get(d2, "undetermined")
    return f"{text}\n\nRouting determination: {route}. Bug assessment: {bug}."


def load():
    rows = [json.loads(l) for l in DS.open()]
    return [r for r in rows if r["split"] == "development"], [r for r in rows if r["split"] == "test"]


def smoke_issues(dev):
    rng = random.Random(zlib.crc32(b"k8s-smoke"))
    return sorted(rng.sample(dev, SMOKE_N), key=lambda r: r["number"])


def done_calls():
    if not RAW.exists():
        return {}, 0
    done, attempts = {}, 0
    for l in RAW.open():
        d = json.loads(l)
        done[(d["number"], d["arm"], d["repeat"])] = d
        attempts += int(d.get("attempt") or 1)
    return done, attempts


def valid(rec):
    return rec.get("http_status") == 200 and rec.get("parsed_response")


def run(issues, client, label):
    done, attempts = done_calls()
    failed, version_seen = [], set()
    with RAW.open("a", encoding="utf-8") as f:
        for k, iss in enumerate(issues, 1):
            d1 = d2 = None
            ok = True
            for arm in ARMS:
                state = node_state(iss["text"], arm, d1, d2)
                calls = []
                for r in range(1, REPEATS + 1):
                    key = (iss["number"], arm, r)
                    if key in done:
                        rec = done[key]
                    else:
                        if attempts >= CAP:
                            raise SystemExit(f"STOP: call cap {CAP} reached")
                        rec = client.ask(state=state, questions=QUESTIONS[arm],
                                         test_group=f"k8s:{iss['split']}:{iss['number']}:{arm}:{r}").to_json_dict()
                        attempts += int(rec.get("attempt") or 1)
                        row = {"number": iss["number"], "split": iss["split"], "arm": arm, "repeat": r, **rec}
                        f.write(json.dumps(row, default=str) + "\n")
                        f.flush()
                        done[key] = row
                        rec = row
                    m = (rec.get("raw_response") or {}).get("model") if isinstance(rec.get("raw_response"), dict) else None
                    if m:
                        version_seen.add(m)
                    calls.append(rec)
                if not any(valid(c) for c in calls):
                    ok = False
                if arm == "choice":
                    d1 = reduce_choice_or_score_cell(calls)["modal_decision"]
                elif arm == "noul":
                    d2 = reduce_noul_cell(calls)["decision"]
            if not ok:
                failed.append(iss["number"])
            print(f"[{label}] {k}/{len(issues)} issues, attempts so far {attempts}", file=sys.stderr)
            if version_seen - {EXPECTED_MODEL}:
                raise SystemExit(f"STOP: resolved model {sorted(version_seen)} != {EXPECTED_MODEL}")
            if len(failed) > FAIL_RATE_STOP * len(issues) and len(failed) > 1:
                raise SystemExit(f"STOP: {len(failed)} failed issues exceeds 1% of {len(issues)}")
    return {"label": label, "issues": len(issues), "failed_issues": failed, "attempts_total": attempts,
            "models_seen": sorted(version_seen)}


def preflight():
    dev, test = load()
    smoke = smoke_issues(dev)
    _, attempts = done_calls()
    plan = {"dataset_sha256": hashlib.sha256(DS.read_bytes()).hexdigest(),
            "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "development": len(dev), "test": len(test),
            "smoke_issues": len(smoke), "smoke_calls": len(smoke) * 9,
            "full_calls_excluding_smoke": (len(dev) + len(test) - len(smoke)) * 9,
            "planned_total": (len(dev) + len(test)) * 9, "cap_including_retries": CAP,
            "attempts_already_recorded": attempts}
    assert plan["planned_total"] <= CAP, "plan exceeds cap"
    return plan


def selftest():
    assert node_state("T", "choice", None, None) == "T"
    assert node_state("T", "noul", "node", None) == "T\n\nRouting determination: node."
    assert node_state("T", "score", "storage", 1) == "T\n\nRouting determination: storage. Bug assessment: a bug."
    assert node_state("T", "score", None, None) == "T\n\nRouting determination: undetermined. Bug assessment: undetermined."
    assert node_state("T", "score", "network", 0) == "T\n\nRouting determination: network. Bug assessment: not a bug."
    assert set(QUESTIONS["choice"]["routing"]["criteria"]) == {"network", "storage", "node"}
    assert len(QUESTIONS["score"]["priority"]["criteria"]) == 3
    assert F(1, 1) == "defer" and F(0, 1) == "accept" and F(0, 2) == "escalate"
    # the frozen strings must match the protocol text exactly
    proto = (ROOT / "research" / "methodology" / "independent_workflow_preregistration.md").read_text()
    for arm, q in QUESTIONS.items():
        inner = list(q.values())[0]
        assert inner["instructions"] in proto, arm
        crit = inner.get("criteria", {})
        for c in (crit.values() if isinstance(crit, dict) else crit):
            assert c in proto, c
    print("selftest OK")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--full", action="store_true")
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--confirm-270-k8s-smoke-calls", dest="confirm_smoke", action="store_true")
    ap.add_argument("--confirm-k8s-full-calls", dest="confirm_full", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    plan = preflight()
    print(json.dumps(plan, indent=1))
    if not (a.smoke or a.full):
        print("Dry run only. No Jev calls were made.")
        return
    from jev_client import ClientConfig, JevClient  # live path only
    client = JevClient(config=ClientConfig(max_retries=2))
    dev, test = load()
    if a.smoke:
        if not (a.live and a.confirm_smoke):
            raise SystemExit("Refusing: smoke needs --live --confirm-270-k8s-smoke-calls")
        res = run(smoke_issues(dev), client, "smoke")
    else:
        if not (a.live and a.confirm_full):
            raise SystemExit("Refusing: full run needs --live --confirm-k8s-full-calls")
        meta = json.loads(META.read_text()) if META.exists() else {}
        if not meta.get("smoke", {}).get("models_seen") == [EXPECTED_MODEL]:
            raise SystemExit("Refusing: smoke test must pass the version check first")
        smoke_ids = {r["number"] for r in smoke_issues(dev)}
        res = run(smoke_issues(dev) + [r for r in dev if r["number"] not in smoke_ids] + test, client, "full")
    meta = json.loads(META.read_text()) if META.exists() else {}
    meta[res["label"]] = {**res, "plan": plan}
    META.write_text(json.dumps(meta, indent=1))
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
