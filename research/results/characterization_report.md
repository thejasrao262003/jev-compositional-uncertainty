# Step 0A — API Characterization Report

Run: 2026-09-21T15:48:30Z. 21 live calls to `https://api.typesafe.ai/v1/systemone`.
Raw data: `../data/characterization/raw_responses.jsonl` (source of truth),
`parsed_responses.jsonl` (derived), `run_metadata.json` (config, package
versions, status/parse counts). Client: `../src/jev_client/`.

**Scope discipline, as approved:** this report is strictly observational.
It makes **no calibration, accuracy, or reliability claims** — there is no
ground truth attached to any of these 21 items, and none should be inferred
from a model's output looking "plausible." Where a result is suggestive of
something Step 0B/Step 2 should investigate, it is stated as an open
question, not a finding.

## 1. Observed facts (what the live API actually did)

- **Endpoint/method/auth matched docs exactly**: `POST
  .../v1/systemone`, `Authorization: Bearer <key>`, JSON body
  `{state, model, questions}`. No 401s — the key loaded from `.env` worked.
- **Model version resolution confirmed**: requesting `"model": "jev-latest"`
  resolved to a concrete pinned string, `"jev-1.13.0"`, returned in every
  response's top-level `model` field. This is exactly the reproducibility
  hook the client was built to capture.
- **All three primitives matched their documented output shape** on all 19
  successful (HTTP 200) calls — zero `schema_mismatch` and zero
  undocumented/extra fields detected (the pydantic models use
  `extra="allow"`, so this is a real absence, not an artifact of a strict
  schema silently dropping fields). See `literature_matrix`-adjacent doc
  `../jev_api_notes.md` for the documented shapes being checked against.
- **`score`'s weighted-mean formula verified exactly**: for
  `score_many_levels`, probabilities `{0:0.29, 1:0.71, 2..4:0.0}` yield
  `score = 0*0.29 + 1*0.71 = 0.71` — matches the returned `score: 0.71`
  bit-for-bit (2 d.p.).
- **`probabilities` summed to 1.0** in every `choice`/`score` response
  checked.
- **`noul` is confirmed live to be a continuous value**, not binary:
  observed values included `0.99`, `0.47`, `0.42` — not just `{0.0, 1.0}`.
  No `confidence` field present on any `noul` answer, consistent with docs.
- **Determinism (n=1 item, 4 repeats):** the same exact request
  (`choice_ambiguous`, identical `state`+`questions`, identical
  `input_hash` across all 4 calls) returned **bit-identical** `choice`,
  `confidence`, and `probabilities` on 4/4 repeats. No numerical jitter
  observed. **Caveat: this is one item repeated 4 times, not a general
  claim about determinism across the input space** — see §4.
