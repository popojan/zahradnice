#pragma once

#include "display.h"
#include <vector>
#include <string>
#include <iosfwd>

class HeadlessDisplay : public Display {
public:
    HeadlessDisplay();
    void resize(int rows, int cols);

    void put(int r, int c, wchar_t ch, int color_slot, int attrs) override;
    void register_pair(int slot, char fore, char back) override;
    void clear() override;

    void set_status(const std::wstring& s) { status_ = s; }

    int rows() const { return rows_; }
    int cols() const { return cols_; }

    void dump_text(const std::string& path) const;
    void dump_ansi(const std::string& path) const;

private:
    void write_text(std::wostream& f) const;
    void write_ansi(std::wostream& f) const;

    int rows_ = 0;
    int cols_ = 0;
    struct Cell { wchar_t ch = L' '; int slot = 0; int attrs = 0; };
    std::vector<Cell> grid_;
    struct Pair { char fore = 7; char back = 0; };
    std::vector<Pair> palette_;
    std::wstring status_;
};
