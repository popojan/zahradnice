#!/usr/bin/env python3
"""model_tm.py -- a Tsetlin-machine-shaped fabric as arithmetic (Granmo 2018, simplified).
C clauses (half positive, half negative polarity), each with 2*nin literal automata
(state 1..2N, include iff state > N). Vote = sum(pos) - sum(neg); the readout is either
the exact sign (READOUT=exact) or a gambler's-ruin counter of gain K over clause outputs.
Feedback probability: TM-style (T - v)/(2T) or the fabric approximation 'wrong=1, right=Q'.
usage: model_tm.py C N s T task n seeds [K] [FB=tm|wrong] [Q]"""
import os, random, sys
C = int(sys.argv[1]); N = int(sys.argv[2]); S = float(sys.argv[3]); T = int(sys.argv[4])
task = sys.argv[5]; n = int(sys.argv[6]); seeds = int(sys.argv[7])
K = int(sys.argv[8]) if len(sys.argv) > 8 else 0
FB = sys.argv[9] if len(sys.argv) > 9 else "tm"
Q = float(sys.argv[10]) if len(sys.argv) > 10 else 0.1
nin = int(os.environ.get("NIN", 8))
def run(seed):
    rng = random.Random(seed * 7919 + 17)
    def label(bits):
        if task == "maj": return int(sum(bits) > nin // 2)
        if task == "and": return bits[0] & bits[1]
        if task == "xor": return bits[0] ^ bits[1]
        if task == "par3": return bits[0] ^ bits[1] ^ bits[2]
    A = [[N] * (2 * nin) for _ in range(C)]      # all excluded, at the boundary
    pol = [1 if c < C // 2 else -1 for c in range(C)]
    out = []
    for t in range(n):
        bits = [rng.randint(0, 1) for _ in range(nin)]; y = label(bits)
        lits = bits + [1 - b for b in bits]
        co = []
        for c in range(C):
            inc = [k for k in range(2 * nin) if A[c][k] > N]
            co.append(int(all(lits[k] for k in inc)))          # empty clause -> 1 (training semantics)
        v = sum(pol[c] * co[c] for c in range(C))
        if K:
            s = sum(1 for c in range(C) if co[c] and pol[c] > 0); d = 1 + sum(1 for c in range(C) if co[c] and pol[c] < 0)
            r = d / s if s else None
            pred = 0 if s == 0 else int(rng.random() < 1.0 / (1.0 + min(r, 1e6) ** K))
        else:
            pred = int(v > 0) if v != 0 else rng.randint(0, 1)
        out.append(int(pred == y))
        vc = max(-T, min(T, v))
        for c in range(C):
            if FB == "tm":
                p = (T - vc) / (2 * T) if y == 1 else (T + vc) / (2 * T)
            else:
                p = 1.0 if pred != y else Q
            if rng.random() >= p: continue
            type1 = (y == 1 and pol[c] > 0) or (y == 0 and pol[c] < 0)
            if type1:
                if co[c]:
                    for k in range(2 * nin):
                        if lits[k]:
                            if rng.random() < (S - 1) / S: A[c][k] = min(2 * N, A[c][k] + 1)
                        else:
                            if rng.random() < 1 / S: A[c][k] = max(1, A[c][k] - 1)
                else:
                    for k in range(2 * nin):
                        if rng.random() < 1 / S: A[c][k] = max(1, A[c][k] - 1)
            else:
                if co[c]:
                    for k in range(2 * nin):
                        if not lits[k] and A[c][k] <= N: A[c][k] = min(2 * N, A[c][k] + 1)
    return sum(out[-n // 4:]) / (n // 4), A
for seed in range(1, seeds + 1):
    acc, A = run(seed)
    print("C=%d N=%d s=%g T=%d K=%d FB=%s %s s%d final_acc=%.3f" % (C, N, S, T, K, FB, task, seed, acc))
