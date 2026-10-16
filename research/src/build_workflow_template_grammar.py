"""Deterministic template grammar for workflow-composition evaluation content.

Spec: research/methodology/workflow_template_grammar_spec.md (Draft 4).

Draft 4 design: every instance is ONE incident about ONE named service S.
The impact pool owns S (its claim is about S), and the routing and severity
sentences are templates with an {S} slot filled at instance assembly. So the
impact label is entailed for the very service whose infrastructure and
feature the other two sentences describe (independent review, C3).

Expands a small, finite, fully listed vocabulary and audits the expansion.
Labels come from the structured variables that built each unit (pool, value)
and are never parsed back out of text. No API calls, and no Jev involvement.
This script does not assign units to instances; it fixes which units are
reserved for the second calibration pilot and which for the main run.
"""

from __future__ import annotations

import hashlib
import itertools
import json
import random
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SRC_DIR))

import build_score_phase_b_manifest as score_bpb  # noqa: E402  (read-only: prior-text corpus)
import build_workflow_calibration_pilot_manifest as pilot1  # noqa: E402  (read-only: prior-text corpus)

REPO_ROOT = SRC_DIR.parent.parent
DATA_DIR = REPO_ROOT / "research" / "data" / "characterization"
RESULTS_DIR = REPO_ROOT / "research" / "results"
THIS_FILE = Path(__file__).resolve()

SEED = "workflow-template-grammar-v4"   # v1-v3 = Drafts 1-3

# Second calibration pilot: pilot 1's 30-instance schedule (18 cells once + 12 off-diagonal).
PILOT2_QUOTA = {("routing", "network"): 15, ("routing", "database"): 15,
                ("impact", "0"): 10, ("impact", "1"): 10, ("impact", "unclear"): 10,
                ("severity", "0"): 10, ("severity", "1"): 10, ("severity", "2"): 10}

# Capacity ceiling (Draft 4: lowered from 1,260 by decision of 2026-10-16).
# Balanced allocation N_eval = 18k needs 9k routing units per c1 value and 6k
# units per c2 / c3 value. If Revision 12 sizing needs more, the build stops.
N_MAX = 720
K_MAX = N_MAX // 18

S = "{S}"   # the instance's service, owned by the impact pool

# ===========================================================================
# Vocabulary. Every list is the complete vocabulary for its slot.
# ===========================================================================

# --- impact pool: the service S and the claim about it ---------------------
# S names must carry no routing or severity cue (they appear in all three
# sentences). Customer-facing and internal names carry their own audience
# signal, which is CONSISTENT with the label by construction; impact:unclear
# names must be audience-neutral (A10b).
S_CUSTOMER = ["the checkout service", "the storefront", "the customer portal", "the public website",
              "the sign-up flow", "the shopping-cart service", "the customer billing portal", "the help center",
              "the product search page", "the order-tracking page", "the customer mobile app", "the booking site",
              "the video player", "the customer dashboard", "the loyalty rewards app", "the gift-card store",
              "the customer messaging inbox", "the patient appointment scheduler", "the online course player",
              "the recipe app", "the customer onboarding wizard", "the subscription management page",
              "the returns portal", "the customer review pages", "the trip planner", "the photo sharing app",
              "the customer support chat", "the client e-signature portal", "the restaurant reservation app",
              "the event ticketing site", "the parcel tracking app", "the marketplace listing pages",
              "the customer feedback form", "the hotel booking app"]
S_INTERNAL = ["the nightly reconciliation job", "the internal cost dashboard", "the analytics team's reporting tool",
              "the internal support-triage tool", "the legacy metrics exporter", "the CI build runner",
              "the quarterly compliance report generator", "the internal wiki", "the employee onboarding portal",
              "the expense-approval tool", "the hackathon voting app", "the office room-booking system",
              "the engineering on-call scheduler", "the design-review tracker", "the payroll export script",
              "the staff training portal", "the internal code-search tool", "the build-artifact packager",
              "the license-compliance scanner", "the internal developer handbook site", "the team goals tracker",
              "the vendor-invoice reconciliation script", "the developer sandbox environment",
              "the internal feature-ideas board", "the hiring pipeline dashboard", "the IT hardware asset tracker",
              "the internal survey tool", "the release-notes drafting tool", "the security-awareness quiz app",
              "the finance forecasting model", "the HR question chatbot", "the laptop provisioning script",
              "the test-fixture generator", "the performance-review tool", "the code-coverage reporter",
              "the internal mailing-list digest", "the procurement form", "the dependency-update bot",
              "the internal travel-booking tool", "the static-analysis pipeline", "the badge-access audit report",
              "the UX research library", "the capacity-planning model", "the retention-policy checker",
              "the internal icon library site", "the incident postmortem collection",
              "the sales-commission calculator", "the employee directory", "the design-system playground",
              "the legal-hold tracker", "the benchmark results site", "the translation-memory tool",
              "the board-deck generator", "the brand-asset library", "the meeting-notes summarizer",
              "the engineering blog drafts site", "the parking-permit tool", "the compliance training tracker",
              "the bug-bash leaderboard", "the warehouse staff rota tool", "the grant-tracking tool",
              "the patent-disclosure tracker", "the company podcast feed", "the facilities maintenance tracker",
              "the mentoring-match tool", "the cafeteria menu site", "the hardware-loan tracker",
              "the dev-environment image builder", "the architecture-diagram library",
              "the interview-scheduling assistant",
              "the internal holiday planner", "the office supplies form", "the internal job board",
              "the staff newsletter builder", "the internal ideas portal", "the engineering metrics dashboard",
              "the internal access-approval portal", "the internal style-guide site",
              "the conference-room display app", "the staff shuttle schedule", "the internal recognition app",
              "the security-review tracker", "the vendor contract tracker", "the internal audit checklist tool",
              "the staff wellness portal", "the code-review reminder bot", "the internal tech-radar site",
              "the internal floor-plan viewer", "the team retrospective board", "the expense-policy chatbot",
              "the staff equipment form", "the internal release-train tracker",
              "the incident drill scheduler", "the internal sprint-planning board", "the onboarding buddy matcher",
              "the internal metrics catalog", "the staff phone directory", "the internal translation intake form",
              "the legal intake form", "the brand-review tracker", "the training-video library",
              "the hackathon project gallery", "the staff feedback survey", "the office temperature dashboard",
              "the internal print monitor", "the staff timesheet tool", "the certificate-renewal reminder",
              "the employee referral tracker", "the font-license register", "the staff badge photo tool",
              "the interview question bank", "the market-research library", "the pricing-approval tool",
              "the staff relocation planner", "the board-meeting minutes site", "the staff skills inventory",
              "the budget-planning tool", "the cost-center mapping tool", "the internal procurement catalog",
              "the staff learning-plan tool", "the recovery runbook site", "the design-critique scheduler",
              "the internal desk-booking app", "the engineering ladder site", "the podcast-taping scheduler",
              "the analytics sandbox", "the staff awards nomination form", "the open-source approval form",
              "the internal quiz builder", "the staff carpool board", "the internal glossary site"]
