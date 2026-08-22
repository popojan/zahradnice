#!/usr/bin/env python3
"""Night-9: consolidation — closing the open questions of nights 4/7/8.

A. (n7) The m=8 ring-24 s-rise with neutral per-event flows:
   windowed drift analysis at 4x horizon — is E[ds | low tape] > 0
   while E[ds | full tape] ~ 0 (transient shelter during partial
   collapses)?
B. (n7) Shelter scaling: a 3-stroke s (extra settle state V) should
   raise machinery residence on s and with it the collapse-regime
   s-share, if the residence theory is right.
C. (n8) Codon-dependent collapse boundary: fine damage grid x
   {base, pair} — where does the commons die, per arm?
D. (n4) CONTESTED REPAIR — the missing cell of the night-4 law.
   No movers: two static tissues B/D; every hole adjacent to tissue
   is claimed via west-claim (reqwrite ~X) and, in the contested
   arm, ALSO via east-claim (westclaim, the new negative-offset
   shape). Handicap wd on D's claims. Prediction: uncontested arm
   handicap invisible (night 4); contested arm handicap = selection.

Usage: python3 night9.py [--jobs N] [--workdir DIR]
Outputs: night9_{drift,dwell,boundary,contested}.csv, summary.
"""
import argparse
import csv
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
import night8

ROOT = Path(__file__).resolve().parents[2]
BIN = ROOT / "zahradnice"
RING = 24
GEOM = (6, RING)

_WORKDIR = None


def _pool_init(workdir_str):
    global _WORKDIR
    _WORKDIR = Path(workdir_str)
    night8._pool_init(workdir_str)


def engine(cfg, seed, inp, trace, dump):
    r = subprocess.run(
        [str(BIN), "--headless", "--screen", f"{GEOM[0]},{GEOM[1]}",
         "--seed", str(seed), "--input", inp, "--dump-screen", str(dump),
         "--trace", str(trace), str(cfg)],
        capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip())


def run_one(rules, extra, init, seed, inp, tag, glyphs):
    """Run + exact replay; returns (s0, applies, grid, cnt, imap)."""
    cfg = _WORKDIR / f"{tag}_s{seed}.cfg"
    cfg.write_text(gen_family.compile_cfg(rules, tag, extra, init))
    d0 = _WORKDIR / f"{tag}_s{seed}_i.txt"
    engine(cfg, seed, "z", _WORKDIR / f"{tag}_s{seed}_i.trace", d0)
    s0 = tuple(analyzers.parse_dump(d0, *GEOM))
    tr = _WORKDIR / f"{tag}_s{seed}.trace"
    dp = _WORKDIR / f"{tag}_s{seed}.txt"
    engine(cfg, seed, inp, tr, dp)
    applies = analyzers.parse_trace(tr)
    imap = gen_family.idx_map(rules, extra)
    grid = [list(r) for r in s0]
    cnt = Counter(c for row in s0 for c in row if c in glyphs)
    expect = "\n".join(analyzers.parse_dump(dp, *GEOM))
    for p in (tr, dp, d0):
        p.unlink()
    return s0, applies, grid, cnt, imap, expect


def step(grid, cnt, imap, ap, glyphs):
    lhs, idx, ro, co, trig = ap
    rule = imap[(lhs, idx)]
    for dc, ch in gen_family.writes(rule):
        r, c = ro - 1, (co + dc) % RING
        old = grid[r][c]
        if old in glyphs:
            cnt[old] -= 1
        if ch in glyphs:
            cnt[ch] += 1
        grid[r][c] = ch
    return rule


def check_exact(grid, expect, tag):
    if "\n".join("".join(r) for r in grid) != expect:
        sys.exit(f"EXACT-FAIL {tag}")


# --- A: drift vs tape level, night-7 chemistry, 4x horizon ----------

