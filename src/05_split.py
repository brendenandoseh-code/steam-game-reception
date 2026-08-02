"""Day 2 step 1 - materialise the codebook samples BEFORE any review text is read.

The whole point of this file is what it does NOT do: it never loads the `review`
column. If the discovery and held-out sets were drawn after looking at text, the
codebook could be tuned to the held-out set and its precision/recall would be
meaningless. So the split is fixed first, committed, and hashed.

Discipline enforced structurally, not by good intentions:
  - only ID and stratification columns are read out of reviews_raw.csv
  - the frozen exclusion list from Day 1 is applied BY ID, never by re-reading text
  - the seed is a constant in this file, not a runtime value
  - IDs are sorted before sampling, so row order in the CSV cannot change the draw

Frame: negative reviews only. The study was narrowed on 2026-08-02 to objections
and positioning risk, so positives are out of scope for coding.
"""

import csv
import hashlib
import json
import random
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from steam import ROOT  # noqa: E402

DATA, OUT = ROOT / "data", ROOT / "outputs"

SEED = 20260802
N_DISCOVERY = 100
N_HELDOUT = 150
MIN_PER_GAME_DISCOVERY = 1
MIN_PER_GAME_HELDOUT = 2
TEXT_COLUMN = "review"          # deliberately never read


def allocate(counts, total, floor):
    """Largest-remainder proportional allocation with a per-game floor."""
    games = sorted(counts)
    alloc = {g: min(floor, counts[g]) for g in games}
    remaining = total - sum(alloc.values())
    pool = {g: counts[g] - alloc[g] for g in games}
    denom = sum(pool.values())
    if remaining > 0 and denom > 0:
        exact = {g: remaining * pool[g] / denom for g in games}
        base = {g: int(exact[g]) for g in games}
        for g in games:
            base[g] = min(base[g], pool[g])
        left = remaining - sum(base.values())
        for g in sorted(games, key=lambda g: (-(exact[g] - int(exact[g])), g)):
            if left <= 0:
                break
            if base[g] < pool[g]:
                base[g] += 1
                left -= 1
        for g in games:
            alloc[g] += base[g]
    return alloc


def main():
    excluded = {r["recommendationid"] for r in
                csv.DictReader(open(OUT / "excluded_reviews.csv", encoding="utf-8"))}

    # Read ONLY the columns needed to stratify. Text is never materialised.
    pool = defaultdict(list)
    with open(DATA / "reviews_raw.csv", encoding="utf-8") as f:
        rdr = csv.DictReader(f)
        assert TEXT_COLUMN in rdr.fieldnames, "expected a review column to exist and be skipped"
        for r in rdr:
            if r["voted_up"] != "False":
                continue
            if r["recommendationid"] in excluded:
                continue
            pool[(r["appid"], r["name"], r["axis"])].append(r["recommendationid"])

    counts = {k: len(v) for k, v in pool.items()}
    total_neg = sum(counts.values())
    print(f"eligible negative reviews (post-exclusion): {total_neg:,} across {len(counts)} games")

    d_alloc = allocate(counts, N_DISCOVERY, MIN_PER_GAME_DISCOVERY)
    h_alloc = allocate(counts, N_HELDOUT, MIN_PER_GAME_HELDOUT)

    rng = random.Random(SEED)
    discovery, heldout, strata = [], [], []
    for key in sorted(pool):
        appid, name, axis = key
        ids = sorted(pool[key])                      # deterministic regardless of file order
        rng.shuffle(ids)
        d_n, h_n = d_alloc[key], h_alloc[key]
        assert d_n + h_n <= len(ids), f"{name}: allocation exceeds pool"
        d_ids, h_ids = ids[:d_n], ids[d_n:d_n + h_n]   # disjoint by construction
        discovery += [{"recommendationid": i, "appid": appid, "name": name, "axis": axis} for i in d_ids]
        heldout += [{"recommendationid": i, "appid": appid, "name": name, "axis": axis} for i in h_ids]
        strata.append({"appid": appid, "name": name, "axis": axis,
                       "eligible_negatives": len(ids), "discovery_n": d_n, "heldout_n": h_n})

    assert len(discovery) == N_DISCOVERY, len(discovery)
    assert len(heldout) == N_HELDOUT, len(heldout)
    assert not ({r["recommendationid"] for r in discovery} & {r["recommendationid"] for r in heldout})

    for fname, rows in [("discovery_ids.csv", discovery), ("heldout_ids.csv", heldout),
                        ("split_strata.csv", strata)]:
        with (OUT / fname).open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader(); w.writerows(rows)

    files = {}
    for n in ["discovery_ids.csv", "heldout_ids.csv", "split_strata.csv"]:
        p = OUT / n
        files[n] = {"sha256": hashlib.sha256(p.read_bytes()).hexdigest(), "bytes": p.stat().st_size}

    manifest = {
        "phase": "day2_split",
        "created_before_reading_any_review_text": True,
        "seed": SEED,
        "frame": "negative reviews only (voted_up == False), Day 1 exclusion list applied by id",
        "eligible_negatives": total_neg,
        "n_discovery": N_DISCOVERY,
        "n_heldout": N_HELDOUT,
        "allocation": f"largest-remainder proportional to eligible negatives per game, "
                      f"floor {MIN_PER_GAME_DISCOVERY} discovery / {MIN_PER_GAME_HELDOUT} held-out",
        "disjoint": True,
        "depends_on_day1_manifest": json.loads((OUT / "freeze_manifest.json").read_text(encoding="utf-8"))["files"]["reviews_raw.csv"]["sha256"],
        "files": files,
    }
    (OUT / "split_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    by_axis = defaultdict(lambda: [0, 0])
    for s in strata:
        by_axis[s["axis"]][0] += s["discovery_n"]
        by_axis[s["axis"]][1] += s["heldout_n"]
    print(f"seed={SEED}   discovery={len(discovery)}   held-out={len(heldout)}   disjoint=True")
    for a in sorted(by_axis):
        print(f"   {a:<10} discovery={by_axis[a][0]:>3}  held-out={by_axis[a][1]:>3}")
    print(f"per-game floor honoured: every one of {len(strata)} games appears in both samples")
    print("wrote discovery_ids.csv, heldout_ids.csv, split_strata.csv, split_manifest.json")
    print("NO REVIEW TEXT WAS READ.")


if __name__ == "__main__":
    main()
