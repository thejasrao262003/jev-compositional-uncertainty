"""Build the cleaned Linux kernel Bugzilla dataset for the replication
proposed in research/methodology/kernel_replication_proposal.md (§3).

A replication of build_mozilla_dataset.py on a second tracker. Everything
that can be shared is IMPORTED from the Mozilla builder, not copied: the
text cleaning and truncation (`clean`), the length limits, the fuzzing and
intermittent markers. The Mozilla builder is pinned by hash; this script
refuses to run if it has changed. Only the data source, the component
groups, the severity mapping, the regression field and two privacy steps
(kernel trailer lines, reporter/assignee names) differ.

Reads the public bugzilla.kernel.org REST API only (read-only, polite:
User-Agent set, 0.5 s between requests, limit/offset paging). No Jev API
call is made. Labels come from Bugzilla fields, never from text. Sampling
is a seeded shuffle per cell, fixed before any Jev output exists.

Privacy: reporter/assignee e-mail addresses and names are never written
or printed. Names are requested only to scrub them from the text, in
memory, and then dropped.

Outputs (research/data/kernel/):
  dataset.jsonl          one cleaned bug per line
  dataset_manifest.json  filters, seed, per-cell counts, exclusion counts,
                         truncation statistics, hashes
  dataset_hashes.json    SHA-256 of dataset.jsonl and of this script
"""

from __future__ import annotations

import hashlib
import json
import os
import random
import re
import statistics
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SRC_DIR))

import build_mozilla_dataset as moz  # noqa: E402  (cleaning, limits, markers - reused unchanged)

MOZILLA_BUILDER_SHA256 = "64d71a61f1e169ba179fd5e3976f1751e610a89090b455b21cfaf50526c3d913"

BZ = "https://bugzilla.kernel.org/rest"
USER_AGENT = "jev-research-kernel-replication/1.0 (read-only research; no account)"
SLEEP_S = 0.5
PAGE = 500
SEED = "kernel-replication-v1"
TARGET_PER_CELL = moz.TARGET_PER_CELL      # 40
MAX_CHARS = moz.MAX_CHARS                  # 2000 (used by moz.clean)
MIN_CHARS = moz.MIN_CHARS                  # 100
RECENT_FROM = "2018-01-01"

FIXED_RESOLUTIONS = ["CODE_FIX", "PATCH_ALREADY_AVAILABLE"]

# (product, components or None = all components). NFS/NFSD are excluded:
# ambiguous between network and storage.
GROUPS = {
    "network": [
        ("Networking", None),
        ("Drivers", ["Network", "network-wireless", "network-wireless-intel"]),
    ],
    "storage": [
        ("IO/Storage", None),
        ("File System", ["ext4", "btrfs", "XFS"]),
    ],
}
# Kernel severity -> project score level. blocking and high merge (as S1+S2 did).
LEVELS = {"blocking": 2, "high": 2, "normal": 1, "low": 0}
CELL_SEVERITIES = {2: ["blocking", "high"], 1: ["normal"], 0: ["low"]}
DEFAULT_SEVERITY = "normal"
# A severity change is disqualifying when it moves AWAY from a deliberate,
# non-default value (mirrors Mozilla: moving from the default is allowed).
RETRIAGE_FROM = {"blocking", "high", "low", "enhancement"}

# Fuzzing: Mozilla's markers unchanged, plus the kernel's own fuzzers.
KERNEL_FUZZING_MARKERS = ["syzkaller", "syzbot"]
FUZZING_MARKERS = moz.FUZZING_MARKERS + KERNEL_FUZZING_MARKERS

# Privacy pre-step (before moz.clean): kernel patch trailers carry names.
TRAILER_RE = re.compile(
    r"^\s*(signed-off-by|reported-by|reported-and-tested-by|tested-by|acked-by|reviewed-by|"
    r"suggested-by|co-developed-by|cc|from|to|reply-to)\s*:.*$", re.I | re.M)

# Descriptive only (never used to select): lines that look like log output.
LOG_LINE_RE = re.compile(
    r"^\s*(\[\s*\d+\.\d+\]|<\d>|\[<[0-9a-f]+>\]|\?\s+\S+\+0x[0-9a-f]+/0x[0-9a-f]+|"
    r"\S+\+0x[0-9a-f]+/0x[0-9a-f]+|(RIP|RSP|RAX|RBX|RCX|RDX|Call Trace|Code):|"
    r"[A-Z][a-z]{2}\s+\d+\s+\d\d:\d\d:\d\d\s)", re.I)

ROOT = SRC_DIR.parent
OUT_DIR = ROOT / "data" / "kernel"


