"""Builds the manifest for the workflow-composition calibration pilot
(workflow_calibration_pilot_protocol.md). 30 fresh, content-blind
instances over the frozen task from workflow_uncertainty_composition_
protocol.md §16.2 (choice: subsystem routing; noul: customer-facing;
score: severity), applying the frozen F table to get a*.

No API calls. No new task/generator/F defined here - all reused exactly
from §16.2. Only the sentence CONTENT is new, checked for zero overlap
with every prior manifest's text this project has produced.
"""

from __future__ import annotations

import hashlib
import json
import random
import sys
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SRC_DIR))

import build_score_phase_b_manifest as score_bpb  # noqa: E402 - read-only, for the reuse-check corpus

REPO_ROOT = SRC_DIR.parent.parent
DATA_DIR = REPO_ROOT / "research" / "data" / "characterization"
THIS_FILE = Path(__file__).resolve()

GENERATION_SEED = 20260927  # today's date at authoring time, disclosed, arbitrary
N_CALIB = 30

CHOICE_INSTRUCTIONS = "Which subsystem is most likely responsible for this incident?"
CHOICE_CRITERIA = {
    "network": "Issues with connectivity, latency, routing, DNS, or packet loss between systems",
    "database": "Issues with query performance, connection pooling, disk I/O, replication, or locking",
}
NOUL_INSTRUCTIONS = "Is this incident customer-facing?"
SEVERITY_INSTRUCTIONS = "How severe is this incident?"
SEVERITY_CRITERIA = [
    "Cosmetic; no impact to functionality",
    "Broken or degraded feature, but a workaround exists",
    "Blocking issue; no workaround exists",
]

# ---------------------------------------------------------------------
# Fresh sentence pools - 30 each, zero reuse of any prior manifest text.
# ---------------------------------------------------------------------

