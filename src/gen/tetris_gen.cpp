// tetris_gen: emits programs/tetris2/tetris.cfg via genlib.
// C++ port of scripts/tetris_generator.py (kept as POC oracle).

#include "genlib.h"

#include <algorithm>
#include <climits>
#include <iostream>
#include <iterator>
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
    std::string colour;                       // human-readable name (comments)
    int color_code = 7;                       // curses fg code 0-7
    std::optional<std::string> color_attr;    // BOLD / DIM if set
    std::vector<Orientation> orientations;
    int spawn_idx = 0;
    std::vector<int> rotation_chain;
};

// Glyph allocation in one place. The `frozen` marker is X — every frozen
// piece-cell occupies a 2-col-aligned terminal pair (X, piece-glyph) so the
// piece colour follows the cell through line-clear gravity shifts.
// `gravity` is the rising particle non-terminal during line clear; chosen as
// `|` (non-letter) so it never collides with text written to the screen
// (e.g. "Game Over" — earlier we used `v` and the v-dissipate rule erased
// the v out of the text).
struct TetrisSyms {
    wchar_t wall    = L'H';
    wchar_t walker  = L'R';
    wchar_t seed    = L'P';
    wchar_t frozen  = L'X';
    wchar_t gravity = L'|';
    wchar_t signal  = L'^';   // post-freeze rise signal — tunnels through any
                              //  cell via memory-restore (`$`); see
                              //  emit_signal_rise() and original tetris.cfg
                              //  rule `==^T$78-` (lines 958–960).
    wchar_t piece_I = L'I';
    wchar_t piece_T = L'T';
};

static const TetrisSyms syms;

// Header pre-loaded with the piece's colour foreground (the glyph itself,
// declared via #color directives). Background stays default (transparent).
static g::Header coloured(const Piece& p, wchar_t lhs, wchar_t trigger, g::Write replace) {
    auto h = g::header(lhs, trigger, replace);
    h.fore = static_cast<char>(p.glyph);
    return h;
}

// Header for piece movement rules: BOTH fore and back are '0' (black). Two
// effects: (1) back='0' clears trail bg-colour from cells the piece vacates,
// so the previous-frame fill colour does not linger after the piece moves;
// (2) fore='0' makes the briefly-visible glyph letters invisible against
// the black bg, so during the 1-step gap before the next f-tick paints the
// piece with bg=alias the piece reads as a piece-shaped *void* rather than
// a row of skeleton letters — the eye perceives the void→fill transition
// as smoother than fill→letters→fill flicker. (User-observed.)
static g::Header coloured_move(const Piece& p, wchar_t lhs, wchar_t trigger, g::Write replace) {
    auto h = coloured(p, lhs, trigger, replace);
    h.fore = '0';
    h.back = '0';
    return h;
}

// Per-orientation full-body render: matches the FULL piece body (all body
// cells equal to the piece-glyph) and re-writes every body cell with
// fg=back=alias. Single rule application = whole piece painted atomically,
// avoiding the partial-piece flicker that happens when each cell is rendered
// independently across multiple engine steps. One render rule per
// orientation; orientations have distinct body shapes so each rule matches
// only its own orientation (no cross-firing).
//
// Trigger `f` (the instant timer with #timing f 0) fires on every engine
// step not otherwise consumed by an input or scheduled timer (g, s, a, d,
// w, e). Wildcard `?` was tried but slowed the game ~20× — engine's
// weighted sampler picked render over move too often. A 1-step bg=0 flash
// between the move tick and the next f-tick remains; eliminating it needs
// seed-then-fill (write a 1-cell seed on move) — see task #13.
static std::string emit_render(const Piece& p, const Orientation& o);  // defined below terminal_set

// Wall + spawn-beacon render — ONE-SHOT. The seed places lowercase h's and
// c at wall and beacon positions; these convert rules fire once per cell to
// rewrite them as uppercase H / C with bg=white. After conversion all h/c
// cells are gone and these rules never fire again, eliminating the
// per-f-tick repaint overhead (~50 idempotent rule applications per tick
// the previous version cost). Walker / freeze / spawn rules continue to
// match uppercase H / C as before.
static std::string emit_wall_render() {
    g::LhsPattern lhs;
    g::RhsPattern rhs;
    auto h_wall = g::header(L'h', L'f', g::put(syms.wall));   // h -> H
    h_wall.fore = '7'; h_wall.back = '7';
    auto h_beacon = g::header(L'c', L'f', g::put(L'C'));      // c -> C
    h_beacon.fore = '7'; h_beacon.back = '7';
    auto body = g::emit_body_horizontal(lhs, rhs);
    return "# === Wall + spawn beacon: one-shot h/c -> H/C with bg=white ===\n"
         + g::emit_rule(h_wall, body)   + "\n"
         + g::emit_rule(h_beacon, body);
}

