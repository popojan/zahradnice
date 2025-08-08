# Modular Programs: Program Inheritance and Inclusion System

## Overview

Implement a program inheritance and inclusion system that allows Zahradnice programs to compose functionality from multiple sources, enabling code reuse, modularity, and hierarchical game design. This addresses the current limitation where programs exist as monolithic .cfg files with significant code duplication across similar games.

## Current Limitations

- **Monolithic Programs**: Each .cfg file contains all rules, leading to duplication
- **Code Duplication**: Common patterns (movement, menus, collision) repeated across games
- **Maintenance Overhead**: Bug fixes require changes in multiple files
- **Limited Composition**: Cannot combine behavior from different programs
- **Single Active Program**: Only one program's rules active at a time (program switching exists but is exclusive)

## Proposed Solution

### 1. Program Inclusion System

#### Syntax Options

**Option A - Simple Inclusion**
```
#include common/controls.cfg
#include ui/menu-system.cfg
```

**Option B - Namespaced Inclusion**
```
#include common/controls.cfg as ctrl
#include ui/menu-system.cfg as menu
```

**Option C - Inheritance Model**
```
#extends common/base-game.cfg
# Local rules can override parent rules
```

### 2. Namespace System

#### Non-Terminal Namespaces
- **Explicit**: `ctrl:A`, `menu:M`, `local:L`
- **Implicit**: Local symbols take precedence, then search included namespaces
- **Resolution Order**: Local → First Include → Second Include → etc.

#### Trigger Namespaces
- **Global Triggers**: `space`, `q`, `x` remain globally accessible
- **Scoped Triggers**: `ctrl:w`, `menu:e` for namespace-specific behaviors
- **Fallback**: Unqualified triggers search all namespaces

#### Sound/Dictionary Namespaces
- **Prefixed**: `ui:click.wav`, `game:explosion.wav`
- **Override**: Local definitions override included ones
- **Shared**: Common sounds automatically shared across namespaces

### 3. Rule Resolution Algorithm

#### Loading Phase
1. Parse include/extend statements first
2. Load parent/included programs recursively
3. Build dependency graph (detect cycles)
4. Merge rule sets with precedence

#### Runtime Resolution
1. **Trigger Match**: Find all rules matching current trigger
2. **Namespace Search**: Local → Included (order matters)  
3. **Context Validation**: Apply spatial/temporal context matching
4. **Weight Selection**: Use combined weight from all matching rules
5. **Rule Application**: Execute selected rule with namespace context

### 4. Implementation Architecture

#### Grammar2D Class Changes
```cpp
class Grammar2D {
    // Current members
    std::unordered_map<char, Rules> R;
    std::unordered_set<char> V;
    std::unordered_map<char, std::string> dict;
    
    // New members for modularity
    std::vector<std::string> includes;
    std::unordered_map<std::string, Grammar2D> modules;
    std::unordered_map<char, std::string> symbol_namespace;
    
    // New methods
    void loadIncludes(const std::string& base_path);
    Rules resolveRules(char trigger, const std::string& context);
    void mergeGrammar(const Grammar2D& parent, const std::string& ns);
};
```

#### File Organization
```
programs/
├── base/
│   ├── controls.cfg      # Common movement (a/d/w/s)
│   ├── menu.cfg          # Menu navigation
│   ├── collision.cfg     # Boundary checking
│   └── audio.cfg         # Standard sound mappings
├── components/
│   ├── physics.cfg       # Gravity, momentum
│   ├── ui-elements.cfg   # Status displays, notifications
│   └── animations.cfg    # Visual effects
└── games/
    ├── snake-modular.cfg # Uses base/controls + components/physics
    ├── tetris-modular.cfg # Uses base/controls + components/physics
    └── menu-modular.cfg   # Uses base/menu + components/ui-elements
```

## Use Cases and Benefits

### 1. Shared Game Mechanics
**Before:**
- Snake, Tetris, Arkanoid all implement a/d/w/s movement separately
- Each has duplicate collision detection logic
- Bug fixes require changes in multiple files

**After:**
```
# snake-modular.cfg
#include base/controls.cfg
#include base/collision.cfg

# Only snake-specific rules here
==HwU77  # Snake head turning
==BKB>77 # Snake body movement
```

### 2. UI Component Library
**Common Menu System:**
```
# base/menu.cfg
=|xea # Enter action trigger
=Dxs~ # Down selection  
=Dxw~ # Up selection
=|xq quit # Quit functionality
```

**Game-Specific Menus:**
```
# tetris-modular.cfg  
#include base/menu.cfg as menu

# Override specific menu actions
=menu:a tetris-start.cfg
=menu:s tetris-options.cfg
```

