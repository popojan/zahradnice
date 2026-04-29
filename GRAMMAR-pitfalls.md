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

**Avoid.** Use **one-shot conversion**: write *lowercase* glyphs in the seed / move RHS, then have a converter rule `==hfH77` that turns lowercase into uppercase + bg=alias. Once converted, the lowercase glyph is gone and the conversion rule never refires.

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

## Adding new entries

When a future session discovers a new gotcha:

1. Add an entry here with **Symptom / Cause / Avoid** sections.
2. Cross-reference from the relevant `genlib_lessons_session_N.md` memory.
3. If the gotcha implies a static-check candidate, note it in `backlog/research/zahradnice-check.md`.
