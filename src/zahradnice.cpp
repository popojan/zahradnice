#include <ncursesw/ncurses.h>
#include <clocale>
#include <iostream>
#include "grammar.h"
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
#include <ctime>
#include <cstring>
#include <vector>
#include <set>

// Global state for statusline template inheritance
static std::wstring active_statusline_template = L"";
static std::wstring current_help_text = L"";

// Simple wide string replacement helper
static void replace_all(std::wstring &str, const std::wstring &from, const std::wstring &to) {
    size_t start_pos = 0;
    while ((start_pos = str.find(from, start_pos)) != std::wstring::npos) {
        str.replace(start_pos, from.length(), to);
        start_pos += to.length();
    }
}

// Simple integer to wide string conversion
static std::wstring int_to_wstring(int value) {
    if (value == 0) return L"0";

    std::wstring result;
    bool negative = value < 0;
    if (negative) value = -value;

    while (value > 0) {
        result = static_cast<wchar_t>(L'0' + value % 10) + result;
        value /= 10;
    }

    if (negative) result = L"-" + result;
    return result;
}

// Render statusline with template substitution
static std::wstring render_statusline(int score, int steps, int moves, int parallel_pct) {
    std::wstring tmpl;
    if (!active_statusline_template.empty()) {
        tmpl = active_statusline_template;
    } else {
        tmpl = L"Score: {score} Steps: {steps} {parallel} {help}";
    }

    // Perform variable substitutions
    replace_all(tmpl, L"{score}", int_to_wstring(score));
    replace_all(tmpl, L"{steps}", int_to_wstring(steps));
    replace_all(tmpl, L"{moves}", int_to_wstring(moves));

    if (parallel_pct >= 0) {
        replace_all(tmpl, L"{parallel}", int_to_wstring(parallel_pct) + L"%");
    } else {
        replace_all(tmpl, L"{parallel}", L"");
    }

    replace_all(tmpl, L"{help}", current_help_text);

    return tmpl;
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
                      const std::vector<uint64_t> &snapshot_steps) {
    FILE *f = std::fopen(replay_path.c_str(), "r");
    if (!f) {
        std::cerr << "Cannot open replay file: " << replay_path << std::endl;
        return 1;
    }

    // Parse header: "# zahradnice-trace vN", "# seed=N", "# screen=R,C"
    int rec_seed = 1, rec_rows = 24, rec_cols = 80, trace_version = 0;
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
        else if (std::sscanf(line, "# screen=%d,%d", &r, &c) == 2) {
            rec_rows = r; rec_cols = c;
        }
        after_header = std::ftell(f);
    }
    if (trace_version != 0 && trace_version < 2) {
        std::cerr << "Trace is v" << trace_version
                  << "; this build expects v2. Convert with scripts/upgrade_trace_v1_to_v2.py."
                  << std::endl;
        std::fclose(f);
        return 1;
    }

    initscr();
    start_color();
    raw();
    noecho();
    keypad(stdscr, TRUE);
    timeout(0);
    curs_set(0);

    int host_row, host_col;
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

    srand(rec_seed);
    srandom(rec_seed);

    Derivation w;
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

    // Compute viewport offset for replay (centers the recorded viewport in host terminal)
    int rep_off_row = (host_row - rec_rows) / 2;
    int rep_off_col = (host_col - rec_cols) / 2;
    w.set_render_offset(rep_off_row, rep_off_col);
    clear_outside_viewport(rep_off_row, rep_off_col, rec_rows, rec_cols);

    auto take_replay_screenshot = [&]() {
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
        take_screenshot(base + ".txt", false, rep_off_row, rep_off_col, rec_rows, rec_cols);
        take_screenshot(base + ".ansi", true, rep_off_row, rep_off_col, rec_rows, rec_cols);
    };
    std::set<uint64_t> snapshot_pending(snapshot_steps.begin(), snapshot_steps.end());

    auto render_status = [&](const char *phase) {
        char buf[512];
        const char *pp = paused ? "PAUSED" : phase;
        if (diverged_at) {
            std::snprintf(buf, sizeof(buf),
                "REPLAY %s: ev=%llu d=%dms | DIV@%llu rec='%s'/%d live='%s'/%d (SPACE n F12 +- ESC)",
                pp, (unsigned long long)events_processed, delay_ms,
                (unsigned long long)diverged_at,
                div_rec_head.c_str(), div_rec_score,
                div_live_head.c_str(), div_live_score);
        } else {
            std::snprintf(buf, sizeof(buf),
                "REPLAY %s: %s | ev=%llu score=%d d=%dms (SPACE pause, n step, F12 shot, +- speed, ESC)",
                pp, cur_path.c_str(),
                (unsigned long long)events_processed, score_live, delay_ms);
        }
        std::string s(buf);
        if (static_cast<int>(s.size()) > rec_cols) s.resize(rec_cols);
        std::wstring blank(rec_cols, L' ');
        mvaddwstr(rep_off_row, rep_off_col, blank.c_str());
        mvaddstr(rep_off_row, rep_off_col, s.c_str());
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
        while (paused && !aborted) {
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
        wint_t kch;
        if (wget_wch(stdscr, &kch) != ERR) {
            handle_key(kch);
            if (aborted) break;
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
                if (!cfg.loadFromFile(p)) continue;
                if (cfg.thread_count == 0) cfg.thread_count = 1;  // replay is force-execute
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
            if (base && *base) {
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
            char *head_s = strtok_r(nullptr, "\t", &saveptr); // head (rest of line)
            if (!trig_s) continue;
            int rec_score = sc ? std::atoi(sc) : score_seen;
            score_seen = rec_score;

            char src_ch = (src_s && src_s[0] && src_s[0] != '-') ? src_s[0] : 0;
            wchar_t trig = 0;
            int got = std::mbtowc(&trig, trig_s, MB_CUR_MAX);
            if (got < 1) trig = static_cast<unsigned char>(trig_s[0]);

            Grammar2D::Rule rule_dummy = {};
            std::vector<wchar_t> sounds_dummy;
            w.stepMultithreaded(trig, score_live, &rule_dummy, &sounds_dummy, src_ch);
            ++events_processed;

            // --replay-snapshot: capture a screenshot when the recorded step
            // matches a requested step. Uses the trace's step column directly,
            // which equals events_processed under deterministic replay.
            if (!snapshot_pending.empty() && step_s) {
                uint64_t step_v = std::strtoull(step_s, nullptr, 10);
                auto it = snapshot_pending.find(step_v);
                if (it != snapshot_pending.end()) {
                    render_status(diverged_at ? "DIV" : "RUN");
                    take_snapshot_at(step_v);
                    snapshot_pending.erase(it);
                }
            }

            // Internal divergence test: compare live rule head + score to recording.
            // First divergence is sticky — captured for status display.
            if (!diverged_at && head_s) {
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
                if (rec_head != live_head || rec_score != score_live) {
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
    timeout(2000);  // brief pause so user sees final state
    wint_t k;
    wget_wch(stdscr, &k);

    endwin();
    std::fclose(f);

    if (diverged_at) {
        std::cerr << "Replay diverged at event " << diverged_at
                  << ": recorded rule '" << div_rec_head << "' score=" << div_rec_score
                  << "; live rule '" << div_live_head << "' score=" << div_live_score
                  << std::endl;
        return 3;
    }
    if (aborted) std::cerr << "Replay aborted by user." << std::endl;
    else std::cerr << "Replay completed: " << events_processed
                   << " events, final score=" << score_live << std::endl;
    return 0;
}

int main(int argc, char *argv[]) {
    setlocale(LC_ALL, "");

    std::string config(".");
    std::string trace_path, stats_path, replay_path;
    int seed = 0;
    int max_threads = 0;
    int replay_delay = 0;
    int screen_rows = 0, screen_cols = 0;
    std::vector<uint64_t> snapshot_steps;

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
                "  --screen R,C         Constrain engine to RxC viewport (≤ actual terminal)\n";
            return 0;
        } else if (a == "--seed") { if (!needs_value(i)) return 1; seed = std::atoi(argv[++i]); }
        else if (a == "--max-threads") { if (!needs_value(i)) return 1; max_threads = std::atoi(argv[++i]); }
        else if (a == "--trace") { if (!needs_value(i)) return 1; trace_path = argv[++i]; }
        else if (a == "--stats") { if (!needs_value(i)) return 1; stats_path = argv[++i]; }
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

    if (!replay_path.empty()) {
        return run_replay(replay_path, replay_delay, snapshot_steps);
    }

    config = resolve_program_path(config, "");

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
    int steps = 0;
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
    w.set_trace_file(trace_fp);
    w.set_stats_file(stats_fp);

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
    }

    std::string prev_config;  // For program_unload markers
    std::vector<std::string> caller_stack;  // Stack of calling programs

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

        Grammar2D cfg;
        std::unordered_map<wchar_t, std::shared_ptr<sample>> sounds;

        // Check if program is cached
        auto cache_it = program_cache.find(config);
        if (cache_it != program_cache.end()) {
            // Use cached program
            cfg = cache_it->second;
            sounds = sound_cache[config];
        } else {
            // Load and cache new program
            if (cfg.loadFromFile(config) == false) {
                std::cerr << "Program " << config << " not found, exiting." << std::endl;
                err = 1;
                break;
            }

            // Auto-detect thread count if not set.
            // When recording a trace, force single-thread for replay determinism.
            if (cfg.thread_count == 0) {
                if (trace_active) {
                    cfg.thread_count = 1;
                } else {
                    cfg.thread_count = std::thread::hardware_concurrency();
                    if (cfg.thread_count == 0) cfg.thread_count = 1; // fallback
                }
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
        w.start();

        // Restore running state after program switch
        if (was_running) {
            paused = false;
            timeout(0);
        }

        wint_t wch = L' ';
        wint_t last = L' ';

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
                    caller_stack.push_back(config);
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
            std::wstring left_content = render_statusline(score, steps, moves, parallel_pct);

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

            int result = wget_wch(stdscr, &wch);
            if (result == ERR) {
                wch = ERR;
            }

            // Track if this was real user input (not timing event)
            bool user_input = (result != ERR);

            //time lapse
            //save CPU if no rule applicable
            if (!success && last == wch) {
                wch = ERR;
            }

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

                // Only if no interval timing fired, check immediate timing
                if (wch == 0) {
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
                    ++steps;
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
                                config = caller_stack[0];  // Top-level program
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
                                config = caller_stack.back();
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
                last = wch;
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
