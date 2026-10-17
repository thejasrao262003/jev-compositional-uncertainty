"""Robustness checks requested in review of the cross-model results. EXPLORATORY
(not pre-registered); no API calls; reads committed outputs only.

1. 95% bootstrap CIs (stratified by tracker, B=2000) for E_dec, E_jev_frozen and
   final-step confidence, per model, with n.
2. Leakage: bug-id overlap and exact / near-duplicate text between the 442
   training and 500 held-out bugs (near-duplicate = word-shingle Jaccard >= 0.8).
3. Additional baselines on the held-out split:
   low routing (choice) confidence, low regression (noul) confidence,
   severity-distribution entropy, and two class-frequency rules fit on the
   model's own training bugs: error rate by predicted severity level, and
   error rate by workflow action.
4. Readout sensitivity: OLMo X1/X2 excluding bugs with any request whose label
   mass < 0.5; and the superseded (readout v1) vs corrected (v2) numbers.

  python3 research/src/openjev/robustness_checks.py
"""
from __future__ import annotations

import json
import math
import re
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))
import analyze_crossmodel as ac  # noqa: E402
import run_heldout_validation as hv  # noqa: E402
import workflow_risk_probe as wp  # noqa: E402

ROOT = HERE.parents[2]
OUT = ROOT / "research" / "results" / "openjev_robustness_checks.json"
LABELS = {"Jev 1.13": None, **{m: m.replace("/", "__") for m in ac.MODELS}}


def ci(rows, col):
    vals = hv.boot(rows, lambda rs: hv._auc(rs, col))
    return [round(vals[int(0.025 * len(vals))], 3), round(vals[int(0.975 * len(vals)) - 1], 3)]


def jev_heldout_P():
    data = hv.load_heldout()
    rows = [json.loads(line) for line in hv.raw_path(False).open()]
    P = hv.per_bug(data, rows)
    for k, p in P.items():
        p["split"] = "heldout"
    return P


def jev_train_P():
    out = {}
    for d in ("mozilla", "kernel"):
        for i, p in ac.__dict__.get("_unused", {}).items():
            pass
        import paper_statistics as ps
        sys.path.insert(0, str(ROOT / "research" / "paper" / "latex"))
        for bid, p in ps.load(d).items():
            out[("train", d, bid)] = {"split": "train", "tracker": d, "red": p["red"], "s1": p["s1"],
                                     "a_star": p["a_star"], "bug": p["bug"]}
    return out


def extra_scores(held, train):
    """Single-signal and class-frequency baselines (higher = riskier)."""
    def lvl(p):
        d = p["red"]["score"]["modal_decision"]
        return "unstable" if d is None else str(d)
    rate_lvl, rate_act = defaultdict(lambda: [0, 0]), defaultdict(lambda: [0, 0])
    for p in train:
        y = int(p["s1"] != p["a_star"])
        rate_lvl[lvl(p)][0] += y
        rate_lvl[lvl(p)][1] += 1
        rate_act[p["s1"]][0] += y
        rate_act[p["s1"]][1] += 1
    prior = sum(int(p["s1"] != p["a_star"]) for p in train) / len(train)
    rl = {k: (a + prior) / (n + 1) for k, (a, n) in rate_lvl.items()}   # light smoothing toward the prior
    ra = {k: (a + prior) / (n + 1) for k, (a, n) in rate_act.items()}
    rows = []
    for key, p in held.items():
        dec, unc = wp.features(p)
        rows.append({"tracker": p["tracker"], "y": int(p["s1"] != p["a_star"]),
                     "low_choice_conf": -unc["choice_conf"], "low_noul_conf": -unc["noul_conf"],
                     "score_entropy": unc["score_entropy"],
                     "rule_rate_by_severity": rl.get(lvl(p), prior), "rule_rate_by_action": ra.get(p["s1"], prior)})
    return rows


def shingles(t, k=5):
    w = re.findall(r"\w+", t.lower())
    return {" ".join(w[i:i + k]) for i in range(max(1, len(w) - k + 1))}


