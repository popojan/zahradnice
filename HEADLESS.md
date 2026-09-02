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

`--param NAME=VALUE` (repeatable) overrides a `#parameter` declared by
the program — the sweep knob that does not need a regenerated file. It
applies to the program named on the command line only, not to programs it
launches. The resolved vector and the spliced include paths are recorded
in the trace header (`# param`, `# include`). See GRAMMAR.md,
"Parameters".

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
