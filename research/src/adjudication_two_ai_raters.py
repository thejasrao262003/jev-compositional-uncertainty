"""Two-AI-rater analysis (human_target_validation_protocol.md, Amendment 2). Exploratory. No API calls.
Rater 1 = AI pilot (Amendment 1 mapping, R1/R2); rater 2 = ratings_CLAUDE.csv (full rubric).
  .venv/bin/python research/src/adjudication_two_ai_raters.py"""
import csv, json, random, sys
from collections import Counter
from pathlib import Path
SRC = Path(__file__).resolve().parent
sys.path.insert(0, str(SRC))
import intervention_test as it  # noqa: E402
from build_workflow_calibration_pilot_manifest import F  # noqa: E402
from adjudication_ai_pilot_lib import wilson, kappa  # noqa: E402
ROOT = SRC.parents[1]
ADJ = ROOT / "research" / "data" / "adjudication"
OUT = ROOT / "research" / "results" / "adjudication_two_ai_raters.json"
CT = {"cant_tell", "request_evidence"}


def kboot(a, b, seed=1):
    rng = random.Random(seed); ks = []
    for _ in range(2000):
        idx = [rng.randrange(len(a)) for _ in a]
        v = kappa([a[i] for i in idx], [b[i] for i in idx])
        if v == v:
            ks.append(v)
    ks.sort()
    return [round(ks[int(.025 * len(ks))], 3), round(ks[int(.975 * len(ks)) - 1], 3)]


def pair(a, b, name):
    keep = [(x, y) for x, y in zip(a, b) if x not in CT and y not in CT]
    xa, xb = [x for x, _ in keep], [y for _, y in keep]
    k = sum(x == y for x, y in keep)
    return {"comparison": name, "n": len(keep), "agree": k, "agreement": round(k / len(keep), 3),
            "wilson95": wilson(k, len(keep)), "kappa": round(kappa(xa, xb), 3), "kappa_ci95": kboot(xa, xb)}


key = json.loads((ADJ / "key_DO_NOT_OPEN_UNTIL_RATED.json").read_text())
labels = {}
for t in ("mozilla", "kernel"):
    for l in (ROOT / "research" / "data" / "heldout" / f"{t}_heldout.jsonl").open():
        b = json.loads(l); labels[(t, b["bug_id"])] = b
_, held, _ = it.load_model("Jev 1.13")
ai = {r["code"]: r["action"] for r in csv.DictReader((ADJ / "ratings_AI_pilot.tsv").open(), delimiter="\t")}
cl = {r["code"]: r for r in csv.DictReader((ADJ / "ratings_CLAUDE.csv").open())}
SEV, REG, ACT = ("severity(0/1/2/cant_tell)", "regression(yes/no/cant_tell)", "action(accept/defer/escalate/cant_tell)")
rows = []
for code in sorted(key):
    t, bid = key[code]["tracker"], key[code]["bug_id"]
    b = labels[(t, bid)]
    c = cl[code]
    sev = int(c[SEV]) if c[SEV] in "012" else None
    reg = {"yes": 1, "no": 0}.get(c[REG])
    rows.append({"code": code, "tracker": t, "level": b["level"], "regression": b["regression"],
                 "a_star": F(b["regression"], b["level"]), "jev": held[(t, bid)]["s1"],
                 "r1_R1": ai[code], "r1_R2": {"defer": "accept"}.get(ai[code], ai[code]),
                 "r2": c[ACT], "r2_sev": sev, "r2_reg": reg,
                 "r2_rule": F(reg, sev) if sev is not None and reg is not None else "cant_tell"})
col = lambda k: [r[k] for r in rows]
out = {"status": "EXPLORATORY two-AI-rater analysis (Amendment 2); NOT the pre-registered human validation; "
                 "rater 2 is the study's analysis assistant, knows F, not blind to the study design",
       "n": len(rows), "target_mix": dict(Counter(col("a_star"))), "rater2_action_mix": dict(Counter(col("r2"))),
       "rater2_cant_tell": {"severity": sum(r["r2_sev"] is None for r in rows),
                            "regression": sum(r["r2_reg"] is None for r in rows),
                            "action": sum(r["r2"] in CT for r in rows)}}
out["action"] = [
    pair(col("r1_R1"), col("r2"), "rater1(R1) vs rater2  [inter-rater baseline]"),
    pair(col("r1_R2"), col("r2"), "rater1(R2) vs rater2  [inter-rater baseline]"),
    pair(col("r2"), col("a_star"), "rater2 vs a*"),
    pair(col("r1_R1"), col("a_star"), "rater1(R1) vs a*"),
    pair(col("r1_R2"), col("a_star"), "rater1(R2) vs a*"),
    pair(col("r2_rule"), col("a_star"), "F(rater2 severity, regression) vs a*  [label validity, end to end]"),
    pair(col("r2_rule"), col("r2"), "F(rater2 labels) vs rater2 direct action  [rule validity]"),
]
out["label_validity"] = {
    "severity": pair([str(r["r2_sev"]) if r["r2_sev"] is not None else "cant_tell" for r in rows],
                     [str(r["level"]) for r in rows], "rater2 severity vs tracker level"),
    "regression": pair([str(r["r2_reg"]) if r["r2_reg"] is not None else "cant_tell" for r in rows],
                       [str(r["regression"]) for r in rows], "rater2 regression vs tracker regression"),
    "severity_confusion": dict(sorted(Counter(f"tracker={r['level']} / rater2={r['r2_sev']}" for r in rows).items())),
    "regression_confusion": dict(sorted(Counter(f"tracker={r['regression']} / rater2={r['r2_reg']}" for r in rows).items())),
}
att = Counter()
for r in rows:
    if r["r2"] in CT or r["r2"] == r["a_star"]:
        continue
    if r["r2_rule"] == "cant_tell":
        att["ambiguity (rater can't tell severity or regression)"] += 1
        att["of which raters also disagree"] += r["r1_R1"] in CT or r["r1_R2"] != r["r2"]
        continue
    lab = r["r2_rule"] != r["a_star"]
    rule = r["r2_rule"] != r["r2"]
    amb = r["r2_rule"] == "cant_tell" or r["r1_R1"] in CT or r["r1_R2"] != r["r2"]
    att["label-driven" if lab and not rule else "rule-driven" if rule and not lab else
        "both" if lab and rule else "neither"] += 1
    att["of which raters also disagree"] += amb
out["error_attribution_rater2_vs_a_star"] = dict(att)
out["confusion_rater2_vs_a_star"] = dict(sorted(Counter(f"target={r['a_star']} / rater2={r['r2']}" for r in rows).items()))
R = [r for r in rows if r["r2"] not in CT]
jw, jr = [r["jev"] != r["a_star"] for r in R], [r["jev"] != r["r2"] for r in R]
out["failure_label_check"] = {"n": len(R), "jev_wrong_vs_a_star": sum(jw), "jev_wrong_vs_rater2": sum(jr),
                              "agreement": round(sum(x == y for x, y in zip(jw, jr)) / len(R), 3)}
OUT.write_text(json.dumps(out, indent=2))
print(json.dumps(out, indent=1))
