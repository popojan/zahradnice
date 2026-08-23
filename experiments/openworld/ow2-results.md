# OW-2 — selection among laws (F3, open-world line)

Date: 2026-08-23. Driver `ow2.py`; inheritance emission in
`gen_gated.py`; raw runs `ow2_selection.csv`. Verdict up front:
**endogenous selection among laws exists, is ranked consistently
with the nights census, requires law-inheritance (the control arm
always dies), sits cleanly above a measured neutral-drift null — and
already exhibits the night-11 theme one level up: the inheritance
channel that group survival requires is exactly the channel a
non-viable law uses to persist parasitically and raise world
mortality.**

## Setup

Ring 24, tape row full of A, regulatory row built in equal blocks of
allele glyphs by a replayable builder cursor (night-11-style state
surgery). Drive: `T×200` establish, then 120 × [`p` `q` `T×25`] —
one tape wound (random A/B erased) and one gate wound (random allele
glyph erased) per block. Exact accounting (2-row replay vs dump) on
all 800 sweep runs: 800/800.

**Arms.** *Control*: OW-1-style gated rules — gates are read, never
written; law is territory that can only erode. *Treatment*:
inheritance stamps — every non-anchor tape write also writes the
firing locus's allele onto the target's gate cell (`&` in RHS with
ctxrep = allele), so expansion carries law, wounded or foreign
territory is colonised law-and-all.

**Alleles** (censused F2 genotypes): α `A>A.writeA` (static
repairer), β `A>B.writeA|B>A.req~` (dynamic repairer), γ
`A>B.writeA` (lottery walker), δ `A>A.self` (dier), plus ε ≡ β's
genotype under a second glyph — the **neutral pair** (β,ε) is a
pure-drift null band.

## Results (50 seeds per cell; win counts)

| config | control | treatment |
|---|---|---|
| α+β | DEAD 50 | α 35, β 15 |
| α+γ | DEAD 50 | α 39, DEAD 10, γ 1 |
| α+δ | DEAD 50 | α 50 |
| β+γ | DEAD 50 | β 32, DEAD 18 |
| β+δ | DEAD 50 | β 50 |
| γ+δ | DEAD 50 | DEAD 50 |
| β+ε (null) | DEAD 50 | β 28, ε 22 |
| melee αβγδ | DEAD 50 | α 36, β 8, DEAD 6 |

Sharpening at 200 seeds (treatment): **α+β = 135:65, z = +4.95**
against the fair-coin null; **β+ε = 102:98, z = +0.28**. The α
advantage is real selection; the neutral pair is exactly drift.

Reading of the matrix:

1. **Inheritance is load-bearing.** Without gate-writing, every
   world dies: gates erode, laws vanish locus by locus, the tape
   follows. No selection differential exists to measure.
2. **Selection ranks laws consistently with the census** — with one
   twist. Repairers (α, β) beat non-repairers everywhere; a world
   containing no repairer (γ+δ) always dies. The twist: the census
   graded α and β equally (both verified REPAIR); competition
   *ranks* them, and the blind spawner beats the elegant
   mover+handler archetype 2:1. Statics said "equivalent"; dynamics
   says "not". First dynamics-vs-statics discrepancy of the arc.
3. **A contested non-repairer is worse for the world than a dead
   law.** β+δ never dies; β+γ dies 18/50. Same repairer, same wound
   rate — the difference is the rival.

## Mechanism of point 3 (checked, not eyeballed; 20-seed replays)

- Stamp budgets β+γ: β 42,480 stamps, γ 4,025 — but cross-allele
  overwrites are nearly symmetric: γ→β territory 1,397, β→γ 1,482.
  γ spends ~35% of its stamps on conquest, β ~3.5% on conquest and
  the rest on maintenance. Invasion is a two-way war, not β mopping
  up.
- Mixed-phase duration (rival-law extinction time after build):
  γ persists median **304** applies (IQR 209–489) vs δ's **116**
  (98–132) against β; 534 vs 306 against α. The contested walker
  holds law-space ~2.6× longer, with a fat tail.
- Every locus under γ's law is repair-dead load; mortality is the
  integral of wounds over the prolonged mixed phase. δ, unable to
  stamp, is absorbed quickly and its territory converts to repairing
  law before wounds accumulate: 0/50 deaths.

Night-9's contested/uncontested vocabulary lifts one level: γ is a
*contested law* (fights for law-space through the same channel that
makes group survival possible), δ an *uncontested* one. Night-11's
group-selection inversion reappears above the matter layer: you
cannot have colonisation-based group repair without opening the door
to colonisation-based law parasitism.

## Honest limits

Single wound rate (1+1 per 25 events), single ring (24), block
inits, final-state winner metric; extinction-time and stamp anatomy
on 20 seeds. The α>β mechanism is hypothesised (α's unconditional
east-write invades B-trail cells that β's empty-east handler cannot
colonise, and α's 12-cell applicable mass paints continuously) but
not yet dissected — flagged for OW-3/night-grade treatment.

## Exit → OW-3

Mutation as weighted miscopy: per (rule, allele) an extra header per
mutant target with ctxrep = target glyph and weight ε — mutation
fully in-table, rate = a rule weight. Start from the worst viable
monoculture (γ-uniform) and ask whether the world climbs to the
censused repairers; δ-uniform documents an evolvability dead end
(no expansion → no stamps → no mutation channel). ε=0 is the
control.

Watch it live: `./zahradnice demos/openworld/lawwar.cfg` — β vs γ
frontier war, wounds ambient, p/q to wound by hand.
