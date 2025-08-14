#include "grammar.h"
#include <ncursesw/ncurses.h>
#include <cwchar>
#include <cstring>
#include <sys/stat.h>
#include <zlib.h>
#include <fstream>
#include <algorithm>

static std::string decompress_gzip_file(const std::string& filename) {
    gzFile file = gzopen(filename.c_str(), "rb");
    if (!file) return "";

    std::string result;
    char buffer[4096];
    int bytes_read;

    while ((bytes_read = gzread(file, buffer, sizeof(buffer))) > 0) {
        result.append(buffer, bytes_read);
    }

    gzclose(file);
    return result;
}

bool Grammar2D::_process(const std::vector<std::wstring> &lhs, const std::wstring &rule) {
    for (const auto &x : lhs) {
        addRule(x, rule);
    }
    return true;
}

bool Grammar2D::loadFromFile(const std::string &fname) {
    struct stat buffer;
    std::string filename = fname;

    // Try original filename first (only if it's a regular file)
    if (stat(filename.c_str(), &buffer) == 0 && S_ISREG(buffer.st_mode)) {
        // File exists as-is
    }
    // If not .cfg, try adding /index.cfg
    else if (!fname.ends_with(".cfg") && !fname.ends_with(".cfg.gz")) {
        filename = fname + "/index.cfg";
        if (stat(filename.c_str(), &buffer) != 0) {
            filename += ".gz";
            if (stat(filename.c_str(), &buffer) != 0) {
                return false;
            }
        }
    }
    // Try adding .gz to original filename
    else {
        filename = fname + ".gz";
        if (stat(filename.c_str(), &buffer) != 0) {
            return false;
        }
    }

    std::string content;
    if (filename.ends_with(".gz")) {
        content = decompress_gzip_file(filename);
        if (content.empty()) return false;
    } else {
        std::ifstream file(filename);
        if (!file.is_open()) return false;
        content.assign(std::istreambuf_iterator<char>(file), std::istreambuf_iterator<char>());
    }

    std::vector<std::wstring> lhs;
    std::wstring rule;

    bool first = true;
    size_t start = 0;
    while (start < content.length()) {
        size_t end = content.find('\n', start);
        if (end == std::string::npos) end = content.length();
        std::string line_utf8 = content.substr(start, end - start);
        start = end + 1;
        std::wstring line = string_to_wstring(line_utf8);
        if (!line.empty() && line[0] == '#') //comment
        {
            if (line.size() > 1) {
                if (first && line[1] == L'!') {
                    help = line.substr(2);
                } else if (line[1] == L'=') {
                    if (line.size() > 2 && line[2] == L'=' && line.size() > 3) {
                        // Parse grid configuration: #=G width height
                        int vals[2] = {1, 1};
                        parse_ints<2>(line.substr(3), vals);
                        grid_width = vals[0] > 0 ? vals[0] : 1;
                        grid_height = vals[1] > 0 ? vals[1] : 1;
                    } else {
                        // Dictionary entry: #=<key><value>
                        if (line.length() > 2) {
                            wchar_t key = line[2];
                            std::wstring value = line.substr(3);
                            dict.insert({key, value});
                        }
                    }
                }
            }
            first = false;
            continue;
        }
        if (!line.empty() && line[0] == L'^') //starting symbol
        {
            wchar_t s = line.length() > 1 ? line[1] : L's';

            // Position indicators are still ASCII, so we can convert back
            char ul = line.length() > 2 ? static_cast<char>(line[2]) : 'c';
            char lr = line.length() > 3 ? static_cast<char>(line[3]) : 'c';
            S.push_back({ul, lr, s});
        }
        if (!line.empty() && line[0] == L'=') //new rule LHSs
        {
            if (!rule.empty() && _process(lhs, rule)) {
                rule.clear();
                lhs.clear();
            }
            lhs.push_back(line);
        } else if (!lhs.empty()) {
            if (!rule.empty()) rule += L'\n';
            rule += line;
        }

        first = false;
    }
    if (!rule.empty()) {
        _process(lhs, rule);
    }
    if (S.empty()) {
        S.push_back({'c', 'c', L's'});
    }
    return true;
}

std::pair<int, int> Grammar2D::origin(wchar_t s, const std::wstring &rhs, wchar_t spec, int ord) {
    int r = 0;
    int c = 0;

    for (const wchar_t *p = rhs.c_str(); *p != L'\0'; ++p, ++c) {
        if (*p == L'\n') {
            ++r;
            c = -1;
        } else if (*p == spec) {
            if (ord == 0) {
                return std::pair<int, int>(r, c);
            }
            --ord;
        }
    }
    return std::pair<int, int>(-1, -1);
}

