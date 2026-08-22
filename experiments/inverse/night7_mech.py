#!/usr/bin/env python3
"""Night-7 mechanism discriminators (companion to night7.py).

For m in {8, 2} on ring 24, s0=0.5, 8 seeds, measures:
  A. per-capita REPLICATION ratio s/f (repairs vs instantaneous share)
  B. per-capita DEATH ratio s/f (pokes vs share of pokeable tape)
  C. head residence P(cover=s) by tape-level quartile, and wipe
     episodes (tape<=2) with pre/post composition.
Findings (2026-08-22): A ~= 1.00 and B ~= 1.00 at both damage rates —
per-event flows are composition-neutral; composition dynamics act
through state structure: at m=2 the system sits in the lowest tape
quartile ~90% of the time with P(cover=s)=0.82 (machinery shelter),
while regrowth phases run at P(cover=s)=0.02 (f rebuilds).

Usage: python3 night7_mech.py
"""
import subprocess
import statistics
from collections import Counter
from pathlib import Path
import tempfile

import gen_family as gf
import analyzers
import night7

BIN = night7.BIN
SEEDS = range(1, 9)


def run(m, seed, workdir):
    rules = night7.rules7()
    extra = gf.poke_rules("fs")
    cfg = workdir / "mech.cfg"
    cfg.write_text(gf.compile_cfg(rules, "mech", extra,
                                  night7.init_lines(24, 0.5)))
    d0, t0 = workdir / "i.txt", workdir / "i.trace"
    d1, t1 = workdir / "r.txt", workdir / "r.trace"
    for inp, dump, tr in (("z", d0, t0), (night7.protocol(m), d1, t1)):
        subprocess.run([str(BIN), "--headless", "--screen", "6,24",
                        "--seed", str(seed), "--input", inp,
                        "--dump-screen", str(dump), "--trace", str(tr),
                        str(cfg)], capture_output=True, text=True)
    s0 = analyzers.parse_dump(d0, 6, 24)
    return gf.idx_map(rules, extra), s0, analyzers.parse_trace(t1)


def main():
    workdir = Path(tempfile.mkdtemp(prefix="n7mech_"))
    for m in (8, 2):
        rep = Counter()
        rep_share = []
        die = Counter()
        die_share = []
        buckets = {q: Counter() for q in range(4)}
        wipes = []
        for seed in SEEDS:
            imap, s0, applies = run(m, seed, workdir)
            grid = [list(r) for r in s0]
            cnt = Counter(c for row in s0 for c in row if c in "fsFSW")
            in_wipe = False
            for lhs, idx, ro, co, trig in applies:
                rule = imap[(lhs, idx)]
                f_, s_ = night7.comp(cnt)
                tape = cnt["f"] + cnt["s"]
                q = min(3, tape * 4 // 23)
                buckets[q]["s"] += cnt["S"] + cnt["W"]
                buckets[q]["f"] += cnt["F"]
                if trig == "p":
                    die[rule.lhs] += 1
                    if tape:
                        die_share.append(cnt["s"] / tape)
                elif rule.kind == "reqwrite" and rule.arg[0] == "~":
                    rep[rule.arg[1]] += 1
                    if f_ + s_:
                        rep_share.append(s_ / (f_ + s_))
                if tape <= 2 and not in_wipe:
                    in_wipe = True
                    wipes.append([s_ / (f_ + s_) if f_ + s_ else None,
                                  None])
                if tape >= 12 and in_wipe:
                    in_wipe = False
                    wipes[-1][1] = s_ / (f_ + s_)
                for dc, ch in gf.writes(rule):
                    r, c = ro - 1, (co + dc) % 24
                    old = grid[r][c]
                    if old in "fsFSW":
                        cnt[old] -= 1
                    if ch in "fsFSW":
                        cnt[ch] += 1
                    grid[r][c] = ch
        ws_r = statistics.mean(rep_share)
        ws_d = statistics.mean(die_share)
        print(f"m={m}:")
        print(f"  A birth: rep f {rep['f']} s {rep['s']}, per-capita s/f "
              f"{(rep['s'] / ws_r) / (rep['f'] / (1 - ws_r)):.3f}")
        print(f"  B death: die f {die['f']} s {die['s']}, per-capita s/f "
              f"{(die['s'] / ws_d) / (die['f'] / (1 - ws_d)):.3f}")
        for q in range(4):
            b = buckets[q]
            tot = b["s"] + b["f"]
            if tot:
                print(f"  C residence q{q}: P(cover=s) {b['s'] / tot:.3f} "
                      f"(n={tot})")
        done = [w for w in wipes if w[1] is not None]
        if done:
            print(f"  wipes completed {len(done)}: s-share "
                  f"{statistics.mean(w[0] for w in done):.2f} -> "
                  f"{statistics.mean(w[1] for w in done):.2f}")


if __name__ == "__main__":
    main()
