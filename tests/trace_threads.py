#!/usr/bin/env python3
"""Regression test: a trace carries the thread count it was recorded at.

`#threads` is a dynamical parameter, not a performance knob. The multi-rule
gate decides how many rules may co-fire per step, so the derivation depends on
it -- an experiment measured the contact process's effective lambda_c moving
with the count (survival at 0.4375: 14% -> 0% for N 1->8). A run is therefore
not identified by its seed alone, and a trace that omits the count is not a
reproducible artifact.

What is guarded here:

  * the count reaches the trace header, from both front ends;
  * a single-threaded trace still replays to a byte-identical screen;
  * a multithreaded trace replays to a byte-identical screen too, which is
    what the astep column bought: `step` counts applied rules (thread-count
    independent for a confluent program, so it cannot delimit a batch) and
    `astep` counts steps, so consecutive lines sharing one were applied
    together and replay feeds their trigger once;
  * the batch structure is actually there -- at N threads the mean batch size
    rises, so astep must advance more slowly than step.

usage: tests/trace_threads.py [path-to-zahradnice-headless] [path-to-zahradnice]
"""

import os
import subprocess
import sys
import tempfile

HEADLESS = sys.argv[1] if len(sys.argv) > 1 else "./zahradnice-headless"
COMBINED = sys.argv[2] if len(sys.argv) > 2 else "./zahradnice"
TICKS = "T" * 200
SCREEN = "10,20"

# Every cell is an anchor and converts exactly once, so at #threads > 1 the
# step really does batch -- which is what makes the replay case bite.
PROG = ("#! t\n"
        "#timing T 0\n"
        "^.**\n"
        "==.Ta20   1 1\n@@@\n"
        "==.Tb20   1 1\n@@@\n")

fails = []


def check(name, ok, detail=""):
    print(f"{'PASS' if ok else 'FAIL'} trace/{name}" + (f": {detail}" if detail and not ok else ""))
    if not ok:
        fails.append(name)


def record(d, threads):
    """Record a run at a given thread count; return (trace, screen)."""
    cfg = os.path.join(d, "p.cfg")
    with open(cfg, "w") as f:
        f.write(PROG)
    trace = os.path.join(d, f"t{threads}.trace")
    screen = os.path.join(d, f"t{threads}.txt")
    subprocess.run(
        [HEADLESS, cfg, "--seed", "5", "--screen", SCREEN, "--threads", str(threads),
         "--input", TICKS, "--trace", trace, "--dump-screen", screen],
        capture_output=True, text=True, check=True)
    return trace, screen


def header(path, key):
    for line in open(path):
        if not line.startswith("#"):
            return None
        if line.startswith(f"# {key}="):
            return line.strip().split("=", 1)[1]
    return None


def replay(trace, out):
    p = subprocess.run(
        [COMBINED, "--headless", "--replay", trace, "--dump-screen", out],
        capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr


with tempfile.TemporaryDirectory() as d:
    # --- the count reaches the header ------------------------------------
    t1, s1 = record(d, 1)
    t4, s4 = record(d, 4)
    check("header-records-threads",
          header(t1, "threads") == "1" and header(t4, "threads") == "4",
          f"got {header(t1, 'threads')!r} and {header(t4, 'threads')!r}")

    # --- a single-threaded trace still replays exactly ---------------------
    out1 = os.path.join(d, "replay1.txt")
    rc1, log1 = replay(t1, out1)
    same = (rc1 == 0 and os.path.exists(out1)
            and open(out1).read().splitlines()[1:] == open(s1).read().splitlines()[1:])
    check("single-threaded-replays-exactly", same, log1.strip()[:200])

    # --- a multithreaded trace replays exactly as well ---------------------
    out4 = os.path.join(d, "replay4.txt")
    rc4, log4 = replay(t4, out4)
    same4 = (rc4 == 0 and os.path.exists(out4)
             and open(out4).read().splitlines()[1:] == open(s4).read().splitlines()[1:])
    check("multithreaded-replays-exactly", same4,
          log4.strip()[:200] or "screen differs")

    # --- the batch really is a batch --------------------------------------
    def steps(path):
        """(applied rules, distinct asteps) -- i.e. rules and batches."""
        lines = [l.rstrip("\n").split("\t") for l in open(path)
                 if l.startswith("apply\t")]
        return len(lines), len({l[-1] for l in lines})

    r1, a1 = steps(t1)
    r4, a4 = steps(t4)
    check("astep-counts-steps-not-rules", r1 == a1 and a4 < r4,
          f"threads=1 gave {r1} rules/{a1} steps (want equal), "
          f"threads=4 gave {r4}/{a4} (want fewer steps than rules)")
    check("rule-count-is-thread-independent", r1 == r4,
          f"{r1} rules at one thread, {r4} at four -- the program is confluent, "
          "so the totals must match")

    # --- the interactive front end pins the count and records it -----------
    # zahradnice.cpp writes its header before any program is loaded, so it
    # pins the count to 1 rather than record a value it cannot yet know.
    if os.path.exists(COMBINED):
        cfg = os.path.join(d, "p.cfg")
        tc = os.path.join(d, "combined.trace")
        subprocess.run(
            [COMBINED, "--headless", cfg, "--seed", "5", "--screen", SCREEN,
             "--input", TICKS, "--trace", tc,
             "--dump-screen", os.path.join(d, "combined.txt")],
            capture_output=True, text=True)
        check("combined-records-threads", header(tc, "threads") == "1",
              f"got {header(tc, 'threads')!r}")

print("----")
if fails:
    print(f"trace: {len(fails)} failed: {', '.join(fails)}")
    sys.exit(1)
print("trace: all passed")