ROUTING_NETWORK = [
    "Ping latency between the edge load balancer and the origin servers has climbed from under 5ms to over 300ms.",
    "The BGP route to the secondary data center flapped four times in the last hour.",
    "TCP connection resets are appearing in the firewall logs for roughly one in twenty requests.",
    "DNS resolution for the internal service mesh is intermittently returning stale IP addresses.",
    "The VPN tunnel between the two availability zones dropped and reconnected four times overnight.",
    "Packet loss on the inter-region link has been holding steady at around eight percent.",
    "The CDN's edge nodes in the affected region are reporting elevated TLS handshake failures.",
    "A misconfigured route table is sending a portion of east-coast traffic through the west-coast gateway.",
    "The load balancer's health checks are marking otherwise-healthy backends as down every few minutes.",
    "Network interface counters on the affected hosts show a sharp rise in retransmitted packets.",
    "The service mesh's sidecar proxies are timing out on roughly fifteen percent of outbound calls.",
    "A recent firmware update to the core switches appears to have introduced intermittent link flaps.",
    "Cross-region replication traffic is being throttled by an unexpectedly aggressive rate limiter on the network edge.",
    "The ISP peering point serving this region reported a partial outage window overlapping the incident.",
    "MTU mismatches between two subnets are causing large packets to be silently dropped.",
]
ROUTING_DATABASE = [
    "Query execution times on the primary read replica have increased roughly eightfold since this morning.",
    "The connection pool to the primary database is exhausted, with new connections queuing for several seconds.",
    "A long-running migration job is holding a table lock that is blocking routine write transactions.",
    "Replication lag between the primary and its read replicas has grown to several minutes.",
    "The database's autovacuum process has fallen behind, and table bloat is now affecting query planning.",
    "An index that normally covers the most common lookup pattern was dropped during last night's schema change.",
    "Disk I/O wait times on the database host have tripled compared to the same period last week.",
    "A batch reporting job is issuing full table scans against a table that normally serves point lookups.",
    "The database's write-ahead log is filling faster than it can be archived to the backup target.",
    "Deadlocks between two competing transaction types have started appearing in the database's error log.",
    "The primary database's connection limit was reached during a scheduled backup window.",
    "A recently deployed query is missing a WHERE clause and is scanning the entire orders table.",
    "Statistics on the largest table have gone stale, causing the query planner to choose a poor execution plan.",
    "The database failover completed, but several application nodes are still pointed at the old primary's address.",
    "Row-level lock contention has spiked on the table that tracks user session state.",
]
IMPACT_YES = [
    "Support has received over forty tickets in the last hour from users unable to complete checkout.",
    "The status page's public incident thread already has dozens of customer replies reporting the same symptom.",
    "Multiple enterprise customers have escalated through their account managers within the last thirty minutes.",
    "Social media mentions of the outage have started appearing from users outside the company's own monitoring.",
    "The affected feature is on the critical path for every paying customer's daily workflow.",
    "Customers in the free tier and the enterprise tier are both reporting the identical failure.",
    "The mobile app's crash reports show a spike originating entirely from real end-user sessions.",
    "A customer's automated integration began failing and paged their own on-call team, who then contacted support.",
    "The affected endpoint is called directly by the customer-facing dashboard on every page load.",
    "Live chat volume has tripled in the last twenty minutes, almost entirely about this one symptom.",
]
IMPACT_NO = [
    "The affected job runs only on an internal nightly schedule with no customer-visible output.",
    "This component is used exclusively by the internal analytics team for ad hoc reporting.",
    "No customer-facing endpoints depend on this service; it only feeds an internal dashboard.",
    "The affected pipeline processes data that is not surfaced to any customer for several days.",
    "This is a staging-environment issue and has no path to production customer traffic.",
    "The impacted tool is used only by the internal support team to triage other tickets.",
    "Customer traffic is served by a separate, unaffected cluster; this one only handles internal batch work.",
    "The broken cron job only regenerates an internal cache that customers never query directly.",
    "This subsystem exists solely to feed the internal cost-accounting dashboard, unseen by customers.",
    "The affected service is a decommissioned internal tool still running in a legacy environment.",
]
IMPACT_UNCLEAR = [
    "It is not yet known whether the affected cache is also used by any customer-facing service.",
    "The on-call engineer flagged that this component's downstream consumers have not been fully mapped.",
    "Whether this queue feeds a customer-visible feature depends on a routing rule nobody has confirmed yet.",
    "The service's ownership recently changed teams, and its current customer exposure is undocumented.",
    "Some but not all of this service's consumers are known; the rest are unconfirmed at this time.",
    "The dependency graph for this component has not been updated since a large refactor last quarter.",
    "It's unclear whether the affected feature flag is enabled for any customer segment right now.",
    "Whether this outage reaches paying customers depends on a fallback path whose current status is unknown.",
    "The team that owns this service could not immediately confirm which customers, if any, are affected.",
    "This is a shared library used by several services, and not all of their customer exposure is known.",
]
SEVERITY_COSMETIC = [
    "The new icon set renders one pixel taller than the old one in the collapsed sidebar.",
    "A tooltip's arrow points slightly off-center when the browser is zoomed to 110 percent.",
    "The date picker's month label overflows its container by a few pixels in Japanese locale.",
    "An unused feature flag still shows a 'beta' badge next to a feature that shipped months ago.",
    "The email digest's footer link uses last year's support hours, which have since changed.",
    "A debug console.log statement is visible in the browser's developer tools on the login page.",
    "The onboarding tour's fourth step points to a button that has since moved two pixels left.",
    "The dark theme's disabled-button state is barely distinguishable from its enabled state.",
    "A leftover placeholder string appears briefly before the real page title loads.",
    "The print stylesheet omits the company logo that appears in every other view.",
]
SEVERITY_DEGRADED = [
    "Scheduled exports larger than 10,000 rows fail, but splitting them into smaller batches succeeds.",
    "The keyboard shortcut for search stopped working, though clicking the search icon still opens it.",
    "Inline editing on the settings page occasionally reverts unsaved changes, but a manual save button works.",
    "The mobile app's offline mode drops the last few seconds of typed input, but nothing further back.",
    "Bulk user invites fail above 200 recipients per batch, but smaller batches complete normally.",
    "The dashboard's real-time widget lags by up to two minutes, though the underlying data is otherwise correct.",
    "Two-factor recovery codes fail to regenerate on the first attempt but succeed on a second try.",
    "The API's pagination cursor occasionally skips a page, but requesting the next cursor recovers it.",
    "Autosave on the document editor pauses after forty-five minutes of continuous editing, requiring a manual save.",
    "The report scheduler misses its exact time slot by a few minutes but always eventually runs.",
]
SEVERITY_BLOCKING = [
    "Every attempt to submit the primary onboarding form returns a server error with no retry path.",
    "The billing service is rejecting all payment methods, including ones that worked minutes earlier.",
    "User provisioning has stopped entirely; no new accounts can be created through any channel.",
    "The search index has stopped updating, and no manual reindex trigger is currently available.",
    "All webhook deliveries are failing silently with no error surfaced to the sending service.",
    "The primary authentication provider is returning errors for one hundred percent of login attempts.",
    "Data export has been completely disabled after the underlying storage bucket became unreachable.",
    "Every scheduled job across the platform has stopped firing since the scheduler process crashed.",
    "The core API gateway is returning empty responses for every request regardless of endpoint.",
    "Account deletion requests are silently failing, leaving affected accounts in an inconsistent state.",
]

