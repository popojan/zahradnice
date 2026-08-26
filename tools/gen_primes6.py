#!/usr/bin/env python3
"""Generate programs/primes/06-umeo.cfg -- Umeo's eight-state real-time array.

    H. Umeo, K. Miyamoto, Y. Abe, "Real-Time Prime Generators Implemented on
    Small-State Cellular Automata", in A. Adamatzky (ed.), Automata,
    Universality, Computation, Emergence, Complexity and Computation vol. 12,
    Springer 2015, pp. 341-352, doi:10.1007/978-3-319-09039-9_15.  Section
    15.3.2, "Eight-State Real-Time Prime Generator on CA with O(1)-Bit
    Communication"; the rule set is their Fig. 15.7.

Why this and not primes5
------------------------
primes5 is Fischer 1965, and pays his factor of three: his b-pulse crawls at
speed 1/3, which forces a block of length k to have period 3k, so the verdict
for n lands in column 3n.  Umeo's blocks reciprocate at speed 1 -- period 2k
-- and cross out every 2k-th member from k^2 for ODD k only, the even
multiples having been dealt with once by 2.  No time dilation:

    the verdict for n stands in column n.

The partitions are also cheaper.  Fischer marks cell k(k+1)/2 for every k;
Umeo marks cell i^2, and partition S_i (between C_{i^2} and C_{(i+1)^2}) is
the one that handles k = 2i+1.  So the mark for k sits at ((k-1)/2)^2 rather
than k^2/2, and the array needs ~N/4 cells against Fischer's ~N/2.  Together
that is about six times less screen for the same range, in eight states
rather than forty-seven.

Provenance of the table
-----------------------
Fig. 15.7 is nine sub-tables laid three across, with ragged column spacing --
`pdftotext -layout` cannot be trusted on it, so TABLE below was recovered from
word bounding boxes.  Only eight sub-tables carry a centre state, which is how
one knows `*` is the array boundary and not a ninth state.

The recovery is checked, not assumed: SNAPSHOT is the paper's own Fig. 15.8
(50 cells, t = 0..70) and simulating TABLE reproduces all 71 rows exactly --
3550 cell values.  The generator refuses to emit anything if that fails.

Layout on screen (rows are cells, columns are time -- as in primes5)
--------------------------------------------------------------------
  row 0        status line (engine)
  row 1        C_1: the number line.  Its state IS the output, `1` prime and
               `0` composite -- and it is not a special alphabet, it is the
               same eight states the rest of the field uses.
  rows 2..R-2  C_2, C_3, ...
  row R-1      wall.  The right `*` column of Fig. 15.7 is only quiescent
               extension (all three of its defined entries agree with `.`),
               so the wall reads as "the array continues, quiescent, we just
               cannot draw it".
  column 0     the configuration at t = 0: C_1 = `0`, everything else `.`

One rewrite per cell: with nine symbols a single (up, mid, down) rule table is
only ~300 rules, so unlike primes5 there is no need to split the step in two.

Capacity
--------
Exact up to N needs a partition for every prime p <= sqrt(N), and partition
S_i is usable only once the array reaches (i+1)(i+2) -- one full mark spacing
past its own right mark.  With P the largest prime <= sqrt(N):

    cells >= (P+1)(P+3)/4          i.e. h_min ~ N/4

Measured exactly at P = 7, 11, 13, 17, 19, 23 (cells 20, 42, 56, 90, 110,
156).  Beyond that the machine degrades the way primes2 and primes5 do -- a
composite goes uncrossed and is called prime.  Note the range is NOT monotone
in the row count: an array that ends mid-partition does worse than a shorter
one that ends cleanly (27 cells reach 84, where 26 reach 120), because a
half-built partition has nothing to reciprocate against.
"""

import os
from collections import defaultdict

STATES = ['.', '0', '1', 'V', 'R', 'L', 'r', '/']
BOUND = '*'
SYMS = STATES + [BOUND]

