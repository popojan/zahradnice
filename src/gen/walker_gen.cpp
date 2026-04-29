// walker_gen: minimal sprite animation generated via genlib's art loader.
// Demonstrates parse_art / art_lhs / art_rhs / art_frame_diff at honest scale.
// Compare with animation_gen.cpp which uses programmatic cell lists.

#include "genlib.h"

#include <iostream>

namespace g = genlib;

// Frames are written as ASCII art. The '@' marker is the anchor cell
// (becomes (0, 0) in the pattern); spaces are no-cell. Both frames must
// agree on the anchor location.

static const std::string frame_A = R"( ___
( @ )
 / \)";

static const std::string frame_B = R"( ___
( @ )
 \ /)";

int main() {
    std::cout
        << "#! walker {parallel}\n"
        << "#help walker: idle bob - SPACE pause - ESC quit\n"
        << "#timing T 600\n"
        << "#control ~ pause\n"
        << "^Acc\n\n";

    // Spawn: A on a clear area -> Y, draw frame A around it.
    {
        auto art = g::parse_art(frame_A);
        g::LhsPattern lhs;
        for (auto& kv : art) lhs[kv.first] = g::empty();
        g::RhsPattern rhs = g::art_rhs(frame_A);
        std::cout << g::emit_rule(g::header(L'A', L'T', g::put(L'Y')),
                                  g::emit_body_vertical(lhs, rhs)) << "\n\n";
    }

    // Y -> Z: minimum-rule diff between the two frames.
    {
        auto d = g::art_frame_diff(frame_A, frame_B);
        std::cout << g::emit_rule(g::header(L'Y', L'T', g::put(L'Z')),
                                  g::emit_body_vertical(d.lhs, d.rhs)) << "\n\n";
    }

    // Z -> Y: reverse diff.
    {
        auto d = g::art_frame_diff(frame_B, frame_A);
        std::cout << g::emit_rule(g::header(L'Z', L'T', g::put(L'Y')),
                                  g::emit_body_vertical(d.lhs, d.rhs)) << "\n\n";
    }

    return 0;
}
