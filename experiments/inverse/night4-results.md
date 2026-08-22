# Inverse emergence, night 4: heredity, and what selection actually selects

Natural selection composed from three verified mechanisms (repair,
damage-driven proliferation, variation): two lineages share one
24-ring and one mechanism — the night-2 archetype (unconditional
mover + empty-east handler) — with distinct glyph pairs, heads A/C,
trails B/D. **The trail is the genome**: one heritable bit,
spatially distributed; wounds respawn heads from the local trail, so
lineages breed true by construction. Movers overwrite foreign
matter (territory war). Head dead + trail alive = DORMANT
(resurrectable by a wound); last trail cell gone = EXTINCT
(absorbing). Selection knob: weight w ∈ {1, ½, ¼} on lineage-2's
handler (repair speed) or mover (walk speed); damage interval
m ∈ {∞, 16, 8, 4, 2}; 24 seeds; 24k-event horizon. Driver
`night4.py`, data `night4_selection.csv`; 600 runs, all trace↔dump
exact, 204 ms/run, 32 s wall (jobs=8).

Watch it live: `./zahradnice demos/inverse/heredity.cfg` (neutral
weights; green vs cyan, p = wound).

## Findings

**1. Heredity and the seed bank work.** Lineages breed true through
proliferation, merging, and dormancy cycles. At heavy damage
(m=2, w=¼ handler) the handicapped lineage goes head-dead and is
resurrected from its dormant trail in 21/24 runs (mean 4.8
resurrections/run; median dormancy 8.5 events, max 51). Trail as
dormant genome is exactly the bank/dormancy motif from the memory
triad, now arising in a 4-rule system.

**2. The selection dichotomy (the night's law).** Two traits of the
same organism, same weight handicap, opposite fates:

- **Walk speed is under absolute selection.** Mover handicap loses
  **240/240 runs** — at every damage rate *including none*, even at
  w=½. Median extinction of the slow lineage: 22 events — decided
  during the establishment chase, before the first wound. Mechanism:
  heads race for the same cells every event; the territory boundary
  drifts ballistically at the weight difference. Drift never gets a
  vote.
- **Repair speed is under no detectable selection.** Handler
  handicap is invisible at every damage rate (pooled fixation 43:53
  across 96 handicapped runs — drift; the w=∞-damage rows are
  bit-identical across w, confirming handlers are strictly dormant
  without wounds). The handicapped lineage repairs *late* but
  repairs: wounds are **uncontested** — a hole waits for its owner's
  handler, whose only competitor is a distant head walking toward
  it, a race even a 4× slower handler almost never loses.

The law: **selection acts on contested rates only.** The mover
competes head-to-head for the shared event budget every single
event (zero-sum territory conversion); the handler fires in a
private niche no rival can enter. This is Peak-B's thesis —
evolution when time is the contested resource — materializing
uninvited as a selection dichotomy: rate differences matter exactly
where processes pay from the same clock for the same cells.

**3. The announced hypothesis is refuted, and that's the result.**
Night 3 predicted "differential repair speed becomes selection,
strength rising with damage." Wrong in this geometry — repair is a
private good on a 1-D ring. For repair-rate selection to bind, the
wound itself must be contested (rival matter adjacent to the same
hole): 2-D fronts or boundary-clustered damage would create that.
Filed as the night-5-shaped question. **CLOSED (night 9, section D):** with claims contested from both sides of a hole, the same handicap that was bit-identically invisible uncontested becomes 24/24 lethal — see night9-results.md.

**4. Coexistence is always transient here.** No COEXIST outcome in
600 runs at the 24k horizon; drift-arm fixation completes in
~100–200 events (gambler's ruin on the head gap, ~gap² scaling).
A 1-D ring with overwrite competition has no coexistence mechanism
— niches, not rings, are where coexistence would live.

## Harness note

The weight knob required a header fix in the compiler: header fields
are positional and can only be omitted by truncation, so a
score/weight tail after a short field block gets misparsed as
ctx/ctxrep (silently: weight stays 1). `gen_family.head()` now emits
the full field block (`==DTC78   0 0.25`) when w ≠ 1 — caught by
`zahradnice-check explain` before it contaminated the sweep.
Sampler fairness was verified empirically along the way: 0.512 A
share over 1,800 two-mover events, 30 seeds (one 53:7 seed traced
to post-extinction monoculture plus an honest tail event, not bias).

## Where this leaves the summit

Multiplication (night 3), heredity and dormancy (tonight), and
selection (tonight, on contested rates) all exist in ≤6 rules. The
missing summit ingredient is **in-run variation**: lineages here are
authored, not born. A rare trail-glyph flip (low-weight rewrite rule
— mutation as fixed law) would let lineages *arise*; with selection
known to act on contested rates, the arena must make the mutant's
advantage a contested one. That is night 5.
