"""Step 0A.1: controlled ambiguity characterization (feasibility check).

Purpose: determine whether the Jev API produces a MEASURABLE response to a
controlled, pre-registered manipulation of evidence overlap - not whether
Jev is "calibrated" (no ground truth is attached to any item here; this is
still strictly observational, one level more deliberate than Step 0A).

Design discipline (per collaborator review): the criterion-satisfaction
matrix below is defined FIRST, as data, before any prompt text is written.
The prompt text is an implementation of that matrix, not the other way
around. Across all 8 `choice` items: identical instructions, identical
criteria dict, identical option count (2), identical sentence count (4)
and closely matched sentence length/register, drawn from a fixed 8-sentence
pool (4 "network"-flavored, 4 "database"-flavored). Only WHICH sentences
are included (the N:D ratio) varies by condition - that ratio is the one
manipulated variable.
"""

from __future__ import annotations

import json
import math
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
DATA_DIR.mkdir(parents=True, exist_ok=True)
RAW_PATH = DATA_DIR / "step0a1_raw_responses.jsonl"
PARSED_PATH = DATA_DIR / "step0a1_parsed_responses.jsonl"
META_PATH = DATA_DIR / "step0a1_run_metadata.json"

# --- Fixed sentence pool (criterion-satisfaction matrix building blocks) --
# Matched register/length (~90-110 chars each): "<subject> <verb-phrase> <detail>."

N = {  # network-flavored symptom sentences
    "N1": "Requests are timing out at the load balancer before reaching any application server.",
    "N2": "Ping latency to the affected host has spiked from 2ms to over 400ms.",
    "N3": "The firewall logs show a sudden burst of dropped packets on the primary uplink.",
    "N4": "DNS resolution for internal services is intermittently failing across the cluster.",
}
D = {  # database-flavored symptom sentences
    "D1": "Query execution times in the slow-query log have increased tenfold in the last hour.",
    "D2": "The connection pool is reporting frequent 'too many connections' errors.",
    "D3": "Disk I/O wait times on the primary replica have climbed sharply since the last deploy.",
    "D4": "Several write transactions are failing with lock-timeout errors.",
}

CHOICE_INSTRUCTIONS = "Which subsystem is most likely responsible for this incident?"
CHOICE_CRITERIA = {
    "network": "Issues with connectivity, latency, routing, DNS, or packet loss between systems",
    "database": "Issues with query performance, connection pooling, disk I/O, or transaction locking",
}

# The pre-registered manipulation matrix: (condition, item_key, sentence keys in order, intended N:D ratio)
CHOICE_MATRIX = [
    ("baseline", "baseline_network", ["N1", "N2", "N3", "N4"], "4:0"),
    ("baseline", "baseline_database", ["D1", "D2", "D3", "D4"], "0:4"),
    ("moderate", "moderate_network", ["N1", "N2", "N3", "D1"], "3:1"),
    ("moderate", "moderate_database", ["N1", "D1", "D2", "D3"], "1:3"),
    ("high_overlap", "high_overlap_a", ["N1", "N2", "D1", "D2"], "2:2"),
    ("high_overlap", "high_overlap_b", ["D3", "D4", "N3", "N4"], "2:2"),
    ("symmetric", "symmetric_a", ["N1", "D1", "N2", "D2"], "2:2 (mirrored pairs, interleaved)"),
    ("symmetric", "symmetric_b", ["D1", "N1", "D2", "N2"], "2:2 (mirrored pairs, order-swapped)"),
]


def build_state(sentence_keys: list[str]) -> str:
    pool = {**N, **D}
    return " ".join(pool[k] for k in sentence_keys)


CHOICE_ITEMS = [
    dict(
        key=item_key,
        condition=condition,
        ratio=ratio,
        sentence_keys=keys,
        state=build_state(keys),
        questions={"subsystem": {"type": "choice", "instructions": CHOICE_INSTRUCTIONS, "criteria": CHOICE_CRITERIA}},
    )
    for (condition, item_key, keys, ratio) in CHOICE_MATRIX
]

# --- Score equivalents: same idea, one clear level-2 item, one item
# deliberately balanced between level 1 and level 2 (matched register).
SCORE_CRITERIA = [
    "Cosmetic; no impact to functionality",
    "Broken or degraded feature, but a workaround exists",
    "Blocking issue; no workaround exists",
]
SCORE_ITEMS = [
    dict(
        key="score_clear_level2",
        condition="clear",
        state="The checkout API returns HTTP 500 for every request. No customer "
        "has been able to complete a purchase for the last 40 minutes, and "
        "there is no alternate path to check out.",
        questions={"severity": {"type": "score", "instructions": "How severe is the reported issue?", "criteria": SCORE_CRITERIA}},
    ),
    dict(
        key="score_boundary_1_vs_2",
        condition="boundary",
        state="The checkout API returns HTTP 500 for about half of requests. "
        "Customers can complete a purchase by retrying two or three times, "
        "which most manage to do, but a portion give up and abandon the cart.",
        questions={"severity": {"type": "score", "instructions": "How severe is the reported issue?", "criteria": SCORE_CRITERIA}},
    ),
]

