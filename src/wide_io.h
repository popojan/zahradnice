#ifndef WIDE_IO_H
#define WIDE_IO_H

#include <cstring>
#include <ios>
#include <locale>

// Program files are UTF-8 by definition (GRAMMAR.md), so every wide
// file stream must carry UTF-8 regardless of the process locale — the
// classic-locale codecvt dies on the first non-Latin-1 character and
// silently fail-states the stream (empty dumps). File encoding is a
// data-format contract, not an environment preference, so the facet is
// hand-rolled: <codecvt> is deprecated in C++17 and removed in C++20,
// while deriving from std::codecvt itself remains fully supported.
// Decoding never fails: malformed bytes become U+FFFD (the robust-parser
// philosophy), encoding sanitizes surrogates/out-of-range to U+FFFD.
class Utf8Codecvt : public std::codecvt<wchar_t, char, std::mbstate_t> {
public:
    explicit Utf8Codecvt(std::size_t refs = 0)
        : std::codecvt<wchar_t, char, std::mbstate_t>(refs) {}

protected:
    static int encode(unsigned long c, char *buf) {
        if (c >= 0xD800 && (c <= 0xDFFF || c > 0x10FFFF)) c = 0xFFFD;
        if (c < 0x80) { buf[0] = (char)c; return 1; }
        if (c < 0x800) {
            buf[0] = (char)(0xC0 | (c >> 6));
            buf[1] = (char)(0x80 | (c & 0x3F));
            return 2;
        }
        if (c < 0x10000) {
            buf[0] = (char)(0xE0 | (c >> 12));
            buf[1] = (char)(0x80 | ((c >> 6) & 0x3F));
            buf[2] = (char)(0x80 | (c & 0x3F));
            return 3;
        }
        buf[0] = (char)(0xF0 | (c >> 18));
        buf[1] = (char)(0x80 | ((c >> 12) & 0x3F));
        buf[2] = (char)(0x80 | ((c >> 6) & 0x3F));
        buf[3] = (char)(0x80 | (c & 0x3F));
        return 4;
    }

    // Decode one char at p (p < end). Returns bytes consumed and sets c;
    // 0 means incomplete tail (need more input).
    static int decode(const char *p, const char *end, unsigned long &c) {
        unsigned char b = (unsigned char)*p;
        int need;
        if (b < 0x80) { c = b; return 1; }
        else if ((b & 0xE0) == 0xC0) { need = 1; c = b & 0x1F; }
        else if ((b & 0xF0) == 0xE0) { need = 2; c = b & 0x0F; }
        else if ((b & 0xF8) == 0xF0) { need = 3; c = b & 0x07; }
        else { c = 0xFFFD; return 1; }
        if (end - p - 1 < need) return 0;
        for (int i = 1; i <= need; ++i) {
            unsigned char cb = (unsigned char)p[i];
            if ((cb & 0xC0) != 0x80) { c = 0xFFFD; return 1; }
            c = (c << 6) | (cb & 0x3F);
        }
        return need + 1;
    }

    result do_out(state_type &, const wchar_t *from, const wchar_t *from_end,
                  const wchar_t *&from_next, char *to, char *to_end,
                  char *&to_next) const override {
        while (from < from_end) {
            char buf[4];
            int n = encode((unsigned long)*from, buf);
            if (to_end - to < n) break;
            std::memcpy(to, buf, n);
            to += n;
            ++from;
        }
        from_next = from;
        to_next = to;
        return from == from_end ? ok : partial;
    }

    result do_in(state_type &, const char *from, const char *from_end,
                 const char *&from_next, wchar_t *to, wchar_t *to_end,
                 wchar_t *&to_next) const override {
        while (from < from_end && to < to_end) {
            unsigned long c;
            int n = decode(from, from_end, c);
            if (n == 0) break;  // incomplete sequence: wait for more bytes
            *to++ = (wchar_t)c;
            from += n;
        }
        from_next = from;
        to_next = to;
        return from == from_end ? ok : partial;
    }

    result do_unshift(state_type &, char *to, char *,
                      char *&to_next) const override {
        to_next = to;
        return ok;
    }

    int do_length(state_type &, const char *from, const char *end,
                  std::size_t max) const override {
        const char *p = from;
        std::size_t count = 0;
        while (p < end && count < max) {
            unsigned long c;
            int n = decode(p, end, c);
            if (n == 0) break;
            p += n;
            ++count;
        }
        return (int)(p - from);
    }

    bool do_always_noconv() const noexcept override { return false; }
    int do_encoding() const noexcept override { return 0; }
    int do_max_length() const noexcept override { return 4; }
};

inline void imbue_utf8(std::wios &s) {
    s.imbue(std::locale(s.getloc(), new Utf8Codecvt));
}

#endif
