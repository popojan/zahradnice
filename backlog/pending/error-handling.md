# Error Handling Strategy

This document outlines the lightweight error handling strategy for making Zahradnice fail-proof while maintaining minimal binary size.

## Analysis Summary

The codebase currently has several vulnerability categories that can cause crashes with malformed user programs:

### Critical Vulnerabilities

1. **Bounds violations** - Multiple `.at()` calls become undefined behavior with `-fno-exceptions` 
   - Located in `grammar.cpp:80-288` (string parsing)
   - Risk: Segmentation fault on short strings

2. **Memory allocation failures** - Raw `new[]` without checking
   - Located in `grammar.cpp:315-316` (Derivation::init)
   - Risk: std::bad_alloc exception (disabled) or nullptr dereference

3. **Array access** - Unchecked memory array indexing
   - `memory[r*col+c]` and `screen_chars[r*col+c]` throughout grammar.cpp
   - Risk: Buffer overflow/underflow

4. **File parsing** - No size limits, minimal error checking
   - `gzread()` and file operations in `loadFromFile()`
   - Risk: Memory exhaustion, corrupted data processing

5. **Integer parsing** - Silent failure modes
   - `wcstol()`/`atoi()` return 0 for both errors and valid input
   - Risk: Incorrect program behavior

### Secondary Issues

- Unicode conversion fallbacks may process invalid data
- Container operations fail silently without exceptions
- SDL/ncurses calls lack error checking

## Lightweight Strategy

**Core Principle:** Replace exception-throwing operations with bounds-checked alternatives, add minimal validation at input boundaries. Use `std::exit(1)` for unrecoverable errors to maintain fail-fast behavior without error messages.

### 1. Safe String Access

Replace all `.at()` calls with length-checked access:

```cpp
// Current (unsafe):
if (line.at(0) == '#')

// Safe replacement:  
if (line.length() > 0 && line[0] == '#')
```

**Implementation locations:**
- `grammar.cpp:80` - comment detection
- `grammar.cpp:83, 85, 86, 95` - dictionary parsing
- `grammar.cpp:105, 107, 110, 111` - starting symbol parsing
- `grammar.cpp:114` - rule detection
- `grammar.cpp:166` - color parsing
- `grammar.cpp:214, 222, 223, 249, 252, 258, 269, 276, 281, 288` - rule construction

### 2. Memory Allocation Safety

Add allocation failure checks with immediate termination:

```cpp
// Current (unsafe):
memory = new G[row * col];
screen_chars = new wchar_t[row * col];

// Safe replacement:
memory = new(std::nothrow) G[row * col];
screen_chars = new(std::nothrow) wchar_t[row * col];
if (!memory || !screen_chars) std::exit(1);
```

**Implementation location:** `grammar.cpp:315-316`

### 3. Input Size Validation

Add file size limits to prevent memory exhaustion:

```cpp
// In loadFromFile() after stat():
constexpr size_t MAX_FILE_SIZE = 1024 * 1024; // 1MB limit
if (buffer.st_size > MAX_FILE_SIZE) return false;
```

**Implementation location:** `grammar.cpp:38` (after stat call)

### 4. Array Bounds Validation

Add bounds checking helper and use throughout:

```cpp
// In Derivation class:
inline bool valid_pos(int r, int c) const { 
    return r >= 0 && r < row && c >= 0 && c < col; 
}

// Usage before all memory[]/screen_chars[] access:
if (!valid_pos(wrapped_r, wrapped_c)) return false; // or continue
```

**Implementation locations:**
- `grammar.cpp:395, 468, 469, 513, 533, 536, 539, 545, 549, 553` - All memory/screen_chars access

### 5. Safe Integer Parsing

Replace direct `wcstol()`/`atoi()` with validated parsing:

```cpp
template<typename T> 
static bool safe_parse(const wchar_t* str, T& result) {
    if (!str) return false;
    wchar_t* end;
    errno = 0;
    long val = std::wcstol(str, &end, 10);
    if (errno || *end != 0 || val < std::numeric_limits<T>::min() || 
        val > std::numeric_limits<T>::max()) return false;
    result = static_cast<T>(val);
    return true;
}
```

**Implementation locations:**
- `zahradnice.cpp:34` - seed parsing
- `zahradnice.cpp:92, 94, 95, 97` - timing parsing  
- `grammar.h:97` - integer list parsing
- All `wcstol()` calls in rule parsing

### 6. Wrap Coordinate Validation

Ensure wrap functions handle edge cases:

```cpp
inline int wrap_row(int r) const {
    if (effective_max_row <= 0) return 1; // Fallback
    return (r - 1 + effective_max_row) % effective_max_row + 1;
}

inline int wrap_col(int c) const {
    if (effective_max_col <= 0) return 0; // Fallback
    return (c + effective_max_col) % effective_max_col;
}
```

**Implementation location:** `grammar.h:140-149`

## Implementation Priority

1. **High Priority** - Memory allocation safety (prevents immediate crashes)
2. **High Priority** - String bounds checking (most common vulnerability)
3. **Medium Priority** - Array bounds validation (prevents memory corruption)
4. **Medium Priority** - File size limits (prevents resource exhaustion)
5. **Low Priority** - Integer parsing safety (improves robustness)

## Size Impact Analysis

**Estimated binary size increase:** 50-100 bytes total

- Bounds checking helpers: ~20 bytes
- Additional conditionals: ~30-50 bytes  
- Safe parsing functions: ~30-40 bytes (template instantiations)

**Key to minimal overhead:** Use `std::exit(1)` instead of:
- Exception throwing (disabled anyway)
- Error message printing (saves string literals)
- Complex error recovery (just fail fast)

## Testing Strategy

1. **Malformed files:** Test with truncated .cfg files, oversized files
2. **Invalid strings:** Test with strings shorter than expected  
3. **Memory stress:** Test with large terminal sizes
4. **Invalid integers:** Test with non-numeric timing values
5. **Edge coordinates:** Test rules that access screen boundaries

## Compatibility

This strategy maintains full compatibility:
- No API changes
- No behavioral changes for valid programs
- Only adds early termination for invalid cases that would crash anyway
- Preserves existing fail-fast philosophy