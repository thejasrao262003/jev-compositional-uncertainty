# Mozilla validation — results (descriptive)

Agreement is with Mozilla triage labels, not accuracy. The sample is balanced by severity cell, so
pooled figures describe this design, not real-world rates. Per-cell figures are in the JSON.
Strategy figures score against `a* = F(regression, level)`: only the node labels are
externally validated, not the target action.

## Subset `all` (n=202) — PRIMARY
- choice agreement 0.8861386138613861, noul agreement 0.801980198019802, score agreement 0.5297029702970297, wording-arm agreement 0.5594059405940595
- RQ-A1, S4 row: P(Jev level > Mozilla) = 0.7924528301886793 (k=42/53); wording arm 0.66 (k=33/50)
- RQ-A2, choice >=0.90 band: {'band': '>=0.90', 'n': 172, 'mean_confidence': 0.9947286821705427, 'agreement': 0.9593023255813954, 'gap': 0.03542635658914728}

## Subset `no_routing_cue` (n=75)
- choice agreement 0.84, noul agreement 0.7866666666666666, score agreement 0.5733333333333334, wording-arm agreement 0.5333333333333333
- RQ-A1, S4 row: P(Jev level > Mozilla) = 0.7619047619047619 (k=16/21); wording arm 0.631578947368421 (k=12/19)
- RQ-A2, choice >=0.90 band: {'band': '>=0.90', 'n': 55, 'mean_confidence': 0.9945454545454546, 'agreement': 0.9636363636363636, 'gap': 0.030909090909090997}

## Subset `no_regression_wording` (n=183)
- choice agreement 0.8907103825136612, noul agreement 0.8032786885245902, score agreement 0.5136612021857924, wording-arm agreement 0.546448087431694
- RQ-A1, S4 row: P(Jev level > Mozilla) = 0.7843137254901961 (k=40/51); wording arm 0.6458333333333334 (k=31/48)
- RQ-A2, choice >=0.90 band: {'band': '>=0.90', 'n': 158, 'mean_confidence': 0.9947257383966244, 'agreement': 0.9620253164556962, 'gap': 0.03270042194092815}

## Subset `recent_12_months` (n=54)
- choice agreement 0.9074074074074074, noul agreement 0.8148148148148148, score agreement 0.6296296296296297, wording-arm agreement 0.6111111111111112
- RQ-A1, S4 row: P(Jev level > Mozilla) = 1.0 (k=7/7); wording arm 0.8571428571428571 (k=6/7)
- RQ-A2, choice >=0.90 band: {'band': '>=0.90', 'n': 47, 'mean_confidence': 0.9967375886524822, 'agreement': 0.9574468085106383, 'gap': 0.03929078014184384}

