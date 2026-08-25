#!/usr/bin/env python3
"""EW-11 — walls are linkage: the unit of selection, re-earned (F4).

Registered protocol and predictions: ew-design.md §EW-11
(P11-1..4). Full-column walls make sectors that hold their own
description, machinery, law, and matter; sector genomes encode
faithful (b) or sloppy (p) copiers; only machine error can
discover the robust allele μ. Sparse tape seeding gives the
growth phase where stamps (and hence miscopies) happen.
Arms: walls-mixed / open-mixed / walls-faithful / walls-sloppy.

Usage: python3 ew11.py [--jobs N] [--seeds N] [--workdir DIR]
Outputs: ew11_runs.csv, summary on stdout.
"""
import argparse
import csv
import statistics
import sys
import subprocess
import tempfile
import time
from pathlib import Path
from multiprocessing import Pool

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "inverse"))
import gen_family
import analyzers
import gen_earned

R = gen_family.Rule
ROOT = Path(__file__).resolve().parents[2]
BIN = ROOT / "zahradnice"

ROWS, RING = 6, 64        # tape=1 fuel=2 code=3 mach=4 reg=5
CAD, EST, M, BLOCKS = 16, 200, 10, 120
EPS_D, EPS = 0.005, 0.2
FAITH, SLOPPY, XLATOR = "Π", "π", "Ω"
CODONS = {"b": FAITH, "p": SLOPPY, "w": XLATOR}
SECT = 16
WALL_COLS = tuple(SECT * i + SECT - 1 for i in range(RING // SECT))
W_OFF, M_OFF = (0, 8), (2, 4, 6, 10, 12)
A_OFF = (1, 5, 9, 13)

ALLELES = {"α": [R("A", "B", "write", "A")],
           "μ": [R("A", "B", "write", "A"), R("B", "A", "req", "~")]}

ARMS = {                  # arm -> (walls, genome per sector)
    "walls-mixed": (True, ("p", "b", "p", "b")),
    "open-mixed": (False, ("p", "b", "p", "b")),
    "walls-faithful": (True, ("b", "b", "b", "b")),
    "walls-sloppy": (True, ("p", "p", "p", "p")),
}

_WORK = None
_CTX = None


def world_bootstrap(arm):
    walls, genomes = ARMS[arm]
    rows = {r: {} for r in (-4, -3, -2, -1, 0)}   # tape fuel code mach reg
    for s, genome in enumerate(genomes):
        base = SECT * s
        for off in A_OFF:
            rows[-4][base + off] = "A"
        for off in W_OFF:
            rows[-2][base + off] = "w"
            rows[-1][base + off + 1] = XLATOR
        for off in M_OFF:
            rows[-2][base + off] = genome
            rows[-1][base + off + 1] = CODONS[genome]
    rows[-3][0] = "."          # keeps the fuel body line non-blank
    if walls:
        for c in WALL_COLS:
            for r in rows:
                rows[r][c] = "|"
    lines = []
    for r in (-4, -3, -2, -1):
        line = "".join(rows[r].get(k, " ") for k in range(RING))
        lines.append("  " + line.rstrip())
    anchor = ["@", "@", "@"] + [" "] * RING
    anchor[2] = "@"
    for c, g in rows[0].items():
        anchor[c + 2] = g
    body = "\n".join(lines) + "\n" + "".join(anchor).rstrip()
    writes = [(0, 0, "α")] if 0 not in rows[0] else []
    for r in (-4, -3, -2, -1, 0):
        writes += [(r, k, g) for k, g in sorted(rows[r].items())]
    return ([("==Zbα", writes)], body)


def machine_groups(glyph, eps):
    fw = 1 - eps if eps else 1
    return [gen_earned.copier_copy(glyph, ["α", "μ"], eps=eps,
                                   trig="C", faith_w=fw),
            gen_earned.copier_walk(glyph, ["α", "μ"], trig="C"),
            gen_earned.copier_pass(glyph, trig="C"),
            gen_earned.copier_decay(glyph, EPS_D, trig="C"),
            gen_earned.wall_hop(glyph, w=0.05, trig="C")]


def build_cfg(arm):
    groups = []
    for g, rules in ALLELES.items():
        for r in rules:
            groups += gen_earned.unstamped_groups(r, g)
    groups += machine_groups(FAITH, 0)
    groups += machine_groups(SLOPPY, EPS)
    groups += gen_earned.translator_rules(XLATOR, CODONS, trig="C")
    groups.append(gen_earned.copier_decay(XLATOR, EPS_D, trig="C"))
    groups.append(gen_earned.wall_hop(XLATOR, w=0.05, trig="C"))
    groups.append(world_bootstrap(arm))
    text, imap = gen_earned.assemble(
        "ew11 {steps}", ["^αl*", "^Zll"], groups,
        gen_family.poke_rules())
    return text, imap, groups


def key_kinds(groups):
    kinds, per = {}, {}
    for heads, _body in groups:
        for h, w in heads:
            lhs = h[2]
            i = per.get(lhs, 0)
            per[lhs] = i + 1
            if lhs == SLOPPY and len(h) > 8 and h[7] == "α" \
                    and h[8] == "μ":
                kinds[(lhs, i)] = "discover"
    return kinds


def inputs():
    unit = "T" + "C" * CAD
    return "b" + unit * EST + ("p" + unit * M) * BLOCKS


def run_engine(cfg, seed, inp, trace, dump):
    cmd = [str(BIN), "--headless", "--screen", f"{ROWS},{RING}",
           "--seed", str(seed), "--input", inp,
           "--trace", str(trace), "--dump-screen", str(dump), str(cfg)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"engine failed on {cfg}: {r.stderr.strip()}")


def eval_run(task):
    arm, seed = task
    walls, genomes = ARMS[arm]
    cfg_path, imap, kinds, s0 = _CTX[arm]
    tag = f"{arm}_s{seed}"
    trace, dump = _WORK / f"{tag}.trace", _WORK / f"{tag}.txt"
    run_engine(Path(cfg_path), seed, inputs(), trace, dump)
    applies = analyzers.parse_trace(trace)
    grid = [list(row) for row in s0]
    first_disc = None
    for lhs, idx, ro, co, _t in applies:
        if kinds.get((lhs, idx)) == "discover" and first_disc is None:
            first_disc = (co + 1) % RING // SECT
        for dr, dc, ch in imap[(lhs, idx)]:
            grid[(ro - 1 + dr) % (ROWS - 1)][(co + dc) % RING] = ch
    final = ["".join(r) for r in grid]
    exact = final == list(analyzers.parse_dump(dump, ROWS, RING))
    trace.unlink()
    dump.unlink()
    tape, mach, reg = final[0], final[3], final[4]
    out = {"arm": arm, "seed": seed, "exact": exact,
           "disc_sector": first_disc if first_disc is not None else -1}
    for s, genome in enumerate(genomes):
        cols = range(SECT * s, SECT * s + SECT - 1)
        alive = sum(1 for c in cols if tape[c] in "AB")
        out[f"alive{s}"] = alive
        out[f"mu{s}"] = sum(1 for c in cols if reg[c] == "μ")
        out[f"mach{s}"] = sum(1 for c in cols
                              if mach[c] in (FAITH, SLOPPY, XLATOR))
        out[f"surv{s}"] = int(alive >= (SECT - 1) // 2)
        out[f"genome{s}"] = genome
    return out


def _pool_init(workdir_str, ctx):
    global _WORK, _CTX
    _WORK = Path(workdir_str)
    _CTX = ctx


def probe_init(workdir):
    cfg = workdir / "probe.cfg"
    cfg.write_text("#!probe\n#threads 1\n^αl*\n^Zll\n==zzz\n@@@\n")
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
        Path(tempfile.mkdtemp(prefix="ew11_"))
    workdir.mkdir(parents=True, exist_ok=True)
    print(f"binary {BIN}\nworkdir {workdir}")

    s0 = probe_init(workdir)
    ctx = {}
    for arm in ARMS:
        text, imap, groups = build_cfg(arm)
        p = workdir / f"{arm}.cfg"
        p.write_text(text)
        ctx[arm] = (str(p), imap, key_kinds(groups), s0)

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
    cols = (["arm", "seed", "disc_sector", "exact"]
            + [f"{k}{s}" for s in range(4)
               for k in ("genome", "alive", "mu", "mach", "surv")])
    with open(here / "ew11_runs.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for r in sorted(rows, key=lambda r: (r["arm"], r["seed"])):
            w.writerow([r[c] for c in cols])

    n = args.seeds
    for arm in ARMS:
        sub = [r for r in rows if r["arm"] == arm]
        by = {"p": {"surv": 0, "alive": 0.0, "mu": 0.0, "n": 0},
              "b": {"surv": 0, "alive": 0.0, "mu": 0.0, "n": 0}}
        for r in sub:
            for s in range(4):
                g = r[f"genome{s}"]
                by[g]["surv"] += r[f"surv{s}"]
                by[g]["alive"] += r[f"alive{s}"]
                by[g]["mu"] += r[f"mu{s}"]
                by[g]["n"] += 1
        disc = [r["disc_sector"] for r in sub if r["disc_sector"] >= 0]
        parts = []
        for g, lab in (("p", "sloppy"), ("b", "faithful")):
            if by[g]["n"]:
                parts.append(
                    f"{lab}: surv {by[g]['surv']}/{by[g]['n']} "
                    f"alive {by[g]['alive'] / by[g]['n']:.1f} "
                    f"mu {by[g]['mu'] / by[g]['n']:.1f}")
        dshare = (sum(1 for d in disc
                      if ARMS[arm][1][d] == "p") / len(disc)
                  if disc else None)
        ds = f"  disc-in-sloppy {dshare:.2f} (n={len(disc)})" \
            if dshare is not None else "  no discoveries"
        print(f"{arm:>14}: " + " | ".join(parts) + ds)


if __name__ == "__main__":
    main()
