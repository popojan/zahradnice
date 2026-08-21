# Language

Zahradnice programs are configuration files (`.cfg`, optionally gzip-compressed as `.cfg.gz`) interpreted as 2D grammar-driven transformations on a terminal screen. This document is a complete reference. Source of truth: `src/grammar.cpp` and `src/grammar.h`; runtime semantics in `src/zahradnice.cpp`.

## Main loop

1. **Load a program**, recursively processing `#include` directives as text substitution. The assembled text is parsed line by line.
2. **Acquire a trigger**: either a user keypress, or a timing event (when a `#timing` interval has elapsed since last firing), or `0` (no event) when nothing is pending.
3. **Find applicable rules** whose trigger key matches and whose LHS context matches the screen state at some position.
4. **Sample one or more rules** (cumulative-weight random selection):
   - **Single-threaded** (`#threads 1`): exactly one rule.
   - **Multi-threaded** (`#threads >1`): up to N rules whose write-and-read footprints (bounding boxes) do not overlap.
5. **Apply** the chosen rule(s): write replacement cells, update score, queue sounds, fire engine actions, or trigger program switches.
6. **Repeat** from step 2.

The screen row 0 is reserved for the status line. Rule rows are 1..N-1.

## Lexical structure

Each line of the assembled text is classified by its first character:

| First char | Meaning |
|---|---|
| `# ` (with space) | Comment — ignored. |
| `#!` (no space) | Status line template; **must be the very first line** of the program (after include resolution). |
| `#<keyword> ...` | Configuration directive (see below). |
| `^` | Initial symbol. |
| `=` | Rule header. |
| anything else | Body line, attached to the most recently seen rule header(s). |

> **Body-line escape**: a body line whose first character is `#`, `^`, or `=` is silently classified as comment / initial symbol / new rule header — its content is *not* added to the rule body. To author body cells whose leftmost column would land on `#`/`^`/`=`, indent the entire body uniformly by one space column (which preserves all anchor-relative offsets, since both `@` markers shift together). This is a load-time concern only; the engine itself never sees the dropped content.

A line that begins with `#<keyword>` where the keyword is unknown is silently ignored. To comment out a keyword, prefix with a space (`# #timing B 500`) or `# `.

### Encoding

Files are decoded as UTF-8 to wide characters. Non-ASCII characters are valid in rule bodies, replacements, and as non-terminals; ASCII characters that have special syntactic meaning (`=`, `^`, `#`, `@`, `&`, `!`, `%`, `*`, `$`, `~`, `?`) cannot be used naively as terminals if they would conflict with the role they play in the local context — see the per-position rules below.

### Includes

`#include <path>` substitutes the contents of another file at that point in the assembled text. Resolution rules:

- `<path>` is resolved relative to the directory of the **current including file** (not the top-level program).
- The same path-completion logic as program loading applies: if `<path>` doesn't exist, try `<path>.gz`, or if `<path>` lacks a `.cfg`/`.cfg.gz` extension, try `<path>/index.cfg` and `<path>/index.cfg.gz`.
- Circular includes are silently skipped (each path is included at most once per top-level load).
- Includes may be nested.

Because includes are textual substitution, the order of declarations in the **assembled** text matters. Convention: include files containing only `#`-declarations early.

## Configuration directives

All directives use the form `#<keyword> <args>` (no space between `#` and keyword). A directive must precede any code that depends on it.

### Status line template

`#!<template>` — defines the status line template. **Must be the first non-empty line of the program.** Subsequent programs in a call stack inherit the most recent program's template if they do not declare their own. Variables substituted at render time:

| Variable | Meaning |
|---|---|
| `{score}` | Cumulative score (preserved across program switches). |
| `{steps}` | Total rule applications (preserved across program switches). |
| `{moves}` | User-input rule applications only (excludes timing events and ineffective keypresses). |
| `{parallel}` | Parallel-execution percentage as e.g. `42%`; empty if no threading stats. |
| `{help}` | Current program's `#help` text. |

Template content is rendered left-aligned. The most recently applied rule's header text is always rendered right-aligned on the same line, truncating the template if necessary.

### Help text

`#help <text>` — local-only help text (not inherited across program switches). Substituted into `{help}` in the active template. Convention: put inheritable branding in `#!`, contextual help in `#help`.

### Timing

`#timing <char> <interval-ms>` — declares `<char>` as a timing trigger that fires every `<interval-ms>` milliseconds when no user input is pending. Multiple timings are allowed. `<interval-ms>` of `0` means "fire whenever no other event is pending" (immediate timing). Timings are checked in declaration order; the first overdue interval-based timing fires; only if none is overdue, the first immediate timing fires.

