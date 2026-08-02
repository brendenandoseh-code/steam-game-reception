"""Step 3 - acceptance gate. NON-MUTATING ON FAILURE. Exits non-zero on failure.

Revision history, because both bugs are instructive:

rev1 produced a FALSE GREEN: missingness printed but never entered the failure
     list, so the gate reported PASS on unusable data.

rev2 fixed that but was DESTRUCTIVE ON FAILURE: it wrote canonical outputs while
     checks were still running. A mutation test that correctly returned non-zero
     had already overwritten three output files with results computed from the
     mutated input. Restoring the input did not restore the outputs, and the
     corrupted state was committed. The freeze manifest detected it - but only
     because someone finally ran a verification pass.

rev3 (this file) computes every output in memory and writes canonical files only
     after all checks pass. A failing run touches nothing.

The lesson worth keeping: a failing test is not automatically non-destructive.
"""

import csv
import datetime as dt
import statistics
import sys
import urllib.parse
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from steam import ROOT, fetch  # noqa: E402

DATA, OUT = ROOT / "data", ROOT / "outputs"

# Frozen BEFORE any codebook sampling so it cannot be tuned to taste.
MIN_REVIEW_CHARS = 3
# Below this, a default-vs-included difference cannot be told apart from
# reviews accruing between the two requests (captured 22-59 min apart).
AMBIGUITY_FLOOR = 100
MAX_MISSING_PCT = 5.0
MIN_GAMES_PER_SEGMENT = 3
# Parsed as ints downstream, so any blank is a crash rather than a clean failure.
ZERO_TOLERANCE = ["timestamp_created", "playtime_at_review_min", "playtime_forever_min"]
REQUIRED = ["appid", "name", "axis", "recommendationid", "voted_up", "review",
            "playtime_at_review_min", "playtime_forever_min", "timestamp_created"]


def utc_date(ts: int) -> str:
    """UTC, not local time. date.fromtimestamp() makes hashes machine-dependent."""
    return dt.datetime.fromtimestamp(int(ts), dt.timezone.utc).date().isoformat()


