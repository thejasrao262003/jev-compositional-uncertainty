# Mozilla Bugzilla Extension — Proposal for Review

Status: **proposal, not approved.** No Jev API call has been made for
this work, and none is requested until this document is reviewed. The
only network access so far is read-only Bugzilla queries:
- counts: `research/src/mozilla_feasibility_counts.py` →
  `research/results/mozilla_feasibility_counts.json`
- the cleaned Part A dataset, built so it can be reviewed alongside
  this proposal: `research/src/build_mozilla_dataset.py` →
  `research/data/mozilla/` (§2.7)

Building the dataset before approval goes ahead of the usual "protocol
first" order. It is offered for inspection only. If the design changes
in review, the dataset is rebuilt; nothing has been run against it.

Proposed by: Tushar (tushar.m@mobisy.com). Reviewer: Thejas.

## 0. Summary

Two separate pieces of work, both using public Mozilla Bugzilla data.
They are independent: either can be approved without the other.

| Part | What it does | What it touches | Jev calls |
|---|---|---|---|
| **A. Realistic validation study** | Runs the same 3-node chain on real, human-labeled Firefox bug reports | New, separate artifacts only. Nothing frozen changes | 2,020 (202 bugs as built), only after approval |
| **B. Vocabulary source for the template grammar** | Uses Mozilla bug summaries as a provenance-tracked source for the grammar's short content vocabularies (grammar spec §5, Option A) | Input to the open §5 decision. Grammar is not frozen, so nothing frozen changes | 0 |

Part A fills a gap the project has already named: the research plan
(§5, "Assumptions that still need validation") requires "at least one
realistic/externally-validated task before the final paper," and none
has been chosen. Part B targets the one open decision blocking the
template grammar: proposition-level capacity in the blocking pool.

## 1. Why Mozilla Bugzilla

