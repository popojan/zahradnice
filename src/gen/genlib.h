#pragma once

// genlib: authoring-time helpers for emitting zahradnice .cfg programs.
// Hides grammar metasymbols (~, &, !, %, $, @) behind enum-tagged predicates.
// Generators describe rule intent via Match/Write; genlib emits the syntax.

#include <map>
#include <optional>
#include <set>
#include <string>
#include <utility>
#include <vector>

namespace genlib {

using Cell = std::pair<int, int>;  // (dr, dc) offset from rule anchor
using CellSet = std::set<Cell>;

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

// Set every cell in `cells` to the same Match/Write. Saves the inner-loop
// boilerplate that otherwise appears in every rule emission.
template <class CellRange>
inline void mark_each(LhsPattern& p, const CellRange& cells, Match m) {
    for (auto& c : cells) p[c] = m;
}
template <class CellRange>
inline void mark_each(RhsPattern& p, const CellRange& cells, Write w) {
    for (auto& c : cells) p[c] = w;
}

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
    int score = 0;     // appended after a space iff non-default
    int weight = 1;    // appended after a space iff score or weight non-default
};

// Concise factory for the common case (lhs + trigger + replace, no colours / ctx).
inline Header header(wchar_t lhs, wchar_t trigger, Write replace = preserve()) {
    Header h; h.lhs = lhs; h.trigger = trigger; h.replace = replace; return h;
}

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

// Emit a `#color <key> <code>[,<attr>]` directive declaring a colour alias
// usable in Header.fore / Header.back. Generators that want self-documenting
// generated cfg should emit these once at the program top and reference the
// alias char in headers.
std::string emit_color_alias(wchar_t key, int code,
                             std::optional<std::string> attr = std::nullopt);

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
CellSet            shifted(const CellSet&,           int dr, int dc);

// Convert vector of cells to a set (for spatial set-ops below).
inline CellSet as_set(const std::vector<Cell>& v) { return CellSet(v.begin(), v.end()); }

// Set difference: cells in `a` but not in `b`.
CellSet difference(const CellSet& a, const CellSet& b);

// When rotating with the screen pivot fixed, how the screen anchor must
// shift. Inputs are piece-cell coords; output is terminal-cell coords.
// Free function — anchor and pivot are not bundled together at the API
// level, since not all shapes have a pivot and not all rotations want one.
Cell rotation_anchor_shift(Cell from_anchor, Cell from_pivot,
                           Cell to_anchor,   Cell to_pivot,
                           int grid_w = 1, int grid_h = 1);

// --- Move-diff helpers ---
//
// "Rule that moves a shape" pattern: given old (matched) and new (target)
// cell sets relative to the rule anchor, the minimum-RHS rule erases cells
// in old\new and writes cells in new\old.

struct MoveDiff {
    CellSet erase;  // cells in old \ new (caller may want to drop {0,0})
    CellSet write;  // cells in new \ old
};
inline MoveDiff move_diff(const CellSet& old_cells, const CellSet& new_cells) {
    return { difference(old_cells, new_cells), difference(new_cells, old_cells) };
}

// Header.replace decision when the anchor is at (0, 0): if the new shape
// covers the anchor, write the glyph; otherwise erase. (Tetris fall/lateral
// /rotation all repeat this.)
inline Write replace_for_move(const CellSet& new_cells, wchar_t glyph) {
    return new_cells.count({0, 0}) ? put(glyph) : erase();
}

// --- ASCII art loader ---
//
// Parse multi-line ASCII art into cell maps relative to an anchor marker.
// Spaces are treated as no-cell. The anchor marker (default '@') identifies
// the cell that becomes (0, 0) in the output; it's excluded from the cells.
//
// Designed so generators emit big-body sprite/animation rules without
// hand-listing every cell. Architectural reservation in earlier sessions
// was: keep emit_body_* taking patterns directly so a future loader slots
// in — that future is now.

using ArtMap = std::map<Cell, wchar_t>;

ArtMap parse_art(const std::string& art, char anchor_marker = '@');

// Every cell in the art becomes a literal-char Match.
LhsPattern art_lhs(const std::string& art, char anchor_marker = '@');

// Every cell in the art becomes a put-char Write.
RhsPattern art_rhs(const std::string& art, char anchor_marker = '@');

// Diff two frames into a minimum-rule (LHS = full frame_a, RHS = changed cells).
// Cells in (a \ b) are erased; cells in (b \ a) are written; cells where
// position is in both but glyph differs become put(b's glyph). Cells unchanged
// across frames are absent from RHS (preserve).
struct DiffResult { LhsPattern lhs; RhsPattern rhs; };
DiffResult art_frame_diff(const std::string& frame_a, const std::string& frame_b,
                          char anchor_marker = '@');

}  // namespace genlib