- **Errors, two distinct shapes observed:**
  - Unknown question `"type": "maybe"` → **HTTP 400**,
    `{"detail": {"error_type": "api_usage_error", "message": "Invalid request."}}`
    — a generic, low-detail app-level error.
  - Missing required `criteria` field on a `choice` question → **HTTP 422**,
    `{"detail": [{"type": "missing", "loc": ["body","questions","team","choice","criteria"], "msg": "Field required", ...}]}`
    — a structured, field-level validation error (the shape strongly
    resembles FastAPI/pydantic's default validation error format, though
    that's an inference, not confirmed — see §3).
  - Both are recoverable/parseable — this client's `parse_status="http_error"`
    path preserved both raw bodies correctly.
- **No retries fired** — no 429/5xx responses at this volume (21 calls in
  ~20 seconds). No network errors.
- **Latency:** 817–1100ms per call, no clear pattern by primitive type or
  input length at this small sample.
- **Token usage does not scale linearly with input character count.**
  E.g. `edge_empty_state` (0 input characters) still cost 352
  `input_tokens` — there is a substantial fixed overhead, presumably from
  the system-level scaffolding/instructions/criteria TypeSafe wraps around
  `state`. `output_tokens` roughly track the number of options/levels in
  `criteria` (52 for a 5-option choice vs. 35 for 2-option; 71 for the
  3-question mixed call) more than input length.
- **Undocumented behaviors observed (not stated one way or the other in
  the docs, so these are new facts, not contradictions):**
  - Empty `state` (`""`) is **accepted**, not rejected — HTTP 200 — and
    the `choice` response for the empty-state item came back with a
    visibly spread distribution (`{shipping:0.49, billing:0.44,
    returns:0.07}`, confidence `0.23`) rather than an error or a
    degenerate default.
  - A `choice` question with **only one option** in `criteria` is
    accepted, not rejected (docs state an upper bound of 255 options,
    silent on a lower bound) — returned `choice: "shipping"`,
    `confidence: 1.0`, `probabilities: {"shipping": 1.0}`.

## 2. Documentation-derived expectations that were confirmed

- Request/response field names and shapes (§1).
- `noul` has no separate `confidence` field (confirmed live, not just in
  docs — 4/4 `noul` responses had no `confidence` key).
- `choice`/`score` both expose `probabilities` + a derived `confidence`.
- Mixed-type requests (`choice`+`score`+`noul` in one call) are answered
  independently in a single response, as documented ("in parallel and in
  isolation") — `mixed_all_three` returned three independent, sensible
  answers keyed by question name in one call.

## 3. Unresolved ambiguities (need investigation, not yet answered)

- **The exact `confidence` formula is not reverse-engineered here** — only
  the qualitative direction (more spread → lower confidence) was
  eyeballed as plausible from a handful of examples. Deriving/confirming
  the exact formula (docs don't give one beyond "a statistic computed from
  the probability distribution") is not needed for Step 0A's scope and
  should not be assumed for Step 0B's analysis without further checking.
- **Whether the 422 error format is genuinely FastAPI/pydantic-shaped**, or
  coincidentally similar, is an inference from one example, not confirmed
  (would need e.g. a second, differently-malformed request to corroborate
  the pattern — not done here to keep the call budget small).
- **Whether a model version can be explicitly pinned** (vs. always
  requesting the floating `"jev-latest"` alias) was not tested — no request
  used an explicit version string. This matters for Step 2 reproducibility
  and should be checked before the main experiment (try requesting
  `"model": "jev-1.13.0"` directly and confirm it's accepted/behaves
  identically).
- **Rate limits are entirely uncharacterized** — 21 calls in ~20s never
  triggered a 429. Step 0B's ~540-call design will need either a
  deliberately slower request rate or a dedicated small burst test before
  committing to the full run, to avoid discovering rate-limit behavior for
  the first time mid-audit.
- **Whether `probabilities` can ever be sparse/omit a listed option** is
  still unconfirmed — all observed `probabilities` dicts included every
  option/level from `criteria`, including ones at exactly `0.0`.

## 4. The one finding that should change Step 0B's design (not a calibration claim — an item-design finding)

Two of the four `basic_choice` items and the `repeated_identical` item were
deliberately hand-written to *feel* ambiguous (e.g., a support message that
plausibly touches both "returns" and "shipping"). **None of them elicited
an intermediate `confidence` value** — all came back `confidence: 1.0`
with a one-hot `probabilities` distribution. The one item that *did*
elicit a genuinely spread distribution was the **empty-state** edge case
(no input at all), and the two `noul` items I expected to be
borderline (`noul_ambiguous`, and `needs_escalation` inside the mixed
call) did come back intermediate (`0.47`, `0.42`).

This is a **characterization finding about item design, not a claim about
Jev's calibration**: hand-picking text that *reads as* ambiguous to a human
did not reliably produce intermediate model confidence for `choice`, at
least in this small sample. Two hypotheses, both untested by this run:
(a) `choice` may only report distributed probability when the *criteria
themselves* are close (e.g. near-synonymous option descriptions), not when
the *input text* is lexically ambiguous between otherwise-distinct
criteria; (b) 4 items is simply too few to conclude anything about how
often intermediate confidence occurs. **Recommendation: before running the
full ~540-call Step 0B design, run a small (~10–15 call) follow-up that
deliberately varies a controllable ambiguity parameter** (e.g., criteria
description overlap, or an explicit blend of two category exemplars in the
input) and checks whether intermediate confidence values become reachable
— otherwise Step 0B risks spending its full budget on items that all land
at `confidence≈1.0`, which would fail Gate C (below) regardless of
Jev's true calibration properties.

## 5. Failures / non-200 responses (complete list)

| test_group | HTTP status | Error body |
|---|---|---|
| `edge_invalid:edge_invalid_type` | 400 | `{"detail":{"error_type":"api_usage_error","message":"Invalid request."}}` |
| `edge_invalid:edge_missing_criteria` | 422 | `{"detail":[{"type":"missing","loc":["body","questions","team","choice","criteria"],"msg":"Field required",...}]}` |

No timeouts, no network errors, no retries triggered, no 401/403/429/5xx
observed. Both failures were intentional (edge-case probes), correctly
recorded with raw body preserved, and both are informative rather than
inconclusive (see §1).

## 6. Gate assessment

| Gate | Verdict | Basis |
|---|---|---|
| **A — Semantic validity** | **PASS** | All documented shapes confirmed live across 19/19 successful calls; `score` formula verified exactly; no undocumented fields found (extra-field detection was active, not just absence of contrary evidence). |
| **B — Output comparability** | **OPEN BY DESIGN** | `choice`/`score` share a directly comparable representation (distribution + derived confidence); `noul` is confirmed live to structurally differ (bare scalar, no confidence field) — this is the confirmed premise of Candidate 3, not a gate failure. Not resolvable by characterization alone; it's the research question. |
| **C — Identifiability** | **NEEDS INVESTIGATION** | See §4. Hand-picked "ambiguous-looking" items did not reliably elicit intermediate `choice` confidence in this small sample; empty-state and `noul` items did show spread. A targeted ~10-15 call follow-up is recommended before committing the full Step 0B budget. |
| **D — Reproducibility** | **PASS, with caveats** | Model resolves to a concrete, recorded version (`jev-1.13.0`); full config/input hashing works; 4/4 identical repeats were bit-identical for the one item tested. Caveats: only one item's repeat-stability was tested; whether a version can be explicitly pinned is unconfirmed (§3); `jev-latest` is a floating alias — future runs must keep checking and recording the resolved `model` field, not assume stability. |
| **E — Experimental viability** | **CONDITIONAL** | There is real, non-degenerate structure in the outputs (e.g., empty-state produced genuine spread; `noul` produced intermediate values), so calibration/ranking analysis is plausible in principle — but contingent on resolving Gate C first. Proceeding straight to the full Step 0B design now would risk a degenerate result set. |

## 7. Recommendation

**Do not proceed directly to the full ~540-call Step 0B design yet.** Run
the small ambiguity-sweep follow-up described in §4 first (≈10-15 calls,
still well within "characterization," not a calibration claim) to confirm
intermediate confidence values are reachable for `choice`/`score` under a
controllable manipulation, not just for `noul` and degenerate (empty)
inputs. Once that's done, Gate C can be resolved and Step 0B's full design
can proceed with an item-generation method known to actually spread
confidence across the range — otherwise its ECE/reliability-diagram output
risks being degenerate regardless of Jev's true properties.

Everything else (Gates A, D; the API contract; error handling; mixed-call
behavior) is solid enough to build on. No changes to `../src/jev_client/`
are indicated by this run's findings — the two error-response shapes and
the empty-state/single-option acceptance are new facts worth keeping in
mind for Step 0B/Step 2's input validation, but don't require client code
changes.

## 8. Reproducibility

```
.venv/bin/python3 research/src/run_step0a.py
```

Requires `JEV_API_KEY` in `.env` (repo root) or the environment. Package
versions used: Python 3.14.5, requests 2.34.2, pydantic 2.13.5 (see
`../data/characterization/run_metadata.json`). Re-running will hit the
live API again (21 new calls, not cached) — the script does not currently
skip calls whose `input_hash` was already seen; that's a reasonable
addition if this script is re-run often, not added here to keep Step 0A's
scope minimal.
