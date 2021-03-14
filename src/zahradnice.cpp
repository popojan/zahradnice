#include <ncurses.h>
#include <string.h>
#include "hexgrid.h"
#include "kvetina.h"
#include <iostream>
#include "cfg2d.h"

int main(int argc, char* argv[])
{
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

  Derivation w(cfg);
  w.start(row-2,col/2);

  char ch = ' ';
  while(ch != 'q') {
    ch = getch();

    if (ch == ' ') {
      w.step();
      refresh();
    }
    else if (ch == 'n') {
      w.start(row-2,rand() % col);
      refresh();
    }
  }
  endwin();
  return 0;
}
