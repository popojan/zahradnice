# Infinite Screen with Sparse Grid Implementation - REJECTED

## Status: REJECTED

**Decision**: Rejected in favor of toroidal (cyclic) screen system already implemented.

**Rationale**: 
- **WYSIWYG Principle**: Users should see the complete game state within terminal bounds
- **Infinite complexity**: Infinite screen adds viewport management, scrolling, and performance complexity  
- **Toroidal superiority**: Current `#grid` directive provides elegant cyclic wrapping within visible bounds
- **Terminal constraints**: Terminal-based games work best with bounded, visible play areas

**Current alternative**: Use `#grid <width> <height>` for toroidal wrapping within terminal dimensions.

---

## Original Proposal (REJECTED)

Implement a **truly infinite coordinate space** using a sparse grid data structure with a **viewport system**. The terminal screen becomes a movable "window" into unlimited 2D space, enabling terminal-size-independent programs and massive-scale simulations.

## Core Concept

### World vs Screen Coordinates

- **World Coordinates**: Unlimited integer space (-∞ to +∞ for both x,y)
- **Screen Coordinates**: Terminal display area (0 to row-1, 0 to col-1)  
- **Viewport**: Position in world space that maps to center of screen

### Sparse Grid Storage

Only store symbols that exist, using world coordinates:
```cpp
class InfiniteGrid {
    std::unordered_map<std::pair<long, long>, char, hash_pair> symbols;
    std::unordered_map<std::pair<long, long>, G, hash_pair> memory;  // G = {char, fore, back, zord}
    
    long viewport_x, viewport_y;  // World coordinates of viewport center
    int screen_rows, screen_cols;  // Terminal dimensions
};
```

## Key Implementation Changes

### 1. Coordinate Transformation System

**World to Screen conversion:**
```cpp
std::pair<int, int> world_to_screen(long world_x, long world_y) {
    int screen_x = (int)(world_x - viewport_x + screen_cols / 2);
    int screen_y = (int)(world_y - viewport_y + screen_rows / 2);
    return {screen_y, screen_x};
}

std::pair<long, long> screen_to_world(int screen_row, int screen_col) {
    long world_x = screen_col - screen_cols / 2 + viewport_x;
    long world_y = screen_row - screen_rows / 2 + viewport_y;
    return {world_x, world_y};
}
```

**Visibility checking:**
```cpp
bool is_visible(long world_x, long world_y) {
    auto [screen_row, screen_col] = world_to_screen(world_x, world_y);
    return screen_row >= 0 && screen_row < screen_rows && 
           screen_col >= 0 && screen_col < screen_cols;
}
```

### 2. Sparse Symbol Storage

**Current:** `std::unordered_map<std::pair<int, int>, char>` using screen coordinates

**New:** `std::unordered_map<std::pair<long, long>, char>` using world coordinates

```cpp
class InfiniteDerivation {
    std::unordered_map<std::pair<long, long>, char, hash_pair> world_symbols;
    std::unordered_map<std::pair<long, long>, G, hash_pair> world_memory;
    
    long viewport_x = 0, viewport_y = 0;
    int screen_rows, screen_cols;
    
    // Get symbol at world coordinates (returns '~' for empty space)
    char get_symbol(long world_x, long world_y) {
        auto it = world_symbols.find({world_x, world_y});
        return it != world_symbols.end() ? it->second : '~';
    }
    
    void set_symbol(long world_x, long world_y, char symbol) {
        if (symbol == '~' || symbol == ' ') {
            world_symbols.erase({world_x, world_y});  // Remove from sparse storage
        } else {
            world_symbols[{world_x, world_y}] = symbol;
        }
    }
};
```

### 3. Context Checking with Infinite Space

**Current:** Boundary detection with `#` character

**New:** Context checking across infinite space:

