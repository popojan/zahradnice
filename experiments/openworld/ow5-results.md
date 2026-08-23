# OW-5 — the sweeps: ε × wound phase map, and the α>β dissection

Date: 2026-08-23. Drivers `ow5_phase.py` (1,200 runs) and
`ow5_duel.py` (400 runs + 30-seed ledger); raw data `ow5_phase.csv`,
`ow5_duel.csv`; exact accounting 1,600/1,600. Verdict up front:
**wounds are the immune system of the peak — mutation load kills
where selection is weakest, and heavier bombardment *accelerates*
rescue because expansion (and therefore mutation) rides the holes
wounds create. In the duel, α's whole advantage is stamp-budget:
politeness costs it everything (0:100), quadrupling β's mover flips
the duel outright (0:100), and quadrupling β's handler does nothing
— night-4's contested/uncontested dichotomy survives the lift to
law space intact.**

## Part A — phase map (4-allele arena, OW-3 mutation, 30 seeds/cell)

P(survive) at a fixed ~10.6k-event horizon; M = T-events per
[p q] wound block (wound share of events = 2/(M+2)):

**γ-start (rescue):**

| ε \ M | 50 | 25 | 12 | 6 |
|---|---|---|---|---|
| 0 | 0 | 0 | 0 | 0 |
| 0.001 | 13 | 9 | 11 | 9 |
| 0.003 | 17 | 19 | 17 | 14 |
| 0.01 | 17 | 19 | 18 | **24** |
| 0.03 | 17 | 18 | **24** | 23 |

**α-start (retention):**

| ε \ M | 50 | 25 | 12 | 6 |
|---|---|---|---|---|
| 0 | 30 | 30 | 30 | 30 |
| 0.001 | 28 | 30 | 30 | 30 |
| 0.003 | 23 | 25 | 29 | 30 |
| 0.01 | **19** | 24 | 23 | 28 |
| 0.03 | **18** | 21 | 26 | 25 |

Findings (both pre-registered predictions inverted):

1. **No error catastrophe up to ε=0.03** — rescue is monotone-ish in
   ε and saturates; Q1's predicted downturn is absent in this range.
2. **Damage fuels evolution.** At high ε, rescue *improves* with
   wound rate (pooled ε≥0.01: 47/60 at M=6 vs 34/60 at M=50,
   z≈2.5). Mechanism: mutation rides stamps, stamps ride expansion,
   expansion needs empty cells — wounds manufacture the very
   substrate of variation (night-5's "wounding = expression
   mechanism" recurring at law level).
3. **Mutation load is deadliest where selection is weakest.** The
   α-world degrades most at the *lowest* wound rate (M=50: 30→18
   across ε) and is nearly immune at M=6 (≥25/30 everywhere).
   The same wounds that kill a γ-world defend an α-world: they
   punish the degenerate laws mutation keeps seeding before those
   metastasize. Mutation–selection balance, materialized.
4. **The good corner is harsh + mutable**: at M=6, ε=0.01 gives
   both rescue 24/30 and retention 28/30 — a wound regime friendly
   to whoever can adapt, hostile to nobody but the frozen.
5. **Q4 ledger** (γ-start, pooled): mutant stamps land δ 34% /
   γ 31% / β 31% / α 5% — the standing load of an α-dominated world
   is one-third inert fossils and one-third parasites; the peak
   allele itself is the rarest mutant target because its own fires
   only stamp away from itself.

## Part B — the duel (100 seeds/arm, OW-2 arena, no mutation)

| arm | α wins | β wins | α-share | z vs 0.5 |
|---|---|---|---|---|
| base (α vs β) | 66 | 34 | 0.660 | +3.20 |
| polite (α needs empty east) | 0 | 100 | 0.000 | −10.0 |
| hboost (β handler w=4) | 65 | 35 | 0.650 | +3.00 |
| mboost (β mover w=4) | 0 | 100 | 0.000 | −10.0 |

Ledger (base, 30 seeds): α fires 66,753 events to β's 29,247
(2.28×); mean territory 14.7 vs 8.5 gates; per-gate event rate
0.047 vs 0.036 (1.32×). Cross-stamp anatomy: β→onto-A 1,318 vs
α→onto-B 1,201 — **invasion is symmetric per stamp**; the naive
overwrite story (D2) is wrong as an asymmetry claim. What differs
is the *budget*: α buys 2.28× the paint.

Reading:

1. **The duel currency is law-painting throughput, bought with
   event share.** Remove α's constant firing (polite arm: dormant
   when intact, like a pure repairer) and it cannot even maintain
   its own gates against β's walk-through painting: 0:100.
2. **Night-4's dichotomy survives the lift to law space.** The
   mover rate is contested — w=4 triples β's painting share and
   flips the duel to 0:100. The handler rate stays *uncontested
   even during a law war* — holes in β territory are claimed by
   the local handler before any frontier process reaches them, so
   w=4 on the handler moves the share by 0.01 (nothing). D4
   confirmed, D5 (the predicted inversion) refuted: repair speed
   is a private good at every level we have now tested.
3. The all-or-nothing arms (0:100 both ways from a 66:34 baseline)
   suggest the duel sits near a bifurcation in painting-rate ratio
   — a hypothesis for a dedicated night, not a claim.

## Honest limits

Phase map at one ring and one horizon (the rescue–wound interaction
could shift with horizon); ε grid stops at 0.03 (the catastrophe
may exist beyond); duel ledger on 30 seeds; the bifurcation reading
of the 0:100 arms is uninstrumented.

## Exit → OW-6 (M2: currency)

Everything so far runs on free matter — α's winning strategy is
literally "spam writes forever". Fuel tokens in matter (resource
row, feed-and-consume as rules, chemostat drive) price exactly the
thing α spends: unconditional expansion. The M2 question inherited
from the design doc and night-11's rent-paying parasite: **does the
spam-champion survive being billed?** Predicted inversion candidate:
β's economical wound-triggered repair wins once writes cost fuel.
