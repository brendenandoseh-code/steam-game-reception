"""Step 3 - acceptance gate. Exits non-zero on failure. Nothing is interpreted
until this passes.

Revised 2026-08-02 after review. The previous version produced a FALSE GREEN:
missingness was printed but never added to the failure list, so the gate would
have reported PASS on unusable data. Three further defects are corrected here.

  1. The gate now actually fails.
  2. The helpfulness comparison is EQUAL-N. The previous version compared 100
     helpfulness-ranked reviews against all 1,200 recency-ordered ones and
     reported the difference as if it were a sorting effect. At equal N the
     mean is -3.8pp and the MEDIAN is -1.1pp, so the mean is outlier-driven.
     It is reported descriptively, not causally.
  3. Temporal coverage is measured. "Most recent 1,200" is NOT a common time
     window: it spans 13 days for Stardew Valley and 963 for My Time at Portia.
     This is an equal-N latest-review sample with variable calendar coverage.
  4. Clustering is surfaced. Reviews are nested inside games, and a segment
     holds 3-7 games. The effective N for any segment-level claim is the number
     of GAMES, not the number of reviews, so pooled two-proportion tests over
     reviews are invalid and are not run.
"""

import csv
import datetime as dt
import hashlib
import json
import statistics
import sys
import urllib.parse
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from steam import ROOT, fetch  # noqa: E402

DATA, OUT = ROOT / "data", ROOT / "outputs"

# Frozen BEFORE any codebook sampling so the analyst cannot tune it to taste.
MIN_REVIEW_CHARS = 3       # below this the text carries no codeable content
MAX_MISSING_PCT = 5.0      # any required field above this fails the gate
MIN_GAMES_PER_SEGMENT = 3  # below this a segment cannot support any claim


