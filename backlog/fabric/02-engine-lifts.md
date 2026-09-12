# Engine lifts the ladder may ask for

Status: proposed 2026-09-12. House rule for this line, set by the user:
engine changes are **allowed** whenever they serve the goal — the
"per-program features go in the cfg" rule is suspended here. The
discipline that replaces it: every lift names the rung that triggers
it, and no lift is built before its rung needs it.

Ranked by when the ladder meets them.

## L-A Episode protocol in headless (trigger: R0.1, immediately)

What the supervised protocol needs per sample: feed a phase trigger
*until quiescent*, then let the harness read the output row, then feed
the next phase. Today:
- `--input` is open-loop (G1), final-frame only (G2), and a settled
  program still pays a full scan per no-op event (the `idle_cpu` note in
  CLAUDE.md), so over-feeding `i` characters works but wastes scans.
- G6 (feed-until-quiescence) is the deferred item that exactly matches
  "inference is done when no rule applies".

Smallest lift: a repeat marker in the input language, e.g. `i*` =
"feed `i` until it applies nothing", implemented in
`headless_runner.cpp` where the loop already knows whether a step
applied anything. Second smallest: `--dump-every PHASE` or an
incremental stdin mode (G1) so the harness can read the output row
mid-run for R2.2's error-sign computation. Together they are dozens of
lines and close G1, G2 and G6 in one stroke, for every future
experiment, not only this line.

## L-B Data in and out (trigger: R0.1)

- **In:** zero-change option is a *write head*: rules on triggers `0`/`1`
  advance a head glyph along the input row writing the bit. Cost: one
  event per input bit. Fine through 8×8. A `--plant FILE` per episode
  (caller-supplied starting symbols already exist for menus) would make
  a 28×28 sample one call instead of 784 events — build only when the
  head is the bottleneck, which is after tier 3.
- **Out:** the score channel *is* the metric (a scoring rule fires on
  "correct output cell fired ∧ label present"), exactly accounted and
  replayable. No lift.

## L-C Numeric glyph classes (trigger: rule-count pain in R0.1/R3.1)

Signed magnitudes of range N need 2N glyphs and rules enumerated per
glyph (fire rules with header weight k; ±1 learning rules per k).
Generators absorb this comfortably to N≈8 (a few hundred rules). If a
rung wants N≈64 or Braille-as-8-bit-counter, the honest lift is a
laws-level numeric class: body/context tokens meaning "glyph in
family F with value ≥ v" and RHS tokens "value ±1", plus header weight
"= value". The prior verdict (§13(c): consider only if the friction
recurs broadly) stands; this line is the second occurrence after
genlib's size-inflation analysis, and on the GPU sibling numeric cells
are native anyway — so prefer the sibling to the lift unless tier 4
needs it in the repo.

## L-D A third dimension (trigger: dense inter-layer connectivity)

Bands on a tall screen (`--screen R,C`) give layers with local
connectivity, which is what every rung on the ladder wants. A real
`#layers` directive with z-offsets in bodies would only be needed for
dense (non-local) connectivity, which the fabric deliberately does not
have, or for 2-D input planes stacked in z (28×28 bitmaps as a plane
rather than a row) — that one *will* come at tier 5, and belongs to
the GPU sibling's data model, not to the curses engine.

## L-E Confluence checker (trigger: before R5.0, ideally with R0.1)

`zahradnice-check confluent CFG`: statically verify the CA-family
contract (foundations §3) — RHS writes only the anchor, every rule
anchored on a phase's undecided glyph reads no undecided glyph, each
phase's rewrites are write-once along the declared order. A checked
family is exactly parallel on any schedule; the checker is the
portability contract between the repo and the sibling, and it also
documents *which* Zahradnice programs are jump-chain-sensitive (all
the nights) and which are not (this line). Cheap, and it makes the
ladder's central claim machine-verified.

## L-F Family transpiler cfg → sibling rule table (trigger: R5.0)

A checked CA-family cfg is a list of (anchor glyph, offset pattern with
`!`/`%`/`&` classes, RHS glyph, weight, trigger). That is a table the
sibling can load directly. A small Python transpiler over the parsed
rule set (genlib already has the parser side) keeps the cfg as the
single authored artifact; the sibling never grows its own language
until a rung needs a primitive the cfg cannot say (counts; see
`03-gpu-sibling.md`).

## L-G Incremental matching (trigger: tiers 2–4 too slow in the repo)

With write-once phases, most anchors are settled most of the time; the
rule index (`anchors_for`, probes) already avoids scanning rules that
cannot match, but every event still walks all anchors of the trigger's
family. Dirty-region tracking (re-test only anchors whose window
changed since the last event) was estimated in §11.4 to buy as much as
a match-on-GPU design at a fraction of the effort. Build only if a
tier-4 rung is measurably scan-bound after L-A removed the no-op
scans.

## Explicitly not needed (keep rejected)

- **Runtime rule mutation (G3).** Weights are matter; a synapse glyph
  with header-weight-per-glyph is a mutable weight with laws untouched.
  The demotion of 2026-08-21 holds even harder here.
- **Real-valued cells.** The line's premise is Wolfram's: bits suffice.
  A float channel would be the thesis giving up.
- **Global reductions in the engine.** The bus (trigger) broadcasts;
  reductions happen in matter (wavefronts) or in the harness (teacher).
  A built-in "sum over the screen" would be action-at-a-distance,
  invisible in the trace — the same reason score-gating stays rejected.
- **A true back-arrow (run edits its rule table).** Same reasons as
  `substrate-mismatches.md` §0; structural plasticity edits *cells*,
  which is all Wolfram's "rewriting the network" needs.
