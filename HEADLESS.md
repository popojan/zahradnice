# Headless mode

Run the engine without ncurses. Drives the LLM-authoring loop ("edit
rule → bash one-shot → read text → adjust") and removes the
`pty.fork` shim previously needed to drive `--replay` from a
non-interactive context.

The engine state lives in `screen_chars[]` + `memory[]` regardless of
backend, so headless dumps reflect exactly what a curses run would
have shown.

## Quick start

```sh
# Drive a program with a script of triggers; print the final screen
./zahradnice --headless --input "BBBBBB" --seed 42 programs/snake/index.cfg

# Pipe stdin → triggers (no flag needed)
printf 'B%.0s' {1..100} | ./zahradnice --headless --seed 42 programs/snake/index.cfg

# Replay a recorded trace deterministically (no terminal needed)
./zahradnice --headless --replay foo.trace

# Take a screenshot at trace step 1174 without launching a terminal
./zahradnice --headless --replay foo.trace --replay-snapshot 1174

# Capture screen + per-rule stats; suppress the dump itself
./zahradnice --headless --input "BBB" --stats out.stats prog >/dev/null
```

## CLI

```
--headless              Skip ncurses init/render.
--input STR             Drive engine with STR (one byte per event).
                        Use `~` for SPACE (raw spaces are stripped).
--input @PATH           Read trigger string from PATH (whitespace stripped).
--input @-              Read trigger string from stdin (whitespace stripped).
                        Implicit default in --headless when stdin is not a TTY.
--max-steps N           Stop after N applied rules (matches trace `step`).
--dump-screen PATH      Write final screen on exit. Format dispatch:
                          `-`         → stdout, isatty auto (TTY=ansi, pipe=txt)
                          `-.ansi`    → stdout, force ANSI
                          `-.txt`     → stdout, force plain
                          `*.ansi`    → file, ANSI
                          everything else → file, plain text
                        Default in headless mode: `-` (stdout).
                        Suppress with `>/dev/null`.
```

Composes with `--replay`, `--replay-snapshot`, `--mem-snapshot`,
`--trace`, `--trace-cell`, `--stats`, `--seed`, `--screen`. See
TRACING.md for those flags.

`--threads N` pins how many rules may be applied per step. It is part of a
run's identity, not a speed setting: the multi-rule gate changes which rules
co-fire, so a seed reproduces a trajectory only at the thread count that
produced it (an experiment measured the contact process's effective lambda_c
moving with it). The count is recorded in the trace header as `# threads=N`.
Replay reconstructs single-threaded runs only -- a trace logs one `apply` line
per applied rule and marks no batch boundaries, so a multi-rule step cannot be
told from the same rules applied in sequence; replaying one is refused with a
message rather than mis-reported as a divergence.

`--param NAME=VALUE` (repeatable) overrides a `#parameter` declared by
the program — the sweep knob that does not need a regenerated file. It
applies to the program named on the command line only, not to programs it
launches. The resolved vector and the spliced include paths are recorded
in the trace header (`# param`, `# include`). See GRAMMAR.md,
"Parameters".

## Control actions and program switching

A rule that fires a `#control` action (`pause`, `clear`, `reset`, `return`,
`quit`) or a `#program` switch does here what it does under curses, and the
trace records the transitions as `program_unload` / `program_load` pairs. So a
menu is drivable end to end:

```sh
# walk down to Ants, run it for 400 ticks, come back; the menu re-opens on
# the entry it left through
./zahradnice-headless programs/index.cfg --seed 1 \
    --input "TT$(printf 's%.0s' {1..11})e$(printf 'T%.0s' {1..400})qTTTTTT"
```

`pause` has the only mapping that needs stating: interactively it blocks on the
keyboard, so timing events stop happening while keys still arrive. Headless it
means the same thing — a `#timing` trigger in the input script is skipped while
paused, a key is not — which is what lets a script unpause.

`quit`, and `return` with an empty call stack, end the run: remaining input is
not consumed, and the event count in the summary reflects that.

Sounds are the exception: `#sound` is parsed and the rule's sound character is
resolved, but nothing is played and no audio device is opened.

Until 2026-09 none of this worked. The runner applied the rule and dropped
everything but the screen write, silently — and because a headless run also
ends when no rule is applicable, a program that merely settled looked exactly
like one that quit on cue. `tests/control_actions.py` pins the difference
using programs that never run out of applicable rules.

## Defaults (Unix-symmetric)

`--headless` mode is symmetric on both ends, both gated by
`isatty(2)`:

| | TTY | pipe / redirect |
|---|---|---|
| stdin (input)  | error: no input source | implicit `--input @-` |
| stdout (dump)  | ANSI                   | plain text             |

So a one-shot becomes:

```sh
printf 'B%.0s' {1..100} | ./zahradnice --headless --seed 42 prog/x.cfg
#                       ^ stdin pipe → triggers   ^ stdout pipe → plain
```

Or, fully written out:

```sh
./zahradnice --headless --input @- --dump-screen - --seed 42 prog/x.cfg < ticks.txt
```

Suppress the implicit dump with `>/dev/null` if you only care about
the trace/stats. Override the implicit input by passing `--input STR`
or `--replay PATH`.

## Allowed combinations

```
--headless --input STR    [--max-steps N]  [--dump-screen P]   live-style drive
--headless --replay TRACE [--max-steps N]  [--dump-screen P]   deterministic replay
                          [--replay-snapshot S]                screenshot at step S
                          [--mem-snapshot S]                   memsnap_step<N>.txt
```

Rejected:
- `--headless` without `--replay` and without `--input` (no input source).
- `--input` with `--replay` (two input sources).
- `--input` without `--headless` (live mode uses keyboard).

## --input details

The string is consumed byte-by-byte; each byte is one trigger lookup
in `Grammar2D::R`. Engine treats keypress and timing triggers
uniformly, so `BBBaBBB` mixes timing ticks (`B`) and keypresses (`a`)
without special-casing. For `--input @PATH` the file content has all
whitespace (spaces, tabs, newlines) stripped after load — write
multi-line readable scripts.

For long sequences, use the shell:

```sh
# 1000 ticks via printf
./zahradnice --headless --input "$(printf 'B%.0s' {1..1000})" prog

# Or build a script file
printf 'B\n%.0s' {1..1000} > /tmp/ticks
./zahradnice --headless --input @/tmp/ticks prog
```

## Closed loop: `--stream` and `--until`

`--input` is open-loop: the whole script is fixed before the run. Two
flags make the headless runner drivable from a program that decides the
next byte from what the last one did:

```sh
# bytes are consumed as they arrive on stdin; the trace is line-buffered,
# so a driver can tail it between writes. EOF ends the run.
./zahradnice-headless prog.cfg --stream --trace run.trace --seed 1

# one byte runs a whole phase: each trigger in CHARS is re-fed while it
# applies something (a control action or program switch ends the expansion)
./zahradnice-headless prog.cfg --input 'b10110010ionc' --until iofc
```

`--until` is the "feed until no rule applies" the experiment harnesses
used to approximate with over-long budgets — and a budget that came out
short corrupted a protocol silently. A trigger that never quiesces is cut
by `--max-steps`, or by a 10⁷-application guard with an error. Both flags
are exercised by `tests/stream_input.py` (`make test-stream`).

## Status row in dumps

Engine row 0 is reserved for the status line (game writes go through
`wrap_row` which maps to rows 1..rows−1). Headless dumps overlay the
captured status into row 0 — visually 1:1 with ncurses screenshots.
The dump includes `HEADLESS: <program> ev=<N> score=<N>` (or
`REPLAY` for replay mode).

## Headless-only build (`zahradnice-headless`)

```sh
make zahradnice-headless     # 76 KB; no ncurses, no SDL
./zahradnice-headless --input "BBBB" --seed 42 prog/x.cfg
```

Validates the architectural seam: `libgrammar.a` carries no terminal
dependency. Not built by `make install`. Useful when you want a
small, dependency-free binary for CI or LLM authoring; the full
`zahradnice` binary remains the default.

## Determinism

`--seed` (or implicit time-based) seeds both `srand` and `srandom`.
Single-threaded execution by default in headless+input. Replay forces
`thread_count=1` and replays the recorded trigger sequence
bit-for-bit until engine logic actually changes — divergence is
reported on stderr.

## See also

- `TRACING.md` — record / replay / stats for live curses mode.
- `backlog/pending/headless-mode.md` — design notes and rationale.
- `GRAMMAR.md` — the `.cfg` rule language.
