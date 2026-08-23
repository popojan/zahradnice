# OW-4 — the full-F2 landscape walk: 96 singleton alleles (F3)

Date: 2026-08-23. Driver `ow4.py`; raw runs `ow4_runs.csv`,
trajectories `ow4_traj.csv`; 320 runs, exact accounting 320/320.
Verdict up front: **the 96-cube is harsh and the walk is real —
discovery outruns rescue, mutational reach is bounded by the
lifetime of the matter a law maintains, and the headline surprise is
niche construction: a lineage that could not reach the censused
A-peak converted the world to B-matter and found the B-mirror peak
instead — a rule the static census graded dead. Viability is
matter-relative, and the world manufactures its own matter.**

## Setup

Every F2 menu rule is its own allele — the menu is exactly the cube
(lhs∈AB)×(rep∈AB~)×(req-east∈{∅,A,B,~})×(write-east∈{∅,A,B,~}) =
96, so **point mutation** = change one slot (degree 9). Mutation
stays stamp-borne (miscopy headers at weight ε), with one physics
tightening applied to the F3 compiler: **inheritance rides matter
creation** — an eraser write (space) stamps no law. OW-2/3 arena
otherwise unchanged (ring 24, `T×200 + 400×[p q T×25]`, ~10.8k
events, 40 seeds/cell). Night-2's k=1 census of this exact space:
one repairer (α = `A>A.writeA`), 3 walkers, ~90 frozen/dying laws.

Starts: uniform γ (`A>B.writeA`, 1 step from α), uniform walker2
(`A>B.writeB`, 2 steps, both paths through active intermediates),
and a per-seed **random regulatory row** (24-cursor builder chain —
compile-time randomness, fully replayable; P(α dealt at start)
≈ 22%).

## Results

| start | ε | survive | α-dominant | α discovered de novo |
|---|---|---|---|---|
| γ | 0.003 | 6/40 | 6 | 13 |
| γ | 0.01 | 9/40 | 9 | 22 |
| walker2 | 0 | 0/40 | 0 | 0 |
| walker2 | 0.003 | 1/40 | 0 | 0 |
| walker2 | 0.01 | 4/40 | 0 | 0 |
| random | 0 | 4/40 | 4 | 0 |
| random | 0.003 | 4/40 | 3 | 5 |
| random | 0.01 | 5/40 | 5 | 14 |

1. **Survival requires a spawner-class law.** Random-soup worlds
   without α in the initial deal die 35/35 at ε=0 (with α dealt:
   4/5 survive, at both ε=0 and 0.003). Every γ-start survivor
   discovered α first; zero no-discovery survivors exist anywhere.
   Mutation opens a genuine de-novo channel: at ε=0.01, 3/35
   α-absent soups were rescued by discovery.
2. **Discovery ≠ rescue.** γ-start at ε=0.01: α found in 22/40
   worlds, only 9 lived — finding the peak is necessary, sweeping
   it before wounds win is the second race. Below the peak more
   mutation helps on both counts (22 vs 13 discoveries, 9 vs 6
   survivals) — jointly with OW-3's peak result, the sign of ε
   depends on where the world sits.
3. **The mutation budget is material.** walker2 never discovered α
   in 120 runs despite sitting 2 steps away. Cause: its law
   *consumes its own substrate* — every fire converts an A to B and
   writes B, so the A-population that powers firing strictly
   declines; median tape death at **62 applies** (γ, which re-writes
   A east, sustains itself: median 150–232 and fires indefinitely).
   A law's reach in mutation space is bounded by the lifetime of
   the matter it maintains — OW-3's "evolvability is matter-bound"
   sharpened into a clock.
4. **Niche construction (the surprise).** walker2's five survivors
   are dominated not by α but by **`B>B.writeB`** — the B-mirror of
   the blind spawner, ONE lhs-flip from walker2. The ancestor
   flooded the ring with B-matter; in that self-made world the
   B-spawner is the repairer, and the census (which initialized
   with A-matter and graded `B>B.writeB` dead) was measuring the
   wrong landscape. One survivor even shows stable two-niche
   partitioning: `B>B.writeB` territory (B-accumulating) beside
   `B>A.writeB` territory (a B-anchored walker leaving an A-trail),
   each region under its matched law. Where night-4 found "no
   coexistence ever on a 1-D ring" for lineages on shared matter,
   laws coexist by *partitioning substrate niches they themselves
   produce*.
5. **Mutation-selection balance in the soup**: at ε=0 every
   surviving world is a gate-row monoculture (mean diversity 1.0);
   at ε=0.01 stationary diversity ≈ 3.2 (dominant + mutant cloud).
   One marginal survivor (random, ε=0.003) is a γ-remnant at
   alive=7 — the lottery walker limping at horizon.

## Pre-registered predictions, scored

P1 (γ climbs, below OW-3's rate) **confirmed** — 6–9/40 vs 33/50 in
the 4-allele world. P2 (walker2 climbs at a lower rate) **wrong in
the interesting direction** — it never reaches α at all; it
niche-constructs to the B-peak instead. P3 (random survivors
α-dominant; ε=0 survival only by initial luck) **confirmed** (12/13
α-dominant). P4 (fossil burden ≫ useful mutation) **not directly
measured** — mutant-fate accounting deferred to the OW-5 sweeps.

## Honest limits

Single wound rate and ring; horizon 10.8k events (longer horizons
might rescue more discoveries — the discovery→rescue gap is
horizon-relative); niche-construction observed in 5 runs (small n,
mechanism transparent though: the lhs-flip is 1 step and the
B-matter is the ancestor's own output); per-glyph mutant-fate
ledger not yet built.

## Exit → OW-5

The sweeps: ε × wound-rate phase map for the 4-allele system
(rescue window, error threshold, parasite regeneration), plus the
α>β mechanism dissection (overwrite-vs-mass hypotheses, the
polite-α arm, handler-weight intervention — testing whether
night-4's contested/uncontested law predicts which weights matter
at a law frontier).
