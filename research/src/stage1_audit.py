"""Stage 1 post-execution audit: descriptive, protocol-oriented only.

Per review: "the first analysis pass should be descriptive and
protocol-oriented... Only after this audit should the H1/H2b analysis
proceed." This script computes the eight requested categories mechanically
- it does NOT draw any H1/H2b conclusion (does not say "this confirms/
refutes calibration"). Numbers are reported plainly; interpretation is
deferred to a separately-labeled follow-up analysis pass.

Uses analyze_stage1.py's actual (self-tested, H2a-gated, complete-cell-
enforcing) functions for repeat instability and presentation sensitivity -
not reimplemented here.
"""

from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SRC_DIR))

from analyze_stage1 import (  # noqa: E402
    compute_presentation_sensitivity,
    compute_repeat_instability,
    load_gate_outcomes,
    noul_h2a_passed,
    top_two_gap,
)

REPO_ROOT = SRC_DIR.parent.parent
DATA_DIR = REPO_ROOT / "research" / "data" / "characterization"
RAW_PATH = DATA_DIR / "stage1_raw_responses.jsonl"
MANIFEST_PATH = DATA_DIR / "stage1_manifest_choice_noul.json"


def selected_decision(answer: dict) -> str:
    if answer["type"] == "choice":
        return answer["choice"]
    if answer["type"] == "noul":
        return "yes" if answer["noul"] >= 0.5 else "no"
    raise ValueError(answer["type"])


def confidence_like(answer: dict) -> float:
    """Choice: confidence field. Noul: distance-from-0.5 concentration analogue (2*|v-0.5|)."""
    if answer["type"] == "choice":
        return answer["confidence"]
    if answer["type"] == "noul":
        return abs(answer["noul"] - 0.5) * 2
    raise ValueError(answer["type"])


