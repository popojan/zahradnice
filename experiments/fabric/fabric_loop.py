#!/usr/bin/env python3
"""fabric_loop.py -- closed-loop driver for a multi-S Tsetlin fabric (needs the
engine's --stream and --until). Each sample is 12-13 bytes: 8 bits, `i`, `o`,
the teacher (p/n, or silent P/N for held-out test samples), the feedback trigger
that selects S for this sample (training samples only), `c`. The driver tails the
trace, reads the outcome of every sample as it lands, and chooses S per epoch.

policies:  fixed:S | schedule:S@t,S@t,... | ucb[:c] | random
usage: fabric_loop.py CFG --task xor --n 6000 --seed 1 --screen 53,20 --holdout 0.5 --test-every 4 --policy ucb --epoch 200
"""
import argparse, math, os, random, re, subprocess, sys, tempfile, time

ap = argparse.ArgumentParser()
ap.add_argument("cfg"); ap.add_argument("--task", default="xor"); ap.add_argument("--n", type=int, default=6000)
ap.add_argument("--seed", type=int, default=1); ap.add_argument("--nin", type=int, default=8)
ap.add_argument("--screen", default="53,20"); ap.add_argument("--holdout", type=float, default=0.5)
ap.add_argument("--test-every", type=int, default=4); ap.add_argument("--policy", default="ucb")
ap.add_argument("--epoch", type=int, default=200, help="training samples per S decision")
ap.add_argument("--win", type=int, default=1500)
ap.add_argument("--bin", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../zahradnice-headless"))
a = ap.parse_args()

# S -> trigger map from the generator's comment line
smap = {}
for line in open(a.cfg, encoding="utf-8"):
    m = re.match(r"# S triggers: (.*)", line)
    if m:
        for kv in m.group(1).split():
            t, s = kv.split("="); smap[float(s)] = t
        break
assert smap, "cfg carries no '# S triggers' line (generate with S=a,b,c)"
arms = sorted(smap)

rng = random.Random(a.seed * 7919 + 17)
nin = a.nin
space = list(range(1 << nin)); rng.shuffle(space)
ntest = int(round(a.holdout * len(space))); test_set, train_set = space[:ntest], space[ntest:]
randlab = {x: rng.randint(0, 1) for x in range(1 << nin)}
w_thr = [rng.choice([-2, -1, 1, 2]) for _ in range(nin)]
dots = sorted(sum(wi * ((x >> i) & 1) for i, wi in enumerate(w_thr)) for x in range(1 << nin)); b_thr = dots[len(dots) // 2]
def label(bits):
    t = a.task
    if t == "maj": return int(sum(bits) > nin // 2)
    if t == "and": return bits[0] & bits[1]
    if t == "and3": return bits[0] & bits[1] & bits[2]
    if t == "xor": return bits[0] ^ bits[1]
    if t == "par3": return bits[0] ^ bits[1] ^ bits[2]
    if t == "thr": return int(sum(wi * bi for wi, bi in zip(w_thr, bits)) > b_thr)
    if t == "rand": return randlab[sum(bi << i for i, bi in enumerate(bits))]
    if t == "proto":   # within Hamming distance 1 of 11110000 or 00001111
        p1 = sum(bits[i] != (1 if i < 4 else 0) for i in range(8)); p2 = 8 - p1
        return int(min(p1, p2) <= 1)
    raise SystemExit("unknown task " + t)

# policy
def parse_policy(p):
    if p.startswith("fixed:"): return ("fixed", float(p[6:]))
    if p.startswith("schedule:"):
        sched = sorted((int(x.split("@")[1]), float(x.split("@")[0])) for x in p[9:].split(","))
        return ("schedule", sched)
    if p.startswith("ucb"): return ("ucb", float(p[4:]) if ":" in p else 0.5)
    if p == "random": return ("random", None)
    raise SystemExit("bad policy " + p)
pol, parg = parse_policy(a.policy)
stats = {s: [0, 0.0] for s in arms}     # arm -> [epochs, sum of rewards]
def choose(epoch_idx, trained):
    if pol == "fixed": return parg
    if pol == "schedule":
        cur = parg[0][1]
        for t, s in parg:
            if trained >= t: cur = s
        return cur
    if pol == "random": return rng.choice(arms)
    for s in arms:
        if stats[s][0] == 0: return s
    N = sum(v[0] for v in stats.values())
    return max(arms, key=lambda s: stats[s][1] / stats[s][0] + parg * math.sqrt(2 * math.log(N) / stats[s][0]))

# engine
d = tempfile.mkdtemp(dir=os.environ.get("FABRIC_TMP")); tr = os.path.join(d, "loop.trace")
until = "io" + "".join(smap.values()) + "c"
eng = subprocess.Popen([a.bin, a.cfg, "--seed", str(a.seed), "--screen", a.screen, "--stream", "--until", until, "--trace", tr],
                       stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
while not os.path.exists(tr): time.sleep(0.01)
tf = open(tr, "rb"); pending = b""
def next_marking():
    """block until the next teacher marking lands in the trace; return '+' / '-' / '/'.
    The file is being appended to: only complete lines are decoded."""
    global pending
    while True:
        chunk = tf.read()
        if not chunk:
            if eng.poll() is not None: raise SystemExit("engine exited early: " + eng.stderr.read())
            time.sleep(0.002); continue
        pending += chunk
        while b"\n" in pending:
            raw, pending = pending.split(b"\n", 1)
            f = raw.decode("utf-8").split("\t")
            if f[0] == "apply" and f[4] in "pnPN" and f[10][4] in "+-/" and (f[10][2] in "YN" or ord(f[10][2]) >= 0x2800):
                return f[10][4]

eng.stdin.write("b"); eng.stdin.flush()
outcomes = []; is_test = []; used = []; epoch_log = []
t0 = time.time(); trained = 0; epoch_idx = 0; cur_S = choose(0, 0); ep_test = []
for t in range(a.n):
    test = a.test_every > 0 and (t + 1) % a.test_every == 0 and test_set
    x = rng.choice(test_set if test else train_set); bits = [(x >> i) & 1 for i in range(nin)]; y = label(bits)
    msg = "".join(str(v) for v in bits) + "io" + (("P" if y else "N") if test else ("p" if y else "n"))
    if not test: msg += smap[cur_S]
    msg += "c"
    eng.stdin.write(msg); eng.stdin.flush()
    o = next_marking(); ok = o == "+"
    outcomes.append(ok); is_test.append(bool(test)); used.append(cur_S)
    if test: ep_test.append(ok)
    else:
        trained += 1
        if trained % a.epoch == 0:
            r = sum(ep_test) / max(1, len(ep_test))
            stats[cur_S][0] += 1; stats[cur_S][1] += r
            epoch_log.append((cur_S, r)); ep_test = []
            epoch_idx += 1; cur_S = choose(epoch_idx, trained)
eng.stdin.close(); eng.wait(); wall = time.time() - t0
ev = re.search(r"Headless run: (\d+) events", eng.stderr.read())
acc = lambda seg: sum(seg) / max(1, len(seg))
tr_ = [o for o, s in zip(outcomes, is_test) if not s]; te = [o for o, s in zip(outcomes, is_test) if s]
tag = "%s %s seed=%d policy=%s" % (os.path.basename(a.cfg), a.task, a.seed, a.policy)
print("%s  train %.3f  TEST %.3f  (%d test samples, last quarter)  %.0f ev/s  %.0fs" %
      (tag, acc(tr_[-len(tr_) // 4:]), acc(te[-len(te) // 4:]), len(te) // 4, int(ev.group(1)) / wall if ev else 0, wall))
k = a.win // a.test_every
print("  TEST windows: " + " ".join("%.2f" % acc(te[i:i + k]) for i in range(0, len(te), k)))
if pol != "fixed":
    print("  epochs (S:test-acc): " + " ".join("%g:%.2f" % e for e in epoch_log))
    print("  arm use: " + "  ".join("S=%g x%d mean %.2f" % (s, v[0], v[1] / v[0] if v[0] else 0) for s, v in stats.items()))
__import__("shutil").rmtree(d, ignore_errors=True)