char Grammar2D::getColor(wchar_t c, const char def) {
    char val = -1;

    // First try if it's a direct digit character
    if (c >= L'0' && c <= L'9') {
        val = static_cast<char>(c - L'0');
    } else {
        // Look up in dictionary for wide character keys
        auto it = dict.find(c);
        if (it != dict.end()) {
            if (!it->second.empty()) {
                wchar_t first_char = it->second[0];
                if (first_char >= L'0' && first_char <= L'9') {
                    val = static_cast<char>(first_char - L'0');
                }
            }
        }
    }
    return val >= 0 && val <= 9 ? val : def;
}

wchar_t Grammar2D::utf8_to_wchar(const std::string& utf8_char) {
    if (utf8_char.empty()) return L' ';

    wchar_t wc;
    std::mbstate_t state = {};
    size_t len = std::mbrtowc(&wc, utf8_char.c_str(), utf8_char.length(), &state);

    // Return the wide character if conversion succeeds, otherwise return ASCII equivalent or '?'
    if (len > 0 && len != static_cast<size_t>(-1) && len != static_cast<size_t>(-2)) {
        return wc;
    } else if (utf8_char.length() == 1) {
        // ASCII character - direct conversion
        return static_cast<wchar_t>(utf8_char[0]);
    }
    return L'?';
}

std::wstring Grammar2D::string_to_wstring(const std::string& str) {
    if (str.empty()) return L"";

    // Get required buffer size
    size_t len = std::mbstowcs(nullptr, str.c_str(), 0);
    if (len == static_cast<size_t>(-1)) {
        // Conversion failed, fallback to simple ASCII conversion
        std::wstring result;
        for (char c : str) {
            result += static_cast<wchar_t>(c);
        }
        return result;
    }

    // Convert UTF-8 to wide string
    std::wstring result(len, L'\0');
    std::mbstowcs(&result[0], str.c_str(), len);
    return result;
}

void Grammar2D::addRule(const std::wstring &lhs, const std::wstring &rhs) {
    wchar_t s = lhs.length() > 2 ? lhs[2] : L's';
    if (R.find(s) == R.end()) {
        R[s] = Rules();
        V.insert(s);
    }
    Rule rule;
    rule.load = false;
    rule.sound = 0;
    if (lhs.length() > 1 && lhs[1] != L'=') {
        wchar_t c = lhs[1];
        if (std::wstring(L">])|").find(c) == std::wstring::npos) {
            sounds.insert(c);
            rule.sound = c;
        } else {
            rule.sound = 0;
            rule.load = true;
            rule.clear = c == L')' || c == L'|';
            rule.pause = c == L']' || c == L'|';
        }
    }
    auto o = origin(s, rhs, L'@', 0);
    auto m = origin(s, rhs, L'@', 1);
    auto q = origin(s, rhs, L'@', 2);
    rule.lhsa = lhs;
    rule.lhs = s;
    rule.ro = o.first;
    rule.co = o.second;
    rule.rm = m.first;
    rule.cm = m.second;
    rule.rq = q.first;
    rule.cq = q.second;
    rule.rhs = rhs;
    char fore = 7; //default: white foreground
    char back = 8; //default: transparent background
    if (lhs.size() > 5) {
        fore = getColor(lhs[5], fore);
    }
    if (lhs.size() > 6) {
        back = getColor(lhs[6], back);
    }
    rule.fore = fore;
    rule.back = back;
    int reward = 0; //default reward
    int weight = 1;
    rule.key = lhs.length() > 3 ? lhs[3] : L'?';
    if (lhs.size() > 11) {
        int vals[2] = {0, 1};
        parse_ints<2>(lhs.substr(11), vals);
        reward = vals[0];
        weight = vals[1];
        if (weight < 1) weight = 1;
    }
    rule.reward = reward;
    rule.weight = weight;
    if (lhs.length() > 7)
        rule.ctx = lhs[7];
    else
        rule.ctx = static_cast<wchar_t>(-1);
    if (rule.ctx == L'?')
        rule.ctx = static_cast<wchar_t>(-1);

    if (lhs.length() > 8) {
        rule.ctxrep = lhs[8];
    } else
        rule.ctxrep = L' ';

    if (lhs.size() > 9)
        rule.zord = lhs[9];
    else
        rule.zord = L'a';

    if (rule.ctxrep == L'*') {
        rule.ctxrep = rule.lhs;
    }
    rule.rep = lhs.length() > 4 ? lhs[4] : L' ';
    //std::replace(rule.rhs.begin(), rule.rhs.end(), L'@', rule.rep);
    std::replace(rule.rhs.begin(), rule.rhs.end(), L'*', rule.lhs);
    R[s].push_back(rule);
}

Derivation::Derivation(): memory(nullptr), screen_chars(nullptr), clear_needed(true) {
}

