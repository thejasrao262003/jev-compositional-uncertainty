"""Executes the Stage 1 core run for `choice` and `noul` (NOT `score`).

NOT YET RUN. Written and validated (JevClient usage, per
step0b_design_specification.md §15 check #9) ahead of execution, per the
project's practice of writing and validating runners before spending API
budget. Do not run this against the live API without separate,
explicit sign-off - it is not gated by this file itself.

Call plan (108 calls core, matches
step0b_design_specification.md §11's Stage 1 budget for two primitives):
  - 60 primary items x 1 call each, canonical presentation.
  - 12-item robustness+repeat subset x 2 alternate presentations each
    (reverse, seeded_shuffle - both precomputed and frozen in the
    manifest's `alternate_orders`, never generated here) = 24 calls.
  - Same 12 items x 2 additional canonical-order repeats = 24 calls.

Reserve/overflow replacement (the manifest's `overflow_replacement_list`)
is NOT automated here - per §11, any reserve substitution is a reviewed,
manual step applied to a specific failed cell, never a silent runner
behavior.
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
MANIFEST_PATH = DATA_DIR / "stage1_manifest_choice_noul.json"
RAW_PATH = DATA_DIR / "stage1_raw_responses.jsonl"
PARSED_PATH = DATA_DIR / "stage1_parsed_responses.jsonl"
META_PATH = DATA_DIR / "stage1_run_metadata.json"

CHOICE_QSPEC = {
    "A": {
        "instructions": "Is this incident most likely caused by infrastructure or by an application-level change?",
        "criteria": {
            "infrastructure": "Network, hardware, DNS, load-balancing, or platform-level causes",
            "application": "A code, configuration, or deploy-level cause within a specific service",
        },
    },
    "B": {
        "instructions": "Which team should handle this support ticket: billing or shipping?",
        "criteria": {
            "billing": "Charges, invoices, refunds, payment methods, promotional codes",
            "shipping": "Delivery status, tracking, damaged or lost packages, address changes",
        },
    },
}
NOUL_QSPEC = {
    "A": {"instructions": "Does this transaction look fraudulent?"},
    "B": {"instructions": "Does this message look like a phishing or scam attempt?"},
}


def build_state(item: dict, order: list[str]) -> str:
    text_by_id = {s["opaque_id"]: s["text"] for s in item["sentences"]}
    return " ".join(text_by_id[oid] for oid in order)


def build_question(item: dict) -> dict:
    primitive = item["primitive"]
    domain = item["domain"]
    spec = (CHOICE_QSPEC if primitive == "choice" else NOUL_QSPEC)[domain]
    q = {"type": primitive, "instructions": spec["instructions"]}
    if "criteria" in spec:
        q["criteria"] = spec["criteria"]
    return q


def build_plan(manifest: dict) -> list[dict]:
    items_by_id = {it["item_id"]: it for it in manifest["items"]}
    subset = set(manifest["robustness_repeat_subset_ids"])
    alt_orders = manifest["alternate_orders"]
    plan = []
    for item in manifest["items"]:
        if "overflow" in item["item_id"]:
            continue  # reserve items are not called unless manually substituted in
        plan.append({"item_id": item["item_id"], "call_purpose": "primary_canonical",
                     "order": item["canonical_order"], "repeat_index": 1})
        if item["item_id"] in subset:
            for alt_name, alt_order in alt_orders[item["item_id"]].items():
                plan.append({"item_id": item["item_id"], "call_purpose": f"alt_presentation_{alt_name}",
                             "order": alt_order, "repeat_index": None})
            for r in (2, 3):
                plan.append({"item_id": item["item_id"], "call_purpose": "canonical_repeat",
                             "order": item["canonical_order"], "repeat_index": r})
    return plan


def main() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text())
    items_by_id = {it["item_id"]: it for it in manifest["items"]}
    plan = build_plan(manifest)
    print(f"Planned calls: {len(plan)} (expected 108 for the core Stage 1 choice+noul run)", file=sys.stderr)

    client = JevClient(config=ClientConfig())
    raw_f = RAW_PATH.open("w", encoding="utf-8")
    parsed_f = PARSED_PATH.open("w", encoding="utf-8")
    records = []

    for idx, call in enumerate(plan, 1):
        item = items_by_id[call["item_id"]]
        state = build_state(item, call["order"])
        question = build_question(item)
        print(f"[{idx}/{len(plan)}] {call['item_id']} :: {call['call_purpose']}", file=sys.stderr)
        rec = client.ask(state=state, questions={item["item_id"]: question},
                          test_group=f"stage1:{call['call_purpose']}:{item['item_id']}")
        d = rec.to_json_dict()
        ans = None
        if d["http_status"] == 200 and d["parsed_response"]:
            ans = list(d["parsed_response"]["answers"].values())[0]
        row = {
            "request_id": d["request_id"], "timestamp_utc": d["timestamp_utc"],
            "item_id": item["item_id"], "primitive": item["primitive"], "domain": item["domain"],
            "condition": item["condition"], "call_purpose": call["call_purpose"],
            "repeat_index": call["repeat_index"], "reference_label": item["reference_label"],
            "is_contested": item["is_contested"], "state": state, "http_status": d["http_status"],
            "latency_ms": d["latency_ms"], "raw_response": d["raw_response"], "error": d["error"],
            "input_hash": d["input_hash"], "answer": ans,
        }
        raw_f.write(json.dumps(row) + "\n")
        parsed_f.write(json.dumps({"request_id": d["request_id"], "item_id": item["item_id"],
                                    "call_purpose": call["call_purpose"], "answer": ans}) + "\n")
        raw_f.flush(); parsed_f.flush()
        records.append(row)

    raw_f.close(); parsed_f.close()
    meta = {
        "run_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "manifest_path": str(MANIFEST_PATH),
        "manifest_content_hash": __import__("hashlib").sha256(
            json.dumps(manifest, sort_keys=True).encode("utf-8")).hexdigest(),
        "total_calls_planned": len(plan), "total_calls_made": len(records),
        "client_config": client.config.redacted_dict(),
        "package_versions": {"python": platform.python_version(), "requests": requests.__version__, "pydantic": pydantic.VERSION},
        "http_status_counts": {},
    }
    for r in records:
        meta["http_status_counts"][str(r["http_status"])] = meta["http_status_counts"].get(str(r["http_status"]), 0) + 1
    META_PATH.write_text(json.dumps(meta, indent=2))
    print(f"\nDone. {len(records)} calls. {meta['http_status_counts']}", file=sys.stderr)


if __name__ == "__main__":
    main()
