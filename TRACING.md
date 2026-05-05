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
# zahradnice-trace v1
# seed=42
# screen=24,80
```

Then events, one per line:

| event | columns |
|---|---|
| `program_load`   | step, score, path |
| `program_unload` | step, score, path |
| `program_exit`   | step, score |
| `apply`          | step, score, src, trig, lhs, idx, ro, co, head |
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
- **head** — the rule's authored `=...` line (the same identifier the
  status bar shows for "last applied rule"); makes each line
  self-readable without consulting the stats file

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

The recorded rule head plus `idx` and `src_line` (look up in the stats
file) take you straight to the cfg line involved. From there, the trace
events around step 1842 show what state the engine was in just before the
divergence — read the preceding 20 lines of the trace, you'll see exactly
which screen cells were touched, in what order, and with which triggers.

**3. (Optional) screenshot for full-state confirmation.**

If the divergence is subtle and you want to see the actual screen state
diverge, edit `baseline.log` to inject a checkpoint just before the
suspicious step:

```
sed -i '1842i\
screenshot\t1841\tcheckpoint_pre_clear' baseline.log
```

Re-record the baseline (with the same seed) so the pre-divergence
screenshot file exists, then replay against the new build:

```
diff checkpoint_pre_clear.txt checkpoint_pre_clear_replay.txt
```

A row-by-row diff of the screen at the exact moment things go wrong.

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
