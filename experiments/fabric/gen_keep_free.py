#!/usr/bin/env python3
"""gen_keep_free.py -- the keep fabric with NO PHASES and no driver: one timing trigger, the world inside the
program. A watchable demo of learning as rewriting (loom utopia 3.4, phase-free operation; roadmap 3e demo).

What happens, all on trigger T, in whatever order the sampler picks -- the order does not matter, because
every rule waits for its inputs to be decided:
  reset   the head R at input column 1 blanks the literal rows, sets every row's output to P (permit), resets
          the registers and the readout cell, then becomes the dealing head >.
  permit  a row with a zero synapse re-rolls with a small probability (drops its literals, sends its done
          token, picks L fresh literals by competing rules, and sits this sample out); otherwise P -> U0.
  deal    the head > walks the input row; at each column two rules of equal weight write the bit (o/x on
          the input row, t/u into every literal row and its negation) -- the randomness is the rule weight.
  check   a row in U_j with an include marker X over a dealt literal: true -> the literal becomes V and the
          row counts (U_j -> U_j+1, after L -> M matched); false -> the row fails (0). Rows decide as the
          bits arrive: anytime evaluation.
  emit    a matched row with a nonzero synapse sends it as a token into its lane (M -> E); then every
          finished row sends a DONE token (E -> Z, 0 -> z). Tokens ride the lane down; at the readout row
          synapse tokens add into P or N (carry chains), done tokens increment the DONE register.
  decide  when DONE == H every row has spoken and every synapse token is in (it went ahead of its row's
          done token): the readout cell compares P and N digit by digit -> Y or N.
  teach   the label is XOR of input bits 1 and 2, read by the rule from the input row: right -> + (score),
          wrong -> - and a head { (missed) or } (false alarm) on the lane; the head walks the rows, +-1
          on the synapse of every matched row, dies at the readout row; then R is planted for the next sample.
Params: H L M NIN OUT. Screen 3H+5 rows x LANE+3D+2 cols. Run: ./zahradnice experiments/fabric/keep-free.cfg
(SPACE to start; #timing T 3 -- a few hundred events per sample, learning visible in minutes)."""
import os
H = int(os.environ.get("H", 16)); L = int(os.environ.get("L", 2)); M = int(os.environ.get("M", 8)); NIN = int(os.environ.get("NIN", 8))
THETA = 1; MS = int(os.environ.get("MS", 2)); PREROLL = float(os.environ.get("PREROLL", 0.02))
OUT = os.environ.get("OUT", "keep-free.cfg")
B10 = 10; D = max(3, len(str(H * M + THETA)), len(str(H)))
SEP = NIN + 1; SYN = 2 * NIN + 2; LANE = SYN + 1
POSK = list(range(1, NIN + 1)) + list(range(SEP + 1, SEP + 1 + NIN))
def rowB(h): return 2 + 3 * h                       # anchor B at (0, 0); A row = rowB - 1
YR = 2 + 3 * H                                      # readout row: readout cell at col 0, registers right of the lane
PREG, NREG, DREG = LANE + 1, LANE + D + 1, LANE + 2 * D + 1
COLS = LANE + 3 * D + 2; ROWS = YR + 3
def dig(d): return chr(0x2880 + d)
def tok(w): return chr(0x28A0 + M + w)
DT = chr(0x28E1)                                                        # the done token
def syn(w):
    if w == 0: return "."
    return "ABCDEFGHI"[w - 1] if w > 0 else "abcdefghi"[-w - 1]
def U(j): return chr(0x2900 + j)                                        # j literals confirmed, undecided
RRB = [chr(0x28C0 + n) for n in range(L + 1)]                           # build-time picking: n literals still to pick, ends in U0
RRR = [chr(0x28D0 + n) for n in range(L + 1)]                           # re-roll picking: ends in z (sits the sample out)
START = chr(0x2840); HEADSDONE = chr(0x2842); EM = chr(0x2910)                  # EM: matched row, synapse token sent (E would be synapse +5)
SEED = chr(0x28FF)                                                       # the build anchor: B would be synapse +2, and everything runs on one trigger
def CMP(i): return chr(0x2860 + i)
MARKERS = set("#_>|otuxVR01YNMZzP+-{}X") | {START, HEADSDONE, EM, SEED, DT} | set(RRB) | set(RRR) | {U(j) for j in range(L)} | {CMP(i) for i in range(D)}
assert not ({syn(w) for w in range(-M, M + 1)} & MARKERS), "synapse alphabet collides with a marker (the letter B was the build anchor once)"
assert len(MARKERS) == len("#_>|otuxVR01YNMZzP+-{}X") + 5 + 2 * (L + 1) + L + D, "marker glyphs collide with each other"

def header(lhs, trig, rhs, ctx=" ", ctxrep=" ", score=0, weight=1):
    h = "==" + lhs + trig + rhs + "78" + ctx + ctxrep
    assert len(h) == 9, h
    return "%s %d %s" % (h, score, "%g" % weight)
