#!/usr/bin/env python3
"""Night-4 inverse: HEREDITY — natural selection composed from three
verified mechanisms (repair, damage-driven proliferation, variation).

Two lineages share one ring and one mechanism (the night-2 archetype:
unconditional mover + empty-east handler) but carry distinct glyph
pairs: heads A/C, trails B/D. The trail IS the genome (one heritable
bit, spatially distributed): wounds respawn heads from the local
trail, so lineages breed true by construction. Movers overwrite
foreign matter, so lineages compete for territory. A lineage with a
head is ACTIVE; head lost but trail alive is DORMANT (a wound on its
trail resurrects it — the seed-bank motif); last trail cell
overwritten is EXTINCT (absorbing: heredity lost).

Selection knob: weight w on lineage-2's handler (repair speed).
Sweep: damage interval m (None = no damage) x w x seeds. Claims
under test: (1) heredity persists through proliferation/merge cycles;
(2) differential repair speed becomes selection, with strength
rising in damage rate; (3) dormancy/resurrection is load-bearing.

Per run (exact accounting: replay checked against the final dump):
outcome FIX1/FIX2/COEXIST/ALLDEAD, extinction times, mean territory
share, resurrection counts, dormant time.

Usage: python3 night4.py [--jobs N] [--workdir DIR]
Outputs: night4_selection.csv, summary on stdout.
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

GEOM = (6, 24)                      # ring of 24
INIT = "^Acl\n^Ccc"                 # heads start half a ring apart
H_EST = 64                          # cover the ring, mostly pre-collision
DUR = 24000                         # damage-phase events, equal for all m
M_VALUES = (None, 16, 8, 4, 2)      # poke every m+1 events; None = never
W_VALUES = (1, 0.5, 0.25)           # lineage-2 handler weight
SEEDS = tuple(range(1, 25))

_WORKDIR = None
_INIT0 = None


def lineage_rules(w, target="handler"):
    """Lineage 2 handicapped by weight w on its handler (repair
    speed) or its mover (walk speed); w=1 is the neutral baseline."""
    R = gen_family.Rule
    wm = w if target == "mover" else 1
    wh = w if target == "handler" else 1
    return [R("A", "B", "write", "A"), R("B", "A", "req", "~"),
            R("C", "D", "write", "C", w=wm),
            R("D", "C", "req", "~", w=wh)]


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


def _pool_init(workdir_str, init0):
    global _WORKDIR, _INIT0
    _WORKDIR = Path(workdir_str)
    _INIT0 = init0


def lineage_replay(rules, extra, s0, applies, cols):
    """Incremental replay tracking lineage populations; O(1)/apply.
    Heads: A, C; trails: B, D. Returns final grid, per-glyph counts
    trajectory statistics, extinction/resurrection/dormancy metrics."""
    imap = gen_family.idx_map(rules, extra)
    grid = [list(r) for r in s0]
    cnt = Counter(ch for row in s0 for ch in row if ch in "ABCD")
    t_ext = [None, None]
    res = [0, 0]
    dormant = [0, 0]
    share_sum, share_n = 0.0, 0
    for i, (lhs, idx, ro, co, _t) in enumerate(applies):
        rule = imap[(lhs, idx)]
        head_was = (cnt["A"], cnt["C"])
        for dc, ch in gen_family.writes(rule):
            r, c = ro - 1, (co + dc) % cols
            old = grid[r][c]
            if old in "ABCD":
                cnt[old] -= 1
            if ch in "ABCD":
                cnt[ch] += 1
            grid[r][c] = ch
        l = (cnt["A"] + cnt["B"], cnt["C"] + cnt["D"])
        for j, (h, hw) in enumerate(zip((cnt["A"], cnt["C"]), head_was)):
            if t_ext[j] is None:
                if l[j] == 0:
                    t_ext[j] = i + 1
                elif h == 0:
                    dormant[j] += 1
                if hw == 0 and h > 0 and l[j] > 0:
                    res[j] += 1
        if l[0] + l[1] > 0:
            share_sum += l[0] / (l[0] + l[1])
            share_n += 1
    final = "\n".join("".join(r) for r in grid)
    l = (cnt["A"] + cnt["B"], cnt["C"] + cnt["D"])
    outcome = ("ALLDEAD" if l[0] + l[1] == 0 else
               "COEXIST" if l[0] > 0 and l[1] > 0 else
               "FIX1" if l[0] > 0 else "FIX2")
    return {"final": final, "outcome": outcome,
            "t_ext1": t_ext[0], "t_ext2": t_ext[1],
            "res1": res[0], "res2": res[1],
            "dormant1": dormant[0], "dormant2": dormant[1],
            "mean_share1": share_sum / share_n if share_n else 0.0,
            "end_l1": l[0], "end_l2": l[1]}


def eval_point(task):
    m, w, target = task
    rules = lineage_rules(w, target)
    extra = gen_family.poke_rules("ABCD")
    tag = f"m{m}_w{w:g}_{target}"
    cfg = _WORKDIR / f"n4_{tag}.cfg"
    cfg.write_text(gen_family.compile_cfg(rules, f"n4_{tag}", extra, INIT))
    inp = protocol(m)
    rows, engine_s = [], 0.0
    for seed in SEEDS:
        trace = _WORKDIR / f"n4_{tag}_s{seed}.trace"
        dump = _WORKDIR / f"n4_{tag}_s{seed}.txt"
        engine_s += run_engine(cfg, seed, inp, trace, dump)
        applies = analyzers.parse_trace(trace)
        r = lineage_replay(rules, extra, list(_INIT0), applies, GEOM[1])
        if r["final"] != "\n".join(analyzers.parse_dump(dump, *GEOM)):
            sys.exit(f"EXACT-FAIL {tag} seed {seed}")
        r.update(m="inf" if m is None else m, w=w, target=target,
                 seed=seed, pokes=sum(1 for a in applies if a[4] == "p"))
        del r["final"]
        rows.append(r)
        trace.unlink()
        dump.unlink()
    return {"rows": rows, "engine_s": engine_s}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", type=int, default=1)
    ap.add_argument("--workdir", default=None)
    args = ap.parse_args()
    workdir = Path(args.workdir) if args.workdir else \
        Path(tempfile.mkdtemp(prefix="night4_"))
    workdir.mkdir(parents=True, exist_ok=True)
    print(f"binary {BIN}\nworkdir {workdir}")

    probe = workdir / "probe.cfg"
    probe.write_text(gen_family.compile_cfg(lineage_rules(1), "probe",
                                            gen_family.poke_rules("ABCD"),
                                            INIT))
    dump = workdir / "probe.txt"
    run_engine(probe, 1, "z", workdir / "probe.trace", dump)
    init0 = tuple(analyzers.parse_dump(dump, *GEOM))

    # w=1 is target-independent: run it once (labelled 'none').
    tasks = [(m, 1, "none") for m in M_VALUES] + \
            [(m, w, t) for m in M_VALUES for w in W_VALUES if w != 1
             for t in ("handler", "mover")]
    print(f"{len(tasks)} (m,w) points x {len(SEEDS)} seeds "
          f"= {len(tasks) * len(SEEDS)} runs of ~{H_EST + DUR} events")
    t0 = time.perf_counter()
    if args.jobs > 1:
        with Pool(args.jobs, _pool_init, (str(workdir), init0)) as pool:
            results = pool.map(eval_point, tasks, chunksize=1)
    else:
        _pool_init(str(workdir), init0)
        results = [eval_point(t) for t in tasks]
    wall = time.perf_counter() - t0
    rows = [r for res in results for r in res["rows"]]
    engine_s = sum(res["engine_s"] for res in results)
    print(f"wall {wall:.1f}s, engine {engine_s:.1f}s "
          f"({1000 * engine_s / len(rows):.0f} ms/run), exactness: all pass")

    here = Path(__file__).parent
    cols = ["m", "w", "target", "seed", "outcome", "t_ext1", "t_ext2",
            "res1", "res2", "dormant1", "dormant2", "mean_share1",
            "end_l1", "end_l2", "pokes"]
    with open(here / "night4_selection.csv", "w", newline="") as f:
        wtr = csv.DictWriter(f, cols)
        wtr.writeheader()
        for r in rows:
            wtr.writerow({c: (f"{r[c]:.3f}" if isinstance(r[c], float)
                              else r[c]) for c in cols})

    print("\nper (m, w, target): outcomes | mean share1 | "
          "resurrections/run (lin1, lin2):")
    for m in M_VALUES:
        mm = "inf" if m is None else m
        for w, t in [(1, "none")] + [(w, t) for w in W_VALUES if w != 1
                                     for t in ("handler", "mover")]:
            sub = [r for r in rows if r["m"] == mm and r["w"] == w
                   and r["target"] == t]
            oc = Counter(r["outcome"] for r in sub)
            share = sum(r["mean_share1"] for r in sub) / len(sub)
            r1 = sum(r["res1"] for r in sub) / len(sub)
            r2 = sum(r["res2"] for r in sub) / len(sub)
            print(f"  m={mm:>3} w={w:<4} {t:<7} "
                  f"FIX1 {oc.get('FIX1', 0):>2}  FIX2 {oc.get('FIX2', 0):>2}  "
                  f"COEX {oc.get('COEXIST', 0):>2}  DEAD {oc.get('ALLDEAD', 0):>2}"
                  f" | share1 {share:.2f} | res {r1:.1f}, {r2:.1f}")


if __name__ == "__main__":
    main()
