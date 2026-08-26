#!/usr/bin/env python3
"""Generate programs/primes/01-eratosthenes.cfg -- Sieve of Eratosthenes.

Spatial encoding: the magnitude of a natural number IS its screen column.
Row 1 is the number line, row d (2..DMAX) is the comb of divisor d.

Machine
-------
  >   scan cursor, verdict still open        (non-terminal)
  x   scan cursor, verdict already composite (non-terminal)
  o   dormant divisor marker, sits at (d, d) on the diagonal
  +   head of an activated comb (written where the dormant marker was)
  W   comb walker of row d: always parked on the next multiple of d
  -   comb tooth (a multiple that has been struck out)
  #   prime          (number line)
  .   composite      (number line)
  |   right-edge stop
  A   odometer head, still carrying      (non-terminal)
  B   odometer head, done carrying       (non-terminal)
  _   "this column is labelled" flag

The cursor walks right one column per verdict.  Every rule is anchored on
the cursor, so at most a handful of rules are ever applicable and the
whole derivation is confluent -- no rule lottery decides anything.

  Service_d  walker of d sits directly below the cursor -> strike the
             tooth, hop the walker d columns right, verdict := composite.
  Spawn_d    dormant marker of d sits directly below the cursor (that
             happens exactly at column d) and no walker does -> d is
             prime, so activate its comb at column 2d.
  Kill_d     dormant marker below an already-composite cursor -> d is
             composite, its comb is never built.
  P          nothing below the cursor at all -> prime, advance.
  A          only teeth below the cursor -> composite, advance.

Advance is gated on "all combs clear at this column", so every walker
standing on the current column is necessarily serviced before the cursor
moves on.  That is the whole synchronisation story.

Odometer tape: rows NUM_TOP..NUM_BOT carry the value of each column written
vertically in base BASE, least significant digit at the bottom.  Column c's
label is column c-1's label plus one, so one add-with-carry head walking UP
the column writes it -- the same primitive an unbounded register machine
would need.  The cursor may only advance once the head has raised the flag.

Halting: advance rules require the cell DMAX columns ahead to be empty.
The seeded '|' at the right edge therefore stops the cursor DMAX columns
early, which is exactly the margin a walker needs to never wrap around.
"""

import os

DMAX = 13           # trial divisors 2..DMAX
CUR_ROW = 1         # number line
GUARD = DMAX        # look-ahead used as the halt guard

BASE = 10           # numeral base of the odometer tape
NUMLEN = 3          # digits per column label (BASE**NUMLEN must exceed the
                    # widest screen the sieve can classify)
FLAG_ROW = 14       # 'numeral of this column is finished' flag
NUM_TOP = FLAG_ROW + 1
NUM_BOT = NUM_TOP + NUMLEN - 1

DIGITS = '0123456789abcdefghijklmnopqrstuvwxyz'[:BASE]
DIVISORS = list(range(2, DMAX + 1))

DFLAG = FLAG_ROW - CUR_ROW      # row offsets, seen from the cursor
DTOP = NUM_TOP - CUR_ROW
DBOT = NUM_BOT - CUR_ROW


def dr(d):
    """Row offset of divisor d's comb, seen from the cursor."""
    return d - CUR_ROW


def header(sound='=', lhs='>', trig='T', rep=' ', fore='7', back='8',
           ctx=' ', ctxrep=' ', tail=None):
    """Positional rule header.  Fields are at fixed offsets; a score/weight
    tail must start at offset 10, so the field block is always emitted in
    full when there is a tail (GRAMMAR-pitfalls #20, #24)."""
    h = '=' + sound + lhs + trig + rep + fore + back + ctx + ctxrep
    if tail is not None:
        return h + ' ' + tail
    return h.rstrip()


def body(lhs_cells, rhs_cells):
    """Lay out a horizontal body from two offset->char maps.

    Offsets are (row, col) relative to the cursor.  (0,0) is the anchor on
    the LHS side and the rep cell on the RHS side, so neither map needs to
    mention it.  The LHS region is everything left of the boundary column,
    the RHS region everything right of it -- both regions carry their own
    origin, so equal offsets denote the same screen cell.
    """
    lhs_cells = dict(lhs_cells)
    rhs_cells = dict(rhs_cells)
    assert (0, 0) not in lhs_cells and (0, 0) not in rhs_cells

    rows = [r for r, _ in lhs_cells] + [r for r, _ in rhs_cells] + [0]
    lcols = [c for _, c in lhs_cells] + [0]
    rcols = [c for _, c in rhs_cells] + [0]

    r0, r1 = min(rows), max(rows)
    a = -min(lcols)                 # body column of the LHS anchor '@'
    b = a + max(lcols) + 1          # body column of the boundary '@'
    q = b + 1 - min(rcols)          # body column of the RHS anchor '@'
    width = q + max(rcols) + 1

    grid = [[' '] * width for _ in range(r1 - r0 + 1)]
    for (r, c), ch in lhs_cells.items():
        grid[r - r0][a + c] = ch
    for (r, c), ch in rhs_cells.items():
        grid[r - r0][q + c] = ch
    grid[-r0][a] = '@'
    grid[-r0][b] = '@'
    grid[-r0][q] = '@'

    # Leading space: a body line starting with '#', '^' or '=' would be
    # silently reclassified.  Shifting every line by one column shifts both
    # anchors together, so all offsets survive.
    return '\n'.join((' ' + ''.join(row)).rstrip() for row in grid)


out = []
add = out.append

