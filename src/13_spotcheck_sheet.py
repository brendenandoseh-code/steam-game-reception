"""Day 3 - build the analyst's blank spot-check sheet.

30 rows drawn from the held-out 150. Blank labels, full text, no machine
predictions and no reference labels, so the analyst codes them cold. The
disagreement rate between these and the AI-produced reference labels is what
tells a reader how much to trust the reference labels at all.
"""

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from steam import ROOT  # noqa: E402

OUT = ROOT / "outputs"
COLS = ["bugs_crashes", "performance", "ui_controls", "opacity_teaching", "tedium_grind",
        "monetization_dlc", "unfinished_abandoned", "update_regression", "npc_ai_pathing",
        "shallow_repetitive", "procgen_hollow", "rng_unfair", "difficulty_punishing",
        "developer_conduct", "taste_mismatch", "non_substantive"]


def main():
    picks = {r["row"] for r in csv.DictReader(open(OUT / "spotcheck_rows.csv", encoding="utf-8"))}
    sheet = [r for r in csv.DictReader(open(OUT / "heldout_coding_sheet.csv", encoding="utf-8"))
             if r["row"] in picks]
    assert len(sheet) == 30, len(sheet)

    rows = [{"row": s["row"], "review_text": s["review_text"], **{c: "" for c in COLS}}
            for s in sheet]
    path = OUT / "analyst_spotcheck_sheet.csv"
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    print(f"wrote {path.name}: {len(rows)} rows, {len(COLS)} blank label columns")
    print("  contains: row number, full review text")
    print("  withheld: game, sub-genre, machine predictions, reference labels")


if __name__ == "__main__":
    main()
