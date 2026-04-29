#include "genlib.h"

#include <algorithm>
#include <sstream>
#include <stdexcept>

namespace genlib {

namespace {

// Map Match to its on-screen body glyph.
char match_glyph(const Match& m) {
    switch (m.kind) {
        case Match::Kind::Glyph:       return static_cast<char>(m.glyph);
        case Match::Kind::Empty:       return '~';
        case Match::Kind::Ctx:         return '&';
        case Match::Kind::NotCtx:      return '!';
        case Match::Kind::CtxOrCtxRep: return '%';
    }
    throw std::logic_error("genlib: unhandled Match::Kind");
}

char write_glyph(const Write& w) {
    switch (w.kind) {
        case Write::Kind::Glyph:    return static_cast<char>(w.glyph);
        case Write::Kind::Erase:    return '~';
        case Write::Kind::Ctx:      return '&';
        case Write::Kind::Memory:   return '$';
        case Write::Kind::Preserve: return ' ';
    }
    throw std::logic_error("genlib: unhandled Write::Kind");
}

// Indent-escape (friction journal B7): if any body line would start with a
// parser-special char, indent every line by one space.
std::string safe_indent(const std::string& body) {
    bool needs = false;
    bool at_line_start = true;
    for (char c : body) {
        if (at_line_start && (c == '#' || c == '^' || c == '=')) { needs = true; break; }
        at_line_start = (c == '\n');
    }
    if (!needs) return body;

    std::string out;
    out.reserve(body.size() + body.size() / 16 + 1);
    out.push_back(' ');
    for (char c : body) {
        out.push_back(c);
        if (c == '\n') out.push_back(' ');
    }
    return out;
}

// Render a 2D char grid back to text, trimming trailing spaces on each line.
std::string grid_to_string(const std::vector<std::vector<char>>& grid) {
    std::string out;
    for (size_t i = 0; i < grid.size(); ++i) {
        const auto& row = grid[i];
        size_t end = row.size();
        while (end > 0 && row[end - 1] == ' ') --end;
        out.append(row.data(), end);
        if (i + 1 < grid.size()) out.push_back('\n');
    }
    return out;
}

}  // namespace

// --- Header ---

std::string emit_header(const Header& h) {
    std::string out;
    out.push_back('=');
    out.push_back(static_cast<char>(h.sound));
    out.push_back(static_cast<char>(h.lhs));
    out.push_back(static_cast<char>(h.trigger));
    out.push_back(write_glyph(h.replace));

    bool need_ext = h.fore || h.back || h.ctx || h.ctxrep;
    if (need_ext) {
        out.push_back(h.fore ? *h.fore : '7');
        out.push_back(h.back ? *h.back : '8');
        out.push_back(h.ctx ? static_cast<char>(*h.ctx) : ' ');
        out.push_back(h.ctxrep ? static_cast<char>(*h.ctxrep) : ' ');
    }
    return out;
}

// --- Body builders ---

std::string emit_body_vertical(const LhsPattern& lhs, const RhsPattern& rhs) {
    // Column extent across both regions plus anchor at (0,0).
    int min_dc = 0, max_dc = 0;
    auto note_dc = [&](int dc) { min_dc = std::min(min_dc, dc); max_dc = std::max(max_dc, dc); };
    for (auto& kv : lhs) note_dc(kv.first.second);
    for (auto& kv : rhs) note_dc(kv.first.second);
    int C = -min_dc;  // anchor column in body grid

    // LHS row extent (include anchor row 0).
    int lhs_min_dr = 0, lhs_max_dr = 0;
    for (auto& kv : lhs) { lhs_min_dr = std::min(lhs_min_dr, kv.first.first);
                           lhs_max_dr = std::max(lhs_max_dr, kv.first.first); }
    int R_a = -lhs_min_dr;
    int boundary_row = R_a + lhs_max_dr + 1;

    int rhs_min_dr = 0, rhs_max_dr = 0;
    for (auto& kv : rhs) { rhs_min_dr = std::min(rhs_min_dr, kv.first.first);
                           rhs_max_dr = std::max(rhs_max_dr, kv.first.first); }
    int R_b = boundary_row + 1 - rhs_min_dr;

    int nrows = R_b + rhs_max_dr + 1;
    int ncols = C + max_dc + 1;
    std::vector<std::vector<char>> g(nrows, std::vector<char>(ncols, ' '));

    for (auto& kv : lhs) g[R_a + kv.first.first][C + kv.first.second] = match_glyph(kv.second);
    g[R_a][C] = '@';
    g[boundary_row][C] = '@';
    for (auto& kv : rhs) g[R_b + kv.first.first][C + kv.first.second] = write_glyph(kv.second);
    g[R_b][C] = '@';

    return safe_indent(grid_to_string(g));
}

std::string emit_body_horizontal(const LhsPattern& lhs, const RhsPattern& rhs) {
    int lhs_min_dr = 0, lhs_max_dr = 0, lhs_min_dc = 0, lhs_max_dc = 0;
    for (auto& kv : lhs) {
        lhs_min_dr = std::min(lhs_min_dr, kv.first.first);
        lhs_max_dr = std::max(lhs_max_dr, kv.first.first);
        lhs_min_dc = std::min(lhs_min_dc, kv.first.second);
        lhs_max_dc = std::max(lhs_max_dc, kv.first.second);
    }
    int R_a = -lhs_min_dr;
    int C_a = -lhs_min_dc;
    int lhs_max_col = C_a + lhs_max_dc;
    int boundary_col = lhs_max_col + 1;

    int rhs_min_dr = 0, rhs_max_dr = 0, rhs_min_dc = 0, rhs_max_dc = 0;
    for (auto& kv : rhs) {
        rhs_min_dr = std::min(rhs_min_dr, kv.first.first);
        rhs_max_dr = std::max(rhs_max_dr, kv.first.first);
        rhs_min_dc = std::min(rhs_min_dc, kv.first.second);
        rhs_max_dc = std::max(rhs_max_dc, kv.first.second);
    }
    int R_b = R_a;
    if (R_b + rhs_min_dr < 0) {
        int bump = -(R_b + rhs_min_dr);
        R_a += bump;
        R_b += bump;
    }
    int C_b = boundary_col + 1 - rhs_min_dc;

    int nrows = std::max(R_a + lhs_max_dr, R_b + rhs_max_dr) + 1;
    int ncols = std::max(lhs_max_col, C_b + rhs_max_dc) + 1;
    std::vector<std::vector<char>> g(nrows, std::vector<char>(ncols, ' '));

    for (auto& kv : lhs) g[R_a + kv.first.first][C_a + kv.first.second] = match_glyph(kv.second);
    g[R_a][C_a] = '@';
    g[R_a][boundary_col] = '@';
    for (auto& kv : rhs) g[R_b + kv.first.first][C_b + kv.first.second] = write_glyph(kv.second);
    g[R_b][C_b] = '@';

    return safe_indent(grid_to_string(g));
}

std::string emit_rule(const Header& h, const std::string& body) {
    return emit_header(h) + '\n' + body;
}

// --- Geometry primitives ---

std::vector<Cell> terminal_cells(const Shape& s, int grid_w, int grid_h) {
    std::vector<Cell> out;
    out.reserve(s.cells.size() * static_cast<size_t>(grid_w) * grid_h);
    int ar = s.anchor.first, ac = s.anchor.second;
    for (auto& pc : s.cells) {
        int pr = pc.first, pcc = pc.second;
        for (int dr = 0; dr < grid_h; ++dr) {
            for (int dc = 0; dc < grid_w; ++dc) {
                out.emplace_back((pr - ar) * grid_h + dr, (pcc - ac) * grid_w + dc);
            }
        }
    }
    return out;
}

std::vector<Cell> shifted(const std::vector<Cell>& cells, int dr, int dc) {
    std::vector<Cell> out;
    out.reserve(cells.size());
    for (auto& c : cells) out.emplace_back(c.first + dr, c.second + dc);
    return out;
}

CellSet shifted(const CellSet& cells, int dr, int dc) {
    CellSet out;
    for (auto& c : cells) out.emplace(c.first + dr, c.second + dc);
    return out;
}

CellSet difference(const CellSet& a, const CellSet& b) {
    CellSet out;
    for (auto& c : a) if (!b.count(c)) out.insert(c);
    return out;
}

Cell rotation_anchor_shift(Cell from_anchor, Cell from_pivot,
                           Cell to_anchor,   Cell to_pivot,
                           int grid_w, int grid_h) {
    int fdr = (from_pivot.first  - from_anchor.first)  * grid_h;
    int fdc = (from_pivot.second - from_anchor.second) * grid_w;
    int tdr = (to_pivot.first    - to_anchor.first)    * grid_h;
    int tdc = (to_pivot.second   - to_anchor.second)   * grid_w;
    return {fdr - tdr, fdc - tdc};
}

// --- ASCII art loader ---

ArtMap parse_art(const std::string& art, char anchor_marker) {
    int anchor_row = 0, anchor_col = 0;
    bool found = false;

    auto walk = [&](auto on_cell) {
        int r = 0, c = 0;
        for (char ch : art) {
            if (ch == '\n') { ++r; c = 0; continue; }
            on_cell(r, c, ch);
            ++c;
        }
    };

    walk([&](int r, int c, char ch) {
        if (!found && ch == anchor_marker) {
            anchor_row = r; anchor_col = c; found = true;
        }
    });
    if (!found) {
        throw std::invalid_argument("genlib::parse_art: anchor marker not found");
    }

    ArtMap out;
    walk([&](int r, int c, char ch) {
        if (ch == ' ' || ch == '\t' || ch == '\r') return;
        if (ch == anchor_marker && r == anchor_row && c == anchor_col) return;
        out[{r - anchor_row, c - anchor_col}] = static_cast<wchar_t>(ch);
    });
    return out;
}

LhsPattern art_lhs(const std::string& art, char anchor_marker) {
    LhsPattern p;
    for (auto& kv : parse_art(art, anchor_marker)) p[kv.first] = lit(kv.second);
    return p;
}

RhsPattern art_rhs(const std::string& art, char anchor_marker) {
    RhsPattern p;
    for (auto& kv : parse_art(art, anchor_marker)) p[kv.first] = put(kv.second);
    return p;
}

DiffResult art_frame_diff(const std::string& a, const std::string& b, char anchor_marker) {
    auto ma = parse_art(a, anchor_marker);
    auto mb = parse_art(b, anchor_marker);
    DiffResult out;
    for (auto& kv : ma) out.lhs[kv.first] = lit(kv.second);
    for (auto& kv : ma) {
        auto it = mb.find(kv.first);
        if (it == mb.end())               out.rhs[kv.first] = erase();
        else if (it->second != kv.second) out.rhs[kv.first] = put(it->second);
    }
    for (auto& kv : mb) {
        if (!ma.count(kv.first))          out.rhs[kv.first] = put(kv.second);
    }
    return out;
}

}  // namespace genlib
