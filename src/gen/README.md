# genlib

Authoring-time helpers for emitting zahradnice `.cfg` programs from C++.
Generators describe rule **intent** via enum-tagged predicates; genlib emits
the syntax — including the metasymbols (`~ & ! % $ @`), positional fields,
indent-escape, and boundary anchors. No `libgrammar` dependency.

Stable, validated by three generators (`tetris_gen.cpp`, `animation_gen.cpp`,
plus the Python POC `scripts/tetris_generator.py`). Will evolve as more
generators land.

## Quick start

```cpp
#include "genlib.h"
#include <iostream>
namespace g = genlib;

int main() {
    g::LhsPattern lhs;
    lhs[{-1, 0}] = g::lit(L'H');     // wall above
    lhs[{ 1, 0}] = g::empty();       // empty cell below

    g::RhsPattern rhs;
    rhs[{1, 0}] = g::put(L'X');      // write X below

    std::cout << g::emit_rule(
        g::header(L'A', L'g', g::erase()),    // lhs A, trigger g, erase anchor
        g::emit_body_vertical(lhs, rhs));
}
```

Build by linking `libgenlib.a`. See `Makefile` targets `gen-tetris`,
`build/animation_gen`.

## Types

### Cell vocabulary (LHS predicates)

| Constructor       | Body glyph | Meaning                                     |
|-------------------|------------|---------------------------------------------|
| `lit(c)`          | `c`        | literal char match                          |
| `empty()`         | `~`        | empty cell                                  |
| `ctx()`           | `&`        | matches header field 6                      |
| `not_ctx()`       | `!`        | not equal to header field 6                 |
| `ctx_or_rep()`    | `%`        | equals header field 6 **or** field 7        |

### Cell vocabulary (RHS actions)

| Constructor       | Body glyph | Meaning                                     |
|-------------------|------------|---------------------------------------------|
| `put(c)`          | `c`        | literal char write                          |
| `erase()`         | `~`        | write space (clear cell)                    |
| `write_ctx()`     | `&`        | write header field 7                        |
| `write_memory()`  | `$`        | restore from local memory                   |
| `preserve()`      | ` `        | no-op (default; only meaningful in Header)  |

Absent cells in `LhsPattern` = no constraint. Absent cells in `RhsPattern` =
no-op (preserve).

### Header

```cpp
struct Header {
    wchar_t sound = L'=';        // field S; '=' = no sound
    wchar_t lhs;                 // field 1, non-terminal
    wchar_t trigger;             // field 2, key or timing char
    Write   replace = preserve();// field 3, what's written at the anchor
    std::optional<char>    fore, back;     // fields 4, 5
    std::optional<wchar_t> ctx, ctxrep;    // fields 6, 7
};
Header header(wchar_t lhs, wchar_t trigger, Write replace = preserve());
```

The `header(...)` factory covers the common case in one line. Set the
optional fields directly when needed (colours, `&`/`%`/`!` bindings).

## Emission

| Function                                   | Output                                |
|--------------------------------------------|---------------------------------------|
| `emit_header(h)`                           | header line, no newline               |
| `emit_body_vertical(lhs, rhs)`             | LHS region above boundary, RHS below  |
| `emit_body_horizontal(lhs, rhs)`           | LHS region left of boundary, RHS right|
| `emit_rule(h, body)`                       | header + `\n` + body                  |

**Boundary direction convention** (per `feedback_horizontal_body_preference`
memory): match the rule's action axis. Falls/freezes/R-walks → vertical;
lateral moves / rotations / spawns / horizontal painters → horizontal.

**Indent-escape** (B7 in friction journal): bodies whose lines would start
with `#`, `^`, or `=` get a leading-space added to every line so the parser
doesn't silently drop them. Automatic — generators don't think about it.

## Geometry primitives

```cpp
struct Shape { std::vector<Cell> cells; Cell anchor = {0, 0}; };

std::vector<Cell> terminal_cells(const Shape&, int grid_w=1, int grid_h=1);
std::vector<Cell> shifted(const std::vector<Cell>&, int dr, int dc);
CellSet            shifted(const CellSet&,           int dr, int dc);
CellSet            difference(const CellSet&, const CellSet&);
CellSet            as_set(const std::vector<Cell>&);

Cell rotation_anchor_shift(Cell from_anchor, Cell from_pivot,
                           Cell to_anchor,   Cell to_pivot,
                           int grid_w=1, int grid_h=1);
```

Game-specific bundles (`Orientation`, `Piece`, `Sprite`) belong in the
generator, not here. Geometry helpers stay free-function-oriented so future
primitives accumulate without bloating any single struct.

## Bulk pattern construction

```cpp
template <class CellRange>
void mark_each(LhsPattern& p, const CellRange& cells, Match m);
template <class CellRange>
void mark_each(RhsPattern& p, const CellRange& cells, Write w);
```

Used in every rule emission to avoid the `for (cell : cells) p[cell] = …`
boilerplate. Accepts `std::vector<Cell>`, `CellSet`, or any iterable of
`Cell`.

## Move-diff helpers