S_SHARED = ["the shared templating layer", "the message queue", "the shared auth library", "the feature-flag service",
            "the image-processing worker pool", "the geo-lookup service", "the email-template service",
            "the shared approval-rules service", "the slug-generation service", "the event fan-out service",
            "the shared logging agent", "the PDF rendering service", "the shared configuration service",
            "the A/B testing service", "the shared secrets manager", "the job scheduler", "the shared search service",
            "the spam-filtering service", "the timezone-conversion library", "the localization service",
            "the event-bus listener group", "the shared metrics library", "the audit-event emitter",
            "the document-conversion worker pool", "the barcode generation service", "the shared retry library",
            "the JSON serialization library", "the session signing service", "the analytics event collector",
            "the email-validation library", "the device registry", "the content-moderation queue",
            "the shared markdown renderer", "the license-key validation service", "the background-image optimizer",
            "the date-formatting library", "the experiment-assignment service", "the partner-integration adapter",
            "the shared spreadsheet parser", "the ranking-signals pipeline", "the message signature verifier",
            "the plural-rules library", "the feature-usage tracker", "the image-moderation classifier",
            "the phone-number formatter", "the PDF watermarking step", "the credential refresher",
            "the font-subsetting service", "the map-tile renderer", "the profanity filter", "the sitemap generator",
            "the identifier allocation service", "the calendar-availability service",
            "the shared scheduling library", "the document-tagging worker", "the shared encryption helper",
            "the shared image-cropping service", "the config-rollout service", "the shared health-check service",
            "the feature-toggle sync job", "the text-normalization library", "the workflow engine",
            "the shared rule evaluator", "the shared thumbnail service", "the shared webform builder",
            "the color-palette service"]

IMPACT_FRAMES = ["{W} reports that {claim}.", "According to {w}, {claim}.", "As {w} notes, {claim}."]  # all values; attribution first
WHO = ["the owning team", "the on-call engineer", "the platform team", "the incident commander",
       "the service catalog", "the architecture team"]

IMPACT_YES_CLAIM = "{g} customers are reporting problems with {S} through {src}"
SEGMENTS = ["enterprise", "free-tier", "EU-based", "self-serve", "paying", "newly signed-up", "long-standing", "APAC"]
SOURCES = ["support tickets", "the public status page", "live chat", "in-app feedback", "social-media posts",
           "emails to the help desk"]
IMPACT_NO_CLAIMS = ["{S} is used only by internal teams, and no customer has any access to it",
                    "no customer uses {S}, which exists only for the company's own teams",
                    "{S} serves no customers and is used only for the company's internal work",
                    "{S} runs entirely on internal-only infrastructure that customers never reach",
                    "{S} is isolated from everything customers use and has no customer-facing dependents"]
IMPACT_UNCLEAR_CLAIMS = [
    "it has not been mapped which customer-facing services, if any, depend on {S}",
    "the downstream consumers of {S} have not been fully mapped, so its customer exposure is unknown",
    "it is not yet known which customers, if any, depend on {S}",
    "it is unclear whether {S} is enabled for any customer segment",
    "nobody can currently tell whether customers use {S}, because its usage reports are no longer kept",
    "two teams disagree about whether {S} is part of any customer-facing workflow"]

# --- routing pool: S's infrastructure ---------------------------------------
ROUTING_FRAMES = ["Monitoring for {S} shows {chg} in {m} on its {c} {t}.",   # identical for network and database
                  "Alerts for {S} report {chg} in {m} at its {c} {t}.",
                  "{S_cap}'s on-call dashboard shows {chg} in {m} on its {c} {t}."]
CHANGE_NP = ["a roughly twofold increase", "a roughly threefold increase", "an approximately tenfold increase",
             "an abrupt jump", "a steady climb", "erratic fluctuations"]   # Draft 4: "a sharp spike" dropped (severity cue)
TIME = ["since this morning", "over the past hour", "since the last deploy", "since about 02:00 UTC",
        "over the last thirty minutes", "since the maintenance window ended"]
ROUTING = {
    "network": {
        "component": ["edge load balancer", "upstream DNS resolvers", "inter-region backbone link",
                      "VPN gateway between availability zones", "CDN edge nodes", "perimeter firewall",
                      "service-mesh sidecar proxies", "NAT gateway", "top-of-rack switches",
                      "regional ingress routers", "peering link to the upstream ISP",
                      "WAN link to the backup data center", "private DNS zone", "east-west network switches"],
        "metric": ["packet loss", "retransmitted packets", "round-trip latency", "connection resets",
                   "dropped connections", "interface discards", "link flaps", "connection timeouts"],
    },
    "database": {
        "component": ["primary database", "read replicas", "job-queue database", "state table",
                      "reporting database", "database connection pool", "scheduling database",
                      "permissions database", "audit-log database", "configuration database",
                      "metadata database", "search-index database", "event-history database", "backup replica"],
        "metric": ["query execution time", "slow queries", "lock wait time", "replication lag", "deadlocks",
                   "disk I/O wait", "connection-pool saturation", "transaction rollbacks"],
    },
}
# Draft 4 routing fit (review, minor): metric classes a component can show.
ROUTING_METRIC_EXCLUDED = {
    ("network", "upstream DNS resolvers"): {"interface discards", "link flaps"},
    ("network", "private DNS zone"): {"interface discards", "link flaps"},
    ("network", "service-mesh sidecar proxies"): {"interface discards", "link flaps"},
}
REPLICATION_COMPONENTS = {"primary database", "read replicas", "backup replica"}
POOL_SATURATION_COMPONENTS = {"database connection pool", "primary database"}
CONNECTION_POOL_ONLY = {"query execution time", "slow queries", "connection-pool saturation"}

