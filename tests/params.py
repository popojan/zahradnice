#!/usr/bin/env python3
"""Regression test: `#parameter` declarations and `--param` overrides.

The properties worth guarding are the ones an edit could silently break:

  * substitution does not move a rule -- `src_line` is the trace's rule
    identity, and `ladder_stats.py` / `bandit_stats.py` re-parse the .cfg to
    map line -> rule. A parameterized file and the same file with the value
    written out by hand must trace byte-identically, `src_line` included.
  * an override actually reaches the weight, and changes the derivation.
  * an `#include` path may be parameterized (one skeleton, swapped rule
    blocks), and a path that resolves to nothing fails loudly.
  * an undeclared `{NAME}` fails loudly rather than surviving as a literal.
  * the places deliberately left alone stay alone: rule bodies (geometry is
    positional) and the `#!` status template (whose {score}/{steps} share the
    syntax) -- tested with a parameter named `score`, which collides on
    purpose.

There are two ways into the same engine -- the standalone
`zahradnice-headless` and `zahradnice --headless` -- and they fill
HeadlessOptions in different places, so an override must be shown to reach
both. The combined binary dropped them silently until this test existed.

usage: tests/params.py [path-to-zahradnice-headless] [path-to-zahradnice]
"""

import os
import subprocess
import sys
import tempfile

BIN = sys.argv[1] if len(sys.argv) > 1 else "./zahradnice-headless"
COMBINED = sys.argv[2] if len(sys.argv) > 2 else "./zahradnice"
TICKS = "T" * 200
SCREEN = "10,20"

fails = []


def check(name, ok, detail=""):
    print(f"{'PASS' if ok else 'FAIL'} params/{name}" + (f": {detail}" if detail and not ok else ""))
    if not ok:
        fails.append(name)


def run(cfg, *args, expect_ok=True):
    """Run one program; return (returncode, stderr, screen, trace)."""
    d = os.path.dirname(cfg)
    screen, trace = os.path.join(d, "out.txt"), os.path.join(d, "out.trace")
    p = subprocess.run(
        [BIN, cfg, "--seed", "5", "--screen", SCREEN, "--threads", "1",
         "--input", TICKS, "--dump-screen", screen, "--trace", trace, *args],
        capture_output=True, text=True)
    body = open(screen).read() if p.returncode == 0 and os.path.exists(screen) else ""
    tr = open(trace).read() if p.returncode == 0 and os.path.exists(trace) else ""
    return p.returncode, p.stderr, body, tr


def run_combined(cfg, *args):
    """The same run through `zahradnice --headless`; screen only."""
    screen = os.path.join(os.path.dirname(cfg), "combined.txt")
    p = subprocess.run(
        # the combined binary spells the thread cap --max-threads
        [COMBINED, "--headless", cfg, "--seed", "5", "--screen", SCREEN,
         "--max-threads", "1", "--input", TICKS, "--dump-screen", screen, *args],
        capture_output=True, text=True)
    return p.returncode, p.stderr, (open(screen).read() if p.returncode == 0
                                    and os.path.exists(screen) else "")


def write(d, name, text):
    path = os.path.join(d, name)
    with open(path, "w") as f:
        f.write(text)
    return path


def applies(trace):
    """Applied rules as (event, score, trigger, lhs, idx, row, col, src_line, head)."""
    return [l.split("\t")[1:] for l in trace.splitlines() if l.startswith("apply")]


def field(screen):
    """The playfield, without row 0 -- the status line's own letters would
    otherwise be counted as cells (results.md records this exact trap)."""
    return "\n".join(screen.splitlines()[1:])


def counts(screen, chars):
    f = field(screen)
    return {c: f.count(c) for c in chars}


