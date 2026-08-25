#!/usr/bin/env python3
"""Figures for the capstone (What Someone Can Keep), regenerated
from the same CSVs as the text's numbers. Outputs to paper/figs/:

  kept-units.pdf    EW-11: per-sector survival by genome and arm
                    (the 0/400 wall, the outsourcing inversion)
  kept-linkage.pdf  EW-9 + EW-10: faithful share across
                    environments and linkage arms
  kept-code.pdf     EW-8: survival by code arm; the mosaic drifts

Print conventions as fig_ow.py / fig_ew.py.
"""
import csv
import math
import statistics
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).parent
FIGS = HERE.parents[1] / "paper" / "figs"
FIGS.mkdir(parents=True, exist_ok=True)

BLUE, ORANGE, GREEN, GRAY = "#0072B2", "#D55E00", "#009E73", "#666666"


def style(ax):
    ax.grid(True, color="#dddddd", linewidth=0.6, zorder=0)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)


def ci95(k, n):
    p = k / n
    return 1.96 * math.sqrt(p * (1 - p) / n)


def fig_units():
    rows = list(csv.DictReader(open(HERE / "ew11_runs.csv")))
    cells = []                      # (label, k, n, color)
    for arm, genome, label, col in (
            ("walls-faithful", "b", "faithful\nisolated", GRAY),
            ("walls-sloppy", "p", "sloppy\nisolated", BLUE),
            ("walls-mixed", "p", "sloppy\nmixed+walls", BLUE),
            ("walls-mixed", "b", "faithful\nmixed+walls", ORANGE),
            ("open-mixed", "p", "sloppy\nopen", GREEN),
            ("open-mixed", "b", "faithful\nopen", GREEN)):
        k = n = 0
        for r in rows:
            if r["arm"] != arm:
                continue
            for s in range(4):
                if r[f"genome{s}"] == genome:
                    n += 1
                    k += int(r[f"surv{s}"])
        cells.append((label, k, n, col))
    fig, ax = plt.subplots(figsize=(4.9, 3.0))
    for i, (label, k, n, col) in enumerate(cells):
        p = k / n
        ax.bar(i, p, color=col, width=0.62, zorder=3)
        ax.errorbar(i, p, yerr=ci95(k, n), color="#333333", capsize=3,
                    lw=1.0, zorder=4)
        ax.annotate(f"{k}/{n}", xy=(i, p), xytext=(i, p + 0.04),
                    ha="center", fontsize=7.5, color="#333333")
    ax.set_xticks(range(len(cells)))
    ax.set_xticklabels([c[0] for c in cells], fontsize=7.5)
    ax.set_ylabel("sector survival")
    ax.set_ylim(0, 1.12)
    ax.annotate("the outsourcing inversion", xy=(2.5, 0.30),
                ha="center", fontsize=8, color=ORANGE)
    style(ax)
    fig.tight_layout()
    fig.savefig(FIGS / "kept-units.pdf")
    plt.close(fig)


def fig_linkage():
    pts = []                        # (label, mean, ci, color)
    for path, arm, label, col in (
            ("ew9_runs.csv", "neutral", "neutral", GRAY),
            ("ew9_runs.csv", "deleterious", "deleterious", BLUE),
            ("ew9_runs.csv", "beneficial", "beneficial\n(public)", GRAY),
            ("ew10_runs.csv", "viscous", "beneficial\nviscous", GRAY),
            ("ew10_runs.csv", "kin", "beneficial\nkin-gated", ORANGE),
            ("ew10_runs.csv", "viscous-kin", "viscous\n+kin", ORANGE),
            ("ew10_runs.csv", "invade-public", "invasion\npublic", GREEN),
            ("ew10_runs.csv", "invade-kin", "invasion\nkin", GREEN)):
        shares = [float(r["share_f"])
                  for r in csv.DictReader(open(HERE / path))
                  if r["arm"] == arm and r["share_f"]]
        m = statistics.mean(shares)
        ci = 1.96 * statistics.stdev(shares) / math.sqrt(len(shares))
        pts.append((label, m, ci, col))
    fig, ax = plt.subplots(figsize=(4.9, 3.0))
    for i, (label, m, ci, col) in enumerate(pts):
        ax.errorbar(i, m, yerr=ci, color=col, marker="o", ms=5,
                    capsize=3, lw=1.2, zorder=3)
    ax.axhline(0.5, color="#bbbbbb", lw=0.8, zorder=1)
    ax.set_xticks(range(len(pts)))
    ax.set_xticklabels([p[0] for p in pts], fontsize=7)
    ax.set_ylabel("faithful lineage share")
    ax.set_ylim(0.1, 0.72)
    ax.annotate("drift", xy=(0.05, 0.51), fontsize=8, color=GRAY)
    ax.annotate("faithful favoured", xy=(0.7, 0.63), fontsize=8,
                color=BLUE)
    ax.annotate("mutator favoured", xy=(3.6, 0.17), fontsize=8,
                color=ORANGE)
    style(ax)
    fig.tight_layout()
    fig.savefig(FIGS / "kept-linkage.pdf")
    plt.close(fig)


def fig_code():
    rows = list(csv.DictReader(open(HERE / "ew8_runs.csv")))
    arms = [("baseline", "intact code"), ("closure", "wounded,\nx-closure"),
            ("no-x", "wounded,\nno closure"), ("mosaic", "mosaic,\nwounded"),
            ("pure2", "swapped\ncode")]
    cols = [BLUE, BLUE, GRAY, ORANGE, GRAY]
    fig, ax = plt.subplots(figsize=(4.9, 3.0))
    for i, (arm, label) in enumerate(arms):
        sub = [r for r in rows if r["arm"] == arm]
        k = sum(1 for r in sub if r["survived"] == "True")
        p = k / len(sub)
        ax.bar(i, p, color=cols[i], width=0.62, zorder=3)
        ax.errorbar(i, p, yerr=ci95(k, len(sub)), color="#333333",
                    capsize=3, lw=1.0, zorder=4)
        ax.annotate(f"{k}", xy=(i, p), xytext=(i, p + 0.04),
                    ha="center", fontsize=8, color="#333333")
    shares = [float(r["t1_share"]) for r in rows
              if r["arm"] == "mosaic" and r["t1_share"]]
    ax.annotate(f"mosaic code share {statistics.mean(shares):.3f}"
                f" ± {statistics.stdev(shares):.3f}: pure drift",
                xy=(2.1, 0.86), fontsize=8, color=ORANGE)
    ax.set_xticks(range(len(arms)))
    ax.set_xticklabels([a[1] for a in arms], fontsize=7.5)
    ax.set_ylabel("worlds surviving (of 100)")
    ax.set_ylim(0, 1.0)
    style(ax)
    fig.tight_layout()
    fig.savefig(FIGS / "kept-code.pdf")
    plt.close(fig)


if __name__ == "__main__":
    fig_units()
    fig_linkage()
    fig_code()
    print("figures written to", FIGS)
