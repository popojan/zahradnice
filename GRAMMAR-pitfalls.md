# GRAMMAR pitfalls

Companion to `GRAMMAR.v2.md`. The reference describes *what the language is*; this document describes *what bites you when you write rules*. Each entry documents an engine quirk or design trap discovered the hard way during the tetris2 sessions, with a concrete symptom, the underlying cause, and how to avoid it.

Entries are roughly ordered by how often they recur in practice.

---

## 1. Empty cells are `~` after engine input, not `' '`

**Symptom.** A rule with `!` (not-equal-to-ctx) and `header.ctx = ' '` (literal space) fires on every empty cell in the playfield, immediately and continuously.

**Cause.** The matcher in `grammar.cpp` reads the screen cell into `ctx` and **converts `' '` to `'~'` before** the comparison `req == L'!' && ctx == rule.ctx`. So:

- `header.ctx = '~'` → `!` matches when cell is non-empty (including X, piece glyphs, walls). Almost always what you want.
- `header.ctx = ' '` → `!` *always matches* because converted screen `'~'` never equals literal `' '`.

**Avoid.** Any field-6 / field-7 (ctx / ctxrep) that is meant to align with empty space must be `~`, not literal space.

**See also.** GRAMMAR.v2.md §Body line 241: *"Spaces are always no-ops … to match a space cell, use `~`."*

---

## 2. `put(L' ')` writes nothing — use `erase()` (`~`) for spaces

**Symptom.** A rule that writes the text "Game Over" via `put` per character leaves the **piece's background colour visible through the gap between "Game" and "Over"**.

