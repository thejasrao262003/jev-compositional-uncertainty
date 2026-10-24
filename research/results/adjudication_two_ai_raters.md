# Two AI raters of target validity (exploratory)

**Protocol:** `human_target_validation_protocol.md` Amendment 2. Rater 2's
ratings (`ratings_CLAUDE.csv`) were committed in `de50947` before the key
was joined.
**Code:** `research/src/adjudication_two_ai_raters.py`.
**Numbers:** `adjudication_two_ai_raters.json`.

**This is NOT the pre-registered human validation.**
- **Rater 1** is an AI pilot: actions only, 10 of 50 rated "can't tell".
- **Rater 2** is the study's own analysis assistant. It knows F and is not
  blind to the design, so its agreement with a\* may be biased upward.

## Action agreement (Cohen's κ, bootstrap 95%)

| Comparison | n | Agreement [Wilson 95%] | κ [95%] |
|---|---|---|---|
| Rater 1 (R1) vs rater 2 (inter-rater) | 40 | 0.500 [0.35, 0.65] | 0.220 [−0.03, 0.44] |
| Rater 1 (R2) vs rater 2 (inter-rater) | 40 | 0.575 [0.42, 0.72] | 0.323 [0.15, 0.51] |
| Rater 2 vs a\* | 50 | 0.560 [0.42, 0.69] | 0.285 [0.08, 0.49] |
| Rater 1 (R1) vs a\* | 40 | 0.375 [0.24, 0.53] | −0.157 [−0.33, 0.07] |
| Rater 1 (R2) vs a\* | 40 | 0.550 [0.40, 0.69] | 0.015 [−0.19, 0.25] |

## Where rater 2 departs from a\*

- **Label validity:**
  - severity vs the tracker: agreement 0.47, κ −0.041. In 13 cases
    rater 2 said blocking where the tracker said 1, and in 5 the reverse.
  - regression vs the tracker: agreement 0.89, κ 0.739. Rater 2 answered
    "can't tell" on 14 bugs.
- **Rule validity:** F applied to rater 2's own labels agreed with its
  direct action at 0.80 (κ 0.673).
- **Error attribution** (22 disagreements with a\*):
  - 12 label-driven;
  - 4 rule-driven;
  - 6 ambiguity (rater can't tell).
- **Confusion:** of the 33 accept targets, rater 2 deferred 7 and
  escalated 7. Of the 9 escalate targets, it accepted 3.
- **Failure-label check:** Jev's "wrong action" (a ≠ a\*) matches
  a ≠ rater-2 action on 60% of the bugs (23 vs 19 failures).

## Reading

- **The target matches rater 2 about as well as the two raters match
  each other** (κ 0.29 vs 0.22–0.32). Neither agreement is high.
- **Rater 1's near-chance agreement with a\* is partly that rater:** it
  also agrees only weakly with rater 2.
- **The weak link is the tracker severity field,** not the regression
  field or the rule. Tracker severity is often a default value rather
  than an assessment.
- **Consequence:** the failure label is a noisy proxy. The paper keeps
  "disagreement with the operational target" wording. The two-human
  validation stays open.
