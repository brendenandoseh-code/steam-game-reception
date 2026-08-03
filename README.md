# Steam game reception — what players in negative reviews actually object to

**Status:** Data collection and codebook v1 are frozen, and v1 has now been validated against my
hand-coding of the held-out 150. **The instrument failed.** Rules and hand-coding agree on the exact
label set in 30 of 150 reviews (20%); micro precision is 0.516 and micro recall 0.496; 9 of 16
categories have usable support and their median F1 is 0.562. Full result and failure analysis in
[VALIDATION_V1.md](VALIDATION_V1.md); a 12-slide walkthrough of the sampling traps and the failed
instrument is in `Steam_Game_Reception_Validation_Deck.pptx`. No player insight is published, and the
per-game rates in `outputs/category_rates.csv` remain unvalidated rule output.

A messaging and positioning study built on public Steam review text. A review score tells a
publisher *that* players are unhappy; it does not say *why*. This takes the negative reviews
across an established simulation-game comparison set and asks what players are objecting to,
how that differs by sub-genre, and what it implies for a new entrant's positioning risks.

## Data

**19 games, 22,796 English reviews.** Two public Steam endpoints, no API key, no scraping:

- `store.steampowered.com/appreviews/{appid}` — review text, recommend flag, playtime at review, timestamp
- `store.steampowered.com/api/appdetails` — name, genres, release date, price, Metacritic

Comparison set: colony/management sims (7), grand strategy and dynasty (3), emergent narrative (4),
life sims (5). Purposively selected to span the positioning axes a new entrant must choose between.

## What Day 1 found before any analysis

**The obvious way to pull this data is wrong.** `filter=all` is Steam's helpfulness-weighted view,
not an unweighted one, and its cursor pagination stalls near 200 reviews. A first pull using it
silently truncated most games — Wildermyth returned 92 of 13,082 available English reviews.
`filter=recent` pages reliably. Anyone pulling Steam reviews without checking this gets a
truncated sample and no error message. At equal N the helpfulness view is more negative in 10 of 16 games, by a median of 1.1 points.

**"Most recent 1,200 reviews" is not a time window.** Coverage runs from 13 days (Stardew Valley)
to 963 days (My Time at Portia), median 192, because review volume differs by two orders of
magnitude across the set. This is an equal-N latest-review sample and is described that way.

**Reviews are clustered inside games.** A sub-genre holds 3 to 7 games, so the effective N for any
sub-genre claim is the game count, not the review count. Pooled two-proportion tests over 4,798
clustered reviews would be badly overconfident and are not run.

**Steam withholds off-topic review-bomb periods by default.** Retained, and the sensitivity is computed
per game rather than inherited silently. Four games show unambiguous withholding (Factorio +3,355,
Crusader Kings III +1,194, Europa Universalis IV +624, Victoria 3 +396). Five others differ by only
1-3 reviews, which cannot be told apart from ordinary accrual: the two requests were captured 22-59
minutes apart. Largest absolute rate impact is 0.225pp. See `outputs/offtopic_sensitivity.csv`.

**A candidate signal that did not survive.** Rule matches for `procgen_hollow` concentrate in
emergent-narrative games (3 of 4 at 7.0-18.8%; 14 of the other 15 games at or near zero). That was
recorded as a concentration of *keyword matches*, not evidence about what reviewers meant, and held
back pending hand-coding. Hand-coding has now been done and the category scored precision 0.250 and
recall 0.111 on the held-out 150. Roughly three in four of the matches producing that concentration
are not the objection the category names, so it cannot be read as evidence about procedural
generation. The study's central question stays open. See [VALIDATION_V1.md](VALIDATION_V1.md).

**"Uncoded" is coverage, not recall.** 20.2% of negative reviews match no rule, against 12% on the
discovery sample the rules were built from. That gap measures where the rules are silent. It is not a
recall estimate: a coded review can still contain an objection the rules missed, and an uncoded review
may legitimately have no objection to code.

