#!/usr/bin/env python3
"""EW-1 — necessity + conditional equivalence (F4, earned family).

Pre-registrations (ew-design.md):
  P1-1 necessity — arm f4none (no copiers): the regulatory row never
    gains an allele beyond the initially stamped region; matter
    halts one cell past it; night-2 repair verdicts collapse.
  P1-2 conditional equivalence — arm f4sat (machinery seeded at
    density 1/2, copy/walk free and faithful) reproduces arm f3's
    (authored stamps) outcome distribution per allele ON THE
    MATTER-EVENT SUBSEQUENCE; the copier time tax is reported as
    the event-inflation factor, not hidden.
  P1-3 exactness — trace-replay == dump on every run, all arms.

World: 4 playfield rows (tape/fuel/machinery/regulatory), ring 6,
uniform allele per world, night-2 drive b + T*H + 3x(p + T*H).
Verdicts run on tape-row states sampled at matter events only
(copier walks would smear periodicity); pokes are matter events.

Usage: python3 ew1.py [--jobs N] [--seeds N] [--workdir DIR]
Outputs: ew1_runs.csv, summary on stdout.
"""
import argparse
import csv
import math
import sys
import subprocess
import tempfile
import time
from collections import Counter
from pathlib import Path
from multiprocessing import Pool

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "inverse"))
import gen_family
import analyzers
import gen_gated
import gen_earned

R = gen_family.Rule
ROOT = Path(__file__).resolve().parents[2]
BIN = ROOT / "zahradnice"

ROWS, RING = 5, 6                    # tape=1 fuel=2 mach=3 reg=4
H, ROUNDS = 400, 3
COPIER = "Π"
MATTER = "AB"

ALLELES = {
    "α": [R("A", "A", "write", "A")],
    "β": [R("A", "B", "write", "A"), R("B", "A", "req", "~")],
    "γ": [R("A", "B", "write", "A")],
    "δ": [R("A", "A", "self", None)],
}
POKE = gen_family.poke_rules()

_WORK = None
_CTX = None


def protocol(cad):
    unit = ("T" + "C" * cad) * H
    return "b" + unit + ("p" + unit) * ROUNDS


def build_f3(g):
    """Authored-channel control: F3 inheritance emission, uniform."""
    lines = ["#!ew1f3 {steps}", "#threads 1", "^Auc", f"^{g}l*"]
    emis = []
    for r in ALLELES[g]:
        lines += [gen_gated.inherit_head(r, g),
                  gen_gated.inherit_body(r, stamps=True)]
        emis.append((r.lhs, gen_gated.inherit_writes(r, g, stamps=True)))
    for r in POKE:
        lines += [gen_family.head(r), gen_family.body(r)]
        emis.append((r.lhs, [(0, dc, ch)
                             for dc, ch in gen_family.writes(r)]))
    imap, per = {}, {}
    for lhs, w in emis:
        i = per.get(lhs, 0)
        imap[(lhs, i)] = w
        per[lhs] = i + 1
    return "\n".join(lines) + "\n", imap


def build_f4(g, machinery):
    """Earned arm: unstamped matter; machinery iff requested."""
    groups = []
    for r in ALLELES[g]:
        groups += gen_earned.unstamped_groups(r, g)
    if machinery:
        groups.append(gen_earned.copier_copy(COPIER, [g], trig="C"))
        groups.append(gen_earned.copier_walk(COPIER, [g], trig="C"))
        groups.append(gen_earned.bootstrap(g, COPIER, RING, density=2))
    name = "ew1sat" if machinery else "ew1none"
    return gen_earned.assemble(f"{name} {{steps}}",
                               ["^Auc", f"^{g}l*"], groups, POKE)


def run_engine(cfg, seed, inp, trace, dump):
    cmd = [str(BIN), "--headless", "--screen", f"{ROWS},{RING}",
           "--seed", str(seed), "--input", inp,
           "--trace", str(trace), "--dump-screen", str(dump), str(cfg)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"engine failed on {cfg}: {r.stderr.strip()}")


def probe_init(workdir, tag, init_block):
    cfg = workdir / f"probe_{tag}.cfg"
    cfg.write_text(f"#!probe\n#threads 1\n{init_block}\n==zzz\n@@@\n")
    dump = workdir / f"probe_{tag}.txt"
    run_engine(cfg, 1, "q", workdir / "probe.trace", dump)
    return tuple(analyzers.parse_dump(dump, ROWS, RING))


