# Codebook v1 validation: the instrument did not work

**Result: codebook v1 does not measure what it claims to measure.** Across the 150 held-out
negative reviews, the frozen regex rules and my hand-coding agree on the exact label set in 30 of
150 reviews (20%). Micro precision is 0.516 and micro recall is 0.496. Nine of sixteen categories
have enough support on both sides to produce a usable figure, and of those nine the median F1 is
0.562. One category, `bugs_crashes`, clears F1 0.70.

No per-game objection rate in this repository should be read as a measurement of what reviewers
meant. `outputs/category_rates.csv` remains unvalidated rule output.

## What was actually tested

The design was fixed before the test, which is what makes this result meaningful rather than an
after-the-fact opinion:

- Rules were drafted from the 100-review discovery sample only and frozen at commit `5af32b6`.
  The held-out 150 were not opened first.
- The coding sheet withheld game name, sub-genre, appid and machine predictions, on full
  untruncated text, in a fixed-random order (`src/08_coding_sheet.py`).
- `CODEBOOK.md` recorded one predicted weakness before validation: that `procgen_hollow`
  over-matches on generic phrases carrying no claim about generation.
- Sparse categories were declared inconclusive in advance rather than being reported as results.

Rules were not revised after seeing the held-out data. What follows is v1 as committed.

## Per-category result

| Category | Machine | Analyst | TP | FP | FN | Precision | Recall | F1 | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| bugs_crashes | 30 | 38 | 24 | 6 | 14 | 0.800 | 0.632 | 0.706 | usable |
| tedium_grind | 21 | 21 | 14 | 7 | 7 | 0.667 | 0.667 | 0.667 | usable |
| opacity_teaching | 15 | 12 | 9 | 6 | 3 | 0.600 | 0.750 | 0.667 | usable |
| non_substantive | 14 | 12 | 8 | 6 | 4 | 0.571 | 0.667 | 0.615 | usable |
| ui_controls | 16 | 16 | 9 | 7 | 7 | 0.562 | 0.562 | 0.562 | usable |
| unfinished_abandoned | 15 | 15 | 8 | 7 | 7 | 0.533 | 0.533 | 0.533 | usable |
| developer_conduct | 25 | 14 | 10 | 15 | 4 | 0.400 | 0.714 | 0.513 | usable |
| monetization_dlc | 13 | 11 | 6 | 7 | 5 | 0.462 | 0.545 | 0.500 | usable |
| shallow_repetitive | 14 | 44 | 12 | 2 | 32 | 0.857 | 0.273 | 0.414 | usable |
| update_regression | 14 | 9 | 6 | 8 | 3 | 0.429 | 0.667 | 0.522 | inconclusive |
| npc_ai_pathing | 19 | 6 | 3 | 16 | 3 | 0.158 | 0.500 | 0.240 | inconclusive |
| performance | 9 | 6 | 5 | 4 | 1 | 0.556 | 0.833 | 0.667 | inconclusive |
| taste_mismatch | 1 | 11 | 1 | 0 | 10 | 1.000 | 0.091 | 0.167 | inconclusive |
| procgen_hollow | 4 | 9 | 1 | 3 | 8 | 0.250 | 0.111 | 0.154 | inconclusive |
| difficulty_punishing | 1 | 10 | 0 | 1 | 10 | 0.000 | 0.000 | – | inconclusive |
| rng_unfair | 14 | 0 | 0 | 14 | 0 | 0.000 | – | – | inconclusive |

"Inconclusive" means support below 10 on one or both sides, so the figure rests on too few reviews
to carry weight. It does not mean the category performed well.

Source: `outputs/validation_metrics.csv`, from `py src/12_metrics.py`.

## Failure mode 1: the rules encode topic, not stance

The largest single source of false positives is patterns that match a subject being *mentioned*
rather than an objection being *made*. Mentioning a developer is not criticising conduct. Mentioning
DLC is not objecting to price.

| Pattern | Category | Fired, analyst agreed | Fired, analyst disagreed |
|---|---|---|---|
| `\brandom(ness\|ly)?\b` | rng_unfair | 0 | 11 |
| `\bupdates?\b` | update_regression | 6 | 7 |
| `\bparadox\b` | developer_conduct | 3 | 6 |
| `\bnpcs?\b` | npc_ai_pathing | 1 | 6 |
| `\bdevs?\b` | developer_conduct | 2 | 5 |
| `\bdeveloper` | developer_conduct | 4 | 5 |
| `\bdlcs?\b` | monetization_dlc | 4 | 5 |
| `\bstuck\b` | npc_ai_pathing | 0 | 4 |
| `\bstupid\b` | npc_ai_pathing | 0 | 4 |

Twenty-two of the 76 category-and-pattern combinations that fired on the held-out 150 never once
fired on a review I agreed with, accounting for 43 wasted firings.

`rng_unfair` is the clearest case and the most instructive. It fired 14 times and I agreed zero
times, giving precision 0.000. Eleven of those firings came from `\brandom(ness|ly)?\b`, which in
this corpus overwhelmingly appears in phrases like "randomly generated" — a description of
procedural content, not a complaint that outcomes are arbitrary. The rule captures a different
construct from the one the codebook defines. Tightening it will not help; it was aimed at the wrong
target.

`npc_ai_pathing` fails the same way through `\bstuck\b` and `\bstupid\b`, which in practice attach
to the player being stuck and to general insults aimed at anything.

