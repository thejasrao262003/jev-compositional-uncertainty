"""Deterministic template grammar for workflow-composition evaluation content.

Spec: research/methodology/workflow_template_grammar_spec.md.

Expands a small, finite, fully listed vocabulary into evidence sentences
and audits the expansion. Labels come from the structured variables that
built each sentence (pool, value) and are never parsed back out of the
text. No API calls, and no Jev involvement in any text.

This script EXPANDS and AUDITS the grammar only. It does not assign
sentences to pilot or evaluation instances: it only fixes which semantic
keys are reserved for the second calibration pilot and which for the
main run.
"""

from __future__ import annotations

import hashlib
import itertools
import json
import random
import re
import sys
from collections import Counter
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SRC_DIR))

import build_score_phase_b_manifest as score_bpb  # noqa: E402  (read-only: prior-text corpus)
import build_workflow_calibration_pilot_manifest as pilot1  # noqa: E402  (read-only: prior-text corpus)

REPO_ROOT = SRC_DIR.parent.parent
DATA_DIR = REPO_ROOT / "research" / "data" / "characterization"
RESULTS_DIR = REPO_ROOT / "research" / "results"
THIS_FILE = Path(__file__).resolve()

SEED = "workflow-template-grammar-v3"   # Draft 3; v1 = Draft 1, v2 = Draft 2

# Second calibration pilot uses pilot 1's 30-instance schedule
# (18 cells once + 12 off-diagonal), so it needs these units per value.
PILOT2_QUOTA = {("routing", "network"): 15, ("routing", "database"): 15,
                ("impact", "0"): 10, ("impact", "1"): 10, ("impact", "unclear"): 10,
                ("severity", "0"): 10, ("severity", "1"): 10, ("severity", "2"): 10}

# Capacity ceiling. Balanced allocation uses N_eval = 18k, needing 9k routing
# units per c1 value and 6k units per c2 / c3 value.
N_MAX = 1260          # k = 70; covers n_required up to d_template ~= 0.40
K_MAX = N_MAX // 18

# ---------------------------------------------------------------------------
# Vocabulary. Every list below is the complete vocabulary for its slot.
# ---------------------------------------------------------------------------

CHANGE_NP = ["a roughly twofold increase", "a roughly threefold increase",
             "an approximately tenfold increase", "a sharp spike", "a steady climb",
             "an abrupt jump", "erratic fluctuations"]
TIME = ["since this morning", "over the past hour", "since the last deploy",
        "since about 02:00 UTC", "over the last thirty minutes", "since the maintenance window ended"]
ROUTING_FRAMES = ["Alerts for {c} show {chg} in {m} {t}.",
                  "Monitoring shows {chg} in {m} on {c} {t}.",
                  "The on-call dashboard reports {chg} in {m} at {c} {t}."]

ROUTING = {
    "network": {
        "component": ["the edge load balancer", "the core switch in the primary data center",
                      "the inter-region backbone link", "the VPN gateway between availability zones",
                      "the private DNS resolvers", "the CDN edge nodes in the affected region",
                      "the perimeter firewall", "the service-mesh sidecar proxies",
                      "the NAT gateway for the private subnets", "the top-of-rack switches in row C",
                      "the regional ingress routers", "the peering link to the upstream ISP",
                      "the WAN link to the backup data center", "the anycast DNS edge"],
        "metric": ["packet loss", "round-trip latency", "connection resets", "retransmitted packets",
                   "dropped connections", "interface errors", "link flaps", "connection timeouts"],
    },
    "database": {
        # Draft 3: audience-coded names replaced (user-accounts, billing, orders,
        # payments, loyalty-program) so routing sentences carry no customer cue.
        "component": ["the primary database", "the read replicas", "the jobs database cluster",
                      "the session-state table", "the reporting database", "the primary's connection pool",
                      "the scheduling database", "the permissions database", "the inventory database",
                      "the audit-log database", "the product-catalog database", "the general-ledger database",
                      "the shipping database", "the configuration database"],
        "metric": ["query execution time", "lock wait time", "replication lag", "deadlocks", "disk I/O wait",
                   "connection-pool saturation", "slow queries", "transaction rollbacks"],
    },
}

