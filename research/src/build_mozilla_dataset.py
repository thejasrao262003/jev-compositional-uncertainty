"""Build the cleaned Mozilla Bugzilla dataset for Part A of
research/methodology/mozilla_realistic_validation_proposal.md (§2.3).

Reads the public bugzilla.mozilla.org REST API only. No Jev API call is
made. Labels come from Bugzilla fields, never from text. Sampling is a
seeded shuffle per cell, fixed before any Jev output exists.

Outputs (research/data/mozilla/):
  dataset.jsonl          one cleaned bug per line
  dataset_manifest.json  filters, seed, per-cell counts, exclusion counts,
                         builder script hash
  dataset_hashes.json    SHA-256 of dataset.jsonl and of this script
"""

import hashlib
import json
import random
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

BZ = "https://bugzilla.mozilla.org/rest"
CREATED_FROM = "2021-01-01"
SEED = "mozilla-realistic-validation-v1"
TARGET_PER_CELL = 40
MAX_CHARS = 2000
MIN_CHARS = 100

GROUPS = {
    "network": [
        ("Core", "Networking"),
        ("Core", "Networking: HTTP"),
        ("Core", "Networking: DNS"),
        ("Core", "Networking: Cookies"),
    ],
    "storage": [
        ("Core", "Storage: IndexedDB"),
        ("Core", "SQLite and Embedded Database Bindings"),
        ("Core", "Storage: Quota Manager"),
        ("Core", "Storage: localStorage & sessionStorage"),
        ("Core", "Storage: Cache API"),
    ],
}
# Mozilla severity -> project score level (proposal §1 table). S1 and S2 merge.
LEVELS = {"S1": 2, "S2": 2, "S3": 1, "S4": 0}
CELL_SEVERITIES = {2: ["S1", "S2"], 1: ["S3"], 0: ["S4"]}

FUZZING_MARKERS = ["found while fuzzing", "fuzzfetch", "grizzly", "--enable-fuzzing",
                   "fuzzing-team", "oss-fuzz", "fuzzilli"]

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "mozilla"


def get(path, params=None, attempts=5):
    url = f"{BZ}/{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params, doseq=True)
    req = urllib.request.Request(url, headers={"User-Agent": "jev-research-dataset-builder"})
    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.load(r)
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as e:
            transient = not isinstance(e, urllib.error.HTTPError) or e.code >= 500
            if not transient or attempt == attempts - 1:
                raise
            time.sleep(2 ** attempt)


def candidates(group, severities):
    comps = GROUPS[group]
    params = {
        "type": "defect",
        "resolution": "FIXED",
        "chfield": "[Bug creation]",
        "chfieldfrom": CREATED_FROM,
        "chfieldto": "Now",
        "product": sorted({p for p, _ in comps}),
        "component": [c for _, c in comps],
        "severity": severities,
        "include_fields": "id,summary,severity,component,product,keywords,creation_time,cf_crash_signature",
        "limit": 0,
    }
    bugs = get("bug", params)["bugs"]
    return sorted(bugs, key=lambda b: b["id"])  # order fixed before the seeded shuffle


# ---------------------------------------------------------------------------
# Cleaning (proposal §2.3). Deterministic; no model involved.
# ---------------------------------------------------------------------------

URL_RE = re.compile(r"https?://\S+|www\.\S+")
EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+(\.[\w-]+)+")
FENCE_RE = re.compile(r"```.*?(```|$)", re.S)
STACK_RE = re.compile(r"^\s*(#?\d+\s+\S+\s*(0x[0-9a-f]+|!|::|\.dll|\.so)|at\s+\S+\(.*\)|\S+\.(cpp|h|rs|js):\d+)",
                      re.I)
DROP_LINE_RE = re.compile(r"^\s*(user agent:|mozilla/5\.0|created attachment \d+|\(in reply to)", re.I)


def clean(summary, description):
    text = FENCE_RE.sub(" ", description)
    lines = []
    for line in text.splitlines():
        if DROP_LINE_RE.match(line) or STACK_RE.match(line):
            continue
        line = line.lstrip("> ").rstrip()
        lines.append(line)
    text = "\n".join(lines)
    full = f"{summary.strip()}\n\n{text}"  # summary is scrubbed too, not just the body
    full = URL_RE.sub("[link]", full)
    full = EMAIL_RE.sub("[email]", full)
    full = re.sub(r"[ \t]+", " ", full)
    full = re.sub(r"\n{3,}", "\n\n", full).strip()
    if len(full) > MAX_CHARS:
        cut = full[:MAX_CHARS]
        boundary = max(cut.rfind(". "), cut.rfind(".\n"), cut.rfind("\n\n"))
        full = cut[: boundary + 1] if boundary > MAX_CHARS // 2 else cut
    return full.strip()


