#pragma once

#include "display.h"

class CursesDisplay : public Display {
public:
    void put(int r, int c, wchar_t ch, int color_slot, int attrs) override;
    void register_pair(int slot, char fore, char back) override;
    void set_offset(int dr, int dc) override { offset_row = dr; offset_col = dc; }
    void clear() override;

private:
    int offset_row = 0;
    int offset_col = 0;
};