def check_mozilla_builder() -> None:
    actual = hashlib.sha256((SRC_DIR / "build_mozilla_dataset.py").read_bytes()).hexdigest()
    if actual != MOZILLA_BUILDER_SHA256:
        raise SystemExit(f"build_mozilla_dataset.py changed: {actual} != pinned {MOZILLA_BUILDER_SHA256}")


# ---------------------------------------------------------------------------
# HTTP (read-only, polite)
# ---------------------------------------------------------------------------

# Optional raw-response cache, OUTSIDE the repo (it holds unscrubbed bug
# data, including names). Set KERNEL_BZ_CACHE_DIR to enable it; a cleaning
# change can then be re-run offline. The manifest records whether a cache
# was used and when its responses were fetched.
REPO_ROOT = SRC_DIR.parent.parent
CACHE_DIR = Path(os.environ["KERNEL_BZ_CACHE_DIR"]).resolve() if os.environ.get("KERNEL_BZ_CACHE_DIR") else None
if CACHE_DIR is not None and (CACHE_DIR == REPO_ROOT or REPO_ROOT in CACHE_DIR.parents):
    raise SystemExit("KERNEL_BZ_CACHE_DIR must be outside the repository (it holds unscrubbed data)")
FETCH_LOG = {"cache_hits": 0, "network_fetches": 0, "fetched_utc": []}


def _fetch(url: str, attempts: int) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                data = json.load(r)
            time.sleep(SLEEP_S)
            return data
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as e:
            transient = not isinstance(e, urllib.error.HTTPError) or e.code >= 500 or e.code == 429
            if not transient or attempt == attempts - 1:
                raise
            time.sleep(2 ** (attempt + 1))
    raise RuntimeError("unreachable")


def get(path: str, params: dict | None = None, attempts: int = 5) -> dict:
    url = f"{BZ}/{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params, doseq=True)
    cache_file = None
    if CACHE_DIR is not None:
        cache_file = CACHE_DIR / (hashlib.sha256(url.encode("utf-8")).hexdigest() + ".json")
        if cache_file.exists():
            entry = json.loads(cache_file.read_text(encoding="utf-8"))
            FETCH_LOG["cache_hits"] += 1
            FETCH_LOG["fetched_utc"].append(entry["fetched_utc"])
            return entry["data"]
    data = _fetch(url, attempts)
    now = datetime.now(timezone.utc).isoformat()
    FETCH_LOG["network_fetches"] += 1
    FETCH_LOG["fetched_utc"].append(now)
    if cache_file is not None:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        tmp = cache_file.with_suffix(".tmp")
        tmp.write_text(json.dumps({"url": url, "fetched_utc": now, "data": data}), encoding="utf-8")
        tmp.replace(cache_file)
    return data


def fetch_record() -> dict:
    t = sorted(FETCH_LOG["fetched_utc"])
    return {"cache_used": CACHE_DIR is not None,
            "cache_location": "scratchpad directory outside the repository (not committed)" if CACHE_DIR else None,
            "cache_hits": FETCH_LOG["cache_hits"], "network_fetches": FETCH_LOG["network_fetches"],
            "earliest_fetch_utc": t[0] if t else None, "latest_fetch_utc": t[-1] if t else None}


def search(params: dict) -> list[dict]:
    """All matching bugs, paged with limit/offset in bug-id order."""
    out, offset = [], 0
    while True:
        page = get("bug", {**params, "order": "bug_id", "limit": PAGE, "offset": offset})["bugs"]
        out.extend(page)
        if len(page) < PAGE:
            return out
        offset += PAGE


def group_query(product: str, components: list[str] | None, severities: list[str],
                fields: str) -> dict:
    p = {"product": product, "resolution": FIXED_RESOLUTIONS, "severity": severities,
         "include_fields": fields}
    if components:
        p["component"] = components
    return p


CANDIDATE_FIELDS = "id,summary,severity,component,product,creation_time,cf_regression"


# Bugzilla returns *_detail only when the base field is also requested.
PEOPLE_FIELDS = "creator,assigned_to,creator_detail,assigned_to_detail"


ROLE_ACCOUNT_RE = re.compile(r"assignee|virtual|default|maintainers?\b|\bbugs?\b|\bteam\b|\blist\b|nobody", re.I)


