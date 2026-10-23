"""Evidence audit, sections C and D of evidence_audit_and_baselines_plan.md.

C: linked-report overlap between held-out and development bugs, using the
   public Bugzilla REST APIs (read-only tracker requests; no model calls).
   Responses are cached under research/data/audit/ (IDs and link fields only).
D: AUROC by bug recency (contamination proxy), descriptive.

  .venv/bin/python research/src/evidence_audit.py [--fetch]
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

from sklearn.metrics import roc_auc_score

SRC = Path(__file__).resolve().parent
sys.path.insert(0, str(SRC))
import intervention_test as it  # noqa: E402
import run_heldout_validation as hv  # noqa: E402

ROOT = it.ROOT
CACHE = ROOT / "research" / "data" / "audit" / "bugzilla_links.json"
OUT = ROOT / "research" / "results" / "evidence_audit.json"
API = {"mozilla": "https://bugzilla.mozilla.org/rest/bug", "kernel": "https://bugzilla.kernel.org/rest/bug"}
RECENT_CUTOFF = "2025-10-17"  # filed within 12 months before the held-out sample was drawn (both trackers)
FIELDS = {"mozilla": "id,dupe_of,duplicates,see_also,blocks,depends_on,regressed_by,regressions",
          "kernel": "id,dupe_of,see_also,blocks,depends_on"}


def ids():
    out = {}
    for t in ("mozilla", "kernel"):
        dev = [json.loads(l)["bug_id"] for l in (ROOT / "research" / "data" / t / "dataset.jsonl").open()]
        held = [json.loads(l)["bug_id"] for l in (ROOT / "research" / "data" / "heldout" / f"{t}_heldout.jsonl").open()]
        out[t] = {"dev": dev, "held": held}
    return out


def fetch(all_ids):
    links = {}
    for t, d in all_ids.items():
        links[t] = {}
        allb = d["dev"] + d["held"]
        for i in range(0, len(allb), 100):
            chunk = allb[i:i + 100]
            url = f"{API[t]}?" + urllib.parse.urlencode({"id": ",".join(map(str, chunk)), "include_fields": FIELDS[t]})
            req = urllib.request.Request(url, headers={"User-Agent": "research-audit (read-only)"})
            with urllib.request.urlopen(req, timeout=60) as r:
                data = json.loads(r.read().decode())
            for b in data.get("bugs", []):
                rec = {}
                for f in FIELDS[t].split(",")[1:]:
                    v = b.get(f)
                    if v in (None, "", []):
                        continue
                    if f == "see_also":
                        v = [s for s in v if isinstance(s, str)]
                    rec[f] = v
                links[t][str(b["id"])] = rec
            time.sleep(1.0)
    return links


def linked_ids(rec, tracker):
    out = set()
    for f, v in rec.items():
        vals = v if isinstance(v, list) else [v]
        for x in vals:
            if isinstance(x, int):
                out.add(x)
            elif isinstance(x, str) and ("show_bug.cgi?id=" in x) and (("mozilla" in x) == (tracker == "mozilla")):
                try:
                    out.add(int(x.split("id=")[1].split("&")[0].split("#")[0]))
                except ValueError:
                    pass
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fetch", action="store_true")
    a = ap.parse_args()
    all_ids = ids()
    if a.fetch or not CACHE.exists():
        CACHE.parent.mkdir(parents=True, exist_ok=True)
        CACHE.write_text(json.dumps(fetch(all_ids), indent=1))
    links = json.loads(CACHE.read_text())
    res = {"status": "AUDIT / EXPLORATORY", "C_linked_reports": {}, "D_recency": {}}

    flagged = set()
    for t, d in all_ids.items():
        dev, held = set(d["dev"]), set(d["held"])
        pairs = []
        for h in held:
            for x in linked_ids(links[t].get(str(h), {}), t):
                if x in dev:
                    pairs.append([h, x])
        for dv in dev:
            for x in linked_ids(links[t].get(str(dv), {}), t):
                if x in held:
                    pairs.append([x, dv])
        pairs = sorted({tuple(p) for p in pairs})
        flagged |= {(t, h) for h, _ in pairs}
        res["C_linked_reports"][t] = {"held_out": len(held), "development": len(dev),
                                      "records_fetched": sum(1 for b in held | dev if str(b) in links[t]),
                                      "heldout_bugs_linked_to_a_dev_bug": len({h for h, _ in pairs}),
                                      "pairs": [list(p) for p in pairs]}

    # HR1 contrast without linked bugs (Jev, frozen estimator), descriptive.
    _, held, est = it.load_model("Jev 1.13")
    keep = [p for k, p in held.items() if (p["tracker"], p["bug"]["bug_id"]) not in flagged]
    y = [int(p["s1"] != p["a_star"]) for p in keep]
    e = [hv.risk(est, p, "DECISION") for p in keep]
    c = [-p["red"]["score"]["mean_confidence"] if p["red"]["score"]["mean_confidence"] is not None else 0 for p in keep]
    res["C_linked_reports"]["HR1_without_linked"] = {"n": len(keep), "auroc_E_dec": round(roc_auc_score(y, e), 3),
                                                     "auroc_final_step_conf": round(roc_auc_score(y, c), 3)}

    # D: recency split.
    for mname in ["Jev 1.13"] + it.ac.MODELS:
        _, held, est = it.load_model(mname)
        out = {}
        for t in ("mozilla", "kernel"):
            for recent in (True, False):
                S = [p for p in held.values() if p["tracker"] == t and
                     (p["bug"]["creation_time"] >= RECENT_CUTOFF) == recent]
                yy = [int(p["s1"] != p["a_star"]) for p in S]
                key = f"{t}:{'recent' if recent else 'older'}"
                if len(S) < 2 or not (0 < sum(yy) < len(yy)):
                    out[key] = {"n": len(S)}
                    continue
                out[key] = {"n": len(S), "interpretable": len(S) >= 30,
                            "auroc_E_dec": round(roc_auc_score(yy, [hv.risk(est, p, "DECISION") for p in S]), 3),
                            "auroc_final_step_conf": round(roc_auc_score(
                                yy, [-(p["red"]["score"]["mean_confidence"] or 0) for p in S]), 3)}
        res["D_recency"][mname] = out
    OUT.write_text(json.dumps(res, indent=2))
    print(json.dumps({k: v for k, v in res["C_linked_reports"].items() if k != "pairs"}, indent=1)[:1500])
    print(json.dumps(res["D_recency"]["Jev 1.13"], indent=1))


if __name__ == "__main__":
    main()
