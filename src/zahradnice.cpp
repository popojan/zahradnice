#include <ncursesw/ncurses.h>
#include <clocale>
#include <iostream>
#include "grammar.h"
#include "statusline.h"
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

    // If program path already includes directory, use relative to current directory
    if (program_path.find('/') != std::string::npos) {
        base_path = program_path;
    } else {
        // Get directory of current config
        size_t last_slash = current_config.find_last_of("/");
        if (last_slash != std::string::npos) {
            // Current config has directory, use that directory
            base_path = current_config.substr(0, last_slash) + "/" + program_path;
        } else {
            // Current config has no directory, use current working directory
            base_path = program_path;
        }
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

void clear_status(size_t len) {
    std::wstring empty(len, L' ');
    mvaddwstr(0, 0, empty.c_str());
}

int main(int argc, char *argv[]) {
    setlocale(LC_ALL, "");

    if (argc > 1) {
        auto param = std::string(argv[1]);
        if (param == "-h" || param == "--help") {
            std::cout
                    << "Usage: ./zahradnice [<program.cfg>] [seed] [max-threads]"
                    << std::endl
                    << "  program.cfg  - Program to run (default: current directory)"
                    << std::endl
                    << "  seed         - Random seed (default: time-based)"
                    << std::endl
                    << "  max-threads  - Maximum worker threads (default: hardware cores)"
                    << std::endl;
            return 0;
        }
    }

    std::string config(".");
    int seed = 0;
    int max_threads = 0; // 0 = auto-detect

    if (argc > 1) config = argv[1];
    if (argc > 2) seed = std::atoi(argv[2]);
    if (argc > 3) max_threads = std::atoi(argv[3]);

    config = resolve_program_path(config, config);

    // Initialize global thread pool with command-line specified max threads
    Derivation::initializeGlobalThreadPool(max_threads);

    if (Mix_OpenAudio(44100, MIX_DEFAULT_FORMAT, 2, 1024) < 0) {
        //cannot initialize sounds
    }

    Mix_AllocateChannels(32);

    int score = 0;
    int steps = 0;
    int moves = 0;
    bool started = false;

    if (seed == 0) {
        srand(time(0));
    }
    else {
        srand(seed);
    }

    int row, col;

    initscr();
    start_color();
    raw();
    noecho();
    timeout(0);  // Non-blocking mode since programs start running
    curs_set(0);

    Derivation w;
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

            // Auto-detect thread count if not set
            if (cfg.thread_count == 0) {
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

        // Initialize status line renderer for this program
        StatusLineRenderer::initialize_program(cfg.help, cfg.help_text);

        // Control key translation handled by reverse dictionary mappings

        getmaxyx(stdscr, row, col);

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

            // print status using template system
            clear_status(col);

            // Get threading stats
            auto [parallel, total] = w.getThreadingStats();
            int parallel_pct = total > 0 ? (100 * parallel / total) : -1;

            // Render left part (template content)
            std::string left_content = StatusLineRenderer::render(score, steps, moves, parallel_pct);

            // Render right part (rule display)
            std::wstring lhsa_truncated = rule.lhsa;
            int display_width = wcswidth(lhsa_truncated.c_str(), lhsa_truncated.length());
            if (display_width < 0) display_width = lhsa_truncated.length(); // fallback for non-printable chars

            // Ensure space for rule display
            int max_left_width = col - display_width - 1;
            if (max_left_width > 0 && left_content.length() > max_left_width) {
                left_content = left_content.substr(0, max_left_width);
            }

            // Display left content
            if (max_left_width > 0) {
                mvprintw(0, 0, left_content.c_str());
            }

            // Display right content (rule) - shift one char left to keep cursor on top row
            if (display_width > 0 && display_width < col) {
                int start_col = col - display_width - 1;  // Shift one position left
                if (start_col >= 0) {
                    mvaddwstr(0, start_col, lhsa_truncated.c_str());
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

            // Apply a single rule (counts as a step) or handle timing
            {
                rule.sound = 0;
                std::vector<wchar_t> applied_sounds;
                success = w.stepMultithreaded(wch, score, &rule, &applied_sounds);
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
                            paused = true;
                            timeout(-1);
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
                else if (wch == L'T') {
                    std::this_thread::sleep_for(std::chrono::milliseconds{50});
                }
                last = wch;
            }

            //refresh();
        }
    }

    endwin();

    Mix_CloseAudio();
    Mix_Quit();

    return err;
}