// One-shot convert: lowercase x + lowercase piece-glyph -> uppercase X +
// uppercase piece-glyph with bg=alias. Stacked one header per piece colour.
// LHS anchor = lowercase x; ctx = lowercase glyph (matches the seed pair as
// freshly written by freeze / v-swap). After firing, both cells become
// uppercase + bg=alias and the rule's lhs=x no longer matches — fires once
// per pair, never again. Other rules (line-clear LHS, freeze ctx_or_rep,
// dissipate) continue to match uppercase X as before.
static std::string emit_frozen_render(const std::vector<Piece>& pieces) {
    auto seed_x = static_cast<wchar_t>(std::tolower(static_cast<int>(syms.frozen)));
    g::LhsPattern lhs;
    lhs[{0, 1}] = g::ctx();              // lowercase glyph adjacent to lowercase x
    g::RhsPattern rhs;
    rhs[{0, 1}] = g::write_ctx();        // writes uppercase ctxrep
    auto body = g::emit_body_horizontal(lhs, rhs);

    std::string out = "# === Frozen x+lower-glyph -> X+upper-glyph (one-shot per pair) ===\n";
    for (size_t i = 0; i < pieces.size(); ++i) {
        auto h = g::header(seed_x, L'f', g::put(syms.frozen));   // lhs=x → X
        h.fore = static_cast<char>(pieces[i].glyph);
        h.back = static_cast<char>(pieces[i].glyph);
        h.ctx    = static_cast<wchar_t>(std::tolower(static_cast<int>(pieces[i].glyph))); // lower
        h.ctxrep = pieces[i].glyph;                                                       // upper
        if (i + 1 < pieces.size()) out += g::emit_header(h) + "\n";
        else                       out += g::emit_rule(h, body) + "\n";
    }
    return out;
}

// --- Piece data (matches Python POC byte-for-byte) ---

static std::vector<Piece> all_pieces() {
    return {
        Piece{
            L'I', "cyan", 6, {},
            {
                {"H", g::Shape{{{0,0},{0,1},{0,2},{0,3}}, {0,0}}, {0,1}},
                {"V", g::Shape{{{0,0},{1,0},{2,0},{3,0}}, {0,0}}, {1,0}},
            },
            0, {0, 1},
        },
        Piece{
            L'T', "magenta", 5, {},
            {
                {"T0", g::Shape{{{0,1},{1,0},{1,1},{1,2}}, {0,1}}, {1,1}},
                {"T1", g::Shape{{{0,0},{1,0},{1,1},{2,0}}, {0,0}}, {1,0}},
                {"T2", g::Shape{{{0,0},{0,1},{0,2},{1,1}}, {0,0}}, {0,1}},
                {"T3", g::Shape{{{0,1},{1,0},{1,1},{2,1}}, {0,1}}, {1,1}},
            },
            0, {0, 1, 2, 3},
        },
        Piece{
            L'J', "blue", 4, {},
            {
                {"J0", g::Shape{{{0,0},{1,0},{1,1},{1,2}}, {0,0}}, {1,1}},
                {"J1", g::Shape{{{0,0},{0,1},{1,0},{2,0}}, {0,0}}, {1,0}},
                {"J2", g::Shape{{{0,0},{0,1},{0,2},{1,2}}, {0,0}}, {0,1}},
                {"J3", g::Shape{{{0,1},{1,1},{2,0},{2,1}}, {0,1}}, {1,1}},
            },
            0, {0, 1, 2, 3},
        },
        // L: mirror of J — bright yellow stands in for orange
        Piece{
            L'L', "orange", 3, std::string("BOLD"),
            {
                {"L0", g::Shape{{{0,2},{1,0},{1,1},{1,2}}, {0,2}}, {1,1}},
                {"L1", g::Shape{{{0,0},{1,0},{2,0},{2,1}}, {0,0}}, {1,0}},
                {"L2", g::Shape{{{0,0},{0,1},{0,2},{1,0}}, {0,0}}, {0,1}},
                {"L3", g::Shape{{{0,0},{0,1},{1,1},{2,1}}, {0,0}}, {1,1}},
            },
            0, {0, 1, 2, 3},
        },
        Piece{
            L'O', "yellow", 3, {},
            {
                {"O0", g::Shape{{{0,0},{0,1},{1,0},{1,1}}, {0,0}}, {0,0}},
            },
            0, {},
        },
        Piece{
            L'S', "green", 2, {},
            {
                {"S0", g::Shape{{{0,1},{0,2},{1,0},{1,1}}, {0,1}}, {1,1}},
                {"S1", g::Shape{{{0,0},{1,0},{1,1},{2,1}}, {0,0}}, {1,1}},
            },
            0, {0, 1},
        },
        Piece{
            L'Z', "red", 1, {},
            {
                {"Z0", g::Shape{{{0,0},{0,1},{1,1},{1,2}}, {0,0}}, {1,1}},
                {"Z1", g::Shape{{{0,1},{1,0},{1,1},{2,0}}, {0,1}}, {1,1}},
            },
            0, {0, 1},
        },
    };
}

// --- Geometry helpers ---

using g::CellSet;

// Terminal-cells of an Orientation, using the tetris #grid 2 1 convention.
static CellSet terminal_set(const Orientation& o) {
    return g::as_set(g::terminal_cells(o.shape, /*grid_w=*/2, /*grid_h=*/1));
}

// Lowercase counterpart of a piece glyph — used as the "seed / dirty"
// state. Move rules write lowercase; render converts to uppercase + bg=alias.
static wchar_t seed_of(const Piece& p) {
    return static_cast<wchar_t>(std::tolower(static_cast<int>(p.glyph)));
}

