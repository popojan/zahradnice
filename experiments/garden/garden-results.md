# garden: the MVP — species differing in learning capability (2026-08-21/22)

The experiment that earns the gardener her name: three species in one
toroidal seasonal world, identical in every metabolic respect,
differing ONLY in learning machinery — `n` (white, no learning), `i`
(yellow, linear reward-inaction), `p` (cyan, reward-penalty /
MENACE confiscation). **Reward is metabolic, not a score**: a
correct-in-season foraging attempt writes an offspring into adjacent
ground (learners deposit their arm token west — where the parent
itself reads it next event — in the same rewrite); a wrong attempt is
a wasted event; rent kills; selection is competition for vacancies.
Score tallies births as telemetry only; nothing reads it. Zero
engine changes; 59–77 generated rules (`gen_garden.py`); exact
per-species population + token accounting (`garden_stats.py`,
trace↔screen, **72/72 runs exact**).

Design notes that mattered: deposits must land where their OWN
lineage reads them (the first draft deposited east of the offspring —
the one direction catalysis cannot see; learners paid memory rent and
learned nothing); every attempt shares the same two-ground geometry
across species and arms (no mechanical bias); arms are
survival-symmetric *within* each species, so between-species
differences are learning machinery alone — with one honest exception
measured below.

## Regime scan (180k events, 6 seeds, mean populations)

| seasons | n | i | p | i's correct-share | p's |
|---|---|---|---|---|---|
| const | 316 | 396 | **416** | 0.613 | 0.607 |
| 90k | 332 | 405 | 403 | — | — |
| 30k | 338 | 398 | 404 | 0.534 | 0.592 |
| 10k | 338 | 403 | 393 | — | — |
| 4k | 348 | 390 | 407 | — | — |
| 2k | 355 | 397 | 382 | **0.318** | 0.433 |

Two honest surprises:

1. **No inversion at any speed — because fitness here is
   attempt-mass-dominated.** At 2k seasons the learners' memories are
   *anti-correlated* with the world (i answers wrong 68% of the
   time — tokens always reflect the previous block) and they STILL
   outbreed n, because catalytic tokens add attempt mass and a wrong
   attempt costs only a wasted event. Being busy beats being right
   when errors are cheap. (Fecundity selection swamps information
   selection — the confound is itself an eco-evolutionary finding.)
2. **The bandit's plasticity threshold didn't transfer** because the
   garden's memory is small and metabolically embodied (~110 tokens,
   flips in 5–10k events) where the bandit's 1200-token registry took
   ~15k to turn over: **the cost of plasticity scales with the size
   of the memory being rewritten.** The bigger the brain, the
   stabler the world must be.

## The toxic garden (TOX=0.25: a wrong attempt kills with p≈0.2)

Making errors expensive moves fitness from mass to information:

| seasons | n | i | p |
|---|---|---|---|
| const | 293 | 362 | **383** |
| 30k | 320 | 368 | **386** |
| 2k | 320 | 335 | **392** |

- i's edge over n collapses toward zero as seasons accelerate
  (69 → 15) — the plasticity threshold emerges once errors bite.
- **Punishment's value grows with switching speed** (p−i: +21 →
  +18 → +57): when stale knowledge is lethal, confiscating it fast
  is the winning trait. In the cheap-error garden, punishment was a
  *cost* at 2k (382 vs i's 397 — confiscation trades busy-ness for
  accuracy); in the toxic garden it is the *king* at 2k. **The value
  of unlearning is set by the price of error** — measured by
  flipping one environmental constant.

## Architecture evolution (mutation ladder n↔i↔p, start = pure n)

`garden-evo.cfg` (MUT=0.1, START=n): offspring occasionally carry the
neighbouring architecture; the world begins with twelve non-learners
and no learning anywhere. Results (6 seeds each, 18/18 exact):

- **Evolution discovers learning unaided**: both learning
  architectures emerge via the n→i→p mutation path and reach
  two-thirds of the field within 30k events.
- **The equilibrium is a stable polymorphism, not fixation** — and
  its shares quantitatively reproduce the fixed-species competition:
  toxic const 311/357/380 evolved vs 293/362/383 seeded; toxic p2
  326/348/371 vs 320/335/392. The garden's verdict is invariant to
  whether species are planted or evolved.
- Cheap p2 evolved: 365/394/396 — the non-learner stays fully
  competitive when errors are cheap, and the i-vs-p difference that
  fixed competition resolved (397 vs 382) is blurred below the
  mutational load (μ/2 flux homogenizes small fitness gaps).
- Diversity is the outcome, not a failure mode: no architecture ever
  fixates. Coexistence is held by immigration (design), by slow
  local competition (spatial refugia), and by a genuine stabilizer —
  **memory's space rent**: learner territory carries its token load,
  reducing its own vacancy supply, which keeps the lean non-learners
  in the game. An ecosystem answers nonstationarity with a portfolio
  of architectures, not a champion.

## The threshold, pinned (toxic garden, season-length scan)

Fixed three-species competition, toxic errors, 18/18 exact
(6 seeds/regime, mean populations):

| seasons | n | i | p |
|---|---|---|---|
| 8k | 322 | 373 | 372 |
| 4k | 322 | 359 | 376 |
| 2k | 320 | 335 | 392 |
| 1k | **347** | 340 | 353 |

The naive learner's edge over the non-learner vanishes between 4k
and 1k seasons; punishment stays ahead down to 2k and is marginal at
1k. **The adaptive-value-of-learning threshold sits at season
lengths of roughly 1-4k events, and punishment extends learning's
profitable range about fourfold toward faster worlds.**

## What the MVP demonstrates

Selection acting on learning *architectures* — not on traits — in a
shared world, with the ecology's own verdicts: learners beat
non-learners when information matters; naive learners degrade to
non-learner level in fast worlds; active unlearning wins exactly
where errors are lethal and frequent. All of it emergent from
population dynamics over immutable rules; the analysis never touched
a fitness function — fitness IS the population trajectory. Rules of
thumb earned: co-locate memory with its reader; cheap errors select
for activity, expensive errors for accuracy; memory size sets the
plasticity bill.

Not claimed: the mass-vs-information confound means the cheap-error
garden's learner advantage is largely fecundity, not intelligence
(documented, not hidden); parameters hand-tuned (W=0.2, C=1, M=0.02,
D=0.03, TOX=0.25); series files for const/p30/p2 on disk are the
toxic variant (prefixed `tox-`); deterministic regeneration of any
variant is one command.

Files: `gen_garden.py` (W/C/M/D/SEED/PUN/TOX/OUT), `garden.cfg`
(current = toxic), `garden_stats.py`, `gardensweep.sh` (CONDS),
`summary-garden*.csv`, per-run series. Watchable:
`./zahradnice experiments/garden/garden.cfg` — white forgets, yellow
remembers, cyan forgets *on purpose*; hold `b` to change the season.
