# Program Validation Utility

## Problem Statement

The main Zahradnice engine uses extremely robust parsing that prioritizes stability over user feedback. While this prevents crashes, it creates a developer experience issue:

- **Silent failures**: Malformed rules are ignored without warning
- **No feedback**: Users may not realize their programs contain errors
- **Debugging difficulty**: Hard to identify why rules don't trigger as expected
- **Typo tolerance**: Syntax errors are silently ignored, leading to unexpected behavior

## Proposed Solution: Separate Validation Utility

Create a dedicated program validation tool (`zahradnice-validate` or `zahradnice-lint`) that provides comprehensive error checking and feedback without impacting the main engine's size or stability.

## Architecture Benefits

**Separation of Concerns:**
- **Main engine**: Optimized for runtime stability, minimal size, fail-safe operation
- **Validation utility**: Optimized for developer experience, detailed reporting, comprehensive analysis

**No Compromises:**
- Engine remains crash-proof and minimal
- Developers get excellent tooling and feedback
- Optional tool - doesn't affect end-user experience

## Proposed Features

### Core Validation
- **Syntax checking**: Validate rule format, detect malformed entries
- **Symbol analysis**: Check for undefined non-terminals, unused symbols  
- **Context validation**: Verify context patterns are well-formed
- **Dictionary verification**: Validate sound paths, color definitions, timing values
- **Starting symbol checks**: Ensure valid placement and symbol definitions

### Advanced Analysis
- **Rule coverage**: Identify rules that can never trigger
- **Dead code detection**: Find unreachable symbols or unused dictionary entries
- **Performance warnings**: Flag potentially expensive rule sets
- **Program flow analysis**: Trace possible execution paths
- **Dependency analysis**: Map symbol relationships and transformations

### Development Workflow Integration
- **File watching**: Automatically validate on save
- **IDE integration**: Provide LSP or plugin for real-time validation
- **Batch processing**: Validate entire program directories
- **CI/CD integration**: Add validation to build pipelines

## Implementation Approaches

### Option 1: Standalone C++ Utility
- Share grammar parsing code with main engine
- Separate compilation with different optimization flags
- Full access to internal data structures
- Consistent behavior with main engine

### Option 2: External Tool (Python/Rust/etc.)
- Independent implementation of parser
- More flexible for rapid feature development  
- Rich ecosystem for text processing and reporting
- Could provide web-based or GUI interfaces

### Option 3: Extended Engine Mode
- Add `--validate` flag to main engine
- Conditional compilation of validation features
- Single codebase, but larger binary size
- Less separation of concerns

## Workflow Examples

### Basic Validation
```bash
# Validate single program
./zahradnice-validate programs/snake.cfg

# Validate with detailed output
./zahradnice-validate --verbose programs/tetris.cfg

# Validate entire directory
./zahradnice-validate programs/
```

### Sample Output
```
Validating programs/my-game.cfg...

ERRORS:
  Line 23: Malformed rule header '=s?x' - missing context specification
  Line 45: Unknown symbol 'Q' referenced in rule
  
WARNINGS:  
  Line 12: Rule for symbol 'unused_symbol' never triggered
  Line 67: Sound file 'missing.wav' not found
  
SUGGESTIONS:
  Consider adding quit rule for better user experience
  Rule weight distribution heavily favors symbol 'S' (85% of triggers)
  
Summary: 2 errors, 2 warnings, 2 suggestions
```

## Development Priorities

### Phase 1: Core Validation
1. **Rule syntax checking** - Detect malformed rule headers
2. **Symbol validation** - Check for undefined references
3. **Basic error reporting** - Line numbers and error descriptions

### Phase 2: Advanced Analysis  
1. **Rule coverage analysis** - Identify unreachable rules
2. **Performance analysis** - Flag potential bottlenecks
3. **Program flow tracing** - Map symbol transformations

### Phase 3: Developer Integration
1. **File watching** - Auto-validation on changes
2. **IDE plugins** - Real-time validation in editors
3. **Documentation generation** - Extract program documentation from comments

## Benefits for Zahradnice Ecosystem

**For Engine Stability:**
- Main engine remains minimal and crash-proof
- No runtime performance impact
- Maintains size optimization goals

**For Developer Experience:**
- Immediate feedback on program errors
- Better debugging capabilities  
- Improved program quality
- Faster development iteration

**For Project Growth:**
- Lowers barrier to entry for new users
- Enables more complex programs through better tooling
- Professional development workflow
- Community contribution friendly

## Technical Considerations

### Code Sharing
- Extract common grammar parsing logic into shared library
- Ensure validation utility uses same parsing rules as engine
- Consider parser generator approach for consistency

### Performance
- Validation utility can afford slower, more thorough analysis
- Memory usage not as critical as main engine
- Can implement expensive algorithms for comprehensive checking

### Extensibility
- Plugin architecture for custom validation rules
- Configuration for project-specific requirements  
- API for third-party tool integration

## Future Enhancements

- **Interactive debugger**: Step through program execution
- **Visual program editor**: GUI tool with real-time validation
- **Program optimization**: Suggest rule restructuring for better performance
- **Documentation generator**: Extract program behavior documentation
- **Test framework**: Unit testing for grammar programs
- **Profiling support**: Runtime performance analysis

## Conclusion

A separate validation utility provides the best of both worlds: a minimal, stable runtime engine and comprehensive development tooling. This approach aligns with the project's philosophy of fail-fast development practices while maintaining runtime robustness.

The utility would significantly improve the developer experience without compromising the core engine's design goals of minimal size and maximum stability.