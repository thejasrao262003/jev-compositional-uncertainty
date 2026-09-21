"""Builds the actual Phase B item content (real sentence text) for the 9
compositions frozen at the DESIGN level in score_semantic_validation_
specification.md (6 items) and score_mvsa_supplement_v1.json (3 items).

REAL GAP THIS SCRIPT CLOSES: every prior artifact in the `score` semantic-
validation track (the spec, the supplement design, the bounded-validation
protocol) defines items as abstract level-multisets, e.g. `(0,0,0,1)` -
none of them contain actual sentence text. There is nothing to send to the
API yet. This was not previously flagged because no runner existed to
need it. Building the runner (per review's request) surfaced it.

No API calls. No network import. Sentences are authored fresh, in a single
domain (SaaS/ops incident reports, thematically continuous with
run_step0a2.py's SEV_POOL but zero text reuse from it or any other prior
manifest - checked below, not assumed), with opaque, non-semantic IDs
("b001".."b039" - the prefix identifies this as a Phase-B-batch sentence,
nothing about the ID encodes severity level, per score_semantic_
validation_specification.md §3's content-blind rule). Assignment to items
uses a seeded shuffle per level, consumed in a fixed, disclosed item order,
so it is mechanical and reproducible - not fitted to any observed output
(none exists; nothing here has ever touched a real Jev response).
"""

from __future__ import annotations

import hashlib
import json
import random
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
RESULTS_DIR = REPO_ROOT / "research" / "results"
DATA_DIR = REPO_ROOT / "research" / "data" / "characterization"
THIS_FILE = Path(__file__).resolve()

GENERATION_SEED = 1729

SEVERITY_INSTRUCTIONS = "How severe is the reported issue?"
SEVERITY_CRITERIA = [
    "Cosmetic; no impact to functionality",
    "Broken or degraded feature, but a workaround exists",
    "Blocking issue; no workaround exists",
]

# Fixed item processing order (disclosed, not incidental) - source_group +
# composition tuple exactly as they appear in the frozen documents.
FROZEN_PRIMARY_ORDER = [
    (0, 0, 0, 1), (0, 0, 0, 2), (0, 0, 1, 2),
    (0, 1, 1, 2), (0, 1, 2, 2), (1, 1, 1, 2),
]
SUPPLEMENT_V1_ORDER = [
    (0, 0, 0, 1, 2), (0, 0, 0, 2, 2), (0, 0, 2, 2, 2),
]

# Pre-registered expected values (transcribed from the already-frozen
# documents, not recomputed here first - this script independently
# RE-derives them below and asserts agreement, so a transcription error
# would be caught, not silently trusted).
EXPECTED_FROZEN = {
    (0, 0, 0, 1): {"M": 0, "X": 1, "A_unrounded": 0.25, "A_rounded": 0},
    (0, 0, 0, 2): {"M": 0, "X": 2, "A_unrounded": 0.50, "A_rounded": 1},
    (0, 0, 1, 2): {"M": 0, "X": 2, "A_unrounded": 0.75, "A_rounded": 1},
    (0, 1, 1, 2): {"M": 1, "X": 2, "A_unrounded": 1.00, "A_rounded": 1},
    (0, 1, 2, 2): {"M": 2, "X": 2, "A_unrounded": 1.25, "A_rounded": 1},
    (1, 1, 1, 2): {"M": 1, "X": 2, "A_unrounded": 1.25, "A_rounded": 1},
}
EXPECTED_SUPPLEMENT = {
    (0, 0, 0, 1, 2): {"M": 0, "X": 2, "A_unrounded": 0.6, "A_rounded": 1},
    (0, 0, 0, 2, 2): {"M": 0, "X": 2, "A_unrounded": 0.8, "A_rounded": 1},
    (0, 0, 2, 2, 2): {"M": 2, "X": 2, "A_unrounded": 1.2, "A_rounded": 1},
}

# ---------------------------------------------------------------------
# Fresh sentence pool - one domain, 39 sentences, zero reuse of any prior
# manifest's text (checked in run_uniqueness_checks below).
# ---------------------------------------------------------------------

