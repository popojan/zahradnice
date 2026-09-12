#!/usr/bin/env python3
"""Regression test: --stream (trigger bytes read from stdin as they arrive) and
--until (a trigger re-fed while it applies something).

--input is open-loop: the whole script is fixed before the run. A driver that
wants to choose the next byte from what the last one did needs the engine to
consume bytes as they come and to log applications as they happen. --until
closes the other gap: phases whose length is not known in advance were fed
over-long budgets, and a budget that came out short silently corrupted the
protocol. Both are checked on the bandit, which applies a rule on every
`a`/`b` event and never settles, and on a program that does settle.

usage: tests/stream_input.py [path-to-zahradnice-headless]
"""
import os, subprocess, sys, tempfile, time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BANDIT = 'experiments/bandit/bandit.cfg'
failures = []

def applied(trace):
    try:
        return sum(1 for l in open(trace, encoding='utf-8') if l.startswith('apply'))
    except FileNotFoundError:
        return 0

def wait_for(pred, timeout=5.0):
    t0 = time.time()
    while time.time() - t0 < timeout:
        if pred(): return True
        time.sleep(0.02)
    return pred()

def main():
    binary = sys.argv[1] if len(sys.argv) > 1 else './zahradnice-headless'
    os.chdir(REPO)
    d = tempfile.mkdtemp()
    trace = os.path.join(d, 'stream.trace')

    # --stream: bytes are processed before stdin is closed
    p = subprocess.Popen([binary, BANDIT, '--seed', '1', '--screen', '10,20', '--stream', '--trace', trace],
                         stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    p.stdin.write('aaa'); p.stdin.flush()
    if not wait_for(lambda: applied(trace) >= 3):
        failures.append('stream: 3 bytes written, %d applied before EOF' % applied(trace))
    p.stdin.write('a a\n'); p.stdin.flush()          # whitespace is skipped, like @PATH
    if not wait_for(lambda: applied(trace) >= 5):
        failures.append('stream: 5 bytes written, %d applied before EOF' % applied(trace))
    p.stdin.close(); p.wait()
    err = p.stderr.read()
    if p.returncode != 0 or 'Headless run: 5 events' not in err:
        failures.append('stream: exit %d, stderr %r' % (p.returncode, err.strip()))

    # --stream rejects --input
    r = subprocess.run([binary, BANDIT, '--stream', '--input', 'aa'], capture_output=True, text=True)
    if r.returncode == 0:
        failures.append('--stream with --input was accepted')

    # --until: one byte runs a settling phase to quiescence; the bandit never
    # settles, so its expansion must be cut by --max-steps.
    r = subprocess.run([binary, BANDIT, '--seed', '1', '--screen', '10,20', '--input', 'a',
                        '--until', 'a', '--max-steps', '50'], capture_output=True, text=True)
    if 'Headless run: 50 events' not in r.stderr:
        failures.append('until on a non-settling trigger: %r' % r.stderr.strip())
    # a settling one: the menu's frame is drawn by one-shot rules on the first tick
    menu_trace = os.path.join(d, 'menu.trace')
    r1 = subprocess.run([binary, 'programs/index.cfg', '--seed', '1', '--input', 'T', '--until', 'T',
                         '--trace', menu_trace], capture_output=True, text=True)
    n_until = applied(menu_trace)
    r2 = subprocess.run([binary, 'programs/index.cfg', '--seed', '1', '--input', 'T' * 400,
                         '--trace', menu_trace], capture_output=True, text=True)
    n_budget = applied(menu_trace)
    if n_until == 0 or n_until != n_budget:
        failures.append('until on a settling trigger: %d applied, over-fed budget applied %d' % (n_until, n_budget))

    if failures:
        for f in failures: print('FAIL', f)
        sys.exit(1)
    print('stream/until: ok (%d applied to quiescence on the menu)' % n_until)

if __name__ == '__main__':
    main()
