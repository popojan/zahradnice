#!/usr/bin/env python3
"""Figures for paper #2 (The Subtraction Ladder), all regenerated
from the same drivers/CSVs as the text's numbers. Outputs to
paper/figs/:

  spacetime.txt  archetype healing, space-time (text; the substrate's
                 native rendering)
  phase.pdf      night-3 recovery fraction vs damage interval
                 (archetype, rings 6 and 12)
  rho.pdf        night-10 mean boundary-density trajectories, m=4
  rmap.pdf       live residence map R(x) vs frozen dwell theory

Print conventions: single axis, fixed series order, CVD-safe hues
with line-style+marker secondary encoding (grayscale-legible),
recessive grid, direct labels.
"""
import csv
import statistics
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import gen_family as gf
import analyzers
import night7
import night10

HERE = Path(__file__).parent
FIGS = HERE.parent.parent / "paper" / "figs"
FIGS.mkdir(parents=True, exist_ok=True)
BIN = HERE.parent.parent / "zahradnice"
WORK = Path(tempfile.mkdtemp(prefix="figs_"))

# fixed series styles: (color, linestyle, marker) — CVD-safe hues,
# style+marker as secondary encoding for grayscale
STYLES = [("#4477AA", "-", "o"), ("#CC3311", "--", "s"),
          ("#228833", "-.", "^"), ("#66666E", ":", "D")]

plt.rcParams.update({
    "font.size": 9, "axes.linewidth": 0.6, "axes.grid": True,
    "grid.color": "#DDDDDD", "grid.linewidth": 0.4,
    "legend.frameon": False, "figure.dpi": 150,
    "axes.spines.top": False, "axes.spines.right": False})


def engine(cfg, geom, seed, inp, trace, dump):
    r = subprocess.run(
        [str(BIN), "--headless", "--screen", f"{geom[0]},{geom[1]}",
         "--seed", str(seed), "--input", inp, "--dump-screen",
         str(dump), "--trace", str(trace), str(cfg)],
        capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip())


# --- Fig 1: space-time text diagram --------------------------------

def fig_spacetime():
    RING = 40
    R = gf.Rule
    rules = [R("A", "B", "write", "A"), R("B", "A", "req", "~")]
    extra = gf.poke_rules("AB")
    cfg = WORK / "st.cfg"
    cfg.write_text(gf.compile_cfg(rules, "st", extra, "^Acl"))
    inp = "T" * 78 + "p" + "T" * 26 + "p" + "T" * 40
    engine(cfg, (6, RING), 5, "z", WORK / "i.trace", WORK / "i.txt")
    s0 = analyzers.parse_dump(WORK / "i.txt", 6, RING)
    engine(cfg, (6, RING), 5, inp, WORK / "r.trace", WORK / "r.txt")
    applies = analyzers.parse_trace(WORK / "r.trace")
    imap = gf.idx_map(rules, extra)
    grid = [list(r_) for r_ in s0]
    lines = []
    poked = False
    for i, (lhs, idx, ro, co, trig) in enumerate(applies):
        rule = imap[(lhs, idx)]
        for dc, ch in gf.writes(rule):
            grid[ro - 1][(co + dc) % RING] = ch
        if trig == "p":
            poked = True
        if (i + 1) % 6 == 0:
            row = "".join(grid[2]).replace(" ", ".")
            mark = "  <-- wound" if poked else ""
            lines.append(f"ev {i+1:3d}   {row}{mark}")
            poked = False
    if "\n".join("".join(r_) for r_ in grid) != "\n".join(
            analyzers.parse_dump(WORK / "r.txt", 6, RING)):
        sys.exit("EXACT-FAIL spacetime")
    body = "\n".join(lines)
    (FIGS / "spacetime.tex").write_text(
        "\\begtt\n" + body + "\n\\endtt\n")
    print(f"spacetime.tex: {len(lines)} rows")


# --- Fig 2: night-3 phase diagram ----------------------------------

