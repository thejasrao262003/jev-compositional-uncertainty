# Linux Kernel Bugzilla Replication — Proposal for Review

Status: **Revision 1 (decisions K1–K6 fixed); no Jev call made.** The dataset, its
builder, the feasibility counts, the runner, its self-tests and the
dry-run preflight are done (§8). The **2,160** live calls (and the
216-call smoke test that would come first) still need explicit,
separate approval (§10, K1). The only network access so far is public,
read-only queries to `https://bugzilla.kernel.org/rest` (User-Agent set,
0.5 s between requests, limit/offset paging).

Replicates: `research/methodology/mozilla_realistic_validation_proposal.md`
(Part A, Revisions 1–3). Feasibility survey:
`research/results/second_dataset_feasibility.md`.

As with Mozilla, the dataset is built before approval so it can be
inspected alongside this proposal. If the design changes in review, the
dataset is rebuilt; nothing has been run against it.

## Revision 1 — decisions K1–K6 (2026-10-16), fixed before any Jev call

Decided on the recommendations recorded in the session log. All of the
following are **pre-registered descriptive subsets**. None replaces `all`
as the primary population. They are coded in `run_kernel_validation.py`
`SUBSETS` and shown in the dry-run's `subset_sizes`.

| # | Decision | Implementation |
|---|---|---|
| K1 | Approved as staged: **smoke test first** (24 bugs, 216 calls), the full run (2,160) separately | Each live step still needs its own explicit authorization. Not yet given. |
| K2 | Wording arm dropped (§4) | Unchanged |
| K3 | `cf_regression = ---` stays coded 0 | **New subset `regression_field_set`** (Yes/No only, n = 146; 94/240 = 39% unset) |
| K4 | `no_routing_cue_extended` kept as secondary | n = 26: descriptive only, too small for any per-cell reading |
| K5 | Cleaned text stays in git **while the repository is private** (it is: not publicly resolvable on GitHub) | If the repo is ever made public, replace the text with bug IDs + `text_sha256` before publishing. The builder regenerates the text. Same rule proposed for Mozilla D4. |
| K6 | Truncation rule unchanged; no log-stripping arm | **New subsets `hard_cut` (49) / `not_hard_cut` (191) and `log_dominated` (log share ≥ 0.5, 41) / `not_log_dominated` (199)** |

**Also pre-registered:**
- **Severity changes:** `severity_changed_after_filing` (15) /
  `severity_as_filed` (225). Those 15 labels may be a maintainer's rather
  than the reporter's.
- **Routing question:** the storage criterion's browser-oriented wording
  ("IndexedDB, quota") is kept unchanged so the comparison with Mozilla
  holds. It is a disclosed loose fit for disk and filesystem bugs.
- **Memorization:** `recent_since_2018` (n = 35) is reported
  descriptively. It is too small to rule memorization out, and is
  stated as such.

Self-test (11/11) and dry-run pass with these subsets. No Jev call has
been made.

## 1. Purpose

The Mozilla study checks, on real text, findings that were established
only on constructed items: `score`'s upward lean on low-severity input
(RQ-A1), high-confidence `choice` errors (RQ-A2), how the strategies
behave on real inputs (RQ-A3), and repeat instability (RQ-A4). One
tracker is one labeling process. This study runs **the same chain, the
same questions and the same analysis code** on an independent tracker,
the Linux kernel Bugzilla, whose labels come from a **different
process**: the reporter, not a triager.

That difference is the point and the caveat at once:
- If a pattern (e.g. the lean on the lowest level) appears against both
  Mozilla's owner-assigned S1–S4 and the kernel's reporter-set severity,
  it is less likely to be an artifact of one labeling process.
- Agreement here means **agreement with the person who filed the bug**.
  Everywhere the Mozilla proposal says "agreement with Mozilla triage",
  this study says "agreement with the reporter-set label".

**Nothing is tuned.** No threshold, strategy rule, constant, question
wording or reduction rule is changed for this study, and **its results
must not be used to set any Step 2 threshold or constant**, exactly as
for Mozilla (Mozilla proposal §4).

## 2. What is identical to Mozilla, and what differs