def body(lhs_cells, rhs_cells):
    lr0 = min([0] + [r for r, _ in lhs_cells]); lr1 = max([0] + [r for r, _ in lhs_cells])
    lc0 = min([0] + [c for _, c in lhs_cells]); lc1 = max([0] + [c for _, c in lhs_cells])
    rr0 = min([0] + [r for r, _ in rhs_cells]); rr1 = max([0] + [r for r, _ in rhs_cells])
    rc0 = min([0] + [c for _, c in rhs_cells]); rc1 = max([0] + [c for _, c in rhs_cells])
    Wd = lc1 - lc0 + 1; R0, R1 = min(lr0, rr0), max(lr1, rr1)
    rows = [[" "] * (Wd + 1 + (rc1 - rc0 + 1)) for _ in range(R1 - R0 + 1)]
    def put(r, c, ch):
        assert rows[r - R0][c] == " ", (r, c, ch); rows[r - R0][c] = ch
    put(0, -lc0, "@")
    for (r, c), ch in lhs_cells.items(): put(r, c - lc0, ch)
    put(0, Wd, "@"); base = Wd + 1 - rc0; put(0, base, "@")
    for (r, c), ch in rhs_cells.items(): put(r, base + c, ch)
    lines = ["".join(row).rstrip() for row in rows]
    assert lines[0].strip()
    for ln in lines: assert ln[:1] not in ("#", "=", "^"), ln
    return "\n".join(lines)
out = []
def rule(h, lhs, rhs=None):
    out.append(h); out.append(body(lhs, rhs or {}))

out.append("#! keep fabric, no phases: XOR of bits 1,2 among %d   correct={score}   steps={steps}" % NIN)
out.append("# Generated by gen_keep_free.py H=%d L=%d M=%d NIN=%d D=%d -- do not edit. One trigger, no driver:" % (H, L, M, NIN, D))
out.append("# the head deals random bits, rows decide as bits arrive, tokens sum in registers, the readout answers,")
out.append("# a rule reads the label off the input row and teaches, and the next sample is dealt. Everything is rewriting.")
out.append("#help o/x=bits  X=literal  t/u/V=literal false/true/confirmed  A..H/a..h=synapse  tokens ride the lane  P N DONE=registers  {}=heads  SPACE run")
out.append("#threads 1")
out.append("#timing T %d" % MS)
out.append("#control q return")                                       # launched from the Evolution menu: q goes back
out.append("^%sul" % SEED)

def register_init():
    r = {}
    for i in range(D): r[(0, PREG + i)] = dig(0); r[(0, NREG + i)] = dig(0); r[(0, DREG + i)] = dig(0)
    r[(0, NREG + D - 1)] = dig(THETA)
    return r
# build: input row with the dealing head, rows picking their first literals, the readout row
rhs = {(0, c): "_" for c in range(1, NIN + 1)}; rhs[(0, SEP)] = "|"; rhs[(0, 1)] = ">"
for h in range(H):
    b = rowB(h); rhs[(b, 0)] = RRB[L]; rhs[(b, SEP)] = "|"; rhs[(b, SYN)] = "."
    for k in POSK: rhs[(b, k)] = "."
rhs[(YR, 0)] = START
for (dr, dc), ch in register_init().items(): rhs[(YR + dr, dc)] = ch
rule(header(SEED, "T", "#"), {}, rhs)

out.append("# reset: the head R (input column 1, next to #) blanks the literal rows, permits every row, resets registers and readout, deals")
reset = {(0, c - 1): "_" for c in range(2, NIN + 1)}                  # offsets from R, which stands at input column 1
for h in range(H):
    for k in POSK: reset[(rowB(h) - 1, k - 1)] = "~"
    reset[(rowB(h), -1)] = "P"
for (dr, dc), ch in register_init().items(): reset[(YR + dr, dc - 1)] = ch
reset[(YR, -1)] = START
rule(header("R", "T", ">"), {}, reset)                              # R only ever stands at input column 1 (the end rule plants it there)

out.append("# permit: P -> U0, or (zero synapse, small weight) re-roll: drop the literals, send the done token, pick afresh, sit out")
rule(header("P", "T", U(0)), {(0, SYN): "."}, {})
rule(header("P", "T", U(0), ctx="."), {(0, SYN): "!"}, {})
drop = {(0, k): "." for k in POSK}; drop[(0, LANE)] = DT
rule(header("P", "T", RRR[L], weight=PREROLL), {(0, SYN): ".", (0, LANE): "~"}, drop)

out.append("# deal: the head writes a random bit (two rules of equal weight) into the input row and every literal row, then moves")
for ch, lit, neg in (("o", "u", "t"), ("x", "t", "u")):
    lits = {}
    for h in range(H): lits[(rowB(h) - 1, 0)] = lit; lits[(rowB(h) - 1, SEP)] = neg
    adv = dict(lits); adv[(0, 1)] = ">"
    rule(header(">", "T", ch, ctx="|"), {(0, 1): "!"}, adv)
    rule(header(">", "T", ch), {(0, 1): "|"}, lits)