### Sounds

`#sound <char> <path>` — registers `<char>` as a sound trigger and loads the WAV file at `<path>`. Sound paths are resolved relative to the program file's directory (with fallback to current working directory). Reference `<char>` in rule header field `S` (sound) to play the sound when the rule fires.

### Programs

`#program <char> <path>` — maps `<char>` to another program file. When a rule with `<char>` in header field `S` fires, the engine pushes the current program onto the call stack and loads `<path>`. Path resolution is the same as for `#include`. Use a `#control <c> return` action to pop back.

### Engine actions

`#control <char> <action>` — registers `<char>` as an engine action. When a rule with `<char>` in header field `S` fires, the action runs. Recognised actions:

| Action | Behaviour |
|---|---|
| `pause` | Toggle pause/unpause. |
| `clear` | Clear screen and re-apply the program's starting symbols. |
| `reset` | Reset to the top-level program on the call stack (clears the stack). |
| `return` | Pop one frame from the call stack; quit if the stack is empty. |
| `quit` | Quit the application. |

### Color aliases

`#color <char> <color-spec>` — defines `<char>` as a colour alias usable in header fields `4` (foreground) and `5` (background). `<color-spec>` is `<digit>` or `<digit>,<attr>` where:

- `<digit>` is a colour code (see Colours below).
- `<attr>` is `BOLD` or `DIM` (curses attributes).

Example: `#color M 1,BOLD` makes `M` bold red.

When header field `4` or `5` contains a character that is not a digit, the engine looks it up in the colour-alias dictionary. Unknown aliases fall back to the default colour for that field. **Note:** the same dictionary is used; `#color` is the only directive that writes to it.

### Grid

`#grid <width> <height>` — declares grid alignment for toroidal wrapping. Default is `1 1` (no alignment). Affects:

- The effective screen area used for wrapping: `(col / width) * width` columns by `((row - 1) / height) * height` rows.
- Initial-symbol placement when the position char is one of the uppercase variants `L`/`C`/`R`/`X` (grid-aligned).

### Threads

