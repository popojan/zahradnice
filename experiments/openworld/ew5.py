#!/usr/bin/env python3
"""EW-5 — the self-reproduction kernel (F4, the description rung live).

Registered protocol and predictions: ew-design.md §EW-5 (P5-1..4).
Machinery is maintained by TRANSLATION of a description on the code
row; codon w encodes the translator itself. Arms: kernel /
no-executor / no-w / q-dose.

Usage: python3 ew5.py [--jobs N] [--seeds N] [--workdir DIR]
Outputs: ew5_runs.csv, summary on stdout.
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

ROWS, RING = 6, 24        # tape=1 fuel=2 code=3 mach=4 reg=5
CAD, EST, M, BLOCKS = 4, 200, 5, 200
EPS_D = 0.005
COPIER, XLATOR = "Π", "Ω"
CODONS = {"b": COPIER, "w": XLATOR}
SPAWNER = R("A", "A", "write", "A")
W_COLS = (0, 6, 12, 18)

ARMS = ("kernel", "no-executor", "no-w", "q16", "q8", "q4")

_WORK = None
_CTX = None


def layout(arm):
    """(code_row, mach_row) as col->glyph dicts."""
    code, mach = {}, {}
    for j in range(0, RING, 2):
        code[j] = "w" if (j in W_COLS and arm != "no-w") else "b"
    for j in range(1, RING, 2):
        if arm == "no-executor":
            mach[j] = COPIER
        else:
            mach[j] = XLATOR if j - 1 in W_COLS else COPIER
    return code, mach


Q_EVERY = {"q16": 16, "q8": 8, "q4": 4}


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
    groups = []
    groups += gen_earned.unstamped_groups(SPAWNER, "α")
    groups.append(gen_earned.copier_copy(COPIER, ["α"], trig="C"))
    groups.append(gen_earned.copier_walk(COPIER, ["α"], trig="C"))
    groups.append(gen_earned.copier_pass(COPIER, trig="C"))
    groups.append(gen_earned.copier_decay(COPIER, EPS_D, trig="C"))
    if arm != "no-executor":
        groups += gen_earned.translator_rules(XLATOR, CODONS, trig="C")
        groups.append(gen_earned.copier_decay(XLATOR, EPS_D, trig="C"))
    groups.append(world_bootstrap(arm))
    extra = list(gen_family.poke_rules())
    extra += [R(g, "~", "self", None, "q") for g in "bw"]
    return gen_earned.assemble("ew5 {steps}",
                               ["^Au*", "^αl*", "^Zll"], groups, extra)


def construct_keys(imap):
    """(lhs, idx) of translator execute headers -> product glyph."""
    out = {}
    for k, w in imap.items():
        if k[0] == XLATOR:
            prods = [ch for dr, dc, ch in w if dc == 1 and ch != " "
                     and dr == 0 and ch != XLATOR]
            built = [ch for dr, dc, ch in w
                     if (dr, dc) == (0, 1) and ch in (COPIER, XLATOR)]
            if len(w) == 3 and built:
                out[k] = built[0]
    return out


def inputs(arm):
    unit = "T" + "C" * CAD
    q_every = Q_EVERY.get(arm)
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
    cfg_path, imap, ckeys, s0 = _CTX[arm]
    tag = f"{arm}_s{seed}"
    trace, dump = _WORK / f"{tag}.trace", _WORK / f"{tag}.txt"
    run_engine(Path(cfg_path), seed, inputs(arm), trace, dump)
    applies = analyzers.parse_trace(trace)
    grid = [list(row) for row in s0]
    built = {COPIER: 0, XLATOR: 0}
    for lhs, idx, ro, co, _t in applies:
        if (lhs, idx) in ckeys:
            built[ckeys[(lhs, idx)]] += 1
        for dr, dc, ch in imap[(lhs, idx)]:
            grid[(ro - 1 + dr) % (ROWS - 1)][(co + dc) % RING] = ch
    final = ["".join(r) for r in grid]
    exact = final == list(analyzers.parse_dump(dump, ROWS, RING))
    trace.unlink()
    dump.unlink()
    tape, code, mach, reg = final[0], final[2], final[3], final[4]
    alive = sum(tape.count(c) for c in "AB")
    copiers = mach.count(COPIER)
    xlators = mach.count(XLATOR)
    active = sum(1 for c in range(RING)
                 if tape[c] in "AB" and reg[c] == "α")
    survived = alive >= RING // 2 and (copiers + xlators) >= 1
    return {"arm": arm, "seed": seed, "exact": exact,
            "survived": survived, "alive": alive, "active": active,
            "copiers": copiers, "xlators": xlators,
            "built_pi": built[COPIER], "built_omega": built[XLATOR],
            "codons": sum(code.count(c) for c in "bw")}


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
        Path(tempfile.mkdtemp(prefix="ew5_"))
    workdir.mkdir(parents=True, exist_ok=True)
    print(f"binary {BIN}\nworkdir {workdir}")

    s0 = probe_init(workdir)
    ctx = {}
    for arm in ARMS:
        text, imap = build_cfg(arm)
        p = workdir / f"{arm}.cfg"
        p.write_text(text)
        ctx[arm] = (str(p), imap, construct_keys(imap), s0)

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
    cols = ["arm", "seed", "survived", "alive", "active", "copiers",
            "xlators", "built_pi", "built_omega", "codons", "exact"]
    with open(here / "ew5_runs.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for r in sorted(rows, key=lambda r: (r["arm"], r["seed"])):
            w.writerow([r[c] for c in cols])

    n = args.seeds
    for arm in ARMS:
        sub = [r for r in rows if r["arm"] == arm]
        surv = sum(r["survived"] for r in sub)
        agg = {c: sum(r[c] for r in sub) / n
               for c in ("alive", "copiers", "xlators", "built_pi",
                         "built_omega", "codons")}
        print(f"{arm:>12}: survived {surv}/{n}  alive {agg['alive']:.1f}"
              f"  machinery Π {agg['copiers']:.1f} Ω "
              f"{agg['xlators']:.1f}  built Π {agg['built_pi']:.0f} Ω "
              f"{agg['built_omega']:.1f}  codons {agg['codons']:.1f}")


if __name__ == "__main__":
    main()
