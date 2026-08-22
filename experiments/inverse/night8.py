#!/usr/bin/env python3
"""Night-8 inverse: CLOSING THE LOOP — sequences that program the
machinery that copies them.

Chemistry = night 7's tape commons (9 uniform rules) plus ONE
uniform template, the homogeneity codon (2 instances, weight 1,
glyph-symmetric): a head covering a gene whose WEST neighbour is the
same glyph — i.e. the head is READING a run — gains a second,
co-applicable repair rule for a hole east. Rule multiplicity, not
weight: repair mass doubles at run sites. The copy written extends
the very run that was read: pattern -> machine behaviour -> pattern,
benefit cis by construction.

Claims tested against the no-boost NULL (plain night-7 law, which
also extends runs passively — the null must be measured, not
assumed):
  1. run structure ratchets: mean/max run length grows above null;
  2. composition stays f/s-symmetric (selection on PATTERN, not glyph);
  3. doubled repair mass shifts the m=2 collapse boundary.

Usage: python3 night8.py [--jobs N] [--workdir DIR]
Outputs: night8_codon.csv, summary on stdout.
"""
import argparse
import csv
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

ROOT = Path(__file__).resolve().parents[2]
BIN = ROOT / "zahradnice"

RING = 24
H_EST = 32
DUR = 24000
ARMS = ("base", "boost", "pair")
M_VALUES = (None, 8, 4, 2)
SEEDS = tuple(range(1, 65))
SAMPLE_EVERY = 50

_WORKDIR = None


def rules8(arm):
    R = gen_family.Rule
    rules = night7.rules7()
    if arm == "boost":
        rules += [R("F", "F", "wreqwrite", "f~f"),
                  R("S", "S", "wreqwrite", "s~s")]
    elif arm == "pair":
        rules += [R("F", "F", "gapwrite", "ff"),
                  R("S", "S", "gapwrite", "ss")]
    return rules


def run_stats(row):
    """(mean run length, max run, n runs) of the circular gene row;
    holes break runs; heads count as their covered glyph."""
    g = ["f" if c in "fF" else "s" if c in "sSW" else None for c in row]
    n = len(g)
    if not any(x is not None for x in g):
        return (0.0, 0, 0)
    start = None
    for i in range(n):
        if g[i] is not None and g[i - 1] != g[i]:
            start = i
            break
    if start is None:
        return (float(n), n, 1)
    runs, cur, ln = [], None, 0
    for k in range(n):
        x = g[(start + k) % n]
        if x is None:
            if cur:
                runs.append(ln)
            cur, ln = None, 0
        elif x == cur:
            ln += 1
        else:
            if cur:
                runs.append(ln)
            cur, ln = x, 1
    if cur:
        runs.append(ln)
    return (sum(runs) / len(runs), max(runs), len(runs))


def codon_replay(rules, extra, s0, applies, cols):
    imap = gen_family.idx_map(rules, extra)
    grid = [list(r) for r in s0]
    cnt = Counter(c for row in s0 for c in row if c in "fsFSW")
    rep = Counter()
    samples = []
    min_tape = cnt["f"] + cnt["s"]
    for i, (lhs, idx, ro, co, trig) in enumerate(applies):
        rule = imap[(lhs, idx)]
        if trig == "T":
            if rule.kind == "reqwrite" and rule.arg[0] == "~":
                rep["base"] += 1
            elif rule.kind in ("wreqwrite", "gapwrite"):
                rep["boost"] += 1
        for dc, ch in gen_family.writes(rule):
            r, c = ro - 1, (co + dc) % cols
            old = grid[r][c]
            if old in "fsFSW":
                cnt[old] -= 1
            if ch in "fsFSW":
                cnt[ch] += 1
            grid[r][c] = ch
        tape = cnt["f"] + cnt["s"]
        if tape < min_tape:
            min_tape = tape
        if (i + 1) % SAMPLE_EVERY == 0:
            f_, s_ = night7.comp(cnt)
            rm, rx, nr = run_stats(grid[2])
            samples.append((rm, rx, tape, s_ / (f_ + s_) if f_ + s_
                            else None))
    final = "\n".join("".join(r) for r in grid)
    return final, cnt, rep, samples, min_tape


