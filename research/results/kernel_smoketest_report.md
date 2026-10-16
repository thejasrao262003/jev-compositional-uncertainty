# Kernel replication - results (descriptive)

Agreement is with REPORTER-set kernel Bugzilla labels, not with triage and not accuracy. The sample is
balanced by severity cell, so pooled figures describe this design, not real-world rates. Per-cell
figures are in the JSON. Strategy figures score against `a* = F(regression, level)`: only the node
labels are external, not the target action. No wording arm (proposal §2.4).

## Subset `all` (n=24) - PRIMARY
- choice agreement 1.0, noul agreement 0.625, score agreement 0.375
- RQ-K1, level-0 (reporter 'low') row: P(Jev level > reporter level) = 0.875 (k=7/8, unstable 0)
- RQ-K2, choice >=0.90 band: {'band': '>=0.90', 'n': 24, 'mean_confidence': 1.0, 'agreement': 1.0, 'gap': 0.0}

## Subset `no_routing_cue` (n=20)
- choice agreement 1.0, noul agreement 0.65, score agreement 0.35
- RQ-K1, level-0 (reporter 'low') row: P(Jev level > reporter level) = 0.8571428571428571 (k=6/7, unstable 0)
- RQ-K2, choice >=0.90 band: {'band': '>=0.90', 'n': 20, 'mean_confidence': 1.0, 'agreement': 1.0, 'gap': 0.0}

## Subset `no_routing_cue_extended` (n=1)
- choice agreement 1.0, noul agreement 0.0, score agreement 0.0
- RQ-K1, level-0 (reporter 'low') row: P(Jev level > reporter level) = 1.0 (k=1/1, unstable 0)
- RQ-K2, choice >=0.90 band: {'band': '>=0.90', 'n': 1, 'mean_confidence': 1.0, 'agreement': 1.0, 'gap': 0.0}

## Subset `no_regression_wording` (n=24)
- choice agreement 1.0, noul agreement 0.625, score agreement 0.375
- RQ-K1, level-0 (reporter 'low') row: P(Jev level > reporter level) = 0.875 (k=7/8, unstable 0)
- RQ-K2, choice >=0.90 band: {'band': '>=0.90', 'n': 24, 'mean_confidence': 1.0, 'agreement': 1.0, 'gap': 0.0}

## Subset `recent_since_2018` (n=0)
- choice agreement None, noul agreement None, score agreement None
- RQ-K1, level-0 (reporter 'low') row: P(Jev level > reporter level) = None (k=0/0, unstable 0)
- RQ-K2, choice >=0.90 band: {'band': '>=0.90', 'n': 0}

## Subset `regression_field_set` (n=12)
- choice agreement 1.0, noul agreement 0.8333333333333334, score agreement 0.5
- RQ-K1, level-0 (reporter 'low') row: P(Jev level > reporter level) = 1.0 (k=1/1, unstable 0)
- RQ-K2, choice >=0.90 band: {'band': '>=0.90', 'n': 12, 'mean_confidence': 1.0, 'agreement': 1.0, 'gap': 0.0}

## Subset `hard_cut` (n=7)
- choice agreement 1.0, noul agreement 0.8571428571428571, score agreement 0.5714285714285714
- RQ-K1, level-0 (reporter 'low') row: P(Jev level > reporter level) = None (k=0/0, unstable 0)
- RQ-K2, choice >=0.90 band: {'band': '>=0.90', 'n': 7, 'mean_confidence': 1.0, 'agreement': 1.0, 'gap': 0.0}

## Subset `not_hard_cut` (n=17)
- choice agreement 1.0, noul agreement 0.5294117647058824, score agreement 0.29411764705882354
- RQ-K1, level-0 (reporter 'low') row: P(Jev level > reporter level) = 0.875 (k=7/8, unstable 0)
- RQ-K2, choice >=0.90 band: {'band': '>=0.90', 'n': 17, 'mean_confidence': 1.0, 'agreement': 1.0, 'gap': 0.0}

## Subset `log_dominated` (n=5)
- choice agreement 1.0, noul agreement 1.0, score agreement 0.6
- RQ-K1, level-0 (reporter 'low') row: P(Jev level > reporter level) = None (k=0/0, unstable 0)
- RQ-K2, choice >=0.90 band: {'band': '>=0.90', 'n': 5, 'mean_confidence': 1.0, 'agreement': 1.0, 'gap': 0.0}

## Subset `not_log_dominated` (n=19)
- choice agreement 1.0, noul agreement 0.5263157894736842, score agreement 0.3157894736842105
- RQ-K1, level-0 (reporter 'low') row: P(Jev level > reporter level) = 0.875 (k=7/8, unstable 0)
- RQ-K2, choice >=0.90 band: {'band': '>=0.90', 'n': 19, 'mean_confidence': 1.0, 'agreement': 1.0, 'gap': 0.0}

## Subset `severity_changed_after_filing` (n=1)
- choice agreement 1.0, noul agreement 0.0, score agreement 1.0
- RQ-K1, level-0 (reporter 'low') row: P(Jev level > reporter level) = 0.0 (k=0/1, unstable 0)
- RQ-K2, choice >=0.90 band: {'band': '>=0.90', 'n': 1, 'mean_confidence': 1.0, 'agreement': 1.0, 'gap': 0.0}

## Subset `severity_as_filed` (n=23)
- choice agreement 1.0, noul agreement 0.6521739130434783, score agreement 0.34782608695652173
- RQ-K1, level-0 (reporter 'low') row: P(Jev level > reporter level) = 1.0 (k=7/7, unstable 0)
- RQ-K2, choice >=0.90 band: {'band': '>=0.90', 'n': 23, 'mean_confidence': 1.0, 'agreement': 1.0, 'gap': 0.0}

