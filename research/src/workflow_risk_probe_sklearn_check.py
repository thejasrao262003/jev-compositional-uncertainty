"""Independent cross-check of workflow_risk_probe.py with scikit-learn
(LogisticRegression, C = 1/lambda = 1.0, standardized features, lbfgs).
Same features, target, folds count/repeats and cross-tracker split.
EXPLORATORY; no API calls.

  .venv/bin/python3 research/src/workflow_risk_probe_sklearn_check.py
"""
import json
import sys
from pathlib import Path

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import RepeatedStratifiedKFold, cross_val_predict
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, str(Path(__file__).resolve().parent))
import workflow_risk_probe as wp  # noqa: E402

data = {d: wp.build(d) for d in ("mozilla", "kernel")}
out = {"within": {}, "cross": {}}
model = lambda: make_pipeline(StandardScaler(), LogisticRegression(C=1.0 / wp.LAMBDA, max_iter=5000))
for d, rows in data.items():
    y = np.array([r["y"] for r in rows])
    out["within"][d] = {}
    for kind in ("DECISION", "UNCERTAINTY", "ALL"):
        X = np.array([wp.vec(r, kind) for r in rows])
        rskf = RepeatedStratifiedKFold(n_splits=wp.FOLDS, n_repeats=wp.REPEATS, random_state=0)
        aucs = []
        for rep in range(wp.REPEATS):
            from sklearn.model_selection import StratifiedKFold
            p = cross_val_predict(model(), X, y, cv=StratifiedKFold(wp.FOLDS, shuffle=True, random_state=rep),
                                  method="decision_function")
            aucs.append(roc_auc_score(y, p))
        out["within"][d][kind] = round(float(np.mean(aucs)), 3)
for tr, te in (("mozilla", "kernel"), ("kernel", "mozilla")):
    out["cross"][f"{tr}->{te}"] = {}
    for kind in ("DECISION", "UNCERTAINTY", "ALL"):
        m = model().fit(np.array([wp.vec(r, kind) for r in data[tr]]), [r["y"] for r in data[tr]])
        s = m.decision_function(np.array([wp.vec(r, kind) for r in data[te]]))
        out["cross"][f"{tr}->{te}"][kind] = round(float(roc_auc_score([r["y"] for r in data[te]], s)), 3)
print(json.dumps(out, indent=1))
(Path(wp.OUT).parent / "workflow_risk_probe_sklearn_check.json").write_text(json.dumps(out, indent=2))