# Fig. 15.7, transposed to one row per (left, centre) pair; each row
# lists the new state for right neighbour in the order
#   . 0 1 V R L r / *
# '-' marks a combination the table leaves blank (it never occurs).
TABLE = {
    ('.', '.'): '../..L//.',
    ('0', '.'): '/0--/.---',
    ('1', '.'): '..--.L//-',
    ('V', '.'): '.1--.L//-',
    ('R', '.'): 'RRrRRR-r-',
    ('L', '.'): '../.0--/-',
    ('r', '.'): '----L--r-',
    ('/', '.'): '.-/..L-/-',
    ('.', '0'): '.V0R0r.R-',
    ('0', '0'): '0---1--R-',
    ('1', '0'): 'R-----10-',
    ('V', '0'): '1------r-',
    ('R', '0'): '0-/----V-',
    ('L', '0'): 'VRV----R-',
    ('r', '0'): '0------/-',
    ('/', '0'): '0L-------',
    ('*', '0'): '00011001-',
    ('.', '1'): 'V---V111-',
    ('0', '1'): 'R-RVLLL0-',
    ('1', '1'): '-../L-L--',
    ('V', '1'): '111111.1-',
    ('R', '1'): 'V---V1-1-',
    ('L', '1'): 'V---V111-',
    ('r', '1'): 'V---V1-1-',
    ('/', '1'): 'V-.-V1-1-',
    ('*', '1'): '-10000---',
    ('.', 'V'): 'V0VVV1-1-',
    ('0', 'V'): '-L---L---',
    ('1', 'V'): 'R1--L--1-',
    ('V', 'V'): '-V----1--',
    ('R', 'V'): 'V-0--1-1-',
    ('L', 'V'): 'V----1-1-',
    ('r', 'V'): 'V----1-1-',
    ('/', 'V'): 'V----111-',
    ('.', 'R'): '..LL.../.',
    ('0', 'R'): 'RV--V1-1-',
    ('1', 'R'): '..LL0-./-',
    ('V', 'R'): '..--L----',
    ('R', 'R'): 'Rr--r--VR',
    ('L', 'R'): '-LLL/----',
    ('r', 'R'): '-rLL.----',
    ('/', 'R'): '.-LLr--/-',
    ('.', 'L'): '../.L.-/-',
    ('0', 'L'): 'R---Rrr--',
    ('1', 'L'): 'RRrRR-r--',
    ('V', 'L'): 'RRrR-R-r-',
    ('R', 'L'): '-LrR--V--',
    ('L', 'L'): '-VrRR----',
    ('r', 'L'): '--rR-----',
    ('/', 'L'): '..-.-.---',
    ('.', 'r'): '-.L----/-',
    ('0', 'r'): '-R--V11--',
    ('1', 'r'): '.0LLR--/-',
    ('V', 'r'): '-V----R--',
    ('R', 'r'): '0R-------',
    ('L', 'r'): '-VLL-----',
    ('r', 'r'): '-VLLr----',
    ('/', 'r'): '--L----/-',
    ('.', '/'): '.L/..L//-',
    ('0', '/'): '0---V----',
    ('1', '/'): '.---.L-/-',
    ('V', '/'): '.1--.L//-',
    ('R', '/'): 'R0rRr--r-',
    ('L', '/'): '.-/.---/-',
    ('r', '/'): 'R--R-----',
    ('/', '/'): '.-/..L-/-',
}

