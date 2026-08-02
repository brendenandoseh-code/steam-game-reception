# Scope

**Status:** data collection complete and frozen (`outputs/freeze_manifest.json`). Codebook v1 drafted
and applied. The blinded held-out sheet is built and awaiting hand-coding; no validated metrics exist yet.

## Why I am doing this

I am building a simulation game where a generated world runs on its own and the lives inside it
accumulate into history. That raises a design question I could not answer from intuition: when players
dislike a game in this category, what are they actually objecting to, and does procedurally generated
content draw a *distinct* complaint or just the same complaints as everything else?

That question is answerable from public data. Steam reviews are the largest body of unprompted consumer
reaction to these games that exists, and the negative ones say plainly what went wrong.

So this is a positioning analysis of an established category, done to understand the risks facing a new
entrant. I have a personal stake in the answer, which is exactly why the guards below matter: it would
be easy to find the result I want.

## The question

> A review score tells you *that* players are unhappy, not *why*. Across the established simulation
> category, what do players in negative reviews actually object to, how do those objections differ by
> sub-genre, and what does that imply about the positioning risks facing a new entrant?

Objections only. An earlier version promised both praise and objections while the codebook only ever
coded negative reviews. Objections alone is the honest scope and the more useful half for a positioning
question.

## Guards against finding what I want

I want `procgen_hollow` to be a real and distinct objection, because it bears on a game I am building.
That is a motivated-reasoning risk, handled structurally rather than by good intentions:

- Discovery and held-out samples were drawn, hashed and committed **before any review text was read**,
  so the codebook cannot be tuned to its own test set.
- The codebook is **frozen** once applied. A category that performs badly is reported as a v1 result,
  not quietly patched.
- The held-out coding sheet is **blinded**: no game name, no sub-genre, no machine predictions, fixed
  random order. If I could see which reviews came from emergent-narrative games I would code toward the
  answer I expect.
- Known weaknesses are recorded **before** validation. Eight of the 76 `procgen_hollow` matches fire on
  generic phrasing with no reference to generation at all, and the category has only four
  machine-positives in the held-out set, so its precision will be inconclusive whatever the coding
  shows. Both are written into `CODEBOOK.md`, before any labelling.

## Data

Two public Steam endpoints, no API key, no scraping. Verified working 2026-08-02.

**Reviews** — `store.steampowered.com/appreviews/{appid}` — free text, recommend flag, playtime at
review, timestamp, early-access flag, purchase context, helpfulness votes. `query_summary` returns
lifetime totals per game, which are the correct denominators.

**Metadata** — `store.steampowered.com/api/appdetails` — name, genres, release date, price, Metacritic.

Raw pulls are gitignored; only derived aggregates are committed.

## Scope guards

**In:**
- **19 titles, resolved and name-verified** (`outputs/comparison_set.csv`): colony/management 7,
  grand-strategy/dynasty 3, emergent-narrative 4, life sim 5. Chosen to span the positioning axes a new
  entrant must pick between. **Purposive, not random**, so it characterises this set and does not
  estimate a category population.
- English-language reviews only.
- Up to 1,200 reviews per game via `filter=recent`. 17 of 19 returned exactly 1,200 unique reviews; two
  returned 1,198 after de-duplication. 22,796 total.
- One outcome variable: `voted_up`.
- Segmentation: **sub-genre** (the positioning axis) and **playtime band**. Price tier is dropped: the
  API's `final` price reflects whatever sale is running at pull time, so it is not a stable attribute.

**Out, deliberately:**
- Non-English reviews. I cannot validate coding in languages I do not read.
- Off-the-shelf sentiment scoring. Unvalidated on this text type; the codebook is defensible and the
  sentiment library is not.
- Topic modelling. Eats days and produces categories that cannot be hand-checked.
- Predictive modelling. Adds nothing to the question.
- **Primary survey research.** A concept test recruited from sim-game communities would select on the
  outcome variable: appeal measured among people already filtered for appetite for this genre is not a
  biased estimate, it is an uninterpretable one, and disclosure does not repair it. Everything here runs
  on secondary data and needs no recruitment and no respondents.
- Any paid data source.

## Method

**1. Sampling.** Measured, not assumed. Steam offers no random ordering. `filter=recent` is strict
recency and pages reliably; `filter=all` is helpfulness-weighted and its pagination stalls near 200
reviews. An earlier draft of this scope had these backwards. The sample uses `filter=recent`.

Three consequences, stated plainly rather than buried:

- **It is an equal-N latest-review sample, not a time window.** Coverage runs from 13 days (Stardew
  Valley) to 963 days (My Time at Portia), median 192. Never describe it as "current sentiment".
- **Helpfulness ordering differs from recency ordering** by a median of 1.1 points and a mean of 3.8
  across 16 games, more negative in 10 of 16. Report both; the mean is outlier-driven. This describes
  two orderings; it does not demonstrate a causal effect of sorting.
- **Steam withholds off-topic review-bomb periods by default.** Retained, sensitivity computed per game
  into `outputs/offtopic_sensitivity.csv`. Four games show unambiguous withholding (Factorio +3,355,
  Crusader Kings III +1,194, Europa Universalis IV +624, Victoria 3 +396). Five more differ by 1-3
  reviews, which cannot be separated from ordinary accrual because the two requests were captured 22-59
  minutes apart; those are not counted as affected. Largest absolute rate impact is 0.225pp.

**2. Codebook.** Not a black box. Categories drafted from a 100-review discovery sample, turned into
explicit rules, applied mechanically, then validated against a fresh hand-coded 150. Definitions,
coding rules, authorship and known weaknesses are in `CODEBOOK.md`.

**3. Comparison, not pooled inference.** Reviews are clustered inside games, and a sub-genre holds only
3 to 7 games. The effective N for any sub-genre claim is the game count, not the review count. Pooled
two-proportion tests over reviews would treat thousands of clustered reviews as independent
observations and are **not run**. Report per-game rates and the distribution across games; a sub-genre
difference has to be visible as separation between games, not between pooled percentages.

**4. Unit of analysis.** The **review** is the unit for objection coding. The **game** is the unit for
rates. Never average review-level rates across games without weighting, and say which grain each chart
uses.

## Deliverable

A short deck answering the question, with scope and caveats up front rather than buried, one idea per
slide, and a method appendix carrying the per-category validation metrics.

Charts generated in Python for reproducibility; the deck assembled by hand so it reads as a deliverable
rather than a report dump.

## Acceptance checks

Before any interpretation:

- [x] Schema and types validated on both endpoints
- [x] Duplicate `recommendationid` values removed
- [x] Missingness quantified; timestamp and playtime are zero-tolerance
- [x] Sampled positive rate reconciled against lifetime totals per game
- [x] Games per sub-genre reported as the effective N; no pooled review-level test is run
- [x] Every output hashed into a phase manifest, and verification fails closed when one is missing
- [ ] Per-category precision, recall and F1 computed on the held-out sample
- [ ] Every number in the deck traceable to a script; no hand-typed figures
