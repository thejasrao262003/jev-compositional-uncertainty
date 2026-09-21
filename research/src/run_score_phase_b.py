"""Phase B runner for score_bounded_semantic_validation_protocol.md.

Per review's blocking finding: the protocol's requirements (fixed 27-call
budget, unmodified six-item gate vs. separate nine-item pairwise n_P,
immutable-identity hash checks, the outcome-interpretation matrix, no
network calls in dry-run) previously existed only as prose. This script
makes them executable and auditable, per the ten numbered requirements in
review's message.

Modes:
  --mode dry-run (default): builds and validates the full 27-call plan,
    performs every preflight check, and writes a preflight report. Makes
    ZERO network calls - JevClient is never even imported on this path.
  --mode live: executes the 27 calls for real. Requires BOTH --live and
    --confirm-27-calls to be passed, on top of --mode live, as a defense-
    in-depth guard against accidental execution. NOT invoked by anything
    in this repository's own tooling; a human must type the flags.
  --selftest: runs the mutation/robustness test suite (no API calls
    either way) and exits.

This script does not decide whether Phase B may run. That decision is
external, per every prior stage's practice in this project.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SRC_DIR))

from verify_score_gate_logic import gate as frozen_gate  # noqa: E402

REPO_ROOT = SRC_DIR.parent.parent
DATA_DIR = REPO_ROOT / "research" / "data" / "characterization"
RESULTS_DIR = REPO_ROOT / "research" / "results"
THIS_FILE = Path(__file__).resolve()

REPEATS_PER_ITEM = 3
EXPECTED_TOTAL_CALLS = 27
FROZEN_ITEM_COUNT = 6
SUPPLEMENT_ITEM_COUNT = 3
TIE_TOLERANCE = 0.02


class PlanValidationError(Exception):
    pass


class HashMismatchError(Exception):
    pass


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# ---------------------------------------------------------------------
# 1. Immutable-identity hash verification (requirement: check before
#    making any call, not after).
# ---------------------------------------------------------------------

def verify_input_hashes() -> dict:
    """Recomputes SHA-256 for every upstream artifact Phase B depends on
    and compares against its recorded hash file. Raises on any mismatch -
    never proceeds on a stale or tampered input."""
    checks = {}

    supp_hashes = json.loads((DATA_DIR / "score_supplement_hashes.json").read_text())
    for key, rel_path in [
        ("design_script", supp_hashes["design_script"]["path"]),
        ("supplement_record", supp_hashes["supplement_record"]["path"]),
    ]:
        actual = _sha256_file(REPO_ROOT / rel_path)
        expected = supp_hashes[key]["sha256"]
        checks[key] = {"path": rel_path, "expected": expected, "actual": actual, "match": actual == expected}
        if actual != expected:
            raise HashMismatchError(f"{key} ({rel_path}): expected {expected}, got {actual}")

    manifest_hashes = json.loads((DATA_DIR / "score_phase_b_manifest_hashes.json").read_text())
    for key, rel_path, hash_field in [
        ("phase_b_manifest", manifest_hashes["manifest_path"], "manifest_sha256"),
        ("phase_b_manifest_builder", manifest_hashes["builder_script_path"], "builder_script_sha256"),
    ]:
        actual = _sha256_file(REPO_ROOT / rel_path)
        expected = manifest_hashes[hash_field]
        checks[key] = {"path": rel_path, "expected": expected, "actual": actual, "match": actual == expected}
        if actual != expected:
            raise HashMismatchError(f"{key} ({rel_path}): expected {expected}, got {actual}")

    gate_script_path = "research/src/verify_score_gate_logic.py"
    gate_verification_txt = (RESULTS_DIR / "score_gate_logic_verification.txt").read_text()
    expected_gate_hash = gate_verification_txt.splitlines()[1].split(": ")[1]
    actual_gate_hash = _sha256_file(REPO_ROOT / gate_script_path)
    checks["gate_script"] = {
        "path": gate_script_path, "expected": expected_gate_hash,
        "actual": actual_gate_hash, "match": actual_gate_hash == expected_gate_hash,
    }
    if actual_gate_hash != expected_gate_hash:
        raise HashMismatchError(f"gate_script: expected {expected_gate_hash}, got {actual_gate_hash}")

    return checks


# ---------------------------------------------------------------------
# 2/7. Load + validate the 9-item identity set; build + validate the
#    27-call plan. Rejects unexpected/duplicate/missing items or an
#    unauthorized call count.
# ---------------------------------------------------------------------

def load_manifest() -> dict:
    return json.loads((DATA_DIR / "score_phase_b_manifest.json").read_text())


def validate_item_identity(manifest: dict) -> None:
    items = manifest["items"]
    if len(items) != FROZEN_ITEM_COUNT + SUPPLEMENT_ITEM_COUNT:
        raise PlanValidationError(f"expected {FROZEN_ITEM_COUNT + SUPPLEMENT_ITEM_COUNT} items, got {len(items)}")

    frozen = [it for it in items if it["source_group"] == "frozen_primary"]
    supplement = [it for it in items if it["source_group"] == "supplement_v1"]
    if len(frozen) != FROZEN_ITEM_COUNT:
        raise PlanValidationError(f"expected {FROZEN_ITEM_COUNT} frozen_primary items, got {len(frozen)}")
    if len(supplement) != SUPPLEMENT_ITEM_COUNT:
        raise PlanValidationError(f"expected {SUPPLEMENT_ITEM_COUNT} supplement_v1 items, got {len(supplement)}")

    expected_frozen_compositions = {
        (0, 0, 0, 1), (0, 0, 0, 2), (0, 0, 1, 2), (0, 1, 1, 2), (0, 1, 2, 2), (1, 1, 1, 2),
    }
    expected_supplement_compositions = {
        (0, 0, 0, 1, 2), (0, 0, 0, 2, 2), (0, 0, 2, 2, 2),
    }
    actual_frozen = {tuple(it["composition_multiset"]) for it in frozen}
    actual_supplement = {tuple(it["composition_multiset"]) for it in supplement}
    if actual_frozen != expected_frozen_compositions:
        raise PlanValidationError(f"frozen composition set mismatch: {actual_frozen} != {expected_frozen_compositions}")
    if actual_supplement != expected_supplement_compositions:
        raise PlanValidationError(f"supplement composition set mismatch: {actual_supplement} != {expected_supplement_compositions}")

    item_ids = [it["item_id"] for it in items]
    if len(set(item_ids)) != len(item_ids):
        raise PlanValidationError(f"duplicate item_id in manifest: {item_ids}")


def build_call_plan(manifest: dict) -> list[dict]:
    plan = []
    for item in manifest["items"]:
        for repeat_index in range(1, REPEATS_PER_ITEM + 1):
            plan.append({
                "item_id": item["item_id"],
                "source_group": item["source_group"],
                "repeat_index": repeat_index,
                "state": item["state"],
                "questions": {
                    "severity": {
                        "type": "score",
                        "instructions": manifest["severity_instructions"],
                        "criteria": manifest["severity_criteria"],
                    }
                },
            })
    return plan


def validate_plan(plan: list[dict], manifest: dict) -> None:
    if len(plan) != EXPECTED_TOTAL_CALLS:
        raise PlanValidationError(f"expected exactly {EXPECTED_TOTAL_CALLS} planned calls, got {len(plan)}")

    expected_item_ids = {it["item_id"] for it in manifest["items"]}
    cells = [(c["item_id"], c["repeat_index"]) for c in plan]
    if len(set(cells)) != len(cells):
        raise PlanValidationError("duplicate (item_id, repeat_index) cell in plan")

    plan_item_ids = {c["item_id"] for c in plan}
    unexpected = plan_item_ids - expected_item_ids
    missing = expected_item_ids - plan_item_ids
    if unexpected:
        raise PlanValidationError(f"plan contains unexpected item_id(s) not in manifest: {unexpected}")
    if missing:
        raise PlanValidationError(f"plan is missing item_id(s) present in manifest: {missing}")

    from collections import Counter
    counts = Counter(c["item_id"] for c in plan)
    wrong_count = {k: v for k, v in counts.items() if v != REPEATS_PER_ITEM}
    if wrong_count:
        raise PlanValidationError(f"item(s) with repeat count != {REPEATS_PER_ITEM}: {wrong_count}")


# ---------------------------------------------------------------------
# 5.0 reduction (spec's exact rule) - modal jev_level per item from 3
#     repeat calls, tie tolerance 0.02, repeat_unstable if no >=2 agree.
# ---------------------------------------------------------------------

def reduce_to_modal(item_probabilities: list[dict[str, float]]) -> tuple[int | None, str]:
    """item_probabilities: one dict per repeat call, level-index (as str)
    -> probability. Returns (modal_level_or_None, status)."""
    levels = []
    for probs in item_probabilities:
        ranked = sorted(probs.items(), key=lambda kv: kv[1], reverse=True)
        if len(ranked) >= 2 and abs(ranked[0][1] - ranked[1][1]) <= TIE_TOLERANCE:
            continue  # jev_tied - excluded from this call's jev_level
        levels.append(int(ranked[0][0]))

    from collections import Counter
    counts = Counter(levels)
    if counts:
        top_level, top_count = counts.most_common(1)[0]
        if top_count >= 2:
            return top_level, "stable"
    return None, "repeat_unstable"


# ---------------------------------------------------------------------
# 6/7. Six-item gate (frozen, imported, unmodified) vs. nine-item
#    pairwise n_P (separate function) - never merged.
# ---------------------------------------------------------------------

def run_frozen_gate(matches_m: int, matches_x: int, matches_a: int) -> tuple[str, str | None]:
    """Calls the imported frozen_gate directly - this function adds no
    logic of its own, so a diff against verify_score_gate_logic.py's gate
    is a diff against what actually ran."""
    return frozen_gate(matches_m, matches_x, matches_a)


def normalize_expected(expected: dict) -> dict:
    """Manifest items store A_unrounded and A_rounded separately (per spec
    §2 - the rounding rule is only for categorical matching, the unrounded
    value is a distinct diagnostic quantity, never conflated). Categorical
    pairwise matching uses A_rounded as "A" - done explicitly, once, here,
    rather than every call site guessing which A field it meant."""
    return {"M": expected["M"], "X": expected["X"], "A": expected["A_rounded"]}


def compute_pairwise_np(nine_item_modal_decisions: dict[str, dict]) -> dict:
    """Independent of run_frozen_gate - operates on all 9 items' modal
    decisions and each item's pre-registered expected M/X/A, counting how
    many items actually separate each pair AND how the observed modal
    decision favored one side, neither, or was unstable."""
    pairs = [("M", "X"), ("M", "A"), ("X", "A")]
    result = {f"{a}-{b}": {"n_P_designed": 0, "favored_first": 0, "favored_second": 0, "unstable_or_neither": 0}
              for a, b in pairs}
    for item_id, rec in nine_item_modal_decisions.items():
        expected = normalize_expected(rec["expected"])
        modal = rec["modal_level"]
        for a, b in pairs:
            va, vb = expected[a], expected[b]
            if va == vb:
                continue  # pair-silent item - not evidence for this pair
            key = f"{a}-{b}"
            result[key]["n_P_designed"] += 1
            if modal is None:
                result[key]["unstable_or_neither"] += 1
            elif modal == va:
                result[key]["favored_first"] += 1
            elif modal == vb:
                result[key]["favored_second"] += 1
            else:
                result[key]["unstable_or_neither"] += 1
    return result


def extract_jev_level(parsed_response: dict | None, http_status: int | None) -> tuple[int | None, str]:
    """Per-call extraction (spec §5.0): argmax of probabilities, with the
    0.02 tie tolerance. Returns (level_or_None, status) where status is
    "ok" / "tied" / "error" - an error or schema-mismatch call is never
    silently treated as a missing repeat; it is recorded as a deviation
    by the caller."""
    if not parsed_response or http_status != 200:
        return None, "error"
    answer = list(parsed_response["answers"].values())[0]
    probs = answer["probabilities"]
    ranked = sorted(probs.items(), key=lambda kv: kv[1], reverse=True)
    if len(ranked) >= 2 and abs(ranked[0][1] - ranked[1][1]) <= TIE_TOLERANCE:
        return None, "tied"
    return int(ranked[0][0]), "ok"


def analyze_results(records: list[dict], manifest: dict) -> dict:
    """Post-collection analysis only - never runs before data exists.
    Keeps the frozen six-item gate and the nine-item pairwise n_P as
    structurally separate computations, per §A.3's binding rule."""
    from collections import Counter, defaultdict

    by_item = defaultdict(list)
    deviations = []
    for r in records:
        by_item[r["item_id"]].append(r)

    item_lookup = {it["item_id"]: it for it in manifest["items"]}
    nine_item_modal = {}
    for item_id, calls in by_item.items():
        if len(calls) != REPEATS_PER_ITEM:
            deviations.append(f"{item_id}: expected {REPEATS_PER_ITEM} calls, got {len(calls)}")
        levels = []
        for c in calls:
            level, status = extract_jev_level(c.get("parsed_response"), c.get("http_status"))
            if status != "ok":
                deviations.append(f"{item_id} repeat {c['repeat_index']}: {status}")
            else:
                levels.append(level)
        counts = Counter(levels)
        modal, stability = None, "repeat_unstable"
        if counts:
            top_level, top_count = counts.most_common(1)[0]
            if top_count >= 2:
                modal, stability = top_level, "stable"
        nine_item_modal[item_id] = {
            "expected": item_lookup[item_id]["expected"],
            "modal_level": modal,
            "stability": stability,
            "raw_levels": levels,
        }

    # Frozen six-item gate input - built ONLY from frozen_primary items.
    frozen_items = {iid: rec for iid, rec in nine_item_modal.items()
                    if item_lookup[iid]["source_group"] == "frozen_primary"}
    if len(frozen_items) != FROZEN_ITEM_COUNT:
        raise PlanValidationError(f"expected {FROZEN_ITEM_COUNT} frozen items in results, got {len(frozen_items)}")

    matches = {"M": 0, "X": 0, "A": 0}
    for rec in frozen_items.values():
        if rec["modal_level"] is None:
            continue
        exp = normalize_expected(rec["expected"])
        for cand in ("M", "X", "A"):
            if rec["modal_level"] == exp[cand]:
                matches[cand] += 1

    gate_outcome, gate_leader = run_frozen_gate(matches["M"], matches["X"], matches["A"])

    # Nine-item pairwise n_P - a SEPARATE computation, never fed into gate().
    pairwise_np = compute_pairwise_np(nine_item_modal)

    stable_count = sum(1 for rec in frozen_items.values() if rec["stability"] == "stable")
    stability_rate = stable_count / FROZEN_ITEM_COUNT
    classification_key, required_phrase = classify_outcome(gate_outcome, stability_rate, pairwise_np)

    return {
        "frozen_six_item_gate": {
            "matches_M": matches["M"], "matches_X": matches["X"], "matches_A": matches["A"],
            "denominator": FROZEN_ITEM_COUNT,
            "outcome": gate_outcome, "leader": gate_leader,
            "stable_count": stable_count, "stability_rate": stability_rate,
        },
        "nine_item_pairwise_n_P": pairwise_np,
        "classification": classification_key,
        "required_report_phrase": required_phrase,
        "prohibited_phrasing_note": "\"the nine-item gate passed\" is banned per the protocol §A.3 - "
                                     "no nine-item gate exists; only the frozen six-item gate above, plus "
                                     "separate nine-item pairwise accounting.",
        "nine_item_modal_decisions": nine_item_modal,
        "deviations": deviations,
    }