```cpp
bool dryapply(long world_ro, long world_co, const Grammar2D::Rule &rule) {
    long world_r = world_ro;
    long world_c = world_co;
    
    for (const char *p = rule.rhs.c_str(); *p != '\0'; ++p, ++world_c) {
        if (*p == '\n') {
            ++world_r;
            world_c = world_co - 1;
            continue;
        }
        
        // Get context from infinite world space
        char ctx = get_symbol(world_r, world_c);
        
        // Apply rule matching logic (no boundary special cases)
        char req = *p;
        if (req == '@') req = rule.lhs;
        if (*p == '&') req = rule.ctx;
        if (req == ' ') req = '~';
        
        if ((req != '!' && req != '%' && req != ctx)
            || (req == '!' && ctx == rule.ctx)
            || (*p == '%' && ctx != rule.ctxrep && ctx != rule.ctx)) {
            return false;
        }
    }
    return true;
}
```

### 4. Rule Application in Infinite Space

```cpp
bool apply(long world_ro, long world_co, const Grammar2D::Rule &rule) {
    long world_r = world_ro;
    long world_c = world_co;
    
    for (const char *p = rule.rhs.c_str(); *p != '\0'; ++p, ++world_c) {
        if (*p == '\n') {
            ++world_r;
            world_c = world_co - 1;
            continue;
        }
        
        // Apply replacements in world space
        char rep = *p;
        if (rep == '@') rep = rule.rep;
        if (rep == '&') rep = rule.ctxrep;
        
        // Store in sparse world grid
        set_symbol(world_r, world_c, rep);
        
        // Update screen if visible
        if (is_visible(world_r, world_c)) {
            auto [screen_row, screen_col] = world_to_screen(world_r, world_c);
            mvaddch(screen_row, screen_col, rep);
        }
    }
    return true;
}
```

### 5. Viewport Management

**Automatic viewport following:**
```cpp
void update_viewport() {
    // Option 1: Follow center of mass of active symbols
    if (!world_symbols.empty()) {
        long sum_x = 0, sum_y = 0;
        for (const auto& [coords, symbol] : world_symbols) {
            sum_x += coords.first;
            sum_y += coords.second;
        }
        viewport_x = sum_x / world_symbols.size();
        viewport_y = sum_y / world_symbols.size();
    }
    
    // Option 2: Follow specific symbol (player character)
    // Option 3: Manual viewport control with keys
    // Option 4: Fixed viewport at origin
}
```

**Screen refresh after viewport change:**
```cpp
void refresh_viewport() {
    clear();  // Clear screen
    
    // Render all visible symbols from world space
    for (const auto& [world_coords, symbol] : world_symbols) {
        if (is_visible(world_coords.first, world_coords.second)) {
            auto [screen_row, screen_col] = world_to_screen(world_coords.first, world_coords.second);
            mvaddch(screen_row, screen_col, symbol);
        }
    }
    
    refresh();
}
```

### 6. Initial Symbol Placement

**Current:** Screen-relative positioning

**New:** World-space positioning with viewport consideration:

```cpp
void place_initial_symbols() {
    for (const auto& start_symbol : g.S) {
        long world_x = 0, world_y = 0;  // Default to world origin
        
        // Interpret positioning relative to current viewport or world origin
        if (start_symbol.lr == 'c') {
            world_x = viewport_x;  // Center on viewport
        } else if (start_symbol.lr == 'l') {
            world_x = viewport_x - screen_cols/2;  // Left edge of viewport
        }
        // ... handle other positioning modes
        
        set_symbol(world_y, world_x, start_symbol.s);
    }
}
```

## Advanced Features

### 1. Terminal Size Independence

**Resize handling:**
```cpp
void handle_terminal_resize(int new_rows, int new_cols) {
    screen_rows = new_rows;
    screen_cols = new_cols;
    
    refresh_viewport();  // Rerender with new dimensions
    // Viewport position unchanged - world content unaffected
}
```

### 2. Viewport Control

