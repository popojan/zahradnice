# Replay-driven in-engine rule editor

## Sketch

Pausing a replay opens up live rule debugging directly inside the engine,
without leaving the program. With the trace replay infrastructure in place,
we already have:

- A frozen, deterministic engine state at any chosen step
- The ability to step forward / re-derive
- Knowledge of which rules are applicable at the current state (via the
  same dry-run scan the engine already performs)
- Source-line attribution for every rule (`Rule::source_line`)

Add a small editor pane and you have something like a built-in REPL for
the grammar.

## Capabilities the user wants

- Pause replay at a chosen step
- Show all rules currently applicable at this state, with positions
- Choose one to "what-if" execute and see the resulting state
- Edit a rule in-place (in a side pane), re-parse, continue replay
- Optionally restart from the same step with the edited rule to compare

## UI constraint

The user explicitly prefers:

- Editor pane *beside* the main rendered window (not overlapping)
- Means the program's virtual viewport must be smaller than the host
  terminal — easy via the replay's existing virtual-viewport sizing
  (recorded `screen=R,C` doesn't have to match host size)
- Clean, minimal, self-contained sources — no ncurses-overlapping-window
  libraries, no third-party TUI dependencies. Layout is: main viewport
  occupies one rectangle; editor occupies another; both written
  directly via ncurses positioning

## Approximate scope

- Pane management: ~50 LOC of layout math
- Editor: line-buffered text input via ncurses, syntax-naive (rules
  are short, no syntax highlighting needed initially) — ~150 LOC
- Re-parse + hot-reload single rule into `Grammar2D::R[lhs]`: needs a
  small addition to `Grammar2D` to mutate a single rule, ~30 LOC
- Replay-state branching: snapshot screen + memory + RNG state, restore
  on cancel — ~50 LOC if we add state checkpointing, free if we just
  re-replay from start

Total ~280 LOC plus the design decisions about state-snapshot semantics.

## Why this is high-value

- Closes the bug-hunt loop completely: see bug → pause replay at bug →
  identify suspect rule from applicable set → edit → see fix work in
  the same engine instance, same state
- Makes the LLM-authoring loop tighter too: LLM proposes a rule edit,
  user pastes into the editor, replay continues with new rule live
- Educational/demo value: someone learning the grammar can pause any
  running program and inspect "what could fire here"

## Triggers / dependencies

- The replay feature must be in (it is, as of this branch)
- The instrumentation's `Rule::source_line` is reused for jump-to-source
- A small libgrammar API: load-single-rule from string + replace-by-index,
  for the hot-reload path

## Open questions for when this is picked up

- State snapshotting strategy: full screen + memory snapshot (cheap,
  <100 KB per checkpoint) vs. re-replay from start (free, slower
  for late-state bugs)
- How many alternative-result previews to show simultaneously? One at
  a time with cycling, or three side-by-side?
- Editor scope — single rule, or whole cfg with cursor on suspect rule?
- Persistence — does an in-editor edit write back to the cfg on disk,
  or stay in-memory until explicitly saved?

## Longer-arc framing (deliberately out of scope now)

This feature, taken further, blurs into "zahradnice as a programming game
of its own": the player pauses a running program, inspects the state,
authors or edits rules to shape what happens next, and watches their
edits play out. The engine becomes both the runtime and the level editor.
Niche audience — somewhere at the intersection of Zachtronics-style
puzzles, esolang tinkering, and live coding — but a real one. Worth
remembering as a possible long-term direction, even though anything
beyond "pause and edit a rule" is firmly out of scope today.
