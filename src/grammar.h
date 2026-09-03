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
#include <set>
#include <map>
#include <cstdio>

#include "display.h"

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
        // Trailing `?`: the caller supplies this symbol. On a `return` the
        // engine plants the key of the #program entry that launched the
        // child instead of `s`; `s` is the default for every other entry.
        bool param = false;
    };

    std::wstring help;          // Status line template (from #!)
    std::wstring help_text;     // Help content (from #help)

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
        double weight;
        wchar_t sound;
        bool load;
        bool engine_action;
        int source_line = 0;
        // First LHS cell that pins an exact character, as an offset from
        // the anchor. Checking it costs one array read and rejects most
        // rules before the dry run. probe_ch == 0 means the rule pins
        // nothing (bare `@@@` body, or every cell is `!` / `%` / any-ctx)
        // and must always be tried.
        wchar_t probe_ch = 0;
        int probe_dr = 0;
        int probe_dc = 0;
    };

    typedef std::vector<Rule> Rules;
    std::unordered_set<wchar_t> sounds;

    std::unordered_map<wchar_t, Rules> R;
    std::unordered_map<wchar_t, std::wstring> dict;
    
    // Engine actions (parsed from #control directives, for rule-based actions only)
    std::unordered_map<wchar_t, std::string> engine_actions;

    // Grid configuration for symbol alignment (default 1,1 = no constraints)
    int grid_width = 1;
    int grid_height = 1;

    // Timing configuration - map from character to interval (ms)
    std::unordered_map<wchar_t, int> timing_chars;

    // Transient characters: writes to memory.c are suppressed (overlay semantic).
    // Default = empty (every write updates memory.c, including non-terminals).
    // Programs that need moving-particle / transparent-overlay behaviour declare
    // these via the #transient directive.
    std::unordered_set<wchar_t> transient_chars;

    // Sound paths (parsed from dictionary)
    std::unordered_map<wchar_t, std::string> sound_paths;

    // Program paths (parsed from dictionary)
    std::unordered_map<wchar_t, std::string> program_paths;

    // Multithreading configuration
    int thread_count = 0;

    // Parameters. `#parameter NAME VALUE` declares a default; `{NAME}` in a
    // directive's arguments or in a rule header's score/weight tail is replaced
    // while the file is assembled. Substitution runs *during* include splicing,
    // so an `#include` path may itself be parameterized -- which is why a
    // parameter must be declared before the line that uses it, the same law
    // `#sound`, `#color`, `#program` and `#control` already obey.
    //
    // Deliberately not substituted: rule bodies and single-character header
    // fields (geometry is positional -- a variable-width value would shift
    // columns), the `#!` status template (its {steps}/{score} share the
    // syntax), and plain comments.
    std::map<std::string, std::string> params;           // resolved, in name order
    std::map<std::string, std::string> param_overrides;  // CLI/caller; win over the file
    std::vector<std::string> resolved_includes;          // provenance for the trace
    std::string load_error;                              // non-empty => load failed

    Grammar2D() {
        // No default dictionary entries needed - functions return same key/digit if not found
        // Auto-detect thread count (0 = use all cores, 1 = single-threaded)
        thread_count = 0;
    }

    bool _process(const std::vector<std::wstring> &lhs,
                  const std::vector<int> &lhs_lines,
                  const std::wstring &rule);

    bool loadFromFile(const std::string &fname);

private:
    // Recursive file loading with include support. Not const: it resolves
    // `#parameter` declarations and records the includes it actually spliced.
    std::string loadFileWithIncludes(const std::string &fname, std::set<std::string> &included_files);

    // Replace `{NAME}` in the permitted part of one assembled line. `from` is
    // the first column that may be substituted (10 for a rule header's
    // score/weight tail, 0 for a directive's arguments). Returns false and
    // fills load_error when a referenced parameter was never declared.
    bool substituteParams(std::string &line, size_t from,
                          const std::string &fname, int lineno);

    std::pair<int, int> origin(wchar_t s, const std::wstring &rhs, wchar_t spec, int ord = 0);

    void addRule(const std::wstring &lhs, const std::wstring &rhs, int source_line = 0);

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

    // Get engine action for a character (returns empty string if not found)
    std::string getEngineAction(wchar_t ch) const;

