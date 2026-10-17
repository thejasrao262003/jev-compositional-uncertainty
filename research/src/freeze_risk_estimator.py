"""Freeze the workflow-risk estimator for the held-out test
(research/methodology/workflow_risk_heldout_preregistration.md).

Trains ONCE on all 442 Mozilla + kernel bugs already collected, with the
settings fixed in the exploratory probe (workflow_risk_probe.py): L2
logistic regression, lambda = 1, standardized features, plain gradient
descent. No tuning: the settings are the probe's, chosen before its first
run. Writes the coefficients, standardization constants, feature order and
training-data hashes to research/results/frozen_risk_estimator_v1.json,
plus a sha256 of that file, which the held-out runner verifies before
scoring.

PRIMARY estimator: DECISION features (what Jev decided + the workflow action).
SECONDARY: ALL features (decisions + uncertainty signals).

  python3 research/src/freeze_risk_estimator.py
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import workflow_risk_probe as wp  # noqa: E402

OUT = ROOT / "research" / "results" / "frozen_risk_estimator_v1.json"
TRAIN_FILES = ["research/data/mozilla/dataset.jsonl", "research/data/mozilla/mozilla_validation_raw_responses.jsonl",
               "research/data/kernel/dataset.jsonl", "research/data/kernel/kernel_validation_raw_responses.jsonl"]


def sha(p: str) -> str:
    return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()


def feature_names(kind: str, row: dict) -> list[str]:
    d = row["dec"] if kind == "DECISION" else {**row["dec"], **row["unc"]}
    return sorted(d)


def main() -> None:
    if OUT.exists():
        raise SystemExit(f"{OUT.name} exists; the estimator is frozen. Refusing to overwrite.")
    rows = wp.build("mozilla") + wp.build("kernel")
    est = {}
    for kind in ("DECISION", "ALL"):
        model = wp.fit([wp.vec(r, kind) for r in rows], [r["y"] for r in rows])
        est[kind] = {"features": feature_names(kind, rows[0]), **{k: model[k] for k in ("mu", "sd", "w", "b")}}
    rec = {"version": "v1", "status": "FROZEN before any held-out data exists",
           "primary": "DECISION", "secondary": "ALL",
           "target": "S1 action (F on node decisions) != a*", "risk_score": "linear predictor (higher = riskier)",
           "settings": {"lambda": wp.LAMBDA, "lr": wp.LR, "iters": wp.ITERS},
           "trained_on": {"n": len(rows), "files_sha256": {f: sha(f) for f in TRAIN_FILES}},
           "estimators": est}
    OUT.write_text(json.dumps(rec, indent=2))
    digest = hashlib.sha256(OUT.read_bytes()).hexdigest()
    (OUT.with_suffix(".sha256")).write_text(digest + "\n")
    print(f"frozen: {OUT.relative_to(ROOT)}  sha256={digest}")
    for kind, e in est.items():
        top = sorted(zip(e["features"], e["w"]), key=lambda t: -abs(t[1]))[:5]
        print(kind, [(f, round(w, 2)) for f, w in top])


if __name__ == "__main__":
    main()