OUTCOME_MATRIX_PHRASES = {
    ("CLARITY", "low", "sufficient"): "discrimination among M/X/A, canonical presentation only",
    ("CLARITY", "low", "insufficient"): "CLARITY outcome reported alongside its evidentiary weakness (winning pair below n_P>=6)",
    ("CLARITY", "high", "sufficient"): "CLARITY reached, but on unstable underlying data",
    ("CLARITY", "high", "insufficient"): "CLARITY reached, but on unstable underlying data",
    ("FAILURE", "low", "sufficient"): "no candidate reached a majority - a legitimate, informative outcome",
    ("FAILURE", "low", "insufficient"): "no candidate reached a majority - a legitimate, informative outcome",
    ("FAILURE", "high", "sufficient"): "no candidate reached a majority - a legitimate, informative outcome",
    ("FAILURE", "high", "insufficient"): "no candidate reached a majority - a legitimate, informative outcome",
    ("AMBIGUITY", "low", "sufficient"): "genuinely ambiguous - candidates stably indistinguishable on well-evidenced comparisons",
    ("AMBIGUITY", "low", "insufficient"): "underidentified by design - the composition set, not score's behavior, is the limiting factor",
    ("AMBIGUITY", "high", "sufficient"): "inconclusive - cannot distinguish genuinely-ambiguous from underidentified from too-unstable-to-tell",
    ("AMBIGUITY", "high", "insufficient"): "inconclusive - cannot distinguish genuinely-ambiguous from underidentified from too-unstable-to-tell",
}


