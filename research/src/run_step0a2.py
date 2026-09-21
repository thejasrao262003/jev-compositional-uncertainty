"""Step 0A.2: two small, focused follow-ups requested after Step 0A.1 review.

(A) `choice` order/repeat factorial: ONE fixed 2:2 evidence pool (the exact
    four sentences from Step 0A.1's symmetric_a/symmetric_b), run under 6
    prespecified permutations x 3 repeats each = 18 calls. Isolates
    permutation variability from repeat variability (a second evidence
    pool was explicitly deferred - see report §0 - to keep this scoped).

(B) `score` matched-evidence-pool characterization: a small pool of
    severity-pre-labeled sentences (3 per level x 3 levels), used to build
    clear/mixed/near-boundary items, including one repeat-triplet and one
    order-swap pair. 9 calls.

Both remain strictly observational - no ground truth, no calibration claim.
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
DATA_DIR.mkdir(parents=True, exist_ok=True)

# =====================================================================
# (A) choice order/repeat factorial
# =====================================================================

# Exact same four sentences as Step 0A.1's symmetric_a/symmetric_b, reused
# deliberately so this follow-up is directly comparable to that result.
N1 = "Requests are timing out at the load balancer before reaching any application server."
N2 = "Ping latency to the affected host has spiked from 2ms to over 400ms."
D1 = "Query execution times in the slow-query log have increased tenfold in the last hour."
D2 = "The connection pool is reporting frequent 'too many connections' errors."

CHOICE_INSTRUCTIONS = "Which subsystem is most likely responsible for this incident?"
CHOICE_CRITERIA = {
    "network": "Issues with connectivity, latency, routing, DNS, or packet loss between systems",
    "database": "Issues with query performance, connection pooling, disk I/O, or transaction locking",
}

# 6 prespecified permutations, chosen to distinguish hypotheses:
# P1/P2: pair-adjacent orderings (= Step 0A.1's symmetric_a / symmetric_b)
# P3/P4: block orderings (all-network-then-database and reverse)
# P5/P6: cross-interleaved orderings that break the pairing structure
PERMUTATIONS = {
    "P1_pairadj_N-first": [N1, D1, N2, D2],
    "P2_pairadj_D-first": [D1, N1, D2, N2],
    "P3_block_N-then-D": [N1, N2, D1, D2],
    "P4_block_D-then-N": [D1, D2, N1, N2],
    "P5_cross_a": [N1, D2, N2, D1],
    "P6_cross_b": [D2, N1, D1, N2],
}
REPEATS_PER_PERMUTATION = 3


def choice_plan() -> list[tuple[str, dict]]:
    plan = []
    for perm_key, sentences in PERMUTATIONS.items():
        for r in range(1, REPEATS_PER_PERMUTATION + 1):
            plan.append((
                "order_repeat_factorial",
                dict(
                    key=f"{perm_key}_rep{r}",
                    permutation=perm_key,
                    repeat_index=r,
                    state=" ".join(sentences),
                    questions={"subsystem": {"type": "choice", "instructions": CHOICE_INSTRUCTIONS, "criteria": CHOICE_CRITERIA}},
                ),
            ))
    return plan


# =====================================================================
# (B) score matched-evidence-pool characterization
# =====================================================================

SEVERITY_CRITERIA = [
    "Cosmetic; no impact to functionality",
    "Broken or degraded feature, but a workaround exists",
    "Blocking issue; no workaround exists",
]

L0 = {  # level 0: cosmetic
    "L0a": "The tooltip on the settings icon is misaligned by a few pixels on Safari.",
    "L0b": "A footer link points to an outdated documentation URL that still resolves correctly.",
    "L0c": "The changelog page lists a feature as 'coming soon' that already shipped last quarter.",
}
L1 = {  # level 1: degraded, workaround exists
    "L1a": "Exporting a report to PDF fails intermittently, but exporting to CSV works as a workaround.",
    "L1b": "The dashboard's live-refresh stops updating after 10 minutes, but a manual reload fixes it.",
    "L1c": "Search results are missing filters for one category, but users can still find items by browsing.",
}
L2 = {  # level 2: blocking, no workaround
    "L2a": "The password reset endpoint returns a 500 error for every request, locking out affected users.",
    "L2b": "Background job processing has stopped entirely; no queued jobs have completed in over an hour.",
    "L2c": "All outbound emails, including password resets and receipts, have stopped sending entirely.",
}
SEV_POOL = {**L0, **L1, **L2}


def score_state(keys: list[str]) -> str:
    return " ".join(SEV_POOL[k] for k in keys)


SCORE_ITEMS = [
    # (key, condition, sentence_keys) - aggregation/independence/contradiction
    # assumptions documented in the report, not assumed here.
    ("score_clear_L0", "clear_level0", ["L0a", "L0b"]),
    ("score_clear_L2", "clear_level2", ["L2a", "L2b"]),
    ("score_mix_L0_L2", "contradictory_0v2", ["L0a", "L2a"]),
    ("score_mix_L1_L2", "boundary_1v2", ["L1a", "L2b"]),
    ("score_mix_L0_L1", "boundary_0v1", ["L0c", "L1c"]),
    ("score_mix_L1_L2_swapped", "boundary_1v2_order_swap", ["L2b", "L1a"]),
    ("score_mix_L1_L2_repeat1", "boundary_1v2_repeat", ["L1a", "L2b"]),
    ("score_mix_L1_L2_repeat2", "boundary_1v2_repeat", ["L1a", "L2b"]),
]


def score_plan() -> list[tuple[str, dict]]:
    plan = []
    for key, condition, keys in SCORE_ITEMS:
        plan.append((
            "score_matched_pool",
            dict(
                key=key, condition=condition, sentence_keys=keys,
                state=score_state(keys),
                questions={"severity": {"type": "score", "instructions": "How severe is the reported issue?", "criteria": SEVERITY_CRITERIA}},
            ),
        ))
    return plan


# =====================================================================
# Runner
# =====================================================================

def run(plan: list[tuple[str, dict]], raw_path: Path, parsed_path: Path, meta_path: Path, extra_meta: dict):
    client = JevClient(config=ClientConfig())
    raw_f = raw_path.open("w", encoding="utf-8")
    parsed_f = parsed_path.open("w", encoding="utf-8")
    records = []

    for idx, (test_group, item) in enumerate(plan, 1):
        print(f"[{idx}/{len(plan)}] {test_group} :: {item['key']}", file=sys.stderr)
        rec = client.ask(state=item["state"], questions=item["questions"], test_group=f"{test_group}:{item['key']}")
        d = rec.to_json_dict()
        ans = None
        if d["http_status"] == 200 and d["parsed_response"]:
            ans = list(d["parsed_response"]["answers"].values())[0]

        row = {
            "request_id": d["request_id"], "timestamp_utc": d["timestamp_utc"],
            "test_group": d["test_group"], "item_meta": {k: v for k, v in item.items() if k not in ("questions",)},
            "questions_spec": d["questions_spec"], "http_status": d["http_status"],
            "latency_ms": d["latency_ms"], "raw_response": d["raw_response"], "error": d["error"],
            "input_hash": d["input_hash"], "answer": ans,
        }
        raw_f.write(json.dumps(row) + "\n")
        parsed_f.write(json.dumps({"request_id": d["request_id"], "test_group": d["test_group"], "answer": ans}) + "\n")
        raw_f.flush(); parsed_f.flush()
        records.append(row)

    raw_f.close(); parsed_f.close()
    meta = {
        "run_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "total_calls": len(records),
        "client_config": client.config.redacted_dict(),
        "config_hash": client.config.config_hash(),
        "package_versions": {"python": platform.python_version(), "requests": requests.__version__, "pydantic": pydantic.VERSION},
        **extra_meta,
    }
    meta_path.write_text(json.dumps(meta, indent=2))
    return records


def main() -> None:
    cplan = choice_plan()
    crecords = run(
        cplan,
        DATA_DIR / "step0a2_order_raw_responses.jsonl",
        DATA_DIR / "step0a2_order_parsed_responses.jsonl",
        DATA_DIR / "step0a2_order_run_metadata.json",
        {"permutations": PERMUTATIONS, "repeats_per_permutation": REPEATS_PER_PERMUTATION},
    )

    print("\n=== (A) choice order/repeat: database-probability by permutation x repeat ===", file=sys.stderr)
    for r in crecords:
        if r["answer"]:
            probs = r["answer"]["probabilities"]
            im = r["item_meta"]
            print(f"  {im['permutation']:22s} rep{im['repeat_index']}  choice={r['answer']['choice']:9s} "
                  f"conf={r['answer']['confidence']:.2f}  database_p={probs.get('database'):.2f}", file=sys.stderr)

    splan = score_plan()
    srecords = run(
        splan,
        DATA_DIR / "step0a2_score_raw_responses.jsonl",
        DATA_DIR / "step0a2_score_parsed_responses.jsonl",
        DATA_DIR / "step0a2_score_run_metadata.json",
        {"severity_pool": SEV_POOL, "items": [{"key": k, "condition": c, "sentence_keys": ks} for (k, c, ks) in SCORE_ITEMS]},
    )

    print("\n=== (B) score matched-pool results ===", file=sys.stderr)
    for r in srecords:
        if r["answer"]:
            im = r["item_meta"]
            print(f"  {im['key']:30s} cond={im['condition']:28s} score={r['answer']['score']:.2f} "
                  f"conf={r['answer']['confidence']:.2f}  probs={r['answer']['probabilities']}", file=sys.stderr)

    print(f"\nDone. {len(crecords)} + {len(srecords)} = {len(crecords)+len(srecords)} calls.", file=sys.stderr)


if __name__ == "__main__":
    main()
