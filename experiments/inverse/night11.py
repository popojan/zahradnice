#!/usr/bin/env python3
"""Night-11 inverse: COMPARTMENTS VS THE ORDER-FUELED PARASITE.

The classical answer to parasites is compartmentalization: split the
population into groups, let them grow, pool, re-inoculate — group-
level variance plus differential contribution suppresses the
parasite (stochastic corrector: Szathmary & Demeter 1987; transient
compartmentalization: Matsumura 2016, Blokhuis 2018/2020). Every
model in that literature assumes a replicase and free compartments.
Here we test the classical protocol against night-10's order-fueled
parasite, in a substrate with no copy primitive and compartments
that share ONE event budget.

Geometry: compartments are screen ROWS — rule bodies are single-row,
so rows are strictly isolated column-torus rings, yet all (rule,
position) matches compete for the same serialized event stream:
compartments pay each other's bills. Damage pokes land matter-
proportionally across all rows.

Transient compartmentalization is the harness's pipette (same
status as pokes — environment, not law): every E events the run is
paused, all compartment contents are pooled, and compartments are
re-inoculated; heads are re-placed (machinery is eternal). Two
mixing modes bracket what group-level heredity CAN transmit:
  scr  — classical TC pooling: genes pooled as a multiset,
         re-dealt scattered (composition heritable, ORDER not);
  chk  — gentle pooling: gene sequences concatenated and dealt as
         contiguous chunks (runs partially heritable);
  none — pure isolation, no mixing (same law, same events).
State surgery between episodes is exact: a builder nonterminal B
(harness law, dedicated trigger bytes) rewrites the screen cell by
cell from the input protocol; every episode is trace-replayed and
verified byte-for-byte.

Predictions from the arc's own laws, stated before running:
  (a) L6 inversion — small compartments order faster (night-4
      fixation), and order is parasite fuel: compartmentalization
      should MAINTAIN or RAISE the parasite band, not suppress it;
  (b) group selection has nothing to grip — the parasite is a
      matter-benefactor (night-10 finding 3), so cov(contribution,
      rho) ~ 0; at m=2 it may go POSITIVE (parasitized compartments
      hold MORE matter — selection FOR the parasite);
  (c) scr-mixing transmits no order, so by L5 group heredity of the
      phase variable is absent and TC cannot select on it.

Sweep: chem {paraonly, plain-control} x structure {bulk4, 2x24,
4x12, 8x6, bulk8} (total capacity 48, machinery matched 4 heads —
8x6 needs 8, paired with bulk8) x m {8, 2} x mix {none, scr, chk}
x 24 shared seeds. Exact accounting throughout.

Usage: python3 night11.py [--jobs N] [--workdir DIR]
Outputs: night11_tc.csv, summary on stdout.
"""
import argparse
import csv
import random
import statistics
import subprocess
import sys
import tempfile
import time
import zlib
from collections import Counter
from pathlib import Path
from multiprocessing import Pool

import gen_family
import analyzers
import night7
import night8
import night10
from night10_exponent import site_counts

ROOT = Path(__file__).resolve().parents[2]
BIN = ROOT / "zahradnice"
R = gen_family.Rule

STRUCTS = {                      # name: (K rows, n cols, heads/comp)
    "bulk4": (1, 48, 4),
    "c2x24": (2, 24, 2),
    "c4x12": (4, 12, 1),
    "c8x6": (8, 6, 1),
    "bulk8": (1, 48, 8),
}
M_VALUES = (8, 2)
MIXES = ("none", "scr", "chk")
SEEDS = tuple(range(1, 25))
E_DYN = 1500
EPISODES = 16
STRIDE = 37
GENE = {"f": "f", "F": "f", "s": "s", "S": "s", "W": "s"}
HEADOF = {"f": "F", "s": "S"}
INSTR = {"f": "f", "s": "s", " ": "h", "F": "1", "S": "2"}

BUILD_STD = [R("B", "f", "write", "B", "f"),
             R("B", "s", "write", "B", "s"),
             R("B", "~", "write", "B", "h"),
             R("B", "F", "write", "B", "1"),
             R("B", "S", "write", "B", "2"),
             R("B", "~", "self", None, "q")]
BDOWN = R("B", "~", "bdown", None, "v")

_WORKDIR = None


def rules11(chem):
    return (night10.rules10("paraonly") if chem == "paraonly"
            else night7.rules7())


