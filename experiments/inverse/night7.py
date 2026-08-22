#!/usr/bin/env python3
"""Night-7 inverse: THE TAPE COMMONS — de-novo selection in pattern
space, nine rules, no dials, no mutation operator, no authored
fitness.

World: the ring is a circular chromosome of genes f/s; heads
(F/S/W) are eternal polymerases walking east. Structure, not
weights: crossing f costs 1 event, crossing s costs 2 (settle W).
Pokes wound the TAPE only. The only replication in the universe:
a head beside a hole writes a copy of the gene it covers into it
(repair = replication; copying is machinery-mediated). Variation =
initial standing diversity; no mutation rules exist.

The unauthored game: f speeds every polymerase downstream (public
good); s slows the commons, and slowly-patrolled sectors grow
larger wound-gaps that are filled as a single-gene burst from the
west flank. Whether s spreads (tragedy of the commons), f holds
(maintenance wins), or they balance is genuinely unknown before
the run — that is the point.

Per run: composition trajectory (s-share), the replication/death
ledger per gene type, patrol speed by quarter (commons health),
minimum tape (bottlenecks). Exact accounting: incremental replay
vs final dump.

Usage: python3 night7.py [--jobs N] [--workdir DIR]
Outputs: night7_commons.csv, summary on stdout.
"""
import argparse
import csv
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from multiprocessing import Pool

import gen_family
import analyzers

ROOT = Path(__file__).resolve().parents[2]
BIN = ROOT / "zahradnice"

H_EST = 32
DUR = 24000
RINGS = {24: ("^Fcl", "^Fcc"), 48: ("^Fcl", "^Fcc", "^Fcr")}
S0FRAC = (0.25, 0.5)
M_VALUES = (None, 8, 4, 2)
SEEDS = tuple(range(1, 17))
SAMPLE_EVERY = 50

COVER = {"F": "f", "S": "s", "W": "s"}

_WORKDIR = None


def rules7():
    R = gen_family.Rule
    return [R("F", "f", "reqwrite", "fF"), R("F", "f", "reqwrite", "sW"),
            R("S", "s", "reqwrite", "fF"), R("S", "s", "reqwrite", "sW"),
            R("W", "S", "self", None),
            R("F", "F", "reqwrite", "~f"), R("S", "S", "reqwrite", "~s")]


def init_lines(cols, s0frac):
    k = int(cols * s0frac)
    return "\n".join(["^fc*"] + ["^sc?"] * k + list(RINGS[cols]))


def protocol(m):
    if m is None:
        return "T" * (H_EST + DUR)
    return "T" * H_EST + ("p" + "T" * m) * (DUR // (m + 1))


def run_engine(cfg, geom, seed, inp, trace, dump):
    cmd = [str(BIN), "--headless", "--screen", f"{geom[0]},{geom[1]}",
           "--seed", str(seed), "--input", inp, "--dump-screen", str(dump),
           "--trace", str(trace), str(cfg)]
    t0 = time.perf_counter()
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"engine failed ({r.returncode}): "
                           f"{r.stderr.strip()}")
    return time.perf_counter() - t0


def _pool_init(workdir_str):
    global _WORKDIR
    _WORKDIR = Path(workdir_str)


def comp(cnt):
    """(n_f, n_s) counting covered glyphs under heads."""
    return (cnt["f"] + cnt["F"], cnt["s"] + cnt["S"] + cnt["W"])


