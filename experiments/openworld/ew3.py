#!/usr/bin/env python3
"""EW-3 — who pays for the polymerase (F4, the summit test).

Registered protocol and predictions: ew-design.md §EW-3 (P3-1a..d).
Two alleles, identical matter law (spawner A>A.writeA); α owns the
build-copier rule, β free-rides. All territorial change is
wound-mediated annexation from the west, machinery permitting.

Arms: none / both / free / taxed (see design doc).

Usage: python3 ew3.py [--jobs N] [--seeds N] [--workdir DIR]
Outputs: ew3_runs.csv, summary on stdout.
"""
import argparse
import csv
import math
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
EST, BLOCKS = 200, 120
# regime -> (cadence, units between wounds, copier decay, seeds)
REGIMES = {"abundant": (16, 25, 0.05, 200),
           "mid": (4, 10, 0.1, 100),
           "scarce": (1, 5, 0.2, 100)}
COPIER = "Π"
GLYPHS = ("α", "β")
KEY = {"α": "a", "β": "b"}
SPAWNER = R("A", "A", "write", "A")

_WORK = None
_CTX = None


def build_cfg(arm, eps_d):
    """-> (cfg_text, imap). Builder cursor W paints the regulatory
    row (ow2 pattern); machinery law on byte C; build per arm."""
    groups = []
    for g in GLYPHS:
        groups += gen_earned.unstamped_groups(SPAWNER, g)
    groups.append(gen_earned.copier_copy(COPIER, list(GLYPHS), trig="C"))
    groups.append(gen_earned.copier_walk(COPIER, list(GLYPHS), trig="C"))
    groups.append(gen_earned.copier_decay(COPIER, eps_d, trig="C"))
    builders = {"none": (), "both": GLYPHS, "free": ("α",),
                "taxed": ("α",)}[arm]
    trig = "T" if arm == "taxed" else "C"
    for g in builders:
        groups.append(gen_earned.build_rule("A", g, COPIER, trig=trig))
    text, imap = gen_earned.assemble(
        f"ew3{arm} {{steps}}", ["^Au*", "^Wll"], groups,
        gen_family.poke_rules())
    lines = [text.rstrip("\n")]
    extra = []
    for g in GLYPHS:                              # cursor: paint + step
        lines += [f"==W{KEY[g]}{g}", "@@@W"]
        extra.append(("W", [(0, 0, g), (0, 1, "W")]))
    lines += ["==We" + GLYPHS[0], "@@@"]          # finalizer at wrap
    extra.append(("W", [(0, 0, GLYPHS[0])]))
    per = {}
    for (lhs, _i) in imap:
        per[lhs] = max(per.get(lhs, -1), _i)
    for lhs, w in extra:
        i = per.get(lhs, -1) + 1
        imap[(lhs, i)] = w
        per[lhs] = i
    return "\n".join(lines) + "\n", imap


