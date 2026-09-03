// Curses-free zahradnice driver. Links libgrammar.a only — no ncurses,
// no SDL. Validates the architectural seam (libgrammar carries no
// terminal dependency); not built into the default release.

#include "headless_runner.h"
#include <clocale>
#include <iostream>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>
#include <unistd.h>

int main(int argc, char* argv[]) {
    setlocale(LC_ALL, "");
    // Keep %lf/%g byte-exact ("0.25" never "0,25"): fractional rule
    // weights are a file-format contract, not a locale preference.
    setlocale(LC_NUMERIC, "C");

    zg::HeadlessOptions opts;
    opts.rows = 24;
    opts.cols = 80;

    auto need = [&](int i) -> bool {
        if (i + 1 >= argc) {
            std::cerr << "missing value for " << argv[i] << "\n";
            return false;
        }
        return true;
    };

    bool seen_pos = false;
    for (int i = 1; i < argc; ++i) {
        std::string a = argv[i];
        if (a == "-h" || a == "--help") {
            std::cout <<
                "Usage: zahradnice-headless PROGRAM [options]\n"
                "  --input STR | @PATH | @-  trigger sequence (one byte/event; ~=SPACE)\n"
                "                            default: read stdin if not a TTY\n"
                "  --seed N                  RNG seed\n"
                "  --screen R,C              viewport (default 24,80)\n"
                "  --max-steps N             stop after N applied rules\n"
                "  --threads N               worker threads; 1 makes a run\n"
                "                            reproducible across machines\n"
                "  --dump-screen PATH        write final screen (default `-` = stdout)\n"
                "                            `-.ansi`/`-.txt` force stdout format\n"
                "  --trace PATH              write event trace\n"
                "  --stats PATH              write per-rule stats summary\n"
                "  --param NAME=VALUE        override a #parameter (repeatable)\n";
            return 0;
        }
        else if (a == "--input")       { if (!need(i)) return 1; opts.input_arg = argv[++i]; }
        else if (a == "--seed")        { if (!need(i)) return 1; opts.seed = std::atoi(argv[++i]); }
        else if (a == "--max-steps")   { if (!need(i)) return 1; opts.max_steps = std::strtoull(argv[++i], nullptr, 10); }
        else if (a == "--threads")     { if (!need(i)) return 1; opts.threads = std::atoi(argv[++i]); }
        else if (a == "--dump-screen") { if (!need(i)) return 1; opts.dump_path = argv[++i]; }
        else if (a == "--trace")       { if (!need(i)) return 1; opts.trace_path = argv[++i]; }
        else if (a == "--stats")       { if (!need(i)) return 1; opts.stats_path = argv[++i]; }
        else if (a == "--param") {
            if (!need(i)) return 1;
            std::string kv = argv[++i];
            size_t eq = kv.find('=');
            if (eq == std::string::npos || eq == 0) {
                std::cerr << "--param expects NAME=VALUE\n";
                return 1;
            }
            opts.params[kv.substr(0, eq)] = kv.substr(eq + 1);
        }
        else if (a == "--screen") {
            if (!need(i)) return 1;
            if (std::sscanf(argv[++i], "%d,%d", &opts.rows, &opts.cols) != 2
                || opts.rows < 2 || opts.cols < 2) {
                std::cerr << "bad --screen value\n";
                return 1;
            }
        }
        else if (!a.empty() && a[0] == '-') { std::cerr << "unknown option: " << a << "\n"; return 1; }
        else if (!seen_pos) { opts.config_path = a; seen_pos = true; }
        else { std::cerr << "extra positional: " << a << "\n"; return 1; }
    }

    if (opts.config_path.empty()) {
        std::cerr << "missing program path\n";
        return 1;
    }
    if (opts.input_arg.empty() && !isatty(STDIN_FILENO)) opts.input_arg = "@-";
    if (opts.input_arg.empty()) {
        std::cerr << "no input source (pipe stdin or pass --input STR / @PATH)\n";
        return 1;
    }
    if (opts.dump_path.empty()) opts.dump_path = "-";

    return zg::run_headless_input(opts);
}
