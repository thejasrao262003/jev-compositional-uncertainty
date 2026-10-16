# Mozilla validation — results (descriptive)

Agreement is with Mozilla triage labels, not accuracy. The sample is balanced by severity cell, so
pooled figures describe this design, not real-world rates. Per-cell figures are in the JSON.
Strategy figures score against `a* = F(regression, level)`: only the node labels are
externally validated, not the target action.

## Subset `all` (n=21) — PRIMARY
- choice agreement 0.9047619047619048, noul agreement 0.7619047619047619, score agreement 0.6666666666666666, wording-arm agreement 0.6666666666666666
- RQ-A1, S4 row: P(Jev level > Mozilla) = 0.5 (k=3/6); wording arm 0.4 (k=2/5)
- RQ-A2, choice >=0.90 band: {'band': '>=0.90', 'n': 19, 'mean_confidence': 0.9989473684210527, 'agreement': 0.9473684210526315, 'gap': 0.05157894736842117}

## Subset `no_routing_cue` (n=8)
- choice agreement 0.75, noul agreement 0.625, score agreement 0.75, wording-arm agreement 0.625
- RQ-A1, S4 row: P(Jev level > Mozilla) = 0.3333333333333333 (k=1/3); wording arm 0.3333333333333333 (k=1/3)
- RQ-A2, choice >=0.90 band: {'band': '>=0.90', 'n': 6, 'mean_confidence': 0.9966666666666667, 'agreement': 0.8333333333333334, 'gap': 0.16333333333333333}

## Subset `no_regression_wording` (n=18)
- choice agreement 0.8888888888888888, noul agreement 0.7777777777777778, score agreement 0.6111111111111112, wording-arm agreement 0.6666666666666666
- RQ-A1, S4 row: P(Jev level > Mozilla) = 0.5 (k=3/6); wording arm 0.4 (k=2/5)
- RQ-A2, choice >=0.90 band: {'band': '>=0.90', 'n': 16, 'mean_confidence': 0.99875, 'agreement': 0.9375, 'gap': 0.06125000000000003}

## Subset `recent_12_months` (n=8)
- choice agreement 1.0, noul agreement 0.75, score agreement 0.625, wording-arm agreement 0.625
- RQ-A1, S4 row: P(Jev level > Mozilla) = 1.0 (k=1/1); wording arm 1.0 (k=1/1)
- RQ-A2, choice >=0.90 band: {'band': '>=0.90', 'n': 8, 'mean_confidence': 1.0, 'agreement': 1.0, 'gap': 0.0}

