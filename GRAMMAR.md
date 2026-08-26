# Language

Zahradnice programs are configuration files (`.cfg`, optionally gzip-compressed as `.cfg.gz`) interpreted as 2D grammar-driven transformations on a terminal screen. This document is a complete reference. Source of truth: `src/grammar.cpp` and `src/grammar.h`; runtime semantics in `src/zahradnice.cpp`.

Companion documents: `GRAMMAR-pitfalls.md` (engine quirks that bite in practice), `HEADLESS.md` (driving the engine without a terminal), `TRACING.md` (instrumentation).

## Main loop

1. **Load a program**, recursively processing `#include` directives as text substitution. The assembled text is parsed line by line.
2. **Acquire a trigger**: either a user keypress, or a timing event (when a `#timing` interval has elapsed since last firing), or `0` (no event) when nothing is pending.
3. **Find applicable rules** whose trigger key matches and whose LHS context matches the screen state at some position.
4. **Sample one or more rules** (cumulative-weight random selection):
   - Normally exactly one rule per event.
   - Only for an *immediate* timing trigger (`#timing <c> 0`) under `#threads >1`: up to N rules whose footprints do not overlap. See [Multi-rule execution](#multi-rule-execution).
5. **Apply** the chosen rule(s): write replacement cells, update score, queue sounds, fire engine actions, or trigger program switches.
6. **Repeat** from step 2.

Screen row 0 is reserved for the status line. Rule rows are 1..N-1.

Key case matters everywhere: triggers, non-terminals, and context characters are compared literally.

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

> **Conversely**, any non-`=` line that *follows* a rule header is swallowed into that rule's body — including `^` seed lines and `#`-less text. Put every `^` initial symbol and every directive **before the first rule header**.

A line that begins with `#<keyword>` where the keyword is unknown is silently ignored. To comment out a keyword, prefix with a space (`# #timing B 500`) or `# `.

### Encoding

Files are decoded as UTF-8 to wide characters. Non-ASCII characters are valid in rule bodies, replacements, and as non-terminals; ASCII characters that have special syntactic meaning (`=`, `^`, `#`, `@`, `&`, `!`, `%`, `*`, `$`, `~`, `?`) cannot be used naively as terminals if they would conflict with the role they play in the local context — see the per-position rules below.

### Includes

`#include <path>` substitutes the contents of another file at that point in the assembled text. Resolution rules:

- `<path>` is resolved relative to the directory of the **current including file** (not the top-level program). An absolute path fails silently.
- The same path-completion logic as program loading applies: if `<path>` doesn't exist, try `<path>.gz`, or if `<path>` lacks a `.cfg`/`.cfg.gz` extension, try `<path>/index.cfg` and `<path>/index.cfg.gz`.
- Circular includes are silently skipped (each path is included at most once per top-level load).
- Includes may be nested.

Because includes are textual substitution, the order of declarations in the **assembled** text matters. Convention: include files containing only `#`-declarations early.

## Configuration directives

All directives use the form `#<keyword> <args>` (no space between `#` and keyword). A directive must precede any code that depends on it — `#sound`, `#program`, `#control` and `#color` are resolved while rule headers are being parsed, so a rule referring to a character declared *later* in the file silently gets the wrong meaning (typically: registered as a sound that does not exist, i.e. a no-op).

### Status line template

`#!<template>` — defines the status line template. **Must be the very first line of the file** (after include resolution): a blank line or a comment before it is enough to disable it silently. Variables substituted at render time:

| Variable | Meaning |
|---|---|
| `{score}` | Cumulative score (preserved across program switches). |
| `{steps}` | Successful steps. A step that applied several rules in parallel counts once. |
| `{moves}` | Steps triggered by user input only (excludes timing events and ineffective keypresses). |
| `{parallel}` | Parallel-execution percentage as e.g. `42%`; empty if no threading stats have accumulated. |
| `{help}` | Current program's `#help` text. |

If no program has declared a template, the default is:

```
Score: {score} Steps: {steps} {parallel} {help}
```

**Inheritance.** The active template is a single global, not a stack: whenever a program with a non-empty `#!` is loaded it becomes the template for every subsequently loaded program that does not declare its own — including programs returned to via the call stack. `#help` is the opposite: it is re-read on every program load, so it is always local to the running program (and becomes empty if the program declares none).

The practical split: put inheritable branding in `#!` (`#! Sokoban: {score} | {help}` keeps "Sokoban:" across all subroutines), put contextual text in `#help`. Prefer `{help}` in the template over literal help text so subroutines can override it.

Template content is rendered left-aligned. The most recently applied rule's header text is always rendered right-aligned on the same line, truncating the template if necessary.

### Help text

`#help <text>` — local-only help text (not inherited across program switches). Substituted into `{help}` in the active template.

### Timing

`#timing <char> <interval-ms>` — declares `<char>` as a timing trigger that fires every `<interval-ms>` milliseconds when no user input is pending. Multiple timings are allowed. `<interval-ms>` of `0` means "fire whenever no other event is pending" (immediate timing).

At most one timing fires per main-loop iteration. Overdue interval-based timings are checked first; only if none is overdue does an immediate timing fire. Within each of those two groups the order is **unspecified** (the timing table is a hash map, not declaration-ordered) — do not declare two interval timings that can come due simultaneously and expect a particular one to win.

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

Any other action word is accepted by the parser and then silently ignored at runtime.

A `#control` declaration on its own does nothing: engine actions are fired *by rules*, so the key must also be a rule trigger, and that rule needs an anchor that exists in every state the key must work from (scenery is the usual choice). For clearing at program **load** time use a bare `^` starting symbol; `#control <c> clear` is the runtime equivalent.

### Colour aliases

`#color <char> <color-spec>` — defines `<char>` as a colour alias usable in header fields `4` (foreground) and `5` (background). `<color-spec>` is `<digit>` or `<digit>,<attr>` where:

- `<digit>` is a colour code (see Colours below).
- `<attr>` is `BOLD` or `DIM` (curses attributes).

Example: `#color M 1,BOLD` makes `M` bold red.

When header field `4` or `5` contains a character that is not a digit, the engine looks it up in the colour-alias dictionary. Unknown aliases fall back to the default colour for that field. An alias may also override a digit, since the dictionary is consulted first.

### Transient characters

`#transient <chars>` — lists characters whose writes do **not** update the saved character in local memory (only the saved background is updated). Every character not listed is "sticky": writing it stores it in memory, so a later `$` restores it.

This is what moving sprites need. A non-terminal walking across scenery must be declared transient, or the trail it leaves behind is itself — see [Local memory](#local-memory) and the sprite pattern below.

### Grid

`#grid <width> <height>` — declares grid alignment for toroidal wrapping. Default is `1 1` (no alignment). Affects:

- The effective screen area used for wrapping: `(col / width) * width` columns by `((row - 1) / height) * height` rows.
- Initial-symbol placement when the position char is one of the uppercase variants `L`/`C`/`R`/`X` (grid-aligned).

### Threads

`#threads <count>` — sets the number of rules that may be applied in parallel per step. `0` (default) means auto-detect from CPU count. `1` means single-threaded (one rule per step). `>1` allows up to `<count>` non-conflicting rules per step, but only for immediate timing triggers. See [Multi-rule execution](#multi-rule-execution).

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

Starting symbols write the screen but **not** local memory — a `$` restore over a cell that was only ever painted by a `^` seed yields a blank, not the seeded character.

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

When multiple rules are applicable across all positions and rules, one (or more, in multi-rule mode) is selected by cumulative-weight random sampling, then applied.

### Header

A header is a single line of the form:

```
=S1234567 <score> <weight>
```

The labels `=`, `S`, `1`–`7` correspond directly to the character positions in the header string. The reference table below uses the same labels in its **Pos** column. Trailing fields may be omitted by leaving the header shorter; missing fields take their defaults.

| Pos | Field | Default |
|---|---|---|
| `=` | Header marker — always `=`, identifies the line as a rule header. | required |
| `S` | Sound / program / engine-action character. One of: `=` for silent; a `#sound` char to play that sound; a `#program` char to switch programs; a `#control` char to fire that engine action. (Resolution order: `#program` → `#control` → otherwise registered as a sound.) | `=` (silent) |
| `1` | LHS non-terminal — the character that this rule rewrites. Becomes a member of the non-terminal set V. | `s` |
| `2` | Trigger key. `~` is normalised to space (the SPACE key). `?` matches any trigger (wildcard). | `?` (wildcard) |
| `3` | RHS non-terminal replacement — the character written at the third `@` in the body (the LHS-anchor `@` is not written). The default is space, which is a **no-op write** (preserves whatever's at the LHS-anchor cell): if you want to *erase* the LHS-anchor cell to empty, use `~` here, not space. See "Body characters" for the space-vs-`~` distinction. | space (no-op) |
| `4` | Foreground colour. A digit `0`–`7` or a `#color` alias. | `7` (white) |
| `5` | Background colour. A digit `0`–`7`, `8` for transparent, or a `#color` alias. | `8` (transparent) |
| `6` | Extra context match — the character that `&` cells in the body's LHS region must equal, and that `!` and `%` cells are tested against. | (none) |
| `7` | Extra context replacement — character written at `&` cells in the body's RHS region. | space (no-op) |
| (space) | Separator between the field block and score/weight. | — |
| `<score> <weight>` | Whitespace-separated: an integer score and a weight. The weight may be a decimal (e.g. `0.01`) so rare events need not inflate every other weight; scores are always integers. Non-positive weight is clamped to 1. | `0` `1` |

The score/weight tail is read from a **fixed offset**: character 10 of the header line, i.e. immediately after the full nine-character field block `=S1234567` plus one separator space. A header that omits trailing fields and then appends a tail (`==ATB 5 2`) misparses silently — pad the field block out to full width first.

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

In field `6` (context match):
- `~` → matches an empty (space) cell. This is the token for "must be blank"; conversely `!` with field `6` set to `~` means "must be non-blank".
- `?` (or an omitted field) → **no context character is defined**. It does *not* mean "any character": a `&` cell can then never match, so the rule never fires. `!` cells, by contrast, match everything (nothing is equal to "no character"), and `%` cells match only field `7`.
- Otherwise: a literal character.

In field `7` (context replacement):
- `*` → the LHS non-terminal (substituted at parse time).
- `~` → writes a space.
- An omitted field (or a literal space) → no-op: `&` cells in the RHS region write nothing.
- Otherwise: a literal character.

There is only one context pair per rule, shared by every `&`, `!` and `%` cell in the body. A rule needing two different context characters must be split into two rules.

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

`./zahradnice-check explain CFG --line N` prints a rule's resolved geometry — which cells it reads and writes, at which offsets — and settles layout questions faster than counting columns by hand.

#### Body characters

| Char | Role in LHS region (matching) | Role in RHS region (writing) |
|---|---|---|
| (space) | No-op — neither matches nor writes. | No-op. |
| `~` | Matches a screen cell containing space. | Writes a space. |
| `@` | First/second/third occurrence have positional roles (see above); other `@`s are illegal. | — |
| `&` | Matches against field `6` (never matches if field `6` is unset). | Writes field `7` (with `*` meaning LHS non-terminal). |
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
# On any trigger, replace A with B.
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

Weights are relative *within one step's applicable set*. A tiny weight does not make an event rare when it is the only rule that matches — it will fire every step until something else becomes applicable.

### Multi-rule execution

Multiple rules per step are gated: they require `#threads > 1` **and** a trigger that is an immediate timing (`#timing <c> 0`) **and** an event that did not come from a keypress. Keypresses and interval-based timings always apply exactly one rule, so discrete-event semantics (one move per key, one tick per interval) are preserved regardless of thread count.

When the gate opens:

1. The applicable set is computed as above, then shuffled to remove order bias.
2. Up to `thread_count` rules are sampled one at a time (without replacement, weight-proportional). Each candidate's bounding box is computed over its **actual non-space cells** — LHS cells at the dry-run origin, RHS cells at the apply origin, boundary marker excluded. If the bounding box overlaps any previously selected rule's bounding box, the candidate is discarded; otherwise it is added to the selected set.
3. All selected rules are applied — concurrently if a global thread pool is available, sequentially otherwise. The score is incremented by the sum of rewards. All sounds are queued. Engine actions and program switches: only the first selected rule's are processed.

The conflict footprint is **conservative by design**: it covers read-only LHS cells as well as written ones. This guarantees that any parallel step's outcome is reachable by *some* single-threaded interleaving — multi-rule execution never produces a screen state that single-rule execution could not. The cost is lost parallelism in two situations: (a) two rules read the same cell but neither writes to it, and (b) two rules' bounding rectangles overlap but their actual non-space cells are disjoint (e.g., complementary L-shaped bodies). In both situations the rules will not co-fire in the same step; they will fire on consecutive steps instead, with no change to eventual screen state.

### Wrapping

All coordinate writes and reads are wrapped toroidally over the effective screen area:

- Rows wrap modulo `effective_max_row = ((row - 1) / grid_height) * grid_height`, mapping into `[1, effective_max_row]` (row 0 is reserved for status).
- Columns wrap modulo `effective_max_col = (col / grid_width) * grid_width`, mapping into `[0, effective_max_col - 1]`.

Cells beyond the effective area are not accessible; rules that anchor to wrapped positions implicitly operate on the wrapped cell. There is no off-screen: a walker that leaves an edge reappears on the opposite one, so no edge-handling rules are needed — and none can detect an edge either.

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

- By default **every** rule write stores the full `G` struct (the just-written char and colours) as the new memory value at that cell — non-terminals included. Memory is "sticky".
- For a character listed in `#transient <chars>`, only the **background** of the memory `G` is updated; the character and the rest of the saved struct are preserved. This is the overlay semantic that lets a sprite move through scenery without destroying it.
- Starting symbols (`^` lines) bypass memory entirely: they paint the screen only.

Memory is read as a side effect of:

- A rule body cell containing `$` in the RHS region — restores the cell to the saved `G`. This is the standard "restore the scenery" pattern when a sprite leaves a cell.
- A rule writing a cell whose background field is `8` (transparent) — the saved background is used.

The direct consequence: a moving non-terminal that is *not* declared transient overwrites memory as it goes, so restoring behind it reproduces the sprite instead of the scenery, painting a solid trail. Declare the sprite's characters `#transient`.

## Multithreading

`#threads <count>`:

- `0` — auto-detect from `std::thread::hardware_concurrency()`, falling back to 1. Recording a trace (`--trace`) forces 1 for replay determinism.
- `1` — single-threaded; one rule per step.
- `>1` — multi-rule execution as described above, subject to the immediate-timing gate.

A global thread pool is shared across all loaded programs (its size is set by `--max-threads`, defaulting to the hardware concurrency with a fallback of 4). Threading statistics (`{parallel}` template variable) accumulate over the lifetime of the engine process.

## Program switching and the call stack

A `#program <char> <path>` directive maps a character to a program. A rule whose field `S` is that character pushes the current program onto the call stack and loads the target program. The derivation state (screen contents) carries across the switch — programs are compositional, which also means a launched program inherits the caller's screen unless it clears (bare `^`) or floods (`^g**`) it.

`#control <char> return` pops one frame from the stack, returning to the caller. If the stack is empty, the engine quits.

`#control <char> reset` empties the stack and returns to the top-level program.

Call/return in full — `main.cfg` hands control to `utility.cfg`, which hands it back:

```
# main.cfg — 'U' calls the utility, replacing S with R
#program U utility.cfg
=USTR
@@@
```

```
# utility.cfg — does its work, then 'R' returns to the caller
#control R return
=RRTU
@@@
```

Stack operations (`return`, `reset`, `quit`) are `#control` actions, not `#program` mappings — a program cannot return to its caller by naming the caller's file, because that would push another frame.

ESC is always available as an emergency exit, regardless of declarations.

## Default keys

The engine itself reserves only:

- **ESC** — emergency exit (always).
- **F12** — capture two screenshots of the current screen (plain text and ANSI-coloured) named `screenshot_<timestamp>.txt` / `.ansi` in the current working directory.

All other keys, including space, `q`, `x`, `B`, `M`, `T`, must be wired through `#control` (for engine actions) or appear as a rule trigger (for program-defined behaviour). Programs start **unpaused**; SPACE pauses only if a rule wires `#control <c> pause`.

## Worked patterns

The bodies below are complete and were run against the engine; each can be pasted into a `.cfg` as-is.

### Sprite shifting with scenery preserved

A sprite `S` moves one cell right on `d`, restoring whatever scenery (`.`) it covered.

```
#transient S
==Sd$77.*
@&@@&
```

Reading the header: rewrite `S` on `d`; field `3` is `$`, so the cell the sprite vacates is restored from memory; fields `4`/`5` are white-on-white; field `6` is `.`, so the `&` cell to the right must be scenery; field `7` is `*`, which resolves to the LHS non-terminal `S`, so that neighbour becomes the sprite.

The body places `@1` and its `&` neighbour in the LHS region, and `@3` with its `&` neighbour in the RHS region; because both `&` cells sit at offset +1 from their own anchor, they address the same screen cell — the one being checked and then written.

`#transient S` is what makes the trail scenery rather than a line of `S`. Without it, memory records the sprite at each cell it passes and `$` faithfully restores it.

### Conditional move via `!`

A block `B` falls one row per tick, but only while the cell below is not a wall `W`:

```
#timing T 0
==BT~77W
@
!
@
@
B
```

Field `6` is `W` and the LHS cell below the anchor is `!`, which matches anything *other than* `W`. Field `3` is `~`, erasing the vacated cell; the literal `B` in the RHS region writes the block one row down. The body is vertical (the third `@` is below the first), so rows 0–1 are the LHS region, row 2 is the boundary, and rows 3–4 are the RHS region.

### Either-of via `%`

`%` matches a cell holding either field `6` or field `7`, which is how a rule accepts two alternatives without being split in two:

```
==ATB77xy
@%@@%
```

Here the neighbour may be `x` or `y`. Note that `%` and `!` are LHS-only: in the RHS region they are written to the screen literally.

## Not implemented

The following appeared in earlier documentation but are not implemented in current code:

- `*` as a context-match token (field `6`) meaning "the LHS non-terminal" — only field `7` gets that substitution; in field `6`, `*` is a literal asterisk.
- `$` as a context-match token (field `6`) — only `$` as a body **replacement** char is meaningful (memory restore).
- `#` as an "out-of-screen" context-match token — the toroidal wrapping leaves no cell out of screen, and the matching code does not specially recognise `#`.
- `?` in field `6` as a wildcard that makes `&` match anything — it disables the context character, and `&` cells then never match.
- `restart` engine action — `#control` accepts the keyword but the runtime has no handler; only `pause`, `clear`, `reset`, `return`, `quit` fire. Use `clear` or program switching for restart-like behaviours.
- `#control <old-key> <new-key>` as a control-key remapping mechanism — `#control`'s second argument is an action name, never a key. Remapping is done by changing the rule's trigger character.
- `B`/`M`/`T` as built-in "manual step" keys with long/medium/instant semantics — the engine attaches no meaning to them. They are ordinary keys, conventionally used as `#timing` characters.
