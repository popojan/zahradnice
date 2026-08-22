#!/usr/bin/env python3
"""Night-6 inverse: THE STROKE LADDER — mechanism heredity without
weight dials.

Night 5's fitness was an authored rate (w=0.5 vs 1 on identical rule
shapes). Night 6 removes the dial: ALL rule weights are 1 (only the
mutation clock mu differs, and it is lineage-symmetric). The law is a
library of three walking ENGINES that differ structurally:

  1-stroke  A  ->step             (1 event/cell)   trail B
  2-stroke  C ->G ->step          (2 events/cell)  trail D
  3-stroke  E ->H ->I ->step      (3 events/cell)  trail F

Fitness = events consumed per cell advanced — the shared event
budget itself is the fitness function (Peak-B). Handlers are the
genome->mechanism map: trail glyph + hole -> that engine's ready
head. Mutation flips trail glyphs among {B,D,F} symmetrically.

Init: the SLOWEST engine alone; evolution must climb the ladder.
Observables: birth times per engine, the majority PATH (sequential
3>2>1 vs leapfrog 3>1 — F->B mutations allow skipping — vs stuck),
and the mean-fitness trajectory. Reverse control: start 1-stroke,
expect no displacement ever. m=inf control: no births.

Usage: python3 night6.py [--jobs N] [--workdir DIR]
Outputs: night6_ladder.csv, summary on stdout.
"""
import argparse
import csv
import subprocess
import sys
import tempfile
import time
from collections import Counter
from pathlib import Path
from multiprocessing import Pool

import gen_family
import analyzers

ROOT = Path(__file__).resolve().parents[2]
BIN = ROOT / "zahradnice"

GEOM = (6, 24)
H_EST = 128
DUR = 32000
INITS = {"slow": "^Ecc", "fast": "^Acc"}
M_VALUES = (None, 8, 2)
MU_VALUES = (0.001, 0.003, 0.01)
SEEDS = tuple(range(1, 25))
SAMPLE_EVERY = 50

TRAILS = "BDF"
HEADS = {1: "A", 2: "CG", 3: "EHI"}
LINEAGE_OF = {g: k for k, hs in HEADS.items() for g in hs}
LINEAGE_OF.update({"B": 1, "D": 2, "F": 3})
SPEED = {1: 1.0, 2: 0.5, 3: 1 / 3}

_WORKDIR = None


def rules6(mu):
    R = gen_family.Rule
    rules = [R("A", "B", "write", "A"),
             R("C", "G", "self", None), R("G", "D", "write", "C"),
             R("E", "H", "self", None), R("H", "I", "self", None),
             R("I", "F", "write", "E"),
             R("B", "A", "req", "~"), R("D", "C", "req", "~"),
             R("F", "E", "req", "~")]
    for t1 in TRAILS:
        for t2 in TRAILS:
            if t1 != t2:
                rules.append(R(t1, t2, "self", None, w=mu))
    return rules


