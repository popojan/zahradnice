#!/usr/bin/env python3
"""EW-6 — description replication and healing (F4).

Registered protocol and predictions: ew-design.md §EW-6 (P6-1..4).
Two-copy redundancy: transcriptase Φ backs the description up to
row 2 and restores wounded code cells from the backup; codon t
encodes Φ itself. Arms: healed / healed-q16 / healed-q8 /
healed-q4 / bare-q8 / no-t-q8.

Usage: python3 ew6.py [--jobs N] [--seeds N] [--workdir DIR]
Outputs: ew6_runs.csv, summary on stdout.
"""
import argparse
import csv
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

ROWS, RING = 6, 32        # tape=1 backup=2 code=3 mach=4 reg=5
CAD, EST, M, BLOCKS = 4, 200, 5, 200
EPS_D = 0.005
COPIER, XLATOR, SCRIPT = "Π", "Ω", "Φ"
SPAWNER = R("A", "A", "write", "A")
W_COLS, T_COLS = (0, 8, 16, 24), (12, 28)

ARMS = {                       # arm -> (has_phi, q_every)
    "bare": (False, None),
    "healed": (True, None),
    "healed-q16": (True, 16),
    "healed-q8": (True, 8),
    "healed-q4": (True, 4),
    "bare-q8": (False, 8),
    "no-t-q8": (True, 8),
}

_WORK = None
_CTX = None


def layout(arm):
    has_phi = ARMS[arm][0]
    with_t = has_phi and arm != "no-t-q8"
    code, mach = {}, {}
    for j in range(0, RING, 2):
        if j in W_COLS:
            code[j] = "w"
        elif with_t and j in T_COLS:
            code[j] = "t"
        else:
            code[j] = "b"
    for j in range(1, RING, 2):
        if j - 1 in W_COLS:
            mach[j] = XLATOR
        elif has_phi and j - 1 in T_COLS:
            mach[j] = SCRIPT
        else:
            mach[j] = COPIER
    return code, mach


def world_bootstrap(arm):
    code, mach = layout(arm)
    crow = "".join(code.get(k, " ") for k in range(RING))
    mrow = "".join(mach.get(k, " ") for k in range(RING))
    body = "  " + crow.rstrip() + "\n  " + mrow.rstrip() + "\n@@@"
    writes = ([(0, 0, "α")]
              + [(-2, k, g) for k, g in sorted(code.items())]
              + [(-1, k, g) for k, g in sorted(mach.items())])
    return ([("==Zbα", writes)], body)


def build_cfg(arm):
    has_phi = ARMS[arm][0]
    codons = {"b": COPIER, "w": XLATOR}
    if has_phi:
        codons["t"] = SCRIPT
    groups = []
    groups += gen_earned.unstamped_groups(SPAWNER, "α")
    groups.append(gen_earned.copier_copy(COPIER, ["α"], trig="C"))
    groups.append(gen_earned.copier_walk(COPIER, ["α"], trig="C"))
    groups.append(gen_earned.copier_pass(COPIER, trig="C"))
    groups.append(gen_earned.copier_decay(COPIER, EPS_D, trig="C"))
    groups += gen_earned.translator_rules(XLATOR, codons, trig="C")
    groups.append(gen_earned.copier_decay(XLATOR, EPS_D, trig="C"))
    if has_phi:
        groups += gen_earned.transcriptase_rules(SCRIPT, codons,
                                                 trig="C")
        groups.append(gen_earned.copier_decay(SCRIPT, EPS_D, trig="C"))
    groups.append(world_bootstrap(arm))
    extra = list(gen_family.poke_rules())
    extra += [R(g, "~", "self", None, "q") for g in "bwt"]
    return gen_earned.assemble("ew6 {steps}",
                               ["^Au*", "^αl*", "^Zll"], groups, extra)


def key_kinds(imap):
    """(lhs, idx) -> 'build' | 'backup' | 'restore' for accounting."""
    kinds = {}
    for k, w in imap.items():
        if k[0] == XLATOR and len(w) == 3 and any(
                (dr, dc) == (0, 1) and ch in (COPIER, XLATOR, SCRIPT)
                for dr, dc, ch in w):
            kinds[k] = "build"
        elif k[0] == SCRIPT and any(dr == -2 for dr, _dc, _c in w):
            kinds[k] = "backup"
        elif k[0] == SCRIPT and any(
                dr == -1 and ch in "bwt" for dr, _dc, ch in w):
            kinds[k] = "restore"
    return kinds


