#pragma once

#include "grammar.h"
#include "display_headless.h"
#include <string>
#include <unordered_set>

namespace zg {

struct HeadlessOptions {
    std::string config_path;
    std::string input_arg;     // literal STR | @PATH | @-
    std::string trace_path;    // "" = no trace
    std::string stats_path;    // "" = no stats
    std::string dump_path;     // "" = no dump; "-" / "-.ansi" / "-.txt" / file
    int seed = 0;
    int rows = 24;
    int cols = 80;
    uint64_t max_steps = 0;
    std::unordered_set<std::pair<int,int>, hash_pair> watch_cells;
};

bool prepare_input_string(const std::string& arg, std::string& out);

void dump_screen_by_ext(const HeadlessDisplay& d, const std::string& path);

int run_headless_input(const HeadlessOptions& opts);

}
