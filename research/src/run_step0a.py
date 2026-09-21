"""Step 0A: API characterization run.

Strictly observational per the collaborator-approved scope: characterizes
the live Jev API contract, output semantics, determinism, and error
behavior. Does NOT compute or claim anything about calibration, accuracy,
or reliability - there is no ground truth attached to these items, and
none should be inferred. Every raw response is preserved verbatim in
raw_responses.jsonl; parsed_responses.jsonl is a derived, best-effort
parse for convenience and is never the source of truth if the two disagree.

Run with:  .venv/bin/python3 research/src/run_step0a.py
Requires JEV_API_KEY in the environment or research/../.env (repo root .env).
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

RAW_PATH = DATA_DIR / "raw_responses.jsonl"
PARSED_PATH = DATA_DIR / "parsed_responses.jsonl"
META_PATH = DATA_DIR / "run_metadata.json"

# --- The coverage matrix (21 calls; see research/results/characterization_report.md
# for the rationale of each group and item). Each entry becomes one
# JevClient.ask() call except the repeated-identical group, which reuses
# one fixed entry N times.

AMBIGUOUS_CHOICE_CRITERIA = {
    "returns": "Exchanges, wrong or damaged items, requests to send an item back",
    "shipping": "Delivery status, delays, lost packages, carrier issues",
    "billing": "Charges, invoices, payment problems, refund amounts",
}

BASIC_CHOICE = [
    dict(
        key="choice_clear",
        state="My package arrived three weeks late and the box was crushed. "
        "Tracking says delivered but I never received it.",
        questions={"team": {"type": "choice", "instructions": "Which team should handle this support ticket?", "criteria": AMBIGUOUS_CHOICE_CRITERIA}},
    ),
    dict(
        key="choice_ambiguous",
        state="The item I received doesn't match what I ordered, and now I need "
        "to send it back, but I'm also worried it was mispicked during "
        "fulfillment and shipped from the wrong warehouse.",
        questions={"team": {"type": "choice", "instructions": "Which team should handle this support ticket?", "criteria": AMBIGUOUS_CHOICE_CRITERIA}},
    ),
    dict(
        key="choice_two_options",
        state="Reminder: your Q3 report is due Friday. Please submit via the "
        "usual portal. Let me know if you have questions.",
        questions={"label": {"type": "choice", "instructions": "Is this message spam or not spam?", "criteria": {"spam": "Unsolicited, promotional, or fraudulent content", "not_spam": "Legitimate, expected correspondence"}}},
    ),
    dict(
        key="choice_many_options",
        state="def add(a, b):\n    return a + b\n\nprint(add(2, 3))",
        questions={"language": {"type": "choice", "instructions": "Which programming language is this code snippet written in?", "criteria": {"python": "Python", "javascript": "JavaScript", "rust": "Rust", "go": "Go", "java": "Java"}}},
    ),
]

SEVERITY_CRITERIA = [
    "Cosmetic; no impact to functionality",
    "Broken or degraded feature, but a workaround exists",
    "Blocking issue; no workaround exists",
]

BASIC_SCORE = [
    dict(
        key="score_low",
        state="The button color on the settings page is slightly off-brand.",
        questions={"severity": {"type": "score", "instructions": "How severe is the reported issue?", "criteria": SEVERITY_CRITERIA}},
    ),
    dict(
        key="score_high",
        state="The production database is down and no customers can check out.",
        questions={"severity": {"type": "score", "instructions": "How severe is the reported issue?", "criteria": SEVERITY_CRITERIA}},
    ),
    dict(
        key="score_ambiguous",
        state="The search feature returns results slower than usual for about "
        "10% of users, but there's a manual filter workaround.",
        questions={"severity": {"type": "score", "instructions": "How severe is the reported issue?", "criteria": SEVERITY_CRITERIA}},
    ),
    dict(
        key="score_many_levels",
        state="The reviewer left one comment: 'LGTM, nice tests.' No other feedback.",
        questions={"quality": {"type": "score", "instructions": "Rate the code review quality.", "criteria": [
            "No substantive feedback given",
            "Minimal feedback, surface-level only",
            "Some useful feedback on a subset of the change",
            "Thorough feedback covering most of the change",
            "Exceptionally thorough, covers correctness, tests, and design",
        ]}},
    ),
]

BASIC_NOUL = [
    dict(
        key="noul_true",
        state="URGENT: Your account will be suspended in 24 hours. Click here "
        "immediately to verify your password and social security number: "
        "http://secure-bank-verify.ru/login",
        questions={"is_phishing": {"type": "noul", "instructions": "Is this email attempting a phishing attack?"}},
    ),
    dict(
        key="noul_false",
        state="Hi team, attaching the agenda for tomorrow's 10am standup. "
        "Let me know if you want to add anything.",
        questions={"is_phishing": {"type": "noul", "instructions": "Is this email attempting a phishing attack?"}},
    ),
    dict(
        key="noul_ambiguous",
        state="Your subscription payment failed. Please update your billing "
        "info within 3 days to avoid service interruption. Reply to this "
        "email with questions.",
        questions={"is_phishing": {"type": "noul", "instructions": "Is this email attempting a phishing attack?"}},
    ),
    dict(
        key="noul_with_criteria",
        state="A $4,000 charge was made at 3am from a new device in a country "
        "the cardholder has never visited, on a card with no prior "
        "large-transaction history.",
        questions={"is_fraud": {"type": "noul", "instructions": "Does this transaction look fraudulent?", "criteria": {"true": "Strong indicators of fraud are present", "false": "Transaction looks consistent with normal use"}}},
    ),
]

MIXED_PRIMITIVES = dict(
    key="mixed_all_three",
    state="A customer emailed asking to return a laptop that arrived with a "
    "cracked screen. They also mentioned the delivery was two days late.",
    questions={
        "team": {"type": "choice", "instructions": "Which team should handle this support ticket?", "criteria": AMBIGUOUS_CHOICE_CRITERIA},
        "severity": {"type": "score", "instructions": "How severe is the reported issue?", "criteria": SEVERITY_CRITERIA},
        "needs_escalation": {"type": "noul", "instructions": "Does this ticket need to be escalated to a manager?"},
    },
)

EDGE_INVALID = [
    dict(
        key="edge_empty_state",
        state="",
        questions={"team": {"type": "choice", "instructions": "Which team should handle this support ticket?", "criteria": AMBIGUOUS_CHOICE_CRITERIA}},
    ),
    dict(
        key="edge_invalid_type",
        state="This is a normal support message about a late package.",
        questions={"bad": {"type": "maybe", "instructions": "Which team should handle this?", "criteria": AMBIGUOUS_CHOICE_CRITERIA}},
    ),
    dict(
        key="edge_missing_criteria",
        state="This is a normal support message about a late package.",
        questions={"team": {"type": "choice", "instructions": "Which team should handle this support ticket?"}},
    ),
    dict(
        key="edge_single_option_choice",
        state="This is a normal support message about a late package.",
        questions={"team": {"type": "choice", "instructions": "Which team should handle this support ticket?", "criteria": {"shipping": "Delivery status, delays, lost packages"}}},
    ),
]

REPEATED_IDENTICAL_SOURCE = BASIC_CHOICE[1]  # choice_ambiguous, repeated 4x
REPEATED_IDENTICAL_N = 4


def build_plan() -> list[tuple[str, dict]]:
    plan: list[tuple[str, dict]] = []
    for item in BASIC_CHOICE:
        plan.append(("basic_choice", item))
    for item in BASIC_SCORE:
        plan.append(("basic_score", item))
    for item in BASIC_NOUL:
        plan.append(("basic_noul", item))
    for i in range(REPEATED_IDENTICAL_N):
        item = dict(REPEATED_IDENTICAL_SOURCE)
        item = {**item, "key": f"{item['key']}_repeat{i+1}"}
        plan.append(("repeated_identical", item))
    for item in EDGE_INVALID:
        plan.append(("edge_invalid", item))
    plan.append(("mixed_primitives", MIXED_PRIMITIVES))
    return plan


def main() -> None:
    client = JevClient(config=ClientConfig())
    plan = build_plan()

    raw_f = RAW_PATH.open("w", encoding="utf-8")
    parsed_f = PARSED_PATH.open("w", encoding="utf-8")

    records = []
    for test_group, item in plan:
        print(f"[{len(records)+1}/{len(plan)}] {test_group} :: {item['key']}", file=sys.stderr)
        rec = client.ask(state=item["state"], questions=item["questions"], test_group=f"{test_group}:{item['key']}")
        d = rec.to_json_dict()
        raw_f.write(json.dumps({
            "request_id": d["request_id"], "timestamp_utc": d["timestamp_utc"],
            "test_group": d["test_group"], "primitives": d["primitives"],
            "state": d["state"], "questions_spec": d["questions_spec"],
            "http_status": d["http_status"], "latency_ms": d["latency_ms"],
            "raw_response": d["raw_response"], "error": d["error"],
            "is_retry": d["is_retry"], "attempt": d["attempt"],
            "input_hash": d["input_hash"], "config_hash": d["config_hash"],
        }) + "\n")
        parsed_f.write(json.dumps({
            "request_id": d["request_id"], "test_group": d["test_group"],
            "parse_status": d["parse_status"], "parse_notes": d["parse_notes"],
            "parsed_response": d["parsed_response"],
        }) + "\n")
        raw_f.flush()
        parsed_f.flush()
        records.append(d)

    raw_f.close()
    parsed_f.close()

    meta = {
        "run_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "total_calls": len(records),
        "test_groups": sorted({r["test_group"].split(":")[0] for r in records}),
        "client_config": client.config.redacted_dict(),
        "config_hash": client.config.config_hash(),
        "package_versions": {
            "python": platform.python_version(),
            "requests": requests.__version__,
            "pydantic": pydantic.VERSION,
        },
        "http_status_counts": {},
        "parse_status_counts": {},
    }
    for r in records:
        meta["http_status_counts"][str(r["http_status"])] = meta["http_status_counts"].get(str(r["http_status"]), 0) + 1
        meta["parse_status_counts"][r["parse_status"]] = meta["parse_status_counts"].get(r["parse_status"], 0) + 1

    META_PATH.write_text(json.dumps(meta, indent=2))
    print(f"\nDone. {len(records)} calls. Wrote {RAW_PATH}, {PARSED_PATH}, {META_PATH}", file=sys.stderr)
    print(json.dumps(meta["http_status_counts"], indent=2), file=sys.stderr)
    print(json.dumps(meta["parse_status_counts"], indent=2), file=sys.stderr)


if __name__ == "__main__":
    main()