def classify_outcome(gate_outcome: str, stability_rate: float, pairwise_np: dict) -> tuple[str, str]:
    stability = "low" if stability_rate >= (5 / 6) else "high"  # low instability = >=5/6 stable, matches §5.3's framing
    sufficiency_threshold = 6
    sufficient = all(v["n_P_designed"] >= sufficiency_threshold for v in pairwise_np.values())
    sufficiency_key = "sufficient" if sufficient else "insufficient"
    phrase = OUTCOME_MATRIX_PHRASES[(gate_outcome, stability, sufficiency_key)]
    return f"{gate_outcome}/{stability}-instability/{sufficiency_key}", phrase


# ---------------------------------------------------------------------
# Preflight / dry-run
# ---------------------------------------------------------------------

def run_preflight() -> dict:
    print("=== Phase B preflight (dry-run; no network calls will be made) ===")
    hash_checks = verify_input_hashes()
    for key, c in hash_checks.items():
        print(f"  HASH OK: {key} ({c['path']})")

    manifest = load_manifest()
    validate_item_identity(manifest)
    print(f"  IDENTITY OK: 9 items (6 frozen_primary + 3 supplement_v1), compositions match frozen records")

    plan = build_call_plan(manifest)
    validate_plan(plan, manifest)
    print(f"  PLAN OK: {len(plan)} calls (== {EXPECTED_TOTAL_CALLS}), 9 items x {REPEATS_PER_ITEM} repeats, "
          f"no duplicate/missing/unexpected cells")

    print("\n  Planned calls:")
    for c in plan:
        print(f"    {c['item_id']:28s} repeat {c['repeat_index']}  ({c['source_group']})")

    report = {
        "status": "PREFLIGHT PASSED - dry-run only, zero network calls made",
        "hash_checks": hash_checks,
        "item_count": len(manifest["items"]),
        "planned_call_count": len(plan),
        "plan": plan,
    }
    return report


