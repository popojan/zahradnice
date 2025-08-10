#include <ncursesw/ncurses.h>
#include <locale.h>
#include <iostream>
#include "grammar.h"
#include <thread>
#include <chrono>
#include <cmath>
#include <SDL2/SDL_mixer.h>
#include "sample.h"
#include <sstream>
#include <algorithm>

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

    std::string config("programs/menu.cfg");
    int seed = 0;

    std::stringstream ss;
    std::for_each(argv + 1, argv + argc, [&ss](char *arg) { ss << arg << " "; });
    ss >> config;
    ss >> seed;

    if (Mix_OpenAudio(44100, MIX_DEFAULT_FORMAT, 2, 1024) < 0) {
        //cannot initialize sounds
    }

    Mix_AllocateChannels(32);

    int score = 0;
    int steps = 0;
    int errs = 0;
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

    while (config != "quit") {
        bool success = true;
        bool paused = true;
        int elapsed_t = 0;
        int elapsed_b = 0;
        int elapsed_m = 0;

        Grammar2D cfg;
        cfg.loadFromFile(config);

        std::unordered_map<wchar_t, sample> sounds;
        // load timing if defined
        int B = 500;
        int M = 50;
        int T = 0;
        auto it = cfg.dict.find(L'T'); {
            if (it != cfg.dict.end()) {
                std::string timing_str(it->second.begin(), it->second.end()); // Convert wstring to string
                std::stringstream ss(timing_str);
                ss >> B;
                ss >> M;
                ss >> T;
            }
        }

        // load sounds if defined
        for (wchar_t c: cfg.sounds) {
            auto it = cfg.dict.find(c);
            if (it != cfg.dict.end()) {
                std::string sound_path(it->second.begin(), it->second.end()); // Convert wstring to string
                sounds.insert(std::make_pair(c, sample(sound_path, 100)));
            }
        }

        getmaxyx(stdscr, row, col);

        //top row reserved as status line
        w.reset(cfg, row, col);
        if (clear) w.init();
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
                std::wstring lhsa_substr = rule.lhsa.substr(5);
                std::string lhsa_narrow(lhsa_substr.begin(), lhsa_substr.end());
                std::stringstream ss(lhsa_narrow);
                std::string new_program;
                ss >> new_program;
                if (new_program == "quit") {
                    config = new_program;
                } else {
                    std::stringstream nss;
                    nss << config.substr(0, config.rfind('/')) << "/" << new_program;
                    config = nss.str();
                    clear = rule.clear;
                    if (rule.pause)
                        timeout(-1);
                }
                break;
            }

            // print status
            std::ostringstream ss;
            ss << "Score: " << score << " Steps: " << steps;

            // average reward per step
            double reward = static_cast<float>(score) / (steps > 0 ? steps : 1);
            ss << " Skill: " << reward; //<< std::endl;
            ss << " Errors: " << errs << std::endl;

            if (elapsed_b == 0 || paused) {
                auto limit = std::min(static_cast<size_t>(col-1), cfg.help.size());
                std::wstring help_truncated = cfg.help;
                help_truncated.erase(limit, std::wstring::npos);
                mvaddwstr(0, 0, help_truncated.c_str());
            }
            else {
                auto limit = std::min(static_cast<size_t>(col-1), ss.str().size());
                mvprintw(0, 0, ss.str().erase(limit, std::string::npos).c_str());
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

            if (wch == L'x') {
                paused = true;
                timeout(-1);
                getmaxyx(stdscr, row, col);
                w.reset(cfg, row, col);
                w.init();
                w.start();
            }

            // toggle pause

            else if (wch == L' ') {
                paused = !paused;
                if (!paused) {
                    timeout(0);
                } else {
                    timeout(-1);
                }
            }

            // apply a single rule (counts as a step)

            else {
                rule.sound = 0;
                success = w.step(static_cast<wchar_t>(wch), score, &rule, errs);
                if (success) {
                    ++steps;
                }
                else if (wch == L'T') {
                    std::this_thread
                            ::sleep_for(
                                std::chrono::milliseconds{50}
                            );
                }
                last = wch;
            }

            //refresh();
        }
    }

    endwin();

    return 0;
}