1. **Severity labels match the existing `score` scale almost word for
   word.** Mozilla's own definitions
   (wiki.mozilla.org/BMO/UserGuide/BugFields#bug_severity):

   | Mozilla | Mozilla definition (verbatim) | Project level (`severity_criteria`) |
   |---|---|---|
   | S1 | "(Catastrophic) Blocks development/testing, may impact more than 25% of users, causes data loss, likely dot release driver, and no workaround available" | 2: "Blocking issue; no workaround exists" |
   | S2 | "(Serious) Major functionality/product severely impaired or a high impact issue and a satisfactory workaround does not exist" | 2 |
   | S3 | "(Normal) Blocks non-critical functionality or a work around exists" | 1: "Broken or degraded feature, but a workaround exists" |
   | S4 | "(Small/Trivial) minor significance, cosmetic issues, low or no impact to users" | 0: "Cosmetic; no impact to functionality" |

   The workaround / no-workaround boundary is the same one the project's
   scale uses. That's unusual for public bug data.
2. **Component labels give a natural `choice` target**: Networking
   components vs. Storage components, which mirrors the existing
   `network` / `database` routing question.
3. **Labels are set by human triagers**, independent of anything this
   project built. That is the property construction-defined data can't
   have.
4. **Public, free, and queryable** through a REST API with no key.

## 2. Part A — Realistic validation study

### 2.1 Research questions (descriptive; not hypothesis tests)

Each is a direct re-check, on real text, of a finding so far established
only on constructed items:

- **RQ-A1 (severity lean).** In the first calibration pilot, `score`
  never chose level 0: all 10 cosmetic items were rated 1 or 2 (5 and
  5). Phase B found `score` aligned with the highest-severity sentence
  on 6/6 items. *Does the upward lean appear on bugs triaged S4?*
- **RQ-A2 (high-confidence errors).** Stage 1 found a `choice` subgroup
  with mean confidence 0.92 and accuracy 2/6. Strategy 4a's `≥ 0.90`
  trigger rests on it. *On real text, is `choice` agreement lower in
  the ≥ 0.90 band than the confidence suggests?*
- **RQ-A3 (strategies).** *How do Strategies 1, 2 and 4a, exactly as
  frozen in Revision 10, behave on real inputs?* Reported descriptively.
  This study is **not** powered for, and **must not** be presented as,
  a replication of the Step 2 primary comparison.
- **RQ-A4 (repeat instability).** *What share of real inputs are
  `repeat_unstable` at each node?*

### 2.2 Node mapping

The chain, adapter and repeat structure are the same as the first
calibration pilot (3 nodes × 3 repeats, each node's input gets the
upstream modal decisions appended). Only the input text and label
sources change.

| Node | Question (same wording as pilot unless noted) | Label source |
|---|---|---|
| 1 `choice` | "Which subsystem is most likely responsible for this incident?" Criteria: `network` (unchanged); `database` → renamed **`storage`**, description "Issues with local data storage: databases, IndexedDB, quota, caches, or persistence" | Component group (§2.3) |
| 2 `noul` | **Changed:** "Is this bug a regression (something that used to work and broke)?" | Bugzilla keyword `regression` |
| 3 `score` | Unchanged wording and criteria | Severity mapping, §1 table |

**Why `regression` and not `crash` for node 2** (data, not preference;
from `mozilla_feasibility_counts.json`):

| Severity | Crash-keyword rate (network) | Regression-keyword rate (network) |
|---|---:|---:|
| S2 | 84/160 = 53% | 72/160 = 45% |
| S3 | 90/738 = 12% | 152/738 = 21% |
| S4 | 12/301 = 4% | 115/301 = 38% |

`crash` is close to a proxy for severity (53% → 4%), which would make
nodes 2 and 3 nearly redundant and confound `F`. `regression` occurs at
every severity level. The storage group shows the same pattern (crash
20/55 → 2/60; regression 25/55, 45/162, 24/60). **Decision for the
reviewer** (§5, D2).

**Target action.** `a* = F(c_2*, c_3*)` with `F` unchanged from §16.2,
reading `c_2* = 1` as "regression". So: blocking → escalate; degraded +
regression → defer; degraded, not regression → accept; cosmetic →
accept. Mozilla has no "unclear" label, so the `request_more_evidence`
branch is never a target here. That's disclosed, not patched.

### 2.3 Data

**Source.** bugzilla.mozilla.org REST API, public bugs only.

**Inclusion.** `type = defect`, `resolution = FIXED`, created on or
after 2021-01-01 (all on the S1–S4 scale; legacy blocker/critical/…
labels are excluded rather than mapped), severity ∈ {S1, S2, S3, S4}.

**Component groups** (frozen in the feasibility script):
- `network`: Core :: Networking, Networking: HTTP, Networking: DNS,
  Networking: Cookies.
- `storage`: Core :: Storage: IndexedDB, SQLite and Embedded Database
  Bindings, Storage: Quota Manager, Storage: localStorage &
  sessionStorage, Storage: Cache API.
- Excluded as ambiguous between the two groups: Networking: Cache,
  DOM: Networking.

**Available pool** (counts as of 2026-10-03, before exclusions):

| Group | S1 | S2 | S3 | S4 |
|---|---:|---:|---:|---:|
| network | 7 | 160 | 738 | 301 |
| storage | 0 | 55 | 162 | 60 |

**Exclusions, fixed before sampling and before any Jev output exists:**
0. Auto-filed CI test failures: keyword `intermittent-failure` or
   `intermittent-testcase`, a summary starting "Intermittent", "Perma"
   or "Permanent", or a description with the Treeherder "**Filed by:**"
   header. Their severity is a flaky test's priority, not user impact:
   S4 on these means "low-priority test failure", not "cosmetic".
   (Added after inspecting the first build; see §2.6a.)
1. Bugs filed by fuzzing (reporter is a known fuzzing account, or the
   description contains the fuzzing harness boilerplate). Their
   severity reflects security triage of an assertion, not user impact.
2. Descriptions under 100 characters after cleaning.
3. Bugs whose severity was changed after the first triage (the
   history endpoint gives this). The *current* severity is used for
   everything else. Count excluded under this rule is reported.

**Input text.** `summary + "\n\n" + first comment`, cleaned: URLs →
`[link]`, email addresses removed, fenced code blocks and stack frames
removed, user-agent lines removed, then truncated at 2,000 characters
on a sentence boundary. Median raw description length in a 48-bug
sample: 1,274 characters (network), 2,023 (storage).

**Sampling.** 6 cells (2 groups × 3 severity levels, S1+S2 merged as
level 2). **Target 40 bugs per cell, 240 total**, drawn by a seeded
shuffle (seed recorded in the manifest). If a cell has fewer than 40
after exclusions (storage S1+S2 is the risk: 55 before exclusions), the
cell takes every eligible bug and the shortfall is reported. No cell is
topped up from another. The regression label is recorded, not balanced.

**Text handling.** Bug text is public but user-authored. The cleaned
text is included in `dataset.jsonl` on this branch so it can be
reviewed. Emails are already replaced with `[email]` and URLs with
`[link]`. Whether it stays in git after merge is decision D4 (§5). If
not, the record keeps bug IDs, labels and `text_sha256`, and the builder
re-derives the text.

**The dataset is a snapshot.** Bugzilla is live: bugs get re-triaged,
edited and newly fixed, so re-running the builder later can select
different bugs. `dataset.jsonl` plus its hash in `dataset_hashes.json`
is the frozen artifact, not the query.

### 2.4 Calls and cost

| Arm | Calls |
|---|---:|
| Primary: 240 bugs × 3 nodes × 3 repeats | 2,160 |
| Label-wording check: 240 bugs × 1 `score` call with Mozilla's verbatim S-definitions as criteria (§2.5) | 240 |
| **Total** (at the 240-bug target; 2,020 at the 202 bugs as built, §2.6a) | **2,400** |

From the 524 project calls to date, mean input is 380 tokens per call.
Bug inputs are longer: about 650 tokens per call is assumed, so about
1.6M input tokens in total. At the blog's listed $0.042/MTok (not
verified against the console), that's under $0.10. At the observed
~6.5 s latency, it's about 4.3 hours sequential.

