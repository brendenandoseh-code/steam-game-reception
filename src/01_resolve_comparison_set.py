"""Step 1 - resolve and verify the comparison set.

Candidate appids are verified against the store API by name before any
review pulling happens. A wrong appid silently poisons everything
downstream, so this step is separate and its output is committed.

Positioning axes the set is chosen to span:
  colony    - you manage a settlement, story emerges from systems
  grand     - dynasty/empire scale, generational succession
  emergent  - explicit emergent-narrative or procedural-story games
  life      - ordinary domestic life, no empire
"""

import csv
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from steam import ROOT, appdetails  # noqa: E402

CANDIDATES = [
    (294100, "RimWorld", "colony"),
    (975370, "Dwarf Fortress", "colony"),
    (457140, "Oxygen Not Included", "colony"),
    (427520, "Factorio", "colony"),
    (1162750, "Songs of Syx", "colony"),
    (242920, "Banished", "colony"),
    (1029780, "Going Medieval", "colony"),
    (1158310, "Crusader Kings III", "grand"),
    (236850, "Europa Universalis IV", "grand"),
    (529340, "Victoria 3", "grand"),
    (1158310, "_dup_guard", "grand"),
    (333640, "Caves of Qud", "emergent"),
    (233860, "Kenshi", "emergent"),
    (763890, "Wildermyth", "emergent"),
    (986130, "Shadows of Doubt", "emergent"),
    (1222670, "The Sims 4", "life"),
    (413150, "Stardew Valley", "life"),
    (666140, "My Time At Portia", "life"),
    (599140, "Graveyard Keeper", "life"),
    (972660, "Spiritfarer", "life"),
]

OUT = ROOT / "outputs"
OUT.mkdir(exist_ok=True)


def main():
    seen, rows, failed = set(), [], []
    for appid, expected, axis in CANDIDATES:
        if appid in seen:
            continue
        seen.add(appid)
        d = appdetails(appid)
        if not d:
            failed.append((appid, expected, "no data returned"))
            print(f"  FAIL  {appid:>8}  {expected}")
            continue
        if d.get("type") != "game":
            failed.append((appid, expected, f"type={d.get('type')}"))
            print(f"  SKIP  {appid:>8}  {d.get('name')} (type={d.get('type')})")
            continue

        price = d.get("price_overview") or {}
        rows.append(
            {
                "appid": appid,
                "name": d.get("name"),
                "expected_name": expected,
                "axis": axis,
                "name_matches": expected.lower() in re.sub(r"[™®℠]", "", (d.get("name") or "")).lower(),
                "genres": "|".join(g["description"] for g in d.get("genres", [])),
                "release_date": (d.get("release_date") or {}).get("date"),
                "is_free": d.get("is_free"),
                "price_cents": price.get("final"),
                "price_usd": (price.get("final") or 0) / 100 if price.get("final") else None,
                "metacritic": (d.get("metacritic") or {}).get("score"),
            }
        )
        flag = "" if rows[-1]["name_matches"] or expected.startswith("_") else "  <-- NAME MISMATCH"
        print(f"  ok    {appid:>8}  {d.get('name')}{flag}")

    rows = [r for r in rows if not r["expected_name"].startswith("_")]
    path = OUT / "comparison_set.csv"
    with path.open("w", newline="", encoding="utf-8") as f:
        wr = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        wr.writeheader()
        wr.writerows(rows)

    print(f"\nresolved {len(rows)} games -> {path.relative_to(ROOT)}")
    mismatches = [r for r in rows if not r["name_matches"]]
    print(f"name mismatches: {len(mismatches)} {[r['name'] for r in mismatches]}")
    print(f"failed lookups : {len(failed)} {failed}")
    by_axis = {}
    for r in rows:
        by_axis[r["axis"]] = by_axis.get(r["axis"], 0) + 1
    print("by positioning axis:", json.dumps(by_axis))
    free = [r["name"] for r in rows if r["is_free"]]
    nopr = [r["name"] for r in rows if not r["is_free"] and r["price_cents"] is None]
    print(f"free-to-play: {free}")
    print(f"paid but no price returned (regional/bundle): {nopr}")


if __name__ == "__main__":
    main()