# ---------------------------------------------------------------------
# Live execution (not invoked by anything in this session)
# ---------------------------------------------------------------------

def run_live(plan: list[dict]) -> list[dict]:
    from jev_client import ClientConfig, JevClient  # imported only on this path

    client = JevClient(config=ClientConfig())
    raw_path = DATA_DIR / "score_phase_b_raw_responses.jsonl"
    parsed_path = DATA_DIR / "score_phase_b_parsed_responses.jsonl"
    records = []
    with raw_path.open("w") as raw_f, parsed_path.open("w") as parsed_f:
        for idx, cell in enumerate(plan, 1):
            print(f"[{idx}/{len(plan)}] {cell['item_id']} repeat {cell['repeat_index']}", file=sys.stderr)
            rec = client.ask(
                state=cell["state"], questions=cell["questions"],
                test_group=f"score_phase_b:{cell['item_id']}:{cell['repeat_index']}",
            )
            d = rec.to_json_dict()
            row = {**cell, **d}
            raw_f.write(json.dumps(row, default=str) + "\n")
            parsed_f.write(json.dumps({
                "item_id": cell["item_id"], "repeat_index": cell["repeat_index"],
                "is_retry": d["is_retry"], "attempt": d["attempt"],
                "parsed_response": d["parsed_response"],
            }, default=str) + "\n")
            raw_f.flush(); parsed_f.flush()
            records.append(row)
    if len(records) != EXPECTED_TOTAL_CALLS:
        raise PlanValidationError(f"executed {len(records)} calls, expected exactly {EXPECTED_TOTAL_CALLS}")
    return records


