#!/usr/bin/env python3
"""Generate programs/ants.cfg -- ant colony foraging (Deneubourg pheromone model).

The model is the textbook one (Deneubourg's double-bridge experiment ->
Resnick's StarLogo ants -> Wilensky's NetLogo "Ants"), reduced to what a
Type-0 grammar over a character grid can carry:

  * an ant is a *directed* particle: glyph = (laden?, heading)
  * it walks forward / left / right, never backwards, weight-biased
    towards forward -- a persistent walk, not a diffusive one
  * every move stamps a pheromone stub on the cell it vacates
  * the stub is *polarised*: it always points the way to the nest.
    An outbound ant stamps the direction it came from, a laden one the
    direction it is going.  Both mean the same thing, so one field
    serves two readings: laden ants walk downstream (home), outbound
    ants walk upstream (towards whatever the trail was laid from).
    This is what replaces NetLogo's numeric nest-scent gradient, which
    a grammar with no arithmetic cannot compute.
  * a stub is heavy (fresh) when laid on top of an existing trail --
    traffic reinforces -- and light (exploratory) when laid on bare
    ground.  Decay is heavy -> light -> gone, one rule each, so a
    trail's lifetime is exponential: evaporation.
  * trail following is Deneubourg's *probabilistic* response, not an
    argmax over neighbours (which the language cannot express either):
    the engine's weight-proportional sampler IS the choice function.
    Weight per candidate direction is set by what that cell holds.

Everything else follows: piles are eaten crumb by crumb, the near pile
goes first, and the colony re-aims at the next one as the old trail
evaporates.

Rule count is ~180, hence a generator.  Weights are all #parameter, so
they can be swept without regenerating:

    ./zahradnice programs/ants.cfg --param W_F_GOOD=40 --param P_FADE=0.1

Usage: python3 tools/gen_ants.py > programs/ants.cfg
"""

import sys

# ---------------------------------------------------------------- glyphs

DELTA = [(-1, 0), (0, 1), (1, 0), (0, -1)]          # N E S W
NAME = "NESW"

ANT = {
    'out': "↑→↓←",              # up right down left
    'lad': "⇑⇒⇓⇐",              # doubled = carrying
}
HEAVY = "╹╺╻╸"                  # fresh stub, per direction
LIGHT = "╵╶╷╴"                  # faded stub
FOOD = "●"
NEST = "▒"

FG_OUT, FG_LAD, FG_FADE, FG_NEST, FG_FOOD = 'A', 'B', 'F', 'N', 'B'
BG = '0'

opp = lambda d: (d + 2) % 4
left = lambda d: (d + 3) % 4
right = lambda d: (d + 1) % 4

# ------------------------------------------------------------- emission

out = []
def emit(*lines):
    for ln in lines:
        out.append(ln.rstrip())


def header(s, lhs, trig, rep, fg, bg, ctx='', ctxrep='', score=None, weight=None):
    """One rule header.  Score/weight is positional: it must start at index 10."""
    line = '=' + s + lhs + trig + rep + fg + bg + ctx + ctxrep
    if score is not None or weight is not None:
        line = line.ljust(9) + ' %s %s' % (score or 0, weight if weight else 1)
    return line


def body(lhs, rhs, vertical):
    """Render a rule body from cell maps keyed by offset from their own anchor.

    Both anchors are implicit at (0,0) of their own map; the boundary @ is
    placed between the two regions.  The whole body is indented one column so
    that a leftmost cell can never be read as a '#'/'^'/'=' line marker.
    """
    lhs = dict(lhs); rhs = dict(rhs)
    lhs.setdefault((0, 0), '@'); rhs.setdefault((0, 0), '@')
    cells = {}

    if not vertical:
        rows = [r for r, _ in lhs] + [r for r, _ in rhs]
        c1 = -min(c for _, c in lhs)
        bnd = c1 + max(c for _, c in lhs) + 1
        c3 = bnd + 1 - min(c for _, c in rhs)
        for (r, c), ch in lhs.items():
            cells[(r, c1 + c)] = ch
        for (r, c), ch in rhs.items():
            cells[(r, c3 + c)] = ch
        cells[(0, bnd)] = '@'
    else:
        col = -min([c for _, c in lhs] + [c for _, c in rhs])
        r1 = -min(r for r, _ in lhs)
        bnd = r1 + max(r for r, _ in lhs) + 1
        r3 = bnd + 1 - min(r for r, _ in rhs)
        for (r, c), ch in lhs.items():
            cells[(r1 + r, col + c)] = ch
        for (r, c), ch in rhs.items():
            cells[(r3 + r, col + c)] = ch
        cells[(bnd, col)] = '@'
        rows = [r for r, _ in cells]

    rows = [r for r, _ in cells]
    lines = []
    for r in range(min(rows), max(rows) + 1):
        row = [ch for ch in cells if ch[0] == r]
        if not row:
            lines.append('')
            continue
        wide = max(c for _, c in row)
        buf = [' '] * (wide + 1)
        for (rr, c), ch in cells.items():
            if rr == r:
                buf[c] = ch
        lines.append((' ' + ''.join(buf)).rstrip())
    return lines