def compile_cfg11(rules, name):
    extra = gen_family.poke_rules("fs") + BUILD_STD
    lines = [f"#!{name}", "#threads 1", "^Bul"]
    for r in list(gen_family.canonical(rules)) + extra:
        lines.append(gen_family.head(r))
        lines.append(gen_family.body(r))
    lines += ["==Bv~", "@@@", "  B"]
    return "\n".join(lines) + "\n"


def imap11(rules):
    extra = gen_family.poke_rules("fs") + BUILD_STD
    m = gen_family.idx_map(rules, extra)
    nb = sum(1 for (lhs, _i) in m if lhs == "B")
    m[("B", nb)] = BDOWN
    return m


def skip_plan(K, n):
    """Per-row (write-order columns, skip column) for the builder."""
    col, plan = 0, []
    for _r in range(K):
        order = [(col + j) % n for j in range(n - 1)]
        skip = (col + n - 1) % n
        plan.append((order, skip))
        col = skip
    return plan


def rot_to_hole(cells, skip):
    """Rotate a row so the skip column is empty."""
    n = len(cells)
    if cells[skip] == " ":
        return cells
    h0 = next(j for j, c in enumerate(cells) if c == " ")
    sh = (skip - h0) % n
    out = [" "] * n
    for j, c in enumerate(cells):
        out[(j + sh) % n] = c
    return out


def build_protocol(comps, plan):
    n = len(comps[0])
    out = []
    for r, (order, skip) in enumerate(plan):
        assert comps[r][skip] == " ", "skip column not empty"
        out += [INSTR[comps[r][c]] for c in order]
        out.append("v" if r < len(plan) - 1 else "q")
    return "".join(out)


def place_heads(genes, h, rng):
    """Convert h sampled genes to heads; pad with 'f' if short."""
    created = 0
    while len(genes) < h:
        genes.append("f")
        created += 1
    for j in rng.sample(range(len(genes)), h):
        genes[j] = HEADOF[GENE[genes[j]]]
    return created


def scatter(genes, n, skip, rng):
    cells = [" "] * n
    for j, g in zip(rng.sample(range(n), len(genes)), genes):
        cells[j] = g
    return rot_to_hole(cells, skip)


def contiguous(genes, n, skip, rng):
    cells = [" "] * n
    off = rng.randrange(n)
    for j, g in enumerate(genes):
        cells[(off + j) % n] = g
    return rot_to_hole(cells, skip)


