#!/usr/bin/env python3
"""Per-rung population trajectory from a forest-ladder.cfg trace.

Usage: ladder_stats.py CFG TRACE [--sample N] > series.csv

Re-parses CFG to classify every rule header by its (1-based) line
number, then replays TRACE apply events into exact per-rung population
counts (the trace's src_line field disambiguates rules whose head text
alone would not — e.g. the four transmission directions per victim).

Event effects: seed/growth +1 offspring rung; lightning -1 rung,
fire +1; transmission -1 victim rung, fire +1; mortality -1 rung;
burnout fire -1.

Output: CSV step,pop1..pop5,fire,share1..share5,meanrung sampled every
N events (default 500) plus a final row; a summary line on stderr.
"""
import sys

RUNGS = "12345"
SEEDG = {chr(0x2800 + 2 ** int(k) - 1): k for k in RUNGS}  # braille -> rung


def classify(cfg_path):
    """(line-number -> (kind, rung) for every rule header, init pops)."""
    lines = open(cfg_path).read().splitlines()
    out = {}
    init = dict.fromkeys(RUNGS, 0)
    for l in lines:
        if l.startswith("^") and len(l) > 1 and l[1] in RUNGS:
            init[l[1]] += 1
    # group consecutive header lines; body = following non-header,
    # non-directive, non-blank lines
    i = 0
    while i < len(lines):
        if not lines[i].startswith("="):
            i += 1
            continue
        heads = []
        while i < len(lines) and lines[i].startswith("="):
            heads.append((i + 1, lines[i]))
            i += 1
        body = []
        while i < len(lines) and lines[i] and lines[i][0] not in "=#^":
            body.append(lines[i])
            i += 1
        bodytext = "".join(body)
        for lineno, h in heads:
            lhs, trig, rhs = h[2], h[3], h[4] if len(h) > 4 else " "
            if lhs == "." and trig == "T" and rhs in RUNGS:
                kind = "seed" if bodytext.strip() == "@@@" else "grow"
                out[lineno] = (kind, rhs)
            elif lhs in RUNGS and trig == "l":
                out[lineno] = ("ignite", lhs)
            elif lhs == "A" and rhs == "A":
                victim = next(c for c in bodytext if c in RUNGS)
                out[lineno] = ("burn", victim)
            elif lhs in RUNGS and trig == "T" and rhs == ".":
                out[lineno] = ("mort", lhs)
            elif lhs == "." and trig == "T" and rhs in SEEDG:
                out[lineno] = ("deposit", SEEDG[rhs])
            elif lhs in SEEDG and rhs == lhs:
                out[lineno] = ("sprout", SEEDG[lhs])
            elif lhs in SEEDG and rhs in RUNGS:
                out[lineno] = ("germ", SEEDG[lhs])
            elif lhs in SEEDG and rhs == ".":
                out[lineno] = ("decay", SEEDG[lhs])
            elif lhs == "A" and rhs == ".":
                out[lineno] = ("out", None)
            else:
                out[lineno] = ("other", None)
    return out, init


def main():
    cfg, trace = sys.argv[1], sys.argv[2]
    sample = 500
    if "--sample" in sys.argv:
        sample = int(sys.argv[sys.argv.index("--sample") + 1])
    rules, pop = classify(cfg)
    bank = dict.fromkeys(RUNGS, 0)
    fire = 0
    events = dict.fromkeys(("seed", "grow", "ignite", "burn", "mort",
                            "out", "deposit", "sprout", "germ", "decay",
                            "other"), 0)
    step = 0

    def row():
        tot = sum(pop.values())
        shares = [pop[k] / tot if tot else 0.0 for k in RUNGS]
        mean = (sum(int(k) * pop[k] for k in RUNGS) / tot) if tot else 0.0
        btot = sum(bank.values())
        bmean = (sum(int(k) * bank[k] for k in RUNGS) / btot) if btot else 0.0
        print(f"{step}," + ",".join(str(pop[k]) for k in RUNGS)
              + f",{fire}," + ",".join(f"{s:.4f}" for s in shares)
              + f",{mean:.4f},"
              + ",".join(str(bank[k]) for k in RUNGS)
              + f",{btot},{bmean:.4f}")

    print("step," + ",".join(f"pop{k}" for k in RUNGS) + ",fire,"
          + ",".join(f"share{k}" for k in RUNGS) + ",meanrung,"
          + ",".join(f"bank{k}" for k in RUNGS) + ",banktot,bankmean")
    for line in open(trace):
        f = line.rstrip("\n").split("\t")
        if f[0] != "apply":
            continue
        step = int(f[1])
        kind, rung = rules.get(int(f[9]), ("missing", None))
        events[kind if kind in events else "other"] += 1
        if kind in ("seed", "grow"):
            pop[rung] += 1
        elif kind in ("ignite", "burn"):
            pop[rung] -= 1
            fire += 1
        elif kind == "mort":
            pop[rung] -= 1
        elif kind == "sprout":
            pop[rung] += 1
        elif kind == "deposit":
            bank[rung] += 1
        elif kind == "germ":
            bank[rung] -= 1
            pop[rung] += 1
        elif kind == "decay":
            bank[rung] -= 1
        elif kind == "out":
            fire -= 1
        elif kind == "missing":
            sys.exit(f"trace rule at cfg line {f[9]} not classified")
        if step % sample == 0:
            row()
    row()
    tot = sum(pop.values())
    mean = (sum(int(k) * pop[k] for k in RUNGS) / tot) if tot else 0.0
    print(f"final step={step} pops="
          + "/".join(str(pop[k]) for k in RUNGS)
          + f" fire={fire} bank=" + "/".join(str(bank[k]) for k in RUNGS)
          + f" meanrung={mean:.3f} events={events}",
          file=sys.stderr)


if __name__ == "__main__":
    main()
