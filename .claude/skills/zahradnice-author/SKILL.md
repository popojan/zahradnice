---
name: zahradnice-author
description: Author zahradnice .cfg programs (Type-0 grammar games for the terminal engine). Use when writing or modifying any `.cfg` file under this repository, or when the user asks for a new game/animation/demo in this codebase.
---

# Zahradnice authoring

Zahradnice programs are configuration files in a custom 2D-grammar DSL. The runtime is forgiving — malformed headers, undefined references, and mis-shaped bodies fail **silently**. There is no compiler error; rules just never fire. Write defensively, and lean on the diagnostic toolchain below — it exists precisely because of this.

## Source of truth

Read `GRAMMAR.md` (repo root) end-to-end before writing rules. It is the single complete language spec, verified against `src/grammar.cpp` + `src/grammar.h` + the running engine. Then skim `GRAMMAR-pitfalls.md` — documented engine quirks; check it before re-debugging anything that feels like an engine bug.

Do not infer header semantics from existing programs alone — many programs exploit defaults or shorthand that obscure the field positions. Cross-check against the spec's field-position table.

## Authoring loop (headless — no human in the loop)

The engine runs without a terminal; you can drive and observe everything yourself. See `HEADLESS.md` for full CLI.

1. **Write or edit** the `.cfg`. No rebuild needed for cfg-only changes.
2. **Run one-shot**: `./zahradnice --headless --seed 42 --input "TTTTaTT" prog.cfg` — one byte per event; keypress and timing triggers are fed uniformly (a byte `T` fires trigger `T` whether or not `#timing` declares it; `#timing` matters for live-mode auto-firing). `~` in the input string means SPACE. `--input @file` reads a whitespace-stripped script.
3. **Read the final screen** from stdout (`--dump-screen -` is the headless default; `-.txt` forces plain text), or `--max-steps N` to stop mid-run.
4. **Record what happened**: add `--trace t.log` (every applied rule: step, lhs, per-lhs rule idx, anchor row/col, source line, head) and `--stats s.txt` (per-rule applied/applicable/considered — surfaces never-firing and lottery-loser rules at a glance). See `TRACING.md`.
5. **Determinism**: `--seed N` + `#threads 1` (or `--trace`, which forces single-thread) makes runs bit-reproducible. `--screen R,C` pins geometry (playfield is rows 1..R−1 × C cols; row 0 is the status line).

Live-mode notes when a human does run it: programs load **unpaused** (SPACE only works if wired to `#control <c> pause`); F12 dumps `screenshot_*.txt/.ansi`; ESC always exits.

## Diagnostic toolbox

| Tool | Use |
|---|---|
| `./zahradnice-check explain CFG --line N` (or `--head '=...'`) | decode one rule's resolved geometry: which cells it reads vs writes, at what offsets. Build with `make zahradnice-check`. |
| `./zahradnice-check why CFG --screen FILE --trigger K` | dynamic no-fire diagnostics: why a rule does/doesn't match against an actual screen dump |
| `--trace` + `--replay t.log` | deterministic replay with divergence detection; `--replay-snapshot S` screenshots at step S |
| `make test` / `make update-tests` | golden tests: `tests/<prog>/*.input` driven through `zahradnice-headless`, dumps diffed against `.expected` |
| `make zahradnice-headless` | 76 KB curses/SDL-free binary for CI and scripted runs |

For experiments that need trust in numbers, the house pattern is **exact accounting**: reconstruct state from the trace in a script and diff against `--dump-screen` every run (reference implementation: `experiments/inverse/analyzers.py`).

## Pre-flight checklist for every rule

Silent failure modes hide here; run through this before considering a rule written. When in doubt, `zahradnice-check explain` settles geometry questions instantly — prefer it over hand-counting columns.