| Element | Mozilla | Kernel | Same? |
|---|---|---|---|
| Chain | choice → noul → score, 3 repeats each | same | **identical** (imported) |
| Questions | `CHOICE_Q`, `NOUL_Q`, `SCORE_Q` | the same Python objects, imported | **identical** |
| Adapter | `node_state` (incl. "undetermined") | imported | **identical** |
| Reduction, Strategies 1 / 2 (Rev 11) / 4a (Rev 11) / 5 / Rev 10 versions | frozen modules | imported, hash-pinned | **identical** |
| Analysis (`analyze`) | `run_mozilla_validation.analyze` | the same function, wrapped (§5) | **identical** |
| Cleaning + truncation | `build_mozilla_dataset.clean` | imported, hash-pinned | **identical** |
| Cells | 2 groups × 3 levels, target 40, seeded shuffle | same | identical rule |
| Routing groups | Core :: Networking* vs Storage* | §3.2 | data source |
| Severity mapping | S1+S2→2, S3→1, S4→0 | blocking+high→2, normal→1, low→0 | data source |
| Regression label | keyword `regression` | `cf_regression == "Yes"` | data source |
| Label-wording arm | Mozilla's verbatim S4→S1 definitions | **dropped** (§4) | differs |
| Recent subset | last 12 months | created ≥ 2018-01-01 | differs (volume) |
| Extra privacy step | — | kernel trailer lines and reporter/assignee names scrubbed | addition |
| Fuzzing markers | Mozilla list | Mozilla list + `syzkaller`, `syzbot` | addition |

## 3. Data

### 3.1 Source and inclusion
bugzilla.kernel.org REST (Bugzilla 5.1.1), public bugs only. Resolution
`CODE_FIX` or `PATCH_ALREADY_AVAILABLE` (the kernel's "fixed").
Severity ∈ {blocking, high, normal, low}; `enhancement` is excluded (not
a defect). No creation-date lower bound (the kernel tracker's volume is
too low; see §7 on old bugs).

### 3.2 Node mapping and labels

| Node | Label source |
|---|---|
| 1 `choice` | **network** = product *Networking* (all components: IPV4, IPV6, Netfilter/Iptables, Wireless, Other) + product *Drivers* components *Network*, *network-wireless*, *network-wireless-intel*. **storage** = product *IO/Storage* (all components) + product *File System* components *ext4*, *btrfs*, *XFS*. *File System :: NFS / NFSD* excluded: ambiguous between the two. |
| 2 `noul` | `cf_regression == "Yes"` → 1; `"No"` or unset (`---`) → 0. Reporter-set. |
| 3 `score` | blocking + high → 2; normal → 1; low → 0. Reporter-set; `normal` is the default. |

Target action `a* = F(c2*, c3*)` with `F` unchanged (§16.2), as for
Mozilla. `request_more_evidence` is never a target.

### 3.3 Available pool (fixed bugs, all years; `kernel_feasibility_counts.json`)

| Group | level 2 | level 1 | level 0 | of which since 2018 (2 / 1 / 0) | `cf_regression = Yes` (2 / 1 / 0) |
|---|---:|---:|---:|---:|---:|
| network | 512 | 1,617 | 99 | 116 / 308 / 7 | 123 / 444 / 13 |
| storage | 338 | 1,092 | 56 | 50 / 187 / 7 | 76 / 257 / 3 |

Every cell has ≥ 40; storage level 0 is the tightest at 56.

### 3.4 Exclusions (fixed before sampling and before any Jev output)
The Mozilla rules, applied with the Mozilla code or its direct analogue:
0. Auto-filed CI failures: Mozilla's summary prefixes ("intermittent",
   "perma ", "permanent") and description marker. The kernel tracker has
   no intermittent keywords, so the keyword test is dropped.
1. Fuzzing: Mozilla's markers plus `syzkaller` / `syzbot` (the kernel's
   fuzzers), in the first comment or (kernel markers) the summary.
2. Body under 100 characters after cleaning (same measure).
3. Severity changed **away from a deliberate value** (blocking, high,
   low, enhancement) after filing. Moving from the default `normal` is
   allowed, mirroring Mozilla's allowance for moves from `--`/`normal`.
   Who made a change is never read or stored. Per-bug
   `severity_changed_after_filing` is recorded so the "reporter-set"
   claim can be checked on the built data.

### 3.5 Input text (same rule as Mozilla, stated)
`summary + "\n\n" + first comment`, after a kernel privacy pre-step
(below), cleaned by Mozilla's `clean()` unchanged: fenced code blocks,
Mozilla-regex stack-frame lines, user-agent and attachment lines
removed; URLs → `[link]`; emails incl. `name [at] host` → `[email]`;
then **truncated at 2,000 characters, at the last ". ", ".\n" or blank
line if one falls after character 1,000, otherwise by a hard cut.**

