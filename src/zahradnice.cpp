#include <ncurses.h>
#include <string.h>
#include <iostream>
#include "grammar.h"
#include <thread>
#include <chrono>

int main(int argc, char* argv[])
{
  if(argc < 2) {
    std::cout
       << "Usage: ./zahradnice <program.cfg> [<timestep>] [seed]"
       << std::endl;
    return 0;
  }

  std::string config;
  int seed = 123;
  int T = 0;

  {
    std::stringstream ss;
    std::for_each(argv + 1, argv + argc, [&ss](char * arg) { ss << arg << " "; });

    ss >> config;
    ss >> T;
    ss >> seed;
  }

  //start paused

  int score = 0;
  int steps = 0;
  bool success = true;
  bool paused = true;
  int elapsed = 0;
  bool started = false;

  srand(seed);
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

  Derivation w(cfg, row, col);
  w.start();

  char ch = ' ';
  char last = ' ';

  std::string rule;

  while(ch != 'q') {

    // print status

    std::ostringstream ss;
    ss << "Score: " << score << " Steps: " << steps;

    // average reward per step
    double reward = static_cast<float>(score)/(steps > 0 ? steps : 1);
    ss << " Skill: " << reward << std::endl;

    if(paused)
      mvprintw(0, 0, cfg.help.c_str());
    else
      mvprintw(0, 0, ss.str().c_str());
    mvprintw(0, col - rule.length() - 1, rule.c_str());

    ch = getch();

    //time lapse

    if(ch == ERR) {
      ch = 'T';
      elapsed += 1;
      if(elapsed % 100 == 0) {
        ch = 'B';
      }
    }

    //save CPU if no rule applicable

    if(!success && last == ch) {
      using namespace std::chrono_literals;
      std::this_thread::sleep_for(200ms);
    }

    const int MANY = 100;

    //restart scene

    if (ch == 'x') {
      paused = true;
      timeout(-1);
      w.restart();
      w.start();
    }

    //many steps without refresh

    else if (ch == 'F') {
      for(int i = 0; i < MANY; +i) {
        if(w.step(last, score, rule))
          ++steps;
      }
    }

    // toggle pause

    else if (ch == ' ') {
      paused = !paused;
      if(!paused) {
        timeout(T);
      } else {
        timeout(-1);
      }
    }

    // apply a single rule (counts as a step)

    else {
      success = w.step(ch, score, rule);
      if(success)
        ++steps;
      last = ch;
    }

    //refresh();
  }

  endwin();

  return 0;
}
