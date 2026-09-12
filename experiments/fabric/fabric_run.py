#!/usr/bin/env python3
"""fabric_run.py -- drive an R0.1 fabric through supervised samples, headless.

usage: fabric_run.py CFG --task maj|thr|xor|par3|and --n 2000 --seed 1 [--ib 100] [--win 200]
Prints windowed accuracy, undecided rate, events per sample, and the learned synapse row.
"""
import argparse, os, random, subprocess, sys, tempfile, time

ap = argparse.ArgumentParser()
ap.add_argument("cfg")
ap.add_argument("--task", default="maj")
ap.add_argument("--n", type=int, default=2000)
ap.add_argument("--seed", type=int, default=1)
ap.add_argument("--nin", type=int, default=8)

ap.add_argument("--win", type=int, default=200)
ap.add_argument("--bin", default=os.path.join(os.path.dirname(__file__), "../../zahradnice-headless"))
ap.add_argument("--keep", action="store_true", help="keep trace/dump next to the cfg")
ap.add_argument("--noteach", action="store_true", help="no teacher: measure decisions only")
ap.add_argument("--fixed", default=None, help="type this bit string every sample")
ap.add_argument("--phases", default="i:300,T:10,c:14", help="per-sample phases after typing: char:count, T = teacher char")
ap.add_argument("--screen", default="6,16")
ap.add_argument("--until", default="", help="engine --until CHARS: these phase triggers run to quiescence from one byte")
ap.add_argument("--every", default="", help="N:CHARS — after every N-th sample also feed CHARS (e.g. 1000:r)")
ap.add_argument("--warmup", default="", help="bytes fed once after build (e.g. r for the initial re-roll)")
ap.add_argument("--holdout", type=float, default=0.0, help="fraction of the 2^nin inputs never used for training")
ap.add_argument("--test-every", type=int, default=0, help="every k-th sample is a held-out test sample with the silent teacher P/N")
a = ap.parse_args()

