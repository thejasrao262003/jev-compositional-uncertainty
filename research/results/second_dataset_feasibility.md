# Second real-data dataset — feasibility survey (2026-10-16)

**Goal.** Replicate the Mozilla validation on an independent tracker with
the same three-step chain (subsystem routing, regression yes/no, 3-level
severity), using about 40 bugs per (subsystem × severity) cell. Only
public, read-only REST queries were made. No Jev calls.

**Requirements.**
- **Routing:** a network vs. storage component split, so the frozen
  routing question can be reused unchanged.
- **Regression:** a regression flag.
- **Severity:** a severity or priority field with at least 3 usable
  levels.
- **Counts:** about 40 per cell.
- **Label quality:** preferably set or checked by maintainers, not
  only by reporters.

| Tracker | Network / storage split | Regression flag | Severity levels | Cell counts (fixed bugs) | Who sets severity | Verdict |
|---|---|---|---|---|---|---|
| **Linux kernel Bugzilla** | Networking + Drivers/network* vs IO/Storage + ext4/btrfs/XFS | `cf_regression` Yes/No (about 20% Yes) | blocking / high / normal / low → 2 / 2 / 1 / 0 | net 512 / 1,617 / 99; storage 338 / 1,092 / 56 (levels 2 / 1 / 0) | **Reporter.** 0 of 75 sampled non-default bugs had severity changed after filing | **Feasible, with a label-quality caveat** |
| Apache JIRA (Kafka, HBase, Ignite, Cassandra) | Clean network vs storage components | Labels almost never used (1 in about 700) | Blocker … Trivial | Network level 0: 16, level 2: 28 (under 40) | Maintainers often adjust (12/30 Blockers changed by a non-reporter) | Fails on regression and on network counts |
| Kubernetes (GitHub) | `sig/network` vs `sig/storage` | `kind/regression`, rare (12 total) | `priority/*` (urgency, not severity) | Backlog cells 10–11 | Maintainers | Too thin; priority isn't severity |
| Fedora (Red Hat Bugzilla) | NetworkManager etc. vs lvm2/udisks2 etc. | `Regression` keyword, rare | Mostly "unspecified" | — | — | Fails on severity |
| WebKit Bugzilla | No network component ("Page Loading" closest) vs "Website Storage" | `Regression` keyword | Blocker … Trivial, mostly Normal | not counted | Reporter | Weak routing split |
| KDE, GNOME | No usable split; GNOME moved to GitLab | — | — | — | — | Not viable |

## Recommendation

**Use the Linux kernel Bugzilla as the second dataset, with the caveat
built into the claims:**
- **Routing:** component, as with Mozilla.
- **Regression:** `cf_regression`.
- **Severity:** blocking + high → 2, normal → 1, low → 0.
- **Cells:** 40 per cell, all 6 feasible. Storage level 0 is the
  tightest, with 56 available.

**Caveats to carry into the claims:**
1. **Kernel severity and the regression flag are the reporter's own
   claims.** Agreement there means agreement with the person who filed
   the bug, not with triage. That is a different reference from
   Mozilla's owner-assigned S1–S4. It makes the replication informative
   in a specific way: if `score`'s middle-compression appears against
   both references, it is less likely to be an artifact of one labeling
   process.
2. **Level 1 is the default value,** so it includes bugs whose severity
   was never considered. Expect it to be the noisiest level.
3. **Text is different:** descriptions are dominated by logs, stack
   traces and dmesg output. That needs a truncation rule fixed before
   any call, as for Mozilla.
4. **Training-data exposure:** kernel bugs are old and widely mirrored,
   so memorization risk is higher than for Mozilla. Keep the
   recent-bugs subset (counts since 2018 are smaller: 34–308 per cell).

**Next if approved:**
1. A pre-registered proposal mirroring Tushar's Mozilla proposal: the
   same analysis code and questions, with only the data source and the
   severity mapping changed.
2. A dataset builder.
3. Feasibility counts frozen as JSON.
4. A dry-run, then a smoke test.
5. The full run, about 2,424 calls.

Each live step needs separate authorization.
