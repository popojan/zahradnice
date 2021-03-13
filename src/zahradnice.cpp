#include <ncurses.h>                    /* ncurses.h includes stdio.h */
#include <string.h>
#include "hexgrid.h"

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

int main()
{
 char mesg[]="Just a string";           /* message to be appeared on the screen */
 int row,col;                           /* to store the number of rows and *
                                         * the number of colums of the screen */
 initscr();
 raw();
 noecho();
 curs_set(0);
 /* start the curses mode */
 getmaxyx(stdscr,row,col);              /* get the number of rows and columns */
 int x = row-6;//row/2;
 int y = (col-strlen(mesg))/2;

 start_color();                  /* Start color                  */
 init_pair(1, COLOR_YELLOW, COLOR_BLACK);
 init_pair(2, COLOR_BLUE, COLOR_BLACK);
 init_pair(3, COLOR_RED, COLOR_BLACK);
 init_pair(4, COLOR_CYAN, COLOR_BLACK);
 init_pair(5, COLOR_YELLOW, COLOR_BLUE);
 init_pair(6, COLOR_YELLOW, COLOR_BLACK);


  HexGrid grid2(1, 1, 0);
  for(int i = 0; i <= row; ++i)
    for(int j = 0; j < col/4; ++j)
      grid2.render(i, j);
 attron(COLOR_PAIR(6));

flower(x, y);
flower(x, y+17);
flower(x, y-11);

attroff(COLOR_PAIR(6));

 //mvprintw(row-2,0,"This screen has %d rows and %d columns\n",row,col);
 //printw("Try resizing your window(if possible) and then run this program again");
 refresh();
char ch = '\0';
int r = 5;
int c = 5;

attron(COLOR_PAIR(6));
grid2.render(r, c);
attroff(COLOR_PAIR(6));
getch(); 
while(ch != 'x') {
  ch = getch();
	int nr = r, nc = c;
	bool move = false;
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
  if(move && r >= 0 && c >= 0) {
 		nc -= (r % 2);
    attron(COLOR_PAIR(3));
    grid2.render(r, c);
    attroff(COLOR_PAIR(3));

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
