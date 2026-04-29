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

## What's NOT here yet

Promoted only when 2nd or 3rd generator confirms the abstraction:

- **Move-diff helper** (`old_cells`, `new_cells` → `{erase, write}`). Tetris
  fall/lateral/rotation all do this; will lift once snake's head-step
  confirms the same shape generalises.
- **Art loader**. Loading multi-line ASCII blocks as `LhsPattern`/`RhsPattern`
  with substitution. Highnoon-scale sprites force this; today's animations
  use tiny inline cell lists. Architectural reservation: `LhsPattern` is
  externally constructible and `emit_body_*` accepts the pattern directly,
  so a future `art_to_pattern(...)` slots in without breaking the API.
- **Shared types with `libgrammar`**. The `ColorSpec` lift, the cell-predicate
  vocabulary header — defer to when the linter lands and a `grammar_vocab.h`
  contract becomes natural.

## Reference generators

- `tetris_gen.cpp` — full I+T tetromino set (spawn, fall, freeze, lateral,
  rotation). Byte-identical to `scripts/tetris_generator.py`.
- `animation_gen.cpp` — minimal frame-flip-flop animation; demonstrates
  Header.replace as state flip-flop and the indent-escape on `^`-leading
  lines.