IMPACT_YES = {
    # Draft 3: every source is a singular noun phrase customers send, with no
    # inner "from", so frames agree in number and never repeat "from".
    "source": ["a surge of support tickets", "a wave of replies on the public status page",
               "a wave of escalations through their account managers", "a wave of social-media posts",
               "a burst of live-chat messages", "a surge of in-app feedback submissions",
               "a burst of urgent pages via their own on-call teams"],
    "segment": ["enterprise", "free-tier", "EU-based", "mobile-app", "self-serve", "healthcare",
                "retail", "APAC"],
    # Draft 3: every surface is a page or screen ("the issue on X" reads naturally);
    # "the public API" and "file uploads" removed (network-leaning words).
    "surface": ["the checkout page", "the login screen", "the main dashboard", "the developer portal",
                "the billing pages", "the search page", "the notifications page", "the file manager"],
    "frames": ["{G} customers have sent {s} about the issue on {f}.",
               "Over the past hour, {g} customers have sent {s} about the issue on {f}.",
               "Since this morning, {g} customers have been sending {s} about the issue on {f}."],
}
IMPACT_NO = {
    "component": ["the nightly reconciliation job", "the internal cost dashboard", "the staging cluster",
                  "the analytics team's ad-hoc reporting tool", "the internal support-triage tool",
                  "the legacy metrics exporter", "the CI build runner", "the quarterly compliance report generator",
                  "the internal wiki", "the employee onboarding portal", "the expense-approval tool",
                  "the hackathon voting app", "the office room-booking system", "the engineering on-call scheduler",
                  "the design-review tracker", "the payroll export script", "the staff training portal",
                  "the internal code-search tool", "the build-artifact packager", "the license-compliance scanner",
                  "the internal developer handbook site", "the team goals tracker",
                  "the vendor-invoice reconciliation script", "the developer sandbox environment",
                  "the internal feature-request board", "the hiring pipeline dashboard",
                  "the IT hardware asset tracker", "the internal survey tool", "the release-notes drafting tool",
                  "the security-awareness quiz app", "the finance forecasting model",
                  "the HR question chatbot", "the laptop provisioning script", "the test-fixture generator",
                  "the performance-review tool", "the code-coverage reporter", "the internal mailing-list digest",
                  "the procurement request form", "the dependency-update bot", "the internal travel-booking tool",
                  "the static-analysis pipeline", "the badge-access audit report", "the UX research library",
                  "the capacity-planning model", "the retention-policy checker", "the internal icon library site",
                  "the incident postmortem collection", "the sales-commission calculator", "the employee directory",
                  "the design-system playground", "the legal-hold tracker", "the benchmark results site",
                  "the translation-memory tool", "the board-deck generator", "the brand-asset library",
                  "the meeting-notes summarizer", "the engineering blog drafts site", "the visitor sign-in kiosk",
                  "the parking-permit tool", "the compliance training tracker", "the bug-bash leaderboard",
                  "the warehouse staff rota tool", "the grant-tracking tool", "the patent-disclosure tracker",
                  "the company podcast feed", "the facilities maintenance tracker", "the mentoring-match tool",
                  "the cafeteria menu site", "the hardware-loan tracker", "the dev-environment image builder",
                  "the architecture-diagram library", "the interview-scheduling assistant"],
    "evidence": ["{c} is used only by internal teams", "no customer-facing service depends on {c}",
                 "{c} serves no production customers", "{c} is isolated from the customer-serving cluster",
                 "{c} only produces output that no customer ever sees",
                 "{c} runs entirely on internal-only infrastructure",
                 "{c} has no dependency path to any customer product",
                 "{c} contains only synthetic test fixtures",
                 "{c} is excluded from every customer-facing service-level agreement"],
    "who": ["the owning team", "the platform team", "the on-call SRE", "the service catalog",
            "the architecture review record", "the dependency map", "the team lead", "a recent access review"],
    "frames": ["{W} confirms that {e}.", "According to {w}, {e}.", "{E}, as {w} has confirmed."],
}
IMPACT_UNCLEAR = {
    "component": ["the shared templating layer", "the message queue", "the shared auth library",
                  "the feature-flag service", "the image-processing worker pool", "the pricing-rules service",
                  "the geo-lookup service", "the email-template service",
                  "the shared approval-rules service", "the slug-generation service", "the event fan-out service",
                  "the shared logging agent", "the PDF rendering service", "the currency-conversion service",
                  "the address-validation service", "the shared configuration service", "the A/B testing service",
                  "the recommendation engine", "the tax-calculation library", "the shared secrets manager",
                  "the job scheduler", "the shared search service", "the spam-filtering service",
                  "the timezone-conversion library", "the localization service", "the event-bus consumer group",
                  "the shared metrics client library", "the audit-event emitter", "the document-conversion worker pool",
                  "the barcode generation service", "the shared retry library", "the user-preferences service",
                  "the fraud-scoring model", "the JSON serialization library", "the session signing service",
                  "the analytics event collector", "the email-validation library", "the device registry",
                  "the content-moderation queue", "the shared avatar service", "the coupon-validation service",
                  "the delivery-estimate service", "the shared markdown renderer", "the license-key validation service",
                  "the background-image optimizer", "the date-formatting library", "the experiment-assignment service",
                  "the partner-integration adapter", "the shared spreadsheet parser", "the ranking-signals pipeline",
                  "the profile-enrichment service", "the shared captcha service", "the message signature verifier",
                  "the order-status poller", "the plural-rules library", "the feature-usage tracker",
                  "the image-moderation classifier", "the phone-number formatter", "the shipping-rate calculator",
                  "the referral-credit service", "the PDF watermarking step", "the loyalty-points service",
                  "the credential refresher", "the receipt-generation service", "the font-subsetting service",
                  "the map-tile renderer", "the profanity filter", "the subscription-entitlement checker",
                  "the sitemap generator", "the identifier allocation service", "the price-history service",
                  "the gift-card balance service", "the attachment virus scanner", "the calendar-availability service"],
    "aspect": ["it has not been confirmed whether any customer-facing service depends on {c}",
               "the downstream consumers of {c} have not been fully mapped",
               "whether failures in {c} reach customers depends on a fallback whose status is unknown",
               "the customer exposure of {c} has been undocumented since an ownership change",
               "it is unclear whether {c} is enabled for any customer segment",
               "the dependency graph covering {c} has not been updated since a large refactor, so its customer exposure is unknown",
               "it is not yet known which customers, if any, depend on {c}",
               "the usage history that would show whether customers use {c} has already been purged",
               "two teams disagree about whether {c} is part of any customer-facing workflow"],
    "who": ["the on-call engineer", "the owning team", "the platform team", "the SRE lead",
            "the incident commander", "the service catalog", "the architecture team", "the support liaison"],
    "frames": ["{W} reports that {a}.", "According to {w}, {a}.", "{A}, and {w} could not confirm either way."],
}

