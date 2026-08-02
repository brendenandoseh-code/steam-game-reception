"""Verify every phase manifest. Run: py src/verify.py

Each phase owns its own manifest and covers exactly its own outputs, so a later
phase's artifacts cannot invalidate an earlier freeze. This checks all of them
and exits non-zero if any file has drifted.
"""

import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from steam import ROOT  # noqa: E402

DATA, OUT = ROOT / "data", ROOT / "outputs"
MANIFESTS = ["freeze_manifest.json", "split_manifest.json"]


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    problems = []
    for mname in MANIFESTS:
        mp = OUT / mname
        if not mp.exists():
            print(f"{mname}: not present, skipped")
            continue
        m = json.loads(mp.read_text(encoding="utf-8"))
        print(f"{mname}  ({m.get('phase', 'day1_freeze')})")
        for name, meta in m["files"].items():
            p = (DATA if name == "reviews_raw.csv" else OUT) / name
            if not p.exists():
                problems.append(f"{mname}: MISSING {name}")
                print(f"   MISSING  {name}")
                continue
            ok = sha(p) == meta["sha256"]
            if not ok:
                problems.append(f"{mname}: CHANGED {name}")
            print(f"   {'match  ' if ok else 'CHANGED'}  {name}")

        # the split must still describe the same raw data it was drawn from
        dep = m.get("depends_on_day1_manifest")
        if dep:
            actual = sha(DATA / "reviews_raw.csv")
            ok = dep == actual
            if not ok:
                problems.append(f"{mname}: drawn from a different reviews_raw.csv")
            print(f"   {'match  ' if ok else 'CHANGED'}  <- raw data this split was drawn from")

    print()
    if problems:
        print(f"VERIFY FAILED ({len(problems)}): {problems}")
        return 1
    print("VERIFY OK - all phase manifests match")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