### 3. Progressive Game Development
**Base Game:**
```
# base/platformer.cfg
# Basic movement, gravity, collision
==ST>42 # Movement rules
==RTfall # Gravity
```

**Extended Versions:**
```
# platformer-with-enemies.cfg
#extends base/platformer.cfg
# Add enemy AI rules

# platformer-with-powerups.cfg  
#extends base/platformer.cfg
# Add powerup collection rules
```

### 4. Audio/Visual Consistency
**Shared Definitions:**
```
# base/audio.cfg
#=1sounds/click.wav
#=2sounds/chime.wav  
#=3sounds/clack.wav
```

**All Games Include:**
```
#include base/audio.cfg
# Consistent audio across all games
```

## Technical Challenges and Solutions

### 1. Symbol Conflicts
**Problem:** Multiple modules define same non-terminal
**Solution:** 
- Explicit namespacing: `module:A` vs `other:A`
- Override semantics: Local definitions win
- Conflict detection at load time

### 2. Rule Precedence
**Problem:** Multiple rules match same trigger/context
**Solution:**
- Weighted combination from all namespaces
- Explicit precedence declaration
- Namespace search order determines priority

### 3. Performance Impact
**Problem:** More rules to check, namespace lookups
**Solution:**
- Pre-compile combined rule sets at load time
- Cache namespace resolution results
- Optimize for common cases (local rules first)

### 4. Debugging Complexity
**Problem:** Hard to trace which module provided a rule
**Solution:**
- Debug mode shows rule source namespace
- Dependency visualization tools
- Clear error messages with module context

### 5. Circular Dependencies
**Problem:** Module A includes B, B includes A
**Solution:**
- Dependency graph analysis at load time
- Error reporting for cycles
- Forward declaration syntax if needed

## Implementation Phases

### Phase 1: Basic Inclusion
- Add `#include` syntax parsing
- Implement simple file inclusion (no namespaces)
- Local rules override included rules
- Test with simple shared components

### Phase 2: Namespace System
- Add namespace syntax (`module:symbol`)
- Implement namespace resolution algorithm
- Support aliasing (`#include file.cfg as alias`)
- Update rule matching to consider namespaces

### Phase 3: Advanced Features
- Rule precedence controls
- Conditional inclusion (`#ifdef`, `#ifndef`)
- Module interfaces and contracts
- Performance optimizations

### Phase 4: Tooling and Ecosystem
- Dependency visualization
- Module documentation generator
- Standard library of common components
- Migration tools for existing programs

## Backward Compatibility

- Existing .cfg files work unchanged
- Include system is opt-in
- No performance impact for non-modular programs
- Gradual migration path available

## Risks and Mitigations

### High Risk: Implementation Complexity
- **Risk:** Grammar parsing becomes significantly more complex
- **Mitigation:** Implement incrementally, maintain comprehensive tests

### Medium Risk: Performance Degradation
- **Risk:** Runtime rule resolution becomes slower
- **Mitigation:** Pre-compile rule sets, profile-guided optimization

### Medium Risk: User Confusion
- **Risk:** Namespace system too complex for casual users
- **Mitigation:** Clear documentation, optional complexity, simple defaults

### Low Risk: Maintenance Burden
- **Risk:** More complex codebase harder to maintain
- **Mitigation:** Clear separation of concerns, modular implementation

## Success Metrics

1. **Code Reuse**: >50% reduction in duplicate rules across similar games
2. **Development Speed**: New games can be created 2x faster using components
3. **Maintainability**: Bug fixes propagate automatically to dependent games  
4. **Community Adoption**: Standard library of common components emerges
5. **Performance**: <10% overhead for modular programs vs monolithic

## Alternative Approaches Considered

### 1. Runtime Module System
- **Pros**: More flexible, dynamic loading
- **Cons**: Complex implementation, performance overhead
- **Decision**: Static inclusion simpler and fits grammar model better

### 2. Macro Preprocessing
- **Pros**: Simple text substitution approach
- **Cons**: No semantic understanding, limited composition
- **Decision**: Full grammar integration provides better features

### 3. External Module Format
- **Pros**: Clean separation, could enable visual editors
- **Cons**: Breaks from existing .cfg format
- **Decision**: Extend existing format for consistency

## Conclusion

Program inheritance and inclusion would transform Zahradnice from a collection of monolithic programs into a modular, composable system. This enables code reuse, faster development, and easier maintenance while preserving the unique character of the grammar-based approach. The implementation should be incremental, starting with simple inclusion and evolving toward full namespace support.

The feature addresses a fundamental limitation in the current architecture and opens possibilities for community-driven component libraries, educational progressions, and rapid game prototyping within the Zahradnice ecosystem.