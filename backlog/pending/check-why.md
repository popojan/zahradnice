# `zahradnice-check why` — dynamic rule-match diagnostics

## Purpose

Answer the question every authoring session asks at least once:
"why did rule N (not) fire here?" Inputs are a cfg, a concrete
screen state, and a trigger. Output ranks rules by match outcome:
matching, near-miss, excluded.

This is the dynamic counterpart to the existing
`zahradnice-check explain --line N` (which decodes one rule's
geometry statically). It's now cheap to host in `zahradnice-check`
because headless mode made the engine matcher curses-free.

Headlines:

- One subcommand: `zahradnice-check why CFG --screen FILE --trigger K [--rule N]`.
- Reuses the existing engine matcher (`Derivation::apply_impl<true>`)
  via a small refactor so there's zero drift risk.
- Inputs are exactly the artefacts the test harness already produces
  (`--dump-screen -.txt`), so authoring + debugging share one format.

## Inputs

| Input | Source |
|---|---|
| cfg | positional arg |
| screen | `--screen FILE` — a `--dump-screen -.txt` file from `zahradnice-headless` |
| trigger | `--trigger K` — single character; `~` means SPACE (matches `--input` convention) |
| rule (optional) | `--rule N` — focus on the rule whose head is on cfg line N |
| screen size | inferred from the dump's row × max-col |

The screen dump's first row is the status line (program help + last
lhsa), not engine state. The tool skips it and treats rows 1.. as
the engine viewport — same row-0-is-status convention the engine
uses internally (`wrap_row` keeps row 0 for the status line).

## Algorithm

1. Load grammar from cfg.
2. Load screen dump → `wchar_t screen[rows][cols]` (row 0 from dump
   is discarded, row 1.. of dump becomes engine rows 0..). Build
   the non-terminal position index `x` by scanning every cell for
   chars that appear as LHS in any rule.
3. For each rule `r` in `g.R`:
   - **Excluded — trigger**: if `r.key != trigger && r.key != '?'`,
     classify as excluded with reason "trigger mismatch".
   - **Excluded — anchor absent**: if `r.lhs` doesn't appear anywhere
     in `x`, classify as excluded with reason "anchor not on screen".
   - Otherwise, for each `(R, C)` where `screen[R][C] == r.lhs`:
     - Call the matcher in **explain mode** (see below). Result:
       - `MATCH` → record (rule, R, C) as a matching position.
       - `NEAR_MISS_K` → record (rule, R, C, first-failed-cell, K)
         where K is the count of failing context cells, capped at
         some small bound (default 3).
       - `MISS` (more than K cells wrong) → drop unless `--rule N`
         focuses on it.
4. Print sections: Matching, Near-misses, Excluded. With `--rule N`,
   print a detailed per-cell breakdown for that rule at every
   anchor position.

## Engine refactor: `apply_impl<true>` → callback-based

The current matcher returns `bool` on first mismatch (correct for
the hot path; useless for "why"). Refactor to thread an optional
callback through:

```cpp
// Per-cell match outcome reported during DryRun.
struct CellProbe {
    int wrapped_r, wrapped_c;
    wchar_t expected;   // resolved (anchor/context/wildcard expanded)
    wchar_t actual;     // screen_chars[wrapped_r * col + wrapped_c]
    bool matched;
};

// Optional sink. If non-null, every probed context cell is reported
// and the matcher continues past mismatches to gather full coverage.
// If null, early-exit on first miss (current behaviour, hot path).
using ProbeSink = void (*)(const CellProbe&, void*);

template <bool DryRun>
bool apply_impl(int ro, int co, const Grammar2D::Rule &rule,
                ProbeSink sink = nullptr, void* sink_ctx = nullptr);
```

Hot path is preserved: when `sink == nullptr` the inner loop
short-circuits as today (verified by inspection of the generated
code under `-Os` — the constant-null branch folds away). When
`sink != nullptr`, the matcher runs the full LHS region without
early exit and reports each cell.

The returned `bool` retains its old meaning (match / no-match) so
callers that only want yes/no don't change.

**Why thread the callback rather than write a parallel matcher.**
The matcher logic has subtle special cases (`@`/`&`/`!`/`%`,
SPACE↔`~` normalisation, `'!' && ctx == rule.ctx` reject). A
parallel implementation in the check tool would silently drift
from engine semantics — exactly the failure mode this tool is
meant to *prevent*. One matcher, two views.

## Tool-side: `MatchReport` collection

```cpp
struct MatchReport {
    bool matched;
    std::vector<CellProbe> cells;  // every probed cell, in body order
};
```

The tool's sink fills `cells`. After the matcher returns, the tool
can:

- Count failed cells → near-miss bucket.
- Find the first failed cell → focused error message.
- Render an annotated body diagram (cell-by-cell ✓/✗) for `--rule N`.

## Output