def eval_A(seed):
    rules = night7.rules7()
    extra = gen_family.poke_rules("fs")
    inp = "T" * 32 + ("p" + "T" * 8) * (96000 // 9)
    s0, applies, grid, cnt, imap, expect = run_one(
        rules, extra, night7.init_lines(RING, 0.5), seed, inp,
        "n9A", "fsFSW")
    samples = []
    for i, ap in enumerate(applies):
        step(grid, cnt, imap, ap, "fsFSW")
        if (i + 1) % 50 == 0:
            f_, s_ = night7.comp(cnt)
            samples.append((cnt["f"] + cnt["s"],
                            s_ / (f_ + s_) if f_ + s_ else None))
    check_exact(grid, expect, f"A{seed}")
    pairs = [(samples[i][0], samples[i + 1][1] - samples[i][1])
             for i in range(len(samples) - 1)
             if samples[i][1] is not None and samples[i + 1][1] is not None]
    n = len(samples)
    quarters = [samples[min(n - 1, (k * n) // 4)][1] for k in (1, 2, 3, 4)]
    return {"seed": seed, "pairs": pairs, "quarters": quarters}


# --- B: shelter scaling with stroke cost ----------------------------

def rules_s3():
    R = gen_family.Rule
    return [R("F", "f", "reqwrite", "fF"), R("F", "f", "reqwrite", "sW"),
            R("S", "s", "reqwrite", "fF"), R("S", "s", "reqwrite", "sW"),
            R("W", "V", "self", None), R("V", "S", "self", None),
            R("F", "F", "reqwrite", "~f"), R("S", "S", "reqwrite", "~s")]


def eval_B(task):
    arm, m, seed = task
    rules = night7.rules7() if arm == "s2" else rules_s3()
    glyphs = "fsFSW" if arm == "s2" else "fsFSWV"
    extra = gen_family.poke_rules("fs")
    s0, applies, grid, cnt, imap, expect = run_one(
        rules, extra, night7.init_lines(RING, 0.5), seed,
        night7.protocol(m), f"n9B_{arm}_m{m}", glyphs)
    res_s = res_f = 0
    samples = []
    for i, ap in enumerate(applies):
        step(grid, cnt, imap, ap, glyphs)
        res_s += cnt["S"] + cnt["W"] + cnt["V"]
        res_f += cnt["F"]
        if (i + 1) % 50 == 0:
            f_ = cnt["f"] + cnt["F"]
            s_ = cnt["s"] + cnt["S"] + cnt["W"] + cnt["V"]
            samples.append((cnt["f"] + cnt["s"],
                            s_ / (f_ + s_) if f_ + s_ else None))
    check_exact(grid, expect, f"B{arm}{m}s{seed}")
    lastq = [s for s in samples[3 * len(samples) // 4:]
             if s[1] is not None]
    return {"arm": arm, "m": m, "seed": seed,
            "residence_s": res_s / (res_s + res_f),
            "s_lastq": (statistics.mean(x[1] for x in lastq)
                        if lastq else None),
            "tape_lastq": (statistics.mean(x[0] for x in lastq)
                           if lastq else 0)}


# --- D: contested repair --------------------------------------------

def rules_claim(arm, wd):
    R = gen_family.Rule
    rules = [R("B", "B", "reqwrite", "~B"),
             R("D", "D", "reqwrite", "~D", w=wd)]
    if arm == "contested":
        rules += [R("B", "B", "westclaim", "B"),
                  R("D", "D", "westclaim", "D", w=wd)]
    return rules


def eval_D(task):
    arm, wd, seed = task
    rules = rules_claim(arm, wd)
    extra = gen_family.poke_rules("BD")
    init = "\n".join(["^Bc*"] + ["^Dc?"] * 12)
    inp = "T" * 32 + ("p" + "T" * 4) * (24000 // 5)
    s0, applies, grid, cnt, imap, expect = run_one(
        rules, extra, init, seed, inp, f"n9D_{arm}_w{wd:g}", "BD")
    b0, d0 = cnt["B"], cnt["D"]
    samples = []
    for i, ap in enumerate(applies):
        step(grid, cnt, imap, ap, "BD")
        if (i + 1) % 50 == 0:
            t = cnt["B"] + cnt["D"]
            samples.append(cnt["B"] / t if t else None)
    check_exact(grid, expect, f"D{arm}{wd}s{seed}")
    lastq = [s for s in samples[3 * len(samples) // 4:] if s is not None]
    return {"arm": arm, "wd": wd, "seed": seed,
            "b_init": b0 / (b0 + d0),
            "b_lastq": statistics.mean(lastq) if lastq else None,
            "d_extinct": cnt["D"] == 0, "b_extinct": cnt["B"] == 0}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", type=int, default=8)
    ap.add_argument("--workdir", default=None)
    args = ap.parse_args()
    workdir = Path(args.workdir) if args.workdir else \
        Path(tempfile.mkdtemp(prefix="night9_"))
    workdir.mkdir(parents=True, exist_ok=True)
    here = Path(__file__).parent
    print(f"binary {BIN}\nworkdir {workdir}")
    night8.SEEDS = tuple(range(1, 25))
    t0 = time.perf_counter()

    with Pool(args.jobs, _pool_init, (str(workdir),)) as pool:
        A = pool.map(eval_A, range(1, 17))
        B = pool.map(eval_B, [(a, m, s) for a in ("s2", "s3")
                              for m in (8, 2) for s in range(1, 17)])
        C = pool.map(night8.eval_point,
                     [(a, m) for a in ("base", "pair")
                      for m in (2, 3, 4, 5, 6, 8)], chunksize=1)
        D = pool.map(eval_D, [(a, w, s)
                              for a in ("uncontested", "contested")
                              for w in (1, 0.5, 0.25)
                              for s in range(1, 25)])
    print(f"all sections done, wall {time.perf_counter() - t0:.1f}s, "
          f"exactness: all pass\n")

    # --- A summary
    pairs = [p for r in A for p in r["pairs"]]
    print("A. drift vs tape level (m=8, 16 seeds, 96k events):")
    for lo, hi in ((0, 14), (15, 17), (18, 20), (21, 24)):
        ds = [d for t, d in pairs if lo <= t <= hi]
        if len(ds) < 10:
            print(f"   tape {lo}-{hi}: n={len(ds)} (skipped)")
            continue
        m_ = statistics.mean(ds)
        sem = statistics.stdev(ds) / len(ds) ** 0.5
        print(f"   tape {lo:>2}-{hi:<2} E[ds]x1000 = {1000 * m_:+.2f} "
              f"(t={m_ / sem:.1f}, n={len(ds)})")
    q = [statistics.mean(r["quarters"][k] for r in A) for k in range(4)]
    print(f"   s-share by quarter: {' -> '.join(f'{x:.2f}' for x in q)}")
    with open(here / "night9_drift.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["seed", "q1", "q2", "q3", "q4"])
        for r in A:
            w.writerow([r["seed"]] + [f"{x:.3f}" for x in r["quarters"]])

    # --- B summary
    print("\nB. shelter scaling (residence theory test):")
    with open(here / "night9_dwell.csv", "w", newline="") as f:
        w = csv.DictWriter(f, ["arm", "m", "seed", "residence_s",
                               "s_lastq", "tape_lastq"])
        w.writeheader()
        for r in B:
            w.writerow({k: (f"{v:.3f}" if isinstance(v, float) else v)
                        for k, v in r.items()})
    for m in (8, 2):
        for arm in ("s2", "s3"):
            sub = [r for r in B if r["arm"] == arm and r["m"] == m]
            res = statistics.mean(r["residence_s"] for r in sub)
            ss = [r["s_lastq"] for r in sub if r["s_lastq"] is not None]
            print(f"   m={m} {arm}: residence(s) {res:.2f}, "
                  f"s-share lastq {statistics.mean(ss):.2f}, tape "
                  f"{statistics.mean(r['tape_lastq'] for r in sub):.1f}")

    # --- C summary
    rows = [r for res in C for r in res["rows"]]
    with open(here / "night9_boundary.csv", "w", newline="") as f:
        w = csv.DictWriter(f, ["arm", "m", "seed", "tape_lastq",
                               "runmean_lastq"], extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: (f"{v:.3f}" if isinstance(v, float) else v)
                        for k, v in r.items() if k in
                        ("arm", "m", "seed", "tape_lastq",
                         "runmean_lastq")})
    print("\nC. codon collapse boundary (mean tape | collapsed<=6 frac):")
    hdr = "   m:     " + "".join(f"{m:>12}" for m in (2, 3, 4, 5, 6, 8))
    print(hdr)
    for arm in ("base", "pair"):
        line = f"   {arm:<6}"
        for m in (2, 3, 4, 5, 6, 8):
            sub = [r for r in rows if r["arm"] == arm
                   and r["m"] == m]
            tp = statistics.mean(r["tape_lastq"] for r in sub)
            cf = sum(1 for r in sub if r["tape_lastq"] <= 6) / len(sub)
            line += f"  {tp:4.1f}/{cf:.2f} "
        print(line)

    # --- D summary
    with open(here / "night9_contested.csv", "w", newline="") as f:
        w = csv.DictWriter(f, ["arm", "wd", "seed", "b_init", "b_lastq",
                               "d_extinct", "b_extinct"])
        w.writeheader()
        for r in D:
            w.writerow({k: (f"{v:.3f}" if isinstance(v, float) else v)
                        for k, v in r.items()})
    print("\nD. contested repair (night-4 missing cell). B-share "
          "init->lastq | D extinctions /24:")
    for arm in ("uncontested", "contested"):
        for wd in (1, 0.5, 0.25):
            sub = [r for r in D if r["arm"] == arm and r["wd"] == wd]
            bi = statistics.mean(r["b_init"] for r in sub)
            bl = [r["b_lastq"] for r in sub if r["b_lastq"] is not None]
            de = sum(r["d_extinct"] for r in sub)
            print(f"   {arm:<12} wd={wd:<4}: {bi:.2f} -> "
                  f"{statistics.mean(bl):.2f} | D-extinct {de}/24")


if __name__ == "__main__":
    main()
