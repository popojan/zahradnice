#!/usr/bin/env python3
"""Per-species population + learning trajectory from a garden trace.

Usage: garden_stats.py CFG TRACE [--sample N] > series.csv

Kinds per src_line: birth(s) [score 1, lhs=rhs=s; deposits its body's
token], waste(s) [score 0, lhs=rhs=s, no '.' write], confisc(s)
[score 0, token in body ending '.'], rent-death(s) [lhs=s rhs='.'],
seed(s) [lhs='.'], decay(token). Correct-share per species per window
= births/(births+wastes) — the realized policy quality.

CSV: step,season,popn,popi,popp,tokix,tokiy,tokpx,tokpy,
bn,wn,bi,wi,bp,wp,score  (b*/w* per window). Exactness on stderr.
"""
import sys

SPECIES = "nip"
TOK = {"⠃": ("i", "x"), "⠘": ("i", "y"), "⠇": ("p", "x"), "⠸": ("p", "y")}


def assemble(path):
    return open(path, encoding="utf-8").read().splitlines()


def classify(cfg_path):
    lines = assemble(cfg_path)
    out = {}
    i = 0
    while i < len(lines):
        if not lines[i].startswith("="):
            i += 1
            continue
        lineno, h = i + 1, lines[i]
        i += 1
        body = []
        while i < len(lines) and lines[i] and lines[i][0] not in "=#^":
            body.append(lines[i])
            i += 1
        lhs, rhs = h[2], h[4] if len(h) > 4 else " "
        parts = h.split()
        score = int(parts[-2]) if len(parts) >= 3 else 0
        # geometric body parse: cells + the three @ anchors
        cells = [(r, c, ch) for r, l in enumerate(body)
                 for c, ch in enumerate(l) if ch != " "]
        ats = [(r, c) for r, c, ch in cells if ch == "@"]
        rhs_toks, lhs_tok_off, rhs_dot_off = [], set(), set()
        if len(ats) == 3:
            (r1, c1), (rb, cb), (r3, c3) = ats
            for r, c, ch in cells:
                if ch == "@":
                    continue
                if c > cb:
                    if ch in TOK:
                        rhs_toks.append(ch)
                    if ch == ".":
                        rhs_dot_off.add((r - r3, c - c3))
                elif c < cb and ch in TOK:
                    lhs_tok_off.add((ch, (r - r1, c - c1)))
        rhs_species = [ch for _, c, ch in
                       ((r, c, ch) for r, c, ch in cells)
                       if ch in SPECIES and len(ats) == 3 and c > ats[1][1]]
        if lhs == "." and rhs in SPECIES:
            out[lineno] = ("seed", rhs, None)
        elif lhs in SPECIES and rhs == lhs:
            if score == 1:
                born = rhs_species[0] if rhs_species else lhs
                out[lineno] = ("birth", lhs,
                               (rhs_toks[0] if rhs_toks else None, born))
            else:
                eaten = next((t for t, off in lhs_tok_off
                              if off in rhs_dot_off), None)
                if eaten:
                    out[lineno] = ("confisc", lhs, eaten)
                else:
                    out[lineno] = ("waste", lhs, None)
        elif lhs in SPECIES and rhs == ".":
            attempt = any(ch != "@" for _, _, ch in cells)
            out[lineno] = ("toxdeath" if attempt else "death", lhs, None)
        elif lhs in TOK and rhs == ".":
            out[lineno] = ("decay", lhs, None)
        else:
            out[lineno] = ("other", None, None)
    return out


def main():
    cfg, trace = sys.argv[1], sys.argv[2]
    sample = 1000
    if "--sample" in sys.argv:
        sample = int(sys.argv[sys.argv.index("--sample") + 1])
    rules = classify(cfg)
    pop = dict.fromkeys(SPECIES, 0)
    for l in assemble(cfg):
        if l.startswith("^") and len(l) > 1 and l[1] in SPECIES:
            pop[l[1]] += 1
    tok = dict.fromkeys(TOK, 0)
    win = {k: 0 for s in SPECIES for k in (f"b{s}", f"w{s}")}
    step = score = 0
    season = ""
    print("step,season,popn,popi,popp,tokix,tokiy,tokpx,tokpy,"
          "bn,wn,bi,wi,bp,wp,score")
    for line in open(trace, encoding="utf-8"):
        f = line.rstrip("\n").split("\t")
        if f[0] != "apply":
            continue
        step, score, season = int(f[1]), int(f[2]), f[4]
        kind, who, aux = rules.get(int(f[9]), ("missing", None, None))
        if kind == "birth":
            dep, born = aux
            pop[born] += 1
            win[f"b{who}"] += 1
            if dep:
                tok[dep] += 1
        elif kind == "waste":
            win[f"w{who}"] += 1
        elif kind == "confisc":
            win[f"w{who}"] += 1
            tok[aux] -= 1
        elif kind == "death":
            pop[who] -= 1
        elif kind == "toxdeath":
            pop[who] -= 1
            win[f"w{who}"] += 1
        elif kind == "seed":
            pop[who] += 1
        elif kind == "decay":
            tok[who] -= 1
        elif kind == "missing":
            sys.exit(f"unclassified rule at cfg line {f[9]}")
        if step % sample == 0:
            print(f"{step},{season},{pop['n']},{pop['i']},{pop['p']},"
                  f"{tok['⠃']},{tok['⠘']},{tok['⠇']},{tok['⠸']},"
                  + ",".join(str(win[f'{k}{s}']) for s in SPECIES
                             for k in "bw") + f",{score}")
            win = {k: 0 for k in win}
    print(f"final step={step} pop={pop} tok={tok} score={score}",
          file=sys.stderr)


if __name__ == "__main__":
    main()
