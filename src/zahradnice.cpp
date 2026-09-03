#include <ncursesw/ncurses.h>
#include <clocale>
#include <iostream>
#include "wide_io.h"
#include "grammar.h"
#include "display_curses.h"
#include "display_headless.h"
#include "headless_runner.h"
#include "status.h"
#include <thread>
#include <chrono>
#include <SDL2/SDL_mixer.h>
#include "sample.h"
#include <cstdlib>
#include <algorithm>
#include <unistd.h>
#include <libgen.h>
#include <sys/stat.h>
#include <unordered_map>
#include <memory>
#include <fstream>
#include <sstream>
#include <ctime>
#include <cstring>
#include <vector>
#include <set>

// Global state for statusline template inheritance
static std::wstring active_statusline_template = L"";
static std::wstring current_help_text = L"";

// Render statusline with template substitution. The template is the
// *inherited* one (a program with no `#!` keeps its caller's caption), which
// is the one thing this path does differently; the substitution is shared.
static std::wstring render_statusline(int score, int steps, int batches, int moves, int parallel_pct) {
    return zg::substitute_status_vars(
        active_statusline_template.empty()
            ? std::wstring(zg::kDefaultStatusTemplate)
            : active_statusline_template,
        score, steps, batches, moves, parallel_pct, current_help_text);
}

// Take a screenshot of the current terminal content to a text file.
// capture_colors: if true, output ANSI escape sequences for colors
// rect_top/left/rows/cols: clip to a rectangle; if rect_rows<=0 capture full terminal.
static bool take_screenshot(const std::string& filename, bool capture_colors = false,
                             int rect_top = 0, int rect_left = 0,
                             int rect_rows = -1, int rect_cols = -1) {
    int max_row, max_col;
    getmaxyx(stdscr, max_row, max_col);
    int top = (rect_rows > 0) ? rect_top : 0;
    int left = (rect_cols > 0) ? rect_left : 0;
    int height = (rect_rows > 0) ? std::min(rect_rows, max_row - top) : max_row;
    int width = (rect_cols > 0) ? std::min(rect_cols, max_col - left) : max_col;

    std::wofstream file(filename);
    if (!file.is_open()) {
        return false;
    }
    imbue_utf8(file);

    for (int r = top; r < top + height; ++r) {
        std::wstring line;
        for (int c = left; c < left + width; ++c) {
            cchar_t ch;
            if (mvin_wch(r, c, &ch) == OK) {
                // Extract the wide character(s) and attributes
                wchar_t wch[CCHARW_MAX + 1];
                attr_t attrs;
                short color_pair;
                if (getcchar(&ch, wch, &attrs, &color_pair, NULL) == OK) {
                    if (capture_colors && color_pair > 0) {
                        // Get the actual foreground and background colors from the pair
                        short fg, bg;
                        pair_content(color_pair, &fg, &bg);

                        // Generate ANSI escape sequence for colors
                        // Basic 8 colors: 30-37 (fg), 40-47 (bg)
                        // Bright colors: 90-97 (fg), 100-107 (bg)
                        std::wstring color_seq;

                        // Handle foreground color
                        if (fg < 8) {
                            color_seq += L"\033[3" + std::to_wstring(fg) + L"m";
                        } else if (fg < 16) {
                            color_seq += L"\033[9" + std::to_wstring(fg - 8) + L"m";
                        }

                        // Handle background color
                        if (bg < 8) {
                            color_seq += L"\033[4" + std::to_wstring(bg) + L"m";
                        } else if (bg < 16) {
                            color_seq += L"\033[10" + std::to_wstring(bg - 8) + L"m";
                        }

                        // Handle attributes (bold, underline, etc.)
                        if (attrs & A_BOLD) {
                            color_seq += L"\033[1m";
                        }
                        if (attrs & A_UNDERLINE) {
                            color_seq += L"\033[4m";
                        }
                        if (attrs & A_REVERSE) {
                            color_seq += L"\033[7m";
                        }

                        line += color_seq;
                    }

                    // Add the character
                    if (wch[0] != 0) {
                        line += wch[0];
                    } else {
                        line += L' ';
                    }

                    // Reset colors after each character if colors were applied
                    if (capture_colors && color_pair > 0) {
                        line += L"\033[0m";
                    }
                } else {
                    line += L' ';
                }
            } else {
                line += L' ';
            }
        }
        // Trim trailing spaces from the line (but preserve color codes)
        if (!capture_colors) {
            size_t end = line.find_last_not_of(L' ');
            if (end != std::wstring::npos) {
                line = line.substr(0, end + 1);
            }
        }
        file << line << L'\n';
    }

    file.close();
    return true;
}

std::string resolve_sound_path(const std::string& sound_path, const std::string& program_dir) {
    // If path is already absolute, use as-is
    if (!sound_path.empty() && sound_path[0] == '/') {
        return sound_path;
    }

    struct stat buffer;

    // Try relative to program file directory first
    std::string program_relative = program_dir + "/" + sound_path;
    if (stat(program_relative.c_str(), &buffer) == 0) {
        return program_relative;
    }

    // Fallback to current working directory
    return sound_path;
}

std::string resolve_program_path(const std::string& program_path, const std::string& current_config) {

    // If program path is already absolute, use as-is
    if (!program_path.empty() && program_path[0] == '/') {
        return program_path;
    }

    std::string base_path;

    // Get directory of current config
    size_t last_slash = current_config.find_last_of("/");
    if (last_slash != std::string::npos) {
        // Current config has directory, use that directory
        base_path = current_config.substr(0, last_slash) + "/" + program_path;
    } else {
        // Current config has no directory, use current working directory
        base_path = program_path;
    }

    // Apply file completion logic from loadFromFile
    struct stat buffer;

    // Try original path first
    if (stat(base_path.c_str(), &buffer) == 0 && S_ISREG(buffer.st_mode)) {
        return base_path;
    }

    // If not .cfg, try adding /index.cfg
    if (!base_path.ends_with(".cfg") && !base_path.ends_with(".cfg.gz")) {
        std::string index_path = base_path + "/index.cfg";
        if (stat(index_path.c_str(), &buffer) == 0) {
            return index_path;
        }
        // Try compressed index
        std::string index_gz_path = index_path + ".gz";
        if (stat(index_gz_path.c_str(), &buffer) == 0) {
            return index_gz_path;
        }
    }
    // Try adding .gz to original path
    else {
        std::string gz_path = base_path + ".gz";
        if (stat(gz_path.c_str(), &buffer) == 0) {
            return gz_path;
        }
    }

    // If nothing found, return original base_path (let loadFromFile handle the error)
    return base_path;
}

void clear_status(int row, int col, size_t len) {
    std::wstring empty(len, L' ');
    mvaddwstr(row, col, empty.c_str());
}

