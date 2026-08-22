#!/usr/bin/env python3
"""Night-10 inverse: THE MUTATOR ECOLOGY — deceptive codons in 1-D.

Chemistry = night 7's tape commons + up to two uniform,
glyph-symmetric codon templates:

  pair (honest, night 8):  same-glyph west + 2-gap -> write covered
                           gene TWICE (yield for runs);
  mutator (deceptive):     OTHER-glyph west + hole  -> write the
                           WEST gene instead of the covered one.

The mutator is night-8's boost with one character flipped: at a
boundary the hole's fill is contested 50/50 between the covered
gene (base repair) and the west gene reaching through the machinery
(mutator). Fidelity is therefore pattern-encoded: runs copy exactly,
boundaries mutate — and each miscopy CREATES boundaries, so
disorder is potentially autocatalytic. Two candidate phases: crystal
(runs, pair-yield, fidelity 1) vs glass (alternation, churn,
fidelity 1/2), damage rate as temperature.

Arms on shared seeds from one random init: plain (null), order
(+pair), mut (+mutator), full (both). Measured: boundary density
rho (0=crystal, ~0.5=random), run length, tape level, per-written-
cell fidelity, glyph symmetry. Exact accounting throughout.

Usage: python3 night10.py [--jobs N] [--workdir DIR]
Outputs: night10_ecology.csv, summary on stdout.
"""
import argparse
import csv
import statistics
import subprocess
import sys
import tempfile
import time
from collections import Counter
from pathlib import Path
from multiprocessing import Pool

import gen_family
import analyzers
import night7
import night8

ROOT = Path(__file__).resolve().parents[2]
BIN = ROOT / "zahradnice"
RING = 24
GEOM = (6, RING)
ARMS = ("plain", "order", "mut", "full", "para", "paraonly")
M_VALUES = (8, 4, 2)
SEEDS = tuple(range(1, 33))

_WORKDIR = None


def rules10(arm):
    R = gen_family.Rule
    rules = night7.rules7()
    if arm in ("order", "full"):
        rules += [R("F", "F", "gapwrite", "ff"),
                  R("S", "S", "gapwrite", "ss")]
    if arm in ("mut", "full"):
        rules += [R("F", "F", "wreqwrite", "s~s"),
                  R("S", "S", "wreqwrite", "f~f")]
    if arm == "para":
        rules += [R("F", "F", "gapwrite", "ff"),
                  R("S", "S", "gapwrite", "ss")]
    if arm in ("para", "paraonly"):
        # the deceptive pair: run-context yield spent on WRONG copies
        rules += [R("F", "F", "gapwrite", "fs"),
                  R("S", "S", "gapwrite", "sf")]
    return rules


def boundary_density(row):
    g = ["f" if c in "fF" else "s" if c in "sSW" else None for c in row]
    n = len(g)
    pairs = diff = 0
    for i in range(n):
        a, b = g[i], g[(i + 1) % n]
        if a is not None and b is not None:
            pairs += 1
            if a != b:
                diff += 1
    return diff / pairs if pairs else None


def _pool_init(workdir_str):
    global _WORKDIR
    _WORKDIR = Path(workdir_str)