void Derivation::reset(const Grammar2D &g, int row, int col) {
    this->g = g;
    if (this->row != row || this->col != col) {
        clear_needed = true;
        this->row = row;
        this->col = col;
    } else {
        clear_needed = false;
    }
    // Cache wrap calculation values
    this->effective_max_row = ((row - 1) / g.grid_height) * g.grid_height;
    this->effective_max_col = (col / g.grid_width) * g.grid_width;
}

void Derivation::init(bool clear) {
    if (clear || clear_needed) {
        delete [] memory;
        delete [] screen_chars;
        memory = new(std::nothrow) G[row * col];
        screen_chars = new(std::nothrow) wchar_t[row * col];
        if (!memory || !screen_chars) std::exit(1);
        restart();
        initColors();
    }
}

void Derivation::initColors() {
    char cols[8] = {
        COLOR_BLACK,
        COLOR_RED,
        COLOR_GREEN,
        COLOR_YELLOW,
        COLOR_BLUE,
        COLOR_MAGENTA,
        COLOR_CYAN,
        COLOR_WHITE
    };

    int N = sizeof(cols) / sizeof(char);

    int colidx = 1;

    for (int i = 0; i < N; ++i) {
        for (int j = 0; j < N; ++j) {
            colors[{cols[i], cols[j]}] = colidx;
            init_pair(colidx, cols[i], cols[j]);
            ++colidx;
        }
    }
}

Derivation::~Derivation() {
    delete [] memory;
    delete [] screen_chars;
}

void Derivation::start() {
    for (const auto &s : g.S) {
        // Use grid-aligned effective dimensions consistent with wrap functions
        int effective_col = (col / g.grid_width) * g.grid_width;
        int effective_row = ((row - 1) / g.grid_height) * g.grid_height;
        int c = col / 2;
        int r = row / 2;
        if (s.lr == 'l') {
            c = 0;
        } else if (s.lr == 'r') {
            c = col - 1;
        } else if (s.lr == 'c') {
            c = col / 2;
        } else if (s.lr == 'R') {
            c = effective_col - g.grid_width; // Right edge, grid-aligned
        } else if (s.lr == 'C') {
            c = g.grid_width * ((effective_col / g.grid_width) / 2); // Center, grid-aligned
        } else if (s.lr == 'X') {
            c = g.grid_width * ((rand() % (effective_col / g.grid_width))); // Random, grid-aligned
        } else {
            c = rand() % col;
        }
        if (s.ul == 'u') {
            r = 1;
        } else if (s.ul == 'l') {
            r = row - 1;
        } else if (s.ul == 'c') {
            r = row / 2;
        } else if (s.ul == 'L') {
            r = g.grid_height * (((row - 2) / g.grid_height)) + 1; // Lower row, grid-aligned
        } else if (s.ul == 'C') {
            r = g.grid_height * ((effective_row / g.grid_height) / 2); // Center row, grid-aligned
        } else if (s.ul == 'X') {
            r = g.grid_height * ((rand() % ((row - 1) / g.grid_height))) + 1; // Random row, grid-aligned
        } else {
            r = rand() % (row - 1) + 1;
        }
        x[{r, c}] = s.s;
        cchar_t cchar;
        wchar_t wch[2] = {s.s, 0};
        setcchar(&cchar, wch, 0, 0, NULL);
        mvadd_wch(r, c, &cchar);
        // Update redundant character storage
        screen_chars[r * col + c] = s.s;
    }
}

bool Derivation::step(wchar_t key, int &score, Grammar2D::Rule *dbgrule) {
    //random nonterminal instance

    //nonterminal alterable by rules from group key
    std::unordered_set<wchar_t> a;
    for (const auto &rr : g.R) {
        for (const auto &rrr : rr.second) {
            if (rrr.key == key || rrr.key == L'?') a.insert(rrr.lhs);
        }
    }
    //all nonterminal positions
    std::vector<std::pair<int, int> > xx;
    for (auto nit = x.begin(); nit != x.end(); ++nit) {
        if (a.find(nit->second) != a.end())
            xx.push_back(nit->first);
    }

    if (xx.size() <= 0)
        return false;
    struct abc {
        wchar_t a;
        std::vector<std::pair<int, int> >::difference_type b;
        std::vector<Grammar2D::Rule>::difference_type c;
    };
    std::vector<abc> nr;
    double sumw = 0.0;
    auto prob = -1.0;
    //find all applicable rules and their weights
    for (auto nit = xx.begin(); nit != xx.end(); ++nit) {
        auto &n = x[*nit];
        auto res = g.R.find(n);
        if (res != g.R.end()) {
            //random rule
            auto &rs = res->second;
            for (auto rit = rs.begin(); rit != rs.end(); ++rit) {
                if (rit->key == key || rit->key == L'?') {
                    bool app = apply_impl<true>(nit->first - rit->ro, nit->second - rit->co, *rit);
                    if (app) {
                        sumw += rit->weight;
                        nr.push_back({n, nit - xx.begin(), rit - rs.begin()});
                    }
                }
            }
        }
    }
    //select a random applicable rule
    prob = static_cast<double>(random()) / RAND_MAX * sumw;
    sumw = 0.0;
    for (auto nit = nr.begin(); nit != nr.end(); ++nit) {
        auto &rule = g.R.find(nit->a)->second[nit->c];
        sumw += rule.weight;
        if (sumw >= prob) {
            auto &rc = xx[nit->b];
            bool applied = rule.load || apply_impl<false>(rc.first - rule.rq, rc.second - rule.cq, rule);
            if (applied) {
                *dbgrule = rule;
                score += rule.reward;
                return true;
            }
        }
    }
    return false;
}

