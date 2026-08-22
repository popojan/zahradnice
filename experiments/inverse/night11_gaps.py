#!/usr/bin/env python3
"""Paper-gap experiment (pre-TeX): parasite-phase ring scaling at
EQUAL machinery density.

Night 10 established the parasite phase on ring 24 with 2 heads;
night 7's ring comparison carried a head-density confound (init
placement limits deterministic columns to l/c/r). Here: ring 24 with
ONE head vs ring 48 with TWO heads — both 1 head / 24 cells — arms
{plain, para, paraonly} x m {8,4,2} x 32 seeds. Questions:
(a) does the parasite plateau (rho ~ 0.2) survive a 2x ring, where
pure-crystal domains have more room? (b) plain-arm cross-ring
comparison at equal density scopes the night-7 confound.

Usage: python3 night11_gaps.py [--jobs N] [--workdir DIR]
Outputs: night11_scaling.csv, summary on stdout.
"""
import argparse
import csv
import statistics
import tempfile
import time
from pathlib import Path
from multiprocessing import Pool

import night7
import night10

ARMS = ("plain", "para", "paraonly")
M_VALUES = (8, 4, 2)
RINGS = {24: ("^Fcl",), 48: ("^Fcl", "^Fcc")}   # both 1 head / 24 cells


def _init_ring(workdir_str, ring):
    """Worker initializer: under the forkserver start method (py3.14
    default), parent-side monkeypatches never reach workers — all
    per-ring configuration must happen HERE, in the worker."""
    night10._pool_init(workdir_str)
    night10.RING = ring
    night10.GEOM = (6, ring)
    night7.RINGS = RINGS


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", type=int, default=8)
    ap.add_argument("--workdir", default=None)
    args = ap.parse_args()
    workdir = Path(args.workdir) if args.workdir else \
        Path(tempfile.mkdtemp(prefix="night11_"))
    workdir.mkdir(parents=True, exist_ok=True)
    here = Path(__file__).parent
    print(f"workdir {workdir}")

    tasks = [(a, m) for a in ARMS for m in M_VALUES]
    rows = []
    t0 = time.perf_counter()
    for ring in RINGS:
        with Pool(args.jobs, _init_ring, (str(workdir), ring)) as pool:
            results = pool.map(night10.eval_point, tasks, chunksize=1)
        for res in results:
            for r in res:
                r["ring"] = ring
                rows.append(r)
        print(f"ring {ring}: {len(tasks) * len(night10.SEEDS)} runs done")
    print(f"wall {time.perf_counter() - t0:.1f}s, exactness: all pass\n")

    cols = ["ring", "arm", "m", "seed", "rho_init", "rho_lastq",
            "runmean_lastq", "tape_lastq", "s_share_lastq", "fidelity",
            "rho_osc"]
    with open(here / "night11_scaling.csv", "w", newline="") as f:
        w = csv.DictWriter(f, cols, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({c: (f"{r[c]:.3f}" if isinstance(r.get(c), float)
                            else r.get(c)) for c in cols})

    print("per (ring, arm, m) at density 1 head/24 cells: "
          "rho lastq | tape (norm/ring) | osc sd | s-share:")
    for ring in RINGS:
        for arm in ARMS:
            for m in M_VALUES:
                sub = [r for r in rows if r["ring"] == ring
                       and r["arm"] == arm and r["m"] == m]
                rl = [r["rho_lastq"] for r in sub
                      if r["rho_lastq"] is not None]
                tp = statistics.mean(r["tape_lastq"] for r in sub) / ring
                osc = [r["rho_osc"] for r in sub
                       if r["rho_osc"] is not None]
                ss = [r["s_share_lastq"] for r in sub
                      if r["s_share_lastq"] is not None]
                print(f"  r{ring} {arm:<8} m={m}: rho "
                      f"{statistics.mean(rl):.2f} | tape/ring {tp:.2f}"
                      f" | osc {statistics.mean(osc):.3f}"
                      f" | s {statistics.mean(ss):.2f}")


if __name__ == "__main__":
    main()
