#!/usr/bin/env python3
"""Driving a real zahradnice on a pty: spawn, watch, type at it, screenshot.

Shared by the tests that need the curses binary rather than the headless
one — anything about the main loop, program switching or CPU behaviour.
Linux only: reads utime+stime from /proc/<pid>/stat.
"""

import fcntl
import os
import pty
import select
import signal
import struct
import termios
import threading
import time

F12 = b'\x1b[24~'      # takes a screenshot into the engine's cwd
CLK = os.sysconf('SC_CLK_TCK')
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Child:
    """A zahradnice run on a pty, drained continuously: a full pty buffer
    would block the engine and make its CPU reading meaningless."""

    def __init__(self, binary, args, cwd=None, rows=24, cols=80):
        self.pid, self.fd = pty.fork()
        if self.pid == 0:
            os.environ['TERM'] = 'xterm-256color'
            if cwd:
                os.chdir(cwd)
            os.execv(binary, [binary] + args)
            os._exit(127)
        fcntl.ioctl(self.fd, termios.TIOCSWINSZ,
                    struct.pack('HHHH', rows, cols, 0, 0))
        self.alive = True
        self.painted = 0  # bytes the engine has written to the terminal
        threading.Thread(target=self._drain, daemon=True).start()

    def _drain(self):
        while self.alive:
            r, _, _ = select.select([self.fd], [], [], 0.05)
            if not r:
                continue
            try:
                data = os.read(self.fd, 65536)
            except OSError:
                return
            if not data:
                return
            self.painted += len(data)

    def ticks(self):
        """CPU ticks used so far, or None if the process is gone."""
        try:
            with open('/proc/%d/stat' % self.pid) as f:
                fields = f.read().rsplit(')', 1)[1].split()
            if fields[0] in ('Z', 'X'):
                return None
            return int(fields[11]) + int(fields[12])
        except (IOError, OSError, IndexError):
            return None

    def sample(self, seconds):
        """Percent of one core used over the next `seconds`."""
        t0, c0 = time.time(), self.ticks()
        if c0 is None:
            return None
        time.sleep(seconds)
        t1, c1 = time.time(), self.ticks()
        if c1 is None:
            return None
        return 100.0 * (c1 - c0) / CLK / (t1 - t0)

    def press(self, keys):
        os.write(self.fd, keys)

    def stop(self):
        self.alive = False
        try:
            os.kill(self.pid, signal.SIGKILL)
            os.waitpid(self.pid, 0)
        except OSError:
            pass
        try:
            os.close(self.fd)
        except OSError:
            pass


def screenshot(child, cwd):
    """F12 the engine and return the screenshot's lines, status line first.

    One press has to be enough: a sleeping loop must still answer its
    keyboard, and that is half of what this test is about."""
    for stale in os.listdir(cwd):
        os.remove(os.path.join(cwd, stale))
    child.press(F12)
    for _ in range(40):
        time.sleep(0.1)
        shots = [f for f in os.listdir(cwd) if f.endswith('.txt')]
        if shots:
            time.sleep(0.2)  # let the write finish
            with open(os.path.join(cwd, shots[0]), errors='replace') as f:
                return [line.rstrip() for line in f.read().splitlines()]
    return None
