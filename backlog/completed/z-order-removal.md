# Z-Order Removal - COMPLETED

## Overview
✅ **COMPLETED**: Removed the z-order layering system from the Zahradnice grammar engine to simplify the codebase while maintaining core functionality.

## Implementation Status
- ✅ Z-order feature completely removed from engine
- ✅ Rule syntax simplified from 9 characters to 8 characters  
- ✅ All affected programs updated to new syntax
- ✅ System complexity reduced without breaking functionality

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

## Technical Changes Implemented

### Code Removed
- ✅ `Rule.zord` field removed from `grammar.h`
- ✅ `G.zord` field removed from `grammar.h` 
- ✅ Z-order parsing logic removed from `grammar.cpp`
- ✅ Z-order comparison removed from rule application logic
- ✅ Memory initialization updated to remove z-order field

### Simplifications Achieved
1. ✅ **Rule Structure**: 9th character removed from rule syntax (`=S1234567` instead of `=S12345678`)
2. ✅ **Memory**: Reduced `G` struct size by 1 byte per screen position
3. ✅ **Rendering**: Eliminated unnecessary z-order comparison check
4. ✅ **Grammar**: Simplified rule format documentation
5. ✅ **Score Parsing**: Updated to expect score/weight at position 10 instead of 11

### Programs Updated
The following programs were updated to use 8-character rule syntax:
- ✅ `programs/archived/arkanoid.cfg`
- ✅ `programs/flowers.cfg`
- ✅ `programs/highnoon.cfg` 
- ✅ `programs/maze.cfg`

## Benefits Realized
- ✅ **Simplicity**: Reduced cognitive load for grammar authors (8-char vs 9-char rules)
- ✅ **Performance**: Eliminated unnecessary comparisons during rendering  
- ✅ **Memory**: Reduced memory usage per screen position
- ✅ **Maintenance**: Less code to maintain and debug
- ✅ **Language Evolution**: Demonstrated maturity by removing early design decisions

## Design Philosophy Validation
This removal validates the principle that **language features should be driven by current needs, not legacy constraints**. The original Z-order feature was added to solve a specific problem in `flowers.cfg`, but as the language matured, better solutions emerged:

- **Memory system (`$`)** - More flexible state preservation
- **Rule weights** - Better probabilistic control  
- **Context matching** - More precise rule application

The current `flowers.cfg` demonstrates sophisticated layering effects using these mature features instead of Z-order, proving the removal was architecturally sound.

## Completion Status
✅ **FULLY IMPLEMENTED** - Z-order system completely removed, all programs updated, documentation revised.