`#threads <count>` — sets the number of rules that may be applied in parallel per step. `0` (default) means auto-detect from CPU count. `1` means single-threaded (one rule per step). `>1` allows up to `<count>` non-conflicting rules per step. See [Multi-rule execution](#multi-rule-execution) below.

## Initial symbols

`^<char><v-pos><h-pos>` — places `<char>` on the screen at program start.

- `<char>` defaults to `s` if absent.
- `<v-pos>`: vertical position. Default `c` (centre).
- `<h-pos>`: horizontal position. Default `c` (centre).

A bare `^` (single character, no payload) is a special **clear marker**: it requests that the screen be cleared before placing the rest of the starting symbols. Place it as the first `^` line:

```
^         # Clear the screen first
^Scc      # Then place S at centre
```

### Position characters

Vertical:

| Char | Position |
|---|---|
| `u` | Top row (row 1). |
| `l` | Bottom row (row N-1). |
| `c` | Approximate middle. |
| `L` | Bottom row aligned to grid height. |
| `C` | Approximate middle aligned to grid height. |
| `X` | Random row aligned to grid height. |
| `*` | **All** rows (fill marker, see below). |
| (anything else) | Random row. |

Horizontal:

| Char | Position |
|---|---|
| `l` | Left edge (column 0). |
| `r` | Right edge. |
| `c` | Approximate centre. |
| `R` | Right edge aligned to grid width. |
| `C` | Approximate centre aligned to grid width. |
| `X` | Random column aligned to grid width. |
| `*` | **All** columns (fill marker, see below). |
| (anything else) | Random column. |

Uppercase variants (`L`/`C`/`R`/`X`) require `#grid` to give meaningful results other than the defaults; with the default `#grid 1 1` they behave the same as their lowercase counterparts. They exist to support full-block (double-width) grammars where columns must be even-aligned.

### Fill marker `*`

A `*` in a position fills that whole axis: `^g**` floods the entire
field with `g`, `^gc*` writes a full row of `g` at the centre row,
`^g*l` a full column at the left edge. This is the dual of the bare
`^` clear marker (clear/fill duality) and replaces the common
"materialize the background with a one-shot spread cascade" idiom —
needed because rules cannot anchor on empty cells, so a background
symbol is the way to make emptiness matchable.

## Rules

A rule consists of one or more **headers** (lines starting with `=`) followed by a multi-line **body**. All headers immediately preceding a body share that body — equivalent to writing one rule per header with a copied body.

A rule is **applicable** at a screen position when:

1. Its trigger character matches the current trigger.
2. The screen character at the rule's anchor position equals the LHS non-terminal.
3. Every non-space cell of the rule body's LHS region matches the corresponding screen cell (per the matching rules below).

When multiple rules are applicable across all positions and rules, one (or more, in multi-threaded mode) is selected by cumulative-weight random sampling, then applied.

### Header

A header is a single line of the form:

```
=S1234567 <score> <weight>
```

The labels `=`, `S`, `1`–`7` correspond directly to the character positions in the header string. The reference table below uses the same labels in its **Pos** column. All fields except the leading `=` and field `1` may be omitted by leaving the header shorter; missing fields take their defaults. A single space separates the field block from the optional integer score and weight tail.

| Pos | Field | Default |
|---|---|---|
| `=` | Header marker — always `=`, identifies the line as a rule header. | required |
| `S` | Sound / program / engine-action character. One of: `=` for silent; a `#sound` char to play that sound; a `#program` char to switch programs; a `#control` char to fire that engine action. (Resolution order: `#program` → `#control` → otherwise registered as a sound.) | `=` (silent) |
| `1` | LHS non-terminal — the character that this rule rewrites. Becomes a member of the non-terminal set V. | `s` |
| `2` | Trigger key. `~` is normalised to space (the SPACE key). `?` matches any trigger (wildcard). | `?` (wildcard) |
| `3` | RHS non-terminal replacement — the character written at the third `@` in the body (the LHS-anchor `@` is not written). The default is space, which is a **no-op write** (preserves whatever's at the LHS-anchor cell): if you want to *erase* the LHS-anchor cell to empty, use `~` here, not space. See "Body characters" for the space-vs-`~` distinction. | space (no-op) |
| `4` | Foreground colour. A digit `0`–`7` or a `#color` alias. | `7` (white) |
| `5` | Background colour. A digit `0`–`7`, `8` for transparent, or a `#color` alias. | `8` (transparent) |
| `6` | Extra context match — character that `&` cells in the body's LHS region must match against (subject to special tokens below). | (none — equivalent to `?`) |
| `7` | Extra context replacement — character written at `&` cells in the body's RHS region. `*` is substituted by the LHS non-terminal at parse time. | space |
| (space) | Separator between the field block and score/weight. | — |
| `<score> <weight>` | Whitespace-separated: an integer score and a weight. The weight may be a decimal (e.g. `0.01`) so rare events need not inflate every other weight; scores are always integers. Non-positive weight is clamped to 1. | `0` `1` |

#### Special tokens

In field `2` (trigger):
- `~` → SPACE key.
- `?` → wildcard; rule fires regardless of trigger character.
- Any other character is a literal trigger key.

In fields `4` (foreground) and `5` (background):
- `0`–`7` are direct colour codes.
- `8` (background only) is transparent — the actual background at apply time is read from the cell's saved memory (see [Local memory](#local-memory)).
- Any other character is looked up in the colour-alias dictionary (`#color`).
- An unknown alias falls back to the field's default.

In fields `6` (context match) and `7` (context replacement):
- `?` in field `6` → "any character" (suppresses context matching for `&` cells).
- `*` in field `7` → the LHS non-terminal (substituted at parse time).
- Otherwise: a literal character.

### Body

The body is one or more lines of text following a header (or a stack of headers). It contains exactly **three `@` markers**:

1. **First `@`** — the anchor: the rule's LHS non-terminal position. The body cell here must equal the LHS character (field `1`) for the rule to apply.
2. **Second `@`** — the boundary marker: separates the LHS region (matched against the screen) from the RHS region (written to the screen). This cell is never matched and never written.
3. **Third `@`** — the RHS anchor: the position where the LHS non-terminal's replacement (field `3`) is written.

The body is parsed cell-by-cell. Each non-newline character occupies one cell; newlines advance to the next row. Body cells are resolved relative to the non-terminal's screen position, but the LHS and RHS regions use **different body-coordinate origins**:

- **LHS region** (dry-run, matched against screen): a cell at body position `(br, bc)` is checked at screen offset `(br − ro, bc − co)` from the non-terminal, where `(ro, co)` is `@1`'s position in the body.
- **RHS region** (apply, written to screen): a cell at body position `(br, bc)` is written at screen offset `(br − rq, bc − cq)` from the non-terminal, where `(rq, cq)` is `@3`'s position in the body.

For horizontal rules all three `@` markers are on the same body row (`ro = rq`), so row offsets are identical across the two regions. Column offsets differ by `cq − co` (the gap between `@1` and `@3`). A LHS cell at body column `co + Δ` and an RHS cell at body column `cq + Δ` both resolve to screen column offset `+Δ` — they reference the **same screen column** despite occupying different body columns. This is the standard idiom for writing to the same neighbour that was checked in dry-run.

The boundary direction is inferred from the layout: if the third `@` is to the right of the first `@`, the body is **horizontal** (LHS is to the left of the boundary, RHS to the right); otherwise **vertical** (LHS above, RHS below). Mixed layouts are not supported.

#### Body characters

| Char | Role in LHS region (matching) | Role in RHS region (writing) |
|---|---|---|
| (space) | No-op — neither matches nor writes. | No-op. |
| `~` | Matches a screen cell containing space. | Writes a space. |
| `@` | First/second/third occurrence have positional roles (see above); other `@`s are illegal. | — |
| `&` | Matches against field `6` (with `?` meaning any). | Writes field `7` (with `*` meaning LHS non-terminal). |
| `*` | At parse time, replaced by the LHS non-terminal. | Same. |
| `!` | Matches any cell whose contents are **not** equal to field `6`. | Written literally (likely unintended; avoid in RHS). |
| `%` | Matches any cell whose contents are **either** field `6` **or** field `7`. | Written literally (likely unintended; avoid in RHS). |
| `$` | Treated as a literal `$` for matching. | Restores the cell from local memory (the `G` struct previously saved at this position). |
| any other | Literal match against the screen cell. | Literal write to the screen, with the rule's foreground/background. |

**Spaces are always no-ops.** A literal space in the body neither matches nor writes anything. To match a space cell, use `~`. To write a space, use `~` (which is rewritten to space at apply time).

The boundary `@` cell is special: it is never matched in dry-run and never written in apply.

### Examples

Minimal silent rule:

```
# On any timing trigger, replace A with B.
==A?B
@@@
```

Context-aware rule:

```
# When the user presses 'e' and A is surrounded by 'x', replace A with B
# and replace each 'x' with 'o', play sound C, foreground red, background yellow.
=CAeB13
   x   o
  x@x@o@o
   x   o
```

Multi-header shortcut combining two complementary rules:

```
=CAeB13xo
==BeA34ox
   &   &
  &@&@&@&
   &   &
```

## Rule application semantics

### Selection

For trigger key `K`:

1. The set of non-terminals reachable by any rule with key `K` or `?` is computed.
2. The current screen positions of any of those non-terminals are gathered.
3. For each (position, rule) pair where the rule's key is `K` or `?` and the rule's LHS non-terminal equals the screen char at the position, the body's LHS region is dry-run matched against the screen.
4. The set of (position, rule) pairs that pass the dry-run is the **applicable set**.

If the applicable set is empty, the step is a no-op.

Otherwise, one applicable pair is sampled with probability proportional to `rule.weight`. The selected rule is applied: the body's RHS region is written to the screen, score is incremented by `rule.reward`, the rule's sound (if any) is queued, and the rule's program-switch / engine-action effect (if any) is fired.

### Multi-rule execution

When `#threads > 1`:

1. The applicable set is computed as above.
2. Up to `thread_count` rules are sampled one at a time (without replacement, weight-proportional). Each candidate's bounding box is computed over **all non-space body cells** (LHS region and RHS region together). If the bounding box overlaps any previously selected rule's bounding box, the candidate is discarded; otherwise it is added to the selected set.
3. All selected rules are applied — concurrently if a global thread pool is available, sequentially otherwise. The score is incremented by the sum of rewards. All sounds are queued. (Engine actions and program switches: only the first selected rule's are processed in the runtime.)

The multi-rule conflict footprint is **conservative by design**: it covers the entire body, including read-only LHS cells. This guarantees that any parallel step's outcome is reachable by *some* single-threaded interleaving — multithreaded execution never produces a screen state that single-threaded execution could not. The cost is lost parallelism in two situations: (a) two rules read the same cell but neither writes to it, and (b) two rules' bounding rectangles overlap but their actual non-space cells are disjoint (e.g., complementary L-shaped bodies). In both situations the rules will not co-fire in the same step; they will fire on consecutive steps instead, with no change to eventual screen state.

### Wrapping

All coordinate writes and reads are wrapped toroidally over the effective screen area:

- Rows wrap modulo `effective_max_row = ((row - 1) / grid_height) * grid_height`, mapping into `[1, effective_max_row]` (row 0 is reserved for status).
- Columns wrap modulo `effective_max_col = (col / grid_width) * grid_width`, mapping into `[0, effective_max_col - 1]`.

Cells beyond the effective area are not accessible; rules that anchor to wrapped positions implicitly operate on the wrapped cell.

## Colours

Eight base colour codes (foreground 0–7; background 0–8 with 8 = transparent):

| Code | Colour |
|---|---|
| 0 | Black |
| 1 | Red |
| 2 | Green |
| 3 | Yellow |
| 4 | Blue |
| 5 | Magenta |
| 6 | Cyan |
| 7 | White |
| 8 | Transparent (background only) |

**Transparent background.** When a rule writes a cell with background `8`, the actual background written is the one previously saved in local memory at that position (see below). This allows sprites to preserve the underlying scenery's background.

## Local memory

The engine maintains, for every screen cell, a saved `G` struct holding `(char, fore, back, fore_attrs, back_attrs)`. Initial values are `(' ', 7, 0, 0, 0)`.

Memory is updated as a side effect of writing cells:

- When a rule writes a **terminal** character (one not in the non-terminal set V) to a cell, the full `G` struct (the just-written char and colours) is stored as the new memory value at that cell.
- When a rule writes a **non-terminal** character to a cell, only the **background** of the memory `G` is updated; the rest of the saved struct is preserved. This is what enables sprites (non-terminals moving through scenery) to leave the underlying terminal characters intact in memory while overwriting the visible cell.

Memory is read as a side effect of:

- A rule body cell containing `$` in the RHS region — restores the cell to the saved `G`. This is the standard "restore the scenery" pattern when a sprite leaves a cell.
- A rule writing a cell whose background field is `8` (transparent) — the saved background is used.

## Multithreading

`#threads <count>`:

- `0` — auto-detect from `std::thread::hardware_concurrency()`, with fallback to 4.
- `1` — single-threaded; the original semantics: one rule per step.
- `>1` — multi-rule execution as described above.

A global thread pool is shared across all loaded programs. Threading statistics (`{parallel}` template variable) accumulate over the lifetime of the engine process.

## Program switching and the call stack

A `#program <char> <path>` directive maps a character to a program. A rule whose field `S` is that character pushes the current program onto the call stack and loads the target program. The derivation state (screen contents) carries across the switch — programs are compositional.

`#control <char> return` pops one frame from the stack, returning to the caller. If the stack is empty, the engine quits.

`#control <char> reset` empties the stack and returns to the top-level program.

ESC is always available as an emergency exit, regardless of declarations.

## Default keys

The engine itself reserves only:

- **ESC** — emergency exit (always).
- **F12** — capture two screenshots of the current screen (plain text and ANSI-coloured) named `screenshot_<timestamp>.txt` / `.ansi` in the current working directory.

All other keys, including space, `q`, `x`, `B`, `M`, `T`, must be wired through `#control` (for engine actions) or appear as a rule trigger (for program-defined behaviour).

## Worked patterns

### Sprite shifting with scenery preserved

Pattern: a sprite character `S` moves one cell to the right when the user presses `d`, leaving behind whatever character was there before.

```
# Header: silent, S→s on 'd', context match * (any char) replaced by $ (restore from memory)
==Sd  ?$
@@*$@
# LHS region: the sprite cell containing S, and the cell to its right (any non-space).
# RHS region: '$' restores the cell S vacated; new cell becomes S (the @ is replaced by 's').
```

(Sketch — exact field layout depends on whether the trailing column is part of LHS or RHS; the principle is `$` in RHS to restore.)

### Conditional rule via `!`

Pattern: a non-terminal `B` advances downward, but only if the cell below is **not** a wall character `W`.

```
=BB  W
@
@
```

With field `6` set to `W`, the body's LHS region uses `!` to require that the cell below B is anything other than W:

(Final layout depends on choice of horizontal/vertical body; the point is that `!` cells succeed exactly when the screen char is not equal to field `6`.)

### Either-of via `%`

Pattern: a rule fires if a context cell holds either of two characters (set in fields `6` and `7`). Use `%` in the body's LHS region.

## Known TODOs and unimplemented documentation claims

The following appeared in earlier documentation but are not implemented in current code; they are excluded from this spec:

- `$` as a context-match special token (field `6`) — only `$` as a body **replacement** char is meaningful (memory restore).
- `#` as an "out-of-screen" context-match token — the toroidal wrapping leaves no cell out of screen, and the matching code does not specially recognise `#`.
- `restart` engine action — `#control` accepts the keyword but the runtime has no handler; only `pause`, `clear`, `reset`, `return`, `quit` fire. Use `clear` or program switching for restart-like behaviours.
- `B`/`M`/`T` as built-in "manual step" keys with long/medium/instant semantics — only `T` has a special runtime effect (a 50 ms post-step sleep). `B` and `M` are ordinary keys; programs can use them as triggers but the engine attaches no semantics to them.
