#!/usr/bin/env python3
"""Figures for paper #3 (Law Made of Matter), regenerated from the
same CSVs as the text's numbers. Outputs to paper/figs/:

  ow-dose.pdf     the causal dose-response (wound-fed fraction)
  ow-sigmoid.pdf  the war curve at three ring sizes
  ow-phase.pdf    epsilon x wound phase map (rescue / retention)
  ow-niche.tex    B-mirror niche construction, space-time (text;
                  the substrate's native rendering)

Also prints w*_det with its propagated error from ow9_frontier.csv.
Print conventions as fig_nights.py: single axis, fixed series
order, CVD-safe hues with line-style+marker secondary encoding,
recessive grid, direct labels.
"""
import csv
import math
import statistics
import subprocess
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "inverse"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import analyzers
import ow4

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


def fig_dose():
    by_c = defaultdict(Counter)
    for r in csv.DictReader(open(HERE / "ow9_dose.csv")):
        by_c[int(r["c"])][r["dom"]] += 1
    xs = sorted(by_c)
    fx = [c / 4 for c in xs]
    share, se, dead = [], [], []
    for c in xs:
        a, b = by_c[c]["α"], by_c[c]["β"]
        n = a + b
        share.append(a / n if n else float("nan"))
        se.append(ci95(a, n) if n else 0)
        dead.append(by_c[c]["DEAD"] / sum(by_c[c].values()))
    fig, ax = plt.subplots(figsize=(4.6, 3.1))
    style(ax)
    ax.errorbar(fx, share, yerr=se, color=BLUE, marker="o", mfc="white",
                capsize=2.5, zorder=3, label="α-share")
    ax.plot(fx, dead, color=GRAY, marker="s", mfc="white", ls="--",
            zorder=3, label="dead worlds")
    ax.axhline(0.5, color="#bbbbbb", lw=0.8, ls=":")
    ax.text(0.02, 0.93, "α-share of decided duels", color=BLUE,
            transform=ax.transAxes, fontsize=9)
    ax.text(0.02, 0.30, "fraction of worlds dead", color=GRAY,
            transform=ax.transAxes, fontsize=9)
    ax.set_xlabel("wound-fed fraction of a fixed influx (k = 4)")
    ax.set_ylabel("fraction")
    ax.set_ylim(-0.03, 1.03)
    fig.tight_layout()
    fig.savefig(FIGS / "ow-dose.pdf")
    plt.close(fig)


def fig_sigmoid():
    by = defaultdict(Counter)
    for r in csv.DictReader(open(HERE / "ow9_cliff.csv")):
        by[(int(r["ring"]), float(r["w"]))][r["dom"]] += 1
    fig, ax = plt.subplots(figsize=(4.6, 3.1))
    style(ax)
    for ring, color, ls, mk in ((24, BLUE, "-", "o"),
                                (48, ORANGE, "--", "s"),
                                (96, GREEN, ":", "^")):
        ws = sorted(w for r, w in by if r == ring)
        ys = [by[(ring, w)]["α"] /
              (by[(ring, w)]["α"] + by[(ring, w)]["β"]) for w in ws]
        es = [ci95(by[(ring, w)]["α"],
                   by[(ring, w)]["α"] + by[(ring, w)]["β"]) for w in ws]
        ax.errorbar(ws, ys, yerr=es, color=color, ls=ls, marker=mk,
                    mfc="white", capsize=2, zorder=3)
        ax.text(ws[-1] + 0.008, ys[-1], f"ring {ring}", color=color,
                fontsize=9, va="center")
    ax.axhline(0.5, color="#bbbbbb", lw=0.8, ls=":")
    ax.set_xlabel("β mover weight w")
    ax.set_ylabel("α-share")
    ax.set_xlim(0.985, 1.32)
    ax.set_ylim(0, 1.03)
    fig.tight_layout()
    fig.savefig(FIGS / "ow-sigmoid.pdf")
    plt.close(fig)