For any rule that moves a shape (tetris fall/lateral/rotation, animation
frame transition, hypothetical sokoban box-push):

```cpp
struct MoveDiff { CellSet erase, write; };
MoveDiff move_diff(const CellSet& old_cells, const CellSet& new_cells);

// Header.replace decision: glyph if new shape covers anchor, else erase.
Write replace_for_move(const CellSet& new_cells, wchar_t glyph);
```

`move_diff` returns the minimum-RHS sets — caller still drops `{0, 0}` from
`erase` if the anchor is handled by `Header.replace` (typical for tetris).

## ASCII art loader

For sprite scenery and animation frames where cell-list construction is
tedious:

```cpp
using ArtMap = std::map<Cell, wchar_t>;
ArtMap parse_art(const std::string& art, char anchor_marker = '@');

LhsPattern art_lhs(const std::string& art, char anchor_marker = '@');
RhsPattern art_rhs(const std::string& art, char anchor_marker = '@');

struct DiffResult { LhsPattern lhs; RhsPattern rhs; };
DiffResult art_frame_diff(const std::string& a, const std::string& b,
                          char anchor_marker = '@');
```

The marker char identifies the anchor cell (becomes `(0, 0)` in patterns).
Spaces are no-cell. Every other char becomes a literal-glyph cell.

`art_frame_diff` is the canonical animation builder: LHS = full frame_a;
RHS = erase cells in `a \ b`, put cells in `b \ a`, put the new glyph where
the position is in both but the glyph differs. Cells unchanged across
frames produce no RHS entry (preserve).

```cpp
auto d = g::art_frame_diff(frame_a, frame_b);
std::cout << g::emit_rule(g::header(L'Y', L'T', g::put(L'Z')),
                          g::emit_body_vertical(d.lhs, d.rhs));
```

A bonus consequence: emitted bodies *visually contain the original art*
because the diff's RHS occupies the same body-grid positions as the source
ASCII. Generated `.cfg` files read like authored ones.

## Pattern cookbook

Recipes for the recurring shapes that have appeared across multiple generators
or are worth reaching for as named idioms. Each entry: *use case → code →
why it works → when not to use*. Cross-references to
[`GRAMMAR-pitfalls.md`](../../GRAMMAR-pitfalls.md) where relevant.

### 1. One-shot lowercase→uppercase converter

**Use case.** Paint static scenery (walls, beacons, decorations) once without
firing the rule every f-tick.

```cpp
// Seed places lowercase 'h' at every wall cell.
// Converter fires once per cell, replacing 'h' with 'H' + bg=white.
// After conversion, lowercase cells are gone — the rule never refires.
auto h = g::header(L'h', L'f', g::put(L'H'));
h.fore = '7';
h.back = '7';                  // bg=white for the wall; or piece colour
g::LhsPattern lhs;             // empty: no extra context
g::RhsPattern rhs;             // empty: header.replace handles the write
std::cout << g::emit_rule(h, g::emit_body_horizontal(lhs, rhs));
// Emits:  ==hfH77 \n @@@
```

**Why it works.** A render rule that always matches always fires
(see pitfalls §4). The lowercase glyph acts as a *single-use trigger*:
once converted, the LHS no longer matches that cell. Any number of
cells can be "primed" by the seed; each gets exactly one rule
application.

**Don't use.** When the rendered cell legitimately needs to change every
frame (e.g. a blinking caret).

### 2. Full-body atomic per-orientation render

**Use case.** Rendering a multi-cell sprite (tetris piece, animated
character) atomically — every body cell painted in **one** rule application
to avoid the partial-piece flicker that comes from per-cell rules racing
across multiple ticks.

```cpp
// Move / spawn rules write LOWERCASE body cells (the "dirty" / unrendered
// state). The render rule matches all-lowercase and writes uppercase +
// bg=alias.  Per orientation, one render rule.
auto cells = terminal_set(orientation);
auto seed  = std::tolower(piece.glyph);

g::LhsPattern lhs;
g::RhsPattern rhs;
for (auto& c : g::difference(cells, {{0, 0}})) {
    lhs[c] = g::lit(seed);          // expects lowercase (just-moved) state
    rhs[c] = g::put(piece.glyph);   // writes uppercase + bg=alias
}

auto h = g::header(seed, L'f', g::put(piece.glyph));
h.fore = static_cast<char>(piece.glyph);
h.back = static_cast<char>(piece.glyph);   // bg=alias dictionary lookup

std::cout << g::emit_rule(h, g::emit_body_horizontal(lhs, rhs));
```

**Why it works.** The match-once-then-vanish trick from Recipe 1, scaled
to a multi-cell shape. After the render fires, lowercase cells are gone;
the render rule cannot refire until another move re-introduces the seed.
Every body cell is written in one rule application — visually atomic.

**Don't use.** Single-cell sprites where flicker isn't observable — a
plain idempotent painter is simpler. Or sprites whose colour changes
every frame independent of position — a different mechanism is needed.

### 3. X+colour 2-col-aligned pair encoding

**Use case.** Pieces freeze and stack; line-clear gravity must shift frozen
cells down preserving their piece colour.