REPEAT_SOURCE_KEY = "symmetric_a"
REPEAT_N = 2  # two ADDITIONAL calls beyond the one already in CHOICE_ITEMS -> n=3 total for this item


def entropy_bits(probs: dict[str, float]) -> float | None:
    vals = [p for p in probs.values() if p > 0]
    if not vals or abs(sum(probs.values()) - 1.0) > 1e-6:
        return None
    return -sum(p * math.log2(p) for p in vals)


def top_two_gap(probs: dict[str, float]) -> float:
    s = sorted(probs.values(), reverse=True)
    return s[0] - (s[1] if len(s) > 1 else 0.0)


def main() -> None:
    client = JevClient(config=ClientConfig())

    plan: list[tuple[str, dict]] = [("controlled_choice", item) for item in CHOICE_ITEMS]
    plan += [("score_equivalent", item) for item in SCORE_ITEMS]
    repeat_source = next(i for i in CHOICE_ITEMS if i["key"] == REPEAT_SOURCE_KEY)
    for i in range(REPEAT_N):
        item = {**repeat_source, "key": f"{repeat_source['key']}_repeat{i+1}"}
        plan.append(("repeat_control", item))

    raw_f = RAW_PATH.open("w", encoding="utf-8")
    parsed_f = PARSED_PATH.open("w", encoding="utf-8")
    records = []

    for idx, (test_group, item) in enumerate(plan, 1):
        print(f"[{idx}/{len(plan)}] {test_group} :: {item['key']}", file=sys.stderr)
        rec = client.ask(state=item["state"], questions=item["questions"], test_group=f"{test_group}:{item['key']}")
        d = rec.to_json_dict()

        stats = None
        if d["http_status"] == 200 and d["parsed_response"]:
            ans = list(d["parsed_response"]["answers"].values())[0]
            if ans["type"] == "choice":
                probs = ans["probabilities"]
                stats = {
                    "selected": ans["choice"], "confidence": ans["confidence"],
                    "max_probability": max(probs.values()), "entropy_bits": entropy_bits(probs),
                    "top_two_gap": top_two_gap(probs), "probabilities": probs,
                }
            elif ans["type"] == "score":
                probs = ans["probabilities"]
                stats = {
                    "score": ans["score"], "confidence": ans["confidence"],
                    "max_probability": max(probs.values()), "entropy_bits": entropy_bits(probs),
                    "top_two_gap": top_two_gap(probs), "probabilities": probs,
                }

        raw_f.write(json.dumps({
            "request_id": d["request_id"], "timestamp_utc": d["timestamp_utc"],
            "test_group": d["test_group"], "condition": item.get("condition"),
            "ratio": item.get("ratio"), "sentence_keys": item.get("sentence_keys"),
            "state": d["state"], "questions_spec": d["questions_spec"],
            "http_status": d["http_status"], "latency_ms": d["latency_ms"],
            "raw_response": d["raw_response"], "error": d["error"],
            "input_hash": d["input_hash"],
        }) + "\n")
        parsed_f.write(json.dumps({
            "request_id": d["request_id"], "test_group": d["test_group"],
            "condition": item.get("condition"), "ratio": item.get("ratio"),
            "parse_status": d["parse_status"], "stats": stats,
        }) + "\n")
        raw_f.flush(); parsed_f.flush()
        records.append({**d, "condition": item.get("condition"), "ratio": item.get("ratio"), "stats": stats})

    raw_f.close(); parsed_f.close()

    meta = {
        "run_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "total_calls": len(records),
        "client_config": client.config.redacted_dict(),
        "config_hash": client.config.config_hash(),
        "package_versions": {"python": platform.python_version(), "requests": requests.__version__, "pydantic": pydantic.VERSION},
        "choice_matrix": [{"condition": c, "item": k, "sentence_keys": ks, "ratio": r} for (c, k, ks, r) in CHOICE_MATRIX],
    }
    META_PATH.write_text(json.dumps(meta, indent=2))

    print("\n=== Summary: choice items, max_probability by condition ===", file=sys.stderr)
    for r in records:
        if r["test_group"].startswith("controlled_choice") and r["stats"]:
            print(f"  {r['condition']:12s} {r['test_group']:45s} ratio={r['ratio']:30s} "
                  f"max_p={r['stats']['max_probability']:.3f} entropy={r['stats']['entropy_bits']} "
                  f"conf={r['stats']['confidence']}", file=sys.stderr)
    print(f"\nDone. Wrote {RAW_PATH}, {PARSED_PATH}, {META_PATH}", file=sys.stderr)


if __name__ == "__main__":
    main()
