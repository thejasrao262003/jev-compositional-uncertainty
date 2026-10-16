"""Uncertainty intervals and cross-dataset comparisons for the paper.
No API calls: recomputes everything from the committed raw responses.

Writes paper_statistics.json next to this file.

Methods (stated in the paper's §Statistics):
- AUROC: Mann-Whitney estimate; 95% percentile bootstrap CI over bugs
  (B = 2000, seed fixed). Bugs are distinct reports with no shared unit,
  so resampling bugs is the natural bootstrap.
- Paired strategy difference P(S1 correct) - P(S2 correct): exact McNemar
  test on discordant pairs; 95% percentile bootstrap CI over bugs.
  S2's escalation set is recomputed inside every bootstrap resample
  (it ranks within the evaluated set).
- Cross-dataset contrast (difference of the two paired differences):
  independent bootstraps per dataset; CI of the contrast.
- H1 cost difference vs random overrides: the randomization p-value
  (conditional on the evaluated set, as in the protocol) and a bootstrap CI
  over bugs for the per-bug difference from the exact random expectation.
  The override set is recomputed inside each resample.

  python3 research/paper/latex/paper_statistics.py
"""
from __future__ import annotations

import json
import random
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE.parents[1] / "src"
sys.path.insert(0, str(SRC))

import run_kernel_validation as kv  # noqa: E402
import run_mozilla_validation as moz  # noqa: E402
from mozilla_exploratory_analysis import auroc, exact_mcnemar  # noqa: E402
from workflow_strategies_r11 import conf_product, prevalence_q, strategy_2_r11  # noqa: E402
from workflow_strategies_r12 import cost, h1_randomization_test, n_overrides, strategy_2h  # noqa: E402

B = 2000
SEED = 20261016


def load(dataset: str):
    if dataset == "kernel":
        bugs = kv.load_dataset()
        rows = [json.loads(line) for line in open(kv.RAW_OUT)]
        rows += [dict(r, arm="wording") for r in rows if r["arm"] == "score"]   # shadow, unused
    else:
        bugs = moz.load_dataset()
        rows = [json.loads(line) for line in open(moz.RAW_OUT)]
    moz.check_complete(bugs, rows)
    by = defaultdict(lambda: defaultdict(list))
    for r in rows:
        by[r["bug_id"]][r["arm"]].append(r)
    per = {}
    for b in bugs:
        red = moz.reduce_bug(by[b["bug_id"]])
        s1 = moz.strategy_1_decision_only(red["choice"]["modal_decision"], red["noul"], red["score"])
        per[b["bug_id"]] = {"bug": b, "red": red, "a_star": moz.F(b["regression"], b["level"]), "s1": s1}
    return per


def inst(per, ids):
    return [(i, per[i]["red"]["choice"], per[i]["red"]["noul"], per[i]["red"]["score"]) for i in ids]


def node_signals(per, ids):
    """(confidence, correct) per node, as in the analysis."""
    out = {"choice": ([], []), "noul": ([], []), "score": ([], [])}
    for i in ids:
        p, b = per[i]["red"], per[i]["bug"]
        out["choice"][0].append(p["choice"]["mean_confidence"] or 0.0)
        out["choice"][1].append(p["choice"]["modal_decision"] == b["group"])
        out["noul"][0].append(2 * abs(p["noul"]["mean_noul"] - 0.5))
        out["noul"][1].append(p["noul"]["decision"] == b["regression"])
        d = p["score"]["modal_decision"]
        out["score"][0].append(p["score"]["mean_confidence"] or 0.0)
        out["score"][1].append(d is not None and int(d) == b["level"])
    return out


def composition(per, ids):
    """Per evaluated set: S1/S2 correctness vectors, the two AUROC targets
    and the H1 cost difference. Recomputes S2's and 2h's set-relative
    rankings on `ids` (a list that may contain repeats from resampling;
    repeats get distinct keys)."""
    keyed = [(f"{n}:{i}", i) for n, i in enumerate(ids)]
    pk = {k: per[i] for k, i in keyed}
    instances = [(k, pk[k]["red"]["choice"], pk[k]["red"]["noul"], pk[k]["red"]["score"]) for k, _ in keyed]
    q = prevalence_q([pk[k]["a_star"] for k, _ in keyed])
    s2 = strategy_2_r11(instances, q)
    base = {k: pk[k]["s1"] for k, _ in keyed}
    a_star = {k: pk[k]["a_star"] for k, _ in keyed}
    y1 = [base[k] == a_star[k] for k, _ in keyed]
    y2 = [s2[k] == a_star[k] for k, _ in keyed]
    # AUROC target A: among bugs S1 did not escalate, is the target "escalate"
    # (a serious bug F missed)? Score = low confidence product.
    cand = [k for k, _ in keyed if base[k] != "escalate"]
    cp = {k: conf_product(*[pk[k]["red"][n] for n in ("choice", "noul", "score")]) for k, _ in keyed}
    neg_cp = {k: -(cp[k] if cp[k] is not None else -1.0) for k in cp}
    auc_missed = auroc([neg_cp[k] for k in cand], [a_star[k] == "escalate" for k in cand])
    # AUROC target B: is S1's action wrong (any class)?
    auc_wrong = auroc([neg_cp[k] for k, _ in keyed], [base[k] != a_star[k] for k, _ in keyed])
    # H1: 2h vs exact random expectation, per bug
    h = strategy_2h(base, instances)
    kk = n_overrides(len(base), len(cand))
    gain = {k: cost("escalate", a_star[k]) - cost(base[k], a_star[k]) for k in cand}
    exp_rand = sum(cost(base[k], a_star[k]) for k in base) + (kk * sum(gain.values()) / len(cand) if cand else 0)
    diff = (sum(cost(h[k], a_star[k]) for k in base) - exp_rand) / len(base)
    return {"y1": y1, "y2": y2, "auc_missed": auc_missed, "auc_wrong": auc_wrong, "h1_diff": diff,
            "base": base, "h": h, "a_star": a_star}