# Draft 3: severity sentences are AUDIENCE-NEUTRAL. They say nothing about who
# is affected (no "users report", "a user noticed", "every user"), and their
# subjects could belong to an internal tool or a customer product. Whether the
# incident is customer-facing is stated only by the impact sentence (A10).
SEV_COSMETIC = {
    "element": ["the settings tooltip", "the sidebar icon", "the footer copyright text", "the date picker label",
                "the 'beta' badge", "the section divider", "the search placeholder text",
                "the email header logo", "the print-view page title", "the avatar border",
                "the primary button's hover shade", "the tour arrow",
                # Draft 3 additions (text-bearing, then visual-only)
                "the empty-state message", "the breadcrumb trail", "the settings tab label", "the toast message",
                "the list column header", "the dialog title", "the help-panel heading",
                "the loading spinner", "the card shadow", "the progress bar", "the scrollbar"],
    "defect": ["is misaligned by a few pixels", "renders in a slightly wrong color", "shows outdated wording",
               "sits one pixel off its grid", "briefly flickers on load", "wraps awkwardly onto a second line",
               "uses inconsistent capitalization", "is truncated with an ellipsis"],
    "context": ["in Safari", "in dark mode", "at 125% browser zoom", "in the German locale",
                "on narrow mobile screens", "in high-contrast mode"],
    "frames": ["{E} {d} {x}.", "{X}, {e} {d}.", "A design review found that {e} {d} {x}."],
}
SEV_DEGRADED = {
    "feature": ["scheduled report exports", "bulk tag edits", "live dashboard widgets",
                "inline edits on the settings page", "keyboard search shortcuts", "document autosaves",
                "paginated list views", "scheduled email digests", "calendar syncs",
                "image attachments", "saved search alerts", "spreadsheet imports", "image thumbnail previews",
                "chart exports", "comment notifications", "file conversions",
                "bulk file moves", "photo gallery syncs", "project board updates", "contact list imports",
                "report schedule edits", "shared folder syncs", "task list refreshes", "batch image imports",
                "zip downloads", "note syncs", "activity feed updates", "spreadsheet edits"],
    "failure": ["fail intermittently", "fail on large inputs", "stall after a long session",
                "drop recent changes occasionally", "update a few minutes late", "skip items now and then",
                "fail on the first attempt", "stop updating after a while"],
    "workaround": ["but retrying the action succeeds", "but a page refresh restores normal behavior",
                   "but the same task still works through the desktop app",
                   "but the previous version of the feature is still available",
                   "but the task can still be run manually",
                   "but splitting the work into smaller batches succeeds",
                   "but saving manually first prevents any loss",
                   "but reopening the page shows the current state"],
    "frames": ["{F} {r}, {w}.", "Testing shows that {f} {r}, {w}.", "Since the last release, {f} {r}, {w}."],
}
# Draft 3: text defects (outdated wording, wrapping/truncation, capitalization;
# defect classes 2, 4, 5) apply only to elements that carry text.
COSMETIC_TEXT_ELEMENTS = {"the settings tooltip", "the footer copyright text", "the date picker label",
                          "the 'beta' badge", "the search placeholder text", "the print-view page title",
                          "the empty-state message", "the breadcrumb trail", "the settings tab label",
                          "the toast message", "the list column header", "the dialog title", "the help-panel heading"}
COSMETIC_TEXT_DEFECT_CLASSES = {2, 4, 5}

# Draft 3: which failure classes (SYN severity:1) a feature can plausibly show.
# 0 intermittent and 6 first-attempt fit everything; 1 large inputs needs an
# input; 2 stall needs a long-running view or sync; 3 losing changes needs
# editing; 4 lateness and 5 skipping need a stream of items.
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

# Draft 3: "unusable/corrupted output" (failure class 2, SYN severity:2) applies
# only to functions that produce output.
BLOCKING_OUTPUT_FUNCTIONS = {"report generation", "report export", "PDF generation", "image resizing",
                             "spreadsheet import", "file preview", "template rendering", "text extraction",
                             "chart rendering", "file conversion", "document translation", "document search",
                             "label printing", "thumbnail generation", "image compression", "audio transcription",
                             "subtitle generation", "summary generation", "document merging", "screenshot capture",
                             "export packaging", "page layout rendering"}