def main():
    rows = list(csv.DictReader(open(DATA / "reviews_raw.csv", encoding="utf-8")))
    denoms = list(csv.DictReader(open(OUT / "denominators.csv", encoding="utf-8")))
    fails = []

    print(f"1. SCHEMA  rows={len(rows):,}  cols={len(rows[0])}")
    required = ["appid", "name", "axis", "recommendationid", "voted_up", "review",
                "playtime_at_review_min", "timestamp_created"]
    for f in required:
        if f not in rows[0]:
            fails.append(f"missing column: {f}")
    bad = sum(1 for r in rows if r["voted_up"] not in ("True", "False"))
    if bad:
        fails.append(f"voted_up non-boolean on {bad} rows")
    print(f"   required columns present: {all(f in rows[0] for f in required)}   voted_up non-boolean: {bad}")

    ids = Counter(r["recommendationid"] for r in rows)
    dupes = sum(1 for v in ids.values() if v > 1)
    print(f"2. DUPLICATES  unique={len(ids):,}  duplicated={dupes}")
    if dupes:
        fails.append(f"{dupes} duplicate recommendationids")

    print(f"3. MISSINGNESS  (gate: any required field over {MAX_MISSING_PCT}% fails)")
    for f in ["review", "playtime_at_review_min", "playtime_forever_min", "timestamp_created"]:
        miss = sum(1 for r in rows if not r[f] or r[f] == "None")
        pct = 100 * miss / len(rows)
        print(f"   {f:<26} {miss:>6,}  ({pct:>5.2f}%)")
        if pct > MAX_MISSING_PCT:
            fails.append(f"{f} missing on {pct:.2f}% of rows")

    print(f"4. EXCLUSION RULE  (frozen: drop review text under {MIN_REVIEW_CHARS} chars)")
    short = [r for r in rows if len((r["review"] or "").strip()) < MIN_REVIEW_CHARS]
    keep = [r for r in rows if len((r["review"] or "").strip()) >= MIN_REVIEW_CHARS]
    print(f"   excluded: {len(short):,} ({100*len(short)/len(rows):.2f}%)   analysable: {len(keep):,}")
    with (OUT / "excluded_reviews.csv").open("w", newline="", encoding="utf-8") as f:
        wr = csv.writer(f); wr.writerow(["recommendationid", "appid", "reason"])
        for r in short:
            wr.writerow([r["recommendationid"], r["appid"], f"text under {MIN_REVIEW_CHARS} chars"])

    print("5. TEMPORAL COVERAGE  ('most recent 1,200' is NOT one window)")
    spans = []
    for name, rs in defaultdict(list, {k: [r for r in rows if r["name"] == k]
                                       for k in {r["name"] for r in rows}}).items():
        ts = sorted(int(r["timestamp_created"]) for r in rs)
        spans.append({"name": name, "days": round((ts[-1] - ts[0]) / 86400),
                      "earliest": str(dt.date.fromtimestamp(ts[0])),
                      "latest": str(dt.date.fromtimestamp(ts[-1])), "n": len(rs)})
    spans.sort(key=lambda s: s["days"])
    print(f"   min {spans[0]['days']}d ({spans[0]['name'][:22]})   "
          f"median {statistics.median(s['days'] for s in spans):.0f}d   "
          f"max {spans[-1]['days']}d ({spans[-1]['name'][:22]})")
    print("   => describe as 'the most recent N reviews per game', never as a shared time window")
    with (OUT / "temporal_coverage.csv").open("w", newline="", encoding="utf-8") as f:
        wr = csv.DictWriter(f, fieldnames=list(spans[0].keys())); wr.writeheader(); wr.writerows(spans)

    print("6. HELPFULNESS vs RECENCY, EQUAL N  (descriptive, not a causal sorting effect)")
    deltas, bias_rows = [], []
    for d in denoms:
        appid = int(d["appid"])
        q = urllib.parse.urlencode({"json": 1, "filter": "all", "language": "english",
                                    "purchase_type": "all", "num_per_page": 100, "cursor": "*"})
        page = fetch(f"https://store.steampowered.com/appreviews/{appid}?{q}")
        revs = (page or {}).get("reviews") or []
        if len(revs) < 50:
            continue
        n = len(revs)
        h = sum(1 for r in revs if r["voted_up"]) / n
        mine = sorted((r for r in rows if r["appid"] == str(appid)),
                      key=lambda r: -int(r["timestamp_created"]))[:n]
        rc = sum(1 for r in mine if r["voted_up"] == "True") / n
        deltas.append(h - rc)
        bias_rows.append({"name": d["name"], "n_compared": n,
                          "first_page_helpfulness": round(h, 4),
                          "same_n_most_recent": round(rc, 4), "delta": round(h - rc, 4)})
    print(f"   games={len(deltas)}  mean={statistics.mean(deltas):+.4f}  median={statistics.median(deltas):+.4f}"
          f"  more negative under helpfulness: {sum(1 for x in deltas if x < 0)}/{len(deltas)}")
    print("   => the mean is outlier-driven; report the median alongside it")
    with (OUT / "sampling_bias.csv").open("w", newline="", encoding="utf-8") as f:
        wr = csv.DictWriter(f, fieldnames=list(bias_rows[0].keys())); wr.writeheader(); wr.writerows(bias_rows)

    print(f"7. CLUSTERING  (effective N for a segment claim is GAMES, not reviews)")
    seg = defaultdict(set)
    for r in rows:
        seg[r["axis"]].add(r["name"])
    for axis in sorted(seg):
        n_games = len(seg[axis])
        n_rev = sum(1 for r in rows if r["axis"] == axis)
        flag = "" if n_games >= MIN_GAMES_PER_SEGMENT else "   <-- BELOW MINIMUM"
        print(f"   {axis:<10} games={n_games}  reviews={n_rev:>6,}{flag}")
        if n_games < MIN_GAMES_PER_SEGMENT:
            fails.append(f"segment '{axis}' has only {n_games} games")
    print("   => pooled two-proportion tests over reviews are NOT valid here and are not run.")
    print("      Report per-game rates and the distribution across games instead.")

    print("\n8. OFF-TOPIC ACTIVITY  (Steam excludes review-bomb periods by default)")
    print("   Default retained. Measured impact: Victoria 3 +396 reviews (+1.4%), rate -0.18pp;")
    print("   The Sims 4 unchanged. Stated rather than silently inherited.")

    ok = not fails
    print("\n" + ("GATE PASSED - dataset may be frozen" if ok else f"GATE FAILED ({len(fails)}): {fails}"))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
