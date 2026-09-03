#!/usr/bin/env python3
"""Regression test: #control actions and #program switching, driven headless.

These used to work only under curses. The headless runner stepped the
derivation and threw the applied rule away, so a control rule *applied* --
the trace even logged it -- and then nothing happened: `q` did not quit, `x`
did not clear, SPACE did not pause, and a menu entry never opened. The
failure was invisible from the outside, and worse, a headless run ends as
soon as no rule is applicable, which makes a program that settles look
exactly like one that quit on cue. Every assertion here is therefore against
a program that never runs out of applicable rules.

usage: tests/control_actions.py [path-to-zahradnice-headless]
"""

import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ANTS = 'programs/ants.cfg'
MENU = 'programs/index.cfg'
TRAIL = '╹╺╻╸╵╶╷╴'
ANT = '↑→↓←⇑⇒⇓⇐'

failures = []


def run(binary, prog, keys, threads=1, seed=1, trace=None):
    """Run one script. Returns (applied_events, screen_without_status)."""
    cmd = [binary, prog, '--screen', '24,80', '--seed', str(seed),
           '--threads', str(threads), '--input', keys, '--dump-screen', '-.txt']
    if trace:
        cmd += ['--trace', trace]
    p = subprocess.run(cmd, capture_output=True, text=True, cwd=REPO)
    events = 0
    for line in p.stderr.splitlines():
        if 'Headless run:' in line:
            events = int(line.split('run:')[1].split('events')[0])
    screen = p.stdout.split('\n', 1)[1] if '\n' in p.stdout else ''
    return events, screen


def check(label, got, want):
    if got == want:
        print('PASS %s' % label)
    else:
        print('FAIL %s: got %r, expected %r' % (label, got, want))
        failures.append(label)


def main():
    binary = sys.argv[1] if len(sys.argv) > 1 else './zahradnice-headless'
    binary = os.path.abspath(binary)
    if not os.access(binary, os.X_OK):
        print('FAIL: %s is not executable' % binary)
        return 1

    # `return` with nothing on the call stack quits. Ants always has an
    # applicable rule, so a short run is the action firing, not quiescence.
    n, _ = run(binary, ANTS, 'T' * 50)
    check('no key runs to the end of the script', n, 50)
    n, _ = run(binary, ANTS, 'T' * 20 + 'q' + 'T' * 30)
    check('q returns, and returns out of the top frame', n, 21)

    # `clear` re-applies the starting symbols: the board comes back whole.
    _, eaten = run(binary, ANTS, 'T' * 3000)
    _, blank = run(binary, ANTS, 'T' * 3000 + 'x')
    _, fresh = run(binary, ANTS, 'T' * 3000 + 'x' + 'T' * 5)
    check('the run ate into a pile', eaten.count('●') < 63, True)
    check('x clears the screen', (blank.count('●'), blank.count('▒')), (0, 0))
    check('and the program redraws itself',
          (fresh.count('●'), fresh.count('▒'),
           sum(fresh.count(c) for c in ANT)), (63, 39, 10))

    # `pause` stops timing events and lets keys through -- that is the only
    # way to unpause. Every ants tick applies exactly one rule, so the event
    # count is the arithmetic of what got through.
    base, _ = run(binary, ANTS, 'T' * 200 + 'T' * 20)
    paused, _ = run(binary, ANTS, 'T' * 200 + '~' + 'T' * 20)
    resumed, _ = run(binary, ANTS, 'T' * 200 + '~' + 'T' * 10 + '~' + 'T' * 9)
    check('unpaused, every tick applies', base, 220)
    check('SPACE swallows the ticks after it', paused, 201)
    check('SPACE again lets them through', resumed, 211)

    # #program switching, and the menu that is re-entered on the entry you
    # left through: walk to Ants, run it, come back.
    trace = os.path.join(REPO, 'tests', '.control_actions.trace')
    keys = 'TT' + 's' * 11 + 'e' + 'T' * 400 + 'q' + 'T' * 6
    _, screen = run(binary, MENU, keys, trace=trace)
    cursor = [l.split('|x|', 1)[1].strip() for l in screen.split('\n') if '|x|' in l]
    check('the menu comes back on the entry it left through',
          cursor[0] if cursor else None, 'Ants')
    with open(trace, encoding='utf-8') as f:
        moves = [l.split('\t')[3].strip() for l in f if l.startswith('program_load')]
    os.remove(trace)
    check('and the trace records both transitions', moves,
          ['programs/index.cfg', 'programs/ants.cfg', 'programs/index.cfg'])

    print('----')
    print('control-actions: %s'
          % ('all passed' if not failures else 'FAILED (%d)' % len(failures)))
    return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(main())
