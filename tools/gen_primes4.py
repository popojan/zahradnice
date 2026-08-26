#!/usr/bin/env python3
"""Generate programs/primes/04-packed.cfg -- packed static counter sieve.

The line so far:
  primes   divisors hardcoded, magnitude = column
  primes2  divisor = height of a band, unary, sum(p+1) rows
  primes3  divisor = a numeral, one row per divisor, records slide with a scan
  primes4  divisor = a numeral, records PACKED and STATIC, a head walks to them

Why packed and static
---------------------
A terminal is wider than tall.  One record per row wastes most of a wide screen
and caps you near 46 divisors -- exact only below 44521, which is under what
the clock allows.  Packing records along rows at a fixed pitch lifts that to
hundreds of divisors in a handful of rows.

Packing rules out sliding: you cannot shift 400 records per candidate.  So the
records sit still and one head visits them, which is strictly cheaper anyway --
the divisor half never changes, and primes3 copied it every step for nothing.
With a static record the entire borrow chain is a SINGLE rule (one per position
of the lowest non-zero digit), so a divisor costs one rule application per
candidate.

Layout (slot pitch W = 2*NDIG+2, declared as #grid so column wrap is aligned)
----------------------------------------------------------------------------
  row 1   home slot:  H nnn f ppp    candidate, verdict, last prime found
  row 2   scratch lane for the candidate register head
  row 3+  record rows: slot 0 is a header, slots 1.. are records
          record:  * ddd : kkk       divisor, candidates until its multiple

  header  F  first record row     +  row holds records     -  row still empty

A pass steps slot to slot (+W); stepping off the last slot wraps onto the row's
own header, which sends the head down a row.  An empty row costs one step.
Arriving home writes the verdict, and on a prime copies the candidate into the
"last prime" field and gives it a record.

Allocation keeps the insertion point fixed rather than transporting digits: it
pushes every record one slot along, then writes the new record into slot 1 of
row 3 -- a fixed offset from the register, so nothing has to be carried.

Range: divisors and candidates < BASE**NDIG.  Only primes below
BASE**ceil(NDIG/2) are given a record -- every composite in range has a prime
factor at most its own square root, so the rest would cost per candidate and
cross out nothing.  That bound is a digit-width test, not a count, so it needs
no counter: "the top NDIG-HALF digits of the candidate are zero".  Without it
a taller screen is a linearly SLOWER one (measured: 3.2x at 24x80).

python3 tools/gen_primes4.py [BASE [NDIG]]
"""

import os
import sys

BASE = int(sys.argv[1]) if len(sys.argv) > 1 else 10
NDIG = int(sys.argv[2]) if len(sys.argv) > 2 else 4
assert 2 <= BASE <= 36 and NDIG >= 1   # head glyphs are punctuation,
# digits are 0-9a-z; past 36 the alphabet would need remapping too

_ALPHABET = ('0123456789abcdefghijklmnopqrstuvwxyz'
             'ABCDEFGHIJKLMNOPQRSTUVWXYZ')
if BASE > len(_ALPHABET):
    _ALPHABET += ''.join(chr(0x100 + i) for i in range(BASE - len(_ALPHABET)))
DIG = _ALPHABET[:BASE]
TOP = DIG[-1]

W = 2 * NDIG + 2                 # slot pitch
SEPX = NDIG + 1                  # ':' inside a record / verdict flag at home
DLO = NDIG                       # least significant divisor digit
KLO = 2 * NDIG + 1               # least significant counter digit
K2D = -(NDIG + 1)                # counter cell -> matching divisor cell

MARK, SEP = '[', ':'      # NOT '*': a body '*' is rewritten to the rule's lhs
HOME, FIRST, USED, FREE = 'H', 'F', '+', '-'
PRIME, COMP = '#', '.'

# absolute anchors
REG = [(1, DLO - i) for i in range(NDIG)]      # register digit i (0 = lsb)
LAST = [(1, KLO - i) for i in range(NDIG)]     # last-prime digit i
SLOT1 = W                                      # column of row 3's first record


def off(frm, to):
    return (to[0] - frm[0], to[1] - frm[1])