**Manual viewport movement:**
```cpp
void move_viewport(char key) {
    switch(key) {
        case 'H': viewport_x -= 10; break;  // Scroll left
        case 'L': viewport_x += 10; break;  // Scroll right  
        case 'J': viewport_y += 10; break;  // Scroll down
        case 'K': viewport_y -= 10; break;  // Scroll up
    }
    refresh_viewport();
}
```

### 3. World Bounds (Optional)

For performance, optionally limit world coordinates:
```cpp
const long WORLD_MIN = -1000000;
const long WORLD_MAX = 1000000;

bool in_world_bounds(long x, long y) {
    return x >= WORLD_MIN && x <= WORLD_MAX && 
           y >= WORLD_MIN && y <= WORLD_MAX;
}
```

## Grammar Language Extensions

### New Viewport Controls

**Special rules for viewport management:**
```
# Viewport control rule
==HvH    # Move viewport left on 'v' key
world_move -10 0

==LvL    # Move viewport right on 'v' key  
world_move 10 0
```

### World-Space Positioning

**Extended positioning syntax:**
```
^Sww    # Place at world origin (0,0)
^S+50+100  # Place at world coordinates (50,100)
^S-25-30   # Place at world coordinates (-25,-30)
```

## Performance Considerations

### Memory Usage

**Sparse storage efficiency:**
- Only active cells consume memory
- Large empty regions cost nothing
- Memory usage proportional to content, not world size

**Memory optimization:**
```cpp
// Periodic cleanup of empty regions
void cleanup_empty_regions() {
    for (auto it = world_symbols.begin(); it != world_symbols.end();) {
        if (it->second == '~' || it->second == ' ') {
            it = world_symbols.erase(it);
        } else {
            ++it;
        }
    }
}
```

### Rendering Performance

**Viewport culling:**
- Only render symbols within viewport
- Skip invisible rule applications for performance
- Batch screen updates

**Optimization strategies:**
```cpp
// Only apply rules to symbols near viewport
bool should_process_symbol(long world_x, long world_y) {
    const int ACTIVE_MARGIN = 50;  // Process symbols within margin of viewport
    return abs(world_x - viewport_x) < screen_cols/2 + ACTIVE_MARGIN &&
           abs(world_y - viewport_y) < screen_rows/2 + ACTIVE_MARGIN;
}
```

## Implementation Phases

### Phase 1: Core Infrastructure
1. Implement coordinate transformation functions
2. Create sparse grid data structures  
3. Basic viewport management
4. Simple symbol placement and rendering

### Phase 2: Rule System Integration
1. Modify `dryapply` for infinite space context checking
2. Modify `apply` for infinite space rule application
3. Update step function for world-space symbol processing
4. Handle memory system in infinite space

### Phase 3: Advanced Features
1. Viewport following algorithms
2. Terminal resize handling
3. Performance optimizations
4. World-space positioning extensions

### Phase 4: New Grammar Features
1. Viewport control rules
2. World-space positioning syntax
3. Advanced world management commands
4. Performance tuning and optimization

## Use Cases Enabled

### Large-Scale Simulations
- **Conway's Life**: Thousands of cells, unlimited growth
- **Ecosystem simulations**: Large populations across vast areas
- **Physics simulations**: Particle systems with unlimited space

### Games with Exploration
- **World exploration**: Player moves through vast worlds
- **Procedural content**: Generate world as player explores
- **Multi-scale games**: Zoom from macro to micro views

### Educational Applications
- **Mathematical visualization**: Plot functions across large domains
- **Algorithm demonstration**: Show sorting, pathfinding across large datasets
- **Scientific modeling**: Visualize large-scale phenomena

## Conclusion

The infinite sparse grid approach provides **true unlimited space** and **terminal size independence** at the cost of **implementation complexity**. It enables entirely new classes of applications impossible with fixed-screen approaches, making it ideal for large-scale simulations, exploration games, and educational tools.

This approach transforms Zahradnice from a **terminal-bounded** engine into a **world-scale** simulation platform.