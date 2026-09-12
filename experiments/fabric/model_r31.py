#!/usr/bin/env python3
"""model_r31.py -- two-layer fabric with spatial sign-backprop, as arithmetic.
Hidden units and the output are gambler's-ruin counters (gain K). Teacher marks
the output; each hidden unit derives a 'todo' from the output error and the sign
of its outgoing synapse, gated by its own activity; all synapses step +-1 on
active inputs. Usage: model_r31.py K N THETA H task n seeds [LR]"""
import os, random, sys
ONE = int(os.environ.get("ONE", 0))
NOZERO = int(os.environ.get("NOZERO", 0))
REROLL = int(os.environ.get("REROLL", 0))   # every REROLL samples, re-roll hidden units with |Wo|<=1
K = int(sys.argv[1]); N = int(sys.argv[2]); THETA = float(sys.argv[3]); H = int(sys.argv[4])
task = sys.argv[5]; n = int(sys.argv[6]); seeds = int(sys.argv[7]); LR = float(sys.argv[8]) if len(sys.argv) > 8 else 1.0
nin = int(__import__("os").environ.get("NIN", 8))
def fire(rng, s, d):
    if s == 0: return False
    r = d / s
    if r < 1e-9: return True
    try: p = 1.0 / (1.0 + r ** K)
    except OverflowError: p = 0.0
    return rng.random() < p
def run(seed):
    rng = random.Random(seed * 7919 + 17)
    def label(bits):
        if task == "maj": return int(sum(bits) > nin // 2)
        if task == "and": return bits[0] & bits[1]
        if task == "xor": return bits[0] ^ bits[1]
        if task == "par3": return bits[0] ^ bits[1] ^ bits[2]
    R = int(sys.argv[9]) if len(sys.argv) > 9 else 2      # random init range
    FREEZE = int(sys.argv[10]) if len(sys.argv) > 10 else 0  # 1 = hidden layer never learns
    EPS = float(sys.argv[11]) if len(sys.argv) > 11 else 0.0 # exploration floor (base up-mass)
    MODE = sys.argv[12] if len(sys.argv) > 12 else "sign"    # sign = sign-backprop, pert = reward-modulated
    Wh = [[rng.randint(-R, R) for _ in range(nin + 1)] for _ in range(H)]
    Wo = [rng.randint(-R, R) for _ in range(H + 1)]
    if NOZERO: Wo = [w if w != 0 else rng.choice([-1, 1]) for w in Wo]
    if __import__("os").environ.get("IDEAL"):          # ideal XOR features in the first two hidden units
        Wh[0] = [6, -6] + [0] * (nin - 1); Wh[1] = [-6, 6] + [0] * (nin - 1)
    out = []
    for t in range(n):
        bits = [rng.randint(0, 1) for _ in range(nin)]; y = label(bits)
        act = bits + [1]
        h = []
        for j in range(H):
            s = EPS + sum(Wh[j][i] for i in range(nin + 1) if act[i] and Wh[j][i] > 0)
            d = THETA + sum(-Wh[j][i] for i in range(nin + 1) if act[i] and Wh[j][i] < 0)
            h.append(int(fire(rng, s, d)))
        hact = h + [1]
        s = EPS + sum(Wo[j] for j in range(H + 1) if hact[j] and Wo[j] > 0)
        d = THETA + sum(-Wo[j] for j in range(H + 1) if hact[j] and Wo[j] < 0)
        o = int(fire(rng, s, d))
        out.append(int(o == y))
        if REROLL and (t + 1) % REROLL == 0:
            for j in range(H):
                if abs(Wo[j]) <= 1:
                    Wh[j] = [rng.randint(-R, R) for _ in range(nin + 1)]; Wo[j] = 0
        err = 0 if o == y else (1 if y else -1)     # +1 missed, -1 false alarm
        if MODE == "pert" and not FREEZE:
            rew = 1 if o == y else -1
            for j in range(H):
                todo = rew * (1 if h[j] else -1)
                for i in range(nin + 1):
                    if act[i] and rng.random() < LR: Wh[j][i] = max(-N, min(N, Wh[j][i] + todo))
        if err:
            todos = []
            for j in range(H if (not FREEZE and MODE == "sign") else 0):
                todo = err * (1 if Wo[j] > 0 else -1 if Wo[j] < 0 else 0)
                if todo > 0 and h[j] == 1: todo = 0     # already firing
                if todo < 0 and h[j] == 0: todo = 0     # already silent
                if todo: todos.append((j, todo))
            if ONE and todos: todos = [rng.choice(todos)]
            for j, todo in todos:
                for i in range(nin + 1):
                    if act[i] and rng.random() < LR: Wh[j][i] = max(-N, min(N, Wh[j][i] + todo))
            for j in range(H + 1):
                if hact[j] and rng.random() < LR:
                    Wo[j] = max(-N, min(N, Wo[j] + err))
                    if NOZERO and Wo[j] == 0 and j < H: Wo[j] = err      # skip zero: the sign must exist
    return sum(out[-n // 4:]) / (n // 4), Wh, Wo
for seed in range(1, seeds + 1):
    acc, Wh, Wo = run(seed)
    print("K=%d N=%d th=%g H=%d lr=%g %s s%d final_acc=%.3f Wo=%s Wh=%s" % (K, N, THETA, H, LR, task, seed, acc, Wo, Wh if H <= 4 else "..."))