def inputs(arm):
    unit = "T" + "C" * CAD
    q_every = ARMS[arm][1]
    blocks = ""
    for i in range(BLOCKS):
        wound = "pq" if q_every and i % q_every == 0 else "p"
        blocks += wound + unit * M
    return "b" + unit * EST + blocks


def run_engine(cfg, seed, inp, trace, dump):
    cmd = [str(BIN), "--headless", "--screen", f"{ROWS},{RING}",
           "--seed", str(seed), "--input", inp,
           "--trace", str(trace), "--dump-screen", str(dump), str(cfg)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"engine failed on {cfg}: {r.stderr.strip()}")


def eval_run(task):
    arm, seed = task
    cfg_path, imap, kinds, s0 = _CTX[arm]
    tag = f"{arm}_s{seed}"
    trace, dump = _WORK / f"{tag}.trace", _WORK / f"{tag}.txt"
    run_engine(Path(cfg_path), seed, inputs(arm), trace, dump)
    applies = analyzers.parse_trace(trace)
    grid = [list(row) for row in s0]
    n = {"build": 0, "backup": 0, "restore": 0}
    for lhs, idx, ro, co, _t in applies:
        kind = kinds.get((lhs, idx))
        if kind:
            n[kind] += 1
        for dr, dc, ch in imap[(lhs, idx)]:
            grid[(ro - 1 + dr) % (ROWS - 1)][(co + dc) % RING] = ch
    final = ["".join(r) for r in grid]
    exact = final == list(analyzers.parse_dump(dump, ROWS, RING))
    trace.unlink()
    dump.unlink()
    tape, bak, code, mach = final[0], final[1], final[2], final[3]
    alive = sum(tape.count(c) for c in "AB")
    machinery = sum(mach.count(g) for g in (COPIER, XLATOR, SCRIPT))
    survived = alive >= RING // 2 and machinery >= 1
    return {"arm": arm, "seed": seed, "exact": exact,
            "survived": survived, "alive": alive,
            "copiers": mach.count(COPIER),
            "xlators": mach.count(XLATOR),
            "scripts": mach.count(SCRIPT),
            "builds": n["build"], "backups": n["backup"],
            "restores": n["restore"],
            "codons_code": sum(code.count(c) for c in "bwt"),
            "codons_bak": sum(bak.count(c) for c in "bwt")}


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
        Path(tempfile.mkdtemp(prefix="ew6_"))
    workdir.mkdir(parents=True, exist_ok=True)
    print(f"binary {BIN}\nworkdir {workdir}")

    s0 = probe_init(workdir)
    ctx = {}
    for arm in ARMS:
        text, imap = build_cfg(arm)
        p = workdir / f"{arm}.cfg"
        p.write_text(text)
        ctx[arm] = (str(p), imap, key_kinds(imap), s0)

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
    cols = ["arm", "seed", "survived", "alive", "copiers", "xlators",
            "scripts", "builds", "backups", "restores", "codons_code",
            "codons_bak", "exact"]
    with open(here / "ew6_runs.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for r in sorted(rows, key=lambda r: (r["arm"], r["seed"])):
            w.writerow([r[c] for c in cols])

    n = args.seeds
    for arm in ARMS:
        sub = [r for r in rows if r["arm"] == arm]
        surv = sum(r["survived"] for r in sub)
        agg = {c: sum(r[c] for r in sub) / n
               for c in cols[3:-1]}
        print(f"{arm:>11}: survived {surv}/{n}  alive {agg['alive']:.1f}"
              f"  mach Π {agg['copiers']:.1f} Ω {agg['xlators']:.1f} "
              f"Φ {agg['scripts']:.1f}  restores {agg['restores']:.1f}"
              f"  codons {agg['codons_code']:.1f}+{agg['codons_bak']:.1f}")


if __name__ == "__main__":
    main()