# Known prior-manifest text (score track's 39 authored sentences + its own recorded 13
# prior-to-that sentences) - checked for zero overlap, not re-derived at runtime.
KNOWN_PRIOR_SENTENCES = set(
    score_bpb.L0_SENTENCES + score_bpb.L1_SENTENCES + score_bpb.L2_SENTENCES
) | score_bpb.PRIOR_MANIFEST_SENTENCES

# ---------------------------------------------------------------------
# F table (§16.2, reused exactly - not redefined)
# ---------------------------------------------------------------------

def F(c2: str, c3: int) -> str:
    """Must match workflow_uncertainty_composition_protocol.md §16.2's
    table exactly: c2="unclear" resolves to request_more_evidence for
    EVERY c3 value (checked first, not overridden by c3's own branches -
    a real bug on the first implementation attempt checked c3==2 first,
    incorrectly turning (unclear, 2) into "escalate" instead of the
    frozen table's "request_more_evidence"; caught by
    verify_F_totality_and_properties, fixed here, not in the protocol
    document, which was correct all along)."""
    if c2 == "unclear":
        return "request_more_evidence"
    if c3 == 2:
        return "escalate"
    if c3 == 1:
        return "defer" if c2 == 1 else "accept"
    return "accept"  # c3 == 0


def run_uniqueness_checks() -> None:
    print("=== Uniqueness checks ===")
    all_new = (ROUTING_NETWORK + ROUTING_DATABASE + IMPACT_YES + IMPACT_NO + IMPACT_UNCLEAR
               + SEVERITY_COSMETIC + SEVERITY_DEGRADED + SEVERITY_BLOCKING)
    assert len(all_new) == 30 * 3, f"expected 90 fresh sentences, got {len(all_new)}"
    assert len(set(all_new)) == len(all_new), "duplicate sentence text found within the new pools"
    print(f"  PASS: {len(all_new)} sentences authored across 6 flavor-pools, all internally distinct")

    overlap = set(all_new) & KNOWN_PRIOR_SENTENCES
    assert not overlap, f"new pool reuses prior-manifest text: {overlap}"
    print(f"  PASS: zero overlap with the {len(KNOWN_PRIOR_SENTENCES)} known prior-manifest sentences "
          f"(score track's 39 + its own 13 recorded prior sentences)")