def fig_phase():
    surv = defaultdict(int)
    tot = defaultdict(int)
    for r in csv.DictReader(open(HERE / "ow5_phase.csv")):
        key = (r["start"], float(r["eps"]), int(r["m"]))
        tot[key] += 1
        surv[key] += r["dom"] != "DEAD"
    epss = [0.0, 0.001, 0.003, 0.01, 0.03]
    ms = [50, 25, 12, 6]
    fig, axes = plt.subplots(1, 2, figsize=(6.6, 2.9))
    for ax, start, title in ((axes[0], "γ", "rescue (γ-start)"),
                             (axes[1], "α", "retention (α-start)")):
        grid = [[surv[(start, e, m)] / tot[(start, e, m)]
                 for m in ms] for e in epss]
        im = ax.imshow(grid, cmap="viridis", vmin=0, vmax=1,
                       aspect="auto", origin="lower")
        for i, e in enumerate(epss):
            for j, m in enumerate(ms):
                v = surv[(start, e, m)]
                ax.text(j, i, str(v), ha="center", va="center",
                        fontsize=8,
                        color="white" if grid[i][j] < 0.55 else "black")
        ax.set_xticks(range(4),
                      [f"{2 / (m + 2):.0%}" for m in ms])
        ax.set_yticks(range(5), [f"{e:g}" for e in epss])
        ax.set_xlabel("wound share of events")
        ax.set_title(title, fontsize=10)
    axes[0].set_ylabel("mutation weight ε")
    fig.tight_layout()
    fig.savefig(FIGS / "ow-phase.pdf")
    plt.close(fig)


TRANS = {"ğ": "g", "Ę": "e"}


def fig_niche():
    work = Path(tempfile.mkdtemp(prefix="fign_"))
    text, imap, prefix, _ = ow4.build_cfg("walker2", 0.01, 20)
    cfg = work / "w2.cfg"
    cfg.write_text(text)
    d0 = work / "i.txt"
    subprocess.run([str(ow4.BIN), "--headless", "--screen", "3,24",
                    "--seed", "20", "--input", "z",
                    "--dump-screen", str(d0), str(cfg)],
                   capture_output=True, text=True)
    s0 = analyzers.parse_dump(d0, 3, 24)
    tr = work / "t.trace"
    subprocess.run([str(ow4.BIN), "--headless", "--screen", "3,24",
                    "--seed", "20", "--input", ow4.drive(prefix),
                    "--trace", str(tr), "--dump-screen",
                    str(work / "d.txt"), str(cfg)],
                   capture_output=True, text=True)
    applies = analyzers.parse_trace(tr)
    grid = [list(r) for r in s0]
    n = len(applies)
    samples = sorted({3, 8} | {int(n * f) for f in
                      (0.002, 0.02, 0.1, 0.2, 0.3, 0.45, 0.6, 0.8, 1.0)})
    out = []
    for i, (lhs, idx, ro, co, _t) in enumerate(applies):
        for dr, dc, ch in imap[(lhs, idx)]:
            grid[(ro - 1 + dr) % 2][(co + dc) % 24] = ch
        if i + 1 in samples:
            tape = "".join(grid[0]).replace(" ", ".")
            out.append(f"ev {i + 1:>5}   {tape}")
    gates = "".join(TRANS.get(g, "\u00b7" if g != " " else ".")
                    for g in grid[1])
    out.append(f"ev {n:>5}   {gates}   (the law row)")
    (FIGS / "ow-niche.tex").write_text(
        "\\begtt\n" + "\n".join(out) + "\n\\endtt\n")


def wstar():
    per = defaultdict(list)
    for r in csv.DictReader(open(HERE / "ow9_frontier.csv")):
        if int(r["ring"]) == 48 and int(r["steps"]):
            per[float(r["w"])].append(int(r["dsum"]) / int(r["steps"]))
    mu, se = {}, {}
    for w, xs in per.items():
        mu[w] = statistics.mean(xs)
        se[w] = statistics.stdev(xs) / len(xs) ** 0.5
    a, b = -mu[1.1], mu[1.2]
    s = a + b
    w = 1.1 + 0.1 * a / s
    dw = 0.1 / s ** 2 * math.sqrt((b * se[1.1]) ** 2 + (a * se[1.2]) ** 2)
    print(f"w*_det = {w:.3f} ± {dw:.3f}  "
          f"(μ(1.1) = {mu[1.1]:+.5f} ± {se[1.1]:.5f}, "
          f"μ(1.2) = {mu[1.2]:+.5f} ± {se[1.2]:.5f})")


if __name__ == "__main__":
    fig_dose()
    fig_sigmoid()
    fig_phase()
    fig_niche()
    wstar()
    print("figures written to", FIGS)
