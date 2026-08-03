"""Day 3 - ingest the analyst's hand-coded labels for the held-out 150.

These are the analyst's own labels, coded against CODEBOOK.md on the blinded
sheet from 08_coding_sheet.py. They are the human side of the validation.

Empty rows are allowed. A review whose objection has no category in v1 is a
finding about codebook coverage, not a gap in the coding, and the count is
reported rather than forced into non_substantive.

Run: py src/14_analyst_labels.py [path/to/coded_sheet.csv]
"""

import csv
import hashlib
import importlib.util
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from steam import ROOT  # noqa: E402

spec = importlib.util.spec_from_file_location("codebook", Path(__file__).parent / "06_codebook.py")
cb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cb)

DATA, OUT = ROOT / "data", ROOT / "outputs"
DEFAULT_IN = DATA / "analyst_coded_heldout.csv"
CATEGORIES = sorted(c for c in cb.CATEGORIES if c != "uncoded")


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip().lower()


def fail(problems: list[str]) -> None:
    print(f"\nINGEST REFUSED ({len(problems)} problem(s)):")
    for p in problems:
        print(f"  - {p}")
    raise SystemExit(1)


def main() -> int:
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_IN
    if not src.exists():
        fail([f"input not found: {src}"])

    sheet = list(csv.DictReader(open(src, encoding="utf-8-sig")))
    held = {r["row"]: r for r in
            csv.DictReader(open(OUT / "heldout_coding_sheet.csv", encoding="utf-8"))}

    missing = [c for c in ["row", "recommendationid"] + CATEGORIES if c not in (sheet[0] if sheet else {})]
    if missing:
        fail([f"input is missing required columns: {missing}"])

    seen = [r["row"].strip() for r in sheet]
    if sorted(seen, key=lambda x: int(x) if x.isdigit() else -1) != [str(i) for i in range(1, 151)]:
        absent = [str(i) for i in range(1, 151) if str(i) not in set(seen)]
        dupes = sorted({r for r in seen if seen.count(r) > 1})
        fail([f"expected rows 1-150 exactly once; missing {absent or 'none'}, duplicated {dupes or 'none'}"])

    problems: list[str] = []
    rows, empty = [], []
    for r in sheet:
        n = r["row"].strip()
        h = held[n]

        if r["recommendationid"].strip() != h["recommendationid"]:
            problems.append(f"row {n}: recommendationid {r['recommendationid']} does not match the "
                            f"blinded sheet ({h['recommendationid']}); rows have drifted")
        if "review_text" in r and norm(r["review_text"]) != norm(h["review_text"]):
            problems.append(f"row {n}: review_text differs from the sheet that was coded")

        vals = {}
        for c in CATEGORIES:
            v = (r[c] or "").strip()
            if v not in ("0", "1"):
                problems.append(f"row {n}: {c} is {v!r}, expected 0 or 1")
                v = "0"
            vals[c] = int(v)

        labels = {c for c in CATEGORIES if vals[c]}
        if "non_substantive" in labels and len(labels) > 1:
            problems.append(f"row {n}: rule 4 - non_substantive must be exclusive, got {sorted(labels)}")
        if not labels:
            empty.append(n)

        rows.append({"row": int(n), "recommendationid": h["recommendationid"],
                     "n_labels": len(labels), **vals})

    if problems:
        fail(problems)

    rows.sort(key=lambda r: r["row"])
    path = OUT / "analyst_labels.csv"
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    manifest = {
        "phase": "day3_analyst_labels",
        "labeller": "the analyst, hand-coded against CODEBOOK.md on the blinded sheet",
        "attestation": "Brenden states these are his own labels. A Codex-generated copy of the same "
                       "sheet was submitted first as a deliberate test of whether AI review would "
                       "detect the substitution; it did.",
        "empty_rows": empty,
        "empty_rows_meaning": "objection has no category in codebook v1; a coverage finding, not a coding gap",
        "depends_on_sheet_sha": hashlib.sha256((OUT / "heldout_coding_sheet.csv").read_bytes()).hexdigest(),
        "depends_on_input_sha": hashlib.sha256(src.read_bytes()).hexdigest(),
        "files": {"analyst_labels.csv": {
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "bytes": path.stat().st_size}},
    }
    (OUT / "analyst_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    tot = sum(r["n_labels"] for r in rows)
    print(f"ingested {len(rows)} analyst-coded rows from {src.name}")
    print(f"  {tot} label assignments, {tot / len(rows):.2f} per review")
    print(f"  {len(empty)} rows carry no category (no v1 category fits): {empty}")
    print(f"\n  {'category':<24}{'support':>8}")
    for c in CATEGORIES:
        print(f"  {c:<24}{sum(r[c] for r in rows):>8}")
    print(f"\nwrote analyst_labels.csv and analyst_manifest.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
