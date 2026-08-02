# Steam game reception — what players in negative reviews actually object to

**Status:** Day 1 complete. Data pulled, validated, and frozen. Coding and deck not started.

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
per game rather than inherited silently (9 of 19 games affected; largest is Factorio at
+3,355 reviews). Rate impact is small throughout, at most 0.23pp. See
`outputs/offtopic_sensitivity.csv`.

## Reproduce it

```bash
py src/01_resolve_comparison_set.py   # verify appids against the store API by name
py src/02_pull_reviews.py             # pull reviews + population denominators
py src/03_validate.py                 # acceptance gate; exits non-zero on failure
py src/04_freeze.py create            # write the hash manifest
py src/04_freeze.py verify            # check current files against it
```

Every API response is cached to `data/cache/`, so a re-run makes no network calls and must
reproduce identical hashes. Raw pulls are gitignored; only derived aggregates are committed.

The gate is tested to fail, not just to pass: injecting a duplicate ID, blanking timestamps, or
thinning a segment below three games each produce a non-zero exit.

## Honest notes (data caveats)

- **English only.** Coding cannot be validated in languages I do not read.
- **The comparison set is purposive**, not a random sample. Findings characterise this set.
- **Steam offers no random ordering.** Every available ordering is biased in a known way; the
  choice is which known bias to take and to state.
- **Sampled positive rates sit below lifetime rates for 17 of 19 games as point estimates**, and for
  15 of 19 the Wilson interval excludes the lifetime rate. That is partly real sentiment drift and
  partly an artifact of unequal time coverage. Do not read it as one effect.
- **Price is excluded from segmentation.** The API returns the price at pull time, which reflects
  whatever sale is running.

## How I used AI

I used an AI assistant for three things here: drafting and debugging the Python, learning parts of
the Steam API I had not used before, and editing the prose in this README.

I did not use it to decide what to analyze or to interpret the results. The questions, the analytic
choices, and every finding and recommendation above are mine. I can walk through any number on this
page and explain why it is there.

The sampling defects above are the useful example: the first version of the pull was AI-drafted,
looked correct, ran without error, and was wrong in two ways at once. Reconciling the sample against
the population denominators is what surfaced it.
