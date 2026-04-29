---
name: zahradnice-author
description: Author zahradnice .cfg programs (Type-0 grammar games for the terminal engine). Use when writing or modifying any `.cfg` file under this repository, or when the user asks for a new game/animation/demo in this codebase.
---

# Zahradnice authoring

Zahradnice programs are configuration files in a custom 2D-grammar DSL. The runtime is forgiving — malformed headers, undefined references, and mis-shaped bodies fail **silently**. There is no compiler error; rules just never fire. Write defensively.

## Source of truth

Read `GRAMMAR.v2.md` (repo root) end-to-end before writing rules. It is the complete language spec, generated against `src/grammar.cpp` + `src/grammar.h`. If `GRAMMAR.v2.md` is absent, fall back to `GRAMMAR.md` (older, has documented gaps).

Do not infer header semantics from existing programs alone — many programs exploit defaults or shorthand that obscure the field positions. Cross-check against the spec's field-position table.

## Authoring loop

You don't have an interactive terminal. Your loop is:

1. **Write or edit** the `.cfg` file.
2. **Build** (only if engine source changed): `make zahradnice-size`. Editing only `.cfg` files needs no rebuild.
3. **Run** the program: `./zahradnice path/to/program.cfg [seed]`. Use a fixed `[seed]` integer for determinism when randomness is involved.
4. **Capture state** by sending F12 — the engine writes `screenshot_<timestamp>.txt` (plain) and `.ansi` (coloured) to the working directory. Read the `.txt` to inspect screen state.
5. **Reload** during a session by triggering a rule whose action is `#control <c> reset` (or restart the binary). There is no built-in "reload current file" key unless the program declares one.

Programs load **unpaused** — the engine starts running rules immediately on the first frame. SPACE only does anything if the program wires it to `#control <c> pause` (which then toggles pause state on each press). To capture initial state without any rules firing, start the program and F12 immediately, or wire SPACE to pause and press it before any timing trigger has elapsed.

**You cannot drive the engine interactively from this loop.** Until the headless replay tool exists (deliberately deferred — see `backlog/pending/llm-authoring.md`), expect that observing dynamic behaviour requires the human to play the program and report back, or that you stage the program in a state where one F12 capture suffices. Note this friction.

## Pre-flight checklist for every rule

Before considering a rule "written", verify each of these against the spec — silent failure modes hide here:

1. **Header field count.** The header is `=S1234567`. Count positions from `=`. If you stop early, defaults apply (see spec). Double-check field 1 (LHS non-terminal) is correct — this is the rule's anchor.
2. **Trigger (field 2) is reachable.** Either it is `?` (wildcard), a literal user keypress, or declared via `#timing`. A trigger char with no declaration and no user pressing it = rule never fires.
3. **Body has exactly three `@`.** First = LHS anchor; second = boundary (never matched, never written); third = RHS anchor. Any other count is malformed (silently dropped).
4. **Boundary direction.** If the third `@` is to the right of the first, the body is horizontal (LHS left of boundary, RHS right). Otherwise vertical (LHS above, RHS below). Mixed = unsupported.
5. **LHS / RHS shapes align cell-for-cell.** Each non-space LHS cell has a corresponding RHS cell at the mirrored offset. Misalignment = the rule applies but writes to unexpected positions.
6. **Spaces are no-ops both sides.** A literal space in the body matches nothing and writes nothing. To match a space cell, use `~`. To write a space, use `~`.
7. **Context cells (`&`) require field 6 (and field 7) to be set** if you want non-wildcard matching/writing. `?` in field 6 = match anything.
8. **`!` and `%` are LHS-only.** `!` matches "not equal to field 6"; `%` matches "field 6 OR field 7". On the RHS they write the literal char `!` or `%`.
9. **`$` in RHS = restore from local memory.** Use to leave scenery intact when a sprite vacates a cell.
10. **Status line directive `#!` must be the very first non-empty line** of the assembled program (after `#include` resolution). If absent, no status line.

When a rule "doesn't fire", run through this checklist before suspecting the engine.

