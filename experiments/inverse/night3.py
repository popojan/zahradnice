#!/usr/bin/env python3
"""Night-3 inverse: the repair phase diagram under SUSTAINED damage.

Subjects: the 16 verified dynamic repairers from night 2 (read from
night2_verify.csv), the unique k=1 static repairer A>A.writeA, and
the night-1 flip-flop as a doomed control. Protocol per run:
establish T*200, bombard with POKES x [p + T*m] for damage interval
m in M_VALUES, then a T*400 recovery window. Measured per run
(analyzers.sustain_verdict): survival, post-bombardment recovery of
the pre (class, period), and population statistics sampled before
each poke (proliferation watch: does damage BREED walkers?).

Questions: (1) collapse threshold m* per mechanism, and does it
track night-2 repair times (walk-to-wound mechanisms should have
larger m* on the larger ring; adjacent-respawn ones should not);
(2) is there a proliferation regime (mean head count > 1) between
health and collapse?

Usage: python3 night3.py [--jobs N] [--workdir DIR]
Outputs: night3_sustain.csv, summary on stdout.
"""
import argparse
import csv
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from multiprocessing import Pool

import gen_family
import analyzers

ROOT = Path(__file__).resolve().parents[2]
BIN = ROOT / "zahradnice"

GEOMS = ((6, 6), (6, 12))
SEEDS = (1, 2, 3, 4, 5, 6)
H_EST, H_FINAL, POKES = 200, 400, 100
M_VALUES = (0, 1, 2, 3, 5, 8, 12, 20, 40)

_WORKDIR = None
_INITS = None


def dyn_satisfiers():
    here = Path(__file__).parent
    by_id = {gen_family.rule_id(r): r for r in gen_family.menu2()}
    out = []
    with open(here / "night2_verify.csv") as f:
        for row in csv.DictReader(f):
            if row["repair_dyn"] == "True":
                out.append(tuple(by_id[x] for x in row["genotype"].split("|")))
    return out


def run_engine(cfg, geom, seed, inp, trace, dump):
    cmd = [str(BIN), "--headless", "--screen", f"{geom[0]},{geom[1]}",
           "--seed", str(seed), "--input", inp, "--dump-screen", str(dump),
           "--trace", str(trace), str(cfg)]
    t0 = time.perf_counter()
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"engine failed ({r.returncode}) on {cfg}: "
                           f"{r.stderr.strip()}")
    return time.perf_counter() - t0


def probe_init(workdir, geom):
    cfg = workdir / f"probe_{geom[0]}x{geom[1]}.cfg"
    cfg.write_text("#!probe\n#threads 1\n^Acc\n==ATB\n@@@\n")
    dump = workdir / f"probe_{geom[0]}x{geom[1]}.txt"
    cmd = [str(BIN), "--headless", "--screen", f"{geom[0]},{geom[1]}",
           "--seed", "1", "--input", "z", "--dump-screen", str(dump),
           str(cfg)]
    subprocess.run(cmd, capture_output=True, text=True)
    return tuple(analyzers.parse_dump(dump, *geom))


def _pool_init(workdir_str, inits):
    global _WORKDIR, _INITS
    _WORKDIR = Path(workdir_str)
    _INITS = inits


