"""Power simulation for K1 of independent_workflow_preregistration.md (Issue D).

Simulates the paired, one-sided bootstrap test of
AUROC(action-rule score) - AUROC(final-step confidence) > 0
on a test set of n issues. No data and no model calls.

Generative model: Y ~ Bernoulli(p). Two latent risk scores, bivariate normal
with correlation rho, each shifted by delta_k * Y. The confidence score is
continuous with AUROC 0.55 (near chance, as observed). The action-rule score
is the latent cut into 3 tied levels (like accept / defer / escalate, with
level shares 60/25/15%), and its shift is tuned so its AUROC is 0.55 + D.

  .venv/bin/python research/src/k8s_power_simulation.py
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from scipy.stats import norm, rankdata

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "research" / "results" / "k8s_power_simulation.json"
AUC_CONF = 0.55
DIFFS = [0.03, 0.06, 0.10, 0.20]
PREV = [0.25, 0.45]
RHO = [0.2, 0.5]
NS = [500, 300]
SIMS, B = 300, 400
CUTS = norm.ppf([0.60, 0.85])           # 3 tied levels: 60% / 25% / 15% (in the null population)
rng = np.random.default_rng(20261023)


def auc(score, y):
    r = rankdata(score)
    n1 = y.sum()
    n0 = len(y) - n1
    return (r[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)


def draw(n, p, rho, d_conf, d_rule, rng):
    y = (rng.random(n) < p).astype(int)
    z = rng.multivariate_normal([0, 0], [[1, rho], [rho, 1]], size=n)
    conf = z[:, 0] + d_conf * y
    rule = np.digitize(z[:, 1] + d_rule * y, CUTS).astype(float)
    return y, conf, rule


def tune_rule_shift(target, p, rho):
    """Shift giving the 3-level rule score the target AUROC (large-sample)."""
    lo, hi = 0.0, 4.0
    for _ in range(30):
        mid = (lo + hi) / 2
        y, _, r = draw(200_000, p, rho, 0.0, mid, np.random.default_rng(1))
        lo, hi = (mid, hi) if auc(r, y) < target else (lo, mid)
    return (lo + hi) / 2


def one_study(n, p, rho, d_conf, d_rule):
    y, c, r = draw(n, p, rho, d_conf, d_rule, rng)
    while not (0 < y.sum() < n):
        y, c, r = draw(n, p, rho, d_conf, d_rule, rng)
    diffs = []
    for _ in range(B):
        i = rng.integers(0, n, n)
        if 0 < y[i].sum() < n:
            diffs.append(auc(r[i], y[i]) - auc(c[i], y[i]))
    pval = np.mean(np.array(diffs) <= 0)
    return pval


def main():
    d_conf = np.sqrt(2) * norm.ppf(AUC_CONF)
    out = {"design": {"auc_conf": AUC_CONF, "rule_levels": "3 tied levels (60/25/15%)", "sims": SIMS, "B": B},
           "cells": []}
    for D in DIFFS:
        for p in PREV:
            for rho in RHO:
                d_rule = tune_rule_shift(AUC_CONF + D, p, rho)
                for n in NS:
                    ps = np.array([one_study(n, p, rho, d_conf, d_rule) for _ in range(SIMS)])
                    cell = {"diff": D, "prevalence": p, "rho": rho, "n": n,
                            "power_alpha_0.05": round(float(np.mean(ps <= 0.05)), 3),
                            "power_alpha_0.0167_holm_worst": round(float(np.mean(ps <= 0.05 / 3)), 3)}
                    out["cells"].append(cell)
                    print(cell, flush=True)
    OUT.write_text(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