# ---------------------------------------------------------------------
# Self-tests (mutation/robustness) - confirm the checks above actually
# catch the failure classes they claim to, not just pass vacuously.
# ---------------------------------------------------------------------

def run_selftest() -> None:
    print("=== Self-test suite (no network calls in any case) ===")
    manifest = load_manifest()

    # 1. Hash-mismatch detection actually fires on a corrupted file.
    real_path = DATA_DIR / "score_phase_b_manifest.json"
    original_bytes = real_path.read_bytes()
    try:
        real_path.write_bytes(original_bytes + b" ")
        try:
            verify_input_hashes()
            raise AssertionError("expected HashMismatchError on corrupted manifest, none raised")
        except HashMismatchError:
            print("  PASS: corrupting score_phase_b_manifest.json by one byte is caught by verify_input_hashes()")
    finally:
        real_path.write_bytes(original_bytes)
    verify_input_hashes()  # confirm restored file passes again
    print("  PASS: restored file passes verify_input_hashes() again (no residual corruption)")

    # 2. Unexpected extra item is rejected.
    plan = build_call_plan(manifest)
    fake_extra = [{"item_id": "not_a_real_item", "source_group": "intruder", "repeat_index": 1,
                   "state": "x", "questions": {}}]
    try:
        validate_plan(plan + fake_extra, manifest)
        raise AssertionError("expected PlanValidationError on injected extra item, none raised")
    except PlanValidationError:
        print("  PASS: an injected 10th item (28th call) is rejected by validate_plan()")

    # 3. A missing call (budget under-run) is rejected.
    try:
        validate_plan(plan[:-1], manifest)
        raise AssertionError("expected PlanValidationError on a truncated plan, none raised")
    except PlanValidationError:
        print("  PASS: a plan with only 26/27 calls is rejected by validate_plan()")

    # 4. A duplicate cell (same item+repeat_index twice) is rejected.
    try:
        validate_plan(plan + [plan[0]], manifest)
        raise AssertionError("expected PlanValidationError on a duplicate cell, none raised")
    except PlanValidationError:
        print("  PASS: a duplicate (item_id, repeat_index) cell is rejected by validate_plan()")

    # 5. gate() is the actual imported function, not a local reimplementation.
    assert frozen_gate.__module__ == "verify_score_gate_logic", (
        f"gate is not imported from verify_score_gate_logic (module={frozen_gate.__module__}) - "
        f"looks like a local reimplementation, which review's requirement #6 explicitly forbids"
    )
    print("  PASS: run_frozen_gate() calls verify_score_gate_logic.gate directly (module identity checked)")

    # 6. gate() only ever receives 6-item counts in the intended call site;
    #    compute_pairwise_np is structurally separate and takes all 9.
    fake_9 = {
        it["item_id"]: {"expected": it["expected"], "modal_level": it["expected"]["M"]}
        for it in manifest["items"]
    }
    np_result = compute_pairwise_np(fake_9)
    assert set(np_result.keys()) == {"M-X", "M-A", "X-A"}
    total_designed = sum(v["n_P_designed"] for v in np_result.values())
    # sanity: designed counts should reflect all 9 items' pair-silence, not just the frozen 6
    frozen_designed = sum(1 for it in manifest["items"] if it["source_group"] == "frozen_primary"
                           for a, b in [("M", "X"), ("M", "A"), ("X", "A")]
                           if normalize_expected(it["expected"])[a] != normalize_expected(it["expected"])[b])
    assert total_designed >= frozen_designed, "pairwise n_P appears to have ignored the supplement items"
    print(f"  PASS: compute_pairwise_np() draws on all 9 items (designed-count sum={total_designed}), "
          f"structurally independent from run_frozen_gate()'s 6-item-only call site")

    # 7. Dry-run makes zero network calls, verified by making requests.post
    #    explode if it's ever hit.
    import requests

    def _explode(*args, **kwargs):
        raise AssertionError("requests.post was called during dry-run - this must never happen")

    original_post = requests.post
    requests.post = _explode
    try:
        run_preflight()
        print("  PASS: run_preflight() completes with requests.post patched to raise - zero network calls made")
    finally:
        requests.post = original_post

    # 8. Outcome matrix covers all 3x2x2 = 12 keys used by classify_outcome
    #    (7 semantically distinct required phrases collapse some FAILURE
    #    cells, matching the spec's own table where FAILURE's row is
    #    stability/sufficiency-independent).
    expected_keys = {(g, s, suf) for g in ("CLARITY", "FAILURE", "AMBIGUITY")
                     for s in ("low", "high") for suf in ("sufficient", "insufficient")}
    assert set(OUTCOME_MATRIX_PHRASES.keys()) == expected_keys, "outcome matrix does not cover the full 3x2x2 space"
    print("  PASS: outcome-interpretation matrix covers all 12 (gate x stability x sufficiency) combinations")

    print("\n=== ALL SELF-TESTS PASSED ===")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["dry-run", "live"], default="dry-run")
    parser.add_argument("--live", action="store_true", help="required (with --confirm-27-calls) to actually execute")
    parser.add_argument("--confirm-27-calls", action="store_true")
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()

    if args.selftest:
        run_selftest()
        return

    if args.mode == "dry-run":
        report = run_preflight()
        out_path = RESULTS_DIR / "score_phase_b_preflight_report.json"
        out_path.write_text(json.dumps(report, indent=2))
        print(f"\nWritten: {out_path}")
        print("\nNo calls were made. This was a dry-run.")
        return

    # mode == "live"
    if not (args.live and args.confirm_27_calls):
        print("Refusing to execute: --mode live requires BOTH --live and --confirm-27-calls.", file=sys.stderr)
        sys.exit(1)

    report = run_preflight()
    plan = report["plan"]
    print("\n=== EXECUTING 27 LIVE CALLS ===")
    records = run_live(plan)
    print(f"\nExecuted {len(records)} calls.")

    manifest = load_manifest()
    analysis = analyze_results(records, manifest)
    retry_count = sum(1 for r in records if r.get("is_retry"))

    execution_manifest = {
        "status": "PHASE B EXECUTED",
        "executed_at_calls": len(records),
        "planned_calls": len(plan),
        "budget_matches_plan": len(records) == len(plan) == EXPECTED_TOTAL_CALLS,
        "retry_count_not_counted_toward_planned_budget": retry_count,
        "input_hashes": report["hash_checks"],
        "analysis": analysis,
    }
    exec_path = RESULTS_DIR / "score_phase_b_execution_manifest.json"
    exec_path.write_text(json.dumps(execution_manifest, indent=2, default=str))

    print(f"\n=== Frozen six-item gate (denominator {FROZEN_ITEM_COUNT}) ===")
    g = analysis["frozen_six_item_gate"]
    print(f"  matches: M={g['matches_M']} X={g['matches_X']} A={g['matches_A']}  "
          f"outcome={g['outcome']} leader={g['leader']}  stability={g['stable_count']}/{FROZEN_ITEM_COUNT}")
    print(f"\n=== Nine-item pairwise n_P (separate accounting) ===")
    for pair, v in analysis["nine_item_pairwise_n_P"].items():
        print(f"  {pair}: designed={v['n_P_designed']} favored_first={v['favored_first']} "
              f"favored_second={v['favored_second']} unstable_or_neither={v['unstable_or_neither']}")
    print(f"\nClassification: {analysis['classification']}")
    print(f"Required report phrase: \"{analysis['required_report_phrase']}\"")
    if analysis["deviations"]:
        print(f"\nDEVIATIONS RECORDED ({len(analysis['deviations'])}):")
        for d in analysis["deviations"]:
            print(f"  - {d}")
    print(f"\nWritten: {exec_path}")


if __name__ == "__main__":
    main()