def eval_point(task):
    arm, m = task
    geom = (6, RING)
    rules = rules8(arm)
    extra = gen_family.poke_rules("fs")
    tag = f"{arm}_m{m}"
    cfg = _WORKDIR / f"n8_{tag}.cfg"
    cfg.write_text(gen_family.compile_cfg(rules, f"n8_{tag}", extra,
                                          night7.init_lines(RING, 0.5)))
    inp = night7.protocol(m) if m is not None else \
        "T" * (H_EST + DUR)
    rows, engine_s = [], 0.0
    for seed in SEEDS:
        dump0 = _WORKDIR / f"n8_{tag}_s{seed}_i.txt"
        t0 = time.perf_counter()
        subprocess.run([str(BIN), "--headless", "--screen",
                        f"{geom[0]},{geom[1]}", "--seed", str(seed),
                        "--input", "z", "--dump-screen", str(dump0),
                        str(cfg)], capture_output=True, text=True)
        trace = _WORKDIR / f"n8_{tag}_s{seed}.trace"
        dump = _WORKDIR / f"n8_{tag}_s{seed}.txt"
        r = subprocess.run([str(BIN), "--headless", "--screen",
                            f"{geom[0]},{geom[1]}", "--seed", str(seed),
                            "--input", inp, "--dump-screen", str(dump),
                            "--trace", str(trace), str(cfg)],
                           capture_output=True, text=True)
        engine_s += time.perf_counter() - t0
        if r.returncode != 0:
            raise RuntimeError(r.stderr.strip())
        s0 = tuple(analyzers.parse_dump(dump0, *geom))
        applies = analyzers.parse_trace(trace)
        final, cnt, rep, samples, min_tape = codon_replay(
            rules, extra, list(s0), applies, RING)
        if final != "\n".join(analyzers.parse_dump(dump, *geom)):
            sys.exit(f"EXACT-FAIL {tag} seed {seed}")
        rm0, rx0, _ = run_stats(list(s0)[2])
        lastq = samples[3 * len(samples) // 4:]
        alive = [s for s in lastq if s[2] > 0]
        rows.append({
            "arm": arm, "m": "inf" if m is None else m, "seed": seed,
            "runmean_init": rm0, "runmax_init": rx0,
            "runmean_lastq": (sum(s[0] for s in alive) / len(alive)
                              if alive else None),
            "runmax_lastq": (max(s[1] for s in alive) if alive
                             else None),
            "tape_lastq": (sum(s[2] for s in alive) / len(alive)
                           if alive else 0),
            "s_share_lastq": (sum(s[3] for s in alive if s[3] is not None)
                              / max(1, sum(1 for s in alive
                                           if s[3] is not None))
                              if alive else None),
            "rep_base": rep["base"], "rep_boost": rep["boost"],
            "min_tape": min_tape})
        for p in (trace, dump, dump0):
            p.unlink()
    return {"rows": rows, "engine_s": engine_s}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", type=int, default=1)
    ap.add_argument("--workdir", default=None)
    args = ap.parse_args()
    workdir = Path(args.workdir) if args.workdir else \
        Path(tempfile.mkdtemp(prefix="night8_"))
    workdir.mkdir(parents=True, exist_ok=True)
    global _WORKDIR
    print(f"binary {BIN}\nworkdir {workdir}")

    tasks = [(a, m) for a in ARMS for m in M_VALUES]
    print(f"{len(tasks)} points x {len(SEEDS)} seeds "
          f"= {len(tasks) * len(SEEDS)} runs")
    t0 = time.perf_counter()
    if args.jobs > 1:
        with Pool(args.jobs, _pool_init, (str(workdir),)) as pool:
            results = pool.map(eval_point, tasks, chunksize=1)
    else:
        _pool_init(str(workdir))
        results = [eval_point(t) for t in tasks]
    wall = time.perf_counter() - t0
    rows = [r for res in results for r in res["rows"]]
    print(f"wall {wall:.1f}s "
          f"({1000 * sum(res['engine_s'] for res in results) / len(rows):.0f}"
          f" ms/run engine), exactness: all pass")

    here = Path(__file__).parent
    cols = ["arm", "m", "seed", "runmean_init", "runmean_lastq",
            "runmax_init", "runmax_lastq", "tape_lastq", "s_share_lastq",
            "rep_base", "rep_boost", "min_tape"]
    with open(here / "night8_codon.csv", "w", newline="") as f:
        w = csv.DictWriter(f, cols)
        w.writeheader()
        for r in rows:
            w.writerow({c: (f"{r[c]:.3f}" if isinstance(r[c], float)
                            else r[c]) for c in cols})

    print("\nper (arm, m): run length init -> lastq | max run | tape | "
          "boost share of repairs | s-share:")
    for m in M_VALUES:
        mm = "inf" if m is None else m
        for arm in ARMS:
            sub = [r for r in rows if r["arm"] == arm and r["m"] == mm]
            ri = sum(r["runmean_init"] for r in sub) / len(sub)
            rl = [r["runmean_lastq"] for r in sub
                  if r["runmean_lastq"] is not None]
            rx = [r["runmax_lastq"] for r in sub
                  if r["runmax_lastq"] is not None]
            tp = sum(r["tape_lastq"] for r in sub) / len(sub)
            rb = sum(r["rep_base"] for r in sub)
            rB = sum(r["rep_boost"] for r in sub)
            ss = [r["s_share_lastq"] for r in sub
                  if r["s_share_lastq"] is not None]
            print(f"  m={mm:>3} {arm:<5}: run {ri:.1f}->"
                  f"{sum(rl)/len(rl) if rl else 0:.1f} | max "
                  f"{sum(rx)/len(rx) if rx else 0:4.1f} | tape {tp:4.1f}"
                  f" | boost {rB/(rb+rB) if rb+rB else 0:.2f}"
                  f" | s {sum(ss)/len(ss) if ss else 0:.2f}")


def _pool_init(workdir_str):
    global _WORKDIR
    _WORKDIR = Path(workdir_str)


if __name__ == "__main__":
    main()