def _pop_names(bug: dict) -> dict:
    """Reporter and assignee display names and login handles, removed from
    the record and kept IN MEMORY ONLY under `_names`, to scrub them from
    the text. They are never written or printed. Role accounts ("Default
    virtual assignee for ...") are skipped: they are not people."""
    real, handles = [], []
    for k in ("creator", "assigned_to"):
        v = bug.pop(k, None)
        if isinstance(v, str) and v and "@" not in v:
            handles.append(v)
    for k in ("creator_detail", "assigned_to_detail"):
        d = bug.pop(k, None) or {}
        if d.get("real_name"):
            real.append(d["real_name"])
        for h in (d.get("name"), d.get("nick")):
            if isinstance(h, str) and h and "@" not in h:
                handles.append(h)
    return {"real": [n for n in real if "@" not in n and not ROLE_ACCOUNT_RE.search(n)],
            "handles": [h for h in handles if not ROLE_ACCOUNT_RE.search(h)]}


def candidates(group: str, severities: list[str]) -> list[dict]:
    bugs = {}
    for product, comps in GROUPS[group]:
        for b in search(group_query(product, comps, severities, CANDIDATE_FIELDS + "," + PEOPLE_FIELDS)):
            b["_names"] = _pop_names(b)
            bugs[b["id"]] = b
    return [bugs[i] for i in sorted(bugs)]  # order fixed before the seeded shuffle


def first_comment(bug_id: int) -> str:
    return get(f"bug/{bug_id}/comment")["bugs"][str(bug_id)]["comments"][0]["text"]


def severity_history(bug_id: int) -> tuple[bool, bool]:
    """(retriaged, changed_at_all). Only field names and values are read;
    who made the change is never looked at or kept."""
    history = get(f"bug/{bug_id}/history")["bugs"][0]["history"]
    retriaged = changed = False
    for event in history:
        for change in event["changes"]:
            if change["field_name"] == "severity":
                changed = True
                if change["removed"] in RETRIAGE_FROM:
                    retriaged = True
    return retriaged, changed


# ---------------------------------------------------------------------------
# Cleaning: privacy pre-step, then the Mozilla clean() unchanged.
# ---------------------------------------------------------------------------

# Name parts never scrubbed on their own: role accounts ("Networking Other",
# "drivers_network") would otherwise blank ordinary words.
NAME_PART_STOPWORDS = {"the", "and", "kernel", "linux", "bugzilla", "other", "network", "networking",
                       "drivers", "driver", "storage", "file", "system", "filesystem", "wireless", "intel",
                       "default", "assignee", "bugs", "bug", "maintainer", "maintainers", "team", "list",
                       "block", "scsi", "ext4", "btrfs", "xfs", "ide", "ata", "nvme", "acpi", "none", "nobody",
                       # common English words that also occur as name parts
                       "not", "error", "can", "get", "set", "new", "old", "one", "two", "all", "any", "may",
                       "see", "use", "run", "try", "for", "from", "with", "but", "you", "his", "her", "who"}


def scrub_names(text: str, names: dict) -> tuple[str, int]:
    """Full real names, whole login handles (>= 4 chars) and real-name
    parts (capitalized in the name, >= 3 chars, not a stopword), all case-
    insensitively, so a lowercase hostname, volume-group name or /home/<user>
    path that repeats a name part is scrubbed too."""
    n = 0
    full, parts = set(), set()
    for name in names["real"]:
        name = name.strip()
        own = [p for p in re.split(r"[\s,()\[\]<>\"'_.-]+", name)
               if len(p) >= 3 and p[0].isupper() and p.lower() not in NAME_PART_STOPWORDS]
        if own:
            full.add(name)
            parts.update(own)
    full.update(h.strip() for h in names["handles"]
                if len(h.strip()) >= 4 and h.strip().lower() not in NAME_PART_STOPWORDS)
    for tok in sorted(full, key=len, reverse=True):
        text, k = re.subn(rf"(?<!\w){re.escape(tok)}(?!\w)", "[name]", text, flags=re.I)
        n += k
    for tok in sorted(parts, key=len, reverse=True):
        text, k = re.subn(rf"(?<!\w){re.escape(tok)}(?!\w)", "[name]", text, flags=re.I)
        n += k
    return text, n


def prepare(summary: str, raw: str, names: dict) -> tuple[str, str, int, int]:
    """Returns (summary', description') after the privacy pre-step, plus
    counts of dropped trailer lines and scrubbed name occurrences."""
    body, n_trailers = TRAILER_RE.subn("", raw)
    body, n1 = scrub_names(body, names)
    summary, n2 = scrub_names(summary, names)
    return summary, body, n_trailers, n1 + n2