### 2.5 Analysis (all descriptive, fixed now)

- **Per node:** agreement with the Mozilla label, with Wilson 95%
  intervals. Called "agreement with Mozilla triage," never "accuracy."
- **`score`:** the full 3×3 confusion matrix (true level × modal Jev
  level), and **P(Jev level > Mozilla level)** per true level. RQ-A1 is
  answered by the S4 row. The label-wording arm repeats the S4 row
  using Mozilla's own definitions as criteria. If the lean disappears
  there, it's a criteria-wording effect, not a `score` property, and
  must be reported that way.
- **`choice`:** agreement by confidence band, using both binning schemes
  from `stage1_h1h2b_analysis.py` (equal-width and equal-mass), plus the
  ≥ 0.90 band on its own (RQ-A2). Unified 2-term Brier and ECE, with the
  same conventions as Stage 1.
- **`noul`:** the same unified Brier and ECE, plus a reliability table.
- **Strategies 1, 2, 4a:** `P(Y_decision = 1)`, coverage, and the 2×2
  discordance tables against Strategy 2. Reported as counts. Not tested.
- **Repeat instability:** rate per node.

### 2.6 Known limitations (to carry into any write-up)

1. **Possible training contamination.** Bugzilla has been public for
   decades, and Jev may have seen these bugs. Jev's training cutoff
   isn't known. Mitigation: report results separately for bugs created
   in the most recent 12 months, as a descriptive split. This reduces
   the risk but doesn't remove it.
2. **Label noise.** Severity is one triager's judgment, and S3 is the
   usual default. Disagreement with Jev isn't automatically Jev's
   error. That's why the wording is "agreement."
3. **S4 is broader than "cosmetic."** It also covers "minor
   significance, low or no impact," so some level-1 answers on S4 bugs
   are defensible. The label-wording arm (§2.5) exists for this reason.
4. **Domain shift from the constructed data.** Browser bug reports, not
   ops incidents. Results can't be pooled with the pilot's, only set
   side by side.
5. **Node 2's question differs** from the constructed chain's
   (regression vs. customer-facing), so `F`'s action semantics differ
   too.
6. **Not powered.** About 200–240 bugs gives roughly ±0.10 Wilson half-width on a
   per-level proportion at n ≈ 80. That's enough to see whether the S4
   lean recurs, not to compare strategies.

