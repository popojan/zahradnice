#!/usr/bin/env python3
"""Regression test: the engine sleeps when the screen cannot change.

Rule applicability depends only on the screen state, so a trigger that
applied nothing cannot succeed again against an unchanged screen. The main
loop must therefore block in wget_wch() until a key or an interval timing
event, instead of re-asking as fast as the CPU allows.

Three things can go wrong, one per check:

  spin      a settled program pins a core at 100%. That was the state
            between 905fba5 (which removed the sleep on a failed T step)
            and idle_timeout_ms() -- every `#timing T 0` program, the menu
            included, kept asking a screen that could not answer.

  oversleep the cure sleeping through work: an idle screen must still be
            woken by its interval timings (the menu keeps repainting while
            nobody touches it), and a program must reach the screen it is
            supposed to settle on -- Umeo's sieve is compared against it,
            so a nap taken while rules still applied shows up as an
            unfinished screen.

  throttle  the cure sleeping unconditionally -- a nap on every pass of
            the loop -- which costs nothing when idle but caps a program
            that still has work.

Linux only: reads utime+stime from /proc/<pid>/stat.

usage: tests/idle_cpu.py [path-to-zahradnice]
"""

import os
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ptyharness import REPO, Child, screenshot

BUSY_PCT = 25.0        # an idle program must stay well under this
SAMPLE_S = 2.0         # length of one CPU sample window
SETTLE_S = 1.5         # grace before the first sample
MAX_WAIT_S = 24.0      # give a slow machine time to finish computing
MIN_APPLIES = 1000     # over SETTLE_S + SAMPLE_S, when work never runs out
TICK_S = 2.5           # long enough for a 500ms interval timing to fire


def wait_until_idle(child, label, seen):
    """Sample until one window comes in under BUSY_PCT. False = kept spinning."""
    deadline = time.time() + MAX_WAIT_S
    while time.time() < deadline:
        pct = child.sample(SAMPLE_S)
        if pct is None:
            print('FAIL %s: process died' % label)
            return False
        seen.append(pct)
        if pct < BUSY_PCT:
            return True
    print('FAIL %s: still spinning after %.0fs, samples %s'
          % (label, MAX_WAIT_S, ' '.join('%.0f%%' % p for p in seen)))
    return False


def check_idle_but_ticking(binary, program, label):
    """A settled program must stop burning CPU -- and still be woken by its
    own interval timings, which are what keep a menu animating. Watched
    through the bytes it paints, since a keystroke would wake it itself."""
    child = Child(binary, [program, '--seed', '1'])
    try:
        time.sleep(SETTLE_S)
        seen = []
        if not wait_until_idle(child, label, seen):
            return False
        before = child.painted
        time.sleep(TICK_S)
        painted = child.painted - before
        if painted == 0:
            print('FAIL %s: idles at %.0f%% CPU but painted nothing in %.1fs '
                  '-- its interval timing never woke it'
                  % (label, seen[-1], TICK_S))
            return False
        print('PASS %s: idles at %.0f%% CPU, still ticking (%d bytes in %.1fs)'
              % (label, seen[-1], painted, TICK_S))
        return True
    finally:
        child.stop()


def check_settles(binary, program, expected_path, label):
    """...and it must be the finished screen it settles on, not a stalled one."""
    cwd = tempfile.mkdtemp()
    child = Child(binary, [os.path.join(REPO, program), '--seed', '1'], cwd=cwd)
    try:
        time.sleep(SETTLE_S)
        seen = []
        if not wait_until_idle(child, label, seen):
            return False
        shot = screenshot(child, cwd)
        if shot is None:
            print('FAIL %s: no screenshot taken' % label)
            return False
        got = [line.rstrip() for line in shot[1:]]
        with open(os.path.join(REPO, expected_path), errors='replace') as f:
            want = [line.rstrip() for line in f.read().splitlines()[1:]]
        if got != want:
            first = next((i for i, (a, b) in enumerate(zip(got, want)) if a != b),
                         min(len(got), len(want)))
            print('FAIL %s: settled on an unfinished screen, row %d differs\n'
                  '  got  %r\n  want %r' % (label, first + 1,
                                            got[first:first + 1],
                                            want[first:first + 1]))
            return False
        print('PASS %s: settled on the finished screen' % label)
        return True
    finally:
        child.stop()
        for stale in os.listdir(cwd):
            os.remove(os.path.join(cwd, stale))
        os.rmdir(cwd)


def check_running(binary, program, label):
    """A program that always has a rule to apply must not be throttled."""
    tmp = tempfile.mkdtemp()
    trace = os.path.join(tmp, 'rate.trace')
    child = Child(binary, [program, '--seed', '1', '--trace', trace])
    try:
        time.sleep(SETTLE_S + SAMPLE_S)
    finally:
        child.stop()
    applies = 0
    try:
        with open(trace, errors='replace') as f:
            applies = sum(1 for line in f if line.startswith('apply'))
    except IOError:
        pass
    for stale in os.listdir(tmp):
        os.remove(os.path.join(tmp, stale))
    os.rmdir(tmp)
    if applies >= MIN_APPLIES:
        print('PASS %s: %d rules applied, not throttled' % (label, applies))
        return True
    print('FAIL %s: only %d rules applied in ~%.0fs -- something sleeps even '
          'when rules are applicable' % (label, applies, SETTLE_S + SAMPLE_S))
    return False


def main():
    binary = sys.argv[1] if len(sys.argv) > 1 else './zahradnice'
    if not os.access(binary, os.X_OK):
        print('FAIL: %s is not executable' % binary)
        return 1
    binary = os.path.abspath(binary)
    os.chdir(REPO)
    ok = True
    # The default menu: idle from the moment it is drawn, and `#timing T 0`.
    ok &= check_idle_but_ticking(binary, 'programs/index.cfg', 'idle/menu')
    # Umeo's real-time sieve: computes hard, then stands still forever.
    ok &= check_settles(binary, 'programs/primes/06-umeo.cfg',
                        'tests/primes/06-umeo.expected', 'idle/umeo')
    # Flowers never runs out of applicable rules.
    ok &= check_running(binary, 'programs/flowers.cfg', 'rate/flowers')
    print('----')
    print('idle-cpu: %s' % ('all passed' if ok else 'FAILED'))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
