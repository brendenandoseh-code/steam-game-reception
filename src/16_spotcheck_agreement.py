"""Day 3 - inter-coder agreement on the 30-row spot-check.

Compares my labels against a second reader's on the 30 rows selected by
10_spotcheck_select.py before either of us started. The second reader is an AI
(Codex), reading the same untruncated text against the same frozen codebook,
with no access to my labels or to the regex output.

This is the only independent second reading in the project, and it exists to
answer one question: how much agreement is achievable on this task at all? A
rules-versus-me figure of 20% means little without knowing whether two careful
readers would agree 95% of the time or 50% of the time. See VALIDATION_V1.md.

It is not human validation. Thirty rows is thin, and an AI second reader is not
a second analyst. Both limits are stated wherever the number is used.

Supersedes the earlier codex_ai_spotcheck_agreement.csv, which was computed
outside src/ and anchored to reference_labels.csv, a file that no longer exists.

Run: py src/16_spotcheck_agreement.py
"""

import csv
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from steam import ROOT  # noqa: E402

spec = importlib.util.spec_from_file_location("codebook", Path(__file__).parent / "06_codebook.py")
cb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cb)

OUT = ROOT / "outputs"
CATEGORIES = sorted(c for c in cb.CATEGORIES if c != "uncoded")


def main() -> int:
    picks = [r["row"] for r in csv.DictReader(open(OUT / "spotcheck_rows.csv", encoding="utf-8"))]
    second = {r["row"]: r for r in
              csv.DictReader(open(OUT / "codex_ai_spotcheck_labels.csv", encoding="utf-8"))}
    mine = {r["row"]: r for r in
            csv.DictReader(open(OUT / "analyst_labels.csv", encoding="utf-8"))}

    if sorted(second, key=int) != sorted(picks, key=int):
        print("second reader's rows do not match the pre-selected spot-check rows")
        return 1
    missing = [p for p in picks if p not in mine]
    if missing:
        print(f"rows missing from analyst_labels.csv: {missing}")
        return 1

    # Two Jaccard figures, because they answer different questions and differ
    # materially here (0.588 vs 0.706). Micro pools every positive assignment
    # and so is dominated by reviews carrying many labels; macro weights each
    # review equally. Micro is the more conservative of the two and is the one
    # quoted in VALIDATION_V1.md.
    exact, jac, inter, union = 0, [], 0, 0
    for p in picks:
        a = {c for c in CATEGORIES if mine[p][c] == "1"}
        b = {c for c in CATEGORIES if (second[p].get(c) or "").strip() == "1"}
        if a == b:
            exact += 1
        inter += len(a & b)
        union += len(a | b)
        jac.append(len(a & b) / len(a | b) if a | b else 1.0)

    rows = []
    for c in CATEGORIES:
        a = {p for p in picks if mine[p][c] == "1"}
        b = {p for p in picks if (second[p].get(c) or "").strip() == "1"}
        both, a_only, b_only = len(a & b), len(a - b), len(b - a)
        f1 = 2 * both / (2 * both + a_only + b_only) if both else 0.0
        rows.append({"category": c, "analyst_support": len(a), "second_reader_support": len(b),
                     "both_positive": both, "analyst_only": a_only, "second_reader_only": b_only,
                     "positive_overlap_f1": round(f1, 3)})

    path = OUT / "spotcheck_agreement.csv"
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    rate = exact / len(picks)
    manifest = {
        "phase": "day3_spotcheck_agreement",
        "first_reader": "the analyst (outputs/analyst_labels.csv)",
        "second_reader": "Codex AI reading pass on the 30 pre-selected rows",
        "NOT_human_validation": True,
        "purpose": "estimate the achievable agreement ceiling on this coding task, "
                   "as context for the rules-versus-analyst figures in VALIDATION_V1.md",
        "limits": "30 rows; the second reader is an AI, not a second analyst",
        "n_rows": len(picks),
        "exact_label_set_agreement_n": exact,
        "exact_label_set_agreement_rate": round(rate, 3),
        "pooled_positive_jaccard_micro": round(inter / union, 3),
        "mean_row_jaccard_macro": round(sum(jac) / len(jac), 3),
        "depends_on_analyst_sha": hashlib.sha256((OUT / "analyst_labels.csv").read_bytes()).hexdigest(),
        "depends_on_selection_sha": hashlib.sha256((OUT / "spotcheck_rows.csv").read_bytes()).hexdigest(),
        "files": {"spotcheck_agreement.csv": {
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "bytes": path.stat().st_size}},
    }
    (OUT / "spotcheck_agreement_manifest.json").write_text(json.dumps(manifest, indent=2),
                                                           encoding="utf-8")

    print(f"spot-check agreement on {len(picks)} rows (analyst vs second reader)")
    print(f"  exact label-set agreement : {exact}/{len(picks)} = {rate:.1%}")
    print(f"  pooled Jaccard (micro)    : {inter / union:.3f}")
    print(f"  mean row Jaccard (macro)  : {sum(jac) / len(jac):.3f}")
    print(f"\n  {'category':<24}{'mine':>6}{'2nd':>6}{'both':>6}{'F1':>7}")
    for r in rows:
        if r["analyst_support"] or r["second_reader_support"]:
            print(f"  {r['category']:<24}{r['analyst_support']:>6}{r['second_reader_support']:>6}"
                  f"{r['both_positive']:>6}{r['positive_overlap_f1']:>7.3f}")
    print(f"\nwrote spotcheck_agreement.csv and spotcheck_agreement_manifest.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