# --- severity pool: S's feature and its state ------------------------------
# One frame set for all three values, and "; " as the only connective, so no
# frame, opening or punctuation mark identifies the level (review, M5).
SEVERITY_FRAMES = ["In {S}, {body}.", "Since the last release of {S}, {body}.",
                   "The incident report for {S} says that {body}."]
SEV_COSMETIC = {
    "element": ["the settings tooltip", "the sidebar icon", "the footer copyright text", "the date picker label",
                "the 'beta' badge", "the section divider", "the search placeholder text", "the email header logo",
                "the print-view page title", "the avatar border", "the primary button's hover shade",
                "the tour arrow", "the empty-state message", "the breadcrumb trail", "the settings tab label",
                "the toast message", "the list column header", "the dialog title", "the help-panel heading",
                "the loading spinner", "the card shadow", "the progress bar", "the scrollbar"],
    "defect": ["is misaligned by a few pixels", "sits one pixel off its grid", "renders in a slightly wrong color",
               "shows outdated wording", "briefly flickers on load", "wraps awkwardly onto a second line",
               "is truncated with an ellipsis", "uses inconsistent capitalization"],
    "context": ["in Safari", "in dark mode", "at 125% browser zoom", "in the German locale",
                "in high-contrast mode", "at narrow window widths"],
    "qualifier": "nothing else is affected",
}
COSMETIC_TEXT_ELEMENTS = {"the settings tooltip", "the footer copyright text", "the date picker label",
                          "the 'beta' badge", "the search placeholder text", "the print-view page title",
                          "the empty-state message", "the breadcrumb trail", "the settings tab label",
                          "the toast message", "the list column header", "the dialog title", "the help-panel heading"}
COSMETIC_TEXT_DEFECT_CLASSES = {2, 4, 5}

SEV_DEGRADED = {
    "feature": ["scheduled report exports", "bulk tag edits", "live dashboard widgets",
                "inline edits on the settings page", "keyboard search shortcuts", "document autosaves",
                "paginated list views", "scheduled email digests", "calendar syncs", "image attachments",
                "saved search alerts", "spreadsheet imports", "image thumbnail previews", "chart exports",
                "comment notifications", "file conversions", "bulk file moves", "photo gallery syncs",
                "project board updates", "contact list imports", "report schedule edits", "shared folder syncs",
                "task list refreshes", "batch image imports", "zip downloads", "note syncs",
                "activity feed updates", "spreadsheet edits"],
    "failure": ["fail intermittently", "fail on large inputs", "stall after a long session",
                "stop updating after a while", "drop recent changes occasionally", "update a few minutes late",
                "skip items now and then", "fail on the first attempt"],
    "workaround": ["retrying the action succeeds", "a page refresh restores normal behavior",
                   "the same task still works from another screen",
                   "the previous version of the feature is still available", "the task can still be run by hand",
                   "splitting the work into smaller batches succeeds", "saving by hand first prevents any loss",
                   "reopening the page shows the current state"],
}
_ANY = {"the same task still works from another screen", "the previous version of the feature is still available"}
WORKAROUND_FITS = {
    0: _ANY | {"retrying the action succeeds", "a page refresh restores normal behavior",
               "the task can still be run by hand"},
    1: _ANY | {"splitting the work into smaller batches succeeds", "the task can still be run by hand"},
    2: _ANY | {"a page refresh restores normal behavior", "reopening the page shows the current state"},
    3: _ANY | {"saving by hand first prevents any loss"},
    4: _ANY | {"reopening the page shows the current state"},
    5: _ANY | {"retrying the action succeeds", "the task can still be run by hand"},
    6: _ANY | {"retrying the action succeeds", "a page refresh restores normal behavior"},
}
FEATURE_FAILURE_FITS = {
    "scheduled report exports": {0, 1, 5, 6}, "bulk tag edits": {0, 1, 3, 5, 6},
    "live dashboard widgets": {0, 2, 4, 6}, "inline edits on the settings page": {0, 3, 6},
    "keyboard search shortcuts": {0, 6}, "document autosaves": {0, 2, 3, 6},
    "paginated list views": {0, 1, 2, 5, 6}, "scheduled email digests": {0, 4, 5, 6},
    "calendar syncs": {0, 2, 3, 4, 5, 6}, "image attachments": {0, 1, 6},
    "saved search alerts": {0, 4, 5, 6}, "spreadsheet imports": {0, 1, 5, 6},
    "image thumbnail previews": {0, 1, 2, 4, 6}, "chart exports": {0, 1, 6},
    "comment notifications": {0, 4, 5, 6}, "file conversions": {0, 1, 5, 6},
    "bulk file moves": {0, 1, 5, 6}, "photo gallery syncs": {0, 2, 3, 4, 5, 6},
    "project board updates": {0, 2, 4, 6}, "contact list imports": {0, 1, 5, 6},
    "report schedule edits": {0, 3, 6}, "shared folder syncs": {0, 2, 3, 4, 5, 6},
    "task list refreshes": {0, 2, 4, 6}, "batch image imports": {0, 1, 5, 6},
    "zip downloads": {0, 1, 6}, "note syncs": {0, 2, 3, 4, 5, 6},
    "activity feed updates": {0, 2, 4, 5, 6}, "spreadsheet edits": {0, 3, 6},
}
SEV_BLOCKING = {
    "function": ["report generation", "scheduled job execution", "report export", "notification sending",
                 "file sharing", "document signing", "PDF generation", "image resizing", "calendar sync",
                 "email delivery", "spreadsheet import", "file preview", "audit trail capture",
                 "the approval workflow", "form submission", "comment posting", "task assignment",
                 "template rendering", "attachment handling", "label printing", "text extraction",
                 "workflow automation", "event scheduling", "survey distribution", "chart rendering",
                 "dashboard refresh", "file conversion", "time tracking", "document translation",
                 "document search", "tag management", "bulk editing", "version history",
                 "task reminder delivery", "permission management", "draft saving", "thumbnail generation",
                 "image compression", "audio transcription", "subtitle generation", "summary generation",
                 "document merging", "screenshot capture", "export packaging", "page layout rendering",
                 "invoice layout", "certificate generation", "form validation", "photo editing",
                 "calendar export"],
    # Draft 4 (review C1): "stopped" and "fails on every attempt" are one claim.
    "failure": ["has stopped working entirely", "is completely unavailable", "fails on every attempt",
                "has halted with no progress", "produces unusable output every time",
                "produces garbled output every time"],
    # Draft 4 (review C2): EVERY scope filler explicitly denies any workaround.
    "scope": ["no workaround exists", "there is no workaround of any kind",
              "no workaround exists, not even doing it by hand",
              "no workaround exists, not even retrying",
              "no workaround exists, not even rolling back to the previous version"],
}
BLOCKING_OUTPUT_FUNCTIONS = {"report generation", "report export", "PDF generation", "image resizing",
                             "spreadsheet import", "file preview", "template rendering", "text extraction",
                             "chart rendering", "file conversion", "document translation", "document search",
                             "label printing", "thumbnail generation", "image compression", "audio transcription",
                             "subtitle generation", "summary generation", "document merging", "screenshot capture",
                             "export packaging", "page layout rendering", "invoice layout",
                             "certificate generation", "calendar export"}