def ci(vals):
    v = sorted(x for x in vals if x is not None)
    return [round(v[int(0.025 * len(v))], 3), round(v[int(0.975 * len(v)) - 1], 3)]


def analyse(dataset: str) -> dict:
    per = load(dataset)
    ids = list(per)
    rng = random.Random(f"{SEED}:{dataset}")
    sig = node_signals(per, ids)
    point_c = composition(per, ids)
    out = {"n": len(ids), "auroc_own": {}, "composition": {}}
    for node, (c, y) in sig.items():
        boots = []
        for _ in range(B):
            idx = [rng.randrange(len(ids)) for _ in ids]
            boots.append(auroc([c[j] for j in idx], [y[j] for j in idx]))
        out["auroc_own"][node] = {"point": round(auroc(c, y), 3), "ci95": ci(boots)}
    d_point = (sum(point_c["y1"]) - sum(point_c["y2"])) / len(ids)
    b1 = sum(a and not b for a, b in zip(point_c["y1"], point_c["y2"]))
    b2 = sum(b and not a for a, b in zip(point_c["y1"], point_c["y2"]))
    boot_d, boot_m, boot_w, boot_h = [], [], [], []
    for _ in range(B):
        sample = [ids[rng.randrange(len(ids))] for _ in ids]
        c = composition(per, sample)
        boot_d.append((sum(c["y1"]) - sum(c["y2"])) / len(sample))
        boot_m.append(c["auc_missed"])
        boot_w.append(c["auc_wrong"])
        boot_h.append(c["h1_diff"])
    # canonical ordering (bug ids, as in mozilla_exploratory_analysis) for the reported p-value
    base_o = {i: per[i]["s1"] for i in ids}
    a_o = {i: per[i]["a_star"] for i in ids}
    h1 = h1_randomization_test(base_o, strategy_2h(base_o, inst(per, ids)), a_o)
    out["composition"] = {
        "S1_minus_S2": {"point": round(d_point, 3), "ci95": ci(boot_d),
                        "discordant_S1_only": b1, "discordant_S2_only": b2,
                        "exact_mcnemar_p": exact_mcnemar(b1, b2)},
        "auroc_missed_serious": {"point": round(point_c["auc_missed"], 3), "ci95": ci(boot_m),
                                 "target": "among bugs S1 did not escalate: target is escalate"},
        "auroc_S1_wrong": {"point": round(point_c["auc_wrong"], 3), "ci95": ci(boot_w),
                           "target": "S1's action differs from a*"},
        "h1_per_bug_cost_diff_vs_random": {"point": round(point_c["h1_diff"], 3), "ci95": ci(boot_h),
                                           "randomization_p": round(h1["p_two_sided"], 4),
                                           "totals": [h1["hybrid_total_cost"], round(h1["random_expected_total_cost"], 1)]},
    }
    out["_boot_d"] = boot_d
    return out


def main():
    res = {d: analyse(d) for d in ("mozilla", "kernel")}
    bm, bk = res["mozilla"].pop("_boot_d"), res["kernel"].pop("_boot_d")
    contrast = [a - b for a, b in zip(bm, bk)]
    point = res["mozilla"]["composition"]["S1_minus_S2"]["point"] - res["kernel"]["composition"]["S1_minus_S2"]["point"]
    res["cross_dataset"] = {"S1_minus_S2_mozilla_minus_kernel": {"point": round(point, 3), "ci95": ci(contrast),
                            "note": "independent bootstraps per dataset; CI covering 0 = no evidence the effects differ"}}
    res["method"] = {"bootstrap_resamples": B, "seed": SEED, "ci": "95% percentile"}
    (HERE / "paper_statistics.json").write_text(json.dumps(res, indent=2))
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
