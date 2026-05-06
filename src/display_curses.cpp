#include "display_curses.h"
#include <ncursesw/ncurses.h>

static int translate_attrs(int e) {
    int a = 0;
    if (e & zg::ATTR_BOLD) a |= A_BOLD;
    if (e & zg::ATTR_DIM)  a |= A_DIM;
    return a;
}

void CursesDisplay::put(int r, int c, wchar_t ch, int color_slot, int attrs) {
    cchar_t cchar;
    wchar_t wch[2] = { ch, 0 };
    setcchar(&cchar, wch, translate_attrs(attrs), static_cast<short>(color_slot), NULL);
    mvadd_wch(r + offset_row, c + offset_col, &cchar);
}

void CursesDisplay::register_pair(int slot, char fore, char back) {
    init_pair(slot, fore, back);
}

void CursesDisplay::clear() {
    ::clear();
}