# Fig. 15.8: the paper's own snapshots, 50 cells, t = 0..70.
SNAPSHOT = [
    '0.................................................',
    '0/................................................',
    '10................................................',
    '1R/...............................................',
    '0/R...............................................',
    '1V.R..............................................',
    '0R..R.............................................',
    '1RR..R............................................',
    '00RR..R...........................................',
    '01VRR..R..........................................',
    '0VLLRR..R.........................................',
    '1LRR/RR..R........................................',
    '0R/VrrRR..R.......................................',
    '11R1Rr.RR..R......................................',
    '0LLV.0L.RR..R.....................................',
    '0rRV1rR0.RR..R....................................',
    '0VL0.Rr0/.RR..R...................................',
    '1LRV/.R/0..RR..R..................................',
    '0RL1../00/..RR..R.................................',
    '11rV./LLR0...RR..R................................',
    '0LLV/L.RL0/...RR..R...............................',
    '0rR1L.0.LR0....RR..R..............................',
    '0VL1R...LL0/....RR..R.............................',
    '1LrV.R.L.VR0.....RR..R............................',
    '0rLV..R..V.0/.....RR..R...........................',
    '01RV...R.V1R0......RR..R..........................',
    '0LLV....RV1.0/......RR..R.........................',
    '0rRV....L01.R0.......RR..R........................',
    '0VLV...L.VR..0/.......RR..R.......................',
    '1LRV..L..V.R.R0........RR..R......................',
    '0RLV.L...V..R.0/........RR..R.....................',
    '11RVL....V...RR0.........RR..R....................',
    '0LL1R....V....r0/.........RR..R...................',
    '0rrV.R...V..././0..........RR..R..................',
    '01LV..R..V.././L0/..........RR..R.................',
    '0LRV...R.V././L.R0...........RR..R................',
    '0RLV....RV/./L.0.0/...........RR..R...............',
    '11RV....L1./L...0R0............RR..R..............',
    '0LLV...L/V/L....0V0/............RR..R.............',
    '0rRV..L/.1L.....RLr0.............RR..R............',
    '0VLV.L/./1R......VV0/.............RR..R...........',
    '1LRVL/.//V.R.....VVr0..............RR..R..........',
    '0RL1r.//.V..R....V1V0/..............RR..R.........',
    '11r1.r/..V...R...V11r0...............RR..R........',
    '0LLV//R..V....R..V1L00/...............RR..R.......',
    '0rR1/..R.V.....R.V1RRR0................RR..R......',
    '0VL1....RV......RV10rr0/................RR..R.....',
    '1LrV....LV......L0111V/0.................RR..R....',
    '0rLV...L.V.....L.VR./110/.................RR..R...',
    '01RV..L..V....L..V.r/..00..................RR..R..',
    '0LLV.L...V...L...V//R..V0/..................RR..R.',
    '0rRVL....V..L....1/..R.0r0...................RR..R',
    '0VL1R....V.L..../1....R.R0/...................RR..',
    '1LrV.R...VL....//V.....R.V0....................RR.',
    '0rLV..R..1R...//.V......R01/....................RR',
    '01RV...R/V.R.//..V......./0......................R',
    '0LLV.../RV..r/...V....../L0/......................',
    '0rRV../.LV.//R...V...../L.R0......................',
    '0VLV./.L.V//..R..V..../L.0.0/.....................',
    '1LRV/.L..1/....R.V.../L...0R0.....................',
    '0RL1.L../1......RV../L....0V0/....................',
    '11rVL..//V......LV./L.....RLr0....................',
    '0LL1R.//.V.....L.V/L.......VV0/...................',
    '0rrV.r/..V....L..1L........VVr0...................',
    '01LV//R..V...L../1R........V1V0/..................',
    '0LR1/..R.V..L..//V.R.......V11r0..................',
    '0RL1....RV.L..//.V..R......V1L00/.................',
    '11rV....LVL..//..V...R.....V1RRR0.................',
    '0LLV...L.1R.//...V....R....V10rr0/................',
    '0rRV..L./V.r/....V.....R...V111V/0................',
    '0VLV.L./.V//R....V......R..V1./110/...............',
]


# --------------------------------------------------------------------------
# The array
# --------------------------------------------------------------------------

DELTA = {}
for (_l, _c), _row in TABLE.items():
    for _r, _v in zip(SYMS, _row):
        if _v != '-':
            DELTA[(_l, _c, _r)] = _v


# Cutting the array short drives it into (left, centre, right) combinations
# the paper's table leaves blank -- they cannot arise in the semi-infinite
# array it was designed for.  Undefined means the signal dies: the truncation
# absorbs rather than reflects, which is what keeps the degradation graceful
# (a composite goes uncrossed and is called prime, instead of a real prime
# being struck by a partition that has nothing to reciprocate against).
DEAD = '.'


def step(cfg, seen=None):
    """One CA step.  Beyond the last cell the array is quiescent."""
    out = []
    for i, c in enumerate(cfg):
        left = cfg[i - 1] if i > 0 else BOUND
        right = cfg[i + 1] if i + 1 < len(cfg) else '.'
        v = DELTA.get((left, c, right), DEAD)
        if seen is not None:
            seen[(left, c, right)] = v
        out.append(v)
    return out


def run(ncells, tmax, seen=None):
    cfg = ['0'] + ['.'] * (ncells - 1)
    hist = [list(cfg)]
    for _ in range(tmax):
        cfg = step(cfg, seen)
        hist.append(list(cfg))
    return hist


# Array lengths simulated when the rule table is collected: every truncation
# a terminal could impose, plus a long one for the interior combinations that
# only show up once many partitions are running.
CELL_RANGE = list(range(2, 81)) + [120, 200]


def collect():
    """Every triple the engine can actually meet, over all truncations."""
    seen = {}
    for nc in CELL_RANGE:
        run(nc, 3 * nc + 40, seen)
    return seen


def sieve(n):
    ok = [True] * (n + 1)
    ok[0] = ok[1] = False
    for i in range(2, int(n ** .5) + 1):
        if ok[i]:
            for j in range(i * i, n + 1, i):
                ok[j] = False
    return ok