## Honest notes (data caveats)

- **English only.** Coding cannot be validated in languages I do not read.
- **The comparison set is purposive**, not a random sample. Findings characterise this set.
- **Steam offers no random ordering.** Every available ordering is biased in a known way; the
  choice is which known bias to take and to state.
- **Sampled positive rates sit below lifetime rates for 17 of 19 games as point estimates**, and for
  15 of 19 the Wilson interval excludes the lifetime rate. This is **compatible with** sentiment
  changing over time, but the design cannot separate that from unequal time coverage and non-random
  ordering. Do not report it as drift.
- **Price is excluded from segmentation.** The API returns the price at pull time, which reflects
  whatever sale is running.

## How I used AI

This project is AI-assisted throughout, and the codebook in particular is **an AI-drafted candidate**,
not an analyst-authored instrument. An AI assistant read the 100-review discovery sample, proposed the
16 objection categories, wrote the regex rules that operationalise them, ran them across all 3,004
negative reviews, and drafted the aggregate summary. It also wrote the pull, validation and freeze code.

What stays with me: the question, the scope, the verification, and every interpretation that ships.
The held-out 150 are coded by me against the blinded sheet, in `outputs/analyst_labels.csv`, and that
coding is the single reference standard this repository holds. It is what
[VALIDATION_V1.md](VALIDATION_V1.md) measures v1 against.

A second AI (Codex) independently read 30 of the 150, selected by `src/10_spotcheck_select.py` before
coding began. Its exact label sets agree with mine on 15 of 30 (50%), pooled Jaccard 0.588
(`src/16_spotcheck_agreement.py`, `outputs/spotcheck_agreement.csv`). That is not human validation and
does not replace the analyst standard, but it is the only independent second reading here, and
[VALIDATION_V1.md](VALIDATION_V1.md) uses it to estimate how much agreement was achievable on this task.

An earlier AI reading pass over the same 150 was removed from the repository rather than kept. It was
built as scaffolding so the metrics and manifest chain could be exercised before my coding existed, and
once my coding landed the two files were label-identical, so keeping both offered no second opinion and
invited the two from being read as sources corroborating each other.

No precision or accuracy figure is reported anywhere in this repository without saying who produced the
labels behind it. The per-game rates in `outputs/category_rates.csv` remain **unvalidated rule output**:
they show where a keyword rule fired, and v1 validation establishes that this is a poor proxy for what
reviewers meant.

## Reproduce it

```bash
py src/01_resolve_comparison_set.py   # verify appids against the store API by name
py src/02_pull_reviews.py             # pull reviews + population denominators
py src/03_validate.py                 # acceptance gate; exits non-zero on failure
py src/04_freeze.py create            # write the day-1 hash manifest
py src/05_split.py                    # discovery/held-out IDs, before reading text
py src/06_codebook.py                 # frozen rules (imported, not run directly)
py src/07_apply.py                    # apply rules to all negatives
py src/08_coding_sheet.py             # blinded held-out sheet
py src/09_figures.py                  # descriptive charts (not validation-dependent)
py src/10_spotcheck_select.py         # pick the 30-row inter-coder spot-check, before coding
py src/13_spotcheck_sheet.py          # blank spot-check sheet for the second reader
py src/14_analyst_labels.py           # ingest my hand-coding, with gates
py src/12_metrics.py                  # per-category precision/recall/F1 vs my labels
py src/15_error_analysis.py           # per-pattern attribution of v1's failures
py src/16_spotcheck_agreement.py      # second reader vs my labels on the 30 rows
py src/verify.py                      # check ALL FOUR phase manifests
py src/test_gate.py                   # gate invariants
```

Every API response is cached to `data/cache/`, so a re-run makes no network calls and must
reproduce identical hashes. Raw pulls are gitignored; only derived aggregates are committed.

The gate is tested to fail, not just to pass: injecting a duplicate ID, blanking timestamps, or
thinning a segment below three games each produce a non-zero exit.