def eval_point(task):
    arm, m = task
    rules = rules10(arm)
    extra = gen_family.poke_rules("fs")
    imap = gen_family.idx_map(rules, extra)
    rows = []
    for seed in SEEDS:
        tag = f"n10_{arm}_m{m}_s{seed}"
        cfg = _WORKDIR / f"{tag}.cfg"
        cfg.write_text(gen_family.compile_cfg(
            rules, tag, extra, night7.init_lines(RING, 0.5)))
        d0 = _WORKDIR / f"{tag}_i.txt"
        for inp, dump, tr in (
                ("z", d0, _WORKDIR / f"{tag}_i.trace"),
                (night7.protocol(m), _WORKDIR / f"{tag}.txt",
                 _WORKDIR / f"{tag}.trace")):
            r = subprocess.run(
                [str(BIN), "--headless", "--screen",
                 f"{GEOM[0]},{GEOM[1]}", "--seed", str(seed),
                 "--input", inp, "--dump-screen", str(dump),
                 "--trace", str(tr), str(cfg)],
                capture_output=True, text=True)
            if r.returncode != 0:
                raise RuntimeError(r.stderr.strip())
        s0 = tuple(analyzers.parse_dump(d0, *GEOM))
        applies = analyzers.parse_trace(_WORKDIR / f"{tag}.trace")
        grid = [list(rr) for rr in s0]
        cnt = Counter(c for row in s0 for c in row if c in "fsFSW")
        rep = Counter()
        samples = []
        for i, ap in enumerate(applies):
            lhs, idx, ro, co, trig = ap
            rule = imap[(lhs, idx)]
            if trig == "T":
                if rule.kind == "reqwrite" and rule.arg[0] == "~":
                    rep["base"] += 1
                elif rule.kind == "gapwrite":
                    rep["pair" if rule.arg[0] == rule.arg[1]
                        else "dpair"] += 1
                elif rule.kind == "wreqwrite":
                    rep["mut"] += 1
            for dc, ch in gen_family.writes(rule):
                rr, c = ro - 1, (co + dc) % RING
                old = grid[rr][c]
                if old in "fsFSW":
                    cnt[old] -= 1
                if ch in "fsFSW":
                    cnt[ch] += 1
                grid[rr][c] = ch
            if (i + 1) % 50 == 0:
                f_, s_ = night7.comp(cnt)
                rm, _, _ = night8.run_stats(grid[2])
                samples.append((cnt["f"] + cnt["s"],
                                s_ / (f_ + s_) if f_ + s_ else None,
                                boundary_density(grid[2]), rm))
        if "\n".join("".join(rr) for rr in grid) != "\n".join(
                analyzers.parse_dump(_WORKDIR / f"{tag}.txt", *GEOM)):
            sys.exit(f"EXACT-FAIL {tag}")
        for p in (cfg, d0, _WORKDIR / f"{tag}_i.trace",
                  _WORKDIR / f"{tag}.txt", _WORKDIR / f"{tag}.trace"):
            p.unlink()
        rho0 = boundary_density(list(s0)[2])
        lastq = [s for s in samples[3 * len(samples) // 4:]
                 if s[2] is not None]
        faithful = rep["base"] + 2 * rep["pair"]
        total = faithful + rep["mut"] + 2 * rep["dpair"]
        rows.append({
            "arm": arm, "m": m, "seed": seed, "rho_init": rho0,
            "rho_lastq": (statistics.mean(s[2] for s in lastq)
                          if lastq else None),
            "runmean_lastq": (statistics.mean(s[3] for s in lastq)
                              if lastq else None),
            "tape_lastq": (statistics.mean(s[0] for s in lastq)
                           if lastq else 0),
            "s_share_lastq": (statistics.mean(
                s[1] for s in lastq if s[1] is not None)
                if any(s[1] is not None for s in lastq) else None),
            "fidelity": faithful / total if total else None,
            "rho_traj": ";".join(
                f"{samples[min(len(samples) - 1, k * len(samples) // 8)][2]:.2f}"
                if samples[min(len(samples) - 1,
                               k * len(samples) // 8)][2] is not None
                else "-" for k in range(1, 9)) if samples else "",
            "rho_osc": (statistics.stdev(
                s[2] for s in samples[len(samples) // 2:]
                if s[2] is not None)
                if sum(1 for s in samples[len(samples) // 2:]
                       if s[2] is not None) > 2 else None),
            "rep_base": rep["base"], "rep_pair": rep["pair"],
            "rep_mut": rep["mut"], "rep_dpair": rep["dpair"]})
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", type=int, default=8)
    ap.add_argument("--workdir", default=None)
    args = ap.parse_args()
    workdir = Path(args.workdir) if args.workdir else \
        Path(tempfile.mkdtemp(prefix="night10_"))
    workdir.mkdir(parents=True, exist_ok=True)
    here = Path(__file__).parent
    print(f"binary {BIN}\nworkdir {workdir}")
    tasks = [(a, m) for a in ARMS for m in M_VALUES]
    print(f"{len(tasks)} points x {len(SEEDS)} seeds "
          f"= {len(tasks) * len(SEEDS)} runs")
    t0 = time.perf_counter()
    with Pool(args.jobs, _pool_init, (str(workdir),)) as pool:
        results = pool.map(eval_point, tasks, chunksize=1)
    rows = [r for res in results for r in res]
    print(f"wall {time.perf_counter() - t0:.1f}s, exactness: all pass\n")

    cols = ["arm", "m", "seed", "rho_init", "rho_lastq",
            "runmean_lastq", "tape_lastq", "s_share_lastq", "fidelity",
            "rho_traj", "rho_osc", "rep_base", "rep_pair", "rep_mut",
            "rep_dpair"]
    with open(here / "night10_ecology.csv", "w", newline="") as f:
        w = csv.DictWriter(f, cols)
        w.writeheader()
        for r in rows:
            w.writerow({c: (f"{r[c]:.3f}" if isinstance(r[c], float)
                            else r[c]) for c in cols})

    print("per (m, arm): rho init->lastq (0=crystal, .5=random) | "
          "run | tape | fidelity | s-share:")
    for m in M_VALUES:
        for arm in ARMS:
            sub = [r for r in rows if r["arm"] == arm and r["m"] == m]
            ri = statistics.mean(r["rho_init"] for r in sub)
            rl = [r["rho_lastq"] for r in sub
                  if r["rho_lastq"] is not None]
            rm = [r["runmean_lastq"] for r in sub
                  if r["runmean_lastq"] is not None]
            tp = statistics.mean(r["tape_lastq"] for r in sub)
            fi = [r["fidelity"] for r in sub if r["fidelity"] is not None]
            ss = [r["s_share_lastq"] for r in sub
                  if r["s_share_lastq"] is not None]
            print(f"  m={m} {arm:<5}: rho {ri:.2f}->"
                  f"{statistics.mean(rl):.2f} | run "
                  f"{statistics.mean(rm):4.1f} | tape {tp:4.1f} | fid "
                  f"{statistics.mean(fi):.3f} | s "
                  f"{statistics.mean(ss):.2f}")


if __name__ == "__main__":
    main()