private:
    std::pair<char, int> getColorAndAttrs(wchar_t val, char def_color, int def_attrs = 0);
    char getColor(wchar_t val, char def);
};


struct RuleApplication {
    std::pair<int, int> position;
    Grammar2D::Rule rule;
    size_t rule_index;
    double weight;
};

// Per-cell match outcome reported during an "explain mode" dry-run
// (apply_impl<true> with a non-null probe sink). One probe per LHS-
// region body cell evaluated, in body order.
struct CellProbe {
    int body_r, body_c;       // body coords (0-indexed within rule.rhs)
    int screen_r, screen_c;   // wrapped screen coords
    wchar_t body_ch;          // raw body char ('@', '&', '!', '%', or literal)
    wchar_t expected;         // resolved required char (anchor/ctx expanded)
    wchar_t actual;           // screen_chars[screen_r * col + screen_c], '~' if SPACE
    bool matched;
};

// Sink invoked once per probed cell. Engine ignores when null
// (default behaviour: early-exit on first mismatch).
using ProbeSink = void (*)(const CellProbe&, void*);

struct ScreenArea {
    int min_row, max_row, min_col, max_col;

    bool overlaps(const ScreenArea& other) const {
        return !(max_row < other.min_row || min_row > other.max_row ||
                 max_col < other.min_col || min_col > other.max_col);
    }
};

struct RuleStats {
    uint32_t considered = 0;
    uint32_t applicable_locs = 0;
    uint32_t applied = 0;
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

    // param_key: the #program key of the entry that launched the program we
    // are returning from, or 0. It replaces the symbol of any `^…?` start.
    void start(wchar_t param_key = 0);

    bool step(wchar_t key, int &score, Grammar2D::Rule *dbgrule, char src = 0);

    ScreenArea calculateRuleArea(int ro, int co, const Grammar2D::Rule &rule);

    std::vector<RuleApplication> gatherApplicableRules(wchar_t key);

    // Anchor characters a trigger key can rewrite. Depends only on the
    // grammar, so it is computed once per key instead of by walking every
    // rule on every step.
    const std::unordered_set<wchar_t>& anchors_for(wchar_t key);

    // Rules for one (anchor, trigger) pair, indexed by the character their
    // probe cell pins. Most rule sets pin the same cell throughout, so one
    // screen read picks the handful of rules that can possibly match instead
    // of walking the whole family. Rules that pin a different cell -- or pin
    // nothing at all, e.g. a bare `@@@` body -- sit in `others` and are always
    // tried. Both lists are ascending, so merging them reproduces the plain
    // scan order exactly.
    struct RuleIndex {
        int dr = 0, dc = 0;
        std::unordered_map<wchar_t, std::vector<uint32_t>> by_char;
        std::vector<uint32_t> others;
        bool has_probe = false;
    };
    const RuleIndex& rules_for(wchar_t anchor, wchar_t key);
    const std::vector<uint32_t>* candidates(wchar_t anchor, wchar_t key,
                                           int pr, int pc);

    bool stepMultithreaded(wchar_t key, int &score, Grammar2D::Rule *dbgrule,
                           std::vector<wchar_t> *sounds = nullptr, char src = 0);

    // Instrumentation — only active when files are set; zero cost when off.
    void set_trace_file(FILE* fp) { trace_fp = fp; }
    void set_stats_file(FILE* fp) { stats_fp = fp; }
    // Watched cells: every write to (r,c) in this set emits a `cellwrite`
    // trace event (requires trace_fp). Empty = no per-cell tracing (default).
    void set_watch_cells(const std::unordered_set<std::pair<int,int>, hash_pair>& cells) {
        watch_cells = cells;
    }
    void log_program_load(const std::string &path, int score);
    void log_program_unload(const std::string &path, int score);
    void log_program_exit(int score);
    void dump_stats_for_program(const std::string &path);
    // Dump memory[r,c] (char + colour + attrs) for non-default cells only.
    // One line per cell: `r c char fore back fore_attrs back_attrs`.
    // Header comment carries the step for the snapshot.
    void dump_memory(FILE *fp, uint64_t step) const;
    uint64_t get_event_step() const { return event_step; }
    // Trajectory replay: force-execute a previously-recorded apply.
    bool apply_recorded(wchar_t lhs, size_t idx, int ro, int co);
    // Set the output backend. nullptr = no rendering (engine state still
    // lives in screen_chars[] + memory[], so headless dumps work).
    void set_display(Display* d) { display_ = d; }

