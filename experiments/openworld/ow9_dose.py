#!/usr/bin/env python3
"""OW-9 postscript driver — the causal dose-response, as a CSV.

Fixed influx k=4, wound-fed fraction c/4 swept 0..1 by drive bytes
alone (the mix compiler's rule table is identical in every cell;
the carrion feed rule is trigger-filtered before gathering, so the
c=0 arm is bit-identical to OW-6's rain k=4 runs at equal seeds —
a pipeline identity check, not an independent replication).

Usage: python3 ow9_dose.py    Output: ow9_dose.csv + summary.
"""
import csv
import sys
import tempfile
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "inverse"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import analyzers
import ow7

K, SEEDS = 4, 60


def main():
    work = Path(tempfile.mkdtemp(prefix="ow9dose_"))
    text, imap = ow7.build_cfg(("α", "β"), "mix")
    cfg = work / "c.cfg"
    cfg.write_text(text)
    d0 = work / "i.txt"
    ow7.run_engine(cfg, 1, "z", work / "t.trace", d0)
    s0 = analyzers.parse_dump(d0, ow7.ROWS, ow7.RING)
    prefix = "".join(ow7.KEY[g] for g in
                     [("α", "β")[min(i * 2 // ow7.RING, 1)]
                      for i in range(ow7.RING)]) + "e"
    rows, fails = [], 0
    for c in range(K + 1):
        inp = prefix + "T" * ow7.EST + \
            ("pq" + "f" * (K - c) + "g" * c + "T" * ow7.M) * ow7.BLOCKS
        wins = Counter()
        for seed in range(1, SEEDS + 1):
            tr, du = work / "x.trace", work / "x.txt"
            ow7.run_engine(cfg, seed, inp, tr, du)
            grid = [list(row) for row in s0]
            for lhs, idx, ro, co, _t in analyzers.parse_trace(tr):
                for dr, dc, ch in imap[(lhs, idx)][0]:
                    grid[(ro - 1 + dr) % (ow7.ROWS - 1)][
                        (co + dc) % ow7.RING] = ch
            final = ["".join(x) for x in grid]
            if final != analyzers.parse_dump(du, ow7.ROWS, ow7.RING):
                fails += 1
            gates = Counter(g for g in final[2] if g in "αβ")
            dom = gates.most_common(1)[0][0] if gates else "DEAD"
            rows.append((c, seed, dom))
            wins[dom] += 1
        a, b = wins.get("α", 0), wins.get("β", 0)
        share = a / (a + b) if a + b else float("nan")
        print(f"c={c}/4: α:{a:>2} β:{b:>2} DEAD:{wins.get('DEAD', 0):>2}"
              f"  α-share {share:.3f}")
    print(f"exactness failures: {fails}/{len(rows)}")
    with open(Path(__file__).parent / "ow9_dose.csv", "w",
              newline="") as f:
        w = csv.writer(f)
        w.writerow(["c", "seed", "dom"])
        w.writerows(rows)


if __name__ == "__main__":
    main()