def eval_run(task):
    g, arm, cad, seed = task
    cfg_path, imap, s0 = _CTX[(g, arm)]
    tag = f"{arm}_{cad}_{ord(g)}_s{seed}"
    trace, dump = _WORK / f"{tag}.trace", _WORK / f"{tag}.txt"
    run_engine(Path(cfg_path), seed, protocol(cad), trace, dump)
    applies = analyzers.parse_trace(trace)
    grid = [list(row) for row in s0]
    m_states = ["".join(grid[0])]
    m_applies = []
    for a in applies:
        lhs, idx, ro, co, _t = a
        for dr, dc, ch in imap[(lhs, idx)]:
            grid[(ro - 1 + dr) % (ROWS - 1)][(co + dc) % RING] = ch
        if lhs in MATTER:
            m_states.append("".join(grid[0]))
            m_applies.append(a)
    final = ["".join(r) for r in grid]
    exact = final == list(analyzers.parse_dump(dump, ROWS, RING))
    v = analyzers.repair_verdict(m_states, m_applies, H, H, ROUNDS)
    trace.unlink()
    dump.unlink()
    tape, reg = final[0], final[3]
    alive = sum(tape.count(c) for c in MATTER)
    active = sum(1 for c in range(RING)
                 if tape[c] in MATTER and reg[c] not in (" ",
                                                        gen_earned.PLACE))
    return {"glyph": g, "arm": arm, "cad": cad, "seed": seed,
            "exact": exact,
            "outcome": v["outcome"], "alive": alive, "active": active,
            "qmarks": reg.count(gen_earned.PLACE),
            "copiers": final[2].count(COPIER),
            "matter_events": len(m_applies), "total_events": len(applies)}


def _pool_init(workdir_str, ctx):
    global _WORK, _CTX
    _WORK = Path(workdir_str)
    _CTX = ctx


def two_prop_z(k1, n1, k2, n2):
    p = (k1 + k2) / (n1 + n2)
    se = math.sqrt(p * (1 - p) * (1 / n1 + 1 / n2))
    return 0.0 if se == 0 else (k1 / n1 - k2 / n2) / se


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", type=int, default=8)
    ap.add_argument("--seeds", type=int, default=200)
    ap.add_argument("--workdir", default=None)
    args = ap.parse_args()
    workdir = Path(args.workdir) if args.workdir else \
        Path(tempfile.mkdtemp(prefix="ew1_"))
    workdir.mkdir(parents=True, exist_ok=True)
    print(f"binary {BIN}\nworkdir {workdir}")

    ctx = {}
    for g in ALLELES:
        s0 = probe_init(workdir, f"i{ord(g)}", f"^Auc\n^{g}l*")
        for arm, built in (("f3", build_f3(g)),
                           ("f4sat", build_f4(g, True)),
                           ("f4none", build_f4(g, False))):
            text, imap = built
            p = workdir / f"{arm}_{ord(g)}.cfg"
            p.write_text(text)
            ctx[(g, arm)] = (str(p), imap, s0)

    tasks = [(g, arm, cad, s) for g in ALLELES
             for arm, cad in (("f3", 1), ("f4none", 1), ("f4sat", 1),
                              ("f4sat", 2), ("f4sat", 4), ("f4sat", 8),
                              ("f4sat", 16), ("f4sat", 32))
             for s in range(1, args.seeds + 1)]
    t0 = time.perf_counter()
    if args.jobs > 1:
        with Pool(args.jobs, _pool_init, (str(workdir), ctx)) as pool:
            rows = pool.map(eval_run, tasks, chunksize=8)
    else:
        _pool_init(str(workdir), ctx)
        rows = [eval_run(t) for t in tasks]
    wall = time.perf_counter() - t0
    inexact = [(r["glyph"], r["arm"], r["seed"]) for r in rows
               if not r["exact"]]
    print(f"{len(rows)} runs, wall {wall:.1f}s, "
          f"exactness failures: {len(inexact)}")
    if inexact:
        print(inexact[:10])
        sys.exit("trace<->screen accounting broken; aborting")

    here = Path(__file__).parent
    with open(here / "ew1_runs.csv", "w", newline="") as f:
        w = csv.writer(f)
        cols = ["glyph", "arm", "cad", "seed", "outcome", "alive",
                "active", "qmarks", "copiers", "matter_events",
                "total_events", "exact"]
        w.writerow(cols)
        for r in sorted(rows, key=lambda r: (r["glyph"], r["arm"],
                                             r["cad"], r["seed"])):
            w.writerow([r[c] for c in cols])

    n = args.seeds
    for g in sorted(ALLELES):
        by = {k: [r for r in rows if r["glyph"] == g
                  and (r["arm"], r["cad"]) == k]
              for k in (("f3", 1), ("f4none", 1), ("f4sat", 1),
                        ("f4sat", 2), ("f4sat", 4), ("f4sat", 8),
                        ("f4sat", 16), ("f4sat", 32))}
        oc = {k: Counter(r["outcome"] for r in by[k]) for k in by}
        modal = oc[("f3", 1)].most_common(1)[0][0]
        act = {k: sum(r["active"] for r in by[k]) / n for k in by}
        print(f"{g}: f3      {dict(oc[('f3', 1)])}  "
              f"active {act[('f3', 1)]:.2f}")
        for cad in (1, 2, 4, 8, 16, 32):
            k = ("f4sat", cad)
            z = two_prop_z(oc[("f3", 1)][modal], n, oc[k][modal], n)
            print(f"   f4sat c{cad} {dict(oc[k])}  modal '{modal}' "
                  f"z={z:+.2f} {'OK' if abs(z) <= 3 else 'DIVERGES'}  "
                  f"active {act[k]:.2f}")
        k = ("f4none", 1)
        print(f"   f4none  {dict(oc[k])}  active {act[k]:.2f}")


if __name__ == "__main__":
    main()
