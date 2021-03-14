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

  std::unordered_map<char, std::vector<std::string> > rules;
  
  rules['s'] = {{"x\nS"}};
  rules['x'] = {{"x\n|\nX"}};
  rules['x'] = {{"x\n|\nX"}};

  struct NonTerminal {
    char s;
    int r;
    int c;
  };

  std::vector<NonTerminal> nt;

  nt.push_back({'s', row - 2, col/2});

  int i = (random() % nt.size());
  auto n = nt[i];
  mvaddch(n.r, n.c, n.s);

  HexGrid grid2(1, 1, 0, A_BOLD);

  //flower(x, y);
  //flower(x, y+17);
  //flower(x, y-11);


  refresh();
  char ch = '\0';
  int r = 5;
  int c = 5;

  grid2.render(r, c);
  int cid = 7;

  //Kvetina kytka(row - 1, col/2);
  //kytka.render();
  while(ch != 'x') {
    ch = getch();
    int nr = r, nc = c;
    bool move = false;

    if(ch == '1') {
      cid = 2;
    } else if(ch == '2') {
      cid = 3;
    } 
    else if(ch == '3') {
      cid = 7;
    } 
    if(ch == 'q') {
      nr -= 1;
      move = true;
    }
    else if (ch == 'e') {
      nr -=1;
    nc += 1;
      move = true;
    }
    else if(ch == 'w') {
          nc += (r % 2);
     nr -= 2;
      move = true;
    }
    else if(ch == 'd') {
      move = true;
     nr += 1;
      nc += 1;
    }
    else if(ch == 's') {
      move = true;
          nc += (r % 2);
    nr += 2;
    }
    else if(ch == 'a') {
      move = true;
    nr += 1;
    }
    else if (ch == ' ') {
      w.step();
    }
    else if (ch == 'n') {
      w.start(row-2,rand() % col);
      
    }
    if(move && r >= 0 && c >= 0) {
      nc -= (r % 2);
      grid2.render(r, c);

      grid2.render(nr, nc);
      c = nc;
      r = nr;
      refresh();
    }
  }
  endwin();
  return 0;
}
