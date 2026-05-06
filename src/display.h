#pragma once

#include <cwchar>

namespace zg {
    enum Attr : int {
        ATTR_BOLD = 1 << 0,
        ATTR_DIM  = 1 << 1,
    };
}

class Display {
public:
    virtual ~Display() = default;

    virtual void put(int r, int c, wchar_t ch, int color_slot, int attrs) = 0;

    virtual void register_pair(int slot, char fore, char back) {}

    virtual void set_offset(int dr, int dc) {}

    virtual void clear() {}
};
