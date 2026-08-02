# Scope

**Status:** in progress. Data collection complete and frozen (`outputs/freeze_manifest.json`). Codebook v1
drafted and applied. The blinded held-out sheet is built and awaiting hand-coding, so **no validated
metrics exist yet and no conclusions are published**. The repository is public from this point so the
method can be checked before the results exist, not after.

## Why this project exists

I am building a game where a generated world runs for centuries on its own and the ordinary lives
inside it accumulate into history. The bet underneath it is that a simulation can produce a life worth
reading about without an author writing that life in advance. If the bet is wrong, none of the rest of
the design matters.

The failure I actually worry about is not that the simulation breaks. It is that it works exactly as
specified and produces a sequence of events rather than a story: things happen, they are recorded
correctly, and nobody cares. My own build is the worst possible place to test that, because I already
know what every event was supposed to mean. I cannot read my own output cold.

What I can do is look at players who have already run into this in shipped games. Several titles in
this category sell generated narrative as the point, and the players who bounced off them wrote down
why, unprompted, at length, in public. That is a large body of reaction to the exact risk I am
carrying, produced by people with no stake in my project.

The question is whether generated content draws a **distinct** objection at all, or whether players
complain about the same things they complain about everywhere: bugs, grind, price, opacity, an
interface that fights them. The two answers point at different work. If the objection is distinct and
common, generation quality has to clear a bar before anything else gets built on top of it. If it is
rare, or if it turns out to be indistinguishable from ordinary complaints that a game is thin, then the
real risk sits somewhere else and I have been guarding the wrong thing.

I would prefer one of those answers, which is why the guards in the next section exist.

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
