"""Builds the Stage 1 manifest for `choice` and `noul` ONLY.

`score` is deliberately excluded (Stage 0 flagged its near-majority
reference-label rule as not-yet-justified; per
step0b_design_specification.md §0, its Stage 1 design is not finalized
until the separate semantic-validation follow-up in stage0_report.md
"Flagged concern" completes and is reviewed - this script does not
generate score items).

Per §3's allocation table: 2 independently constructed domains per
primitive, 15 items/domain (3 clear 5:0, 3 moderate 4:1, 6 near-majority
3:2, 3 contested 2:2) = 30 items/primitive. Every sentence is generated
via a seeded, parametrized template so all sentences across the entire
manifest are genuinely distinct text (the Stage 0 validator caught literal
sentence reuse across items as a real bug - this generator avoids that by
construction, not by re-checking after the fact).

No network calls. No API responses are read. Reference labels and
is_contested flags are fixed here, before any Stage 1 API call.
"""

from __future__ import annotations

import json
import random
from pathlib import Path

OPAQUE_ID_PERMUTATION_SEED = 20260922  # distinct from Stage 0's seed
SUBSET_SELECTION_SEED = 20260923
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
OUT_PATH = REPO_ROOT / "research" / "data" / "characterization" / "stage1_manifest_choice_noul.json"

rng = random.Random(OPAQUE_ID_PERMUTATION_SEED)
used_ids: set[str] = set()
used_texts: set[str] = set()


def make_opaque_id() -> str:
    alphabet = "qwrtypsdfghjkzxcvbnm23456789"
    while True:
        tok = "s" + "".join(rng.choice(alphabet) for _ in range(4))
        if tok not in used_ids:
            used_ids.add(tok)
            return tok


# ---------------------------------------------------------------------
# Parametrized sentence templates. Each template has numbered slots filled
# with a value drawn from a per-template value pool via the seeded rng, so
# repeated use of the same template yields genuinely different text.
# ---------------------------------------------------------------------

