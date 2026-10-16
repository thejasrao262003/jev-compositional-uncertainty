"""EXPLORATORY, POST-HOC analysis of the full Mozilla run. Not pre-registered.

Nothing here changes the descriptive results in mozilla_validation_results.md
or sets any Step 2 constant. It answers questions raised in review after the
results were seen:
  1. Where do the strategies win and lose, by target class?
  2. Exact McNemar tests on the paired strategy comparisons (exploratory).
  3. Does composed confidence add information BEYOND the node decisions?
     F(decisions) plus escalating the k lowest-confidence bugs, for every k
     (a curve, so no k is chosen), against the exact random-override
     expectation.
  4. Discrimination (AUROC) of each node's own confidence for its own
     agreement, separate from calibration (ECE).
  5. score error audit: which bugs are over- and under-rated.
No API calls. Reads the raw responses already on disk.

  python research/src/mozilla_exploratory_analysis.py
"""

from __future__ import annotations

import json
import math
from collections import Counter, defaultdict

from run_mozilla_validation import (RAW_OUT, RESULTS_DIR, F, check_complete, load_dataset, reduce_bug,
                                    strategy_1_decision_only)
from workflow_strategies_r11 import conf_product, prevalence_q, strategy_2_r11, strategy_4a_r11
from workflow_strategy5_proposal import strategy_5
from workflow_strategies_r12 import R_OVERRIDE, h1_randomization_test, h2_sign_flip_test, strategy_2h, strategy_5h

OUT_JSON = RESULTS_DIR / "mozilla_exploratory_analysis.json"


def exact_mcnemar(b: int, c: int) -> float:
    """Two-sided exact binomial p-value on the discordant pairs."""
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    p = sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n
    return min(1.0, 2 * p)


def auroc(scores: list[float], positives: list[bool]) -> float | None:
    """P(score of a random positive > score of a random negative), ties 1/2."""
    pos = [s for s, y in zip(scores, positives) if y]
    neg = [s for s, y in zip(scores, positives) if not y]
    if not pos or not neg:
        return None
    wins = sum((p > q) + 0.5 * (p == q) for p in pos for q in neg)
    return wins / (len(pos) * len(neg))