def layout():
    return [GLYPHS[0]] * (RING // 2) + [GLYPHS[1]] * (RING // 2)


def inputs(cad, m):
    unit = "T" + "C" * cad
    return ("".join(KEY[g] for g in layout()) + "e"
            + unit * EST + ("p" + unit * m) * BLOCKS)


def run_engine(cfg, seed, inp, trace, dump):
    cmd = [str(BIN), "--headless", "--screen", f"{ROWS},{RING}",
           "--seed", str(seed), "--input", inp,
           "--trace", str(trace), "--dump-screen", str(dump), str(cfg)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"engine failed on {cfg}: {r.stderr.strip()}")


def eval_run(task):
    arm, regime, seed = task
    cad, m, _eps, _n = REGIMES[regime]
    cfg_path, imap, s0 = _CTX[(arm, regime)]
    tag = f"{arm}_{regime}_s{seed}"
    trace, dump = _WORK / f"{tag}.trace", _WORK / f"{tag}.txt"
    run_engine(Path(cfg_path), seed, inputs(cad, m), trace, dump)
    applies = analyzers.parse_trace(trace)
    grid = [list(row) for row in s0]
    for lhs, idx, ro, co, _t in applies:
        for dr, dc, ch in imap[(lhs, idx)]:
            grid[(ro - 1 + dr) % (ROWS - 1)][(co + dc) % RING] = ch
    final = ["".join(r) for r in grid]
    exact = final == list(analyzers.parse_dump(dump, ROWS, RING))
    trace.unlink()
    dump.unlink()
    tape, mach, reg = final[0], final[2], final[3]
    gates = Counter(reg)
    occ = {g: gates.get(g, 0) for g in GLYPHS}
    q = gates.get(gen_earned.PLACE, 0)
    half = RING // 2
    halves = {f"{side}_{g}": sum(1 for c in rng if reg[c] == g)
              for side, rng in (("aland", range(half)),
                                ("bland", range(half, RING)))
              for g in GLYPHS}
    live = {g: n for g, n in occ.items() if n}
    winner = max(live, key=live.get) if len(live) == 1 else (
        "FROZEN" if not live else
        ("COEX" if occ["α"] == occ["β"] else max(occ, key=occ.get)))
    alive_half = {f"alive_{side}": sum(1 for c in rng if tape[c] in "AB")
                  for side, rng in (("a", range(half)),
                                    ("b", range(half, RING)))}
    return {"arm": arm, "regime": regime, "seed": seed, "exact": exact,
            "winner": winner,
            "gates_a": occ["α"], "gates_b": occ["β"], "qmarks": q,
            "copiers": mach.count(COPIER),
            "alive": sum(tape.count(c) for c in "AB"),
            **alive_half, **halves}


def _pool_init(workdir_str, ctx):
    global _WORK, _CTX
    _WORK = Path(workdir_str)
    _CTX = ctx


def probe_init(workdir):
    cfg = workdir / "probe.cfg"
    cfg.write_text("#!probe\n#threads 1\n^Au*\n^Wll\n==zzz\n@@@\n")
    dump = workdir / "probe.txt"
    run_engine(cfg, 1, "q", workdir / "probe.trace", dump)
    return tuple(analyzers.parse_dump(dump, ROWS, RING))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", type=int, default=12)
    ap.add_argument("--seeds", type=int, default=200)
    ap.add_argument("--workdir", default=None)
    args = ap.parse_args()
    workdir = Path(args.workdir) if args.workdir else \
        Path(tempfile.mkdtemp(prefix="ew3_"))
    workdir.mkdir(parents=True, exist_ok=True)
    print(f"binary {BIN}\nworkdir {workdir}")

    s0 = probe_init(workdir)
    ctx = {}
    tasks = []
    for regime, (cad, m, eps_d, seeds) in REGIMES.items():
        seeds = min(seeds, args.seeds) if args.seeds else seeds
        for arm in ("none", "both", "free", "taxed"):
            text, imap = build_cfg(arm, eps_d)
            p = workdir / f"{arm}_{regime}.cfg"
            p.write_text(text)
            ctx[(arm, regime)] = (str(p), imap, s0)
            tasks += [(arm, regime, s) for s in range(1, seeds + 1)]
    t0 = time.perf_counter()
    if args.jobs > 1:
        with Pool(args.jobs, _pool_init, (str(workdir), ctx)) as pool:
            rows = pool.map(eval_run, tasks, chunksize=4)
    else:
        _pool_init(str(workdir), ctx)
        rows = [eval_run(t) for t in tasks]
    wall = time.perf_counter() - t0
    inexact = [(r["arm"], r["regime"], r["seed"]) for r in rows
               if not r["exact"]]
    print(f"{len(rows)} runs, wall {wall:.1f}s, "
          f"exactness failures: {len(inexact)}")
    if inexact:
        print(inexact[:10])
        sys.exit("trace<->screen accounting broken; aborting")

    here = Path(__file__).parent
    cols = ["regime", "arm", "seed", "winner", "gates_a", "gates_b",
            "qmarks", "copiers", "alive", "alive_a", "alive_b",
            "aland_α", "aland_β", "bland_α", "bland_β", "exact"]
    with open(here / "ew3_runs.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for r in sorted(rows, key=lambda r: (r["regime"], r["arm"],
                                             r["seed"])):
            w.writerow([r[c] for c in cols])

    for regime in REGIMES:
        print(f"--- {regime} (cad {REGIMES[regime][0]}, "
              f"M {REGIMES[regime][1]}, eps_d {REGIMES[regime][2]})")
        for arm in ("none", "both", "free", "taxed"):
            sub = [r for r in rows if r["arm"] == arm
                   and r["regime"] == regime]
            n = len(sub)
            wc = Counter(r["winner"] for r in sub)
            ga = sum(r["gates_a"] for r in sub) / n
            gb = sum(r["gates_b"] for r in sub) / n
            qm = sum(r["qmarks"] for r in sub) / n
            cp = sum(r["copiers"] for r in sub) / n
            anx = sum(r["bland_α"] for r in sub) / n
            bnx = sum(r["aland_β"] for r in sub) / n
            ava = sum(r["alive_a"] for r in sub) / n
            avb = sum(r["alive_b"] for r in sub) / n
            wa, wb = wc.get("α", 0), wc.get("β", 0)
            zbin = (wa - wb) / math.sqrt(wa + wb) if (wa + wb) else 0.0
            print(f"{arm:>6}: winners {dict(wc)}  z(α-β)={zbin:+.2f}  "
                  f"gates α {ga:.1f} β {gb:.1f} ? {qm:.1f}  "
                  f"copiers {cp:.1f}")
            print(f"        alive α-land {ava:.1f}/12 β-land {avb:.1f}/12"
                  f"  annexation: α holds {anx:.1f}/12 of β-land, "
                  f"β holds {bnx:.1f}/12 of α-land")


if __name__ == "__main__":
    main()
