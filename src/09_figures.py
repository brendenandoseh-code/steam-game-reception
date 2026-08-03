"""Day 3 step 1 - figures.

Every chart here reports something the data collection established and the
validation does not depend on. Charts of objection rates are deliberately
absent: those rest on an unvalidated codebook and would imply a finding the
project has not yet earned.

Each figure states its own unit of analysis in the subtitle, because the single
easiest way to mislead with this dataset is to draw a review-level chart and let
a reader think it is a game-level one.
"""

import csv
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from steam import ROOT  # noqa: E402

OUT, FIG = ROOT / "outputs", ROOT / "visuals"
FIG.mkdir(exist_ok=True)

INK, MUTED, ACCENT, WARN = "#1F3355", "#8A94A6", "#2E6F9E", "#B4553C"
plt.rcParams.update({"font.size": 9, "axes.edgecolor": MUTED, "axes.labelcolor": INK,
                     "text.color": INK, "xtick.color": MUTED, "ytick.color": MUTED,
                     "axes.spines.top": False, "axes.spines.right": False,
                     "figure.facecolor": "white", "axes.facecolor": "white"})


def frame(ax, title, subtitle):
    ax.set_title(title, loc="left", fontsize=12, fontweight="bold", color=INK, pad=18)
    ax.text(0, 1.02, subtitle, transform=ax.transAxes, fontsize=8.5, color=MUTED, va="bottom")


def rows(name):
    return list(csv.DictReader(open(OUT / name, encoding="utf-8")))


def fig_coverage():
    d = sorted(rows("temporal_coverage.csv"), key=lambda r: int(r["days"]))
    fig, ax = plt.subplots(figsize=(8, 4.6))
    y = range(len(d))
    ax.barh(list(y), [int(r["days"]) for r in d], color=[WARN if int(r["days"]) > 365 else ACCENT for r in d], height=.62)
    ax.set_yticks(list(y)); ax.set_yticklabels([r["name"][:26] for r in d], fontsize=8)
    ax.set_xlabel("days spanned by that game's 1,200 most recent English reviews")
    frame(ax, "The same sample size covers wildly different time windows",
          "unit: game (n=19). Equal-N latest reviews, not a shared calendar window.")
    ax.axvline(365, color=MUTED, ls=":", lw=1)
    ax.text(372, .4, "1 year", fontsize=7.5, color=MUTED)
    fig.tight_layout(); fig.savefig(FIG / "01_temporal_coverage.png", dpi=200); plt.close(fig)


def fig_sampling_bias():
    d = sorted(rows("sampling_bias.csv"), key=lambda r: float(r["delta"]))
    fig, ax = plt.subplots(figsize=(8, 4.4))
    vals = [float(r["delta"]) * 100 for r in d]
    ax.barh(range(len(d)), vals, color=[WARN if v < 0 else ACCENT for v in vals], height=.62)
    ax.set_yticks(range(len(d))); ax.set_yticklabels([r["name"][:26] for r in d], fontsize=8)
    ax.axvline(0, color=INK, lw=.9)
    ax.set_xlabel("percentage points: first helpfulness-ranked page minus same-N most recent")
    frame(ax, "Which ordering you pull changes the answer",
          "unit: game (n=16 comparable). Descriptive difference between two orderings, not a causal effect.")
    fig.tight_layout(); fig.savefig(FIG / "02_sampling_bias.png", dpi=200); plt.close(fig)


def fig_reconciliation():
    d = rows("denominators.csv")
    fig, ax = plt.subplots(figsize=(7.4, 4.6))
    for r in d:
        s, l = float(r["sampled_pos_rate"]) * 100, float(r["lifetime_pos_rate_english"]) * 100
        ax.plot([l, s], [r["name"][:24]] * 2, color=MUTED, lw=1, zorder=1)
        ax.scatter(l, r["name"][:24], s=26, color=ACCENT, zorder=2)
        ax.scatter(s, r["name"][:24], s=26, color=WARN, zorder=2)
    ax.tick_params(axis="y", labelsize=8)
    ax.set_xlabel("% of reviews positive")
    frame(ax, "The sample runs harsher than the lifetime record for 17 of 19 games",
          "unit: game. Blue = lifetime English rate; orange = this sample. Compatible with sentiment change,\n"
          "but inseparable from unequal time coverage and non-random ordering.")
    fig.tight_layout(); fig.savefig(FIG / "03_reconciliation.png", dpi=200); plt.close(fig)


