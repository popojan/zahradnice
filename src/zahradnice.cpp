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

        std::unordered_map<char, sample> sounds;
        // load timing if defined
        int B = 500;
        int M = 50;
        int T = 0;
        auto it = cfg.dict.find('T'); {
            if (it != cfg.dict.end()) {
                std::stringstream ss(it->second);
                ss >> B;
                ss >> M;
                ss >> T;
            }
        }

        // load sounds if defined
        for (char c: cfg.sounds) {
            auto it = cfg.dict.find(c);
            if (it != cfg.dict.end()) {
                sounds.insert(std::make_pair(c, sample(it->second, 100)));
            }
        }

        getmaxyx(stdscr, row, col);

        //top row reserved as status line
        w.reset(cfg, row, col);
        if (clear) w.init();
        w.start();

        char ch = ' ';
        char last = ' ';

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
                std::stringstream ss(rule.lhsa.substr(5));
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
                mvprintw(0, 0, cfg.help.erase(limit, std::string::npos).c_str());
            }
            else {
                auto limit = std::min(static_cast<size_t>(col-1), ss.str().size());
                mvprintw(0, 0, ss.str().erase(limit, std::string::npos).c_str());
                limit = std::min(static_cast<size_t>(col-1), rule.lhsa.size());
                mvprintw(0, col - rule.lhsa.erase(limit, std::string::npos).length() - 1, rule.lhsa.c_str());
            }

            ch = getch();

            //time lapse
            //save CPU if no rule applicable
            if (!success && last == ch) {
                ch = ERR;
            }

            if (ch == ERR) {
                ch = 0;
                auto stop = std::chrono::steady_clock::now();
                std::chrono::duration<double, std::milli> duration = stop - start;
                int el_t = T > 0 ? static_cast<int>(duration.count() / T) : elapsed_t + 1;
                int el_b = static_cast<int>(duration.count() / B);
                int el_m = static_cast<int>(duration.count() / M);
                if (el_t > elapsed_t) {
                    ch = 'T';
                    elapsed_t = el_t;
                }
                if (el_m > elapsed_m) {
                    ch = 'M';
                    elapsed_m = el_m;
                }
                if (el_b > elapsed_b) {
                    ch = 'B';
                    elapsed_b = el_b;
                }
            }

            //restart scene

            if (ch == 'x') {
                paused = true;
                timeout(-1);
                getmaxyx(stdscr, row, col);
                w.reset(cfg, row, col);
                w.init();
                w.start();
            }

            // toggle pause

            else if (ch == ' ') {
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
                success = w.step(ch, score, &rule, errs);
                if (success) {
                    ++steps;
                }
                else if (ch == 'T') {
                    std::this_thread
                            ::sleep_for(
                                std::chrono::milliseconds{50}
                            );
                }
                last = ch;
            }

            //refresh();
        }
    }

    endwin();

    return 0;
}
