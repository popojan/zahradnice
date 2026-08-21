#!/usr/bin/env python3
"""E2 retention readout from ret* series files.

Usage: bank_probe.py ladder "bankoff bankslow bankfast"

Phase layout (event ~ input char; drift is negligible without freezes):
A = none [0,40k) stores a rung-1 world+bank, B = fiery [40k,40k+B)
overwrites the standing crop, C = none [40k+B,+120k) measures recovery.
t50 = events into phase C until standing share1 >= 0.5 (NA if never,
censored at ~120k). bank1/banktot at C start = the surviving memory.
"""
import csv
import glob
import statistics
import sys

outdir, tags = sys.argv[1], sys.argv[2].split()
print(f"{'cfg':9} {'B':>7} {'seed':>4} {'t50':>7} {'bank1@C':>8}"
      f" {'banktot@C':>9} {'meanrung@C':>10}")
summary = {}
for tag in tags:
    for f in sorted(glob.glob(f"{outdir}/series-{tag}-ret*-s*.csv")):
        cond = f.split(f"{tag}-")[1].split("-s")[0]
        seed = f.split("-s")[-1][:-4]
        B = int(cond[3:])
        cstart = 40000 + B
        rows = list(csv.DictReader(open(f)))
        atc = min((r for r in rows if int(r["step"]) >= cstart),
                  key=lambda r: int(r["step"]), default=None)
        t50 = None
        for r in rows:
            if int(r["step"]) >= cstart and float(r["share1"]) >= 0.5:
                t50 = int(r["step"]) - cstart
                break
        key = (tag, B)
        summary.setdefault(key, []).append(t50)
        print(f"{tag:9} {B:>7} {seed:>4} "
              f"{t50 if t50 is not None else 'NA':>7} "
              f"{atc['bank1']:>8} {atc['banktot']:>9} "
              f"{float(atc['meanrung']):>10.2f}")
print()
print(f"{'cfg':9} {'B':>7} {'t50 median':>10}  (NA = no recovery in ~120k)")
for (tag, B), v in sorted(summary.items()):
    vals = [x for x in v if x is not None]
    na = len(v) - len(vals)
    med = f"{statistics.median(vals):.0f}" if vals else "-"
    extra = f" +{na}NA" if na else ""
    print(f"{tag:9} {B:>7} {med:>10}{extra}")