## Common rule families and patterns

These are the patterns hand-written programs reach for repeatedly. Implementing them is tedious and error-prone — that is *expected* friction for this exercise; do not invent custom helpers. Just write the rules out, and note where the tedium hurts most.

- **Sprite shift.** Two effects per move: write the sprite at the new cell, restore the old cell from memory (`$` in RHS). Each direction × variant is a separate rule header.
- **Rotation.** A rotating piece needs one rule per orientation. The rotation key transitions orientation N → N+1; each orientation has its own movement rules. Total rule count grows as `orientations × directions`.
- **Boundary / collision check.** Use `!` in the LHS context with field 6 set to the wall character: the cell must be "not a wall" for the rule to fire.
- **Toroidal wrapping** is automatic. Do not write rules that try to handle screen edges manually unless you've set `#grid` and need grid-aligned behaviour.
- **Line completion / row scan.** Requires LHS context cells across an entire row. Long rule bodies. Painful by hand.

## Audio and visuals

- Declare `#sound <c> path/to/file.wav` before referencing `<c>` in field S of any header. Sound paths under `sounds/` are pre-loaded in the repo (`sounds/click.wav`, `sounds/chime.wav`, etc.).
- Foreground/background colour codes 0–7 (white = 7, transparent bg = 8). Aliases via `#color <c> <digit>[,BOLD|DIM]`.
- The same character cannot simultaneously be a sound, program, and engine action — resolution order is `#program` → `#control` → sound (spec field S).

## When stuck

If a rule does not fire and the pre-flight checklist passes:

- Check the **trigger declaration** path: is the key actually arriving? Timing keys only fire when the corresponding `#timing` interval has elapsed.
- Print the screen with F12 and confirm the LHS region characters are exactly what your body's LHS region matches against. A space in the screen vs `~` in the body, or vice-versa, is a frequent silent failure.
- Verify the **non-terminal set**: a character in field 1 must appear *somewhere* in the program (initial symbol, prior rule's RHS, or another rule's body) for it ever to be on screen.
- Suspect coordinate drift: the cell-for-cell shape alignment between LHS and RHS regions must match. Re-count.

There is currently no `--check` linter and no trace tool. **This is the exercise's central friction.** If you find yourself repeatedly running the program just to discover that a rule has a malformed header or an undeclared trigger, **note it explicitly** — that is exactly the kind of friction this exercise is meant to surface.

## Friction journal (mandatory output)

The purpose of authoring through this skill is to **surface pain points** that drive future tooling (linter, headless replay, trace introspection, rule-family generators). While working, keep a short running journal of friction encountered, in `friction-journal.md` next to your program, with entries like:

- *Spent 20 minutes debugging a non-firing rule; root cause was an undeclared trigger key. A linter would have caught this.*
- *Wrote 16 nearly-identical rule headers for tetris piece rotation; a generator would collapse this to one.*
- *Could not tell whether rule X never fires or fires but writes outside the visible region. A trace tool would distinguish these.*

Keep entries short, factual, and timestamped (relative is fine: "after ~30 min", "third iteration"). The journal is the **deliverable** alongside the working program.

## Reference programs

For shape and idiom only — do not copy without understanding:

- `programs/tetris/tetris.cfg` — the reference target if the user asks for a tetris-from-scratch exercise. Do **not** read this before attempting; only consult after you have a working draft, to compare approaches.
- `programs/snake/snake.cfg` — sprite-shift + grow-tail patterns.
- `programs/life.cfg` — neighbour-counting via context-match cells.
- `demos/` — minimal teaching programs.

## Out of scope

- Modifying the engine (`src/*.cpp`) to make authoring easier. The skill assumes the engine is fixed; tooling lives in separate binaries (per `backlog/pending/llm-authoring.md`).
- Inventing helper directives (`#expand`, `#rotate`, etc.). The friction these would address is the data this exercise is collecting; do not pre-empt it.
- Running tests. There is no test suite. The journal + screenshots + the working program are the artifacts.