# ===========================================================================
# Cue lexicons. _contains matches the stem plus inflections (review, M4).
# ===========================================================================

NETWORK_CUES = ["network", "latency", "packet", "dns", "router", "switch", "gateway", "firewall", "vpn",
                "cdn", "tls", "tcp", "link", "proxy", "proxies", "load balancer", "isp", "subnet", "ingress",
                "timeout", "peering", "backbone", "nat", "region", "traffic", "endpoint", "webhook", "api",
                "url", "http", "upload", "bandwidth", "throughput", "dispatcher", "request", "respond",
                "route", "path", "socket", "wan", "mesh"]
DATABASE_CUES = ["database", "query", "queries", "replica", "replication", "lock", "deadlock", "transaction",
                 "index", "table", "connection pool", "connection-pool", "disk i/o", "schema", "sql", "ledger",
                 "cache", "caching", "csv", "storage", "record", "rows", "archive", "repository", "logs",
                 "data store", "corrupt", "purge"]
SEVERITY_CUES = ["fail", "down", "broken", "outage", "unable", "error", "blocking", "workaround", "cosmetic",
                 "pixel", "unavailable", "crash", "urgent", "escalat", "surge", "spike", "burst", "critical",
                 "fallback", "halt", "stopped", "garbled", "unusable"]
AUDIENCE_CUES = ["user", "customer", "client", "public", "people", "everyone", "visitor", "member", "subscriber",
                 "consumer", "shopper", "buyer", "patient", "checkout", "cart", "login", "log in", "sign-in",
                 "sign in", "sign-on", "sign-up", "password", "account", "billing", "payment", "refund",
                 "subscription", "order", "loyalty", "support", "admin", "staff", "employee", "internal",
                 "mobile", "desktop app", "two-factor", "profile", "onboarding", "team", "engineer", "store",
                 "marketplace", "booking", "reservation", "ticket", "parcel", "shipping", "product"]
_SUFFIX = r"(?:e?s|ed|ing|ures?|ers?|ion|ions|ation|ations)?"


def _cap(s: str) -> str:
    return s[0].upper() + s[1:]


def _contains(text: str, cue: str) -> bool:
    return re.search(r"(?<![a-z])" + re.escape(cue) + _SUFFIX + r"(?![a-z])", text.lower()) is not None


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s{}]", "", text.lower())).strip()


def _mask_s(text: str) -> str:
    return text.replace("{S_cap}", " ").replace("{S}", " ")


# ===========================================================================
# Proposition signatures (spec §5). Every slot is SYN, IDENTITY or NUISANCE;
# an undeclared slot or unmapped filler stops the build.
# ===========================================================================

