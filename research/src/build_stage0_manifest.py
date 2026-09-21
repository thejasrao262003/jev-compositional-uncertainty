"""Builds the real Stage 0 construction-validation-pilot manifest.

Per step0b_design_specification.md §3/§11 (Revision 3): 26 calls across
three feasibility checks - noul matched-pool + H2a (8 calls, 4 items x 2
repeats each), choice near-majority 3:2 (9 calls, 3 items x 3 repeats),
score near-majority 2:1-adjacent (9 calls, 3 items x 3 repeats).

Every sentence used in this manifest is UNIQUE across the whole manifest -
no sentence (or its opaque ID) is reused across items. This was tightened
after the validator (validate_step0b_manifest.py) caught the first draft
reusing sentences across items to save writing effort, which both
violated opaque-ID uniqueness and introduced unwanted evidence-sharing
correlation between items that should be independent constructions. Fixed
in the construction, not by relaxing the check.

Content-blind opaque sentence IDs are assigned via a seeded random
permutation BEFORE any semantic-label-based construction logic runs, and
are never derived from or correlated with the semantic label. Reference
labels and is_contested flags are fixed here, at construction time, before
any API call - this script makes no network calls and reads no API
responses.
"""

from __future__ import annotations

import json
import random
from pathlib import Path

OPAQUE_ID_PERMUTATION_SEED = 20260921
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
OUT_PATH = REPO_ROOT / "research" / "data" / "characterization" / "stage0_manifest.json"

rng = random.Random(OPAQUE_ID_PERMUTATION_SEED)
used_ids: set[str] = set()


def make_opaque_ids(n: int) -> list[str]:
    """Random 4-char alphanumeric tokens, content-blind by construction -
    generated from the RNG alone, never from any semantic label. Draws
    from the single shared `used_ids` set so IDs are unique manifest-wide."""
    alphabet = "qwrtypsdfghjkzxcvbnm23456789"  # no vowels/0/1/o/l - avoids accidental words, avoids 0/1/o/l confusion
    out = []
    while len(out) < n:
        tok = "s" + "".join(rng.choice(alphabet) for _ in range(4))
        if tok not in used_ids:
            used_ids.add(tok)
            out.append(tok)
    return out


def check_all_unique(*texts_lists: list[str]) -> None:
    seen = set()
    for lst in texts_lists:
        for t in lst:
            assert t not in seen, f"duplicate sentence text: {t!r}"
            seen.add(t)


# ---------------------------------------------------------------------
# noul: single proposition domain, 4 items (5:0, 4:1, 3:2, 2:2), 2 calls
# each. Every sentence below is used in exactly ONE item - no reuse.
# ---------------------------------------------------------------------

NOUL_INSTRUCTIONS = "Does this transaction look fraudulent?"

# item1 (5:0): 5 unique "yes"-supporting sentences
NOUL_5TO0_YES = [
    "The account logged in from four different countries within a single hour today.",
    "The shipping address was changed twice in the three minutes before checkout completed.",
    "This purchase was for $6,200, roughly forty times the account's typical order size.",
    "The device used has no browsing or login history with this account whatsoever.",
    "The session began at 3:47am local time, outside every prior login this account has made.",
]
# item2 (4:1): 4 unique yes + 1 unique no
NOUL_4TO1_YES = [
    "Three failed password attempts preceded this session, followed by an immediate success.",
    "The billing name on the card does not match any name previously used on this account.",
    "A second, smaller test transaction was made ninety seconds before the main purchase.",
    "The account's email address was changed eleven minutes before this order was placed.",
]
NOUL_4TO1_NO = [
    "The purchase category matches roughly a third of this account's orders over the past year.",
]
# item3 (3:2): 3 unique yes + 2 unique no
NOUL_3TO2_YES = [
    "The delivery address is a freight-forwarding warehouse rather than a residential address.",
    "This is the account's first purchase over $500 in its eight-month history.",
    "The order was placed using a VPN endpoint the account has not used before.",
]
NOUL_3TO2_NO = [
    "The card passed a 3-D Secure challenge with a code sent to the phone on file.",
    "The account has placed six similar orders from the same city over the past year.",
]
# item4 (2:2): 2 unique yes + 2 unique no
NOUL_2TO2_YES = [
    "The order total is close to the account's single largest purchase on record.",
    "The recipient name on the shipping label differs from the name on the account.",
]
NOUL_2TO2_NO = [
    "The account has completed four prior orders shipped to this same address.",
    "The purchase occurred during the account's usual Saturday-afternoon shopping window.",
]

check_all_unique(NOUL_5TO0_YES, NOUL_4TO1_YES, NOUL_4TO1_NO, NOUL_3TO2_YES, NOUL_3TO2_NO, NOUL_2TO2_YES, NOUL_2TO2_NO)


