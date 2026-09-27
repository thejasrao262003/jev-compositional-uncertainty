"""Runner for the workflow-composition calibration pilot
(workflow_calibration_pilot_protocol.md). Structurally different from
every prior runner in this project: node 2's and node 3's actual input
depends on the LIVE upstream decision (workflow_uncertainty_composition_
protocol.md §1's chain-dependency property), so execution is sequential
per instance, not a flat pre-computed call plan.

--mode dry-run (default): validates manifest/hashes/strategy logic via
  self-tests-style checks; makes ZERO network calls (structurally - the
  sequential caller that touches JevClient is never invoked on this path).
--mode live: requires --live AND --confirm-270-calibration-calls.
--selftest: mutation/robustness suite, no network calls either way.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SRC_DIR))

REPO_ROOT = SRC_DIR.parent.parent
DATA_DIR = REPO_ROOT / "research" / "data" / "characterization"
RESULTS_DIR = REPO_ROOT / "research" / "results"
THIS_FILE = Path(__file__).resolve()

NODE_ORDER = ["choice", "noul", "score"]  # frozen, per §16.3: choice -> noul -> score
N_CALIB = 30
REPEATS_PER_CELL = 3
TOTAL_CALLS = N_CALIB * len(NODE_ORDER) * REPEATS_PER_CELL  # 270
TIE_TOLERANCE = 0.02
STRATEGY2_PROVISIONAL_THRESHOLD = 0.5  # explicitly NOT the frozen Step 2 threshold - see pilot §5


class HashMismatchError(Exception):
    pass


class PlanValidationError(Exception):
    pass


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# ---------------------------------------------------------------------
# Hash verification
# ---------------------------------------------------------------------

def verify_input_hashes() -> dict:
    checks = {}
    hash_record = json.loads((DATA_DIR / "workflow_calibration_pilot_manifest_hashes.json").read_text())
    for key, rel_path, field in [
        ("pilot_manifest", hash_record["manifest_path"], "manifest_sha256"),
        ("pilot_manifest_builder", hash_record["builder_script_path"], "builder_script_sha256"),
    ]:
        actual = _sha256_file(REPO_ROOT / rel_path)
        expected = hash_record[field]
        checks[key] = {"path": rel_path, "expected": expected, "actual": actual, "match": actual == expected}
        if actual != expected:
            raise HashMismatchError(f"{key} ({rel_path}): expected {expected}, got {actual}")
    return checks


def load_manifest() -> dict:
    return json.loads((DATA_DIR / "workflow_calibration_pilot_manifest.json").read_text())


def validate_manifest_identity(manifest: dict) -> None:
    items = manifest["items"]
    if len(items) != N_CALIB:
        raise PlanValidationError(f"expected {N_CALIB} items, got {len(items)}")
    if len({it["item_id"] for it in items}) != N_CALIB:
        raise PlanValidationError("duplicate item_id in manifest")
    for it in items:
        if it["a_star"] not in {"accept", "escalate", "request_more_evidence", "defer"}:
            raise PlanValidationError(f"{it['item_id']}: invalid a_star {it['a_star']!r}")


# ---------------------------------------------------------------------
# Per-node reduction (§2 of the main protocol)
# ---------------------------------------------------------------------

def reduce_choice_or_score_cell(calls: list[dict]) -> dict:
    """calls: list of {"http_status", "parsed_response"} for 3 repeats."""
    valid = []
    non_tied_levels = []
    for c in calls:
        parsed = c.get("parsed_response")
        if not parsed or c.get("http_status") != 200:
            continue
        answer = list(parsed["answers"].values())[0]
        probs = answer["probabilities"]
        valid.append((answer["confidence"], probs, answer.get("choice") or answer.get("score")))
        ranked = sorted(probs.items(), key=lambda kv: kv[1], reverse=True)
        if len(ranked) >= 2 and abs(ranked[0][1] - ranked[1][1]) <= TIE_TOLERANCE:
            continue
        # for choice, top key IS the decision label (network/database); for score, top key is a level index
        non_tied_levels.append(ranked[0][0])

    counts = Counter(non_tied_levels)
    modal_decision, stable = None, False
    if counts:
        top, top_count = counts.most_common(1)[0]
        if top_count >= 2:
            modal_decision, stable = top, True

    mean_confidence = sum(v[0] for v in valid) / len(valid) if valid else None
    mean_probabilities = None
    if valid:
        all_keys = sorted({k for _, probs, _ in valid for k in probs})
        mean_probabilities = {k: sum(probs.get(k, 0.0) for _, probs, _ in valid) / len(valid) for k in all_keys}

    return {"modal_decision": modal_decision, "stable": stable, "mean_confidence": mean_confidence,
            "mean_probabilities": mean_probabilities, "n_valid_responses": len(valid)}


def reduce_noul_cell(calls: list[dict]) -> dict:
    valid = []
    for c in calls:
        parsed = c.get("parsed_response")
        if not parsed or c.get("http_status") != 200:
            continue
        answer = list(parsed["answers"].values())[0]
        valid.append(answer["noul"])
    mean_noul = sum(valid) / len(valid) if valid else None
    spread = (max(valid) - min(valid)) if valid else None
    decision = noul_decision(mean_noul) if mean_noul is not None else None
    return {"mean_noul": mean_noul, "spread": spread, "decision": decision, "n_valid_responses": len(valid)}


def noul_decision(mean_noul: float) -> int:
    """Canonical noul-decision extraction rule, per the main protocol §2 - frozen, reused everywhere."""
    return 1 if mean_noul >= 0.5 else 0


# ---------------------------------------------------------------------
# Strategies (§7 of the main protocol) - implemented exactly as frozen
# ---------------------------------------------------------------------

def strategy_1_decision_only(node1_decision: str, node2_bundle: dict, node3_bundle: dict) -> str:
    """F applied to observed node2/node3 decisions in place of (c2*, c3*) - §5 of the pilot protocol."""
    from build_workflow_calibration_pilot_manifest import F
    c2_obs = node2_bundle["decision"]
    c3_obs = node3_bundle["modal_decision"]
    if c3_obs is None:
        return "escalate"  # no modal decision at all - cannot apply F, fail safe
    return F(c2_obs, int(c3_obs))


def strategy_2_naive_confidence(node1_bundle: dict, node2_bundle: dict, node3_bundle: dict) -> str:
    conf_1 = node1_bundle["mean_confidence"]
    conf_2 = 2 * abs(node2_bundle["mean_noul"] - 0.5) if node2_bundle["mean_noul"] is not None else 0.0
    conf_3 = node3_bundle["mean_confidence"]
    if conf_1 is None or conf_3 is None:
        return "escalate"
    conf_product = conf_1 * conf_2 * conf_3
    return "accept" if conf_product >= STRATEGY2_PROVISIONAL_THRESHOLD else "escalate"


def strategy_3_primitive_aware(node1_bundle: dict, node2_bundle: dict, node3_bundle: dict,
                                score_presentation_risk_active: bool) -> str:
    """Per §7.3, Revision 6: choice's decision has no counterpart in F's
    (c2,c3) input space, so it plays no role in THIS generator's action
    rule (it remains scored on its own via C_1/Δ, unaffected). w_choice
    is retained as a named constant elsewhere in the protocol for a
    future generator where it would apply; unused here, not silently
    dropped."""
    w_noul = 0.5  # disclosed discount constant - not consulted for the action itself,
                  # only relevant to a future weighted-combination generator
    w_score = 0.0 if score_presentation_risk_active else 1.0

    if w_score == 0.0:
        return "escalate"  # score suppressed; F structurally requires a c3-equivalent input

    noul_decision_val = node2_bundle["decision"]
    score_decision = node3_bundle["modal_decision"]
    if noul_decision_val is None or score_decision is None:
        return "escalate"  # missing input, fail safe

    from build_workflow_calibration_pilot_manifest import F
    return F(noul_decision_val, int(score_decision))


def strategy_4a_abstention_aware(node1_bundle: dict, node2_bundle: dict, node3_bundle: dict,
                                  score_presentation_risk_active: bool,
                                  cross_node_disagreement: bool) -> str:
    if not node1_bundle["stable"] or not node3_bundle["stable"]:
        return "escalate"  # repeat-instability trigger (deployable, §8)
    if node1_bundle["mean_confidence"] is not None and node1_bundle["mean_confidence"] >= 0.90:
        return "escalate"  # choice confidence risk region (deployable, §8)
    if cross_node_disagreement:
        return "escalate"  # cross-node disagreement trigger (deployable, §8)
    return strategy_3_primitive_aware(node1_bundle, node2_bundle, node3_bundle, score_presentation_risk_active)


# ---------------------------------------------------------------------
# Preflight / dry-run
# ---------------------------------------------------------------------

def run_preflight() -> dict:
    print("=== Calibration-pilot preflight (dry-run; no network calls) ===")
    hash_checks = verify_input_hashes()
    for key, c in hash_checks.items():
        print(f"  HASH OK: {key} ({c['path']})")
    manifest = load_manifest()
    validate_manifest_identity(manifest)
    print(f"  IDENTITY OK: {N_CALIB} items, all a_star values valid")
    print(f"  PLAN: {N_CALIB} instances x {len(NODE_ORDER)} nodes x {REPEATS_PER_CELL} repeats "
          f"= {TOTAL_CALLS} planned calls (sequential per instance - node 2/3 states depend on "
          f"live upstream decisions, so no flat plan can be precomputed)")
    return {"status": "PREFLIGHT PASSED", "hash_checks": hash_checks, "total_planned_calls": TOTAL_CALLS}


# ---------------------------------------------------------------------
# Live execution - sequential per instance
# ---------------------------------------------------------------------

def build_node_state(node_idx: int, item: dict, node1_decision: str | None, node2_decision: int | None) -> str:
    evidence = item["shared_evidence_state"]
    if node_idx == 0:
        return evidence
    if node_idx == 1:
        return f"{evidence} Routing determination: {node1_decision}."
    impact_label = "customer-facing" if node2_decision == 1 else "not customer-facing"
    return f"{evidence} Routing determination: {node1_decision}. Customer impact assessment: {impact_label}."


def run_live(manifest: dict) -> list[dict]:
    from jev_client import ClientConfig, JevClient

    client = JevClient(config=ClientConfig())
    raw_path = DATA_DIR / "workflow_calibration_pilot_raw_responses.jsonl"
    parsed_path = DATA_DIR / "workflow_calibration_pilot_parsed_responses.jsonl"
    all_records = []
    call_idx = 0

    with raw_path.open("w") as raw_f, parsed_path.open("w") as parsed_f:
        for item in manifest["items"]:
            node1_calls, node2_calls, node3_calls = [], [], []
            node1_decision = None
            node2_decision = None

            for node_idx, node_type in enumerate(NODE_ORDER):
                state = build_node_state(node_idx, item, node1_decision, node2_decision)
                if node_type == "choice":
                    questions = {"routing": {"type": "choice", "instructions": manifest["choice_instructions"],
                                              "criteria": manifest["choice_criteria"]}}
                elif node_type == "noul":
                    questions = {"impact": {"type": "noul", "instructions": manifest["noul_instructions"]}}
                else:
                    questions = {"severity": {"type": "score", "instructions": manifest["severity_instructions"],
                                               "criteria": manifest["severity_criteria"]}}

                calls_this_node = []
                for repeat_index in range(1, REPEATS_PER_CELL + 1):
                    call_idx += 1
                    print(f"[{call_idx}/{TOTAL_CALLS}] {item['item_id']} node={node_type} repeat {repeat_index}",
                          file=sys.stderr)
                    rec = client.ask(state=state, questions=questions,
                                      test_group=f"workflow_calibration_pilot:{item['item_id']}:{node_type}:{repeat_index}")
                    d = rec.to_json_dict()
                    row = {"item_id": item["item_id"], "node_type": node_type, "node_position": node_idx,
                           "repeat_index": repeat_index, "state": state, **d}
                    raw_f.write(json.dumps(row, default=str) + "\n")
                    parsed_f.write(json.dumps({
                        "item_id": item["item_id"], "node_type": node_type, "repeat_index": repeat_index,
                        "is_retry": d["is_retry"], "attempt": d["attempt"], "parsed_response": d["parsed_response"],
                    }, default=str) + "\n")
                    raw_f.flush(); parsed_f.flush()
                    calls_this_node.append(d)
                    all_records.append(row)

                if node_type == "choice":
                    node1_calls = calls_this_node
                    bundle = reduce_choice_or_score_cell(calls_this_node)
                    node1_decision = bundle["modal_decision"]
                elif node_type == "noul":
                    node2_calls = calls_this_node
                    bundle = reduce_noul_cell(calls_this_node)
                    node2_decision = bundle["decision"]
                else:
                    node3_calls = calls_this_node

    if len(all_records) != TOTAL_CALLS:
        raise PlanValidationError(f"executed {len(all_records)} calls, expected exactly {TOTAL_CALLS}")
    return all_records


def analyze(manifest: dict, records: list[dict]) -> dict:
    from collections import defaultdict
    by_item_node = defaultdict(list)
    for r in records:
        by_item_node[(r["item_id"], r["node_type"])].append(r)

    per_item_results = {}
    for item in manifest["items"]:
        iid = item["item_id"]
        node1_bundle = reduce_choice_or_score_cell(by_item_node[(iid, "choice")])
        node2_bundle = reduce_noul_cell(by_item_node[(iid, "noul")])
        node3_bundle = reduce_choice_or_score_cell(by_item_node[(iid, "score")])

        # Deployable triggers only (§8 of the main protocol) - the score
        # construction-class flag is diagnostic-only and NEVER used here.
        score_presentation_risk_active = False  # no deployable score trigger fires by default in this pilot
        cross_node_disagreement = False  # no manifest-level joint-inconsistency rule defined for this pilot's task

        a1 = strategy_1_decision_only(node1_bundle["modal_decision"], node2_bundle, node3_bundle)
        a2 = strategy_2_naive_confidence(node1_bundle, node2_bundle, node3_bundle)
        a3 = strategy_3_primitive_aware(node1_bundle, node2_bundle, node3_bundle, score_presentation_risk_active)
        a4a = strategy_4a_abstention_aware(node1_bundle, node2_bundle, node3_bundle,
                                            score_presentation_risk_active, cross_node_disagreement)

        a_star = item["a_star"]
        y = {"1": int(a1 == a_star), "2": int(a2 == a_star), "3": int(a3 == a_star), "4a": int(a4a == a_star)}
        per_item_results[iid] = {"a_star": a_star, "actions": {"1": a1, "2": a2, "3": a3, "4a": a4a}, "Y_decision": y}

    pairs = [("2", "3"), ("2", "4a"), ("1", "2"), ("1", "3"), ("1", "4a"), ("3", "4a")]
    discordance = {}
    for s1, s2 in pairs:
        n_discordant = sum(1 for res in per_item_results.values() if res["Y_decision"][s1] != res["Y_decision"][s2])
        discordance[f"{s1}_vs_{s2}"] = {"n_discordant": n_discordant, "n_total": len(per_item_results),
                                         "rate": n_discordant / len(per_item_results)}

    return {"per_item_results": per_item_results, "discordance": discordance,
            "primary_discordance_rates": {"2_vs_3": discordance["2_vs_3"]["rate"],
                                           "2_vs_4a": discordance["2_vs_4a"]["rate"]}}


# ---------------------------------------------------------------------
# Self-tests
# ---------------------------------------------------------------------

def _fake_choice_call(decision="network", confidence=0.9, other_probs=None):
    probs = {"network": 0.05, "database": 0.05}
    probs[decision] = confidence
    if other_probs:
        probs.update(other_probs)
    return {"http_status": 200, "parsed_response": {"answers": {"routing": {
        "type": "choice", "choice": decision, "confidence": confidence, "probabilities": probs}}}}


def _fake_score_call(level=0, confidence=0.9):
    probs = {"0": 0.05, "1": 0.05, "2": 0.05}
    probs[str(level)] = confidence
    return {"http_status": 200, "parsed_response": {"answers": {"severity": {
        "type": "score", "score": float(level), "confidence": confidence, "probabilities": probs}}}}


def _fake_noul_call(value=0.5):
    return {"http_status": 200, "parsed_response": {"answers": {"impact": {"type": "noul", "noul": value}}}}


def run_selftest() -> None:
    print("=== Self-test suite (no network calls) ===")

    # 1. Hash-tamper detection
    real_path = DATA_DIR / "workflow_calibration_pilot_manifest.json"
    original = real_path.read_bytes()
    try:
        real_path.write_bytes(original + b" ")
        try:
            verify_input_hashes()
            raise AssertionError("expected HashMismatchError, none raised")
        except HashMismatchError:
            print("  PASS: corrupted pilot manifest is caught by verify_input_hashes()")
    finally:
        real_path.write_bytes(original)
    verify_input_hashes()
    print("  PASS: restored file passes again")

    # 2. Dry-run network guard
    import requests
    def _explode(*a, **k):
        raise AssertionError("requests.post called during dry-run")
    original_post = requests.post
    requests.post = _explode
    try:
        run_preflight()
        print("  PASS: run_preflight() makes zero network calls")
    finally:
        requests.post = original_post

    # 3. Reduction correctness: choice modal decision + all-3-response aggregation
    calls = [_fake_choice_call("network", 0.9), _fake_choice_call("network", 0.8), _fake_choice_call("database", 0.7)]
    b = reduce_choice_or_score_cell(calls)
    assert b["stable"] and b["modal_decision"] == "network"
    expected_mean_conf = (0.9 + 0.8 + 0.7) / 3
    assert abs(b["mean_confidence"] - expected_mean_conf) < 1e-9, "mean_confidence must average ALL 3 responses"
    print(f"  PASS: choice reduction - modal='network' (2/3), mean_confidence={b['mean_confidence']:.3f} "
          f"reflects all 3 responses, not just the 2 matching the modal decision")

    # 4. noul reduction + canonical decision rule
    nb = reduce_noul_cell([_fake_noul_call(0.7), _fake_noul_call(0.6), _fake_noul_call(0.8)])
    assert abs(nb["mean_noul"] - 0.7) < 1e-9
    assert nb["decision"] == 1  # >= 0.5
    print(f"  PASS: noul reduction - mean_noul={nb['mean_noul']:.2f}, canonical decision={nb['decision']}")

    # 5. F re-import sanity + strategy 1 (decision-only)
    node2_bundle = {"decision": 1}
    node3_bundle = reduce_choice_or_score_cell([_fake_score_call(2, 0.9)] * 3)
    a1 = strategy_1_decision_only("network", node2_bundle, node3_bundle)
    assert a1 == "escalate", f"expected escalate for (c2=1,c3=2), got {a1}"
    print(f"  PASS: strategy_1_decision_only correctly applies F to observed decisions ({a1})")

    # 6. Strategy 2 threshold behavior (provisional 0.5)
    n1 = reduce_choice_or_score_cell([_fake_choice_call("network", 0.9)] * 3)
    n2 = reduce_noul_cell([_fake_noul_call(0.9)] * 3)  # conf_2 = 2*|0.9-0.5| = 0.8
    n3 = reduce_choice_or_score_cell([_fake_score_call(0, 0.9)] * 3)
    a2 = strategy_2_naive_confidence(n1, n2, n3)
    conf_product = 0.9 * 0.8 * 0.9
    expected = "accept" if conf_product >= STRATEGY2_PROVISIONAL_THRESHOLD else "escalate"
    assert a2 == expected, f"conf_product={conf_product}, expected {expected}, got {a2}"
    print(f"  PASS: strategy_2_naive_confidence matches conf_product={conf_product:.3f} vs "
          f"threshold={STRATEGY2_PROVISIONAL_THRESHOLD} -> {a2}")

    # 7. Cost-isolation: strategies never reference a_star or cost(.,.) - structural
    #    check via source inspection (no strategy function takes a_star or cost as an arg).
    import inspect
    for fn in (strategy_1_decision_only, strategy_2_naive_confidence, strategy_3_primitive_aware,
               strategy_4a_abstention_aware):
        params = inspect.signature(fn).parameters
        assert "a_star" not in params and "cost" not in params, (
            f"{fn.__name__} must not take a_star/cost as an argument (cost-isolation binding rule, §7)"
        )
    print("  PASS: no strategy function takes a_star or cost(.,.) as an argument (cost/F isolation confirmed structurally)")

    print("\n=== ALL SELF-TESTS PASSED ===")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["dry-run", "live"], default="dry-run")
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--confirm-270-calibration-calls", action="store_true")
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()

    if args.selftest:
        run_selftest()
        return

    if args.mode == "dry-run":
        report = run_preflight()
        out_path = RESULTS_DIR / "workflow_calibration_pilot_preflight_report.json"
        out_path.write_text(json.dumps(report, indent=2))
        print(f"\nWritten: {out_path}")
        print("\nNo calls were made. This was a dry-run.")
        return

    if not (args.live and args.confirm_270_calibration_calls):
        print("Refusing to execute: --mode live requires BOTH --live and "
              "--confirm-270-calibration-calls.", file=sys.stderr)
        sys.exit(1)

    report = run_preflight()
    manifest = load_manifest()
    print("\n=== EXECUTING 270 LIVE CALIBRATION-PILOT CALLS ===")
    records = run_live(manifest)
    analysis = analyze(manifest, records)

    execution_manifest = {
        "status": "CALIBRATION PILOT EXECUTED - result feeds ONLY the §14 sample-size formula, per "
                   "the exhaustive prohibited-use list in workflow_calibration_pilot_protocol.md §2",
        "total_calls": len(records),
        "input_hashes": report["hash_checks"],
        "per_item_results": analysis["per_item_results"],
        "discordance": analysis["discordance"],
        "primary_discordance_rates_for_power_analysis": analysis["primary_discordance_rates"],
    }
    out_path = RESULTS_DIR / "workflow_calibration_pilot_execution_manifest.json"
    out_path.write_text(json.dumps(execution_manifest, indent=2, default=str))

    print(f"\nPrimary discordance rates (feed §14's power analysis ONLY):")
    for pair, rate in analysis["primary_discordance_rates"].items():
        print(f"  {pair}: {rate:.3f}")
    print(f"\nWritten: {out_path}")


if __name__ == "__main__":
    main()
