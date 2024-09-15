#include <ncurses.h>
#include <string.h>
#include <iostream>
#include "grammar.h"
#include <thread>
#include <chrono>
#include <ao/ao.h>
#include <math.h>
#include <sndfile.h>
#include <SDL2/SDL_mixer.h>
#include "sample.h"

int main(int argc, char* argv[])
{
  if(argc < 2) {
    std::cout
       << "Usage: ./zahradnice <program.cfg> [<timestep>] [seed]"
       << std::endl;
    return 0;
  }

  std::string config;
  int seed = 0;
  int T = 500;
  int M;

  {
    std::stringstream ss;
    std::for_each(argv + 1, argv + argc, [&ss](char * arg) { ss << arg << " "; });

    ss >> config;
    ss >> T;
    M = T/10;
    ss >> seed;
  }

  if (Mix_OpenAudio(44100, MIX_DEFAULT_FORMAT, 2, 1024) < 0) {
    // Error message if can't initialize
  }

  // Amount of channels (Max amount of sounds playing at the same time)
  Mix_AllocateChannels(32);

  int score = 0;
  int steps = 0;
  int errs = 0;
  bool success = true;
  bool paused = true;
  int elapsed = 0;
  int elapsed_m = 0;

  bool started = false;

  srand(seed || time(0));
  int row, col;

  initscr();
  start_color();
  raw();
  noecho();
  timeout(-1);
  curs_set(0);
  getmaxyx(stdscr, row, col);
  //typeahead(-1);

  //top row reserved as status line

  int x = row - 1;  int y = col/2;


  Grammar2D cfg;
  cfg.loadFromFile(config);

  std::unordered_map<char, sample> sounds;
  for(char c: cfg.sounds)
  {
    auto it = cfg.dict.find(c);
    if (it != cfg.dict.end())
    {
      sounds.insert(std::make_pair(c, sample(it->second, 100)));
    }
  }

  Derivation w(cfg, row, col);
  w.start();

  char ch = ' ';
  char last = ' ';

  Grammar2D::Rule rule;

  auto start = std::chrono::steady_clock::now();

  while(ch != 'q') {

    // play sound if any
    if(rule.sound != 0) {
      auto it = sounds.find(rule.sound);
      if(it != sounds.end())
      {
        it->second.play();
      }
    }
    // print status

    std::ostringstream ss;
    ss << "Score: " << score << " Steps: " << steps;

    // average reward per step
    double reward = static_cast<float>(score)/(steps > 0 ? steps : 1);
    ss << " Skill: " << reward;//<< std::endl;
    ss << " Errors: " << errs << std::endl;

    if(elapsed == 0)
      mvprintw(0, 0, cfg.help.c_str());
    else {
      mvprintw(0, 0, ss.str().c_str());
      mvprintw(0, col - rule.lhsa.length() - 1, rule.lhsa.c_str());
    }

    ch = getch();

    //time lapse
    //save CPU if no rule applicable

    if(!success && last == ch) {
      //std::this_thread
      //  ::sleep_for(
      //    std::chrono::milliseconds{1}
      //);
      ch = ERR;
    }


    if(ch == ERR) {
      ch = 'T';
      auto stop = std::chrono::steady_clock::now();
      std::chrono::duration<double, std::milli> duration = stop - start;
      int el = static_cast<int>(duration.count() / T);
      int el_m = static_cast<int>(duration.count() / M);
      if(el_m > elapsed_m) {
        ch = 'M';
        elapsed_m = el_m;
      }
      if(el > elapsed) {
        ch = 'B';
        elapsed = el;
      }
    }

    const int MANY = 100;

    //restart scene

    if (ch == 'x') {
      paused = true;
      timeout(0);
      w.restart();
      w.start();
    }

    // toggle pause

    else if (ch == ' ') {
      paused = !paused;
      if(!paused) {
        timeout(0);
      } else {
        timeout(-1);
      }
    }

    // apply a single rule (counts as a step)

    else {
      success = w.step(ch, score, &rule, errs);
      if(success)
        ++steps;
      last = ch;
    }

    //refresh();
  }

  endwin();

  return 0;
}