Privacy pre-step (hard rule: no reporter/assignee emails or names in any
file): kernel patch trailers (`Signed-off-by:`, `Reported-by:`, `Cc:`,
`From:` …) are dropped; reporter/assignee real names and login handles
are fetched **in memory only** and replaced by `[name]`, case-
insensitively: full names, login handles (≥ 4 characters) and name
parts (≥ 3 characters, not a stopword or common word). Role accounts
such as "Default virtual assignee for …" are skipped; any residual
token containing `@` becomes `[email]`. Records carry only bug id, URL,
group, component, severity, level, regression, creation time, flags,
truncation statistics, text and its hash; the preflight rejects any
other field and any email-like string.

### 3.6 Sampling
Seed `kernel-replication-v1`, one seeded shuffle per cell over the
bug-id-sorted pool, first 40 eligible bugs taken; no top-ups; regression
recorded, not balanced. The dataset is a snapshot: `dataset.jsonl` plus
its hash is the frozen artifact, not the query.

### 3.7 The built dataset

| Cell | Eligible | Intermittent | Fuzzing | Too short | Re-triaged | **Selected** |
|---|---:|---:|---:|---:|---:|---:|
| network, level 2 | 512 | 0 | 0 | 1 | 0 | **40** |
| network, level 1 | 1,617 | 0 | 0 | 2 | 0 | **40** |
| network, level 0 | 99 | 0 | 0 | 2 | 0 | **40** |
| storage, level 2 | 338 | 0 | 0 | 0 | 0 | **40** |
| storage, level 1 | 1,092 | 1 | 0 | 0 | 0 | **40** |
| storage, level 0 | 56 | 0 | 0 | 0 | 0 | **40** |

**240 bugs, no shortfall** (Mozilla: 202). Labels: 46/240 regressions
(network 10 / 9 / 6, storage 8 / 11 / 2 for levels 2 / 1 / 0); 35 created
since 2018; 15/240 had severity changed after filing, always from the
default (none was re-triaged away from a deliberate value).

**Severity changes.** 15/240 had severity changed after filing, every
one a move away from the default `normal` (12 to `low`: 7 network, 5
storage; 3 to `high`). Under the Mozilla rule these are allowed (a first
setting of a non-default value), and none was re-triaged away from a
deliberate value. Who made the change is not read, so for these 15 the
label may be a maintainer's, not the reporter's. They are flagged
(`severity_changed_after_filing`) and can be split out descriptively.

**Truncation (Mozilla's rule, unchanged).** 97/240 texts exceed 2,000
characters after cleaning (median before truncation 1,483; max 54,595).
48 are cut at a sentence or paragraph boundary and **49 by a hard cut**
(Mozilla: 3 of 202). The difference is the text, not the rule: kernel
reports are long log pastes with no ". " or blank line in the second
half of the window (hard-cut texts have a median of 4,116 characters
before truncation). Final length: 170–2,000, median 1,311 (Mozilla 553).

**Log-dominated texts.** 41/240 have ≥ 50% of non-blank lines matching
a log pattern (dmesg timestamps, oops/register lines, `func+0x../0x..`
frames, syslog prefixes); 29 of them are also hard-cut. They are **not
excluded and not cleaned further**: the replication keeps Mozilla's
cleaning so that only the data source changes, and the log share is
recorded per bug (`log_line_share`) for descriptive splitting. The
pattern is descriptive only and never used for selection.

**Privacy counts.** 7 trailer lines dropped; 85 reporter/assignee name
occurrences scrubbed in 22 bugs; 52 residual `@` tokens replaced. An
independent check re-fetched the reporter/assignee names for all 240
bugs (in memory) and found **0** bugs with any remaining name part or
handle (case-insensitive) and 0 email-like strings.

**Build provenance.** The REST responses were cached outside the
repository (scratchpad; never committed, because it holds unscrubbed
data) so cleaning changes can be re-run offline; a cached rebuild is
byte-identical. `dataset_manifest.json` records `fetch.cache_used`, the
number of cache hits vs. network fetches, and the fetch window
(2026-10-16, 14:04–14:27 UTC). The build history is disclosed: the first
three builds selected the same 240 bugs; the rebuilds changed only the
name scrub (the first build's scrub received no names because Bugzilla
returns `creator_detail` only with `creator`; the second over-scrubbed
role-account words; the third missed lowercase hostname / path forms).
All of this happened before any Jev call.

## 4. Why the label-wording arm is dropped

Mozilla's wording arm passed Mozilla's own published S1–S4 definitions
as `score` criteria, to separate a criteria-wording effect from a
`score` property. The kernel Bugzilla has **no official severity
definitions** comparable to Mozilla's: its field values (blocking, high,
normal, low) come with no published descriptive text, and reporters set
them without guidance. Any criteria we wrote would be ours, not the
tracker's, so the arm would no longer test "the labeler's own wording".
It is dropped rather than invented. Consequence: if the level-0 lean
appears here, this study cannot say whether it is a wording effect; the
Mozilla wording arm remains the evidence on that question.

