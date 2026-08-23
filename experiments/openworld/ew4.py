#!/usr/bin/env python3
"""EW-4 — miscopy rescues the world (F4, earning the mutation channel).

Registered protocol and predictions: ew-design.md §EW-4 (P4-1..4).
All-α world, machinery bootstrapped and decaying; the builder allele
μ is reachable only through sloppy-copier miscopy at repair sites.
Machine error is the only source of law novelty.

Arms: faithful / sloppy_e001 / sloppy_e005 / sloppy_e02 / nowound.

Usage: python3 ew4.py [--jobs N] [--seeds N] [--workdir DIR]
Outputs: ew4_runs.csv, summary on stdout.
"""
import argparse
import csv
import statistics
import sys
import subprocess
import tempfile
import time
from collections import Counter
from pathlib import Path
from multiprocessing import Pool

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "inverse"))
import gen_family
import analyzers
import gen_earned

R = gen_family.Rule
ROOT = Path(__file__).resolve().parents[2]
BIN = ROOT / "zahradnice"

ROWS, RING = 5, 24                  # tape=1 fuel=2 mach=3 reg=4
CAD, EST, M, BLOCKS = 4, 200, 5, 200
EPS_D = 0.01
GLYPHS = ("α", "μ")                 # μ = spawner + build, α = spawner only
SPAWNER = R("A", "A", "write", "A")

ARMS = {                            # arm -> (machine glyph, eps, wounds)
    "faithful": ("Π", 0, True),
    "sloppy_e001": ("π", 0.01, True),
    "sloppy_e005": ("π", 0.05, True),
    "sloppy_e02": ("π", 0.2, True),
    "nowound": ("π", 0.05, False),
}

_WORK = None
_CTX = None


def build_cfg(machine, eps):
    groups = []
    for g in GLYPHS:
        groups += gen_earned.unstamped_groups(SPAWNER, g)
    groups.append(gen_earned.copier_copy(machine, list(GLYPHS),
                                         eps=eps, trig="C"))
    groups.append(gen_earned.copier_walk(machine, list(GLYPHS), trig="C"))
    groups.append(gen_earned.copier_decay(machine, EPS_D, trig="C"))
    groups.append(gen_earned.build_rule("A", "μ", machine, trig="C"))
    groups.append(gen_earned.bootstrap("α", machine, RING, density=2))
    return gen_earned.assemble("ew4 {steps}", ["^Au*", "^αl*"], groups,
                               gen_family.poke_rules())


def inputs(wounds):
    unit = "T" + "C" * CAD
    body = ("p" + unit * M) if wounds else (unit * M)
    return "b" + unit * EST + body * BLOCKS


def run_engine(cfg, seed, inp, trace, dump):
    cmd = [str(BIN), "--headless", "--screen", f"{ROWS},{RING}",
           "--seed", str(seed), "--input", inp,
           "--trace", str(trace), "--dump-screen", str(dump), str(cfg)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"engine failed on {cfg}: {r.stderr.strip()}")


def eval_run(task):
    arm, seed = task
    machine, eps, wounds = ARMS[arm]
    cfg_path, imap, s0 = _CTX[arm]
    tag = f"{arm}_s{seed}"
    trace, dump = _WORK / f"{tag}.trace", _WORK / f"{tag}.txt"
    run_engine(Path(cfg_path), seed, inputs(wounds), trace, dump)
    applies = analyzers.parse_trace(trace)
    grid = [list(row) for row in s0]
    first_mu = None
    for j, (lhs, idx, ro, co, _t) in enumerate(applies):
        for dr, dc, ch in imap[(lhs, idx)]:
            rr = (ro - 1 + dr) % (ROWS - 1)
            cc = (co + dc) % RING
            if (ch == "μ" and rr == 3 and grid[rr][cc] != "μ"
                    and first_mu is None):
                first_mu = j
            grid[rr][cc] = ch
    final = ["".join(r) for r in grid]
    exact = final == list(analyzers.parse_dump(dump, ROWS, RING))
    trace.unlink()
    dump.unlink()
    tape, mach, reg = final[0], final[2], final[3]
    gates = Counter(reg)
    alive = sum(tape.count(c) for c in "AB")
    copiers = mach.count(machine)
    rescued = alive >= RING // 2 and copiers >= 1
    return {"arm": arm, "seed": seed, "exact": exact,
            "rescued": rescued, "alive": alive,
            "gates_a": gates.get("α", 0), "gates_m": gates.get("μ", 0),
            "qmarks": gates.get(gen_earned.PLACE, 0),
            "copiers": copiers,
            "first_mu": first_mu if first_mu is not None else -1,
            "events": len(applies)}