// Definition of the forward-declared emit_render — needs terminal_set above.
//
// One-shot per-orientation render: matches the *seed* (lowercase) body and
// writes the rendered (uppercase) body with bg=alias. After firing, the
// lowercase cells are gone — the rule never refires until another move
// re-introduces the seed. Roughly mirrors the original tetris.cfg
// `==jTjbB ... @&@JJ@&JJ` j→J pattern.
static std::string emit_render(const Piece& p, const Orientation& o) {
    auto cells = terminal_set(o);
    auto seed = seed_of(p);
    g::LhsPattern lhs;
    g::RhsPattern rhs;
    for (auto& c : g::difference(cells, {{0, 0}})) {
        lhs[c] = g::lit(seed);     // expects lowercase (just-moved) state
        rhs[c] = g::put(p.glyph);  // writes uppercase + bg=alias
    }
    auto h = g::header(seed, L'f', g::put(p.glyph));
    h.fore = static_cast<char>(p.glyph);
    h.back = static_cast<char>(p.glyph);
    return g::emit_rule(h, g::emit_body_horizontal(lhs, rhs));
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
    auto seed = seed_of(p);
    CellSet siblings;
    for (auto& c : cells) if (c != g::Cell{0, 0}) siblings.insert(c);

    g::LhsPattern lhs;
    lhs[{-1, 0}] = g::lit(L'C');
    g::mark_each(lhs, siblings, g::empty());

    g::RhsPattern rhs;
    g::mark_each(rhs, siblings, g::put(seed));   // siblings as seed → render fires next f-tick

    // Anchor written as seed too, so the render rule (lhs=seed) matches at
    // anchor and converts everything to uppercase + bg=alias atomically.
    return g::emit_rule(coloured(p, syms.walker, L'f', g::put(seed)),
                        g::emit_body_horizontal(lhs, rhs));
}

// Line clearing + shift-particle gravity.
//
// Mechanism (after the original programs/tetris/tetris.cfg):
//   Clear:     row of 10 X at even offsets -> 10 v particles + 10 erases.
//   v rise:    v + empty pair above + empty right -> v jumps up one row.
//   v swap:    v + X+glyph pair above + empty right -> v rises, pair drops.
//   v end:     v + wall/beacon above -> v dissipates.
// Each cleared row spawns 10 rising v's; each v drags its column's blocks
// down by one row as it ascends. All gravity rules force back='0' so cells
// the v passes through have memory.bg reset to black; the frozen-X render
// then re-paints the new (lower) X+glyph pair with bg=alias on the next
// step. Without back='0', emptied cells retained the previous render's bg
// and showed as ghost-coloured blocks above the new stack top.
static std::string emit_line_clear(const std::vector<Piece>& pieces) {
    std::ostringstream out;
    constexpr int ROW_W = 20;

    out << "# === Line clear: 10 X at even offsets -> 10 v particles (+10 score) ===\n";
    {
        // Force anchor at the leftmost interior col (=4) by requiring left
        // neighbour to be a wall H. Without this, the rule could anchor at
        // either col 4 or col 5 (both inside a fully-frozen row) — odd-col
        // anchoring places v's at cols 5..23 and the rightmost v ends up
        // with the right wall H at its above-right, where no rule fires.
        g::LhsPattern lhs;
        lhs[{0, -1}] = g::lit(syms.wall);
        for (int c = 2; c < ROW_W; c += 2) lhs[{0, c}] = g::lit(syms.frozen);
        g::RhsPattern rhs;
        for (int c = 1; c < ROW_W; ++c)
            rhs[{0, c}] = (c % 2 == 0) ? g::put(syms.gravity) : g::erase();
        auto h = g::header(syms.frozen, L'f', g::put(syms.gravity));
        h.fore = '7'; h.back = '0';
        h.score = 10;  // +10 per cleared row
        out << g::emit_rule(h, g::emit_body_horizontal(lhs, rhs)) << "\n";
    }

    out << "# === v rises through empty space ===\n";
    {
        g::LhsPattern lhs;
        lhs[{-1, 0}] = g::empty();
        lhs[{-1, 1}] = g::empty();
        lhs[{ 0, 1}] = g::empty();
        g::RhsPattern rhs;
        rhs[{-1, 0}] = g::put(syms.gravity);
        auto h = g::header(syms.gravity, L'f', g::erase());
        h.fore = '7'; h.back = '0';
        out << g::emit_rule(h, g::emit_body_horizontal(lhs, rhs)) << "\n";
    }

    out << "# === X+glyph pair drops through v (gravity, per piece colour) ===\n";
    {
        // The dropped pair is written LOWERCASE (x + lowercase glyph); the
        // frozen-convert rule promotes it to uppercase + bg=alias next f-tick.
        // ctx matches the existing UPPERCASE colour-glyph above; ctxrep is the
        // lowercase variant (so `&` LHS reads upper, `&` RHS writes lower).
        auto seed_x = static_cast<wchar_t>(std::tolower(static_cast<int>(syms.frozen)));
        g::LhsPattern lhs;
        lhs[{0, 1}] = g::ctx();             // existing colour-glyph (uppercase) adjacent to X
        lhs[{1, 0}] = g::lit(syms.gravity);         // v below
        lhs[{1, 1}] = g::empty();           // empty diagonal-down (clearance)
        g::RhsPattern rhs;
        rhs[{0, 1}] = g::erase();           // erase old colour-glyph cell
        rhs[{1, 0}] = g::put(seed_x);       // x drops one row (lowercase)
        rhs[{1, 1}] = g::write_ctx();       // & writes ctxrep = LOWERCASE glyph
        auto body = g::emit_body_horizontal(lhs, rhs);

        for (size_t i = 0; i < pieces.size(); ++i) {
            auto h = g::header(syms.frozen, L'f', g::put(syms.gravity));
            h.fore = '7';
            h.back = '0';
            h.ctx    = pieces[i].glyph;                                                  // upper
            h.ctxrep = static_cast<wchar_t>(std::tolower(static_cast<int>(pieces[i].glyph))); // lower
            if (i + 1 < pieces.size()) out << g::emit_header(h) << "\n";
            else                       out << g::emit_rule(h, body) << "\n";
        }
    }

    out << "# === v dissipates when above is anything not ~ or X ===\n";
    {
        // ctx_or_rep matches ctx OR ctxrep — pair blockers two at a time
        // and stack the headers on a single body. Covers: top wall, centre
        // beacon, piece glyphs, walker states. back='0' clears trail bg.
        g::LhsPattern lhs;
        lhs[{-1, 0}] = g::ctx_or_rep();
        g::RhsPattern rhs;
        auto body = g::emit_body_vertical(lhs, rhs);

        const std::vector<std::pair<wchar_t, wchar_t>> pairs = {
            {L'H', L'C'},  // top wall, centre beacon
            {L'I', L'T'},  // piece glyphs (next piece in flight above)
            {L'J', L'L'},
            {L'O', L'S'},
            {L'Z', L'R'},  // last piece + walker
            {L'Q', L'Q'},  // walker (singleton, paired with self)
        };
        for (size_t i = 0; i < pairs.size(); ++i) {
            auto h = g::header(syms.gravity, L'f', g::erase());
            h.fore = '7'; h.back = '0';
            h.ctx = pairs[i].first;
            h.ctxrep = pairs[i].second;
            if (i + 1 < pairs.size()) out << g::emit_header(h) << "\n";
            else                       out << g::emit_rule(h, body) << "\n";
        }
    }

    return out.str();
}