def fig_phase():
    rows = list(csv.DictReader(open(HERE / "night3_sustain.csv")))
    fig, ax = plt.subplots(figsize=(4.6, 3.0))
    series = [
        ("A>B.writeA|B>A.req~", 6, "adjacent-respawn, ring 6",
         dict(color="#4477AA", ls="-", marker="o", ms=4, lw=1.6)),
        ("A>B.writeA|B>A.req~", 12,
         "adjacent-respawn, ring 12 (identical)",
         dict(color="#CC3311", ls="none", marker="s", ms=8,
              mfc="none", mew=1.3)),
        ("A>~.writeB|B>A.reqwrite~B", 6, "walk-to-wound, ring 6",
         dict(color="#228833", ls="-.", marker="^", ms=5, lw=1.4)),
        ("A>~.writeB|B>A.reqwrite~B", 12, "walk-to-wound, ring 12",
         dict(color="#66666E", ls=":", marker="D", ms=6, mfc="none",
              mew=1.2, lw=1.4))]
    for gid, ring, label, kw in series:
        sub = sorted((r for r in rows if r["gid"] == gid
                      and r["ring"] == str(ring)),
                     key=lambda r: int(r["m"]))
        xs = [int(r["m"]) for r in sub]
        ys = [float(r["recovery"]) for r in sub]
        ax.plot(xs, ys, label=label, **kw)
    ax.set_xscale("symlog", linthresh=1)
    ax.set_xticks([0, 1, 2, 3, 5, 8, 12, 20, 40])
    ax.set_xticklabels(["0", "1", "2", "3", "5", "8", "12", "20", "40"])
    ax.set_xlabel("damage interval m  (events between wounds)")
    ax.set_ylabel("recovery fraction")
    ax.set_ylim(-0.05, 1.05)
    ax.legend(loc="upper left", fontsize=8)
    fig.tight_layout()
    fig.savefig(FIGS / "phase.pdf")
    plt.close(fig)
    print("phase.pdf")


# --- Fig 3: rho trajectories (regenerated, mean over 32 seeds) -----

