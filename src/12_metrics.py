"""Day 3 - per-category agreement between the frozen rules and the reference labels.

Reports TP, FP, FN, support on both sides, precision, recall and F1 per category.
No single pooled agreement rate: the scheme is multi-label and the categories are
unevenly frequent, so one number would be carried by the common ones.

Compares the frozen rules against the analyst's hand-coded labels. A different
label file can be passed as an argument; whichever is used is printed on every
run and written into the output, because which labels sit behind a precision
figure changes what that figure means.

  py src/12_metrics.py                              # outputs/analyst_labels.csv
  py src/12_metrics.py path/to/other_labels.csv

Every category with thin support on either side is marked inconclusive.
"""

import csv
import importlib.util
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from steam import ROOT  # noqa: E402

spec = importlib.util.spec_from_file_location("codebook", Path(__file__).parent / "06_codebook.py")
cb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cb)

DATA, OUT = ROOT / "data", ROOT / "outputs"
MIN_SUPPORT = 10   # below this on either side, the category is inconclusive


SOURCE_NOTE = {
    "analyst_labels.csv": "hand-coded by the analyst against the blinded sheet. "
                          "See outputs/analyst_manifest.json.",
}


def main():
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT / "analyst_labels.csv"
    if not src.exists():
        print(f"label file not found: {src}")
        return 1
    out_name = "validation_metrics.csv" if src.name == "analyst_labels.csv" \
        else f"validation_metrics_{src.stem}.csv"

    ref = {r["recommendationid"]: r for r in
           csv.DictReader(open(src, encoding="utf-8"))}
    raw = {r["recommendationid"]: r for r in
           csv.DictReader(open(DATA / "reviews_raw.csv", encoding="utf-8"))}

    cats = [c for c in cb.CATEGORIES if c != "uncoded"]
    rows = []
    for rid, rr in ref.items():
        machine = set(cb.code(raw[rid]["review"]))
        human = {c for c in cats if rr[c] == "1"}
        rows.append((machine, human))

    out = []
    for c in cats:
        tp = sum(1 for m, h in rows if c in m and c in h)
        fp = sum(1 for m, h in rows if c in m and c not in h)
        fn = sum(1 for m, h in rows if c not in m and c in h)
        prec = tp / (tp + fp) if tp + fp else None
        rec = tp / (tp + fn) if tp + fn else None
        f1 = 2 * prec * rec / (prec + rec) if prec and rec else None
        conclusive = (tp + fn) >= MIN_SUPPORT and (tp + fp) >= MIN_SUPPORT
        out.append({"category": c, "machine_support": tp + fp, "reference_support": tp + fn,
                    "tp": tp, "fp": fp, "fn": fn,
                    "precision": round(prec, 3) if prec is not None else "",
                    "recall": round(rec, 3) if rec is not None else "",
                    "f1": round(f1, 3) if f1 is not None else "",
                    "verdict": "usable" if conclusive else "INCONCLUSIVE (thin support)"})

    for r in out:
        r["label_source"] = src.name
    with (OUT / out_name).open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0].keys())); w.writeheader(); w.writerows(out)

    print(f"labels: {src.name}   ({len(ref)} rows)\n")
    print(f"{'category':<24}{'mach':>5}{'ref':>5}{'TP':>4}{'FP':>4}{'FN':>4}"
          f"{'prec':>7}{'rec':>7}{'F1':>7}   verdict")
    for r in sorted(out, key=lambda r: -r["reference_support"]):
        p = f"{r['precision']:.3f}" if r["precision"] != "" else "   -  "
        rc = f"{r['recall']:.3f}" if r["recall"] != "" else "   -  "
        f1 = f"{r['f1']:.3f}" if r["f1"] != "" else "   -  "
        print(f"{r['category']:<24}{r['machine_support']:>5}{r['reference_support']:>5}"
              f"{r['tp']:>4}{r['fp']:>4}{r['fn']:>4}{p:>7}{rc:>7}{f1:>7}   {r['verdict']}")
    usable = [r for r in out if r["verdict"] == "usable"]
    print(f"\n{len(usable)} of {len(out)} categories have support on both sides for a usable figure.")
    print(f"wrote {out_name}")
    print(f"Label source: {src.name} - {SOURCE_NOTE.get(src.name, 'provenance not recorded')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
