#!/usr/bin/env python3
"""Regression test: a menu is re-entered with the entry you left through.

A `^<default><v><h>?` starting symbol says "this symbol is the caller's".
When a program returns, the engine plants the #program key of the entry
that launched it there instead of the default, and the menu's decode rules
turn that key into the cursor's row. The menu holds no state of its own:
the key rides on the call-stack frame, which is where the parent/child
relation already lives, so it works the same at any depth.

Driven through a pty because program switching only exists in the curses
engine — the headless runner loads one program and stays in it.

usage: tests/menu_memory.py [path-to-zahradnice]
"""

import os
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ptyharness import REPO, Child, screenshot

KEY_GAP = 0.7    # between keystrokes
RUN_S = 2.0      # let a launched program actually run before quitting it


def cursor_row(shot):
    """The label on the row carrying the |x| cursor, or None."""
    for line in shot:
        if '|x|' in line:
            return line.split('|x|', 1)[1].strip()
    return None


def walk(child, keys, gap=KEY_GAP):
    for k in keys:
        child.press(k.encode())
        time.sleep(gap)


def check(binary, label, script):
    """script: list of (keys, pause, expected-entry-or-None-to-skip)."""
    cwd = tempfile.mkdtemp()
    child = Child(binary, [os.path.join(REPO, 'programs/index.cfg'), '--seed', '1'],
                  cwd=cwd)
    ok = True
    try:
        time.sleep(1.0)
        for keys, pause, expect in script:
            walk(child, keys)
            time.sleep(pause)
            if expect is None:
                continue
            shot = screenshot(child, cwd)
            got = cursor_row(shot) if shot else None
            if got != expect:
                print('FAIL %s: after %r the cursor is on %r, expected %r'
                      % (label, keys, got, expect))
                ok = False
                break
        if ok:
            print('PASS %s' % label)
        return ok
    finally:
        child.stop()
        for stale in os.listdir(cwd):
            os.remove(os.path.join(cwd, stale))
        os.rmdir(cwd)


def main():
    binary = sys.argv[1] if len(sys.argv) > 1 else './zahradnice'
    if not os.access(binary, os.X_OK):
        print('FAIL: %s is not executable' % binary)
        return 1
    binary = os.path.abspath(binary)
    os.chdir(REPO)
    ok = True

    # One level: leave the main menu into a submenu, come back to it.
    ok &= check(binary, 'menu/submenu', [
        ('sssssss', 0.3, 'Primes'),   # walk down to Primes
        ('e', 1.0, None),             # into the primes submenu
        ('q', 1.0, 'Primes'),         # ...and back out, still on Primes
    ])

    # Two levels, same mechanism: a sieve returns into the submenu on its
    # own entry, and the submenu then returns into the main menu on its.
    ok &= check(binary, 'menu/depth-2', [
        ('sssssss', 0.3, 'Primes'),
        ('e', 1.0, 'Eratosthenes'),   # submenu opens on its own default
        ('sssss', 0.3, 'Umeo 2015'),
        ('e', RUN_S, None),           # run Umeo
        ('q', 1.0, 'Umeo 2015'),      # back into the submenu, on Umeo
        ('q', 1.0, 'Primes'),         # back into the main menu, on Primes
    ])

    print('----')
    print('menu-memory: %s' % ('all passed' if ok else 'FAILED'))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