def header(sound='=', lhs='>', trig='T', rep=' ', fore='7', back='8',
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
    return '\n'.join((' ' + ''.join(row)).rstrip() for row in grid)


out = []
add = out.append


def rule(lhs_cells, rhs_cells, **kw):
    add(header(**kw))
    add(body(lhs_cells, rhs_cells))
    add('')


add('# Packed static counter sieve. Generated by tools/gen_primes4.py')
add('# (BASE=%d, NDIG=%d, slot pitch %d) -- edit there.' % (BASE, NDIG, W))
add('#')
add('# row 1  H nnn f ppp   candidate, verdict, last prime found')
add('# row 3+ slot 0 is a row header, then records:  [ ddd : kkk')
add('#        ddd = divisor, kkk = candidates left until its next multiple')
add('#')
add('# One head walks slot to slot; a record costs ONE rule application,')
add('# because a static counter lets the whole borrow chain be a single rule.')
add('# kkk = 0 means "multiple": the row reloads kkk := ddd-1 and the pass is')
add('# marked composite. Arriving home prints the verdict and, on a prime,')
add('# pushes every record one slot along so the new one lands at a fixed spot.')
add('#')
add('#   > <  walking a row (< = multiple seen)   { }  descending a row')
add('#   ? ,  reload: borrow / copy               A )  candidate + 1')
add('#   "    copy candidate to last-prime field  Y    lay out row headers')
add("#   ; '  find the free slot                  _ |  push records one slot")
add('#   ] ^ `  write the new record: divisor half / counter half')
add('#help Packed: records stand still, a head visits them   space=pause  c=restart  q=quit')
add('#timing T 0')
add('#grid %d 1' % W)
add('#transient ><{};(')
add('#control Z pause')
add('#control C clear')
add('#control Q return')
add('#color G 2,BOLD')
add('#color N 6')
add('#color D 4')
add('')
add('# --- seeds ---')
add('^')
add('^Sul')
add('')

# --- setup ----------------------------------------------------------------
add('# --- setup: home slot, row 3 header, then lay out the other headers ---')
S = (1, 0)
setup = {off(S, (1, SEPX)): COMP}
for i in range(NDIG):
    setup[off(S, REG[i])] = DIG[1] if i == 0 else DIG[0]
    setup[off(S, LAST[i])] = DIG[0]
for c in range(W):
    setup[off(S, (3, c))] = FIRST
setup[off(S, (4, 0))] = 'Y'
rule({}, setup, lhs='S', rep=HOME, fore='G')

add('# every remaining row gets a FREE header; then start the machine')
spread = {(0, c): FREE for c in range(1, W)}
rule({(1, 0): HOME}, {**spread, (2, DLO): 'A'}, lhs='Y', rep=FREE, fore='D')
rule({(1, 0): '~'}, {**spread, (1, 0): 'Y'}, lhs='Y', rep=FREE, fore='D')

# --- candidate register ---------------------------------------------------
add('# --- candidate + 1: the head sits in row 2 and rewrites the digit')
add('# above it, so it can read and write the same cell ---')
for v in range(BASE):
    if v + 1 < BASE:
        rule({(-1, 0): DIG[v]}, {(-1, 0): DIG[v + 1], (0, -1): ')'},
             lhs='A', rep='~', fore='G')
    else:
        rule({(-1, 0): DIG[v]}, {(-1, 0): DIG[0], (0, -1): 'A'},
             lhs='A', rep='~', fore='G')
add('# walk out to column 0 and launch the pass at the first record row.')
add('# A still carrying at column 0 means the register overflowed: halt,')
add('# rather than wrap and quietly start lying.')
rule({(-1, 0): HOME}, {(1, 0): '{'}, lhs=')', rep='~')
rule({(-1, 0): HOME}, {}, lhs='A', rep='~')
rule({(-1, 0): '!'}, {(0, -1): ')'}, lhs=')', rep='~', ctx=HOME)

# --- walking head ---------------------------------------------------------
add('# --- walking a row ---')
for s, sv in (('>', '{'), ('<', '}')):
    add('# decrement, by position of the lowest non-zero counter digit')
    for j in range(NDIG):
        for v in range(1, BASE):
            lo = {(0, KLO - i): DIG[0] for i in range(j)}
            lo[(0, KLO - j)] = DIG[v]
            hi = {(0, KLO - i): TOP for i in range(j)}
            hi[(0, KLO - j)] = DIG[v - 1]
            hi[(0, W)] = s
            rule(lo, hi, lhs=s, rep='$', fore='N')
    add('# counter already zero: a multiple -- reload it from the divisor')
    rule({(0, KLO - i): DIG[0] for i in range(NDIG)}, {(0, KLO): '?'},
         lhs=s, rep='$')
    add('# free slot: step over it.  header: hand over to the descender')
    rule({(0, KLO): '~'}, {(0, W): s}, lhs=s, rep='$')
    for hd in (USED, FIRST):
        rule({(0, 1): hd}, {(1, 0): sv}, lhs=s, rep='$')

add('# --- descending: skip empty rows, enter used ones, stop at home ---')
for s, sv in (('>', '{'), ('<', '}')):
    rule({(0, 1): FREE}, {(1, 0): sv}, lhs=sv, rep='$')
    for hd in (USED, FIRST):
        rule({(0, 1): hd}, {(0, W): s}, lhs=sv, rep='$')

# --- reload ---------------------------------------------------------------
add('# --- reload kkk := ddd - 1 (divisor sits at a fixed offset) ---')
for v in range(BASE):
    dec = DIG[v - 1] if v > 0 else TOP
    rule({(0, K2D): DIG[v], (0, -1): '!'}, {(0, -1): ',' if v else '?'},
         lhs='?', rep=dec, fore='G', ctx=SEP)
    rule({(0, K2D): DIG[v], (0, -1): SEP}, {(0, NDIG): '<'},
         lhs='?', rep=dec, fore='G')
    rule({(0, K2D): DIG[v], (0, -1): '!'}, {(0, -1): ','},
         lhs=',', rep=DIG[v], fore='G', ctx=SEP)
    rule({(0, K2D): DIG[v], (0, -1): SEP}, {(0, NDIG): '<'},
         lhs=',', rep=DIG[v], fore='G')

# --- verdict --------------------------------------------------------------
add('# --- home: the verdict flag tells the descender it has come round ---')
rule({(0, SEPX): '%'}, {(0, SEPX): COMP, (1, DLO): 'A'}, lhs='}', rep='$',
     fore='D', ctx=PRIME, ctxrep=COMP)
add('# survived every divisor: print it, count it, then give it a record')
rule({(0, SEPX): '%'}, {(0, SEPX): PRIME, (0, KLO): '"'}, lhs='{', rep='$',
     fore='G', ctx=PRIME, ctxrep=COMP, tail='1 1')

add('# copy the candidate into the "last prime" field, then decide')
P_END = (1, KLO - (NDIG - 1))
for v in range(BASE):
    rule({(0, K2D): DIG[v], (0, -1): '!'}, {(0, -1): '"'},
         lhs='"', rep=DIG[v], fore='G', ctx=PRIME)

# --- who gets a record ----------------------------------------------------
# Only primes p <= sqrt(BASE**NDIG) can cross out anything in range: every
# composite below BASE**NDIG has a prime factor at most its own square root.
# Cost is linear in the record count, so handing a record to every prime
# makes a TALLER screen slower -- 56.5 events/candidate at 27 records against
# 216.6 at 100, for verdicts that were already exact at 27.
#
# The test needs no counter and no comparator: p < BASE**HALF is exactly
# "the top NDIG-HALF digits of the candidate are zero", and the copy walk
# ends at P_END, a fixed offset from every register digit.
HALF = (NDIG + 1) // 2         # ceil, so odd NDIG keeps a few spare records
HIGH = [i for i in range(HALF, NDIG)]          # digits that must all be zero
MSB = NDIG - 1
REG_AT = {i: (0, -i - 2) for i in range(NDIG)}  # register digit i, from P_END
GO_ALLOC = {off(P_END, (3, SLOT1)): ';'}
GO_NEXT = {off(P_END, (2, DLO)): 'A'}

add('# --- small enough to matter (top %d of %d digits zero): allocate ---'
    % (len(HIGH), NDIG))
for v in range(BASE):
    if MSB in HIGH and v != 0:
        continue                                  # handled by the skip rules
    keep = {REG_AT[i]: DIG[0] for i in HIGH if i != MSB}
    rule({(0, K2D): DIG[v], (0, -1): '%', **keep}, GO_ALLOC,
         lhs='"', rep=DIG[v], fore='G', ctx=PRIME, ctxrep=COMP)

if HIGH:
    add('# --- too big to divide anything in range: print it, skip the')
    add('# record, straight on to the next candidate. Cases are split by the')
    add('# LOWEST non-zero high digit, so exactly one of them ever matches.')
    for v in range(1, BASE):                      # top digit itself non-zero
        rule({(0, K2D): DIG[v], (0, -1): '%'}, GO_NEXT,
             lhs='"', rep=DIG[v], fore='G', ctx=PRIME, ctxrep=COMP)
    for j in HIGH:
        if j == MSB:
            continue
        for w in range(1, BASE):
            keep = {REG_AT[i]: DIG[0] for i in HIGH if i < j}
            keep[REG_AT[j]] = DIG[w]
            rule({(0, K2D): DIG[0], (0, -1): '%', **keep}, GO_NEXT,
                 lhs='"', rep=DIG[0], fore='G', ctx=PRIME, ctxrep=COMP)

# --- allocation -----------------------------------------------------------
add('# --- find the first free slot (same walk, changing nothing) ---')
for v in range(BASE):
    rule({(0, KLO): DIG[v]}, {(0, W): ';'}, lhs=';', rep='$')
rule({(0, KLO): '~'}, {}, lhs=';', rep='_')
for hd in (USED, FIRST, FREE):
    rule({(0, 1): hd}, {(1, 0): '('}, lhs=';', rep='$')
    rule({(0, 1): hd}, {(0, W): ';'}, lhs='(', rep='$')
add('# came all the way round to home: the area is full, no more divisors')
rule({(0, SEPX): '%'}, {(1, DLO): 'A'}, lhs='(', rep='$',
     ctx=PRIME, ctxrep=COMP)

add('# --- push every record one slot along, walking backwards ---')
add('# c copies from the slot to the left, e from the last slot of the row')
add('# above -- which is where -W wraps to when you stand on slot 1.')
rule({(0, -W): MARK}, {(0, KLO): '|'}, lhs='_', rep='~')
add('# reached the very first record slot: build the new record here')
rule({(0, -W): FIRST}, {(0, DLO): ']'}, lhs='_', rep=MARK, fore='N')
add('# slot 1: the previous record is the row above; promote an empty header')
rule({(0, -W + 1): USED}, {(0, KLO): '\\'}, lhs='_', rep='~')
rule({(0, -W + 1): FREE},
     {**{(0, -W + c): USED for c in range(W)}, (0, KLO): '\\'},
     lhs='_', rep='~', fore='D')

add('# copy one slot from its predecessor, cell by cell, right to left')
for src, hd, back in ((-W, '|', (0, -W)), (-2 * W, '\\', (-1, -2 * W))):
    for v in range(BASE):
        rule({(0, src) if hd == '|' else (-1, src): DIG[v]}, {(0, -1): hd},
             lhs=hd, rep=DIG[v], fore='N')
    rule({(0, src) if hd == '|' else (-1, src): SEP}, {(0, -1): hd},
         lhs=hd, rep=SEP, fore='D')
    rule({(0, src) if hd == '|' else (-1, src): MARK}, {back: '_'},
         lhs=hd, rep=MARK, fore='N')

add('# --- new record: ddd := candidate, kkk := candidate - 1 ---')
add('# Row 3 slot 1 is a fixed offset from the register, so nothing moves.')
N_AT = [(3, SLOT1 + DLO - i) for i in range(NDIG)]
M_AT = [(3, SLOT1 + KLO - i) for i in range(NDIG)]
for v in range(BASE):
    rule({off(N_AT[0], REG[0]): DIG[v], (0, -1): '!'}, {(0, -1): ']'},
         lhs=']', rep=DIG[v], fore='N', ctx=MARK)
    rule({off(N_AT[0], REG[0]): DIG[v], (0, -1): MARK},
         {(0, NDIG): SEP, (0, KLO - (DLO - NDIG + 1)): '^'},
         lhs=']', rep=DIG[v], fore='N')
    dec = DIG[v - 1] if v > 0 else TOP
    rule({off(M_AT[0], REG[0]): DIG[v], (0, -1): '!'},
         {(0, -1): '`' if v else '^'}, lhs='^', rep=dec, fore='N', ctx=SEP)
    rule({off(M_AT[0], REG[0]): DIG[v], (0, -1): SEP},
         {off((3, SLOT1 + SEPX + 1), (2, DLO)): 'A'},
         lhs='^', rep=dec, fore='N')
    rule({off(M_AT[0], REG[0]): DIG[v], (0, -1): '!'}, {(0, -1): '`'},
         lhs='`', rep=DIG[v], fore='N', ctx=SEP)
    rule({off(M_AT[0], REG[0]): DIG[v], (0, -1): SEP},
         {off((3, SLOT1 + SEPX + 1), (2, DLO)): 'A'},
         lhs='`', rep=DIG[v], fore='N')

add('# --- controls (engine actions need a rule to fire them: #17) ---')
for act, key in (('Z', '~'), ('C', '|'), ('Q', 'q')):
    for cur in ('>', '<'):
        add(header(sound=act, lhs=cur, trig=key))
add(' @@@')
add('')

path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                    '..', 'programs', 'primes', '04-packed.cfg')
with open(path, 'w') as fh:
    fh.write('\n'.join(out))
print('wrote %s  base=%d digits=%d pitch=%d  %d rules'
      % (os.path.normpath(path), BASE, NDIG, W,
         sum(1 for l in out if l.startswith('='))))
