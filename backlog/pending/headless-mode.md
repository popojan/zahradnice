# Headless mode: run the engine without ncurses

## Goal

Let zahradnice execute a program (live, scripted, or replayed) without
initialising ncurses, dumping screen state to a file at the end (and
at any number of intermediate checkpoints via the existing
`--replay-snapshot` / `--mem-snapshot` machinery).

Closes the LLM-authoring iteration loop. Today every rule rewrite
requires the user to launch a real terminal and describe what they
saw; with headless dump it becomes `edit → bash one-shot → Read
.txt → adjust`. Also eliminates the `python3 pty.fork` 52×213 shim
the previous tetris hunt session needed to drive `--replay` from a
non-interactive context.

## Big picture

Two axes are entangled in the current binary:

| | input source | output sink |
|---|---|---|
| live | keyboard | ncurses TTY |
| `--replay PATH` | recorded trace | ncurses TTY (+ snapshot files) |

`--headless` is **not** a third input mode. It's an orthogonal switch
on the output axis: "skip ncurses init/render; engine state lives in
`screen_chars[]` and `memory[]`, dump those when asked." Input source
is whatever the user supplies via existing or new flags. So:

| invocation | input | output |
|---|---|---|
| `--headless --replay PATH --replay-snapshot S` | recorded trace | snapshot files at S |
| `--headless --max-steps N --dump-screen out` | none (pure ticks) | final screen |
| `--headless --input STR --dump-screen out` | scripted triggers | final screen |
| live (today) | keyboard | ncurses |

`--input` and `--replay` are kept separate even though both feed
triggers. Replay is "reproduce a recorded run, validate divergence"
(10-column trace v2). Input is "drive the engine with chosen
actions, judge output externally" (one trigger char per byte). They
serve different audiences — replay's value is that it knows what
*should* happen at each step; input doesn't and shouldn't.

## CLI surface

New flags (all additive; existing flags unchanged):

```
--headless              Skip ncurses init/render. Engine runs against
                        screen_chars[] and memory[] only.

--input STR             Feed STR as a sequence of trigger chars; one
                        char per event opportunity. Use `~` to send a
                        literal SPACE keypress (ASCII spaces are
                        stripped for readability, same convention as
                        cfg rule bodies).
--input @PATH           Read trigger string from PATH. Whitespace
                        (spaces, tabs, newlines) is stripped after
                        load — write multi-line readable scripts.

--max-steps N           Stop after N applied rules. Counter matches
                        the trace `step` column (void iterations do
                        not count). Composes with --input, --replay,
                        and live.

--dump-screen PATH      On exit, write final screen to PATH. Format
                        chosen by extension: `.txt` (chars only),
                        `.ansi` (with colour escapes). Same output
                        as F12 / `--replay-snapshot` for the same
                        moment in time. Status bar included as first
                        row, 1:1 with ncurses screenshots.
```

### Composition rules (validated at flag-parse)

Allowed:
- `--headless --input STR [--max-steps N] [--dump-screen P]`
- `--headless --replay TRACE [--replay-snapshot S] [--mem-snapshot S] [--dump-screen P]`
- `--headless --max-steps N [--dump-screen P]` (pure tick-driven, e.g. life, animations)
- `--dump-screen P` without `--headless` (final screenshot at exit of a live or replay run)

Rejected:
- `--headless` without any of `--input` / `--replay` / `--max-steps`
  (engine would hang silently with no input source and no stop
  condition).
- `--input` together with `--replay` (two input sources, ambiguous).

## Architecture

### Display + Input interfaces in libgrammar

After the refactor, **nothing in libgrammar.a includes `<ncurses.h>`**.
The library becomes terminal-agnostic. This is what makes a future
`make zahradnice-headless` build feasible (link without `-lncursesw`,
drop `display_curses.o`, ship a curses-free binary).

```cpp
// src/display.h (new, in libgrammar)
class Display {
public:
    virtual ~Display() = default;
    virtual void put(int r, int c, wchar_t ch, short pair, int attrs) = 0;
    virtual void status(const char* msg) {}
    virtual void refresh() {}
    virtual void dump_text(const std::string& path) {}
    virtual void dump_ansi(const std::string& path) {}
};

class InputSource {
public:
    virtual ~InputSource() = default;
    virtual int next() = 0;       // ERR if blocked or exhausted
    virtual bool exhausted() = 0;
};
```

Implementations:
- `CursesDisplay` (engine binary only, `src/display_curses.cpp`):
  wraps the existing two `mvadd_wch` sites in `grammar.cpp:650, :825`
  plus the status-line + screenshot logic currently in
  `zahradnice.cpp`.
