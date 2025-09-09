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
    // If program path is "quit", return as-is
    if (program_path == "quit") {
        return program_path;
    }

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
    timeout(-1);
    curs_set(0);

    Derivation w;
    std::vector<std::string> caller_stack;  // Stack of calling programs

    bool clear = true;  // Clear on first program load
    bool err = 0;
    bool paused = true;
    while (config != "quit") {
        int elapsed_t = 0;
        int elapsed_b = 0;
        int elapsed_m = 0;

        bool success = true;

        Grammar2D cfg;
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

        std::unordered_map<wchar_t, sample> sounds;
        // Use pre-parsed timing values
        int B = cfg.B_step;
        int M = cfg.M_step;
        int T = cfg.T_step;

        // Load sounds from pre-parsed paths with proper resolution
        for (const auto& sound_entry : cfg.sound_paths) {
            std::string resolved_path = resolve_sound_path(sound_entry.second, program_dir);
            sounds.insert({sound_entry.first, sample(resolved_path, 100)});
        }

        // Control key translation handled by reverse dictionary mappings

        getmaxyx(stdscr, row, col);

        //top row reserved as status line
        w.reset(cfg, row, col);
        w.init(clear || cfg.clear_requested);
        clear = false;  // Subsequent program switches preserve state
        w.start();

        wint_t wch = L' ';
        wint_t last = L' ';

        Grammar2D::Rule rule = {};  // Initialize all members to zero/false

        auto start = std::chrono::steady_clock::now();

        while (true) {
            // switch programs if requested (check first)
            if (success && rule.load && rule.sound != 0) {
                // Look up program path from dictionary
                auto it = cfg.program_paths.find(rule.sound);
                if (it != cfg.program_paths.end()) {
                    std::string new_program = it->second;
                    if (new_program == "return") {
                        // Pop from caller stack
                        if (!caller_stack.empty()) {
                            config = caller_stack.back();
                            caller_stack.pop_back();
                        } else {
                            config = "quit";  // No caller to return to
                        }
                    } else {
                        // Push current program to stack and switch
                        caller_stack.push_back(config);
                        config = resolve_program_path(new_program, config);
                    }
                    break;
                }
            }
            // Sound playing is now handled in the rule application section

            // print status
            auto [parallel, total] = w.getThreadingStats();
            std::string status_text = "Score: " + std::to_string(score) + " Steps: " + std::to_string(steps);
            if (total > 0) {
                status_text += " (" + std::to_string(100 * parallel / total) + "%)";
            }

            if (elapsed_b == 0 || paused) {
                auto limit = std::min(static_cast<size_t>(col-1), cfg.help.size());
                std::wstring help_truncated = cfg.help;
                help_truncated.erase(limit, std::wstring::npos);
                clear_status(col);
                mvaddwstr(0, 0, help_truncated.c_str());
            }
            else {
                auto limit = std::min(static_cast<size_t>(col-1), status_text.size());
                clear_status(col);
                if (limit < status_text.length()) status_text.erase(limit);
                mvprintw(0, 0, status_text.c_str());
                limit = std::min(static_cast<size_t>(col-1), rule.lhsa.size());
                std::wstring lhsa_truncated = rule.lhsa;
                lhsa_truncated.erase(limit, std::wstring::npos);

                // Calculate actual display width (wide chars take 2 columns)
                int display_width = wcswidth(lhsa_truncated.c_str(), lhsa_truncated.length());
                if (display_width < 0) display_width = lhsa_truncated.length(); // fallback

                int start_col = col - display_width - 1;
                if (start_col < 0) start_col = 0; // prevent overflow
                mvaddwstr(0, start_col, lhsa_truncated.c_str());
            }

            int result = wget_wch(stdscr, &wch);
            if (result == ERR) {
                wch = ERR;
            }

            //time lapse
            //save CPU if no rule applicable
            if (!success && last == wch) {
                wch = ERR;
            }

            if (wch == ERR) {
                wch = 0;
                auto stop = std::chrono::steady_clock::now();
                std::chrono::duration<double, std::milli> duration = stop - start;
                int el_t = T > 0 ? static_cast<int>(duration.count() / T) : elapsed_t + 1;
                int el_b = static_cast<int>(duration.count() / B);
                int el_m = static_cast<int>(duration.count() / M);
                if (el_t > elapsed_t) {
                    wch = L'T';
                    elapsed_t = el_t;
                }
                if (el_m > elapsed_m) {
                    wch = L'M';
                    elapsed_m = el_m;
                }
                if (el_b > elapsed_b) {
                    wch = L'B';
                    elapsed_b = el_b;
                }
            }

            //restart scene
            // Translate user input for control keys
            wchar_t control_key = cfg.getControlKey(wch);

            if (control_key == L'x') {
                paused = true;
                timeout(-1);
                getmaxyx(stdscr, row, col);
                w.reset(cfg, row, col);
                w.init(true);
                w.start();
            }

            // toggle pause

            else if (control_key == L' ') {
                paused = !paused;
                if (!paused) {
                    timeout(0);
                } else {
                    timeout(-1);
                }
            }
            else if(control_key == L'q' && !success && paused) {
                config = "quit";
                break;
            }
            // Emergency exit (ESC) - always works, bypasses dictionary
            else if(wch == 27) { // ESC key
                config = "quit";
                break;
            }
            // apply a single rule (counts as a step)

            else {
                // Translate user input to internal control key if remapped
                wchar_t translated_key = cfg.getControlKey(wch);

                rule.sound = 0;
                std::vector<wchar_t> applied_sounds;
                success = w.stepMultithreaded(translated_key, score, &rule, &applied_sounds);
                if (success) {
                    ++steps;
                    // Play all sounds from applied rules
                    for (wchar_t sound_char : applied_sounds) {
                        auto it = sounds.find(sound_char);
                        if (it != sounds.end()) {
                            it->second.play();
                        }
                    }
                }
                else if (translated_key == L'T') {
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
