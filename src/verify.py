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
MANIFESTS = ["freeze_manifest.json", "split_manifest.json", "codebook_manifest.json",
             "analyst_manifest.json"]


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def resolve(name: str) -> Path:
    """Manifests reference three kinds of path: the raw file in data/, plain
    output names in outputs/, and project-relative paths like CODEBOOK.md or
    src/06_codebook.py. Resolve all three."""
    if name == "reviews_raw.csv":
        return DATA / name
    if "/" in name or (ROOT / name).exists() and not (OUT / name).exists():
        return ROOT / name
    return OUT / name


def main():
    problems = []
    for mname in MANIFESTS:
        mp = OUT / mname
        if not mp.exists():
            # Fail closed. A missing manifest previously printed "skipped" and
            # the run could still report VERIFY OK, which is the same
            # fail-open shape as a manifest nothing asks.
            problems.append(f"{mname}: MISSING MANIFEST")
            print(f"{mname}: MISSING - a required manifest is absent")
            continue
        m = json.loads(mp.read_text(encoding="utf-8"))
        print(f"{mname}  ({m.get('phase', 'day1_freeze')})")
        for name, meta in m["files"].items():
            p = resolve(name)
            if not p.exists():
                problems.append(f"{mname}: MISSING {name}")
                print(f"   MISSING  {name}")
                continue
            ok = sha(p) == meta["sha256"]
            if not ok:
                problems.append(f"{mname}: CHANGED {name}")
            print(f"   {'match  ' if ok else 'CHANGED'}  {name}")

        # lineage: each phase pins the artifacts it was derived from
        for label, key, target in [
            ("raw data this split was drawn from", "depends_on_day1_manifest", DATA / "reviews_raw.csv"),
            ("raw data this codebook was applied to", "depends_on_raw_sha", DATA / "reviews_raw.csv"),
            ("held-out IDs this sheet was built from", "depends_on_heldout_ids_sha", OUT / "heldout_ids.csv"),
        ]:
            dep = m.get(key)
            if not dep:
                continue
            ok = dep == sha(target)
            if not ok:
                problems.append(f"{mname}: lineage broken - {label}")
            print(f"   {'match  ' if ok else 'CHANGED'}  <- {label}")

    print()
    if problems:
        print(f"VERIFY FAILED ({len(problems)}): {problems}")
        return 1
    print("VERIFY OK - all phase manifests match")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