def self_check():
    """Refuse to emit unless the recovered table reproduces the paper."""
    n = len(SNAPSHOT[0])
    hist = run(n, len(SNAPSHOT) - 1)
    for t, want in enumerate(SNAPSHOT):
        got = ''.join(hist[t])
        assert got == want, 'Fig. 15.8 row t=%d:\n  want %s\n  got  %s' % (
            t, want, got)
    # ... and that C_1 really is the characteristic sequence of the primes
    nmax, cells = 120, 26
    hist = run(cells, nmax)
    truth = sieve(nmax)
    for t in range(2, nmax + 1):
        assert (hist[t][0] == '1') == truth[t], 'wrong verdict at n=%d' % t
    return len(SNAPSHOT), n


# --------------------------------------------------------------------------
# cfg emission (header/body helpers follow gen_primes2.py)
# --------------------------------------------------------------------------

WALL = '_'          # the truncation row
HEAD = 'H'          # field head
HEAD1 = 'h'         # head for C_1, which has no row above
ORIGIN = 'Q'        # quiescent, seeded in column 0 (spawns the heads)
ORIGIN1 = 'q'       # C_1's t=0 state, likewise seeded

COLOUR = {'.': 'D', '0': 'D', '1': 'G', 'V': 'M',
          'R': '3', 'L': '6', 'r': '6', '/': '3'}


def header(sound='=', lhs=HEAD, trig='T', rep=' ', fore='7', back='8',
           ctx=' ', ctxrep=' ', tail=None):
    h = '=' + sound + lhs + trig + rep + fore + back + ctx + ctxrep
    return h + ' ' + tail if tail is not None else h.rstrip()


def body(lhs_cells, rhs_cells):
    lhs_cells, rhs_cells = dict(lhs_cells), dict(rhs_cells)
    assert (0, 0) not in lhs_cells and (0, 0) not in rhs_cells
    rows = [r for r, _ in lhs_cells] + [r for r, _ in rhs_cells] + [0]
    lcols = [c for _, c in lhs_cells] + [0]
    rcols = [c for _, c in rhs_cells] + [0]
    r0, r1 = min(rows), max(rows)
    a = -min(lcols)
    b = a + max(lcols) + 1
    q = b + 1 - min(rcols)
    grid = [[' '] * (q + max(rcols) + 1) for _ in range(r1 - r0 + 1)]
    for (r, c), ch in lhs_cells.items():
        grid[r - r0][a + c] = ch
    for (r, c), ch in rhs_cells.items():
        grid[r - r0][q + c] = ch
    grid[-r0][a] = grid[-r0][b] = grid[-r0][q] = '@'
    # Leading space: a body line opening with '#', '^' or '=' is silently
    # reclassified.  Shifting every line keeps all anchor-relative offsets.
    return '\n'.join((' ' + ''.join(row)).rstrip() for row in grid)