def main() -> None:
    bugs = load_dataset()
    rows = [json.loads(line) for line in open(RAW_OUT)]
    check_complete(bugs, rows)
    by = defaultdict(lambda: defaultdict(list))
    for r in rows:
        by[r["bug_id"]][r["arm"]].append(r)
    per = {}
    for b in bugs:
        red = reduce_bug(by[b["bug_id"]])
        per[b["bug_id"]] = {"bug": b, "red": red, "a_star": F(b["regression"], b["level"]),
                            "1": strategy_1_decision_only(red["choice"]["modal_decision"], red["noul"], red["score"]),
                            "4a": strategy_4a_r11(red["choice"], red["noul"], red["score"])}
    ids = list(per)
    inst = [(i, per[i]["red"]["choice"], per[i]["red"]["noul"], per[i]["red"]["score"]) for i in ids]
    q = prevalence_q([per[i]["a_star"] for i in ids])
    s2 = strategy_2_r11(inst, q)
    s5 = strategy_5(inst, q)
    for i in ids:
        per[i]["2"] = s2[i]
        per[i]["5"] = s5["actions"][i]
    out = {"status": "EXPLORATORY / POST-HOC - not pre-registered; sets no Step 2 constant", "n": len(ids), "q": q}

    # 1. correctness by target class
    strategies = ("1", "4a", "2", "5")
    by_class = {}
    for a in ("accept", "escalate", "defer", "request_more_evidence"):
        sub = [i for i in ids if per[i]["a_star"] == a]
        if sub:
            by_class[a] = {"n": len(sub), **{s: sum(per[i][s] == a for i in sub) for s in strategies}}
    out["correct_by_target_class"] = by_class
    out["action_counts"] = {s: dict(Counter(per[i][s] for i in ids)) for s in strategies}

    # 2. exact McNemar, exploratory
    mc = {}
    for x, y in (("4a", "2"), ("1", "2"), ("5", "2"), ("1", "4a")):
        bx = sum(per[i][x] == per[i]["a_star"] and per[i][y] != per[i]["a_star"] for i in ids)
        by_ = sum(per[i][y] == per[i]["a_star"] and per[i][x] != per[i]["a_star"] for i in ids)
        mc[f"{x}_vs_{y}"] = {f"{x}_only_right": bx, f"{y}_only_right": by_, "exact_p_two_sided": exact_mcnemar(bx, by_)}
    out["exact_mcnemar_exploratory"] = mc

    # 3. confidence beyond decisions: F(decisions) then escalate the k least
    #    confident (by conf_product; by Strategy 5's U) among bugs F did not
    #    already escalate. Random baseline is the exact expectation.
    base = {i: per[i]["1"] for i in ids}
    base_right = {i: base[i] == per[i]["a_star"] for i in ids}
    cand = [i for i in ids if base[i] != "escalate"]
    gain_if_flip = {i: (per[i]["a_star"] == "escalate") - base_right[i] for i in cand}  # +1, 0 or -1
    cp = {i: conf_product(*inst[ids.index(i)][1:]) for i in cand}
    order_cp = sorted(cand, key=lambda i: (-1.0 if cp[i] is None else cp[i], str(i)))
    order_u = sorted(cand, key=lambda i: (-s5["U"][i], str(i)))
    mean_gain = sum(gain_if_flip.values()) / len(cand)
    curve, acc_cp, acc_u = [], sum(base_right.values()), sum(base_right.values())
    for k in range(len(cand) + 1):
        if k:
            acc_cp += gain_if_flip[order_cp[k - 1]]
            acc_u += gain_if_flip[order_u[k - 1]]
        curve.append({"k": k, "conf_product": acc_cp, "strategy5_U": acc_u,
                      "random_expected": sum(base_right.values()) + k * mean_gain})
    out["override_curve"] = {
        "description": "correct count when F(decisions) additionally escalates the k least-confident bugs it had not escalated",
        "base_correct": sum(base_right.values()), "n_candidates": len(cand),
        "candidates_whose_target_is_escalate": sum(per[i]["a_star"] == "escalate" for i in cand),
        "points": curve}
    out["auroc_override_vs_target_escalate"] = {
        "conf_product_low": auroc([-(cp[i] if cp[i] is not None else -1) for i in cand],
                                  [per[i]["a_star"] == "escalate" for i in cand]),
        "strategy5_U_high": auroc([s5["U"][i] for i in cand], [per[i]["a_star"] == "escalate" for i in cand])}
    # Operational question the a* grading does not ask: does low composed
    # confidence flag the bugs where F(decisions) is WRONG (any class)?
    cp_all = {i: conf_product(*inst[n][1:]) for n, i in enumerate(ids)}
    f_wrong = [not base_right[i] for i in ids]
    out["auroc_confidence_flags_F_error"] = {
        "n_F_wrong": sum(f_wrong),
        "conf_product_low": auroc([-(cp_all[i] if cp_all[i] is not None else -1) for i in ids], f_wrong),
        "strategy5_U_high": auroc([s5["U"][i] for i in ids], f_wrong),
        "score_conf_low": auroc([-(per[i]["red"]["score"]["mean_confidence"] or 0.0) for i in ids], f_wrong)}

    # 4. discrimination of each node's confidence for its own agreement
    ch_ok = [per[i]["red"]["choice"]["modal_decision"] == per[i]["bug"]["group"] for i in ids]
    ch_c = [per[i]["red"]["choice"]["mean_confidence"] or 0.0 for i in ids]
    nl_ok = [per[i]["red"]["noul"]["decision"] == per[i]["bug"]["regression"] for i in ids]
    nl_c = [2 * abs(per[i]["red"]["noul"]["mean_noul"] - 0.5) for i in ids]
    sc_ok = [per[i]["red"]["score"]["modal_decision"] is not None
             and int(per[i]["red"]["score"]["modal_decision"]) == per[i]["bug"]["level"] for i in ids]
    sc_c = [per[i]["red"]["score"]["mean_confidence"] or 0.0 for i in ids]
    out["auroc_own_confidence_vs_own_agreement"] = {
        "choice": auroc(ch_c, ch_ok), "noul": auroc(nl_c, nl_ok), "score": auroc(sc_c, sc_ok),
        "errors": {"choice": ch_ok.count(False), "noul": nl_ok.count(False), "score": sc_ok.count(False)},
        "choice_errors_at_conf_ge_0.90": sum(1 for c, k in zip(ch_c, ch_ok) if c >= 0.90 and not k)}
    nl_dir = Counter((per[i]["bug"]["regression"], per[i]["red"]["noul"]["decision"]) for i in ids)
    out["noul_confusion_true_vs_jev"] = {f"{t}->{d}": v for (t, d), v in nl_dir.items()}

    # 5. score error audit (project criteria arm)
    def lvl(i, arm="score"):
        d = per[i]["red"][arm]["modal_decision"]
        return None if d is None else int(d)
    audit = {}
    for name, sel, err in (
            ("serious_underrated", lambda b: b["level"] == 2, lambda i: lvl(i) is not None and lvl(i) < 2),
            ("minor_overrated", lambda b: b["level"] == 0, lambda i: lvl(i) is not None and lvl(i) > 0)):
        grp = defaultdict(lambda: [0, 0])
        for i in ids:
            b = per[i]["bug"]
            if not sel(b):
                continue
            keys = [f"severity={b['severity']}", f"group={b['group']}", f"regression={b['regression']}",
                    f"crash={b['crash']}", f"recent={b['recent_12_months']}",
                    "length=" + ("short<400" if len(b["text"]) < 400 else "long>=400")]
            for key in keys:
                grp[key][1] += 1
                grp[key][0] += err(i)
        audit[name] = {k: {"errors": v[0], "n": v[1]} for k, v in sorted(grp.items())}
    out["score_error_audit"] = audit
    out["score_mean_confidence_by_true_level"] = {
        t: sum(sc_c[n] for n, i in enumerate(ids) if per[i]["bug"]["level"] == t)
        / sum(1 for i in ids if per[i]["bug"]["level"] == t) for t in (0, 1, 2)}

    # 6. Revision 12's primary tests applied DESCRIPTIVELY (R_OVERRIDE was
    #    fixed in the Revision 12 addendum before this was computed; Mozilla
    #    sets no Step 2 constant, and these p-values are not confirmatory).
    a_star = {i: per[i]["a_star"] for i in ids}
    h2a = strategy_2h(base, inst)
    h5a = strategy_5h(base, inst)
    out["revision12_tests_descriptive"] = {
        "r_override": R_OVERRIDE,
        "H1_2h_vs_random": h1_randomization_test(base, h2a, a_star),
        "H1_5h_vs_random": h1_randomization_test(base, h5a, a_star) if h5a else "NOT COMPUTABLE",
        "H2_5h_vs_2h": h2_sign_flip_test(h5a, h2a, a_star) if h5a else "NOT COMPUTABLE",
        "Y_decision": {"1": sum(base_right.values()),
                       "2h": sum(h2a[i] == a_star[i] for i in ids),
                       "5h": sum(h5a[i] == a_star[i] for i in ids) if h5a else None}}

    OUT_JSON.write_text(json.dumps(out, indent=2, default=str))
    print(json.dumps({k: v for k, v in out.items() if k != "override_curve"}, indent=1, default=str))
    oc = out["override_curve"]
    print("override base", oc["base_correct"], "candidates", oc["n_candidates"],
          "of which target escalate", oc["candidates_whose_target_is_escalate"])
    for p in oc["points"]:
        if p["k"] in (0, 3, 5, 10, 15, 20, 30, 50, 86, oc["n_candidates"]):
            print(p)


if __name__ == "__main__":
    main()
