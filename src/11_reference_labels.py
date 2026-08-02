"""Day 3 - reference labels for the held-out 150.

AUTHORSHIP, stated plainly: these labels were produced by an AI assistant
reading each review and judging it against CODEBOOK.md. They were NOT produced
by the analyst. The analyst spot-checks 30 rows independently and the
disagreement rate on that subset is reported alongside every metric.

Why this is still worth measuring: the rules in 06_codebook.py match patterns;
these labels come from reading. Those are different processes, so agreement
between them is informative about where the rules over- and under-fire. It is
NOT a human reference standard, and no document in this repository says it is.

Codes, abbreviated for legibility:
  bug bugs_crashes      per performance        ui  ui_controls
  opa opacity_teaching  ted tedium_grind       mon monetization_dlc
  unf unfinished_abandoned                     upd update_regression
  npc npc_ai_pathing    shl shallow_repetitive pro procgen_hollow
  rng rng_unfair        dif difficulty_punishing
  dev developer_conduct tas taste_mismatch     non non_substantive
  (empty = an objection the codebook has no category for, or none identified)
"""

import csv
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from steam import ROOT  # noqa: E402

OUT = ROOT / "outputs"

ABBR = {
    "bug": "bugs_crashes", "per": "performance", "ui": "ui_controls",
    "opa": "opacity_teaching", "ted": "tedium_grind", "mon": "monetization_dlc",
    "unf": "unfinished_abandoned", "upd": "update_regression", "npc": "npc_ai_pathing",
    "shl": "shallow_repetitive", "pro": "procgen_hollow", "rng": "rng_unfair",
    "dif": "difficulty_punishing", "dev": "developer_conduct", "tas": "taste_mismatch",
    "non": "non_substantive",
}

LABELS = {
    1: "mon dev", 2: "ted shl tas", 3: "ted ui per", 4: "dif shl", 5: "shl",
    6: "", 7: "ted shl", 8: "non", 9: "bug shl", 10: "ui ted",
    11: "tas", 12: "tas", 13: "shl", 14: "per unf", 15: "shl",
    16: "bug per npc", 17: "upd", 18: "bug unf", 19: "bug ui", 20: "npc upd",
    21: "ted", 22: "opa ui", 23: "bug", 24: "pro shl", 25: "shl dif",
    26: "non", 27: "upd bug dev", 28: "opa", 29: "unf", 30: "shl",
    31: "ui bug ted shl", 32: "non", 33: "dif", 34: "upd bug", 35: "shl bug",
    36: "mon dev", 37: "non", 38: "ted shl", 39: "mon dev", 40: "opa",
    41: "bug", 42: "mon", 43: "mon", 44: "shl", 45: "bug upd",
    46: "non", 47: "bug", 48: "bug", 49: "ted tas", 50: "shl",
    51: "upd", 52: "bug", 53: "non", 54: "non", 55: "bug unf",
    56: "dif", 57: "pro opa ui", 58: "opa ted shl", 59: "bug", 60: "shl",
    61: "ted mon", 62: "pro shl", 63: "", 64: "ted shl", 65: "upd",
    66: "dev", 67: "unf dev", 68: "bug ui", 69: "mon bug dev", 70: "pro shl ui",
    71: "ui dif", 72: "shl unf", 73: "unf", 74: "npc bug unf", 75: "opa ui",
    76: "", 77: "shl unf", 78: "bug npc", 79: "shl", 80: "shl",
    81: "bug ui", 82: "unf dev upd", 83: "bug unf", 84: "tas", 85: "dev",
    86: "opa ui unf", 87: "bug dev", 88: "non", 89: "bug", 90: "mon ted shl",
    91: "bug", 92: "bug", 93: "shl", 94: "ted shl", 95: "shl",
    96: "opa", 97: "", 98: "shl ted", 99: "opa ted", 100: "tas",
    101: "bug ui", 102: "shl", 103: "tas", 104: "bug unf dev upd", 105: "bug unf",
    106: "opa", 107: "unf dev", 108: "pro shl", 109: "tas", 110: "ted shl",
    111: "bug", 112: "shl", 113: "non", 114: "ted shl", 115: "pro shl",
    116: "bug", 117: "bug", 118: "ted per", 119: "tas", 120: "mon",
    121: "mon", 122: "dif ui tas", 123: "ui dif", 124: "shl dif", 125: "non",
    126: "per bug", 127: "bug", 128: "opa ui", 129: "npc dif", 130: "opa",
    131: "ted shl", 132: "shl", 133: "non", 134: "pro shl", 135: "mon dev",
    136: "shl", 137: "", 138: "tas", 139: "npc bug", 140: "pro bug",
    141: "ted shl", 142: "per shl", 143: "pro shl", 144: "bug", 145: "ted shl",
    146: "", 147: "non", 148: "dif", 149: "bug", 150: "dev",
}

CATEGORIES = sorted(ABBR.values())


def main():
    sheet = list(csv.DictReader(open(OUT / "heldout_coding_sheet.csv", encoding="utf-8")))
    assert len(sheet) == 150 and len(LABELS) == 150

    rows = []
    for s in sheet:
        codes = [ABBR[a] for a in LABELS[int(s["row"])].split()]
        assert not ("non_substantive" in codes and len(codes) > 1), \
            f"row {s['row']}: non_substantive must be exclusive"
        rows.append({"row": int(s["row"]), "recommendationid": s["recommendationid"],
                     "n_labels": len(codes),
                     **{c: int(c in codes) for c in CATEGORIES}})

    path = OUT / "reference_labels.csv"
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)

    manifest = {
        "phase": "day3_reference_labels",
        "labeller": "AI assistant, by reading each review against CODEBOOK.md",
        "NOT_a_human_reference_standard": True,
        "analyst_role": "independent spot-check of 30 rows; disagreement rate reported with every metric",
        "why_still_informative": "the rules match patterns, these labels come from reading; different "
                                 "processes, so agreement locates where the rules over- and under-fire",
        "depends_on_sheet_sha": hashlib.sha256((OUT / "heldout_coding_sheet.csv").read_bytes()).hexdigest(),
        "files": {"reference_labels.csv": {
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "bytes": path.stat().st_size}},
    }
    (OUT / "reference_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    tot = sum(r["n_labels"] for r in rows)
    blank = sum(1 for r in rows if r["n_labels"] == 0)
    print(f"{len(rows)} reference labels written, {tot} label assignments, "
          f"{tot/len(rows):.2f} per review")
    print(f"  {blank} reviews carry no label (an objection the codebook has no category for)")
    for c in CATEGORIES:
        n = sum(r[c] for r in rows)
        print(f"   {c:<24}{n:>4}")


if __name__ == "__main__":
    main()