## Failure mode 2: objections expressed in language no rule anticipated

Thirty-one of 150 reviews (20.7%) matched no rule at all yet carry a label from my coding. This is
the harder failure, because it is not fixable by writing more careful patterns.

`shallow_repetitive` shows it most starkly: I coded it 44 times, the rules caught 12, missing 32.
The rule looks for `shallow`, `boring`, `bland`, `soulless`, `sterile`. Reviewers said things like
"there just isn't enough reward in this game" and "a laughable, yet sad, reskin of the basic
concepts of Anno 1602." Both are depth complaints. Neither contains any word the rule knows. The
vocabulary of "this game has no depth" is effectively unbounded, and a keyword rule samples an
arbitrary corner of it.

The same applies to `difficulty_punishing` (10 of 10 missed) and `taste_mismatch` (10 of 11 missed),
where the rules only recognise a handful of fixed idioms.

Note that `shallow_repetitive` has the highest precision in the whole set (0.857) alongside the
worst recall of any usable category (0.273). When the rule fires it is usually right. It just
almost never fires. Precision alone would have made this category look like v1's best performer.

## The category the study was built on

`procgen_hollow` failed in both directions at once. It fired 4 times, of which I agreed with 1. I
coded it 9 times, of which it caught 1. Precision 0.250, recall 0.111, and thin enough on both
sides to be inconclusive regardless.

The over-firing half was predicted in `CODEBOOK.md` before validation and is confirmed. The
under-firing half was not predicted and is the more interesting finding: reviewers who object to
hollow generated content tend to do it by narrating an example rather than naming the mechanism.
One missed review makes the objection by describing an absurd generated relationship and its lack of
consequence, without using the words procedural, generated, random or repeat.

**This invalidates the candidate signal reported in the README.** That signal was a concentration of
`procgen_hollow` rule matches in emergent-narrative games (3 of 4 games at 7.0–18.8%, against at or
near zero for 14 of the other 15). It was correctly labelled a keyword concentration rather than a
finding. It now has a measured precision of 0.250 behind it on held-out data, so roughly three in
four of the matches that produced that concentration are not the objection the category names. The
concentration cannot be interpreted as evidence about procedural generation, and the study's central
question stays open.

## How much agreement was achievable

A 20% exact-match rate needs a reference point, because the ceiling on this task is not 100%.
Multi-label coding of free text is hard, and two careful readers of the same review often differ.

The repository holds one measurement of that. `src/10_spotcheck_select.py` drew 30 of the 150 rows
before coding began, and a second AI (Codex) read those 30 independently against the same codebook,
without access to my labels or to the regex output. Its exact label sets agree with mine on 15 of 30
(50%), pooled Jaccard 0.588 across all positive assignments, 0.706 averaged per review
(`outputs/spotcheck_agreement.csv`). It is the only independent second reading in the project.

It is a thin benchmark: 30 rows, and the second reader is an AI rather than a second human coder.
Taken for what it is, it puts the achievable exact-match rate nearer 50% than 100%. v1's 20% sits
well below that, so task difficulty does not account for the gap on its own. It also sets a realistic
target: a v2 reaching roughly 50% would be at the limit this evidence can distinguish.

## What I am not claiming

- **Not that the categories are wrong.** This tests the regex operationalisation, not the 16
  definitions. A category can be well-defined and badly implemented, which is what
  `shallow_repetitive` looks like.
- **Not a general accuracy figure.** These are per-category figures on one purposive comparison set
  of 19 simulation games, in English, from an equal-N latest-review sample.
- **Not that the seven inconclusive categories failed.** They have too little support to say, which
  is itself a result of the sample size and the category rarity.
- **Not that rules are the wrong approach.** `bugs_crashes` at F1 0.706 suggests objections with a
  concrete, stable vocabulary are tractable this way. The abstract ones are not.

## Provenance

Every figure here compares the frozen rules against `outputs/analyst_labels.csv`, my hand-coding of
the blinded sheet. That is the only reference standard in the repository, and the footer of every
`12_metrics.py` run names it.

An earlier AI reading pass over the same 150 was removed rather than kept. It existed as scaffolding
so the metrics and manifest chain could be built before my coding was done. Once my coding landed the
two files were label-identical, so it offered no second opinion and only created the risk of the two
being read as agreeing sources. The one genuinely independent reading is the 30-row spot-check above.

## Reproduce

```bash
py src/14_analyst_labels.py         # ingest hand-coded labels, with gates
py src/12_metrics.py                # per-category precision/recall/F1
py src/15_error_analysis.py         # per-pattern failure attribution
py src/16_spotcheck_agreement.py    # second reader vs my labels on 30 rows
py src/verify.py                    # all four phase manifests
```

Outputs: `analyst_labels.csv`, `analyst_manifest.json`, `validation_metrics.csv`,
`v1_error_analysis.csv`, `spotcheck_agreement.csv`.

## What v2 would need

Recorded here so the boundary is dated and explicit: these 150 reviews are now spent as a test set.
Any v2 written against the failures above is fitted to them, and any v2 metric computed on the same
150 is in-sample and not comparable to the figures in this document. Measuring v2 honestly requires a
fresh held-out sample drawn from the negatives outside the current split.

The failures point in different directions. The topic-not-stance patterns are fixable by requiring a
complaint term near the entity term. The vocabulary failures are not fixable lexically and would need
a different method, which then has to be validated on its own terms rather than inheriting the trust
this one did not earn.
