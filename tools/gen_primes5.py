#!/usr/bin/env python3
"""Generate programs/primes/05-fischer.cfg -- Fischer's real-time prime array.

    P. C. Fischer, "Generation of Primes by a One-Dimensional Real-Time
    Iterative Array", JACM 12(3) (1965) 388-394, doi:10.1145/321281.321290.
    Full text: backlog/research/fischer-1965.txt

What is different from primes2
------------------------------
primes2 draws the same kind of picture -- rows are cells, columns are time,
mirrors bound bands, a token bounces inside one -- but it is not a cellular
automaton: its allocation ray travels up-LEFT, i.e. backwards in time, and it
crosses O(p) cells inside a single column.  Fischer's array has no such move.
Every signal here travels at speed <= 1 cell per column:

    a  speed 1 both ways        partition builder
    b  speed 1/3 both ways      "this number has a divisor" (and, rightwards,
                                 the other half of the partition builder)
    c  speed 1/2 right, 1 left  oscillates inside one block, period 3k

so the screen is a lawful space-time diagram and the verdict for n stands in
column 3n.  That is the whole point: real time.  The price is Fischer's own
"less efficient" sieve -- a block is built for EVERY k >= 2, not just primes,
so blocks cost sum_{k<=sqrt N} k ~ N/2 rows where primes2 needs only ~N/ln N.

Machine
-------
  Blocks.  Cell p_k = k(k+1)/2 becomes a P-machine at time (3k^2+k)/2 - 1;
  everything between p_{k-1} and p_k is block k, of length k.  An a-pulse and
  a b-pulse launched rightwards meet exactly at p_{k+1} because a runs three
  times faster and starts k+1 cells behind -- that meeting IS the allocation,
  and it needs no arithmetic and no divisor in the rule set (primes2's one
  good property, kept).

  Marking.  A c-pulse oscillates in block k with period 3k.  Every time it
  turns round at the left end, a b-pulse leaves for M_0 at speed 1/3 and gets
  there at time 3k^2, 3k(k+1), 3k(k+2), ... -- i.e. k^2, k^2+k, ... crossed
  out.  M_0 prints '#' at time 3n when no b arrived, '.' otherwise.

Layout on screen
----------------
  row 0        status line (engine)
  row 1        M_0, the number line: one verdict every third column
  rows 2..R-2  cells M_1, M_2, ...   (a P-machine shows as a mirror '=')
  row R-1      wall: the array is truncated here, pulses are absorbed
  column 0     the configuration at t = 0
  columns 1..  one per time step

Derivation
----------
There is no scan head walking a column.  Every row carries its OWN head and
derives its own cell from the three cells to its left, which is exactly the
CA step.  Rows advance independently and wait on each other only through the
positive literals in their context, so the wavefront is ragged and the
picture assembles in parallel -- and the derivation stays confluent because a
head simply cannot fire until its three left neighbours are final.

Two rewrites per cell: pass A folds in the cell's own carry plus whatever the
row above delivers, pass B folds in what the row below delivers.  Splitting
it that way is what keeps the rule table at ~420 rules instead of the ~1000
a single-pass (up, mid, down) table would need.
"""

import os
import sys
from collections import defaultdict

# --------------------------------------------------------------------------
# 1. Fischer's array, exactly as Table 1 / Lemmas 1-2 give it.
#
# A pending emission (sig, dir, k) held at time t means: the neighbour in
# direction dir receives sig at time t+k.  That is the paper's convention --
# "output emitted to L at t+2" = "the left neighbour has it at t+2".
# --------------------------------------------------------------------------

QUIESCENT = ('N', ())