### 2.6a The built dataset (2026-10-04)

Built by `build_mozilla_dataset.py` (seed
`mozilla-realistic-validation-v1`). **202 bugs, not 240.** Two storage
cells fell short. Per §2.3's rule, they took every eligible bug and
were not topped up.

| Cell | Eligible | Intermittent | Fuzzing | Too short | Re-triaged | **Selected** | Shortfall |
|---|---:|---:|---:|---:|---:|---:|---:|
| network, level 2 (S1+S2) | 167 | 0 | 1 | 6 | 9 | **40** | 0 |
| network, level 1 (S3) | 738 | 2 | 3 | 6 | 1 | **40** | 0 |
| network, level 0 (S4) | 301 | 55 | 0 | 9 | 2 | **40** | 0 |
| storage, level 2 (S1+S2) | 55 | 4 | 12 | 4 | 7 | **28** | 12 |
| storage, level 1 (S3) | 162 | 4 | 1 | 11 | 1 | **40** | 0 |
| storage, level 0 (S4) | 60 | 44 | 0 | 2 | 0 | **14** | 26 |

Exclusion counts cover only the bugs inspected before a cell filled
(the shuffle stops at 40).

**Build history, disclosed.** The first build (211 bugs) had no
intermittent exclusion. Reading its output showed that auto-filed CI
test failures made up 23 of its 63 S4 bugs. Those would have corrupted
RQ-A1, which is about the S4 row. Exclusion 0 was added and the dataset
rebuilt. The same pass found 22 email addresses written as
`name [at] host`, which the email scrub missed; that is fixed too. This
happened before any Jev call, by reading the data, not from any result.

Observations for review:
- **Most S4 bugs in these components are CI noise.** Intermittent
  failures were 55 of 106 inspected network S4 bugs and 44 of 60
  storage S4 bugs. Real, human-reported S4 storage bugs are scarce
  (14), so the storage S4 cell is small. RQ-A1 should be read mainly
  from the network S4 cell (40).
- **Storage's serious bugs include many fuzzing finds**: 12 of 55
  excluded on that ground.
- **The text sometimes states the label outright.** 19 descriptions
  contain "regress", and 12 of those carry the `regression` keyword. One
  (bug 2024666) discusses its own severity. These are left in: this is
  what real input looks like. The analysis should report agreement with
  and without them.
- Labels: 52 of 202 are regressions, 43 are crash-tagged, and 54 were
  created in the most recent 12 months.
- Cleaned text: 151–2,000 characters, median 553. No URLs, email
  addresses or intermittent-failure reports remain (checked).

At 202 bugs the call count is 202 × 9 + 202 = **2,020**, not 2,400.

### 2.7 Artifacts (all new; nothing existing is modified)

```
research/src/mozilla_feasibility_counts.py              (exists)
research/results/mozilla_feasibility_counts.json        (exists)
research/src/build_mozilla_dataset.py                   (exists)
research/data/mozilla/dataset.jsonl                     (exists; cleaned bugs + labels)
research/data/mozilla/dataset_manifest.json             (exists; per-cell + exclusion counts)
research/data/mozilla/dataset_hashes.json               (exists)
research/src/run_mozilla_validation.py                  (after approval)
research/results/mozilla_validation_execution_manifest.json
research/results/mozilla_validation_report.md
```

Same discipline as the rest of the repo: the manifest is built and
hash-locked → runner self-tests → dry-run preflight with
`requests.post` patched to raise → explicit approval → live run behind
`--live --confirm-2020-mozilla-calls` (the count for the built 202-bug
dataset, §2.6a).

## 3. Part B — Mozilla as a vocabulary source for the grammar

### 3.1 The problem it addresses

Grammar spec §5: at the proposition level, `severity:2` (blocking) has
160 distinct propositions against 256 needed at N ≈ 738, because its
**function** slot has only 10 entries. The spec estimates about 16
functions in total at N ≈ 738 and about 27 at N = 1,260, so 6 to 17
new ones. The same spec
recommends Option A: enlarge the content vocabularies, keeping them a
finite, reviewable list.

