#!/usr/bin/env python3
"""Night-5 inverse: MUTATION — in-run variation, and evolution's arrow.

Fixed law (6 T-rules + poke harness): slow lineage A/B (mover weight
WS=0.5), fast lineage C/D (mover weight 1), equal handlers, and
mutation as law — trail copying errors B<->D at weight MU, paying
from the same event budget as everything else. Per night 4, the
fitness difference sits on the CONTESTED rate (walk speed), so
selection can see it.

Init is a single resident lineage; the other must ARISE. A mutant
trail cell is expressed only when a wound lands east of it (handler
respawn) — damage is the expression mechanism, not just the
selection pressure. Predictions: (a) m=inf: mutants churn in the
trail, never expressed, no evolution (control); (b) slow-start +
damage: fast lineage born, ballistic takeover; (c) fast-start +
damage: slow mutants born and always die (the arrow).

Per run: birth time of the mutant lineage, takeover security time,
birth/mutation event counts, mutant share in the final quarter,
outcome in {NO_BIRTH, RESIDENT_HOLDS, TAKEOVER, ALLDEAD}. Exact
accounting: incremental replay checked against the final dump.

Usage: python3 night5.py [--jobs N] [--workdir DIR]
Outputs: night5_evolution.csv, summary on stdout.
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
H_EST = 64
DUR = 24000
WS = 0.5
INITS = {"slow": "^Acc", "fast": "^Ccc"}
M_VALUES = (None, 16, 8, 4, 2)
MU_VALUES = (0.001, 0.003, 0.01)
SEEDS = tuple(range(1, 25))
SAMPLE_EVERY = 50

_WORKDIR = None


def rules5(mu):
    R = gen_family.Rule
    return [R("A", "B", "write", "A", w=WS), R("B", "A", "req", "~"),
            R("C", "D", "write", "C"), R("D", "C", "req", "~"),
            R("B", "D", "self", None, w=mu),
            R("D", "B", "self", None, w=mu)]


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


def evolution_replay(rules, extra, s0, applies, cols, mutant_head):
    """Incremental replay; slow lineage = A+B, fast = C+D. Returns
    final grid and the evolution observables."""
    imap = gen_family.idx_map(rules, extra)
    grid = [list(r) for r in s0]
    cnt = Counter(ch for row in s0 for ch in row if ch in "ABCD")
    births = Counter()
    muts = Counter()
    t_birth = None
    samples = []
    for i, (lhs, idx, ro, co, _t) in enumerate(applies):
        rule = imap[(lhs, idx)]
        if rule.trig == "T":
            if rule.kind == "req":
                births[rule.rep] += 1
            elif rule.kind == "self":
                muts[f"{rule.lhs}>{rule.rep}"] += 1
        for dc, ch in gen_family.writes(rule):
            r, c = ro - 1, (co + dc) % cols
            old = grid[r][c]
            if old in "ABCD":
                cnt[old] -= 1
            if ch in "ABCD":
                cnt[ch] += 1
            grid[r][c] = ch
        if t_birth is None and cnt[mutant_head] > 0:
            t_birth = i + 1
        if (i + 1) % SAMPLE_EVERY == 0:
            samples.append((cnt["A"] + cnt["B"], cnt["C"] + cnt["D"]))
    final = "\n".join("".join(r) for r in grid)
    return final, cnt, births, muts, t_birth, samples


def eval_point(task):
    initk, m, mu = task
    rules = rules5(mu)
    extra = gen_family.poke_rules("ABCD")
    tag = f"{initk}_m{m}_mu{mu:g}"
    cfg = _WORKDIR / f"n5_{tag}.cfg"
    cfg.write_text(gen_family.compile_cfg(rules, f"n5_{tag}", extra,
                                          INITS[initk]))
    probe_dump = _WORKDIR / f"n5_{tag}_init.txt"
    run_engine(cfg, 1, "z", _WORKDIR / f"n5_{tag}_init.trace", probe_dump)
    s0 = tuple(analyzers.parse_dump(probe_dump, *GEOM))
    inp = protocol(m)
    mutant_head = "C" if initk == "slow" else "A"
    mut_pair = ("A", "B") if mutant_head == "A" else ("C", "D")
    rows, engine_s = [], 0.0
    for seed in SEEDS:
        trace = _WORKDIR / f"n5_{tag}_s{seed}.trace"
        dump = _WORKDIR / f"n5_{tag}_s{seed}.txt"
        engine_s += run_engine(cfg, seed, inp, trace, dump)
        applies = analyzers.parse_trace(trace)
        final, cnt, births, muts, t_birth, samples = evolution_replay(
            rules, extra, list(s0), applies, GEOM[1], mutant_head)
        if final != "\n".join(analyzers.parse_dump(dump, *GEOM)):
            sys.exit(f"EXACT-FAIL {tag} seed {seed}")
        slow_end = cnt["A"] + cnt["B"]
        fast_end = cnt["C"] + cnt["D"]
        mut_end = cnt[mut_pair[0]] + cnt[mut_pair[1]]
        res_end = slow_end + fast_end - mut_end
        if slow_end + fast_end == 0:
            outcome = "ALLDEAD"
        elif t_birth is None:
            outcome = "NO_BIRTH"
        elif mut_end > res_end:
            outcome = "TAKEOVER"
        else:
            outcome = "RESIDENT_HOLDS"
        # t_secure: first sample after which the mutant total stays
        # strictly ahead to the end (events); None if never.
        t_secure = None
        if outcome == "TAKEOVER":
            ahead = [(f if initk == "slow" else s) >
                     (s if initk == "slow" else f)
                     for s, f in samples]
            j = len(ahead)
            while j > 0 and ahead[j - 1]:
                j -= 1
            t_secure = (j + 1) * SAMPLE_EVERY
        lastq = samples[3 * len(samples) // 4:]
        mshare = [(f if initk == "slow" else s) / (s + f)
                  for s, f in lastq if s + f]
        rows.append({
            "init": initk, "m": "inf" if m is None else m, "mu": mu,
            "seed": seed, "outcome": outcome, "t_birth": t_birth,
            "t_secure": t_secure,
            "births_A": births["A"], "births_C": births["C"],
            "mut_BD": muts["B>D"], "mut_DB": muts["D>B"],
            "mutant_share_lastq":
                sum(mshare) / len(mshare) if mshare else 0.0,
            "end_slow": slow_end, "end_fast": fast_end,
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
        Path(tempfile.mkdtemp(prefix="night5_"))
    workdir.mkdir(parents=True, exist_ok=True)
    print(f"binary {BIN}\nworkdir {workdir}")

    tasks = [(i, m, mu) for i in INITS for m in M_VALUES
             for mu in MU_VALUES]
    print(f"{len(tasks)} (init,m,mu) points x {len(SEEDS)} seeds "
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
    cols = ["init", "m", "mu", "seed", "outcome", "t_birth", "t_secure",
            "births_A", "births_C", "mut_BD", "mut_DB",
            "mutant_share_lastq", "end_slow", "end_fast", "pokes"]
    with open(here / "night5_evolution.csv", "w", newline="") as f:
        w = csv.DictWriter(f, cols)
        w.writeheader()
        for r in rows:
            w.writerow({c: (f"{r[c]:.3f}" if isinstance(r[c], float)
                            else r[c]) for c in cols})

    def med(v):
        v = sorted(x for x in v if x is not None)
        return v[len(v) // 2] if v else "-"

    print("\nper (init, m, mu): outcomes | med t_birth | med t_secure "
          "| mutant share (last quarter):")
    for initk in INITS:
        for m in M_VALUES:
            mm = "inf" if m is None else m
            for mu in MU_VALUES:
                sub = [r for r in rows if r["init"] == initk
                       and r["m"] == mm and r["mu"] == mu]
                oc = Counter(r["outcome"] for r in sub)
                share = sum(r["mutant_share_lastq"] for r in sub) / len(sub)
                print(f"  {initk:<4} m={mm:>3} mu={mu:<5} "
                      f"TAKE {oc.get('TAKEOVER', 0):>2}  "
                      f"HOLD {oc.get('RESIDENT_HOLDS', 0):>2}  "
                      f"NOBIRTH {oc.get('NO_BIRTH', 0):>2}  "
                      f"DEAD {oc.get('ALLDEAD', 0):>2} | "
                      f"birth {med([r['t_birth'] for r in sub]):>5} | "
                      f"secure {med([r['t_secure'] for r in sub]):>5} | "
                      f"share {share:.2f}")


if __name__ == "__main__":
    main()