1. **Header field count.** The header is `=S1234567` (positions from `=`). Short headers take defaults. Field 1 (LHS non-terminal) is the anchor — double-check it.
2. **Trigger (field 2) is reachable**: `?` (wildcard), a literal key, a `#timing` char, or a byte you feed via `--input`.
3. **Body has exactly three `@`.** First = LHS anchor; second = boundary (never matched, never written); third = RHS anchor.
4. **Boundary direction.** Third `@` right of the first → horizontal (LHS left, RHS right); otherwise vertical (LHS above, RHS below). Mixed = unsupported. Prefer the direction matching the action (vertical for fall, horizontal for lateral).
5. **LHS / RHS regions have separate origins** (`@1` and `@3`). A LHS cell at offset Δ from `@1` and a RHS cell at offset Δ from `@3` address the **same screen cell** — align shapes cell-for-cell or writes land off-target.
6. **Spaces are no-ops both sides.** Match a space with `~`; write a space with `~`. Field 3 default (space) is a no-op write — to erase the anchor use `~` there.
7. **Context cells (`&`) require field 6.** `?` or an omitted field 6 is *not* a wildcard — it leaves the context character undefined, and `&` cells then never match, so the rule silently never fires. (`!` is the opposite: with field 6 unset it matches everything.) One ctx pair per rule, shared by every `&`/`!`/`%` cell.
8. **`!` and `%` are LHS-only** (RHS writes them literally).
9. **`$` in RHS restores the cell from local memory** — the sprite-vacates-a-cell idiom. Memory is **sticky by default**: declare moving glyphs in `#transient <chars>` or the sprite overwrites memory as it travels and `$` restores the sprite, painting a solid trail. Note `^` seeds never populate memory, so `$` over a cell only ever painted by a seed yields blank.
10. **`#!` status template must be the very first line**; body lines starting with `#`, `^`, or `=` are silently reclassified — indent the whole body one column if the leftmost cell would collide (both `@` anchors shift together, offsets survive).
11. **Toroidal wrapping is automatic** over the effective area — no edge-handling rules needed, and walkers wrap around rather than freeze.

## Scale: when to generate instead of hand-write

Hand-write up to roughly a dozen rules. Beyond that (piece rotations, direction × variant matrices, alphabet-indexed rule families), write a generator: C++ against `src/gen/genlib.h` (see `src/gen/README.md`, including the Pattern cookbook) or a plain Python emitter (house examples: `experiments/garden/gen_garden.py`, `experiments/inverse/gen_family.py`). Generators make admissibility structural — everything emitted parses — and are the standing answer to rule-family tedium; do not add helper directives to the engine for this.

## Sound, colour, programs

- `#sound <c> path.wav` before referencing `<c>` in header field S; assets under `sounds/`.
- Colours 0–7 (bg 8 = transparent, reads saved cell background); aliases via `#color <c> <digit>[,BOLD|DIM]`.
- Field S resolution order: `#program` → `#control` → sound.

## When stuck

A rule doesn't fire and the checklist passes:

- `zahradnice-check why` against a `--dump-screen` capture of the offending state — it reports which LHS cell failed to match.
- `--stats`: `considered > 0, applicable 0` means geometry/context mismatch; `considered 0` means the trigger never arrives or the anchor char is never on screen.
- Screen-vs-body space confusion (` ` on screen vs `~` in body) remains the most frequent silent failure.
- Verify the anchor char actually appears: initial symbol, another rule's RHS, or a body write.

## Friction journal

When authoring friction occurs — a silent failure that cost real time, a tool gap, a spec ambiguity — log it in `backlog/research/<topic>-friction.md` (git-ignored, that's intended): short, factual, timestamped entries. The journals drive tooling priorities; several tools in the toolbox above exist because earlier journals demanded them.

## Reference programs

For shape and idiom: `programs/snake/snake.cfg` (sprite-shift, grow-tail), `programs/life.cfg` (neighbour counting via context cells), `programs/tetris/tetris.cfg` (large hand-written program; generated counterpart via `src/gen/tetris_gen.cpp`), `demos/` (minimal teaching programs). Exception: if the user frames a task as a from-scratch exercise, do **not** read reference programs first — the friction signal is the point of the exercise.

## Out of scope

Modifying the engine (`src/*.cpp`) to make a single program easier. The engine is fixed law; per-program behaviour belongs in the cfg, authoring convenience belongs in generators and the check/trace toolchain. Engine changes need broad justification and are their own conversation.