### Default (no `--rule`)

```
$ zahradnice-check why programs/hex/index.cfg \
    --screen state.txt --trigger q

Matching rules (would fire on 'q'):
  hex.cfg:61  ==Oq~70o~a   anchor 'O' at (10, 40)
  hex.cfg:62  ==Oq~70o.a   anchor 'O' at (10, 40)
  hex.cfg:64  ==Oq~70~~    anchor 'O' at (10, 40)

Near-misses (≤3 cells off):
  hex.cfg:63  ==Oq~70owa   1 cell off at (10, 40):
                           (9, 38) expected 'w', got '_'

Excluded:
  hex.cfg:6   =QOQm        trigger mismatch ('Q' ≠ 'q')
  hex.cfg:75-86 ==Od…       trigger mismatch ('d' ≠ 'q')
  hex.cfg:88-102 ==Ow…      trigger mismatch ('w' ≠ 'q')
  ... (15 more, --verbose to list)
```

Coordinates are 0-indexed engine coords (the same row/col system
the trace and `explain` already use). Screen-row 0 = engine row 0
= immediately below the status line.

### Focused (`--rule N`)

For one rule, print the per-cell map at every anchor position.
Reuses the body-cell layout that `explain` already prints:

```
$ zahradnice-check why programs/hex/index.cfg \
    --screen state.txt --trigger q --rule 63

Rule hex.cfg:63  ==Oq~70owa  (lhs 'O', trigger 'q')

  Anchor 'O' at (10, 40):
    body  screen   expected  actual  outcome
    (0,0) (8, 38)  '_'       '_'     ✓
    (0,1) (8, 39)  '_'       '_'     ✓
    (1,0) (9, 38)  'w'       '_'     ✗  ← first miss
    (1,1) (9, 39)  'w'       '_'     ✗
    (2,0) (10,38)  '@'       'O'     ✓ (anchor)
    ...

  → would not fire at (10, 40): 2 context cells mismatch.
```

## Limitations (v1)

1. **Memory-restore (`$`)** rules can't be reasoned about from a
   screen dump alone — the `$` cell reads `memory[r,c]`, not
   `screen_chars[r,c]`. v1 flags rules whose body contains `$` as
   "match depends on memory state — not represented in screen
   dump". Fix later: take an optional `--memory FILE` from
   `--mem-snapshot`.
2. **`#threads >1` conflict resolution** is not modelled — the
   tool reports rules that *could* fire, not which one(s) the
   parallel scheduler would actually pick under contention. This
   matches `apply_impl<true>` semantics (it answers "is this rule
   applicable here", not "would it win the conflict resolution").
3. **Trigger pacing** (B/M/T timing) is not exercised — `--trigger`
   is a single key, not a step count. To diagnose "why didn't this
   fire over N steps", run headless with `--trace` and inspect the
   trace; `why` answers the per-step question only.

## Implementation order

1. Refactor `apply_impl<true>` to accept the optional probe sink.
   Verify zero overhead in hot path (size-build binary should not
   grow; spot-check generated assembly).
2. Add `screen-load` helper to `src/check/`: parse a `--dump-screen
   -.txt` file into a 2D `wchar_t` buffer, return rows/cols.
3. Add `why` subcommand to `src/check/check.cpp` that:
   - parses args (`--screen`, `--trigger`, `--rule`),
   - constructs a `Derivation` against an in-memory display
     (the `HeadlessDisplay` already in libgrammar is fine — we
     don't even render, we just need the matcher),
   - drops the loaded screen into `screen_chars` and rebuilds `x`,
   - iterates rules and runs the matcher with the probe sink,
   - formats the three-section output.
4. Tests: `tests/check/why-*` directory with cfg fragments + screen
   dumps + expected stdout. Reuse the existing `make test`
   harness.

Step 1 is the only engine-touching step. Steps 2–4 are self-
contained inside `src/check/`.

## Relationship to other backlog items

- `pending/program-validation.md` — the linter umbrella. This page
  is the dynamic-diagnostic chapter; static-lint chapters stay
  there.
- `pending/llm-authoring.md` — the "Trace introspection" section
  points here for near-miss diagnostics.
- `pending/debug-tooling-tetris-bughunt.md` — item 4 (`--explain`
  in the validator) overlaps the focused output format here. After
  this lands, that item collapses to "use `why --rule N` instead".

## Open questions

- Near-miss cap K: 3 by default is a guess. Could be `--near-miss
  N` flag. Worth tuning once we use it on hex/tetris.
- Should `why` accept a screen dump produced by the curses engine
  (F12 screenshot) interchangeably? Format is the same `.txt` /
  `.ansi` shape, so yes. ANSI input would need decolouring; for v1,
  require the plain `.txt` variant.
- Should we allow `--screen -` (stdin)? Yes, trivial; aligns with
  headless's `--input @-`.