// Game over: when R reaches the spawn position (above C) and *any* cell in
// the spawn area is non-empty, no piece can spawn — the stack reached the
// top. Without a robust check, a stack that doesn't peak at col 12 (the
// spawn column) leaves R cycling endlessly through the walker state machine.
//
// Implementation: use `!` (not-equal-to-ctx) with ctx=' ' (space) to match
// any non-empty cell. Emit one rule per probed spawn-area cell — checking
// (1, 0), (0, 1), (1, 1) covers all 7 pieces' spawn bodies (vertical
// orientations occupy (1, 0)/(1, 1); I horizontal occupies (0, 1)).
//
// Each rule erases R, prints "Game Over" right of the spawn column, and
// toggles pause via the `~` engine action (wired in the framework).
static std::string emit_game_over() {
    g::RhsPattern rhs;
    const char* text = "Game Over";
    for (int i = 0; text[i]; ++i)
        // `put(L' ')` would emit a literal space body cell, which the engine
        // treats as a no-op (GRAMMAR.md §Body) — leaving piece bg showing
        // through the space between "Game" and "Over". Use erase() so the
        // gap is written as a real space terminal with bg=0 (black).
        rhs[{0, 2 + i}] = (text[i] == ' ') ? g::erase()
                                           : g::put(static_cast<wchar_t>(text[i]));

    std::string out = "# === Game Over: any cell in spawn area non-empty ===\n";
    // Probes cover the union of spawn-body cells across all 7 pieces — the
    // 3-cell coverage missed cases where the stack peaked at cols/rows the
    // 3 probes didn't sample. With these 10 probes any piece's spawn block
    // condition raises Game Over.
    std::vector<g::Cell> probes = {
        {0, 1}, {0, 3}, {0, 5}, {0, 7},   // I-horizontal sibling row
        {1, -2}, {1, -1},                 // S0 / T-piece left-flank below row
        {1, 0}, {1, 1}, {1, 2}, {1, 3},   // most piece bodies' below row
    };
    for (auto& probe : probes) {
        g::LhsPattern lhs;
        lhs[{-1, 0}] = g::lit(L'C');     // R above the centre beacon (spawn-ready)
        lhs[probe]    = g::ctx();         // probed spawn cell is frozen X

        auto h = g::header(syms.walker, L'f', g::erase());
        h.sound = L'~';     // `#control ~ pause` — auto-pauses
        h.fore = '7'; h.back = '0';
        // ctx = X (the frozen-stack marker, written at every even col of every
        // frozen pair). The earlier formulation used `!` with ctx=`~` (= "any
        // non-empty cell") — that fired on transient `|` gravity particles
        // rising through the spawn area during a multi-row clear, causing a
        // premature game over while the stack was still well below the spawn
        // row. Switching to `&` ctx=X restricts the trigger to the *only*
        // glyph that durably indicates "stack reached this cell": the frozen
        // marker. Transients (|, ^, walker glyphs) no longer match.
        //
        // Coverage note: of the 10 probes below, only the even-col offsets
        // ((1, -2), (1, 0), (1, 2)) can ever match X — frozen pairs place X
        // at even cols only (glyph at odd cols). The odd-col probes are dead
        // rules under this ctx but harmless to leave; the even-col probes
        // alone cover the union of below-spawn-body cells across all pieces
        // sufficiently for the post-spawn `stuck-at-top` rule to handle any
        // remaining edge cases.
        h.ctx = syms.frozen;
        out += g::emit_rule(h, g::emit_body_horizontal(lhs, rhs)) + "\n";
    }
    return out;
}

