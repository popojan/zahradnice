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
- `/programs/<name>/` - A collection: `index.cfg` is its submenu, siblings are the
  programs it launches (`sokoban`, `primes`). A submenu uses `#control Q return`,
  so `q` always goes one level up; only the top-level menu quits.
- `/experiments/index.cfg` - Submenu over a curated few of the research programs,
  reached from the main menu as **Evolution**. The programs stay where their papers
  and result docs link them; only an index and a `q`-triggered return rule were added,
  so no derivation changed. A research program keeps its own `#!` because its counter
  is named (`pop=`, `grains=`, `births=`, `reward=`) — it gains `{help}` rather than
  losing the template.
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
- `x` - Map from (row,col) coordinates to characters representing current screen state (non-terminals only)
- `memory` - Array for local state storage used by advanced programs
- `screen_chars` - Flat `wchar_t` array indexed by `r*col + c`, redundantly mirroring the displayed character at every cell. Read in `apply_impl` for every context-match. Introduced to avoid mutex contention on curses reads from worker threads, but is also the architectural reason single-threaded rule matching is fast: every dry-run match becomes an O(1) array index instead of a curses round-trip or `x` map lookup. The cost that dominates is the *match* phase, not the post-match one: `gatherApplicableRules` / `step` are fully serial, and before the rule index below they dry-ran every rule of a family at every anchor on screen — measured at 8018 dry-runs per applied rule for `programs/primes/06-umeo.cfg`.
- Rule matching is indexed, in `Derivation`:
  - `anchors_for(key)` caches which characters a trigger can rewrite (it used to be rebuilt from every rule on every step).
  - Each `Rule` carries a **probe**: the first LHS cell that pins an exact character, as an offset from the anchor.
    A bare `@@@` body, or one whose cells are all `!` / `%` / any-ctx, pins nothing (`probe_ch == 0`) and is always tried.
  - `rules_for(anchor, key)` buckets a family by the character its probe pins, keeping rules that pin a different cell
    (or nothing) in `others`. Both lists are ascending and are merged, so candidates arrive in plain scan order —
    the derivation is byte-identical to the unindexed scan for a given seed. Measured 4–11x fewer dry-runs, 1.03–2.5x wall clock.
- Threading helps when work is measured in applied rules rather than trigger events: 06-umeo is ~2.4x faster at 4 threads.
  Feeding a fixed oversized trigger count hides this, because every trigger after the program settles still pays a full scan.
- Grid-based 2D transformation system with color support

## Special Files

- `GRAMMAR.md` - Complete language reference and syntax guide
- `README.md` - Project overview and program descriptions  
- `plosinovka.cfg` - Example complex program demonstrating advanced features
- `programs/index.cfg` - Default startup program that provides program selection interface
- `programs/primes/` - Six sieves, each moving the divisor further out of the rule
  set; `05-fischer` and `06-umeo` are real-time cellular automata (see `tools/gen_primes*.py`)
- `demos/` - Simple tutorial programs for learning the grammar language