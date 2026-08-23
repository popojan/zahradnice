#!/usr/bin/env python3
"""Night-10 addendum: THE GROWTH-LAW AUDIT — is the parasite phase
parabolic coexistence in disguise?

The literature audit (paper/related-work.md) flagged one rival
explanation for night-10's permanent two-type coexistence:
sub-exponential ("parabolic") replicator kinetics, where per-capita
growth declining in OWN abundance yields survival-of-everybody
(Szathmary & Gladkih 1989; Paczko, Szathmary & Szilagyi 2024). This
addendum replays the night-10 arms and separates the two mechanisms
by signatures they cannot share:

  parabolic:    production of glyph g is autocatalytic — rate
                ~ x_g^p (p<1) THROUGH OWN ABUNDANCE; x_g = 0 is
                absorbing (no x^p law regrows an extinct type).
  fuel-coupled: minority production is a CROSS channel — the
                deceptive pair writes g out of the OTHER glyph's
                run context; rate independent of x_g; x_g = 0 is
                NOT absorbing (resurrection from the majority
                crystal).

Measured per (arm, m), pooled over the night-10 seeds:
  1. birth-source decomposition vs own-share bins (base/pair = own
     channel, dpair = cross channel);
  2. production propensity AT extinction: gap-context sites of the
     majority machinery while x_g = 0 (any positive value cannot be
     mimicked by k*x^p), plus resurrection counts and extinct time;
  3. the naive exponent p_naive a growth-law fit would report
     (log birth rate vs log x_g), to state the confusion explicitly;
  4. covert-spatial-structure check (audit defense 2): best
     circular-shift overlap of minority occupancy between samples
     vs permutation null, drift concentration, minority run length
     vs shuffled null.
Control: the order arm (honest pair, identical site geometry,
own-glyph writes) has no cross channel — extinction there must be
absorbing, though the same naive fit sees the same site kinetics.

Usage: python3 night10_exponent.py [--jobs N] [--workdir DIR]
Outputs: night10_exponent.csv (per run),
         night10_exponent_bins.csv (pooled tables), stdout summary.
"""
import argparse
import csv
import math
import random
import statistics
import subprocess
import sys
import tempfile
import time
from collections import Counter
from pathlib import Path
from multiprocessing import Pool

import gen_family
import analyzers
import night7
import night10

ROOT = Path(__file__).resolve().parents[2]
BIN = ROOT / "zahradnice"
RING = 24
GEOM = (6, RING)
ARMS = ("order", "para", "paraonly")
M_VALUES = (8, 4, 2)
SEEDS = tuple(range(1, 33))
STRIDE = 37            # sampling stride, coprime with ring and m+1
SP_EVERY = 11          # spatial check every SP_EVERY-th sample
SP_PERMS = 6
NB = 12                # share bins
OWN = {"F": "f", "S": "s"}

_WORKDIR = None


def genome(row):
    return ["f" if c in "fF" else "s" if c in "sSW" else None
            for c in row]


def site_counts(row):
    """Applicable production sites: (base_F, base_S, gap_F, gap_S)."""
    n = len(row)
    bF = bS = gF = gS = 0
    for i, c in enumerate(row):
        if c not in "FS":
            continue
        e1, e2, w = row[(i + 1) % n], row[(i + 2) % n], row[i - 1]
        if c == "F":
            bF += e1 == " "
            gF += w == "f" and e1 == " " and e2 == " "
        else:
            bS += e1 == " "
            gS += w == "s" and e1 == " " and e2 == " "
    return bF, bS, gF, gS


def run_lengths(g):
    """Mean circular run length of each glyph, holes break runs."""
    n = len(g)
    runs = Counter()
    tot = Counter()
    i = 0
    if all(x == g[0] for x in g):
        return {g[0]: float(n)} if g[0] else {}
    while g[i] == g[i - 1]:
        i += 1
    for k in range(n):
        j = (i + k) % n
        c = g[j]
        if c is None:
            continue
        if g[j - 1] != c:
            runs[c] += 1
        tot[c] += 1
    return {c: tot[c] / runs[c] for c in runs}


def best_shift(a_pos, b_pos, n):
    """(max overlap, argmax shift) of position sets on a ring."""
    best, arg = -1, 0
    bset = set(b_pos)
    for sh in range(n):
        ov = sum(1 for p in a_pos if (p + sh) % n in bset)
        if ov > best:
            best, arg = ov, sh
    return best, arg


def _pool_init(workdir_str):
    global _WORKDIR
    _WORKDIR = Path(workdir_str)


