"""Pre-flight static validator for Step 0B item manifests.

Implements the 11-point checklist in
research/methodology/step0b_design_specification.md §15. Checks 1-8
validate a machine-readable item manifest (JSON); checks 9-11 validate an
analysis/runner script by static inspection (grep-level, not execution) -
they report "not applicable" if no script path is given or the file
doesn't exist yet, rather than failing, since that code hasn't been
written yet (see §15's closing note).

This script is runnable today. It has not yet been run against a real
Step 0B manifest, because that manifest has not been generated - only the
self-test fixture below exists so far. Generating the real Stage 0/Stage 1
manifests is a separate, downstream deliverable.

Usage:
    python3 validate_step0b_manifest.py <manifest.json> [--analysis-script PATH] [--prior-hash-file PATH]
    python3 validate_step0b_manifest.py --self-test
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


class CheckResult:
    def __init__(self, check_id: str, name: str, status: str, detail: str):
        self.check_id = check_id
        self.name = name
        self.status = status  # "pass" | "fail" | "not_applicable"
        self.detail = detail

    def to_dict(self) -> dict[str, Any]:
        return {"check_id": self.check_id, "name": self.name, "status": self.status, "detail": self.detail}


def _all_sentences(manifest: dict) -> list[dict]:
    out = []
    for item in manifest.get("items", []):
        out.extend(item.get("sentences", []))
    return out


def check_unique_opaque_ids(manifest: dict) -> CheckResult:
    ids = [s["opaque_id"] for s in _all_sentences(manifest)]
    dupes = {i for i in ids if ids.count(i) > 1}
    if dupes:
        return CheckResult("1", "unique opaque IDs", "fail", f"duplicate opaque IDs: {sorted(dupes)}")
    return CheckResult("1", "unique opaque IDs", "pass", f"{len(ids)} sentences, all opaque IDs unique")


def check_opaque_ids_content_blind(manifest: dict) -> CheckResult:
    meta = manifest.get("metadata", {})
    if "opaque_id_permutation_seed" not in meta:
        return CheckResult("2", "opaque IDs content-blind", "fail", "no opaque_id_permutation_seed recorded in metadata")
    offenders = []
    for s in _all_sentences(manifest):
        label = str(s.get("semantic_label", "")).lower()
        oid = str(s.get("opaque_id", "")).lower()
        # crude but effective: opaque IDs must not contain any token from the label
        label_tokens = [t for t in label.replace("_", " ").split() if len(t) >= 3]
        if any(tok in oid for tok in label_tokens):
            offenders.append((s.get("opaque_id"), s.get("semantic_label")))
    if offenders:
        return CheckResult("2", "opaque IDs content-blind", "fail", f"opaque ID appears to encode semantic label: {offenders}")
    return CheckResult("2", "opaque IDs content-blind", "pass", "permutation seed recorded; no opaque ID contains a token from its semantic label")


def check_canonical_order_derivable(manifest: dict) -> CheckResult:
    bad_items = []
    for item in manifest.get("items", []):
        opaque_ids = [s["opaque_id"] for s in item.get("sentences", [])]
        expected = sorted(opaque_ids)
        stored = item.get("canonical_order")
        if stored != expected:
            bad_items.append(item.get("item_id"))
    if bad_items:
        return CheckResult("3", "canonical order derivable from opaque IDs", "fail", f"mismatch on items: {bad_items}")
    return CheckResult("3", "canonical order derivable from opaque IDs", "pass",
                        f"canonical_order == sorted(opaque_ids) for all {len(manifest.get('items', []))} items")


def check_reference_labels_match_condition(manifest: dict) -> CheckResult:
    bad = []
    for item in manifest.get("items", []):
        contested = item.get("is_contested")
        ref = item.get("reference_label")
        if contested is True and ref is not None:
            bad.append((item.get("item_id"), "contested item has a non-null reference_label"))
        if contested is False and ref is None:
            bad.append((item.get("item_id"), "non-contested item has a null reference_label"))
        if contested not in (True, False):
            bad.append((item.get("item_id"), "is_contested not explicitly boolean"))
    if bad:
        return CheckResult("4", "reference labels match condition", "fail", str(bad))
    return CheckResult("4", "reference labels match condition", "pass",
                        f"all {len(manifest.get('items', []))} items: reference_label presence matches is_contested")


def check_manifest_immutability(manifest: dict, manifest_path: Path, prior_hash_path: Path | None) -> CheckResult:
    content_hash = hashlib.sha256(json.dumps(manifest, sort_keys=True).encode("utf-8")).hexdigest()
    stage = manifest.get("stage", "unknown")
    if prior_hash_path is None:
        return CheckResult("5", "manifest immutability", "not_applicable",
                            f"no prior-hash file given; this run's hash for stage={stage} is {content_hash[:16]}... "
                            "(pass --prior-hash-file next time to detect changes)")
    if not prior_hash_path.exists():
        prior_hash_path.write_text(json.dumps({stage: content_hash}, indent=2))
        return CheckResult("5", "manifest immutability", "pass",
                            f"no prior hash on record for stage={stage}; recorded {content_hash[:16]}... as baseline")
    recorded = json.loads(prior_hash_path.read_text())
    if stage in recorded and recorded[stage] != content_hash:
        return CheckResult("5", "manifest immutability", "fail",
                            f"stage={stage} manifest hash changed since baseline "
                            f"({recorded[stage][:16]}... -> {content_hash[:16]}...)")
    recorded[stage] = content_hash
    prior_hash_path.write_text(json.dumps(recorded, indent=2))
    return CheckResult("5", "manifest immutability", "pass", f"stage={stage} manifest hash unchanged ({content_hash[:16]}...)")


def check_seeds_recorded(manifest: dict) -> CheckResult:
    # Tooling note (fixed before any real manifest was validated, not in
    # response to one): subset_selection_seed only applies to manifests
    # that actually have a Layer-2/3 robustness/repeat subset (Stage 1).
    # Stage 0 has no such subset (§2), so requiring that key unconditionally
    # was an overly strict carryover from the Stage-1-shaped schema this
    # check was originally written against.
    meta = manifest.get("metadata", {})
    required = ["opaque_id_permutation_seed"]
    has_subset_concept = ("robustness_repeat_subset_ids" in manifest) or ("overflow_replacement_list" in manifest)
    if has_subset_concept:
        required.append("subset_selection_seed")
    missing = [k for k in required if k not in meta]
    if missing:
        return CheckResult("6", "seeds recorded", "fail", f"missing metadata keys: {missing}")
    return CheckResult("6", "seeds recorded", "pass", f"metadata contains: {required}")


def check_subset_membership_fixed(manifest: dict) -> CheckResult:
    subset = manifest.get("robustness_repeat_subset_ids")
    if subset is None:
        return CheckResult("7", "robustness/repeat subset fixed", "not_applicable",
                            "manifest has no robustness_repeat_subset_ids field (e.g. a Stage 0 manifest)")
    all_ids = {item["item_id"] for item in manifest.get("items", [])}
    unknown = [sid for sid in subset if sid not in all_ids]
    if unknown:
        return CheckResult("7", "robustness/repeat subset fixed", "fail", f"subset references unknown item IDs: {unknown}")
    if len(subset) != len(set(subset)):
        return CheckResult("7", "robustness/repeat subset fixed", "fail", "subset list contains duplicate item IDs")
    return CheckResult("7", "robustness/repeat subset fixed", "pass",
                        f"{len(subset)} item IDs, all present in manifest, no duplicates "
                        "(full re-derivation-from-seed check requires the subset-selection code, not just the manifest)")


def check_reserve_rules_structural(manifest: dict) -> CheckResult:
    overflow = manifest.get("overflow_replacement_list")
    if overflow is None:
        return CheckResult("8", "reserve rules structural", "not_applicable", "manifest has no overflow_replacement_list field")
    items_by_id = {item["item_id"]: item for item in manifest.get("items", [])}
    bad = []
    for original_id, replacement_id in overflow.items():
        orig = items_by_id.get(original_id)
        repl = items_by_id.get(replacement_id)
        if orig is None or repl is None:
            bad.append((original_id, replacement_id, "unknown item ID"))
            continue
        if orig.get("primitive") != repl.get("primitive") or orig.get("condition") != repl.get("condition"):
            bad.append((original_id, replacement_id, "replacement is not same primitive/condition as original"))
    if bad:
        return CheckResult("8", "reserve rules structural", "fail", str(bad))
    return CheckResult("8", "reserve rules structural", "pass",
                        f"{len(overflow)} preregistered replacements, each matching its original's primitive/condition")


def _read_scripts(paths: list[Path] | None) -> dict[str, str]:
    if not paths:
        return {}
    return {str(p): p.read_text() for p in paths if p.exists()}


def check_client_usage(analysis_script_paths: list[Path] | None) -> CheckResult:
    texts = _read_scripts(analysis_script_paths)
    if not texts:
        return CheckResult("9", "uses JevClient (not raw requests)", "not_applicable",
                            "no analysis/runner script path given, or none of the given files exist yet")
    hits = [f for f, t in texts.items() if "JevClient" in t]
    if hits:
        return CheckResult("9", "uses JevClient (not raw requests)", "pass", f"JevClient referenced in: {hits}")
    return CheckResult("9", "uses JevClient (not raw requests)", "fail",
                        f"JevClient not referenced in any of: {list(texts.keys())}")


def check_noul_gating(analysis_script_paths: list[Path] | None) -> CheckResult:
    texts = _read_scripts(analysis_script_paths)
    if not texts:
        return CheckResult("10", "noul metrics gated on h2a_passed", "not_applicable",
                            "no analysis script path given, or none of the given files exist yet")
    hits = [f for f, t in texts.items() if "h2a" in t.lower() and ("gate" in t.lower() or "pass" in t.lower())]
    if hits:
        return CheckResult("10", "noul metrics gated on h2a_passed", "pass", f"H2a gate logic referenced in: {hits}")
    return CheckResult("10", "noul metrics gated on h2a_passed", "fail",
                        f"no H2a gate reference found in any of: {list(texts.keys())}")


def check_complete_cell_filtering(analysis_script_paths: list[Path] | None) -> CheckResult:
    texts = _read_scripts(analysis_script_paths)
    if not texts:
        return CheckResult("11", "complete-cell filtering before aggregation", "not_applicable",
                            "no analysis script path given, or none of the given files exist yet")
    hits = [f for f, t in texts.items()
            if ("m==3" in t.replace(" ", "") or "m == 3" in t or "k==3" in t.replace(" ", "") or "k == 3" in t
                or "!= 3" in t or "!=3" in t.replace(" ", ""))]
    if hits:
        return CheckResult("11", "complete-cell filtering before aggregation", "pass",
                            f"explicit m==3 / k==3 completeness check found in: {hits}")
    return CheckResult("11", "complete-cell filtering before aggregation", "fail",
                        f"no explicit m==3 / k==3 completeness check found in any of: {list(texts.keys())} "
                        "(heuristic text search - verify manually too)")


def validate(manifest_path: Path, analysis_script_paths: list[Path] | None = None, prior_hash_path: Path | None = None) -> list[CheckResult]:
    manifest = json.loads(manifest_path.read_text())
    return [
        check_unique_opaque_ids(manifest),
        check_opaque_ids_content_blind(manifest),
        check_canonical_order_derivable(manifest),
        check_reference_labels_match_condition(manifest),
        check_manifest_immutability(manifest, manifest_path, prior_hash_path),
        check_seeds_recorded(manifest),
        check_subset_membership_fixed(manifest),
        check_reserve_rules_structural(manifest),
        check_client_usage(analysis_script_paths),
        check_noul_gating(analysis_script_paths),
        check_complete_cell_filtering(analysis_script_paths),
    ]


def print_report(results: list[CheckResult]) -> bool:
    ok = True
    for r in results:
        marker = {"pass": "PASS", "fail": "FAIL", "not_applicable": "N/A "}[r.status]
        print(f"[{marker}] #{r.check_id} {r.name}: {r.detail}")
        if r.status == "fail":
            ok = False
    print(f"\nOverall: {'PASS (no failures; N/A items need a manifest/script to check)' if ok else 'FAIL'}")
    return ok


# --- Self-test fixture: a tiny, deliberately-correct dummy manifest -------

def _self_test_manifest() -> dict:
    return {
        "stage": "stage0_selftest",
        "metadata": {"opaque_id_permutation_seed": 12345, "subset_selection_seed": 67890},
        "items": [
            {
                "item_id": "dummy_001",
                "primitive": "choice",
                "domain": "A",
                "condition": "near_majority",
                "sentences": [
                    {"opaque_id": "s07", "semantic_label": "supports_optA", "text": "Example sentence one."},
                    {"opaque_id": "s02", "semantic_label": "supports_optA", "text": "Example sentence two."},
                    {"opaque_id": "s11", "semantic_label": "supports_optA", "text": "Example sentence three."},
                    {"opaque_id": "s04", "semantic_label": "supports_optB", "text": "Example sentence four."},
                    {"opaque_id": "s09", "semantic_label": "supports_optB", "text": "Example sentence five."},
                ],
                "canonical_order": ["s02", "s04", "s07", "s09", "s11"],
                "reference_label": "optA",
                "is_contested": False,
            },
            {
                "item_id": "dummy_002",
                "primitive": "choice",
                "domain": "A",
                "condition": "contested",
                "sentences": [
                    {"opaque_id": "s05", "semantic_label": "supports_optA", "text": "Example sentence six."},
                    {"opaque_id": "s08", "semantic_label": "supports_optB", "text": "Example sentence seven."},
                ],
                "canonical_order": ["s05", "s08"],
                "reference_label": None,
                "is_contested": True,
            },
            {
                "item_id": "dummy_003_overflow",
                "primitive": "choice",
                "domain": "A",
                "condition": "near_majority",
                "sentences": [
                    {"opaque_id": "s13", "semantic_label": "supports_optA", "text": "Overflow sentence."},
                ],
                "canonical_order": ["s13"],
                "reference_label": "optA",
                "is_contested": False,
            },
        ],
        "robustness_repeat_subset_ids": ["dummy_001"],
        "overflow_replacement_list": {"dummy_001": "dummy_003_overflow"},
    }


def run_self_test() -> None:
    import tempfile

    manifest = _self_test_manifest()
    with tempfile.TemporaryDirectory() as td:
        mpath = Path(td) / "dummy_manifest.json"
        mpath.write_text(json.dumps(manifest, indent=2))
        print("=== Self-test: dummy manifest, no analysis script (checks 9-11 should be N/A) ===")
        results = validate(mpath, analysis_script_paths=None, prior_hash_path=None)
        ok = print_report(results)
        assert ok, "self-test manifest should pass all manifest-level checks"
        assert all(r.status in ("pass",) for r in results if r.check_id in {"1", "2", "3", "4", "6", "7", "8"}), \
            "checks 1,2,3,4,6,7,8 must all PASS on the self-test fixture"
        assert all(r.status == "not_applicable" for r in results if r.check_id in {"9", "10", "11"}), \
            "checks 9,10,11 must be N/A with no analysis script given"
        print("\nSelf-test assertions passed.")

        print("\n=== Self-test: deliberately broken manifest (duplicate opaque ID) should FAIL check 1 ===")
        broken = json.loads(json.dumps(manifest))
        broken["items"][0]["sentences"][1]["opaque_id"] = broken["items"][0]["sentences"][0]["opaque_id"]
        bpath = Path(td) / "broken_manifest.json"
        bpath.write_text(json.dumps(broken, indent=2))
        results2 = validate(bpath, analysis_script_paths=None, prior_hash_path=None)
        ok2 = print_report(results2)
        assert not ok2, "broken manifest with duplicate opaque IDs must FAIL overall"
        assert results2[0].status == "fail" and results2[0].check_id == "1"
        print("\nSelf-test assertions passed (broken-manifest case correctly fails).")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", nargs="?", help="Path to a Step 0B item manifest JSON file")
    parser.add_argument("--analysis-script", type=Path, action="append", default=None,
                         help="Path to an analysis/runner script (checks 9-11); repeatable")
    parser.add_argument("--prior-hash-file", type=Path, default=None, help="Path to a hash-tracking file (check 5)")
    parser.add_argument("--self-test", action="store_true", help="Run the built-in self-test instead of validating a real manifest")
    args = parser.parse_args()

    if args.self_test:
        run_self_test()
        sys.exit(0)

    if not args.manifest:
        parser.error("manifest path required unless --self-test is given")

    results = validate(Path(args.manifest), args.analysis_script, args.prior_hash_file)
    ok = print_report(results)
    sys.exit(0 if ok else 1)
