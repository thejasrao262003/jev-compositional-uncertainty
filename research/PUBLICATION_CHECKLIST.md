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

## Release audit (2026-10-17)

Read-only audit of the tracked tree and history. Nothing was published.

**Secrets: pass.**
- `.env` was never committed (`git log --all -- .env` is empty).
- The API key string occurs in no commit of any branch. Searched with
  `git grep` across `git rev-list --all`.
- No other key-like strings were found.

**Bug text: §1's file list is out of date.** All files with bug text
(field `text`) or call inputs (field `state`) are listed below. Scrub
every one of them for the public tree.

| File | Field |
|---|---|
| `research/data/mozilla/dataset.jsonl` | text |
| `research/data/kernel/dataset.jsonl` | text |
| `research/data/heldout/mozilla_heldout.jsonl` | text |
| `research/data/heldout/kernel_heldout.jsonl` | text |
| `research/data/mozilla/mozilla_{validation,smoketest}_raw_responses.jsonl` | state |
| `research/data/kernel/kernel_{validation,smoketest}_raw_responses.jsonl` | state |
| `research/data/heldout/heldout{,_smoketest}_raw_responses.jsonl` | state |

- **Constructed content needs no scrub.** `research/data/characterization/*`
  holds `state` too, but it is our own constructed content, not bug text.
- **Cross-model outputs are clean.** The files in `research/data/openjev*`
  hold bug IDs and parsed answers only, with no text.

**Personal data:**
- **Bug-text files:** no email addresses (already scrubbed).
- **Elsewhere:** only the two authors' public emails (paper and README),
  and **one work email**,
  `research/methodology/mozilla_realistic_validation_proposal.md:18`
  (`tushar.m@mobisy.com`). Replace it or confirm with Tushar.
- **Commit authors:** 53 commits use a work email
  (`thejas.rao@lyzr.ai`). Under option A, history is not published, but
  choose the author identity for the fresh commit.

**Still open, and not checkable by audit:**
- TypeSafe's terms on publishing a Jev benchmark.
- The OpenJev weights licence is CC BY-NC 4.0. We publish outputs only,
  not weights; confirm that is acceptable.
- Choose a licence for the public repository.
- Map the cited commit hashes (option A).
