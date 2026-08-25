#!/usr/bin/env python3
"""EW-8 — the code's keeper, and the frozen accident (F4).

Registered protocol and predictions: ew-design.md §EW-8 (P8-1..4).
Mortal keepers rebuilt only by translating codon x; pure and
mosaic codon tables. Arms: baseline / closure / no-x / pure2 /
mosaic.

Usage: python3 ew8.py [--jobs N] [--seeds N] [--workdir DIR]
Outputs: ew8_runs.csv, summary on stdout.
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

ROWS, RING = 6, 32        # tape=1 code=2 table=3 mach=4 reg=5
CAD, EST, M, BLOCKS = 4, 200, 5, 200
EPS_D = 0.005
COPIER, XLATOR, KEEPER = "Π", "Ω", "Ξ"
TABLES = {"1": {"b": COPIER, "w": XLATOR, "x": KEEPER},
          "2": {"b": XLATOR, "w": COPIER, "x": KEEPER}}
SPAWNER = R("A", "A", "write", "A")
W_COLS, X_COLS = (0, 10, 20), (4, 14, 24)

ARMS = {                  # arm -> (table_layout, with_x, r_every)
    "baseline": ("1", True, None),
    "closure": ("1", True, 4),
    "no-x": ("1", False, 4),
    "pure2": ("2", True, None),
    "mosaic": ("12", True, 4),
}

_WORK = None
_CTX = None


def world_bootstrap(arm):
    layout, with_x, _r = ARMS[arm]
    code, mach = {}, {}
    for j in range(0, RING, 2):
        if j in W_COLS:
            code[j] = "w"
        elif with_x and j in X_COLS:
            code[j] = "x"
        else:
            code[j] = "b"
    for j in range(1, RING, 2):
        if j - 1 in W_COLS:
            mach[j] = XLATOR
        elif j - 1 in X_COLS:
            mach[j] = KEEPER
        else:
            mach[j] = COPIER
    if layout == "12":
        trow = "1" * (RING // 2) + "2" * (RING // 2)
    else:
        trow = layout * RING
    crow = "".join(code.get(k, " ") for k in range(RING))
    mrow = "".join(mach.get(k, " ") for k in range(RING))
    body = ("  " + crow.rstrip() + "\n  " + trow + "\n  "
            + mrow.rstrip() + "\n@@@")
    writes = ([(0, 0, "α")]
              + [(-3, k, g) for k, g in sorted(code.items())]
              + [(-2, k, trow[k]) for k in range(RING)]
              + [(-1, k, g) for k, g in sorted(mach.items())])
    return ([("==Zbα", writes)], body)


def build_cfg(arm):
    groups = []
    groups += gen_earned.unstamped_groups(SPAWNER, "α")
    groups.append(gen_earned.copier_copy(COPIER, ["α"], trig="C"))
    groups.append(gen_earned.copier_walk(COPIER, ["α"], trig="C"))
    groups.append(gen_earned.copier_pass(COPIER, trig="C"))
    groups.append(gen_earned.copier_decay(COPIER, EPS_D, trig="C"))
    groups += gen_earned.translator_tabled(XLATOR, TABLES, trig="C")
    groups.append(gen_earned.copier_decay(XLATOR, EPS_D, trig="C"))
    groups += gen_earned.table_copier(KEEPER, list(TABLES),
                                      drift_w=1.0, trig="C")
    groups.append(gen_earned.copier_decay(KEEPER, EPS_D, trig="C"))
    groups.append(world_bootstrap(arm))
    extra = list(gen_family.poke_rules())
    extra += [R(s, "~", "self", None, "r") for s in TABLES]
    return gen_earned.assemble("ew8 {steps}",
                               ["^Au*", "^αl*", "^Zll"], groups, extra)


def key_kinds(imap):
    kinds = {}
    for k, w in imap.items():
        if k[0] == XLATOR and len(w) == 3 and any(
                (dr, dc) == (0, 1) and ch in (COPIER, XLATOR, KEEPER)
                for dr, dc, ch in w):
            prod = next(ch for dr, dc, ch in w if (dr, dc) == (0, 1))
            kinds[k] = ("build", prod)
        elif k[0] == KEEPER and any(dr == -1 and ch in TABLES
                                    for dr, _dc, ch in w):
            kinds[k] = ("repair", None)
    return kinds


def inputs(arm):
    unit = "T" + "C" * CAD
    r_every = ARMS[arm][2]
    blocks = ""
    for i in range(BLOCKS):
        wound = "pr" if r_every and i % r_every == 0 else "p"
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
    built = {COPIER: 0, XLATOR: 0, KEEPER: 0}
    repairs = 0
    for lhs, idx, ro, co, _t in applies:
        kk = kinds.get((lhs, idx))
        if kk:
            kind, prod = kk
            if kind == "build":
                built[prod] += 1
            else:
                repairs += 1
        for dr, dc, ch in imap[(lhs, idx)]:
            grid[(ro - 1 + dr) % (ROWS - 1)][(co + dc) % RING] = ch
    final = ["".join(r) for r in grid]
    exact = final == list(analyzers.parse_dump(dump, ROWS, RING))
    trace.unlink()
    dump.unlink()
    tape, table, mach = final[0], final[2], final[3]
    alive = sum(tape.count(c) for c in "AB")
    machinery = sum(mach.count(g) for g in (COPIER, XLATOR, KEEPER))
    survived = alive >= RING // 2 and machinery >= 1
    t1 = table.count("1")
    t2 = table.count("2")
    return {"arm": arm, "seed": seed, "exact": exact,
            "survived": survived, "alive": alive,
            "copiers": mach.count(COPIER),
            "xlators": mach.count(XLATOR),
            "keepers": mach.count(KEEPER),
            "built_pi": built[COPIER], "built_omega": built[XLATOR],
            "built_xi": built[KEEPER], "repairs": repairs,
            "t1": t1, "t2": t2,
            "t1_share": t1 / (t1 + t2) if t1 + t2 else None}


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
        Path(tempfile.mkdtemp(prefix="ew8_"))
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
            "keepers", "built_pi", "built_omega", "built_xi",
            "repairs", "t1", "t2", "t1_share", "exact"]
    with open(here / "ew8_runs.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for r in sorted(rows, key=lambda r: (r["arm"], r["seed"])):
            w.writerow([r[c] for c in cols])

    n = args.seeds
    for arm in ARMS:
        sub = [r for r in rows if r["arm"] == arm]
        surv = sum(r["survived"] for r in sub)
        agg = {c: sum(r[c] for r in sub) / n
               for c in ("alive", "copiers", "xlators", "keepers",
                         "built_xi", "repairs", "t1", "t2")}
        shares = [r["t1_share"] for r in sub
                  if r["t1_share"] is not None]
        sh = (f"  T1share {statistics.mean(shares):.3f}"
              f"±{statistics.stdev(shares):.3f}"
              if len(shares) > 1 else "")
        print(f"{arm:>9}: survived {surv}/{n}  alive {agg['alive']:.1f}"
              f"  mach Π {agg['copiers']:.1f} Ω {agg['xlators']:.1f} "
              f"Ξ {agg['keepers']:.1f}  builtΞ {agg['built_xi']:.1f}  "
              f"repairs {agg['repairs']:.1f}  table {agg['t1']:.1f}+"
              f"{agg['t2']:.1f}{sh}")


if __name__ == "__main__":
    main()