// Stuck-at-top game over (Bug A fix). Mirrors emit_freeze's structure: full
// piece-body match (so the rule fires only on the *active* piece anchor, not
// frozen X+glyph pairs mid-stack), per-orientation, per-below_cell sub-rules.
// The difference vs freeze is the LHS at (-1, 0): freeze requires `empty`;
// this rule requires `!` (above ≠ empty) — covering wall H, beacon C, and
// overhang X with a single predicate, no ctx-pair multiplexing.
//
// Why shape-aware: a pure anchor-only rule like {anchor + above + below}
// fails for any multi-cell piece. For a J0 piece at the spawn row with X
// immediately below the bottom row of the piece, the anchor's "below" is
// the *piece's own body cell*, not the stack — the rule never fires.
// Mirroring freeze's full-body match means each below_cell sub-rule looks
// exactly one cell below the piece's bottom row in that 2-col-aligned
// column, which IS the cell that's wall/X.
//
// Single ctx (=`~`, the empty marker) lets us:
//   - `!` at (-1, 0) → above ≠ empty (matches H, C, X, or any piece glyph
//     mid-flight; the latter is harmless because pieces don't fly above an
//     active piece in normal play).
//   - lit(X) at below_cell → restrict to "stack X reached this column".
//     Note: at top-of-playfield stuck cases, below is always X — the bottom
//     wall H is far below. Dropping H below means stuck-at-bottom-wall
//     (only possible for I-vertical pieces at body rows 18+) goes back to
//     the regular freeze rule, which correctly handles it via (-1, 0)=empty.
//
// 2 headers per body (g, s triggers); 1 body per (piece, orientation,
// below_cell). Half the rule count of the previous 2-ctx-pair version.
static std::vector<std::string> emit_stuck_at_top_game_over(const std::vector<Piece>& pieces) {
    std::vector<std::string> out;

    for (const auto& p : pieces) {
        for (const auto& o : p.orientations) {
            for (const auto& below_cell : below_2col_aligned(o)) {
                g::LhsPattern lhs;
                lhs[{-1, 0}] = g::not_ctx();   // ! above: ≠ ctx (= ~)
                g::mark_each(lhs, g::difference(terminal_set(o), {{0, 0}}),
                             g::lit(p.glyph));
                lhs[below_cell] = g::lit(syms.frozen);   // below = X (stack)

                g::RhsPattern rhs;
                const char* text = "Game Over";
                for (int i = 0; text[i]; ++i)
                    rhs[{0, 2 + i}] = (text[i] == ' ')
                        ? g::erase()
                        : g::put(static_cast<wchar_t>(text[i]));
                auto body = g::emit_body_vertical(lhs, rhs);

                std::string headers;
                for (wchar_t trig : {L'g', L's'}) {
                    auto h = g::header(p.glyph, trig, g::erase());
                    h.sound = L'~';     // pause
                    h.fore = '7'; h.back = '0';
                    h.ctx = L'~';       // empty marker (engine maps ' ' → '~')
                    headers += g::emit_header(h) + "\n";
                }
                out.push_back(headers + body);
            }
        }
    }
    return out;
}

