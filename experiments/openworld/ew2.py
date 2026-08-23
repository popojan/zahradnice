#!/usr/bin/env python3
"""EW-2 — the fuel economy of law-copying (F4, earning the price).

Registered protocol and predictions: ew-design.md §EW-2 (P2-2',
P2-3'). Copying costs one positional fuel token; feed placement is
drive-controlled via half-ring markers. Machinery eternal.

Arms: starve / left / right / both.

Usage: python3 ew2.py [--jobs N] [--seeds N] [--workdir DIR]
Outputs: ew2_runs.csv, summary on stdout.
"""
import argparse
import csv
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

ROWS, RING = 6, 24        # tape=1 marker=2 fuel=3 mach=4 reg=5
CAD, EST, M, BLOCKS = 4, 100, 10, 150
HALF = RING // 2
SPAWNER = R("A", "A", "write", "A")
COPIER = "Π"
FEED = {"starve": "", "left": "ff", "right": "gg", "both": "fg"}

_WORK = None
_CTX = None


def world_bootstrap():
    """One-shot render anchored on a reg-row α: marker halves at
    (−3,·), `.` fuel background at (−2,·), copiers density 1/2 at
    (−1,·)."""
    markers = "<" * HALF + ">" * HALF
    dots = "." * RING
    mach = "".join(COPIER if k % 2 == 0 else " "
                   for k in range(RING))
    body = ("  " + markers + "\n  " + dots + "\n  " + mach.rstrip()
            + "\n@@@")
    writes = ([(0, 0, "α")]
              + [(-3, k, markers[k]) for k in range(RING)]
              + [(-2, k, ".") for k in range(RING)]
              + [(-1, k, COPIER) for k in range(0, RING, 2)])
    return ([("==Zbα", writes)], body)


def feed_rule(marker, trig):
    """Drop fuel below a weight-uniform random half marker."""
    return ([("==" + marker + trig, [(1, 0, "o")])], "@\n@\n@\no")


def build_cfg():
    groups = []
    groups += gen_earned.unstamped_groups(SPAWNER, "α")
    groups.append(gen_earned.copier_copy(COPIER, ["α"],
                                         trig="C", priced=True))
    groups.append(gen_earned.copier_walk(COPIER, ["α"],
                                         trig="C"))
    groups.append(gen_earned.copier_pass(COPIER, trig="C"))
    groups.append(world_bootstrap())
    groups.append(feed_rule("<", "f"))
    groups.append(feed_rule(">", "g"))
    return gen_earned.assemble("ew2 {steps}",
                               ["^Au*", "^αl*", "^Zll"], groups,
                               gen_family.poke_rules())


def copy_keys(imap):
    return {k for k, w in imap.items()
            if any(dr == 1 and ch == "α" for dr, dc, ch in w)}


def inputs(arm, blocks):
    unit = "T" + "C" * CAD
    return ("b" + unit * EST
            + ("p" + FEED[arm] + unit * M) * blocks)


def run_engine(cfg, seed, inp, trace, dump):
    cmd = [str(BIN), "--headless", "--screen", f"{ROWS},{RING}",
           "--seed", str(seed), "--input", inp,
           "--trace", str(trace), "--dump-screen", str(dump), str(cfg)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"engine failed on {cfg}: {r.stderr.strip()}")


