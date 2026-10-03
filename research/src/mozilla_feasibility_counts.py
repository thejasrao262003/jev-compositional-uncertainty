"""Feasibility counts for the proposed Mozilla Bugzilla realistic-validation
study (research/methodology/mozilla_realistic_validation_proposal.md).

Queries the public bugzilla.mozilla.org REST API for counts only (plus a
small description-length sample). No Jev API call is made, no bug text is
written to disk. Output: research/results/mozilla_feasibility_counts.json.
"""

import json
import statistics
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

BZ = "https://bugzilla.mozilla.org/rest"
CREATED_FROM = "2021-01-01"
SEVERITIES = ["S1", "S2", "S3", "S4"]
KEYWORDS = ["crash", "regression"]  # candidate labels for the noul node

# Subsystem groups -> choice label. Networking: Cache and DOM: Networking are
# deliberately excluded: each straddles both groups.
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

OUT = Path(__file__).resolve().parents[1] / "results" / "mozilla_feasibility_counts.json"


def get(path, params, attempts=4):
    url = f"{BZ}/{path}?{urllib.parse.urlencode(params, doseq=True)}"
    req = urllib.request.Request(url, headers={"User-Agent": "jev-research-feasibility"})
    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code < 500 or attempt == attempts - 1:
                raise
            time.sleep(2 ** attempt)  # transient 5xx from bugzilla.mozilla.org


def base_params(components):
    return {
        "type": "defect",
        "resolution": "FIXED",
        "chfield": "[Bug creation]",
        "chfieldfrom": CREATED_FROM,
        "chfieldto": "Now",
        "product": sorted({p for p, _ in components}),
        "component": [c for _, c in components],
    }


def count(components, **extra):
    return get("bug", {**base_params(components), "count_only": 1, **extra})["bug_count"]


def description_lengths(components, severity, n=8):
    bugs = get("bug", {**base_params(components), "severity": severity,
                       "include_fields": "id", "limit": n})["bugs"]
    lengths = []
    for b in bugs:
        comments = get(f"bug/{b['id']}/comment", {})["bugs"][str(b["id"])]["comments"]
        lengths.append(len(comments[0]["text"]))
    return lengths


def main():
    record = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "source": BZ,
        "filters": {"type": "defect", "resolution": "FIXED", "created_from": CREATED_FROM},
        "groups": {g: [f"{p} :: {c}" for p, c in comps] for g, comps in GROUPS.items()},
        "counts_by_severity": {},
        **{f"{kw}_keyword_counts_by_severity": {} for kw in KEYWORDS},
        "description_chars_sample": {},
    }
    for group, comps in GROUPS.items():
        record["counts_by_severity"][group] = {s: count(comps, severity=s) for s in SEVERITIES}
        for kw in KEYWORDS:
            record[f"{kw}_keyword_counts_by_severity"][group] = {
                s: count(comps, severity=s, keywords=kw, keywords_type="allwords")
                for s in SEVERITIES
            }
        lengths = [n for s in ("S2", "S3", "S4") for n in description_lengths(comps, s)]
        record["description_chars_sample"][group] = {
            "n": len(lengths),
            "median": statistics.median(lengths),
            "max": max(lengths),
        }
    OUT.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(record, indent=2))


if __name__ == "__main__":
    main()
