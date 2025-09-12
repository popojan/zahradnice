# Language

## General controls

Key case matters. **Note:** All control keys must be explicitly declared in programs using `#control` directives. No keys are reserved by default (except ESC for emergency exit).

Example control declarations:
```
#control ~ pause      # Space toggles pause/unpause
#control x restart    # x restarts the program  
#control q quit       # q quits when paused
```

* `ESC` ... emergency exit (always available, bypasses all control systems) 

## Main loop
1. **load a program** config (processing all `#include` directives)
1. choose a **trigger key** based either on timing events or user pressed keys 
1. for the given trigger key find all **applicable rules** in the current state (based on non-terminals and their context)
1. **choose randomly** rule(s) to apply (sample according to rule weights if unequal):
   * **Single-threaded mode** (`#threads 1`): Choose exactly one rule
   * **Multi-threaded mode** (`#threads >1`): Choose up to N non-conflicting rules that can be applied simultaneously
1. **apply** the chosen rule(s) to change state and optionally alter score and/or play sound
1. **handle special actions** if the rule triggered any:
   * Engine actions (pause, restart, reset, quit)
   * Program switching (load a given program and repeat from 2.)
1. **repeat** from 2. 

## Syntax

Lines starting with
* `# ` (space after #) ... comments
* `#include <filename>` ... include another file (processed as text substitution)
* `#keyword` (no space after #) ... configuration keywords (#timing, #control, etc.)
* To comment out keywords: `#timing B 500` → `# #timing B 500`
* If rule bodies need `#` at start of line, precede with spaces to avoid parsing as keyword/comment
* `^` ... initial symbol and its position
* `=` ... rule or special rule header
* otherwise the line forms a part of body belonging to the preceding rule headers

**Important:** All `#` declarations must precede their usage. Include files early in the program or ensure included files contain only declarations.

### Defining rules
Rules consist of one or more headers, and a rule body.

For the rule to be **applicable** to a char on screen these conditions must be met:

* trigger char matches
* non-terminal char matches with the char on screen at the given position
* surrounding context matches 

#### Rule header
`=<s-char><nonterminal-char><trigger-char><fore-color-char><bg-color-char><extra-context-char><extra-replacement-char> <rule-score-num> <rule-weight-num>`

i.e. these chars and tokens left to right `=S1234567 <score> <weight>`

* `S.` `=` for silence, or a sound/program/engine-action char previously defined, i.e. `#sound S sounds/click.wav`, `#control P pause`
* `1.` LHS non-terminal character (obligatory)
* `2.` trigger char (a rule is invoked by pressing corresponding key, timing events, or `~` for space key) (obligatory)
* `3.` RHS non-terminal replacement character (first @ in the rule body to be replaced by this char) (obligatory)
* `4.` foreground char (`0` black, `1` red, `2` green, `3` yellow, `4` blue, `5` magenta, `6` cyan, `7` white) (default `7`) or a dictionary entry value if not a digit
* `5.` background char (same as foreground plus `8` for transparent) (default `8`)
* `6.` extra required context char (special values: `?` for any, `*` for LHS char, `$` for char saved in memory, `#` for out-of-screen, `~` empty space) at each char `&` in the rule body
* `7.` extra required context replacement (char to replace `&` in the rule body, special values: `~` space)
* `<score>` integer (default `0`)
* `<weight>` positive integer (default `1`)

Specifying multiple headers for a single body is a shortcut equivalent to creating multiple single-header rules with the same body.

#### Rule body

Contains three `@` symbols at its core.
* First `@` ... defines the *relative* LHS position of the non-terminal symbol
* Second `@` ... marks the boundary between the LHS (required context) and RHS (replacement)
* Third `@` ... defines the *relative* position of the RHS non-terminal replacement

Minimal example:

```
# on an instant time step silently replace A with B
==ATB
@@@
```
Example:

```
# when user presses key `e` rewrite A with B (if surrounded by x's)
#  and surrounding x's by o's (play sound C) and color the foreground
#  in red and background in yellow 
=CAeB13
   x   o
  x@x@o@o
   x   o
# when user presses key `e` rewrite B with A (if surrounded by o's)
#  and surrounding o's by x's (silently) and color the foreground
#  in yellow and background in blue  
==BeA34
   o   x
  o@o@x@x
   o   x
```
Complex example (shortcut combining both the above rules):

```
=CAeB13xo
==BeA34ox
   &   &
  &@&@&@&
   &   &
```
### Initial symbols

Initial symbols are optional and define starting symbols to be placed on screen.

`^<inital-symbol-char><vertical-placement-char><horizontal-placement-char>`

**Special case:** Plain `^` (with no characters following) requests screen clearing before placing other starting symbols. This is useful for utility programs that need a clean slate.

**Example:**
```
^        # Clear screen first  
^Scc     # Then place S symbol at center
```

The chars can be one of the following. There are uppercase variants 
to force column indices divisible by 2 to allow defining full-block
(double the character width) grammars, for the more or less square
look of the 'pixels'.

* vertical
  * `u` upper row
  * `l` lower row
  * `L` lower row but index divisible by 2
  * `c` approximate middle row
  * `C` approximate middle row with index divisible by 2
  * `X` random row but index divisible by 2
  * `<other>` random row
* horizontal
  * `l` left edge of the screen
  * `r` right edge of the screen
  * `R` right edge of the screen but divisible by 2
  * `c` approximate center column
  * `C` approximate center column divisible by two
  * `X` random column but divisible with 2
  * `<other>` random column 
### Configuration directives

**Status Line Templates:**
* `#!<template>` ... defines status line template with variable substitution (must be first line)
  - Template variables: `{score}`, `{steps}`, `{moves}`, `{parallel}`, `{help}`
  - Example: `#! Score: {score} | Steps: {steps} {parallel} | {help}`
  - Template inheritance: Last program with `#!` directive sets template for all subroutines
  - If no `#!` directive, inherits template or uses default: `Score: {score} Steps: {steps} {parallel} {help}`
* `#help <text>` ... defines help content for `{help}` variable in template
  - Help text is always local to current program (no inheritance)  
  - Example: `#help Snake: a/s/d/w move, space/x/q general`

**Inherited vs Local Content:**
- **Inherited text**: Put directly in `#!` template - persists across all subroutines
  - `#! Sokoban: {score} | {help}` → "Sokoban:" shows in all subroutines
- **Local text**: Put in `#help` directive - changes per program  
  - `#help Level Select: w/s choose` → only shows in current program
- **Design choice**: Balance persistent branding vs contextual flexibility

**Template Variables:**
- `{score}` - Current score (accumulated across program switches)
- `{steps}` - Number of rules applied (accumulated across program switches)  
- `{moves}` - Number of successful user actions that resulted in rule application (excludes timing events and ineffective keypresses)
- `{parallel}` - Parallel rule execution percentage, e.g. `(85%)` (empty if no threading stats)
- `{help}` - Current program's help text from `#help` directive

**Status Line Layout:**
- Template content is displayed on the left side
- Last applied rule pattern is always displayed right-aligned  
- Template content is truncated if needed to leave space for rule display

**Examples:**
```
# Pattern 1: Inherited branding + local help
#! Sokoban: {score} | {moves} moves | {help}
#help Level 1 - push boxes to targets
# → Subroutines show: "Sokoban: 42 | 15 moves | Level Select: w/s choose"

# Pattern 2: Fully flexible (everything local)
#! {score} | {moves} moves | {help}
#help Snake: a/s/d/w move, space/x/q general
# → Subroutines show: "42 | 15 moves | Menu: w/s select e/enter"

# Pattern 3: Minimal template
#! {help}
#help Tetris: w/rotate s/drop a/d/move
# → Shows only contextual help, no counters
```

**Best Practices:**
- Always use `{help}` in templates rather than embedding help text directly in `#!`
- Plain text in `#!` works but loses variable substitution (not recommended)
- Use `#help` directive for all contextual help text to maintain clean separation
* `#include <filename>` ... include another file at this position (recursive includes supported, circular includes ignored)

**Timing:**
* `#timing <char> <interval-ms>` ... define timing trigger (e.g. `#timing T 500` makes T fire every 500ms)
  - Use interval `0` for immediate timing (fires when no other input occurs)
  - Multiple timing directives supported for different characters
  - No timing events occur unless explicitly declared

**Engine Actions:**
* `#control <char> <action>` ... define engine control actions:
  - `#control ~ pause` ... space toggles pause/unpause
  - `#control x restart` ... restart current program
  - `#control r reset` ... reset to top-level program from stack
  - `#control c clear` ... clear screen and restart current program with its starting symbols (runtime clearing)
  - `#control t return` ... pop call stack, return to caller (or quit if at top-level)
  - `#control q quit` ... quit application

Note: For clearing at program load time, use plain `^` as a starting symbol. For runtime clearing during program execution, use `#control c clear`.

**Other:**
* `#grid <width> <height>` ... define grid alignment for toroidal wrapping; defaults to 1/1
* `#threads <count>` ... define thread count for parallel rule execution; defaults to auto-detect CPU cores
* `#sound <char> <path>` ... define sound mapping (e.g. `#sound S sounds/click.wav`)
* `#program <char> <path>` ... define program mapping for switching (e.g. `#program 1 snake.cfg`)
* `#color <char> <color>,<attrs>` ... define color with attributes (e.g. `#color M 5,BOLD`)

### Program switching

Programs can call other programs using a compositional system that preserves derivation state.

**1. Define program mappings:**
```
#program 1 snake.cfg
#program 2 tetris.cfg
```

**2. Use mapped characters in rules:**
```
=X1T~        # When X symbol and T key pressed, replace with ~ and switch to snake.cfg
@@@
```

**Key features:**
- **Compositional:** Derivation state (screen contents) flows between programs
- **Call stack:** Programs can return to their caller using `#control return`
- **Standard rules:** Program switching uses normal rule syntax with RHS replacement  
- **File completion:** Supports `.cfg`, `.gz`, and directory/index.cfg resolution

**Note:** For stack operations (return, quit, reset), use `#control` actions instead of program mappings.

**Example call/return pattern:**
```
#! main.cfg - calls utility, replaced S with R on T
#program U utility.cfg
#control R return
=USTR
@@@


#! utility.cfg - does work (replaces R with U on T) and returns  
#control R return
=RRTU
@@@
```

### Color attributes and control remapping

**Color with attributes:**
* `#color <char> <color-code>,<attribute>` ... define color with attributes
* Available attributes: `BOLD`, `DIM`
* Examples:
    * `#color M 1,BOLD` - define 'M' as bold red
    * `#color D 7,DIM` - define 'D' as dimmed white
    * `#color P 5,BOLD` - define 'P' as bold magenta

**Control key remapping:**
* `#control <old-key> <new-key>` ... remap control keys
* Available controls: `B` (long step), `M` (medium step), `T` (instant step), `q` (quit), `~` (unpause/space)
* Examples:
    * `#control ~ ,` - remap unpause from space to comma
    * `#control q .` - remap quit from 'q' to period
* Note: ESC key always works as emergency exit regardless of remapping

## Multithreaded Execution

The grammar engine supports parallel rule execution for improved performance in complex scenarios like Conway's Game of Life.

### Thread Configuration

Use `#threads <count>` to control threading behavior:

* `#threads 0` - Auto-detect CPU cores (default)
* `#threads 1` - Single-threaded mode (original behavior)
* `#threads N` - Use exactly N threads

### Execution Semantics

**Single-threaded mode** (`#threads 1`):
- Finds all applicable rules for the current trigger
- Randomly selects exactly one rule based on weights
- Applies that single rule

**Multi-threaded mode** (`#threads >1`):
- Finds all applicable rules for the current trigger
- Randomly selects up to N non-conflicting rules (where N = thread count)
- Uses area-based conflict detection to ensure rules don't overlap
- Applies all selected rules simultaneously in parallel

**Key difference:** Multi-threaded mode can apply multiple rules per step, fundamentally changing program behavior compared to the traditional one-rule-per-step execution.

### Performance Impact

Multi-threading provides significant speedup in scenarios with many independent rule applications (e.g., cellular automata). The engine displays threading statistics in the status line as `Steps: X (Y%)` showing step count and parallelization percentage.

## TODO

Not yet covered by this introduction:

* special chars `!` and `%` in rule bodies.
* local memory (used e.g. in `flowers.cfg`)
* `#` char as an implicit (outer) screen boundary
