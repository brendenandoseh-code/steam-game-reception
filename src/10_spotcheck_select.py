"""Day 3 - select the 30-row inter-coder spot-check, before either coder starts.

Design: the analyst codes all 150 and is the reference standard. A second coder
(the AI assistant) independently codes a 30-row subset, blind to the analyst's
labels, and the disagreement rate between them is reported alongside the
precision/recall figures.

The second coder's labels are written and committed BEFORE the analyst submits
theirs. That ordering is the point: it removes any possibility that the
second-coder labels were tuned to agree.

Selection is deterministic (fixed seed, sorted first) and spans the sheet's
presentation order so the subset is not clustered in one stretch of reading.
"""

import csv
import hashlib
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from steam import ROOT  # noqa: E402

OUT = ROOT / "outputs"
SPOTCHECK_SEED = 3007
N_SPOTCHECK = 30


def main():
    sheet = list(csv.DictReader(open(OUT / "heldout_coding_sheet.csv", encoding="utf-8")))
    assert len(sheet) == 150

    # Systematic sample across presentation order, then jittered by seed, so the
    # subset is spread through the reading rather than bunched.
    rng = random.Random(SPOTCHECK_SEED)
    stride = len(sheet) / N_SPOTCHECK
    picks = sorted({min(len(sheet) - 1, int(i * stride + rng.random() * stride))
                    for i in range(N_SPOTCHECK)})
    while len(picks) < N_SPOTCHECK:                      # fill any collision
        cand = rng.randrange(len(sheet))
        if cand not in picks:
            picks = sorted(picks + [cand])

    rows = [{"row": sheet[i]["row"], "recommendationid": sheet[i]["recommendationid"]}
            for i in picks]
    path = OUT / "spotcheck_rows.csv"
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["row", "recommendationid"])
        w.writeheader(); w.writerows(rows)

    manifest = {
        "phase": "day3_spotcheck_selection",
        "purpose": "inter-coder reliability subset; second coder labels these blind to the analyst",
        "seed": SPOTCHECK_SEED,
        "n": len(rows),
        "selected_before_either_coder_started": True,
        "reference_standard": "the analyst, who codes all 150",
        "second_coder": "AI assistant, this subset only, labels committed before the analyst submits",
        "depends_on_sheet_sha": hashlib.sha256((OUT / "heldout_coding_sheet.csv").read_bytes()).hexdigest(),
        "files": {"spotcheck_rows.csv": {
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "bytes": path.stat().st_size}},
    }
    (OUT / "spotcheck_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"selected {len(rows)} of 150 for the spot-check, seed {SPOTCHECK_SEED}")
    print(f"  rows: {', '.join(r['row'] for r in rows)}")
    print("wrote spotcheck_rows.csv and spotcheck_manifest.json")


if __name__ == "__main__":
    main()
