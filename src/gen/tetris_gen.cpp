// tetris_gen: emits programs/tetris2/tetris.cfg via genlib.
// C++ port of scripts/tetris_generator.py (kept as POC oracle).

#include "genlib.h"

#include <climits>
#include <iostream>
#include <set>
#include <sstream>
#include <string>
#include <vector>

namespace g = genlib;

// --- Tetris-specific model (built on top of genlib primitives) ---

struct Orientation {
    std::string name;
    g::Shape shape;     // cells + anchor (piece-cell coords)
    g::Cell pivot;
};

struct Piece {
    wchar_t glyph;
    std::string colour;
    std::vector<Orientation> orientations;
    int spawn_idx = 0;
    std::vector<int> rotation_chain;
};

// Glyph allocation in one place. Renaming `frozen` from '#' to '*' is one
// field edit instead of grep-and-pray across the whole generator.
struct TetrisSyms {
    wchar_t wall    = L'H';
    wchar_t walker  = L'R';
    wchar_t seed    = L'P';
    wchar_t frozen  = L'#';
    wchar_t piece_I = L'I';
    wchar_t piece_T = L'T';
};

static const TetrisSyms syms;

// --- Piece data (matches Python POC byte-for-byte) ---

static std::vector<Piece> all_pieces() {
    return {
        Piece{
            L'I', "cyan",
            {
                {"H", g::Shape{{{0,0},{0,1},{0,2},{0,3}}, {0,0}}, {0,1}},
                {"V", g::Shape{{{0,0},{1,0},{2,0},{3,0}}, {0,0}}, {1,0}},
            },
            0, {0, 1},
        },
        Piece{
            L'T', "magenta",
            {
                {"T0", g::Shape{{{0,1},{1,0},{1,1},{1,2}}, {0,1}}, {1,1}},
                {"T1", g::Shape{{{0,0},{1,0},{1,1},{2,0}}, {0,0}}, {1,0}},
                {"T2", g::Shape{{{0,0},{0,1},{0,2},{1,1}}, {0,0}}, {0,1}},
                {"T3", g::Shape{{{0,1},{1,0},{1,1},{2,1}}, {0,1}}, {1,1}},
            },
            0, {0, 1, 2, 3},
        },
    };
}

// --- Geometry helpers ---

using g::CellSet;

// Terminal-cells of an Orientation, using the tetris #grid 2 1 convention.
static CellSet terminal_set(const Orientation& o) {
    return g::as_set(g::terminal_cells(o.shape, /*grid_w=*/2, /*grid_h=*/1));
}

// One cell per piece-cell-pair directly below the piece (left terminal col).
// Sufficient for freeze sub-rules because all blockers (walls, frozen) come
// in 2-col-aligned pairs.
static std::vector<g::Cell> below_2col_aligned(const Orientation& o) {
    auto cells = terminal_set(o);
    std::set<int> even_cols;
    for (auto& c : cells) if (c.second % 2 == 0) even_cols.insert(c.second);
    std::vector<g::Cell> out;
    for (int col : even_cols) {
        int max_r = INT_MIN;
        for (auto& c : cells) if (c.second == col || c.second == col + 1)
            if (c.first > max_r) max_r = c.first;
        out.emplace_back(max_r + 1, col);
    }
    return out;
}

// All terminal cells directly below the piece, one per occupied column.
static CellSet below_all(const Orientation& o) {
    auto cells = terminal_set(o);
    std::set<int> cols;
    for (auto& c : cells) cols.insert(c.second);
    CellSet out;
    for (int col : cols) {
        int max_r = INT_MIN;
        for (auto& c : cells) if (c.second == col && c.first > max_r) max_r = c.first;
        out.emplace(max_r + 1, col);
    }
    return out;
}

// --- Per-rule emission ---

static std::string emit_spawn(const Piece& p, const Orientation& o) {
    auto cells = terminal_set(o);
    CellSet siblings;
    for (auto& c : cells) if (c != g::Cell{0, 0}) siblings.insert(c);

    g::LhsPattern lhs;
    lhs[{-1, 0}] = g::lit(syms.wall);
    for (auto& c : siblings) lhs[c] = g::empty();

    g::RhsPattern rhs;
    for (auto& c : siblings) rhs[c] = g::put(p.glyph);

    g::Header h;
    h.lhs = syms.walker;
    h.trigger = L'f';
    h.replace = g::put(p.glyph);

    return g::emit_rule(h, g::emit_body_horizontal(lhs, rhs));
}