// Post-freeze rise: `^` ascends through the playfield via memory restore,
// passing through frozen X stack and empty cells alike, until the cell above
// is the top wall H or the C beacon — at which point `^` converts to R and
// the existing horizontal walker takes over. This mirrors the original
// tetris.cfg pattern (rule `==^T$78-`, lines 958–960):
//
//     ==^T$78-       header: replace=$ (memory restore at LHS anchor),
//     ! ^                    back=8 (transparent), ctx=`-` (barrier)
//     @@@            body:   `!` above means "above != ctx"; `^` written above.
//
// Why memory restore matters (GRAMMAR.md §Local memory): when a char declared
// in `#transient` is written, only the *background* of memory is updated; the
// saved terminal char is preserved. So when `^` overwrites an X cell (and the
// program declares `#transient ^v`, which it must), memory still
// holds the X struct (char + colours). When `^` moves on, header `replace=$`
// restores the X to the screen verbatim — the stack is *unchanged* visually
// even though `^` tunneled through it.
//
// We split the rise into two LHS predicates — `^ + above=empty` and
// `^ + above=X` — using `&` (matches ctx). A single `!` rule with ctx=H
// would also rise past the C beacon (C != H, so `!` matches), depositing
// `^` inside the wall row at col 12. Two `&` rules give precise control:
// rise only through cells we explicitly opt in to (~ and X).
//
// Two arrival rules convert `^` to R when above is H (any non-spawn col) or
// C (col 12, spawn-ready). After arrival, R is at the topmost interior row,
// and the existing R-walk-left / Q-right state machine handles horizontal
// traversal to the spawn col.
static std::string emit_signal_rise() {
    std::ostringstream out;
    out << "# === Signal rise: `^` tunnels up via memory-restore (Bug B fix) ===\n";

    // `^` + above empty -> memory restore at LHS, write `^` above.
    {
        auto h = g::header(syms.signal, L'f', g::write_memory());
        h.fore = '7'; h.back = '8';   // back=8 transparent (preserves saved bg)
        h.ctx = L'~';                 // empty marker
        g::LhsPattern lhs;
        lhs[{-1, 0}] = g::ctx();      // & cell, matches ctx (=empty)
        g::RhsPattern rhs;
        rhs[{-1, 0}] = g::put(syms.signal);
        out << "# ^ rises through empty\n";
        out << g::emit_rule(h, g::emit_body_vertical(lhs, rhs)) << "\n";
    }
    // `^` + above frozen X -> memory restore at LHS, write `^` above. Memory
    // at the X cell holds the X glyph + piece-colour bg (terminal write); the
    // tunneled cell is restored verbatim when `^` moves on.
    {
        auto h = g::header(syms.signal, L'f', g::write_memory());
        h.fore = '7'; h.back = '8';
        h.ctx = syms.frozen;
        g::LhsPattern lhs;
        lhs[{-1, 0}] = g::ctx();
        g::RhsPattern rhs;
        rhs[{-1, 0}] = g::put(syms.signal);
        out << "# ^ rises through frozen X (the Bug B case)\n";
        out << g::emit_rule(h, g::emit_body_vertical(lhs, rhs)) << "\n";
    }
    // `^` + above wall H -> R at current. Trigger: existing R-walk-left fires
    // next, taking R along the topmost interior row toward the spawn col.
    {
        auto h = g::header(syms.signal, L'f', g::put(syms.walker));
        h.fore = '7'; h.back = '8';
        h.ctx = syms.wall;
        g::LhsPattern lhs;
        lhs[{-1, 0}] = g::ctx();
        g::RhsPattern rhs;
        out << "# ^ arrived at top wall -> R\n";
        out << g::emit_rule(h, g::emit_body_vertical(lhs, rhs)) << "\n";
    }
    // `^` + above C beacon -> R at current. Trigger: existing per-piece spawn
    // rule fires next (spawn LHS expects R with C above). This short-circuits
    // the horizontal traversal when `^` happens to rise in the spawn column.
    {
        auto h = g::header(syms.signal, L'f', g::put(syms.walker));
        h.fore = '7'; h.back = '8';
        h.ctx = L'C';
        g::LhsPattern lhs;
        lhs[{-1, 0}] = g::ctx();
        g::RhsPattern rhs;
        out << "# ^ arrived under C beacon -> R (spawn-ready)\n";
        out << g::emit_rule(h, g::emit_body_vertical(lhs, rhs)) << "\n";
    }

    return out.str();
}

// Walker state machine: R walks up; at top row, walks left to wall, becomes Q,
// walks right; arriving below the C beacon, Q becomes R so spawn fires.
static std::string emit_walker_state_machine() {
    std::ostringstream out;
    out << "# === Walker state machine: R-left-to-wall, Q-right-to-centre ===\n";
    out << "# (R-walk-up replaced by signal-rise via `^`; see emit_signal_rise.)\n";

    // R + above wall H + left empty -> R one cell left, erase anchor.
    {
        g::LhsPattern lhs;
        lhs[{-1, 0}] = g::lit(syms.wall);
        lhs[{ 0,-1}] = g::empty();
        g::RhsPattern rhs;
        rhs[{0, -1}] = g::put(syms.walker);
        out << "# R walks left when at top row\n";
        out << g::emit_rule(g::header(syms.walker, L'f', g::erase()),
                            g::emit_body_horizontal(lhs, rhs)) << "\n";
    }

    // R + above wall H + left wall H -> R becomes Q (turn around).
    {
        g::LhsPattern lhs;
        lhs[{-1, 0}] = g::lit(syms.wall);
        lhs[{ 0,-1}] = g::lit(syms.wall);
        g::RhsPattern rhs;
        out << "# R hits left wall -> becomes Q\n";
        out << g::emit_rule(g::header(syms.walker, L'f', g::put(L'Q')),
                            g::emit_body_horizontal(lhs, rhs)) << "\n";
    }

    // Q + above wall H + right empty -> Q one cell right, erase anchor.
    {
        g::LhsPattern lhs;
        lhs[{-1, 0}] = g::lit(syms.wall);
        lhs[{ 0, 1}] = g::empty();
        g::RhsPattern rhs;
        rhs[{0, 1}] = g::put(L'Q');
        out << "# Q walks right when at top row\n";
        out << g::emit_rule(g::header(L'Q', L'f', g::erase()),
                            g::emit_body_horizontal(lhs, rhs)) << "\n";
    }

    // Q + above C -> Q becomes R (so the per-piece R-spawn rule fires).
    {
        g::LhsPattern lhs;
        lhs[{-1, 0}] = g::lit(L'C');
        g::RhsPattern rhs;
        out << "# Q reaches centre column -> becomes R (spawn-ready)\n";
        out << g::emit_rule(g::header(L'Q', L'f', g::put(syms.walker)),
                            g::emit_body_vertical(lhs, rhs)) << "\n";
    }

    return out.str();
}