def table(typ, inL, inR):
    """Table 1.  Returns (emissions, new_type)."""
    out = set()
    ntyp = typ
    if typ == 'N':
        if 'a' in inL and 'b' in inL:              # line 1: allocate
            ntyp = 'P'
            out |= {('b', 'R', 2), ('a', 'L', 2)}
        elif 'a' in inL:                            # line 2
            out |= {('a', 'R', 1)}
        elif 'b' in inL:                            # line 4
            out |= {('b', 'R', 3)}
        if 'c' in inL:                              # line 6
            out |= {('c', 'R', 2)}
        if 'a' in inR:                              # line 3
            out |= {('a', 'L', 1)}
        if 'b' in inR:                              # line 5
            out |= {('b', 'L', 3)}
        if 'c' in inR:                              # line 7
            out |= {('c', 'L', 1)}
    else:                                           # P
        if 'a' in inL:                              # line 8
            out |= {('a', 'R', 1)}
        assert 'b' not in inL, 'Table 1 line 10 says this cannot happen'
        if 'c' in inL:                              # line 12
            out |= {('c', 'L', 1)}
        if 'a' in inR:                              # line 9: block starts up
            out |= {('a', 'R', 1), ('c', 'R', 2), ('b', 'L', 3)}
        if 'b' in inR:                              # line 11
            out |= {('b', 'L', 3)}
        if 'c' in inR:                              # line 13: turn round, mark
            out |= {('c', 'R', 2), ('b', 'L', 3)}
    return frozenset(out), ntyp


# M_0, the end machine.  Fischer emits the verdict for n at time 3n+1; here
# it is shown at 3n instead, because in a space-time diagram the b-arrival is
# known while column 3n is being drawn.  Tags:
#   S0..S3  the first four columns (start-up; S3 relays the a coming back)
#   p1, p2  the two columns after a verdict
#   VP, VC  a verdict column: prime / composite
M0_TAGS = ('S0', 'S1', 'S2', 'S3', 'p1', 'p2', 'VP', 'VC')

M0_PEND = {
    'S0': frozenset({('a', 'R', 1), ('b', 'R', 1)}),   # t=0: fire a and b
    'S3': frozenset({('a', 'R', 1)}),                  # t=3: relay a rightwards
}


def m0_step(tag, inR):
    """Next tag for M_0.  `inR` is what cell 1 delivers leftwards."""
    assert 'c' not in inR, 'no c-pulse can reach M_0'
    if tag == 'S0':
        return 'S1'
    if tag == 'S1':
        return 'S2'
    if tag == 'S2':
        assert 'a' in inR, 'Lemma 1 (k=1): the a returns to M_0 at t=3'
        return 'S3'
    if tag == 'S3':
        return 'p1'
    if tag in ('VP', 'VC'):
        return 'p1'
    if tag == 'p1':
        return 'p2'
    if tag == 'p2':
        assert 'a' not in inR, 'only one a ever reaches M_0'
        return 'VC' if 'b' in inR else 'VP'
    raise AssertionError(tag)


def m0_pend(tag):
    return M0_PEND.get(tag, frozenset())


def delivers(state, d):
    """What `state` hands to its neighbour in direction d on the next step."""
    if state == WALL:
        return frozenset()
    typ, pend = state
    if typ == '0':
        pend = m0_pend(pend)
    return frozenset(s for (s, dd, k) in pend if dd == d and k == 1)


WALL = ('_', ())          # the truncation row; absorbs, delivers nothing


def carry(state):
    typ, pend = state
    return frozenset((s, d, k - 1) for (s, d, k) in pend if k >= 2)


def step_cell(mid, up, dn):
    """One CA step for a field cell (rows 2..): mid from its two neighbours."""
    typ, _ = mid
    out, ntyp = table(typ, delivers(up, 'R'), delivers(dn, 'L'))
    return (ntyp, tuple(sorted(carry(mid) | out)))


def step_half(mid, up):
    """Pass A: carry + everything the row above delivers."""
    typ, _ = mid
    out, ntyp = table(typ, delivers(up, 'R'), frozenset())
    return (ntyp, tuple(sorted(carry(mid) | out)))


def step_rest(inter, dn):
    """Pass B: fold in what the row below delivers."""
    typ, pend = inter
    out, ntyp = table(typ, frozenset(), delivers(dn, 'L'))
    assert ntyp == typ, 'only the row above can turn N into P'
    return (typ, tuple(sorted(set(pend) | out)))


def step_m0(mid, dn):
    return ('0', m0_step(mid[1], delivers(dn, 'L')))


# --------------------------------------------------------------------------
# 2. Run the array and collect every rule the engine will ever need.
# --------------------------------------------------------------------------