static std::string emit_fall(const Piece& p, const Orientation& o) {
    auto old_cells = terminal_set(o);
    CellSet new_cells;
    for (auto& c : old_cells) new_cells.emplace(c.first + 1, c.second);

    auto erase_cells = g::difference(g::difference(old_cells, new_cells), {{0, 0}});
    auto write_cells = g::difference(new_cells, old_cells);

    g::LhsPattern lhs;
    for (auto& c : g::difference(old_cells, {{0, 0}})) lhs[c] = g::lit(p.glyph);
    for (auto& c : below_all(o)) lhs[c] = g::empty();

    g::RhsPattern rhs;
    for (auto& c : erase_cells) rhs[c] = g::erase();
    for (auto& c : write_cells) rhs[c] = g::put(p.glyph);

    g::Header h;
    h.lhs = p.glyph;
    h.trigger = L'g';
    h.replace = g::erase();

    return g::emit_rule(h, g::emit_body_vertical(lhs, rhs));
}

static std::vector<std::string> emit_freeze(const Piece& p, const Orientation& o) {
    auto cells = terminal_set(o);
    std::vector<std::string> out;
    for (auto& below_cell : below_2col_aligned(o)) {
        g::LhsPattern lhs;
        lhs[{-1, 0}] = g::empty();  // R needs space to be written
        for (auto& c : g::difference(cells, {{0, 0}})) lhs[c] = g::lit(p.glyph);
        lhs[below_cell] = g::ctx_or_rep();  // wall (field 6) OR frozen (field 7)

        g::RhsPattern rhs;
        rhs[{-1, 0}] = g::put(syms.walker);
        for (auto& c : g::difference(cells, {{0, 0}})) rhs[c] = g::put(syms.frozen);

        g::Header h;
        h.lhs = p.glyph;
        h.trigger = L'g';
        h.replace = g::put(syms.frozen);
        h.ctx = syms.wall;
        h.ctxrep = syms.frozen;

        out.push_back(g::emit_rule(h, g::emit_body_vertical(lhs, rhs)));
    }
    return out;
}

static std::string emit_lateral(const Piece& p, const Orientation& o, int dc) {
    auto old_cells = terminal_set(o);
    CellSet new_cells;
    for (auto& c : old_cells) new_cells.emplace(c.first, c.second + dc);

    auto erase_cells = g::difference(old_cells, new_cells);
    auto write_cells = g::difference(new_cells, old_cells);

    g::LhsPattern lhs;
    for (auto& c : g::difference(old_cells, {{0, 0}})) lhs[c] = g::lit(p.glyph);
    for (auto& c : write_cells) lhs[c] = g::empty();

    g::RhsPattern rhs;
    for (auto& c : g::difference(erase_cells, {{0, 0}})) rhs[c] = g::erase();
    for (auto& c : write_cells) rhs[c] = g::put(p.glyph);

    g::Header h;
    h.lhs = p.glyph;
    h.trigger = (dc < 0) ? L'a' : L'd';
    h.replace = new_cells.count({0, 0}) ? g::put(p.glyph) : g::erase();

    return g::emit_rule(h, g::emit_body_horizontal(lhs, rhs));
}

// Pre-shaped rotation move: from-cells stay relative to from-anchor, but
// to-cells are shifted by rotation_anchor_shift so the screen pivot is fixed.
static std::pair<g::LhsPattern, g::RhsPattern>
rotation_patterns(const Piece& p, const Orientation& from, const Orientation& to) {
    auto from_cells = terminal_set(from);
    auto sh = g::rotation_anchor_shift(from.shape.anchor, from.pivot,
                                       to.shape.anchor,   to.pivot,
                                       /*grid_w=*/2, /*grid_h=*/1);
    CellSet to_cells_in_from;
    for (auto& c : terminal_set(to)) to_cells_in_from.emplace(c.first + sh.first,
                                                              c.second + sh.second);

    auto erase_cells = g::difference(from_cells, to_cells_in_from);
    auto write_cells = g::difference(to_cells_in_from, from_cells);

    g::LhsPattern lhs;
    for (auto& c : g::difference(from_cells, {{0, 0}})) lhs[c] = g::lit(p.glyph);
    for (auto& c : write_cells) lhs[c] = g::empty();

    g::RhsPattern rhs;
    for (auto& c : g::difference(erase_cells, {{0, 0}})) rhs[c] = g::erase();
    for (auto& c : write_cells) rhs[c] = g::put(p.glyph);

    return {lhs, rhs};
}

static bool anchor_in_to(const Piece& p, const Orientation& from, const Orientation& to) {
    auto sh = g::rotation_anchor_shift(from.shape.anchor, from.pivot,
                                       to.shape.anchor,   to.pivot, 2, 1);
    for (auto& c : terminal_set(to))
        if (g::Cell{c.first + sh.first, c.second + sh.second} == g::Cell{0, 0}) return true;
    return false;
}