def make_noul_item(item_id: str, condition: str, yes_texts: list[str], no_texts: list[str]) -> dict:
    yes_ids = make_opaque_ids(len(yes_texts))
    no_ids = make_opaque_ids(len(no_texts))
    sentences = [
        {"opaque_id": i, "semantic_label": "supports_yes", "text": t} for i, t in zip(yes_ids, yes_texts)
    ] + [
        {"opaque_id": i, "semantic_label": "supports_no", "text": t} for i, t in zip(no_ids, no_texts)
    ]
    canonical_order = sorted(s["opaque_id"] for s in sentences)
    n_yes, n_no = len(yes_texts), len(no_texts)
    is_contested = n_yes == n_no
    reference_label = None if is_contested else ("yes" if n_yes > n_no else "no")
    return {
        "item_id": item_id,
        "primitive": "noul",
        "domain": "stage0_domain1",
        "condition": condition,
        "sentences": sentences,
        "canonical_order": canonical_order,
        "reference_label": reference_label,
        "is_contested": is_contested,
        "calls_planned": 2,
    }


noul_items = [
    make_noul_item("noul_5to0", "clear_5to0", NOUL_5TO0_YES, []),
    make_noul_item("noul_4to1", "moderate_4to1", NOUL_4TO1_YES, NOUL_4TO1_NO),
    make_noul_item("noul_3to2", "near_majority_3to2", NOUL_3TO2_YES, NOUL_3TO2_NO),
    make_noul_item("noul_2to2", "contested_2to2", NOUL_2TO2_YES, NOUL_2TO2_NO),
]

# ---------------------------------------------------------------------
# choice: single domain, 3 near-majority (3:2) items, 3 calls each.
# Every sentence below is used in exactly ONE item - no reuse.
# ---------------------------------------------------------------------

CHOICE_INSTRUCTIONS = "Should this be treated as a genuine regression requiring rollback, or as noise?"
CHOICE_CRITERIA = {
    "regression": "Strong, corroborated evidence of a real code-caused regression requiring rollback",
    "noise": "Evidence suggests this is not a genuine, reproducible regression",
}

# item1: 3 regression + 2 noise
CHOICE_1_REG = [
    "The error rate climbed above 5% for the third consecutive deploy this week.",
    "The stack trace points directly at a null check missing from yesterday's new module.",
    "Rolling back the last deploy immediately resolved the issue in a staging test.",
]
CHOICE_1_NOISE = [
    "The on-call engineer could not reproduce the issue after two separate attempts.",
    "A similar report last quarter turned out to be a monitoring false positive.",
]
# item2: 3 regression + 2 noise (independent sentences)
CHOICE_2_REG = [
    "Four separate teams filed tickets describing the identical intermittent failure this week.",
    "The regression only reproduces on the code path added in yesterday's release.",
    "Reverting a single recent commit made the failure stop appearing in every test run.",
]
CHOICE_2_NOISE = [
    "The affected users are concentrated in one region with known unstable network conditions.",
    "The failure only appears under a synthetic load pattern that doesn't match real traffic.",
]
# item3: 3 regression + 2 noise (independent sentences)
CHOICE_3_REG = [
    "The crash-reporting dashboard shows a tenfold spike starting exactly at the deploy time.",
    "Three independent customers reported the same error message within an hour of release.",
    "A bisect of recent commits isolates the failure to a single, small code change.",
]
CHOICE_3_NOISE = [
    "The metric spike coincides with a known third-party outage unrelated to this service.",
    "Support could not find any customer-facing impact matching the internal alert.",
]

check_all_unique(CHOICE_1_REG, CHOICE_1_NOISE, CHOICE_2_REG, CHOICE_2_NOISE, CHOICE_3_REG, CHOICE_3_NOISE)


def make_choice_item(item_id: str, reg_texts: list[str], noise_texts: list[str]) -> dict:
    reg_ids = make_opaque_ids(len(reg_texts))
    noise_ids = make_opaque_ids(len(noise_texts))
    sentences = [
        {"opaque_id": i, "semantic_label": "supports_regression", "text": t} for i, t in zip(reg_ids, reg_texts)
    ] + [
        {"opaque_id": i, "semantic_label": "supports_noise", "text": t} for i, t in zip(noise_ids, noise_texts)
    ]
    canonical_order = sorted(s["opaque_id"] for s in sentences)
    return {
        "item_id": item_id,
        "primitive": "choice",
        "domain": "stage0_domain1",
        "condition": "near_majority_3to2",
        "sentences": sentences,
        "canonical_order": canonical_order,
        "reference_label": "regression",  # 3 supporting sentences vs 2, by construction
        "is_contested": False,
        "calls_planned": 3,
    }