def commons_replay(rules, extra, s0, applies, cols):
    imap = gen_family.idx_map(rules, extra)
    grid = [list(r) for r in s0]
    from collections import Counter
    cnt = Counter(ch for row in s0 for ch in row if ch in "fsFSW")
    samples = []
    pokes = Counter()
    repairs = Counter()
    moves_q = [0, 0, 0, 0]
    n = len(applies)
    min_tape = sum(comp(cnt))
    for i, (lhs, idx, ro, co, trig) in enumerate(applies):
        rule = imap[(lhs, idx)]
        if trig == "p":
            pokes[rule.lhs] += 1
        elif rule.kind == "reqwrite":
            if rule.arg[0] == "~":
                repairs[rule.arg[1]] += 1
            else:
                moves_q[min(3, 4 * i // n)] += 1
        for dc, ch in gen_family.writes(rule):
            r, c = ro - 1, (co + dc) % cols
            old = grid[r][c]
            if old in "fsFSW":
                cnt[old] -= 1
            if ch in "fsFSW":
                cnt[ch] += 1
            grid[r][c] = ch
        tape = cnt["f"] + cnt["s"]
        if tape < min_tape:
            min_tape = tape
        if (i + 1) % SAMPLE_EVERY == 0:
            samples.append(comp(cnt))
    final = "\n".join("".join(r) for r in grid)
    return final, cnt, samples, pokes, repairs, moves_q, min_tape


def eval_point(task):
    ring, s0frac, m = task
    geom = (6, ring)
    rules = rules7()
    extra = gen_family.poke_rules("fs")
    tag = f"r{ring}_s{s0frac:g}_m{m}"
    cfg = _WORKDIR / f"n7_{tag}.cfg"
    cfg.write_text(gen_family.compile_cfg(rules, f"n7_{tag}", extra,
                                          init_lines(ring, s0frac)))
    inp = protocol(m)
    rows, engine_s = [], 0.0
    for seed in SEEDS:
        dump0 = _WORKDIR / f"n7_{tag}_s{seed}_init.txt"
        run_engine(cfg, geom, seed, "z",
                   _WORKDIR / f"n7_{tag}_s{seed}_init.trace", dump0)
        s0 = tuple(analyzers.parse_dump(dump0, *geom))
        trace = _WORKDIR / f"n7_{tag}_s{seed}.trace"
        dump = _WORKDIR / f"n7_{tag}_s{seed}.txt"
        engine_s += run_engine(cfg, geom, seed, inp, trace, dump)
        applies = analyzers.parse_trace(trace)
        final, cnt, samples, pokes, repairs, moves_q, min_tape = \
            commons_replay(rules, extra, list(s0), applies, ring)
        if final != "\n".join(analyzers.parse_dump(dump, *geom)):
            sys.exit(f"EXACT-FAIL {tag} seed {seed}")
        from collections import Counter as C0
        icnt = C0(ch for row in s0 for ch in row if ch in "fsFSW")
        fi, si = comp(icnt)
        lastq = samples[3 * len(samples) // 4:]
        sl = [s / (f + s) for f, s in lastq if f + s]
        ff, sf = comp(cnt)
        rows.append({
            "ring": ring, "heads": len(RINGS[ring]), "s0frac": s0frac,
            "m": "inf" if m is None else m, "seed": seed,
            "s_init": si / (fi + si),
            "s_final": sf / (ff + sf) if ff + sf else None,
            "s_lastq": sum(sl) / len(sl) if sl else None,
            "pokes_f": pokes["f"], "pokes_s": pokes["s"],
            "repairs_f": repairs["f"], "repairs_s": repairs["s"],
            "moves_q1": moves_q[0], "moves_q4": moves_q[3],
            "min_tape": min_tape})
        trace.unlink()
        dump.unlink()
        dump0.unlink()
    return {"rows": rows, "engine_s": engine_s}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", type=int, default=1)
    ap.add_argument("--workdir", default=None)
    args = ap.parse_args()
    workdir = Path(args.workdir) if args.workdir else \
        Path(tempfile.mkdtemp(prefix="night7_"))
    workdir.mkdir(parents=True, exist_ok=True)
    print(f"binary {BIN}\nworkdir {workdir}")

    tasks = [(r, s0, m) for r in RINGS for s0 in S0FRAC
             for m in M_VALUES]
    print(f"{len(tasks)} points x {len(SEEDS)} seeds "
          f"= {len(tasks) * len(SEEDS)} runs of ~{H_EST + DUR} events")
    t0 = time.perf_counter()
    if args.jobs > 1:
        with Pool(args.jobs, _pool_init, (str(workdir),)) as pool:
            results = pool.map(eval_point, tasks, chunksize=1)
    else:
        _pool_init(str(workdir))
        results = [eval_point(t) for t in tasks]
    wall = time.perf_counter() - t0
    rows = [r for res in results for r in res["rows"]]
    engine_s = sum(res["engine_s"] for res in results)
    print(f"wall {wall:.1f}s, engine {engine_s:.1f}s "
          f"({1000 * engine_s / len(rows):.0f} ms/run), exactness: all pass")

    here = Path(__file__).parent
    cols = ["ring", "heads", "s0frac", "m", "seed", "s_init", "s_final",
            "s_lastq", "pokes_f", "pokes_s", "repairs_f", "repairs_s",
            "moves_q1", "moves_q4", "min_tape"]
    with open(here / "night7_commons.csv", "w", newline="") as f:
        w = csv.DictWriter(f, cols)
        w.writeheader()
        for r in rows:
            w.writerow({c: (f"{r[c]:.3f}" if isinstance(r[c], float)
                            else r[c]) for c in cols})

    print("\nper (ring, s0, m): s-share init -> lastq (mean over seeds) | "
          "replication ledger | patrol speed q1->q4:")
    for ring in RINGS:
        for s0 in S0FRAC:
            for m in M_VALUES:
                mm = "inf" if m is None else m
                sub = [r for r in rows if r["ring"] == ring
                       and r["s0frac"] == s0 and r["m"] == mm]
                si = sum(r["s_init"] for r in sub) / len(sub)
                sl = [r["s_lastq"] for r in sub if r["s_lastq"] is not None]
                slm = sum(sl) / len(sl) if sl else float("nan")
                rf = sum(r["repairs_f"] for r in sub) / len(sub)
                rs = sum(r["repairs_s"] for r in sub) / len(sub)
                q1 = sum(r["moves_q1"] for r in sub) / len(sub)
                q4 = sum(r["moves_q4"] for r in sub) / len(sub)
                mt = min(r["min_tape"] for r in sub)
                print(f"  r{ring} s0={s0} m={mm:>3}: "
                      f"s {si:.2f}->{slm:.2f} | rep f {rf:6.0f} s {rs:6.0f}"
                      f" | moves {q1:5.0f}->{q4:5.0f} | min_tape {mt}")


if __name__ == "__main__":
    main()
