# Z-Order Removal

## Overview
Remove the z-order layering system from the Zahradnice grammar engine to simplify the codebase while maintaining core functionality.

## Current State
- Z-order is implemented but **unused in current programs**
- Only backup programs (`programs.bak/flowers.cfg`, `programs.bak/maze.cfg`) contain z-order usage
- System adds complexity without providing value to existing games

### Photon System Analysis (programs/flowers.cfg)
The current `programs/flowers.cfg` (original "zahradnice" program) implements a complex photon system using the `f` non-terminal for yellow diagonal-flowing symbols. All photon rules use memory restoration (`$`) instead of z-order layering:

**Basic photon rule:**
- `==ff$` - photon restores from memory

**Timed photon movement and interactions:**
- `==fT$38C`, `==fT$38M`, `==fT$38.` - photon moves through different symbols
- `==fT$38g`, `==fT$38p`, `==fT$38H`, `==fT$38ff` - photon interactions

**Photon-obstacle interactions:**
- `==fT$30#`, `==fT$30X`, `==fT$30A` - photon hits walls/obstacles

**Directional photon movement:**
- `==fT$38|f`, `==fT$38\f`, `==fT$38/f` - diagonal/vertical movement
- `==fT$38_f`, `==fT$38-f`, `==fT$38~f` - horizontal movement

**Colored photon spawning:**
- `==fT$10w1b`, `==fT$30w2b`, `==fT$40w3b`, `==fT$50w4b` - spawn photons in different colors

This demonstrates that **complex visual layering effects are achieved through the memory system alone**, confirming z-order is unnecessary for sophisticated animations.

## Technical Impact

### Code to Remove
- `Rule.zord` field in `grammar.h:59`
- `G.zord` field in `grammar.h:98` 
- Z-order parsing in `grammar.cpp:161-164`
- Z-order comparison in `grammar.cpp:418`
- Memory initialization in `grammar.cpp:327`

### Simplifications
1. **Rule Structure**: Remove 9th character from rule syntax
2. **Memory**: Reduce `G` struct size by 1 byte per screen position
3. **Rendering**: Eliminate z-order comparison check
4. **Grammar**: Simplify rule format documentation

### Breaking Changes
- Rule syntax changes from `=<sound><nonterminal><trigger><replacement><colors><context><z-order>` to `=<sound><nonterminal><trigger><replacement><colors><context>`
- Backup programs using z-order would need updates (minimal impact)

## Benefits
- **Simplicity**: Reduces cognitive load for grammar authors
- **Performance**: Eliminates unnecessary comparisons during rendering
- **Memory**: Slightly reduces memory usage per screen position
- **Maintenance**: Less code to maintain and debug

## Alternatives Considered
1. **Keep as-is**: Maintains unused complexity
2. **Document only**: Doesn't address simplification goal
3. **Make optional**: Adds conditional complexity

## Recommendation
**Proceed with removal** - aligns with simplicity goals and eliminates unused feature.