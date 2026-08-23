#!/usr/bin/env python3
"""Figures for paper #4 (Machinery That Earns the Channels),
regenerated from the same CSVs as the text's numbers. Outputs to
paper/figs/:

  ew-bandwidth.pdf  EW-1: convergence to F3's outcome distribution
                    in machinery cadence (the bandwidth limit)
  ew-scarcity.pdf   EW-3: alpha win share among decided runs per
                    regime (saturation null -> 99:1)
  ew-rescue.pdf     EW-4: rescue probability vs miscopy rate
  ew-kernel.pdf     EW-5: survival by arm (the self-reference
                    ordering + description-wound doses)

Print conventions as fig_ow.py: single axis, fixed series order,
CVD-safe hues, line-style+marker secondary encoding, recessive
grid, direct labels.
"""
import csv
import math
from collections import Counter, defaultdict
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


def fig_bandwidth():
    rows = list(csv.DictReader(open(HERE / "ew1_runs.csv")))
    modal = {}
    for g in "αβγδ":
        f3 = Counter(r["outcome"] for r in rows
                     if r["glyph"] == g and r["arm"] == "f3")
        modal[g] = f3.most_common(1)[0][0]
    cads = [1, 2, 4, 8, 16, 32]
    fig, ax = plt.subplots(figsize=(4.6, 3.0))
    series = (("β", BLUE, "-", "o"), ("γ", ORANGE, "--", "s"),
              ("α", GREEN, ":", "^"))
    for g, col, ls, mk in series:
        ys, es = [], []
        for c in cads:
            sub = [r for r in rows if r["glyph"] == g
                   and r["arm"] == "f4sat" and int(r["cad"]) == c]
            k = sum(1 for r in sub if r["outcome"] == modal[g])
            ys.append(k / len(sub))
            es.append(ci95(k, len(sub)))
        ax.errorbar(cads, ys, yerr=es, color=col, ls=ls, marker=mk,
                    ms=4, lw=1.4, capsize=2, zorder=3, label=g)
        f3sub = [r for r in rows if r["glyph"] == g and r["arm"] == "f3"]
        k3 = sum(1 for r in f3sub if r["outcome"] == modal[g])
        ax.axhline(k3 / len(f3sub), color=col, lw=0.7, alpha=0.45,
                   zorder=1)
    ax.set_xscale("log", base=2)
    ax.set_xticks(cads)
    ax.set_xticklabels([str(c) for c in cads])
    ax.set_ylim(-0.04, 1.09)
    ax.set_xlabel("machinery cadence (C bytes per matter byte)")
    ax.set_ylabel("share of runs at F3's modal outcome")
    ax.annotate("β (dyn. repairer)", xy=(16, 1.0), xytext=(4.3, 0.86),
                color=BLUE, fontsize=8)
    ax.annotate("γ (lottery walker)", xy=(16, 0.575),
                xytext=(14, 0.44), color=ORANGE, fontsize=8)
    ax.annotate("α (static repairer)", xy=(2, 1.0), xytext=(1.0, 0.93),
                color=GREEN, fontsize=8)
    ax.annotate("thin lines: F3 authored-stamp reference",
                xy=(1, 0.02), color=GRAY, fontsize=7)
    style(ax)
    fig.tight_layout()
    fig.savefig(FIGS / "ew-bandwidth.pdf")
    plt.close(fig)


def fig_scarcity():
    rows = list(csv.DictReader(open(HERE / "ew3_runs.csv")))
    regimes = ["abundant", "mid", "scarce"]
    fig, ax = plt.subplots(figsize=(4.6, 3.0))
    series = (("free", BLUE, "-", "o"), ("taxed", ORANGE, "--", "s"),
              ("both", GRAY, ":", "^"))
    xs = range(len(regimes))
    for arm, col, ls, mk in series:
        ys, es = [], []
        for reg in regimes:
            sub = [r for r in rows if r["arm"] == arm
                   and r["regime"] == reg]
            wa = sum(1 for r in sub if r["winner"] == "α")
            wb = sum(1 for r in sub if r["winner"] == "β")
            ys.append(wa / (wa + wb))
            es.append(ci95(wa, wa + wb))
        ax.errorbar(xs, ys, yerr=es, color=col, ls=ls, marker=mk,
                    ms=4, lw=1.4, capsize=2, zorder=3)
    ax.axhline(0.5, color="#bbbbbb", lw=0.8, zorder=1)
    ax.set_xticks(list(xs))
    ax.set_xticklabels(["abundant\n(cad 16, M 25)", "mid\n(cad 4, M 10)",
                        "scarce\n(cad 1, M 5)"], fontsize=8)
    ax.set_ylim(0.3, 1.04)
    ax.set_ylabel("α win share among decided runs")
    ax.annotate("free (α builds, no cost)", xy=(2, 0.99),
                xytext=(0.95, 0.90), color=BLUE, fontsize=8)
    ax.annotate("taxed (builds displace α's matter events)",
                xy=(2, 0.97), xytext=(0.62, 0.72), color=ORANGE,
                fontsize=8)
    ax.annotate("both build (drift null)", xy=(1, 0.49),
                xytext=(0.05, 0.40), color=GRAY, fontsize=8)
    style(ax)
    fig.tight_layout()
    fig.savefig(FIGS / "ew-scarcity.pdf")
    plt.close(fig)


