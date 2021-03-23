#include <ncurses.h>
#include <string.h>
#include <iostream>
#include "grammar.h"
#include <thread>
#include <chrono>

int main(int argc, char* argv[])
{
  int numKeyPress = 0;
  int score = 0;
  bool success = true;
  bool paused = false;
  std::istringstream iss(argv[2]);
  int seed = 131;
  iss >> seed;
  iss.clear();
  iss.str(argv[3]);
  int tout = -1;
  iss >> tout;
  srand(seed);//time(NULL));
  int row, col;
  initscr();
  start_color();
  raw();
  noecho();
  //nodelay(stdscr, true);
  timeout(tout);
  curs_set(0);
  getmaxyx(stdscr, row, col);
  typeahead(-1);
  int x = row - 1;
  int y = col/2;

  Grammar2D cfg('s', "xmlr");

  std::string config("basic.cfg");
  if(argc > 1) {
    config  = std::string(argv[1]);
  }
  cfg.loadFromFile(config);

  Derivation w(cfg, row, col);
  w.start();

  char ch = ' ';
  char last = ' ';
  while(ch != 'q') {
    ch = getch();

    if(ch == ERR) {
      ch = 'T';
    }
    if(!success && last == ch) {
      using namespace std::chrono_literals;
      std::this_thread::sleep_for(200ms);
    }
    if (ch == 'x') {
      w.restart();
      w.start();
    }
    else if (ch == 'F') {
      for(int i = 0; i < 100;++i) {
        if(w.step(last, score))
          ++numKeyPress;
      }
    }
    else if (ch == ' ') {
      paused = !paused;
      if(!paused) {
        timeout(tout);
      } else {
        timeout(-1);
      }
    }
    else {
      success = w.step(ch, score);
      if(success)
        ++numKeyPress;
      last = ch;
    }
    std::ostringstream ss;
    ss << "Score: " << score << " Steps: " << numKeyPress;
    ss << " Skill: " << (static_cast<float>(score)/(numKeyPress > 0 ? numKeyPress : 1)) << std::endl;
    mvprintw(0,0,ss.str().c_str());
    refresh();
  }
  endwin();
  return 0;
}
