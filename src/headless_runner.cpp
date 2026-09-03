#include "headless_runner.h"
#include "status.h"

#include <cstdio>
#include <cstdlib>
#include <ctime>
#include <fstream>
#include <iostream>
#include <sstream>
#include <thread>
#include <unistd.h>

namespace zg {

bool prepare_input_string(const std::string& arg, std::string& out) {
    std::string raw;
    if (arg == "@-") {
        std::ostringstream ss;
        ss << std::cin.rdbuf();
        raw = ss.str();
    } else if (!arg.empty() && arg[0] == '@') {
        std::ifstream f(arg.substr(1));
        if (!f) {
            std::cerr << "Cannot open --input file: " << arg.substr(1) << std::endl;
            return false;
        }
        std::ostringstream ss;
        ss << f.rdbuf();
        raw = ss.str();
    } else {
        raw = arg;
    }
    out.clear();
    out.reserve(raw.size());
    for (char c : raw) {
        if (c == ' ' || c == '\t' || c == '\n' || c == '\r') continue;
        out.push_back(c == '~' ? ' ' : c);
    }
    return true;
}

void dump_screen_by_ext(const HeadlessDisplay& d, const std::string& path) {
    bool to_stdout = (path == "-" || path == "-.ansi" || path == "-.txt");
    bool ansi;
    if (path == "-.ansi")     ansi = true;
    else if (path == "-.txt") ansi = false;
    else if (path == "-")     ansi = isatty(STDOUT_FILENO);
    else                      ansi = (path.size() >= 5
                                      && path.compare(path.size() - 5, 5, ".ansi") == 0);
    std::string actual = to_stdout ? "-" : path;
    if (ansi) d.dump_ansi(actual);
    else      d.dump_text(actual);
}

int run_headless_input(const HeadlessOptions& opts) {
    std::string input_str;
    if (!prepare_input_string(opts.input_arg, input_str)) return 1;

    const std::string initial_config = opts.config_path;

    // Re-parsed on every entry rather than cached the way the curses front end
    // does it: a headless run enters a handful of programs, a Grammar2D holds
    // nothing that must survive between entries, and caching them measured 8
    // bytes of binary either way. The interactive cache is there for latency
    // this path does not have.
    auto load_program = [&](const std::string& path, Grammar2D& g) -> bool {
        // --param reaches the program named on the command line and no other,
        // so a menu's wrapper entries keep the values they set themselves.
        if (path == initial_config) g.param_overrides = opts.params;
        if (!g.loadFromFile(path)) return false;
        if (opts.threads > 0) {
            // Explicit --threads wins over the program's own #threads: a run
            // pinned to one worker is reproducible whatever the host's core
            // count, which is what the fixture tests rely on.
            g.thread_count = opts.threads;
        } else if (g.thread_count == 0) {
            g.thread_count = opts.trace_path.empty()
                ? std::thread::hardware_concurrency() : 1;
        }
        return true;
    };

    Grammar2D cfg;
    if (!load_program(initial_config, cfg)) {
        std::cerr << "Cannot load program: " << initial_config << std::endl;
        return 1;
    }

    int actual_seed = (opts.seed == 0) ? static_cast<int>(time(0)) : opts.seed;
    srand(actual_seed);
    srandom(actual_seed);
    Derivation::initializeGlobalThreadPool(cfg.thread_count);

    Derivation w;
    HeadlessDisplay disp;
    disp.resize(opts.rows, opts.cols);
    w.set_display(&disp);

    FILE* trace_fp = nullptr;
    if (!opts.trace_path.empty()) {
        trace_fp = std::fopen(opts.trace_path.c_str(), "w");
        if (trace_fp) {
            std::setvbuf(trace_fp, nullptr, _IOLBF, 0);
            w.set_trace_file(trace_fp);
            std::fprintf(trace_fp, "# zahradnice-trace v3\n");
            std::fprintf(trace_fp, "# seed=%d\n", actual_seed);
            std::fprintf(trace_fp, "# screen=%d,%d\n", opts.rows, opts.cols);
            // #threads is a dynamical parameter, not a performance knob: the
            // multi-rule gate changes which rules co-fire, and an experiment
            // measured the contact process's lambda_c moving with it. A trace
            // that does not carry it cannot be replayed.
            std::fprintf(trace_fp, "# threads=%d\n", cfg.thread_count);
            // Provenance: with parameters a run is no longer determined by the
            // top-level path alone. An analyzer re-parses the program to map
            // src_line -> rule, so it needs the resolved values and the exact
            // files that were spliced.
            for (const auto& [name, value] : cfg.params)
                std::fprintf(trace_fp, "# param %s=%s\n", name.c_str(), value.c_str());
            for (const auto& path : cfg.resolved_includes)
                std::fprintf(trace_fp, "# include %s\n", path.c_str());
        }
    }
    FILE* stats_fp = nullptr;
    if (!opts.stats_path.empty()) {
        stats_fp = std::fopen(opts.stats_path.c_str(), "w");
        if (stats_fp) {
            std::setvbuf(stats_fp, nullptr, _IOLBF, 0);
            w.set_stats_file(stats_fp);
        }
    }
    if (!opts.watch_cells.empty()) w.set_watch_cells(opts.watch_cells);

    // The program loop, mirroring the curses front end: a rule may switch
    // programs or fire a #control action, and both mean leaving the inner
    // event loop and reloading. Without this the actions were parsed, applied
    // and logged, and then silently dropped -- `q` did not quit and `x` did
    // not clear, which made every control key untestable.
    struct Frame { std::string path; wchar_t key; };
    std::vector<Frame> caller_stack;
    wchar_t pending_param = 0;      // key handed to the next start(), then spent
    bool clear_screen = true;       // the first load clears; a switch composes
    bool paused = false;
    int score = 0;
    size_t ip = 0;                  // event cursor, continuous across programs
    bool stopped = false;           // --max-steps reached

    std::string config = initial_config;
    std::string prev_config;
    std::wstring active_template;   // `#!` is global and outlives its program
    std::wstring help_text;         // `#help` is re-read on every load
    std::wstring last_lhsa;
    std::vector<wchar_t> sounds_dummy;

    while (config != "quit" && !stopped) {
        Grammar2D g;
        if (!load_program(config, g)) {
            std::cerr << "Cannot load program: " << config << std::endl;
            return 1;
        }

        if (!prev_config.empty()) {
            w.log_program_unload(prev_config, score);
            w.dump_stats_for_program(prev_config);
        }
        w.log_program_load(config, score);
        prev_config = config;

        if (!g.help.empty()) active_template = g.help;
        help_text = g.help_text;

        w.reset(g, opts.rows, opts.cols);
        w.init(clear_screen);
        clear_screen = false;
        w.start(pending_param);
        pending_param = 0;

        Grammar2D::Rule rule = {};
        rule.lhsa = last_lhsa;

        while (ip < input_str.size()) {
            wchar_t trig = static_cast<wchar_t>(
                static_cast<unsigned char>(input_str[ip++]));
            char src = g.timing_chars.count(trig) ? 't' : 'k';
            // Paused, the curses loop blocks on the keyboard, so timing events
            // simply never happen; a keypress still gets through, which is how
            // anything ever unpauses. Same rule here.
            if (paused && src == 't') continue;

            // Cleared per event: on a step that applies nothing these still
            // hold the last applied rule, and would fire its action again.
            rule.sound = 0;
            rule.load = false;
            rule.engine_action = false;
            bool applied = w.stepMultithreaded(trig, score, &rule, &sounds_dummy, src);
            if (applied) last_lhsa = rule.lhsa;
            if (!applied) {
                if (opts.max_steps > 0 && w.get_event_step() >= opts.max_steps) {
                    stopped = true;
                    break;
                }
                continue;
            }

            if (rule.load && rule.sound != 0) {
                auto it = g.program_paths.find(rule.sound);
                if (it != g.program_paths.end()) {
                    caller_stack.push_back({config, rule.sound});
                    config = zg::resolve_program_path(it->second, config);
                    break;
                }
            } else if (rule.engine_action && rule.sound != 0) {
                const std::string action = g.getEngineAction(rule.sound);
                if (action == "pause") {
                    paused = !paused;
                } else if (action == "clear") {
                    // Counted as an unload/load pair so per-program stats reset
                    // exactly as they do interactively.
                    w.log_program_unload(config, score);
                    w.dump_stats_for_program(config);
                    w.log_program_load(config, score);
                    w.init(true);
                    w.reset(g, opts.rows, opts.cols);
                    w.start();
                } else if (action == "reset") {
                    if (!caller_stack.empty()) {
                        config = caller_stack[0].path;
                        caller_stack.clear();
                        break;
                    }
                } else if (action == "return") {
                    if (!caller_stack.empty()) {
                        config = caller_stack.back().path;
                        pending_param = caller_stack.back().key;
                        caller_stack.pop_back();
                    } else {
                        config = "quit";   // nothing to return to
                    }
                    break;
                } else if (action == "quit") {
                    config = "quit";
                    break;
                }
            }

            if (opts.max_steps > 0 && w.get_event_step() >= opts.max_steps) {
                stopped = true;
                break;
            }
        }
        if (ip >= input_str.size()) break;   // input exhausted
    }
    uint64_t events = w.get_event_step();

    if (!prev_config.empty()) {
        w.log_program_unload(prev_config, score);
        w.dump_stats_for_program(prev_config);
    }
    w.log_program_exit(score);

    if (!opts.dump_path.empty()) {
        auto [par, tot] = w.getThreadingStats();
        int parallel_pct = tot > 0 ? (100 * par / tot) : -1;
        std::wstring line = format_status_line(active_template, help_text, score,
                                               static_cast<int>(events),
                                               static_cast<int>(w.get_batch_step()),
                                               0, parallel_pct, last_lhsa, opts.cols);
        disp.set_status(line);
        dump_screen_by_ext(disp, opts.dump_path);
    }

    if (trace_fp) std::fclose(trace_fp);
    if (stats_fp) std::fclose(stats_fp);
    std::cerr << "Headless run: " << events
              << " events, final score=" << score << std::endl;
    return 0;
}

}
