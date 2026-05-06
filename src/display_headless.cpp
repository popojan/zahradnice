#include "display_headless.h"
#include <fstream>
#include <iostream>

HeadlessDisplay::HeadlessDisplay() {
    palette_.resize(65);  // slots 1..64
}

void HeadlessDisplay::resize(int rows, int cols) {
    rows_ = rows;
    cols_ = cols;
    grid_.assign(static_cast<size_t>(rows) * static_cast<size_t>(cols), Cell{});
}

void HeadlessDisplay::put(int r, int c, wchar_t ch, int color_slot, int attrs) {
    if (r < 0 || c < 0 || r >= rows_ || c >= cols_) return;
    grid_[static_cast<size_t>(r) * cols_ + c] = { ch, color_slot, attrs };
}

void HeadlessDisplay::register_pair(int slot, char fore, char back) {
    if (slot < 0 || slot >= static_cast<int>(palette_.size())) return;
    palette_[slot] = { fore, back };
}

void HeadlessDisplay::clear() {
    for (auto& cell : grid_) cell = Cell{};
}

// Engine reserves row 0 for the status line (writes go through wrap_row,
// which maps to rows 1..rows-1). At dump time we overlay the captured
// status string into row 0 — matches what ncurses screenshots show.
static std::wstring status_row(const std::wstring& s, int cols) {
    std::wstring out = s;
    if (static_cast<int>(out.size()) > cols) out.resize(cols);
    if (static_cast<int>(out.size()) < cols) out.append(cols - out.size(), L' ');
    return out;
}

void HeadlessDisplay::write_text(std::wostream& f) const {
    for (int r = 0; r < rows_; ++r) {
        std::wstring line;
        if (r == 0) {
            line = status_row(status_, cols_);
        } else {
            line.reserve(cols_);
            for (int c = 0; c < cols_; ++c) {
                wchar_t ch = grid_[r * cols_ + c].ch;
                line.push_back(ch == 0 ? L' ' : ch);
            }
        }
        size_t end = line.find_last_not_of(L' ');
        if (end != std::wstring::npos) line.resize(end + 1);
        else line.clear();
        f << line << L'\n';
    }
}

void HeadlessDisplay::write_ansi(std::wostream& f) const {
    auto emit_attrs = [&](int slot, int attrs) {
        f << L"\033[0m";
        if (slot > 0 && slot < static_cast<int>(palette_.size())) {
            char fg = palette_[slot].fore;
            char bg = palette_[slot].back;
            if (fg >= 0 && fg <= 7) f << L"\033[3" << static_cast<wchar_t>(L'0' + fg) << L"m";
            if (bg >= 0 && bg <= 7) f << L"\033[4" << static_cast<wchar_t>(L'0' + bg) << L"m";
        }
        if (attrs & zg::ATTR_BOLD) f << L"\033[1m";
        if (attrs & zg::ATTR_DIM)  f << L"\033[2m";
    };
    for (int r = 0; r < rows_; ++r) {
        if (r == 0) {
            f << L"\033[0m" << status_row(status_, cols_) << L"\033[0m\n";
            continue;
        }
        int prev_slot = -1, prev_attrs = -1;
        for (int c = 0; c < cols_; ++c) {
            const Cell& cell = grid_[r * cols_ + c];
            if (cell.slot != prev_slot || cell.attrs != prev_attrs) {
                emit_attrs(cell.slot, cell.attrs);
                prev_slot = cell.slot;
                prev_attrs = cell.attrs;
            }
            f << (cell.ch == 0 ? L' ' : cell.ch);
        }
        f << L"\033[0m\n";
    }
}

void HeadlessDisplay::dump_text(const std::string& path) const {
    if (path == "-") {
        write_text(std::wcout);
        std::wcout.flush();
        return;
    }
    std::wofstream f(path);
    if (!f) return;
    write_text(f);
}

void HeadlessDisplay::dump_ansi(const std::string& path) const {
    if (path == "-") {
        write_ansi(std::wcout);
        std::wcout.flush();
        return;
    }
    std::wofstream f(path);
    if (!f) return;
    write_ansi(f);
}