L0_SENTENCES = [
    "The favicon appears slightly blurry when the browser window is resized below 400 pixels wide.",
    "A tooltip on the export button remains visible for about half a second after the mouse moves away.",
    "The dark mode theme renders the secondary sidebar with a slightly lighter shade than the primary sidebar.",
    "An unused CSS class causes a 2-pixel margin discrepancy on the notifications panel in Firefox only.",
    "The onboarding checklist still shows a completed step with a strikethrough that renders inconsistently in print view.",
    "The changelog entry for last month's release has a typo in the word 'improvements.'",
    "The settings page's save confirmation toast appears in the wrong corner on ultra-wide monitors.",
    "A placeholder image is shown for roughly one second before the user's avatar loads on first login.",
    "The help center search bar's magnifying glass icon is misaligned by a few pixels in Safari.",
    "The billing history table's date column header is left-aligned while every other column header is centered.",
    "An extra blank line appears at the bottom of exported CSV files when opened in a text editor.",
    "The keyboard shortcut hint for 'undo' still references a key combination from an older version of the app.",
    "The footer copyright year has not been updated to the current year on the marketing site.",
    "A decorative divider line between sections is rendered one pixel thicker on mobile Safari than elsewhere.",
    "The loading spinner on the reports page briefly flashes twice before settling into a steady animation.",
    "The dropdown menu for language selection lists 'English' twice, both pointing to the same locale.",
    "A deprecated banner about an old feature still appears on a settings tab that no longer has that feature.",
    "The support ticket confirmation email's logo is rendered at a slightly lower resolution than in other emails.",
]
L1_SENTENCES = [
    "Bulk-exporting more than 500 rows to Excel times out, but exporting in smaller batches of 200 rows succeeds.",
    "The mobile app's push notifications arrive with a delay of several minutes, though in-app notifications still update immediately.",
    "Uploading a profile photo larger than 5MB fails silently, but resizing the image first allows the upload to complete.",
    "The team calendar view does not sync recurring events created on mobile, but events created on desktop sync correctly.",
    "Autosave stops working after the browser tab has been idle for over an hour, though a manual save still succeeds.",
    "The API rate-limit counter resets incorrectly for accounts on the legacy pricing plan, but a support-issued token bypasses it.",
    "Inline comments on shared documents fail to load on the first attempt, but a page refresh reliably fixes it.",
    "The search index lags behind newly created records by up to ten minutes, though records are still retrievable by direct link.",
    "Two-factor authentication codes sent by SMS are occasionally delayed by a minute or two, but the authenticator app option works instantly.",
]
L2_SENTENCES = [
    "The checkout page throws an unhandled exception for every user attempting to pay with a stored credit card.",
    "Database replication between the primary and read replicas has stopped entirely, and no failover has occurred.",
    "The authentication service is rejecting all valid login attempts with a generic 'internal error' response.",
    "Scheduled backups have not completed successfully for the past four consecutive nights.",
    "The main API gateway is returning HTTP 503 for every request, regardless of endpoint or payload.",
    "Customer support agents are unable to open any existing ticket; the ticket detail view crashes on load for all users.",
    "Order fulfillment has halted because the warehouse integration is silently dropping every shipment request.",
    "The mobile app crashes immediately on launch for all users on the latest OS update, with no workaround available.",
    "Encrypted file uploads are being corrupted in transit, making every uploaded document unreadable on download.",
    "The permissions service is denying access to all users, including administrators, locking everyone out of the platform.",
    "Real-time analytics dashboards have shown no data for six hours because the ingestion pipeline has stalled completely.",
    "The password reset flow fails at every step because the email delivery service has stopped accepting new jobs.",
]

