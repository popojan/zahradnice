#pragma once

#include "grammar.h"
#include <string>

namespace zg {
    // Build the unified status line used by all dump paths (headless,
    // replay snapshots, headless replay final dump). Left side: the
    // program-defined `#!` template (cfg.help), with {score}/{steps}/
    // {moves}/{parallel}/{help} substituted. Right side: the last
    // applied rule's `lhsa`. Output is padded to `cols` so the lhsa
    // sits in the top-right corner — visually 1:1 with live curses.
    std::wstring format_status_line(const Grammar2D& cfg,
                                     int score, int steps, int moves,
                                     int parallel_pct,
                                     const std::wstring& lhsa,
                                     int cols);
}
