"""Formal H1/H2b statistical write-up for Stage 1 `choice` + `noul`.

Per step0b_design_specification.md §8A/§9 and the collaborator-authorized
7-step order. `score` is not included (still blocked). This is a
CONFIRMATORY analysis pass on already-collected, frozen data - it makes
no new API calls and does not modify the manifest, labels, or item set.

Brier-score terminology fix (per review): `choice`'s original single-term
"(1-p_reference)^2" calculation is preserved below as an audit artifact,
clearly labeled as the one-term convention. A NEW unified metric is added
that uses the SAME formally defined 2-term binary scoring rule for both
primitives (mapping each primitive's output to "probability assigned to
the reference/correct outcome", y=1 by construction on non-contested
items), so `choice` and `noul` are only ever compared under one common,
explicitly stated convention - never the mismatched one-term-vs-native
forms from the previous report.
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SRC_DIR))

from analyze_stage1 import (  # noqa: E402
    compute_presentation_sensitivity,
    compute_repeat_instability,
    load_gate_outcomes,
    noul_h2a_passed,
    selected_decision,
)

REPO_ROOT = SRC_DIR.parent.parent
DATA_DIR = REPO_ROOT / "research" / "data" / "characterization"
RESULTS_DIR = REPO_ROOT / "research" / "results"
RAW_PATH = DATA_DIR / "stage1_raw_responses.jsonl"
MANIFEST_PATH = DATA_DIR / "stage1_manifest_choice_noul.json"
GATE_PATH = DATA_DIR / "stage0_gate_outcomes.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def confidence_like(answer: dict) -> float:
    if answer["type"] == "choice":
        return answer["confidence"]
    if answer["type"] == "noul":
        return abs(answer["noul"] - 0.5) * 2
    raise ValueError(answer["type"])


def p_reference(record: dict) -> float:
    """Probability the primitive assigns to the reference/correct outcome,
    unified convention (used ONLY for the new comparable Brier metric)."""
    ans = record["answer"]
    ref = record["reference_label"]
    if ans["type"] == "choice":
        return ans["probabilities"].get(ref, 0.0)
    if ans["type"] == "noul":
        return ans["noul"] if ref == "yes" else (1 - ans["noul"])
    raise ValueError(ans["type"])


def wilson_interval(successes: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (float("nan"), float("nan"))
    phat = successes / n
    denom = 1 + z ** 2 / n
    center = (phat + z ** 2 / (2 * n)) / denom
    half = (z * math.sqrt(phat * (1 - phat) / n + z ** 2 / (4 * n ** 2))) / denom
    return (max(0.0, center - half), min(1.0, center + half))


def spearman(xs: list[float], ys: list[float]) -> float | None:
    """Manual Spearman rank correlation (average ranks for ties). Returns
    None if either series has zero variance (undefined correlation)."""
    n = len(xs)
    if n < 3:
        return None

    def ranks(vals: list[float]) -> list[float]:
        order = sorted(range(n), key=lambda i: vals[i])
        r = [0.0] * n
        i = 0
        while i < n:
            j = i
            while j + 1 < n and vals[order[j + 1]] == vals[order[i]]:
                j += 1
            avg_rank = (i + j) / 2 + 1
            for k in range(i, j + 1):
                r[order[k]] = avg_rank
            i = j + 1
        return r

    rx, ry = ranks(xs), ranks(ys)
    mx, my = sum(rx) / n, sum(ry) / n
    num = sum((rx[i] - mx) * (ry[i] - my) for i in range(n))
    denx = math.sqrt(sum((v - mx) ** 2 for v in rx))
    deny = math.sqrt(sum((v - my) ** 2 for v in ry))
    if denx == 0 or deny == 0:
        return None
    return num / (denx * deny)


def reliability_table_equal_width(items: list[dict], n_bins: int = 4) -> list[dict]:
    bins = [[] for _ in range(n_bins)]
    for r in items:
        c = confidence_like(r["answer"])
        correct = selected_decision(r["answer"]) == r["reference_label"]
        idx = min(int(c * n_bins), n_bins - 1)
        bins[idx].append((c, correct))
    out = []
    for i, b in enumerate(bins):
        lo, hi = i / n_bins, (i + 1) / n_bins
        if b:
            mean_conf = sum(c for c, _ in b) / len(b)
            acc = sum(1 for _, k in b if k) / len(b)
            out.append({"bin": f"[{lo:.2f},{hi:.2f}{']' if i == n_bins - 1 else ')'}",
                        "n": len(b), "mean_confidence": mean_conf, "observed_accuracy": acc,
                        "gap": abs(mean_conf - acc)})
        else:
            out.append({"bin": f"[{lo:.2f},{hi:.2f}{']' if i == n_bins - 1 else ')'}",
                        "n": 0, "mean_confidence": None, "observed_accuracy": None, "gap": None})
    return out


def reliability_table_equal_mass(items: list[dict], n_bins: int = 4) -> list[dict]:
    scored = sorted(items, key=lambda r: confidence_like(r["answer"]))
    n = len(scored)
    base = n // n_bins
    extra = n % n_bins
    out = []
    idx = 0
    for i in range(n_bins):
        size = base + (1 if i < extra else 0)
        chunk = scored[idx: idx + size]
        idx += size
        if chunk:
            confs = [confidence_like(r["answer"]) for r in chunk]
            corrects = [selected_decision(r["answer"]) == r["reference_label"] for r in chunk]
            mean_conf = sum(confs) / len(confs)
            acc = sum(corrects) / len(corrects)
            out.append({"bin": f"rank-group {i+1}/{n_bins} (conf {min(confs):.2f}-{max(confs):.2f})",
                        "n": len(chunk), "mean_confidence": mean_conf, "observed_accuracy": acc,
                        "gap": abs(mean_conf - acc)})
        else:
            out.append({"bin": f"rank-group {i+1}/{n_bins}", "n": 0, "mean_confidence": None,
                        "observed_accuracy": None, "gap": None})
    return out


def ece(table: list[dict], n_total: int) -> float:
    return sum((b["n"] / n_total) * b["gap"] for b in table if b["n"] > 0)


def main() -> None:
    lines = []

    def p(*a):
        s = " ".join(str(x) for x in a)
        print(s)
        lines.append(s)

    rows = [json.loads(l) for l in RAW_PATH.open() if l.strip()]
    manifest = json.loads(MANIFEST_PATH.read_text())
    gate_outcomes = load_gate_outcomes()
    subset_ids = set(manifest["robustness_repeat_subset_ids"])

    p("# Step 1. Frozen analysis input")
    p(f"- raw responses: {RAW_PATH.name} sha256={sha(RAW_PATH)[:16]}...")
    p(f"- manifest: {MANIFEST_PATH.name} sha256={sha(MANIFEST_PATH)[:16]}...")
    p(f"- Stage 0 gate outcomes: {GATE_PATH.name} sha256={sha(GATE_PATH)[:16]}...")
    p(f"- this analysis script: {Path(__file__).name} sha256={sha(Path(__file__))[:16]}...")
    p(f"- noul H2a recorded status: pass={noul_h2a_passed(gate_outcomes)}")
    p()

    canonical = [r for r in rows if r["call_purpose"] == "primary_canonical"]

    p("# Step 2. Scoring-rule definitions (resolved per review)")
    p("- `choice` one-term metric (AUDIT ARTIFACT, preserved, NOT used for cross-primitive")
    p("  comparison): Brier_1term_i = (1 - probabilities[reference_label])^2, y=1 constant.")
    p("- `noul` native metric (AUDIT ARTIFACT, preserved, NOT used for cross-primitive")
    p("  comparison): Brier_native_i = (y_i - noul_value)^2, y_i = 1[reference_label=='yes'].")
    p("- **NEW, unified, cross-primitive-comparable metric**: for BOTH primitives, define")
    p("  p_ref = P(primitive assigns to the reference/correct outcome) - for `choice`,")
    p("  probabilities[reference_label]; for `noul`, noul_value if reference=='yes' else")
    p("  1-noul_value. Then Brier_unified_i = 2 * (1 - p_ref)^2 (the standard 2-term binary")
    p("  Brier score (p-1)^2+(1-p)^2, since y=1 by construction on non-contested items).")
    p("  THIS is the only metric compared across primitives below.")
    p()

    p("# Step 3. Rank correlation (Spearman, confidence-like vs. correctness)")
    for primitive in ("choice", "noul"):
        nc = [r for r in canonical if r["primitive"] == primitive and not r["is_contested"]]
        confs = [confidence_like(r["answer"]) for r in nc]
        correct = [1.0 if selected_decision(r["answer"]) == r["reference_label"] else 0.0 for r in nc]
        rho = spearman(confs, correct)
        p(f"  [{primitive}] n={len(nc)}, quantity correlated: confidence-like "
          f"({'top-two probability gap' if primitive == 'choice' else '2*|noul-0.5|'}) vs. "
          f"binary correctness (1=selected-decision matches reference_label).")
        p(f"    expected direction (H1/H2b): positive (higher confidence -> higher correctness)")
        if rho is None:
            n_correct = sum(correct)
            cause = (f"correctness was constant (y_i=1 for all {len(nc)} observations, {int(n_correct)}/{len(nc)} correct)"
                     if len(set(correct)) == 1 else "confidence-like was constant across all observations")
            p(f"    Spearman rho: NOT COMPUTED - {cause}, producing zero variance and an undefined "
              f"correlation. This is a precise, stated cause, not a generic 'insufficient data' note.")
        else:
            p(f"    Spearman rho: {rho:.3f} (n={len(nc)} non-contested items out of 30 primary items for "
              f"this primitive; this measures RANK ASSOCIATION between confidence-like and correctness, "
              f"NOT a calibration test - P(correct|confidence=c)~=c is a stronger, separate claim this "
              f"statistic does not address; no significance test performed, n too small for a reliable p-value)")
    p()

    p("# Step 4. Reliability summaries (two binning schemes, both with counts, per §8A)")
    for primitive in ("choice", "noul"):
        nc = [r for r in canonical if r["primitive"] == primitive and not r["is_contested"]]
        p(f"  [{primitive}] n={len(nc)}")
        ew = reliability_table_equal_width(nc, 4)
        em = reliability_table_equal_mass(nc, 4)
        p(f"    -- equal-width binning (4 bins) --")
        for b in ew:
            if b["n"]:
                p(f"      {b['bin']:14s} n={b['n']:3d} mean_conf={b['mean_confidence']:.3f} "
                  f"obs_acc={b['observed_accuracy']:.3f} |gap|={b['gap']:.3f}")
            else:
                p(f"      {b['bin']:14s} n=0 (empty bin)")
        p(f"    ECE (equal-width): {ece(ew, len(nc)):.4f}")
        p(f"    -- equal-mass binning (4 rank-groups; ties may straddle a group boundary,")
        p(f"       disclosed limitation at this n) --")
        for b in em:
            if b["n"]:
                p(f"      {b['bin']:34s} n={b['n']:3d} mean_conf={b['mean_confidence']:.3f} "
                  f"obs_acc={b['observed_accuracy']:.3f} |gap|={b['gap']:.3f}")
            else:
                p(f"      {b['bin']:34s} n=0")
        p(f"    ECE (equal-mass): {ece(em, len(nc)):.4f}")
    p()

    p("# Step 5. Scoring metrics (accuracy w/ Wilson CI, all three Brier variants)")
    for primitive in ("choice", "noul"):
        nc = [r for r in canonical if r["primitive"] == primitive and not r["is_contested"]]
        matches = sum(1 for r in nc if selected_decision(r["answer"]) == r["reference_label"])
        lo, hi = wilson_interval(matches, len(nc))
        p(f"  [{primitive}] accuracy: {matches}/{len(nc)} = {matches/len(nc):.3f}, "
          f"95% Wilson CI [{lo:.3f}, {hi:.3f}] (n={len(nc)}, small-sample - wide interval expected)")
        briers_unified = [2 * (1 - p_reference(r)) ** 2 for r in nc]
        p(f"    Brier (unified, cross-primitive-comparable): {sum(briers_unified)/len(briers_unified):.4f}")
        if primitive == "choice":
            b1 = [(1 - r["answer"]["probabilities"].get(r["reference_label"], 0.0)) ** 2 for r in nc]
            p(f"    Brier (one-term, audit artifact only): {sum(b1)/len(b1):.4f}")
        else:
            bn = [(1.0 if r["reference_label"] == "yes" else 0.0) - r["answer"]["noul"] for r in nc]
            bn = [x ** 2 for x in bn]
            p(f"    Brier (native, audit artifact only): {sum(bn)/len(bn):.4f}")
    p()
    p("  Metric comparability vs. experimental comparability (per review, stated explicitly):")
    p("  the unified Brier score places both primitives on the same formal binary scoring")
    p("  convention - that is a mathematical fact. It does NOT make the two numbers evidence")
    p("  of one primitive being 'more reliable' than the other, because: (1) different")
    p("  primitive semantics (choice vs. noul), (2) different constructed item sets and")
    p("  domains, (3) different native uncertainty representations, (4) construction-defined")
    p("  (not independently validated) reference labels, and (5) no controlled assignment of")
    p("  the same inputs to both primitives. Metric comparability is not experimental")
    p("  comparability - the gap between 0.458 and 0.056 below is descriptive, not causal.")
    p()

    p("# Step 6. Repeat and presentation subsets (12-item subset, NOT extrapolated to full sample)")
    repeat_results, repeat_missing = compute_repeat_instability(rows, gate_outcomes, subset_ids)
    pres_results, pres_missing = compute_presentation_sensitivity(rows, gate_outcomes, subset_ids)
    mean_S = sum(v["S"] for v in repeat_results.values()) / len(repeat_results)
    any_flips = sum(1 for v in repeat_results.values() if v["any_flip"])
    mean_D = sum(v["D"] for v in pres_results.values()) / len(pres_results)
    any_label_changes = sum(1 for v in pres_results.values() if v["label_changes"])
    p(f"  repeat instability: {len(repeat_results)}/12 complete, mean S={mean_S:.3f}, "
      f"items with any flip: {any_flips}/{len(repeat_results)}")
    p(f"  presentation sensitivity: {len(pres_results)}/12 complete, mean D={mean_D:.3f} "
      f"(D=1/3 per item = stable, see §prior report), items with any label change: "
      f"{any_label_changes}/{len(pres_results)}")
    p(f"  This subset (12 of 60 primary items, ~20% per the preregistered sampling rate) is the")
    p(f"  ONLY basis for these two statistics - not generalized to the other 48 items or to")
    p(f"  other evidence pools/domains not tested.")
    p()

    p("# Step 7. Hedged summary (descriptive observation / statistical association / uncertainty / hypothesis stance)")
    p("  Terminology note (per review): 'calibration' below means the formal property")
    p("  P(correct|confidence=c) ~= c. Accuracy, rank association, and calibration are three")
    p("  DIFFERENT properties - a primitive can show one without the others. None of Step 3-6's")
    p("  statistics directly test calibration; they are reliability/confidence-correctness")
    p("  evidence relevant to it, not a calibration test.")
    p()
    p("  [choice]")
    p("    Descriptive observation: under the construction-defined benchmark and canonical")
    p("    presentation used in this study, choice matched its reference label on 18/24")
    p("    non-contested items (95% CI [0.55,0.88]).")
    p("    Statistical association: weak positive rank association (Spearman rho=0.25, n=24,")
    p("    no significance test performed) - directionally consistent with H1's claimed")
    p("    relationship, but weak.")
    p("    Reliability pattern: equal-mass binning identified a high-confidence subgroup (rank-")
    p("    group 2/4: mean confidence 0.915, observed accuracy 0.333, n=6) with a large gap; this")
    p("    subgroup is also part of the dominant high-confidence region under equal-width binning,")
    p("    so the pattern is reflected under both tested partitions on THIS sample. This does NOT")
    p("    establish the pattern is independent of binning choice in general - equal-mass groups")
    p("    are data-dependent, ties can straddle group boundaries, and n=6 in that subgroup is")
    p("    small. See stage1_h1h2b_item_level_audit.csv for the underlying 6 items.")
    p("    Uncertainty: n=24 is small; Wilson interval is wide; several reliability bins have")
    p("    n<=6.")
    p("    Hypothesis stance: the positive rank association is directionally consistent with")
    p("    H1, but it is weak, uncorrected for multiple comparisons, and co-occurs with a")
    p("    high-confidence/low-accuracy subgroup in the same sample - confidence ordering and")
    p("    reliability were not uniformly aligned here. The findings are descriptive; they do")
    p("    not establish general calibration or a dependably useful confidence-based ranking.")
    p()
    p("  [noul]")
    p("    Descriptive observation: noul matched its reference label on all 24/24 non-contested")
    p("    items (95% CI [0.86,1.00]). All four reliability bins (both binning schemes) show")
    p("    100% observed accuracy, while mean confidence-like was below 1.0 in every bin")
    p("    (0.19-0.87 across bins) - i.e., confidence values were systematically below the")
    p("    accuracy actually observed in every bin (underconfidence relative to this sample,")
    p("    not overconfidence).")
    p("    Statistical association: NOT COMPUTED - correctness was constant (y_i=1 for all 24")
    p("    observations), producing zero outcome variance and an undefined correlation.")
    p("    Uncertainty: n=24 is small; perfect observed accuracy in a sample of 24 does not")
    p("    establish the primitive's general error rate (the Wilson interval's lower bound is")
    p("    0.86, not 1.00). The nonzero ECE (0.2542, both binning schemes - identical here")
    p("    because the outcome is constant) means confidence-like values did not numerically")
    p("    match observed accuracy in any bin, even though every decision was correct.")
    p("    Hypothesis stance: the results establish perfect observed correctness within this")
    p("    non-contested sample. They do NOT establish calibration (nonzero reliability gaps in")
    p("    every bin) or a positive confidence-correctness relationship (undefined at this")
    p("    sample's zero outcome variance) - accuracy, calibration, and discrimination are")
    p("    different properties, and only the first is demonstrated here.")

    p()
    p("# Step 8. Supplementary item-level audit table (verifiability, per review)")
    audit_rows = []
    for primitive in ("choice", "noul"):
        nc = [r for r in canonical if r["primitive"] == primitive and not r["is_contested"]]
        em = reliability_table_equal_mass(nc, 4)
        scored = sorted(nc, key=lambda r: confidence_like(r["answer"]))
        n = len(scored)
        base, extra = n // 4, n % 4
        idx = 0
        for i in range(4):
            size = base + (1 if i < extra else 0)
            for r in scored[idx: idx + size]:
                audit_rows.append({
                    "primitive": primitive, "item_id": r["item_id"],
                    "confidence_like": round(confidence_like(r["answer"]), 4),
                    "predicted_decision": selected_decision(r["answer"]),
                    "reference_label": r["reference_label"], "is_contested": r["is_contested"],
                    "correct": selected_decision(r["answer"]) == r["reference_label"],
                    "equal_mass_rank_group": i + 1,
                })
            idx += size
    csv_path = RESULTS_DIR / "stage1_h1h2b_item_level_audit.csv"
    import csv as _csv
    with csv_path.open("w", newline="") as f:
        w = _csv.DictWriter(f, fieldnames=list(audit_rows[0].keys()))
        w.writeheader()
        w.writerows(audit_rows)
    p(f"  Wrote {len(audit_rows)} rows (all 48 non-contested choice+noul items, full audit")
    p(f"  trail: item_id, confidence-like, predicted decision, reference label, correctness,")
    p(f"  equal-mass rank-group assignment) to {csv_path.name}")

    out_path = RESULTS_DIR / "stage1_h1h2b_analysis.md"
    out_path.write_text("# Stage 1 H1/H2b Formal Statistical Write-up (`choice` + `noul`)\n\n"
                         "`score` excluded (blocked). Confirmatory analysis on frozen, already-"
                         "collected data - no new API calls, no manifest/label changes.\n\n```\n"
                         + "\n".join(lines) + "\n```\n")
    print(f"\nWritten to {out_path}")


if __name__ == "__main__":
    main()