def severity_retriaged(bug_id):
    """True if severity was ever changed away from a real S-value.
    Initial triage from '--' (or the pre-2020 default 'normal') is allowed."""
    history = get(f"bug/{bug_id}/history")["bugs"][0]["history"]
    for event in history:
        for change in event["changes"]:
            if change["field_name"] == "severity" and change["removed"] in LEVELS:
                return True
    return False


def first_comment(bug_id):
    return get(f"bug/{bug_id}/comment")["bugs"][str(bug_id)]["comments"][0]["text"]


def build():
    rng = random.Random(SEED)
    recent_cutoff = datetime.now(timezone.utc) - timedelta(days=365)
    records, cells, seen = [], {}, set()
    for group in GROUPS:
        for level in (2, 1, 0):
            pool = candidates(group, CELL_SEVERITIES[level])
            rng.shuffle(pool)
            stats = {"eligible_before_exclusions": len(pool), "excluded_fuzzing": 0,
                     "excluded_too_short": 0, "excluded_severity_retriaged": 0,
                     "excluded_duplicate": 0, "inspected": 0, "selected": 0}
            for bug in pool:
                if stats["selected"] == TARGET_PER_CELL:
                    break
                stats["inspected"] += 1
                if bug["id"] in seen:
                    stats["excluded_duplicate"] += 1
                    continue
                raw = first_comment(bug["id"])
                if any(m in raw.lower() for m in FUZZING_MARKERS):
                    stats["excluded_fuzzing"] += 1
                    continue
                text = clean(bug["summary"], raw)
                if len(text) - len(bug["summary"]) < MIN_CHARS:
                    stats["excluded_too_short"] += 1
                    continue
                if severity_retriaged(bug["id"]):
                    stats["excluded_severity_retriaged"] += 1
                    continue
                seen.add(bug["id"])
                stats["selected"] += 1
                created = datetime.fromisoformat(bug["creation_time"].replace("Z", "+00:00"))
                records.append({
                    "bug_id": bug["id"],
                    "url": f"https://bugzilla.mozilla.org/show_bug.cgi?id={bug['id']}",
                    "group": group,                       # choice label c1*
                    "component": f"{bug['product']} :: {bug['component']}",
                    "severity": bug["severity"],
                    "level": level,                       # score label c3*
                    "regression": int("regression" in bug["keywords"]),  # noul label c2*
                    "crash": int("crash" in bug["keywords"] or bool(bug.get("cf_crash_signature"))),
                    "creation_time": bug["creation_time"],
                    "recent_12_months": created >= recent_cutoff,
                    "text": text,
                    "text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                })
            stats["shortfall"] = TARGET_PER_CELL - stats["selected"]
            cells[f"{group}:level{level}"] = stats
            print(f"{group} level {level}: {stats}")
    return records, cells


def main():
    records, cells = build()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    dataset_path = OUT_DIR / "dataset.jsonl"
    with dataset_path.open("w", encoding="utf-8", newline="\n") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    script_sha = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    dataset_sha = hashlib.sha256(dataset_path.read_bytes()).hexdigest()
    manifest = {
        "status": "built for review; no Jev call made",
        "proposal": "research/methodology/mozilla_realistic_validation_proposal.md",
        "built_utc": datetime.now(timezone.utc).isoformat(),
        "source": BZ,
        "filters": {"type": "defect", "resolution": "FIXED", "created_from": CREATED_FROM,
                    "groups": {g: [f"{p} :: {c}" for p, c in v] for g, v in GROUPS.items()}},
        "severity_to_level": LEVELS,
        "seed": SEED,
        "target_per_cell": TARGET_PER_CELL,
        "cleaning": {"max_chars": MAX_CHARS, "min_body_chars": MIN_CHARS,
                     "removed": ["fenced code blocks", "stack-frame lines", "user-agent lines",
                                 "attachment lines", "URLs -> [link]", "emails -> [email]"],
                     "fuzzing_markers": FUZZING_MARKERS},
        "cells": cells,
        "n_records": len(records),
        "label_balance": {
            "regression": sum(r["regression"] for r in records),
            "crash": sum(r["crash"] for r in records),
            "recent_12_months": sum(r["recent_12_months"] for r in records),
        },
        "builder_script_sha256": script_sha,
        "dataset_sha256": dataset_sha,
        "note": ("Snapshot of live Bugzilla data: a rebuild can differ if bugs are edited, "
                 "re-triaged or newly fixed. dataset.jsonl plus its hash is the frozen artifact, "
                 "not the query."),
    }
    (OUT_DIR / "dataset_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    (OUT_DIR / "dataset_hashes.json").write_text(json.dumps(
        {"dataset.jsonl": dataset_sha, "build_mozilla_dataset.py": script_sha}, indent=2) + "\n",
        encoding="utf-8")
    print(f"\n{len(records)} records -> {dataset_path}")
    print(json.dumps(manifest["label_balance"]))


if __name__ == "__main__":
    main()
