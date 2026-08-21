// zahradnice-check: validation and inspection tool for .cfg programs.
// Subcommands:
//   explain CFG --line N | --head 'HEAD'
//     Print the resolved geometry of one rule (static).
//   why CFG --screen FILE --trigger K [--rule N]
//     Dynamic rule-match diagnostics: which rules fire / are near-miss
//     / are excluded for the given (screen, trigger).

#include "../grammar.h"
#include "../wide_io.h"
#include <algorithm>
#include <clocale>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <iostream>
#include <string>
#include <unordered_map>
#include <unordered_set>
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
    std::cout << "  matches (offset from @1, dry-run origin):\n";
    bool any = false;
    for (auto &cell : cells) {
        if (!cell_in_lhs(rule, cell.br, cell.bc)) continue;
        int dr = cell.br - rule.ro;
        int dc = cell.bc - rule.co;
        std::printf("    (%+d,%+d) '%s' — %s\n", dr, dc,
                    display_char(cell.ch).c_str(),
                    explain_match_token(cell.ch, rule).c_str());
        any = true;
    }
    if (!any) std::cout << "    (none)\n";

    std::cout << "  writes (offset from @3, apply origin):\n";
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
    std::printf("  fore=%d back=%d  reward=%d  weight=%g\n",
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

std::vector<const Grammar2D::Rule *> find_by_head(const Grammar2D &g,
                                                  const std::wstring &head) {
    std::vector<const Grammar2D::Rule *> out;
    for (const auto &kv : g.R) {
        for (const auto &r : kv.second) {
            if (r.lhsa == head) out.push_back(&r);
        }
    }
    return out;
}

std::wstring utf8_to_wstr(const std::string &s) {
    std::wstring out;
    out.reserve(s.size());
    std::mbstate_t st = {};
    const char *p = s.c_str();
    size_t left = s.size();
    while (left > 0) {
        wchar_t wc;
        size_t n = std::mbrtowc(&wc, p, left, &st);
        if (n == 0 || n == (size_t)-1 || n == (size_t)-2) {
            out.push_back((wchar_t)(unsigned char)*p);
            ++p; --left;
        } else {
            out.push_back(wc);
            p += n; left -= n;
        }
    }
    return out;
}

void emit_rule(const std::string &cfg_path, const Grammar2D::Rule &r) {
    print_header(cfg_path, r);
    auto cells = walk_body(r.rhs);
    std::cout << "\n  body grid:\n";
    print_body_grid(cells, r);
    std::cout << "\n";
    print_offset_tables(cells, r);
}

int cmd_explain(int argc, char *argv[]) {
    std::string cfg_path;
    std::string head_str;
    int line = -1;
    for (int i = 0; i < argc; ++i) {
        std::string a = argv[i];
        if (a == "--line") {
            if (i + 1 >= argc) {
                std::cerr << "missing value for --line\n"; return 1;
            }
            line = std::atoi(argv[++i]);
        } else if (a == "--head") {
            if (i + 1 >= argc) {
                std::cerr << "missing value for --head\n"; return 1;
            }
            head_str = argv[++i];
        } else if (!a.empty() && a[0] == '-') {
            std::cerr << "unknown option: " << a << "\n"; return 1;
        } else if (cfg_path.empty()) {
            cfg_path = a;
        } else {
            std::cerr << "extra positional arg: " << a << "\n"; return 1;
        }
    }
    if (cfg_path.empty() || (line < 0 && head_str.empty())) {
        std::cerr <<
            "Usage: zahradnice-check explain CFG (--line N | --head 'HEAD')\n"
            "  CFG     path to .cfg program\n"
            "  --line  source line of the rule head (=HEAD line)\n"
            "  --head  literal head string from the trace's head column\n"
            "          (line-edit robust; copy-paste straight from trace)\n";
        return 2;
    }
    if (line >= 0 && !head_str.empty()) {
        std::cerr << "--line and --head are mutually exclusive\n"; return 1;
    }

    Grammar2D g;
    if (!g.loadFromFile(cfg_path)) {
        std::cerr << "Failed to load: " << cfg_path << "\n";
        return 1;
    }

    if (!head_str.empty()) {
        std::wstring whead = utf8_to_wstr(head_str);
        auto matches = find_by_head(g, whead);
        if (matches.empty()) {
            std::cerr << "No rule with head '" << head_str
                      << "' in " << cfg_path << ".\n";
            return 3;
        }
        if (matches.size() > 1) {
            std::cerr << "Note: " << matches.size()
                      << " rules share this head; printing all.\n\n";
        }
        for (size_t i = 0; i < matches.size(); ++i) {
            if (i) std::cout << "\n";
            emit_rule(cfg_path, *matches[i]);
        }
        return 0;
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
    emit_rule(cfg_path, *r);
    return 0;
}

// ---------- why subcommand ----------

struct LoadedScreen {
    int rows;
    int cols;
    std::vector<wchar_t> buf;  // row-major rows*cols
};

bool load_screen_dump(const std::string &path, LoadedScreen &out) {
    std::wifstream f(path);
    if (!f) {
        std::cerr << "cannot open --screen file: " << path << "\n";
        return false;
    }
    imbue_utf8(f);
    std::vector<std::wstring> lines;
    std::wstring line;
    while (std::getline(f, line)) lines.push_back(line);
    if (lines.empty()) {
        std::cerr << "--screen file is empty\n";
        return false;
    }
    int cols = 0;
    for (const auto &l : lines) cols = std::max(cols, (int)l.size());
    if (cols == 0) {
        std::cerr << "--screen file has no content\n";
        return false;
    }
    out.rows = (int)lines.size();
    out.cols = cols;
    out.buf.assign((size_t)out.rows * out.cols, L' ');
    for (int r = 0; r < out.rows; ++r) {
        const std::wstring &l = lines[r];
        for (int c = 0; c < (int)l.size() && c < out.cols; ++c) {
            out.buf[(size_t)r * out.cols + c] = l[c];
        }
    }
    return true;
}

// Outcome bucket for one (rule, anchor position) probe.
struct WhyResult {
    const Grammar2D::Rule *rule;
    int anchor_r, anchor_c;       // wrapped screen coords of the anchor
    std::vector<CellProbe> probes;
    int miss_count;               // # of failing context cells
};

// Sink used by dry_run_explain: appends to a vector<CellProbe>.
void why_probe_sink(const CellProbe &p, void *ctx) {
    auto *v = static_cast<std::vector<CellProbe>*>(ctx);
    v->push_back(p);
}

const char *body_token_role(wchar_t body_ch) {
    switch (body_ch) {
        case L'@': return "anchor";
        case L'&': return "ctx";
        case L'!': return "not-ctx";
        case L'%': return "ctx-or-ctxrep";
        default:   return "literal";
    }
}

void print_probe_table(const std::vector<CellProbe> &probes) {
    std::printf("    body    screen   body-ch  expected  actual   outcome\n");
    for (const auto &p : probes) {
        char outcome = p.matched ? '*' : 'X';
        std::printf("    (%2d,%2d) (%2d,%2d)  '%s' (%s)  '%s'       '%s'      %s\n",
                    p.body_r, p.body_c,
                    p.screen_r, p.screen_c,
                    display_char(p.body_ch).c_str(),
                    body_token_role(p.body_ch),
                    display_char(p.expected).c_str(),
                    display_char(p.actual).c_str(),
                    p.matched ? "match" : "MISS");
        if (!p.matched) std::printf("                                   ^^^ first miss is decisive\n");
        if (!p.matched) break;  // engine semantics: first miss decides; show it then stop
    }
}

bool rule_uses_memory(const Grammar2D::Rule &rule) {
    return rule.rhs.find(L'$') != std::wstring::npos;
}

int cmd_why(int argc, char *argv[]) {
    std::string cfg_path, screen_path;
    std::string trigger_str;
    int focus_line = -1;
    int near_miss_cap = 3;
    bool verbose = false;

    for (int i = 0; i < argc; ++i) {
        std::string a = argv[i];
        auto need = [&](const char *flag) -> bool {
            if (i + 1 >= argc) {
                std::cerr << "missing value for " << flag << "\n";
                return false;
            }
            return true;
        };
        if (a == "--screen")          { if (!need("--screen")) return 1; screen_path = argv[++i]; }
        else if (a == "--trigger")    { if (!need("--trigger")) return 1; trigger_str = argv[++i]; }
        else if (a == "--rule")       { if (!need("--rule")) return 1; focus_line = std::atoi(argv[++i]); }
        else if (a == "--near-miss")  { if (!need("--near-miss")) return 1; near_miss_cap = std::atoi(argv[++i]); }
        else if (a == "--verbose" || a == "-v") { verbose = true; }
        else if (!a.empty() && a[0] == '-') {
            std::cerr << "unknown option: " << a << "\n"; return 1;
        } else if (cfg_path.empty()) { cfg_path = a; }
        else { std::cerr << "extra positional arg: " << a << "\n"; return 1; }
    }
    if (cfg_path.empty() || screen_path.empty() || trigger_str.empty()) {
        std::cerr <<
            "Usage: zahradnice-check why CFG --screen FILE --trigger K [opts]\n"
            "  CFG            path to .cfg program\n"
            "  --screen FILE  screen state (from `--dump-screen -.txt`); `-` = stdin\n"
            "  --trigger K    single trigger char; `~` means SPACE\n"
            "  --rule N       focus on the rule whose head is on cfg line N\n"
            "  --near-miss N  show rules off by ≤N context cells (default 3)\n"
            "  --verbose      list every excluded rule (default: summary)\n";
        return 2;
    }

    // Resolve trigger.
    std::wstring trig_ws = utf8_to_wstr(trigger_str);
    if (trig_ws.size() != 1) {
        std::cerr << "--trigger must be a single character (got "
                  << trig_ws.size() << " wchars)\n";
        return 1;
    }
    wchar_t trigger = trig_ws[0];
    if (trigger == L'~') trigger = L' ';

    // Load grammar.
    Grammar2D g;
    if (!g.loadFromFile(cfg_path)) {
        std::cerr << "Failed to load: " << cfg_path << "\n";
        return 1;
    }

    // Load screen.
    LoadedScreen scr;
    if (screen_path == "-") {
        // Slurp stdin into a temp file path workaround: read directly here.
        std::vector<std::wstring> lines;
        std::wstring line;
        while (std::getline(std::wcin, line)) lines.push_back(line);
        int cols = 0;
        for (const auto &l : lines) cols = std::max(cols, (int)l.size());
        if (lines.empty() || cols == 0) {
            std::cerr << "stdin: no screen content\n"; return 1;
        }
        scr.rows = (int)lines.size();
        scr.cols = cols;
        scr.buf.assign((size_t)scr.rows * scr.cols, L' ');
        for (int r = 0; r < scr.rows; ++r) {
            const std::wstring &l = lines[r];
            for (int c = 0; c < (int)l.size() && c < scr.cols; ++c) {
                scr.buf[(size_t)r * scr.cols + c] = l[c];
            }
        }
    } else {
        if (!load_screen_dump(screen_path, scr)) return 1;
    }

    // Build a Derivation against the loaded screen.
    Derivation w;
    w.reset(g, scr.rows, scr.cols);
    w.init(true);
    // The engine reserves row 0 for the status line; the dump's row 0
    // is the rendered status. Engine state lives in rows 1..rows-1.
    // SPACE in the dump represents an empty cell; copy as-is — the
    // matcher normalises SPACE↔'~' itself.
    for (int r = 1; r < scr.rows; ++r) {
        for (int c = 0; c < scr.cols; ++c) {
            wchar_t ch = scr.buf[(size_t)r * scr.cols + c];
            w.screen_chars[r * scr.cols + c] = ch;
        }
    }
    // Build x map: every cell whose char is some rule's lhs counts.
    std::unordered_set<wchar_t> all_lhs;
    for (const auto &kv : g.R) all_lhs.insert(kv.first);
    for (int r = 1; r < scr.rows; ++r) {
        for (int c = 0; c < scr.cols; ++c) {
            wchar_t ch = w.screen_chars[r * scr.cols + c];
            if (all_lhs.count(ch)) w.x[{r, c}] = ch;
        }
    }

    // Iterate rules, classify each.
    struct Excluded {
        const Grammar2D::Rule *rule;
        std::string reason;
    };
    std::vector<WhyResult> matched;
    std::vector<WhyResult> near_miss;
    std::vector<Excluded> excluded;

    for (const auto &kv : g.R) {
        wchar_t lhs = kv.first;
        for (const auto &rule : kv.second) {
            // Trigger filter.
            if (rule.key != trigger && rule.key != L'?') {
                excluded.push_back({&rule, "trigger mismatch (rule key '"
                                    + display_char(rule.key) + "')"});
                continue;
            }
            // Anchor present?
            bool any_anchor = false;
            for (const auto &it : w.x) {
                if (it.second == lhs) { any_anchor = true; break; }
            }
            if (!any_anchor) {
                excluded.push_back({&rule, "anchor '"
                                    + display_char(lhs) + "' not on screen"});
                continue;
            }
            // Probe at every anchor position.
            for (const auto &it : w.x) {
                if (it.second != lhs) continue;
                int R = it.first.first;
                int C = it.first.second;
                std::vector<CellProbe> probes;
                bool all_match = w.dry_run_explain(R - rule.ro, C - rule.co,
                                                   rule, why_probe_sink, &probes);
                int misses = 0;
                for (const auto &p : probes) if (!p.matched) ++misses;
                WhyResult res{&rule, R, C, std::move(probes), misses};
                if (all_match)         matched.push_back(std::move(res));
                else if (misses <= near_miss_cap) near_miss.push_back(std::move(res));
                // else drop (miss); --rule mode below still finds it.
            }
        }
    }

    // Focused output mode.
    if (focus_line >= 0) {
        int closest = -1;
        const Grammar2D::Rule *focus = find_by_line(g, focus_line, &closest);
        if (!focus) {
            std::cerr << "No rule at or before line " << focus_line << "\n";
            return 3;
        }
        if (focus->source_line != focus_line) {
            std::cerr << "Note: line " << focus_line
                      << " is not a rule head; using closest preceding head at line "
                      << focus->source_line << ".\n\n";
        }
        std::printf("=== %s:%d  %s ===\n",
                    cfg_path.c_str(), focus->source_line,
                    wstr_to_utf8(focus->lhsa).c_str());
        std::printf("  trigger  = '%s' %s\n",
                    display_char(focus->key).c_str(),
                    (focus->key == trigger || focus->key == L'?')
                      ? "(matches)" : "(MISMATCH — rule key)");
        if (rule_uses_memory(*focus)) {
            std::printf("  WARNING: rule body contains '$' — match outcome may depend\n"
                        "           on memory[r,c] state, which is not represented in the\n"
                        "           screen dump. Result below treats memory cells as ' '.\n");
        }
        std::printf("  lhs      = '%s'\n", display_char(focus->lhs).c_str());
        std::printf("\n");
        // Re-probe just this rule at every anchor position so we get
        // full output even for rules that didn't make it into matched/
        // near_miss (i.e. rules off by more than near_miss_cap cells).
        bool any = false;
        for (const auto &it : w.x) {
            if (it.second != focus->lhs) continue;
            any = true;
            int R = it.first.first;
            int C = it.first.second;
            std::vector<CellProbe> probes;
            bool ok = w.dry_run_explain(R - focus->ro, C - focus->co,
                                        *focus, why_probe_sink, &probes);
            std::printf("  Anchor '%s' at (%d, %d): %s\n",
                        display_char(focus->lhs).c_str(), R, C,
                        ok ? "WOULD FIRE" : "would not fire");
            print_probe_table(probes);
            int misses = 0;
            for (const auto &p : probes) if (!p.matched) ++misses;
            if (!ok) std::printf("  → %d context cell%s mismatch.\n",
                                 misses, misses == 1 ? "" : "s");
            std::printf("\n");
        }
        if (!any) {
            std::printf("  Anchor '%s' not present on screen — rule cannot fire here.\n",
                        display_char(focus->lhs).c_str());
        }
        return 0;
    }

    // Default summary output.
    auto print_pos = [](const WhyResult &r) {
        std::printf("(%d, %d)", r.anchor_r, r.anchor_c);
    };

    std::printf("Trigger '%s' against %s:\n\n",
                display_char(trigger).c_str(), screen_path.c_str());

    std::printf("Matching rules (%zu would fire):\n", matched.size());
    if (matched.empty()) std::printf("  (none)\n");
    for (const auto &r : matched) {
        std::printf("  %s:%d  %s   anchor at ",
                    cfg_path.c_str(), r.rule->source_line,
                    wstr_to_utf8(r.rule->lhsa).c_str());
        print_pos(r);
        if (rule_uses_memory(*r.rule))
            std::printf("   [uses '$', match may depend on memory]");
        std::printf("\n");
    }

    std::printf("\nNear-miss rules (≤%d cell%s off):\n",
                near_miss_cap, near_miss_cap == 1 ? "" : "s");
    if (near_miss.empty()) std::printf("  (none)\n");
    for (const auto &r : near_miss) {
        std::printf("  %s:%d  %s   %d cell%s off at ",
                    cfg_path.c_str(), r.rule->source_line,
                    wstr_to_utf8(r.rule->lhsa).c_str(),
                    r.miss_count, r.miss_count == 1 ? "" : "s");
        print_pos(r);
        std::printf(":\n");
        for (const auto &p : r.probes) {
            if (p.matched) continue;
            std::printf("                       (%d, %d) expected '%s' (%s), got '%s'\n",
                        p.screen_r, p.screen_c,
                        display_char(p.expected).c_str(),
                        body_token_role(p.body_ch),
                        display_char(p.actual).c_str());
            break;  // engine semantics: first miss is decisive
        }
    }

    std::printf("\nExcluded (%zu rule%s):\n",
                excluded.size(), excluded.size() == 1 ? "" : "s");
    if (verbose) {
        for (const auto &e : excluded) {
            std::printf("  %s:%d  %s   %s\n",
                        cfg_path.c_str(), e.rule->source_line,
                        wstr_to_utf8(e.rule->lhsa).c_str(),
                        e.reason.c_str());
        }
    } else {
        // Group by reason for compactness.
        std::unordered_map<std::string, int> by_reason;
        for (const auto &e : excluded) by_reason[e.reason]++;
        for (const auto &kv : by_reason) {
            std::printf("  %d × %s\n", kv.second, kv.first.c_str());
        }
        if (!excluded.empty()) std::printf("  (use --verbose to list)\n");
    }
    return 0;
}

void usage() {
    std::cerr <<
        "Usage: zahradnice-check <subcommand> [args]\n"
        "Subcommands:\n"
        "  explain CFG --line N           resolved geometry of one rule\n"
        "  why CFG --screen FILE --trigger K [--rule N]\n"
        "                                 dynamic rule-match diagnostics\n";
}

}  // namespace

int main(int argc, char *argv[]) {
    setlocale(LC_ALL, "");
    // Keep %lf/%g byte-exact ("0.25" never "0,25"): fractional rule
    // weights are a file-format contract, not a locale preference.
    setlocale(LC_NUMERIC, "C");
    if (argc < 2) { usage(); return 2; }
    std::string sub = argv[1];
    if (sub == "explain") return cmd_explain(argc - 2, argv + 2);
    if (sub == "why")     return cmd_why(argc - 2, argv + 2);
    if (sub == "-h" || sub == "--help") { usage(); return 0; }
    std::cerr << "unknown subcommand: " << sub << "\n";
    usage();
    return 2;
}
