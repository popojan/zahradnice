# Tracing, stats, and replay

Zahradnice can record every rule application during a session and replay it
later, deterministically, with automatic divergence detection. Use it to
reproduce intermittent bugs, verify engine changes don't break existing
behaviour, or study which rules dominate a program's runtime cost.

## CLI

```
./zahradnice [program] [options]
  program              Program path (default: current directory)
  --seed N             Random seed (default: time-based)
  --max-threads N      Worker threads (default: hardware cores)
  --trace PATH         Write event trace (forces single-thread)
  --stats PATH         Write per-rule stats summary
  --replay PATH        Replay a recorded trace; ignores other options
  --replay-delay MS    Delay between replay events (default 0)
  --replay-snapshot S  Comma-separated trace steps to screenshot during replay
  --screen R,C         Constrain engine to RxC viewport (≤ actual terminal)
```

Trace and stats files are line-buffered, safe to `tail -f` while a session
is running. The trace file is plain-text, tab-separated; one event per line.

## Recording

```
./zahradnice programs/tetris/index.cfg --seed 42 \
  --trace /tmp/tetris.log --stats /tmp/tetris.stats
```

Setting `--trace` automatically forces `thread_count = 1`. Single-threading
is required for replay determinism (parallel rule firing involves
thread-scheduling non-determinism that cannot be reproduced). Authors of
continuous-tick simulations who want full parallelism should record without
`--trace`.

Press F12 at any point during recording to drop a screenshot checkpoint;
both the screenshot files (`.txt` + `.ansi`) are saved and a `screenshot`
event is logged into the trace.

## Trace format

Header (always at top of file):
```
# zahradnice-trace v2
# seed=42
# screen=24,80
```

Then events, one per line:

| event | columns |
|---|---|
| `program_load`   | step, score, path |
| `program_unload` | step, score, path |
| `program_exit`   | step, score |
| `apply`          | step, score, src, trig, lhs, idx, ro, co, src_line, head |
| `screenshot`     | step, basename |

Columns are tab-separated. Apply lines:

- **step** — monotonic event counter (one per applied rule)
- **score** — score immediately after this event applied
- **src** — `k` if triggered by user keypress, `t` if by timing tick
- **trig** — the trigger character that caused rule lookup (a key, a
  timing char, or `?` for wildcard)
- **lhs** — the LHS non-terminal of the matched rule
- **idx** — index of the rule within `R[lhs]` (parse-order in the cfg)
- **ro, co** — screen coordinates of the matched LHS character
- **src_line** — line number in the source `.cfg` of the rule's
  `=...` head; pair with `zahradnice-check explain` to decode the
  rule's match/write geometry without grepping
- **head** — the rule's authored `=...` line (the same identifier the
  status bar shows for "last applied rule"); makes each line
  self-readable without consulting the stats file

Trace format is versioned in the header. v1 traces (without
`src_line`) are rejected by replay; convert them with the helper
script `scripts/upgrade_trace_v1_to_v2.py` (reads stats to fill
the new column).

The `(lhs, idx)` pair uniquely identifies a rule within the currently-loaded
program. The preceding `program_load` line tells you which program owns
those indices.

## Stats format

```
# program  programs/tetris/level-02.cfg
# applied  applicable  considered  reward  rule_key  lhs  idx  src_line  ctx  ctxrep  head  rhs_preview
4221       4221        4221        0       T         H    7    842       ~    ~       ==HfH77       HH...
...
```

Sorted by `applied` descending, tie-broken by `applicable_locs / max(applied, 1)`
descending. The wasted-applicability ratio surfaces idempotent-render
explosions and lottery-loser rules at a glance.

- **applied** — times this rule actually fired and committed
- **applicable_locs** — total dry-run successes (sum across all positions
  per call)
- **considered** — total dry-run evaluations (rule was eligible for the
  trigger key)
- **reward, rule_key, lhs, idx, ctx, ctxrep** — header fields of the rule
- **src_line** — line number in the source `.cfg` (jump straight to it
  in your editor)
- **head** — the authored rule line
- **rhs_preview** — first 24 characters of the body, for orientation

A new section is written every time the program changes (load → unload),
each starting with a `# program <path>` comment.

## Inspecting rules: `zahradnice-check explain`

