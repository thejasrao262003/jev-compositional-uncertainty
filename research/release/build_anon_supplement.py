"""Build the anonymized ARR supplementary archives (software + data) from a
clean `git archive` of HEAD. Nothing is uploaded or published.

  python3 research/release/build_anon_supplement.py OUT_DIR --deny TERM [--deny TERM ...]

- Bug-report text is removed: datasets drop `text` (keep `text_sha256`);
  raw responses drop `state` (keep `input_hash`).
- Files that carry author identities by design are excluded (named paper
  builds, release notes, this builder).
- Local machine paths are replaced with <LOCAL_PATH>.
- A pre-registration manifest lists each methodology/frozen artifact's first
  commit (hash, date; no author) and current SHA-256, and verifies every
  committed .sha256 file.
- Every output file is audited for the --deny terms, e-mail addresses and
  local paths; the build fails if anything is found.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import shutil
import subprocess
import tarfile
import zipfile
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXCLUDE = [
    "research/paper/latex/ieee.tex", "research/paper/latex/main.tex", "research/paper/latex/springer.tex",
    "research/paper/latex/ieee.pdf", "research/paper/latex/main.pdf", "research/paper/latex/springer.pdf",
    "research/paper/paper_draft.md", "research/PUBLICATION_CHECKLIST.md",
    "research/release/build_anon_supplement.py", ".gitignore",
]
DATA_PREFIXES = ("research/data/", "research/results/")
EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[a-z]{2,}")
LOCAL = re.compile(r"/(?:Users|home)/[^/\s\"']+")
ALLOWED_EMAILS = {"noreply@anthropic.com"}
SUPPLEMENT_README = """# Anonymized supplementary material

Two archives: `supplementary_software.zip` (code, protocols, paper sources)
and `supplementary_data.zip` (model outputs and analysis results). Both
contain this file and `PREREGISTRATION_MANIFEST.json`.

- **Bug-report text is not redistributed.** Datasets keep bug IDs, tracker
  URLs, labels and `text_sha256`; raw API responses keep every model output
  and `input_hash`, without the input text. The dataset builders in
  `research/src/` regenerate the texts from the public trackers, and the
  hashes verify them.
- **Pre-registration evidence.** `PREREGISTRATION_MANIFEST.json` lists, for
  every protocol and frozen artifact, the commit that added it and its date
  (author fields omitted), the SHA-256 of the committed file, a check of every
  committed `.sha256` lock, and timeline checks showing each protocol was
  committed before the results or data it governs.
- **Anonymization.** Author names are replaced by "Author A"/"Author B",
  e-mail addresses by <EMAIL> and local machine paths by <LOCAL_PATH>;
  where this changed a hashed file, the manifest says so and records the
  hash of the committed original. Named builds of the paper are omitted.
- **Reproducing the paper's numbers:** `research/paper/latex/make_figure_data.py`
  regenerates every table and figure input from `research/results/`, and
  `research/paper/latex/check_paper_numbers.py --acl` checks every reported
  number against the result files. No API key is included; re-running model
  calls requires the reader's own access.