rng = random.Random(a.seed * 7919 + 17)
nin = a.nin
space = list(range(1 << nin)); rng.shuffle(space)
ntest = int(round(a.holdout * len(space)))
test_set, train_set = space[:ntest], space[ntest:]
randlab = {x: rng.randint(0, 1) for x in range(1 << nin)}
if a.task == "thr":
    w = [rng.choice([-2, -1, 1, 2]) for _ in range(nin)]
    dots = sorted(sum(wi * ((x >> i) & 1) for i, wi in enumerate(w)) for x in range(1 << nin))
    b = dots[len(dots) // 2]
def label(bits):
    if a.task == "maj": return int(sum(bits) > nin // 2)
    if a.task == "and": return bits[0] & bits[1]
    if a.task == "xor": return bits[0] ^ bits[1]
    if a.task == "par3": return bits[0] ^ bits[1] ^ bits[2]
    if a.task == "thr": return int(sum(wi * bi for wi, bi in zip(w, bits)) > b)
    if a.task == "rand": return randlab[sum(bi << i for i, bi in enumerate(bits))]
    raise SystemExit("unknown task " + a.task)

labels = []; is_test = []
parts = ["b" + a.warmup]
every_n, every_chars = (int(a.every.split(":")[0]), a.every.split(":")[1]) if a.every else (0, "")
for t in range(a.n):
    test = a.test_every > 0 and (t + 1) % a.test_every == 0
    if a.fixed is not None: bits = [int(ch) for ch in a.fixed]
    else:
        pool = test_set if (test and test_set) else train_set
        x = rng.choice(pool); bits = [(x >> i) & 1 for i in range(nin)]
    y = label(bits); labels.append(y); is_test.append(test)
    parts.append("".join(str(x) for x in bits))
    for ph in a.phases.split(","):
        ch, cnt = ph.split(":"); cnt = int(cnt)
        if ch == "T":
            if a.noteach: continue
            parts.append((("P" if y else "N") if test else ("p" if y else "n")) * cnt)
        else:
            parts.append(ch * cnt)
    if every_n and (t + 1) % every_n == 0: parts.append(every_chars)
inp = "".join(parts)

tag = "%s-%s-s%d" % (os.path.splitext(os.path.basename(a.cfg))[0], a.task, a.seed)
d = tempfile.mkdtemp(dir=os.environ.get("FABRIC_TMP")) if not a.keep else os.path.dirname(os.path.abspath(a.cfg))
inpath = os.path.join(d, tag + ".in"); tr = os.path.join(d, tag + ".trace"); sc = os.path.join(d, tag + ".screen")
open(inpath, "w").write(inp)
t0 = time.time()
r = subprocess.run([a.bin, a.cfg, "--seed", str(a.seed), "--screen", a.screen, "--input", "@" + inpath,
                    "--trace", tr, "--dump-screen", sc] + (["--until", a.until] if a.until else []), capture_output=True, text=True)
wall = time.time() - t0
ev = None
for line in r.stderr.splitlines():
    if line.startswith("Headless run:"):
        ev = int(line.split()[2])
if ev is None:
    sys.stderr.write(r.stderr); raise SystemExit("engine failed")

outcomes = []; undecided = 0
if a.noteach:
    fired = 0
    for line in open(tr, encoding="utf-8"):
        f = line.rstrip("\n").split("\t")
        if f[0] == "apply" and f[4] == "i" and f[10][4] in "01": fired += f[10][4] == "1"
    print("%s fixed=%s fired %d / %d = %.3f" % (tag, a.fixed, fired, a.n, fired / a.n)); raise SystemExit
for line in open(tr, encoding="utf-8"):
    f = line.rstrip("\n").split("\t")
    if f[0] != "apply" or f[4] not in ("p", "n", "P", "N"): continue
    head = f[10]
    if head[4] in "+-/" and head[3] in "pnPN" and len(outcomes) < a.n and (head[2] in "01YN" or ord(head[2]) >= 0x2800):
        # marking rules only: lhs is 0/1 or a counter glyph, rhs k/m/f
        outcomes.append(head[4])
        if ord(head[2]) >= 0x2800: undecided += 1
        if len(outcomes) == a.n: break
plants = sum(1 for line in open(tr, encoding="utf-8") if "\t==#c#" in line)
assert len(outcomes) == a.n and plants >= a.n - 1, ("markings", len(outcomes), "plants", plants, "n", a.n)
acc = lambda seg: sum(1 for o in seg if o == "+") / max(1, len(seg))
tr = [o for o, t in zip(outcomes, is_test) if not t]; te = [o for o, t in zip(outcomes, is_test) if t]
wins = [acc(outcomes[i:i + a.win]) for i in range(0, a.n, a.win)]
final = acc(outcomes[-a.n // 4:])
if te:
    k = a.win // a.test_every
    print("  train acc (windows): " + " ".join("%.2f" % acc(tr[i:i + a.win - k]) for i in range(0, len(tr), a.win - k)) + "  final %.3f" % acc(tr[-len(tr) // 4:]))
    print("  TEST  acc (windows): " + " ".join("%.2f" % acc(te[i:i + k]) for i in range(0, len(te), k)) + "  final %.3f  (holdout %d inputs)" % (acc(te[-len(te) // 4:]), len(test_set)))
screen = open(sc, encoding="utf-8").read().splitlines()
syn = screen[2] if len(screen) > 2 else ""
print("%s task=%s n=%d final_acc=%.3f undecided=%.3f ev/sample=%.1f wall=%.1fs ev/s=%.0f" %
      (tag, a.task, a.n, final, undecided / a.n, ev / a.n, wall, ev / max(wall, 1e-9)))
print("  windows: " + " ".join("%.2f" % x for x in wins))
print("  synapses: " + syn.rstrip())
if a.task == "thr": print("  target w=%s b=%d" % (w, b))
if not a.keep: __import__("shutil").rmtree(d, ignore_errors=True)
