# OW-3 — mutation-selection walk on the censused landscape (F3)

Date: 2026-08-23. Driver `ow3.py`; raw runs `ow3_runs.csv`,
trajectories `ow3_traj.csv`. Verdict up front: **the open world
climbs — from the worst viable monoculture, mutation-selection
ascends to the allele the competition census ranks best (α-dominant
in 27/33 surviving worlds, α-majority reached by the first
checkpoint in all 33) — and the same mutation rate that rescues
worlds below the peak kills worlds at the peak (α-start survival
drops 50/50 → 37/50), partly by regenerating the parasitic law.
Evolvability itself is selectable structure: the non-expanding δ
cannot mutate at all.**

## Mechanism of mutation

Miscopy as a rule weight, fully in-table: for every stamping
(rule, allele g), one extra header per mutant target g′ with
ctx = g, ctxrep = g′, weight ε (`gen_gated.inherit_head(r, g, g2,
eps)`). A firing locus occasionally stamps a *different* law onto
the cell it expands into. Effective per-fire mutation ≈ 3ε/(1+3ε)
≈ 2.9% at ε = 0.01. The reachable law space is the four-allele
table — pre-censused ground (nights 1–2 statics, OW-2 dynamics).

Protocol: OW-2 arena (ring 24, tape full A, uniform regulatory
row), wound drive `T×200 + 400 × [p q T×25]` (~10.8k events),
50 seeds per cell, exact accounting 300/300.

## Results (survival and dominant law at horizon)

| start | ε = 0 | ε = 0.01 |
|---|---|---|
| γ (worst viable) | 0/50 survive (tape extinct, median 517 applies) | **33/50 survive: α 27, γ 4, β 2** |
| α (champion) | 50/50 survive, all α | **37/50 survive: α 30, γ 5, β 2** |
| δ (dier) | 0/50 | 0/50 — mutation cannot save it |

Three findings:

1. **The climb.** Every γ-start survivor reaches α-majority on the
   regulatory row, median by checkpoint 1000 (~9% of the horizon) —
   fast ascent, then stationary α-dominance under recurrent
   mutation load. The open world dynamically rediscovers what the
   OW-2 tournament found and the night-2 census permitted: the
   landscape's peak. (COEX at horizon is the expected stationary
   state under recurrent mutation; "dominant" is the right readout.)
2. **Mutation load cuts the other way at the peak.** The identical ε
   that rescues γ-worlds kills 13/50 α-worlds. In ≥5 of the 13, γ —
   OW-2's contested parasite — was the dominant law at a checkpoint
   before world death (a lower bound; checkpoints every 1000
   applies). Mutation-selection balance here is not a neutral tax:
   the mutant spectrum contains an invasive non-repairer, so load
   occasionally cascades into takeover-then-collapse. Which way
   mutation points depends on where the world sits on the landscape.
3. **Evolvability is structural.** δ-worlds cannot climb at any ε
   because mutation rides the stamp channel and δ never stamps: no
   expansion → no heredity → no variation. A law's mutability is
   not a parameter of the world but a consequence of the law's own
   material activity — the substrate's version of "evolvability is
   itself an evolved property."

## Honest limits

Four-allele law space (the walk is over censused ground by design —
that is the point, not a limitation, but generalising to the 96-rule
F2 table as singleton alleles is the obvious scale-up); single ε,
single wound rate, single ring; takeover-before-death established at
checkpoint resolution only; "dominant" thresholds not swept.

## The arc in one line

P0: law-in-matter is expressible under a frozen table. OW-1: the
gated world is *exactly* the censused physics (distributional
identity). OW-2: laws compete, selection ranks them census-
consistently, inheritance is load-bearing, and a contested
non-repairer is a lethal parasite on law-space. OW-3: the world
climbs to the censused peak, mutation load can regenerate the
parasite, and evolvability itself is matter-bound. All of it with
**zero engine changes**, exact accounting on every run, and A4
literally intact — the rule table never changed once.

Watch it live: `./zahradnice demos/openworld/lawclimb.cfg` — cyan
γ-monoculture, magenta mutation flashes, red α sweeps (or the world
dies first).