// Fall is fired by both the fall-timer 'g' and the player's soft-drop key 's'.
// Two stacked headers share the body — multi-header trick: parser stacks
// consecutive '=' lines onto the body that follows.
static std::string emit_fall(const Piece& p, const Orientation& o) {
    auto old_cells = terminal_set(o);
    auto new_cells = g::shifted(old_cells, 1, 0);
    auto md = g::move_diff(old_cells, new_cells);
    auto seed = seed_of(p);

    g::LhsPattern lhs;
    g::mark_each(lhs, g::difference(old_cells, {{0, 0}}), g::lit(p.glyph));
    g::mark_each(lhs, below_all(o), g::empty());

    g::RhsPattern rhs;
    g::mark_each(rhs, g::difference(md.erase, {{0, 0}}), g::erase());
    // Write seed at ALL new cells (incl. cells overlapping with old positions
    // — for non-I pieces with multi-row bodies, fall has overlap rows). If we
    // only wrote md.write, overlap cells would stay uppercase from previous
    // render and the all-lowercase render LHS would never match — body stuck
    // in mixed case. Same fix as lateral / rotation.
    g::mark_each(rhs, g::difference(new_cells, {{0, 0}}), g::put(seed));

    auto body = g::emit_body_vertical(lhs, rhs);
    std::string out;
    out += g::emit_header(coloured_move(p, p.glyph, L'g', g::erase())) + "\n";  // gravity tick
    out += g::emit_header(coloured_move(p, p.glyph, L's', g::erase())) + "\n";  // soft drop
    out += body;
    return out;
}

// Freeze is also fired by both the gravity tick and the player's soft-drop key
// 's'. RHS writes the X+piece-glyph pair encoding in LOWERCASE (x + lowercase
// piece-glyph). The convert rule (emit_frozen_convert below) fires once per
// pair on the next f-tick to upper-case them with bg=alias. This avoids the
// idempotent per-X-cell repaint that the old XfXIIII rule cost (~per-frozen-
// cell rule applications every f-tick) — same trap as the wall render, same
// fix.
static std::vector<std::string> emit_freeze(const Piece& p, const Orientation& o) {
    auto cells = terminal_set(o);
    auto seed_x = static_cast<wchar_t>(std::tolower(static_cast<int>(syms.frozen)));
    auto seed   = seed_of(p);
    std::vector<std::string> out;
    for (auto& below_cell : below_2col_aligned(o)) {
        g::LhsPattern lhs;
        lhs[{-1, 0}] = g::empty();  // signal `^` needs a clear cell to be written
        g::mark_each(lhs, g::difference(cells, {{0, 0}}), g::lit(p.glyph));
        lhs[below_cell] = g::ctx_or_rep();  // wall (field 6) OR frozen X (field 7)

        g::RhsPattern rhs;
        rhs[{-1, 0}] = g::put(syms.signal);  // `^` rises to spawn cell via memory restore
        // Even-col cells -> lowercase x; odd-col cells -> lowercase piece-glyph.
        // Convert rule promotes them to X + uppercase glyph + bg=alias next f-tick.
        for (auto& c : g::difference(cells, {{0, 0}})) {
            rhs[c] = (c.second % 2 == 0) ? g::put(seed_x) : g::put(seed);
        }

        auto h_g = coloured(p, p.glyph, L'g', g::put(seed_x));   // anchor: x (lowercase)
        h_g.ctx = syms.wall;
        h_g.ctxrep = syms.frozen;     // ctx_or_rep matches H or X (uppercase)
        auto h_s = h_g;
        h_s.trigger = L's';

        auto body = g::emit_body_vertical(lhs, rhs);
        out.push_back(g::emit_header(h_g) + "\n" + g::emit_header(h_s) + "\n" + body);
    }
    return out;
}

static std::string emit_lateral(const Piece& p, const Orientation& o, int dc) {
    auto old_cells = terminal_set(o);
    auto new_cells = g::shifted(old_cells, 0, dc);
    auto md = g::move_diff(old_cells, new_cells);
    auto seed = seed_of(p);

    g::LhsPattern lhs;
    g::mark_each(lhs, g::difference(old_cells, {{0, 0}}), g::lit(p.glyph));
    g::mark_each(lhs, md.write, g::empty());

    g::RhsPattern rhs;
    g::mark_each(rhs, g::difference(md.erase, {{0, 0}}), g::erase());
    // Write seed at ALL new cells (incl. cells overlapping with old positions)
    // so the body becomes uniformly lowercase — render LHS expects all-lower
    // and would otherwise see a mixed-case body and never fire, leaving the
    // piece visually frozen as a single block at the new edge.
    g::mark_each(rhs, g::difference(new_cells, {{0, 0}}), g::put(seed));

    wchar_t trigger = (dc < 0) ? L'a' : L'd';
    return g::emit_rule(coloured_move(p, p.glyph, trigger, g::replace_for_move(new_cells, seed)),
                        g::emit_body_horizontal(lhs, rhs));
}

// Pre-shaped rotation move: cells of `to` are shifted into `from`'s anchor
// frame so the screen pivot stays put.
static CellSet to_cells_in_from_frame(const Orientation& from, const Orientation& to) {
    auto sh = g::rotation_anchor_shift(from.shape.anchor, from.pivot,
                                       to.shape.anchor,   to.pivot,
                                       /*grid_w=*/2, /*grid_h=*/1);
    return g::shifted(terminal_set(to), sh.first, sh.second);
}