with tempfile.TemporaryDirectory() as d:
    # --- substitution is line-neutral, and lands the declared default ------
    # Both files carry the #parameter line, so any difference in src_line is
    # substitution moving a rule, which it must never do.
    param = write(d, "a-param.cfg",
                  "#! t  score={score} steps={steps}\n"
                  "#parameter W 3\n#timing T 0\n^.**\n"
                  "==.Ta20   1 {W}\n@@@\n==.Tb30   1 1\n@@@\n")
    literal = write(d, "a-literal.cfg",
                    "#! t  score={score} steps={steps}\n"
                    "#parameter W 3\n#timing T 0\n^.**\n"
                    "==.Ta20   1 3\n@@@\n==.Tb30   1 1\n@@@\n")
    rc1, _, s1, t1 = run(param)
    rc2, _, s2, t2 = run(literal)
    # The trace names the file it loaded, so equality is asserted on the two
    # things that must not depend on how the weight was spelled: the final
    # screen, and the applied-rule sequence (which carries src_line).
    check("default-equals-literal", rc1 == 0 and rc2 == 0 and s1 == s2,
          "parameterized file reached a different screen than the literal one")
    check("src-line-stable", applies(t1) == applies(t2), "substitution moved a rule")

    # --- an override reaches the weight -----------------------------------
    _, _, s_def, _ = run(param)
    _, _, s_hi, _ = run(param, "--param", "W=100")
    a0, b0 = counts(s_def, "ab").values()
    a1, b1 = counts(s_hi, "ab").values()
    check("override-changes-derivation", a1 > a0 and b1 < b0,
          f"default a={a0} b={b0}, W=100 a={a1} b={b1}")

    # --- a wrapper stands in for a whole variant ---------------------------
    # The pattern that makes one template serve several menu entries: a short
    # file sets the value, then includes the program that declares the default.
    # It only works because a #parameter is a default -- first declaration
    # wins -- and it is what a `#program`-carried parameter would otherwise be
    # needed for.
    write(d, "core.cfg",
          "#parameter SPROUT 100\n#timing T 0\n^.**\n"
          "==.Ta20   1 {SPROUT}\n@@@\n==.Tb30   1 100\n@@@\n")
    calm = write(d, "calm.cfg",
                 "#! calm  score={score} steps={steps}\n"
                 "#parameter SPROUT 10\n#include core.cfg\n")
    fiery = write(d, "fiery.cfg",
                  "#! fiery  score={score} steps={steps}\n"
                  "#parameter SPROUT 400\n#include core.cfg\n")
    _, _, s_calm, _ = run(calm)
    _, _, s_fiery, _ = run(fiery)
    check("wrapper-beats-included-default",
          counts(s_calm, "a")["a"] < counts(s_fiery, "a")["a"],
          f"calm a={counts(s_calm, chr(97))[chr(97)]}, fiery a={counts(s_fiery, chr(97))[chr(97)]}")
    _, _, s_forced, _ = run(calm, "--param", "SPROUT=400")
    check("cli-beats-wrapper", counts(s_forced, "a")["a"] == counts(s_fiery, "a")["a"],
          f"forced a={counts(s_forced, chr(97))[chr(97)]}, fiery a={counts(s_fiery, chr(97))[chr(97)]}")

    # --- parameterized #include -------------------------------------------
    write(d, "frag-on.cfg", "==.Tb30   1 1\n@@@\n")
    write(d, "frag-off.cfg", "# no rules\n")
    skel = write(d, "skel.cfg",
                 "#! t  score={score} steps={steps}\n"
                 "#parameter MODE on\n#timing T 0\n^.**\n"
                 "==.Ta20   1 1\n@@@\n#include frag-{MODE}.cfg\n")
    _, _, s_on, _ = run(skel)
    _, _, s_off, _ = run(skel, "--param", "MODE=off")
    check("include-parameterized",
          counts(s_on, "b")["b"] > 0 and counts(s_off, "b")["b"] == 0,
          f"on b={counts(s_on, chr(98))[chr(98)]}, off b={counts(s_off, chr(98))[chr(98)]}")
    rc, err, _, _ = run(skel, "--param", "MODE=bogus")
    check("include-missing-is-loud", rc != 0 and "not found" in err, err.strip())

    # --- an undeclared name is an error, not a literal ---------------------
    bad = write(d, "bad.cfg",
                "#! t\n#timing T 0\n^.**\n==.Ta20   1 {NOPE}\n@@@\n")
    rc, err, _, _ = run(bad)
    check("undeclared-is-loud", rc != 0 and "undeclared parameter" in err, err.strip())

    # --- bodies and the #! template are left verbatim ----------------------
    # `score` shadows a status variable on purpose: if the #! line were
    # substituted the status would read 9 instead of the real score.
    braces = write(d, "braces.cfg",
                   "#! t  score={score}\n"
                   "#parameter score 9\n#parameter X 9\n#timing T 0\n^.**\n"
                   "==.Ta20   1 1\n@@@{X}\n")
    rc, err, s_br, _ = run(braces)
    status = s_br.splitlines()[0] if s_br else ""
    check("body-not-substituted", rc == 0 and "{X}" in field(s_br), "braces in a body were replaced")
    check("status-template-not-substituted",
          rc == 0 and "score=9" not in status, f"status line reads {status!r}")

    # --- both front ends honour an override -------------------------------
    # zahradnice.cpp and headless_main.cpp fill HeadlessOptions separately;
    # a field added to one is easy to forget in the other.
    # The two front ends are not compared screen-for-screen: the combined
    # binary has no --threads, so cfg.thread_count auto-detects and multi-rule
    # mode shuffles the applicable set, spending the RNG differently. What must
    # hold is that the override reaches the weight here too.
    if os.path.exists(COMBINED):
        rc_c, err_c, s_c_def = run_combined(param)
        _, _, s_c_hi = run_combined(param, "--param", "W=100")
        check("combined-binary-runs", rc_c == 0, err_c.strip())
        ca0, cb0 = counts(s_c_def, "ab").values()
        ca1, cb1 = counts(s_c_hi, "ab").values()
        check("combined-honours-param", ca1 > ca0 and cb1 < cb0,
              "`zahradnice --headless` ignored --param")

    # --- provenance is in the trace ---------------------------------------
    _, _, _, t_prov = run(skel, "--param", "MODE=off")
    check("trace-records-params", "# param MODE=off" in t_prov)
    check("trace-records-includes", "frag-off.cfg" in t_prov)

print("----")
if fails:
    print(f"params: {len(fails)} failed: {', '.join(fails)}")
    sys.exit(1)
print("params: all passed")
