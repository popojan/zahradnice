#include <ncurses.h>
#include <string.h>
#include "hexgrid.h"
#include "kvetina.h"
#include <iostream>
#include "cfg2d.h"

int main(int argc, char* argv[])
{
  int numKeyPress = 0;
  int score = 0;

  srand(time(NULL));
  int row, col;
  initscr();
  raw();
  noecho();
  curs_set(0);
  getmaxyx(stdscr, row, col);

  int x = row - 1;
  int y = col/2;

  start_color();
  
  ContextFreeGrammar2D cfg('s', "xmlr");
  
  std::string config("basic.cfg");
  if(argc > 1) {
    config  = std::string(argv[1]);
  }
  cfg.loadFromFile(config);

  Derivation w(cfg, row, col);
  w.start(row-2,col/2);

  char ch = ' ';
  while(ch != 'q') {
    ch = getch();
    ++numKeyPress;

    if (ch == 'n') {
      w.start(row-2,rand() % col);
    }
    else if (ch == 'x') {
      //numKeyPress = 0;
      //score = 0;
      w.restart();
      w.start(row-2,col/2);
    }
    else {
      score += w.step(ch);
    }

    std::ostringstream ss;
    ss << "Score: " << score << " Steps: " << numKeyPress;
    ss << " Skill: " << (static_cast<float>(score)/(numKeyPress > 0 ? numKeyPress : 1)) << std::endl;
    mvprintw(1,1,ss.str().c_str());
    refresh();
  }
  endwin();
  return 0;
}