# Prior manifests' known sentence text, for the reuse check below - not
# re-derived from those files at runtime (they may not all be trivially
# parseable), but transcribed exactly from run_step0a2.py's own source
# (already read in full earlier in this project) so the check is against
# real prior content, not a strawman.
PRIOR_MANIFEST_SENTENCES = {
    "The tooltip on the settings icon is misaligned by a few pixels on Safari.",
    "A footer link points to an outdated documentation URL that still resolves correctly.",
    "The changelog page lists a feature as 'coming soon' that already shipped last quarter.",
    "Exporting a report to PDF fails intermittently, but exporting to CSV works as a workaround.",
    "The dashboard's live-refresh stops updating after 10 minutes, but a manual reload fixes it.",
    "Search results are missing filters for one category, but users can still find items by browsing.",
    "The password reset endpoint returns a 500 error for every request, locking out affected users.",
    "Background job processing has stopped entirely; no queued jobs have completed in over an hour.",
    "All outbound emails, including password resets and receipts, have stopped sending entirely.",
    "Requests are timing out at the load balancer before reaching any application server.",
    "Ping latency to the affected host has spiked from 2ms to over 400ms.",
    "Query execution times in the slow-query log have increased tenfold in the last hour.",
    "The connection pool is reporting frequent 'too many connections' errors.",
}


def round_half_up(x: float) -> int:
    import decimal
    return int(decimal.Decimal(str(x)).quantize(0, rounding=decimal.ROUND_HALF_UP))


def mode_with_tie_detection(values: list[int]) -> int | None:
    from collections import Counter
    counts = Counter(values)
    max_count = max(counts.values())
    modes = [v for v, c in counts.items() if c == max_count]
    return modes[0] if len(modes) == 1 else None


def run_uniqueness_checks() -> None:
    print("=== Uniqueness checks (per spec §3's content-blind construction rule) ===")
    all_new = L0_SENTENCES + L1_SENTENCES + L2_SENTENCES
    assert len(all_new) == 39, f"expected exactly 39 fresh sentences, got {len(all_new)}"
    assert len(set(all_new)) == 39, "duplicate sentence text found within the new pool"
    print(f"  PASS: 39 sentences authored, all internally distinct (18 L0 + 9 L1 + 12 L2)")

    overlap = set(all_new) & PRIOR_MANIFEST_SENTENCES
    assert not overlap, f"new pool reuses prior-manifest text: {overlap}"
    print(f"  PASS: zero overlap with the {len(PRIOR_MANIFEST_SENTENCES)} known prior-manifest sentences "
          f"(run_step0a2.py's SEV_POOL + Step 0A.1/0A.2's choice sentences)")


def assign_sentences() -> dict[int, list[str]]:
    """Seeded shuffle per level, consumed sequentially - deterministic,
    reproducible, no Jev output involved (none exists at this point)."""
    rng = random.Random(GENERATION_SEED)
    pools = {0: list(L0_SENTENCES), 1: list(L1_SENTENCES), 2: list(L2_SENTENCES)}
    for level in pools:
        rng.shuffle(pools[level])
    return pools


def build_items() -> list[dict]:
    pools = assign_sentences()
    next_id = 1
    items = []

    def consume(level: int) -> tuple[str, str]:
        nonlocal next_id
        opaque_id = f"b{next_id:03d}"
        next_id += 1
        text = pools[level].pop()
        return opaque_id, text

    for source_group, order, expected_table in [
        ("frozen_primary", FROZEN_PRIMARY_ORDER, EXPECTED_FROZEN),
        ("supplement_v1", SUPPLEMENT_V1_ORDER, EXPECTED_SUPPLEMENT),
    ]:
        for composition in order:
            sentence_records = [consume(level) for level in composition]
            # Canonical presentation = opaque IDs sorted ascending (spec §4),
            # applied explicitly here, not assumed to match consumption order.
            sentence_records_sorted = sorted(sentence_records, key=lambda r: r[0])
            sentence_ids = [r[0] for r in sentence_records_sorted]
            sentence_texts = [r[1] for r in sentence_records_sorted]
            # Re-derive M/X/A from the LEVEL MULTISET alone (order-invariant
            # by construction, per the project's established finding) -
            # independent of sentence order/identity.
            levels = list(composition)
            m = mode_with_tie_detection(levels)
            x = max(levels)
            a_unrounded = sum(levels) / len(levels)
            a_rounded = round_half_up(a_unrounded)
            expected = expected_table[composition]
            assert m == expected["M"], f"{composition}: M mismatch, got {m} expected {expected['M']}"
            assert x == expected["X"], f"{composition}: X mismatch"
            assert abs(a_unrounded - expected["A_unrounded"]) < 1e-9, f"{composition}: A_unrounded mismatch"
            assert a_rounded == expected["A_rounded"], f"{composition}: A_rounded mismatch"

            item_id = f"{source_group}_{'_'.join(str(l) for l in composition)}"
            items.append({
                "item_id": item_id,
                "source_group": source_group,
                "composition_multiset": levels,
                "n_sentences": len(levels),
                "sentence_ids_canonical_order": sentence_ids,
                "sentence_levels_by_id": {sid: lvl for sid, lvl in zip(sentence_ids, [r for r in composition])},
                "state": " ".join(sentence_texts),
                "expected": expected,
            })
    return items