# Draft 3: a degraded sentence is built only when its workaround actually
# addresses its failure (keyed by failure class, SYN below). Without this, 15%
# of level-1 sentences stated a "workaround" that didn't work around anything.
WORKAROUND_FITS = {
    0: {"but retrying the action succeeds", "but a page refresh restores normal behavior",
        "but the same task still works through the desktop app",
        "but the previous version of the feature is still available", "but the task can still be run manually"},
    1: {"but splitting the work into smaller batches succeeds", "but the same task still works through the desktop app",
        "but the previous version of the feature is still available", "but the task can still be run manually"},
    2: {"but a page refresh restores normal behavior", "but reopening the page shows the current state",
        "but the same task still works through the desktop app",
        "but the previous version of the feature is still available"},
    3: {"but saving manually first prevents any loss", "but the same task still works through the desktop app",
        "but the previous version of the feature is still available"},
    4: {"but reopening the page shows the current state", "but the same task still works through the desktop app",
        "but the previous version of the feature is still available"},
    5: {"but retrying the action succeeds", "but the task can still be run manually",
        "but the same task still works through the desktop app",
        "but the previous version of the feature is still available"},
    6: {"but retrying the action succeeds", "but a page refresh restores normal behavior",
        "but the same task still works through the desktop app",
        "but the previous version of the feature is still available"},
}
SEV_BLOCKING = {
    "function": ["report generation", "scheduled job execution", "report export", "notification sending",
                 "file sharing", "document signing", "PDF generation", "image resizing", "calendar sync",
                 "email delivery", "spreadsheet import", "file preview", "audit trail recording",
                 "the approval workflow", "form submission", "comment posting", "task assignment",
                 "template rendering", "attachment handling", "label printing", "text extraction",
                 "workflow automation", "event scheduling", "survey distribution", "chart rendering",
                 "dashboard refresh", "file conversion", "time tracking", "document translation",
                 "document search", "tag management", "bulk editing", "version history",
                 "task reminder delivery", "permission management", "draft saving",
                 "thumbnail generation", "image compression", "audio transcription", "subtitle generation",
                 "summary generation", "document merging", "screenshot capture", "export packaging",
                 "page layout rendering"],
    "failure": ["has stopped working entirely", "is completely unavailable", "has halted with no progress",
                "no longer responds at all", "is returning errors for every request",
                "rejects every request it receives", "is failing on every attempt",
                "fails immediately on every attempt", "produces unusable output on every run",
                "returns corrupted results every time"],
    "scope": ["and no workaround exists", "and there is no fallback path",
              "and no alternative route is available", "and it cannot be completed manually either",
              "and retrying does not help", "and the previous version cannot be restored either"],
    "frames": ["{F} {r}, {s}.", "Right now {f} {r}, {s}.", "As of this morning, {f} {r}, {s}."],
}

# ---------------------------------------------------------------------------
# Cue lexicons for the contamination audits.
# ---------------------------------------------------------------------------

NETWORK_CUES = ["network", "latency", "packet", "dns", "router", "switch", "gateway", "firewall", "vpn",
                "cdn", "tls", "tcp", "link", "proxy", "proxies", "load balancer", "isp", "subnet", "ingress",
                "timeout", "peering", "backbone", "nat",
                # Draft 3 additions: network-leaning words the Draft 2 review found outside routing
                "region", "traffic", "endpoint", "request path", "webhook", "api", "url", "http", "upload",
                "bandwidth", "throughput", "dispatcher"]
DATABASE_CUES = ["database", "query", "queries", "replica", "replication", "lock", "deadlock",
                 "transaction", "index", "table", "connection pool", "connection-pool", "disk i/o",
                 "schema", "sql", "ledger",
                 # Draft 3 additions: storage-leaning words the Draft 2 review found outside routing
                 "cache", "caching", "csv", "storage", "records", "rows", "archive", "archiver", "repository",
                 "logs", "data store"]
# Draft 3 (A10): who-is-affected words. Allowed ONLY in impact sentences, which
# alone carry c2*. A routing or severity sentence containing one would leak
# customer-facing evidence into the noul node, which reads all three sentences.
AUDIENCE_CUES = ["user", "customer", "client", "public", "people", "everyone", "visitor", "member",
                 "subscriber", "consumer", "shopper", "buyer", "checkout", "cart", "login", "log in", "sign-in",
                 "sign in", "sign-on", "password", "account", "billing", "payment", "invoice", "refund",
                 "subscription", "order", "loyalty", "support", "admin", "staff", "employee", "internal",
                 "mobile app", "two-factor", "profile", "onboarding"]
SEVERITY_CUES = ["fail", "down", "broken", "outage", "unable", "error", "blocking", "workaround",
                 "cosmetic", "pixel", "unavailable", "crash"]


def _cap(s: str) -> str:
    return s[0].upper() + s[1:]


def _contains(text: str, cue: str) -> bool:
    return re.search(r"(?<![a-z])" + re.escape(cue) + r"(?:e?s)?(?![a-z])", text.lower()) is not None


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", "", text.lower())).strip()


# ---------------------------------------------------------------------------
# Expansion. Each (pool, value) yields a list of (semantic_key, n_frames, render_fn).
# ---------------------------------------------------------------------------

