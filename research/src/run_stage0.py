"""Executes the real Stage 0 construction-validation pilot.

Loads the validated manifest (research/data/characterization/
stage0_manifest.json - validated by validate_step0b_manifest.py before
this script runs, per step0b_design_specification.md §15) and issues
exactly manifest-specified calls_planned calls per item, at each item's
canonical presentation, via JevClient (satisfies §15 check #9). Records
raw + parsed responses and a run summary. Computes ONLY the feasibility
statistics defined in §11/§0 (construction feasibility, output
feasibility) - explicitly does NOT compute or imply any H1/H2 hypothesis
verdict (that is out of scope for Stage 0, per §0's three-way distinction).
"""

from __future__ import annotations

import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SRC_DIR))

import pydantic  # noqa: E402
import requests  # noqa: E402

from jev_client import ClientConfig, JevClient  # noqa: E402

REPO_ROOT = SRC_DIR.parent.parent
DATA_DIR = REPO_ROOT / "research" / "data" / "characterization"
MANIFEST_PATH = DATA_DIR / "stage0_manifest.json"
RAW_PATH = DATA_DIR / "stage0_raw_responses.jsonl"
PARSED_PATH = DATA_DIR / "stage0_parsed_responses.jsonl"
META_PATH = DATA_DIR / "stage0_run_metadata.json"


def build_state(item: dict) -> str:
    text_by_id = {s["opaque_id"]: s["text"] for s in item["sentences"]}
    return " ".join(text_by_id[oid] for oid in item["canonical_order"])


def build_question(item: dict, qspec: dict) -> dict:
    primitive = item["primitive"]
    spec = qspec[primitive]
    q = {"type": primitive, "instructions": spec["instructions"]}
    if "criteria" in spec:
        q["criteria"] = spec["criteria"]
    return q


def main() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text())
    qspec = manifest["questions_spec"]
    client = JevClient(config=ClientConfig())

    plan = []
    for item in manifest["items"]:
        for rep in range(1, item["calls_planned"] + 1):
            plan.append((item, rep))

    raw_f = RAW_PATH.open("w", encoding="utf-8")
    parsed_f = PARSED_PATH.open("w", encoding="utf-8")
    records = []

    for idx, (item, rep) in enumerate(plan, 1):
        print(f"[{idx}/{len(plan)}] {item['item_id']} rep{rep}", file=sys.stderr)
        state = build_state(item)
        question = build_question(item, qspec)
        rec = client.ask(state=state, questions={item["item_id"]: question}, test_group=f"stage0:{item['item_id']}")
        d = rec.to_json_dict()
        ans = None
        if d["http_status"] == 200 and d["parsed_response"]:
            ans = list(d["parsed_response"]["answers"].values())[0]

        row = {
            "request_id": d["request_id"], "timestamp_utc": d["timestamp_utc"],
            "item_id": item["item_id"], "primitive": item["primitive"], "condition": item["condition"],
            "repeat_index": rep, "reference_label": item["reference_label"], "is_contested": item["is_contested"],
            "state": state, "questions_spec": d["questions_spec"], "http_status": d["http_status"],
            "latency_ms": d["latency_ms"], "raw_response": d["raw_response"], "error": d["error"],
            "input_hash": d["input_hash"], "answer": ans,
        }
        raw_f.write(json.dumps(row) + "\n")
        parsed_f.write(json.dumps({
            "request_id": d["request_id"], "item_id": item["item_id"], "repeat_index": rep, "answer": ans,
        }) + "\n")
        raw_f.flush(); parsed_f.flush()
        records.append(row)

    raw_f.close(); parsed_f.close()

    meta = {
        "run_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "manifest_path": str(MANIFEST_PATH),
        "manifest_content_hash": __import__("hashlib").sha256(
            json.dumps(manifest, sort_keys=True).encode("utf-8")).hexdigest(),
        "total_calls_planned": len(plan),
        "total_calls_made": len(records),
        "client_config": client.config.redacted_dict(),
        "package_versions": {"python": platform.python_version(), "requests": requests.__version__, "pydantic": pydantic.VERSION},
        "http_status_counts": {},
    }
    for r in records:
        meta["http_status_counts"][str(r["http_status"])] = meta["http_status_counts"].get(str(r["http_status"]), 0) + 1
    META_PATH.write_text(json.dumps(meta, indent=2))
    print(f"\nDone. {len(records)} calls. HTTP status counts: {meta['http_status_counts']}", file=sys.stderr)


if __name__ == "__main__":
    main()