**Encoding.** Each frozen piece-cell occupies a 2-col-aligned terminal
**pair**: `X` (universal frozen marker) at the even col, the piece glyph
(`I`/`T`/`J`/`L`/`O`/`S`/`Z`) at the odd col. The piece glyph is what
carries the colour; X is what the gravity rule pivots on.

```cpp
// Freeze writes lowercase x + lowercase piece-glyph (per Recipe 1, then
// a converter promotes them).
for (auto& c : g::difference(piece_cells, {{0, 0}})) {
    rhs[c] = (c.second % 2 == 0)
        ? g::put(L'x')                           // even col → x marker
        : g::put(std::tolower(piece.glyph));     // odd col → colour glyph
}
```

**Line-clear gravity rule** (one header per piece colour, all sharing
one body):

```cpp
for (auto& p : pieces) {
    auto h = g::header(syms.frozen, L'f', g::put(syms.gravity));
    h.ctx    = p.glyph;                           // upper-case glyph at +1
    h.ctxrep = std::tolower(p.glyph);             // lower-case after shift
    h.back   = '0';                               // CRITICAL: clear trail bg
    // shared body uses `&` (write_ctx) at (1, +1) to drop the colour
    // glyph one row down.
}
```

**Why it works.** `&` cells in RHS write `header.ctxrep`. Each stacked
header sets ctx/ctxrep to its piece colour, so the same body-shape rule
serves all 7 colours. The X marker uniformly anchors the gravity logic;
the colour glyph rides along.

**Don't use.** Single-colour stack mechanics — just one glyph suffices,
no pair needed.

**Pitfall reference.** §15 of `GRAMMAR-pitfalls.md`: every gravity-shift
rule must set `back='0'` to reset memory bg of vacated cells, otherwise
ghost-coloured trails appear above the new stack top.

### 4. `^` memory-restore signal propagation

**Use case.** A non-terminal needs to traverse the playfield **without
disturbing** the cells it passes through. The motivating use is the
post-freeze walker (Bug B fix in tetris2): R can't safely walk up
through frozen X cells, but `^` can tunnel through them.

```cpp
// `^` rises through any cell of class C (e.g. empty, or X), one cell per
// f-tick. Header replace=$ restores the LHS anchor cell from memory;
// back=8 displays via saved bg. Body's `&` cell at (-1, 0) matches "above
// must equal ctx (= the cell class to tunnel through)".
auto h = g::header(L'^', L'f', g::write_memory());
h.fore = '7';
h.back = '8';                  // transparent: use saved bg
h.ctx  = L'~';                 // tunnel through empty (use L'X' for stack)

g::LhsPattern lhs;
lhs[{-1, 0}] = g::ctx();       // above must equal ctx
g::RhsPattern rhs;
rhs[{-1, 0}] = g::put(L'^');   // write signal one cell up

std::cout << g::emit_rule(h, g::emit_body_vertical(lhs, rhs));
// Pair with a second rule (ctx=X) to also tunnel through frozen stack.
// Pair with arrival rules (ctx=H/C, replace=R) for stop conditions.
```

**Why it works.** GRAMMAR.md §Local memory: a char declared in
`#transient` updates only the *background* of memory when written; the
saved char + colours are preserved. When the rule's `replace=$` restores
the LHS anchor, the cell reappears verbatim. The signal moves; the
scenery is untouched. The `#transient` declaration is load-bearing —
without it memory is sticky and `$` restores the signal itself.

**Don't use.** When traversed cells *should* be erased (use
`replace=erase()` and a normal walker). Or when the signal needs to
react to scenery in flight (then it's a more complex state machine,
not a tunnel).

**Pitfall reference.** §5 of `GRAMMAR-pitfalls.md`. The original
`programs/tetris/tetris.cfg` rule `==^T$78-` (line 958) is the
canonical implementation; this recipe is the genlib-vocabulary form.

---

When a fifth recurring pattern appears in two or more generators, add it
here. The recipe format is deliberate: if you can't fill in *use case →
code → why → when not to use*, the pattern isn't crystallised yet — keep
it inside the consuming generator until it is.

## What's NOT here yet

Promoted only when a future use case confirms the abstraction:

- **Snake-step helpers** (head-direction-encoded glyphs, body trail). Trigger:
  a future snake generator that gets the body-trail encoding right — the
  first attempt (`snake_gen.cpp`) never produced a working game and was
  removed.
- **Multi-frame loop emission** (frame array → cyclic transition rule chain).
  Today the user composes diffs themselves. Trigger: a 3+ frame walking
  animation generator.
- **Shared types with `libgrammar`** (`ColorSpec` lift, `grammar_vocab.h`
  predicate enum). Trigger: linter lands.
- **Linter / validation harness**. Stays a separate binary linking
  `libgrammar.a`.

## Reference generators

- `animation_gen.cpp` — minimal frame-flip-flop using *programmatic cell
  lists*. Useful when the shape is computed, not drawn.
- `walker_gen.cpp` — same animation idiom using the *art loader*. The
  frames are inline raw strings; emitted rule bodies match the original
  art visually. The recommended pattern for sprite/scenery generators.