def eval_run(task):
    arm, blocks, seed = task
    cfg_path, imap, ckeys, s0 = _CTX
    tag = f"{arm}_{blocks}_s{seed}"
    trace, dump = _WORK / f"{tag}.trace", _WORK / f"{tag}.txt"
    run_engine(Path(cfg_path), seed, inputs(arm, blocks), trace, dump)
    applies = analyzers.parse_trace(trace)
    grid = [list(row) for row in s0]
    copies = [0, 0]
    for lhs, idx, ro, co, _t in applies:
        if (lhs, idx) in ckeys:
            copies[0 if co < HALF else 1] += 1
        for dr, dc, ch in imap[(lhs, idx)]:
            grid[(ro - 1 + dr) % (ROWS - 1)][(co + dc) % RING] = ch
    final = ["".join(r) for r in grid]
    exact = final == list(analyzers.parse_dump(dump, ROWS, RING))
    trace.unlink()
    dump.unlink()
    tape, fuel, reg = final[0], final[2], final[4]
    half_stats = {}
    for side, rng in (("l", range(HALF)), ("r", range(HALF, RING))):
        half_stats[f"alive_{side}"] = sum(
            1 for c in rng if tape[c] in "AB")
        half_stats[f"active_{side}"] = sum(
            1 for c in rng if tape[c] in "AB" and reg[c] == "α")
        half_stats[f"q_{side}"] = sum(
            1 for c in rng if reg[c] == gen_earned.PLACE)
        half_stats[f"fuel_{side}"] = sum(
            1 for c in rng if fuel[c] == "o")
    return {"arm": arm, "blocks": blocks, "seed": seed,
            "exact": exact,
            "copies_l": copies[0], "copies_r": copies[1],
            **half_stats}


def _pool_init(workdir_str, ctx):
    global _WORK, _CTX
    _WORK = Path(workdir_str)
    _CTX = ctx


def probe_init(workdir):
    cfg = workdir / "probe.cfg"
    cfg.write_text(
        "#!probe\n#threads 1\n^Au*\n^αl*\n^Zll\n==zzz\n@@@\n")
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
        Path(tempfile.mkdtemp(prefix="ew2_"))
    workdir.mkdir(parents=True, exist_ok=True)
    print(f"binary {BIN}\nworkdir {workdir}")

    s0 = probe_init(workdir)
    text, imap = build_cfg()
    p = workdir / "ew2.cfg"
    p.write_text(text)
    ctx = (str(p), imap, copy_keys(imap), s0)

    tasks = [(arm, blocks, s) for arm in FEED
             for blocks in (60, BLOCKS)
             for s in range(1, args.seeds + 1)]
    t0 = time.perf_counter()
    if args.jobs > 1:
        with Pool(args.jobs, _pool_init, (str(workdir), ctx)) as pool:
            rows = pool.map(eval_run, tasks, chunksize=4)
    else:
        _pool_init(str(workdir), ctx)
        rows = [eval_run(t) for t in tasks]
    wall = time.perf_counter() - t0
    inexact = [(r["arm"], r["blocks"], r["seed"]) for r in rows
               if not r["exact"]]
    print(f"{len(rows)} runs, wall {wall:.1f}s, "
          f"exactness failures: {len(inexact)}")
    if inexact:
        print(inexact[:10])
        sys.exit("trace<->screen accounting broken; aborting")

    here = Path(__file__).parent
    cols = ["arm", "blocks", "seed", "copies_l", "copies_r",
            "alive_l", "alive_r", "active_l", "active_r", "q_l", "q_r",
            "fuel_l", "fuel_r", "exact"]
    with open(here / "ew2_runs.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for r in sorted(rows, key=lambda r: (r["arm"], r["blocks"],
                                             r["seed"])):
            w.writerow([r[c] for c in cols])

    n = args.seeds
    for blocks in (60, BLOCKS):
        print(f"--- horizon {blocks} blocks")
        for arm in FEED:
            sub = [r for r in rows if r["arm"] == arm
                   and r["blocks"] == blocks]
            agg = {c: sum(r[c] for r in sub) / n for c in cols[3:-1]}
            print(f"{arm:>6}: copies L {agg['copies_l']:.1f} R "
                  f"{agg['copies_r']:.1f}  alive L {agg['alive_l']:.1f}"
                  f" R {agg['alive_r']:.1f}  active L "
                  f"{agg['active_l']:.1f} R {agg['active_r']:.1f}  "
                  f"fuel L {agg['fuel_l']:.1f} R {agg['fuel_r']:.1f}")


if __name__ == "__main__":
    main()
