#include "status.h"
#include <cwchar>

static std::wstring int_to_wstring(int value) {
    if (value == 0) return L"0";
    std::wstring result;
    bool neg = value < 0;
    if (neg) value = -value;
    while (value > 0) {
        result = static_cast<wchar_t>(L'0' + value % 10) + result;
        value /= 10;
    }
    if (neg) result = L"-" + result;
    return result;
}

static void replace_all(std::wstring& str,
                        const std::wstring& from, const std::wstring& to) {
    if (from.empty()) return;
    size_t pos = 0;
    while ((pos = str.find(from, pos)) != std::wstring::npos) {
        str.replace(pos, from.length(), to);
        pos += to.length();
    }
}

const wchar_t* const zg::kDefaultStatusTemplate =
    L"Score: {score} Steps: {steps} {parallel} {help}";

std::wstring zg::substitute_status_vars(std::wstring tmpl,
                                        int score, int steps, int batches, int moves,
                                        int parallel_pct,
                                        const std::wstring& help_text) {
    replace_all(tmpl, L"{score}", int_to_wstring(score));
    replace_all(tmpl, L"{steps}", int_to_wstring(steps));
    replace_all(tmpl, L"{batches}", int_to_wstring(batches));
    replace_all(tmpl, L"{moves}", int_to_wstring(moves));
    if (parallel_pct >= 0) {
        replace_all(tmpl, L"{parallel}", int_to_wstring(parallel_pct) + L"%");
    } else {
        replace_all(tmpl, L"{parallel}", L"");
    }
    replace_all(tmpl, L"{help}", help_text);
    return tmpl;
}

std::wstring zg::format_status_line(const Grammar2D& cfg,
                                     int score, int steps, int batches, int moves,
                                     int parallel_pct,
                                     const std::wstring& lhsa,
                                     int cols) {
    std::wstring tmpl = substitute_status_vars(
        cfg.help.empty() ? std::wstring(kDefaultStatusTemplate) : cfg.help,
        score, steps, batches, moves, parallel_pct, cfg.help_text);

    int rhs_w = wcswidth(lhsa.c_str(), lhsa.length());
    if (rhs_w < 0) rhs_w = static_cast<int>(lhsa.length());
    int max_left = cols - rhs_w - 1;
    if (max_left < 0) max_left = 0;

    if (static_cast<int>(tmpl.size()) > max_left) tmpl.resize(max_left);
    while (static_cast<int>(tmpl.size()) < max_left) tmpl.push_back(L' ');
    if (rhs_w > 0) {
        tmpl.push_back(L' ');
        tmpl += lhsa;
    }
    return tmpl;
}