    // Render offset: shift all engine drawing by (dr, dc) on the host terminal.
    // Engine coords (rows/cols passed to reset()) stay 0-indexed internally.
    // Forwarded to the display backend; engine itself only stores for callers.
    void set_render_offset(int dr, int dc);
    int get_offset_row() const { return offset_row; }
    int get_offset_col() const { return offset_col; }
    int get_viewport_rows() const { return row; }
    int get_viewport_cols() const { return col; }

    std::pair<int, int> getThreadingStats();

    static void initializeGlobalThreadPool(int max_threads = 0);

    void restart();

    inline int wrap_row(int r) const {
        // Keep row 0 for status line, wrap rows 1 to row-1.
        // The in-range test is not an optimisation of the formula but of the
        // division: rule matching calls this millions of times and almost
        // every call is already inside the viewport.
        if (r >= 1 && r <= effective_max_row) return r;
        return (r - 1 + effective_max_row) % effective_max_row + 1;
    }

    inline int wrap_col(int c) const {
        if (c >= 0 && c < effective_max_col) return c;
        return (c + effective_max_col) % effective_max_col;
    }

public:
    // Explain-mode dry run: same as apply_impl<true> but does not
    // short-circuit on first mismatch. Reports every probed LHS cell
    // to `sink` (called with `ctx` as its second arg). Returns true
    // iff every cell matched. Hot path is unaffected — engine call
    // sites continue to use apply_impl<true> with the default sink
    // (nullptr) and early-exit on first miss.
    bool dry_run_explain(int ro, int co, const Grammar2D::Rule &rule,
                         ProbeSink sink, void* ctx);

private:
    template<bool DryRun>
    bool apply_impl(int ro, int co, const Grammar2D::Rule &rule,
                    ProbeSink probe_sink = nullptr,
                    void* probe_ctx = nullptr);


    int getColor(char fore, char back);

    Grammar2D g;
    std::unordered_map<wchar_t, std::unordered_set<wchar_t>> anchor_cache;
    std::unordered_map<uint64_t, RuleIndex> rule_index;
    std::vector<uint32_t> cand_;   // scratch, reused per position
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

    // Instrumentation state
    FILE* trace_fp = nullptr;
    FILE* stats_fp = nullptr;
    std::unordered_map<uint64_t, RuleStats> stats;
    // Two counters, deliberately different. `event_step` counts applied
    // *rules*: for a confluent program the total is the same however many
    // threads ran it, which is what makes it a comparable measure. It cannot
    // therefore delimit a multi-rule step, so `apply_step` counts *steps* --
    // one per trigger event that applied anything, whatever the batch size.
    // Consecutive trace lines sharing an apply_step are one batch, which is
    // what lets replay feed the trigger once and expect N rules.
    uint64_t event_step = 0;
    uint64_t apply_step = 0;

    inline uint64_t stats_key(wchar_t lhs, size_t idx) const {
        return (static_cast<uint64_t>(static_cast<uint32_t>(lhs)) << 32) | static_cast<uint32_t>(idx);
    }
    void log_apply(int score, char src, wchar_t trig, wchar_t lhs, size_t idx, int ro, int co);
    // Emit `cellwrite` event for a watched (r,c). Called from apply_impl<false>
    // immediately after the screen + memory write completes (under screen_mutex).
    void log_cellwrite(uint64_t step, int r, int c,
                       wchar_t old_char, wchar_t new_char,
                       bool is_transient,
                       wchar_t memc_old, wchar_t memc_new,
                       const wchar_t *head);
    std::unordered_set<std::pair<int,int>, hash_pair> watch_cells;

    int offset_row = 0;
    int offset_col = 0;

    Display* display_ = nullptr;
};
