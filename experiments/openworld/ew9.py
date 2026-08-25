#!/usr/bin/env python3
"""EW-9 — heritable machine-lineage fidelity (F4).

Registered protocol and predictions: ew-design.md §EW-9 (P9-1..3,
Amendment 9: the nurture spectrum). Faithful Π and sloppy π breed
true; replication is gated on standing over living law, weighted
by that allele's machine-nurture (d=0, α/ν=1, μ=2). Arms:
neutral / deleterious / beneficial.

Usage: python3 ew9.py [--jobs N] [--seeds N] [--workdir DIR]
Outputs: ew9_runs.csv, summary on stdout.
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

ROWS, RING = 5, 24        # tape=1 fuel=2 mach=3 reg=4
CAD, EST, M, BLOCKS = 4, 200, 5, 200
EPS_D, EPS, W_R = 0.005, 0.2, 0.02
FAITH, SLOPPY = "Π", "π"
SPAWNER = R("A", "A", "write", "A")

ARMS = {                  # arm -> (target glyph, target nurture)
    "neutral": ("ν", 1),
    "deleterious": ("d", 0),
    "beneficial": ("μ", 2),
}

_WORK = None
_CTX = None


def machine_groups(glyph, target, nurture, eps):
    """Copy/walk/pass/decay/replicate for one machine lineage.
    Returns (groups, kinds) with kinds[(lhs, per-group order)] noted
    by the caller via emission mirroring."""
    n_mut = 2 if eps else 0
    fw = 1 - eps * n_mut / 2 if eps else 1
    groups = [gen_earned.copier_copy(glyph, ["α", target],
                                     eps=eps, trig="C", faith_w=fw),
              gen_earned.copier_walk(glyph, ["α", target], trig="C"),
              gen_earned.copier_pass(glyph, trig="C"),
              gen_earned.copier_decay(glyph, EPS_D, trig="C"),
              gen_earned.copier_replicate(glyph, "α", w=W_R, trig="C")]
    if nurture > 0:
        groups.append(gen_earned.copier_replicate(
            glyph, target, w=W_R * nurture, trig="C"))
    return groups


def world_bootstrap():
    mach = {j: (FAITH if (j // 2) % 2 == 0 else SLOPPY)
            for j in range(1, RING, 2)}
    mrow = "".join(mach.get(k, " ") for k in range(RING))
    body = "  " + mrow.rstrip() + "\n@@@"
    writes = ([(0, 0, "α")]
              + [(-1, k, g) for k, g in sorted(mach.items())])
    return ([("==Zbα", writes)], body)


def build_cfg(arm):
    target, nurture = ARMS[arm]
    groups = []
    groups += gen_earned.unstamped_groups(SPAWNER, "α")
    if nurture > 0:
        groups += gen_earned.unstamped_groups(SPAWNER, target)
    for glyph in (FAITH, SLOPPY):
        groups += machine_groups(glyph, target, nurture,
                                 eps=EPS if glyph == SLOPPY else 0)
    groups.append(world_bootstrap())
    text, imap = gen_earned.assemble(
        "ew9 {steps}", ["^Au*", "^αl*", "^Zll"], groups,
        gen_family.poke_rules())
    return text, imap, groups


def key_kinds(groups, extra_n=2):
    """Mirror assemble's emission order: (lhs, idx) -> tag."""
    kinds, per = {}, {}
    for heads, _body in groups:
        for h, w in heads:
            lhs = h[2]
            i = per.get(lhs, 0)
            per[lhs] = i + 1
            if lhs in (FAITH, SLOPPY):
                if len(w) == 2 and w[0][2] == lhs and w[1][2] == lhs \
                        and w[0][:2] == (0, 0):
                    kinds[(lhs, i)] = "birth"
                elif len(h) > 8 and h[7] != h[8] and any(
                        dr == 1 for dr, dc, ch in w):
                    kinds[(lhs, i)] = "miscopy"
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
    target, _n = ARMS[arm]
    cfg_path, imap, kinds, s0 = _CTX[arm]
    tag = f"{arm}_s{seed}"
    trace, dump = _WORK / f"{tag}.trace", _WORK / f"{tag}.txt"
    run_engine(Path(cfg_path), seed, inputs(), trace, dump)
    applies = analyzers.parse_trace(trace)
    grid = [list(row) for row in s0]
    births = {FAITH: 0, SLOPPY: 0}
    miscopies = 0
    for lhs, idx, ro, co, _t in applies:
        kk = kinds.get((lhs, idx))
        if kk == "birth":
            births[lhs] += 1
        elif kk == "miscopy":
            miscopies += 1
        for dr, dc, ch in imap[(lhs, idx)]:
            grid[(ro - 1 + dr) % (ROWS - 1)][(co + dc) % RING] = ch
    final = ["".join(r) for r in grid]
    exact = final == list(analyzers.parse_dump(dump, ROWS, RING))
    trace.unlink()
    dump.unlink()
    tape, mach, reg = final[0], final[2], final[3]
    alive = sum(tape.count(c) for c in "AB")
    npi, nsl = mach.count(FAITH), mach.count(SLOPPY)
    survived = alive >= RING // 2 and (npi + nsl) >= 1
    return {"arm": arm, "seed": seed, "exact": exact,
            "survived": survived, "alive": alive,
            "faithful": npi, "sloppy": nsl,
            "share_f": npi / (npi + nsl) if npi + nsl else None,
            "births_f": births[FAITH], "births_s": births[SLOPPY],
            "miscopies": miscopies,
            "g_alpha": reg.count("α"), "g_target": reg.count(target),
            "qmarks": reg.count(gen_earned.PLACE)}


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
        Path(tempfile.mkdtemp(prefix="ew9_"))
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
    cols = ["arm", "seed", "survived", "alive", "faithful", "sloppy",
            "share_f", "births_f", "births_s", "miscopies", "g_alpha",
            "g_target", "qmarks", "exact"]
    with open(here / "ew9_runs.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for r in sorted(rows, key=lambda r: (r["arm"], r["seed"])):
            w.writerow([r[c] for c in cols])

    n = args.seeds
    for arm in ARMS:
        sub = [r for r in rows if r["arm"] == arm]
        surv = sum(r["survived"] for r in sub)
        shares = [r["share_f"] for r in sub if r["share_f"] is not None]
        agg = {c: sum(r[c] for r in sub) / n
               for c in ("alive", "faithful", "sloppy", "births_f",
                         "births_s", "miscopies", "g_target")}
        sh = (f"{statistics.mean(shares):.3f}"
              f"±{statistics.stdev(shares):.3f}" if len(shares) > 1
              else "n/a")
        print(f"{arm:>12}: survived {surv}/{n}  Π {agg['faithful']:.1f}"
              f" π {agg['sloppy']:.1f}  Π-share {sh}  births "
              f"{agg['births_f']:.0f}/{agg['births_s']:.0f}  "
              f"miscopies {agg['miscopies']:.1f}  target-gates "
              f"{agg['g_target']:.1f}")


if __name__ == "__main__":
    main()
