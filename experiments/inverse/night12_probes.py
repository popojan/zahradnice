#!/usr/bin/env python3
"""Theory probes on the parasite phase (paper-v3 queue):

P1. LANGUAGE ORDER: is the stationary word Markov-rational?
    - run-length distribution vs the geometric null implied by the
      measured boundary density rho (a 2-state Markov ring gives
      geometric runs, mean ~ 1/rho);
    - two-point connected correlation C(d) vs the Markov prediction
      (1-2*rho)^d.
    Excess long-range structure would mean the parasite pushes the
    stationary language ABOVE finite-order Markov (up the weighted
    hierarchy); agreement means it stays rational.

P2. IRREVERSIBILITY: a stochastic limit cycle is a circulating
    probability current, forbidden under detailed balance. Probe:
    time-reversal asymmetry of the (rho, runmean) trajectory,
    A(tau) = <d_rho(t) d_run(t+tau) - d_rho(t+tau) d_run(t)>,
    per-seed, t-tested against zero across seeds. Nonzero A with a
    consistent sign = measured probability current = NESS.

Arms: paraonly and para (night-10 chemistry), m in {8, 4}, ring 24,
32 seeds, final half of 24k events as the stationary window. Exact
accounting as always.

Usage: python3 night12_probes.py [--jobs N] [--workdir DIR]
Outputs: night12_language.csv (per-seed stats), summary on stdout.
"""
import argparse
import math
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
import night10

ROOT = Path(__file__).resolve().parents[2]
BIN = ROOT / "zahradnice"
RING = 24
GEOM = (6, RING)
ARMS = ("paraonly", "para")
M_VALUES = (8, 4)
SEEDS = tuple(range(1, 33))
SAMPLE_EVERY = 50
DMAX = 8
TAUMAX = 10

_WORKDIR = None


def _pool_init(workdir_str):
    global _WORKDIR
    _WORKDIR = Path(workdir_str)


def row_stats(row):
    """From one sampled ring row: gene sequence (holes break),
    run-length list, boundary density, correlation counts by d."""
    g = ["f" if c in "fF" else "s" if c in "sSW" else None for c in row]
    n = len(g)
    runs, cur, ln = [], None, 0
    start = None
    for i in range(n):
        if g[i] is not None and g[i - 1] != g[i]:
            start = i
            break
    if start is not None:
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
    elif any(x is not None for x in g):
        runs = [sum(1 for x in g if x is not None)]
    pairs = diff = 0
    for i in range(n):
        a, b = g[i], g[(i + 1) % n]
        if a is not None and b is not None:
            pairs += 1
            if a != b:
                diff += 1
    corr = []
    for d in range(1, DMAX + 1):
        same = tot = 0
        for i in range(n):
            a, b = g[i], g[(i + d) % n]
            if a is not None and b is not None:
                tot += 1
                if a == b:
                    same += 1
        corr.append((same, tot))
    return runs, (diff, pairs), corr