def fig_rescue():
    rows = list(csv.DictReader(open(HERE / "ew4_runs.csv")))
    arms = [("faithful", 0.0), ("sloppy_e001", 0.01),
            ("sloppy_e005", 0.05), ("sloppy_e02", 0.2)]
    xs, ys, es, ds = [], [], [], []
    for arm, eps in arms:
        sub = [r for r in rows if r["arm"] == arm]
        k = sum(1 for r in sub if r["rescued"] == "True")
        d = sum(1 for r in sub if int(r["first_mu"]) >= 0)
        xs.append(eps)
        ys.append(k / len(sub))
        es.append(ci95(k, len(sub)))
        ds.append(d / len(sub))
    fig, ax = plt.subplots(figsize=(4.6, 3.0))
    ax.errorbar(xs, ys, yerr=es, color=BLUE, ls="-", marker="o", ms=4,
                lw=1.4, capsize=2, zorder=3)
    ax.plot(xs, ds, color=ORANGE, ls="--", marker="s", ms=4, lw=1.2,
            zorder=2)
    ax.set_xlabel("miscopy weight ε of the resident machinery")
    ax.set_ylabel("probability")
    ax.set_ylim(-0.03, 0.6)
    ax.annotate("builder allele discovered", xy=(0.2, 0.42),
                xytext=(0.1, 0.47), color=ORANGE, fontsize=8)
    ax.annotate("world rescued", xy=(0.2, 0.40), xytext=(0.13, 0.27),
                color=BLUE, fontsize=8)
    ax.annotate("faithful machinery: 0/100 at ε=0", xy=(0.0, 0.0),
                xytext=(0.002, 0.05), color=GRAY, fontsize=7)
    style(ax)
    fig.tight_layout()
    fig.savefig(FIGS / "ew-rescue.pdf")
    plt.close(fig)


def fig_kernel():
    rows = list(csv.DictReader(open(HERE / "ew5_runs.csv")))
    arms = ["kernel", "no-w", "no-executor", "q16", "q8", "q4"]
    labels = ["kernel", "no self-\nreference", "no\nexecutor",
              "D wound\n/16", "D wound\n/8", "D wound\n/4"]
    cols = [BLUE, ORANGE, GRAY, GREEN, GREEN, GREEN]
    fig, ax = plt.subplots(figsize=(4.6, 3.0))
    for i, arm in enumerate(arms):
        sub = [r for r in rows if r["arm"] == arm]
        k = sum(1 for r in sub if r["survived"] == "True")
        p = k / len(sub)
        ax.bar(i, p, color=cols[i], width=0.62, zorder=3)
        ax.errorbar(i, p, yerr=ci95(k, len(sub)), color="#333333",
                    capsize=3, lw=1.0, zorder=4)
        ax.annotate(f"{k}", xy=(i, p), xytext=(i, p + 0.05),
                    ha="center", fontsize=8, color="#333333")
    ax.set_xticks(range(len(arms)))
    ax.set_xticklabels(labels, fontsize=8)
    ax.set_ylabel("worlds surviving (of 100)")
    ax.set_ylim(0, 1.0)
    style(ax)
    fig.tight_layout()
    fig.savefig(FIGS / "ew-kernel.pdf")
    plt.close(fig)


if __name__ == "__main__":
    fig_bandwidth()
    fig_scarcity()
    fig_rescue()
    fig_kernel()
    print("figures written to", FIGS)