SYN = {
    ("routing", 1): {"packet loss": 0, "retransmitted packets": 0, "round-trip latency": 1,
                     "connection resets": 2, "dropped connections": 2, "interface discards": 3, "link flaps": 4,
                     "connection timeouts": 5,
                     "query execution time": 10, "slow queries": 10, "lock wait time": 11, "replication lag": 12,
                     "deadlocks": 13, "disk I/O wait": 14, "connection-pool saturation": 15,
                     "transaction rollbacks": 16},
    ("routing", 2): {"a roughly twofold increase": 0, "a roughly threefold increase": 1,
                     "an approximately tenfold increase": 2, "an abrupt jump": 3,
                     "a steady climb": 4, "erratic fluctuations": 5},
    ("impact:0", 1): {IMPACT_NO_CLAIMS[0]: 0, IMPACT_NO_CLAIMS[1]: 0, IMPACT_NO_CLAIMS[2]: 0,
                      IMPACT_NO_CLAIMS[3]: 1, IMPACT_NO_CLAIMS[4]: 1},
    ("impact:unclear", 1): {IMPACT_UNCLEAR_CLAIMS[0]: 0, IMPACT_UNCLEAR_CLAIMS[1]: 0, IMPACT_UNCLEAR_CLAIMS[2]: 0,
                            IMPACT_UNCLEAR_CLAIMS[3]: 1, IMPACT_UNCLEAR_CLAIMS[4]: 2, IMPACT_UNCLEAR_CLAIMS[5]: 3},
    ("severity:0", 1): {"is misaligned by a few pixels": 0, "sits one pixel off its grid": 0,
                        "renders in a slightly wrong color": 1, "shows outdated wording": 2,
                        "briefly flickers on load": 3, "wraps awkwardly onto a second line": 4,
                        "is truncated with an ellipsis": 4, "uses inconsistent capitalization": 5},
    ("severity:1", 1): {"fail intermittently": 0, "fail on large inputs": 1, "stall after a long session": 2,
                        "stop updating after a while": 2, "drop recent changes occasionally": 3,
                        "update a few minutes late": 4, "skip items now and then": 5, "fail on the first attempt": 6},
    ("severity:2", 1): {"has stopped working entirely": 0, "is completely unavailable": 0,
                        "fails on every attempt": 0, "has halted with no progress": 0,
                        "produces unusable output every time": 1, "produces garbled output every time": 1},
    ("severity:2", 2): {"no workaround exists": 0, "there is no workaround of any kind": 0,
                        "no workaround exists, not even doing it by hand": 1,
                        "no workaround exists, not even retrying": 2,
                        "no workaround exists, not even rolling back to the previous version": 3},
}
# Slot roles. impact:1's report channel is NUISANCE (not a different claim
# about S); the "who" attribution is a surface slot everywhere.
IDENTITY_SLOTS = {("routing", 0), ("impact:1", 0), ("impact:1", 1), ("impact:0", 0), ("impact:unclear", 0),
                  ("severity:0", 0), ("severity:0", 2), ("severity:1", 0), ("severity:1", 2), ("severity:2", 0)}
NUISANCE_SLOTS = {"impact:1": {2}}
SIGNATURE = {  # documentation of each slot's role, in key order
    "routing": ("S's component", "metric class", "magnitude/shape class"),
    "impact:1": ("subject: S", "affected customer segment", "NUISANCE: report channel"),
    "impact:0": ("subject: S", "claim class (internal use / internal infrastructure)"),
    "impact:unclear": ("subject: S", "unknown-aspect class"),
    "severity:0": ("UI element", "defect class", "condition: display context"),
    "severity:1": ("feature", "failure-mode class", "workaround"),
    "severity:2": ("function", "failure class", "no-workaround scope class"),
}


def _pv(pool: str, value: str) -> str:
    return pool if pool == "routing" else f"{pool}:{value}"


def _proposition_key_of(pool: str, value: str, key) -> tuple:
    pv = _pv(pool, value)
    out = []
    for i, filler in enumerate(key):
        if i in NUISANCE_SLOTS.get(pv, set()):
            continue
        if (pv, i) in SYN:
            out.append(f"class{SYN[(pv, i)][filler]}")   # KeyError = unmapped filler = fail closed
        elif (pv, i) in IDENTITY_SLOTS:
            out.append(filler)
        else:
            raise ValueError(f"undeclared signature slot {pv}[{i}]")
    return tuple(out)


def proposition_key(u: dict) -> tuple:
    return _proposition_key_of(u["pool"], u["value"], u["semantic_key"])


# ===========================================================================
# Fit predicates (combinations that make sense together).
# ===========================================================================

def routing_fits(value: str, k) -> bool:
    c, m, _ = k
    if m in ROUTING_METRIC_EXCLUDED.get((value, c), set()):
        return False
    if value == "database":
        if m == "replication lag" and c not in REPLICATION_COMPONENTS:
            return False
        if m == "connection-pool saturation" and c not in POOL_SATURATION_COMPONENTS:
            return False
        if c == "database connection pool" and m not in CONNECTION_POOL_ONLY:
            return False
    return True


def cosmetic_fits(k) -> bool:
    return SYN[("severity:0", 1)][k[1]] not in COSMETIC_TEXT_DEFECT_CLASSES or k[0] in COSMETIC_TEXT_ELEMENTS


def degraded_fits(k) -> bool:
    cls = SYN[("severity:1", 1)][k[1]]
    return cls in FEATURE_FAILURE_FITS[k[0]] and k[2] in WORKAROUND_FITS[cls]


def blocking_fits(k) -> bool:
    return SYN[("severity:2", 1)][k[1]] != 1 or k[0] in BLOCKING_OUTPUT_FUNCTIONS


# ===========================================================================
# Expansion. Each (pool, value) yields (keys, render, subject_of).
# Rendered texts keep the literal {S} / {S_cap} placeholder.
# ===========================================================================

