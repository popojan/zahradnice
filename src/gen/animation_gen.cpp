// animation_gen: minimal frame-flip-flop animation, generated via genlib.
// Goal: surface the API friction for sprite/animation programs (highnoon-style)
// before deciding what helpers genlib should grow.

#include "genlib.h"

#include <iostream>
#include <vector>

namespace g = genlib;

// Tiny "creature" anchored at the mouth cell (0,0). Head = 5 cells around;
// legs = 2 cells below. Frame A: legs `v v`. Frame B: legs `^ ^`.
// Anchor non-terminal flips Y <-> Z each step so the two transition rules
// are mutually exclusive on context.

static const std::vector<g::Cell> head_cells = {
    {-1, -1}, {-1, 0}, {-1, 1},
    { 0, -1},          { 0, 1},
};
static const std::vector<g::Cell> leg_cells = {{1, -1}, {1, 1}};

int main() {
    std::cout
        << "#! animate {parallel}\n"
        << "#help piku-blink: idle bob - SPACE pause - ESC quit\n"
        << "#timing T 600\n"
        << "#control ~ pause\n"
        << "^Acc\n\n";

    // Spawn: A on clear area -> Y, frame A drawn around it.
    {
        g::LhsPattern lhs;
        g::mark_each(lhs, head_cells, g::empty());
        g::mark_each(lhs, leg_cells,  g::empty());
        g::RhsPattern rhs;
        g::mark_each(rhs, head_cells, g::put(L'o'));
        g::mark_each(rhs, leg_cells,  g::put(L'v'));
        std::cout << g::emit_rule(g::header(L'A', L'T', g::put(L'Y')),
                                  g::emit_body_vertical(lhs, rhs)) << "\n\n";
    }

    // Y -> Z: legs v -> ^
    {
        g::LhsPattern lhs;
        g::mark_each(lhs, head_cells, g::lit(L'o'));
        g::mark_each(lhs, leg_cells,  g::lit(L'v'));
        g::RhsPattern rhs;
        g::mark_each(rhs, leg_cells,  g::put(L'^'));
        std::cout << g::emit_rule(g::header(L'Y', L'T', g::put(L'Z')),
                                  g::emit_body_vertical(lhs, rhs)) << "\n\n";
    }

    // Z -> Y: legs ^ -> v
    {
        g::LhsPattern lhs;
        g::mark_each(lhs, head_cells, g::lit(L'o'));
        g::mark_each(lhs, leg_cells,  g::lit(L'^'));
        g::RhsPattern rhs;
        g::mark_each(rhs, leg_cells,  g::put(L'v'));
        std::cout << g::emit_rule(g::header(L'Z', L'T', g::put(L'Y')),
                                  g::emit_body_vertical(lhs, rhs)) << "\n\n";
    }

    return 0;
}
