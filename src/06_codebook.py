"""Day 2 step 2 - the frozen rule set. See CODEBOOK.md for definitions.

Drafted from the 100 discovery reviews ONLY. The held-out 150 were not opened
before this file was committed, which is what makes the precision and recall
figures in step 3 mean anything.

Rules are deliberately literal. A rule that needs a paragraph of exceptions is a
rule that will not survive hand-validation, and finding that out is the point of
measuring per-category precision rather than asserting a codebook is good.
"""

import re

# Each category maps to a list of regex patterns. Matching is case-insensitive
# on the whole review text. Word boundaries are used to avoid substring traps
# ("grind" must not fire on "grinding gears" as a metaphor is a known risk; it
# is accepted here and will show up as a precision loss if it matters).
RULES = {
    "bugs_crashes": [
        r"\bbugg?(y|ed|s)\b", r"\bbugs\b", r"\bcrash(es|ed|ing)?\b", r"\bglitch",
        r"\bsoft ?lock", r"\bbroken\b", r"\bdoesn'?t work\b", r"\bdon'?t work\b",
        r"\bnot working\b", r"\bgame ?breaking\b", r"\bunplayable\b", r"\bjank",
    ],
    "performance": [
        r"\boptimi[sz]", r"\bunoptimi[sz]", r"\bfps\b", r"\bframerate\b", r"\bframe rate\b",
        r"\blag(gy|s|ging)?\b", r"\bstutter", r"\bruns? (way )?too slow\b", r"\bslow ?down",
        r"\bloading times?\b", r"\bmemory leak\b", r"\bgpu\b", r"\bcpu\b",
    ],
    "ui_controls": [
        r"\bui\b", r"\bu\.?i\.?/?u\.?x\.?\b", r"\bux\b", r"\binterface\b", r"\bcontrols?\b",
        r"\bcamera\b", r"\bhotkey", r"\bkeybind", r"\bmenus?\b", r"\bclunky\b",
        r"\bcumbersome\b", r"\bunintuitive\b",
    ],
    "opacity_teaching": [
        r"\btutorial", r"\bexplain(s|ed|ing)?\b", r"\bopaque\b", r"\bunclear\b",
        r"\bno idea what\b", r"\bdon'?t understand\b", r"\bdoesn'?t tell you\b",
        r"\bwiki\b", r"\buse (a )?guide\b", r"\blook(ing)? (it )?up\b", r"\blearning curve\b",
        r"\bnot explained\b", r"\bconfusing\b",
    ],
    "tedium_grind": [
        r"\bgrind(y|ing)?\b", r"\btedious\b", r"\btedium\b", r"\bslog\b", r"\bchore\b",
        r"\brepetitive\b", r"\bbusywork\b", r"\bbusy work\b", r"\bwaiting\b", r"\bwaste of time\b",
        r"\bmicro ?manag", r"\btoo slow\b", r"\bpacing\b", r"\btime sink\b",
    ],
    "monetization_dlc": [
        r"\bdlcs?\b", r"\bmicrotransaction", r"\bmtx\b", r"\bpaywall", r"\bexpansions?\b",
        r"\bovervalued\b", r"\boverpriced\b", r"\btoo expensive\b", r"\bcash cow\b",
        r"\bmoney grab\b", r"\bpredatory\b", r"\bseason pass\b", r"\bnot worth (the )?(money|price)\b",
        r"\$\d", r"\bprice\b",
    ],
    "unfinished_abandoned": [
        r"\bearly access\b", r"\bunfinished\b", r"\babandon(ed|ing)?\b", r"\balpha\b",
        r"\bbeta\b", r"\btech demo\b", r"\bnot (a )?finished\b", r"\bincomplete\b",
        r"\bhalf ?baked\b", r"\bnot ready\b", r"\bstill in development\b", r"\bpotential\b",
    ],
    "update_regression": [
        r"\bupdates?\b", r"\bpatch(es|ed)?\b", r"\bsince the (last )?(update|patch)\b",
        r"\brollback\b", r"\brevert", r"\bused to be\b", r"\bmade it worse\b",
        r"\bruined\b", r"\bnerf",
    ],
    "npc_ai_pathing": [
        r"\bai\b", r"\ba\.i\.\b", r"\bpathing\b", r"\bpathfind", r"\bnpcs?\b",
        r"\bstuck\b", r"\bcolonists?\b", r"\bpawns?\b", r"\bvillagers?\b", r"\bdwarves\b",
        r"\bstupid\b", r"\bdumb\b",
    ],
    "shallow_repetitive": [
        r"\bshallow\b", r"\bboring\b", r"\bbland\b", r"\bsame ?y\b", r"\blacks? (any )?(depth|flavou?r|content|soul)\b",
        r"\bno (real )?(depth|content|variety|flavou?r)\b", r"\bsoulless\b", r"\bsterile\b",
        r"\bnothing to do\b", r"\bgets old\b", r"\bcookie cutter\b", r"\bspreadsheet\b",
    ],
    "procgen_hollow": [
        r"\bprocedural", r"\bproc ?gen\b", r"\brandomly generated\b", r"\bgenerated (content|stories|quests|cases|events)\b",
        r"\bevents repeat\b", r"\brepeat(ed|ing)? events\b", r"\bno impact\b",
        r"\bdon'?t care about (the )?(characters|npcs)\b", r"\bcan'?t care\b",
        r"\bhandcrafted\b", r"\bhand ?made\b", r"\bauthored\b", r"\btailored\b",
        r"\bdisjointed\b", r"\bcopy ?paste",
    ],
    "rng_unfair": [
        r"\brng\b", r"\brandom(ness|ly)?\b", r"\bluck\b", r"\bdice\b", r"\bgambl",
        r"\bcoin ?flip\b", r"\bunfair\b", r"\bno control over\b",
    ],
    "difficulty_punishing": [
        r"\bunforgiving\b", r"\bpunishing\b", r"\btoo hard\b", r"\bbrutal\b",
        r"\bwithout warning\b", r"\bno warning\b", r"\binstant(ly)? (death|lose|fail)",
        r"\bdifficulty\b", r"\btrial and error\b",
    ],
    "developer_conduct": [
        r"\bdevs?\b", r"\bdeveloper", r"\bpublisher\b", r"\bparadox\b", r"\bea\b",
        r"\bgreed(y)?\b", r"\bcommunity manage", r"\bdiscord mod", r"\bignore(s|d)? (the )?community\b",
        r"\bdon'?t listen\b", r"\bdoesn'?t listen\b",
    ],
    "taste_mismatch": [
        r"\bnot my (cup of tea|style|thing|kind)\b", r"\bnot for me\b",
        r"\bjust didn'?t click\b", r"\bcould not click\b", r"\bcouldn'?t get into\b",
        r"\bpersonal preference\b",
    ],
}

# Exclusive: if a review is non-substantive nothing else is coded.
NON_SUBSTANTIVE_MAX_WORDS = 4
NON_SUBSTANTIVE_PATTERNS = [r"^meh\.?$", r"^\W*$", r"^no+\.?$", r"^bad\.?$", r"^good\.?$"]

COMPILED = {c: [re.compile(p, re.I) for p in pats] for c, pats in RULES.items()}
NS = [re.compile(p, re.I) for p in NON_SUBSTANTIVE_PATTERNS]


def code(text: str):
    """Return the sorted list of category codes a review's text supports."""
    t = (text or "").strip()
    if len(t.split()) <= NON_SUBSTANTIVE_MAX_WORDS or any(p.match(t) for p in NS):
        return ["non_substantive"]
    hits = [c for c, pats in COMPILED.items() if any(p.search(t) for p in pats)]
    return sorted(hits) if hits else ["uncoded"]


CATEGORIES = sorted(RULES) + ["non_substantive", "uncoded"]