def _routing(value: str):
    v = ROUTING[value]
    keys = [k for k in itertools.product(v["component"], v["metric"], CHANGE_NP) if routing_fits(value, k)]

    def render(key, i):
        c, m, chg = key
        t = TIME[(i // 3) % len(TIME)]
        return ROUTING_FRAMES[i % 3].format(S=S, S_cap="{S_cap}", chg=chg, m=m, c=c, t=t), \
            {"frame": i % 3, "time": t}
    return keys, render, lambda k: k[0]


def _impact_render(claim: str, i: int) -> tuple[str, dict]:
    w = WHO[(i // 3) % len(WHO)]
    return IMPACT_FRAMES[i % 3].format(W=_cap(w), w=w, claim=claim, Claim=_cap(claim)), {"frame": i % 3, "who": w}


def _impact(value: str):
    if value == "1":
        keys = list(itertools.product(S_CUSTOMER, SEGMENTS, SOURCES))

        def render(key, i):
            s, g, src = key
            return _impact_render(IMPACT_YES_CLAIM.format(g=g, S=s, src=src), i)
        return keys, render, lambda k: k[0]
    names, claims = (S_INTERNAL, IMPACT_NO_CLAIMS) if value == "0" else (S_SHARED, IMPACT_UNCLEAR_CLAIMS)
    keys = list(itertools.product(names, claims))

    def render(key, i):
        s, claim = key
        return _impact_render(claim.replace("{S}", s), i)
    return keys, render, lambda k: k[0]


def _severity(value: str):
    if value == "0":
        v = SEV_COSMETIC
        keys = [k for k in itertools.product(v["element"], v["defect"], v["context"]) if cosmetic_fits(k)]

        def body(k):
            return f"{k[0]} {k[1]} {k[2]}; {v['qualifier']}"
    elif value == "1":
        v = SEV_DEGRADED
        keys = [k for k in itertools.product(v["feature"], v["failure"], v["workaround"]) if degraded_fits(k)]

        def body(k):
            return f"{k[0]} {k[1]}; {k[2]}"
    else:
        v = SEV_BLOCKING
        keys = [k for k in itertools.product(v["function"], v["failure"], v["scope"]) if blocking_fits(k)]

        def body(k):
            return f"{k[0]} {k[1]}; {k[2]}"

    def render(key, i):
        return SEVERITY_FRAMES[i % 3].format(S=S, body=body(key)), {"frame": i % 3}
    return keys, render, lambda k: k[0]


POOLS = [("routing", "network", _routing), ("routing", "database", _routing),
         ("impact", "0", _impact), ("impact", "1", _impact), ("impact", "unclear", _impact),
         ("severity", "0", _severity), ("severity", "1", _severity), ("severity", "2", _severity)]


def check_signature_declarations() -> None:
    """Fail closed: every slot declared once; every SYN filler mapped; no stale entry."""
    for pool, value, builder in POOLS:
        pv = _pv(pool, value)
        keys, _, _ = builder(value)
        for i in range(len(keys[0])):
            roles = [(pv, i) in SYN, (pv, i) in IDENTITY_SLOTS, i in NUISANCE_SLOTS.get(pv, set())]
            if sum(roles) != 1:
                raise ValueError(f"slot {pv}[{i}] must be declared exactly once, got {roles}")
            if (pv, i) in SYN:
                fillers = {k[i] for k in keys}
                declared = set(SYN[(pv, i)])
                if pool == "routing" and i == 1:   # one SYN map serves both routing values
                    declared &= set(ROUTING[value]["metric"])
                if fillers != declared:
                    raise ValueError(f"SYN map for {pv}[{i}] does not match vocabulary: "
                                     f"unmapped {sorted(fillers - declared)}, stale {sorted(declared - fillers)}")


def expand() -> list[dict]:
    """One unit per PROPOSITION. Filler keys are shuffled with the fixed seed
    and the first key of each proposition is kept. For impact pools the pilot
    reserves whole SUBJECTS (S): every proposition about a pilot service is
    withheld from the main run. Other pools partition by proposition."""
    check_signature_declarations()
    units = []
    for pool, value, builder in POOLS:
        keys, render, subject_of = builder(value)
        shuffled = keys[:]
        random.Random(f"{SEED}:{pool}:{value}").shuffle(shuffled)
        seen, order = set(), []
        for key in shuffled:
            pk = _proposition_key_of(pool, value, key)
            if pk not in seen:
                seen.add(pk)
                order.append(key)
        quota = PILOT2_QUOTA[(pool, value)]
        if pool == "impact":
            by_subject = defaultdict(list)
            for k in order:
                by_subject[subject_of(k)].append(k)
            pilot, pilot_subjects = [], set()
            for k in order:                      # subjects in seeded order, each used fully
                sj = subject_of(k)
                if len(pilot) >= quota:
                    break
                if sj not in pilot_subjects:
                    pilot_subjects.add(sj)
                    pilot.extend(by_subject[sj][:quota - len(pilot)])
            main = [k for k in order if subject_of(k) not in pilot_subjects]
        else:
            pilot, main = order[:quota], order[quota:]
        for partition, part_keys in (("pilot2", pilot), ("main", main)):
            for i, key in enumerate(part_keys):
                text, surface = render(key, i)
                units.append({"pool": pool, "value": value, "partition": partition,
                              "semantic_key": list(key), "subject": subject_of(key),
                              "proposition_key": list(_proposition_key_of(pool, value, key)),
                              "surface": surface, "text": text})
    random.Random(f"{SEED}:ids").shuffle(units)
    for n, u in enumerate(units, 1):
        u["unit_id"] = f"g{n:05d}"          # content-blind: assigned after a global shuffle
    return units


# ===========================================================================
# Audits.
# ===========================================================================

PLURAL_OK = {"the customer review pages", "the marketplace listing pages"}


def _plural_looking(name: str) -> bool:
    last = name.split()[-1]
    return bool(re.search(r"(?<!s)s$", last))


def audit(units: list[dict]) -> dict:
    report, failures = {}, []
    by = defaultdict(list)
    for u in units:
        by[(u["pool"], u["value"])].append(u)
    names = S_CUSTOMER + S_INTERNAL + S_SHARED

    # A1 capacity: main reserve covers N_MAX under balanced allocation; pilot quota exact.
    need = {("routing", v): 9 * K_MAX for v in ("network", "database")}
    need.update({("impact", v): 6 * K_MAX for v in ("0", "1", "unclear")})
    need.update({("severity", v): 6 * K_MAX for v in ("0", "1", "2")})
    cap = Counter((u["pool"], u["value"]) for u in units if u["partition"] == "main")
    pq = Counter((u["pool"], u["value"]) for u in units if u["partition"] == "pilot2")
    report["A1_capacity"] = {f"{p}:{v}": {"main_reserve": cap[(p, v)], "needed_at_N_MAX": need[(p, v)],
                                          "pilot2": pq[(p, v)]} for (p, v) in need}
    for k, n in need.items():
        if cap[k] < n:
            failures.append(f"A1 capacity: {k} has {cap[k]} < {n}")
        if pq[k] != PILOT2_QUOTA[k]:
            failures.append(f"A1 pilot quota: {k} has {pq[k]} != {PILOT2_QUOTA[k]}")

    # A2 exact-string uniqueness (normalized, placeholder kept) and vs prior project text.
    norms = Counter(_norm(u["text"]) for u in units)
    dups = [t for t, c in norms.items() if c > 1]
    prior = set(score_bpb.L0_SENTENCES + score_bpb.L1_SENTENCES + score_bpb.L2_SENTENCES) \
        | score_bpb.PRIOR_MANIFEST_SENTENCES \
        | set(pilot1.ROUTING_NETWORK + pilot1.ROUTING_DATABASE + pilot1.IMPACT_YES + pilot1.IMPACT_NO
              + pilot1.IMPACT_UNCLEAR + pilot1.SEVERITY_COSMETIC + pilot1.SEVERITY_DEGRADED
              + pilot1.SEVERITY_BLOCKING)
    prior_overlap = {_norm(p) for p in prior} & set(norms)
    report["A2_exact_uniqueness"] = {"units": len(units), "normalized_duplicates": len(dups),
                                     "prior_corpus_size": len(prior), "overlap_with_prior": len(prior_overlap)}
    if dups:
        failures.append(f"A2 {len(dups)} normalized duplicate texts")
    if prior_overlap:
        failures.append(f"A2 {len(prior_overlap)} texts overlap prior manifests")

    # A3 proposition-key uniqueness within (pool, value); stored keys recompute.
    for k, us in by.items():
        ks = [tuple(u["proposition_key"]) for u in us]
        if len(ks) != len(set(ks)):
            failures.append(f"A3 duplicate proposition keys in {k}")
        if any(tuple(u["proposition_key"]) != proposition_key(u) for u in us):
            failures.append(f"A3 stored proposition key disagrees with recomputation in {k}")
    # A4 pilot/main disjointness: propositions and texts everywhere; SUBJECTS in impact pools.
    def keyset(part):
        return {(u["pool"], u["value"], tuple(u["proposition_key"])) for u in units if u["partition"] == part}

    def textset(part):
        return {_norm(u["text"]) for u in units if u["partition"] == part}

    def subjset(part):
        return {(u["value"], u["subject"]) for u in units if u["partition"] == part and u["pool"] == "impact"}
    report["A3_A4"] = {"pilot2_main_proposition_overlap": len(keyset("pilot2") & keyset("main")),
                       "pilot2_main_text_overlap": len(textset("pilot2") & textset("main")),
                       "pilot2_main_impact_subject_overlap": len(subjset("pilot2") & subjset("main"))}
    if any(report["A3_A4"].values()):
        failures.append(f"A4 pilot2/main overlap {report['A3_A4']}")
    if len(set(names)) != len(names):
        failures.append("A4 a service name is listed twice or in two impact values")

    # A5 routing cues: routing units carry only their own class's cues; impact and
    # severity units, and every service name, carry none.
    a5 = Counter()
    for u in units:
        t = _mask_s(u["text"])
        net = any(_contains(t, c) for c in NETWORK_CUES)
        db = any(_contains(t, c) for c in DATABASE_CUES)
        if u["pool"] == "routing":
            if not ((net and not db) if u["value"] == "network" else (db and not net)):
                a5["routing_wrong_or_missing_cue"] += 1
                failures.append(f"A5 routing cue: {u['unit_id']} {u['text']!r}")
        elif net or db:
            a5[f"{u['pool']}_contains_routing_cue"] += 1
            failures.append(f"A5 leak: {u['unit_id']} ({u['pool']}) {u['text']!r}")
    for n in names:
        if any(_contains(n, c) for c in NETWORK_CUES + DATABASE_CUES):
            a5["service_name_with_routing_cue"] += 1
            failures.append(f"A5 routing cue in service name {n!r}")
    report["A5_routing_cue_audit"] = dict(a5) or "clean"

    # A6 severity cues: none in impact or routing units, nor in any service name.
    a6 = [u for u in units if u["pool"] != "severity"
          and any(_contains(_mask_s(u["text"]), c) for c in SEVERITY_CUES)]
    a6n = [n for n in names if any(_contains(n, c) for c in SEVERITY_CUES)]
    report["A6_severity_cue_audit"] = {"non_severity_units_with_severity_cues": len(a6),
                                       "service_names_with_severity_cues": a6n,
                                       "examples": [u["text"] for u in a6[:5]]}
    failures.extend(f"A6 severity cue outside severity: {u['unit_id']} {u['text']!r}" for u in a6)
    failures.extend(f"A6 severity cue in service name {n!r}" for n in a6n)

    # A7 distribution per (pool, value, partition).
    dist = {}
    for (p, v) in PILOT2_QUOTA:
        for part in ("pilot2", "main"):
            us = [u for u in by[(p, v)] if u["partition"] == part]
            spread = []
            for slot in range(len(us[0]["semantic_key"])):
                c = Counter(u["semantic_key"][slot] for u in us)
                spread.append([min(c.values()), max(c.values())])
            dist[f"{p}:{v}:{part}"] = {"n": len(us),
                                       "frame_counts": dict(sorted(Counter(u["surface"]["frame"] for u in us).items())),
                                       "slot_min_max": spread, "distinct_subjects": len({u["subject"] for u in us})}
    report["A7_distribution"] = dist

    # A8 label provenance.
    report["A8_label_provenance"] = ("labels (pool, value) are set by the expansion loop before rendering; "
                                     "no code path reads a label back out of rendered text")

    # A9 proposition-level capacity and subject counts (informational; A1 gates capacity).
    report["A9_proposition_capacity"] = {
        f"{p}:{v}": {"units": len(by[(p, v)]), "distinct_subjects": len({u["subject"] for u in by[(p, v)]}),
                     "needed_at_N_MAX_plus_pilot": PILOT2_QUOTA[(p, v)] + (9 if p == "routing" else 6) * K_MAX}
        for (p, v) in PILOT2_QUOTA}

    # A10 audience neutrality: (a) no audience word in routing or severity text
    # outside the {S} slot; (b) impact:unclear service names are audience-neutral.
    a10 = [u for u in units if u["pool"] != "impact"
           and any(_contains(_mask_s(u["text"]), c) for c in AUDIENCE_CUES)]
    a10b = [n for n in S_SHARED if any(_contains(n, c) for c in AUDIENCE_CUES)]
    report["A10_audience_cue_audit"] = {"non_impact_units_with_audience_cues": len(a10),
                                        "shared_service_names_with_audience_cues": a10b,
                                        "examples": [u["text"] for u in a10[:5]]}
    failures.extend(f"A10 audience cue outside impact: {u['unit_id']} {u['text']!r}" for u in a10)
    failures.extend(f"A10b audience cue in impact:unclear service name {n!r}" for n in a10b)

    # A11 fit-table COVERAGE (Draft 4 relabel, review M6). The fit predicates
    # filter keys at build time, so a misfit count here could only be 0. This
    # checks that every table covers its vocabulary; whether the tables are
    # RIGHT is checked by the human review of composed instances (spec §5.6).
    tables_ok = (set(FEATURE_FAILURE_FITS) == set(SEV_DEGRADED["feature"])
                 and COSMETIC_TEXT_ELEMENTS <= set(SEV_COSMETIC["element"])
                 and BLOCKING_OUTPUT_FUNCTIONS <= set(SEV_BLOCKING["function"])
                 and all(w <= set(SEV_DEGRADED["workaround"]) for w in WORKAROUND_FITS.values())
                 and set(WORKAROUND_FITS) == set(SYN[("severity:1", 1)].values()))
    report["A11_fit_table_coverage"] = {"fit_tables_cover_vocabulary": tables_ok}
    if not tables_ok:
        failures.append("A11 fit tables do not match the vocabulary (fail closed)")

    # A12 surface form: singular subjects where singular verbs follow.
    a12 = [f"plural-looking singular subject {n!r}"
           for n in names + SEV_BLOCKING["function"] + SEV_COSMETIC["element"]
           if _plural_looking(n) and n not in PLURAL_OK]
    report["A12_surface_form"] = {"problems": len(a12), "examples": a12[:5]}
    failures.extend(f"A12 {x}" for x in a12)

    # A13 (Draft 4, review M5): no surface form identifies a value within a
    # pool. No two-word opening ({S} masked) used >= 10 times in only one value,
    # and the same connectives in every severity value.
    a13 = []
    for pool in ("routing", "impact", "severity"):
        vals = [v for (p, v) in PILOT2_QUOTA if p == pool]
        openers = {v: Counter(" ".join(_mask_s(u["text"]).split()[:2]) for u in by[(pool, v)]) for v in vals}
        for v in vals:
            for opener, n in openers[v].items():
                if n >= 10 and all(opener not in openers[w] for w in vals if w != v):
                    a13.append(f"{pool}:{v} opener {opener!r} ({n}) appears in no other value")
    sev_vals = ("0", "1", "2")
    conn = {v: {c for u in by[("severity", v)] for c in (" but ", ", and ", "; ") if c in u["text"]}
            for v in sev_vals}
    if len({frozenset(c) for c in conn.values()}) != 1:
        a13.append(f"severity connectives differ by value: {conn}")
    report["A13_value_neutral_surface"] = {"problems": len(a13), "examples": a13[:5]}
    failures.extend(f"A13 {x}" for x in a13)

    # Informational: how far LENGTH alone recovers the value (best two-cut rule).
    leng = {}
    for pool in ("impact", "severity"):
        us = [u for (p, _), lst in by.items() if p == pool for u in lst]
        vals = sorted({u["value"] for u in us})
        ls = sorted({len(u["text"]) for u in us})
        cuts = ls[::max(1, len(ls) // 60)]
        best = 0.0
        for a, b in itertools.combinations(cuts, 2):
            for perm in itertools.permutations(vals):
                acc = sum((perm[0] if len(u["text"]) < a else perm[1] if len(u["text"]) < b else perm[2])
                          == u["value"] for u in us) / len(us)
                best = max(best, acc)
        leng[pool] = {"best_two_cut_length_rule_accuracy": round(best, 3), "chance": round(1 / 3, 3),
                      "mean_length_by_value": {v: round(sum(len(u["text"]) for u in by[(pool, v)])
                                                        / len(by[(pool, v)]), 1) for v in vals}}
    report["length_cue_informational"] = leng

    report["failures"] = failures
    report["passed"] = not failures
    return report


def main() -> None:
    units = expand()
    report = audit(units)
    units_path = DATA_DIR / "workflow_template_grammar_units.json"
    units_path.write_text(json.dumps({
        "status": "Grammar expansion only - not assigned to any pilot or evaluation instance. "
                  "Texts keep the {S}/{S_cap} placeholder for the instance's service (the impact-pool subject).",
        "seed": SEED, "N_MAX": N_MAX, "pilot2_quota": {f"{p}:{v}": q for (p, v), q in PILOT2_QUOTA.items()},
        "generator_sha256": hashlib.sha256(THIS_FILE.read_bytes()).hexdigest(),
        "units": units}, indent=1))
    report["units_sha256"] = hashlib.sha256(units_path.read_bytes()).hexdigest()
    report["generator_sha256"] = hashlib.sha256(THIS_FILE.read_bytes()).hexdigest()
    (RESULTS_DIR / "workflow_template_grammar_audit.json").write_text(json.dumps(report, indent=2))

    print(f"units: {len(units)}  ->  {units_path.relative_to(REPO_ROOT)}")
    print(f"A1 capacity (main reserve / needed at N_MAX={N_MAX}):")
    for k, v in report["A1_capacity"].items():
        subj = report["A9_proposition_capacity"][k]["distinct_subjects"]
        print(f"   {k:18s} {v['main_reserve']:4d} / {v['needed_at_N_MAX']}   pilot {v['pilot2']}   subjects {subj}")
    for key in ("A2_exact_uniqueness", "A3_A4", "A5_routing_cue_audit", "A11_fit_table_coverage"):
        print(key, report[key])
    for key in ("A6_severity_cue_audit", "A10_audience_cue_audit", "A12_surface_form", "A13_value_neutral_surface"):
        print(key, {k: v for k, v in report[key].items() if k != "examples"})
    print("length cue (informational)", report["length_cue_informational"])
    print(f"\nFAILURES: {len(report['failures'])}")
    for f in report["failures"][:30]:
        print("  -", f)
    print("\nPASSED" if report["passed"] else "\nNOT PASSED")


if __name__ == "__main__":
    main()