def rule(headers, lhs, rhs, vertical=False):
    emit(*headers)
    emit(*body(lhs, rhs, vertical))
    emit('')


# ------------------------------------------------------------ the picture
# Offsets from the seeded anchor, which sits at the centre of the nest.

def blob(r0, c0, ch):
    """5x5 pile with the corners knocked off -- 21 crumbs."""
    cells = {}
    for r in range(-2, 3):
        for c in range(-2, 3):
            if abs(r) == 2 and abs(c) == 2:
                continue
            cells[(r0 + r, c0 + c)] = ch
    return cells

# The mound is deliberately broad.  A searching ant wins by touching any of
# 63 crumbs, a laden one by touching the nest, so the nest is the harder
# target and homing was the whole bottleneck: widening it from 17 cells to 39
# took deliveries from 10.5 to 13.5 per 12k steps and, more to the point,
# stopped the colony from occasionally stalling with eight ants lost carrying.
NEST_CELLS = {}
for r, half in ((-2, 2), (-1, 4), (0, 5), (1, 4), (2, 2)):
    for c in range(-half, half + 1):
        NEST_CELLS[(r, c)] = NEST
del NEST_CELLS[(0, 0)]                  # the anchor cell; filled by field 3

# Distance is the experiment, not decoration.  With all three piles close
# the pheromone is decorative: trails form and are followed, but flattening
# the whole trail response (W_*_GOOD/BAD/CROSS all equal) costs nothing
# measurable -- 14.2 +/- 0.9 crumbs per 12k steps against 12.9 +/- 0.9, one
# standard error apart over 24 seeds.  A wide nest in the middle of the
# screen is simply easy to find by walking.  Pushing the last two piles out
# restores the point: over steps 20k-50k, once the near pile is gone and the
# colony is working the distant ones, the response is worth 18.4 +/- 1.2
# against 14.6 +/- 0.8 (n=14).  The near pile stays near so that the first
# trail appears within the first minute of watching.
FOOD_CELLS = {}
FOOD_CELLS.update(blob(-5, 9, FOOD))    # near   -- found first, eaten first
FOOD_CELLS.update(blob(8, -23, FOOD))   # middle -- reached on a trail
FOOD_CELLS.update(blob(-2, 33, FOOD))   # far    -- last resort

ANT_CELLS = {}                          # ten of them, ringing the mound
for c in (-2, 0, 2):
    ANT_CELLS[(-3, c)] = ANT['out'][0]
    ANT_CELLS[(3, c)] = ANT['out'][2]
ANT_CELLS[(0, -6)] = ANT['out'][3]
ANT_CELLS[(-1, -5)] = ANT['out'][3]
ANT_CELLS[(0, 6)] = ANT['out'][1]
ANT_CELLS[(1, 5)] = ANT['out'][1]

# --------------------------------------------------------------- preamble

emit('#! Ants  home={score}  {help}')
emit('# ' + '-' * 70)
emit('# Ant colony foraging.  GENERATED by tools/gen_ants.py -- edit that.')
emit('#')
for glyphs, what, g2, what2 in ((ANT['out'], 'ant, searching', FOOD, 'food crumb'),
                                (ANT['lad'], 'ant, carrying a crumb', NEST, 'nest'),
                                (HEAVY, 'fresh pheromone', LIGHT, 'evaporating')):
    emit('# %s  %-23s%s  %s' % (glyphs, what, g2, what2))