void Derivation::restart() {
    x.clear();
    clear();
    for (int r = 0; r < row; ++r) {
        for (int c = 0; c < col; ++c) {
            memory[r * col + c] = {L' ', 7, 0, L'a'};
            screen_chars[r * col + c] = L' ';
        }
    }
}

template<bool DryRun>
bool Derivation::apply_impl(int ro, int co, const Grammar2D::Rule &rule) {
    int r = ro;
    int c = co;

    bool horiz = rule.cq > rule.co;
    const size_t rhs_length = rule.rhs.length();

    for (size_t i = 0; i < rhs_length; ++i, ++c) {
        wchar_t ch = rule.rhs[i];
        if (ch == L'\n') {
            ++r;
            c = co - 1;
            continue;
        }
        if (ch == L' ')
            continue;

        if constexpr (DryRun) {
            if (horiz) {
                if (c - co >= rule.cm) // @ LHS @ >>RHS<<
                    continue;
            } else {
                if (r - ro >= rule.rm)
                    break;
            }
        } else {
            if (rule.cq > rule.co && c - co <= rule.cm) // @ LHS @ >>RHS<<
                continue;
            if (rule.cq <= rule.co && r - ro <= rule.rm)
                continue;
        }

        // Wrap coordinates cyclically for toroidal screen
        int wrapped_r = wrap_row(r);
        int wrapped_c = wrap_col(c);

        if constexpr (DryRun) {
            wchar_t req = ch;
            wchar_t ctx = screen_chars[wrapped_r * col + wrapped_c];
            if (ctx == L' ') ctx = L'~';
            if (req == L'@') req = rule.lhs;
            if (ch == L'&') req = rule.ctx;
            if (req == L' ') req = L'~';
            if ((req != L'!' && req != L'%' && req != ctx)
                || (req == L'!' && ctx == rule.ctx)
                || (ch == L'%' && ctx != rule.ctxrep && ctx != rule.ctx)) {
                return false;
            }
        } else {
            G saved = {L' ', 7, 8, 'a'};
            wchar_t rep = ch;
            if (rep == L'@') rep = rule.rep;
            if (rep == L'&') rep = rule.ctxrep;
            bool isNonTerminal = g.V.find(rep) != g.V.end();
            if (rep != L' ') {
                if (rep == L'~') rep = L' ';
                char back = rule.back;
                if (rule.back > 7) {
                    back = memory[col * wrapped_r + wrapped_c].back;
                }
                G d = {rep, rule.fore, back, rule.zord};
                if (rep == L'$') d = memory[col * wrapped_r + wrapped_c];
                if (d.c == -1) d = {L' ', rule.fore, back, 'a'};
                int cidx = getColor(d.fore, d.back);
                if (rule.zord >= memory[col * wrapped_r + wrapped_c].zord) {
                    if (cidx > 0) attron(COLOR_PAIR(cidx));
                    cchar_t cchar;
                    wchar_t wch[2] = {d.c, 0};
                    setcchar(&cchar, wch, 0, cidx, NULL);
                    mvadd_wch(wrapped_r, wrapped_c, &cchar);
                    screen_chars[wrapped_r * col + wrapped_c] = d.c;
                    if (!isNonTerminal) {
                        saved = d;
                    } else {
                        saved = memory[col * wrapped_r + wrapped_c];
                        saved.back = d.back;
                    }
                    if (cidx > 0) attroff(COLOR_PAIR(cidx));
                    memory[col * wrapped_r + wrapped_c] = saved;
                }
                auto loc = std::pair{wrapped_r, wrapped_c};
                if (isNonTerminal) {
                    x[loc] = rep;
                } else {
                    x.erase(loc);
                }
            }
        }
    }
    return true;
}

int Derivation::getColor(char fore, char back) {
    auto cit = colors.find({fore, back});
    if (cit != colors.end())
        return cit->second;
    return -1;
}
