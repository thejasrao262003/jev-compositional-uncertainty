"""Builds the manifest for score_presentation_sensitivity_protocol.md
(Revision 3): 3 items x 4 permutations, reusing Phase B's frozen sentence
content VERBATIM.

score_phase_b_manifest.json is never modified here - Phase B already
executed and its record is committed to git (18e000b). This script
regenerates the same 9 items via the exact same deterministic process
(build_score_phase_b_manifest.py's seeded assignment - imported, not
copied) to recover each sentence's own text (the frozen manifest only
stores the already-joined `state` string, not per-sentence text, which
this study needs to construct reordered presentations). It then asserts,
byte-for-byte, that the regenerated content for the 3 selected items
matches the already-frozen, already-hash-verified manifest - proving
verbatim reuse rather than merely claiming it.

No API calls. No new sentences authored.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SRC_DIR))

import build_score_phase_b_manifest as bpb  # noqa: E402 - read-only import, never modifies that file

REPO_ROOT = SRC_DIR.parent.parent
DATA_DIR = REPO_ROOT / "research" / "data" / "characterization"
THIS_FILE = Path(__file__).resolve()

# Selected per score_presentation_sensitivity_protocol.md §2 - fixed by
# composition-level discrimination class alone (2 THREE_WAY + 1 TWO_WAY,
# ascending sort), not by anything Phase B observed.
SELECTED_ITEM_IDS = [
    "frozen_primary_0_0_0_2",
    "frozen_primary_0_0_1_2",
    "frozen_primary_0_0_0_1",
]

PERMUTATION_LABELS = ["P1_canonical", "P2_full_reverse", "P3_severity_first", "P4_severity_last"]
NONCANONICAL_LABELS = ["P2_full_reverse", "P3_severity_first"]  # P4 is a control, not a comparison arm (Revision 4)

PERMUTATION_ROLES = {
    "P1_canonical": "canonical_reference",
    "P2_full_reverse": "noncanonical_comparison",
    "P3_severity_first": "noncanonical_comparison",
    "P4_severity_last": "canonical_repeat_control",
}


class ContentEquivalenceError(Exception):
    """Raised when a permutation claimed to be non-canonical turns out to
    be content-identical to P1_canonical - the exact failure mode
    Revision 4 exists to catch mechanically rather than trust by
    construction."""


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_phase_b_manifest_unmodified() -> None:
    """Phase B's manifest and its hash-lock must still agree - if not,
    something touched a frozen, already-executed artifact and this
    script must refuse to build on top of it."""
    hash_record = json.loads((DATA_DIR / "score_phase_b_manifest_hashes.json").read_text())
    actual = _sha256_file(DATA_DIR / "score_phase_b_manifest.json")
    expected = hash_record["manifest_sha256"]
    assert actual == expected, (
        f"score_phase_b_manifest.json has changed since Phase B executed "
        f"(expected {expected}, got {actual}) - refusing to build on an "
        f"unverified frozen artifact"
    )
    actual_builder = _sha256_file(SRC_DIR / "build_score_phase_b_manifest.py")
    expected_builder = hash_record["builder_script_sha256"]
    assert actual_builder == expected_builder, (
        "build_score_phase_b_manifest.py has changed since Phase B executed - "
        "refusing to regenerate from a modified builder"
    )
    print("  PASS: score_phase_b_manifest.json and its builder script are byte-identical "
          "to their recorded, already-executed hashes")


def regenerate_items_with_text() -> list[dict]:
    """Mirrors build_score_phase_b_manifest.build_items() exactly (same
    seed, same consumption order across all 9 items), but additionally
    captures each sentence's own text - needed to construct presentation-
    order permutations, which the frozen manifest's joined `state` string
    alone cannot provide."""
    pools = bpb.assign_sentences()
    next_id = 1
    items = []

    def consume(level: int) -> tuple[str, str]:
        nonlocal next_id
        opaque_id = f"b{next_id:03d}"
        next_id += 1
        text = pools[level].pop()
        return opaque_id, text

    for source_group, order, expected_table in [
        ("frozen_primary", bpb.FROZEN_PRIMARY_ORDER, bpb.EXPECTED_FROZEN),
        ("supplement_v1", bpb.SUPPLEMENT_V1_ORDER, bpb.EXPECTED_SUPPLEMENT),
    ]:
        for composition in order:
            sentence_records = [consume(level) for level in composition]
            sentence_records_sorted = sorted(sentence_records, key=lambda r: r[0])
            sentence_ids = [r[0] for r in sentence_records_sorted]
            sentence_texts = [r[1] for r in sentence_records_sorted]
            levels = list(composition)
            item_id = f"{source_group}_{'_'.join(str(l) for l in composition)}"
            items.append({
                "item_id": item_id,
                "composition_multiset": levels,
                "sentence_ids_canonical_order": sentence_ids,
                "sentence_texts_canonical_order": sentence_texts,
                "state_canonical": " ".join(sentence_texts),
                "expected": expected_table[composition],
            })
    return items


def verify_verbatim_reuse(regenerated_items: list[dict]) -> dict:
    """Proves, not just claims, that the 3 selected items' regenerated
    content is byte-identical to the already-frozen Phase B manifest."""
    frozen_manifest = json.loads((DATA_DIR / "score_phase_b_manifest.json").read_text())
    frozen_by_id = {it["item_id"]: it for it in frozen_manifest["items"]}
    checks = {}
    for item in regenerated_items:
        if item["item_id"] not in SELECTED_ITEM_IDS:
            continue
        frozen = frozen_by_id[item["item_id"]]
        ids_match = item["sentence_ids_canonical_order"] == frozen["sentence_ids_canonical_order"]
        state_match = item["state_canonical"] == frozen["state"]
        comp_match = item["composition_multiset"] == frozen["composition_multiset"]
        checks[item["item_id"]] = {"ids_match": ids_match, "state_match": state_match, "composition_match": comp_match}
        assert ids_match, f"{item['item_id']}: regenerated sentence IDs diverge from the frozen Phase B manifest"
        assert state_match, f"{item['item_id']}: regenerated canonical state diverges from the frozen Phase B manifest"
        assert comp_match, f"{item['item_id']}: regenerated composition diverges from the frozen Phase B manifest"
    print(f"  PASS: all {len(checks)} selected items' regenerated content (sentence IDs, canonical state, "
          f"composition) is byte-identical to the frozen, already-executed Phase B manifest")
    return checks


def run_verbatim_reuse_mutation_test(regenerated_items: list[dict]) -> None:
    """Confirms verify_verbatim_reuse actually catches a divergence,
    rather than passing vacuously - deliberately corrupts one sentence's
    text in a copy and confirms the assertion fires."""
    import copy
    corrupted = copy.deepcopy(regenerated_items)
    for item in corrupted:
        if item["item_id"] == SELECTED_ITEM_IDS[0]:
            item["state_canonical"] = item["state_canonical"] + " CORRUPTED"
    try:
        verify_verbatim_reuse(corrupted)
        raise AssertionError("expected verify_verbatim_reuse to catch the corrupted state_canonical, it did not")
    except AssertionError as e:
        if "CORRUPTED" in str(e) or "diverges" in str(e):
            print("  PASS: a corrupted canonical state is caught by verify_verbatim_reuse() (mutation test)")
        else:
            raise


def build_permutations(sentence_ids: list[str], sentence_texts: list[str], levels: list[int]) -> dict:
    """P1-P4 exactly per score_presentation_sensitivity_protocol.md §3.
    P3/P4 are independent stable sorts, NOT reverses of each other."""
    canonical = list(zip(sentence_ids, sentence_texts, levels))

    def to_record(pairs):
        ids = [p[0] for p in pairs]
        texts = [p[1] for p in pairs]
        return {"sentence_ids_order": ids, "sentence_texts_order": texts, "state": " ".join(texts)}

    p1 = canonical
    p2 = canonical[::-1]
    p3 = sorted(canonical, key=lambda p: -p[2])  # stable, descending severity
    p4 = sorted(canonical, key=lambda p: p[2])   # stable, ascending severity

    records = {
        "P1_canonical": to_record(p1),
        "P2_full_reverse": to_record(p2),
        "P3_severity_first": to_record(p3),
        "P4_severity_last": to_record(p4),
    }
    p1_ids = records["P1_canonical"]["sentence_ids_order"]
    for label, rec in records.items():
        rec["role"] = PERMUTATION_ROLES[label]
        rec["permutation_distinct_from_P1"] = (rec["sentence_ids_order"] != p1_ids) if label != "P1_canonical" else None
        rec["eligible_for_sensitivity_comparison"] = (label in NONCANONICAL_LABELS)
    return records


def verify_content_equivalence(manifest_items: list[dict]) -> None:
    """Binding safeguard (§4, Revision 4): P2/P3 MUST be distinct from P1;
    P4's coincidence with P1 is EXPECTED and recorded, not an error. This
    is checked mechanically here, not assumed from the role label alone -
    exactly the class of bug this revision exists to catch."""
    for item in manifest_items:
        perms = item["permutations"]
        for label in NONCANONICAL_LABELS:
            if not perms[label]["permutation_distinct_from_P1"]:
                raise ContentEquivalenceError(
                    f"{item['item_id']}: {label} is claimed to be a non-canonical comparison arm "
                    f"but is content-identical to P1_canonical (ids: {perms[label]['sentence_ids_order']}) - "
                    f"refusing to build a manifest with a vacuous 'non-canonical' permutation"
                )
        if perms["P4_severity_last"]["permutation_distinct_from_P1"]:
            print(f"  NOTE: {item['item_id']}: P4_severity_last happens to be DISTINCT from P1 here - "
                  f"the control-role assignment is still correct (P4 is not eligible for sensitivity "
                  f"comparison by definition), but this item does not exhibit the P1==P4 degeneracy "
                  f"the other items do; worth independent confirmation if this changes results interpretation")
        else:
            pass  # expected case for every item in this track, per Revision 4's changelog
    print(f"  PASS: for all {len(manifest_items)} items, P2/P3 are confirmed content-distinct from P1 "
          f"(would have raised ContentEquivalenceError otherwise)")


def run_content_equivalence_mutation_test(manifest_items: list[dict]) -> None:
    """Confirms verify_content_equivalence actually catches a P2==P1
    degeneracy, rather than passing vacuously."""
    import copy
    corrupted = copy.deepcopy(manifest_items)
    corrupted[0]["permutations"]["P2_full_reverse"]["sentence_ids_order"] = \
        list(corrupted[0]["permutations"]["P1_canonical"]["sentence_ids_order"])
    corrupted[0]["permutations"]["P2_full_reverse"]["permutation_distinct_from_P1"] = False
    try:
        verify_content_equivalence(corrupted)
        raise AssertionError("expected ContentEquivalenceError when P2 is forced equal to P1, none raised")
    except ContentEquivalenceError:
        print("  PASS: a P2 forced content-identical to P1 is caught by verify_content_equivalence() (mutation test)")


def main() -> None:
    print("=== Verifying Phase B's frozen manifest is unmodified ===")
    verify_phase_b_manifest_unmodified()

    print("\n=== Regenerating all 9 items via the exact same deterministic process ===")
    regenerated = regenerate_items_with_text()
    assert len(regenerated) == 9

    print("\n=== Verbatim-reuse cross-check (proof, not assertion-in-prose) ===")
    verify_verbatim_reuse(regenerated)
    run_verbatim_reuse_mutation_test(regenerated)

    print(f"\n=== Building permutations for {len(SELECTED_ITEM_IDS)} selected items ===")
    by_id = {it["item_id"]: it for it in regenerated}
    manifest_items = []
    for item_id in SELECTED_ITEM_IDS:
        src = by_id[item_id]
        perms = build_permutations(
            src["sentence_ids_canonical_order"], src["sentence_texts_canonical_order"], src["composition_multiset"],
        )
        # Structural check (per §3's worked example): P3 must not equal reverse(P2) in
        # general - only assert they're allowed to differ, not that they must.
        manifest_items.append({
            "item_id": item_id,
            "composition_multiset": src["composition_multiset"],
            "expected": src["expected"],
            "permutations": perms,
        })
        for label, rec in perms.items():
            print(f"  {item_id:28s} {label:20s} role={rec['role']:26s} ids={rec['sentence_ids_order']}")

    print("\n=== Content-equivalence check (Revision 4, binding) ===")
    verify_content_equivalence(manifest_items)
    run_content_equivalence_mutation_test(manifest_items)

    # Explicit demonstration that P4 != reverse(P3) for (0,0,1,2), per §3's
    # worked example - a structural sanity check, not a required property
    # for every item (it happens to hold only where 2+ sentences share a
    # non-extreme level).
    target = by_id["frozen_primary_0_0_1_2"]
    perms_012 = next(mi["permutations"] for mi in manifest_items if mi["item_id"] == "frozen_primary_0_0_1_2")
    p3_ids = perms_012["P3_severity_first"]["sentence_ids_order"]
    p4_ids = perms_012["P4_severity_last"]["sentence_ids_order"]
    reverse_of_p3 = list(reversed(p3_ids))
    print(f"\n  (0,0,1,2) worked example: P3={p3_ids}  P4={p4_ids}  reverse(P3)={reverse_of_p3}")
    if p4_ids != reverse_of_p3:
        print("  CONFIRMED: P4 != reverse(P3) for this item, exactly as §3 documents")
    else:
        print("  NOTE: P4 happened to equal reverse(P3) for this item's actual sentence assignment "
              "(not the case the protocol's example anticipated, but not itself an error)")

    manifest = {
        "status": "DESIGN CONTENT ONLY - no API calls made or authorized by this script.",
        "purpose": "Manifest for score_presentation_sensitivity_protocol.md Revision 4. "
                   "Reuses 3 of Phase B's frozen n=4 items' sentence content verbatim "
                   "(cross-checked byte-for-byte above), under 4 pre-registered permutations each. "
                   "P4_severity_last is a canonical-equivalent replication control (content-identical "
                   "to P1 for every item here, verified below), NOT a third non-canonical comparison arm - "
                   "only P2_full_reverse and P3_severity_first are eligible for sensitivity comparison.",
        "protocol_reference": "research/methodology/score_presentation_sensitivity_protocol.md",
        "noncanonical_labels": NONCANONICAL_LABELS,
        "permutation_roles": PERMUTATION_ROLES,
        "phase_b_manifest_reference": {
            "path": "research/data/characterization/score_phase_b_manifest.json",
            "sha256_at_build_time": _sha256_file(DATA_DIR / "score_phase_b_manifest.json"),
        },
        "severity_instructions": bpb.SEVERITY_INSTRUCTIONS,
        "severity_criteria": bpb.SEVERITY_CRITERIA,
        "permutation_labels": PERMUTATION_LABELS,
        "items": manifest_items,
        "builder_script_sha256": hashlib.sha256(THIS_FILE.read_bytes()).hexdigest(),
    }
    out_path = DATA_DIR / "score_presentation_sensitivity_manifest.json"
    out_path.write_text(json.dumps(manifest, indent=2))
    manifest_sha256 = hashlib.sha256(out_path.read_bytes()).hexdigest()

    hash_record = {
        "purpose": "Immutability record for score_presentation_sensitivity_manifest.json. "
                   "Any change to which sentences, items, or permutation definitions are used "
                   "requires a new version label and a new entry here.",
        "manifest_path": "research/data/characterization/score_presentation_sensitivity_manifest.json",
        "manifest_sha256": manifest_sha256,
        "builder_script_path": "research/src/build_score_presentation_sensitivity_manifest.py",
        "builder_script_sha256": manifest["builder_script_sha256"],
        "item_ids_immutable_identity": SELECTED_ITEM_IDS,
        "permutation_labels_immutable_identity": PERMUTATION_LABELS,
    }
    hash_path = DATA_DIR / "score_presentation_sensitivity_manifest_hashes.json"
    hash_path.write_text(json.dumps(hash_record, indent=2))

    print(f"\nWritten: {out_path}")
    print(f"Written: {hash_path}")
    print(f"Manifest sha256: {manifest_sha256}")
    print("\n=== ALL CHECKS PASSED ===")


if __name__ == "__main__":
    main()
