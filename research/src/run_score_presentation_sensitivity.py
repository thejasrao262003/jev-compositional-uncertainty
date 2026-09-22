"""Runner for score_presentation_sensitivity_protocol.md (Revision 3).

Implements: hash verification of all upstream inputs, exact 36-call plan
validation, per-cell modal reduction with all-3-response continuous
aggregation (Revision B), stable-cell eligibility (Revision A), the
decision-change/confidence-range/TV-distance estimands (Revision E/minor
clarification), the ordered classification procedure INCLUDING the
Revision 3 item-coverage guard and the UNCLASSIFIABLE / INCONCLUSIVE_BY_
INSTABILITY precedence rules, and a self-test suite specifically
targeting the new logic review required.

--mode dry-run (default): zero network calls.
--mode live: requires --live AND --confirm-36-calls.
--selftest: runs the mutation/robustness suite, no network calls either way.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SRC_DIR))

REPO_ROOT = SRC_DIR.parent.parent
DATA_DIR = REPO_ROOT / "research" / "data" / "characterization"
RESULTS_DIR = REPO_ROOT / "research" / "results"
THIS_FILE = Path(__file__).resolve()

N_ITEMS = 3
PERMUTATION_LABELS = ["P1_canonical", "P2_full_reverse", "P3_severity_first", "P4_severity_last"]
# Revision 4: P4 is a canonical-equivalent replication CONTROL, not a comparison
# arm - it is content-identical to P1 for every item in this track (verified by
# the manifest builder's content-equivalence check). It must never enter the
# primary sensitivity estimands or the classification below.
NONCANONICAL_LABELS = ["P2_full_reverse", "P3_severity_first"]
CONTROL_LABEL = "P4_severity_last"
REPEATS_PER_CELL = 3
EXPECTED_TOTAL_CALLS = N_ITEMS * len(PERMUTATION_LABELS) * REPEATS_PER_CELL  # 36
N_NONCANONICAL_COMPARISONS_PLANNED = N_ITEMS * len(NONCANONICAL_LABELS)  # 6
TIE_TOLERANCE = 0.02

MATERIAL_CONF = 0.15
MATERIAL_DIST = 0.20
NEGLIGIBLE_CONF = 0.10
NEGLIGIBLE_DIST = 0.10
HIGH_INSTABILITY = 1 / 3


class PlanValidationError(Exception):
    pass


class HashMismatchError(Exception):
    pass


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# ---------------------------------------------------------------------
# Hash verification
# ---------------------------------------------------------------------

def verify_input_hashes() -> dict:
    checks = {}

    phase_b_hashes = json.loads((DATA_DIR / "score_phase_b_manifest_hashes.json").read_text())
    for key, rel_path, field in [
        ("phase_b_manifest", phase_b_hashes["manifest_path"], "manifest_sha256"),
        ("phase_b_manifest_builder", phase_b_hashes["builder_script_path"], "builder_script_sha256"),
    ]:
        actual = _sha256_file(REPO_ROOT / rel_path)
        expected = phase_b_hashes[field]
        checks[key] = {"path": rel_path, "expected": expected, "actual": actual, "match": actual == expected}
        if actual != expected:
            raise HashMismatchError(f"{key} ({rel_path}): expected {expected}, got {actual}")

    own_hashes = json.loads((DATA_DIR / "score_presentation_sensitivity_manifest_hashes.json").read_text())
    for key, rel_path, field in [
        ("sensitivity_manifest", own_hashes["manifest_path"], "manifest_sha256"),
        ("sensitivity_manifest_builder", own_hashes["builder_script_path"], "builder_script_sha256"),
    ]:
        actual = _sha256_file(REPO_ROOT / rel_path)
        expected = own_hashes[field]
        checks[key] = {"path": rel_path, "expected": expected, "actual": actual, "match": actual == expected}
        if actual != expected:
            raise HashMismatchError(f"{key} ({rel_path}): expected {expected}, got {actual}")

    return checks


def load_manifest() -> dict:
    return json.loads((DATA_DIR / "score_presentation_sensitivity_manifest.json").read_text())


# ---------------------------------------------------------------------
# Identity + plan validation
# ---------------------------------------------------------------------

def validate_item_identity(manifest: dict) -> None:
    items = manifest["items"]
    if len(items) != N_ITEMS:
        raise PlanValidationError(f"expected {N_ITEMS} items, got {len(items)}")
    for item in items:
        labels = set(item["permutations"].keys())
        if labels != set(PERMUTATION_LABELS):
            raise PlanValidationError(f"{item['item_id']}: permutation labels mismatch: {labels}")
    item_ids = [it["item_id"] for it in items]
    if len(set(item_ids)) != len(item_ids):
        raise PlanValidationError(f"duplicate item_id: {item_ids}")


def build_call_plan(manifest: dict) -> list[dict]:
    plan = []
    for item in manifest["items"]:
        for label in PERMUTATION_LABELS:
            perm = item["permutations"][label]
            for repeat_index in range(1, REPEATS_PER_CELL + 1):
                plan.append({
                    "item_id": item["item_id"],
                    "permutation": label,
                    "repeat_index": repeat_index,
                    "state": perm["state"],
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

    cells = [(c["item_id"], c["permutation"], c["repeat_index"]) for c in plan]
    if len(set(cells)) != len(cells):
        raise PlanValidationError("duplicate (item_id, permutation, repeat_index) cell in plan")

    expected_item_ids = {it["item_id"] for it in manifest["items"]}
    plan_item_ids = {c["item_id"] for c in plan}
    unexpected = plan_item_ids - expected_item_ids
    missing = expected_item_ids - plan_item_ids
    if unexpected:
        raise PlanValidationError(f"plan contains unexpected item_id(s): {unexpected}")
    if missing:
        raise PlanValidationError(f"plan missing item_id(s): {missing}")

    counts = Counter((c["item_id"], c["permutation"]) for c in plan)
    wrong = {k: v for k, v in counts.items() if v != REPEATS_PER_CELL}
    if wrong:
        raise PlanValidationError(f"(item,permutation) cell(s) with repeat count != {REPEATS_PER_CELL}: {wrong}")


# ---------------------------------------------------------------------
# Per-cell reduction (§4): modal decision + all-3-response aggregation
# ---------------------------------------------------------------------

def reduce_cell(calls: list[dict]) -> dict:
    """calls: list of {"http_status", "parsed_response"} for the 3 raw
    repeats of one (item, permutation) cell. Returns modal_level/stable
    plus mean_confidence/mean_probabilities computed over ALL valid raw
    responses (Revision B) - never filtered to modal-matching repeats."""
    valid_responses = []  # (confidence, probabilities) for every http-200, parsed call
    non_tied_levels = []  # jev_level for calls that weren't near-ties
    deviations = []

    for c in calls:
        parsed = c.get("parsed_response")
        if not parsed or c.get("http_status") != 200:
            deviations.append("error")
            continue
        answer = list(parsed["answers"].values())[0]
        probs = answer["probabilities"]
        valid_responses.append((answer["confidence"], probs))
        ranked = sorted(probs.items(), key=lambda kv: kv[1], reverse=True)
        if len(ranked) >= 2 and abs(ranked[0][1] - ranked[1][1]) <= TIE_TOLERANCE:
            deviations.append("tied")
            continue
        non_tied_levels.append(int(ranked[0][0]))

    counts = Counter(non_tied_levels)
    modal_level, stable = None, False
    if counts:
        top_level, top_count = counts.most_common(1)[0]
        if top_count >= 2:
            modal_level, stable = top_level, True

    mean_confidence = None
    mean_probabilities = None
    if valid_responses:
        mean_confidence = sum(r[0] for r in valid_responses) / len(valid_responses)
        all_levels = sorted({lvl for _, probs in valid_responses for lvl in probs})
        mean_probabilities = {
            lvl: sum(probs.get(lvl, 0.0) for _, probs in valid_responses) / len(valid_responses)
            for lvl in all_levels
        }

    return {
        "modal_level": modal_level,
        "stable": stable,
        "mean_confidence": mean_confidence,
        "mean_probabilities": mean_probabilities,
        "raw_levels": non_tied_levels,
        "deviations": deviations,
        "n_valid_responses": len(valid_responses),
    }


# ---------------------------------------------------------------------
# Eligibility (Revision A) + estimands (§6)
# ---------------------------------------------------------------------

def build_item_cells(records: list[dict], manifest: dict) -> dict:
    """records: flat list of executed call records (or, for tests, a
    caller-constructed equivalent). Returns {item_id: {perm_label: cell}}."""
    by_item_perm = defaultdict(list)
    for r in records:
        by_item_perm[(r["item_id"], r["permutation"])].append(r)

    result = {}
    for item in manifest["items"]:
        item_id = item["item_id"]
        result[item_id] = {}
        for label in PERMUTATION_LABELS:
            calls = by_item_perm.get((item_id, label), [])
            result[item_id][label] = reduce_cell(calls)
    return result


def compute_eligibility(item_cells: dict) -> dict:
    """Per item: canonical_stable, and per non-canonical label whether
    that comparison is eligible (both canonical and it are stable)."""
    eligibility = {}
    for item_id, cells in item_cells.items():
        canonical_stable = cells["P1_canonical"]["stable"]
        eligible = {label: (canonical_stable and cells[label]["stable"]) for label in NONCANONICAL_LABELS}
        eligibility[item_id] = {
            "canonical_stable": canonical_stable,
            "eligible_noncanonical": eligible,
            "n_eligible_noncanonical_comparisons": sum(eligible.values()),
        }
    return eligibility


def compute_decision_change(item_cells: dict, eligibility: dict) -> dict:
    numerator, denominator = 0, 0
    exclusions = []
    for item_id, elig in eligibility.items():
        for label in NONCANONICAL_LABELS:
            if elig["eligible_noncanonical"][label]:
                denominator += 1
                canonical_level = item_cells[item_id]["P1_canonical"]["modal_level"]
                perm_level = item_cells[item_id][label]["modal_level"]
                if perm_level != canonical_level:
                    numerator += 1
            else:
                reason = "canonical_unstable" if not elig["canonical_stable"] else "permutation_unstable"
                exclusions.append({"item_id": item_id, "permutation": label, "reason": reason})
    rate = (numerator / denominator) if denominator else None
    return {"numerator": numerator, "denominator": denominator, "rate": rate,
            "n_noncanonical_comparisons_planned": N_NONCANONICAL_COMPARISONS_PLANNED,
            "n_excluded": len(exclusions), "exclusions": exclusions}


def compute_canonical_control_diagnostic(item_cells: dict) -> dict:
    """Section 6.3 (Revision 4): P1-vs-P4 replication diagnostic. P4 is
    content-identical to P1 for every item in this study - this answers
    "how much does score vary across two independent 3-call samples of
    the SAME input" (baseline repeat/session noise), never "is score
    order-sensitive" (no order varied here). Computed and reported
    entirely separately; must never be read by classify()."""
    result = {}
    for item_id, cells in item_cells.items():
        p1, p4 = cells["P1_canonical"], cells[CONTROL_LABEL]
        both_stable = p1["stable"] and p4["stable"]
        modal_agreement = (p1["modal_level"] == p4["modal_level"]) if both_stable else None
        confidence_diff = (
            p4["mean_confidence"] - p1["mean_confidence"]
            if p1["mean_confidence"] is not None and p4["mean_confidence"] is not None else None
        )
        tv_dist = (
            _tv_distance(p1["mean_probabilities"], p4["mean_probabilities"])
            if p1["mean_probabilities"] is not None and p4["mean_probabilities"] is not None else None
        )
        result[item_id] = {
            "both_stable": both_stable,
            "modal_decision_agreement": modal_agreement,
            "confidence_difference_P4_minus_P1": confidence_diff,
            "probability_tv_distance": tv_dist,
            "interpretation": "baseline repeat/session noise diagnostic - NOT evidence about order sensitivity",
        }
    return result


def compute_confidence_range(item_cells: dict, eligibility: dict) -> dict:
    result = {}
    for item_id, elig in eligibility.items():
        if not elig["canonical_stable"]:
            result[item_id] = None  # unavailable, never zero
            continue
        eligible_cells = [item_cells[item_id]["P1_canonical"]]
        for label in NONCANONICAL_LABELS:
            if elig["eligible_noncanonical"][label]:
                eligible_cells.append(item_cells[item_id][label])
        if len(eligible_cells) < 2:
            result[item_id] = None
            continue
        confidences = [c["mean_confidence"] for c in eligible_cells]
        result[item_id] = max(confidences) - min(confidences)
    return result


def _tv_distance(p: dict, q: dict) -> float:
    levels = set(p) | set(q)
    return 0.5 * sum(abs(p.get(l, 0.0) - q.get(l, 0.0)) for l in levels)


def compute_tv_distance(item_cells: dict, eligibility: dict) -> dict:
    result = {}
    for item_id, elig in eligibility.items():
        if not elig["canonical_stable"]:
            result[item_id] = None
            continue
        canonical_probs = item_cells[item_id]["P1_canonical"]["mean_probabilities"]
        distances = []
        for label in NONCANONICAL_LABELS:
            if elig["eligible_noncanonical"][label]:
                distances.append(_tv_distance(canonical_probs, item_cells[item_id][label]["mean_probabilities"]))
        result[item_id] = max(distances) if distances else None
    return result


def compute_instability_rate(item_cells: dict) -> float:
    total = N_ITEMS * len(PERMUTATION_LABELS)
    unstable = sum(1 for cells in item_cells.values() for c in cells.values() if not c["stable"])
    return unstable / total


def secondary_alignment(item_cells: dict, manifest: dict) -> dict:
    """Secondary descriptive analysis only (Revision F) - never used in
    the primary classification below."""
    expected_by_item = {it["item_id"]: it["expected"] for it in manifest["items"]}
    result = {}
    for item_id, cells in item_cells.items():
        exp = expected_by_item[item_id]
        exp_norm = {"M": exp["M"], "X": exp["X"], "A": exp["A_rounded"]}
        result[item_id] = {}
        for label, cell in cells.items():
            modal = cell["modal_level"]
            result[item_id][label] = {
                cand: (modal is not None and modal == val) for cand, val in exp_norm.items()
            }
    return result


# ---------------------------------------------------------------------
# Classification (§7) - UNCLASSIFIABLE / coverage guard / instability precedence
# ---------------------------------------------------------------------

def classify(item_cells: dict, eligibility: dict, decision_change: dict,
             confidence_range: dict, tv_distance: dict, instability_rate: float) -> dict:
    # Step 1: unclassifiable
    if all(not elig["canonical_stable"] for elig in eligibility.values()):
        return {"final_classification": "UNCLASSIFIABLE", "raw_classification": None,
                "item_coverage_complete": False, "n_items_with_eligible_comparisons": 0,
                "n_items_without_eligible_comparisons": N_ITEMS,
                "n_excluded_canonical_equivalent_controls": N_ITEMS}

    n_items_with = sum(1 for elig in eligibility.values() if elig["n_eligible_noncanonical_comparisons"] >= 1)
    n_items_without = N_ITEMS - n_items_with
    item_coverage_complete = (n_items_with == N_ITEMS)

    any_decision_change = decision_change["numerator"] > 0

    conf_values = [v for v in confidence_range.values() if v is not None]
    dist_values = [v for v in tv_distance.values() if v is not None]
    any_material_conf = any(v >= MATERIAL_CONF for v in conf_values)
    any_material_dist = any(v >= MATERIAL_DIST for v in dist_values)

    if any_decision_change or any_material_conf or any_material_dist:
        raw = "MATERIAL"
    elif (item_coverage_complete
          and all(v < NEGLIGIBLE_CONF for v in conf_values)
          and all(v < NEGLIGIBLE_DIST for v in dist_values)
          and len(conf_values) == N_ITEMS and len(dist_values) == N_ITEMS):
        raw = "NEGLIGIBLE"
    else:
        raw = "INCONCLUSIVE"

    high_instability = instability_rate >= HIGH_INSTABILITY
    if raw == "NEGLIGIBLE" and high_instability:
        final = "INCONCLUSIVE_BY_INSTABILITY"
    elif high_instability:
        final = f"{raw} (unstable underlying data)"
    else:
        final = raw

    return {
        "final_classification": final,
        "raw_classification": raw,
        "item_coverage_complete": item_coverage_complete,
        "n_items_with_eligible_comparisons": n_items_with,
        "n_items_without_eligible_comparisons": n_items_without,
        "n_excluded_canonical_equivalent_controls": N_ITEMS,  # fixed - P4 structurally excluded, all 3 items
        "instability_rate": instability_rate,
        "high_instability": high_instability,
    }


# ---------------------------------------------------------------------
# Preflight / dry-run
# ---------------------------------------------------------------------

def run_preflight() -> dict:
    print("=== Presentation-sensitivity preflight (dry-run; no network calls) ===")
    hash_checks = verify_input_hashes()
    for key, c in hash_checks.items():
        print(f"  HASH OK: {key} ({c['path']})")

    manifest = load_manifest()
    validate_item_identity(manifest)
    print(f"  IDENTITY OK: {N_ITEMS} items x {len(PERMUTATION_LABELS)} permutations")

    plan = build_call_plan(manifest)
    validate_plan(plan, manifest)
    print(f"  PLAN OK: {len(plan)} calls (== {EXPECTED_TOTAL_CALLS})")

    return {"status": "PREFLIGHT PASSED", "hash_checks": hash_checks,
            "planned_call_count": len(plan), "plan": plan}


# ---------------------------------------------------------------------
# Live execution
# ---------------------------------------------------------------------

def run_live(plan: list[dict]) -> list[dict]:
    from jev_client import ClientConfig, JevClient

    client = JevClient(config=ClientConfig())
    raw_path = DATA_DIR / "score_presentation_sensitivity_raw_responses.jsonl"
    parsed_path = DATA_DIR / "score_presentation_sensitivity_parsed_responses.jsonl"
    records = []
    with raw_path.open("w") as raw_f, parsed_path.open("w") as parsed_f:
        for idx, cell in enumerate(plan, 1):
            print(f"[{idx}/{len(plan)}] {cell['item_id']} {cell['permutation']} repeat {cell['repeat_index']}", file=sys.stderr)
            rec = client.ask(state=cell["state"], questions=cell["questions"],
                              test_group=f"score_presentation_sensitivity:{cell['item_id']}:{cell['permutation']}:{cell['repeat_index']}")
            d = rec.to_json_dict()
            row = {**cell, **d}
            raw_f.write(json.dumps(row, default=str) + "\n")
            parsed_f.write(json.dumps({
                "item_id": cell["item_id"], "permutation": cell["permutation"], "repeat_index": cell["repeat_index"],
                "is_retry": d["is_retry"], "attempt": d["attempt"], "parsed_response": d["parsed_response"],
            }, default=str) + "\n")
            raw_f.flush(); parsed_f.flush()
            records.append(row)
    if len(records) != EXPECTED_TOTAL_CALLS:
        raise PlanValidationError(f"executed {len(records)} calls, expected {EXPECTED_TOTAL_CALLS}")
    return records


# ---------------------------------------------------------------------
# Self-tests
# ---------------------------------------------------------------------

def _fake_call(http_status=200, level=0, confidence=0.9, other_probs=None):
    probs = {"0": 0.05, "1": 0.05, "2": 0.05}
    probs[str(level)] = confidence
    if other_probs:
        probs.update(other_probs)
    return {"http_status": http_status,
            "parsed_response": {"answers": {"severity": {"confidence": confidence, "probabilities": probs}}}}


def run_selftest() -> None:
    print("=== Self-test suite (no network calls) ===")
    manifest = load_manifest()

    # 1. Hash-tamper detection
    real_path = DATA_DIR / "score_presentation_sensitivity_manifest.json"
    original = real_path.read_bytes()
    try:
        real_path.write_bytes(original + b" ")
        try:
            verify_input_hashes()
            raise AssertionError("expected HashMismatchError, none raised")
        except HashMismatchError:
            print("  PASS: corrupted sensitivity manifest is caught by verify_input_hashes()")
    finally:
        real_path.write_bytes(original)
    verify_input_hashes()
    print("  PASS: restored file passes again")

    # 2. Plan validation: extra item, truncated plan, duplicate cell
    plan = build_call_plan(manifest)
    fake_extra = [{"item_id": "intruder", "permutation": "P1_canonical", "repeat_index": 1, "state": "x", "questions": {}}]
    try:
        validate_plan(plan + fake_extra, manifest)
        raise AssertionError("expected rejection of injected item")
    except PlanValidationError:
        print("  PASS: an injected extra item is rejected")
    try:
        validate_plan(plan[:-1], manifest)
        raise AssertionError("expected rejection of truncated plan")
    except PlanValidationError:
        print(f"  PASS: a plan with only {len(plan)-1}/{len(plan)} calls is rejected")
    try:
        validate_plan(plan + [plan[0]], manifest)
        raise AssertionError("expected rejection of duplicate cell")
    except PlanValidationError:
        print("  PASS: a duplicate cell is rejected")

    # 3. Dry-run network guard
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

    # 4. NEW - unstable canonical cell excludes the item, never zeroes it
    item_cells_unstable_canonical = {
        "item_A": {
            "P1_canonical": reduce_cell([_fake_call(level=0), _fake_call(level=1), _fake_call(level=2)]),  # all differ -> unstable
            "P2_full_reverse": reduce_cell([_fake_call(level=0)] * 3),
            "P3_severity_first": reduce_cell([_fake_call(level=0)] * 3),
            "P4_severity_last": reduce_cell([_fake_call(level=0)] * 3),
        }
    }
    elig = compute_eligibility(item_cells_unstable_canonical)
    assert elig["item_A"]["canonical_stable"] is False
    conf_range = compute_confidence_range(item_cells_unstable_canonical, elig)
    dist = compute_tv_distance(item_cells_unstable_canonical, elig)
    assert conf_range["item_A"] is None, "unstable canonical cell must yield None (unavailable), not 0"
    assert dist["item_A"] is None, "unstable canonical cell must yield None (unavailable), not 0"
    print("  PASS: an unstable canonical cell excludes the item from confidence-range/TV-distance "
          "(reported as unavailable/None, never as 0)")

    # 5. NEW - continuous aggregation uses ALL 3 responses, not modal-matching only
    # 2 calls at level 0 (conf 0.9), 1 outlier call at level 1 (conf 0.5) -> modal=0 (stable),
    # but mean_confidence must reflect all 3, not just the two level-0 calls.
    mixed_cell = reduce_cell([_fake_call(level=0, confidence=0.9), _fake_call(level=0, confidence=0.9),
                              _fake_call(level=1, confidence=0.5)])
    assert mixed_cell["stable"] and mixed_cell["modal_level"] == 0
    expected_mean_conf = (0.9 + 0.9 + 0.5) / 3
    assert abs(mixed_cell["mean_confidence"] - expected_mean_conf) < 1e-9, (
        f"mean_confidence should average ALL 3 responses ({expected_mean_conf}), got {mixed_cell['mean_confidence']}"
    )
    print(f"  PASS: mean_confidence ({mixed_cell['mean_confidence']:.3f}) reflects all 3 raw responses, "
          f"not just the 2 that matched the modal decision")

    # 6. NEW - NEGLIGIBLE-raw + high instability -> INCONCLUSIVE_BY_INSTABILITY
    clean_stable_cell = lambda: reduce_cell([_fake_call(level=0, confidence=0.90)] * 3)
    unstable_cell = lambda: reduce_cell([_fake_call(level=0), _fake_call(level=1), _fake_call(level=2)])
    item_cells_high_instab = {}
    for i in range(3):
        item_id = f"item_{i}"
        item_cells_high_instab[item_id] = {
            "P1_canonical": clean_stable_cell(),
            "P2_full_reverse": clean_stable_cell(),
            "P3_severity_first": unstable_cell() if i < 2 else clean_stable_cell(),
            "P4_severity_last": unstable_cell() if i < 2 else clean_stable_cell(),
        }
    elig2 = compute_eligibility(item_cells_high_instab)
    dc2 = compute_decision_change(item_cells_high_instab, elig2)
    cr2 = compute_confidence_range(item_cells_high_instab, elig2)
    tv2 = compute_tv_distance(item_cells_high_instab, elig2)
    instab2 = compute_instability_rate(item_cells_high_instab)
    result2 = classify(item_cells_high_instab, elig2, dc2, cr2, tv2, instab2)
    assert instab2 >= HIGH_INSTABILITY, f"fixture should have high instability, got {instab2}"
    assert result2["raw_classification"] == "NEGLIGIBLE", f"expected raw NEGLIGIBLE, got {result2['raw_classification']}"
    assert result2["final_classification"] == "INCONCLUSIVE_BY_INSTABILITY", (
        f"expected final INCONCLUSIVE_BY_INSTABILITY, got {result2['final_classification']}"
    )
    print(f"  PASS: a raw-NEGLIGIBLE result under high instability ({instab2:.2f}) is reported as "
          f"INCONCLUSIVE_BY_INSTABILITY, never as NEGLIGIBLE")

    # 7. NEW - partial item coverage (2 of 3 items with zero eligible
    #    non-canonical comparisons) must NOT reach NEGLIGIBLE even though
    #    the 1 available comparison is clean and instability is low.
    item_cells_partial = {
        "item_1": {  # only P1 stable; all non-canonical unstable -> 0 eligible comparisons
            "P1_canonical": clean_stable_cell(),
            "P2_full_reverse": unstable_cell(),
            "P3_severity_first": unstable_cell(),
            "P4_severity_last": unstable_cell(),
        },
        "item_2": {  # same - 0 eligible comparisons
            "P1_canonical": clean_stable_cell(),
            "P2_full_reverse": unstable_cell(),
            "P3_severity_first": unstable_cell(),
            "P4_severity_last": unstable_cell(),
        },
        "item_3": {  # fully clean, 1 eligible comparison, well below thresholds
            "P1_canonical": clean_stable_cell(),
            "P2_full_reverse": clean_stable_cell(),
            "P3_severity_first": unstable_cell(),
            "P4_severity_last": unstable_cell(),
        },
    }
    elig3 = compute_eligibility(item_cells_partial)
    dc3 = compute_decision_change(item_cells_partial, elig3)
    cr3 = compute_confidence_range(item_cells_partial, elig3)
    tv3 = compute_tv_distance(item_cells_partial, elig3)
    instab3 = compute_instability_rate(item_cells_partial)
    result3 = classify(item_cells_partial, elig3, dc3, cr3, tv3, instab3)
    assert result3["item_coverage_complete"] is False, "expected incomplete coverage (2 of 3 items with 0 eligible comparisons)"
    assert result3["n_items_with_eligible_comparisons"] == 1
    assert result3["final_classification"] != "NEGLIGIBLE", (
        f"NEGLIGIBLE must be unreachable with incomplete item coverage, got {result3['final_classification']}"
    )
    assert "INCONCLUSIVE" in result3["final_classification"], (
        f"expected an INCONCLUSIVE variant, got {result3['final_classification']}"
    )
    print(f"  PASS: partial item coverage (only {result3['n_items_with_eligible_comparisons']}/3 items with an "
          f"eligible comparison) yields {result3['final_classification']}, NEGLIGIBLE confirmed unreachable")

    # 8. Positive-path sanity: full coverage, all clean, low instability -> NEGLIGIBLE reachable
    item_cells_clean = {
        f"item_{i}": {label: clean_stable_cell() for label in PERMUTATION_LABELS} for i in range(3)
    }
    elig4 = compute_eligibility(item_cells_clean)
    dc4 = compute_decision_change(item_cells_clean, elig4)
    cr4 = compute_confidence_range(item_cells_clean, elig4)
    tv4 = compute_tv_distance(item_cells_clean, elig4)
    instab4 = compute_instability_rate(item_cells_clean)
    result4 = classify(item_cells_clean, elig4, dc4, cr4, tv4, instab4)
    assert result4["final_classification"] == "NEGLIGIBLE", (
        f"expected NEGLIGIBLE reachable in the fully-clean case, got {result4['final_classification']}"
    )
    print("  PASS: NEGLIGIBLE remains reachable in the fully-clean, full-coverage, low-instability case "
          "(the coverage guard doesn't make it vacuously unreachable)")

    # 9. NEW - UNCLASSIFIABLE precedence: every canonical cell unstable,
    #    even though non-canonical cells look perfectly clean, must not
    #    be reachable as NEGLIGIBLE/MATERIAL/INCONCLUSIVE.
    item_cells_all_canonical_unstable = {
        f"item_{i}": {
            "P1_canonical": unstable_cell(),
            "P2_full_reverse": clean_stable_cell(),
            "P3_severity_first": clean_stable_cell(),
            "P4_severity_last": clean_stable_cell(),
        } for i in range(3)
    }
    elig5 = compute_eligibility(item_cells_all_canonical_unstable)
    dc5 = compute_decision_change(item_cells_all_canonical_unstable, elig5)
    cr5 = compute_confidence_range(item_cells_all_canonical_unstable, elig5)
    tv5 = compute_tv_distance(item_cells_all_canonical_unstable, elig5)
    instab5 = compute_instability_rate(item_cells_all_canonical_unstable)
    result5 = classify(item_cells_all_canonical_unstable, elig5, dc5, cr5, tv5, instab5)
    assert result5["final_classification"] == "UNCLASSIFIABLE", (
        f"expected UNCLASSIFIABLE when every canonical cell is unstable, got {result5['final_classification']}"
    )
    assert all(v is None for v in cr5.values()), "confidence_range must be None everywhere when canonical is unstable"
    assert all(v is None for v in tv5.values()), "tv_distance must be None everywhere when canonical is unstable"
    print("  PASS: every canonical cell unstable -> UNCLASSIFIABLE, even though the non-canonical "
          "cells alone look clean (precedence over NEGLIGIBLE/MATERIAL/INCONCLUSIVE confirmed)")

    # 10. NEW - MATERIAL (via decision change) takes precedence over what
    #     would otherwise be a clean NEGLIGIBLE reading: full coverage,
    #     all confidence/TV values below negligible thresholds, but one
    #     eligible comparison shows a decision flip.
    item_cells_flip = {
        "item_1": {  # decision flip: P1 modal=0, P3 modal=1, both stable -> eligible, differs
            "P1_canonical": reduce_cell([_fake_call(level=0, confidence=0.9)] * 3),
            "P2_full_reverse": reduce_cell([_fake_call(level=0, confidence=0.9)] * 3),
            "P3_severity_first": reduce_cell([_fake_call(level=1, confidence=0.9)] * 3),
            "P4_severity_last": reduce_cell([_fake_call(level=0, confidence=0.9)] * 3),
        },
        "item_2": {label: clean_stable_cell() for label in PERMUTATION_LABELS},
        "item_3": {label: clean_stable_cell() for label in PERMUTATION_LABELS},
    }
    elig6 = compute_eligibility(item_cells_flip)
    dc6 = compute_decision_change(item_cells_flip, elig6)
    cr6 = compute_confidence_range(item_cells_flip, elig6)
    tv6 = compute_tv_distance(item_cells_flip, elig6)
    instab6 = compute_instability_rate(item_cells_flip)
    result6 = classify(item_cells_flip, elig6, dc6, cr6, tv6, instab6)
    assert dc6["numerator"] == 1, f"expected exactly 1 decision change, got {dc6['numerator']}"
    assert all(v < NEGLIGIBLE_CONF for v in cr6.values() if v is not None), "fixture should have low confidence ranges"
    assert result6["final_classification"] == "MATERIAL", (
        f"a decision change must force MATERIAL even when confidence/TV values look negligible, "
        f"got {result6['final_classification']}"
    )
    print("  PASS: a single eligible decision change forces MATERIAL even though every confidence/TV "
          "value is independently below the negligible thresholds (decision-change precedence confirmed)")

    # 11. NEW (Revision 4, review's required test #1) - P4 structurally
    #     excluded from the comparison set.
    assert CONTROL_LABEL not in NONCANONICAL_LABELS, "P4 must never be a member of NONCANONICAL_LABELS"
    assert set(NONCANONICAL_LABELS) == {"P2_full_reverse", "P3_severity_first"}
    print("  PASS: P4_severity_last is structurally excluded from NONCANONICAL_LABELS "
          "(review's required test #1)")

    # 12. NEW (Revision 4, required tests #2/#3/#5/#7) - a single fixture
    # where P4 is given an EXTREME, artificial difference from P1 (wildly
    # different level, confidence, probabilities) while P1/P2/P3 remain
    # clean and matching. If P4 were leaking into any primary estimand,
    # this would show up as a large decision-change/confidence-range/
    # TV-distance value, or as a MATERIAL classification, or as blocking
    # NEGLIGIBLE. None of that may happen.
    # level=2 (opposite of clean_stable_cell()'s level=0) with confidence=0.30 -
    # clearly non-tied (0.30 vs the two 0.05 fillers) and clearly different
    # from clean_stable_cell()'s confidence=0.90, without being a degenerate
    # near-uniform distribution that the tie check would exclude entirely.
    extreme_p4_cell = reduce_cell([_fake_call(level=2, confidence=0.30)] * 3)
    item_cells_extreme_p4 = {
        f"item_{i}": {
            "P1_canonical": clean_stable_cell(),
            "P2_full_reverse": clean_stable_cell(),
            "P3_severity_first": clean_stable_cell(),
            CONTROL_LABEL: extreme_p4_cell,
        } for i in range(3)
    }
    elig7 = compute_eligibility(item_cells_extreme_p4)
    dc7 = compute_decision_change(item_cells_extreme_p4, elig7)
    cr7 = compute_confidence_range(item_cells_extreme_p4, elig7)
    tv7 = compute_tv_distance(item_cells_extreme_p4, elig7)
    instab7 = compute_instability_rate(item_cells_extreme_p4)
    result7 = classify(item_cells_extreme_p4, elig7, dc7, cr7, tv7, instab7)
    assert dc7["numerator"] == 0 and dc7["denominator"] == N_NONCANONICAL_COMPARISONS_PLANNED, (
        f"P4's extreme value must not appear in decision_change at all, got {dc7}"
    )
    for item_id, v in cr7.items():
        assert v is not None and v < NEGLIGIBLE_CONF, (
            f"P4's extreme confidence must not leak into confidence_range for {item_id}, got {v}"
        )
    for item_id, v in tv7.items():
        assert v is not None and v < NEGLIGIBLE_DIST, (
            f"P4's extreme probabilities must not leak into tv_distance for {item_id}, got {v}"
        )
    assert result7["final_classification"] == "NEGLIGIBLE", (
        f"an extreme P4 value must not prevent NEGLIGIBLE when P1/P2/P3 are clean, got {result7['final_classification']}"
    )
    assert result7["item_coverage_complete"] is True, "P4's stability/instability must not affect item_coverage_complete"
    print("  PASS: an artificially extreme P4 cell (opposite level, distinctly different confidence) leaks into NEITHER "
          "decision_change, confidence_range, nor tv_distance, and does not block NEGLIGIBLE "
          "(review's required tests #2/#3/#5/#7)")

    # 13. NEW (required test #4) - P1 and P4 remain separately recorded,
    # never pooled into a single 6-response cell.
    p1_cell = item_cells_extreme_p4["item_0"]["P1_canonical"]
    p4_cell = item_cells_extreme_p4["item_0"][CONTROL_LABEL]
    assert p1_cell is not p4_cell and p1_cell["mean_confidence"] != p4_cell["mean_confidence"], (
        "P1 and P4 must remain distinct, independently-computed cells"
    )
    diag = compute_canonical_control_diagnostic(item_cells_extreme_p4)
    assert diag["item_0"]["modal_decision_agreement"] is False  # P1=level0, P4=level2, both stable
    assert diag["item_0"]["confidence_difference_P4_minus_P1"] < 0  # P4's 0.05 << P1's 0.90
    print("  PASS: P1 and P4 remain two distinct, separately-recorded cells - never pooled - and the "
          "P1/P4 canonical-control diagnostic (§6.3) correctly reports their disagreement as descriptive "
          "context, not as a classification input (review's required test #4)")

    # 14. Required test #8 (manifest-builder-level) is covered by
    # build_score_presentation_sensitivity_manifest.py's own
    # run_content_equivalence_mutation_test(), run as part of that
    # script's main() - not duplicated here.
    print("  NOTE: required test #8 (manifest rejects P2/P3 content-identical to P1) is implemented and "
          "run in build_score_presentation_sensitivity_manifest.py's own mutation test, not here")

    print("\n=== ALL SELF-TESTS PASSED ===")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["dry-run", "live"], default="dry-run")
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--confirm-36-calls", action="store_true")
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()

    if args.selftest:
        run_selftest()
        return

    if args.mode == "dry-run":
        report = run_preflight()
        out_path = RESULTS_DIR / "score_presentation_sensitivity_preflight_report.json"
        out_path.write_text(json.dumps(report, indent=2))
        print(f"\nWritten: {out_path}")
        print("\nNo calls were made. This was a dry-run.")
        return

    if not (args.live and args.confirm_36_calls):
        print("Refusing to execute: --mode live requires BOTH --live and --confirm-36-calls.", file=sys.stderr)
        sys.exit(1)

    report = run_preflight()
    plan = report["plan"]
    print("\n=== EXECUTING 36 LIVE CALLS ===")
    records = run_live(plan)
    manifest = load_manifest()
    item_cells = build_item_cells(records, manifest)
    eligibility = compute_eligibility(item_cells)
    decision_change = compute_decision_change(item_cells, eligibility)
    confidence_range = compute_confidence_range(item_cells, eligibility)
    tv_distance = compute_tv_distance(item_cells, eligibility)
    instability_rate = compute_instability_rate(item_cells)
    classification = classify(item_cells, eligibility, decision_change, confidence_range, tv_distance, instability_rate)
    alignment = secondary_alignment(item_cells, manifest)
    canonical_control_diagnostic = compute_canonical_control_diagnostic(item_cells)

    execution_manifest = {
        "status": "PRESENTATION-SENSITIVITY STUDY EXECUTED",
        "study_description": "A two-variant presentation-sensitivity study (P2_full_reverse, "
                              "P3_severity_first) with a canonical-equivalent replication control "
                              "(P4_severity_last), evaluated across three selected items.",
        "planned_calls": len(plan),
        "actual_calls": len(records),
        "input_hashes": report["hash_checks"],
        "item_cells": item_cells,
        "eligibility": eligibility,
        "decision_change": decision_change,
        "confidence_range": confidence_range,
        "tv_distance": tv_distance,
        "instability_rate": instability_rate,
        "classification": classification,
        "secondary_alignment_descriptive_only": alignment,
        "canonical_control_diagnostic_P1_vs_P4_descriptive_only": canonical_control_diagnostic,
    }
    out_path = RESULTS_DIR / "score_presentation_sensitivity_execution_manifest.json"
    out_path.write_text(json.dumps(execution_manifest, indent=2, default=str))
    print(f"\nFinal classification: {classification['final_classification']}")
    print(f"Written: {out_path}")


if __name__ == "__main__":
    main()
