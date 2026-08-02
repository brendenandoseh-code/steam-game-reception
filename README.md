# Steam game reception — what players in negative reviews actually object to

**Status:** Day 1 complete and frozen. Codebook v1 drafted and applied. The blinded held-out sheet is
built and awaiting analyst hand-coding; no validated metrics exist yet, and the deck is not started.

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

**A candidate signal, not a finding.** Rule matches for `procgen_hollow` concentrate in
emergent-narrative games (3 of 4 at 7.0-18.8%; 14 of the other 15 games at or near zero). That is a
concentration of *keyword matches*, and it is not yet evidence about what reviewers meant. Two reasons
to withhold judgement: 8 of the 76 matches fire only on generic phrases with no reference to
generation, and 21 of the 76 also carry `shallow_repetitive`, which itself appears in all four
emergent games at 6.9-23.0%. Any claim that these are distinct objections has to survive hand-coding
first.

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
The held-out 150 are labelled by me, blind to the machine predictions and to which game each review
came from. Software has necessarily processed their text; what has not happened is any analyst reading
or labelling of them, precisely because the assistant cannot be both the instrument and the reference standard
for its own accuracy.

Per `ANALYST_OPERATING_SYSTEM.md` section 13, no precision or accuracy figure is reported here without
saying who produced the reference labels. Until that hand-coding is done, the category rates below are
**unvalidated rule output**: they show where a keyword rule fired, not what reviewers meant.

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
py src/verify.py                      # check ALL THREE phase manifests
py src/test_gate.py                   # gate invariants
```

Every API response is cached to `data/cache/`, so a re-run makes no network calls and must
reproduce identical hashes. Raw pulls are gitignored; only derived aggregates are committed.

The gate is tested to fail, not just to pass: injecting a duplicate ID, blanking timestamps, or
thinning a segment below three games each produce a non-zero exit.
