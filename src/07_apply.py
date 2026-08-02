"""Day 2 step 3 - apply the frozen codebook to every eligible negative review.

Writes:
  outputs/coded_negatives.csv       one row per review, one column per category
  outputs/category_rates.csv        per-GAME rates (the correct grain, see below)
The blinded held-out coding sheet is built separately by 08_coding_sheet.py.
An earlier version built it here and truncated the text at 1,200 characters,
which meant human and machine would have judged different text on 21 reviews.

Grain discipline: rates are computed per GAME and then described across games.
Reviews are clustered inside games and a sub-genre holds only 3-7 of them, so a
pooled review-level percentage would imply far more independent information than
exists. Every rate here carries the game it came from.
"""

import csv
import importlib.util
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from steam import ROOT  # noqa: E402

spec = importlib.util.spec_from_file_location("codebook", Path(__file__).parent / "06_codebook.py")
cb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cb)

DATA, OUT = ROOT / "data", ROOT / "outputs"


def main():
    excluded = {r["recommendationid"] for r in
                csv.DictReader(open(OUT / "excluded_reviews.csv", encoding="utf-8"))}

    coded, by_game = [], defaultdict(lambda: defaultdict(int))
    for r in csv.DictReader(open(DATA / "reviews_raw.csv", encoding="utf-8")):
        if r["voted_up"] != "False" or r["recommendationid"] in excluded:
            continue
        codes = cb.code(r["review"])
        row = {"recommendationid": r["recommendationid"], "appid": r["appid"],
               "name": r["name"], "axis": r["axis"], "n_labels": len(codes)}
        for c in cb.CATEGORIES:
            row[c] = int(c in codes)
        coded.append(row)
        by_game[(r["appid"], r["name"], r["axis"])]["_n"] += 1
        for c in codes:
            by_game[(r["appid"], r["name"], r["axis"])][c] += 1

    with (OUT / "coded_negatives.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(coded[0].keys())); w.writeheader(); w.writerows(coded)

    rates = []
    for (appid, name, axis), c in sorted(by_game.items(), key=lambda kv: kv[0][1]):
        row = {"appid": appid, "name": name, "axis": axis, "n_negative": c["_n"]}
        for cat in cb.CATEGORIES:
            row[f"rate_{cat}"] = round(c[cat] / c["_n"], 4)
        rates.append(row)
    with (OUT / "category_rates.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rates[0].keys())); w.writeheader(); w.writerows(rates)


    print(f"coded {len(coded):,} negative reviews across {len(rates)} games")
    print(f"mean labels per review: {sum(r['n_labels'] for r in coded)/len(coded):.2f}")
    print(f"\nper-category: share of reviews, and the SPREAD ACROSS GAMES (min-max of per-game rates)")
    print(f"   {'category':<24}{'pooled':>8}{'per-game min':>14}{'median':>9}{'max':>8}")
    import statistics
    for cat in cb.CATEGORIES:
        pooled = sum(r[cat] for r in coded) / len(coded)
        per_game = sorted(r[f"rate_{cat}"] for r in rates)
        print(f"   {cat:<24}{pooled:>8.3f}{per_game[0]:>14.3f}"
              f"{statistics.median(per_game):>9.3f}{per_game[-1]:>8.3f}")
    print("\nwrote coded_negatives.csv, category_rates.csv")


if __name__ == "__main__":
    main()