def fig_rho():
    m = 4
    fig, ax = plt.subplots(figsize=(4.6, 2.9))
    arms = [("plain", "no codon"), ("mut", "mutator"),
            ("para", "honest + parasite"), ("paraonly", "parasite only")]
    for (arm, label), (c, ls, mk) in zip(arms, STYLES):
        rules = night10.rules10(arm)
        extra = gf.poke_rules("fs")
        imap = gf.idx_map(rules, extra)
        curves = []
        for seed in range(1, 33):
            cfg = WORK / "r10.cfg"
            cfg.write_text(gf.compile_cfg(
                rules, "r10", extra, night7.init_lines(24, 0.5)))
            engine(cfg, (6, 24), seed, "z", WORK / "i.trace",
                   WORK / "i.txt")
            s0 = analyzers.parse_dump(WORK / "i.txt", 6, 24)
            engine(cfg, (6, 24), seed, night7.protocol(m),
                   WORK / "r.trace", WORK / "r.txt")
            applies = analyzers.parse_trace(WORK / "r.trace")
            grid = [list(r_) for r_ in s0]
            ser = []
            for i, (lhs, idx, ro, co, trig) in enumerate(applies):
                rule = imap[(lhs, idx)]
                for dc, ch in gf.writes(rule):
                    grid[ro - 1][(co + dc) % 24] = ch
                if (i + 1) % 100 == 0:
                    ser.append(night10.boundary_density(grid[2]))
            curves.append([x for x in ser if x is not None])
        n = min(len(cv) for cv in curves)
        mean = [statistics.mean(cv[i] for cv in curves)
                for i in range(n)]
        se = [statistics.stdev(cv[i] for cv in curves)
              / len(curves) ** 0.5 for i in range(n)]
        W = 5   # display smoothing only
        sm = [statistics.mean(mean[max(0, i - W // 2):i + W // 2 + 1])
              for i in range(n)]
        ss = [statistics.mean(se[max(0, i - W // 2):i + W // 2 + 1])
              for i in range(n)]
        xs = [100 * (i + 1) for i in range(n)]
        if arm in ("para", "paraonly"):
            ax.fill_between(xs, [a - b for a, b in zip(sm, ss)],
                            [a + b for a, b in zip(sm, ss)],
                            color=c, alpha=0.25, lw=0)
        ax.plot(xs, sm, ls, color=c, lw=1.5, label=label)
        if arm == "paraonly":
            ax.annotate("parasite only", xy=(24200, sm[-1] + 0.022),
                        fontsize=8, color=c, ha="right")
        if arm == "para":
            ax.annotate("honest + parasite", xy=(24200, sm[-1] - 0.038),
                        fontsize=8, color=c, ha="right")
        if arm == "mut":
            ax.annotate("no codon, mutator: crystal",
                        xy=(6000, 0.035), fontsize=8, color="#555555")
    ax.set_xlabel("events")
    ax.set_ylabel(r"boundary density  $\rho$")
    ax.set_ylim(0, 0.56)
    ax.set_xlim(0, 24500)
    ax.legend(loc="upper right", ncols=2, fontsize=7.5)
    fig.tight_layout()
    fig.savefig(FIGS / "rho.pdf")
    plt.close(fig)
    print("rho.pdf")


# --- Fig 4: residence map ------------------------------------------

def fig_rmap():
    import night9
    fig, ax = plt.subplots(figsize=(4.2, 3.2))
    xx = [i / 100 for i in range(101)]
    ax.plot(xx, xx, color="#AAAAAA", lw=0.9, ls="--")
    ax.annotate("identity", xy=(0.72, 0.68), fontsize=8,
                color="#888888", rotation=38)
    for k, (c, ls, mk) in zip((2, 3), STYLES):
        ax.plot(xx, [k * x / (1 - x + k * x) for x in xx],
                color=c, lw=0.9, ls=":",
                label=f"frozen dwell, k={k}")
    for k, (c, ls, mk) in zip((2, 3), STYLES):
        rules = night7.rules7() if k == 2 else night9.rules_s3()
        glyphs = "fsFSW" if k == 2 else "fsFSWV"
        extra = gf.poke_rules("fs")
        imap = gf.idx_map(rules, extra)
        init = "\n".join(["^fc*"] + ["^sc?"] * 12 + ["^Fcl", "^Fcc"])
        bins = {}
        for seed in range(1, 17):
            cfg = WORK / "rm.cfg"
            cfg.write_text(gf.compile_cfg(rules, "rm", extra, init))
            engine(cfg, (6, 24), seed, "z", WORK / "i.trace",
                   WORK / "i.txt")
            s0 = analyzers.parse_dump(WORK / "i.txt", 6, 24)
            engine(cfg, (6, 24), seed, night7.protocol(8),
                   WORK / "r.trace", WORK / "r.txt")
            applies = analyzers.parse_trace(WORK / "r.trace")
            grid = [list(r_) for r_ in s0]
            acc = [0, 0, 0, 0]
            for i, (lhs, idx, ro, co, trig) in enumerate(applies):
                rule = imap[(lhs, idx)]
                for dc, ch in gf.writes(rule):
                    grid[ro - 1][(co + dc) % 24] = ch
                if i % 7 == 0:
                    c2 = Counter(ch for row in grid for ch in row
                                 if ch in glyphs)
                    acc[0] += c2["S"] + c2["W"] + c2["V"]
                    acc[1] += c2["F"]
                    acc[2] += c2["s"] + c2["S"] + c2["W"] + c2["V"]
                    acc[3] += c2["f"] + c2["F"]
                if (i + 1) % 500 == 0:
                    if acc[0] + acc[1] and acc[2] + acc[3]:
                        R = acc[0] / (acc[0] + acc[1])
                        x = acc[2] / (acc[2] + acc[3])
                        if 0.02 < x < 0.98:
                            b = round(x * 20) / 20
                            sx, sR, n = bins.get((k, b), (0, 0, 0))
                            bins[(k, b)] = (sx + x, sR + R, n + 1)
                    acc = [0, 0, 0, 0]
        pts = sorted((v[0] / v[2], v[1] / v[2])
                     for kk, v in bins.items()
                     if kk[0] == k and v[2] >= 8)
        ax.plot([p[0] for p in pts], [p[1] for p in pts],
                color=c, lw=1.4, ls="-", marker=mk, ms=4,
                label=f"live, measured, k={k}")
    ax.set_xlabel(r"composition  $x$  (share of slow gene s)")
    ax.set_ylabel(r"machinery residence  $R(x)$")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.legend(loc="lower right", fontsize=8)
    fig.tight_layout()
    fig.savefig(FIGS / "rmap.pdf")
    plt.close(fig)
    print("rmap.pdf")


if __name__ == "__main__":
    fig_spacetime()
    fig_phase()
    fig_rho()
    fig_rmap()
