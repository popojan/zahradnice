# Namespace Design Analysis for Modular Programs

## Problem Statement

Modular programs require splitting rulesets into reusable components while handling two critical collision types:
1. **Non-terminal Symbol Collisions**: Different modules using the same single-character symbols
2. **Trigger Key Collisions**: Multiple modules responding to the same input keys

The goal is maximum reusability where authors can create modules without knowing how they'll be reused, while preserving the single-character non-terminal constraint.

## Design Approaches Analyzed

### 1. Pure Implicit Namespaces (Recommended)

**Concept**: Each module's non-terminals exist in complete isolation. `A` in `controls.cfg` is fundamentally different from `A` in `physics.cfg`, even though they appear identical.

**Advantages**:
- Preserves single-character syntax completely
- Maximum reusability - authors never worry about symbol conflicts
- Simple mental model - symbols are always local to the module
- No syntax changes required

**Disadvantages**:
- No direct inter-module communication via non-terminals
- Potential duplication of common patterns
- Modules cannot share semantic conventions

### 2. Explicit Namespaces (Document's Approach)

**Concept**: Use syntax like `physics:A` or `controls:W` to reference symbols from other modules.

**Advantages**:
- Clear and unambiguous references
- Enables controlled sharing and communication
- Explicit dependency tracking

**Disadvantages**:
- Breaks single-character constraint
- More verbose syntax
- Authors must know other modules' internals

### 3. Hybrid: Implicit with Protocol Symbols

**Concept**: Most symbols are implicit, but special Unicode characters serve as shared "protocol symbols" for inter-module communication.

**Example**:
- Regular symbols (A-Z, a-z, 0-9): Implicit/isolated
- Protocol symbols (α, β, γ, ∀, ∃, ∴): Shared across all modules
- Mathematical/Greek symbols as communication channels

**Advantages**:
- Preserves single-character constraint
- Enables controlled cooperation
- Clear visual distinction between local and shared symbols

**Disadvantages**:
- Requires Unicode input/display
- Limited number of "protocol" symbols
- Two-tier symbol system complexity

### 4. Semantic Vocabulary Sharing

**Concept**: Common semantic symbols (P=player, E=enemy, W=wall) are implicitly shared when modules opt-in.

**Implementation**:
```cfg
#semantic_sharing on
# P, E, W, etc. are now shared with other modules that opt in
```

**Advantages**:
- Natural cooperation around common concepts
- Optional - modules can remain fully isolated
- Single-character preserved

**Disadvantages**:
- Requires standardized vocabulary
- Potential for semantic mismatches
- Implicit dependencies harder to track

### 5. Trigger-Based Communication

**Concept**: Modules remain symbol-isolated but communicate through shared trigger events.

**Example**:
- Module A generates trigger `collision` when player hits wall
- Module B responds to `collision` trigger with its own rules
- Non-terminals never shared, only trigger events

**Advantages**:
- Complete symbol isolation
- Event-driven communication model
- Natural for many game interactions

**Disadvantages**:
- Limited to trigger-based communication
- Cannot share spatial/visual state directly
- May require new trigger generation mechanisms

## Recommended Architecture

Based on the analysis, I recommend a **layered hybrid approach**:

### Core Design: Pure Implicit Namespaces
- All standard non-terminals (A-Z, a-z, 0-9) are completely isolated per module
- Authors never worry about symbol conflicts
- Maximum reusability achieved

### Communication Layer: Protocol Symbols + Trigger Events

#### Protocol Symbols (Optional)
- Reserve Unicode range for shared communication: `α`, `β`, `γ`, `δ`, `ε`, `ζ`, `η`, `θ`
- Modules can use these for inter-operation when needed
- Visual distinction makes shared vs. local symbols obvious

#### Enhanced Trigger System
- Modules can generate custom triggers: `#trigger collision`
- Other modules respond to these triggers: `=collision A B77`
- Enables event-driven communication without symbol sharing

### Implementation Strategy

#### Phase 1: Pure Implicit (MVP)
```cpp
class ModuleGrammar {
    std::string module_id;  // Unique per module
    std::unordered_map<char, Rules> local_rules;
    
    // Symbol 'A' in this module is effectively 'module_id:A'
    // but syntax remains just 'A'
};
```

#### Phase 2: Protocol Symbols (Optional Enhancement)
```cpp
class Grammar2D {
    std::unordered_set<char> protocol_symbols = {α, β, γ, δ, ε, ζ, η, θ};
    std::unordered_map<char, Rules> shared_protocol_rules;
};
```

#### Phase 3: Enhanced Triggers (Cooperation Layer)
```cfg
# controls.cfg
#trigger player_moved
==HaB77  # When player moves
#emit player_moved  # Generate trigger for other modules

# physics.cfg  
=player_moved apply_gravity77  # React to movement
```

## Design Trade-offs Analysis

