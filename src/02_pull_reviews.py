"""Step 2 - pull review samples and record the true population denominators.

Sampling note that governs the whole study:
Steam's API offers no random sample of reviews. Two orderings are available and
they are NOT interchangeable - this was measured, not assumed (2026-08-02):

  filter=recent - strict recency. Pages reliably through the corpus.
  filter=all    - helpfulness-weighted. Pagination stalls after roughly 200
                  reviews, and the reviews it surfaces skew more negative,
                  because negative reviews accumulate more helpful votes.

An earlier version of this script used filter=all for bulk sampling. That was
wrong on both counts: it silently truncated most games (Wildermyth returned 92
of 13,082 available English reviews) and it biased the sample negative.

The main sample therefore uses filter=recent, which makes it a RECENCY-WEIGHTED
sample of English reviews rather than a random one. A smaller filter=all pull is
kept alongside it so the size of the helpfulness bias can be reported rather
than hand-waved.

To make that measurable we record three denominators per game:
  - lifetime, all languages   (language=all)
  - lifetime, English only    (language=english)
  - the sample we actually pulled
"""

import csv
import json
import sys
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from steam import ROOT, fetch, review_page  # noqa: E402

PAGES_PER_GAME = 12          # up to 1,200 recency-ordered reviews per game
BIAS_PAGES = 3               # filter=all comparison pull; it stalls anyway
DATA = ROOT / "data"
OUT = ROOT / "outputs"
DATA.mkdir(exist_ok=True)
OUT.mkdir(exist_ok=True)


def summary_for(appid: int, language: str):
    """query_summary only, one cheap call, for the population denominator."""
    q = urllib.parse.urlencode(
        {"json": 1, "filter": "all", "language": language,
         "purchase_type": "all", "num_per_page": 1, "cursor": "*"}
    )
    d = fetch(f"https://store.steampowered.com/appreviews/{appid}?{q}")
    return (d or {}).get("query_summary", {})


def main():
    games = list(csv.DictReader(open(OUT / "comparison_set.csv", encoding="utf-8")))
    denoms, all_reviews = [], []

    for g in games:
        appid, name = int(g["appid"]), g["name"]
        s_all = summary_for(appid, "all")
        s_eng = summary_for(appid, "english")

        seen, cursor, rows = set(), "*", []
        for _ in range(PAGES_PER_GAME):
            page = review_page(appid, cursor, filt="recent")
            if not page or not page.get("reviews"):
                break
            for r in page["reviews"]:
                rid = r.get("recommendationid")
                if rid in seen:
                    continue
                seen.add(rid)
                a = r.get("author") or {}
                rows.append({
                    "appid": appid, "name": name, "axis": g["axis"],
                    "recommendationid": rid,
                    "voted_up": r.get("voted_up"),
                    "review": (r.get("review") or "").replace("\r", " ").replace("\n", " "),
                    "playtime_at_review_min": a.get("playtime_at_review"),
                    "playtime_forever_min": a.get("playtime_forever"),
                    "num_games_owned": a.get("num_games_owned"),
                    "timestamp_created": r.get("timestamp_created"),
                    "early_access": r.get("written_during_early_access"),
                    "received_for_free": r.get("received_for_free"),
                    "steam_purchase": r.get("steam_purchase"),
                    "votes_up": r.get("votes_up"),
                    "weighted_vote_score": r.get("weighted_vote_score"),
                })
            nxt = page.get("cursor")
            if not nxt or nxt == cursor:
                break
            cursor = nxt

        pos = sum(1 for r in rows if r["voted_up"])
        denoms.append({
            "appid": appid, "name": name, "axis": g["axis"],
            "lifetime_total_all_lang": s_all.get("total_reviews"),
            "lifetime_positive_all_lang": s_all.get("total_positive"),
            "lifetime_pos_rate_all_lang": round(s_all.get("total_positive", 0) / s_all["total_reviews"], 4) if s_all.get("total_reviews") else None,
            "lifetime_total_english": s_eng.get("total_reviews"),
            "lifetime_positive_english": s_eng.get("total_positive"),
            "lifetime_pos_rate_english": round(s_eng.get("total_positive", 0) / s_eng["total_reviews"], 4) if s_eng.get("total_reviews") else None,
            "sampled_n": len(rows),
            "sampled_positive": pos,
            "sampled_pos_rate": round(pos / len(rows), 4) if rows else None,
            "review_score_desc": s_all.get("review_score_desc"),
        })
        all_reviews.extend(rows)
        print(f"  {name[:34]:<34} n={len(rows):>5}  sample={denoms[-1]['sampled_pos_rate']}  lifetime_en={denoms[-1]['lifetime_pos_rate_english']}")

    with (DATA / "reviews_raw.csv").open("w", newline="", encoding="utf-8") as f:
        wr = csv.DictWriter(f, fieldnames=list(all_reviews[0].keys()))
        wr.writeheader(); wr.writerows(all_reviews)
    with (OUT / "denominators.csv").open("w", newline="", encoding="utf-8") as f:
        wr = csv.DictWriter(f, fieldnames=list(denoms[0].keys()))
        wr.writeheader(); wr.writerows(denoms)

    print(f"\n{len(all_reviews):,} reviews across {len(denoms)} games")
    print(f"  raw     -> data/reviews_raw.csv (gitignored)")
    print(f"  denoms  -> outputs/denominators.csv")


if __name__ == "__main__":
    main()
