# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Zahradnice is a terminal-based game engine that uses Type-0 grammars as a domain-specific programming language. The engine implements classic games (Snake, Tetris, Conway's Game of Life, Sokoban, Arkanoid) and artistic simulations through a unique rule-based transformation system.

## Build Commands

**Primary build targets:**
- `make` or `make zahradnice-speed` - Speed-optimized build (-O3)
- `make zahradnice-size` - Size-optimized build (-Os with aggressive stripping)
- `make install` - Creates release package with compressed programs
- `make soko` - Downloads and processes Sokoban levels from web

**Running programs:**
- `./zahradnice` - Starts with default menu program
- `./zahradnice programs/snake.cfg` - Run specific program
- `./zahradnice programs/life.cfg 42` - Run with specific seed for deterministic behavior

**Dependencies:** C++14, ncurses, SDL2_mixer, zlib

**No formal test suite** - testing relies on manual execution of demo programs.

## Architecture

**Core Components:**
- `src/zahradnice.cpp` - Main game loop with ncurses terminal interface, handles SDL2_mixer initialization, timing (B/M/T steps), and user input processing
- `src/grammar.cpp/h` - Grammar parsing and rule execution engine:
  - `Grammar2D` class: Parses `.cfg` files, manages rules, dictionary entries, and sounds  
  - `Derivation` class: Manages 2D game state, applies rules, handles spatial transformations and colors
- `src/sample.cpp/h` - SDL2_mixer audio wrapper for loading and playing WAV files
- `zstr/` - Header-only ZLib compression for program files (used in release builds)

**Grammar Language:** Programs are written in `.cfg` files using a custom DSL based on Type-0 grammars with pattern matching and context-sensitive replacement rules.

**Execution Model:**
1. Load program configuration and initialize 2D derivation with starting symbols
2. Main loop: check for trigger keys (user input or timing), find applicable rules matching non-terminals and context
3. Randomly select one rule (weighted by rule weights), apply transformation to screen state
4. Handle special rules (quit, program switching) or continue execution loop

**Key Language Features:**
- Rules triggered by keypresses or time steps (B/M/T)
- 2D spatial context matching with `@` symbols marking LHS/RHS boundaries
- Color and sound integration
- Program switching and state management
- Memory system for complex behaviors

## Program Structure

**Program files** (`.cfg` format):
- Comments: `# text`
- Initial symbols: `^<char><v-pos><h-pos>`
- Rules: `=<sound><nonterminal><trigger><replacement><colors><context><z-order> <score> <weight>`
- Special rules: quit rules and program switching rules

**Program locations:**
- `/programs/` - Main game collection (~50+ programs)
- `/programs.bak/` - Backup configurations
- `/demos/` - Tutorial and demonstration programs

## Key Controls

**Runtime controls:**
- `SPACE` - Unpause program execution
- `x` - Reload current program
- `B/M/T` - Manual step execution when paused (long/medium/instant)

## Development Patterns

**When modifying games:**
1. Programs load paused by default - use SPACE to start
2. Test changes by pressing `x` to reload current program
3. Use manual stepping (B/M/T) to debug rule applications
4. Check audio assets in `/sounds/` directory structure
5. Compressed programs (`.cfg.gz`) are used in release builds

**Grammar debugging:**
- Rules apply randomly when multiple match - use weights to control probability
- Context matching requires exact character and spatial alignment
- Z-order determines visual layering (higher values in front)

**Audio integration:**
- Define sounds with `#=<key><path/to/file.wav>` dictionary entries
- Reference in rule headers as sound character
- Audio files organized in `/sounds/bass/`, `/sounds/piano/`, `/sounds/vsup/`

## Key Data Structures

**Grammar2D class (`grammar.h:22-87`):**
- `R` - Map from trigger characters to rule vectors
- `V` - Set of non-terminal characters  
- `S` - Vector of starting symbols with positions
- `dict` - Dictionary for sound paths, colors, and timing definitions

**Derivation class (`grammar.h:90-129`):**
- `x` - Map from (row,col) coordinates to characters representing current screen state
- `memory` - Array for local state storage used by advanced programs
- Grid-based 2D transformation system with color and z-order support

## Special Files

- `GRAMMAR.md` - Complete language reference and syntax guide
- `README.md` - Project overview and program descriptions  
- `plosinovka.cfg` - Example complex program demonstrating advanced features
- `programs/menu.cfg` - Default startup program that provides program selection interface
- `demos/` - Simple tutorial programs for learning the grammar language