#!/usr/bin/env python3
"""decode_tm.py SCREEN [C] [NIN] -- read the learned clauses off a Tsetlin-fabric screen dump.
The network is the screen: uppercase automata are included literals."""
import sys
rows = open(sys.argv[1], encoding="utf-8").read().splitlines()
C = int(sys.argv[2]) if len(sys.argv) > 2 else 16; NIN = int(sys.argv[3]) if len(sys.argv) > 3 else 8
for c in range(C):
    r = rows[3 + 3 * c]
    lits = ["x%d" % k for k in range(1, NIN + 1) if r[k].isupper()]
    lits += ["~x%d" % (k - NIN - 1) for k in range(NIN + 2, 2 * NIN + 2) if r[k].isupper()]
    print("%3d %s  %s" % (c, "+" if c < C // 2 else "-", " & ".join(lits) or "(empty)"))
