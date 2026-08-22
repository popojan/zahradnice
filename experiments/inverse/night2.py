#!/usr/bin/env python3
"""Night-2 inverse: minimal SELF-REPAIR under point deletion.

Family F2 (gen_family.menu2, 96 rules: F1 + the combined
require-east+write-east shape), strata k=1,2 exhausted. Harness law
appended to every candidate (not counted in k): byte 'p' erases one
weight-uniform random matter cell (gen_family.poke_rules).

Protocol per run: T*H_EST establish, then ROUNDS x [p + T*H_REC].
Segments are delimited by the poke applies in the trace and
classified with the night-1 classifier; a candidate REPAIRS when
every post-damage segment re-establishes the pre-damage
(class, period) — see analyzers.repair_verdict.

Predicates (all-seeds consensus, identical pre behaviour required):
  P_repair_static  pre FIXED       — structure heals
  P_repair_dyn     pre TRANSLATION/POP_OSC — behaviour heals
Night-1 winners are expected to FAIL P_repair_dyn (single-cell
oscillators die to one poke); whether ANY k<=2 rule-set repairs a
dynamic behaviour is the discovery question of the night.

Usage: python3 night2.py [--jobs N] [--workdir DIR]
Outputs: night2_sweep.csv, night2_verify.csv, summary on stdout.
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

GEOM_SWEEP = (6, 6)
SEEDS_SWEEP = (1, 2, 3)
H_EST, H_REC, ROUNDS = 200, 200, 3
SEEDS_VERIFY = (11, 12, 13)
GEOMS_VERIFY = ((6, 6), (6, 8))
H_EST_V, H_REC_V, ROUNDS_V = 400, 400, 5

_WORKDIR = None
_INITS = None


def protocol(h_est, h_rec, rounds):
    return "T" * h_est + ("p" + "T" * h_rec) * rounds


def run_engine(cfg, geom, seed, inp, trace, dump):
    cmd = [str(BIN), "--headless", "--screen", f"{geom[0]},{geom[1]}",
           "--seed", str(seed), "--input", inp, "--dump-screen", str(dump)]
    if trace:
        cmd += ["--trace", str(trace)]
    cmd.append(str(cfg))
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
    run_engine(cfg, geom, seed=1, inp="z", trace=None, dump=dump)
    return tuple(analyzers.parse_dump(dump, *geom))


def _pool_init(workdir_str, inits):
    global _WORKDIR, _INITS
    _WORKDIR = Path(workdir_str)
    _INITS = inits


def eval_candidate(task):
    ci, rules, seeds, hs, geoms = task
    h_est, h_rec, rounds = hs
    poke = gen_family.poke_rules()
    cfg = _WORKDIR / f"n2c{ci}.cfg"
    cfg.write_text(gen_family.compile_cfg(rules, f"n2c{ci}", poke))
    inp = protocol(h_est, h_rec, rounds)
    runs, engine_s = [], 0.0
    for geom in geoms:
        for seed in seeds:
            tag = f"n2c{ci}_s{seed}_{geom[0]}x{geom[1]}"
            trace = _WORKDIR / f"{tag}.trace"
            dump = _WORKDIR / f"{tag}.txt"
            engine_s += run_engine(cfg, geom, seed, inp, trace, dump)
            applies = analyzers.parse_trace(trace)
            states = analyzers.replay(rules, list(_INITS[geom]),
                                      applies, geom[1], poke)
            exact = states[-1] == "\n".join(
                analyzers.parse_dump(dump, *geom))
            v = analyzers.repair_verdict(states, applies,
                                         h_est, h_rec, rounds)
            v.update(geom=geom, seed=seed, exact=exact)
            runs.append(v)
            trace.unlink()
            dump.unlink()
    return {"ci": ci, "gid": gen_family.genotype_id(rules),
            "k": len(rules), "runs": runs, "engine_s": engine_s}


def consensus(runs):
    """(pre-consensus, outcome-consensus): each the common value or
    MIXED:...; repair claims additionally need identical pre."""
    pres = [f"{r['pre'][0]}/p{r['pre'][1]}" for r in runs]
    outs = [r["outcome"] for r in runs]
    mix = lambda xs: xs[0] if len(set(xs)) == 1 else \
        "MIXED:" + ",".join(f"{v}x{n}" for v, n in sorted(Counter(xs).items()))
    return mix(pres), mix(outs)


def repairs(runs, pre_classes):
    """All runs REPAIR, one pre class everywhere, and one pre period
    per geometry (walker periods legitimately scale with ring size)."""
    if not all(r["outcome"] == "REPAIR" for r in runs):
        return False
    if len({r["pre"][0] for r in runs}) != 1 \
            or runs[0]["pre"][0] not in pre_classes:
        return False
    by_geom = {}
    for r in runs:
        by_geom.setdefault(r["geom"], set()).add(r["pre"][1])
    return all(len(ps) == 1 for ps in by_geom.values())


def sweep_stage(pool_args, candidates, seeds, hs, geoms, label):
    tasks = [(ci, rules, seeds, hs, geoms) for ci, rules in candidates]
    t0 = time.perf_counter()
    if pool_args["jobs"] > 1:
        with Pool(pool_args["jobs"], _pool_init,
                  (pool_args["workdir"], pool_args["inits"])) as pool:
            results = pool.map(eval_candidate, tasks, chunksize=16)
    else:
        _pool_init(pool_args["workdir"], pool_args["inits"])
        results = [eval_candidate(t) for t in tasks]
    wall = time.perf_counter() - t0
    n_runs = sum(len(r["runs"]) for r in results)
    engine_s = sum(r["engine_s"] for r in results)
    inexact = [(r["gid"], run["seed"]) for r in results
               for run in r["runs"] if not run["exact"]]
    print(f"[{label}] {len(tasks)} candidates, {n_runs} runs, "
          f"wall {wall:.1f}s, engine {engine_s:.1f}s "
          f"({1000 * engine_s / n_runs:.1f} ms/run), "
          f"exactness failures: {len(inexact)}")
    if inexact:
        print(inexact[:10])
        sys.exit(f"[{label}] trace<->screen accounting broken; aborting")
    return results


def write_csv(path, results):
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["k", "genotype", "pre", "outcome", "round_classes",
                    "fixed_identical", "repair_static", "repair_dyn"])
        for r in sorted(results, key=lambda r: (r["k"], r["gid"])):
            pre, out = consensus(r["runs"])
            w.writerow([
                r["k"], r["gid"], pre, out,
                ";".join(f"{c}/p{p}" for run in r["runs"]
                         for c, p in run["rounds"]),
                ";".join(str(run["fixed_identical"]) for run in r["runs"]),
                repairs(r["runs"], {"FIXED"}),
                repairs(r["runs"], analyzers.DYNAMIC)])


def census(results, label):
    print(f"\n[{label}] census by (pre, outcome) consensus:")
    for k in sorted({r["k"] for r in results}):
        cnt = Counter(consensus(r["runs"]) for r in results if r["k"] == k)
        for (pre, out), n in sorted(cnt.items(), key=lambda x: -x[1])[:14]:
            print(f"  k={k}  {pre:<22} {out:<16} {n}")
        rest = sum(n for _, n in sorted(cnt.items(),
                                        key=lambda x: -x[1])[14:])
        if rest:
            print(f"  k={k}  (long tail)          {'':<16} {rest}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", type=int, default=1)
    ap.add_argument("--workdir", default=None)
    args = ap.parse_args()

    workdir = Path(args.workdir) if args.workdir else \
        Path(tempfile.mkdtemp(prefix="night2_"))
    workdir.mkdir(parents=True, exist_ok=True)
    print(f"binary {BIN}\nworkdir {workdir}")

    geoms = sorted(set([GEOM_SWEEP]) | set(GEOMS_VERIFY))
    inits = {g: probe_init(workdir, g) for g in geoms}
    pool_args = {"jobs": args.jobs, "workdir": str(workdir),
                 "inits": inits}

    m2 = gen_family.menu2()
    candidates = list(enumerate(gen_family.stratum(1, m2)
                                + gen_family.stratum(2, m2)))
    results = sweep_stage(pool_args, candidates, SEEDS_SWEEP,
                          (H_EST, H_REC, ROUNDS), (GEOM_SWEEP,), "sweep")
    here = Path(__file__).parent
    write_csv(here / "night2_sweep.csv", results)
    census(results, "sweep")

    sat = [r for r in results
           if repairs(r["runs"], analyzers.GOOD_PRE)
           or consensus(r["runs"])[1] == "POKE_ACTIVATED"]
    by_ci = dict(candidates)
    n_stat = sum(1 for r in sat if repairs(r["runs"], {"FIXED"}))
    n_dyn = sum(1 for r in sat if repairs(r["runs"], analyzers.DYNAMIC))
    print(f"\n[sweep] REPAIR satisfiers: static {n_stat}, dynamic {n_dyn}; "
          f"poke-activated {len(sat) - n_stat - n_dyn}; verifying all "
          f"{len(sat)} (seeds {SEEDS_VERIFY}, rings "
          f"{[g[1] for g in GEOMS_VERIFY]}, {ROUNDS_V} pokes, "
          f"H={H_EST_V}/{H_REC_V})")
    vresults = sweep_stage(pool_args, [(r["ci"], by_ci[r["ci"]])
                                       for r in sat],
                           SEEDS_VERIFY, (H_EST_V, H_REC_V, ROUNDS_V),
                           GEOMS_VERIFY, "verify")
    write_csv(here / "night2_verify.csv", vresults)
    census(vresults, "verify")

    for name, classes in (("P_repair_static", {"FIXED"}),
                          ("P_repair_dyn", analyzers.DYNAMIC)):
        ver = [r for r in vresults if repairs(r["runs"], classes)]
        ks = sorted({r["k"] for r in ver})
        kmin = ks[0] if ks else None
        print(f"\n{name}: verified satisfiers {len(ver)}, min k = {kmin}")
        for r in sorted(ver, key=lambda r: (r["k"], r["gid"])):
            pre, _ = consensus(r["runs"])
            print(f"  k={r['k']}  {r['gid']:<44} pre {pre}")


if __name__ == "__main__":
    main()
