#pragma once

#include <ncurses.h>
#include <cmath>

/**                
     __    __    __
    /71\__/73\__/75\__
    \  /62\__/64\__/66
    /51\__/53\__/55\__
    \__/42\_ /44\_ /46
 r  /31\  /33\__/35\__
    \__/22\__/24\__/26
 A  /11\__/13\__/15\__
 |  \__/  \__/  \__/  
 |       
 O----> c  HexGrid(1,1,0)

*/

class HexGrid {

public:
  HexGrid(int ry = 1, int rx = 1, int ex = 0, int flag = 0)
  : ry(ry), rx(rx), ex(ex), flag(flag) {
        
  }

  void render(int row, int col) {
    col *= 2*(ry + 2*rx + ex);
    col -= (row % 2) * (ry + 2*rx + ex);
    row *= ry;
    for(int r = row - 1; r < row + 2*ry; ++r) {
      int dx = std::abs(row + ry - r - 0.5) - 0.5;
      
      char L, R;
      if(r >= row + ry) {
        L = '\\'; R = '/';
      } else {
        R = '\\'; L = '/';
      }
      if ( r == row -1 || r == row + 2*ry - 1) {
        for(int c = col + dx; c < col + 2*ry + 2*rx + ex - dx; ++c) {
          mvaddch(r, c, '_' | flag );
        }
      }
      if(r > row - 1) {
        mvaddch(r, col + dx, L | flag );
        mvaddch(r, col + 2*ry + 2*rx + ex -dx - 1 , R | flag );
      }
    }
  }

private:
  const int ry, rx, ex;
  const int flag;
};
