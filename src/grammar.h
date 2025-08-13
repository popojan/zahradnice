#pragma once

#include <unordered_map>
#include <unordered_set>
#include <string>
#include <fstream>
#include <functional>
#include <vector>
#include <algorithm>
#include <cstdint>
#include <cwchar>
#include <clocale>

struct hash_pair final {
    template<class TFirst, class TSecond>
    size_t operator()(const std::pair<TFirst, TSecond> &p) const noexcept {
        uintmax_t hash = std::hash<TFirst>{}(p.first);
        hash <<= sizeof(uintmax_t) * 4;
        hash ^= std::hash<TSecond>{}(p.second);
        return std::hash<uintmax_t>{}(hash);
    }
};

class Grammar2D {
public:
    // non terminals
    std::unordered_set<wchar_t> V;

    struct Start {
        char ul; //vertical placement
        char lr; //horizontal placement
        wchar_t s; //symbol
    };

    std::wstring help;

    std::vector<Start> S;

    // terminals
    // ... any ASCII char not in nonterminal

    // starting symbol
    struct Rule {
        wchar_t lhs;
        std::wstring lhsa;
        std::wstring rhs;
        int ro;
        int co;
        int rm;
        int cm;
        int rq;
        int cq;
        char fore;
        char back;
        int reward;
        wchar_t key;
        wchar_t ctx;
        wchar_t rep;
        wchar_t ctxrep;
        int weight;
        char zord;
        wchar_t sound;
        bool load;
        bool clear;
        bool pause;
    };

    typedef std::vector<Rule> Rules;
    std::unordered_set<wchar_t> sounds;

    std::unordered_map<wchar_t, Rules> R;
    std::unordered_map<wchar_t, std::wstring> dict;

    // Grid configuration for symbol alignment (default 1,1 = no constraints)
    int grid_width = 1;
    int grid_height = 1;

    Grammar2D() {
    }

    bool _process(const std::vector<std::wstring> &lhs, const std::wstring &rule);

    bool loadFromFile(const std::string &fname);

    std::pair<int, int> origin(wchar_t s, const std::wstring &rhs, wchar_t spec, int ord = 0);

    void addRule(const std::wstring &lhs, const std::wstring &rhs);

    // UTF-8 to wide character conversion helper
    static wchar_t utf8_to_wchar(const std::string& utf8_char);

    // String to wstring conversion helper
    static std::wstring string_to_wstring(const std::string& str);

    friend class Derivation;

private:
    char getColor(wchar_t val, char def);
};


class Derivation {
public:
    std::unordered_map<std::pair<int, int>, wchar_t, hash_pair> x;

    struct G {
        wchar_t c;
        char fore;
        char back;
        char zord;
    };

    G *memory;
    wchar_t *screen_chars;  // Redundant storage of displayed characters for fast context lookup

    Derivation();

    void reset(const Grammar2D &g, int row, int col);

    void init(bool clear);

    void initColors();

    ~Derivation();

    void start();

    bool step(wchar_t key, int &score, Grammar2D::Rule *dbgrule);

    void restart();

    inline int wrap_row(int r) const {
        // Keep row 0 for status line, wrap rows 1 to row-1
        // Use cached effective height
        return (r - 1 + effective_max_row) % effective_max_row + 1;
    }

    inline int wrap_col(int c) const {
        // Use cached effective column width
        return (c + effective_max_col) % effective_max_col;
    }

private:
    template<bool DryRun>
    bool apply_impl(int ro, int co, const Grammar2D::Rule &rule);

    bool dryapply(int ro, int co, const Grammar2D::Rule &rule) {
        return apply_impl<true>(ro, co, rule);
    }

    bool apply(int ro, int co, const Grammar2D::Rule &rule) {
        return apply_impl<false>(ro, co, rule);
    }

    int getColor(char fore, char back);

    Grammar2D g;
    int col, row;
    // Cached wrap calculation values
    bool clear_needed;
    int effective_max_row;
    int effective_max_col;
    std::unordered_map<std::pair<char, char>, int, hash_pair> colors;
};