"""
TIMELINE = [  # (protocol, first result it governs)
    ("research/methodology/workflow_risk_heldout_preregistration.md", "research/results/heldout_validation_results.md"),
    ("research/methodology/openjev_crossmodel_preregistration.md", "research/results/openjev_crossmodel_results.md"),
    ("research/methodology/intervention_test_preregistration.md", "research/results/intervention_test.json"),
    ("research/methodology/case_level_review_development_plan.md", "research/results/case_level_review_dev.json"),
    ("research/methodology/case_level_review_budget_check.md", "research/results/case_level_review_budget_check.json"),
    ("research/methodology/intervention_cost_sensitivity_plan.md", "research/results/intervention_cost_sensitivity.json"),
]
DATA_TIMELINE = [  # (frozen artifact, raw data it must precede)
    ("research/results/frozen_risk_estimator_v1.json", "research/data/heldout/heldout_smoketest_raw_responses.jsonl"),
    ("research/methodology/workflow_risk_heldout_preregistration.md", "research/data/heldout/heldout_smoketest_raw_responses.jsonl"),
]


def git(*args):
    return subprocess.run(["git", "-C", str(ROOT), *args], check=True, capture_output=True, text=True).stdout


def scrub_jsonl(raw: bytes) -> bytes:
    out = []
    for line in raw.decode().splitlines():
        if not line.strip():
            continue
        d = json.loads(line)
        if "text" in d and "text_sha256" in d:
            d.pop("text")
        if "state" in d and "input_hash" in d:
            d.pop("state")
        out.append(json.dumps(d, ensure_ascii=False))
    return ("\n".join(out) + "\n").encode()


def prereg_manifest(files: dict[str, bytes], original: dict[str, bytes]) -> dict:
    tracked = [p for p in files if p.startswith("research/methodology/") or
               (p.startswith("research/results/frozen_") and not p.endswith(".sha256"))]
    rows = []
    for p in sorted(tracked):
        log = git("log", "--diff-filter=A", "--format=%H %cI", "--", p).strip().splitlines()
        first = log[-1].split() if log else ["", ""]
        last = git("log", "-1", "--format=%H %cI", "--", p).strip().split()
        rows.append({"path": p, "first_commit": first[0][:12], "first_commit_date": first[1],
                     "last_commit": last[0][:12], "last_commit_date": last[1],
                     "sha256_committed": hashlib.sha256(original[p]).hexdigest(),
                     "archived_copy_redacted": files[p] != original[p]})
    checks = []
    for p in files:
        if p.endswith(".sha256") and p in original:
            parts = original[p].decode().split()
            want = parts[0]
            target = str(Path(p).parent / parts[1]) if len(parts) > 1 else p[: -len(".sha256")]
            if target not in original and target + ".json" in original:
                target += ".json"
            if target in original:
                got = hashlib.sha256(original[target]).hexdigest()
                checks.append({"hash_file": p, "target": target, "ok": got == want})
            else:
                checks.append({"hash_file": p, "target": target, "ok": False, "missing_target": True})
    order = []
    for proto, governed in TIMELINE:
        tp = git("log", "--diff-filter=A", "--format=%cI", "--", proto).strip().splitlines()
        tg = git("log", "--diff-filter=A", "--format=%cI", "--", governed).strip().splitlines()
        if tp and tg:
            a, b = datetime.fromisoformat(tp[-1]), datetime.fromisoformat(tg[-1])
            order.append({"protocol": proto, "governed": governed, "protocol_committed": a.isoformat(),
                          "governed_first_committed": b.isoformat(), "protocol_first": a <= b})
    for proto, raw in DATA_TIMELINE:
        tp = git("log", "--diff-filter=A", "--format=%cI", "--", proto).strip().splitlines()
        first_call = min(json.loads(l)["timestamp_utc"] for l in original[raw].decode().splitlines() if l.strip())
        a, b = datetime.fromisoformat(tp[-1]), datetime.fromisoformat(first_call)
        order.append({"protocol": proto, "governed": raw + " (first API call)", "protocol_committed": a.isoformat(),
                      "governed_first_committed": b.isoformat(), "protocol_first": a <= b})
    return {"timeline_checks": order,
            "note": "Commit hashes and dates from the authors' private repository (author fields omitted). "
                    "first_commit = when the file was added; protocols were committed before the data they govern. "
                    "sha256_committed hashes the committed file; where archived_copy_redacted is true, the archived "
                    "copy differs only by anonymization (names, e-mails, local paths), so its hash differs.",
            "artifacts": rows, "sha256_file_checks": checks}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--deny", action="append", default=[])
    ap.add_argument("--redact", action="append", default=[], help="NAME=ALIAS, applied case-insensitively")
    a = ap.parse_args()
    redact = [tuple(r.split("=", 1)) for r in a.redact]
    redacted_hashed = []
    out = Path(a.out)
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)

    tar = subprocess.run(["git", "-C", str(ROOT), "archive", "--format=tar", "HEAD"], check=True, capture_output=True).stdout
    files = {}
    with tarfile.open(fileobj=io.BytesIO(tar)) as t:
        for m in t.getmembers():
            if m.isfile() and m.name not in EXCLUDE:
                files[m.name] = t.extractfile(m).read()

    original_files = dict(files)
    for p in list(files):
        if p.endswith(".jsonl") and (b'"text_sha256"' in files[p] or b'"input_hash"' in files[p]):
            files[p] = scrub_jsonl(files[p])
        if p.endswith((".json", ".jsonl", ".md", ".py", ".tex", ".txt", ".sha256", ".bib", ".dat", ".csv")):
            before = files[p]
            txt = LOCAL.sub("<LOCAL_PATH>", before.decode())
            txt = EMAIL.sub(lambda m: m.group(0) if m.group(0) in ALLOWED_EMAILS else "<EMAIL>", txt)
            for name, alias in redact:
                txt = re.sub(re.escape(name), alias, txt, flags=re.IGNORECASE)
            files[p] = txt.encode()
            if files[p] != before and (p.endswith(".sha256") or p.startswith("research/methodology/") or
                                       p.startswith("research/results/frozen_")):
                redacted_hashed.append(p)

    manifest = prereg_manifest(files, original_files)
    files["PREREGISTRATION_MANIFEST.json"] = json.dumps(manifest, indent=2).encode()
    files["SUPPLEMENT_README.md"] = SUPPLEMENT_README.encode()

    problems = []
    deny = [d.lower() for d in a.deny]
    for p, b in files.items():
        try:
            s = b.decode()
        except UnicodeDecodeError:
            s = b.decode("latin-1")
        low = s.lower()
        for d in deny:
            if d in low:
                problems.append(f"{p}: deny term")
        for e in set(EMAIL.findall(s)) - ALLOWED_EMAILS:
            problems.append(f"{p}: email {e}")
        if LOCAL.search(s):
            problems.append(f"{p}: local path")
    bad_checks = [c for c in manifest["sha256_file_checks"] if not c["ok"]] + \
        [c for c in manifest["timeline_checks"] if not c["protocol_first"]]
    (out / "audit.json").write_text(json.dumps({"problems": problems, "bad_sha256": bad_checks,
                                                "n_files": len(files)}, indent=2))
    if problems or bad_checks:
        print(f"AUDIT FAILED: {len(problems)} problems, {len(bad_checks)} bad hashes (see audit.json)")
        return 1

    for name, pick in (("supplementary_software.zip", lambda p: not p.startswith(DATA_PREFIXES)),
                       ("supplementary_data.zip", lambda p: p.startswith(DATA_PREFIXES))):
        with zipfile.ZipFile(out / name, "w", zipfile.ZIP_DEFLATED) as z:
            for p in sorted(files):
                if pick(p) or p == "PREREGISTRATION_MANIFEST.json":
                    zi = zipfile.ZipInfo(p, date_time=(2026, 1, 1, 0, 0, 0))
                    z.writestr(zi, files[p])
    print(f"OK: {len(files)} files; {len(manifest['artifacts'])} pre-registration artifacts; "
          f"{len(manifest['sha256_file_checks'])} sha256 checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
