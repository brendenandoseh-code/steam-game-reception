"""Gate tests. Run: py src/test_gate.py

Asserts three properties that were each violated at some point:

  1. The gate FAILS on defective input (rev1 reported PASS on unusable data).
  2. It fails CLEANLY, with a message rather than a traceback.
  3. It is NON-DESTRUCTIVE on failure (rev2 overwrote canonical outputs while
     checks were still running, and the corruption was committed).

Plus: a Day 2 artifact must not invalidate the Day 1 freeze.

Every mutation is applied to a copy; the original raw file is restored in a
finally block whether or not the suite passes.
"""

import csv
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "reviews_raw.csv"
BAK = ROOT / "data" / "_test_backup.csv"
GATE = [sys.executable, str(ROOT / "src" / "03_validate.py")]
FREEZE = [sys.executable, str(ROOT / "src" / "04_freeze.py")]

MUTATIONS = {
    "duplicate recommendationid": lambda rs: rs + [dict(rs[0])],
    "one blank timestamp":        lambda rs: [{**r, "timestamp_created": ""} if i == 7 else r
                                              for i, r in enumerate(rs)],
    "20% blank timestamps":       lambda rs: [{**r, "timestamp_created": ""} if i % 5 == 0 else r
                                              for i, r in enumerate(rs)],
    "non-numeric playtime":       lambda rs: [{**r, "playtime_at_review_min": "n/a"} if i == 3 else r
                                              for i, r in enumerate(rs)],
    "sub-genre below 3 games":    lambda rs: [r for r in rs
                                              if not (r["axis"] == "grand" and r["name"] != "Victoria 3")],
    "required column dropped":    lambda rs: [{k: v for k, v in r.items() if k != "playtime_forever_min"}
                                              for r in rs],
    "empty dataset":              lambda rs: [],
}


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)


def main():
    shutil.copy(RAW, BAK)
    rows = list(csv.DictReader(open(RAW, encoding="utf-8")))
    failures = []
    try:
        base = run(GATE + [])
        assert base.returncode == 0, "baseline gate must pass before mutating"
        pre = run(FREEZE + ["verify"])
        assert pre.returncode == 0, "manifest must verify before mutating"
        print(f"baseline: gate PASS, manifest VERIFY OK\n")

        for label, mutate in MUTATIONS.items():
            bad = mutate([dict(r) for r in rows])
            with RAW.open("w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=list((bad or rows)[0].keys()))
                w.writeheader(); w.writerows(bad)
            p = run(GATE)
            failed = p.returncode != 0
            clean = "Traceback" not in p.stderr
            shutil.copy(BAK, RAW)                       # restore before verifying outputs
            intact = run(FREEZE + ["verify"]).returncode == 0
            ok = failed and clean and intact
            if not ok:
                failures.append((label, failed, clean, intact))
            print(f"  {'PASS' if ok else 'FAIL'}  {label:<28} "
                  f"fails={failed} clean={clean} outputs_intact={intact}")

        # A Day 2 artifact must not invalidate the Day 1 manifest.
        day2 = ROOT / "outputs" / "_test_day2_artifact.csv"
        day2.write_text("id\n1\n", encoding="utf-8")
        try:
            ok = run(FREEZE + ["verify"]).returncode == 0
            if not ok:
                failures.append(("day-2 artifact invalidates day-1 freeze", None, None, False))
            print(f"  {'PASS' if ok else 'FAIL'}  {'day-2 artifact is out of scope':<28} "
                  f"day1_manifest_still_verifies={ok}")
        finally:
            day2.unlink()
    finally:
        shutil.move(BAK, RAW)

    print()
    if failures:
        print(f"{len(failures)} TEST FAILURE(S): {[f[0] for f in failures]}")
        return 1
    print(f"all {len(MUTATIONS) + 1} gate tests passed; raw file restored")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