// How long the next wget_wch() may block, in curses timeout() units:
//   0  poll — an interval-0 timing char is armed, the program runs full tilt
//   n  wait up to n ms — that is when the next interval timing comes due
//  -1  wait for a key — no clock can wake us
// `quiet` means the last trigger applied nothing: rule applicability depends
// only on the screen state, so re-firing the same immediate trigger against
// an unchanged screen cannot succeed either. Only a key or an interval event
// can make rules applicable again, so we wait for one instead of spinning.
static int idle_timeout_ms(const Grammar2D &cfg,
                           const std::unordered_map<wchar_t, int> &elapsed_counts,
                           const std::chrono::steady_clock::time_point &start,
                           bool quiet) {
    bool immediate = false;
    double soonest = -1.0;  // ms until the next interval event, -1 = no clock
    std::chrono::duration<double, std::milli> since =
        std::chrono::steady_clock::now() - start;
    for (const auto &[timing_char, interval] : cfg.timing_chars) {
        if (interval == 0) { immediate = true; continue; }
        auto it = elapsed_counts.find(timing_char);
        int fired = (it == elapsed_counts.end()) ? 0 : it->second;
        double left = static_cast<double>(fired + 1) * interval - since.count();
        if (left < 0.0) left = 0.0;
        if (soonest < 0.0 || left < soonest) soonest = left;
    }
    if (immediate && !quiet) return 0;
    if (soonest < 0.0) return -1;
    return static_cast<int>(soonest) + 1;
}

// Clear the host-terminal area outside the centred viewport so stale terminal
// content doesn't bleed through. Called once after initscr() when a smaller
// --screen is requested.
static void clear_outside_viewport(int off_row, int off_col, int eff_row, int eff_col) {
    int actual_row, actual_col;
    getmaxyx(stdscr, actual_row, actual_col);
    if (off_row == 0 && off_col == 0
        && eff_row == actual_row && eff_col == actual_col) return;
    std::wstring blank(actual_col, L' ');
    for (int r = 0; r < actual_row; ++r) {
        if (r >= off_row && r < off_row + eff_row) {
            // partial: blank only the columns outside [off_col, off_col+eff_col)
            if (off_col > 0) {
                std::wstring left((size_t)off_col, L' ');
                mvaddwstr(r, 0, left.c_str());
            }
            int right_start = off_col + eff_col;
            if (right_start < actual_col) {
                std::wstring right((size_t)(actual_col - right_start), L' ');
                mvaddwstr(r, right_start, right.c_str());
            }
        } else {
            mvaddwstr(r, 0, blank.c_str());
        }
    }
}

