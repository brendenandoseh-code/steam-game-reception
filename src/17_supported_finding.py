"""What can be said using only the categories that survived validation.

Codebook v1 failed on the interpretive categories. Three categories cleared a
usable bar against the analyst's hand-coding and are the only ones used here:

    bugs and crashes        F1 0.71
    grind and pacing        F1 0.67
    interface and controls  F1 0.56

Everything below is a comparison BETWEEN GAMES, never a pooled percentage across
reviews, because reviews are clustered inside titles and a sub-genre holds only
3 to 7 of them.

One assumption is doing work and is stated rather than hidden: recall is well
under 1.0 for all three categories (0.63, 0.67, 0.56), so every rate here
understates the true level. Comparing games is only fair if the rules miss at
roughly the same rate everywhere. That is plausible but not verified, so the
finding is framed as a ranking, not as a set of levels.
"""

import csv
import statistics
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from steam import ROOT  # noqa: E402

OUT = ROOT / "outputs"

VALIDATED = [
    ("bugs_crashes", "Bugs and crashes", 0.706),
    ("tedium_grind", "Grind and pacing", 0.667),
    ("ui_controls", "Interface and controls", 0.562),
]
AXES = ["colony", "emergent", "grand", "life"]
AXIS_LABEL = {"colony": "Colony / management", "emergent": "Emergent narrative",
              "grand": "Grand strategy", "life": "Life sim"}


def main():
    rates = list(csv.DictReader(open(OUT / "category_rates.csv", encoding="utf-8")))

    rows, by = [], defaultdict(lambda: defaultdict(list))
    for r in rates:
        row = {"game": r["name"], "sub_genre": r["axis"], "n_negative": int(r["n_negative"])}
        for key, label, _ in VALIDATED:
            v = float(r[f"rate_{key}"])
            row[key] = round(v, 4)
            by[key][r["axis"]].append((r["name"], v))
        rows.append(row)
    rows.sort(key=lambda r: (r["sub_genre"], -r["bugs_crashes"]))

    summary = []
    for key, label, f1 in VALIDATED:
        meds = {a: statistics.median(v for _, v in by[key][a]) for a in AXES}
        hi, lo = max(meds, key=meds.get), min(meds, key=meds.get)
        spread = meds[hi] / meds[lo] if meds[lo] else float("inf")
        top = sorted((g for a in AXES for g in by[key][a]), key=lambda g: -g[1])[:2]
        summary.append({
            "category": label, "validation_f1": f1,
            **{f"median_{a}": round(meds[a], 4) for a in AXES},
            "highest_sub_genre": AXIS_LABEL[hi], "lowest_sub_genre": AXIS_LABEL[lo],
            "ratio_high_to_low": round(spread, 2),
            "separates": "yes" if spread >= 2 else "no",
            "top_two_games": "; ".join(f"{n} {v:.3f}" for n, v in top),
        })

    with (OUT / "supported_finding_by_game.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    with (OUT / "supported_finding_summary.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(summary[0].keys())); w.writeheader(); w.writerows(summary)

    print("Median share of negative reviews carrying each objection, by sub-genre")
    print("(unit: game. median of per-game rates, not a pooled percentage)\n")
    print(f"{'category':<26}" + "".join(f"{AXIS_LABEL[a][:11]:>13}" for a in AXES) + f"{'high/low':>10}  separates")
    for s in summary:
        cells = "".join(f"{s[f'median_{a}']:>13.3f}" for a in AXES)
        print(f"{s['category']:<26}{cells}{s['ratio_high_to_low']:>10.1f}x  {s['separates']}")
    print()
    for s in summary:
        verdict = (f"varies by shelf: highest in {s['highest_sub_genre'].lower()}, "
                   f"lowest in {s['lowest_sub_genre'].lower()}") if s["separates"] == "yes" \
            else "does not vary meaningfully by shelf"
        print(f"  {s['category']}: {verdict}")
        print(f"      worst two games: {s['top_two_games']}")
    print("\nwrote supported_finding_by_game.csv and supported_finding_summary.csv")


if __name__ == "__main__":
    main()