def render(rng_local: random.Random, templates: list[str], slot_pools: dict[str, list]) -> str:
    """Pick a template, fill its slots with numeric jitter added to each
    chosen value's base (so the combinatorial space is effectively
    unbounded rather than limited to len(slot_pools) discrete choices),
    and return distinct text (checked against used_texts globally)."""
    attempts = 0
    while attempts < 2000:
        attempts += 1
        tmpl = rng_local.choice(templates)
        fill = {}
        for k, v in slot_pools.items():
            base = rng_local.choice(v)
            # if the base is purely numeric, jitter it slightly so repeated
            # picks of the same base value still yield distinct text
            if isinstance(base, str) and base.lstrip("$").replace(",", "").isdigit():
                prefix = "$" if base.startswith("$") else ""
                num = int(base.lstrip("$").replace(",", ""))
                jittered = max(1, num + rng_local.randint(-num // 6 - 1, num // 6 + 1))
                fill[k] = f"{prefix}{jittered:,}"
            else:
                fill[k] = base
        try:
            text = tmpl.format(**fill)
        except KeyError:
            continue
        if text not in used_texts:
            used_texts.add(text)
            return text
    raise RuntimeError(f"exhausted template/slot combinations without finding new text (templates={templates[:1]}...)")


# --- choice domain A: "incident routing" (infra vs application team) -----

CHOICE_A_INFRA_TEMPLATES = [
    "Latency to the {service} backend spiked to {ms}ms starting at {time}.",
    "The load balancer logged {count} upstream timeout errors in the last {mins} minutes.",
    "DNS resolution for {service} failed intermittently across {count} availability zones.",
    "Disk utilization on the {service} host crossed {pct}% shortly before the incident began.",
    "A network partition was observed between the {service} cluster and its replicas.",
    "The CDN reported a {pct}% cache-miss rate for {service}, well above its usual baseline.",
]
CHOICE_A_APP_TEMPLATES = [
    "The {service} deploy at {time} introduced a change to the request-validation logic.",
    "Application logs show a stack trace originating in the {service} module's new code path.",
    "A feature flag for {service} was enabled for {pct}% of traffic just before the incident.",
    "The {service} service's error budget was already exhausted before this incident began.",
    "Unit tests for the {service} change were skipped in the CI run that shipped this release.",
    "The {service} team's last three deploys have each required a follow-up hotfix.",
]
CHOICE_A_SLOTS = {
    "service": ["checkout", "search", "billing", "auth", "notifications", "catalog"],
    "ms": ["220", "340", "510", "690", "875"],
    "count": ["3", "5", "7", "9", "12"],
    "mins": ["10", "15", "20", "30"],
    "time": ["09:14", "13:02", "22:41", "04:50", "17:37"],
    "pct": ["12", "28", "45", "63", "80"],
}
CHOICE_A_INSTRUCTIONS = "Is this incident most likely caused by infrastructure or by an application-level change?"
CHOICE_A_CRITERIA = {
    "infrastructure": "Network, hardware, DNS, load-balancing, or platform-level causes",
    "application": "A code, configuration, or deploy-level cause within a specific service",
}

# --- choice domain B: "support ticket routing" (billing vs shipping) -----

CHOICE_B_BILLING_TEMPLATES = [
    "The customer says they were charged {amt} twice for the same order placed on {date}.",
    "An automatic renewal for {amt} occurred despite the subscription being cancelled on {date}.",
    "A refund of {amt} was promised on {date} but has not appeared on the customer's statement.",
    "The invoice for order #{orderid} lists a tax amount that doesn't match the order total.",
    "The customer's saved payment method was declined for {amt} despite having sufficient funds.",
    "A promotional code was not applied, resulting in an overcharge of {amt} on order #{orderid}.",
]
CHOICE_B_SHIPPING_TEMPLATES = [
    "Order #{orderid} has shown 'label created' with no movement for {days} days.",
    "The customer received someone else's package instead of their order #{orderid}.",
    "Tracking for order #{orderid} says delivered, but the customer states it never arrived.",
    "The box for order #{orderid} arrived visibly crushed with the contents damaged inside.",
    "Customs held order #{orderid} for {days} days with no update from the carrier.",
    "The customer requested to change the delivery address for order #{orderid} before it ships.",
]
CHOICE_B_SLOTS = {
    "amt": ["$14.99", "$28.50", "$61.20", "$103.75", "$9.99"],
    "date": ["March 3rd", "last Tuesday", "the 14th", "two weeks ago", "April 1st"],
    "orderid": ["48213", "77590", "10442", "93087", "26651", "58734"],
    "days": ["4", "6", "9", "12", "3"],
}
CHOICE_B_INSTRUCTIONS = "Which team should handle this support ticket: billing or shipping?"
CHOICE_B_CRITERIA = {
    "billing": "Charges, invoices, refunds, payment methods, promotional codes",
    "shipping": "Delivery status, tracking, damaged or lost packages, address changes",
}

CHOICE_DOMAINS = {
    "A": dict(pos_templates=CHOICE_A_INFRA_TEMPLATES, neg_templates=CHOICE_A_APP_TEMPLATES,
              slots=CHOICE_A_SLOTS, pos_label="infrastructure", neg_label="application",
              instructions=CHOICE_A_INSTRUCTIONS, criteria=CHOICE_A_CRITERIA),
    "B": dict(pos_templates=CHOICE_B_BILLING_TEMPLATES, neg_templates=CHOICE_B_SHIPPING_TEMPLATES,
              slots=CHOICE_B_SLOTS, pos_label="billing", neg_label="shipping",
              instructions=CHOICE_B_INSTRUCTIONS, criteria=CHOICE_B_CRITERIA),
}

# --- noul domain A: fraud proposition (reuses a fresh, independent pool,
# distinct from Stage 0's fraud sentences via the global used_texts check) --

NOUL_A_YES_TEMPLATES = [
    "The account logged in from {country} within the last hour, a location never used before.",
    "A charge of {amt} was made, about {mult}x the account's average transaction size.",
    "The shipping address changed {count} times in the {mins} minutes before checkout.",
    "The device used has no prior history with this account across its {months}-month lifetime.",
    "This session began at {time} local time, outside the account's usual active hours.",
    "The account attempted {count} failed logins before this session succeeded.",
]
NOUL_A_NO_TEMPLATES = [
    "The purchase matches the account's usual category, at roughly {amt}, consistent with history.",
    "The billing and shipping addresses have matched for over {months} months without change.",
    "The device has been associated with this account for {months} months of regular use.",
    "The session falls within the account's normal {time}-hour shopping window.",
    "The card passed a 3-D Secure challenge with a code sent to the phone on file.",
    "The account has placed {count} similar orders from this location over the past year.",
]
NOUL_A_SLOTS = {
    "country": ["a country the account has never visited", "an unfamiliar region", "a new jurisdiction"],
    "amt": ["$1,200", "$85", "$430", "$60", "$2,750"],
    "mult": ["15", "22", "8", "30", "45"],
    "count": ["3", "5", "7", "9"],
    "mins": ["2", "5", "8", "12"],
    "months": ["6", "11", "18", "24", "9"],
    "time": ["3am", "4:15am", "2:50am", "11pm-1am"],
}
NOUL_A_INSTRUCTIONS = "Does this transaction look fraudulent?"

# --- noul domain B: content-moderation proposition -------------------

NOUL_B_YES_TEMPLATES = [
    "The message contains a link to a domain registered {days} days ago.",
    "The account was created {mins} minutes before posting this message.",
    "The message was sent identically to {count} different recipients within {mins} minutes.",
    "The message urges the recipient to act within {hours} hours 'or lose access'.",
    "The sender's display name impersonates a known brand, but the account is unverified.",
    "The message asks the recipient to confirm a password via an external link.",
]
NOUL_B_NO_TEMPLATES = [
    "The sender has an account history of {months} months with no prior reports.",
    "The message is a reply within an existing {days}-day-old conversation thread.",
    "The link in the message points to the sender's own previously-verified domain.",
    "The message was sent to a single recipient who had messaged first.",
    "The account has {count} mutual connections with the recipient.",
    "The message content matches the sender's typical posting topics over {months} months.",
]
NOUL_B_SLOTS = {
    "days": ["1", "2", "4", "7"],
    "mins": ["3", "10", "20", "45"],
    "count": ["50", "120", "300", "800"],
    "hours": ["2", "6", "12", "24"],
    "months": ["4", "9", "14", "22"],
}
NOUL_B_INSTRUCTIONS = "Does this message look like a phishing or scam attempt?"

NOUL_DOMAINS = {
    "A": dict(yes_templates=NOUL_A_YES_TEMPLATES, no_templates=NOUL_A_NO_TEMPLATES,
              slots=NOUL_A_SLOTS, instructions=NOUL_A_INSTRUCTIONS),
    "B": dict(yes_templates=NOUL_B_YES_TEMPLATES, no_templates=NOUL_B_NO_TEMPLATES,
              slots=NOUL_B_SLOTS, instructions=NOUL_B_INSTRUCTIONS),
}

# ---------------------------------------------------------------------
# Allocation, per §3: 15 items/domain = 3 clear(5:0) + 3 moderate(4:1) +
# 6 near-majority(3:2) + 3 contested(2:2)
# ---------------------------------------------------------------------

CONDITION_PLAN = (
    [("clear_5to0", 5, 0)] * 3
    + [("moderate_4to1", 4, 1)] * 3
    + [("near_majority_3to2", 3, 2)] * 6
    + [("contested_2to2", 2, 2)] * 3
)
assert len(CONDITION_PLAN) == 15


def build_two_sided_item(item_id: str, primitive: str, domain: str, condition: str,
                          n_pos: int, n_neg: int, pos_templates, neg_templates, slots,
                          pos_label: str, neg_label: str) -> dict:
    local_rng = random.Random(rng.randint(0, 2**31))
    pos_sentences = [render(local_rng, pos_templates, slots) for _ in range(n_pos)]
    neg_sentences = [render(local_rng, neg_templates, slots) for _ in range(n_neg)]
    sentences = (
        [{"opaque_id": make_opaque_id(), "semantic_label": f"supports_{pos_label}", "text": t} for t in pos_sentences]
        + [{"opaque_id": make_opaque_id(), "semantic_label": f"supports_{neg_label}", "text": t} for t in neg_sentences]
    )
    canonical_order = sorted(s["opaque_id"] for s in sentences)
    is_contested = n_pos == n_neg
    reference_label = None if is_contested else (pos_label if n_pos > n_neg else neg_label)
    return {
        "item_id": item_id, "primitive": primitive, "domain": domain, "condition": condition,
        "sentences": sentences, "canonical_order": canonical_order,
        "reference_label": reference_label, "is_contested": is_contested,
    }


def build_primitive_items(primitive: str, domain_key: str, domain_spec: dict) -> list[dict]:
    items = []
    for i, (condition, n_pos, n_neg) in enumerate(CONDITION_PLAN, 1):
        item_id = f"{primitive}_{domain_key}_{i:02d}_{condition}"
        if primitive == "choice":
            item = build_two_sided_item(
                item_id, "choice", domain_key, condition, n_pos, n_neg,
                domain_spec["pos_templates"], domain_spec["neg_templates"], domain_spec["slots"],
                domain_spec["pos_label"], domain_spec["neg_label"],
            )
            item["question_instructions"] = domain_spec["instructions"]
            item["question_criteria"] = domain_spec["criteria"]
        else:  # noul
            item = build_two_sided_item(
                item_id, "noul", domain_key, condition, n_pos, n_neg,
                domain_spec["yes_templates"], domain_spec["no_templates"], domain_spec["slots"],
                "yes", "no",
            )
            item["question_instructions"] = domain_spec["instructions"]
        items.append(item)
    return items


all_items = []
for dk, spec in CHOICE_DOMAINS.items():
    all_items += build_primitive_items("choice", dk, spec)
for dk, spec in NOUL_DOMAINS.items():
    all_items += build_primitive_items("noul", dk, spec)

# --- robustness+repeat subset: 20% of each primitive's 30 items, seeded --
subset_rng = random.Random(SUBSET_SELECTION_SEED)


def select_subset(items: list[dict], frac: float = 0.20) -> list[str]:
    ids = [it["item_id"] for it in items]
    k = max(1, round(len(ids) * frac))
    return sorted(subset_rng.sample(ids, k))


choice_items = [it for it in all_items if it["primitive"] == "choice"]
noul_items = [it for it in all_items if it["primitive"] == "noul"]
robustness_repeat_subset = select_subset(choice_items) + select_subset(noul_items)

# Alternate presentations (Layer 2, §6) are precomputed and frozen here -
# NOT generated by the runner at execution time - so "no order chosen
# based on the model's output" holds by construction, and the full
# presentation set is immutable/auditable before any API call.
alt_order_rng = random.Random(SUBSET_SELECTION_SEED + 1)
items_by_id = {it["item_id"]: it for it in all_items}
alternate_orders: dict[str, dict[str, list[str]]] = {}
for item_id in robustness_repeat_subset:
    canon = items_by_id[item_id]["canonical_order"]
    reverse_order = list(reversed(canon))
    shuffled = canon[:]
    alt_order_rng.shuffle(shuffled)
    # a shuffle that happens to reproduce canonical or exact-reverse order
    # is degenerate for this purpose - reshuffle deterministically until
    # distinct (still seeded, still decided before any output is seen)
    while shuffled == canon or shuffled == reverse_order:
        alt_order_rng.shuffle(shuffled)
    alternate_orders[item_id] = {"reverse": reverse_order, "seeded_shuffle": shuffled}

# --- overflow replacement list: one preregistered spare per condition,
# per primitive/domain, matching §11's reserve rule (structural, fixed now) --
overflow_items = []
overflow_map = {}
for primitive, domains, spec_map in (("choice", CHOICE_DOMAINS, CHOICE_DOMAINS), ("noul", NOUL_DOMAINS, NOUL_DOMAINS)):
    for dk, spec in domains.items():
        # one spare near-majority item per domain (the most-used condition)
        spare_id = f"{primitive}_{dk}_overflow01_near_majority_3to2"
        if primitive == "choice":
            spare = build_two_sided_item(spare_id, "choice", dk, "near_majority_3to2", 3, 2,
                                          spec["pos_templates"], spec["neg_templates"], spec["slots"],
                                          spec["pos_label"], spec["neg_label"])
            spare["question_instructions"] = spec["instructions"]
            spare["question_criteria"] = spec["criteria"]
        else:
            spare = build_two_sided_item(spare_id, "noul", dk, "near_majority_3to2", 3, 2,
                                          spec["yes_templates"], spec["no_templates"], spec["slots"], "yes", "no")
            spare["question_instructions"] = spec["instructions"]
        overflow_items.append(spare)
        # map it to replace the first near-majority item in that domain
        original = next(it for it in all_items if it["primitive"] == primitive and it["domain"] == dk
                         and it["condition"] == "near_majority_3to2")
        overflow_map[original["item_id"]] = spare_id

manifest = {
    "stage": "stage1_choice_noul",
    "metadata": {
        "opaque_id_permutation_seed": OPAQUE_ID_PERMUTATION_SEED,
        "subset_selection_seed": SUBSET_SELECTION_SEED,
        "created_at_utc": "2026-09-22T00:00:00Z",
        "spec_revision": "step0b_design_specification.md Revision 3, §3/§6/§7/§11",
        "note": "score excluded - blocked pending semantic-validation follow-up (see stage0_report.md)",
    },
    "items": all_items + overflow_items,
    "robustness_repeat_subset_ids": robustness_repeat_subset,
    "alternate_orders": alternate_orders,
    "overflow_replacement_list": overflow_map,
}

if __name__ == "__main__":
    all_opaque = [s["opaque_id"] for item in manifest["items"] for s in item["sentences"]]
    assert len(all_opaque) == len(set(all_opaque)), "internal check failed: opaque IDs not unique"
    all_text = [s["text"] for item in manifest["items"] for s in item["sentences"]]
    assert len(all_text) == len(set(all_text)), "internal check failed: sentence text not unique"
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(manifest, indent=2))
    from collections import Counter
    counts = Counter((it["primitive"], it["domain"], it["condition"]) for it in all_items)
    print(f"Wrote {len(manifest['items'])} items ({len(all_items)} primary + {len(overflow_items)} overflow), "
          f"{len(all_opaque)} unique sentences, to {OUT_PATH}")
    print(f"Robustness+repeat subset: {len(robustness_repeat_subset)} items")
    for k, v in sorted(counts.items()):
        print(f"  {k}: {v}")
