#!/usr/bin/env python3
"""model_r01.py -- the R0.1 learning rule as plain arithmetic, to separate
'the substrate is faithful' from 'the rule is weak'. Same sampler semantics:
P(fire) = 1/(1+((d/s))**K) with s = up-mass, d = down-mass (gambler's ruin)."""
import random, sys
K = int(sys.argv[1]); N = int(sys.argv[2]); THETA = float(sys.argv[3]); task = sys.argv[4]
n = int(sys.argv[5]); seeds = int(sys.argv[6]); LR = float(sys.argv[7]) if len(sys.argv) > 7 else 1.0
nin = 8
def run(seed):
    rng = random.Random(seed * 7919 + 17)
    if task == "thr":
        w = [rng.choice([-2, -1, 1, 2]) for _ in range(nin)]
        dots = sorted(sum(wi * ((x >> i) & 1) for i, wi in enumerate(w)) for x in range(1 << nin))
        b = dots[len(dots) // 2]
    def label(bits):
        if task == "maj": return int(sum(bits) > nin // 2)
        if task == "and": return bits[0] & bits[1]
        if task == "xor": return bits[0] ^ bits[1]
        if task == "thr": return int(sum(wi * bi for wi, bi in zip(w, bits)) > b)
    W = [0] * (nin + 1)          # last = bias (input always 1)
    out = []
    for t in range(n):
        bits = [rng.randint(0, 1) for _ in range(nin)]; y = label(bits)
        act = bits + [1]
        s = sum(W[i] for i in range(nin + 1) if act[i] and W[i] > 0)
        d = THETA + sum(-W[i] for i in range(nin + 1) if act[i] and W[i] < 0)
        p = 0.0 if s == 0 else 1.0 / (1.0 + (d / s) ** K)
        fire = rng.random() < p
        out.append(int(fire == bool(y)))
        if y and not fire:
            for i in range(nin + 1):
                if act[i] and rng.random() < LR: W[i] = min(N, W[i] + 1)
        if (not y) and fire:
            for i in range(nin + 1):
                if act[i] and rng.random() < LR: W[i] = max(-N, W[i] - 1)
    return sum(out[-n // 4:]) / (n // 4), W
for seed in range(1, seeds + 1):
    acc, W = run(seed)
    print("K=%d N=%d th=%g lr=%g %s s%d final_acc=%.3f W=%s" % (K, N, THETA, LR, task, seed, acc, W))