choice_items = [
    make_choice_item("choice_nm_001", CHOICE_1_REG, CHOICE_1_NOISE),
    make_choice_item("choice_nm_002", CHOICE_2_REG, CHOICE_2_NOISE),
    make_choice_item("choice_nm_003", CHOICE_3_REG, CHOICE_3_NOISE),
]

# ---------------------------------------------------------------------
# score: single domain, 3 near-majority (2:1 adjacent-level) items, 3
# calls each. Every sentence below is used in exactly ONE item - no reuse.
# ---------------------------------------------------------------------

SCORE_INSTRUCTIONS = "How severe is the reported issue?"
SCORE_CRITERIA = [
    "Cosmetic; no impact to functionality",
    "Broken or degraded feature, but a workaround exists",
    "Blocking issue; no workaround exists",
]

# item1: 2 level-1 + 1 level-2
SCORE_1_L1 = [
    "Bulk export times out for files over 200MB, but exporting in smaller batches works.",
    "Saved filters occasionally reset on login, but can be manually reconfigured each time.",
]
SCORE_1_L2 = [
    "New user signups fail at the final step for every account, with no alternate path.",
]
# item2: 2 level-1 + 1 level-2 (independent sentences)
SCORE_2_L1 = [
    "The mobile app's push notifications are delayed by several minutes during peak hours.",
    "Dark mode renders one settings panel with unreadably low contrast on older phones.",
]
SCORE_2_L2 = [
    "The billing webhook has stopped firing entirely, so no invoices are being generated.",
]
# item3: 2 level-1 + 1 level-2 (independent sentences)
SCORE_3_L1 = [
    "The in-app search occasionally returns stale results until the page is manually refreshed.",
    "CSV imports silently drop rows containing emoji, requiring users to strip them first.",
]
SCORE_3_L2 = [
    "Two-factor codes are never delivered, permanently locking out all affected accounts.",
]

check_all_unique(SCORE_1_L1, SCORE_1_L2, SCORE_2_L1, SCORE_2_L2, SCORE_3_L1, SCORE_3_L2)


def make_score_item(item_id: str, l1_texts: list[str], l2_texts: list[str]) -> dict:
    l1_ids = make_opaque_ids(len(l1_texts))
    l2_ids = make_opaque_ids(len(l2_texts))
    sentences = [
        {"opaque_id": i, "semantic_label": "level1", "text": t} for i, t in zip(l1_ids, l1_texts)
    ] + [
        {"opaque_id": i, "semantic_label": "level2", "text": t} for i, t in zip(l2_ids, l2_texts)
    ]
    canonical_order = sorted(s["opaque_id"] for s in sentences)
    return {
        "item_id": item_id,
        "primitive": "score",
        "domain": "stage0_domain1",
        "condition": "near_majority_2to1_adjacent",
        "sentences": sentences,
        "canonical_order": canonical_order,
        "reference_label": "1",  # majority (2 of 3 sentences) supports level 1, by construction
        "is_contested": False,
        "calls_planned": 3,
    }


score_items = [
    make_score_item("score_nm_001", SCORE_1_L1, SCORE_1_L2),
    make_score_item("score_nm_002", SCORE_2_L1, SCORE_2_L2),
    make_score_item("score_nm_003", SCORE_3_L1, SCORE_3_L2),
]

# ---------------------------------------------------------------------

manifest = {
    "stage": "stage0",
    "metadata": {
        "opaque_id_permutation_seed": OPAQUE_ID_PERMUTATION_SEED,
        "created_at_utc": "2026-09-21T00:00:00Z",
        "spec_revision": "step0b_design_specification.md Revision 3, §3/§11",
    },
    "items": noul_items + choice_items + score_items,
    "questions_spec": {
        "noul": {"instructions": NOUL_INSTRUCTIONS},
        "choice": {"instructions": CHOICE_INSTRUCTIONS, "criteria": CHOICE_CRITERIA},
        "score": {"instructions": SCORE_INSTRUCTIONS, "criteria": SCORE_CRITERIA},
    },
}

total_calls = sum(item["calls_planned"] for item in manifest["items"])

if __name__ == "__main__":
    all_opaque = [s["opaque_id"] for item in manifest["items"] for s in item["sentences"]]
    assert len(all_opaque) == len(set(all_opaque)), "internal check failed: opaque IDs not unique"
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(manifest, indent=2))
    print(f"Wrote {len(manifest['items'])} items, {total_calls} planned calls, "
          f"{len(all_opaque)} unique sentences, to {OUT_PATH}")
    for item in manifest["items"]:
        print(f"  {item['item_id']:20s} {item['primitive']:6s} {item['condition']:28s} "
              f"n_sentences={len(item['sentences'])} calls={item['calls_planned']} "
              f"ref_label={item['reference_label']} contested={item['is_contested']}")
