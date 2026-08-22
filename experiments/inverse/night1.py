#!/usr/bin/env python3
"""Night-1 calibration inverse: exhaustively search strata k=1,2 of
family F1 (gen_family) for oscillators, with exact accounting.

Per candidate x seed: compile cfg -> run the real engine headless
(--trace + --dump-screen) -> reconstruct the state trajectory from
the trace -> verify the final state EXACTLY against the dump ->
classify (analyzers). Sweep on a 6-ring; satisfiers of either
oscillator predicate are re-verified on held-out seeds, a longer
horizon, and a second ring size (8) as a robustness poke.

The calibration question: does exhaustion recover the expected
predicate-dependent minima —
  P_state (global state recurs):    k* = 1 (torus walkers)
  P_pop   (populations oscillate):  k* = 2 (flip-flop family)
— and what does a COMPLETE census of minimal mechanisms look like?

Usage: python3 night1.py [--jobs N] [--workdir DIR]
Outputs: night1_sweep.csv, night1_verify.csv, summary on stdout.
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

ROOT = Path(__file__).resolve().parents[2]
BIN = ROOT / "zahradnice"

GEOM_SWEEP = (6, 6)            # --screen R,C: playfield (R-1)xC, ring = C
H_SWEEP = 200
SEEDS_SWEEP = (1, 2, 3)
H_VERIFY = 1000
SEEDS_VERIFY = (11, 12, 13)
GEOMS_VERIFY = ((6, 6), (6, 8))

_WORKDIR = None
_INITS = None


def run_engine(cfg, geom, seed, inp, trace, dump):
    cmd = [str(BIN), "--headless", "--screen", f"{geom[0]},{geom[1]}",
           "--seed", str(seed), "--input", inp, "--dump-screen", str(dump)]
    if trace:
        cmd += ["--trace", str(trace)]
    cmd.append(str(cfg))
    t0 = time.perf_counter()
    r = subprocess.run(cmd, capture_output=True, text=True)
    dt = time.perf_counter() - t0
    if r.returncode != 0:
        raise RuntimeError(f"engine failed ({r.returncode}) on {cfg}: "
                           f"{r.stderr.strip()}")
    return dt


def probe_init(workdir, geom):
    """Initial screen for ^Acc at this geometry, from the engine itself
    (input 'z' triggers nothing -> dump = initial state)."""
    cfg = workdir / f"probe_{geom[0]}x{geom[1]}.cfg"
    cfg.write_text("#!probe\n#threads 1\n^Acc\n==ATB\n@@@\n")
    dump = workdir / f"probe_{geom[0]}x{geom[1]}.txt"
    run_engine(cfg, geom, seed=1, inp="z", trace=None, dump=dump)
    return tuple(analyzers.parse_dump(dump, *geom))


def _pool_init(workdir_str, inits):
    global _WORKDIR, _INITS
    _WORKDIR = Path(workdir_str)
    _INITS = inits


def eval_candidate(task):
    """One candidate over a run matrix; returns per-run classes plus
    exactness flags and the engine-time ledger."""
    ci, rules, seeds, horizon, geoms = task
    cfg = _WORKDIR / f"c{ci}.cfg"
    cfg.write_text(gen_family.compile_cfg(rules, f"c{ci}"))
    runs, engine_s = [], 0.0
    for geom in geoms:
        for seed in seeds:
            tag = f"c{ci}_s{seed}_{geom[0]}x{geom[1]}"
            trace = _WORKDIR / f"{tag}.trace"
            dump = _WORKDIR / f"{tag}.txt"
            engine_s += run_engine(cfg, geom, seed, "T" * horizon,
                                   trace, dump)
            applies = analyzers.parse_trace(trace)
            states = analyzers.replay(rules, list(_INITS[geom]),
                                      applies, geom[1])
            exact = states[-1] == "\n".join(
                analyzers.parse_dump(dump, *geom))
            cls, period, transient = analyzers.classify(states, horizon)
            runs.append({"geom": geom, "seed": seed, "class": cls,
                         "period": period, "transient": transient,
                         "exact": exact, "applies": len(applies)})
            trace.unlink()
            dump.unlink()
    return {"ci": ci, "gid": gen_family.genotype_id(rules),
            "k": len(rules), "runs": runs, "engine_s": engine_s}


def consensus(runs):
    cs = [r["class"] for r in runs]
    if len(set(cs)) == 1:
        return cs[0]
    return "MIXED:" + ",".join(f"{c}x{n}" for c, n
                               in sorted(Counter(cs).items()))


def sweep_stage(pool_args, candidates, seeds, horizon, geoms, label):
    tasks = [(ci, rules, seeds, horizon, geoms)
             for ci, rules in candidates]
    t0 = time.perf_counter()
    if pool_args["jobs"] > 1:
        with Pool(pool_args["jobs"], _pool_init,
                  (pool_args["workdir"], pool_args["inits"])) as pool:
            results = pool.map(eval_candidate, tasks, chunksize=8)
    else:
        _pool_init(pool_args["workdir"], pool_args["inits"])
        results = [eval_candidate(t) for t in tasks]
    wall = time.perf_counter() - t0
    n_runs = sum(len(r["runs"]) for r in results)
    engine_s = sum(r["engine_s"] for r in results)
    inexact = [(r["gid"], run) for r in results
               for run in r["runs"] if not run["exact"]]
    print(f"[{label}] {len(tasks)} candidates, {n_runs} runs, "
          f"wall {wall:.1f}s, engine {engine_s:.1f}s "
          f"({1000 * engine_s / n_runs:.1f} ms/run, "
          f"{n_runs * horizon / engine_s:,.0f} attempted-events/s), "
          f"exactness failures: {len(inexact)}")
    if inexact:
        for gid, run in inexact[:10]:
            print(f"  EXACT-FAIL {gid} {run}")
        sys.exit(f"[{label}] trace<->screen accounting broken; aborting")
    return results


def write_csv(path, results):
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["k", "genotype", "consensus", "classes", "periods",
                    "transients", "p_state", "p_pop"])
        for r in sorted(results, key=lambda r: (r["k"], r["gid"])):
            cs = [x["class"] for x in r["runs"]]
            w.writerow([
                r["k"], r["gid"], consensus(r["runs"]),
                ";".join(cs),
                ";".join(str(x["period"]) for x in r["runs"]),
                ";".join(str(x["transient"]) for x in r["runs"]),
                analyzers.p_state(cs), analyzers.p_pop(cs)])


def census(results, label):
    print(f"\n[{label}] census by consensus class:")
    for k in sorted({r["k"] for r in results}):
        cnt = Counter(consensus(r["runs"]) for r in results
                      if r["k"] == k)
        for cls, n in sorted(cnt.items(), key=lambda x: -x[1]):
            print(f"  k={k}  {cls:<18} {n}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", type=int, default=1)
    ap.add_argument("--workdir", default=None)
    args = ap.parse_args()

    workdir = Path(args.workdir) if args.workdir else \
        Path(tempfile.mkdtemp(prefix="night1_"))
    workdir.mkdir(parents=True, exist_ok=True)
    print(f"binary {BIN}\nworkdir {workdir}")

    geoms = sorted(set([GEOM_SWEEP]) | set(GEOMS_VERIFY))
    inits = {}
    _pool_init(str(workdir), None)
    for geom in geoms:
        inits[geom] = probe_init(workdir, geom)
    pool_args = {"jobs": args.jobs, "workdir": str(workdir),
                 "inits": inits}

    candidates = [(ci, rules) for ci, rules in
                  enumerate(gen_family.stratum(1) + gen_family.stratum(2))]
    results = sweep_stage(pool_args, candidates, SEEDS_SWEEP, H_SWEEP,
                          (GEOM_SWEEP,), "sweep")
    here = Path(__file__).parent
    write_csv(here / "night1_sweep.csv", results)
    census(results, "sweep")

    sat = [r for r in results
           if analyzers.p_state([x["class"] for x in r["runs"]])]
    by_ci = {ci: rules for ci, rules in candidates}
    print(f"\n[sweep] P_state satisfiers: {len(sat)} "
          f"(k=1: {sum(1 for r in sat if r['k'] == 1)}, "
          f"k=2: {sum(1 for r in sat if r['k'] == 2)}); "
          f"verifying ALL of them (held-out seeds {SEEDS_VERIFY}, "
          f"H={H_VERIFY}, rings {[g[1] for g in GEOMS_VERIFY]})")
    vtasks = [(r["ci"], by_ci[r["ci"]]) for r in sat]
    vresults = sweep_stage(pool_args, vtasks, SEEDS_VERIFY, H_VERIFY,
                           GEOMS_VERIFY, "verify")
    write_csv(here / "night1_verify.csv", vresults)
    census(vresults, "verify")

    for pred, fn in (("P_state", analyzers.p_state),
                     ("P_pop", analyzers.p_pop)):
        ver = [r for r in vresults
               if fn([x["class"] for x in r["runs"]])]
        ks = sorted({r["k"] for r in ver})
        kmin = ks[0] if ks else None
        print(f"\n{pred}: verified satisfiers {len(ver)}, min k = {kmin}")
        for r in sorted(ver, key=lambda r: (r["k"], r["gid"])):
            if r["k"] == kmin:
                ps = sorted({x["period"] for x in r["runs"]})
                print(f"  k={r['k']}  {r['gid']:<40} periods {ps}")


if __name__ == "__main__":
    main()
