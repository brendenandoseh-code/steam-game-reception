"""Step 4 - Day 1 freeze manifest. Two explicit modes, never both.

    py src/04_freeze.py create    write the manifest from current files
    py src/04_freeze.py verify    check current files against it, exit non-zero on drift

The previous version only ever wrote. That made the manifest a record nobody
checked, which is how three corrupted outputs were committed with a clean git
status: the manifest had detected the drift the whole time and was never asked.

All dates are UTC. date.fromtimestamp() uses the machine timezone and makes the
manifest hash depend on where it was generated.
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
MANIFEST = OUT / "freeze_manifest.json"


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# EXPLICIT, not a glob. A glob over outputs/ meant the first Day 2 artifact
# (discovery_ids.csv) would register as UNTRACKED and invalidate the Day 1
# freeze. A phase manifest must cover exactly the phase's own outputs.
DAY1_FILES = [
    "reviews_raw.csv",          # in data/
    "comparison_set.csv",
    "denominators.csv",
    "excluded_reviews.csv",
    "offtopic_sensitivity.csv",
    "rejected_appids.csv",
    "sampling_bias.csv",
    "temporal_coverage.csv",
]


def tracked():
    """Exactly the Day 1 outputs. Later phases get their own manifests."""
    return [(DATA if n == "reviews_raw.csv" else OUT) / n for n in DAY1_FILES]


def create():
    rows = list(csv.DictReader(open(DATA / "reviews_raw.csv", encoding="utf-8")))
    ts = [int(r["timestamp_created"]) for r in rows]
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
            "offtopic_activity": "Steam default retained (review-bomb periods withheld). "
                                 "Per-game sensitivity is computed, not asserted: see "
                                 "outputs/offtopic_sensitivity.csv.",
        },
        "known_limitations": [
            "Equal-N latest-review sample per game, NOT a shared calendar window. See "
            "outputs/temporal_coverage.csv for per-game spans.",
            "Reviews are clustered within games; a sub-genre holds 3-7 games, so the effective N "
            "for any sub-genre claim is the game count. Pooled review-level inference is invalid.",
            "English-language reviews only.",
            "Comparison set is purposively selected, not a random sample of the category.",
            "Steam offers no random-sample ordering; every available ordering is biased in a "
            "known way. See outputs/sampling_bias.csv.",
        ],
        "files": {p.name: {"sha256": sha(p), "bytes": p.stat().st_size} for p in tracked()},
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"created {MANIFEST.relative_to(ROOT)}")
    print(f"  {manifest['n_reviews']:,} reviews / {manifest['n_games']} games / "
          f"{manifest['review_timestamp_range_utc'][0]} to {manifest['review_timestamp_range_utc'][1]}")
    for n, m in manifest["files"].items():
        print(f"  {m['sha256'][:16]}  {m['bytes']:>10,}  {n}")
    return 0


def verify():
    if not MANIFEST.exists():
        print("no manifest to verify against")
        return 1
    m = json.loads(MANIFEST.read_text(encoding="utf-8"))
    on_disk = {p.name: p for p in tracked()}
    problems = []

    for name, meta in m["files"].items():
        p = on_disk.pop(name, None)
        if p is None:
            problems.append(f"MISSING {name}")
            print(f"  MISSING  {name}")
            continue
        h = sha(p)
        ok = h == meta["sha256"]
        if not ok:
            problems.append(f"CHANGED {name}")
        print(f"  {'match  ' if ok else 'CHANGED'}  {name}")
    for extra in on_disk:  # cannot occur with an explicit list, kept as a guard
        problems.append(f"UNTRACKED {extra}")
        print(f"  UNTRACKED {extra}")

    if problems:
        print(f"\nVERIFY FAILED ({len(problems)}): {problems}")
        return 1
    print(f"\nVERIFY OK - {len(m['files'])} files match the manifest")
    return 0


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode == "create":
        raise SystemExit(create())
    if mode == "verify":
        raise SystemExit(verify())
    print(__doc__)
    raise SystemExit(2)
