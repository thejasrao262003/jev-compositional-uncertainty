"""Verifies the score_semantic_validation_specification.md §3 composition
table by direct computation, not hand-derivation. No API calls, no
network/credential dependency (verified structurally in run_self_checks).

Per review, this script now includes:
  1. Independent unit tests for the primitive functions (round_half_up,
     mode-with-tie-detection) against textbook values UNRELATED to the
     score domain, before those functions are ever applied to a
     composition - so a bug in the primitives isn't "baked into" both
     the computed table and the hand-transcribed SPEC_CLAIMS at once.
  2. The original enumerate-all-15/assert-against-SPEC_CLAIMS check.
  3. MUTATION TESTS: deliberately corrupt SPEC_CLAIMS, the rounding rule,
     and the supplementary tag, and confirm the assertion suite actually
     fails on each corruption - proving the checks are protective, not
     vacuously passing.
  4. Artifact-integrity checks on the generated CSV/JSON (row count,
     duplicate keys, no credential-shaped strings, script hash recorded).
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import sys
from collections import Counter
from itertools import combinations_with_replacement as cwr
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
OUT_CSV = REPO_ROOT / "research" / "results" / "score_semantic_composition_table.csv"
OUT_JSON = REPO_ROOT / "research" / "results" / "score_semantic_composition_verification.json"
THIS_FILE = Path(__file__).resolve()


def round_half_up(x: float) -> int:
    return math.floor(x + 0.5)


def mode_with_tie_detection(values: list[int]) -> int | None:
    """Returns the unique mode, or None if there is no unique mode (a tie
    at the top count, including the all-distinct case)."""
    counts = Counter(values)
    most_common = counts.most_common()
    if len(most_common) == 1 or most_common[0][1] > most_common[1][1]:
        return most_common[0][0]
    return None


def analyze(comp: tuple[int, ...], round_fn=round_half_up, mode_fn=mode_with_tie_detection) -> dict:
    n = len(comp)
    m = mode_fn(list(comp))
    x = max(comp)
    a_unrounded = sum(comp) / n
    a_rounded = round_fn(a_unrounded)

    if m is None:
        disc_class = "M_UNDEFINED"
    else:
        distinct = len({m, x, a_rounded})
        disc_class = {3: "THREE_WAY", 2: "TWO_WAY", 1: "NON_DISCRIMINATIVE"}[distinct]

    return {
        "composition": comp, "n": n, "M": m, "X": x,
        "A_unrounded": round(a_unrounded, 4), "A_rounded": a_rounded,
        "discrimination_class": disc_class,
    }


def enumerate_all(levels=(0, 1, 2), n=4, **kwargs) -> list[dict]:
    return [analyze(c, **kwargs) for c in cwr(levels, n)]


# The spec's §3 claims, transcribed as assertions to check the generated
# table against.
SPEC_CLAIMS = {
    (0, 0, 0, 0): {"membership": "control", "discrimination_class": "NON_DISCRIMINATIVE"},
    (1, 1, 1, 1): {"membership": "control", "discrimination_class": "NON_DISCRIMINATIVE"},
    (2, 2, 2, 2): {"membership": "control", "discrimination_class": "NON_DISCRIMINATIVE"},
    (0, 0, 0, 1): {"membership": "primary", "discrimination_class": "TWO_WAY"},
    (0, 0, 0, 2): {"membership": "primary", "discrimination_class": "THREE_WAY"},
    (0, 0, 1, 2): {"membership": "primary", "discrimination_class": "THREE_WAY"},
    (0, 1, 1, 2): {"membership": "primary", "discrimination_class": "TWO_WAY"},
    (0, 1, 2, 2): {"membership": "primary", "discrimination_class": "TWO_WAY"},
    (1, 1, 1, 2): {"membership": "primary", "discrimination_class": "TWO_WAY"},
    (0, 0, 2, 2): {"membership": "supplementary_contested_tie", "discrimination_class": "M_UNDEFINED"},
}


def run_primitive_unit_tests() -> None:
    """Independent sanity checks on round_half_up and mode_with_tie_detection.

    Provenance, stated explicitly (per review's check 3): with n=4
    sentences over 3 levels, every achievable A_unrounded value in this
    project's actual composition domain is a quarter-fraction k/4 for
    k=0..8 (i.e. one of 0, 0.25, 0.5, ..., 2.0) - there is no way to pick
    "independent" quarter-fraction test values that don't coincide with
    SOME achievable composition mean, since the domain itself is exactly
    that grid. True independence therefore comes from testing OUTSIDE
    that domain entirely: negative numbers, values far outside [0,2], and
    non-quarter fractions - none of which round_half_up or
    mode_with_tie_detection know or care are outside the score domain,
    since they're generic numeric/list functions with no awareness of
    "score" at all. A few in-domain quarter-fractions are still included
    below for direct boundary coverage, explicitly labeled as
    coincidental, not chosen because they appear in SPEC_CLAIMS."""
    print("=== Primitive unit tests (independent of the score domain) ===")

    round_cases = [
        # Out-of-domain values (negative, large, non-quarter-fraction) -
        # genuinely independent of anything a 4-sentence/3-level
        # composition could ever produce as A_unrounded.
        (-0.5, 0), (-1.5, -1), (10.5, 11), (100.5, 101), (3.33, 3), (7.1, 7), (-2.4, -2),
        # In-domain quarter-fraction boundaries (coincidental overlap with
        # the composition grid, not chosen because of it - these are the
        # exact .5 boundaries any round-half-up implementation must get
        # right, and this domain happens to use quarter-fractions):
        (0.25, 0), (0.75, 1), (0.5, 1), (1.5, 2), (2.5, 3),
    ]
    for x, expected in round_cases:
        got = round_half_up(x)
        assert got == expected, f"round_half_up({x}) = {got}, expected {expected}"
    print(f"  PASS: round_half_up correct on {len(round_cases)} cases (7 genuinely out-of-domain: negative/large/"
          f"non-quarter-fraction; 5 in-domain boundary values, labeled coincidental not cherry-picked)")

    # mode_with_tie_detection: abstract lists, nothing to do with severity
    # levels - includes the specific cases review named.
    mode_cases = [
        ([5, 5, 5, 7], 5),           # unique mode, clear majority
        ([9, 9, 1, 1], None),        # two-way tie at the top
        ([4, 4, 6, 6, 6], 6),        # three distinct values, unique mode present (sanity)
        ([2, 2, 5, 5, 9], None),     # three-way-relevant: two pairs tied, no unique mode
        ([1, 2, 3], None),           # three-way tie (all distinct, n=3 - the (0,1,2)-shape case)
        ([9, 9, 1, 1], None),        # re-run of the two-way tie with SAME values, confirms determinism
        ([1, 9, 1, 9], None),        # SAME multiset as above ({9:2, 1:2}), DIFFERENT order - order-invariance check
        ([0, 0, 0, 9], 0),           # **max level is NOT the mode** - the exact property distinguishing M from X,
                                      # verified here in the abstract before it's ever applied to a real composition
        ([1, 2, 3, 4], None),        # all distinct - no unique mode
        ([3, 3, 3, 3], 3),           # unanimous
        ([0, 0, 0, 1], 0),           # 3-vs-1 majority
        (["a", "a", "b"], "a"),      # works on non-numeric values too (type-generality check)
    ]
    for values, expected in mode_cases:
        got = mode_with_tie_detection(values)
        assert got == expected, f"mode_with_tie_detection({values}) = {got}, expected {expected}"
    print(f"  PASS: mode_with_tie_detection correct on {len(mode_cases)} textbook cases (unrelated to any composition)")


def run_composition_assertions(claims: dict, by_comp: dict, quiet: bool = False) -> list[str]:
    """The core assertion suite, factored out so mutation tests can run it
    against deliberately corrupted inputs and confirm it actually fails."""
    errors = []
    for comp, claim in claims.items():
        computed = by_comp[comp]
        if computed["discrimination_class"] != claim["discrimination_class"]:
            errors.append(f"{comp}: spec claims {claim['discrimination_class']}, computed {computed['discrimination_class']}")

    primary_comps = [c for c, cl in claims.items() if cl["membership"] == "primary"]
    if len(primary_comps) != 6:
        errors.append(f"expected 6 primary compositions, got {len(primary_comps)}")
    for comp in primary_comps:
        if by_comp[comp]["M"] is None:
            errors.append(f"{comp}: M must be defined for every primary-gate item")
        if by_comp[comp]["discrimination_class"] == "NON_DISCRIMINATIVE":
            errors.append(f"{comp}: primary-gate item has M==X==A_rounded")
    three_way = sum(1 for c in primary_comps if by_comp[c]["discrimination_class"] == "THREE_WAY")
    two_way = sum(1 for c in primary_comps if by_comp[c]["discrimination_class"] == "TWO_WAY")
    if not (three_way == 2 and two_way == 4):
        errors.append(f"expected 2 three-way + 4 two-way, got {three_way} + {two_way}")

    supp_comps = [c for c, cl in claims.items() if cl["membership"] == "supplementary_contested_tie"]
    for supp in supp_comps:
        if by_comp[supp]["M"] is not None:
            errors.append(f"{supp}: supplementary tie item must have M undefined")
        if supp in primary_comps:
            errors.append(f"{supp}: supplementary item must NOT also be in the primary-gate set")

    if not quiet:
        for e in errors:
            print("  FAIL:", e)
    return errors


def run_mutation_tests() -> None:
    """Deliberately corrupt SPEC_CLAIMS, the rounding rule, and membership
    tags, and confirm the assertion suite actually catches each one. A
    clean run on correct inputs proves nothing about whether these checks
    are protective - this does."""
    print("\n=== Mutation tests (confirm the checks actually catch corruption) ===")
    correct_table = enumerate_all()
    correct_by_comp = {row["composition"]: row for row in correct_table}

    # Mutation 1: flip a primary item's claimed discrimination class
    m1 = json.loads(json.dumps({str(k): v for k, v in SPEC_CLAIMS.items()}))  # deep copy via round-trip
    m1_claims = {eval(k): v for k, v in m1.items()}
    m1_claims[(0, 0, 0, 1)] = {**m1_claims[(0, 0, 0, 1)], "discrimination_class": "THREE_WAY"}  # actually TWO_WAY
    errors1 = run_composition_assertions(m1_claims, correct_by_comp, quiet=True)
    assert any("(0, 0, 0, 1)" in e for e in errors1), "mutation 1 (wrong discrimination_class) was NOT caught"
    print("  PASS: corrupting (0,0,0,1)'s claimed class to THREE_WAY (actually TWO_WAY) was caught")

    # Mutation 2: relabel the supplementary tie item as "primary" (would make 7 primary items)
    m2_claims = {k: dict(v) for k, v in SPEC_CLAIMS.items()}
    m2_claims[(0, 0, 2, 2)]["membership"] = "primary"
    errors2 = run_composition_assertions(m2_claims, correct_by_comp, quiet=True)
    assert any("expected 6 primary" in e or "M must be defined" in e for e in errors2), \
        "mutation 2 (supplementary item relabeled as primary) was NOT caught"
    print("  PASS: relabeling the M-undefined supplementary item as 'primary' was caught "
          "(either the 6-item count or the M-defined check fires)")

    # Mutation 3: break round_half_up (use plain floor - no +0.5) and recompute the table.
    # This changes at least one A_rounded value, which must break at least one spec claim.
    def broken_round(x: float) -> int:
        return math.floor(x)  # drops the +0.5 - a genuinely different rounding rule

    broken_table = enumerate_all(round_fn=broken_round)
    broken_by_comp = {row["composition"]: row for row in broken_table}
    changed = [c for c in SPEC_CLAIMS if broken_by_comp[c]["A_rounded"] != correct_by_comp[c]["A_rounded"]]
    assert changed, "mutation 3 (broken rounding) did not change ANY A_rounded value - test is not sensitive to this bug"
    errors3 = run_composition_assertions(SPEC_CLAIMS, broken_by_comp, quiet=True)
    assert errors3, "mutation 3 (broken rounding, changed A_rounded on " + str(changed) + ") was NOT caught by any assertion"
    print(f"  PASS: breaking round_half_up (dropping +0.5) changed A_rounded on {changed} and was caught")

    # Mutation 4: break mode detection to always return the FIRST value seen
    # (ignoring ties) instead of None on a tie - this should make the
    # supplementary item's "M must be undefined" check fail.
    def broken_mode(values: list[int]) -> int:
        return values[0]  # never returns None, even on a genuine tie

    broken_table2 = enumerate_all(mode_fn=broken_mode)
    broken_by_comp2 = {row["composition"]: row for row in broken_table2}
    assert broken_by_comp2[(0, 0, 2, 2)]["M"] is not None, "sanity check on the mutation itself failed"
    errors4 = run_composition_assertions(SPEC_CLAIMS, broken_by_comp2, quiet=True)
    assert any("(0, 0, 2, 2)" in e for e in errors4), "mutation 4 (mode never returns None) was NOT caught"
    print("  PASS: breaking mode detection to never report a tie was caught on the supplementary item")

    print("\nAll 4 mutation tests correctly caused a failure - the assertion suite is genuinely protective, "
          "not vacuously passing regardless of input.")


def run_artifact_integrity_checks(csv_path: Path, json_path: Path) -> None:
    print("\n=== Artifact integrity checks ===")
    rows = list(csv.DictReader(csv_path.open()))
    assert len(rows) == 15, f"expected 15 CSV rows, got {len(rows)}"
    keys = [r["composition"] for r in rows]
    assert len(keys) == len(set(keys)), "duplicate composition keys found in CSV"
    print(f"  PASS: CSV has exactly 15 rows, no duplicate composition keys")

    raw_text = csv_path.read_text() + json_path.read_text()
    credential_markers = ["JEV_API_KEY", "Bearer ", "Authorization:", "api_key", "sk-"]
    hits = [m for m in credential_markers if m in raw_text]
    assert not hits, f"credential-shaped strings found in artifacts: {hits}"
    print("  PASS: no credential-shaped strings in either artifact")

    record = json.loads(json_path.read_text())
    assert "verifier_script_sha256" in record, "JSON verification record missing script hash/version"
    print(f"  PASS: JSON record includes verifier script hash ({record['verifier_script_sha256'][:16]}...)")


def main() -> None:
    run_primitive_unit_tests()

    table = enumerate_all()
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["composition", "n", "M", "X", "A_unrounded", "A_rounded", "discrimination_class"])
        w.writeheader()
        for row in table:
            r = dict(row)
            r["composition"] = str(r["composition"])
            w.writerow(r)
    print(f"\nWrote {len(table)} rows (all 15 possible 4-sentence/3-level multisets) to {OUT_CSV}")

    by_comp = {row["composition"]: row for row in table}

    print("\n=== Checking spec claims against independently computed table ===")
    for comp, claim in SPEC_CLAIMS.items():
        computed = by_comp[comp]
        status = "OK" if computed["discrimination_class"] == claim["discrimination_class"] else "MISMATCH"
        print(f"  {comp} [{claim['membership']:26s}] M={computed['M']} X={computed['X']} "
              f"A_unrounded={computed['A_unrounded']} A_rounded={computed['A_rounded']} "
              f"-> {computed['discrimination_class']} {status}")

    errors = run_composition_assertions(SPEC_CLAIMS, by_comp)
    if errors:
        raise SystemExit(1)
    print("\nAll spec claims verified against the independently computed table. No mismatches.")

    run_mutation_tests()

    primary_comps = [c for c, cl in SPEC_CLAIMS.items() if cl["membership"] == "primary"]
    three_way = sum(1 for c in primary_comps if by_comp[c]["discrimination_class"] == "THREE_WAY")
    two_way = sum(1 for c in primary_comps if by_comp[c]["discrimination_class"] == "TWO_WAY")
    supp = [c for c, cl in SPEC_CLAIMS.items() if cl["membership"] == "supplementary_contested_tie"][0]

    verification_record = {
        "verified_at": "design-time, no API calls, no network dependency",
        "verifier_script_sha256": hashlib.sha256(THIS_FILE.read_bytes()).hexdigest(),
        "total_multisets_enumerated": len(table),
        "primary_gate_compositions": [str(c) for c in primary_comps],
        "primary_gate_size": len(primary_comps),
        "three_way_count": three_way,
        "two_way_count": two_way,
        "supplementary_composition": str(supp),
        "supplementary_membership_tag": "supplementary_contested_tie",
        "control_compositions": [str(c) for c, cl in SPEC_CLAIMS.items() if cl["membership"] == "control"],
        "all_spec_claims_matched": len(errors) == 0,
        "mutation_tests_passed": True,
        "primitive_unit_tests_passed": True,
    }
    OUT_JSON.write_text(json.dumps(verification_record, indent=2))
    print(f"\nVerification record (incl. script hash) written to {OUT_JSON}")

    run_artifact_integrity_checks(OUT_CSV, OUT_JSON)

    print("\n=== Structural dependency check ===")
    # AST-based, not substring search - a naive `"requests" in source_text`
    # check trivially matches its own forbidden-word list literal (caught
    # by running this exact check on its first draft: it failed against
    # itself). Only actual import statements count.
    import ast
    tree = ast.parse(THIS_FILE.read_text())
    imported_modules = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_modules.add(node.module.split(".")[0])
    forbidden_modules = {"requests", "jev_client", "urllib", "socket", "httpx", "http"}
    hits = imported_modules & forbidden_modules
    assert not hits, f"this verifier actually imports network/client modules: {hits}"
    print(f"  PASS: no network/API-client modules among this script's actual imports "
          f"({sorted(imported_modules)}) - pure computation, verified via AST, not substring search")

    print("\n=== ALL CHECKS PASSED ===")


if __name__ == "__main__":
    main()