**Cause.** A literal space body cell is engine-no-op (same source line as #1). `g::put(L' ')` emits a literal space body cell — it neither matches nor writes. The cell behind it is whatever was there.

**Avoid.** When emitting text or filling cells with "blank":

```cpp
// Wrong: gap shows stale piece bg
rhs[{0, c}] = g::put(static_cast<wchar_t>(' '));

// Right: writes a real space terminal with rule's bg
rhs[{0, c}] = g::erase();
```

Same applies any time you want a "transparent erase" — use `erase()` (which emits `~`).

---

## 3. One ctx field per rule — `&` / `%` / `!` cells all share it

**Symptom.** You want a rule that fires when "above is wall H AND left is empty AND right is anything-but-X". You can't write it.

**Cause.** Header field 6 is a single character. Body cells use that one ctx for whichever predicate they carry:

- `&` matches `ctx`.
- `%` matches `ctx` OR `ctxrep` (field 7).
- `!` matches anything-except-`ctx`.

Multiple `&`/`%`/`!` cells in one rule **all reference the same ctx**. You cannot say "above ≠ H AND below ≠ C" in a single rule because both `!` cells would compare against the same field-6 character.

**Avoid.** Decompose into multiple rules. Conjunction within a rule is expressed by AND of body cells (each cell's predicate must match). Disjunction across orthogonal conditions is expressed by **emitting multiple rules** that share a body but have different ctx pairs.

Example (from `emit_signal_rise`): the `^` signal needs to stop at H **or** C. We split into two arrival rules — one with `ctx=H, &` cell at (-1,0), one with `ctx=C, &` cell. Both write `R` at the anchor; the engine fires whichever matches.

---

## 4. Idempotent rules explode the rule-application count

**Symptom.** The `{steps}` counter in the status line jumps by hundreds per fall step instead of a handful. Gameplay slows.

**Cause.** A rule that always-matches always-fires. Common shapes:

- A render rule like `==HfH77` with body `@@@` paints H over H every f-tick — fires once per H cell in the playfield, every tick.
- A rule whose LHS context is fully satisfied by its own RHS write — it re-creates its trigger condition.
- A one-shot draw rule (menu, banner, splash) that **paints its own anchor character somewhere in its output**. It correctly consumes the anchor at its own cell, so it looks one-shot — but it now matches at every copy it just painted, drawing the whole picture again offset from each one. Under `#timing T 0` that is an explosion; under a paced timing it is a slow drift. `programs/primes/index.cfg` drew a menu titled `P R I M E S` from an anchor `P`.

**Avoid.** For a draw rule, pick an anchor character the body never writes — that is why `programs/index.cfg` anchors on `Q` and `programs/sokoban/index.cfg` on `1`, neither of which appears in the menus they paint. Otherwise use **one-shot conversion**: write *lowercase* glyphs in the seed / move RHS, then have a converter rule `==hfH77` that turns lowercase into uppercase + bg=alias. Once converted, the lowercase glyph is gone and the conversion rule never refires.

Diagnostic: add `{steps}` to the status line during development. Compare against a known-good reference (original tetris ≈ 2 rule applications per fall step). Anything in the dozens per step is a red flag.

---

## 5. Memory-restore via `$` is the way to "tunnel through scenery"

**Symptom.** A non-terminal needs to traverse cells without overwriting them. Naive approach (just write the non-terminal at each step) destroys the cells behind it.

**Cause / mechanism.** GRAMMAR.v2.md §Local memory:

- When a rule writes a **terminal** char, the full struct (char + colours) is saved as the cell's memory.
- When a rule writes a **non-terminal**, only the *background* of memory is updated; the saved char + colours are preserved.
- A rule body cell `$` in RHS **restores** the cell to its saved struct.
- A rule writing a cell with `back='8'` (transparent) displays using the saved bg.

Combined: a rule with `header.replace = $`, `back = '8'`, and body `^` (or whatever) at `(-1, 0)` literally **moves a non-terminal one cell up while restoring the original cell behind it**. The traversed cell is unchanged in display because non-terminal writes don't touch the saved char.

**Pattern used.** The `^` rise rules in tetris2 (Bug B fix). The signal rises through stack X cells without disturbing them — when `^` moves on, X reappears verbatim.

**Apply when.** Any "send a signal across distance through occupied territory" need. Useful for cell-propagation puzzles, gravity-like animations, anywhere a non-terminal needs to coexist temporarily with terminal scenery.

---

## 6. Conjunction within a rule, disjunction via multiple rules

**Symptom.** "Fire game over if any of these 10 cells is non-empty." How?

**Cause.** A rule's LHS body cells are conjunctively matched — *all* must hold for the rule to fire. There is no `OR` operator within a single rule body.

**Pattern.** Emit one rule per disjunct, all sharing trigger and replace. Pre-spawn game-over uses this: 10 separate rules, each with `lhs[probe] = ctx()` for one specific probe. The engine fires whichever rule's probe currently matches X.

**Cost.** N disjuncts → N rules. If shared body is possible (same RHS, same other LHS cells), the bodies can be stacked under one body in the cfg via consecutive `=` headers — saves repetition but each header is still its own rule entry.

---

## 7. Wildcard `?` trigger destroys gameplay timing

**Symptom.** A rule with trigger `?` becomes a candidate on every f-tick. Sampler picks it disproportionately often vs scheduled triggers. Gameplay slows ~20×.

**Cause.** The engine's weighted-random sampler treats every applicable rule as a candidate. A `?`-trigger rule is applicable every step alongside the actual move/render rules; it dilutes the sampler.

**Avoid.** Use specific timing triggers (`f`, `g`, etc.). Reserve `?` for genuine "fire on any input including timer" cases — and even then, reach for a specific timing trigger first.

---

## 8. `move_diff` returns cells *outside* the overlap

**Symptom.** A piece's lateral / rotation / fall (for multi-row pieces) leaves the body in mixed-case state — some cells uppercase (rendered), some lowercase (just-moved seed). Render LHS expects all-lowercase and never fires.

**Cause.** `g::move_diff(old, new)` returns `(erase = old \ new, write = new \ old)` — the **diff**, not the full target. Cells in the overlap (`old ∩ new`) remain whatever they were on screen before the move (uppercase glyph from previous render).

**Avoid.** Write the seed / lowercase at **all** cells of `new`, not just `move_diff.write`:

```cpp
// Wrong: leaves overlap region in old uppercase state
g::mark_each(rhs, md.write, g::put(seed));

// Right: every cell in the new shape becomes seed
g::mark_each(rhs, g::difference(new_cells, {{0, 0}}), g::put(seed));
```

Cells in `md.erase` (`old \ new`) still get erased separately. Cost: a few extra single-cell writes per move rule.

---

## 9. Non-terminal letters collide with displayable text

**Symptom.** A status / overlay rule writes the string "Game Over". The letter `v` mysteriously gets erased over time.

**Cause.** The engine's non-terminal set V contains every char that has appeared as field-1 of any rule. Cells in the screen at those positions are tracked. If a *display* rule writes a letter that is also a non-terminal, the engine treats those text cells as live non-terminals, and any matching rule fires on them.

**Avoid.** Pick non-letter glyphs for internal-only non-terminals: `|`, `.`, `+`, `^`. Avoid GRAMMAR special chars (`@ # ~ & ! % * $ ^ ?`) and digits (which are colour codes in headers).

In tetris2 the gravity particle moved from `v` (collided with "Game Over"'s `v`) to `|`.

---

## 10. Single timing trigger per main-loop iteration

**Symptom.** The g-tick (move) and f-tick (render) never share an iteration. There is always a refresh between them — visually, a 1-step gap where the piece flashes.

**Cause.** `zahradnice.cpp`'s main loop fires *one* timing trigger per loop iteration: interval > 0 trigger first (by hash order), then interval == 0. So `g` (move, interval 500) and `f` (render, interval 0) are always served on different iterations.

**Implication.** Don't design rules assuming move + render fire together. The structural 1-step bg-clear flash between them is unavoidable unless seed-then-fill flips the cell-write balance.

**Tweak.** `#timing` declaration order matters: `cfg.timing_chars` is `unordered_map<wchar_t, int>` so iteration order is hash-driven. Empirically declaring `f 0` before `g 500` reduces visible flash.

---

## 11. Pre-spawn game-over `!` ctx=`~` matches gravity particles

**Symptom.** Multi-row line clear. Many `|` (gravity particles) rise simultaneously. Game over fires prematurely while the stack is still well below the spawn row.

**Cause.** Probe rule with `lhs[probe] = not_ctx()` and `header.ctx = '~'` matches *anything non-empty* — which includes the `|` particles transiently in the spawn area.

**Avoid.** Use `&` ctx=X (matches the durable frozen marker only). Frozen pairs always have X at every even col, so even-col probes alone fully cover stack detection. Odd-col probes never match X (frozen pairs have piece glyph at odd col) — they're dead but harmless if left in.

---

## 12. Game over needs *many* spawn-area probes (or shape-aware post-spawn rule)

**Symptom.** A piece spawns into a state where it cannot fall (some cell below body is wall/X) AND cannot freeze (the freeze rule's `(-1, 0) = empty` check fails — at the spawn row, `(-1, 0)` is C beacon or wall H). The piece is movable but game over never fires.

**Cause.** Two issues, often combined:

1. The pre-spawn 10-probe rule's coverage is incomplete. 3 probes don't catch all 7 pieces' spawn-body cells; ~10 are needed.
2. Even with full pre-spawn coverage, you must decide: fire pre-spawn early (loses the "last piece freezes at top" UX) or post-spawn (need a shape-aware rule mirroring `emit_freeze`'s structure).

**Pattern.** The post-spawn "stuck-at-top" rule mirrors freeze's per-`(piece, orientation, below_cell)` shape, with `!` at `(-1, 0)` (above ≠ empty) and Game Over text in RHS. Single ctx (`~`); `!` covers wall H, beacon C, and overhang X uniformly. Shape match is required to distinguish active piece anchors from frozen X+glyph pairs mid-stack.

---

## 13. Rule body `lit(p.glyph)` per cell is verbose; `&` with `header.ctx=p.glyph` is one cell

**Symptom.** A piece-shape match using `g::mark_each(lhs, cells, lit(p.glyph))` writes the glyph at every body cell — N body cells in the cfg. The original tetris.cfg uses one `&` cell + `header.ctx=glyph` and is much more compact.

**Trade-off.**

- `lit(p.glyph)` per cell — ✅ leaves ctx free for other body cells (e.g. `%` at below_cell with `ctx=H, ctxrep=X`); ❌ verbose.
- `&` + `header.ctx=p.glyph` — ✅ single cell encodes shape match; ❌ ctx is consumed, conflicts with any other `&`/`%`/`!` cell needing different ctx.

**Decision rule.** Use `lit` when ctx is needed for `%` somewhere else in the body (e.g. freeze's below_cell `%` matching wall-or-X). Use `&` when ctx is otherwise free.

---

## 14. Idempotent fix: lowercase seed → uppercase render is the canonical pattern

**Symptom.** A render rule that matches the rendered (uppercase) body and rewrites it (uppercase) is idempotent — fires every f-tick. Rule application count balloons.

**Pattern.**

1. Move / spawn rules write **lowercase** body cells (the "dirty" / unrendered state).
2. The render rule matches lowercase, writes uppercase + bg=alias.
3. After the render fires once, lowercase cells are gone — the render rule cannot match again until another move re-introduces lowercase seeds.

This is exactly the original `tetris.cfg` `j → JJ`-style pattern.

---

## 15. Frozen-cell colour preservation requires X+glyph 2-col-aligned encoding

**Symptom.** Line-clear gravity moves frozen pairs down a row. The new position is rendered with the rule's bg; piece colour is lost.

**Pattern.** Encode frozen cells as **X + piece-glyph pairs** at 2-col-aligned positions: X at even col, glyph at odd col. The line-clear v-swap rule (one header per piece colour, with `ctx=glyph, ctxrep=lower(glyph)`) shifts the X plus its colour-glyph one row down, preserving colour through the shift.

Each gravity rule must set `back='0'` to reset memory.bg of cells the v vacates; otherwise ghost-coloured trails appear above the new stack top.

---

## 16. `back='8'` (transparent) — semantics depend on terminal vs non-terminal write

**Symptom.** A move rule with `back='8'` doesn't clear the previous render's coloured trail.

**Cause.** With `back='8'`, the displayed bg uses *saved memory bg*. If memory bg was previously set to a piece colour (by a rendered cell), the trail lingers.

**Pattern.**

- Move rule: `back='0'` clears trail bg-colour from cells the piece vacates.
- Render rule: `back=alias` paints the piece's colour bg.
- Move rule: `fore='0'` (black) makes the briefly-visible glyph letters invisible against black bg during the 1-step gap before render re-paints. (User-validated.)
- Gravity rules: `back='0'` to reset memory.bg of cells the v passes through.

---

## 17. `#control X clear` alone does nothing — engine actions need a *rule* to fire them

**Symptom.** A program declares `#control x clear` (intending the `x` key to restart the level). Pressing `x` does nothing.

**Cause.** `#control <char> <action>` only registers the binding in `engine_actions[char] = action`. The action fires **only when a rule whose `sound` field equals `char` is applied**. A keypress on its own — even one matching the control char — does not fire the action; it only triggers rules whose `trigger` field matches.

**Avoid.** Pair the directive with at least one always-applicable rule. Convention: uppercase = control char (sound), lowercase = trigger key. Body is `@@@` (anchor only, no-op).

```
#control X clear
=XJxJ
=XKxK
=XUxU
=XHxH
@@@
```

For each non-terminal that's reliably on screen during the program (here, the four snake-head glyphs J/K/U/H), one rule with `sound=X, lhs=<NT>, trigger=x, replace=<NT>` (idempotent — replace = lhs). Pressing `x` matches one of them; the engine action fires once.

**See also.** `programs/sokoban/rules.cfg` lines 3-4 + the `=XPxP` rule on line 21 for the canonical sokoban pattern.

---

## 18. `memory.c` is sticky by default; opt out with `#transient`

**Symptom 1.** A non-terminal moves across a frozen cell (e.g. tetris's `^` rising through an X+letter pile). After the non-terminal passes, the original frozen char reappears via `$` rep — but only if the engine treated the moving char as transient. If it didn't, the frozen cell is permanently overwritten and gravity / restore breaks.

**Symptom 2 (less obvious).** A `$` memory-restore writes the *correct* char to screen and memory, but the cell silently fails to be eligible for any later rule whose lhs is that char. (E.g. `==XTv...` never fires on cells that the `^`-walk previously traversed, even though they display as X.) This was a separate engine bug — `apply_impl` was writing `rep` (`$`) to the `x` map instead of the resolved char `d.c`. Fixed in 2026-05-06; pair with the symmetric memory.c semantics below.

**Engine semantics (post-2026-05-06).**

- Every non-empty body write updates `memory[r,c]` to the full struct `{c, fore, back, fore_attrs, back_attrs}` of the written cell. This is the **default**.
- Chars listed in `#transient <chars>` are exceptions: writes of those chars only update `memory[r,c].back` (for transparent-overlay support); `memory[r,c].c` and other fields are preserved.
- `$` rep reads `memory[r,c]` and writes the saved struct verbatim. With sticky memory, `$` always restores the most recent terminal write at that cell.
- The `x` map (engine's NT scheduler) is kept in sync with `screen_chars` and `memory.c`; rules whose lhs matches the resolved char will see the cell.

**When to declare `#transient`.**

- *Moving particles*: tetris's `^` (signal-rise marker) and `v` (gravity-fall marker) need to traverse frozen scenery without overwriting it. Declare `#transient ^v`.
- *Rendering cursors* / *transparent overlays*: chars that draw on top of stable scenery and disappear without trace.
- *Anything that should not be remembered*: if you'd be confused by `$` restoring this char somewhere later, mark it transient.

**When NOT to declare `#transient`.**

- Frozen / structural markers (tetris `X`, walls `#`, status glyphs): these *are* the scenery. They must be sticky so `$` can restore them.
- Piece glyphs that get re-rendered every tick (J, L, O, …): they're written non-transiently; the next render cycle naturally overwrites them.

**Concrete worked example (tetris).**

`programs/tetris/index.cfg` declares `#transient ^v`. Frozen cells are stored as X+letter pairs. The `^` rise rule (`==^T$78-`) moves `^` upward through a column of X cells; each step:
1. Writes `^` at the new position (transient → memory unchanged).
2. Writes `$` rep at the old position → engine reads memory, restores X with the original colour. Both `screen_chars` and `x` map agree the cell is X.

If `^` were *not* transient, step 1 would overwrite the X in memory; step 2's `$` restore would then read whatever was last terminally written (often a piece glyph or empty), and the column would corrupt.

**Note on the deprecated asymmetry.** Pre-2026-05-06, the engine had a different rule: non-terminal writes left `memory.c` unchanged automatically; only terminals updated it. That was the source of multiple subtle bugs (naked-X corruption being the canonical one) because it conflated "this char is structural / persistable" with "this char is a non-terminal". `#transient` makes the distinction explicit.

---

## 19. `^` seeds (and any non-`=` line) after a rule are appended to that rule's body

**Symptom.** A wrapper file does `#include rules.cfg` followed by `^` seed lines for the level layout. The last rule of `rules.cfg` silently stops matching — its dependents (e.g. the head-move rule that needs `vv` above) never fire and the program stalls. No parse error, no warning.

**Cause.** The parser's main loop (`grammar.cpp:200-313`) checks line-type in this order: `#` comment (with `continue`), `^` seed (record-and-fall-through), `=` new rule, **else** append to current rule body. The `^` handler does *not* `continue` — it just pushes to the seed vector and falls through. The next branch (`else if (!lhs.empty())`) then appends the line to the rule currently being built. After `#include rules.cfg` is expanded, the wrapper's seed lines fall just past the included file's *last* rule, so they get glommed onto its body. Dry-run match then iterates body cells that look for non-existent characters on screen → match always fails.

**Symptom is direction-of-flow:** the corruption only hits the *last* rule because every previous rule is closed by the next `=` line. Move a single `=...` rule between the include and the seeds and the bug vanishes (the seeds now corrupt that rule, which may or may not matter).

**Avoid.** Place all `^` seed lines *before* `#include`, or before any rules. The wrapper pattern that works:

```
#help …
#control X clear

^
^zxX
^zxX
…
^QCC

#include rules.cfg

# wrapper-only rules (e.g. restart) come after the include
=XJxJ
…
@@@
```

The same rule applies to any non-`=` content (comments after the first column, blank lines with whitespace) appearing after rules — they too get appended. Strict file hygiene (only `=` lines and rule-body cells in the rule-section) is the safe convention.

**Static-check candidate.** A linter could warn when a `#include` is followed by `^` / non-blank-non-`=` lines without an intervening `=`-rule. See `backlog/research/zahradnice-check.md`.

---

## 20. Rule `<score> <weight>` tail is positional (offset 10) — a single space fails silently

**Symptom.** You add a score to a rule header, e.g. `=Q.T~38 2` (want reward +2) or `=SXw~38^ -1`. The program runs without error but the score is wrong — `=Q.T~38 2` scores 0, `=SXd~38> -1` scores +1. No parse error; the rule just behaves as if mis-scored.

**Cause.** The header is parsed **positionally**, not space-delimited. From `grammar.cpp`: fore=`lhs[5]`, back=`lhs[6]`, ctx(field6)=`lhs[7]`, ctxrep(field7)=`lhs[8]`, then the score/weight come from `parse_ints<2>(lhs.substr(10), …)` (only if `lhs.size() > 10`). So position 9 is an ignored separator and the score must begin at **position 10**. `=Q.T~38 2` is only 9 chars — the trailing ` 2` is read as field6=`' '` and field7=`'2'`, never as a score. `=SXd~38> -1` puts `-` at position 9 (separator) and `1` at position 10, so it parses **+1**, not −1. The spec's "a single space separates the field block from the optional tail" is misleading for short headers.

**Avoid.** Pad so the **number starts at position 10** (= marker + 8 field chars + 1 separator). Count the field-block chars after `=`:
- Header filled through f5 (e.g. `=Q.T~38`, 7 chars): need 3 spaces → `=Q.T~38   2`.
- Header filled through f6 (e.g. `=SXd~38>`, `=SXw~38^`, 8 chars): need 2 spaces → `=SXd~38>  -1`.

The padding spaces become field6/field7 (default-equivalent when the body has no `&`; otherwise keep the real f6/f7 chars and only pad the still-missing positions). **Always verify with `zahradnice-check explain --line N` — it prints `reward=` and `weight=`.** Negative numbers parse fine once positioned correctly.

**Static-check candidate.** A linter could flag a header whose trailing integer lands inside a field-block position (likely a mis-positioned score), or whose intended score didn't parse. See `backlog/research/zahradnice-check.md`.

---

## Adding new entries

When a future session discovers a new gotcha:

1. Add an entry here with **Symptom / Cause / Avoid** sections.
2. Cross-reference from the relevant `genlib_lessons_session_N.md` memory.
3. If the gotcha implies a static-check candidate, note it in `backlog/research/zahradnice-check.md`.

---

## 21. `#include` with an absolute path fails silently — zero rules loaded

**Symptom.** A wrapper cfg runs but nothing happens; only the wrapper's own
rules exist. No parse error.

**Cause.** Include resolution prepends the including file's directory to the
path unconditionally (`dir + "/" + include_path`), so an absolute path
becomes a nonexistent relative one and the include contributes nothing.

**Avoid.** Always include by relative path (relative to the *including
file*). Diagnose in one call: `zahradnice-check why CFG --screen DUMP
--trigger T` prints a rule census — a suspiciously small "Excluded (N
rules)" count means the include never loaded.

---

## 22. A tiny weight does not make an event rare once it is the only applicable rule

**Symptom.** A "rare" event (lightning at weight 0.001) fires at effectively
every step in some phase of the program; two "environments" differing only
in that weight behave identically.

**Cause.** Selection is weight-proportional over the *applicable* set. In a
jump chain, rarity is only relative to co-applicable mass: when the field
saturates and competing rules (growth into empty cells, etc.) stop being
applicable, the rare rule is the entire mass and fires with certainty.

**Avoid.** Put genuinely rare drives on their **own trigger char** and
control their rate by cadence — `#timing` interval interactively, input
composition headless (the drive-in-quiescence pattern: `TT…TlTT…`). Weights
tune *relative* rates among co-applicable rules only.

---

## 23. Multi-glyph sprites: every rule needs an anchor-disambiguating body cell

**Symptom.** A sprite rendered with the same non-terminal at several cells
(e.g. a cursor drawing two `>`) misbehaves nondeterministically: an action
rule sometimes writes one row off, into a neighbouring structure — and
validation runs can pass on a lucky draw.

**Cause.** A rule anchored on that glyph is applicable at *each* copy; the
sampler picks any of them, and body offsets are applied relative to the
chosen copy.

**Avoid.** Give every rule anchored on a repeated glyph a body cell that
only matches from the intended copy (e.g. `>` at (1,0) pins the top
bracket). Audit *all* rules on that lhs, including passive ones — two
anchorings with disjoint footprints can even co-fire in one multithreaded
batch (a tax rule double-charged this way).

---

## 24. Score/weight tail requires the full field block — truncated header + tail misparses silently

**Symptom.** A rule authored as `==DTC 0 0.25` (short field block, then
score/weight tail) runs with weight 1 — and worse, the tail bytes are
consumed as header fields: ctx becomes `' '`, ctxrep `'0'`, and the
remainder parses as a bogus reward. No warning; sampling and scoring are
silently wrong.

**Cause.** Header fields are positional. Omission works only by
*truncation* (stopping early); there is no way to skip middle fields. A
tail after a short block lands in the ctx/ctxrep positions.

**Avoid.** When attaching ` <score> <weight>`, always emit all nine field
positions first, e.g. `==DTC78   0 0.25` (fg `7`, bg `8`, blank
ctx/ctxrep). Verify with `zahradnice-check explain --head '...'` — it
prints the parsed weight. (Caught this way in the night-4 generator,
2026-08-22.)

---

## 25. A program launched from a menu inherits the caller's screen

**Symptom.** A program runs fine on its own (`./zahradnice path/to/prog.cfg`) but
appears to hang when chosen from a menu: its status line shows, the step counter
sits still, and the menu is still on screen underneath.

**Cause.** Program switching is compositional by design — "derivation state
(screen contents) flows between programs" (GRAMMAR.md). A program whose seeds do
not cover the field therefore starts on top of the caller's picture. If its rules
need empty cells, they find none. `experiments/convergence/contact.cfg` seeds a
single `^Acc`: launched from a menu that `A` lands in the middle of the menu box,
is walled in by its text, and the only applicable rule left is the one that kills
it — an absorbing state reached on move one.

**Avoid.** Every program reachable from a menu must either open with a bare `^`
(clear) or flood the field (`^.**`, `^0**`). Note `start()` only tests `g.S[0]`:
a `^` that is not the **first** seed is placed as an ordinary symbol and clears
nothing. Seeds may arrive via `#include` (the sokoban levels inherit theirs from
`rules.cfg`), so audit the included text, not just the file.

Cheap check — a program that clears cannot be affected by what preceded it:

```sh
# every seed line of a launch target; the first must be `^`, or one must flood
grep '^\^' programs/foo.cfg
```

(Found when Contact process hung after being reached from the new Evolution
submenu, 2026-08-26.)

---

## 26. A control key needs an anchor that exists in *every* reachable state

**Symptom.** `q` (or any `#control` key) works sometimes and not others — or
works for a while and then stops, leaving the program unquittable.

**Cause.** An engine action needs a rule to fire it (#17), and that rule needs
its anchor character to be on screen *at the moment the key is pressed*. Two
ways to get this wrong:

- **Anchoring on a head.** A machine's head is in exactly one of its states at a
  time. `programs/primes/04-packed.cfg` listed only `>` and `<` while its head
  also passes through `{ } ? , A ) " Y ; ' _ | ] ^` — measured, `q` reached it at
  **7 of 41** sampled moments.
- **Anchoring on something the program can consume.** An absorbing state may
  erase the very character the rule needs.
  `experiments/convergence/contact.cfg` anchors on `A`, and its all-empty state
  is absorbing — so the key died exactly when the run was over.

**Avoid.** Anchor on the seeded scenery (a margin, a wall, a row header, the
origin column) — something the rules never overwrite. Where the field itself can
empty out, note that a cell erased with `~` is still in the `x` map as a space,
so `=q q~` with a bare `@@@` body covers the absorbing state.

Check it rather than reasoning about it — dump the screen at many step counts and
intersect the character sets; what survives every sample is what is safe to
anchor on:

```sh
for k in 5 40 400 4000 30000; do
  ./zahradnice-headless prog.cfg --threads 1 --max-steps $k --input @ticks \
    | tail -n +2 | fold -w1 | sort -u
done   # then intersect
```

(Both cases found while wiring the primes and evolution submenus, 2026-08-26.)
