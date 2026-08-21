#!/usr/bin/env python3
"""Fire-episode statistics from a forest2.cfg trace (stdin or argv[1]).

A fire cell is born by lightning (==cTA) or burn-spread (==ATA) and
dies by burnout (==ATg). An episode is a maximal interval with at
least one fire cell alive; its size is the number of cells it burnt.
"""
import collections
import statistics
import sys

src = open(sys.argv[1]) if len(sys.argv) > 1 else sys.stdin
sizes, alive, cur = [], 0, 0
counts = collections.Counter()
for line in src:
    f = line.rstrip("\n").split("\t")
    if not f or f[0] != "apply":
        continue
    head = f[-1].split()[0]
    counts[head] += 1
    if head.startswith(("==cTA", "==ATA")):
        alive += 1
        cur += 1
    elif head.startswith("==ATg"):
        alive -= 1
        if alive == 0 and cur:
            sizes.append(cur)
            cur = 0
print("rule totals:", dict(counts))
sizes.sort()
n = len(sizes)
print(f"completed fire episodes: {n}  (fires alive at trace end: {alive})")
if n:
    print(f"size min/med/mean/p90/max: {sizes[0]}/"
          f"{statistics.median(sizes):.0f}/{statistics.mean(sizes):.1f}/"
          f"{sizes[int(0.9 * n)]}/{sizes[-1]}")
    h = collections.Counter(s.bit_length() - 1 for s in sizes)
    print("log2 histogram (bucket: count):")
    for b in sorted(h):
        print(f"  {2 ** b:>6}-{2 ** (b + 1) - 1:<6}: {h[b]}")
