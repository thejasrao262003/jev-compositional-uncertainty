"""Builds the blinded packet for human_target_validation_protocol.md. No model calls.
  python3 research/src/build_adjudication_packet.py"""
import json, random, zlib
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
HELD = ROOT / "research" / "data" / "heldout"
OUT = ROOT / "research" / "data" / "adjudication"
rng = random.Random(zlib.crc32(b"adjudication"))
pick = []
for t in ("mozilla", "kernel"):
    bugs = [json.loads(l) for l in (HELD / f"{t}_heldout.jsonl").open()]
    pick += [(t, b) for b in rng.sample(bugs, 25)]
rng.shuffle(pick)
OUT.mkdir(parents=True, exist_ok=True)
codes = {f"H{i + 1:02d}": {"tracker": t, "bug_id": b["bug_id"]} for i, (t, b) in enumerate(pick)}
with (OUT / "packet.md").open("w") as f:
    f.write("# Blinded rating packet (50 bug reports)\n\nRate each report using the rubric in "
            "`research/methodology/human_target_validation_protocol.md`. Do not look anything up.\n\n")
    for c, (t, b) in zip(codes, pick):
        f.write(f"---\n\n## {c}\n\n```\n{b['text']}\n```\n\n")
(OUT / "key_DO_NOT_OPEN_UNTIL_RATED.json").write_text(json.dumps(codes, indent=1))
hdr = "code,severity(0/1/2/cant_tell),regression(yes/no/cant_tell),action(accept/defer/escalate/cant_tell),reason_if_action_differs\n"
for who in ("TM", "TPR"):
    (OUT / f"ratings_{who}_TEMPLATE.csv").write_text(hdr + "".join(f"{c},,,,\n" for c in codes))
print("packet written:", len(codes), "bugs ->", OUT / "packet.md")