def leakage():
    idx = ac.bugs_index()
    tr = {k: b for k, b in idx.items() if k[0] == "train"}
    he = {k: b for k, b in idx.items() if k[0] == "heldout"}
    id_overlap = {(k[1], k[2]) for k in tr} & {(k[1], k[2]) for k in he}
    tr_text = {b["text_sha256"] for b in tr.values()}
    exact = sum(1 for b in he.values() if b["text_sha256"] in tr_text)
    trs = [(k, shingles(b["text"])) for k, b in tr.items()]
    near, worst = 0, 0.0
    for b in he.values():
        s = shingles(b["text"])
        best = max((len(s & t) / len(s | t) for _, t in trs if s and t), default=0)
        worst = max(worst, best)
        near += best >= 0.8
    return {"bug_id_overlap": len(id_overlap), "exact_text_duplicates": exact,
            "near_duplicates_jaccard_ge_0.8": near, "max_jaccard_any_heldout_vs_train": round(worst, 3)}


def main():
    out = {"status": "EXPLORATORY robustness checks (not pre-registered)", "leakage": leakage(), "models": {}}
    jev_est = hv.load_estimator()
    idx = ac.bugs_index()
    # Jev reference
    jh = jev_heldout_P()
    S = ac.score_rows(jh, {"DECISION": jev_est["estimators"]["DECISION"], "ALL": jev_est["estimators"]["ALL"]}, jev_est)
    jt = list(jev_train_P().values())
    X = extra_scores(jh, jt)
    out["models"]["Jev 1.13"] = {"n_heldout": len(S),
                                 "E_dec": [round(hv._auc(S, "E_dec"), 3), ci(S, "E_dec")],
                                 "final_step_conf": [round(hv._auc(S, "low_score_conf"), 3), ci(S, "low_score_conf")],
                                 **{c: round(hv._auc(X, c), 3) for c in ("low_choice_conf", "low_noul_conf", "score_entropy",
                                                                         "rule_rate_by_severity", "rule_rate_by_action")}}
    for m in ac.MODELS:
        f = ac.DATA / f"{m.replace('/', '__')}_raw_responses.jsonl"
        raw = [json.loads(line) for line in f.open()]
        P = ac.per_bug(raw, idx)
        train = [p for p in P.values() if p["split"] == "train"]
        held = {k: p for k, p in P.items() if p["split"] == "heldout"}
        fitted = {}
        for kind in ("DECISION", "ALL"):
            feats = [wp.vec({"dec": wp.features(p)[0], "unc": wp.features(p)[1]}, kind) for p in train]
            names = sorted(wp.features(train[0])[0]) if kind == "DECISION" else \
                sorted({**wp.features(train[0])[0], **wp.features(train[0])[1]})
            fitted[kind] = {"features": names, **wp.fit(feats, [int(p["s1"] != p["a_star"]) for p in train])}
        S = ac.score_rows(held, fitted, jev_est)
        X = extra_scores(held, train)
        rec = {"n_heldout": len(S),
               "E_dec": [round(hv._auc(S, "E_dec"), 3), ci(S, "E_dec")],
               "E_jev_frozen": [round(hv._auc(S, "E_jev_frozen"), 3), ci(S, "E_jev_frozen")],
               "final_step_conf": [round(hv._auc(S, "low_score_conf"), 3), ci(S, "low_score_conf")],
               **{c: round(hv._auc(X, c), 3) for c in ("low_choice_conf", "low_noul_conf", "score_entropy",
                                                       "rule_rate_by_severity", "rule_rate_by_action")}}
        # readout sensitivity: drop bugs with any low-mass request
        if "label_mass" in raw[0]:
            low = {(r["split"], r["tracker"], r["bug_id"]) for r in raw if r.get("label_mass", 1) < 0.5}
            Sk = [r for r in S if r["key"] not in low]
            rec["excluding_low_label_mass_bugs"] = {
                "bugs_dropped_heldout": len(S) - len(Sk),
                "E_dec": round(hv._auc(Sk, "E_dec"), 3), "final_step_conf": round(hv._auc(Sk, "low_score_conf"), 3)}
        out["models"][m] = rec
    sup = json.loads((ROOT / "research" / "data" / "openjev_superseded_readout_v1" / "interim_analysis_buggy_readout.json").read_text())
    out["readout_v1_vs_v2"] = {m: {"v1_E_dec_vs_conf": [sup["models"][m]["X1"]["auroc_E_dec"], sup["models"][m]["X1"]["auroc_low_score_conf"]],
                                   "v2_E_dec_vs_conf": out["models"][m]["E_dec"][0:1] + out["models"][m]["final_step_conf"][0:1]}
                               for m in sup["models"] if isinstance(sup["models"][m], dict)}
    OUT.write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
