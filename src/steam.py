"""Shared Steam API helpers: disk cache, polite rate limiting, backoff.

Every response is cached to data/cache/ so a re-run never re-hits the API.
Steam rate-limits appdetails at roughly 200 requests per 5 minutes; the
reviews endpoint is more forgiving but is throttled here anyway.
"""

import hashlib
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "data" / "cache"
CACHE.mkdir(parents=True, exist_ok=True)

UA = "Mozilla/5.0 (personal research project; github.com/brendenandoseh-code)"
MIN_INTERVAL = 1.6  # seconds between live calls
_last_call = [0.0]


def _cache_path(url: str) -> Path:
    return CACHE / (hashlib.sha256(url.encode()).hexdigest()[:24] + ".json")


def fetch(url: str, retries: int = 4):
    """GET url as JSON, cached. Returns None on unrecoverable failure."""
    cp = _cache_path(url)
    if cp.exists():
        return json.loads(cp.read_text(encoding="utf-8"))

    for attempt in range(retries):
        wait = MIN_INTERVAL - (time.time() - _last_call[0])
        if wait > 0:
            time.sleep(wait)
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=40) as r:
                payload = json.loads(r.read().decode("utf-8"))
            _last_call[0] = time.time()
            cp.write_text(json.dumps(payload), encoding="utf-8")
            return payload
        except urllib.error.HTTPError as e:
            _last_call[0] = time.time()
            if e.code == 429:
                back = 20 * (attempt + 1)
                print(f"    429 rate limited, backing off {back}s")
                time.sleep(back)
                continue
            print(f"    HTTP {e.code} on {url[:80]}")
            return None
        except Exception as e:  # noqa: BLE001 - network flake, retry
            _last_call[0] = time.time()
            print(f"    {type(e).__name__} (attempt {attempt + 1}/{retries})")
            time.sleep(4 * (attempt + 1))
    return None


def appdetails(appid: int):
    url = f"https://store.steampowered.com/api/appdetails?appids={appid}&cc=us&l=english"
    d = fetch(url)
    if not d:
        return None
    node = d.get(str(appid), {})
    return node.get("data") if node.get("success") else None


def review_page(appid: int, cursor: str = "*", num: int = 100, filt: str = "recent"):
    """One page of reviews.

    filt="recent"  - strict recency order, pages reliably through the corpus.
    filt="all"     - Steam's helpfulness-weighted view. Pagination exhausts
                     early (measured: ~200 reviews before the cursor stalls),
                     so it is usable for a bias comparison but NOT for bulk
                     sampling. Verified 2026-08-02.
    """
    q = urllib.parse.urlencode(
        {
            "json": 1,
            "filter": filt,
            "language": "english",
            "purchase_type": "all",
            "num_per_page": num,
            "cursor": cursor,
        }
    )
    return fetch(f"https://store.steampowered.com/appreviews/{appid}?{q}")