def main() -> None:
    rows = [json.loads(l) for l in RAW_PATH.open() if l.strip()]
    manifest = json.loads(MANIFEST_PATH.read_text())
    items_by_id = {it["item_id"]: it for it in manifest["items"]}
    gate_outcomes = load_gate_outcomes()

    report_lines = []

    def p(*a):
        s = " ".join(str(x) for x in a)
        print(s)
        report_lines.append(s)

    p("=" * 70)
    p("1. Call success and schema validation")
    p("=" * 70)
    p(f"  total rows: {len(rows)}")
    p(f"  http status counts: {Counter(r['http_status'] for r in rows)}")
    p(f"  rows with error set: {sum(1 for r in rows if r['error'])}")
    p(f"  rows with unparsed answer: {sum(1 for r in rows if r['answer'] is None)}")

    p()
    p("=" * 70)
    p("2. Model-version consistency")
    p("=" * 70)
    models = Counter(r["raw_response"]["model"] for r in rows)
    p(f"  models observed: {dict(models)}")

    p()
    p("=" * 70)
    p("3. Missingness and replacement accounting")
    p("=" * 70)
    purpose_counts = Counter((r["item_id"], r["call_purpose"]) for r in rows)
    expected_singles = sum(1 for (iid, purpose), c in purpose_counts.items() if purpose != "canonical_repeat")
    expected_repeats = sum(c for (iid, purpose), c in purpose_counts.items() if purpose == "canonical_repeat")
    p(f"  distinct (item,purpose) cells with purpose != canonical_repeat: {expected_singles} (expect 60+12+12=84)")
    p(f"  canonical_repeat calls total: {expected_repeats} (expect 24)")
    p(f"  overflow/replacement item calls made: {sum(1 for r in rows if 'overflow' in r['item_id'])} (expect 0)")

    p()
    p("=" * 70)
    p("4. Complete-cell eligibility (via analyze_stage1.py, H2a-gated)")
    p("=" * 70)
    p(f"  Stage 0 noul H2a recorded status: pass={noul_h2a_passed(gate_outcomes)}")
    subset_ids = set(manifest["robustness_repeat_subset_ids"])
    p(f"  Layer 2/3 subset size (items designed to receive repeats/alt presentations): {len(subset_ids)}")
    p(f"  (NOTE: the other {60 - len(subset_ids)} primary items were only ever planned to get 1 canonical "
      f"call each - they are correctly OUT OF SCOPE for this layer, not 'missing'. An earlier version of "
      f"this audit conflated the two; fixed in analyze_stage1.py before this report was finalized.)")
    repeat_results, repeat_missing = compute_repeat_instability(rows, gate_outcomes, subset_ids)
    pres_results, pres_missing = compute_presentation_sensitivity(rows, gate_outcomes, subset_ids)
    p(f"  repeat-instability: {len(repeat_results)} complete items, {len(repeat_missing)} incomplete (expect 12, 0)")
    p(f"  presentation-sensitivity: {len(pres_results)} complete items, {len(pres_missing)} incomplete (expect 12, 0)")
    if repeat_missing:
        p(f"  INCOMPLETE (repeat): {repeat_missing}")
    if pres_missing:
        p(f"  INCOMPLETE (presentation): {pres_missing}")

    p()
    p("=" * 70)
    p("5. Canonical output summaries (primary_canonical calls only, descriptive)")
    p("=" * 70)
    canonical = [r for r in rows if r["call_purpose"] == "primary_canonical"]
    for primitive in ("choice", "noul"):
        prim_rows = [r for r in canonical if r["primitive"] == primitive]
        confs = [confidence_like(r["answer"]) for r in prim_rows]
        contested = [r for r in prim_rows if r["is_contested"]]
        noncontested = [r for r in prim_rows if not r["is_contested"]]
        p(f"  [{primitive}] n={len(prim_rows)} (contested={len(contested)}, non-contested={len(noncontested)})")
        p(f"    confidence-like: min={min(confs):.3f} max={max(confs):.3f} mean={sum(confs)/len(confs):.3f}")
        saturated = sum(1 for c in confs if c >= 0.9)
        p(f"    saturation rate (confidence-like >= 0.9): {saturated}/{len(confs)} = {saturated/len(confs):.2%}")
        by_cond = Counter(r["condition"] for r in prim_rows)
        p(f"    items by condition: {dict(by_cond)}")

    p()
    p("=" * 70)
    p("6. Repeat instability and presentation sensitivity (full results)")
    p("=" * 70)
    p("  Metric direction, stated explicitly: D(x) = (distinct selected decisions)/k.")
    p("  D=1/3=0.333 means ONE distinct decision across all 3 presentations (STABLE),")
    p("  not three distinct decisions. D=1.0 would mean maximal diversity (all 3 differed).")
    p("  Higher D = more diversity/instability, lower D = more stability. Stated here so")
    p("  it isn't misread as '33% stable' or similar.")
    p("  This subset is 12 items (of 60 primary items) per the preregistered design -")
    p("  results below characterize only this subset, not the full manifest or other pools.")
    p("  -- repeat instability (S, I) --")
    for item_id, res in sorted(repeat_results.items()):
        p(f"    {item_id:35s} S={res['S']:.3f} I={res['I']:.3f} flip={res['any_flip']} decisions={res['decisions']}")
    p("  -- presentation sensitivity (D) --")
    for item_id, res in sorted(pres_results.items()):
        p(f"    {item_id:35s} D={res['D']:.3f} top_prob_range={res['top_prob_range']:.3f} "
          f"max_pairwise_diff={res['max_pairwise_diff']:.3f} label_changes={res['label_changes']}")

    p()
    p("=" * 70)
    p("7. Predefined primitive-specific metrics (mechanical computation only -")
    p("   NOT an H1/H2b interpretation; that is a separate, later step)")
    p("=" * 70)
    p("  Per-primitive quantity definitions, stated explicitly before the numbers (per review Check A/C):")
    p("  [choice] predicted event = 'the selected/canonical reference_label option is correct'.")
    p("           Brier input probability p_i = probabilities[reference_label] (the model's own")
    p("           probability mass on the reference option, NOT the top-two gap). y_i = 1 always,")
    p("           by construction, since we condition on the reference_label being the target event")
    p("           being scored -> Brier_i = (1 - p_i)^2. This is the single-term 'probability of the")
    p("           reference class' formulation, NOT summed across both classes (that variant would")
    p("           be exactly 2x these values for a 2-option choice) - stated so the two conventions")
    p("           are never confused.")
    p("  [noul]   predicted event = 'reference_label == yes'. Brier input probability p_i = the raw")
    p("           `noul` value directly (native primitive output, NOT a transform). y_i = 1 if")
    p("           reference_label=='yes' else 0 -> Brier_i = (y_i - p_i)^2. Standard textbook binary")
    p("           Brier score, no simplification needed (noul has only one probability field).")
    p("  The 'confidence-like' quantity (top-two gap for choice; 2*|noul-0.5| for noul) is used ONLY")
    p("  for the saturation-rate stat above and the reliability-table x-axis below - it is NEVER the")
    p("  input to the Brier calculation for either primitive. Pre-specified in step0b_design_specification.md")
    p("  §8B (g(x) definition) before this data was collected, not chosen after seeing results.")
    p("  Expected direction: higher confidence-like -> expected higher observed accuracy (this is H1/H2b's")
    p("  claim, tested here only as a plain bin table, not yet as a correlation statistic or verdict).")
    for primitive in ("choice", "noul"):
        nc = [r for r in canonical if r["primitive"] == primitive and not r["is_contested"]]
        matches = sum(1 for r in nc if selected_decision(r["answer"]) == r["reference_label"])
        p(f"  [{primitive}] non-contested n={len(nc)}, selected-decision == reference_label: "
          f"{matches}/{len(nc)} = {matches/len(nc):.2%}")
        briers = []
        for r in nc:
            ans = r["answer"]
            if ans["type"] == "choice":
                p_ref = ans["probabilities"].get(r["reference_label"], 0.0)
                briers.append((1 - p_ref) ** 2)
            elif ans["type"] == "noul":
                y = 1.0 if r["reference_label"] == "yes" else 0.0
                briers.append((y - ans["noul"]) ** 2)
        if briers:
            p(f"    Brier score (definition above, non-contested only): {sum(briers)/len(briers):.4f} (n={len(briers)})")
        # 4-bin reliability table, explicit closed/open endpoint convention (per review Check B):
        # bins are left-closed/right-open EXCEPT the last bin, which is closed at 1.00
        # (min(int(c*4),3) already implements this: c=1.0 -> bin index 3, not a 5th bin).
        bins = defaultdict(list)
        for r in nc:
            c = confidence_like(r["answer"])
            correct = selected_decision(r["answer"]) == r["reference_label"]
            bin_idx = min(int(c * 4), 3)
            bins[bin_idx].append(correct)
        p(f"    reliability table (confidence-like -> observed accuracy; bins [0,.25),[.25,.5),[.5,.75),[.75,1.00],")
        p(f"    last bin closed at 1.00, bin counts shown):")
        bin_labels = ["[0.00,0.25)", "[0.25,0.50)", "[0.50,0.75)", "[0.75,1.00]"]
        for i in range(4):
            b = bins.get(i, [])
            if b:
                p(f"      {bin_labels[i]}: n={len(b)} observed_accuracy={sum(b)/len(b):.2%}")
            else:
                p(f"      {bin_labels[i]}: n=0 (empty bin)")

    p()
    p("=" * 70)
    p("8. Deviations from the preregistered execution plan")
    p("=" * 70)
    deviations = []
    if len(rows) != 108:
        deviations.append(f"call count {len(rows)} != planned 108")
    if set(models.keys()) != {"jev-1.13.0"}:
        deviations.append(f"model version drift: {models}")
    if any(r["http_status"] != 200 for r in rows):
        deviations.append("non-200 responses occurred")
    if sum(1 for r in rows if "overflow" in r["item_id"]) != 0:
        deviations.append("overflow/reserve items were called")
    if repeat_missing or pres_missing:
        deviations.append("incomplete cells present")
    p(f"  Deviations found: {deviations if deviations else 'NONE'}")

    out_path = DATA_DIR.parent.parent / "results" / "stage1_execution_audit.md"
    out_path.write_text("# Stage 1 Execution Audit (descriptive, protocol-oriented)\n\n```\n" + "\n".join(report_lines) + "\n```\n")
    print(f"\nWritten to {out_path}")


if __name__ == "__main__":
    main()
