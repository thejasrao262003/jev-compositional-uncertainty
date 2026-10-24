# AI-judge pilot of target validity (exploratory)

**Protocol:** `human_target_validation_protocol.md` Amendment 1
(mapping committed `a7cda8d` before the key was opened).

**Code:** `research/src/adjudication_ai_pilot.py`.

**Numbers:** `adjudication_ai_pilot.json`.

**This is NOT the pre-registered human validation.**
- One AI rater.
- Action ratings only, with no severity or regression ratings.
- 10 of 50 bugs were rated "request evidence" (can't tell).

| Reading of the AI's "defer" | Agreement with a\* (n = 40) | Cohen's κ [95%] |
|---|---|---|
| R1: literally defer | 0.375 [0.24, 0.53] | −0.157 [−0.33, +0.07] |
| R2: as accept (per its rationales) | 0.550 [0.40, 0.69] | +0.015 [−0.19, +0.25] |

**Detail:**
- **Escalate targets:** the AI escalated 2 of 7.
- **Accept targets it escalated:** 6, mostly security-flavoured reports.
- **Jev's failure label** (a ≠ a\*) agrees with "a ≠ AI action" on 53%
  (R1) and 70% (R2) of rated bugs.

**Reading.** Agreement beyond chance is about zero. Without a second
independent rater there is no inter-rater baseline, so this cannot
separate two possibilities:
- (a) the constructed target, built from tracker severity and regression
  fields, is a weak proxy for the action an evaluator would choose
  (which weighs security and user impact);
- (b) a single AI judge is unreliable.

**Consequence.**
- The paper's failure label must be read strictly as disagreement with
  the constructed operational target.
- The pre-registered two-human validation, or at least two independent
  raters giving an inter-rater baseline, is required before any claim
  about real-world decision quality.