def fig_clustering():
    d = rows("category_rates.csv")
    seg = {}
    for r in d:
        seg.setdefault(r["axis"], []).append((r["name"], int(r["n_negative"])))
    fig, ax = plt.subplots(figsize=(7.4, 3.8))
    order = ["colony", "grand", "emergent", "life"]
    for i, a in enumerate(order):
        games = seg[a]
        ax.scatter([i] * len(games), [g[1] for g in games], s=54, color=ACCENT, zorder=3)
        ax.text(i, -260, f"{len(games)} games", ha="center", fontsize=8.5, color=INK, fontweight="bold")
    ax.set_xticks(range(len(order))); ax.set_xticklabels(order)
    ax.set_ylabel("negative reviews in sample")
    ax.set_ylim(-380, None)
    frame(ax, "Sub-genre claims rest on 3 to 7 games, not thousands of reviews",
          "unit: game. Reviews are clustered inside titles, so the game count is the effective N.\n"
          "Pooled review-level tests would be badly overconfident and are not run.")
    fig.tight_layout(); fig.savefig(FIG / "04_clustering.png", dpi=200); plt.close(fig)


def fig_supported_finding():
    """The one finding validation supports: which objection you inherit depends
    on which shelf you position on. Only the three categories that cleared
    validation are shown."""
    d = rows("supported_finding_by_game.csv")
    cats = [("bugs_crashes", "Bugs and crashes", "does not vary by shelf"),
            ("tedium_grind", "Grind and pacing", "3.0x, worst in life sims"),
            ("ui_controls", "Interface and controls", "2.6x, worst in emergent narrative")]
    order = ["colony", "emergent", "grand", "life"]
    labels = {"colony": "colony /\nmanagement", "emergent": "emergent\nnarrative",
              "grand": "grand\nstrategy", "life": "life sim"}
    fig, axs = plt.subplots(1, 3, figsize=(10.5, 4.2), sharey=True)
    for ax, (key, title, note) in zip(axs, cats):
        for i, a in enumerate(order):
            vals = sorted(float(r[key]) * 100 for r in d if r["sub_genre"] == a)
            ax.scatter([i] * len(vals), vals, s=44, color=ACCENT, zorder=3, alpha=.85)
            n = len(vals)
            med = vals[n // 2] if n % 2 else (vals[n // 2 - 1] + vals[n // 2]) / 2
            ax.plot([i - .26, i + .26], [med, med], color=WARN, lw=2.2, zorder=4)
        ax.set_xticks(range(len(order)))
        ax.set_xticklabels([labels[a] for a in order], fontsize=7.5)
        ax.set_xlim(-.5, len(order) - .5)
        ax.set_title(title, fontsize=9.5, color=INK, loc="left", pad=14)
        ax.text(0, 1.008, note, transform=ax.transAxes, fontsize=7.5, color=MUTED, va="bottom")
    axs[0].set_ylabel("% of that game's negative reviews")
    axs[0].set_ylim(0, None)
    fig.suptitle("The objection you inherit depends on which shelf you sit on",
                 x=.012, y=.985, ha="left", fontsize=12, fontweight="bold", color=INK)
    fig.text(.012, .93,
             "unit: game (each dot is one title, orange bar is the sub-genre median). Only the three "
             "categories that\ncleared validation are shown. Rates understate: the rules miss real cases.",
             fontsize=8.5, color=MUTED, va="top")
    fig.tight_layout(rect=(0, 0, 1, .86))
    fig.savefig(FIG / "05_supported_finding.png", dpi=200); plt.close(fig)


if __name__ == "__main__":
    fig_supported_finding()
    fig_supported_finding()
    fig_coverage(); fig_sampling_bias(); fig_reconciliation(); fig_clustering()
    for p in sorted(FIG.glob("*.png")):
        print(f"  {p.name}  {p.stat().st_size//1024} KB")
    print(f"\n{len(list(FIG.glob('*.png')))} figures -> visuals/")
    print("Objection rates shown ONLY for the three categories that cleared validation.")