A separate binary (`make zahradnice-check`) decodes a rule's
geometry — the kind of thing you reach for when a trace `apply` row
or a stats line looks suspect and you want to know exactly which
screen cells the rule reads vs writes.

```
./zahradnice-check explain programs/tetris/tetris.cfg --line 935
```

Output:

```
=== rule at programs/tetris/tetris.cfg:935 ===
  head     = ==vT~70
  lhs      = 'v'   (anchor char this rule rewrites)
  trigger  = 'T'
  rep      = '~'   (replaces '@' on RHS)
  ctx      = '?'   ctxrep = ' '
  fore=7 back=0  reward=0  weight=1
  orient   = horizontal (cq=3, co=0, cm=2, rm=1, rq=1)

  body grid:
          0  1  2  3  4
  r0:     ~  ~  .  v  ~
  role:   L  L  .  R  R
  r1:     @  ~  @  @  ~
  role:   L  L  B  A  R

  legend: L=LHS(read)  R=RHS(write)  B=boundary  A=anchor  .=empty

  matches (offset relative to anchor):
    (-1,-3) '~' — matches space
    (-1,-2) '~' — matches space
    (+0,-3) '@' — matches anchor char 'v'
    (+0,-2) '~' — matches space
  writes (offset relative to anchor):
    (-1,+0) 'v' — writes literal 'v'
    (-1,+1) '~' — writes space
    (+0,+0) '@' — writes rep '~'
    (+0,+1) '~' — writes space
```

### Selectors: `--line` vs `--head`

- `--line N` — select by `=...` head line. If N falls inside a body
  the tool falls back to the closest preceding head with a `Note:`
  line. Fragile under file edits: any insertion above the target
  line shifts the mapping.
- `--head 'STR'` — select by the literal head string (the trace's
  `head` column). Robust to line edits. If multiple rules share the
  head string (rare; happens when a generator stacks `=HEAD` lines
  above a single body) the tool prints all matches.

Use `--head` whenever you've edited the cfg between recording and
inspection. Copy the head string straight from the trace `apply` row.

### Discipline: keep traces aligned with their source

Trace `src_line` and `(lhs, idx)` are anchored to the **file as it
existed at recording time**. Edits between recording and inspection
break the mapping in subtle ways:

- **Appending rules at the end** of a cfg preserves all existing
  line numbers and indices. Always safe.
- **Inserting a rule of a new lhs** preserves indices for all other
  lhs's (idx is per-lhs in `R[lhs]`), but shifts line numbers below
  the insertion.
- **Inserting a rule of an existing lhs** shifts that lhs's
  subsequent indices *and* line numbers below.
- **Deleting a rule** likewise shifts.

Two safe patterns when a hunt requires file edits:

1. Append your changes; re-record after edits land.
2. Snapshot the cfg before editing: `cp tetris.cfg tetris.cfg.recording`.
   `--explain` against the snapshot continues to match the trace.

When the file has shifted but you don't want to re-record, fall back
to `--head 'STR'` lookup.

The decoded `(dr, dc)` offsets are relative to the anchor cell on
screen, which lives at `(ro, co)` per the trace. So a write at offset
`(-1, +5)` lands at screen cell `(ro - 1, co + 5)` — that's how to
attribute a "what overwrote my cell?" question without instrumenting
the engine.

## Replay

```
./zahradnice --replay /tmp/tetris.log --replay-delay 30
```

Replay re-feeds the recorded trigger sequence to the engine; normal rule
selection runs against the fresh state. With both RNGs seeded
(`srand` + `srandom`) from the trace header and single-thread enforced
during recording, the deterministic engine produces a bit-identical
trajectory until something in its logic actually changes.

Press ESC to abort replay early. The replay renders into a virtual viewport
of the recorded screen size — the host terminal must be at least that big,
but it can be larger (the unused area stays blank).

### Divergence detection

Replay compares each fired rule's authored head and post-event score
against the recording. The first mismatch is captured as a sticky
divergence marker and shown in the status line:

```
REPLAY DIV: ev=327 | DIV@327 rec='==MT$48~M'/200 live='==MT$48XM'/200 (ESC)
```

On exit, replay returns code `3` and prints a one-line summary to stderr
if any divergence occurred:

```
Replay diverged at event 327: recorded rule '==MT$48~M' score=200; live rule '==MT$48XM' score=200
```