def eval_point(task):
    arm, m = task
    rules = night10.rules10(arm)
    extra = gen_family.poke_rules("fs")
    imap = gen_family.idx_map(rules, extra)
    rows = []
    births_bin = [Counter() for _ in range(NB)]
    expo_bin = [0] * NB
    births_x = Counter()
    expo_x = Counter()
    for seed in SEEDS:
        rng = random.Random(10_000 * m + seed)
        tag = f"n10x_{arm}_m{m}_s{seed}"
        cfg = _WORKDIR / f"{tag}.cfg"
        cfg.write_text(gen_family.compile_cfg(
            rules, tag, extra, night7.init_lines(RING, 0.5)))
        d0 = _WORKDIR / f"{tag}_i.txt"
        for inp, dump, tr in (
                ("z", d0, _WORKDIR / f"{tag}_i.trace"),
                (night7.protocol(m), _WORKDIR / f"{tag}.txt",
                 _WORKDIR / f"{tag}.trace")):
            r = subprocess.run(
                [str(BIN), "--headless", "--screen",
                 f"{GEOM[0]},{GEOM[1]}", "--seed", str(seed),
                 "--input", inp, "--dump-screen", str(dump),
                 "--trace", str(tr), str(cfg)],
                capture_output=True, text=True)
            if r.returncode != 0:
                raise RuntimeError(r.stderr.strip())
        s0 = tuple(analyzers.parse_dump(d0, *GEOM))
        applies = analyzers.parse_trace(_WORKDIR / f"{tag}.trace")
        grid = [list(rr) for rr in s0]
        cnt = Counter(c for row in s0 for c in row if c in "fsFSW")
        rep = Counter()
        res = Counter()
        ext_ev = Counter()
        extinct = {g: night7.comp(cnt)["fs".index(g)] == 0 for g in "fs"}
        phi0_cross = []
        phi0_own = []
        min_cross = Counter()
        sp_exc = []
        sp_shifts = []
        rl_obs = []
        rl_null = []
        prev_sp = None
        n_samp = 0
        for i, (lhs, idx, ro, co, trig) in enumerate(applies):
            rule = imap[(lhs, idx)]
            xf, xs = night7.comp(cnt)
            tape = xf + xs
            if tape:
                expo_bin[min(NB - 1, int(xf / tape * NB))] += 1
                expo_bin[min(NB - 1, int(xs / tape * NB))] += 1
            expo_x[xf] += 1
            expo_x[xs] += 1
            if trig == "T":
                born = channel = None
                if rule.kind == "reqwrite" and rule.arg[0] == "~":
                    born, channel, k = rule.arg[1], "base", 1
                elif rule.kind == "gapwrite":
                    born = rule.arg[1]
                    channel = ("pair" if born == OWN[rule.lhs]
                               else "dpair")
                    k = 2
                if born:
                    rep[channel] += k
                    x_own = xf if born == "f" else xs
                    q = x_own / tape if tape else 0.0
                    births_bin[min(NB - 1, int(q * NB))][channel] += k
                    births_x[(x_own, channel)] += k
                    if q < 1 / 3:
                        min_cross[channel] += k
            for dc, ch in gen_family.writes(rule):
                rr, c = ro - 1, (co + dc) % RING
                old = grid[rr][c]
                if old in "fsFSW":
                    cnt[old] -= 1
                if ch in "fsFSW":
                    cnt[ch] += 1
                grid[rr][c] = ch
            xf, xs = night7.comp(cnt)
            for g, x in (("f", xf), ("s", xs)):
                if extinct[g]:
                    ext_ev[g] += 1
                    if x > 0:
                        res[g] += 1
                        extinct[g] = False
                elif x == 0:
                    extinct[g] = True
            if (i + 1) % STRIDE == 0:
                n_samp += 1
                row2 = grid[2]
                bF, bS, gF, gS = site_counts(row2)
                if xs == 0:
                    phi0_cross.append(gF)
                    phi0_own.append(bS + gS)
                if xf == 0:
                    phi0_cross.append(gS)
                    phi0_own.append(bF + gF)
                if arm != "order" and n_samp % SP_EVERY == 0:
                    gvec = genome(row2)
                    mg = "f" if xf < xs else "s"
                    pos = [j for j, c in enumerate(gvec) if c == mg]
                    gcells = [j for j, c in enumerate(gvec)
                              if c is not None]
                    if 0 < len(pos) < len(gcells):
                        rl = run_lengths(gvec)
                        if mg in rl:
                            rl_obs.append(rl[mg])
                            nulls = []
                            for _ in range(SP_PERMS):
                                sh = gvec[:]
                                vals = [sh[j] for j in gcells]
                                rng.shuffle(vals)
                                for j, v in zip(gcells, vals):
                                    sh[j] = v
                                rn = run_lengths(sh)
                                if mg in rn:
                                    nulls.append(rn[mg])
                            if nulls:
                                rl_null.append(
                                    sum(nulls) / len(nulls))
                        if prev_sp is not None and prev_sp[1] == mg:
                            ov, sh = best_shift(prev_sp[0], pos, RING)
                            novs = []
                            for _ in range(SP_PERMS):
                                rp = rng.sample(gcells,
                                                min(len(pos),
                                                    len(gcells)))
                                novs.append(best_shift(
                                    prev_sp[0], rp, RING)[0])
                            base = sum(novs) / len(novs)
                            denom = min(len(prev_sp[0]), len(pos))
                            sp_exc.append((ov - base) / denom)
                            if ov > base:
                                sp_shifts.append(sh)
                        prev_sp = (pos, mg)
                    else:
                        prev_sp = None
        if "\n".join("".join(rr) for rr in grid) != "\n".join(
                analyzers.parse_dump(_WORKDIR / f"{tag}.txt", *GEOM)):
            sys.exit(f"EXACT-FAIL {tag}")
        for p in (cfg, d0, _WORKDIR / f"{tag}_i.trace",
                  _WORKDIR / f"{tag}.txt", _WORKDIR / f"{tag}.trace"):
            p.unlink()
        drift_R = None
        if len(sp_shifts) > 3:
            cx = sum(math.cos(2 * math.pi * s / RING)
                     for s in sp_shifts) / len(sp_shifts)
            sy = sum(math.sin(2 * math.pi * s / RING)
                     for s in sp_shifts) / len(sp_shifts)
            drift_R = math.hypot(cx, sy)
        mtot = sum(min_cross.values())
        rows.append({
            "arm": arm, "m": m, "seed": seed,
            "res_f": res["f"], "res_s": res["s"],
            "ext_ev_f": ext_ev["f"], "ext_ev_s": ext_ev["s"],
            "phi0_cross": (statistics.mean(phi0_cross)
                           if phi0_cross else None),
            "phi0_own": (statistics.mean(phi0_own)
                         if phi0_own else None),
            "n_ext_samples": len(phi0_cross),
            "b_base": rep["base"], "b_pair": rep["pair"],
            "b_dpair": rep["dpair"],
            "min_cross_share": (min_cross["dpair"] / mtot
                                if mtot else None),
            "sp_overlap_exc": (statistics.mean(sp_exc)
                               if sp_exc else None),
            "sp_drift_R": drift_R,
            "runlen_obs": (statistics.mean(rl_obs)
                           if rl_obs else None),
            "runlen_null": (statistics.mean(rl_null)
                            if rl_null else None)})
    return {"rows": rows, "bins": (births_bin, expo_bin),
            "xtab": (births_x, expo_x), "arm": arm, "m": m}