def simulate(ncells, tmax, sink=None):
    """Rows 1..ncells are M_0..M_{ncells-1}; below them sits the wall."""
    st = [('0', 'S0')] + [QUIESCENT] * (ncells - 1)
    hits = {}
    for t in range(1, tmax + 1):
        nxt = []
        for i in range(ncells):
            up = st[i - 1] if i > 0 else None
            dn = st[i + 1] if i + 1 < ncells else WALL
            if i == 0:
                new = step_m0(st[i], dn)
                if sink is not None:
                    sink('m0', st[i], dn, new)
            else:
                inter = step_half(st[i], up)
                new = step_rest(inter, dn)
                assert new == step_cell(st[i], up, dn), 'pass split is unsound'
                if sink is not None:
                    sink('A', st[i], up, inter)
                    sink('B', inter, dn, new)
            nxt.append(new)
        st = nxt
        if st[0][1] in ('VP', 'VC'):
            hits[t // 3] = (st[0][1] == 'VP')
    return st, hits


def sieve(n):
    ok = [True] * (n + 1)
    ok[0] = ok[1] = False
    for i in range(2, int(n ** .5) + 1):
        if ok[i]:
            for j in range(i * i, n + 1, i):
                ok[j] = False
    return ok


# Array lengths simulated when the rule table is collected.  The short ones
# cover every position of the truncation wall; the long ones cover interior
# combinations that only appear once many blocks are running.  The table is
# 239 + 179 + 16 rules and stops growing here -- checked stable out to arrays
# of 420 cells, i.e. screens far larger than any terminal.
CELL_RANGE = list(range(3, 61)) + [120, 200]


def collect(cell_range, tmax):
    """Union the rule table over many array truncations."""
    ruleA, ruleB, ruleM = {}, {}, {}

    def sink(kind, anchor, ctx, new):
        d = {'A': ruleA, 'B': ruleB, 'm0': ruleM}[kind]
        key = (anchor, ctx)
        if key in d:
            assert d[key] == new, 'non-deterministic rule at %s' % (key,)
        d[key] = new

    for nc in cell_range:
        simulate(nc, tmax, sink)
    return ruleA, ruleB, ruleM


# --------------------------------------------------------------------------
# 3. Glyphs.  Every distinct state needs its own character -- the engine
#    matches on the character alone -- so combinations get their own glyph
#    too.  Singletons are chosen to read like primes2: '=' mirror, 'v'/'^'
#    the bouncing token, '\' and '/' the fast pulses, digits the countdown
#    of a slow one.
# --------------------------------------------------------------------------

SIG = {
    ('a', 'R', 1): 'aR', ('a', 'L', 1): 'aL', ('a', 'L', 2): 'aL2',
    ('b', 'R', 3): 'bR3', ('b', 'R', 2): 'bR2', ('b', 'R', 1): 'bR1',
    ('b', 'L', 3): 'bL3', ('b', 'L', 2): 'bL2', ('b', 'L', 1): 'bL1',
    ('c', 'R', 2): 'cR2', ('c', 'R', 1): 'cR1', ('c', 'L', 1): 'cL',
}


def key(state):
    if state == WALL:
        return '_'
    typ, pend = state
    if typ == '0':
        return '0:' + pend
    return typ + ':' + ','.join(SIG[s] for s in sorted(pend))


PREFERRED = {
    '_': '_',                 # the wall
    'N:': '.',                # quiescent
    'P:': '=',                # a P-machine: the mirror line
    'N:aR': '\\', 'N:aL': '/',
    'N:cR2': 'v', 'N:cR1': 'V', 'N:cL': '^',
    'N:bL3': '3', 'N:bL2': '2', 'N:bL1': '1',
    'N:bR3': '7', 'N:bR2': '8', 'N:bR1': '9',
    'P:aR': 'X', 'P:cR2': 'W', 'P:cR1': 'U', 'P:cL': 'A',
    'P:bL3': 'E', 'P:bL2': 'F', 'P:bL1': 'G',
    # the number line: a verdict every third column, then two faint fillers
    '0:S0': 'o', '0:S1': 'O', '0:S2': '0', '0:S3': '+',
    '0:p1': "'", '0:p2': '`', '0:VP': '#', '0:VC': '-',
}

HEAD = 'H'          # field head
HEAD0 = 'h'         # M_0 head
ORIGIN = 'Q'        # quiescent, but seeded in column 0 (spawns the heads)

# Chars that carry meaning inside a rule body and so cannot be state glyphs:
# `@` anchor/boundary, `&` ctx, `!` "not ctx", `%` "ctx or ctxrep", `~` space,
# `$` memory restore -- and `*`, which grammar.cpp:524 rewrites to the LHS char
# before the rule is ever matched (a silent one: the body still *looks* right,
# and `zahradnice-check explain` is what shows the substitution).
RESERVED = set(' @&!%~$*')
ALPHABET = [chr(c) for c in range(0x21, 0x7f) if chr(c) not in RESERVED]


class Glyphs:
    def __init__(self):
        self.of = {}            # state key   -> glyph
        self.inters = {}        # state key   -> glyph (pass-A intermediate)
        taken = set(PREFERRED.values()) | {HEAD, HEAD0, ORIGIN}
        self.pool = [c for c in ALPHABET if c not in taken]

    def _fresh(self, what):
        assert self.pool, 'out of glyphs for %s' % what
        return self.pool.pop(0)

    def state(self, st):
        k = key(st)
        if k not in self.of:
            self.of[k] = PREFERRED.get(k) or self._fresh(k)
        return self.of[k]

    def inter(self, st):
        k = key(st)
        if k not in self.inters:
            self.inters[k] = self._fresh('intermediate ' + k)
        return self.inters[k]


# --------------------------------------------------------------------------
# 4. cfg emission (header/body helpers follow gen_primes2.py)
# --------------------------------------------------------------------------

def header(sound='=', lhs='H', trig='T', rep=' ', fore='7', back='8',
           ctx=' ', ctxrep=' ', tail=None):
    """Positional header; the field block is emitted in full whenever a
    score/weight tail follows it (GRAMMAR-pitfalls #20, #24)."""
    h = '=' + sound + lhs + trig + rep + fore + back + ctx + ctxrep
    return h + ' ' + tail if tail is not None else h.rstrip()


def body(lhs_cells, rhs_cells):
    """Horizontal body from two (row, col) -> char maps, offsets relative to
    the anchor.  (0,0) is the anchor on the left and the rep cell on the
    right, so neither map mentions it."""
    lhs_cells, rhs_cells = dict(lhs_cells), dict(rhs_cells)
    assert (0, 0) not in lhs_cells and (0, 0) not in rhs_cells

    rows = [r for r, _ in lhs_cells] + [r for r, _ in rhs_cells] + [0]
    lcols = [c for _, c in lhs_cells] + [0]
    rcols = [c for _, c in rhs_cells] + [0]
    r0, r1 = min(rows), max(rows)
    a = -min(lcols)
    b = a + max(lcols) + 1
    q = b + 1 - min(rcols)
    width = q + max(rcols) + 1

    grid = [[' '] * width for _ in range(r1 - r0 + 1)]
    for (r, c), ch in lhs_cells.items():
        grid[r - r0][a + c] = ch
    for (r, c), ch in rhs_cells.items():
        grid[r - r0][q + c] = ch
    grid[-r0][a] = grid[-r0][b] = grid[-r0][q] = '@'
    # Leading space: a body line opening with '#', '^' or '=' is silently
    # reclassified.  Shifting every line keeps all anchor-relative offsets.
    return '\n'.join((' ' + ''.join(row)).rstrip() for row in grid)


def colour_of(k):
    """Foreground for a state glyph, by what the cell is carrying."""
    if k == 'P:':
        return 'M'                      # the mirror line
    if k.startswith('P'):
        return 'M'
    if k == 'N:':
        return 'D'                      # quiescent field, dimmed away
    if k == '_':
        return 'D'
    if k == '0:VP':
        return 'G'
    if k.startswith('0:'):
        return 'D'
    if 'a' in k.split(':')[1]:
        return '3'                      # a: the partition builder
    if 'c' in k.split(':')[1]:
        return 'G'                      # c: the block's own token
    return '6'                          # b: the verdict carrier


def emit(out):
    add = out.append
    ruleA, ruleB, ruleM = collect(CELL_RANGE, 3 * max(CELL_RANGE) + 4)

    gl = Glyphs()
    # Hand glyphs out in a fixed order so the file is reproducible.
    every = ({s for (s, _) in ruleA} | {s for (_, s) in ruleA}
             | {s for (_, s) in ruleB} | set(ruleB.values())
             | {s for (s, _) in ruleM} | {s for (_, s) in ruleM}
             | set(ruleM.values()) | {WALL, QUIESCENT})
    for s in sorted(every, key=key):
        gl.state(s)
    for it in sorted(set(ruleA.values()), key=key):
        gl.inter(it)

    seen = list(gl.of.values()) + list(gl.inters.values()) + [HEAD, HEAD0,
                                                              ORIGIN]
    assert len(seen) == len(set(seen)), 'glyph collision'
    assert not (set(seen) & RESERVED), 'reserved glyph in use'

    wall = gl.state(WALL)

    # ---- header ----------------------------------------------------------
    add('# Real-time prime generator: a genuine 1-D cellular automaton.')
    add('# Generated by tools/gen_primes5.py -- edit there.')
    add('#')
    add('# P. C. Fischer, "Generation of Primes by a One-Dimensional')
    add('# Real-Time Iterative Array", JACM 12(3) (1965) 388-394.')
    add('#')
    add('# Rows are cells, columns are time.  No signal moves faster than one')
    add('# cell per column -- unlike primes2, whose allocation ray runs')
    add('# backwards in time -- so the verdict for n really does stand in')
    add('# column 3n.  Row 1 is M_0: "#" prime, "," composite.')
    add('#')
    add('#   a  speed 1     builds the partition into blocks')
    add('#   b  speed 1/3   carries "n has a divisor" back to M_0')
    add('#   c  speed 1/2 right, 1 left   oscillates in one block, period 3k')
    add('#')
    add('# Cell k(k+1)/2 turns into a mirror at time (3k^2+k)/2-1; the block')
    add('# it closes has length k and crosses out k^2, k^2+k, k^2+2k, ...')
    add('# Nothing in the rule set mentions a divisor: a block length is')
    add('# matter, exactly as in primes2.')
    add('#')
    add('# Every row carries its own head, so rows advance independently and')
    add('# the wavefront is ragged; a head cannot fire until its three left')
    add('# neighbours are final, which is the whole synchronisation.  Depth is')
    add('# 2 rewrites per column whatever the height, so there is real work')
    add('# to hand to every core; the engine takes them all by default and')
    add('# the screen comes out the same either way.')
    add('#')
    add('# glyphs:')
    for k in sorted(gl.of, key=lambda z: (z[0], z)):
        add('#   %-3s %s' % (gl.of[k], k))
    add('#')
    add('#help Fischer 1965: real time, three columns per number   space=pause  c=restart  q=quit')
    add('#timing T 0')
    add('#control Z pause')
    add('#control C clear')
    add('#control Q return')
    add('#color G 2,BOLD')
    add('#color M 5,BOLD')
    add('#color D 7,DIM')
    add('')

    # ---- seeds (must precede every rule: GRAMMAR-pitfalls #19) -----------
    add('# --- seeds: column 0 is the configuration at t = 0 ---')
    add('^')
    add('^' + ORIGIN + '*l')        # quiescent origin column (spawns heads)
    add('^' + wall + 'l*')          # the array is truncated at the last row
    add('^' + gl.state(('0', 'S0')) + 'ul')
    add('')

    rules = [0]

    def rule(lhs_cells, rhs_cells, **kw):
        add(header(**kw))
        add(body(lhs_cells, rhs_cells))
        add('')
        rules[0] += 1

    # ---- head spawning ---------------------------------------------------
    add('# --- launch one head per row into column 1 ---')
    add('# Anchored on the seeded origin column, so it fires exactly once per')
    add('# row: an interior cell always has a non-empty left neighbour.')
    rule({(0, -1): '~', (0, 1): '~'}, {(0, 1): HEAD},
         lhs=ORIGIN, rep=ORIGIN, fore='D')
    rule({(0, -1): '~', (0, 1): '~'}, {(0, 1): HEAD0},
         lhs=gl.state(('0', 'S0')), rep=gl.state(('0', 'S0')), fore='D')

    # Column 1 is derived from the seeded origin column, which is quiescent
    # everywhere but M_0 yet carries its own glyph (that is what the spawn
    # rule anchors on).  Those few cases get their own rules below rather
    # than a second glyph for every state.

    # ---- pass A: carry + what the row above delivers ---------------------
    add('# --- pass A: fold in this row\'s carry and the row above ---')
    add('# (0,1) must be free: that is what halts a head at the right edge.')
    byA = defaultdict(list)
    for (mid, up), inter in ruleA.items():
        byA[key(mid)].append((mid, up, inter))
    for k in sorted(byA):
        for mid, up, inter in sorted(byA[k], key=lambda z: key(z[1])):
            rule({(-1, -1): gl.state(up), (0, -1): gl.state(mid),
                  (0, 1): '~'}, {},
                 lhs=HEAD, rep=gl.inter(inter), fore=colour_of(key(inter)))
    # column 1: the cell to the left is the seeded origin glyph
    for mid, up, inter in sorted(
            {(QUIESCENT, u, ruleA[(QUIESCENT, u)])
             for u in [QUIESCENT, ('0', 'S0')]}, key=lambda z: key(z[1])):
        rule({(-1, -1): (ORIGIN if up == QUIESCENT else gl.state(up)),
              (0, -1): ORIGIN, (0, 1): '~'}, {},
             lhs=HEAD, rep=gl.inter(inter), fore=colour_of(key(inter)))

    # ---- pass B: fold in what the row below delivers, hand the head on ---
    add('# --- pass B: fold in the row below, hand the head one column on ---')
    byB = defaultdict(list)
    for (inter, dn), new in ruleB.items():
        byB[key(inter)].append((inter, dn, new))
    for k in sorted(byB):
        for inter, dn, new in sorted(byB[k], key=lambda z: key(z[1])):
            rule({(1, -1): gl.state(dn)}, {(0, 1): HEAD},
                 lhs=gl.inter(inter), rep=gl.state(new),
                 fore=colour_of(key(new)))
    # column 1: the cell below-left is the seeded origin glyph
    for inter in sorted({i for i in ruleA.values()}, key=key):
        if (inter, QUIESCENT) in ruleB:
            new = ruleB[(inter, QUIESCENT)]
            rule({(1, -1): ORIGIN}, {(0, 1): HEAD},
                 lhs=gl.inter(inter), rep=gl.state(new),
                 fore=colour_of(key(new)))

    # ---- M_0: one pass, it has no row above ------------------------------
    add('# --- M_0: the number line.  One pass -- it has no row above. ---')
    byM = defaultdict(list)
    for (mid, dn), new in ruleM.items():
        byM[key(mid)].append((mid, dn, new))
    for k in sorted(byM):
        for mid, dn, new in sorted(byM[k], key=lambda z: key(z[1])):
            tail = '1 1' if new == ('0', 'VP') else None
            rule({(0, -1): gl.state(mid), (1, -1): gl.state(dn),
                  (0, 1): '~'}, {(0, 1): HEAD0},
                 lhs=HEAD0, rep=gl.state(new), fore=colour_of(key(new)),
                 tail=tail)
    for dn in [QUIESCENT]:
        mid = ('0', 'S0')
        new = ruleM[(mid, dn)]
        rule({(0, -1): gl.state(mid), (1, -1): ORIGIN, (0, 1): '~'},
             {(0, 1): HEAD0},
             lhs=HEAD0, rep=gl.state(new), fore=colour_of(key(new)))

    # ---- controls --------------------------------------------------------
    add('# --- controls (engine actions need a rule to fire them: #17) ---')
    add('# A head is only ever in ONE of its many states, so anchoring a control')
    add('# solely on head glyphs makes the key work only sometimes. Anchor it on')
    add('# the seeded scenery too -- that is always on screen.')
    for act, k in (('Z', '~'), ('C', 'c'), ('Q', 'q')):
        for cur in (HEAD, ORIGIN):
            add(header(sound=act, lhs=cur, trig=k))
    add(' @@@')
    add('')

    return rules[0], gl


def main():
    # correctness of the reference before anything is emitted
    nmax = 200
    _, hits = simulate(nmax, 3 * nmax + 2)
    truth = sieve(nmax)
    bad = [n for n in range(2, nmax + 1) if hits.get(n) != truth[n]]
    assert not bad, 'reference array disagrees with a real sieve at %s' % bad[:9]

    out = []
    n, gl = emit(out)
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        '..', 'programs', 'primes', '05-fischer.cfg')
    with open(path, 'w') as fh:
        fh.write('\n'.join(out))
    print('wrote %s (%d lines, %d rules, %d state glyphs, %d intermediates)'
          % (os.path.normpath(path), len(out), n, len(gl.of), len(gl.inters)))


if __name__ == '__main__':
    main()