static std::pair<g::LhsPattern, g::RhsPattern>
rotation_patterns(const Piece& p, const Orientation& from, const Orientation& to) {
    auto from_cells = terminal_set(from);
    auto to_cells   = to_cells_in_from_frame(from, to);
    auto md = g::move_diff(from_cells, to_cells);
    auto seed = seed_of(p);

    g::LhsPattern lhs;
    g::mark_each(lhs, g::difference(from_cells, {{0, 0}}), g::lit(p.glyph));
    g::mark_each(lhs, md.write, g::empty());

    g::RhsPattern rhs;
    g::mark_each(rhs, g::difference(md.erase, {{0, 0}}), g::erase());
    // Same fix as lateral: write seed at ALL to_cells (incl. overlap with
    // from_cells) so the body is uniformly lowercase post-rotation.
    g::mark_each(rhs, g::difference(to_cells, {{0, 0}}), g::put(seed));

    return {lhs, rhs};
}

static std::string emit_rotation(const Piece& p, const Orientation& from,
                                 const Orientation& to, wchar_t trigger) {
    auto [lhs, rhs] = rotation_patterns(p, from, to);
    auto replace = g::replace_for_move(to_cells_in_from_frame(from, to), seed_of(p));
    return g::emit_rule(coloured_move(p, p.glyph, trigger, replace),
                        g::emit_body_horizontal(lhs, rhs));
}

static std::string emit_piece(const Piece& p) {
    std::ostringstream out;
    out << "# === " << static_cast<char>(p.glyph) << "-piece (" << p.colour << ") ===\n";
    out << "# spawn\n";
    out << emit_spawn(p, p.orientations[p.spawn_idx]) << "\n";

    for (auto& o : p.orientations) {
        out << "# " << o.name << ": render (full body, atomic)\n";
        out << emit_render(p, o) << "\n";
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
                auto replace = g::replace_for_move(to_cells_in_from_frame(from_o, to_o), p.glyph);

                out << "# " << from_o.name << " <-> " << to_o.name << " (CW & CCW share body)\n";
                auto rep_seed = g::replace_for_move(to_cells_in_from_frame(from_o, to_o), seed_of(p));
                out << g::emit_header(coloured_move(p, p.glyph, L'w', rep_seed)) << "\n";
                out << g::emit_rule(coloured_move(p, p.glyph, L'e', rep_seed),
                                    g::emit_body_horizontal(lhs, rhs)) << "\n";
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

static const char* FRAMEWORK = R"(#!{help} score:{score} rules:{steps}
#help a/d move - w/e rotate - ESC quit
# `f` declared before `g`: cfg.timing_chars is an unordered_map whose
# iteration order is hash-driven, and the user observed the f-first
# declaration reduces piece-move flash — render f-tick fires more
# eagerly relative to the g-tick.
#timing f 0
#timing g 500
#control ~ pause
#grid 2 1
# Initial symbol must precede any rule header (parser double-classifies
# ^-lines that follow a rule, leaking the line text into the previous
# rule's body — see backlog/research/tetris-exercise-friction.md, B1).
^PcC
# === Playfield seed: one-shot perimeter + R placement + C centre beacon ===
# C replaces one wall H at the centre column; R-spawn fires when above is C.
# C and R live at body col 12 (even) so spawn aligns with #grid 2 1.
==Pf~
@@hhhhhhhhhhchhhhhhhhhhhhh
  hh        R           hh
  hh                    hh
  hh                    hh
  hh                    hh
  hh                    hh
  hh                    hh
  hh                    hh
  hh                    hh
  hh                    hh
  hh          @         hh
  hh                    hh
  hh                    hh
  hh                    hh
  hh                    hh
  hh                    hh
  hh                    hh
  hh                    hh
  hh                    hh
  hh                    hh
  hh                    hh
  hhhhhhhhhhhhhhhhhhhhhhhh
# (R-walk-up replaced by `^` signal-rise via memory restore — see
#  emit_signal_rise in tetris_gen.cpp; freeze writes `^` instead of R.)
)";

int main() {
    auto pieces = all_pieces();

    std::cout << FRAMEWORK << "\n";

    std::cout << emit_wall_render() << "\n\n";
    std::cout << emit_signal_rise() << "\n";
    std::cout << emit_walker_state_machine() << "\n";
    std::cout << emit_game_over() << "\n\n";
    std::cout << "# === Stuck-at-top game over (per piece × orient × below_cell) ===\n";
    for (auto& rule : emit_stuck_at_top_game_over(pieces))
        std::cout << rule << "\n";
    std::cout << "\n";
    std::cout << emit_line_clear(pieces) << "\n";

    std::cout << "# === Colour palette ===\n";
    for (auto& p : pieces) {
        std::cout << g::emit_color_alias(p.glyph, p.color_code, p.color_attr)
                  << "  # " << p.colour << "\n";
    }
    std::cout << "\n";

    std::cout << emit_frozen_render(pieces) << "\n";

    for (auto& p : pieces) {
        std::cout << emit_piece(p) << "\n";
    }
    return 0;
}