add('# Sieve of Eratosthenes.  Generated by tools/gen_primes.py -- edit there.')
add('#')
add('# The magnitude of a number is its screen COLUMN.  Row 1 is the number')
add('# line, row d is the comb of divisor d, and the bottom rows label every')
add('# column with its own value in base %d, written vertically.' % BASE)
add('#')
add('#   >  scan cursor, verdict open        o  dormant divisor d, at (d,d)')
add('#   x  scan cursor, verdict composite   +  head of an activated comb')
add('#   W  comb walker, parked on the       -  a struck-out multiple')
add('#      next multiple of its divisor     #  prime      .  composite')
add('#   A  odometer head, carrying          _  column is labelled')
add('#   B  odometer head, copying           |  right-edge stop')
add('#')
add('# A comb is only built for a divisor the sieve has already found prime,')
add('# so rows 4, 6, 8, 9, 10, 12 stay empty -- that is Eratosthenes, not')
add('# trial division.  Divisors run to %d, so verdicts are exact while the' % DMAX)
add('# smallest untested prime factor cannot occur, i.e. for n < %d.' % (
    [q for q in range(DMAX + 1, 99)
     if all(q % k for k in range(2, q))][0] ** 2))
add('#help Eratosthenes: divisors live in the rules   space=pause  c=restart  q=quit')
add('#timing T 10')
add('#control Z pause')
add('#control C clear')
add('#control Q return')
add('#color G 2,BOLD')
add('#color K 0,BOLD')
add('')
add('# --- seeds (must precede every rule: GRAMMAR-pitfalls #19) ---')
add('^')
add('^|ur')          # right-edge stop, on the number line
add('^Sul')          # setup symbol, top left
add('')

add('# --- setup: lay the dormant divisor markers on the diagonal ---')
add('# One rule, because (d,d) is a fixed offset from the seed for every d.')
add(header(lhs='S', rep='~', fore='3'))
add(body({}, {**{(0, 2): '>'},
              **{(dr(d), d): 'o' for d in DIVISORS},
              **{(DFLAG, 2): '_'},
              **{(DBOT - i, 2): DIGITS[(2 // BASE ** i) % BASE]
                 for i in range(NUMLEN)}}))
add('')

for d in DIVISORS:
    add('# --- divisor %d ---' % d)

    # Service: the walker of d is parked on this column, so this column is
    # a multiple of d.  Strike the tooth and hop the walker d to the right.
    add(header(lhs='>', rep='x', fore='6'))
    add(header(lhs='x', rep='x', fore='6'))
    add(body({(dr(d), 0): 'W'},
             {(dr(d), 0): '-', (dr(d), d): 'W'}))
    add('')

    # Spawn: the dormant marker of d is below the cursor -- which happens
    # exactly at column d -- and no walker is, so d has survived the sieve.
    add(header(lhs='>', rep='#', fore='G', tail='1 1'))
    add(body({**{(0, 1): '~', (0, GUARD): '~', (DFLAG, 0): '_', (dr(d), 0): 'o'},
              **{(dr(e), 0): '~' for e in DIVISORS if e != d}},
             {(0, 1): '>', (DBOT, 1): 'A', (dr(d), 0): '+', (dr(d), d): 'W'}))
    add('')

    # Kill: the cursor already knows this column is composite, so d is
    # composite and its comb is never built.
    add(header(lhs='x', fore='4'))
    add(body({(dr(d), 0): 'o'}, {(dr(d), 0): '~'}))
    add('')

add('# --- verdicts ---')
add('# P: no comb reaches this column, and it is past every dormant marker.')
add(header(lhs='>', rep='#', fore='G', tail='1 1'))
add(body({**{(0, 1): '~', (0, GUARD): '~', (DFLAG, 0): '_'},
          **{(dr(e), 0): '~' for e in DIVISORS}},
         {(0, 1): '>', (DBOT, 1): 'A'}))
add('')
add('# A: every comb below is clear or already struck -> composite, advance.')
add('# % matches ctx or ctxrep, i.e. empty-or-tooth.')
add(header(lhs='x', rep='.', fore='4', ctx='~', ctxrep='-'))
add(body({**{(0, 1): '~', (0, GUARD): '~', (DFLAG, 0): '_'},
          **{(dr(e), 0): '%' for e in DIVISORS}},
         {(0, 1): '>', (DBOT, 1): 'A'}))
add('')

add('# --- odometer tape: every column is labelled with its own value ---')
add('# The label of column c is the label of column c-1 plus one, so a single')
add('# add-with-carry head walking UP the column writes it.  A carries, B has')
add('# stopped carrying and only copies.  Base %d, %d digits.' % (BASE, NUMLEN))
for i, v in enumerate(DIGITS):
    if i + 1 < BASE:
        add(header(lhs='A', rep=DIGITS[i + 1], fore='3'))   # carry absorbed
        add(body({(0, -1): v}, {(-1, 0): 'B'}))
    else:
        add(header(lhs='A', rep=DIGITS[0], fore='3'))       # carry propagates
        add(body({(0, -1): v}, {(-1, 0): 'A'}))
    add('')
for v in DIGITS:
    add(header(lhs='B', rep=v, fore='3'))
    add(body({(0, -1): v}, {(-1, 0): 'B'}))
    add('')
add('# Above the most significant digit sits the previous flag: stop there and')
add('# raise this column flag, which is what releases the scan cursor.')
add(header(lhs='A', rep='_', fore='K'))
add(header(lhs='B', rep='_', fore='K'))
add(body({(0, -1): '_'}, {}))
add('')

add('# --- controls (engine actions need a rule to fire them: #17) ---')
for act, key in (('Z', '~'), ('C', 'c'), ('Q', 'q')):
    for cur in '>x':
        add(header(sound=act, lhs=cur, trig=key))
add(' @@@')
add('')

path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                    '..', 'programs', 'primes', '01-eratosthenes.cfg')
with open(path, 'w') as fh:
    fh.write('\n'.join(out))
print('wrote %s (%d lines)' % (os.path.normpath(path), len(out)))
