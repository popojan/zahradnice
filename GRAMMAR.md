# Language

## General controls

Key case matters.

* `SPACE` ... unpause program execution (programs are loaded paused)
* `x` ... reload current program (e.g. when terminal size changed or when in undesired state)
* `B/M/T` ... when paused simulate a single long/medium/instant step manually (rule application) 

## Main loop
1. **load a program** config
1. choose a **trigger key** based either on time lapse (B/M/T) or user pressed keys 
1. for the given trigger key find all **applicable rules** in the current state (based on non-terminals and their context)
1. **choose randomly** one of the rules (sample according to rule weights if unequal)
1. **apply** the chosen rule to change state and optionally alter score and/or play sound
1. **repeat** from 2. if the chosen rule is not a special rule:
   * quit rule (exit to shell)
   * program switching rule (load a given program and repeat from 2.) 

## Syntax

Lines starting with
* `# ` (space after #) ... comments
* `#keyword` (no space after #) ... configuration keywords (#timing, #color, etc.)
* To comment out keywords: `#timing 500 50 0` → `# #timing 500 50 0`
* If rule bodies need `#` at start of line, precede with spaces to avoid parsing as keyword/comment
* `^` ... initial symbol and its position
* `=` ... rule or special rule header
* otherwise the line forms a part of body belonging to the preceding rule headers

### Defining rules
Rules consist of one or more headers, and a rule body.

For the rule to be **applicable** to a char on screen these conditions must be met:

* trigger char matches
* non-terminal char matches with the char on screen at the given position
* surrounding context matches 

#### Rule header
`=<s-char><nonterminal-char><trigger-char><fore-color-char><bg-color-char><extra-context-char><extra-replacement-char><z-order-char> <rule-score-num> <rule-weight-num>`

i.e. these chars and tokens left to right `=S12345678 <score> <weight>`

* `S.` `=` for silence or a sound char previously defined using sound comments, i.e. `#sound S sounds/click.wav` 
* `1.` LHS non-terminal character (obligatory)
* `2.` trigger char (a rule is invoked by pressing corresponding key or by B/M/T time steps) (obligatory)
* `3.` RHS non-terminal replacement character (first @ in the rule body to be replaced by this char) (obligatory)
* `4.` foreground char (`0` black, `1` red, `2` green, `3` yellow, `4` blue, `5` magenta, `6` cyan, `7` white) (default `7`) or a dictionary entry value if not a digit
* `5.` background char (same as foreground plus `8` for transparent) (default `8`)
* `6.` extra required context char (special values: `?` for any, `*` for LHS char, `$` for char saved in memory, `#` for out-of-screen, `~` empty space) at each char `&` in the rule body
* `7.` extra required context replacement (char to replace `&` in the rule body, special values: `~` space)
* `8.` z-order layer char (greater values in front) (default `a`)
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

One or more lines beginning with `^` required.

`^<inital-symbol-char><vertical-placement-char><horizontal-placement-char>`

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
### Special comments

* `#!<Program description>` ... defines a help string shown on top when program execution is paused (e.g. on load) (has to be the first line of a program file)
* `#timing <B-step-ms> <M-step-ms> <T-step-ms>` ... define timing steps (long/medium/instant) in milliseconds; defaults to 500/50/0
* `#grid <width> <height>` ... define grid alignment for toroidal wrapping; defaults to 1/1
* `#sound <char> <path>` ... define sound mapping (e.g. `#sound S sounds/click.wav`)
* `#color <char> <color>,<attrs>` ... define color with attributes (e.g. `#color M 5,BOLD`)
* `#control <old-key> <new-key>` ... remap controls (e.g. `#control x r` remaps reload from x to r)

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
* Available controls: `B` (long step), `M` (medium step), `T` (instant step), `q` (quit), `x` (reload), `~` (unpause/space)
* Examples:
    * `#control x r` - remap reload from 'x' to 'r'
    * `#control ~ ,` - remap unpause from space to comma
    * `#control q .` - remap quit from 'q' to period
* Note: ESC key always works as emergency exit regardless of remapping

### Special rules
**Quit rule**

The `<replacement-char>` is irrelevant; trigger, non-terminal and its potential context in the rule body must be met for the rule to work.

```
=<s-char><nonterminal-char><trigger-char><replacement-char> quit
<left-context>@<right-context>@@
```
**Program switching rule**

Switches to a different program in runtime.
```
=<s-char><nonterminal-char><trigger-char><replacement-char> <relative/program/path/and/filename.cfg>`
<left-context>@<right-context>@@
```

The `<s-char>` can be on of the following

* `>` **keeps** the previous screen content, switches to a given program **running** it immediately 
* `]` **keeps** the previous screen content, switches to a given program **paused**
* `)` **clears** the screen, switches to a given program **running** it immediately 
* `|` **clears** the screen, switches to a given program **paused**

## TODO

Not yet covered by this introduction:

* special chars `!` and `%` in rule bodies.
* local memory (used e.g. in `flowers.cfg`)
* `#` char as an implicit (outer) screen boundary