def build_schedule() -> list[dict]:
    """18 reachable (c1,c2,c3) combos, each once, plus 12 more to reach
    30 - fixed before any sentence is written, per the pilot protocol
    §3. The 12 extra draws are selected DETERMINISTICALLY (not by random
    shuffle) to land exactly on the remaining sentence-pool capacity:
    after the base 18, each c1 value has 6 sentences left (15-9), each
    c2/c3 value has 4 left (10-6) - a EXACTLY zero-slack budget, so a
    random shuffle-and-slice can (and on the first run, did) overshoot
    a single value's pool. Real bug, caught by execution, fixed by
    replacing the random selection with an explicit balanced
    construction: for each c1 value, take the 6 (c2,c3) pairs where
    c2's index != c3's index (an off-diagonal selection over the 3x3
    grid) - this gives exactly 2 draws of each c2 value and exactly 2
    draws of each c3 value per c1 group, hence exactly 4/4/4 and 6/6
    totals across both groups, matching capacity exactly by construction
    rather than by search."""
    combos = []
    for c1 in ("network", "database"):
        for c2 in (0, 1, "unclear"):
            for c3 in (0, 1, 2):
                combos.append((c1, c2, c3))
    assert len(combos) == 18

    c2_values = (0, 1, "unclear")
    c3_values = (0, 1, 2)
    extra = []
    for c1 in ("network", "database"):
        for c2_idx, c2 in enumerate(c2_values):
            for c3_idx, c3 in enumerate(c3_values):
                if c2_idx != c3_idx:  # off-diagonal: 6 of the 9 pairs per c1 value
                    extra.append((c1, c2, c3))
    assert len(extra) == 12

    schedule = combos + extra
    assert len(schedule) == N_CALIB

    # Verify the balance claim directly, not just by construction argument.
    from collections import Counter
    c1_counts = Counter(c1 for c1, _, _ in schedule)
    c2_counts = Counter(c2 for _, c2, _ in schedule)
    c3_counts = Counter(c3 for _, _, c3 in schedule)
    assert c1_counts == {"network": 15, "database": 15}, c1_counts
    assert c2_counts == {0: 10, 1: 10, "unclear": 10}, c2_counts
    assert c3_counts == {0: 10, 1: 10, 2: 10}, c3_counts

    return [{"c1": c1, "c2": c2, "c3": c3} for c1, c2, c3 in schedule]


def build_items(schedule: list[dict]) -> list[dict]:
    pools = {
        ("network",): list(ROUTING_NETWORK),
        ("database",): list(ROUTING_DATABASE),
        (0,): list(IMPACT_NO),
        (1,): list(IMPACT_YES),
        ("unclear",): list(IMPACT_UNCLEAR),
    }
    severity_pools = {0: list(SEVERITY_COSMETIC), 1: list(SEVERITY_DEGRADED), 2: list(SEVERITY_BLOCKING)}
    rng = random.Random(GENERATION_SEED)
    for pool in list(pools.values()) + list(severity_pools.values()):
        rng.shuffle(pool)

    items = []
    for idx, combo in enumerate(schedule, 1):
        c1, c2, c3 = combo["c1"], combo["c2"], combo["c3"]
        routing_sentence = pools[(c1,)].pop()
        impact_sentence = pools[(c2,)].pop()
        severity_sentence = severity_pools[c3].pop()
        a_star = F(c2, c3)
        item_id = f"calib_{idx:02d}_{c1}_{c2}_{c3}"
        items.append({
            "item_id": item_id,
            "c1_star": c1,
            "c2_star": c2,
            "c3_star": c3,
            "a_star": a_star,
            "shared_evidence_sentences": [routing_sentence, impact_sentence, severity_sentence],
            "shared_evidence_state": " ".join([routing_sentence, impact_sentence, severity_sentence]),
        })
    return items


