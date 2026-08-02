# Scope — Steam game reception study

**Status:** Day 1 complete 2026-08-02, dataset frozen (`outputs/freeze_manifest.json`). Day 2 not started.
**Purpose:** close three documented gaps in the portfolio before an NRG interview. Does not block the application, which goes in first.

## Why this project exists

The NRG application has three honest gaps that a single project can close:

| Gap | Why it matters here | How this closes it |
|---|---|---|
| **No entertainment-domain work.** All five existing projects are healthcare or public health. | The role sits in Entertainment, Gaming, Sports & Tech. A reviewer has to take on faith that the skills transfer. | Gaming data, gaming question. |
| **No deck.** Portfolio is Tableau dashboards and READMEs. | The actual deliverable of this job is a client presentation. The posting names PowerPoint and Google Slides and puts "highly visual, creative and story-driven presentations" in two separate bullets. | The primary artifact is a PowerPoint deck, not a dashboard. |
| **No unstructured data.** All five projects use structured CSV, claims, or survey data. | "You're comfortable working with structured and unstructured data" is a stated requirement, and `APPLICATION_BRIEF.md` records this as a claim he currently cannot make. | Review free text is the core input. |

## Revision 2026-08-02, after a competing scope proposal

A second proposal was reviewed and two of its points are adopted.

**Adopted: name a method from the posting.** The original scope invented its own format. The posting lists the methods this team runs by name — "concept evaluation, brand studies, content optimization tests, messaging/positioning evaluation, creative materials tests, market sizing and segmentation." The project should be one of those, in their vocabulary, so a reviewer does not have to translate. This is now framed as a **messaging/positioning evaluation with segmentation**.

**Adopted: QOS as category anchor.** The comparison set is the sim/colony/life-sim category QOS would enter (Dwarf Fortress, RimWorld, Crusader Kings III, Caves of Qud, Kenshi, The Sims). QOS supplies the business question and stays out of the findings, which keeps this a work sample rather than a pitch deck.

**Rejected: the primary survey phase.** The proposal suggested a monadic concept test recruited via Prolific (~$400-600) or free from gaming subreddits and Discord "if you state the bias explicitly." Rejected on both options:

- A convenience sample drawn from sim-game communities **selects on the outcome variable**. Appeal and purchase intent measured among people already filtered for appetite for this genre is not a biased estimate, it is an uninterpretable one, and disclosure does not repair it. Recruiting where Brenden is known adds a demand characteristic.
- $400-600 is poor return on a single application.
- k-means for 4-5 segments at n=200 is thin, and segment stability would have to be defended to people who do this professionally.

Primary research is deferred until an interview is scheduled and a defensible sampling frame exists. **Everything below runs on secondary data and needs no recruitment, no budget, and no respondents.**

**Sequencing note.** The single highest-value artifact is not this project. It is a short writeup of the AI-validation method already documented in `QOS/design/research/METHOD_AND_RUBRIC.md` (evidence bar, unverified-context ledger, reproducible search logs preserving rejected sources and failed searches, triangulation across two independently-checked source families, mandatory adversarial source, WEIRD-bias audit). That maps directly onto the posting's AI Fluency requirement, requires almost no new work, and almost no entry-level applicant can produce anything comparable. Do that first.

## The question

> A review score tells a publisher **that** players are unhappy, not **why**. Across the established simulation category, what do players in negative reviews actually object to, how do those objections differ by sub-genre, and what does that imply about the positioning risks facing a new entrant?

Framed in the posting's own terms: a **messaging/positioning evaluation** built on the voice of the consumer already present in public review text.

**Narrowed 2026-08-02.** An earlier version promised both praise and objections while the codebook only ever coded negative reviews. Objections alone is the honest three-day scope and is the more useful half for a positioning question.

## Data (both endpoints verified working 2026-08-02, no API key required)

**Reviews** — `https://store.steampowered.com/appreviews/{appid}?json=1`
Confirmed fields: `review` (free text), `voted_up` (recommend / not), `author.playtime_at_review` and `author.playtime_forever` (minutes), `timestamp_created`, `written_during_early_access`, `received_for_free`, `steam_purchase`, `refunded`, `votes_up`, `weighted_vote_score`.
`query_summary` returns `total_reviews`, `total_positive`, `total_negative` per game, which are the correct denominators.

**Game metadata** — `https://store.steampowered.com/api/appdetails?appids={appid}&cc=us`
Confirmed fields: `name`, `genres`, `release_date`, `price_overview` (current and initial, in cents), `metacritic.score`, `categories`.

Public, documented, no authentication, no scraping, no terms-of-service problem. Raw pulls are gitignored; only derived aggregates are committed.

## Scope guards

Fixed up front so the project finishes in days rather than becoming open-ended.

**In:**
- **The simulation category comparison set: 19 titles, resolved and name-verified** (`outputs/comparison_set.csv`). Colony/management 7, grand-strategy/dynasty 3, emergent-narrative 4, life sim 5. Chosen to span the positioning axes a new entrant must pick between. **Purposive, not random**, so it characterises this set and does not estimate a category population.
- English-language reviews only
- Up to 1,200 reviews per game via `filter=recent`. 17 of 19 games returned exactly 1,200 unique reviews; two returned 1,198 after de-duplication. 22,796 total.
- One outcome variable: `voted_up`
- Segmentation: **sub-genre** (the positioning axis) and **playtime band**. Price tier is dropped: the API's `final` price reflects whatever sale is running at pull time, so it is not a stable attribute.