def eval_point(task):
    """One (candidate, m) point across all geoms and seeds."""
    ci, rules, m = task
    poke = gen_family.poke_rules()
    cfg = _WORKDIR / f"n3c{ci}.cfg"
    cfg.write_text(gen_family.compile_cfg(rules, f"n3c{ci}", poke))
    inp = "T" * H_EST + ("p" + "T" * m) * POKES + "T" * H_FINAL
    rows, engine_s = [], 0.0
    for geom in GEOMS:
        runs = []
        for seed in SEEDS:
            tag = f"n3c{ci}_m{m}_s{seed}_{geom[1]}"
            trace = _WORKDIR / f"{tag}.trace"
            dump = _WORKDIR / f"{tag}.txt"
            engine_s += run_engine(cfg, geom, seed, inp, trace, dump)
            applies = analyzers.parse_trace(trace)
            states = analyzers.replay(rules, list(_INITS[geom]),
                                      applies, geom[1], poke)
            if states[-1] != "\n".join(analyzers.parse_dump(dump, *geom)):
                sys.exit(f"EXACT-FAIL {tag}")
            runs.append(analyzers.sustain_verdict(states, applies,
                                                  H_EST, H_FINAL))
            trace.unlink()
            dump.unlink()
        n = len(runs)
        rows.append({
            "ci": ci, "gid": gen_family.genotype_id(rules), "k": len(rules),
            "ring": geom[1], "m": m,
            "pre": runs[0]["pre"][0],
            "survival": sum(r["alive"] for r in runs) / n,
            "recovery": sum(r["recovered"] for r in runs) / n,
            "meanA": sum(r["meanA"] for r in runs) / n,
            "meanB": sum(r["meanB"] for r in runs) / n,
            "min_total": min(r["min_total"] for r in runs),
            "max_total": max(r["max_total"] for r in runs),
            "pokes_landed": sum(r["pokes_landed"] for r in runs) / n,
        })
    return {"rows": rows, "engine_s": engine_s}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", type=int, default=1)
    ap.add_argument("--workdir", default=None)
    args = ap.parse_args()
    workdir = Path(args.workdir) if args.workdir else \
        Path(tempfile.mkdtemp(prefix="night3_"))
    workdir.mkdir(parents=True, exist_ok=True)
    print(f"binary {BIN}\nworkdir {workdir}")

    R = gen_family.Rule
    cands = list(dyn_satisfiers())
    cands.append((R("A", "A", "write", "A"),))                # static k*=1
    cands.append((R("A", "B", "self", None),
                  R("B", "A", "self", None)))                 # control
    tasks = [(ci, rules, m) for ci, rules in enumerate(cands)
             for m in M_VALUES]
    print(f"{len(cands)} candidates x {len(M_VALUES)} damage intervals "
          f"x {len(GEOMS)} rings x {len(SEEDS)} seeds "
          f"= {len(tasks) * len(GEOMS) * len(SEEDS)} runs")

    inits = {g: probe_init(workdir, g) for g in GEOMS}
    t0 = time.perf_counter()
    if args.jobs > 1:
        with Pool(args.jobs, _pool_init, (str(workdir), inits)) as pool:
            results = pool.map(eval_point, tasks, chunksize=4)
    else:
        _pool_init(str(workdir), inits)
        results = [eval_point(t) for t in tasks]
    wall = time.perf_counter() - t0
    rows = [r for res in results for r in res["rows"]]
    engine_s = sum(res["engine_s"] for res in results)
    n_runs = len(tasks) * len(GEOMS) * len(SEEDS)
    print(f"wall {wall:.1f}s, engine {engine_s:.1f}s "
          f"({1000 * engine_s / n_runs:.1f} ms/run), exactness: all pass")

    here = Path(__file__).parent
    cols = ["k", "gid", "pre", "ring", "m", "survival", "recovery",
            "meanA", "meanB", "min_total", "max_total", "pokes_landed"]
    with open(here / "night3_sustain.csv", "w", newline="") as f:
        w = csv.DictWriter(f, cols, extrasaction="ignore")
        w.writeheader()
        for r in sorted(rows, key=lambda r: (r["k"], r["gid"],
                                             r["ring"], r["m"])):
            w.writerow({c: (f"{r[c]:.2f}" if isinstance(r[c], float)
                            else r[c]) for c in cols})

    print("\nm* = smallest damage interval with recovery 6/6 "
          "(per ring; '-' = never):")
    gids = sorted({r["gid"] for r in rows},
                  key=lambda g: (min(r["k"] for r in rows
                                     if r["gid"] == g), g))
    for gid in gids:
        line = f"  {gid:<44}"
        for ring in (6, 12):
            ms = [r["m"] for r in rows if r["gid"] == gid
                  and r["ring"] == ring and r["recovery"] == 1.0]
            line += f" ring{ring}: {min(ms) if ms else '-':>3}"
        sub = [r for r in rows if r["gid"] == gid and r["ring"] == 6]
        peak = max(sub, key=lambda r: r["meanA"] + r["meanB"])
        line += (f"  peak-pop@m={peak['m']}: "
                 f"{peak['meanA'] + peak['meanB']:.1f}")
        print(line)


if __name__ == "__main__":
    main()
