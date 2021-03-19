#include <ncurses.h>
#include <string.h>
#include "hexgrid.h"
#include "kvetina.h"
#include <iostream>
#include "cfg2d.h"
#include <thread>
#include <chrono>

int main(int argc, char* argv[])
{
  int numKeyPress = 0;
  int score = 0;

  srand(time(NULL));
  int row, col;
  initscr();
  start_color();
  raw();
  noecho();
  //nodelay(stdscr, true);
  timeout(10);
  curs_set(0);
  getmaxyx(stdscr, row, col);

  int x = row - 1;
  int y = col/2;

  
  ContextFreeGrammar2D cfg('s', "xmlr");
  
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
      //using namespace std::chrono_literals;
      //std::this_thread::sleep_for(200ms);
    }

    if (ch == 'x') {
      //numKeyPress = 0;
      //score = 0;
      w.restart();
      w.start();
    }
    else if (ch == 'F') {
      for(int i = 0; i < 100;++i) {
        if(w.step(last, score))
          ++numKeyPress;
      }
    } else {
      if(w.step(ch, score))
        ++numKeyPress;
      //else if (ch != 'T') //to dangerous
      //  ungetch(ch);
      last = ch;
    }
    //std::ostringstream ss;
    //ss << "Score: " << score << " Steps: " << numKeyPress;
    //ss << " Skill: " << (static_cast<float>(score)/(numKeyPress > 0 ? numKeyPress : 1)) << std::endl;
    //mvprintw(0,0,ss.str().c_str());
    //refresh();
  }
  endwin();
  return 0;
}
