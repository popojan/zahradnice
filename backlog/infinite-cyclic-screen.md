# Infinite Cyclic Screen Implementation

## Overview

Replace the current bounded screen (with `#` boundary detection) with a **toroidal/cyclic screen** where coordinates wrap around modulo the screen dimensions. Objects disappearing on one edge immediately appear on the opposite edge, and context matching wraps around cyclically.

## Current Bounded System

**Boundary Detection:** `grammar.cpp:357-360`
```cpp
char ctx = '#';
if (r > 0 && r < row && c >= 0 && c < col) {
    ctx = mvinch(r, c);
    if (ctx == ' ') ctx = '~';
}
```

**Coordinate Constraints:** `grammar.cpp:397`
```cpp
if (rep != ' ' && r > 0 && r < row && c >= 0 && c < col) {
```

## Proposed Cyclic System

### Core Coordinate Wrapping

Replace boundary checks with modulo arithmetic:

```cpp
// Helper functions for coordinate wrapping
int wrap_row(int r, int max_row) {
    return ((r % max_row) + max_row) % max_row;
}

int wrap_col(int c, int max_col) {
    return ((c % max_col) + max_col) % max_col;
}
```

### Key Changes Required

#### 1. Context Checking (`dryapply` function)

**Current:** `grammar.cpp:357-360`
```cpp
char ctx = '#';
if (r > 0 && r < row && c >= 0 && c < col) {
    ctx = mvinch(r, c);
    if (ctx == ' ') ctx = '~';
}
```

**New:**
```cpp
// Wrap coordinates cyclically
int wrapped_r = wrap_row(r, row);
int wrapped_c = wrap_col(c, col);

// Always get context from wrapped position (no '#' boundaries)
char ctx = mvinch(wrapped_r, wrapped_c);
if (ctx == ' ') ctx = '~';
```

#### 2. Rule Application (`apply` function)

**Current:** `grammar.cpp:397`
```cpp
if (rep != ' ' && r > 0 && r < row && c >= 0 && c < col) {
```

**New:**
```cpp
if (rep != ' ') {
    int wrapped_r = wrap_row(r, row);
    int wrapped_c = wrap_col(c, col);
    
    // Always apply to wrapped coordinates
```

#### 3. Symbol Storage (Derivation::x map)

**Current:** Direct coordinate storage in `std::unordered_map<std::pair<int, int>, char>`

**Challenge:** Wrapped coordinates mean multiple logical positions can map to same screen position

**Solution:** Store using wrapped coordinates consistently:
```cpp
// When storing symbols
int wrapped_r = wrap_row(r, row);
int wrapped_c = wrap_col(c, col);
x[std::pair<int, int>(wrapped_r, wrapped_c)] = symbol;
```

#### 4. Memory System (`memory` array)

**Current:** `col * r + c` indexing assumes bounded coordinates

**New:** Use wrapped coordinates for memory indexing:
```cpp
int wrapped_r = wrap_row(r, row);
int wrapped_c = wrap_col(c, col);
memory[col * wrapped_r + wrapped_c]
```

#### 5. Status Line Positioning

**Current:** Top row (r=0) reserved for status display

**Impact:** Status line would participate in vertical wrapping

**Solutions:**
- **Option A:** Exclude row 0 from wrapping (wrap_row range: 1 to row-1)
- **Option B:** Move status to separate ncurses window/panel
- **Option C:** Overlay status on game area without affecting coordinates

#### 6. Symbol Positioning (`start` function)

**Current:** `grammar.cpp:221-256` - Positions based on screen edges

**Impact:** Edge positions (l/r, u/l) need redefinition in cyclic space

**Minimal Change:** Keep existing positioning logic - edges are still meaningful as starting positions

## Grammar Language Impact

### Special Character Changes

- **Remove `#` boundary detection** - No longer needed
- **Keep other special chars** (`?`, `*`, `$`, `~`) - Unchanged functionality

### New Opportunities

Programs can now implement:
- **Wraparound movement** patterns
- **Infinite scrolling** effects  
- **Toroidal cellular automata** (Conway's Life gliders fly forever)
- **Seamless world boundaries** for games

## Implementation Strategy

### Phase 1: Core Coordinate Wrapping
1. Add `wrap_row` and `wrap_col` helper functions
2. Modify `dryapply` context checking to use wrapped coordinates
3. Modify `apply` rule application to use wrapped coordinates
4. Update memory indexing to use wrapped coordinates

### Phase 2: Data Structure Consistency
1. Ensure `Derivation::x` map uses wrapped coordinates consistently
2. Update symbol positioning and storage logic
3. Handle status line positioning (choose solution A/B/C)

### Phase 3: Testing and Validation
1. Test basic wraparound with simple programs
2. Verify context matching works across boundaries
3. Test memory system with wrapped coordinates
4. Validate existing programs still work correctly

### Phase 4: Demonstration Programs
1. **Wraparound Conway's Life** - Gliders can fly forever
2. **Cyclic Snake** - Snake wraps around edges
3. **Toroidal patterns** - Demonstrate seamless boundaries
4. **Bounded screen emulator** - Show how to recreate old behavior with border symbols

## Backward Compatibility

### Maintaining Bounded Behavior

For programs requiring bounded screens:
1. **Border symbol approach:** Place wall symbols around screen edges in initial setup
2. **New demo program:** `bounded-screen-emulation.cfg` showing how to recreate `#` behavior
3. **Rule patterns:** Standard patterns for creating impermeable boundaries

### Migration Path

1. **Default behavior change:** Switch to cyclic by default
2. **Existing programs:** Most continue working, some gain new capabilities
3. **Documentation update:** Update GRAMMAR.md to remove `#` references
4. **Demo programs:** Add cyclic-specific examples

## Technical Considerations

### Performance Impact
- **Minimal:** Modulo operations are fast
- **Memory:** Same memory usage pattern
- **Rendering:** Same ncurses calls, just wrapped coordinates

### Edge Cases
1. **Very small screens:** Wrap logic must handle row=1, col=1 cases
2. **Negative coordinates:** Modulo arithmetic handles correctly with proposed formula
3. **Context patterns:** Large context patterns may wrap multiple times

### Testing Requirements
1. **Unit tests:** Coordinate wrapping edge cases
2. **Integration tests:** Existing programs functionality
3. **Visual tests:** Wraparound behavior verification
4. **Performance tests:** Ensure no significant slowdown

## Benefits

### For Games
- **Snake:** Natural wraparound movement
- **Conway's Life:** True toroidal topology
- **Tetris:** Side-wraparound possible
- **Artistic programs:** Seamless pattern generation

### For Engine
- **Simplified logic:** No special boundary handling
- **Mathematical elegance:** Toroidal topology is cleaner
- **New possibilities:** Enables new classes of programs
- **Consistent behavior:** No special cases for edges

## Conclusion

Converting to cyclic screen is a **moderate complexity change** with **high impact benefits**. The main implementation work involves systematic replacement of boundary checks with coordinate wrapping, ensuring data structure consistency, and handling the status line positioning.

The change enables new classes of programs while maintaining compatibility with most existing ones, representing a significant enhancement to the engine's capabilities.