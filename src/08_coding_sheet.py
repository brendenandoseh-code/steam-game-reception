"""Day 2 step 4 - build the BLINDED held-out coding sheet.

Three properties the first attempt got wrong:

  1. FULL TEXT. The sheet previously truncated at 1,200 characters. Twenty-one
     of the 150 held-out reviews are longer than that, and twelve of them get
     different machine labels on the full text. Human and machine must judge
     identical text or the comparison is meaningless.

  2. BLINDED. The sheet previously exposed game name and sub-genre and was
     sorted by them. When the expected result is already known ("emergent
     games should show more procgen complaints"), showing the coder which
     bucket each review came from primes exactly the finding under test.

  3. FIXED-RANDOM ORDER. Sorted-by-game order groups similar text together,
     which drifts the coder's threshold within a block.

The 150 IDs are unchanged and the codebook stays frozen. Only presentation
changes. Machine predictions are NOT in this file.
"""

import csv
import hashlib
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from steam import ROOT  # noqa: E402

import importlib.util
spec = importlib.util.spec_from_file_location("codebook", Path(__file__).parent / "06_codebook.py")
cb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cb)

DATA, OUT = ROOT / "data", ROOT / "outputs"
ORDER_SEED = 8021  # distinct from the split seed; only affects presentation order

# taste_mismatch and non_substantive are codeable by a human; uncoded is a
# machine artefact (no rule fired) and must not be offered as a human label.
HUMAN_LABELS = [c for c in cb.CATEGORIES if c != "uncoded"]


def main():
    raw = {r["recommendationid"]: r for r in
           csv.DictReader(open(DATA / "reviews_raw.csv", encoding="utf-8"))}
    held = [r["recommendationid"] for r in
            csv.DictReader(open(OUT / "heldout_ids.csv", encoding="utf-8"))]

    rows = []
    for rid in held:
        text = " ".join((raw[rid]["review"] or "").split())   # whitespace only, no truncation
        rows.append({"recommendationid": rid, "review_text": text,
                     **{c: "" for c in HUMAN_LABELS}})

    random.Random(ORDER_SEED).shuffle(rows)
    for i, r in enumerate(rows, 1):
        r["row"] = i
    rows = [{"row": r.pop("row"), **r} for r in rows]

    path = OUT / "heldout_coding_sheet.csv"
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)

    longest = max(len(r["review_text"]) for r in rows)
    over = sum(1 for r in rows if len(r["review_text"]) > 1200)
    leaked = [c for c in ("name", "axis", "appid") if c in rows[0]]
    assert not leaked, f"sheet leaks stratification fields: {leaked}"
    assert len(rows) == 150 and len({r["recommendationid"] for r in rows}) == 150

    manifest = {
        "phase": "day2_codebook",
        "codebook_frozen_at": "commit 5af32b6, drafted from the 100 discovery reviews only",
        "codebook_authorship": "AI-drafted candidate codebook. Categories and regex rules were "
                               "produced by an AI assistant reading the discovery sample. They are "
                               "validated and interpreted by Brenden, not by the assistant.",
        "sheet_seed_presentation_order": ORDER_SEED,
        "blinded": "game name, sub-genre and appid are withheld; machine predictions are not included",
        "text": "full review text, no truncation",
        "human_labels_offered": HUMAN_LABELS,
        "files": {},
    }
    for n in ["heldout_coding_sheet.csv", "coded_negatives.csv", "category_rates.csv"]:
        p = OUT / n
        manifest["files"][n] = {"sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
                                "bytes": p.stat().st_size}
    for n in ["CODEBOOK.md", "src/06_codebook.py", "src/07_apply.py"]:
        p = ROOT / n
        manifest["files"][n] = {"sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
                                "bytes": p.stat().st_size}
    (OUT / "codebook_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print(f"blinded sheet: {len(rows)} rows, order seed {ORDER_SEED}")
    print(f"  full text: longest {longest:,} chars, {over} rows over the old 1,200 cap")
    print(f"  columns: {', '.join(list(rows[0].keys())[:3])} + {len(HUMAN_LABELS)} blank label columns")
    print(f"  withheld: game name, sub-genre, appid, machine predictions")
    print(f"wrote heldout_coding_sheet.csv and codebook_manifest.json")


if __name__ == "__main__":
    main()