static std::string emit_rotation(const Piece& p, const Orientation& from,
                                 const Orientation& to, wchar_t trigger) {
    auto [lhs, rhs] = rotation_patterns(p, from, to);

    g::Header h;
    h.lhs = p.glyph;
    h.trigger = trigger;
    h.replace = anchor_in_to(p, from, to) ? g::put(p.glyph) : g::erase();

    return g::emit_rule(h, g::emit_body_horizontal(lhs, rhs));
}

static std::string emit_piece(const Piece& p) {
    std::ostringstream out;
    out << "# === " << static_cast<char>(p.glyph) << "-piece (" << p.colour << ") ===\n";
    out << "# spawn\n";
    out << emit_spawn(p, p.orientations[p.spawn_idx]) << "\n";

    for (auto& o : p.orientations) {
        out << "# " << o.name << ": fall\n";
        out << emit_fall(p, o) << "\n";
        auto fz = emit_freeze(p, o);
        out << "# " << o.name << ": freeze (" << fz.size() << " sub-rules)\n";
        for (auto& r : fz) out << r << "\n";
        out << "# " << o.name << ": lateral L/R\n";
        out << emit_lateral(p, o, -2) << "\n";
        out << emit_lateral(p, o, +2) << "\n";
    }

    auto& chain = p.rotation_chain;
    if (chain.size() >= 2) {
        out << "# rotations (CW: w; CCW: e)\n";
        for (size_t i = 0; i < chain.size(); ++i) {
            int from_i = chain[i];
            int cw_i  = chain[(i + 1) % chain.size()];
            int ccw_i = chain[(i + chain.size() - 1) % chain.size()];
            const auto& from_o = p.orientations[from_i];

            if (cw_i == ccw_i) {
                // 2-orientation: CW and CCW share a body — emit both headers
                // before the body so the parser stacks them.
                const auto& to_o = p.orientations[cw_i];
                auto [lhs, rhs] = rotation_patterns(p, from_o, to_o);
                auto replace = anchor_in_to(p, from_o, to_o) ? g::put(p.glyph) : g::erase();

                g::Header h_cw;  h_cw.lhs = p.glyph; h_cw.trigger = L'w'; h_cw.replace = replace;
                g::Header h_ccw; h_ccw.lhs = p.glyph; h_ccw.trigger = L'e'; h_ccw.replace = replace;

                out << "# " << from_o.name << " <-> " << to_o.name << " (CW & CCW share body)\n";
                out << g::emit_header(h_cw) << "\n";
                out << g::emit_rule(h_ccw, g::emit_body_horizontal(lhs, rhs)) << "\n";
            } else {
                out << "# " << from_o.name << " -> " << p.orientations[cw_i].name << " (CW)\n";
                out << emit_rotation(p, from_o, p.orientations[cw_i], L'w') << "\n";
                out << "# " << from_o.name << " -> " << p.orientations[ccw_i].name << " (CCW)\n";
                out << emit_rotation(p, from_o, p.orientations[ccw_i], L'e') << "\n";
            }
        }
    }
    return out.str();
}

// --- Framework (playfield + walker rules) — verbatim ASCII art for now ---

static const char* FRAMEWORK = R"(#!{help} score:{score}
#help a/d move - w/e rotate - ESC quit
#timing g 500
#timing f 0
#control ~ pause
#grid 2 1
# Initial symbol must precede any rule header (parser double-classifies
# ^-lines that follow a rule, leaking the line text into the previous
# rule's body — see backlog/research/tetris-exercise-friction.md, B1).
^PcC
# === Playfield seed: one-shot perimeter + R placement ===
==Pf~
@@HHHHHHHHHHHHHHHHHHHHHHHH
  HH      R             HH
  HH                    HH
  HH                    HH
  HH                    HH
  HH                    HH
  HH                    HH
  HH                    HH
  HH                    HH
  HH                    HH
  HH          @         HH
  HH                    HH
  HH                    HH
  HH                    HH
  HH                    HH
  HH                    HH
  HH                    HH
  HH                    HH
  HH                    HH
  HH                    HH
  HH                    HH
  HHHHHHHHHHHHHHHHHHHHHHHH
# === R-walk: R + empty cell above -> R moves up one row ===
# Mutually exclusive with spawn (above is either ~ or H, not both).
==Rf~
~
@
@
R
@
)";

int main() {
    std::cout << FRAMEWORK << "\n";
    for (auto& p : all_pieces()) {
        std::cout << emit_piece(p) << "\n";
    }
    return 0;
}