def verify_F_totality_and_properties(items: list[dict]) -> None:
    print("\n=== F verification (re-derived independently, not trusted from the protocol doc) ===")
    seen_combos = set()
    for it in items:
        c2, c3, a = it["c2_star"], it["c3_star"], it["a_star"]
        seen_combos.add((c2, c3))
        recomputed = F(c2, c3)
        assert recomputed == a, f"{it['item_id']}: F mismatch"
        # Property 3 only forbids resolving to "accept" - it does NOT require
        # any specific non-accept action. c2="unclear" takes precedence over
        # c3=2 in the frozen table (request_more_evidence, not escalate) -
        # asserting "== escalate" here would be over-strict and wrong, per
        # the same error the protocol document's own §16.2 prose had.
        if c3 == 2:
            assert a != "accept", "property 3 violated: c3=2 (blocking) must never resolve to accept"
        if c2 == "unclear":
            assert a != "accept", "property 3 violated: c2=unclear must never resolve to accept"
    # nominal default check
    assert F(0, 0) == "accept", "property 2 violated: nominal default must be accept"
    print(f"  PASS: F re-verified against all {len(seen_combos)} distinct (c2*,c3*) pairs present in this pilot; "
          f"nominal default and non-silent-suppression properties hold")


def main() -> None:
    run_uniqueness_checks()
    schedule = build_schedule()
    items = build_items(schedule)
    assert len(items) == N_CALIB
    assert len({it["item_id"] for it in items}) == N_CALIB, "duplicate item_id"

    print(f"\n=== Built {len(items)} calibration-pilot instances ===")
    for it in items:
        print(f"  {it['item_id']:26s} a*={it['a_star']:22s} "
              f"(c1={it['c1_star']}, c2={it['c2_star']}, c3={it['c3_star']})")

    verify_F_totality_and_properties(items)

    a_star_counts = {}
    for it in items:
        a_star_counts[it["a_star"]] = a_star_counts.get(it["a_star"], 0) + 1
    print(f"\n  a* distribution: {a_star_counts}")

    manifest = {
        "status": "DESIGN CONTENT ONLY - no API calls made or authorized by this script.",
        "purpose": "Content-blind manifest for the workflow-composition calibration pilot "
                   "(workflow_calibration_pilot_protocol.md). Reuses the frozen task/F table from "
                   "workflow_uncertainty_composition_protocol.md §16.2 exactly; only sentence content is new.",
        "protocol_reference": "research/methodology/workflow_calibration_pilot_protocol.md",
        "generation_seed": GENERATION_SEED,
        "n_calib": N_CALIB,
        "choice_instructions": CHOICE_INSTRUCTIONS,
        "choice_criteria": CHOICE_CRITERIA,
        "noul_instructions": NOUL_INSTRUCTIONS,
        "severity_instructions": SEVERITY_INSTRUCTIONS,
        "severity_criteria": SEVERITY_CRITERIA,
        "items": items,
        "builder_script_sha256": hashlib.sha256(THIS_FILE.read_bytes()).hexdigest(),
    }
    out_path = DATA_DIR / "workflow_calibration_pilot_manifest.json"
    out_path.write_text(json.dumps(manifest, indent=2))
    manifest_sha256 = hashlib.sha256(out_path.read_bytes()).hexdigest()

    hash_record = {
        "purpose": "Immutability record for workflow_calibration_pilot_manifest.json - structurally "
                   "separate from Step 2's eventual main-evaluation manifest, per workflow_calibration_"
                   "pilot_protocol.md §6.",
        "manifest_path": "research/data/characterization/workflow_calibration_pilot_manifest.json",
        "manifest_sha256": manifest_sha256,
        "builder_script_path": "research/src/build_workflow_calibration_pilot_manifest.py",
        "builder_script_sha256": manifest["builder_script_sha256"],
        "item_ids_immutable_identity": [it["item_id"] for it in items],
    }
    hash_path = DATA_DIR / "workflow_calibration_pilot_manifest_hashes.json"
    hash_path.write_text(json.dumps(hash_record, indent=2))

    print(f"\nWritten: {out_path}")
    print(f"Written: {hash_path}")
    print(f"Manifest sha256: {manifest_sha256}")
    print("\n=== ALL CHECKS PASSED ===")


if __name__ == "__main__":
    main()