// Input replay: read a previously-recorded trace and re-feed its triggers to
// the engine, letting normal rule selection decide what fires. Renders into
// a virtual viewport of the recorded screen size, requiring the host terminal
// to be at least that big. Detects divergence (different rule fired or score
// drift) automatically.
static int run_replay(const std::string &replay_path, int delay_ms,
                      const std::vector<uint64_t> &snapshot_steps,
                      const std::vector<uint64_t> &mem_snapshot_steps,
                      const std::unordered_set<std::pair<int,int>, hash_pair> &watch_cells,
                      const std::string &trace_out_path,
                      bool headless,
                      uint64_t max_steps,
                      const std::string &dump_screen_path,
                      const std::map<std::string, std::string> &param_overrides) {
    FILE *f = std::fopen(replay_path.c_str(), "r");
    if (!f) {
        std::cerr << "Cannot open replay file: " << replay_path << std::endl;
        return 1;
    }

    // Parse header: "# zahradnice-trace vN", "# seed=N", "# screen=R,C"
    int rec_seed = 1, rec_rows = 24, rec_cols = 80, trace_version = 0;
    int rec_threads = 1;
    char line[8192];
    long after_header = 0;
    while (std::fgets(line, sizeof(line), f)) {
        if (line[0] != '#') {
            std::fseek(f, after_header, SEEK_SET);
            break;
        }
        int v, r, c;
        if (std::sscanf(line, "# zahradnice-trace v%d", &v) == 1) trace_version = v;
        else if (std::sscanf(line, "# seed=%d", &v) == 1) rec_seed = v;
        else if (std::sscanf(line, "# threads=%d", &v) == 1) rec_threads = v;
        else if (std::sscanf(line, "# screen=%d,%d", &r, &c) == 2) {
            rec_rows = r; rec_cols = c;
        }
        after_header = std::ftell(f);
    }
    // v3 added apply_step, which delimits a multi-rule step; without it a
    // multithreaded run cannot be reconstructed at all, so older traces are
    // re-recorded rather than carried.
    if (trace_version != 3) {
        std::cerr << "Trace is v" << trace_version
                  << "; this build reads v3. Re-record it." << std::endl;
        std::fclose(f);
        return 1;
    }

    int host_row = 0, host_col = 0;
    if (!headless) {
        initscr();
        start_color();
        raw();
        noecho();
        keypad(stdscr, TRUE);
        timeout(0);
        curs_set(0);

        getmaxyx(stdscr, host_row, host_col);
        if (host_row < rec_rows || host_col < rec_cols) {
            endwin();
            std::cerr << "Terminal too small for replay: have "
                      << host_row << "x" << host_col
                      << ", need at least " << rec_rows << "x" << rec_cols
                      << " (resize and retry)" << std::endl;
            std::fclose(f);
            return 2;
        }
    } else {
        host_row = rec_rows;
        host_col = rec_cols;
    }

    srand(rec_seed);
    srandom(rec_seed);

    Derivation w;
    CursesDisplay curses_display;
    HeadlessDisplay headless_display;
    if (headless) {
        headless_display.resize(rec_rows, rec_cols);
        w.set_display(&headless_display);
    } else {
        w.set_display(&curses_display);
    }
    // --trace PATH alongside --replay: write a fresh trace from the replay
    // session (forwards `cellwrite` events when --trace-cell is set).
    FILE *trace_out_fp = nullptr;
    if (!trace_out_path.empty()) {
        trace_out_fp = std::fopen(trace_out_path.c_str(), "w");
        if (trace_out_fp) {
            std::setvbuf(trace_out_fp, nullptr, _IOLBF, 0);
            fprintf(trace_out_fp, "# zahradnice-trace v3\n");
            fprintf(trace_out_fp, "# seed=%d\n", rec_seed);
            fprintf(trace_out_fp, "# screen=%d,%d\n", rec_rows, rec_cols);
            w.set_trace_file(trace_out_fp);
        }
    }
    if (!watch_cells.empty()) {
        w.set_watch_cells(watch_cells);
    }
    std::unordered_map<std::string, Grammar2D> program_cache;
    Grammar2D *cur_cfg = nullptr;
    std::string cur_path;
    bool first_load = true;
    uint64_t events_processed = 0;
    int score_seen = 0;   // score from recording (last seen in trace)
    int score_live = 0;   // score this replay has accumulated
    uint64_t diverged_at = 0;       // event_step of first divergence (0 = none)
    std::string div_rec_head, div_live_head;
    int div_rec_score = 0, div_live_score = 0;
    bool aborted = false;
    bool paused = false;
    std::wstring last_lhsa;

    // Compute viewport offset for replay (centers the recorded viewport in host terminal)
    int rep_off_row = (host_row - rec_rows) / 2;
    int rep_off_col = (host_col - rec_cols) / 2;
    w.set_render_offset(rep_off_row, rep_off_col);
    if (!headless) clear_outside_viewport(rep_off_row, rep_off_col, rec_rows, rec_cols);

    auto take_replay_screenshot = [&]() {
        if (headless) return;  // step 6 will route to display->dump_*
        char ts[64];
        std::time_t t = std::time(nullptr);
        std::strftime(ts, sizeof(ts), "%Y%m%d_%H%M%S", std::localtime(&t));
        char fn[256];
        std::snprintf(fn, sizeof(fn), "replay_step%llu_%s",
                      (unsigned long long)events_processed, ts);
        std::string base(fn);
        take_screenshot(base + ".txt", false, rep_off_row, rep_off_col, rec_rows, rec_cols);
        take_screenshot(base + ".ansi", true, rep_off_row, rep_off_col, rec_rows, rec_cols);
    };

    auto take_snapshot_at = [&](uint64_t step) {
        char fn[64];
        std::snprintf(fn, sizeof(fn), "snapshot_step%llu", (unsigned long long)step);
        std::string base(fn);
        if (headless) {
            auto [par, tot] = w.getThreadingStats();
            int parallel_pct = tot > 0 ? (100 * par / tot) : -1;
            std::wstring line = cur_cfg
                ? zg::format_status_line(*cur_cfg, score_live,
                                         static_cast<int>(events_processed),
                                         static_cast<int>(w.get_batch_step()),
                                         0, parallel_pct, last_lhsa, rec_cols)
                : std::wstring();
            headless_display.set_status(line);
            headless_display.dump_text(base + ".txt");
            headless_display.dump_ansi(base + ".ansi");
        } else {
            take_screenshot(base + ".txt", false, rep_off_row, rep_off_col, rec_rows, rec_cols);
            take_screenshot(base + ".ansi", true, rep_off_row, rep_off_col, rec_rows, rec_cols);
        }
    };
    auto take_memsnap_at = [&](uint64_t step) {
        char fn[64];
        std::snprintf(fn, sizeof(fn), "memsnap_step%llu.txt", (unsigned long long)step);
        FILE *mfp = std::fopen(fn, "w");
        if (!mfp) return;
        w.dump_memory(mfp, step);
        std::fclose(mfp);
    };
    uint64_t cur_batch = 0;      // apply_step of the batch being replayed
    int pending_score = 0;       // score the current batch ends on
    bool have_pending = false;
    std::set<uint64_t> snapshot_pending(snapshot_steps.begin(), snapshot_steps.end());
    std::set<uint64_t> memsnap_pending(mem_snapshot_steps.begin(), mem_snapshot_steps.end());

    // Unified status: cfg's #! template (left) + last-rule lhsa (right).
    // Interactive prepends a tag (PAUSED/DIV/phase) to the lhsa side so
    // state is still visible. Headless never calls this — uses the same
    // format_status_line via the headless dump path.
    auto render_status = [&](const char *phase) {
        if (headless || !cur_cfg) return;
        auto [par, tot] = w.getThreadingStats();
        int parallel_pct = tot > 0 ? (100 * par / tot) : -1;

        std::wstring tag;
        if (paused) tag = L"[PAUSED] ";
        else if (diverged_at) {
            wchar_t b[48];
            std::swprintf(b, 48, L"[DIV@%llu] ", (unsigned long long)diverged_at);
            tag = b;
        } else if (phase && phase[0] && std::strcmp(phase, "RUN") != 0) {
            tag = L"[";
            for (const char* c = phase; *c; ++c) tag.push_back(*c);
            tag += L"] ";
        }
        std::wstring rhs = tag + last_lhsa;

        std::wstring line = zg::format_status_line(*cur_cfg, score_live,
                                                   static_cast<int>(events_processed),
                                                   static_cast<int>(w.get_batch_step()),
                                                   0, parallel_pct, rhs, rec_cols);
        std::wstring blank(rec_cols, L' ');
        mvaddwstr(rep_off_row, rep_off_col, blank.c_str());
        mvaddwstr(rep_off_row, rep_off_col, line.c_str());
        refresh();
    };

    auto handle_key = [&](wint_t k) {
        if (k == 27) { aborted = true; }
        else if (k == L' ') { paused = !paused; }
        else if (k == KEY_F(12)) { take_replay_screenshot(); }
        else if (k == L'+') { delay_ms = (delay_ms <= 1) ? 0 : delay_ms / 2; }
        else if (k == L'-') { delay_ms = (delay_ms == 0) ? 1 : std::min(5000, delay_ms * 2); }
    };

    while (std::fgets(line, sizeof(line), f)) {
        size_t n = std::strlen(line);
        while (n > 0 && (line[n-1] == '\n' || line[n-1] == '\r')) line[--n] = 0;
        if (n == 0 || line[0] == '#') continue;

        // Pause loop: when paused, block until SPACE (resume) or n/RIGHT (step) or ESC
        while (!headless && paused && !aborted) {
            render_status("PAUSED");
            timeout(-1);
            wint_t k;
            int r = wget_wch(stdscr, &k);
            timeout(0);
            if (r == ERR) continue;
            if (k == L'n' || k == KEY_RIGHT) break;  // single-step
            handle_key(k);
        }
        if (aborted) break;

        // Non-blocking input poll while running
        if (!headless) {
            wint_t kch;
            if (wget_wch(stdscr, &kch) != ERR) {
                handle_key(kch);
                if (aborted) break;
            }
        }

        if (std::strncmp(line, "program_load\t", 13) == 0) {
            char *saveptr = nullptr;
            strtok_r(line, "\t", &saveptr);             // "program_load"
            strtok_r(nullptr, "\t", &saveptr);          // step
            char *sc = strtok_r(nullptr, "\t", &saveptr);  // score
            char *pp = strtok_r(nullptr, "\t", &saveptr);  // path
            if (!pp) continue;
            if (sc) score_seen = std::atoi(sc);
            std::string p(pp);
            cur_path = p;

            auto it = program_cache.find(p);
            if (it == program_cache.end()) {
                Grammar2D cfg;
                cfg.param_overrides = param_overrides;
                if (!cfg.loadFromFile(p)) continue;
                // Replay at the count the run was recorded at: it decides how
                // many rules may co-fire, so it is part of the derivation.
                // Pre-`# threads` traces are single-threaded by construction.
                cfg.thread_count = rec_threads;
                program_cache.emplace(p, std::move(cfg));
            }
            cur_cfg = &program_cache.at(p);

            w.reset(*cur_cfg, rec_rows, rec_cols);
            w.init(first_load);
            first_load = false;
            w.start();
            render_status("LOAD");
        } else if (std::strncmp(line, "program_unload\t", 15) == 0
                || std::strncmp(line, "program_reload\t", 15) == 0) {
            // No-op: next program_load handles state
        } else if (std::strncmp(line, "program_exit\t", 13) == 0) {
            break;
        } else if (std::strncmp(line, "screenshot\t", 11) == 0) {
            // Reproduce screenshot at this checkpoint with _replay suffix.
            // Recording: 'screenshot_YYYYMMDD_HHMMSS.{txt,ansi}'
            // Replay:    'screenshot_YYYYMMDD_HHMMSS_replay.{txt,ansi}'
            // External diff compares them. Ad-hoc lines (manually added to
            // trace before replay) work the same way.
            char *saveptr = nullptr;
            strtok_r(line, "\t", &saveptr);          // "screenshot"
            strtok_r(nullptr, "\t", &saveptr);       // step
            char *base = strtok_r(nullptr, "\t", &saveptr);
            if (base && *base && !headless) {
                refresh();  // ensure any pending engine writes are visible
                std::string b(base);
                take_screenshot(b + "_replay.txt", false,
                                rep_off_row, rep_off_col, rec_rows, rec_cols);
                take_screenshot(b + "_replay.ansi", true,
                                rep_off_row, rep_off_col, rec_rows, rec_cols);
            }
        } else if (std::strncmp(line, "apply\t", 6) == 0 && cur_cfg) {
            // Input replay: feed the recorded trigger to the engine; let normal
            // rule selection determine what fires. With seeded RNG and gating
            // (1 rule per keypress / non-zero-interval timing), the same input
            // sequence produces the same outcome until engine logic changes.
            char *saveptr = nullptr;
            strtok_r(line, "\t", &saveptr);             // "apply"
            char *step_s = strtok_r(nullptr, "\t", &saveptr); // step
            char *sc = strtok_r(nullptr, "\t", &saveptr);   // score
            char *src_s = strtok_r(nullptr, "\t", &saveptr); // src
            char *trig_s = strtok_r(nullptr, "\t", &saveptr); // trig
            strtok_r(nullptr, "\t", &saveptr);          // lhs
            strtok_r(nullptr, "\t", &saveptr);          // idx
            strtok_r(nullptr, "\t", &saveptr);          // ro
            strtok_r(nullptr, "\t", &saveptr);          // co
            strtok_r(nullptr, "\t", &saveptr);          // src_line (v2)
            char *head_s = strtok_r(nullptr, "\t", &saveptr); // head
            char *batch_s = strtok_r(nullptr, "\t", &saveptr); // apply_step (v3)
            if (!trig_s) continue;
            int rec_score = sc ? std::atoi(sc) : score_seen;
            score_seen = rec_score;

            char src_ch = (src_s && src_s[0] && src_s[0] != '-') ? src_s[0] : 0;
            wchar_t trig = 0;
            int got = std::mbtowc(&trig, trig_s, MB_CUR_MAX);
            if (got < 1) trig = static_cast<unsigned char>(trig_s[0]);

            // Consecutive lines sharing an apply_step are one multi-rule step:
            // the engine took a single trigger and applied them together. Feed
            // the trigger once per batch and let the live step reproduce the
            // whole batch, rather than feeding it once per rule -- which is
            // what made a multithreaded trace diverge at its first batch.
            uint64_t rec_batch = batch_s ? std::strtoull(batch_s, nullptr, 10) : 0;
            bool new_batch = (rec_batch != cur_batch);
            Grammar2D::Rule rule_dummy = {};
            std::vector<wchar_t> sounds_dummy;
            if (new_batch) {
                // The previous batch is complete; its last line carried the
                // score the live engine should now be showing.
                if (!diverged_at && have_pending && pending_score != score_live) {
                    diverged_at = events_processed;
                    std::cerr << "Replay diverged at step " << cur_batch
                              << ": recorded score=" << pending_score
                              << "; live score=" << score_live << std::endl;
                }
                cur_batch = rec_batch;
                w.stepMultithreaded(trig, score_live, &rule_dummy, &sounds_dummy, src_ch);
                last_lhsa = rule_dummy.lhsa;
            }
            have_pending = true;
            pending_score = rec_score;
            ++events_processed;
            if (max_steps > 0 && events_processed >= max_steps) {
                aborted = true;
            }

            // --replay-snapshot: capture a screenshot when the recorded step
            // matches a requested step. Uses the trace's step column directly,
            // which equals events_processed under deterministic replay.
            if ((!snapshot_pending.empty() || !memsnap_pending.empty()) && step_s) {
                uint64_t step_v = std::strtoull(step_s, nullptr, 10);
                auto sit = snapshot_pending.find(step_v);
                if (sit != snapshot_pending.end()) {
                    render_status(diverged_at ? "DIV" : "RUN");
                    take_snapshot_at(step_v);
                    snapshot_pending.erase(sit);
                }
                auto mit = memsnap_pending.find(step_v);
                if (mit != memsnap_pending.end()) {
                    take_memsnap_at(step_v);
                    memsnap_pending.erase(mit);
                }
            }

            // Internal divergence test: compare live rule head + score to recording.
            // First divergence is sticky — captured for status display.
            if (!diverged_at && head_s && new_batch) {
                std::string rec_head = head_s;
                // wstring → string for comparison (assume ASCII rule heads;
                // non-ASCII chars compared by raw mbstowcs roundtrip would also work)
                std::string live_head;
                live_head.reserve(rule_dummy.lhsa.size());
                char mb[MB_CUR_MAX + 1];
                for (wchar_t wc : rule_dummy.lhsa) {
                    int n = std::wctomb(mb, wc);
                    if (n > 0) live_head.append(mb, n);
                }
                // Head only: dbgrule carries the batch's *first* selected rule,
                // and the score is not comparable until the batch is complete
                // -- it is checked against the batch's last line above.
                if (rec_head != live_head) {
                    diverged_at = events_processed;
                    div_rec_head = rec_head;
                    div_live_head = live_head;
                    div_rec_score = rec_score;
                    div_live_score = score_live;
                    render_status("DIV");
                }
            }

            if ((events_processed & 63) == 0) render_status(diverged_at ? "DIV" : "RUN");
            if (delay_ms > 0) {
                std::this_thread::sleep_for(std::chrono::milliseconds(delay_ms));
            }
        }
    }

    render_status(aborted ? "ABORTED" : "DONE");
    if (!headless) {
        timeout(2000);  // brief pause so user sees final state
        wint_t k;
        wget_wch(stdscr, &k);
        endwin();
    }
    std::fclose(f);
    if (trace_out_fp) std::fclose(trace_out_fp);

    if (diverged_at) {
        std::cerr << "Replay diverged at event " << diverged_at
                  << ": recorded rule '" << div_rec_head << "' score=" << div_rec_score
                  << "; live rule '" << div_live_head << "' score=" << div_live_score
                  << std::endl;
        return 3;
    }
    if (aborted && max_steps > 0 && events_processed >= max_steps) {
        std::cerr << "Replay stopped at --max-steps " << max_steps
                  << ", final score=" << score_live << std::endl;
    } else if (aborted) {
        std::cerr << "Replay aborted by user." << std::endl;
    } else {
        std::cerr << "Replay completed: " << events_processed
                  << " events, final score=" << score_live << std::endl;
    }

    if (headless && !dump_screen_path.empty()) {
        auto [par, tot] = w.getThreadingStats();
        int parallel_pct = tot > 0 ? (100 * par / tot) : -1;
        std::wstring line = cur_cfg
            ? zg::format_status_line(*cur_cfg, score_live,
                                     static_cast<int>(events_processed),
                                     static_cast<int>(w.get_batch_step()),
                                     0, parallel_pct, last_lhsa, rec_cols)
            : std::wstring();
        headless_display.set_status(line);
        zg::dump_screen_by_ext(headless_display, dump_screen_path);
    }
    return 0;
}