**Out, deliberately:**
- Non-English reviews. Cannot validate the coding, so excluded and stated as a limitation.
- Off-the-shelf sentiment scoring. Unvalidated on this text type; the codebook below is defensible and the sentiment library is not.
- Topic modeling (LDA and similar). Eats days and produces categories that cannot be hand-checked.
- Predictive modeling. Adds nothing to the question.
- Any paid data source.

## Method

**1. Sampling.** Measured, not assumed. Steam offers no random ordering. `filter=recent` is strict recency and pages reliably; `filter=all` is helpfulness-weighted and its pagination stalls near 200 reviews. An earlier draft of this scope had these backwards. The sample uses `filter=recent`.

Three consequences to state on the slide, not bury:

- **It is an equal-N latest-review sample, not a time window.** Coverage runs from 13 days (Stardew Valley) to 963 days (My Time at Portia), median 192. Never describe it as "current sentiment" across the category.
- **Helpfulness ordering differs from recency ordering** by a median of 1.1 points and a mean of 3.8 across 16 games, more negative in 10 of 16. Report both statistics; the mean is outlier-driven. This is a description of two orderings, not a demonstrated causal effect of sorting.
- **Steam withholds off-topic review-bomb periods by default.** Retained, and the sensitivity is computed per game into `outputs/offtopic_sensitivity.csv`, not asserted. **Four** games show unambiguous withholding (Factorio +3,355, Crusader Kings III +1,194, Europa Universalis IV +624, Victoria 3 +396). Five more differ by only 1-3 reviews, which cannot be separated from ordinary review accrual because the default and included requests were captured 22-59 minutes apart; those are not counted as affected. Largest absolute rate impact across the set is 0.225pp.

**2. Codebook, hand-validated.** Not a black box:

1. Read a random 100 negative reviews and draft objection categories (performance and bugs, price and value, difficulty and balance, content volume, monetization, story and writing, controls and UI, etc.)
2. Turn each category into explicit keyword and phrase rules
3. Apply the rules across the full sample

Step 4 is the point. Per-category precision and recall are what separate defensible coding from asserted categories.

**Freeze before reading.** The discovery sample IDs, the held-out sample IDs, the random seed, and the stratification are written to `outputs/` *before* any review text is read, so the codebook cannot be tuned to the held-out set.

**3. Comparison, not pooled inference.** Reviews are clustered inside games, and a sub-genre holds only 3 to 7 games. The effective N for any sub-genre claim is therefore the game count, not the review count. Pooled two-proportion tests over reviews would treat 4,798 clustered reviews as 4,798 independent observations and are **not run**. Report per-game objection rates and the distribution across games; if a sub-genre difference is claimed, it has to be visible as a separation between games, not between pooled percentages.

**4. Unit of analysis.** The classic error here is mixing grains. The **review** is the unit for objection coding. The **game** is the unit for reception rates. Never average review-level rates across games without weighting, and say which grain each chart uses.

## Deliverable

A 10 to 12 slide PowerPoint deck, which is the artifact this project exists to produce.

1. Title
2. The question and why a publisher would care
3. What was analyzed, with scope and caveats stated **up front**, not buried
4. Headline finding
5-7. Supporting findings, one idea per slide
8. Where segments genuinely differ
9. Where they do not, stated plainly
10. So what: what a publisher should do differently
11. Limitations

Charts generated in Python for reproducibility; deck assembled in PowerPoint so it actually looks like a client deliverable. A programmatically generated deck reads as generic, and visual craft is being assessed here.

Repository also carries a README matching the existing five, and a `## How I used AI` section consistent with `ANALYST_OPERATING_SYSTEM.md` §13.

## Acceptance checks

Per `ANALYST_OPERATING_SYSTEM.md`, before any interpretation:

- [ ] Schema and types validated on both endpoints
- [ ] Duplicate `recommendationid` values removed
- [ ] Missingness quantified for playtime and review text (price is excluded from the analysis)
- [ ] Sampled positive rate reconciled against `query_summary` totals per game
- [ ] Unit of analysis labeled on every chart
- [ ] Games per sub-genre reported as the effective N; no pooled review-level test is run
- [ ] Per-category precision, recall and F1 computed on the held-out sample and stated in the deck
- [ ] Every number in the deck traceable to a script, no hand-typed figures

## Timeline

Three working days.

- **Day 1** — pull, validate, reconcile against `query_summary`, freeze the dataset
- **Day 2** — draft codebook, apply, hand-validate on the held-out sample, run tests
- **Day 3** — charts, deck, README, repository

## Risks

- **Rate limiting.** Steam throttles. Mitigation: cache every response to disk, back off, and never re-pull.
- **Codebook drift.** Categories invented after seeing results are not findings. Mitigation: freeze the codebook before applying it to the full sample.
- **Scope creep into modeling.** Mitigation: the "Out" list above is binding.
- **Finding nothing surprising.** Acceptable. A clean null with honest confidence intervals is a legitimate result and is more credible than a manufactured headline.

## Open decision

Gaming (Steam) is the recommendation: NRG names it as a sector, the data is richest, and Brenden has genuine domain fluency. Film and TV via MovieLens is the alternative, but it has ratings and tags rather than review text, which would forfeit the unstructured-data gap this project is partly meant to close.
