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

    Grammar2D cfg;
    cfg.param_overrides = opts.params;
    if (!cfg.loadFromFile(opts.config_path)) {
        std::cerr << "Cannot load program: " << opts.config_path << std::endl;
        return 1;
    }
    if (opts.threads > 0) {
        // Explicit --threads wins over the program's own #threads: a run
        // pinned to one worker is reproducible whatever the host's core
        // count, which is what the fixture tests rely on.
        cfg.thread_count = opts.threads;
    } else if (cfg.thread_count == 0) {
        cfg.thread_count = opts.trace_path.empty()
            ? std::thread::hardware_concurrency() : 1;
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
            std::fprintf(trace_fp, "# zahradnice-trace v2\n");
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

    w.reset(cfg, opts.rows, opts.cols);
    w.init(true);
    w.start();
    w.log_program_load(opts.config_path, 0);

    int score = 0;
    Grammar2D::Rule dummy = {};
    std::vector<wchar_t> sounds_dummy;
    std::wstring last_lhsa;
    for (char c : input_str) {
        wchar_t trig = static_cast<wchar_t>(static_cast<unsigned char>(c));
        char src = cfg.timing_chars.count(trig) ? 't' : 'k';
        w.stepMultithreaded(trig, score, &dummy, &sounds_dummy, src);
        last_lhsa = dummy.lhsa;
        if (opts.max_steps > 0 && w.get_event_step() >= opts.max_steps) break;
    }
    uint64_t events = w.get_event_step();

    w.log_program_unload(opts.config_path, score);
    w.dump_stats_for_program(opts.config_path);
    w.log_program_exit(score);

    if (!opts.dump_path.empty()) {
        auto [par, tot] = w.getThreadingStats();
        int parallel_pct = tot > 0 ? (100 * par / tot) : -1;
        std::wstring line = format_status_line(cfg, score,
                                               static_cast<int>(events),
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
