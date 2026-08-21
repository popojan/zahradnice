#!/usr/bin/env python3
"""Summarize a contact-process sweep CSV (stdin or argv[1]).

Per lambda: survival fraction within budget, and extinction-time
statistics over the extinct runs (median/mean/max). The qualitative
readout for Fates-style classification is how the extinction-time
distribution grows as lambda approaches the survival threshold.
"""
import csv
import statistics
import sys


def main():
    src = open(sys.argv[1]) if len(sys.argv) > 1 else sys.stdin
    rows = list(csv.DictReader(src))
    if not rows:
        sys.exit("empty input")
    by_lam = {}
    for r in rows:
        by_lam.setdefault(float(r["lambda"]), []).append(r)
    print(f"{'lambda':>7} {'n':>4} {'survive%':>9} "
          f"{'ext_med':>8} {'ext_mean':>9} {'ext_max':>8}")
    for lam in sorted(by_lam):
        runs = by_lam[lam]
        ext = [int(r["events"]) for r in runs if r["extinct"] == "1"]
        surv = 100.0 * (len(runs) - len(ext)) / len(runs)
        med = f"{statistics.median(ext):8.0f}" if ext else " " * 8
        mean = f"{statistics.mean(ext):9.1f}" if ext else " " * 9
        mx = f"{max(ext):8d}" if ext else " " * 8
        print(f"{lam:7.4f} {len(runs):4d} {surv:9.1f} {med} {mean} {mx}")


if __name__ == "__main__":
    main()