## 5. Calls, cost and run time

| Arm | Calls |
|---|---:|
| 240 bugs × 3 nodes × 3 repeats | **2,160** |
| Smoke test first (first ⌈10%⌉ of each cell: 24 bugs × 9) | 216 (subset of the above data design, separate artifacts) |

Input is longer than Mozilla's (median cleaned text 1,310 vs 553
characters), so about 900 input tokens per call is assumed: about 2M
input tokens, under $0.10 at the blog's listed $0.042/MTok (not verified
against the console). At the Mozilla smoke test's measured 0.57 s per
call, the full run takes about **21 minutes**.

## 6. Analysis (descriptive; identical RQs)

**The analysis is Mozilla's `analyze()` itself**, imported from
`run_mozilla_validation.py` and called unchanged. Because that function
requires a wording arm, the kernel runner passes a **shadow** wording
arm (a copy of the score calls, never sent to Jev) and then deletes
every wording-derived output. A self-test proves the shadow cannot
change any reported number: correct, wrong and all-failed shadows give
byte-identical output. The lean key is renamed
`score_P_jev_above_reporter_label_by_true_level`.

Research questions, the same as Mozilla's with the reference renamed:
- **RQ-K1 (severity lean).** Does `score` lean upward on bugs whose
  reporter chose `low`? P(Jev level > reporter level) per true level,
  over stable decisions, unstable count alongside. The level-0 row is 80
  bugs (Mozilla's S4 row was 54).
- **RQ-K2 (high-confidence errors).** `choice` agreement in the ≥ 0.90
  band vs. its confidence; equal-width and equal-mass bands, ECE, unified
  Brier.
- **RQ-K3 (strategies).** Strategies 1, 2 (Rev 11), 4a (Rev 11), 5
  (proposed) and the Rev 10 versions, `P(Y_decision)`, coverage,
  discordance vs. Strategy 2, plus each rule's selectivity. `q` is the
  label base rate of non-accept `a*`. **Not externally validated** (`a*`
  is our `F` on reporter labels) and **not** a Step 2 replication.
- **RQ-K4 (repeat instability)** per node; `noul` spread.
- Data quality: failed calls per arm, all-failed nodes, undefined-`noul`
  occurrences.
- Per-cell figures lead; pooled figures describe this balanced design.

**Pre-registered subsets** (lexicons frozen in the runner):

| Subset | n | Why |
|---|---:|---|
| `all` | 240 | **Primary** |
| `no_routing_cue` | 191 | Mozilla's lexicons, unchanged |
| `no_routing_cue_extended` | 26 | Mozilla's lexicons + a frozen kernel lexicon (ext4, btrfs, nvme, scsi, wifi, iwlwifi, tcp, netfilter, block, mount, …). Added because Mozilla's browser-oriented lexicon misses most kernel cues. Secondary |
| `no_regression_wording` | 227 | no "regress" in text |
| `recent_since_2018` | 35 | partial contamination check (§7) |

## 7. Known limitations

1. **Reporter-set labels.** Severity and `cf_regression` are the
   reporter's own claims (0/75 in the survey and 1/48 in the feasibility
   sample had severity changed after filing; 15/240 in the built set,
   all moves from the default `normal`, by someone not identified, so
   those 15 may carry a maintainer's label). Agreement is with the filer,
   not with triage.
2. **`normal` is the default**, so level 1 mixes considered and
   never-considered severity. Expect it to be the noisiest level. Also,
   `cf_regression` unset (`---`) is read as "not a regression", so some
   regressions are labeled 0.
3. **Log-heavy text and truncation.** Kernel reports are dominated by
   dmesg output, oops traces and command output. Mozilla's cleaning
   (unchanged here) removes few of these lines, so 97/240 are truncated and 49 hard-cut (Mozilla: 3), and 41 are log-dominated. The
   model often sees logs rather than prose; the fixed 2,000-character
   cut can drop the human description that follows a log.
4. **Memorization risk is higher than for Mozilla.** Kernel bugs are
   old and widely mirrored (most selected bugs are from 2003–2014). The
   recent subset is small (35; level 0 especially) and reduces but does
   not remove the risk.
5. **Old bugs.** Most of the sample predates current kernel subsystems
   (IDE, early wireless stacks), a further domain shift.
6. **Question wording is browser-flavored.** `choice`'s storage
   criterion names "IndexedDB, quota, caches"; it is kept unchanged for
   the replication. A kernel-storage bug (disk, filesystem) still fits
   "local data storage … or persistence", but the fit is looser than on
   Mozilla.
7. **No wording arm** (§4).
8. **Not powered.** Worst-case Wilson 95% half-widths: ±0.11 per level
   (n = 80), ±0.15 per cell (n = 40), ±0.16 for the recent subset (n = 35).
9. **Fuzzing detection is marker-based** (as Mozilla); the name scrub is
   best-effort (third parties named in text are not scrubbed unless in a
   trailer line).
10. **Labels leak into text** (subsystem names, "regress"); measured by
    the subsets, not removed. Mozilla's browser-oriented lexicon marks
    only 49/240 kernel texts as cue-bearing (191 "cue-free"), against 214
    with the kernel lexicon added (26 cue-free). `no_routing_cue` is
    therefore not cue-free here; read `no_routing_cue_extended` (n = 26,
    ±0.19) for that question.

## 8. Artifacts (all new; no existing file modified)

```
research/src/kernel_feasibility_counts.py
research/results/kernel_feasibility_counts.json
research/src/build_kernel_dataset.py
research/data/kernel/dataset.jsonl            (240 cleaned bugs + labels)
research/data/kernel/dataset_manifest.json    (cells, exclusions, truncation, privacy counts, hashes)
research/data/kernel/dataset_hashes.json
research/src/run_kernel_validation.py         (--selftest, --mode dry-run; live guarded)
research/results/kernel_validation_preflight_report.json   (dry-run output)
```
Future, only after approval: `kernel_smoketest_*`,
`kernel_validation_raw_responses.jsonl`,
`kernel_validation_execution_manifest.json`, `kernel_validation_report.md`.

**Readiness.** `run_kernel_validation.py --selftest` passes 11
self-tests (§9) and `--mode dry-run` passes: 240 bugs, 2,160 planned
calls, dataset and builder hashes match, and 9 imported modules match
their pinned hashes. The live path requires `--mode live --live
--confirm-2160-kernel-calls`; the smoke test requires `--smoke-test
--live --confirm-216-kernel-smoke-calls`. Neither has been run.

## 9. Self-tests
- dataset tampering caught (on a temp copy; the real file is never written);
- each of the 9 pinned modules blocks the preflight if changed;
- plan = 2,160 calls; extra, missing, duplicate and wording cells rejected;
- questions and adapter are Mozilla's objects (identity), templates exact;
- synthetic perfect / perfectly-wrong data give agreement 1.0 / 0.0 and an
  exactly detected lean;
- the shadow wording arm cannot change any output; no wording or
  "mozilla" key survives; Mozilla's module state is restored;
- `a* = F(labels)`; no strategy sees a label;
- subset sizes non-empty;
- the Mozilla probe-found defects stay fixed (partial data refused, lean
  excludes unstable, all-failed nodes counted, raw data never
  overwritten, refused before `jev_client` is imported);
- the dataset has only whitelisted fields and no email-like strings;
- the preflight makes zero network calls (`requests` and raw sockets
  patched to raise); `jev_client` is never imported.

## 10. Decisions requested

| # | Decision | Proposed default |
|---|---|---|
| K1 | Approve the study and authorize the 216-call smoke test, then (separately) the 2,160 live calls | Yes, smoke test first |
| K2 | Drop the wording arm (§4) | Yes |
| K3 | Keep `cf_regression = ---` as 0 (vs. excluding unset bugs) | Keep as 0, disclosed |
| K4 | Add `no_routing_cue_extended` as a secondary subset | Yes |
| K5 | Keep the cleaned text in git after merge, or IDs + hashes only | Same decision as Mozilla D4 |
| K6 | Accept Mozilla's truncation rule unchanged despite 49 hard cuts, or pre-register a log-stripping variant as a separate arm | Unchanged (replication); report the hard-cut subset descriptively |
