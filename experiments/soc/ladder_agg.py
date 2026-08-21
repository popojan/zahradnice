#!/usr/bin/env python3
"""Aggregate laddersweep output.

Usage: ladder_agg.py ladder/summary.csv

Per condition: mean/min/max of final meanrung, mean shares, events.
For switch conditions (c2f, f2c): meanrung just before the switch
(last sample <= budget/2) vs final, from the series files.
"""
import csv
import statistics
import sys
from pathlib import Path

path = Path(sys.argv[1])
rows = list(csv.DictReader(open(path)))
conds = []
for r in rows:
    if r["cond"] not in conds:
        conds.append(r["cond"])

print(f"{'cond':6} {'n':>2} {'meanrung':>18} {'share1':>7} {'share5':>7}"
      f" {'pop':>6} {'events':>7} recon")
for c in conds:
    g = [r for r in rows if r["cond"] == c]
    mr = [float(r["meanrung"]) for r in g]
    pops = [[int(r[f"pop{k}"]) for k in "12345"] for r in g]
    tots = [sum(p) for p in pops]
    s1 = statistics.mean(p[0] / t if t else 0 for p, t in zip(pops, tots))
    s5 = statistics.mean(p[4] / t if t else 0 for p, t in zip(pops, tots))
    ev = statistics.mean(int(r["events"]) for r in g)
    bad = sum(r["recon"] != "ok" for r in g)
    print(f"{c:6} {len(g):>2} {statistics.mean(mr):6.2f}"
          f" [{min(mr):5.2f}..{max(mr):5.2f}]"
          f" {s1:7.3f} {s5:7.3f} {statistics.mean(tots):6.0f}"
          f" {ev:7.0f} {'ok' if not bad else f'{bad} BAD'}")

for c in ("c2f", "f2c"):
    pre, post = [], []
    for f in sorted(path.parent.glob(f"series-{c}-s*.csv")):
        srows = list(csv.DictReader(open(f)))
        half = max(int(r["step"]) for r in srows) // 2
        before = [r for r in srows if int(r["step"]) <= half]
        if not before or not srows:
            continue
        pre.append(float(before[-1]["meanrung"]))
        post.append(float(srows[-1]["meanrung"]))
    if pre:
        print(f"{c}: meanrung at switch {statistics.mean(pre):.2f} "
              f"[{min(pre):.2f}..{max(pre):.2f}] -> final "
              f"{statistics.mean(post):.2f} "
              f"[{min(post):.2f}..{max(post):.2f}]  (n={len(pre)})")
