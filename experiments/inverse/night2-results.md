# Inverse emergence, night 2: minimal self-repair under point deletion

First discovery night (night 1 was calibration): what is the
smallest rule-set whose established behaviour survives damage?
Driver `night2.py`; family and harness in `gen_family.py`
(menu2, poke_rules); verdict logic in `analyzers.repair_verdict`.
Raw verdicts: `night2_sweep.csv`, `night2_verify.csv`.

## Setup

**Family F2** = F1 plus the combined require-east+write-east shape
(`@C@@X`: fire only when the east neighbour is C, write X there) —
96-rule menu, otherwise as night 1 (2 glyphs, east-only, unit
weights, single-A init, ring universe). Strata k=1 (96) and k=2
(4,560) exhausted.

**Damage as fixed law**: every candidate gets the harness postlude
`==Ap~` / `==Bp~` (not counted in k) — byte `p` erases one
weight-uniform random matter cell. On non-empty state a poke always
lands, so poke applies delimit trace segments exactly.

**Protocol**: establish T×200, then 3×[p + T×200] (sweep, seeds
1–3, ring 6); verify stage re-runs all sweep satisfiers with held-out
seeds 11–13, rings 6 AND 8, 5 pokes, horizons 400/400. Segments are
classified with the night-1 classifier; **REPAIR** = every
post-damage segment re-establishes the pre-damage (class, period),
with period compared per-ring (walker periods legitimately scale
with ring size). Exact accounting throughout: 14,664/14,664 runs
trace↔dump identical.

## Verdicts (exhaustive within F2)

**P_repair_static (a fixed structure heals): k\* = 1**, unique
satisfier `A>A.writeA` — the blind spawner: every A writes A east,
saturating the ring; a hole is re-filled by its west neighbour's
next fire (expected ~ring events under uniform sampling). The other
k=1 FIXED candidates (5) all die. At k=2 there are 99 verified
static repairers; 90 heal to the *identical* fixed state, 9 to a
different fixed point of the same dynamics (repair of *function*,
not of *form*).

**P_repair_dyn (an oscillating/moving behaviour heals): k\* = 2**,
16 verified satisfiers (12 TRANSLATION-pre, 4 POP_OSC-pre), all
16/16 surviving the harder verify. Night-1's minimal oscillators
all fail, as expected: every single-cell oscillator (flip-flop
family) dies to one poke; the pure walker likewise. The one partial
exception is instructive: the k=1 trail walker `A>B.writeA` repairs
when the poke hits its trail (the walker re-paints it next lap) but
dies when it hits the head — a damage-target lottery that the
all-seeds predicate correctly rejects (MIXED: DIED×2, REPAIR×1).

## The mechanism law

Both structural facts below were checked programmatically over all
16 dynamic satisfiers, not eyeballed:

1. **Damage is the regeneration signal.** Every satisfier contains
   exactly one rule conditioned on an empty east neighbour (`req~`
   or `reqwrite~·`). In the intact state the ring has no empty cell,
   so the repair rule is strictly dormant; the poke's hole is the
   only thing that can activate it. Quiescent-until-wounded repair —
   the release-of-contact-inhibition motif — is not one design
   option among several: within F2 it is the *only* way minimal
   dynamic self-repair exists.
2. **Mover + handler decomposition.** Each satisfier factors as one
   unconditional mover (a `write` shape that keeps the behaviour
   going) plus that one damage-conditioned handler. No satisfier
   uses two conditioned rules or two movers.

Example (the archetype): `A>B.writeA | B>A.req~` — A walks east
leaving a B trail (mover); a B that ever sees empty east — possible
only where a poke struck — turns into a fresh A head (handler).
Poke the trail: the walker repaints it. Poke the head: the hole
left by the erasure itself triggers the trail cell behind it to
respawn the head. The damage carries exactly the information the
repair needs: its own location.

**Time-to-repair** (480 recoveries, ring 6, seeds 21–26): median 5
events, mean 7.9, max 67 — sub-lap healing. Mechanisms whose
handler sits adjacent to any hole (trail-respawn family) heal in
median 3–6; those that must walk the mover to the wound heal in
median 9–11 with tails to ~70.

## Census (sweep, ring 6)

k=1 (96): 1 REPAIR, 83 pre-frozen, 4 pre-empty, 5 FIXED-then-died,
3 walkers (2 died, 1 the lottery case above).
k=2 (4,560): 3,289 pre-frozen + 410 pre-empty (the family's bulk),
380 FIXED died, 99 FIXED repaired; of dynamic-pre candidates,
TRANSLATION: 163 died / 12 repaired (+19 seed-lottery MIXED),
POP_OSC: 44 died / 4 repaired — **dynamic behaviour that survives
damage is rare (~7% of dynamic candidates) and never accidental**:
zero satisfiers lack the dormant handler rule. No poke-activated
candidates (frozen pre, dynamic post) reached consensus.

One sweep satisfier was killed by the verify stage:
`A>B.writeA|B>B.self` (static) degraded on 2/6 held-out runs — the
adversarial verify doing its job.

## Cost ledger

| stage | candidates | runs | wall (jobs=8) | per run |
|---|---|---|---|---|
| sweep, 803-byte protocol ×3 seeds | 4,656 | 13,968 | 10.7 s | 5.1 ms |
| verify, 2,405-byte ×3 seeds ×2 rings | 116 | 696 | 2.9 s | 16.2 ms |

## Batch-runner note (user question, answered)

Could the engine's own program-switching run whole candidate batches
in one process (chain candidates via `#program` next-pointers, bare
`^` clear marker for state isolation, `program_load` trace markers
as delimiters)? **Cfg-side: yes, exactly.** But the S-field
program/control dispatch lives only in the live curses loop
(`zahradnice.cpp` caller_stack); the headless runner fires such
rules as plain rewrites and drops the switch — a live/headless
fidelity gap. Filed in `backlog/pending/headless-program-switch.md`
with the justification sketch; not built now because subprocess mode
covers even a k=3 F2 stratum (~430k runs ≈ 5 min wall) and per-run
exactness checking is stronger than chain-end checking.

## Honest limits & night-3 hooks

- Minimality within F2 (east-only, unit weights, ring). The damage
  model is single point deletion with full recovery windows;
  sustained damage *rates* (poke frequency vs repair time — a
  criticality question) are the natural night-3 axis.
- Damage-as-signal is proven universal for k≤2 in F2; whether richer
  families admit minimal repairers with *internal* redundancy
  (surviving damage without an empty-cell detector) is open —
  requires shapes that can read a second channel (pair cells /
  second row).
- The repair-time tail (max ≈ 70 ≈ 11 laps) comes from sampler
  lottery, not mechanism: a weight lift on the handler would trade
  rule-cost for healing latency — weights enter the genotype at
  that point.
