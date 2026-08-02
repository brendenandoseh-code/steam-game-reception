"""Step 4 - write the freeze manifest.

"Frozen" is meaningless without a hash record. This writes a committed manifest
so any later run can prove it is working on the same bytes: file hashes, row
counts, retrieval window, API parameters, and per-game date coverage.

Re-running this after a cache-only rerun must reproduce identical hashes.
"""

import csv
import datetime as dt
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from steam import ROOT  # noqa: E402

DATA, OUT = ROOT / "data", ROOT / "outputs"


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    raw = DATA / "reviews_raw.csv"
    rows = list(csv.DictReader(open(raw, encoding="utf-8")))
    ts = [int(r["timestamp_created"]) for r in rows]

    files = {}
    for p in [raw] + sorted(OUT.glob("*.csv")):
        files[p.name] = {"sha256": sha(p), "bytes": p.stat().st_size}

    manifest = {
        "frozen_at_utc": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "n_reviews": len(rows),
        "n_games": len({r["appid"] for r in rows}),
        "review_timestamp_range_utc": [
            dt.datetime.fromtimestamp(min(ts), dt.timezone.utc).date().isoformat(),
            dt.datetime.fromtimestamp(max(ts), dt.timezone.utc).date().isoformat(),
        ],
        "api": {
            "reviews_endpoint": "https://store.steampowered.com/appreviews/{appid}",
            "reviews_params": {"json": 1, "filter": "recent", "language": "english",
                               "purchase_type": "all", "num_per_page": 100},
            "pages_per_game": 12,
            "metadata_endpoint": "https://store.steampowered.com/api/appdetails",
            "metadata_params": {"cc": "us", "l": "english"},
            "offtopic_activity": "Steam default retained (review-bomb periods excluded). "
                                 "Measured impact: Victoria 3 +396 reviews (+1.4%), "
                                 "positive rate -0.18pp; The Sims 4 unchanged.",
        },
        "known_limitations": [
            "Equal-N latest-review sample per game, NOT a shared calendar window: "
            "coverage runs 13 days (Stardew Valley) to 963 days (My Time at Portia), median 192.",
            "Reviews are clustered within games; a segment holds 3-7 games, so the effective N "
            "for any segment-level claim is the game count. Pooled review-level inference is invalid.",
            "English-language reviews only.",
            "Comparison set is purposively selected, not a random sample of the category.",
            "Steam offers no random-sample ordering; every available ordering is biased in a known way.",
        ],
        "files": files,
    }

    path = OUT / "freeze_manifest.json"
    path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"wrote {path.relative_to(ROOT)}")
    print(f"  reviews : {manifest['n_reviews']:,} across {manifest['n_games']} games")
    print(f"  window  : {manifest['review_timestamp_range_utc'][0]} to {manifest['review_timestamp_range_utc'][1]}")
    for n, m in files.items():
        print(f"  {m['sha256'][:16]}  {m['bytes']:>10,}  {n}")


if __name__ == "__main__":
    main()