emit('#')
emit('# A stub always points the way home.  Laden ants walk downstream along')
emit('# it, searching ants walk upstream, so one field does the work of')
emit('# NetLogo\'s two scent gradients.  Traffic writes heavy stubs, time')
emit('# fades them: the near pile builds a highway, and when it is eaten the')
emit('# highway evaporates and the colony re-aims at the next pile.')
emit('# ' + '-' * 70)
emit('')
emit('# Tunables.  A #parameter value runs to the end of its line, so the')
emit('# commentary has to sit above rather than beside it.  Override any of')
emit('# them per run: ./zahradnice programs/ants.cfg --param P_FADE=0.05')
emit('#')
emit('# ms between rule applications -- the whole simulation runs on one clock')
emit('#parameter TICK 8')
emit('# a step onto bare ground: straight on, then to either side.  Their')
emit('# ratio is how ballistic the search is; equal weights make it diffusive.')
emit('#parameter W_F_BLANK 3')
emit('#parameter W_S_BLANK 1')
emit('# a step along a trail the useful way.  W_S_GOOD > W_F_BLANK is what')
emit('# makes an ant turn onto a trail it merely brushes past.')
emit('#parameter W_F_GOOD 18')
emit('#parameter W_S_GOOD 6')
emit('# ... and the useless way: home without a crumb, or away with one.')
emit('#parameter W_F_BAD 1.2')
emit('#parameter W_S_BAD 0.4')
emit('# ... and straight across someone else\'s trail.')
emit('#parameter W_F_CROSS 3.6')
emit('#parameter W_S_CROSS 1.2')
emit('# turn on the spot: the wiggle, and the only way out of a dead end')
emit('#parameter W_TURN 0.3')
emit('# pick up / drop off, high enough to beat any step out of the way')
emit('#parameter W_PICK 40')
emit('#parameter W_DROP 40')
emit('# evaporation, fresh -> faded -> gone.  Raise it and trails die before')
emit('# a round trip finishes; lower it and the web fills the screen.  Between')
emit('# about 0.04 and 0.15 the crumb rate barely moves, so these two are set')
emit('# for the picture rather than the throughput: enough fresh trail to read')
emit('# as a highway, enough faded trail to read as a memory of one.')
emit('#parameter P_FADE 0.15')
emit('#parameter P_GONE 0.3')
emit('')
emit('#timing T {TICK}')
emit('#threads 1')
emit('#help SPACE pause   x restart   q quit')
emit('')
emit('# Colours.  A move rule paints the ant and the stub it leaves in one')
emit('# colour, so the two are deliberately the same thing: a trail segment is')
emit('# tinted by whoever last walked it.  Cyan A = searching, green B = laden')
emit('# and food, blue F = evaporating, yellow N = nest.  No trailing comments')
emit('# here either -- `#color B 2,BOLD  # laden` compares the attribute as')
emit('# "BOLD  # laden" and silently drops the bold.')
emit('#color A 6')
emit('#color B 2,BOLD')
emit('#color F 4')
emit('#color N 3')
emit('')
emit('#sound c sounds/click.wav')
emit('#control R return')
emit('#control C clear')
emit('#control P pause')
emit('')
emit('^')
emit('^Zcc')
emit('')

# ----------------------------------------------------------- the drawing
# Three one-shot stages, because a rule paints in a single colour.  Each
# anchor is absent from what it paints, so none of them can fire twice.

emit('# Set the table.  Scenery first and ants last, because the ants start')
emit('# walking the moment they are on screen: painted before the nest was,')
emit('# the ones that had wandered onto a nest cell were painted over and the')
emit('# colony opened two ants short.  The weight keeps the four stages ahead')
emit('# of the ants they create.')
DRAW = 10000
rule([header('=', 'Z', 'T', 'Y', FG_NEST, BG, score=0, weight=DRAW)],
     {}, NEST_CELLS, vertical=True)
rule([header('=', 'Y', 'T', 'X', FG_FOOD, BG, score=0, weight=DRAW)],
     {}, FOOD_CELLS, vertical=True)
rule([header('=', 'X', 'T', 'W', FG_OUT, BG, score=0, weight=DRAW)],
     {}, ANT_CELLS, vertical=True)
emit('# ... and the anchor cell, held out of the mound until the end, becomes')
emit('# the last brick of it.')
rule([header('=', 'W', 'T', NEST, FG_NEST, BG, score=0, weight=DRAW)], {}, {})

emit('# Keys.  Anchored on the nest, the one thing never eaten or moved.')
rule([header('R', NEST, 'q', NEST, FG_NEST, BG),
      header('C', NEST, 'x', NEST, FG_NEST, BG),
      header('P', NEST, '~', NEST, FG_NEST, BG)], {}, {})

# ------------------------------------------------------------ evaporation