def _routing_keys(value: str):
    v = ROUTING[value]
    keys = list(itertools.product(v["component"], v["metric"], CHANGE_NP))

    def render(key, i):
        c, m, chg = key
        frame = ROUTING_FRAMES[i % len(ROUTING_FRAMES)]
        t = TIME[(i // len(ROUTING_FRAMES)) % len(TIME)]
        return frame.format(C=_cap(c), c=c, chg=chg, m=m, t=t), {"frame": i % len(ROUTING_FRAMES), "time": t}
    return keys, render


def _impact_keys(value: str):
    if value == "1":
        v = IMPACT_YES
        keys = list(itertools.product(v["source"], v["segment"], v["surface"]))

        def render(key, i):
            s, g, f = key
            fr = v["frames"][i % 3]
            return fr.format(s=s, S=_cap(s), g=g, G=_cap(g), f=f), {"frame": i % 3}
        return keys, render
    v = IMPACT_NO if value == "0" else IMPACT_UNCLEAR
    slot = "evidence" if value == "0" else "aspect"
    keys = list(itertools.product(v["component"], v[slot], v["who"]))

    def render(key, i):
        c, clause, w = key
        body = clause.format(c=c)
        fr = v["frames"][i % 3]
        return fr.format(W=_cap(w), w=w, e=body, E=_cap(body), a=body, A=_cap(body)), {"frame": i % 3}
    return keys, render


def cosmetic_fits(k) -> bool:
    return SYN[("severity:0", 1)][k[1]] not in COSMETIC_TEXT_DEFECT_CLASSES or k[0] in COSMETIC_TEXT_ELEMENTS


def degraded_fits(k) -> bool:
    cls = SYN[("severity:1", 1)][k[1]]
    return cls in FEATURE_FAILURE_FITS[k[0]] and k[2] in WORKAROUND_FITS[cls]


def blocking_fits(k) -> bool:
    return SYN[("severity:2", 1)][k[1]] != 2 or k[0] in BLOCKING_OUTPUT_FUNCTIONS


def _severity_keys(value: str):
    if value == "0":
        v = SEV_COSMETIC
        keys = [k for k in itertools.product(v["element"], v["defect"], v["context"]) if cosmetic_fits(k)]

        def render(key, i):
            e, d, x = key
            fr = v["frames"][i % 3]
            return fr.format(E=_cap(e), e=e, d=d, x=x, X=_cap(x)), {"frame": i % 3}
        return keys, render
    v = SEV_DEGRADED if value == "1" else SEV_BLOCKING
    a, b, c_ = ("feature", "failure", "workaround") if value == "1" else ("function", "failure", "scope")
    keys = list(itertools.product(v[a], v[b], v[c_]))
    keys = [k for k in keys if (degraded_fits(k) if value == "1" else blocking_fits(k))]

    def render(key, i):
        f, r, w = key
        fr = v["frames"][i % 3]
        return fr.format(F=_cap(f), f=f, r=r, w=w, s=w), {"frame": i % 3}
    return keys, render


POOLS = [("routing", "network", _routing_keys), ("routing", "database", _routing_keys),
         ("impact", "0", _impact_keys), ("impact", "1", _impact_keys), ("impact", "unclear", _impact_keys),
         ("severity", "0", _severity_keys), ("severity", "1", _severity_keys), ("severity", "2", _severity_keys)]


def expand() -> list[dict]:
    """Draft 2 (Option A): one unit per PROPOSITION. All filler keys are
    expanded and shuffled with the fixed seed; the first key of each
    proposition class is kept, so paraphrases are spread across different
    propositions instead of restating one."""
    check_signature_declarations()
    units = []
    for pool, value, builder in POOLS:
        keys, render = builder(value)
        shuffled = keys[:]
        random.Random(f"{SEED}:{pool}:{value}").shuffle(shuffled)
        seen, order = set(), []
        for key in shuffled:
            pk = _proposition_key_of(pool, value, key)
            if pk not in seen:
                seen.add(pk)
                order.append(key)
        quota = PILOT2_QUOTA[(pool, value)]
        for partition, part_keys in (("pilot2", order[:quota]), ("main", order[quota:])):
            for i, key in enumerate(part_keys):
                text, surface = render(key, i)
                units.append({"pool": pool, "value": value, "partition": partition,
                              "semantic_key": list(key),
                              "proposition_key": list(_proposition_key_of(pool, value, key)),
                              "surface": surface, "text": text})
    random.Random(f"{SEED}:ids").shuffle(units)
    for n, u in enumerate(units, 1):
        u["unit_id"] = f"g{n:05d}"          # content-blind: assigned after a global shuffle
    return units


# ---------------------------------------------------------------------------
# Audits.
# ---------------------------------------------------------------------------

def audit(units: list[dict]) -> dict:
    report, failures = {}, []

    # A1 capacity: main reserve must cover N_MAX under balanced allocation.
    need = {("routing", v): 9 * K_MAX for v in ("network", "database")}
    need.update({("impact", v): 6 * K_MAX for v in ("0", "1", "unclear")})
    need.update({("severity", v): 6 * K_MAX for v in ("0", "1", "2")})
    cap = Counter((u["pool"], u["value"]) for u in units if u["partition"] == "main")
    report["A1_capacity"] = {f"{p}:{v}": {"main_reserve": cap[(p, v)], "needed_at_N_MAX": need[(p, v)]}
                             for (p, v) in need}
    for k, n in need.items():
        if cap[k] < n:
            failures.append(f"A1 capacity: {k} has {cap[k]} < {n}")

    # A2 exact-string uniqueness (normalized) across all units and against all prior project text.
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

    # A3 PROPOSITION-key uniqueness within each (pool, value) - gating since
    # Draft 2 (Option A) - and A4 pilot2/main disjointness at proposition level.
    for (p, v) in PILOT2_QUOTA:
        ks = [tuple(u["proposition_key"]) for u in units if (u["pool"], u["value"]) == (p, v)]
        if len(ks) != len(set(ks)):
            failures.append(f"A3 duplicate proposition keys in {p}:{v}")
        if any(tuple(u["proposition_key"]) != _proposition_key_of(p, v, u["semantic_key"])
               for u in units if (u["pool"], u["value"]) == (p, v)):
            failures.append(f"A3 stored proposition key disagrees with recomputation in {p}:{v}")
    pilot_keys = {(u["pool"], u["value"], tuple(u["proposition_key"])) for u in units if u["partition"] == "pilot2"}
    main_keys = {(u["pool"], u["value"], tuple(u["proposition_key"])) for u in units if u["partition"] == "main"}
    pilot_texts = {_norm(u["text"]) for u in units if u["partition"] == "pilot2"}
    main_texts = {_norm(u["text"]) for u in units if u["partition"] == "main"}
    report["A3_A4"] = {"proposition_keys_unique_within_pool_value": not any(f.startswith("A3") for f in failures),
                       "pilot2_main_key_overlap": len(pilot_keys & main_keys),
                       "pilot2_main_text_overlap": len(pilot_texts & main_texts)}
    if pilot_keys & main_keys or pilot_texts & main_texts:
        failures.append("A4 pilot2/main overlap")

    # A5 routing-cue audit: routing sentences carry only their own class's cues;
    # impact and severity sentences carry no routing cues at all.
    a5 = Counter()
    for u in units:
        net = any(_contains(u["text"], c) for c in NETWORK_CUES)
        db = any(_contains(u["text"], c) for c in DATABASE_CUES)
        if u["pool"] == "routing":
            ok = (net and not db) if u["value"] == "network" else (db and not net)
            if not ok:
                a5["routing_wrong_or_missing_cue"] += 1
                failures.append(f"A5 routing cue: {u['unit_id']} {u['text']!r}")
        elif net or db:
            a5[f"{u['pool']}_contains_routing_cue"] += 1
            failures.append(f"A5 leak: {u['unit_id']} ({u['pool']}) {u['text']!r}")
    report["A5_routing_cue_audit"] = dict(a5) or "clean"

    # A6 severity-cue audit: impact sentences must not assert functional severity.
    leaks = [u for u in units if u["pool"] == "impact" and any(_contains(u["text"], c) for c in SEVERITY_CUES)]
    report["A6_impact_severity_cue_audit"] = {"impact_units_with_severity_cues": len(leaks),
                                              "examples": [u["text"] for u in leaks[:5]]}
    for u in leaks:
        failures.append(f"A6 severity cue in impact: {u['unit_id']} {u['text']!r}")

    # A7 distribution: per (pool, value, partition) counts, frame balance, and slot-filler balance.
    dist = {}
    for (p, v) in PILOT2_QUOTA:
        for part in ("pilot2", "main"):
            us = [u for u in units if (u["pool"], u["value"], u["partition"]) == (p, v, part)]
            frames = Counter(u["surface"]["frame"] for u in us)
            slot_spread = []
            for slot in range(3):
                c = Counter(u["semantic_key"][slot] for u in us)
                slot_spread.append([min(c.values()), max(c.values())])
            dist[f"{p}:{v}:{part}"] = {"n": len(us), "frame_counts": dict(sorted(frames.items())),
                                       "slot_min_max": slot_spread}
    report["A7_distribution"] = dist

    # A8 label provenance: every label is a generator variable, never parsed from text.
    report["A8_label_provenance"] = ("labels (pool, value) are set by the expansion loop before rendering; "
                                     "no code path reads a label back out of rendered text")

    # A10 (Draft 3) audience neutrality: no who-is-affected word outside impact.
    a10 = [u for u in units if u["pool"] != "impact" and any(_contains(u["text"], c) for c in AUDIENCE_CUES)]
    report["A10_audience_cue_audit"] = {"non_impact_units_with_audience_cues": len(a10),
                                        "examples": [u["text"] for u in a10[:5]]}
    for u in a10:
        failures.append(f"A10 audience cue outside impact: {u['unit_id']} {u['text']!r}")

    # A11 (Draft 3) slot fit: cosmetic text defects only on text elements;
    # degraded failures fit the feature and workarounds fit the failure;
    # "unusable output" only for output-producing functions.
    fit = {"0": cosmetic_fits, "1": degraded_fits, "2": blocking_fits}
    a11 = [u for u in units if u["pool"] == "severity" and not fit[u["value"]](u["semantic_key"])]
    tables_ok = (set(FEATURE_FAILURE_FITS) == set(SEV_DEGRADED["feature"])
                 and COSMETIC_TEXT_ELEMENTS <= set(SEV_COSMETIC["element"])
                 and BLOCKING_OUTPUT_FUNCTIONS <= set(SEV_BLOCKING["function"]))
    report["A11_slot_fit"] = {"misfit_units": len(a11), "fit_tables_cover_vocabulary": tables_ok}
    if not tables_ok:
        failures.append("A11 fit tables do not match the vocabulary (fail closed)")
    for u in a11:
        failures.append(f"A11 slot misfit: {u['unit_id']} {u['text']!r}")

    # A12 (Draft 3) surface form: singular subjects where frames use singular
    # verbs, one "from" per impact:1 sentence, no doubled time reference.
    a12 = []
    singular_subject_pools = [IMPACT_NO["component"], IMPACT_UNCLEAR["component"], SEV_BLOCKING["function"]]
    for lst in singular_subject_pools:
        for c in lst:
            if re.search(r"(?<!s)s$", c.split()[-1]) and c not in SINGULAR_EXCEPTIONS:
                a12.append(f"plural-looking singular-slot subject {c!r}")
    for u in units:
        if (u["pool"], u["value"]) == ("impact", "1") and u["text"].count(" from ") > 1:
            a12.append(f"double 'from': {u['text']!r}")
        if len(re.findall(r"since (?:the|this|about)|as of this morning", u["text"].lower())) > 1:
            a12.append(f"doubled time reference: {u['text']!r}")
    report["A12_surface_form"] = {"problems": len(a12), "examples": a12[:5]}
    failures.extend(f"A12 {x}" for x in a12)

    report["failures"] = failures
    report["passed"] = not failures
    return report


# Singular-slot subjects that end in "s" but are grammatically singular
SINGULAR_EXCEPTIONS = {"the internal cost dashboard"}


# ---------------------------------------------------------------------------
# A9 (informational): proposition-level capacity. Label-paraphrase slots are
# mapped to synonym classes; nuisance slots (frame, time, "who confirmed")
# are dropped. Two units with the same proposition key say the same thing.
# ---------------------------------------------------------------------------

SYN = {
    ("routing", 2): {"a roughly twofold increase": 0, "a roughly threefold increase": 1,
                     "an approximately tenfold increase": 2, "a sharp spike": 3, "an abrupt jump": 3,
                     "a steady climb": 4, "erratic fluctuations": 5},
    ("impact:0", 1): {"{c} is used only by internal teams": 0, "no customer-facing service depends on {c}": 1,
                      "{c} serves no production customers": 1, "{c} has no dependency path to any customer product": 1,
                      "{c} is isolated from the customer-serving cluster": 2,
                      "{c} runs entirely on internal-only infrastructure": 2,
                      "{c} only produces output that no customer ever sees": 3,
                      "{c} contains only synthetic test fixtures": 4,
                      "{c} is excluded from every customer-facing service-level agreement": 5},
    ("impact:unclear", 1): {
        "it has not been confirmed whether any customer-facing service depends on {c}": 0,
        "the downstream consumers of {c} have not been fully mapped": 0,
        "it is not yet known which customers, if any, depend on {c}": 0,
        "the dependency graph covering {c} has not been updated since a large refactor, so its customer exposure is unknown": 1,
        "the customer exposure of {c} has been undocumented since an ownership change": 1,
        "it is unclear whether {c} is enabled for any customer segment": 2,
        "whether failures in {c} reach customers depends on a fallback whose status is unknown": 3,
        "the usage history that would show whether customers use {c} has already been purged": 4,
        "two teams disagree about whether {c} is part of any customer-facing workflow": 5},
    ("severity:0", 1): {"is misaligned by a few pixels": 0, "sits one pixel off its grid": 0,
                        "renders in a slightly wrong color": 1, "shows outdated wording": 2,
                        "briefly flickers on load": 3, "wraps awkwardly onto a second line": 4,
                        "is truncated with an ellipsis": 4, "uses inconsistent capitalization": 5},
    ("severity:1", 1): {"fail intermittently": 0, "fail on large inputs": 1, "stall after a long session": 2,
                        "stop updating after a while": 2, "drop recent changes occasionally": 3,
                        "update a few minutes late": 4, "skip items now and then": 5, "fail on the first attempt": 6},
    # Draft 3: grouped consistently with §5.2. Draft 2 split total failure into 4
    # classes, one of them distinct only by a time phrase ("down since the last
    # deploy"), which §5.2 itself calls non-content.
    ("severity:2", 1): {"has stopped working entirely": 0, "is completely unavailable": 0,
                        "has halted with no progress": 0, "no longer responds at all": 0,      # no service
                        "is returning errors for every request": 1, "rejects every request it receives": 1,
                        "is failing on every attempt": 1, "fails immediately on every attempt": 1,  # every try errors
                        "produces unusable output on every run": 2,
                        "returns corrupted results every time": 2},                         # runs, output unusable
    ("severity:2", 2): {"and no workaround exists": 0, "and there is no fallback path": 0,
                        "and no alternative route is available": 0,
                        "and it cannot be completed manually either": 1, "and retrying does not help": 2,
                        "and the previous version cannot be restored either": 3},
}
NUISANCE_SLOTS = {"impact:0": {2}, "impact:unclear": {2}}   # "who confirmed" / "who could not confirm"

# Draft 2 (Option A): the canonical proposition signature per pool. Every
# semantic slot is declared exactly once: SYN (paraphrase classes, every
# filler mapped), IDENTITY (each filler is its own proposition, reviewed as
# such) or NUISANCE (dropped). Polarity and the label are fixed by
# (pool, value). An undeclared slot or an unmapped filler stops the build:
# ambiguity blocks, it is never resolved silently as "distinct".
SIGNATURE = {  # documentation of each slot's role, in key order
    "routing": ("subject: component", "predicate: metric", "magnitude/shape class"),
    "impact:1": ("evidence channel", "affected customer segment", "subject: product surface"),
    "impact:0": ("subject: component", "evidence class", "NUISANCE: who confirmed"),
    "impact:unclear": ("subject: component", "unknown-aspect class", "NUISANCE: who could not confirm"),
    "severity:0": ("subject: UI element", "defect class", "condition: display context"),
    "severity:1": ("subject: feature", "failure-mode class", "workaround"),
    "severity:2": ("subject: function", "failure class", "no-workaround scope class"),
}
IDENTITY_SLOTS = {("routing", 0), ("routing", 1), ("impact:1", 0), ("impact:1", 1), ("impact:1", 2),
                  ("impact:0", 0), ("impact:unclear", 0), ("severity:0", 0), ("severity:0", 2),
                  ("severity:1", 0), ("severity:1", 2), ("severity:2", 0)}


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


def check_signature_declarations() -> None:
    """Fail closed: every slot declared once, every SYN filler mapped, no
    filler mapped that the vocabulary doesn't contain."""
    for pool, value, builder in POOLS:
        pv = _pv(pool, value)
        keys, _ = builder(value)
        for i in range(len(keys[0])):
            roles = [(pv, i) in SYN, (pv, i) in IDENTITY_SLOTS, i in NUISANCE_SLOTS.get(pv, set())]
            if sum(roles) != 1:
                raise ValueError(f"slot {pv}[{i}] must be declared exactly once, got {roles}")
            if (pv, i) in SYN:
                fillers = {k[i] for k in keys}
                if fillers != set(SYN[(pv, i)]):
                    raise ValueError(f"SYN map for {pv}[{i}] does not match vocabulary: "
                                     f"unmapped {sorted(fillers - set(SYN[(pv, i)]))}, "
                                     f"stale {sorted(set(SYN[(pv, i)]) - fillers)}")


def a9_proposition_capacity(units: list[dict], k_values=(41, 70)) -> dict:
    res = {}
    for (p, v), quota in PILOT2_QUOTA.items():
        us = [u for u in units if (u["pool"], u["value"]) == (p, v)]
        props = {proposition_key(u) for u in us}
        per_k = 9 if p == "routing" else 6
        res[f"{p}:{v}"] = {"filler_keys": len(us), "proposition_keys": len(props),
                           **{f"needed_at_k{k}(N={18*k})": quota + per_k * k for k in k_values}}
    return res

def main() -> None:
    units = expand()
    report = audit(units)
    units_path = DATA_DIR / "workflow_template_grammar_units.json"
    units_path.write_text(json.dumps({
        "status": "Grammar expansion only - not assigned to any pilot or evaluation instance.",
        "seed": SEED, "N_MAX": N_MAX, "pilot2_quota": {f"{p}:{v}": q for (p, v), q in PILOT2_QUOTA.items()},
        "generator_sha256": hashlib.sha256(THIS_FILE.read_bytes()).hexdigest(),
        "units": units}, indent=1))
    report["A9_proposition_capacity"] = a9_proposition_capacity(units)  # gating via A1 since Draft 2
    report["units_sha256"] = hashlib.sha256(units_path.read_bytes()).hexdigest()
    report["generator_sha256"] = hashlib.sha256(THIS_FILE.read_bytes()).hexdigest()
    (RESULTS_DIR / "workflow_template_grammar_audit.json").write_text(json.dumps(report, indent=2))

    print(f"units: {len(units)}  ->  {units_path.relative_to(REPO_ROOT)}")
    print("A1 capacity (main reserve / needed at N_MAX=1260):")
    for k, v in report["A1_capacity"].items():
        print(f"   {k:18s} {v['main_reserve']:4d} / {v['needed_at_N_MAX']}")
    print("A2", report["A2_exact_uniqueness"])
    print("A3/A4", report["A3_A4"])
    print("A5", report["A5_routing_cue_audit"])
    print("A6", {k: v for k, v in report["A6_impact_severity_cue_audit"].items() if k != "examples"})
    print("A9 proposition-level capacity  [units | proposition keys | needed N=738 | needed N=1260]:")
    for k, v in report["A9_proposition_capacity"].items():
        n738, n1260 = list(v.values())[2:]
        flag = "" if v["proposition_keys"] >= n1260 else "   <-- short at N_MAX"
        print(f"   {k:18s} {v['filler_keys']:4d} | {v['proposition_keys']:4d} | {n738:4d} | {n1260:4d}{flag}")
    print(f"\nFAILURES: {len(report['failures'])}")
    for f in report["failures"][:25]:
        print("  -", f)
    print("\nPASSED" if report["passed"] else "\nNOT PASSED")


if __name__ == "__main__":
    main()
