#include <ncurses.h>                    /* ncurses.h includes stdio.h */
#include <string.h>
#include "hexgrid.h"
#include "kvetina.h"
#include <iostream>
#include "cfg2d.h"

void flower(int x, int y) {

 attron(COLOR_PAIR(1));

 mvaddch(x+3, y+1, '|' | A_BOLD);
 mvaddch(x-1, y+1, '|' | A_BOLD);
 mvaddch(x, y+0, ' ' | A_BOLD);
 mvaddch(x, y+1, '|' | A_BOLD);
 mvaddch(x, y+2, ' ' | A_BOLD);
 mvaddch(x+1, y, '\\' | A_BOLD);
 mvaddch(x+1, y+1, '|' | A_BOLD);
 mvaddch(x+1, y+2, '/' | A_BOLD);
 mvaddch(x+2, y+1, '|' | A_BOLD);
 attron(COLOR_PAIR(3));
 mvaddch(x, y-1, 'O' | A_BOLD);
 attron(COLOR_PAIR(4));
 mvaddch(x, y+3, 'X' | A_BOLD);
 attron(COLOR_PAIR(2));
 mvaddch(x-2, y+1, 'W' | A_BOLD);

}

std::pair<int, int> origin(char s, const std::string& rhs) {
  int r = 0;
  int c = 0;
  for(const char * p = rhs.c_str(); *p != '\0'; ++p, ++c) {
    if(*p == '\n') {
      ++r;
      c = -1;
    }
    else if(*p == s - 0x20) {
      return std::pair<int, int>(r, c);
    }
  }
  return std::pair<int, int>(-1,-1);
} 

void apply(int ro, int co, const std::string& s) {
  int r = ro;
  int c = co;
  for(const char * p = s.c_str(); *p != '\0'; ++p) {
    if(*p == '\n') {
      ++r;
      c = co;
    }
    mvaddch(r, c, *p);
  }
}




int main()
{
  int row, col;
  initscr();
  raw();
  noecho();
  curs_set(0);
  getmaxyx(stdscr, row, col);

  int x = row - 1;
  int y = col/2;

  start_color();
  
  ContextFreeGrammar2D cfg('s', "xlr");
  cfg.addRule('s', "x\nS");
  cfg.addRule('x', "|\nx\nX");
  cfg.addRule('x', "\\\nx\n X");
  cfg.addRule('x', "/\n x\nX");
  cfg.addRule('x', "|\nx   x\n \\_/ \n  X");
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

  init_pair(1, COLOR_YELLOW, COLOR_BLACK);
  init_pair(2, COLOR_BLUE, COLOR_BLACK);
  init_pair(3, COLOR_RED, COLOR_BLACK);
  init_pair(4, COLOR_CYAN, COLOR_BLACK);
  init_pair(5, COLOR_YELLOW, COLOR_BLUE);
  init_pair(6, COLOR_YELLOW, COLOR_BLACK);
  init_pair(7, COLOR_BLACK, COLOR_BLACK);


  HexGrid grid2(1, 1, 0, A_BOLD);
  attron(COLOR_PAIR(6));

  //flower(x, y);
  //flower(x, y+17);
  //flower(x, y-11);

  attroff(COLOR_PAIR(6));

  refresh();
  char ch = '\0';
  int r = 5;
  int c = 5;

  attron(COLOR_PAIR(6));
  grid2.render(r, c);
  attroff(COLOR_PAIR(6));
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
    if(move && r >= 0 && c >= 0) {
      nc -= (r % 2);
      attron(COLOR_PAIR(cid));
      grid2.render(r, c);
      attroff(COLOR_PAIR(cid));

      attron(COLOR_PAIR(6));
      grid2.render(nr, nc);
      attroff(COLOR_PAIR(6));
      c = nc;
      r = nr;
      refresh();
    }
  }
  endwin();
  return 0;
}