out.append("# check: an include marker over a dealt literal -- true: confirm and count; false: the row fails")
for j in range(L):
    for k in POSK:
        rule(header(U(j), "T", U(j + 1) if j + 1 < L else "M"), {(0, k): "X", (-1, k): "t"}, {(-1, k): "V"})
        rule(header(U(j), "T", "0"), {(0, k): "X", (-1, k): "u"}, {})

out.append("# emit: a matched row sends its synapse as a token (M -> EM), then every finished row sends the done token (EM -> Z, 0 -> z)")
for w in range(-M, M + 1):
    if w: rule(header(syn(w), "T", " "), {(0, -SYN): "M", (0, LANE - SYN): "~"}, {(0, -SYN): EM, (0, LANE - SYN): tok(w)})
rule(header("M", "T", EM), {(0, SYN): "."}, {})
rule(header(EM, "T", "Z"), {(0, LANE): "~"}, {(0, LANE): DT})
rule(header("0", "T", "z"), {(0, LANE): "~"}, {(0, LANE): DT})

out.append("# conveyor: a token moves one row down while the cell below is free; it stops at the readout row (blank to its left)")
for g in [tok(w) for w in range(-M, M + 1) if w] + [DT]:
    rule(header(g, "T", "~", ctx="~"), {(3, 0): "~", (0, -1): "!"}, {(3, 0): "*"})

out.append("# add: a synapse token into P (positive) or N (negative) with carry chains; a done token increments DONE")
def adds(g, m, gb):
    low = gb + D - 1
    for d in range(B10):
        if d + m < B10: rule(header(g, "T", "~"), {(0, low): dig(d)}, {(0, low): dig(d + m)}); continue
        for chain in range(1, D):
            lhs = {(0, low): dig(d)}; rhs_ = {(0, low): dig(d + m - B10)}
            for j in range(1, chain): lhs[(0, low - j)] = dig(9); rhs_[(0, low - j)] = dig(0)
            for d1 in range(B10 - 1):
                l2 = dict(lhs); l2[(0, low - chain)] = dig(d1); r2 = dict(rhs_); r2[(0, low - chain)] = dig(d1 + 1)
                rule(header(g, "T", "~"), l2, r2)
for w in range(-M, M + 1):
    if w: adds(tok(w), abs(w), (PREG if w > 0 else NREG) - LANE)
adds(DT, 1, DREG - LANE)

out.append("# decide: when DONE == H, compare P and N from the most significant digit")
done = {(0, DREG + i): dig(int(c)) for i, c in enumerate(str(H).zfill(D))}
def compare_rules(anchor, i, extra):
    nxt = CMP(i + 1) if i + 1 < D else "N"
    for dp in range(B10):
        for dn in range(B10):
            res = "Y" if dp > dn else ("N" if dp < dn else nxt)
            lhs = {(0, PREG + i): dig(dp), (0, NREG + i): dig(dn)}; lhs.update(extra)
            rule(header(anchor, "T", res), lhs, {})
compare_rules(START, 0, done)
for i in range(1, D): compare_rules(CMP(i), i, {})

out.append("# teach: the label is XOR of input bits 1 and 2 (o = 0, x = 1); right -> +, wrong -> - and a head on the lane")
lane_top = (rowB(0) - YR, LANE)
for b1 in "ox":
    for b2 in "ox":
        y = (b1 == "x") != (b2 == "x"); bits = {(-YR, 1): b1, (-YR, 2): b2}
        rule(header("Y", "T", "+" if y else "-", score=1 if y else 0), bits, {} if y else {lane_top: "}"})
        rule(header("N", "T", "-" if y else "+", score=0 if y else 1), bits, {lane_top: "{"} if y else {})
out.append("# feedback: the head steps the synapse of every finished matched row (Z), passes the rest, dies at the readout row")
for g, d in (("{", 1), ("}", -1)):
    for w in range(-M, M + 1):
        rule(header(g, "T", "~"), {(0, -LANE): "Z", (0, -1): syn(w)}, {(0, -1): syn(max(-M, min(M, w + d))), (3, 0): g})
    for st in ["z"] + RRR[1:] + RRB[1:]: rule(header(g, "T", "~"), {(0, -LANE): st}, {(3, 0): g})
    rule(header(g, "T", "~"), {(0, -LANE): "-"}, {(0, -LANE): HEADSDONE})
out.append("# end of the sample: plant R at input column 1 for the next one")
for g in ("+", HEADSDONE): rule(header(g, "T", "~"), {}, {(-YR, 1): "R"})

out.append("# picking literals: a row in a picking state takes a free column, positive or negative, one per event")
for RR, final in ((RRB, U(0)), (RRR, "z")):
    for n in range(L, 0, -1):
        nxt = RR[n - 1] if n > 1 else final
        for i in range(1, NIN + 1):
            free = {(0, i): ".", (0, SEP + i): "."}
            rule(header(RR[n], "T", nxt), free, {(0, i): "X"})
            rule(header(RR[n], "T", nxt), free, {(0, SEP + i): "X"})

open(OUT, "w", encoding="utf-8").write("\n".join(out) + "\n")
print("%s: %d rules, screen %d rows x %d cols" % (OUT, sum(1 for l in out if l.startswith("=")), ROWS, COLS))
