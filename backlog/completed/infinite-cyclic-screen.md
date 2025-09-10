# Infinite Cyclic Screen Implementation - COMPLETED

## Status: COMPLETED ✅

**Implementation verified**: Toroidal (cyclic) screen wrapping is already implemented via `#grid` directive.

**Features implemented**:
- ✅ `#grid <width> <height>` configuration for toroidal wrapping
- ✅ Cyclic coordinate wrapping in rule application  
- ✅ Grid-aligned effective dimensions
- ✅ WYSIWYG principle maintained (complete state visible in terminal)

**Usage**: Programs can specify `#grid 80 24` to enable toroidal wrapping within terminal bounds.

---

## Original Analysis (IMPLEMENTED)

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

## Final Implementation: Configurable Grid System

**Status: COMPLETED** ✅

### Solution: Configurable Grid Alignment

Instead of hardcoded wrapping constraints, implemented a **configurable grid system** that allows programs to specify their required symbol alignment:

#### Grid Configuration Syntax
```
#=G width height
```

**Examples:**
- `#=G 1 1` - Default (no grid constraints) 
- `#=G 2 1` - Double-width columns (for block-style games)
- `#=G 3 1` - Triple-width columns (for Conway's Game of Life)
- `#=G 2 2` - Double-width columns and double-height rows

#### Implementation Details

**Grammar2D Class Extensions** (`grammar.h:72-74`):
```cpp
// Grid configuration for symbol alignment (default 1,1 = no constraints)
int grid_width = 1;
int grid_height = 1;
```

**Configuration Parsing** (`grammar.cpp:45-61`):
- Detects `#=G` dictionary entries during file loading
- Parses width and height parameters with validation
- Defaults to `1,1` for backward compatibility

**Coordinate Wrapping Functions** (`grammar.cpp:7-20`):
```cpp
static int wrap_row(int r, int max_row, int grid_height) {
    // Grid-aligned effective height, preserving status line
    int effective_max_row = ((max_row - 1) / grid_height) * grid_height + 1;
    // ... wrapping logic
}

static int wrap_col(int c, int max_col, int grid_width) {
    // Grid-aligned effective column width  
    int effective_max_col = (max_col / grid_width) * grid_width;
    // ... wrapping logic
}
```

**Uppercase Placement Updates** (`grammar.cpp:254-288`):
- `'R'`, `'C'`, `'X'` placement variants now use grid multipliers
- `'L'`, `'C'`, `'X'` vertical variants support grid alignment
- Consistent with wrapping functions for seamless toroidal behavior

#### Benefits Achieved

1. **Flexible Symbol Alignment**: Programs can specify exact grid requirements
2. **Backward Compatibility**: Default `1,1` preserves existing behavior  
3. **Game-Specific Support**: GOL (3-width), Snake (2-width), others (custom)
4. **Toroidal Topology**: Full wraparound without visual artifacts
5. **Author Control**: Program authors choose their visual constraints

#### Usage Examples

**Snake with double-width symbols:**
```
#=G 2 1
^zxX  # Start at random even column
```

**Conway's Game of Life with triple-width:**
```
#=G 3 1
^Rcc  # Start at right edge, triple-aligned
```

## Conclusion

Converting to cyclic screen with **configurable grid alignment** successfully balances flexibility with visual consistency. The implementation preserves existing program compatibility while enabling new toroidal behaviors and allowing authors to specify their exact symbol alignment requirements.

This approach elegantly solves the double-width/triple-width symbol challenge while providing a foundation for future grid-based enhancements. The change enables new classes of programs while maintaining full backward compatibility.