def wls_slope(pts):
    """Weighted LS slope of y on t, pts = [(t, y, w)]."""
    sw = sum(w for _, _, w in pts)
    mt = sum(t * w for t, _, w in pts) / sw
    my = sum(y * w for _, y, w in pts) / sw
    num = sum(w * (t - mt) * (y - my) for t, y, w in pts)
    den = sum(w * (t - mt) ** 2 for t, _, w in pts)
    return num / den if den else float("nan")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", type=int, default=8)
    ap.add_argument("--workdir", default=None)
    args = ap.parse_args()
    workdir = Path(args.workdir) if args.workdir else \
        Path(tempfile.mkdtemp(prefix="night10x_"))
    workdir.mkdir(parents=True, exist_ok=True)
    here = Path(__file__).parent
    print(f"binary {BIN}\nworkdir {workdir}")
    tasks = [(a, m) for a in ARMS for m in M_VALUES]
    print(f"{len(tasks)} points x {len(SEEDS)} seeds "
          f"= {len(tasks) * len(SEEDS)} runs")
    t0 = time.perf_counter()
    with Pool(args.jobs, _pool_init, (str(workdir),)) as pool:
        results = pool.map(eval_point, tasks, chunksize=1)
    rows = [r for res in results for r in res["rows"]]
    print(f"wall {time.perf_counter() - t0:.1f}s, exactness: all pass\n")

    cols = ["arm", "m", "seed", "res_f", "res_s", "ext_ev_f",
            "ext_ev_s", "phi0_cross", "phi0_own", "n_ext_samples",
            "b_base", "b_pair", "b_dpair", "min_cross_share",
            "sp_overlap_exc", "sp_drift_R", "runlen_obs",
            "runlen_null"]
    with open(here / "night10_exponent.csv", "w", newline="") as f:
        w = csv.DictWriter(f, cols)
        w.writeheader()
        for r in rows:
            w.writerow({c: (f"{r[c]:.3f}" if isinstance(r[c], float)
                            else r[c]) for c in cols})

    with open(here / "night10_exponent_bins.csv", "w",
              newline="") as f:
        w = csv.writer(f)
        w.writerow(["table", "arm", "m", "key", "exposure",
                    "base", "pair", "dpair"])
        for res in results:
            arm, m = res["arm"], res["m"]
            bb, eb = res["bins"]
            for b in range(NB):
                w.writerow(["sharebin", arm, m, f"{b / NB:.3f}",
                            eb[b], bb[b]["base"], bb[b]["pair"],
                            bb[b]["dpair"]])
            bx, ex = res["xtab"]
            for x in sorted(ex):
                w.writerow(["xcount", arm, m, x, ex[x],
                            bx.get((x, "base"), 0),
                            bx.get((x, "pair"), 0),
                            bx.get((x, "dpair"), 0)])

    for res in results:
        arm, m = res["arm"], res["m"]
        sub = [r for r in rows if r["arm"] == arm and r["m"] == m]
        bx, ex = res["xtab"]
        pts = []
        for x in sorted(ex):
            if x < 1 or ex[x] < 500:
                continue
            births = sum(bx.get((x, ch), 0)
                         for ch in ("base", "pair", "dpair"))
            if births:
                pts.append((math.log(x), math.log(births / ex[x]),
                            ex[x]))
        p_naive = wls_slope(pts) if len(pts) > 2 else float("nan")
        b0 = sum(bx.get((0, ch), 0)
                 for ch in ("base", "pair", "dpair"))
        e0 = ex.get(0, 0)
        res_tot = sum(r["res_f"] + r["res_s"] for r in sub)
        res_runs = sum(1 for r in sub if r["res_f"] + r["res_s"])
        ext_tot = sum(r["ext_ev_f"] + r["ext_ev_s"] for r in sub)
        p0c = [r["phi0_cross"] for r in sub
               if r["phi0_cross"] is not None]
        p0o = [r["phi0_own"] for r in sub
               if r["phi0_own"] is not None]
        mcs = [r["min_cross_share"] for r in sub
               if r["min_cross_share"] is not None]
        line = (f"{arm:<8} m={m}: p_naive {p_naive:5.2f} | "
                f"resurrections {res_tot:4d} in {res_runs:2d}/32 runs"
                f" (extinct {ext_tot:6d} ev, births@x=0 {b0}"
                f"/{e0} exp) | ")
        line += (f"phi0 cross {statistics.mean(p0c):.2f} own "
                 f"{statistics.mean(p0o):.2f}" if p0c else "phi0 -")
        if mcs:
            line += f" | minority cross-share {statistics.mean(mcs):.2f}"
        se = [r["sp_overlap_exc"] for r in sub
              if r["sp_overlap_exc"] is not None]
        dr = [r["sp_drift_R"] for r in sub
              if r["sp_drift_R"] is not None]
        ro_ = [r["runlen_obs"] for r in sub
               if r["runlen_obs"] is not None]
        rn_ = [r["runlen_null"] for r in sub
               if r["runlen_null"] is not None]
        if se:
            line += (f" | sp exc {statistics.mean(se):+.3f}"
                     f" driftR {statistics.mean(dr):.2f}"
                     if dr else
                     f" | sp exc {statistics.mean(se):+.3f}")
        if ro_ and rn_:
            line += (f" | runlen {statistics.mean(ro_):.2f}"
                     f" vs null {statistics.mean(rn_):.2f}")
        print(line)

    print("\nshare-bin birth decomposition (pooled, "
          "births per 1k exposure events):")
    for res in results:
        arm, m = res["arm"], res["m"]
        bb, eb = res["bins"]
        cells = []
        for b in range(NB // 2):
            e = eb[b]
            if not e:
                cells.append("      -      ")
                continue
            t = 1000 / e
            cells.append(f"{bb[b]['base'] * t:4.1f}/"
                         f"{bb[b]['pair'] * t:4.1f}/"
                         f"{bb[b]['dpair'] * t:4.1f}")
        print(f"  {arm:<8} m={m} q<0.5 bins (base/pair/dpair): "
              + " | ".join(cells))


if __name__ == "__main__":
    main()
