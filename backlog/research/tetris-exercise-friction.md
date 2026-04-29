# Tetris-from-scratch exercise — friction journal

Single-deliverable journal accompanying `programs/tetris2/tetris.cfg`. Entries are
relative-timestamped; "could-have-known" entries are flagged because they're the
most actionable signal for tooling.

## Architecture phase (before any rule body was written)

### A1. Piece-cell encoding deliberation
*~30 min, could-have-known.*
I oscillated between "one non-terminal char per piece × orientation"
(distinct anchor symbol) and "one non-terminal char per piece, all four cells
share it, anchor disambiguated by LHS context". Settled on the second after
realising V (the non-terminal set) is just `field 1` aggregated across rules,
so a single shared char lets the engine still scan correctly while LHS context
constraints uniquely identify the anchor cell.

The spec defines V tersely; a *worked example* showing
"shared-char + positional-disambiguation" would have collapsed this to a 2-min
read instead of 30 min of reasoning. Tooling implication: a documentation-level
fix (an idiom catalogue) is sufficient — no engine or linter change required.

### A2. Absolute-positioning gap
*~15 min, could-have-known.*
I tried to design a freeze rule that writes a fresh-piece-spawn at a fixed
column, then realised body offsets are LHS-anchor-relative and there is no
absolute coordinate primitive. Workarounds — wide-bodies bridging two regions,
walking-tokens, spawn-at-relative-offset — each have distinct costs. Picked
walking-token + spawn-at-freeze-column as the MVP-cheapest.