emit('# Evaporation.  These compete with the ants for the same steps, which')
emit('# is what keeps the trail field from growing without bound: it settles')
emit('# where deposition and decay balance.')
for d in range(4):
    rule([header('=', HEAVY[d], 'T', LIGHT[d], FG_FADE, BG,
                 score=0, weight='{P_FADE}')], {}, {})
    rule([header('=', LIGHT[d], 'T', '~', FG_FADE, BG,
                 score=0, weight='{P_GONE}')], {}, {})

# -------------------------------------------------------------- movement

WEIGHT = {                       # (class, forward?) -> parameter
    ('blank', True): '{W_F_BLANK}', ('blank', False): '{W_S_BLANK}',
    ('good',  True): '{W_F_GOOD}',  ('good',  False): '{W_S_GOOD}',
    ('bad',   True): '{W_F_BAD}',   ('bad',   False): '{W_S_BAD}',
    ('cross', True): '{W_F_CROSS}', ('cross', False): '{W_S_CROSS}',
}

emit('# Movement.  One body per (state, direction, what is in the way); the')
emit('# three headers over it are the three headings that can move that way,')
emit('# the first one going straight on.')
for state in ('out', 'lad'):
    fg = FG_OUT if state == 'out' else FG_LAD
    for d in range(4):
        dr, dc = DELTA[d]
        # deposit points at the nest: whence I came (outbound), where I go (laden)
        dep = opp(d) if state == 'out' else d
        # the arrow direction each target class holds, and what it is worth
        classes = [(None, 'blank')]
        for a in range(4):
            if a == d:
                kind = 'good' if state == 'lad' else 'bad'
            elif a == opp(d):
                kind = 'bad' if state == 'lad' else 'good'
            else:
                kind = 'cross'
            classes.append((a, kind))
        for a, kind in classes:
            if a is None:
                lhs = {(dr, dc): '~'}
                ctx = ctxrep = ''
                point = dep
            else:
                lhs = {(dr, dc): '%'}
                ctx, ctxrep = HEAVY[a], LIGHT[a]
                # Walking *along* an existing trail (either way down it) the
                # stub copies that trail's own polarity rather than the ant's
                # belief -- an ant going the wrong way up a highway must not
                # reverse the signs behind it.  Cutting across, belief wins.
                point = a if a in (d, opp(d)) else dep
            # Heavy is the recruitment signal, so it is spent narrowly: on a
            # laden ant's whole route home, and where a searching ant is
            # actually getting use out of a trail.  Everything else is a light
            # exploratory mark, which is what the colony remembers by.
            rep = (HEAVY if state == 'lad' or kind == 'good' else LIGHT)[point]
            # The ant keeps its heading across the step; the weights above are
            # the whole of the trail response.  Turning it to face a stub it
            # steps on was tried and measurably lost (~25% fewer crumbs home):
            # the exploratory web is dense, so alignment mostly hands the ant
            # to whichever stale mark it brushed against.
            heads = [header('=', ANT[state][h], 'T', rep, fg, BG, ctx, ctxrep,
                            score=0, weight=WEIGHT[(kind, h == d)])
                     for h in (d, left(d), right(d))]
            rule(heads, lhs, {(dr, dc): ANT[state][d]}, vertical=(dc == 0))

emit('# Turn on the spot: the wiggle, and the way out of a dead end.')
turns = []
for state in ('out', 'lad'):
    fg = FG_OUT if state == 'out' else FG_LAD
    for h in range(4):
        for nd in (left(h), right(h)):
            turns.append(header('=', ANT[state][h], 'T', ANT[state][nd], fg, BG,
                                score=0, weight='{W_TURN}'))
rule(turns, {}, {})

# -------------------------------------------------------- food and nest

emit('# Pick a crumb up, turn away from the pile, become laden.')
for d in range(4):
    dr, dc = DELTA[d]
    heads = [header('=', ANT['out'][h], 'T', ANT['lad'][opp(d)], FG_LAD, BG,
                    score=0, weight='{W_PICK}') for h in range(4)]
    rule(heads, {(dr, dc): FOOD}, {(dr, dc): '~'}, vertical=(dc == 0))

emit('# Drop it at the nest, turn away, go out again.  One point per crumb.')
for d in range(4):
    dr, dc = DELTA[d]
    heads = [header('c', ANT['lad'][h], 'T', ANT['out'][opp(d)], FG_OUT, BG,
                    score=1, weight='{W_DROP}') for h in range(4)]
    rule(heads, {(dr, dc): NEST}, {}, vertical=(dc == 0))

sys.stdout.write('\n'.join(out).rstrip() + '\n')
