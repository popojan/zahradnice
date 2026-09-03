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
    // The template every program falls back to when it declares no `#!`.
    extern const wchar_t* const kDefaultStatusTemplate;

    // Substitute the `{...}` variables of a status template. Split out because
    // there are two callers with genuinely different template *sources* -- the
    // replay/headless path takes it from the loaded Grammar2D, the interactive
    // loop from the inherited `active_statusline_template` (a program with no
    // `#!` of its own keeps its caller's caption). Only the substitution is
    // common, and duplicating it meant a new variable had to be added twice.
    // `steps` is applied rules (what {steps} has always meant); `batches` is
    // steps proper -- one per trigger event that applied anything.
    std::wstring substitute_status_vars(std::wstring tmpl,
                                        int score, int steps, int batches, int moves,
                                        int parallel_pct,
                                        const std::wstring& help_text);

    std::wstring format_status_line(const Grammar2D& cfg,
                                     int score, int steps, int batches, int moves,
                                     int parallel_pct,
                                     const std::wstring& lhsa,
                                     int cols);
}
