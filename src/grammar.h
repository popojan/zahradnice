#pragma once

#include <unordered_map>
#include <unordered_set>
#include <string>
#include <vector>
#include <cstdint>
#include <thread>
#include <mutex>
#include <condition_variable>
#include <atomic>
#include <future>
#include <queue>
#include <functional>
#include <memory>

struct hash_pair final {
    template<class TFirst, class TSecond>
    size_t operator()(const std::pair<TFirst, TSecond> &p) const noexcept {
        uintmax_t hash = std::hash<TFirst>{}(p.first);
        hash <<= sizeof(uintmax_t) * 4;
        hash ^= std::hash<TSecond>{}(p.second);
        return std::hash<uintmax_t>{}(hash);
    }
};

class ThreadPool {
public:
    ThreadPool(size_t threads);
    ~ThreadPool();

    template<class F, class... Args>
    auto enqueue(F&& f, Args&&... args) -> std::future<typename std::result_of<F(Args...)>::type>;

private:
    std::vector<std::thread> workers;
    std::queue<std::function<void()>> tasks;
    std::mutex queue_mutex;
    std::condition_variable condition;
    bool stop;
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
        int fore_attrs;
        int back_attrs;
        int reward;
        wchar_t key;
        wchar_t ctx;
        wchar_t rep;
        wchar_t ctxrep;
        int weight;
        wchar_t sound;
        bool load;
    };

    typedef std::vector<Rule> Rules;
    std::unordered_set<wchar_t> sounds;

    std::unordered_map<wchar_t, Rules> R;
    std::unordered_map<wchar_t, std::wstring> dict;
    std::unordered_map<wchar_t, std::wstring> control_remaps;

    // Grid configuration for symbol alignment (default 1,1 = no constraints)
    int grid_width = 1;
    int grid_height = 1;

    // Timing configuration (default values)
    int B_step = 500;
    int M_step = 50;
    int T_step = 0;

    // Screen clearing flag (set by plain ^ starting symbol)
    bool clear_requested = false;

    // Sound paths (parsed from dictionary)
    std::unordered_map<wchar_t, std::string> sound_paths;

    // Program paths (parsed from dictionary)
    std::unordered_map<wchar_t, std::string> program_paths;

    // Multithreading configuration
    int thread_count = 0;

    Grammar2D() {
        // No default dictionary entries needed - functions return same key/digit if not found
        // Auto-detect thread count (0 = use all cores, 1 = single-threaded)
        thread_count = 0;
    }

    bool _process(const std::vector<std::wstring> &lhs, const std::wstring &rule);

    bool loadFromFile(const std::string &fname);

    std::pair<int, int> origin(wchar_t s, const std::wstring &rhs, wchar_t spec, int ord = 0);

    void addRule(const std::wstring &lhs, const std::wstring &rhs);

    // UTF-8 to wide character conversion helper
    static wchar_t utf8_to_wchar(const std::string& utf8_char);

    // String to wstring conversion helper
    static std::wstring string_to_wstring(const std::string& str);

private:
    // Parse up to N whitespace-delimited integers from wide string
    template<int N> static void parse_ints(const std::wstring& s, int* vals) {
        size_t pos = 0;
        for (int i = 0; i < N; ++i) {
            pos = s.find_first_not_of(L" \t", pos);
            if (pos == std::wstring::npos) break;
            vals[i] = std::wcstol(s.c_str() + pos, nullptr, 10);
            pos = s.find_first_of(L" \t", pos);
        }
    }

public:
    friend class Derivation;

    wchar_t getControlKey(wchar_t control) const;

private:
    std::pair<char, int> getColorAndAttrs(wchar_t val, char def_color, int def_attrs = 0);
    char getColor(wchar_t val, char def);
};


struct RuleApplication {
    std::pair<int, int> position;
    Grammar2D::Rule rule;
    size_t rule_index;
    int weight;
};

struct ScreenArea {
    int min_row, max_row, min_col, max_col;

    bool overlaps(const ScreenArea& other) const {
        return !(max_row < other.min_row || min_row > other.max_row ||
                 max_col < other.min_col || min_col > other.max_col);
    }
};

class Derivation {
public:
    std::unordered_map<std::pair<int, int>, wchar_t, hash_pair> x;

    struct G {
        wchar_t c;
        char fore;
        char back;
        int fore_attrs;
        int back_attrs;
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

    ScreenArea calculateRuleArea(int ro, int co, const Grammar2D::Rule &rule);

    std::vector<RuleApplication> gatherApplicableRules(wchar_t key);

    bool stepMultithreaded(wchar_t key, int &score, Grammar2D::Rule *dbgrule, std::vector<wchar_t> *sounds = nullptr);

    std::pair<int, int> getThreadingStats();

    static void initializeGlobalThreadPool(int max_threads = 0);

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


    int getColor(char fore, char back);

    Grammar2D g;
    int col, row;
    // Cached wrap calculation values
    bool clear_needed;
    int effective_max_row;
    int effective_max_col;
    std::unordered_map<std::pair<char, char>, int, hash_pair> colors;

    // Thread safety for screen operations
    static std::mutex screen_mutex;

    // Global thread pool for rule application (shared across all programs)
    static std::unique_ptr<ThreadPool> global_thread_pool;
};