| Approach | Isolation | Cooperation | Syntax Simplicity | Learning Curve |
|----------|-----------|-------------|-------------------|----------------|
| Pure Implicit | ✓✓✓ | ✗ | ✓✓✓ | ✓✓✓ |
| Explicit NS | ✓✓ | ✓✓✓ | ✗ | ✓ |
| Protocol Symbols | ✓✓ | ✓✓ | ✓✓ | ✓✓ |
| Trigger Events | ✓✓✓ | ✓✓ | ✓✓✓ | ✓✓ |

## Specific Recommendations

### For Zahradnice Implementation:

1. **Start with Pure Implicit Namespaces**
   - Addresses 90% of modular needs
   - Simple to implement and understand
   - Preserves single-character constraint completely

2. **Add Protocol Symbols for Advanced Use Cases**
   - Use Greek letters: `α`, `β`, `γ`, `δ`, `ε`, `ζ`, `η`, `θ` (8 symbols should suffice)
   - These symbols are shared across all modules that use them
   - Clear visual indication of "special" status

3. **Enhance Trigger System for Events**
   - Allow modules to generate custom triggers
   - Enable event-driven communication without symbol coupling
   - Natural fit for game event systems (collision, score, death, etc.)

### Module Organization:
```
programs/
├── base/
│   ├── controls.cfg       # Uses α for "player position" protocol
│   ├── physics.cfg        # Uses α, generates "collision" trigger
│   └── ui.cfg            # Uses β for "score display" protocol
├── games/
│   ├── snake.cfg         # Pure implicit symbols + base modules
│   └── tetris.cfg        # Pure implicit symbols + base modules
```

### Syntax Examples:
```cfg
# controls.cfg - Base module
==Haα77   # Move player, update protocol symbol α
#trigger moved  # Generate event trigger

# snake.cfg - Game module  
#include base/controls.cfg
=moved grow_snake77     # React to movement event
==BSB>77               # Snake-specific rules (pure implicit)
```

## Implementation Complexity

### Runtime Performance:
- Pure implicit: No overhead (symbols internally prefixed with module ID)
- Protocol symbols: Small lookup table for shared symbols
- Enhanced triggers: Event queue processing

### Parse Time:
- Include processing: Linear with dependency depth
- Symbol resolution: O(1) with proper hash table design
- Module loading: Cacheable for repeated use

## Backward Compatibility

All existing `.cfg` files work unchanged:
- No syntax modifications required
- Single-file programs remain pure implicit
- Modular features are opt-in via `#include` statements

## Revised Recommendation: Producer-Controlled Symbol Sharing

After further discussion, the **producer-controlled approach** emerges as the most zen-aligned solution:

### Core Philosophy
- Module authors declare which symbols are **global** (shared) vs **local** (private)
- Preserves the semantic meaning of symbols: `W` means `W` everywhere
- Aligns with OOP interface/implementation separation
- Maintains single-character constraint

### Syntax Design
```cfg
# physics.cfg - Module declares its public interface
#global W E P  # Wall, Enemy, Player (shared symbols)
#local a b c   # Private implementation symbols

==WaE77  # Wall collision (uses global W, private a)
==abcP2  # Private calculation leading to player interaction
```

### Benefits
1. **Semantic Consistency**: `W` always means "Wall" across the ecosystem
2. **Clear Interfaces**: Module authors design their public API
3. **Natural Standards**: Pressure for community conventions (P=player, E=enemy, etc.)
4. **Conflict Resolution**: Clear compile errors when two modules claim same global symbol
5. **Implementation Privacy**: Authors can refactor private symbols without breaking dependents

### Unicode Symbol Space Extension

**Current State**: ASCII-only (256 codepoints) via standard ncurses
**Upgrade Path**: 
- Link with `ncursesw` library
- Add `setlocale(LC_ALL, "")` initialization  
- Use wide character ncurses functions
- **Result**: Access to full Unicode range (1M+ codepoints)

**Unicode Benefits**:
- Semantic symbols: `α β γ δ ε ζ η θ` for advanced protocols
- Mathematical symbols: `∀ ∃ ∴ ∵ ∈ ∉ ⊂ ⊃` for logical operations  
- Game symbols: `♠ ♣ ♥ ♦ ☀ ☽ ★ ▲ ● ◆` for rich visuals
- Cultural symbols: `中 한 あ` for international games

### Implementation Strategy
```cpp
class ModuleGrammar {
    std::string module_id;
    std::unordered_set<wchar_t> global_symbols;  // Declared #global
    std::unordered_set<wchar_t> local_symbols;   // Declared #local  
    std::unordered_map<wchar_t, Rules> rules;
};

class Grammar2D {
    std::unordered_map<wchar_t, std::string> global_symbol_owners;
    // Compile error if multiple modules declare same global symbol
};
```

## Conclusion

The producer-controlled approach preserves the zen principle that symbols should have consistent meaning while enabling sophisticated modular composition. Combined with Unicode support, this provides a virtually unlimited semantic space for the Zahradnice ecosystem to grow.

This design prioritizes **semantic clarity** and **interface discipline** over maximum reusability, which aligns with the project's emphasis on elegance and simplicity.