def eval_point(task):
    arm, m = task
    rules = night10.rules10(arm)
    extra = gen_family.poke_rules("fs")
    imap = gen_family.idx_map(rules, extra)
    rows = []
    for seed in SEEDS:
        tag = f"n12_{arm}_m{m}_s{seed}"
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
        runs_h = Counter()
        bd = [0, 0]
        corr_acc = [[0, 0] for _ in range(DMAX)]
        series = []
        half = len(applies) // 2
        for i, (lhs, idx, ro, co, trig) in enumerate(applies):
            rule = imap[(lhs, idx)]
            for dc, ch in gen_family.writes(rule):
                grid[ro - 1][(co + dc) % RING] = ch
            if (i + 1) % SAMPLE_EVERY == 0 and i >= half:
                runs, (diff, pairs), corr = row_stats(grid[2])
                for r_ in runs:
                    runs_h[r_] += 1
                bd[0] += diff
                bd[1] += pairs
                for d in range(DMAX):
                    corr_acc[d][0] += corr[d][0]
                    corr_acc[d][1] += corr[d][1]
                rm = (sum(runs) / len(runs)) if runs else 0.0
                series.append((diff / pairs if pairs else 0.0, rm))
        if "\n".join("".join(rr) for rr in grid) != "\n".join(
                analyzers.parse_dump(_WORKDIR / f"{tag}.txt", *GEOM)):
            sys.exit(f"EXACT-FAIL {tag}")
        for p in (cfg, d0, _WORKDIR / f"{tag}_i.trace",
                  _WORKDIR / f"{tag}.txt", _WORKDIR / f"{tag}.trace"):
            p.unlink()
        rho = bd[0] / bd[1] if bd[1] else 0.0
        # time-reversal asymmetry of (rho, runmean), per tau
        n = len(series)
        mr = sum(s[0] for s in series) / n
        mm = sum(s[1] for s in series) / n
        asym = []
        for tau in range(1, TAUMAX + 1):
            acc = 0.0
            cnt = 0
            for t in range(n - tau):
                dr0, dm0 = series[t][0] - mr, series[t][1] - mm
                dr1, dm1 = series[t + tau][0] - mr, series[t + tau][1] - mm
                acc += dr0 * dm1 - dr1 * dm0
                cnt += 1
            asym.append(acc / cnt if cnt else 0.0)
        rows.append({"arm": arm, "m": m, "seed": seed, "rho": rho,
                     "runs_h": dict(runs_h),
                     "corr": [(a, b) for a, b in corr_acc],
                     "asym": asym})
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", type=int, default=8)
    ap.add_argument("--workdir", default=None)
    args = ap.parse_args()
    workdir = Path(args.workdir) if args.workdir else \
        Path(tempfile.mkdtemp(prefix="night12_"))
    workdir.mkdir(parents=True, exist_ok=True)
    print(f"workdir {workdir}")
    tasks = [(a, m) for a in ARMS for m in M_VALUES]
    t0 = time.perf_counter()
    with Pool(args.jobs, _pool_init, (str(workdir),)) as pool:
        results = pool.map(eval_point, tasks, chunksize=1)
    rows = [r for res in results for r in res]
    print(f"{len(rows)} runs, wall {time.perf_counter() - t0:.1f}s, "
          f"exactness: all pass\n")

    import csv
    here = Path(__file__).parent
    with open(here / "night12_language.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["arm", "m", "seed", "rho",
                    "runlen_hist", "corr_same_tot", "asym_tau"])
        for r in rows:
            w.writerow([r["arm"], r["m"], r["seed"], f"{r['rho']:.4f}",
                        ";".join(f"{k}:{v}" for k, v
                                 in sorted(r["runs_h"].items())),
                        ";".join(f"{a}/{b}" for a, b in r["corr"]),
                        ";".join(f"{x:.5f}" for x in r["asym"])])

    for arm in ARMS:
        for m in M_VALUES:
            sub = [r for r in rows if r["arm"] == arm and r["m"] == m]
            rho = statistics.mean(r["rho"] for r in sub)
            # P1a: run-length distribution vs geometric(rho)
            hist = Counter()
            for r in sub:
                for k, v in r["runs_h"].items():
                    hist[int(k)] += v
            tot = sum(hist.values())
            meanlen = sum(k * v for k, v in hist.items()) / tot
            p = 1.0 / meanlen
            print(f"{arm} m={m}: rho {rho:.3f}, runs n={tot}, "
                  f"mean length {meanlen:.2f} (geometric p={p:.3f})")
            line1 = "   len:  " + "".join(f"{k:>8}" for k in range(1, 9))
            line2 = "   obs:  " + "".join(
                f"{hist.get(k, 0) / tot:>8.4f}" for k in range(1, 9))
            line3 = "   geom: " + "".join(
                f"{p * (1 - p) ** (k - 1):>8.4f}" for k in range(1, 9))
            tail_obs = sum(v for k, v in hist.items() if k > 8) / tot
            tail_geo = (1 - p) ** 8
            print(line1)
            print(line2 + f"   tail>8 {tail_obs:.4f}")
            print(line3 + f"   tail>8 {tail_geo:.4f}")
            # P1b: correlation decay vs Markov (1-2 rho)^d
            same = [0] * DMAX
            tots = [0] * DMAX
            for r in sub:
                for d in range(DMAX):
                    same[d] += r["corr"][d][0]
                    tots[d] += r["corr"][d][1]
            print("   d:     " + "".join(f"{d:>8}" for d in
                                         range(1, DMAX + 1)))
            print("   C(d):  " + "".join(
                f"{2 * same[d] / tots[d] - 1:>8.3f}"
                for d in range(DMAX)))
            print("   Markov:" + "".join(
                f"{(1 - 2 * rho) ** (d + 1):>8.3f}"
                for d in range(DMAX)))
            # P2: irreversibility
            for tau in (1, 3, 5):
                vals = [r["asym"][tau - 1] for r in sub]
                mu = statistics.mean(vals)
                se = statistics.stdev(vals) / math.sqrt(len(vals))
                print(f"   A(tau={tau}) = {mu:+.5f} "
                      f"(t={mu / se:.2f}, n={len(vals)})")
            print()


if __name__ == "__main__":
    main()
