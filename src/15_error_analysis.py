"""Day 3 - why codebook v1 failed, attributed to individual regex patterns.

The per-category metrics in 12_metrics.py say which categories failed. They do
not say why, and "the rules were weak" is not a finding anyone can act on. This
attributes every false positive to the specific pattern that fired it, and
samples the false negatives, so v1's failure modes are named rather than
summarised.

Two distinct failure shapes show up and they need different fixes:

  OVER-FIRING   a pattern matches text that carries no such objection. The word
                is present, the claim is not. Fixable by tightening the pattern.

  UNDER-FIRING  reviewers express the objection in language the rule never
                anticipated. No amount of tightening helps; the rule needs
                different vocabulary, or the category is not lexically
                addressable at all.

Reads the analyst's labels, not the AI reading pass, though the two are
label-identical (see outputs/analyst_manifest.json).

Run: py src/15_error_analysis.py
"""

import csv
import importlib.util
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from steam import ROOT  # noqa: E402

spec = importlib.util.spec_from_file_location("codebook", Path(__file__).parent / "06_codebook.py")
cb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cb)

DATA, OUT = ROOT / "data", ROOT / "outputs"
CATEGORIES = sorted(c for c in cb.CATEGORIES if c != "uncoded")


def snippet(text: str, width: int = 100) -> str:
    return " ".join((text or "").split())[:width]


def main() -> int:
    human = {r["recommendationid"]: r for r in
             csv.DictReader(open(OUT / "analyst_labels.csv", encoding="utf-8"))}
    raw = {r["recommendationid"]: r for r in
           csv.DictReader(open(DATA / "reviews_raw.csv", encoding="utf-8"))}

    pat_fp = defaultdict(Counter)   # category -> pattern -> false positives
    pat_tp = defaultdict(Counter)   # category -> pattern -> true positives
    fn_examples = defaultdict(list)
    fp_examples = defaultdict(list)
    uncoded_but_human = 0

    for rid, h in human.items():
        text = raw[rid]["review"]
        fired = set(cb.code(text))
        if "uncoded" in fired and int(h["n_labels"]) > 0:
            uncoded_but_human += 1

        for c in CATEGORIES:
            m, hu = c in fired, h[c] == "1"
            if m and not hu:
                fp_examples[c].append(snippet(text))
            if hu and not m:
                fn_examples[c].append(snippet(text))
            if c == "non_substantive" or not m:
                continue
            for p in cb.COMPILED[c]:
                if p.search(text):
                    (pat_tp if hu else pat_fp)[c][p.pattern] += 1

    rows = []
    for c in CATEGORIES:
        for p in set(pat_fp[c]) | set(pat_tp[c]):
            fp, tp = pat_fp[c][p], pat_tp[c][p]
            rows.append({"category": c, "pattern": p, "fired_on_agreed": tp,
                         "fired_on_disagreed": fp, "total_firings": tp + fp,
                         "pattern_precision": round(tp / (tp + fp), 3) if tp + fp else ""})
    rows.sort(key=lambda r: (-r["fired_on_disagreed"], r["category"]))
    with (OUT / "v1_error_analysis.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    print("PATTERNS THAT COST THE MOST PRECISION (fired where the analyst disagreed)\n")
    print(f"  {'category':<22}{'pattern':<34}{'agreed':>7}{'disagreed':>11}")
    for r in rows[:14]:
        print(f"  {r['category']:<22}{r['pattern'][:33]:<34}{r['fired_on_agreed']:>7}"
              f"{r['fired_on_disagreed']:>11}")

    print("\n\nCATEGORIES THE RULES COULD NOT SEE (analyst coded, no rule fired)\n")
    for c in sorted(CATEGORIES, key=lambda c: -len(fn_examples[c])):
        if not fn_examples[c]:
            continue
        print(f"  {c}  ({len(fn_examples[c])} missed)")
        for s in fn_examples[c][:2]:
            print(f"      \"{s}\"")
    print(f"\n\n{uncoded_but_human} reviews matched no rule at all but carry an analyst label.")
    print(f"wrote v1_error_analysis.csv ({len(rows)} pattern rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