def emit(out):
    add = out.append
    n_rules = [0]

    def rule(lhs_cells, rhs_cells, **kw):
        add(header(**kw))
        add(body(lhs_cells, rhs_cells))
        add('')
        n_rules[0] += 1

    add('# Real-time prime generator in eight states -- one column per number.')
    add('# Generated by tools/gen_primes6.py -- edit there.')
    add('#')
    add('# H. Umeo, K. Miyamoto, Y. Abe, "Real-Time Prime Generators')
    add('# Implemented on Small-State Cellular Automata", in Automata,')
    add('# Universality, Computation, ECC vol. 12, Springer 2015, 341-352.')
    add('# The rule set is their Fig. 15.7; this file is that table.')
    add('#')
    add('# Rows are cells, columns are time.  Row 1 is C_1 and its state IS')
    add('# the answer: "1" when the column number is prime, "0" when it is')
    add('# not.  Unlike primes5 there is no time dilation and no separate')
    add('# alphabet for the number line -- eight states do everything.')
    add('#')
    add('# A mark stands on cell i*i; the partition between i*i and (i+1)^2')
    add('# reciprocates with period 2k for k = 2i+1, and crosses out every')
    add('# 2k-th number from k^2 on.  Odd k only: the even multiples were')
    add('# already struck by 2.  No divisor appears anywhere in the rules.')
    add('#')
    add('# states:')
    add('#   .  quiescent      0 1  a verdict at C_1 / working states')
    add('#   V  R  L  r  /     signals building and running the partitions')
    add('#   _  wall: the array is truncated here')
    add('#')
    add('#help Umeo 2015: real time, eight states, one column each   space=pause  c=restart  q=quit')
    add('#timing T 0')
    add('#control Z pause')
    add('#control C clear')
    add('#control Q return')
    add('#color G 2,BOLD')
    add('#color M 5,BOLD')
    add('#color D 7,DIM')
    add('')
    add('# --- seeds: column 0 is the configuration at t = 0 ---')
    add('^')
    add('^' + ORIGIN + '*l')
    add('^' + WALL + 'l*')
    add('^' + ORIGIN1 + 'ul')
    add('')

    add('# --- launch one head per row into column 1 ---')
    add('# Anchored on the seeded origin column, so it fires once per row: an')
    add('# interior cell always has a non-empty left neighbour.')
    rule({(0, -1): '~', (0, 1): '~'}, {(0, 1): HEAD},
         lhs=ORIGIN, rep=ORIGIN, fore='D')
    rule({(0, -1): '~', (0, 1): '~'}, {(0, 1): HEAD1},
         lhs=ORIGIN1, rep=ORIGIN1, fore='D')

    # A cell reads its three left neighbours; `(0,1)` must be free, which is
    # what halts a head against the right edge.
    def field(up, mid, dn, new, **kw):
        rule({(-1, -1): up, (0, -1): mid, (1, -1): dn, (0, 1): '~'},
             {(0, 1): HEAD}, lhs=HEAD, rep=new, fore=COLOUR[new], **kw)

    def line1(mid, dn, new):
        tail = '1 1' if new == '1' else None
        rule({(0, -1): mid, (1, -1): dn, (0, 1): '~'}, {(0, 1): HEAD1},
             lhs=HEAD1, rep=new, fore=COLOUR[new], tail=tail)

    # Fig. 15.7, plus the combinations only a truncated array reaches (those
    # resolve to DEAD).  Ordered so the file is reproducible.
    rules = dict(DELTA)
    rules.update(collect())
    keys = sorted((k for k in rules if k[2] != BOUND),
                  key=lambda k: tuple(SYMS.index(x) for x in (k[1], k[0], k[2])))

    add('# --- the array: one rule per (above, self, below) --------------')
    add('# This block IS Fig. 15.7, plus the combinations only a truncated')
    add('# array can reach, which resolve to a dead signal.  `_` repeats the')
    add('# `.` case: past the wall the array is quiescent.')
    for (up, mid, dn) in keys:
        if up == BOUND:
            continue                       # that is C_1's row, emitted below
        field(up, mid, dn, rules[(up, mid, dn)])
        if dn == '.':
            field(up, mid, WALL, rules[(up, mid, dn)])

    add('# --- C_1: the number line.  No row above it, so `*` is its left. ---')
    for (up, mid, dn) in keys:
        if up != BOUND:
            continue
        line1(mid, dn, rules[(up, mid, dn)])
        if dn == '.':
            line1(mid, WALL, rules[(up, mid, dn)])

    add('# --- column 1 reads the seeded origin column ---')
    q = DELTA[('.', '.', '.')]
    field(ORIGIN, ORIGIN, ORIGIN, q)
    field(ORIGIN, ORIGIN, WALL, q)
    field(ORIGIN1, ORIGIN, ORIGIN, DELTA[('0', '.', '.')])
    field(ORIGIN1, ORIGIN, WALL, DELTA[('0', '.', '.')])
    line1(ORIGIN1, ORIGIN, DELTA[(BOUND, '0', '.')])
    line1(ORIGIN1, WALL, DELTA[(BOUND, '0', '.')])

    add('# --- controls (engine actions need a rule to fire them: #17) ---')
    add('# A head is only ever in ONE of its many states, so anchoring a control')
    add('# solely on head glyphs makes the key work only sometimes. Anchor it on')
    add('# the seeded scenery too -- that is always on screen.')
    for act, k in (('Z', '~'), ('C', 'c'), ('Q', 'q')):
        for cur in (HEAD, ORIGIN):
            add(header(sound=act, lhs=cur, trig=k))
    add(' @@@')
    add('')
    return n_rules[0]


def main():
    rows, cells = self_check()
    out = []
    n = emit(out)
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        '..', 'programs', 'primes', '06-umeo.cfg')
    with open(path, 'w') as fh:
        fh.write('\n'.join(out))
    print('checked %d snapshot rows x %d cells against Fig. 15.8' % (rows, cells))
    print('wrote %s (%d lines, %d rules, %d states)'
          % (os.path.normpath(path), len(out), n, len(STATES)))


if __name__ == '__main__':
    main()
