#pragma once

// genlib: authoring-time helpers for emitting zahradnice .cfg programs.
// Hides grammar metasymbols (~, &, !, %, $, @) behind enum-tagged predicates.
// Generators describe rule intent via Match/Write; genlib emits the syntax.

#include <map>
#include <optional>
#include <string>
#include <utility>
#include <vector>

namespace genlib {

using Cell = std::pair<int, int>;  // (dr, dc) offset from rule anchor

// LHS cell predicate. The grammar's expressive power, named.
struct Match {
    enum class Kind {
        Glyph,         // literal char (terminal or non-terminal)
        Empty,         // ~        empty cell
        Ctx,           // &        equals field 6 (header.ctx)
        NotCtx,        // !        not equal to field 6
        CtxOrCtxRep,   // %        equals field 6 OR field 7
    };
    Kind kind;
    wchar_t glyph = 0;  // for Glyph
};

// RHS cell action.
struct Write {
    enum class Kind {
        Glyph,         // literal char
        Erase,         // ~        write space
        Ctx,           // &        write field 7 (header.ctxrep)
        Memory,        // $        restore from local memory
        Preserve,      // ' '      no-op (only meaningful as Header.replace default)
    };
    Kind kind;
    wchar_t glyph = 0;  // for Glyph
};

// Match constructors
inline Match lit(wchar_t c)        { return {Match::Kind::Glyph, c}; }
inline Match empty()               { return {Match::Kind::Empty, 0}; }
inline Match ctx()                 { return {Match::Kind::Ctx, 0}; }
inline Match not_ctx()             { return {Match::Kind::NotCtx, 0}; }
inline Match ctx_or_rep()          { return {Match::Kind::CtxOrCtxRep, 0}; }

// Write constructors
inline Write put(wchar_t c)        { return {Write::Kind::Glyph, c}; }
inline Write erase()               { return {Write::Kind::Erase, 0}; }
inline Write write_ctx()           { return {Write::Kind::Ctx, 0}; }
inline Write write_memory()        { return {Write::Kind::Memory, 0}; }
inline Write preserve()            { return {Write::Kind::Preserve, 0}; }

// Cell maps. Absent cells in LHS = no constraint; absent in RHS = no-op.
using LhsPattern = std::map<Cell, Match>;
using RhsPattern = std::map<Cell, Write>;

// Rule header (positional fields per GRAMMAR.v2.md).
//   sound:    field S — sound key char; '=' = no sound (default)
//   lhs:      field 1 — non-terminal char being matched
//   trigger:  field 2 — keypress or timing char
//   replace:  field 3 — what to write at the LHS anchor cell
//   fore/back:fields 4/5 — colour digits or aliases
//   ctx/ctxrep:fields 6/7 — extra context match / replacement
struct Header {
    wchar_t sound = L'=';
    wchar_t lhs;
    wchar_t trigger;
    Write replace = preserve();
    std::optional<char> fore;
    std::optional<char> back;
    std::optional<wchar_t> ctx;
    std::optional<wchar_t> ctxrep;
};

// --- Emission ---

// Emit just the header line (e.g. "==Rf~" or "==IgH78H#"). No trailing newline.
std::string emit_header(const Header&);

// Body builders: LHS region above/left of boundary, RHS below/right.
// The boundary is one row/col wide separating the regions; emitter places
// the @ markers automatically. Indent-escape (B7) is applied: if any body
// line would start with a parser-special char (#, ^, =), the entire body is
// indented by one column to neutralise it.
std::string emit_body_vertical(const LhsPattern& lhs, const RhsPattern& rhs);
std::string emit_body_horizontal(const LhsPattern& lhs, const RhsPattern& rhs);

// Compose: header + newline + body.
std::string emit_rule(const Header&, const std::string& body);

// --- Geometry primitives (general; not tied to any specific game) ---
//
// Generators that need richer models (piece-orientation bundles, rotation
// chains, sprite dictionaries) build them on top of these. genlib stays
// free-function-oriented so future primitives accumulate without bloating
// any single struct.

// A 2D shape: a set of cells with a designated anchor (LHS rule anchor).
// Cells are in piece-cell coords (any small integer grid; the caller decides).
struct Shape {
    std::vector<Cell> cells;
    Cell anchor = {0, 0};
};

// Convert a Shape's piece-cells to terminal-cell offsets relative to the LEFT
// terminal col of the anchor piece-cell. Each piece-cell expands to a
// grid_w × grid_h block of terminal cells. Use 1×1 for programs without a
// `#grid` directive; 2×1 for the typical "two-cols-per-tile" convention.
std::vector<Cell> terminal_cells(const Shape&, int grid_w = 1, int grid_h = 1);

// Translate every cell by (dr, dc). Used by lateral moves, falls, etc.
std::vector<Cell> shifted(const std::vector<Cell>&, int dr, int dc);

// When rotating with the screen pivot fixed, how the screen anchor must
// shift. Inputs are piece-cell coords; output is terminal-cell coords.
// Free function — anchor and pivot are not bundled together at the API
// level, since not all shapes have a pivot and not all rotations want one.
Cell rotation_anchor_shift(Cell from_anchor, Cell from_pivot,
                           Cell to_anchor,   Cell to_pivot,
                           int grid_w = 1, int grid_h = 1);

}  // namespace genlib