def _pool_init(workdir_str, ctx):
    global _WORK, _CTX
    _WORK = Path(workdir_str)
    _CTX = ctx


def probe_init(workdir):
    cfg = workdir / "probe.cfg"
    cfg.write_text("#!probe\n#threads 1\n^Au*\n^αl*\n==zzz\n@@@\n")
    dump = workdir / "probe.txt"
    run_engine(cfg, 1, "q", workdir / "probe.trace", dump)
    return tuple(analyzers.parse_dump(dump, ROWS, RING))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", type=int, default=12)
    ap.add_argument("--seeds", type=int, default=100)
    ap.add_argument("--workdir", default=None)
    args = ap.parse_args()
    workdir = Path(args.workdir) if args.workdir else \
        Path(tempfile.mkdtemp(prefix="ew4_"))
    workdir.mkdir(parents=True, exist_ok=True)
    print(f"binary {BIN}\nworkdir {workdir}")

    s0 = probe_init(workdir)
    ctx = {}
    for arm, (machine, eps, _w) in ARMS.items():
        text, imap = build_cfg(machine, eps)
        p = workdir / f"{arm}.cfg"
        p.write_text(text)
        ctx[arm] = (str(p), imap, s0)

    tasks = [(arm, s) for arm in ARMS
             for s in range(1, args.seeds + 1)]
    t0 = time.perf_counter()
    if args.jobs > 1:
        with Pool(args.jobs, _pool_init, (str(workdir), ctx)) as pool:
            rows = pool.map(eval_run, tasks, chunksize=4)
    else:
        _pool_init(str(workdir), ctx)
        rows = [eval_run(t) for t in tasks]
    wall = time.perf_counter() - t0
    inexact = [(r["arm"], r["seed"]) for r in rows if not r["exact"]]
    print(f"{len(rows)} runs, wall {wall:.1f}s, "
          f"exactness failures: {len(inexact)}")
    if inexact:
        print(inexact[:10])
        sys.exit("trace<->screen accounting broken; aborting")

    here = Path(__file__).parent
    cols = ["arm", "seed", "rescued", "alive", "gates_a", "gates_m",
            "qmarks", "copiers", "first_mu", "events", "exact"]
    with open(here / "ew4_runs.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for r in sorted(rows, key=lambda r: (r["arm"], r["seed"])):
            w.writerow([r[c] for c in cols])

    n = args.seeds
    for arm in ARMS:
        sub = [r for r in rows if r["arm"] == arm]
        resc = sum(r["rescued"] for r in sub)
        alive = sum(r["alive"] for r in sub) / n
        gm = sum(r["gates_m"] for r in sub) / n
        cp = sum(r["copiers"] for r in sub) / n
        disc = [r["first_mu"] for r in sub if r["first_mu"] >= 0]
        med = statistics.median(disc) if disc else None
        print(f"{arm:>12}: rescued {resc}/{n}  alive {alive:.1f}/24  "
              f"gates_mu {gm:.1f}  copiers {cp:.1f}  "
              f"mu discovered in {len(disc)}/{n}"
              + (f" (median apply {med:.0f})" if disc else ""))


if __name__ == "__main__":
    main()
