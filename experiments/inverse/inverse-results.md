# Inverse emergence, night 1: calibration on a known minimum

Question calibrated: given a behaviour predicate, can exhaustive
stratified search over an admissible grammar family recover the
*minimal* rule-set producing the behaviour — with exact accounting,
and at what cost per candidate? Target with known answer: smallest
sustained oscillator.

Pipeline: `gen_family.py` (family F1 + genotype→cfg compiler, single
source of truth for both compilation and replay semantics),
`analyzers.py` (trace→state reconstruction, exactness check, cycle
classification, predicates), `night1.py` (driver: sweep + verify).
Raw verdicts: `night1_sweep.csv`, `night1_verify.csv`.

## Family F1 (declared search space)

Genotype = a SET of rules from a 42-rule menu: lhs ∈ {A,B} × anchor
rewrite ∈ {A,B,space} × shape ∈ {self `@@@`, write-east `@@@X`,
require-east `@C@@`} with X,C ∈ {A,B,space}. Trigger `T`, weight 1,
init a single `A` at centre. All geometry is east-only on one row, so
the universe is a ring of `cols` cells (toroidal wrap). Admissibility
is by construction: everything the compiler emits parses and has
well-formed body geometry — no mutate-then-repair, no wasted runs.
The init deliberately breaks A↔B relabelling symmetry (a grammar
whose rules all anchor on B is dead matter), so no symmetry quotient
is applied; raw strata are k=1: 42, k=2: 861.

## Method invariants

- The engine is the only executor of dynamics (headless, `--screen
  6,6` → 5×6 field, one trigger byte per event, `--seed`, `#threads
  1`, `--trace`, `--dump-screen`).
- The state trajectory is reconstructed in Python from the trace
  (anchor positions + per-lhs rule idx) using the genotype's own
  write semantics, and the reconstructed final state is compared
  EXACTLY to the engine's screen dump every run. **3,075/3,075 runs
  exact** (2,709 sweep + 366 verify). Any drift between compiler
  semantics and engine semantics aborts the search.
- Classification per run (horizon H = input length): ABSORBED_EMPTY /
  ABSORBED_FROZEN (applies stall before H — sound as an absorbing
  verdict here because applicability is a deterministic function of
  state under a single trigger), FIXED (sustained period 1),
  TRANSLATION (sustained period ≥2, population vector constant over
  the cycle), POP_OSC (period ≥2, populations vary), APERIODIC (no
  sustained cycle within H, ≥2 observed periods required).
- Predicates, all-seeds consensus: **P_state** = class ∈
  {TRANSLATION, POP_OSC} (global state recurs); **P_pop** = POP_OSC.
- Anti-gaming verify stage: every sweep satisfier re-run on held-out
  seeds (11,12,13), 5× horizon (H=1000), and a second ring size
  (cols=8). All 61 satisfiers survived verification unchanged.

## Verdicts (exhaustive within F1)

**P_state: k\* = 1.** Two satisfiers: `A>~.writeA` (pure walker —
erase self, write A east; wraps the torus, global period = ring size:
6 and 8 measured) and `A>B.writeA` (walker leaving a B trail; after
one lap the trail is complete and the cycle is pure translation over
it). The torus is load-bearing: on a bounded field these would freeze
at the wall.

**P_pop: k\* = 2, proven by k=1 exhaustion.** The full k=1 census is
32 ABSORBED_FROZEN + 5 FIXED + 3 ABSORBED_EMPTY + 2 TRANSLATION —
no single rule in F1 oscillates a population. At k=2 there are
exactly 17 verified satisfiers, collapsing into four mechanism
classes by reachable dynamics:

| class | n | period | mechanism |
|---|---|---|---|
| M1 in-place flip-flop | 9 | 2 | `A>B.self\|B>A.self` core; req-space / write-space decorations reachably inert |
| M2 convert-and-step | 6 | 2×ring (12, 16) | one glyph converts in place, the other erases-and-writes east: a walking flip-flop |
| M3 two-glyph walker | 1 | ring (6, 8) | `A>~.writeB\|B>~.writeA`: walks one cell per event, alternating glyph — population oscillates while translating |
| M4 self-scaffolded context oscillator | 1 | 2 | `A>B.writeB\|B>A.reqB`: first fire writes a static B partner east; the partner never fires (its own east is empty) but is the load-bearing context for `reqB`. The oscillator builds its own wall, then leans on it. |

Watch M4 live: `./zahradnice demos/inverse/m4.cfg` (p destroys it —
contrast with the self-repairing `demos/inverse/repair.cfg`).

M4 is the census's genuine discovery: the only satisfier where a
context-match participates productively, and the smallest example in
F1 of a program constructing inert matter that functions as structure
(trace-verified: all applies anchor at one cell; the partner cell is
written once, never rewritten, never anchors).

Full k=2 census: 462 ABSORBED_FROZEN, 154 FIXED, 134 ABSORBED_EMPTY,
42 TRANSLATION, 28 APERIODIC (no sustained cycle within H=200 —
stochastic spreaders; not proven aperiodic), 17 POP_OSC, 24 MIXED
(seed-dependent class; includes 4 candidates that oscillate on some
seeds only — correctly rejected by the all-seeds predicate).

## Cost ledger

| stage | candidates | runs | wall (jobs=8) | per run |
|---|---|---|---|---|
| sweep, H=200 ×3 seeds | 903 | 2,709 | 2.0 s | 4.6 ms |
| verify, H=1000 ×3 seeds ×2 rings | 61 | 366 | 0.7 s | 7.4 ms |

Per-run cost is process-startup dominated (H=200 and H=1000 cost
nearly the same); ≈220 runs/s per core. Extrapolation for later
nights: 10⁵ candidates × 3 seeds ≈ 25 min at jobs=8 — enumeration
stays affordable up to roughly |stratum| ~ 10⁵–10⁶, after which the
plan is genotype-level stochastic search (MAP-Elites over analyzer
descriptors) with minimality claims downgraded from "minimum within
F" to "smallest found".

## Honest limits

- All minimality claims are **within F1** (east-only geometry, unit
  weights, single-A init, 1-D ring). The claim type is the point:
  stratified exhaustion proves per-family minima; the family is
  declared up front.
- Periodicity is empirical per run (sustained to horizon, ≥2 full
  periods), not proven; determinism is not assumed anywhere — the
  all-seeds consensus plus held-out-seed verification is the
  stochasticity guard.
- Periods of walking mechanisms are functions of ring size (measured
  at 6 and 8); the flip-flop family is geometry-independent, and the
  verify stage distinguishes the two automatically.

## Night-2 hooks

- Predicate library extends to perturbation-response (headless input
  can interleave a "poke" trigger mid-run → self-repair predicate:
  re-convergence after damage).
- Family lifts, in order of cost: both directions, vertical shapes,
  weight tiers, third glyph, 2-cell write shapes. Each lift multiplies
  the menu; the ledger above says when enumeration dies and search
  begins.
- M4's pattern (build inert structure, then use it as context) is the
  seed of the structure-construction predicates on the road to the
  summit question (self-copying without a copy primitive).