def init_comps(K, n, h, plan, rng):
    comps = []
    for r in range(K):
        genes = [rng.choice("fs") for _ in range(max(h, (n - 1) // 2))]
        place_heads(genes, h, rng)
        comps.append(scatter(genes, n, plan[r][1], rng))
    return comps


def mix_comps(grid, mode, K, n, h, plan, rng):
    """Pool end-of-episode rows, re-inoculate. Returns (comps,
    heads_created)."""
    if mode == "scr":
        pool = [GENE[c] for row in grid for c in row if c in GENE]
        rng.shuffle(pool)
        i = min(len(pool) // K, n - 1)
        deals = [pool[k * i:(k + 1) * i] for k in range(K)]
    else:
        seqs = []
        for row in grid:
            holes = [j for j, c in enumerate(row) if c not in GENE]
            start = (holes[0] + 1) if holes else 0
            seqs.append([GENE[row[(start + j) % n]]
                         for j in range(n)
                         if row[(start + j) % n] in GENE])
        order = list(range(K))
        rng.shuffle(order)
        pool = [g for k in order for g in seqs[k]]
        i = min(len(pool) // K, n - 1)
        deals = [pool[k * i:(k + 1) * i] for k in range(K)]
    comps, created = [], 0
    for r in range(K):
        genes = list(deals[r])
        created += place_heads(genes, h, rng)
        if mode == "scr":
            comps.append(scatter(genes, n, plan[r][1], rng))
        else:
            comps.append(contiguous(genes, n, plan[r][1], rng))
    return comps, created


def dyn_input(m, ep, events):
    warm = "T" * 32 if ep == 0 else ""
    return warm + ("p" + "T" * m) * (events // (m + 1))


def row_comp(rc):
    return (rc["f"] + rc["F"], rc["s"] + rc["S"] + rc["W"])


def wmean_rho(grid):
    """(matter-weighted mean rho, [(tape_k, rho_k)])."""
    per = []
    for row in grid:
        tape = sum(1 for c in row if c in GENE)
        per.append((tape, night10.boundary_density(row)))
    tot = sum(t for t, r in per if r is not None)
    if not tot:
        return None, per
    return sum(t * r for t, r in per if r is not None) / tot, per


def _pool_init(workdir_str):
    global _WORKDIR
    _WORKDIR = Path(workdir_str)


def eval_point(task):
    chem, struct, m, mix = task
    K, n, h = STRUCTS[struct]
    rules = rules11(chem)
    imap = imap11(rules)
    plan = skip_plan(K, n)
    geom = (K + 1, n)
    cfg = _WORKDIR / f"n11_{chem}_{struct}_m{m}_{mix}.cfg"
    cfg.write_text(compile_cfg11(rules, cfg.stem))
    n_ep = 1 if mix == "none" else EPISODES
    ep_events = E_DYN * EPISODES if mix == "none" else E_DYN
    rows_out = []
    for seed in SEEDS:
        rng = random.Random(
            1_000_000 * m + 1000 * seed
            + zlib.crc32(f"{chem}|{struct}|{mix}".encode()) % 997)
        comps = init_comps(K, n, h, plan, rng)
        samples = []
        covs = []
        bvars = []
        drifts = []
        res = 0
        ext_ev = 0
        created = 0
        for ep in range(n_ep):
            tag = f"n11_{chem}_{struct}_m{m}_{mix}_s{seed}_e{ep}"
            inp = build_protocol(comps, plan) + dyn_input(
                m, ep, ep_events)
            dump = _WORKDIR / f"{tag}.txt"
            tr = _WORKDIR / f"{tag}.trace"
            r = subprocess.run(
                [str(BIN), "--headless", "--screen",
                 f"{geom[0]},{geom[1]}", "--seed",
                 str(100 * seed + ep), "--input", inp,
                 "--dump-screen", str(dump), "--trace", str(tr),
                 str(cfg)],
                capture_output=True, text=True)
            if r.returncode != 0:
                raise RuntimeError(r.stderr.strip())
            applies = analyzers.parse_trace(tr)
            grid = [[" "] * n for _ in range(K)]
            grid[0][0] = "B"
            rowcnt = [Counter() for _ in range(K)]
            rowcnt[0]["B"] += 1
            extinct = [{g: False for g in "fs"} for _ in range(K)]
            built = False
            ev = 0
            ep_first_rho = None
            for lhs, idx, ro, co, trig in applies:
                rule = imap[(lhs, idx)]
                rr = ro - 1
                if rule.kind == "bdown":
                    for r2, c2, ch in ((rr, co, " "),
                                       (rr + 1, co, "B")):
                        old = grid[r2][c2]
                        if old != " ":
                            rowcnt[r2][old] -= 1
                        if ch != " ":
                            rowcnt[r2][ch] += 1
                        grid[r2][c2] = ch
                else:
                    for dc, ch in gen_family.writes(rule):
                        c2 = (co + dc) % n
                        old = grid[rr][c2]
                        if old != " ":
                            rowcnt[rr][old] -= 1
                        if ch != " ":
                            rowcnt[rr][ch] += 1
                        grid[rr][c2] = ch
                if trig == "q":
                    built = True
                    for k in range(K):
                        xf, xs = row_comp(rowcnt[k])
                        extinct[k]["f"] = xf == 0
                        extinct[k]["s"] = xs == 0
                    continue
                if not built:
                    continue
                ev += 1
                xf, xs = row_comp(rowcnt[rr])
                for g, x in (("f", xf), ("s", xs)):
                    if extinct[rr][g]:
                        if x > 0:
                            res += 1
                            extinct[rr][g] = False
                    elif x == 0:
                        extinct[rr][g] = True
                ext_ev += sum(1 for k in range(K)
                              for g in "fs" if extinct[k][g])
                if ev % STRIDE == 0:
                    rho, per = wmean_rho(grid)
                    tape = sum(t for t, _ in per)
                    gaps = sum(sum(site_counts(row)[2:])
                               for row in grid)
                    rm = (statistics.mean(
                        night8.run_stats(row)[0] for row in grid))
                    samples.append((rho, tape, gaps, rm))
                    if ep_first_rho is None:
                        ep_first_rho = rho
            if "\n".join("".join(rr2) for rr2 in grid) != "\n".join(
                    analyzers.parse_dump(dump, *geom)):
                sys.exit(f"EXACT-FAIL {tag}")
            dump.unlink()
            tr.unlink()
            rho_end, per = wmean_rho(grid)
            if ep_first_rho is not None and rho_end is not None:
                drifts.append(rho_end - ep_first_rho)
            if K > 1:
                valid = [(t, r2) for t, r2 in per if r2 is not None]
                tot = sum(t for t, _ in valid)
                if tot and len(valid) > 1:
                    ws = [t / tot for t, _ in valid]
                    rs = [r2 for _, r2 in valid]
                    mw = sum(w * r2 for w, r2 in zip(ws, rs))
                    covs.append(mw - (sum(rs) / len(rs)))
                    bvars.append(statistics.pvariance(rs))
            if mix != "none" and ep < n_ep - 1:
                comps, cr = mix_comps(grid, mix, K, n, h, plan, rng)
                created += cr
        lastq = samples[3 * len(samples) // 4:]
        lq = [s for s in lastq if s[0] is not None]
        rows_out.append({
            "chem": chem, "struct": struct, "m": m, "mix": mix,
            "seed": seed, "K": K, "n": n, "heads": h,
            "rho_lastq": (statistics.mean(s[0] for s in lq)
                          if lq else None),
            "tape_lastq": (statistics.mean(s[1] for s in lastq)
                           if lastq else 0),
            "fuel_lastq": (statistics.mean(s[2] for s in lastq)
                           if lastq else 0),
            "runmean_lastq": (statistics.mean(s[3] for s in lastq)
                              if lastq else 0),
            "cov_wrho": (statistics.mean(covs) if covs else None),
            "bvar_rho": (statistics.mean(bvars) if bvars else None),
            "drift": (statistics.mean(drifts) if drifts else None),
            "res": res, "ext_ev": ext_ev, "heads_created": created,
            "rho_traj": ";".join(
                f"{samples[min(len(samples) - 1, k * len(samples) // 8)][0]:.2f}"
                if samples[min(len(samples) - 1,
                               k * len(samples) // 8)][0] is not None
                else "-" for k in range(1, 9)) if samples else ""})
    cfg.unlink()
    return rows_out


def tasks():
    out = []
    for struct in STRUCTS:
        for m in M_VALUES:
            for mix in MIXES:
                out.append(("paraonly", struct, m, mix))
    for struct in ("bulk4", "c4x12"):
        for m in M_VALUES:
            for mix in ("none", "scr"):
                out.append(("plain", struct, m, mix))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", type=int, default=8)
    ap.add_argument("--workdir", default=None)
    args = ap.parse_args()
    workdir = Path(args.workdir) if args.workdir else \
        Path(tempfile.mkdtemp(prefix="night11_"))
    workdir.mkdir(parents=True, exist_ok=True)
    here = Path(__file__).parent
    print(f"binary {BIN}\nworkdir {workdir}")
    tl = tasks()
    print(f"{len(tl)} points x {len(SEEDS)} seeds "
          f"= {len(tl) * len(SEEDS)} runs")
    t0 = time.perf_counter()
    with Pool(args.jobs, _pool_init, (str(workdir),)) as pool:
        results = pool.map(eval_point, tl, chunksize=1)
    rows = [r for res in results for r in res]
    print(f"wall {time.perf_counter() - t0:.1f}s, exactness: all pass\n")

    cols = ["chem", "struct", "m", "mix", "seed", "K", "n", "heads",
            "rho_lastq", "tape_lastq", "fuel_lastq", "runmean_lastq",
            "cov_wrho", "bvar_rho", "drift", "res", "ext_ev",
            "heads_created", "rho_traj"]
    with open(here / "night11_tc.csv", "w", newline="") as f:
        w = csv.DictWriter(f, cols)
        w.writeheader()
        for r in rows:
            w.writerow({c: (f"{r[c]:.4f}" if isinstance(r[c], float)
                            else r[c]) for c in cols})

    def agg(sub, key):
        v = [r[key] for r in sub if r[key] is not None]
        return statistics.mean(v) if v else float("nan")

    print("per point (mean over 24 seeds): rho lastq | tape | fuel "
          "| run | cov(w,rho) | res | drift:")
    for chem, struct, m, mix in tl:
        sub = [r for r in rows if (r["chem"], r["struct"], r["m"],
                                   r["mix"]) == (chem, struct, m, mix)]
        print(f"  {chem:<8} {struct:<6} m={m} {mix:<4}: "
              f"rho {agg(sub, 'rho_lastq'):.3f} | "
              f"tape {agg(sub, 'tape_lastq'):5.1f} | "
              f"fuel {agg(sub, 'fuel_lastq'):4.2f} | "
              f"run {agg(sub, 'runmean_lastq'):4.1f} | "
              f"cov {agg(sub, 'cov_wrho'):+.4f} | "
              f"res {sum(r['res'] for r in sub) / len(sub):6.0f} | "
              f"drift {agg(sub, 'drift'):+.3f}")


if __name__ == "__main__":
    main()