Spec is clear ("the engine computes coordinates as
(anchor_row + body_row, ...)") but I attempted to design *around* the limitation
before internalising it. Tooling implication: a `#region` directive that lets
a rule reference a named static cell would unlock fixed-column spawn, line
clearing, and game-over text without grammar-level changes.

### A3. OR-over-positions has no native form
*~5 min, could-have-known.*
"Freeze if any of N below cells is blocked" decomposes to N sub-rules — one per
candidate-blocking position. `!` (not-equal-field-6) and `%` (field-6-or-field-7)
are per-cell predicates only; there is no body-level OR across positions.

For tetris MVP this expands to: 4 freeze sub-rules for I-horizontal, 1 for
I-vertical, 3+2+3+2 for T0/T1/T2/T3. Total: **15 freeze sub-rules** for two
pieces. A rule-family generator that emits "any-of-these-cells-matches-pred"
expansions would compress this to one declarative line per orientation.

### A4. Two-timing-trigger ergonomics (user-prompted)
*Discovered during architecture review.*
I had defaulted to a single timing trigger for both fall and post-freeze
housekeeping (R-walk, spawn). User pointed out the spec supports multiple
`#timing` declarations, with `0`-interval ones acting as a frame-tick fallback
to delayed ones. Adopted `g 500` (delayed: fall + freeze) and `f 0` (immediate:
painters, R-walk, spawn).

Spec covers the declaration-order resolution explicitly — I read that section
but didn't *design against* it. The two-timing pattern is non-obvious enough
that it deserves an idiom note in the spec or skill: "use a `0`-timing for
state-machine housekeeping, a delayed timing for game-tick events."

### A5. `T` as trigger char retains 50ms-sleep semantics (user-flagged)
Listed in the spec's TODO section as a leftover from older code. User flagged
it before I tripped on it. Not exercise-blocking, but it's spec leftover that
will surprise some future author. A clean engine fix removes the asymmetry.

### A6. Wall-painter overhead
*~5 min during proposal, could-have-known.*
Drawing a 4-sided rectangular border requires either ~64 `^` initial-symbol
lines (one per cell, no range syntax) or a 4-painter state machine (8 rules).
Both feel disproportionate for what is conceptually "draw a rectangle". A
`#border` directive, or `^` syntax accepting position-pair ranges, would
collapse this to a single line.

Notable: the painter-state-machine works only because of toroidal wrapping —
each painter detects its corner by walking past it and finding the previous
painter's tail (an H cell where it expected empty). That's a clever but
brittle pattern; it relies on each painter starting at a cell the *previous*
painter has already coloured. Easy to subtly break.

**Update after slice-1 redesign**: replaced the 8 painter rules with a single
big-body rule (one P seed at centre, one rule whose body is the full 22x26
perimeter) once we committed to a fixed-size centred playfield. The big-body
form is *more compact* than painters (one 22-line body vs. eight rules) and
also dodges A6 entirely — there's no "draw a rectangle" loop because the
rectangle is just the literal RHS region. The painter approach only paid off
for terminal-fitting walls; once dimensions are fixed, monolithic-body wins.

## Build phase (slice 1)

### B1. Initial-symbol lines double-classify into the previous rule's body
*Mid slice 1, ~5 min from screenshot to root cause.*
Slice 1 originally used 8 painters and `^Aul` placed at the file end (after
the last rule). The screenshot showed the literal text `^Aul` written into
screen row 3 cols 0-3 alongside the rest of the painted wall. Reading
`grammar.cpp` lines 275-299: the parser classifies `^`-lines as initial
symbols (correctly), then *falls through* to the body-append branch
(`else if (!lhs.empty()) rule += line`), so the `^Aul` line *also* becomes
the next body row of the previous rule. Spec implies the line classes are
exclusive; parser disagrees.

**Workaround**: place all `^` lines before any `=` header so `lhs` is empty
when they're seen.

**Could-have-known if I read the parser**, but the spec presents the line
classes as exclusive, so reading the spec wasn't sufficient. A linter
("unexpected token in body of last rule" / "initial symbol after rules
extends rule body") would catch this in seconds. Or fix the parser to
`continue` after handling `^`.

### B3. Field 3 default = space = no-op, not "erase"
*~5 min from screenshot to root cause; could-have-known if I read apply_impl.*
First slice-1 attempt left `P` visible at the playfield centre. Header was
`==Pf` (4 chars, field 3 omitted, default = space per spec). I expected
"default space" to mean "erase the LHS anchor cell on apply". Reading
`apply_impl` at grammar.cpp:771: `if (rep != L' ') { ... write ... }`. A
literal space `rep` short-circuits the entire write block — **spaces in
body are unconditional no-ops**, including when they arise from field 3.

To erase the LHS anchor cell, field 3 must be `~`, which clears the
space-guard at line 771 and is then converted to space by line 772 inside
the write block.

The spec table is *technically* correct (default = space; "spaces are no-ops"
documented separately) but the casual reading "field 3 default writes nothing
visible at the third @" is *interpretable two ways* — "preserves whatever was
there" vs. "writes empty space". The first is what actually happens. A
worked example "to erase the anchor cell, use `~` not blank" would have
saved this round-trip.

### B4. Programs start unpaused (skill page is wrong)
Skill page asserts "Programs load paused unless they wire SPACE to
`#control <c> pause`". User reports startup is unpaused; verified in
`zahradnice.cpp:309`: `bool paused = false;`. The `#control` directive only
defines the *toggle* binding; it does not change the initial state.
Skill page needs a correction.

### B5. F12 screenshot capture is terminal-dependent
Engine code (`zahradnice.cpp:509-525`) handles `KEY_F(12)` correctly and
writes `screenshot_<timestamp>.{txt,ansi}` to the working directory. User
reports F12 produced no file in their terminal — almost certainly the
terminal emulator (GNOME-Terminal, Konsole, IDE shells) intercepts F12 for
its own UI, so the keystroke never reaches ncurses.

Workarounds: (a) paste screen text manually (what we're doing — works fine
for plain layouts but loses colour info), (b) add an in-program engine
action for screenshot, e.g. `#control X screenshot`, currently unsupported
(only quit/pause/clear/reset/return are recognised).

### B2. Fixed-size centred playfield needs one big body
*Mid slice 1, ~10 min of design churn.*
Pivoted from "terminal-fitting walls via painters" to "fixed 24x22 perimeter
centred on screen" at user's request. Considered: (a) ~64 `^Hxx` lines
(impossible — `^` position chars only address edges/centre, not arbitrary
offsets), (b) place 4 corner-sentinel non-terminals (impossible — `^` lines
can't place at *interior* offsets either), (c) one big rule body with the
entire perimeter encoded as RHS literal cells.

Picked (c). The body is 22 rows × 26 cols ≈ 600 chars — verbose but
mechanical and direct. Two pleasant side effects: collapses 8 painter rules
to 1, and encodes the *exact* fixed dimensions visibly in the cfg so a
reader sees the playfield outline at a glance.

This is interesting evidence that, in this language, *expanding the rule
body* is often cheaper than *adding state-machine non-terminals*. Tooling
implication: a generator that emits big-body "stamp" rules from a sketch
("here is a 24x22 rectangle, fill walls with H, mark spawn at top centre")
would be the highest-leverage primitive for setpiece scenery.

### B6. Off-by-one in body cell columns (V→H rotation)
*~10 min from screenshot to root cause; could-have-known with care.*
The V→H rotation rule produced a 6-cell I-H piece with gaps at offsets
(1, -1) and (1, +5) — i.e., the **last** intended write offset and one
internal write offset both shifted by one because I typed *two* spaces
between the `~~~~` block and the second `II` in body row 1 instead of
*three*. Result: the line was 18 chars instead of 19, and every cell
right of the missing space landed at offset c-1 from where it should.

The bug was visually invisible in the cfg ("~~II~~~~  II  IIII" looks
like a fine, symmetric pattern); only by counting columns and translating
to RHS-anchor offsets did the off-by-one surface. The piece "stopped
falling" because the partially-broken I-H no longer matched any fall
rule's LHS structural check.

Tooling implication (high-value): a linter that, for each rule, takes
the body and renders **per cell** which offset it maps to from the LHS
and RHS anchors, with a side-by-side diff. A two-column report showing
"LHS-cell @ offset (1, +2) | RHS-cell @ offset (1, +1)" for each body row
would have made this trivially visible. Even simpler: a `--ascii-render`
flag that visualises the rule's *effect* on a blank canvas (LHS as
"required" pattern; RHS as "after-apply" pattern) would have caught it
on first inspection. Same pattern of bug will recur in T-piece rotations
where bodies are larger and more asymmetric.

### B7. Body lines starting with `#` are silently eaten by the parser
*~5 min from screenshot to root cause; could-have-known after B1.*
The I-V freeze body had three rows of `##` (the bottom three rows of the
8-cell frozen-block write). At parse time, lines whose `line[0] == '#'`
hit the directive/comment branch in `grammar.cpp:195` and `continue` —
they're never appended to the rule body. Effective body length: 9 rows
instead of 12. Result: only the *top* row of `##` was written (because
that line started with `@#`), leaving 6 `I`s untouched in the lower
rows of the just-frozen piece.

Bug visible in screenshot as a half-frozen vertical I where the top
2 cells became `#` and the bottom 6 stayed `I`.

**Idiom (user-suggested)**: when a body needs cells that would put `#`
at column 0, indent the *entire* body by one space column. All anchor
offsets are preserved because they're relative; only the absolute body
coords shift, and shifting `@` markers along with the body keeps the
arithmetic identical.

This sits in the same family as B1 (parser line-classification
peculiarities not exposed by the spec). A linter that flags
"body-line-zero-char-is-syntactically-special" would catch both. Even
simpler: a documented warning in the spec ("**body lines starting with
`#`, `^`, or `=` are silently dropped — indent by one column to escape**").

### B8. Spawn-at-freeze-column edge case observed in play
*Surfaced during slice 4b validation; user-driven test.*
Architecture proposal accepted "spawn-at-freeze-column" for MVP, deferring
fixed-column spawn. A natural consequence: if a piece freezes against the
right wall, the R token walks up to that column and the spawn rule fails
the "7 empty cells to right" LHS check (cols overlap with the right wall).
R sits at the top of the playfield indefinitely; no new piece appears.

In one test run an I-V frozen at perimeter cols 20-21 produced exactly
this state (R at col 20 of a 24-col-wide perimeter, walls at cols 22-23,
spawn would need cols 21-27 empty — but col 22 is `H`).

Functionally this is a *second* silent-end condition (alongside
"spawn cells full of frozen blocks at top"). Both halt the game without
a verbose end screen. Player learns to keep pieces away from the right
wall during the lateral move, or to ESC.

Future fix path is unchanged: a horizontal R-walk-to-fixed-column phase
between the vertical walk and spawn would resolve both cases. Architecture
already supports adding it (the spawn rule's LHS predicate stays the same;
the new horizontal-walk rule is mutually exclusive on context).

### M1. Token budget is the dominant cost (meta-observation)
*User-raised at end of slice 4b.*
Even when the work proceeds without bugs, this exercise is **token-hungry**
in ways that compound. A breakdown of where the tokens went on this run:

- **Engine source reads**: every "why isn't this rule firing?" round-trips
  through `grammar.cpp` (~500 lines / ~3 K tokens per read). I had to do
  this for line classification (B1), the space-as-no-op rule (B3), the
  apply-vs-dry-run anchor logic (B6), and the header field positions.
  Each read is independently necessary because the spec doesn't surface
  the implementation invariants — but in aggregate it's the single
  largest token sink.

- **Screenshot reads**: even with `offset` + `limit`, a perimeter row is
  ~200 chars wide, so a 25-row read is ~5 KB. Multiple screenshots per
  slice. Reading the *whole* screen on a misread costs ~12 KB.

- **Rule-body iteration**: write rule → submit → fail → re-trace offsets
  → fix. The mental simulation of body-cell-to-screen-offset was the
  bug source in B6 specifically. Doing it at write-time costs no tokens
  but doing it at debug-time costs a re-read + re-trace cycle.

- **Cfg file is verbose by language design**: each rule is a header plus
  a 2D-grid body. Comments to make it human-readable add more. The 24x22
  perimeter rule alone is ~600 chars. The full slice 4 cfg is ~5 KB
  (~1.3 K tokens of "mostly mechanical" text).

**Tooling that would directly reduce token budget**, ranked by leverage:

1. **Linter (`zahradnice-check`)**: catches header field-count, @-count,
   body-cell-offset-alignment errors at write-time. Prevents the entire
   "fail → re-trace → fix" cycle. Would have caught B6 in 1 second.
   Implementation: shares `grammar.o`. Author estimates 1-2 days work.
2. **Coordinate-annotation pass on the linter (`--annotate` flag)**: the
   3-@ body is already its own visual rendering — the cells stand for
   themselves spatially. What the body *doesn't* show is the (dr, dc)
   offset of each cell *from the LHS anchor and the RHS anchor*. For B6,
   the body looked symmetric and fine; the bug was that the right-side
   `IIII` block was at body cols 14-17 instead of 15-18, which shifted
   every offset by -1. An annotation pass that prints body cells with
   their RHS-anchor offsets in the margin would have made the off-by-one
   self-evident. Earlier draft of this entry called for a "rule renderer";
   that's wrong — the rule already renders itself. Coordinate overlay is
   the missing piece, and it's cheap as a linter sub-feature.
3. **Headless replay tool**: scripted input, captured output. Eliminates
   F12 round-trip with the human. Reduces a single test iteration from
   "write → ask → wait for human → read screenshot" to "write → run".
   This is the single biggest **wall-clock** savings (token budget too,
   since I don't need to read 25-row screenshot ranges to verify simple
   things like "did the piece move?").
4. **Rule-family generator**: declarative piece-shape input, emits all
   the lateral/fall/freeze/rotation rule bodies. Compresses the cfg
   ~5-10x and eliminates per-rule body-geometry mistakes. Highest
   pay-off for *future* programs (this exercise's rules can be generator
   training data).
5. **Compressed rule preview / cfg minifier in repo tools**: a `--brief`
   reading mode for rule bodies that strips comments and whitespace —
   reduces token cost when re-reading my own output mid-session.

**Order of likely build**: 1 → 3 → 2 → 4. The linter is cheapest and
prevents the highest-volume class of friction; the headless replay
flips the dev loop fundamentally; the renderer is a natural extension
of the linter; the generator is the longer-horizon win.

### A7. Stacked-header savings smaller than hoped
*During user-feedback round.*
User reminded me of the multi-header / `*`-substitution mechanism. I
revisited the rule count expecting major savings; in practice only
**I-piece rotation pairs** (CW + CCW share a body because the I-tetromino is
2-fold symmetric) collapse cleanly. T-piece rotations all produce *different*
target shapes, so no body-sharing is possible. Painter normal-step rules
move in different directions per painter, so `*` doesn't collapse them.

Net saving: ~4 rule-bodies-worth of typing across the program. The mechanism
is real and worth using, but its scope is narrower than the language's
flexibility suggests.