def write_csv(path: Path, rows):
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def main():
    fails, pending = [], {}          # pending = {filename: rows}, written only on pass

    rows = list(csv.DictReader(open(DATA / "reviews_raw.csv", encoding="utf-8")))
    if not rows:
        print("GATE FAILED: reviews_raw.csv is empty")
        return 1
    denoms = list(csv.DictReader(open(OUT / "denominators.csv", encoding="utf-8")))

    print(f"1. SCHEMA  rows={len(rows):,}  cols={len(rows[0])}")
    missing_cols = [c for c in REQUIRED if c not in rows[0]]
    if missing_cols:
        print(f"   GATE FAILED: missing required columns {missing_cols}")
        return 1                     # bail cleanly rather than IndexError downstream
    bad = sum(1 for r in rows if r["voted_up"] not in ("True", "False"))
    if bad:
        fails.append(f"voted_up non-boolean on {bad} rows")
    print(f"   required columns present: yes   voted_up non-boolean: {bad}")

    ids = Counter(r["recommendationid"] for r in rows)
    dupes = sum(1 for v in ids.values() if v > 1)
    print(f"2. DUPLICATES  unique={len(ids):,}  duplicated={dupes}")
    if dupes:
        fails.append(f"{dupes} duplicate recommendationids")

    print(f"3. MISSINGNESS  (gate: {MAX_MISSING_PCT}% tolerance, except ZERO_TOLERANCE fields)")
    for f in ["review", "playtime_at_review_min", "playtime_forever_min", "timestamp_created"]:
        miss = sum(1 for r in rows if not r[f] or r[f] == "None")
        pct = 100 * miss / len(rows)
        zero = f in ZERO_TOLERANCE
        print(f"   {f:<26} {miss:>6,}  ({pct:>5.2f}%){'   [zero-tolerance]' if zero else ''}")
        if zero and miss:
            # These are parsed as ints downstream. One blank produces a traceback
            # rather than a clean failure, so they cannot carry any tolerance.
            fails.append(f"{f} missing on {miss} rows (zero-tolerance field)")
        elif not zero and pct > MAX_MISSING_PCT:
            fails.append(f"{f} missing on {pct:.2f}% of rows")

    non_numeric = [f for f in ZERO_TOLERANCE
                   if any(not str(r[f]).lstrip("-").isdigit() for r in rows)]
    if non_numeric:
        fails.append(f"non-numeric values in {non_numeric}")

    if fails:
        # Bail before any step that assumes clean types, so a data defect
        # reports as a gate failure rather than a traceback.
        print(f"\nGATE FAILED ({len(fails)}): {fails}")
        print("No canonical outputs were written.")
        return 1

    print("4. RECONCILIATION vs denominators.csv (per game)")
    raw_ids = {r["appid"] for r in rows}
    den_ids = {d["appid"] for d in denoms}
    if raw_ids != den_ids:
        fails.append(f"appid sets differ: raw-only={sorted(raw_ids-den_ids)} denom-only={sorted(den_ids-raw_ids)}")
    by_game = defaultdict(list)
    for r in rows:
        by_game[r["appid"]].append(r)
    mismatch = 0
    for d in denoms:
        rs = by_game.get(d["appid"], [])
        n_ok = len(rs) == int(d["sampled_n"])
        p_ok = sum(1 for r in rs if r["voted_up"] == "True") == int(d["sampled_positive"])
        if not (n_ok and p_ok):
            mismatch += 1
            fails.append(f"{d['name']}: raw rows/positives disagree with denominators.csv")
    print(f"   games reconciled: {len(denoms) - mismatch}/{len(denoms)}")

    print(f"5. EXCLUSION RULE  (frozen: drop review text under {MIN_REVIEW_CHARS} chars)")
    short = [r for r in rows if len((r["review"] or "").strip()) < MIN_REVIEW_CHARS]
    print(f"   excluded: {len(short):,} ({100*len(short)/len(rows):.2f}%)   analysable: {len(rows)-len(short):,}")
    pending["excluded_reviews.csv"] = [
        {"recommendationid": r["recommendationid"], "appid": r["appid"],
         "reason": f"text under {MIN_REVIEW_CHARS} chars"} for r in short
    ] or [{"recommendationid": "", "appid": "", "reason": ""}]

    print("6. TEMPORAL COVERAGE  ('most recent N' is NOT one window)")
    spans = []
    for name in sorted({r["name"] for r in rows}):
        ts = sorted(int(r["timestamp_created"]) for r in rows if r["name"] == name)
        spans.append({"name": name, "n": len(ts), "days": round((ts[-1] - ts[0]) / 86400),
                      "earliest_utc": utc_date(ts[0]), "latest_utc": utc_date(ts[-1])})
    spans.sort(key=lambda s: s["days"])
    print(f"   games={len(spans)}  min {spans[0]['days']}d ({spans[0]['name'][:20]})  "
          f"median {statistics.median(s['days'] for s in spans):.0f}d  "
          f"max {spans[-1]['days']}d ({spans[-1]['name'][:20]})")
    pending["temporal_coverage.csv"] = spans

    print("7. HELPFULNESS vs RECENCY, EQUAL N  (descriptive, not a causal sorting effect)")
    deltas, bias_rows = [], []
    for d in denoms:
        q = urllib.parse.urlencode({"json": 1, "filter": "all", "language": "english",
                                    "purchase_type": "all", "num_per_page": 100, "cursor": "*"})
        page = fetch(f"https://store.steampowered.com/appreviews/{d['appid']}?{q}")
        revs = (page or {}).get("reviews") or []
        mine = sorted(by_game.get(d["appid"], []), key=lambda r: -int(r["timestamp_created"]))
        if len(revs) < 50 or len(mine) < len(revs):
            continue
        n = len(revs)
        h = sum(1 for r in revs if r["voted_up"]) / n
        rc = sum(1 for r in mine[:n] if r["voted_up"] == "True") / n
        deltas.append(h - rc)
        bias_rows.append({"name": d["name"], "n_compared": n,
                          "first_page_helpfulness": round(h, 4),
                          "same_n_most_recent": round(rc, 4), "delta": round(h - rc, 4)})
    if deltas:
        print(f"   games={len(deltas)}  mean={statistics.mean(deltas)*100:+.4f}pp  "
              f"median={statistics.median(deltas)*100:+.4f}pp  "
              f"more negative under helpfulness: {sum(1 for x in deltas if x < 0)}/{len(deltas)}")
        pending["sampling_bias.csv"] = bias_rows
    else:
        fails.append("helpfulness comparison produced no comparable games")

    print("8. OFF-TOPIC SENSITIVITY  (Steam excludes review-bomb periods by default)")
    ot = []
    for d in denoms:
        got = {}
        for label, extra in [("default", {}), ("included", {"filter_offtopic_activity": 0})]:
            q = {"json": 1, "filter": "all", "language": "english",
                 "purchase_type": "all", "num_per_page": 1, "cursor": "*"}
            q.update(extra)
            s = (fetch(f"https://store.steampowered.com/appreviews/{d['appid']}?{urllib.parse.urlencode(q)}")
                 or {}).get("query_summary", {})
            got[label] = (s.get("total_reviews"), s.get("total_positive"))
        (dt_, dp), (it, ip) = got["default"], got["included"]
        if not dt_ or not it:
            continue
        delta = it - dt_
        ot.append({"name": d["name"], "default_total": dt_, "included_total": it,
                   "delta_reviews": delta,
                   # The two calls are minutes to an hour apart, so a handful of
                   # reviews is indistinguishable from ordinary accrual.
                   "interpretation": "off-topic withholding" if delta >= AMBIGUITY_FLOOR
                                     else ("within capture-timing noise" if delta > 0 else "no difference"),
                   "default_pos_rate": round(dp / dt_, 4), "included_pos_rate": round(ip / it, 4),
                   "delta_pos_rate_pp": round((ip / it - dp / dt_) * 100, 4)})
    if ot:
        clear = [o for o in ot if o["delta_reviews"] >= AMBIGUITY_FLOOR]
        noise = [o for o in ot if 0 < o["delta_reviews"] < AMBIGUITY_FLOOR]
        print(f"   unambiguous withholding (>={AMBIGUITY_FLOOR} reviews): {len(clear)}/{len(ot)}   "
              f"largest {max((o['delta_reviews'] for o in ot), default=0):+,}")
        print(f"   within capture-timing noise (1-{AMBIGUITY_FLOOR-1}): {len(noise)}/{len(ot)}  "
              f"- NOT counted as affected")
        print(f"   max absolute rate impact: {max(abs(o['delta_pos_rate_pp']) for o in ot):.3f}pp")
        pending["offtopic_sensitivity.csv"] = ot

    print(f"9. CLUSTERING  (effective N for a sub-genre claim is GAMES, not reviews)")
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
    print("   => pooled two-proportion tests over reviews are NOT valid and are not run.")

    if fails:
        print(f"\nGATE FAILED ({len(fails)}): {fails}")
        print("No canonical outputs were written.")
        return 1

    for fname, data in pending.items():
        write_csv(OUT / fname, data)
    print(f"\nGATE PASSED - wrote {len(pending)} outputs: {', '.join(sorted(pending))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
