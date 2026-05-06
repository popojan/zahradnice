// zahradnice-check: validation and inspection tool for .cfg programs.
// Currently provides one subcommand:
//   explain CFG --line N
//     Print the resolved geometry of the rule whose head is on line N
//     (or, if N falls inside a body, the closest preceding head).

#include "../grammar.h"
#include <clocale>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <iostream>
#include <string>
#include <vector>

namespace {

std::string wstr_to_utf8(const std::wstring &w) {
    std::string out;
    out.reserve(w.size());
    char mb[MB_CUR_MAX + 1];
    for (wchar_t c : w) {
        int n = std::wctomb(mb, c);
        if (n > 0) out.append(mb, n);
        else out.push_back('?');
    }
    return out;
}

std::string display_char(wchar_t c) {
    if (c == L'\0' || c == (wchar_t)-1) return "?";
    if (c < 0x20 || c == 0x7f) {
        char buf[8];
        std::snprintf(buf, sizeof(buf), "\\x%02x", (unsigned)c);
        return buf;
    }
    return wstr_to_utf8(std::wstring(1, c));
}

struct BodyCell {
    int br;       // body row (0-indexed)
    int bc;       // body col (0-indexed)
    wchar_t ch;
};

std::vector<BodyCell> walk_body(const std::wstring &rhs) {
    std::vector<BodyCell> cells;
    int r = 0, c = 0;
    for (wchar_t ch : rhs) {
        if (ch == L'\n') { ++r; c = 0; continue; }
        if (ch != L' ') cells.push_back({r, c, ch});
        ++c;
    }
    return cells;
}

const char *role_name(const Grammar2D::Rule &rule, int br, int bc) {
    bool horiz = rule.cq > rule.co;
    bool boundary = horiz ? (bc == rule.cm && br == rule.rm)
                          : (br == rule.rm && bc == rule.cm);
    if (boundary) return "B";  // boundary separator
    bool is_lhs = horiz ? (bc < rule.cm) : (br < rule.rm);
    return is_lhs ? "L" : "R";
}

bool cell_in_lhs(const Grammar2D::Rule &rule, int br, int bc) {
    bool horiz = rule.cq > rule.co;
    return horiz ? (bc < rule.cm) : (br < rule.rm);
}

bool cell_in_rhs(const Grammar2D::Rule &rule, int br, int bc) {
    bool horiz = rule.cq > rule.co;
    return horiz ? (bc > rule.cm) : (br > rule.rm);
}

// Resolve what a body char *means* in match-time (read) context.
std::string explain_match_token(wchar_t ch, const Grammar2D::Rule &rule) {
    auto wc = [](wchar_t c) { return display_char(c); };
    switch (ch) {
        case L'@': return "matches anchor char '" + wc(rule.lhs) + "'";
        case L'&': return "matches ctx '" + wc(rule.ctx) + "'";
        case L'!': return "matches anything except ctx '" + wc(rule.ctx) + "'";
        case L'%': return "matches ctx '" + wc(rule.ctx) + "' or ctxrep '" + wc(rule.ctxrep) + "'";
        case L'~': return "matches space";
        default:   return "matches literal '" + wc(ch) + "'";
    }
}

// Resolve what a body char *means* in apply-time (write) context.
std::string explain_write_token(wchar_t ch, const Grammar2D::Rule &rule) {
    auto wc = [](wchar_t c) { return display_char(c); };
    switch (ch) {
        case L'@': return "writes rep '" + wc(rule.rep) + "'";
        case L'&': return "writes ctxrep '" + wc(rule.ctxrep) + "'";
        case L'~': return "writes space";
        case L'$': return "writes saved memory cell";
        default:   return "writes literal '" + wc(ch) + "'";
    }
}

void print_body_grid(const std::vector<BodyCell> &cells, const Grammar2D::Rule &rule) {
    if (cells.empty()) { std::cout << "  (empty body)\n"; return; }
    int max_r = 0, max_c = 0;
    for (auto &cell : cells) {
        if (cell.br > max_r) max_r = cell.br;
        if (cell.bc > max_c) max_c = cell.bc;
    }
    const int LABEL_W = 9;  // width of row-label column, must fit "  role: "
    // Column header
    std::printf("%-*s", LABEL_W, "");
    for (int c = 0; c <= max_c; ++c) std::printf("%2d ", c);
    std::cout << "\n";
    for (int r = 0; r <= max_r; ++r) {
        char rlabel[16];
        std::snprintf(rlabel, sizeof(rlabel), "  r%d:", r);
        std::printf("%-*s", LABEL_W, rlabel);
        // char row
        std::vector<std::string> line(max_c + 1, ".");
        for (auto &cell : cells) {
            if (cell.br == r) line[cell.bc] = display_char(cell.ch);
        }
        for (auto &s : line) std::printf("%2s ", s.c_str());
        std::cout << "\n";
        // role row
        std::printf("%-*s", LABEL_W, "  role:");
        std::vector<std::string> roles(max_c + 1, ".");
        for (auto &cell : cells) {
            if (cell.br == r) {
                bool anchor = (cell.br == rule.rq && cell.bc == rule.cq);
                if (anchor) roles[cell.bc] = "A";
                else roles[cell.bc] = role_name(rule, cell.br, cell.bc);
            }
        }
        for (auto &s : roles) std::printf("%2s ", s.c_str());
        std::cout << "\n";
    }
    std::cout << "\n  legend: L=LHS(read)  R=RHS(write)  B=boundary  A=anchor  .=empty\n";
}

void print_offset_tables(const std::vector<BodyCell> &cells, const Grammar2D::Rule &rule) {
    std::cout << "  matches (offset relative to anchor):\n";
    bool any = false;
    for (auto &cell : cells) {
        if (!cell_in_lhs(rule, cell.br, cell.bc)) continue;
        int dr = cell.br - rule.rq;
        int dc = cell.bc - rule.cq;
        std::printf("    (%+d,%+d) '%s' — %s\n", dr, dc,
                    display_char(cell.ch).c_str(),
                    explain_match_token(cell.ch, rule).c_str());
        any = true;
    }
    if (!any) std::cout << "    (none)\n";

    std::cout << "  writes (offset relative to anchor):\n";
    any = false;
    for (auto &cell : cells) {
        if (!cell_in_rhs(rule, cell.br, cell.bc)) continue;
        int dr = cell.br - rule.rq;
        int dc = cell.bc - rule.cq;
        std::printf("    (%+d,%+d) '%s' — %s\n", dr, dc,
                    display_char(cell.ch).c_str(),
                    explain_write_token(cell.ch, rule).c_str());
        any = true;
    }
    if (!any) std::cout << "    (none)\n";
}

void print_header(const std::string &cfg_path, const Grammar2D::Rule &rule) {
    std::printf("=== rule at %s:%d ===\n", cfg_path.c_str(), rule.source_line);
    std::printf("  head     = %s\n", wstr_to_utf8(rule.lhsa).c_str());
    std::printf("  lhs      = '%s'   (anchor char this rule rewrites)\n",
                display_char(rule.lhs).c_str());
    std::printf("  trigger  = '%s'\n", display_char(rule.key).c_str());
    std::printf("  rep      = '%s'   (replaces '@' on RHS)\n",
                display_char(rule.rep).c_str());
    std::printf("  ctx      = '%s'   ctxrep = '%s'\n",
                display_char(rule.ctx == (wchar_t)-1 ? L'?' : rule.ctx).c_str(),
                display_char(rule.ctxrep).c_str());
    std::printf("  fore=%d back=%d  reward=%d  weight=%d\n",
                (int)rule.fore, (int)rule.back, rule.reward, rule.weight);
    bool horiz = rule.cq > rule.co;
    std::printf("  orient   = %s (cq=%d, co=%d, cm=%d, rm=%d, rq=%d)\n",
                horiz ? "horizontal" : "vertical",
                rule.cq, rule.co, rule.cm, rule.rm, rule.rq);
}

const Grammar2D::Rule *find_by_line(const Grammar2D &g, int line, int *closest_le) {
    const Grammar2D::Rule *best = nullptr;
    int best_line = -1;
    for (const auto &kv : g.R) {
        for (const auto &r : kv.second) {
            if (r.source_line == line) return &r;  // exact match
            if (r.source_line < line && r.source_line > best_line) {
                best = &r;
                best_line = r.source_line;
            }
        }
    }
    if (closest_le) *closest_le = best_line;
    return best;
}

int cmd_explain(int argc, char *argv[]) {
    std::string cfg_path;
    int line = -1;
    for (int i = 0; i < argc; ++i) {
        std::string a = argv[i];
        if (a == "--line") {
            if (i + 1 >= argc) {
                std::cerr << "missing value for --line\n"; return 1;
            }
            line = std::atoi(argv[++i]);
        } else if (!a.empty() && a[0] == '-') {
            std::cerr << "unknown option: " << a << "\n"; return 1;
        } else if (cfg_path.empty()) {
            cfg_path = a;
        } else {
            std::cerr << "extra positional arg: " << a << "\n"; return 1;
        }
    }
    if (cfg_path.empty() || line < 0) {
        std::cerr <<
            "Usage: zahradnice-check explain CFG --line N\n"
            "  CFG     path to .cfg program\n"
            "  --line  source line of the rule head (=HEAD line)\n";
        return 2;
    }

    Grammar2D g;
    if (!g.loadFromFile(cfg_path)) {
        std::cerr << "Failed to load: " << cfg_path << "\n";
        return 1;
    }

    int closest = -1;
    const Grammar2D::Rule *r = find_by_line(g, line, &closest);
    if (!r) {
        std::cerr << "No rule found at or before line " << line
                  << " in " << cfg_path << ".\n";
        return 3;
    }
    if (r->source_line != line) {
        std::cerr << "Note: line " << line
                  << " is not a rule head; falling back to closest preceding head at line "
                  << r->source_line << ".\n\n";
    }

    print_header(cfg_path, *r);
    auto cells = walk_body(r->rhs);
    std::cout << "\n  body grid:\n";
    print_body_grid(cells, *r);
    std::cout << "\n";
    print_offset_tables(cells, *r);
    return 0;
}

void usage() {
    std::cerr <<
        "Usage: zahradnice-check <subcommand> [args]\n"
        "Subcommands:\n"
        "  explain CFG --line N    print the resolved geometry of one rule\n";
}

}  // namespace

int main(int argc, char *argv[]) {
    setlocale(LC_ALL, "");
    if (argc < 2) { usage(); return 2; }
    std::string sub = argv[1];
    if (sub == "explain") return cmd_explain(argc - 2, argv + 2);
    if (sub == "-h" || sub == "--help") { usage(); return 0; }
    std::cerr << "unknown subcommand: " << sub << "\n";
    usage();
    return 2;
}
