# Jev API notes (documentation-only — no API calls made yet)

Sourced from `typesafe.ai/blog/introducing-system-one-models-and-jev` and
`docs.typesafe.ai` (`/`, `/confidence`, `/introduction/quickstart`,
`/primitives/choice`, `/primitives/score`, `/primitives/noul`), fetched
2026-09-21. This is documentation review only — nothing here has been
confirmed against a live API response yet. That confirmation is Phase 2
work and requires the approval gate below to be cleared first.

## What Jev is

TypeSafe positions Jev as their first "System One Model": "a
frontier-intelligence function call: unstructured state in, typed
probabilistic decisions out." Claimed to be optimized for structured output
(not string generation), "two orders of magnitude faster and more efficient"
than general LLMs, and unable to hallucinate due to type-safety constraints.
These are vendor marketing claims, not yet independently verified — treat as
hypotheses, not facts, consistent with the project's instruction not to
assume Jev is better than conventional LLMs.

## The three primitives

| Primitive | Input | Output fields | Notes |
|---|---|---|---|
| `choice` | `instructions` + `criteria` (map of option name → description, up to 255 options) | `type`, `choice`, `probabilities` (dict over options, sums to 1.0), `confidence` (0–1) | `confidence` is documented as a distribution-concentration statistic, not a correctness likelihood |
| `score` | `instructions` + `criteria` (ordered array, 2–10 levels) | `type`, `score` (probability-weighted mean of level indices), `confidence` (0–1), `legend` (level index → description), `probabilities` (dict over level indices, sums to 1.0) | `score` example: levels {0,1,2} with probabilities {0.0, 0.57, 0.43} → score = 1.43 |
| `noul` | `instructions` (+ optional `criteria` with `true`/`false` descriptions) | `type`, `noul` (single value in [0,1]) | Documented as "the probability that the answer is yes." **No separate `confidence` field** — per docs, a two-outcome distribution is fully described by one number, so none is given |

All three question types can be mixed in a single API call; each question is
evaluated "in parallel and in isolation against the same state."

## Request/response shape (from `/introduction/quickstart`)

```
POST https://api.typesafe.ai/v1/systemone
Authorization: Bearer <API_KEY>
Content-Type: application/json

{
  "state": "<text to analyze>",
  "model": "jev-latest",
  "questions": {
    "<question_key>": {"type": "choice|score|noul", "instructions": "...", "criteria": {...}}
  }
}
```

Response:
```
{
  "model": "<version_string>",
  "answers": {"<question_key>": {"type": "...", ...type-specific fields}},
  "usage": {"input_tokens": N, "output_tokens": N}
}
```

Not yet confirmed: exact error format, rate limits, retry semantics, whether
`model: "jev-latest"` is pinned or floating at request time (matters for
reproducibility — Phase 2 client must record the *resolved* model version
string from the response, not just the requested alias).

## The calibration claim: a documented tension worth testing empirically

- Blog (marketing page): **"Always communicates confidence and uncertainty
  with every output. Calibrated: higher confidence means higher accuracy."**
- Docs (`/confidence`, technical reference): confidence is **"a statistic
  computed from the probability distribution the answer already gives
  you"** — concentration of the distribution, not a stated accuracy
  guarantee. The docs explicitly say: *"Depending on what you are evaluating,
  a different measure may serve you better, which is exactly why we give you
  the full `probabilities` in the response,"* suggesting even TypeSafe does
  not treat `confidence` as sufficient on its own.

These two statements are not strictly contradictory (a distribution can be
both concentration-derived and empirically well-calibrated to accuracy), but
the docs make no accuracy claim while the blog does, and only one of the two
is a technical reference. Per the project's stated instruction not to assume
calibration, this should be treated as an open empirical question — this is
Candidate Gap 2 in `literature/gap_analysis.md`, planned as mandatory Phase 2
groundwork.

## Pricing (from blog, not verified against console)

$0.042 / MTok input tokens; output tokens described as free. Not yet checked
against `usage` field behavior or whether this is still current pricing.

## Confirmed against the live API (Step 0A, 2026-09-21, 21 calls)

See `results/characterization_report.md` for full detail. Headline
confirmations: `"jev-latest"` resolves to a concrete pinned version string
(`jev-1.13.0`) returned on every response; all documented field shapes for
`choice`/`score`/`noul` matched live responses exactly (zero schema
mismatches, zero undocumented fields across 19 successful calls); `score`'s
weighted-mean formula verified bit-exact; `noul` confirmed genuinely
continuous (not binary) with no `confidence` field, live. New facts not
stated either way in the docs: empty `state` is accepted (200), not
rejected, and produces a visibly non-degenerate spread distribution; a
`choice` question with a single `criteria` option is accepted; unknown
question `type` → HTTP 400 with a generic message; a missing required
field → HTTP 422 with a structured, field-path validation error. One open
item-design finding worth flagging here: hand-picked "ambiguous-sounding"
`choice` inputs did not reliably elicit intermediate confidence in this
small sample (came back confidence≈1.0 instead) — flagged in the report as
needing a targeted follow-up before the full calibration audit (Step 0B).

## Step 0A.1: controlled ambiguity follow-up (2026-09-21, 12 calls)

See `results/step0a1_controlled_ambiguity_report.md` for full detail.
Headline: intermediate `choice` confidence **is** reachable (down to an
exact 50/50 tie), but not via the variable the pilot set out to manipulate
(evidence-sentence-count ratio saturates to confidence 1.0 at anything
≥3:1) — it emerged unpredictably within the 2:2 tier, and **sentence order
alone (same 4 sentences, same content, positions swapped within pairs)
swung confidence from 0.82 to 0.01**, the largest effect observed in the
whole matrix. Also: repeated identical calls are bit-identical when
confidence is saturated (1.0) but show real numerical jitter
(confidence 0.78-0.85 across 3 calls) when confidence is intermediate —
determinism is not uniform across the output range. Both findings must
shape Step 0B's item-generation and sampling design before it is run at
scale.

## Step 0A.2: order/repeat factorial + score matched-pool follow-up (2026-09-21, 26 calls)

See `results/step0a2_order_and_score_report.md`. Confirms and sharpens
Step 0A.1: across 6 permutations of one fixed 4-sentence `choice` evidence
set (3 repeats each), the permutation effect (`R_perm`=0.417 on the
`database`-probability scale) dwarfs the repeat-noise effect (mean range
0.058) — **but at 2 of 6 permutations whose mean landed near the 50/50
boundary, ordinary repeat noise was enough to flip which option was
actually selected**, not just jitter its confidence. The order effect's
mechanism (position vs. adjacency vs. content-pairing) is not yet
identified — only the association is established. Separately, a
matched-evidence-pool method now also works for `score` (resolving Step
0A.1's inconclusive result there), and one item suggests `score` may
aggregate conflicting-severity evidence by tracking the worst symptom
rather than averaging (single data point, flagged not claimed).

## Still unchecked

- `docs.typesafe.ai/patterns` (system design patterns — may contain
  additional guidance relevant to Phase 3 workflow design).
- Actual error responses, rate limits, retry-after semantics.
- Whether `probabilities` for `choice`/`score` can contain a "declined to
  answer" or null case, or is always fully populated.
- Model versioning behavior in practice (does `jev-latest` change under us
  between pilot and main experiment runs? Phase 8 requires recording this).