def main() -> None:
    run_uniqueness_checks()
    items = build_items()
    assert len(items) == 9, f"expected 9 items, got {len(items)}"
    assert len({it["item_id"] for it in items}) == 9, "duplicate item_id"
    all_sentence_ids = [sid for it in items for sid in it["sentence_ids_canonical_order"]]
    assert len(all_sentence_ids) == 39, f"expected 39 total sentence slots, got {len(all_sentence_ids)}"
    assert len(set(all_sentence_ids)) == 39, "a sentence ID was reused across items"
    print(f"\n=== Built and cross-checked {len(items)} items (39 total sentence slots, zero reuse) ===")
    for it in items:
        print(f"  {it['item_id']:28s} n={it['n_sentences']}  expected M={it['expected']['M']} "
              f"X={it['expected']['X']} A={it['expected']['A_rounded']}  ids={it['sentence_ids_canonical_order']}")

    manifest = {
        "status": "DESIGN CONTENT ONLY - no API calls made or authorized by this script.",
        "purpose": "Real sentence content for the 9 items frozen at the composition level in "
                   "score_semantic_validation_specification.md (6) and score_mvsa_supplement_v1.json (3). "
                   "Closes a real gap: those documents defined level-multisets only, never sentence text.",
        "generation_seed": GENERATION_SEED,
        "domain": "saas_ops_incident_reports",
        "severity_instructions": SEVERITY_INSTRUCTIONS,
        "severity_criteria": SEVERITY_CRITERIA,
        "item_processing_order": [it["item_id"] for it in items],
        "items": items,
        "builder_script_sha256": hashlib.sha256(THIS_FILE.read_bytes()).hexdigest(),
    }
    out_path = DATA_DIR / "score_phase_b_manifest.json"
    out_path.write_text(json.dumps(manifest, indent=2))
    manifest_sha256 = hashlib.sha256(out_path.read_bytes()).hexdigest()

    hash_record = {
        "purpose": "Immutability record for score_phase_b_manifest.json, the actual sentence content "
                   "backing the 9 abstract compositions frozen elsewhere. Any change to which sentences "
                   "are used, their assignment, or the composition set requires a new version label and "
                   "a new entry here, per the same discipline as score_supplement_hashes.json.",
        "manifest_path": "research/data/characterization/score_phase_b_manifest.json",
        "manifest_sha256": manifest_sha256,
        "builder_script_path": "research/src/build_score_phase_b_manifest.py",
        "builder_script_sha256": manifest["builder_script_sha256"],
        "item_ids_immutable_identity": [it["item_id"] for it in items],
    }
    hash_path = DATA_DIR / "score_phase_b_manifest_hashes.json"
    hash_path.write_text(json.dumps(hash_record, indent=2))

    print(f"\nWritten: {out_path}")
    print(f"Written: {hash_path}")
    print(f"Manifest sha256: {manifest_sha256}")
    print("\n=== ALL CHECKS PASSED ===")


if __name__ == "__main__":
    main()