def clean_with_truncation(summary: str, body: str) -> tuple[str, dict]:
    """moz.clean() unchanged. To report the truncation kind, the same
    function is also run with the limit lifted (module global restored)."""
    text = moz.clean(summary, body)
    saved = moz.MAX_CHARS
    try:
        moz.MAX_CHARS = 10 ** 9
        full = moz.clean(summary, body)
    finally:
        moz.MAX_CHARS = saved
    if len(full) <= MAX_CHARS:
        kind = "none"
    elif text == full[:MAX_CHARS].strip():
        kind = "hard_cut"
    else:
        kind = "sentence_or_paragraph_boundary"
    lines = [ln for ln in text.splitlines() if ln.strip()]
    log_share = sum(bool(LOG_LINE_RE.match(ln)) for ln in lines) / len(lines) if lines else 0.0
    return text, {"chars_before_truncation": len(full), "truncation": kind, "log_line_share": round(log_share, 4)}


def is_intermittent(bug: dict) -> bool:
    # Mozilla rule minus the keyword test (the kernel tracker has no such keywords).
    return bug["summary"].strip().lower().startswith(moz.INTERMITTENT_PREFIXES)


def leak_check(text: str) -> list[str]:
    problems = []
    if moz.EMAIL_RE.search(text) or "@" in text:
        problems.append("email-like")
    if moz.URL_RE.search(text):
        problems.append("url")
    return problems