def protocol(m):
    if m is None:
        return "T" * (H_EST + DUR)
    return "T" * H_EST + ("p" + "T" * m) * (DUR // (m + 1))


def run_engine(cfg, seed, inp, trace, dump):
    cmd = [str(BIN), "--headless", "--screen", f"{GEOM[0]},{GEOM[1]}",
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


def ladder_replay(rules, extra, s0, applies, cols):
    imap = gen_family.idx_map(rules, extra)
    grid = [list(r) for r in s0]
    cnt = Counter(ch for row in s0 for ch in row if ch in "ABCDEFGHI")
    t_birth = {1: None, 2: None, 3: None}
    births = Counter()
    muts = 0
    samples = []
    for i, (lhs, idx, ro, co, _t) in enumerate(applies):
        rule = imap[(lhs, idx)]
        if rule.trig == "T":
            if rule.kind == "req":
                births[LINEAGE_OF[rule.rep]] += 1
            elif rule.kind == "self" and rule.lhs in TRAILS:
                muts += 1
        for dc, ch in gen_family.writes(rule):
            r, c = ro - 1, (co + dc) % cols
            old = grid[r][c]
            if old in "ABCDEFGHI":
                cnt[old] -= 1
            if ch in "ABCDEFGHI":
                cnt[ch] += 1
            grid[r][c] = ch
        for k in (1, 2, 3):
            if t_birth[k] is None and any(cnt[g] for g in HEADS[k]):
                t_birth[k] = i + 1
        if (i + 1) % SAMPLE_EVERY == 0:
            samples.append(tuple(
                sum(cnt[g] for g in HEADS[k]) + cnt[TRAILS[k - 1]]
                for k in (1, 2, 3)))
    final = "\n".join("".join(r) for r in grid)
    return final, cnt, t_birth, births, muts, samples


def majority_path(samples):
    path, cur = [], None
    for s in samples:
        tot = sum(s)
        if not tot:
            continue
        k = max((1, 2, 3), key=lambda k: s[k - 1])
        if s[k - 1] * 2 > tot and k != cur:
            path.append(k)
            cur = k
    return ">".join(map(str, path)) if path else "-"


def eval_point(task):
    initk, m, mu = task
    rules = rules6(mu)
    extra = gen_family.poke_rules("ABCDEFGHI")
    tag = f"{initk}_m{m}_mu{mu:g}"
    cfg = _WORKDIR / f"n6_{tag}.cfg"
    cfg.write_text(gen_family.compile_cfg(rules, f"n6_{tag}", extra,
                                          INITS[initk]))
    dump0 = _WORKDIR / f"n6_{tag}_init.txt"
    run_engine(cfg, 1, "z", _WORKDIR / f"n6_{tag}_init.trace", dump0)
    s0 = tuple(analyzers.parse_dump(dump0, *GEOM))
    inp = protocol(m)
    rows, engine_s = [], 0.0
    for seed in SEEDS:
        trace = _WORKDIR / f"n6_{tag}_s{seed}.trace"
        dump = _WORKDIR / f"n6_{tag}_s{seed}.txt"
        engine_s += run_engine(cfg, seed, inp, trace, dump)
        applies = analyzers.parse_trace(trace)
        final, cnt, t_birth, births, muts, samples = ladder_replay(
            rules, extra, list(s0), applies, GEOM[1])
        if final != "\n".join(analyzers.parse_dump(dump, *GEOM)):
            sys.exit(f"EXACT-FAIL {tag} seed {seed}")
        lastq = samples[3 * len(samples) // 4:]
        share = [0.0, 0.0, 0.0]
        fit = 0.0
        for s in lastq:
            tot = sum(s)
            if tot:
                for k in (1, 2, 3):
                    share[k - 1] += s[k - 1] / tot
                fit += sum(s[k - 1] * SPEED[k] for k in (1, 2, 3)) / tot
        n = len(lastq)
        share = [x / n for x in share]
        fit /= n
        # death is judged from the FINAL state, not from samples —
        # samples stop with the last apply, so an extinct run's sample
        # tail still shows its last living population.
        alive = sum(cnt[g] for g in "ABCDEFGHI") > 0
        if not alive:
            winner = "DEAD"
        elif max(share) > 0.5:
            winner = f"FIX{share.index(max(share)) + 1}"
        else:
            winner = "MIXED"
        rows.append({
            "init": initk, "m": "inf" if m is None else m, "mu": mu,
            "seed": seed, "winner": winner,
            "t_death": None if alive else len(applies),
            "path": majority_path(samples),
            "t_birth1": t_birth[1], "t_birth2": t_birth[2],
            "t_birth3": t_birth[3],
            "births1": births[1], "births2": births[2],
            "births3": births[3], "mutations": muts,
            "fitness_lastq": fit,
            "share1": share[0], "share2": share[1], "share3": share[2],
            "pokes": sum(1 for a in applies if a[4] == "p")})
        trace.unlink()
        dump.unlink()
    return {"rows": rows, "engine_s": engine_s}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", type=int, default=1)
    ap.add_argument("--workdir", default=None)
    args = ap.parse_args()
    workdir = Path(args.workdir) if args.workdir else \
        Path(tempfile.mkdtemp(prefix="night6_"))
    workdir.mkdir(parents=True, exist_ok=True)
    print(f"binary {BIN}\nworkdir {workdir}")

    tasks = [(i, m, mu) for i in INITS for m in M_VALUES
             for mu in MU_VALUES]
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
    cols = ["init", "m", "mu", "seed", "winner", "t_death", "path", "t_birth1",
            "t_birth2", "t_birth3", "births1", "births2", "births3",
            "mutations", "fitness_lastq", "share1", "share2", "share3",
            "pokes"]
    with open(here / "night6_ladder.csv", "w", newline="") as f:
        w = csv.DictWriter(f, cols)
        w.writeheader()
        for r in rows:
            w.writerow({c: (f"{r[c]:.3f}" if isinstance(r[c], float)
                            else r[c]) for c in cols})

    def med(v):
        v = sorted(x for x in v if x is not None)
        return v[len(v) // 2] if v else "-"

    print("\nper (init, m, mu): winners | paths | med births (2-stroke, "
          "1-stroke) | mean lastq fitness:")
    for initk in INITS:
        for m in M_VALUES:
            mm = "inf" if m is None else m
            for mu in MU_VALUES:
                sub = [r for r in rows if r["init"] == initk
                       and r["m"] == mm and r["mu"] == mu]
                wc = Counter(r["winner"] for r in sub)
                pc = Counter(r["path"] for r in sub)
                fit = sum(r["fitness_lastq"] for r in sub) / len(sub)
                wstr = " ".join(f"{k}:{n}" for k, n in sorted(wc.items()))
                pstr = " ".join(f"{k}:{n}" for k, n
                                in pc.most_common(4))
                print(f"  {initk:<4} m={mm:>3} mu={mu:<5} {wstr:<22} "
                      f"| {pstr:<28} | b2 {med([r['t_birth2'] for r in sub]):>5}"
                      f" b1 {med([r['t_birth1'] for r in sub]):>5}"
                      f" | fit {fit:.2f}")


if __name__ == "__main__":
    main()