- `HeadlessDisplay` (libgrammar, `src/display_headless.cpp`):
  no-op `put` (engine already mirrors to `screen_chars[]`); reads
  the canonical buffer for `dump_text` / `dump_ansi`.
- `KeyboardInput` (engine binary only): wraps `getch()`.
- `TraceInput` (libgrammar): replaces the inline parser inside
  `run_replay`.
- `StringInput` (libgrammar): yields chars from a `std::string`.

`Derivation` gains a `set_display(Display*)` setter; `screen_chars[]`
is already in `Derivation` and stays as canonical state. Both
backends mirror to it; only the curses backend additionally calls
`mvadd_wch`.

### Build composition

| target | links | notes |
|---|---|---|
| `zahradnice` / `zahradnice-speed` (today) | libgrammar + display_curses.o + display_headless.o + ncursesw | runtime `--headless` flag selects backend |
| `zahradnice-headless` (future, stub now) | libgrammar + display_headless.o + headless_main.o | no curses dep; out of scope to ship, in scope to verify links |

## Implementation order

Each step independently testable; bisect-friendly if anything
regresses.

1. **Display interface + screen_chars exposure (libgrammar).**
   Introduce `Display` in libgrammar; move the two `mvadd_wch` sites
   in `grammar.cpp` behind `display_->put(...)`. Implement
   `CursesDisplay` as a literal wrapper. Behavioural diff: zero;
   verify by recording + replaying tetris bit-for-bit.
2. **HeadlessDisplay + `--headless` flag.** No-op `put`; gate
   `initscr/endwin/start_color/etc.` in main. At this point
   `--headless` works only with no input (hangs); the seam exists.
3. **InputSource interface + StringInput.** Add `--input STR` /
   `--input @FILE` (whitespace-stripping, `~` → SPACE). First end-to-
   end headless run:
   `./zahradnice programs/snake.cfg --headless --input "BBBBBB" \
     --max-steps 6 --dump-screen out.txt --seed 42`.
4. **`--max-steps N`.** Counter in main loop; halt when applied
   rule count hits N. Works in live/headless/replay modes.
5. **Refactor `run_replay` onto TraceInput + Display.** Big payoff:
   `--headless --replay TRACE --replay-snapshot S` works without a
   pty shim. Existing replay path keeps working in curses mode.
6. **`--dump-screen` extension dispatch.** `.ansi` route reuses the
   logic from `take_screenshot`; lift into `display->dump_ansi`.
   Status bar included as first row (matches ncurses screenshots).
7. **Stub `make zahradnice-headless` target.** Verify it links
   without ncurses. Don't add to `make install`. Confirms
   architectural goal; concrete release deferred.
8. **Docs.** Update `TRACING.md` with the headless invocations;
   add a short `HEADLESS.md` with the four canonical commands.

## Estimated cost / size impact

- ~250 LoC added (3 small new files), ~30 LoC edited.
- Full binary: ≤ 2 KB growth (one vtable, two display impls, three
  flag arms).
- Future headless-only build: drop `-lncursesw` + `display_curses.o`
  + ~50 LoC of status-line / screenshot logic in main; estimated
  20–30 KB binary, no curses runtime dep.

## Out of scope (deliberate)

- **Unit-test subcommand** (`zahradnice-check unit-test FILE` with
  given/trigger/expect ASCII screens). Separate ticket; this work
  is the precondition.
- **Shipping the curses-free build.** Verify the link succeeds; do
  not add to `make install`.
- **Stdin input** (`--input -`). Marginal value for the LLM-authoring
  loop; defer until requested.
- **Special-key escapes in `--input`** (e.g. `\KEY_LEFT`). All
  existing programs use ASCII triggers; defer.
- **`--dump-status PATH`** as a separate file. Status row is part of
  the screen dump per (4) above.

## Related

- Memory: `tooling_for_llm_authoring.md` (origin of the proposal —
  ranked first of four LLM-authoring tooling items).
- Memory: `trace_replay_infra.md`, `debug_tooling_priorities.md`,
  `debug_tooling_memory_friction.md` — the runtime debug toolchain
  this composes with.
- `TRACING.md` — current `--trace` / `--stats` / `--replay` reference.
- `backlog/pending/centered-viewport-statusline.md` — clarifies
  that screenshots include the status row; headless dump must
  match.
- `backlog/pending/program-validation.md` — host for the future
  `unit-test` subcommand that builds on this.
