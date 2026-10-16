# Before making the repository public

Decided 2026-10-16: the repository is **private during the research** and
will be **made public afterwards**. These steps are required before
publishing. They implement Mozilla D4 and kernel K5.

## 1. Third-party bug text must not be published

Bug-report text from Mozilla Bugzilla and the Linux kernel Bugzilla is
in these tracked files:

| File | Why it holds text |
|---|---|
| `research/data/mozilla/dataset.jsonl` | cleaned bug text |
| `research/data/mozilla/mozilla_validation_raw_responses.jsonl` | every call records its input state (bug text + adapter) |
| `research/data/mozilla/mozilla_smoketest_raw_responses.jsonl` | same |
| `research/data/kernel/dataset.jsonl` | cleaned bug text |
| `research/data/kernel/kernel_*raw_responses.jsonl` (when created) | same |

**For the public version:**
- Replace each text with its bug ID, URL and `text_sha256`.
- Replace each raw response's `state` with its `input_hash`.
- Keep every Jev output.

The builders regenerate the text from the trackers, and the hashes prove
it matches.

## 2. Git history contains the text too

All of those files have been committed. Deleting them in a later commit
does **not** remove them from history. Choose one:

- **A (recommended).** Publish a **fresh repository**, starting from a
  single commit of the scrubbed tree. Keep this private repository as the
  full audit trail, available on request.
- **B.** Rewrite history (`git filter-repo`) to replace the files in
  every commit, then force-push. This is destructive, changes every
  commit hash cited in the docs, and must be done on a clone.

## 3. Other checks

- `.env` (API key) is gitignored and has never been committed (verified
  2026-10-16). Re-check with `git log --all -- .env`.
- Search the published tree for emails and names:
  `grep -rEn "[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[a-z]{2,}"`, and the
  datasets' scrub audits.
- **Before publishing, confirm that TypeSafe's terms allow publishing a
  benchmark of Jev.**
- Commit hashes cited in the docs refer to this private repository.
  Under option A, add a note that maps them.
