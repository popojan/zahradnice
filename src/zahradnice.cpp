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
                    << "Usage: ./zahradnice [<program.cfg>] [seed]"
                    << std::endl;
            return 0;
        }
    }

    std::string config(".");
    int seed = 0;

    if (argc > 1) config = argv[1];
    if (argc > 2) seed = std::atoi(argv[2]);

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

    bool clear = true;
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

        std::unordered_map<wchar_t, sample> sounds;
        // Use pre-parsed timing values
        int B = cfg.B_step;
        int M = cfg.M_step;
        int T = cfg.T_step;

        // Load sounds from pre-parsed paths
        for (const auto& sound_entry : cfg.sound_paths) {
            sounds.insert({sound_entry.first, sample(sound_entry.second, 100)});
        }

        // Control key translation handled by reverse dictionary mappings

        getmaxyx(stdscr, row, col);

        //top row reserved as status line
        w.reset(cfg, row, col);
        w.init(clear);
        w.start();

        wint_t wch = L' ';
        wint_t last = L' ';

        Grammar2D::Rule rule;

        auto start = std::chrono::steady_clock::now();

        while (true) {
            // play sound if any
            if (success && rule.sound != 0) {
                auto it = sounds.find(rule.sound);
                if (it != sounds.end()) {
                    it->second.play();
                }
            }
            // switch programs if requested
            else if (success && rule.load && !rule.lhsa.empty()) {
                std::string new_program("");
                if (rule.lhsa.length() > 5) {
                    std::wstring lhsa_substr = rule.lhsa.substr(5);
                    // Skip leading whitespace, then extract first word
                    size_t start_pos = lhsa_substr.find_first_not_of(L" \t\n\r");
                    std::wstring new_program_wide;
                    if (start_pos != std::wstring::npos) {
                        size_t end_pos = lhsa_substr.find_first_of(L" \t\n\r", start_pos);
                        new_program_wide = (end_pos != std::wstring::npos) ? 
                            lhsa_substr.substr(start_pos, end_pos - start_pos) : 
                            lhsa_substr.substr(start_pos);
                    }
                    // Convert back to UTF-8 string for filesystem operations
                    if (!new_program_wide.empty()) {
                        size_t len = std::wcstombs(nullptr, new_program_wide.c_str(), 0);
                        if (len != static_cast<size_t>(-1)) {
                            new_program.resize(len);
                            std::wcstombs(&new_program[0], new_program_wide.c_str(), len);
                        }
                    }
                }
                if (new_program == "quit") {
                    config = new_program;
                } else {
                    if (config.ends_with(".cfg") || config.ends_with(".cfg.gz")) {
                        config = config.substr(0, config.rfind('/')) + "/" + new_program;
                    } else {
                        config = config + "/" + new_program;
                    }
                    clear = rule.clear;
                    if (rule.pause) {
                        paused = true;
                        timeout(-1);
                    } else {
                        paused = false;
                    }
                }
                break;
            }

            // print status
            std::string status_text = "Score: " + std::to_string(score) + " Steps: " + std::to_string(steps);

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
                success = w.step(translated_key, score, &rule);
                if (success) {
                    ++steps;
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

    return err;
}