def build():
    rng = random.Random(SEED)
    records, cells, seen = [], {}, set()
    privacy = {"trailer_lines_dropped": 0, "name_occurrences_scrubbed": 0, "bugs_with_name_scrubbed": 0,
               "residual_at_sign_removed": 0}
    for group in GROUPS:
        for level in (2, 1, 0):
            pool = candidates(group, CELL_SEVERITIES[level])
            rng.shuffle(pool)
            stats = {"eligible_before_exclusions": len(pool), "excluded_intermittent": 0,
                     "excluded_fuzzing": 0, "excluded_too_short": 0,
                     "excluded_severity_retriaged": 0, "excluded_duplicate": 0,
                     "inspected": 0, "selected": 0}
            for bug in pool:
                if stats["selected"] == TARGET_PER_CELL:
                    break
                stats["inspected"] += 1
                if bug["id"] in seen:
                    stats["excluded_duplicate"] += 1
                    continue
                if is_intermittent(bug):
                    stats["excluded_intermittent"] += 1
                    continue
                raw = first_comment(bug["id"])
                if any(m in raw.lower() for m in moz.INTERMITTENT_MARKERS):
                    stats["excluded_intermittent"] += 1
                    continue
                if any(m in raw.lower() for m in FUZZING_MARKERS) or \
                        any(m in bug["summary"].lower() for m in KERNEL_FUZZING_MARKERS):
                    stats["excluded_fuzzing"] += 1
                    continue
                summary, body, n_tr, n_nm = prepare(bug["summary"], raw, bug.pop("_names"))
                text, trunc = clean_with_truncation(summary, body)
                # Residual '@' (e.g. "user@host" without a TLD) is replaced too.
                if "@" in text:
                    privacy["residual_at_sign_removed"] += text.count("@")
                    text = re.sub(r"\S*@\S*", "[email]", text)
                if len(text) - len(summary) < MIN_CHARS:
                    stats["excluded_too_short"] += 1
                    continue
                retriaged, changed = severity_history(bug["id"])
                if retriaged:
                    stats["excluded_severity_retriaged"] += 1
                    continue
                assert not leak_check(text), (bug["id"], leak_check(text))
                privacy["trailer_lines_dropped"] += n_tr
                privacy["name_occurrences_scrubbed"] += n_nm
                privacy["bugs_with_name_scrubbed"] += int(n_nm > 0)
                seen.add(bug["id"])
                stats["selected"] += 1
                records.append({
                    "bug_id": bug["id"],
                    "url": f"https://bugzilla.kernel.org/show_bug.cgi?id={bug['id']}",
                    "group": group,                                   # choice label c1*
                    "component": f"{bug['product']} :: {bug['component']}",
                    "severity": bug["severity"],                      # reporter-set
                    "level": level,                                   # score label c3*
                    "regression": int(bug.get("cf_regression") == "Yes"),  # noul label c2*
                    "cf_regression": bug.get("cf_regression"),
                    "creation_time": bug["creation_time"],
                    "recent_since_2018": bug["creation_time"][:10] >= RECENT_FROM,
                    "severity_changed_after_filing": changed,
                    **trunc,
                    "text": text,
                    "text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                })
            stats["shortfall"] = TARGET_PER_CELL - stats["selected"]
            cells[f"{group}:level{level}"] = stats
            print(f"{group} level {level}: {stats}", flush=True)
    return records, cells, privacy


def truncation_stats(records: list[dict]) -> dict:
    lens = [len(r["text"]) for r in records]
    pre = [r["chars_before_truncation"] for r in records]
    kinds = {k: sum(r["truncation"] == k for r in records)
             for k in ("none", "sentence_or_paragraph_boundary", "hard_cut")}
    shares = [r["log_line_share"] for r in records]
    return {"truncated": len(records) - kinds["none"], "by_kind": kinds,
            "cleaned_chars_before_truncation": {"median": statistics.median(pre), "max": max(pre)},
            "final_chars": {"min": min(lens), "median": statistics.median(lens), "max": max(lens)},
            "log_line_share": {"median": statistics.median(shares),
                               "bugs_with_share_ge_0.5": sum(s >= 0.5 for s in shares)}}


def main():
    check_mozilla_builder()
    records, cells, privacy = build()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    dataset_path = OUT_DIR / "dataset.jsonl"
    with dataset_path.open("w", encoding="utf-8", newline="\n") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    script_sha = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    dataset_sha = hashlib.sha256(dataset_path.read_bytes()).hexdigest()
    manifest = {
        "status": "built for review; no Jev call made",
        "proposal": "research/methodology/kernel_replication_proposal.md",
        "replicates": "research/methodology/mozilla_realistic_validation_proposal.md",
        "built_utc": datetime.now(timezone.utc).isoformat(),
        "fetch": fetch_record(),
        "source": BZ,
        "filters": {"resolution": FIXED_RESOLUTIONS, "created_from": None,
                    "severity_excluded": ["enhancement"],
                    "groups": {g: [f"{p} :: {', '.join(c) if c else '(all components)'}" for p, c in v]
                               for g, v in GROUPS.items()},
                    "excluded_as_ambiguous": ["File System :: NFS", "File System :: NFSD"]},
        "severity_to_level": LEVELS,
        "severity_label_source": "reporter-set (kernel Bugzilla has no triage step for severity)",
        "regression_label": "cf_regression == 'Yes' -> 1, else ('No' or '---') -> 0",
        "seed": SEED,
        "target_per_cell": TARGET_PER_CELL,
        "cleaning": {"function": "build_mozilla_dataset.clean (imported, unchanged)",
                     "max_chars": MAX_CHARS, "min_body_chars": MIN_CHARS,
                     "truncation_rule": ("cut at 2,000 characters, at the last '. ', '.\\n' or blank line "
                                         "if it falls after character 1,000, else a hard cut"),
                     "privacy_pre_step": ["kernel trailer lines (Signed-off-by:, Reported-by:, Cc:, From:, ...) "
                                          "dropped", "reporter/assignee display names -> [name] (names held in "
                                          "memory only, never written)",
                                          "any residual token containing '@' -> [email]"],
                     "removed": ["fenced code blocks", "stack-frame lines (Mozilla regex)",
                                 "user-agent lines", "attachment lines", "URLs -> [link]",
                                 "emails, incl. 'name [at] host' -> [email]"],
                     "fuzzing_markers": FUZZING_MARKERS},
        "severity_retriage_exclusion": f"severity changed away from one of {sorted(RETRIAGE_FROM)}",
        "intermittent_exclusion": {"summary_prefixes": list(moz.INTERMITTENT_PREFIXES),
                                   "description_markers": moz.INTERMITTENT_MARKERS},
        "cells": cells,
        "n_records": len(records),
        "label_balance": {
            "regression": sum(r["regression"] for r in records),
            "recent_since_2018": sum(r["recent_since_2018"] for r in records),
            "severity_changed_after_filing": sum(r["severity_changed_after_filing"] for r in records),
        },
        "truncation": truncation_stats(records),
        "privacy": privacy,
        "mozilla_builder_sha256": MOZILLA_BUILDER_SHA256,
        "builder_script_sha256": script_sha,
        "dataset_sha256": dataset_sha,
        "note": ("Snapshot of live Bugzilla data: a rebuild can differ if bugs are edited or newly fixed. "
                 "dataset.jsonl plus its hash is the frozen artifact, not the query."),
    }
    (OUT_DIR / "dataset_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    (OUT_DIR / "dataset_hashes.json").write_text(json.dumps(
        {"dataset.jsonl": dataset_sha, "build_kernel_dataset.py": script_sha}, indent=2) + "\n",
        encoding="utf-8")
    print(f"\n{len(records)} records -> {dataset_path}")
    print(json.dumps({"label_balance": manifest["label_balance"], "truncation": manifest["truncation"],
                      "privacy": privacy}, indent=2))


if __name__ == "__main__":
    main()
