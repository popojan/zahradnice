#!/usr/bin/env python3
"""Windowed policy trajectory from a bandit.cfg trace.

Usage: bandit_stats.py CFG TRACE [--sample N] > series.csv

Classifies rules by src_line from the cfg (score tail decides paying;
a paying body whose core row ends with the arm token deposits).
Replays the trace into exact flower/token populations and per-window
arm counts. CSV: step,season,bloomx,bloomy,paidx,paidy,policy,
flx,fly,tokx,toky,score. Exactness summary on stderr.
"""
import sys

ARMS = "xy"
TOK = {"⠋": "x", "⠙": "y"}
ARMTOK = {v: k for k, v in TOK.items()}


def assemble(path, seen=None):
    """Replicate the engine's #include splicing (textual, recursive,
    include line consumed, paths relative to the including file)."""
    import os
    seen = seen or set()
    if path in seen:
        return []
    seen.add(path)
    out = []
    for line in open(path, encoding="utf-8").read().splitlines():
        if line.startswith("#include") and " " in line:
            inc = os.path.join(os.path.dirname(path) or ".",
                               line.split(" ", 1)[1])
            out.extend(assemble(inc, seen))
        else:
            out.append(line)
    return out


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
        lhs, trig, rhs = h[2], h[3], h[4] if len(h) > 4 else " "
        parts = h.split()
        score = int(parts[-2]) if len(parts) >= 3 else 0
        if lhs == "." and rhs in ARMS:
            if score == 0 and any(
                    l.endswith(".") and ARMTOK[rhs] in l for l in body):
                out[lineno] = ("punish", rhs, False, False)
                continue
            dep = score == 1 and any(
                l.endswith(ARMTOK[rhs]) and "@" in l for l in body)
            out[lineno] = ("bloom", rhs, score == 1, dep)
        elif lhs in ARMS and rhs == ".":
            out[lineno] = ("wilt", lhs, False, False)
        elif lhs in TOK and rhs == ".":
            out[lineno] = ("decay", TOK[lhs], False, False)
        else:
            out[lineno] = ("other", None, False, False)
    return out


def main():
    cfg, trace = sys.argv[1], sys.argv[2]
    sample = 1000
    if "--sample" in sys.argv:
        sample = int(sys.argv[sys.argv.index("--sample") + 1])
    rules = classify(cfg)
    fl = dict.fromkeys(ARMS, 0)
    tok = dict.fromkeys(ARMS, 0)
    win = {"bx": 0, "by": 0, "px": 0, "py": 0, "season": ""}
    step = score = 0
    print("step,season,bloomx,bloomy,paidx,paidy,policy,"
          "flx,fly,tokx,toky,score")
    for line in open(trace, encoding="utf-8"):
        f = line.rstrip("\n").split("\t")
        if f[0] != "apply":
            continue
        step, score = int(f[1]), int(f[2])
        win["season"] = f[4]
        kind, arm, paying, dep = rules.get(int(f[9]),
                                           ("missing", None, 0, 0))
        if kind == "bloom":
            fl[arm] += 1
            win["b" + arm] += 1
            if paying:
                win["p" + arm] += 1
            if dep:
                tok[arm] += 1
        elif kind == "punish":
            fl[arm] += 1
            win["b" + arm] += 1
            tok[arm] -= 1
        elif kind == "wilt":
            fl[arm] -= 1
        elif kind == "decay":
            tok[arm] -= 1
        elif kind == "missing":
            sys.exit(f"unclassified rule at cfg line {f[9]}")
        if step % sample == 0:
            tot = win["bx"] + win["by"]
            pol = win["bx"] / tot if tot else 0.5
            print(f"{step},{win['season']},{win['bx']},{win['by']},"
                  f"{win['px']},{win['py']},{pol:.4f},"
                  f"{fl['x']},{fl['y']},{tok['x']},{tok['y']},{score}")
            win.update(bx=0, by=0, px=0, py=0)
    print(f"final step={step} flowers={fl} tokens={tok} score={score}",
          file=sys.stderr)


if __name__ == "__main__":
    main()
