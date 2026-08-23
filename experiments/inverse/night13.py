#!/usr/bin/env python3
"""Night-13 inverse: WALLS AS PAID MATTER — containment priced in
the world's own currencies (night-11's identified follow-up; the
M2 opening).

Night 11 showed FREE compartments (rows) never suppress the
order-fueled parasite and at collapse feed it. Night 13 makes
containment physical and priced: a wall `|` is in-row matter that
(a) displaces one gene of tape capacity, (b) taxes every patrol
crossing (arrive |→a, settle a→b, exit b→| — three events against
f's one and s's two, wall preserved behind the head), and
(c) blocks every pattern-window rule across it — gap-bursts and
deceptive yield cannot reach through a wall, because `|` matches
no gene. A head exiting onto a post-wall hole must repair it
blind (50/50 f/s — walls are miscopy hotspots, reported as an
incidental). Walls are permanent in this night (erosion and
wall-repair economics are the registered follow-up); their price
is capacity plus toll, both paid from the one A3 budget.

Wall sets are period-12 ({5,17}, {5,11,17,23},
{2,5,8,11,14,17,20,23}), so the layout is invariant to which of
the two heads (cols 0/12) anchors the placement shot.

Predictions, stated before running (EW-3's abundance/scarcity law
is the prior FOR walls; night 11 is the prior AGAINST):
  P13-1 at m=8, paraonly: rho falls with wall count — walls
    truncate the runs that fuel deceptive yield and physically
    block cross-sector bursts, the excludability free rows never
    had.
  P13-2 at m=2 (collapse): night-11's inversion (+0.054 rho at
    4x12 rows) does NOT appear — walls' rho <= no-walls, or the
    elevation is reduced.
  P13-3 the price: in PLAIN chemistry walls are pure cost (tape
    lower by capacity + toll-starved repair, rho unimproved) —
    containment is insurance, worth the premium only in the
    epidemic.
  P13-4 incidental: boundary density in the 2-gene zone east of
    walls exceeds sector interiors (the blind-repair mutagenic
    flank).

Arms: chem {plain, paraonly} x walls {0, 2, 4, 8} x m {8, 2} x 24
seeds = 384 runs, ring 24, night-7 init (s0 0.5, heads 2),
protocol b + T*32 + (p + T*m)*, 24k events. Exact accounting.

Usage: python3 night13.py [--jobs N] [--workdir DIR]
Outputs: night13_walls.csv, summary on stdout.
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
from night10 import boundary_density

R = gen_family.Rule
ROOT = Path(__file__).resolve().parents[2]
BIN = ROOT / "zahradnice"
RING = 24
GEOM = (6, RING)
TAPE = 2                               # grid index of the tape row
WALLS = {0: (), 2: (5, 17), 4: (5, 11, 17, 23),
         8: (2, 5, 8, 11, 14, 17, 20, 23)}
M_VALUES = (8, 2)
SEEDS = tuple(range(1, 25))

_WORKDIR = None

WALL_RULES = [
    R("F", "f", "reqwrite", "|a"), R("S", "s", "reqwrite", "|a"),
    R("a", "b", "self", None),
    R("b", "|", "reqwrite", "fF"), R("b", "|", "reqwrite", "sW"),
    R("b", "b", "reqwrite", "~f"), R("b", "b", "reqwrite", "~s"),
]


def rules13(chem, nwalls):
    rules = night7.rules7()
    if chem == "paraonly":
        rules += [R("F", "F", "gapwrite", "fs"),
                  R("S", "S", "gapwrite", "sf")]
    if nwalls:
        rules += WALL_RULES
    return rules


def wall_shot(nwalls):
    """Bootstrap rule text + its replay writes: one head paints the
    period-12 wall set on its own row (anchor-invariant)."""
    line = ["@", "@", "@"] + [" "] * (max(WALLS[nwalls]) + 1)
    for d in WALLS[nwalls]:
        line[d + 2] = "|"                 # @3 at index 2: Δcol = d
    return ("==Fb\n" + "".join(line).rstrip() + "\n",
            [(d, "|") for d in WALLS[nwalls]])


def eval_point(task):
    chem, nwalls, m = task
    rules = rules13(chem, nwalls)
    extra = gen_family.poke_rules("fs")
    imap = gen_family.idx_map(rules, extra)
    boot_key = None
    boot_writes = []
    if nwalls:
        n_f = sum(1 for k in imap if k[0] == "F")
        boot_key = ("F", n_f)
        _text, boot_writes = wall_shot(nwalls)
    arrive = {k for k, r in imap.items()
              if r.kind == "reqwrite" and r.arg == "|a"}
    dpair = {k for k, r in imap.items()
             if r.kind == "gapwrite" and r.arg[0] != r.arg[1]}
    rows = []
    for seed in SEEDS:
        tag = f"n13_{chem}_w{nwalls}_m{m}_s{seed}"
        cfg = _WORKDIR / f"{tag}.cfg"
        text = gen_family.compile_cfg(
            rules, tag, extra, night7.init_lines(RING, 0.5))
        if nwalls:
            text += wall_shot(nwalls)[0]
        cfg.write_text(text)
        d0 = _WORKDIR / f"{tag}_i.txt"
        for inp, dump, tr in (
                ("z", d0, _WORKDIR / f"{tag}_i.trace"),
                ("b" + night7.protocol(m), _WORKDIR / f"{tag}.txt",
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
        crossings = deceptive = 0
        for lhs, idx, ro, co, trig in applies:
            k = (lhs, idx)
            if k == boot_key:
                writes = boot_writes
            else:
                writes = gen_family.writes(imap[k])
                if k in arrive:
                    crossings += 1
                elif k in dpair:
                    deceptive += 1
            for dc, ch in writes:
                grid[ro - 1][(co + dc) % RING] = ch
        final = ["".join(rr) for rr in grid]
        if final != list(analyzers.parse_dump(
                _WORKDIR / f"{tag}.txt", *GEOM)):
            sys.exit(f"EXACT-FAIL {tag}")
        tape = final[TAPE]
        rho = boundary_density(tape)
        genes = sum(1 for c in tape if c in "fsFSW")
        cap = RING - nwalls
        wallpos = [i for i, c in enumerate(tape) if c in "|ab"]
        flank = interior = fd = idd = 0
        gmap = ["f" if c in "fF" else "s" if c in "sSW" else None
                for c in tape]
        fzone = set()
        for wp in wallpos:
            fzone |= {(wp + 1) % RING, (wp + 2) % RING}
        for i in range(RING):
            a_, b_ = gmap[i], gmap[(i + 1) % RING]
            if a_ is None or b_ is None:
                continue
            if i in fzone:
                flank += 1
                fd += a_ != b_
            else:
                interior += 1
                idd += a_ != b_
        rows.append({
            "chem": chem, "walls": nwalls, "m": m, "seed": seed,
            "rho": rho, "tape": genes / cap, "crossings": crossings,
            "deceptive": deceptive,
            "rho_flank": fd / flank if flank else None,
            "rho_interior": idd / interior if interior else None})
        for f in _WORKDIR.glob(f"{tag}*"):
            f.unlink()
    return rows


def _pool_init(workdir_str):
    global _WORKDIR
    _WORKDIR = Path(workdir_str)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", type=int, default=12)
    ap.add_argument("--workdir", default=None)
    args = ap.parse_args()
    workdir = Path(args.workdir) if args.workdir else \
        Path(tempfile.mkdtemp(prefix="n13_"))
    workdir.mkdir(parents=True, exist_ok=True)
    print(f"binary {BIN}\nworkdir {workdir}")

    tasks = [(chem, w, m) for chem in ("plain", "paraonly")
             for w in sorted(WALLS) for m in M_VALUES]
    t0 = time.perf_counter()
    with Pool(args.jobs, _pool_init, (str(workdir),)) as pool:
        allrows = [r for chunk in pool.map(eval_point, tasks)
                   for r in chunk]
    wall = time.perf_counter() - t0
    print(f"{len(allrows)} runs, wall {wall:.1f}s, all exact")

    here = Path(__file__).parent
    cols = ["chem", "walls", "m", "seed", "rho", "tape", "crossings",
            "deceptive", "rho_flank", "rho_interior"]
    with open(here / "night13_walls.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for r in sorted(allrows, key=lambda r: (r["chem"], r["m"],
                                                r["walls"], r["seed"])):
            w.writerow([r[c] for c in cols])

    def tstat(xs, ys):
        nx, ny = len(xs), len(ys)
        mx, my = statistics.mean(xs), statistics.mean(ys)
        vx = statistics.variance(xs) if nx > 1 else 0
        vy = statistics.variance(ys) if ny > 1 else 0
        se = (vx / nx + vy / ny) ** 0.5
        return (mx - my) / se if se else 0.0

    for chem in ("plain", "paraonly"):
        for m in M_VALUES:
            base = [r["rho"] for r in allrows
                    if r["chem"] == chem and r["m"] == m
                    and r["walls"] == 0 and r["rho"] is not None]
            line = [f"{chem} m={m}: rho w0 "
                    f"{statistics.mean(base):.3f}"]
            for w_ in (2, 4, 8):
                sub = [r for r in allrows if r["chem"] == chem
                       and r["m"] == m and r["walls"] == w_]
                rs = [r["rho"] for r in sub if r["rho"] is not None]
                tp = statistics.mean(r["tape"] for r in sub)
                cr = statistics.mean(r["crossings"] for r in sub)
                line.append(f"w{w_} {statistics.mean(rs):.3f} "
                            f"(t={tstat(rs, base):+.1f}) "
                            f"tape {tp:.2f} toll {cr:.0f}")
            print("  ".join(line))
    para8 = [r for r in allrows if r["chem"] == "paraonly"
             and r["walls"] > 0 and r["rho_flank"] is not None
             and r["rho_interior"] is not None]
    fl = [r["rho_flank"] for r in para8]
    it = [r["rho_interior"] for r in para8]
    print(f"flank vs interior rho (paraonly, walled): "
          f"{statistics.mean(fl):.3f} vs {statistics.mean(it):.3f} "
          f"(t={tstat(fl, it):+.1f}, n={len(fl)})")


if __name__ == "__main__":
    main()
