# Objection codebook v1

**Drafted 2026-08-02 from the 100 discovery reviews only.** The held-out 150 have not been opened.
Frozen at commit time: once applied to the full negative sample, categories and rules are not revised.
If v1 performs badly on a category, that is reported as a v1 result, not patched away.

**Multi-label.** A review can object to several things. Most do.

## Categories

| Code | Definition | Discovery evidence |
|---|---|---|
| `bugs_crashes` | Things do not work: crashes, softlocks, broken quests, defects | "buggy shambles... game ending crashes"; "constantly crashed cant even play" |
| `performance` | Framerate, optimisation, load times, late-game slowdown | "completely UNoptimized... by cycle 800 entirely unplayable"; "uses 99% of my GPU" |
| `ui_controls` | Interface, controls, camera, input, on-screen readability | "controls and UI/UX worse than in the pre-steam version"; "Horrible UI" |
| `opacity_teaching` | Systems unexplained; tutorial inadequate; needs an external wiki | "you have to use guide or internet to play this game"; "mechanics aren't explained at all" |
| `tedium_grind` | Grind, pacing, waiting, busywork, disrespect for player time | "waiting endlessly for in-game craft times"; "poorly designed grind" |
| `monetization_dlc` | Price, DLC volume or cost, microtransactions, value for money | "costs more than $100 when you factor in DLC"; "pay over $1000" |
| `unfinished_abandoned` | Ships incomplete, early access abused, development stopped | "abandoned the game in a horribly unfinished state"; "25 dollar tech demo" |
| `update_regression` | A patch or update made the game worse | "After playing more hours with the new patch... the AI is worse"; "1.13 simply isn't working" |
| `npc_ai_pathing` | Agent behaviour: pathing, stuck loops, incompetent or cheating AI | "farmers would rather move rocks than harvest their fields"; "stuck in a loop of climbing a ladder" |
| `shallow_repetitive` | Lacks depth or variety; every session plays the same | "sterile, soulless spreadsheet simulator"; "every job boils down to breaking into homes" |
| `procgen_hollow` | **Procedurally generated content feels disjointed, impersonal, or unearned** | "storytelling feels odd and disjointed due to the procedural generation elements... Events repeat and have no impact"; "it's clear why immersive sims are often tailored and designed and not RNG" |
| `rng_unfair` | Outcomes feel arbitrary rather than earned | "battles are literally gambling doesn't matter if you have 100k men against 10k" |
| `difficulty_punishing` | Unforgiving, punishing, failure without warning | "colony will collapse... without warning"; "the game is seriously unforgiving" |
| `developer_conduct` | Publisher or community-management behaviour, not the product | "Discord mods are absolute trash"; "predatory DLC policies" |
| `taste_mismatch` | Explicitly not for this player; no defect claimed | "Not my cup of tea"; "This game is just a little too micro-managey for me" |
| `non_substantive` | Joke, gibberish, or no codeable objection | "Oxygen was included. Misleading title."; "Meh" |

## Why `procgen_hollow` is separated from `shallow_repetitive`

They co-occur but are not the same objection, and the difference is the whole point of the study.
`shallow_repetitive` says there is not enough content. `procgen_hollow` says the content is generated
and that the generation is *visible*: events that repeat without consequence, characters who cannot be
cared about, cases that could not have been authored. A game whose pitch is procedural narrative is
exposed to the second in a way it is not to the first.

## Coding rules

1. Code what the reviewer objects to, not what they liked.
2. Multi-label. Apply every category the text supports.
3. `taste_mismatch` only when no defect is alleged. If they say it is tedious *and* not for them,
   code `tedium_grind` too.
4. `non_substantive` is exclusive. If it applies, nothing else does.
5. Sarcasm counts as the objection it implies ("great 25 dollar tech demo" is `unfinished_abandoned`).
6. Objections about the publisher rather than the software are `developer_conduct`, even when angry
   about price. Price itself is `monetization_dlc`. Both can apply.
7. Ambiguity is resolved toward *not* coding. A category needs affirmative textual support.

## Authorship

**This is an AI-drafted candidate codebook.** An AI assistant read the discovery sample, proposed the
categories, and wrote the rules. I validate it by hand-coding the held-out 150 and I own every
interpretation drawn from it. It is not described as analyst-authored anywhere.

## Validation plan

Rules are applied mechanically to all eligible negative reviews. The held-out 150 are then hand-coded
by me, blind to machine predictions and to game and sub-genre, on identical untruncated text.
Reported per category: TP, FP, FN, human-positive support, machine-positive support, precision, recall
and F1. A single pooled agreement rate is not reported, because the categories are multi-label and
unevenly frequent, so one number would be inflated by the common ones and hide the ones that failed.

**Sparse categories will be inconclusive and are labelled that way.** `procgen_hollow` has only 4
machine-positives in the held-out 150, so precision for it rests on a handful of reviews no matter how
carefully they are coded. Recall may be estimable if the human finds more; precision will not be.

## Known weakness in v1, recorded before validation

Of the 76 `procgen_hollow` matches across the full negative sample, 68 mention generation explicitly
and **8 match only on generic phrases** (`copy paste`, `no impact`) that carry no claim about
generation at all. The rule therefore over-matches, and the category as currently operationalised
measures *rule firing*, not the semantic definition above. This is stated before validation rather
than discovered by it.
