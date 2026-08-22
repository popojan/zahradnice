# Inverse emergence, night 6: the stroke ladder — mechanism heredity without weight dials

Night 5's confessed sin: fitness was an authored rate (w=0.5 vs 1 on
identical rule shapes). Night 6 removes every dial. **All rule
weights are 1** (the mutation clock μ is the only fractional weight,
and it is lineage-symmetric). The law is a library of three walking
engines that differ only in STRUCTURE — how many rewrite events one
cell of progress costs:

    1-stroke   A --------> step    1 event/cell    trail B
    2-stroke   C -> G ---> step    2 events/cell   trail D
    3-stroke   E -> H -> I -> step 3 events/cell   trail F

Fitness is therefore the shared event budget itself (Peak-B's
thesis as a fitness function): wind-up strokes are events that buy
no distance. Handlers are the genome→mechanism map (trail glyph +
wound → that engine's ready head); mutation flips trail glyphs
among {B,D,F} symmetrically. Init: one engine alone. Driver
`night6.py`, data `night6_ladder.csv`; init {3-stroke, 1-stroke} ×
damage m {∞, 8, 2} × μ {0.001, 0.003, 0.01} × 24 seeds = 432 runs
of ~32k events, all trace↔dump exact, ~310 ms/run, 29 s wall.

Watch it: `./zahradnice demos/inverse/ladder.cfg` — green 3-stroke
evolves into the red 1-stroke, usually skipping yellow.

## Findings

**1. The ladder is climbed — 72/72 at m=8 — and mostly by
leapfrog.** Every moderate-damage slow-start run ends fixed on the
1-stroke engine; mean population fitness rises from 0.33 to
0.96–1.00 (a 3× structural improvement with no dial anywhere).
Paths: direct 3>1 leapfrog beats sequential 3>2>1 roughly 2:1
(direct F→B mutations exist, and once a 1-stroke is born it
outruns everything, including 2-stroke sweeps in progress — clonal
interference visible as 3>2>3>2>1 and 3>1>2>1 churn at higher μ).

**2. Heavy damage turns adaptation into evolutionary rescue.** At
m=2 the 3-stroke resident is *subcritical* — the night-3
budget-share cliff, hit structurally: repaint costs 3 events/cell
against a poke every 3rd event. Un-rescued populations die at
median 237 events. Survival happens only when a faster engine is
born AND establishes before collapse (rescued runs' first 1-stroke
birth: median ~145 events — the race is tight). Rescue probability
is **non-monotone in mutation supply**: 5/24 (μ=0.001) → 8/24
(0.003) → 3/24 (0.01).

**3. The reason it is non-monotone: error catastrophe.** At m=2,
μ=0.01 even the OPTIMAL engine, started as resident, goes extinct
in 19/24 runs (median t_death 5,667 — slow load-driven decay, vs
237 for structural collapse; at μ=0.001 it survives 24/24).
Mutation is rescuer and executioner at once, so rescue peaks at
intermediate μ. And failed rescues still buy time: at μ=0.01 every
dying slow-start run had mutants born, and their deaths stretch to
median 2,910 events — an order of magnitude of borrowed time.

**4. Stored variation again inert without damage.** m=∞: 144/144
no births; trail genotype drifts toward mutation load (the
"genotypic fitness" column rises to 0.49 at μ=0.01) with zero
phenotypic change — the night-5 expression law reproduced in a
richer genome space.

**5. The arrow holds.** 1-stroke-start: 0/144 displacements ever
(deaths at m=2 high-μ are error catastrophe, not displacement —
no slower engine ever took over a living population).

## Consistency across nights

Night 3's phase diagram (budget-share collapse) predicted which
engines are viable at m=2: the 1-stroke (weight-1 archetype)
survives, the 3-stroke cannot — night 6 confirms both, and adds
that the boundary is load-dependent (error catastrophe shifts it).
Night 4's law (selection on contested rates) is why stroke count is
selectable at all: strokes spend the shared budget. Night 5's
expression law (wounds transcribe trail into heads) is unchanged in
the 3-genome alphabet.

## Method note: the third static-vs-dynamic-truth incident

The first sweep classified 60 extinct runs as "resident holds":
population samples are emitted per APPLY, so a dead run's sample
tail still shows its last living population — the classifier never
saw the emptiness. Caught by a consistency check (landed-poke count
37 of 10,666 is impossible for living matter), fixed by judging
death from the final state (which the exactness check pins to the
engine's own dump). Same lesson class as zen-scoring and night 5;
it now has three instances and deserves promotion to a standing
rule: **any observable derived from event-driven samples is blind
to absorbing states; always close the loop on ground-truth state.**

## Honest limits

- The engine library (three gaits) is authored; evolution chooses
  from it. What night 6 established is that the CHOICE mechanism
  needs no dials: structural event-cost is selectable fitness under
  uniform weights. De-novo mechanism *composition* — genomes
  encoding behaviour in open-ended pattern space (tape/polymerase
  designs; pair-cell genomes) — is the remaining remove and the
  actual summit ridge.
- Fitness metric mixes trail+head mass; m=∞ rows report genotypic
  (stored) fitness, phenotypically inert. m=2 fitness averages are
  survivor-biased (dead runs contribute their last living quarter).
