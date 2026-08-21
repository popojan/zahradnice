#!/usr/bin/env python3
"""Avalanche statistics from a manna.cfg trace.

Size of an avalanche = number of topplings between consecutive drive
events. Pass --skip N to discard the first N drives (stationarity
warmup). Reports the log2 histogram, tail percentiles, and the final
score (grains in the pile) as the density check.
"""
import argparse
import collections
import statistics
import sys


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("trace")
    ap.add_argument("--skip", type=int, default=0)
    args = ap.parse_args()

    sizes = []
    cur = None
    drives = 0
    last_score = 0
    for line in open(args.trace):
        f = line.rstrip("\n").split("\t")
        if not f or f[0] != "apply":
            continue
        last_score = int(f[2])
        trig = f[4]
        if trig == "d":
            if cur is not None:
                sizes.append(cur)
            drives += 1
            cur = 0
        elif trig == "T" and cur is not None:
            cur += 1
    if cur is not None:
        sizes.append(cur)

    sizes = sizes[args.skip:]
    n = len(sizes)
    print(f"drives total {drives}, measured {n} (skipped {args.skip}); "
          f"final grains {last_score}")
    if not n:
        return
    nz = sorted(s for s in sizes if s > 0)
    print(f"zero-size fraction: {(n - len(nz)) / n:.2f}")
    if nz:
        print(f"nonzero sizes med/p90/p99/max: {statistics.median(nz):.0f}/"
              f"{nz[int(0.9 * len(nz))]}/{nz[int(0.99 * len(nz))]}/{nz[-1]}")
        h = collections.Counter(s.bit_length() - 1 for s in nz)
        print("log2 histogram (bucket: count):")
        for b in sorted(h):
            print(f"  {2 ** b:>7}-{2 ** (b + 1) - 1:<7}: {h[b]}")


if __name__ == "__main__":
    main()