int main(int argc, char *argv[]) {
    setlocale(LC_ALL, "");
    // Keep %lf/%g byte-exact ("0.25" never "0,25"): fractional rule
    // weights are a file-format contract, not a locale preference.
    setlocale(LC_NUMERIC, "C");

    std::string config(".");
    std::string trace_path, stats_path, replay_path;
    int seed = 0;
    int max_threads = 0;
    int replay_delay = 0;
    int screen_rows = 0, screen_cols = 0;
    std::vector<uint64_t> snapshot_steps;
    std::vector<uint64_t> mem_snapshot_steps;
    std::unordered_set<std::pair<int,int>, hash_pair> watch_cells;
    bool headless = false;
    std::string input_arg;
    uint64_t max_steps = 0;
    std::string dump_screen_path;
    // Parameter overrides live at process level, not in the loaded grammar:
    // they must survive a #program switch, a `clear` and an `x` reload.
    std::map<std::string, std::string> param_overrides;

    auto needs_value = [&](int i) -> bool {
        if (i + 1 >= argc) {
            std::cerr << "missing value for " << argv[i] << std::endl;
            return false;
        }
        return true;
    };

    bool seen_positional = false;
    for (int i = 1; i < argc; ++i) {
        std::string a = argv[i];
        if (a == "-h" || a == "--help") {
            std::cout <<
                "Usage: ./zahradnice [program] [options]\n"
                "  program              Program path (default: current directory)\n"
                "  --seed N             Random seed (default: time-based)\n"
                "  --max-threads N      Worker threads (default: hardware cores)\n"
                "  --trace PATH         Write event trace (forces single-thread)\n"
                "  --stats PATH         Write per-rule stats summary\n"
                "  --replay PATH        Replay a recorded trace; ignores other options\n"
                "  --replay-delay MS    Delay between replay events (default 0)\n"
                "  --replay-snapshot S  Comma-separated trace steps to screenshot during replay\n"
                "  --mem-snapshot S     Comma-separated steps to dump memory[] to memsnap_step<N>.txt\n"
                "  --trace-cell R,C[,R,C...]  Watched cells; emit `cellwrite` events into the trace\n"
                "  --screen R,C         Constrain engine to RxC viewport (≤ actual terminal)\n"
                "  --headless           Skip ncurses init/render (engine still runs)\n"
                "  --input STR          Headless: drive engine with STR (one trigger char per byte)\n"
                "  --input @PATH        Headless: read trigger string from PATH (whitespace stripped)\n"
                "                       Use `~` for SPACE (raw spaces are stripped for readability).\n"
                "  --max-steps N        Stop after N applied rules (matches trace step column)\n"
                "  --dump-screen PATH   On exit, write final screen. PATH=`-` is stdout\n"
                "                       (auto-detect ANSI vs plain via isatty); `-.ansi`/`-.txt`\n"
                "                       force the format. Default in --headless mode is `-`.\n";
            return 0;
        } else if (a == "--seed") { if (!needs_value(i)) return 1; seed = std::atoi(argv[++i]); }
        else if (a == "--max-threads") { if (!needs_value(i)) return 1; max_threads = std::atoi(argv[++i]); }
        else if (a == "--trace") { if (!needs_value(i)) return 1; trace_path = argv[++i]; }
        else if (a == "--stats") { if (!needs_value(i)) return 1; stats_path = argv[++i]; }
        else if (a == "--param") {
            if (!needs_value(i)) return 1;
            std::string kv = argv[++i];
            size_t eq = kv.find('=');
            if (eq == std::string::npos || eq == 0) {
                std::cerr << "--param expects NAME=VALUE" << std::endl;
                return 1;
            }
            param_overrides[kv.substr(0, eq)] = kv.substr(eq + 1);
        }
        else if (a == "--replay") { if (!needs_value(i)) return 1; replay_path = argv[++i]; }
        else if (a == "--replay-delay") { if (!needs_value(i)) return 1; replay_delay = std::atoi(argv[++i]); }
        else if (a == "--replay-snapshot") {
            if (!needs_value(i)) return 1;
            const char *p = argv[++i];
            char *endp;
            while (*p) {
                while (*p == ',' || *p == ' ') ++p;
                if (!*p) break;
                unsigned long long v = std::strtoull(p, &endp, 10);
                if (endp == p) {
                    std::cerr << "bad --replay-snapshot value, expected comma-separated step numbers\n";
                    return 1;
                }
                snapshot_steps.push_back(static_cast<uint64_t>(v));
                p = endp;
            }
        }
        else if (a == "--mem-snapshot") {
            if (!needs_value(i)) return 1;
            const char *p = argv[++i];
            char *endp;
            while (*p) {
                while (*p == ',' || *p == ' ') ++p;
                if (!*p) break;
                unsigned long long v = std::strtoull(p, &endp, 10);
                if (endp == p) {
                    std::cerr << "bad --mem-snapshot value, expected comma-separated step numbers\n";
                    return 1;
                }
                mem_snapshot_steps.push_back(static_cast<uint64_t>(v));
                p = endp;
            }
        }
        else if (a == "--trace-cell") {
            if (!needs_value(i)) return 1;
            // Flat comma/space-separated ints, paired as (r, c). Odd count = error.
            const char *p = argv[++i];
            char *endp;
            std::vector<int> ints;
            while (*p) {
                while (*p == ',' || *p == ' ') ++p;
                if (!*p) break;
                long v = std::strtol(p, &endp, 10);
                if (endp == p) {
                    std::cerr << "bad --trace-cell value, expected comma-separated integers (r,c,r,c,...)\n";
                    return 1;
                }
                ints.push_back(static_cast<int>(v));
                p = endp;
            }
            if (ints.size() % 2 != 0) {
                std::cerr << "--trace-cell needs an even number of integers (r,c pairs)\n";
                return 1;
            }
            for (size_t k = 0; k + 1 < ints.size(); k += 2) {
                watch_cells.insert({ints[k], ints[k+1]});
            }
        }
        else if (a == "--headless") { headless = true; }
        else if (a == "--input") { if (!needs_value(i)) return 1; input_arg = argv[++i]; }
        else if (a == "--max-steps") { if (!needs_value(i)) return 1; max_steps = std::strtoull(argv[++i], nullptr, 10); }
        else if (a == "--dump-screen") { if (!needs_value(i)) return 1; dump_screen_path = argv[++i]; }
        else if (a == "--screen") {
            if (!needs_value(i)) return 1;
            if (std::sscanf(argv[++i], "%d,%d", &screen_rows, &screen_cols) != 2
                || screen_rows < 2 || screen_cols < 2) {
                std::cerr << "bad --screen value, expected R,C with R,C >= 2\n";
                return 1;
            }
        }
        else if (!a.empty() && a[0] == '-') {
            std::cerr << "unknown option: " << a << std::endl;
            return 1;
        } else if (!seen_positional) {
            config = a;
            seen_positional = true;
        } else {
            std::cerr << "extra positional argument: " << a << std::endl;
            return 1;
        }
    }

    // Headless defaults: stdin → triggers, stdout → screen dump. Both
    // gated by isatty so an interactive TTY doesn't accidentally hang
    // (input) or get garbage-painted (output gets ANSI).
    if (headless && input_arg.empty() && replay_path.empty()
        && !isatty(STDIN_FILENO)) {
        input_arg = "@-";
    }
    if (headless && dump_screen_path.empty()) dump_screen_path = "-";

    if (!replay_path.empty()) {
        return run_replay(replay_path, replay_delay, snapshot_steps,
                          mem_snapshot_steps, watch_cells, trace_path, headless, max_steps,
                          dump_screen_path, param_overrides);
    }

    if (headless && !input_arg.empty()) {
        zg::HeadlessOptions opts;
        opts.config_path = resolve_program_path(config, "");
        opts.input_arg   = input_arg;
        opts.trace_path  = trace_path;
        opts.stats_path  = stats_path;
        opts.dump_path   = dump_screen_path;
        opts.seed        = seed;
        opts.rows        = (screen_rows > 0) ? screen_rows : 24;
        opts.cols        = (screen_cols > 0) ? screen_cols : 80;
        opts.max_steps   = max_steps;
        opts.watch_cells = watch_cells;
        opts.params      = param_overrides;
        return zg::run_headless_input(opts);
    }

    if (headless) {
        std::cerr << "--headless requires --replay, --input, or piped stdin "
                  << "(for tick-driven programs, e.g. `printf 'B%.0s' {1..100} | ./zahradnice --headless prog`)\n";
        return 1;
    }

    if (!input_arg.empty() && !headless) {
        std::cerr << "--input requires --headless (live keyboard mode is the default)\n";
        return 1;
    }

    config = resolve_program_path(config, "");

    // `--param` applies to the program named on the command line and to no
    // other. A menu's entries are commonly thin wrappers that differ only by
    // the value they set before including a shared core (GRAMMAR.md,
    // "Parameters"); a process-wide override would silently flatten every one
    // of them to the same thing. To parameterize a child, run the child.
    const std::string initial_config = config;

    // Initialize global thread pool with command-line specified max threads
    Derivation::initializeGlobalThreadPool(max_threads);

    // Open instrumentation log files (no-op if flags unset)
    FILE* trace_fp = nullptr;
    FILE* stats_fp = nullptr;
    if (!trace_path.empty()) {
        trace_fp = std::fopen(trace_path.c_str(), "w");
        if (trace_fp) std::setvbuf(trace_fp, nullptr, _IOLBF, 0);
    }
    if (!stats_path.empty()) {
        stats_fp = std::fopen(stats_path.c_str(), "w");
    }
    bool trace_active = (trace_fp != nullptr);

    if (Mix_OpenAudio(44100, MIX_DEFAULT_FORMAT, 2, 1024) < 0) {
        //cannot initialize sounds
    }

    Mix_AllocateChannels(32);

    int score = 0;
    int moves = 0;
    bool started = false;

    int actual_seed = (seed == 0) ? static_cast<int>(time(0)) : seed;
    srand(actual_seed);
    srandom(actual_seed);  // POSIX random() has separate state from rand()

    int row, col;

    initscr();
    start_color();
    raw();
    noecho();
    keypad(stdscr, TRUE);  // Enable function keys like F12
    timeout(0);  // Non-blocking mode since programs start running
    curs_set(0);

    Derivation w;
    CursesDisplay display;
    w.set_display(&display);
    w.set_trace_file(trace_fp);
    w.set_stats_file(stats_fp);
    if (!watch_cells.empty()) {
        if (!trace_fp) {
            std::cerr << "warning: --trace-cell requires --trace; cellwrite events will not be emitted\n";
        }
        w.set_watch_cells(watch_cells);
    }
    if (!mem_snapshot_steps.empty()) {
        std::cerr << "warning: --mem-snapshot only fires during --replay; ignored in record mode\n";
    }

    // Compute viewport size + centering offset from --screen vs actual terminal
    int actual_row, actual_col;
    getmaxyx(stdscr, actual_row, actual_col);
    int eff_row = (screen_rows > 0) ? screen_rows : actual_row;
    int eff_col = (screen_cols > 0) ? screen_cols : actual_col;
    if (eff_row > actual_row || eff_col > actual_col) {
        endwin();
        std::cerr << "--screen " << screen_rows << "," << screen_cols
                  << " exceeds actual terminal "
                  << actual_row << "x" << actual_col << "; resize and retry\n";
        return 1;
    }
    int off_row = (actual_row - eff_row) / 2;
    int off_col = (actual_col - eff_col) / 2;
    w.set_render_offset(off_row, off_col);
    clear_outside_viewport(off_row, off_col, eff_row, eff_col);

    // Trace header: tool version, seed, viewport dimensions (constrained or actual)
    if (trace_fp) {
        fprintf(trace_fp, "# zahradnice-trace v2\n");
        fprintf(trace_fp, "# seed=%d\n", actual_seed);
        fprintf(trace_fp, "# screen=%d,%d\n", eff_row, eff_col);
        fprintf(trace_fp, "# threads=1\n");  // see the thread-count pin below
        // Only the overrides: this header is written before any program is
        // loaded, and an interactive session may visit several. The resolved
        // per-program vector is in the headless trace, which is what the
        // analyzers read.
        for (const auto &[name, value] : param_overrides)
            fprintf(trace_fp, "# param %s=%s\n", name.c_str(), value.c_str());
    }

    std::string prev_config;  // For program_unload markers
    // Stack of calling programs. A frame remembers the #program key that
    // launched the child, so a `^…?` starting symbol in the caller can be
    // planted with it on the way back — the caller learns which of its
    // entries it is returning from without holding any of its own state.
    struct Frame {
        std::string path;
        wchar_t key;
    };
    std::vector<Frame> caller_stack;
    wchar_t pending_param = 0;  // key handed to the next start(), then spent

    // Program caching
    std::unordered_map<std::string, Grammar2D> program_cache;
    std::unordered_map<std::string, std::unordered_map<wchar_t, std::shared_ptr<sample>>> sound_cache;

    bool clear = true;  // Clear on first program load
    bool err = 0;
    bool paused = false;
    bool was_running = false;  // Track if we were running when switching programs

    std::wstring preserved_rule_lhsa;  // Preserve only display info across switches

    while (config != "quit") {
        // Mark program transition: unload previous, load new
        if (!prev_config.empty()) {
            w.log_program_unload(prev_config, score);
            w.dump_stats_for_program(prev_config);
        }
        w.log_program_load(config, score);
        prev_config = config;

        std::unordered_map<wchar_t, int> elapsed_counts;  // Track elapsed counts per timing char
        bool success = true;
        bool quiet = false;  // last trigger applied nothing: screen is a fixed point

        Grammar2D cfg;
        std::unordered_map<wchar_t, std::shared_ptr<sample>> sounds;

        // Check if program is cached
        auto cache_it = program_cache.find(config);
        if (cache_it != program_cache.end()) {
            // Use cached program
            cfg = cache_it->second;
            sounds = sound_cache[config];
        } else {
            // Load and cache new program. Overrides reach the top-level
            // program only, so the path alone still keys the cache.
            if (config == initial_config) cfg.param_overrides = param_overrides;
            if (cfg.loadFromFile(config) == false) {
                std::cerr << "Program " << config << " not found, exiting." << std::endl;
                err = 1;
                break;
            }

            // Auto-detect thread count if not set. Recording a trace pins it
            // to 1 -- unconditionally, so the `# threads=1` written into the
            // header is true even of a program that asks for more. An
            // interactive session may visit several programs, so a per-program
            // count could not be honestly recorded in a header written once.
            // To record a multithreaded run faithfully, use
            // `zahradnice-headless --threads N --trace`, which resolves the
            // count before writing its header.
            if (trace_active) {
                cfg.thread_count = 1;
            } else if (cfg.thread_count == 0) {
                cfg.thread_count = std::thread::hardware_concurrency();
                if (cfg.thread_count == 0) cfg.thread_count = 1; // fallback
            }

            // Get program directory for sound path resolution
            std::string program_dir = ".";
            size_t last_slash = config.find_last_of("/");
            if (last_slash != std::string::npos) {
                program_dir = config.substr(0, last_slash);
            }

            // Load sounds from pre-parsed paths with proper resolution
            for (const auto& sound_entry : cfg.sound_paths) {
                std::string resolved_path = resolve_sound_path(sound_entry.second, program_dir);
                sounds.insert({sound_entry.first, std::make_shared<sample>(resolved_path, 100)});
            }

            // Cache the loaded program and sounds
            program_cache[config] = cfg;
            sound_cache[config] = sounds;
        }

        // Initialize elapsed counts for all timing characters
        for (const auto& [timing_char, interval] : cfg.timing_chars) {
            elapsed_counts[timing_char] = 0;
        }

        // Initialize statusline template for this program
        current_help_text = cfg.help_text;
        if (!cfg.help.empty()) {
            active_statusline_template = cfg.help;
        }

        // Control key translation handled by reverse dictionary mappings

        row = eff_row;
        col = eff_col;

        //top row reserved as status line
        w.reset(cfg, row, col);
        w.init(clear);
        clear = false;  // Subsequent program switches preserve state
        w.start(pending_param);
        pending_param = 0;

        // Restore running state after program switch
        if (was_running) {
            paused = false;
            timeout(0);
        }

        wint_t wch = L' ';

        Grammar2D::Rule rule = {};  // Initialize fresh rule for each program
        // Restore preserved display info
        rule.lhsa = preserved_rule_lhsa;

        auto start = std::chrono::steady_clock::now();

        while (true) {
            // switch programs if requested (check first)
            if (success && rule.load && rule.sound != 0) {
                // Look up program path from dictionary
                auto it = cfg.program_paths.find(rule.sound);
                if (it != cfg.program_paths.end()) {
                    std::string new_program = it->second;
                    // Track if we were running when switching
                    was_running = !paused;
                    // Push current program to stack and switch
                    caller_stack.push_back({config, rule.sound});
                    config = resolve_program_path(new_program, config);
                    break;
                }
            }
            // Sound playing is now handled in the rule application section

            // print status using template system (row 0 of the centred viewport)
            clear_status(off_row, off_col, col);

            // Get threading stats
            auto [parallel, total] = w.getThreadingStats();
            int parallel_pct = total > 0 ? (100 * parallel / total) : -1;

            // Render left part (template content)
            // `{steps}` is applied rules, as it has always been: a parallel
            // step that landed four rules counts four. It is the measure that
            // does not move with the thread count, and matches the trace's
            // step column and `--max-steps`. `{batches}` counts steps proper --
            // one per trigger event that applied anything. Equal at #threads 1.
            std::wstring left_content = render_statusline(
                score, static_cast<int>(w.get_event_step()),
                static_cast<int>(w.get_batch_step()), moves, parallel_pct);

            // Render right part (rule display)
            std::wstring lhsa_truncated = rule.lhsa;
            int display_width = wcswidth(lhsa_truncated.c_str(), lhsa_truncated.length());
            if (display_width < 0) display_width = lhsa_truncated.length(); // fallback for non-printable chars

            // Ensure space for rule display
            int max_left_width = col - display_width - 1;
            int left_display_width = wcswidth(left_content.c_str(), left_content.length());
            if (left_display_width < 0) left_display_width = left_content.length();

            if (max_left_width > 0 && left_display_width > max_left_width) {
                // Truncate to fit, being careful with wide characters
                std::wstring truncated;
                int width = 0;
                for (wchar_t wc : left_content) {
                    int char_width = wcwidth(wc);
                    if (char_width < 0) char_width = 1;
                    if (width + char_width > max_left_width) break;
                    truncated += wc;
                    width += char_width;
                }
                left_content = truncated;
            }

            // Display left content using wide character function
            if (max_left_width > 0) {
                mvaddwstr(off_row, off_col, left_content.c_str());
            }

            // Display right content (rule) - shift one char left to keep cursor on top row
            if (display_width > 0 && display_width < col) {
                int start_col = col - display_width - 1;  // Shift one position left
                if (start_col >= 0) {
                    mvaddwstr(off_row, off_col + start_col, lhsa_truncated.c_str());
                }
            }

            // Sleep in wget_wch rather than spinning when there is nothing to
            // do; a keypress still wakes us at once.
            timeout(paused ? -1 : idle_timeout_ms(cfg, elapsed_counts, start, quiet));

            int result = wget_wch(stdscr, &wch);
            if (result == ERR) {
                wch = ERR;
            }

            // Track if this was real user input (not timing event)
            bool user_input = (result != ERR);

            //time lapse
            if (wch == ERR) {
                wch = 0;
                auto stop = std::chrono::steady_clock::now();
                std::chrono::duration<double, std::milli> duration = stop - start;

                // First check interval-based timing (overdue events get priority)
                for (const auto& [timing_char, interval] : cfg.timing_chars) {
                    if (interval > 0) {
                        int elapsed = static_cast<int>(duration.count() / interval);
                        if (elapsed > elapsed_counts[timing_char]) {
                            wch = timing_char;
                            elapsed_counts[timing_char] = elapsed;
                            break;
                        }
                    }
                }

                // Only if no interval timing fired, check immediate timing.
                // A quiet screen disarms it: it would fail again, unchanged.
                if (wch == 0 && !quiet) {
                    for (const auto& [timing_char, interval] : cfg.timing_chars) {
                        if (interval == 0) {
                            wch = timing_char;
                            break;
                        }
                    }
                }
            }

            // Emergency exit (ESC) - always works, bypasses all control systems
            if(wch == 27) { // ESC key
                config = "quit";
                break;
            }

            // Global screenshot feature (F12) - always available
            // Takes both plain text and colored screenshots
            if(wch == KEY_F(12)) {
                // Generate timestamp-based filenames
                std::time_t t = std::time(nullptr);
                char timestamp_base[100];
                std::strftime(timestamp_base, sizeof(timestamp_base), "screenshot_%Y%m%d_%H%M%S", std::localtime(&t));

                std::string txt_filename = std::string(timestamp_base) + ".txt";
                std::string ansi_filename = std::string(timestamp_base) + ".ansi";

                bool txt_success = take_screenshot(txt_filename, false,
                                                   off_row, off_col, eff_row, eff_col);
                bool ansi_success = take_screenshot(ansi_filename, true,
                                                    off_row, off_col, eff_row, eff_col);

                if (txt_success || ansi_success) {
                    // Set feedback message to be displayed in next loop iteration
                    rule.lhsa = L"Screenshot saved";
                    // Log as event for replay parity
                    if (trace_fp) {
                        std::fprintf(trace_fp, "screenshot\t%llu\t%s\n",
                                     (unsigned long long)w.get_event_step(),
                                     timestamp_base);
                    }
                }
            }

            // Apply a single rule (counts as a step) or handle timing
            {
                rule.sound = 0;
                std::vector<wchar_t> applied_sounds;
                success = w.stepMultithreaded(wch, score, &rule, &applied_sounds,
                                              user_input ? 'k' : 't');
                if (success) {
                    // Increment moves counter only for successful user input
                    if (user_input) {
                        ++moves;
                    }
                    // Preserve rule display info across program switches
                    preserved_rule_lhsa = rule.lhsa;

                    // Handle rule-based engine actions (counts as moves, unlike direct actions)
                    if (rule.engine_action && rule.sound != 0) {
                        std::string action = cfg.getEngineAction(rule.sound);
                        if (action == "pause") {
                            paused = !paused;  // Toggle pause state
                            timeout(paused ? -1 : 0);  // Set blocking or non-blocking mode
                        } else if (action == "reset") {
                            // Reset to top-level program from stack
                            if (!caller_stack.empty()) {
                                config = caller_stack[0].path;  // Top-level program
                                caller_stack.clear();
                            }
                            // If stack is empty, we're already at top-level, just continue
                            break;
                        } else if (action == "clear") {
                            // Clear screen and restart current program with its starting symbols
                            // Treat as unload+load of same path so stats reset cleanly
                            w.log_program_unload(config, score);
                            w.dump_stats_for_program(config);
                            w.log_program_load(config, score);
                            w.init(true);  // Clear the screen
                            w.reset(cfg, row, col);  // Re-apply starting symbols
                            w.start();  // Start the derivation
                        } else if (action == "return") {
                            // Pop from caller stack
                            if (!caller_stack.empty()) {
                                config = caller_stack.back().path;
                                pending_param = caller_stack.back().key;
                                caller_stack.pop_back();
                            } else {
                                config = "quit";  // No caller to return to
                            }
                            break;
                        } else if (action == "quit") {
                            config = "quit";
                            break;
                        }
                    }

                    // Play all sounds from applied rules
                    for (wchar_t sound_char : applied_sounds) {
                        auto it = sounds.find(sound_char);
                        if (it != sounds.end()) {
                            it->second->play();
                        }
                    }
                }
                // A screen the free-running trigger could not move is a fixed
                // point: nothing but a key or an interval event can change it.
                if (success) {
                    quiet = false;
                } else {
                    auto tit = cfg.timing_chars.find(wch);
                    if (tit != cfg.timing_chars.end() && tit->second == 0) quiet = true;
                }
            }

            //refresh();
        }
    }

    endwin();

    Mix_CloseAudio();
    Mix_Quit();

    // Final instrumentation: unload last program, dump its stats, log exit
    if (!prev_config.empty()) {
        w.log_program_unload(prev_config, score);
        w.dump_stats_for_program(prev_config);
    }
    w.log_program_exit(score);
    if (trace_fp) std::fclose(trace_fp);
    if (stats_fp) std::fclose(stats_fp);

    return err;
}
