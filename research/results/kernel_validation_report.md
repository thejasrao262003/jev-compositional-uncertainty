# Kernel replication - results (descriptive)

Agreement is with REPORTER-set kernel Bugzilla labels, not with triage and not accuracy. The sample is
balanced by severity cell, so pooled figures describe this design, not real-world rates. Per-cell
figures are in the JSON. Strategy figures score against `a* = F(regression, level)`: only the node
labels are external, not the target action. No wording arm (proposal §2.4).

## Subset `all` (n=240) - PRIMARY
- choice agreement 0.975, noul agreement 0.725, score agreement 0.44166666666666665
- RQ-K1, level-0 (reporter 'low') row: P(Jev level > reporter level) = 0.75 (k=60/80, unstable 0)
- RQ-K2, choice >=0.90 band: {'band': '>=0.90', 'n': 230, 'mean_confidence': 0.9974782608695651, 'agreement': 0.991304347826087, 'gap': 0.006173913043478141}

## Subset `no_routing_cue` (n=191)
- choice agreement 0.9685863874345549, noul agreement 0.7382198952879581, score agreement 0.41361256544502617
- RQ-K1, level-0 (reporter 'low') row: P(Jev level > reporter level) = 0.7692307692307693 (k=50/65, unstable 0)
- RQ-K2, choice >=0.90 band: {'band': '>=0.90', 'n': 182, 'mean_confidence': 0.996996336996337, 'agreement': 0.989010989010989, 'gap': 0.007985347985348001}

## Subset `no_routing_cue_extended` (n=26)
- choice agreement 0.8076923076923077, noul agreement 0.6538461538461539, score agreement 0.46153846153846156
- RQ-K1, level-0 (reporter 'low') row: P(Jev level > reporter level) = 0.7777777777777778 (k=7/9, unstable 0)
- RQ-K2, choice >=0.90 band: {'band': '>=0.90', 'n': 20, 'mean_confidence': 0.9813333333333333, 'agreement': 0.9, 'gap': 0.08133333333333326}

## Subset `no_regression_wording` (n=227)
- choice agreement 0.973568281938326, noul agreement 0.7136563876651982, score agreement 0.45374449339207046
- RQ-K1, level-0 (reporter 'low') row: P(Jev level > reporter level) = 0.75 (k=60/80, unstable 0)
- RQ-K2, choice >=0.90 band: {'band': '>=0.90', 'n': 217, 'mean_confidence': 0.9981259600614439, 'agreement': 0.9907834101382489, 'gap': 0.007342549923195052}

## Subset `recent_since_2018` (n=35)
- choice agreement 0.9714285714285714, noul agreement 0.6, score agreement 0.45714285714285713
- RQ-K1, level-0 (reporter 'low') row: P(Jev level > reporter level) = 0.8 (k=4/5, unstable 0)
- RQ-K2, choice >=0.90 band: {'band': '>=0.90', 'n': 32, 'mean_confidence': 0.99875, 'agreement': 1.0, 'gap': 0.0012499999999999734}

## Subset `regression_field_set` (n=146)
- choice agreement 0.9794520547945206, noul agreement 0.7534246575342466, score agreement 0.4452054794520548
- RQ-K1, level-0 (reporter 'low') row: P(Jev level > reporter level) = 0.7567567567567568 (k=28/37, unstable 0)
- RQ-K2, choice >=0.90 band: {'band': '>=0.90', 'n': 140, 'mean_confidence': 0.9963333333333334, 'agreement': 0.9857142857142858, 'gap': 0.010619047619047639}

## Subset `hard_cut` (n=49)
- choice agreement 0.9795918367346939, noul agreement 0.6938775510204082, score agreement 0.2653061224489796
- RQ-K1, level-0 (reporter 'low') row: P(Jev level > reporter level) = 0.9333333333333333 (k=14/15, unstable 0)
- RQ-K2, choice >=0.90 band: {'band': '>=0.90', 'n': 47, 'mean_confidence': 0.9998581560283688, 'agreement': 1.0, 'gap': 0.00014184397163119478}

## Subset `not_hard_cut` (n=191)
- choice agreement 0.9738219895287958, noul agreement 0.7329842931937173, score agreement 0.4869109947643979
- RQ-K1, level-0 (reporter 'low') row: P(Jev level > reporter level) = 0.7076923076923077 (k=46/65, unstable 0)
- RQ-K2, choice >=0.90 band: {'band': '>=0.90', 'n': 183, 'mean_confidence': 0.9968670309653916, 'agreement': 0.9890710382513661, 'gap': 0.007795992714025535}

## Subset `log_dominated` (n=41)
- choice agreement 1.0, noul agreement 0.7804878048780488, score agreement 0.4146341463414634
- RQ-K1, level-0 (reporter 'low') row: P(Jev level > reporter level) = 0.9090909090909091 (k=10/11, unstable 0)
- RQ-K2, choice >=0.90 band: {'band': '>=0.90', 'n': 40, 'mean_confidence': 1.0, 'agreement': 1.0, 'gap': 0.0}

## Subset `not_log_dominated` (n=199)
- choice agreement 0.9698492462311558, noul agreement 0.7135678391959799, score agreement 0.4472361809045226
- RQ-K1, level-0 (reporter 'low') row: P(Jev level > reporter level) = 0.7246376811594203 (k=50/69, unstable 0)
- RQ-K2, choice >=0.90 band: {'band': '>=0.90', 'n': 190, 'mean_confidence': 0.9969473684210526, 'agreement': 0.9894736842105263, 'gap': 0.007473684210526299}

## Subset `severity_changed_after_filing` (n=15)
- choice agreement 0.9333333333333333, noul agreement 0.8666666666666667, score agreement 0.4666666666666667
- RQ-K1, level-0 (reporter 'low') row: P(Jev level > reporter level) = 0.5 (k=6/12, unstable 0)
- RQ-K2, choice >=0.90 band: {'band': '>=0.90', 'n': 14, 'mean_confidence': 0.9985714285714286, 'agreement': 1.0, 'gap': 0.0014285714285714457}

## Subset `severity_as_filed` (n=225)
- choice agreement 0.9777777777777777, noul agreement 0.7155555555555555, score agreement 0.44
- RQ-K1, level-0 (reporter 'low') row: P(Jev level > reporter level) = 0.7941176470588235 (k=54/68, unstable 0)
- RQ-K2, choice >=0.90 band: {'band': '>=0.90', 'n': 216, 'mean_confidence': 0.9974074074074074, 'agreement': 0.9907407407407407, 'gap': 0.00666666666666671}