Mozilla bug summaries are a large, human-written source of real product
functions and real defect descriptions. Using them changes the
vocabulary's provenance from "written by the implementing assistant"
(§2 of the grammar spec) to "adapted from cited, human-written bug
reports." That's a stronger provenance statement.

### 3.2 What it can and can't supply

| Pool | Mozilla source | Useful? |
|---|---|---|
| `severity:2` function slot | S1/S2 summaries | **Yes.** This is the binding shortfall |
| `severity:0` element/defect slots | S4 summaries ("misaligned", "wrong color", "truncated") | Yes, for realism. Not a capacity shortfall |
| `severity:1` workaround slot | S3 descriptions mentioning a workaround | Yes, for realism |
| `impact:0`, `impact:unclear` | none | **No.** Bugzilla has no internal vs. customer-facing notion. These pools still need authoring |
| `routing` | Networking/Storage summaries | **No, deliberately.** See §3.3 |

### 3.3 Procedure

1. **Mine only outside the routing groups.** Severity vocabulary is
   taken from components that are neither networking nor storage (e.g.
   Firefox :: Address Bar, Toolkit :: Downloads, Core :: Printing,
   Firefox :: PDF Viewer). This keeps routing cues out of severity
   sentences at the source. The existing A5 audit (`NETWORK_CUES`,
   `DATABASE_CUES`) still runs and is still gating.
2. **Seeded candidate list.** Fetch S1/S2 summaries (for functions) and
   S4 summaries (for cosmetic elements and defects), shuffled with a
   recorded seed.
3. **Human curation.** A person (not Jev, and not the implementing
   assistant generating freely) reads the list in order and extracts
   generic, domain-neutral noun phrases that fit the existing slot. For
   example, a summary about downloads silently failing becomes the
   function "file downloads"; a summary about broken print layout
   becomes "printing". Browser-specific jargon is dropped.
4. **Provenance per phrase.** Each added vocabulary entry records the
   Bugzilla ID(s) it was adapted from, in the generator source.
5. **Re-run every grammar audit** (A2–A9), with A9's proposition-level
   recount as gating, as Option A requires.

### 3.4 What this doesn't change

The grammar remains a finite, fully listed vocabulary expanded
mechanically. No text enters the grammar without curation. Jev authors
nothing (grammar spec §9). The second calibration pilot, `d_template`,
and N are unaffected except through the enlarged vocabulary that §5
already calls for.

## 4. Relationship to the existing plan

- **Part A** is a separate study with separate artifacts. It doesn't
  touch Revision 10, the frozen pilot, or Step 2's power analysis, and
  its data must never be used to set any Step 2 threshold or constant.
  That would breach the pilot's prohibited-use list in spirit, even
  though this isn't pilot data.
- **Part B** feeds the open grammar decision (§5). It applies only if
  Option A is chosen.
- **Ordering.** Part A can run in parallel with the grammar work. Part
  B must finish before the grammar is frozen.

## 5. Decisions requested from the reviewer

| # | Decision | Proposed default |
|---|---|---|
| D1 | Approve Part A's design (§2) for manifest-building? This does not yet authorize calls | Yes |
| D2 | Node 2 label: `regression` or `crash` | `regression` (§2.2 table) |
| D3 | Include the 240-call label-wording arm? | Yes |
| D4 | Keep the cleaned bug text (`dataset.jsonl`) and future raw responses in git after merge, or strip to IDs + hashes | Keep: it's public data with emails and URLs removed. Confirm Bugzilla's content terms before any public release of the repo |
| D5 | Approve Part B as the source for grammar Option A's blocking-function expansion | Yes, if Option A is chosen |
| D6 | Who does Part B's curation (§3.3 step 3) | Tushar |

## 6. Next steps if approved

1. Review the already-built dataset (`research/data/mozilla/`). Spot-
   check cleaning quality and the cell shortfalls in
   `dataset_manifest.json`, then freeze it (or rebuild it if the design
   changes).
2. Write `run_mozilla_validation.py` by adapting the first pilot's
   runner. Self-tests and a dry-run preflight follow.
3. Ask for explicit live authorization for the 2,020 calls.
4. In parallel: Part B curation → grammar audits → feed into the §5
   decision.