This catches regressions cheaply, with no external tooling. Rule-level
mismatch is sufficient signal for most bug-hunting; for screen-state-level
verification, see screenshot checkpoints below.

### Screenshot checkpoints

For full-state comparison, drop a screenshot during recording (F12). The
trace records:

```
screenshot     1234    screenshot_20260505_180400
```

On replay, the corresponding screenshot is reproduced as
`screenshot_20260505_180400_replay.{txt,ansi}`. Compare with `diff` (or
`sha256sum`, or any image-diff tool on the `.ansi` rendering):

```
diff screenshot_20260505_180400.txt screenshot_20260505_180400_replay.txt
```

You can also **inject ad-hoc screenshot events** into a trace before
replaying. Just add a line `screenshot 0 my_checkpoint` anywhere in the
file before the program ends; replay produces `my_checkpoint_replay.{txt,ansi}`
at that point. The parser doesn't care how the line got into the trace.

## Worked example: catching a regression

Suppose you suspect a recent rule edit changes tetris's gravity behaviour
under specific multi-row clear configurations. The bug-hunting workflow:

**1. Capture a known-good baseline.**

```
git checkout known-good
make zahradnice-size
./zahradnice programs/tetris/index.cfg --seed 17 --trace baseline.log
# play through several line-clears, including the suspicious case
# ESC out
```

**2. Apply your change and replay.**

```
git checkout fix-attempt
make zahradnice-size
./zahradnice --replay baseline.log --replay-delay 20
```

If the change preserves behaviour, replay completes silently:

```
Replay completed: 2734 events, final score=68
```

If it regresses, replay halts on the first divergence and shows where:

```
Replay diverged at event 1842: recorded rule '==XTvgGSS' score=33; live rule '==XTv?(?)' score=33
```

The recorded rule head plus its `src_line` (now in the trace's
`apply` row directly) take you straight to the cfg line involved.
Pipe it through `--explain` to decode what cells the rule reads and
writes:

```
./zahradnice-check explain programs/tetris/tetris.cfg --line 1842
```

From there, the trace events around step 1842 show what state the
engine was in just before the divergence — read the preceding 20
lines of the trace, you'll see exactly which screen cells were
touched, in what order, and with which triggers.

**3. (Optional) screenshot for full-state confirmation.**

For a row-by-row diff of the screen at the exact moment things go
wrong, capture screenshots at chosen steps without mutating the trace:

```
./zahradnice --replay baseline.log --replay-snapshot 1841,1842
diff snapshot_step1841.txt snapshot_step1842.txt
```

If you also want to compare against a known-good capture, take the
baseline run with `--replay-snapshot` first, save the outputs, switch
to the fix-attempt build, re-run replay with the same step list, and
diff the two snapshot sets.

## Determinism contract

Replay is bit-exact when:

- Both runs use the same engine binary (or only changed rule-emission /
  metadata; rule-selection logic is unchanged).
- The trace header's `seed` and `screen` are honoured by replay (they
  are, automatically).
- Recording was made with `--trace` (forces single-thread).

Replay is *informatively divergent* when:

- Engine logic actually changed in ways that affect rule selection or
  application.
- The trace records a session that legitimately depends on engine
  behaviour you've now altered.

In both cases, the divergence event identifies the exact step at which
old and new behaviour diverged, with rule heads and scores side by side.

## Caveats

- **No audio in replay.** SDL mixer is not initialised in replay mode;
  visual-only.
- **Multi-threaded recordings are not supported.** Recording with
  `--max-threads N > 1` and no `--trace` is fine for performance, but
  replay always runs single-threaded; multi-threaded sessions can't be
  faithfully reproduced.
- **Engine-action rules are re-applied via normal rule selection.**
  `clear`/`pause`/`return`/`quit` engine actions execute on replay as
  they did originally. The trace's `program_load`/`program_unload`
  markers ensure the cfg cache is in sync with the recording.

## Internal cost

Instrumentation adds a few hundred bytes of code in `libgrammar.a` and
~16 bytes per (program, rule) at runtime via the stats map. Trace logging
costs one `fprintf` per applied rule. With instrumentation off (no
`--trace`/`--stats`), the cost is one predicted-not-taken branch per
increment site — unmeasurable.
