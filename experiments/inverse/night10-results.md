# Inverse emergence, night 10: deceptive codons — the parasite that keeps the world diverse

Two deceptions, each a one-character edit of a night-8 honest codon,
both uniform and glyph-symmetric, tested in six arms on shared
seeds (plain / order / mut / full / para / paraonly) × m {8,4,2} ×
32 seeds = 576 runs, all exact, 21 s wall. Driver `night10.py`,
data `night10_ecology.csv` (with per-run ρ trajectories). Order
parameter: boundary density ρ (0 = crystal/monoculture, ~0.5 =
random).

- **mutator** (boundary-fueled): OTHER-glyph west + hole → write
  the WEST gene instead of the covered one. At a boundary the fill
  becomes a 50/50 contest between the covered gene and the west
  gene reaching through the machinery — infidelity IS contested
  copying (the night-4/9 law again).
- **deceptive pair** (order-fueled): night-8's pair-yield context
  (same-glyph west + 2-gap) but writing the OTHER glyph twice —
  the crystal's own yield mechanism spent on enemy copies.

## Findings

**1. The mutator fails by starvation.** All mut arms crystallize
completely (ρ 0.49→0.00, fidelity ≥0.985, cumulative mutator share
≤1.5%): the mutator feeds on boundaries, and boundaries are exactly
what the coarsening ratchet destroys. A deception that consumes its
own context is self-limiting — it delays the crystal and then
starves. (Notable in itself: even a 50% miscopy rate at boundaries
cannot stop the night-8 homogenization null.)

**2. The parasite creates a third phase.** Deceptive-pair arms
never crystallize: ρ stabilizes at 0.14–0.26 at every damage rate,
with or without the honest codon competing for the same context,
while every non-parasite arm reaches ρ = 0.00. The trajectories are
flat in the mean from the first checkpoint but fluctuate forever
(second-half sd 0.08→0.20 rising with damage; plain: 0.000) — a
stochastic limit cycle: coarsening grows runs → run context
regenerates → wrong copies re-seed boundaries → local order
collapses → coarsening resumes. **Order-fueled deception cannot
starve; the parasite and the crystal orbit an interior fixed
point.**

**3. The parasite is a matter-benefactor and an information-
corruptor at once.** Its tape levels MATCH the honest-codon arms
(13.9 vs 14.4 at m=4; 4.7 vs 4.7 at m=2) and beat plain in the
collapse regime (3.6 vs 2.5): wrong copies still fill wounds. The
commons thrives; the monoculture just never arrives. Corollary:
since ρ>0 requires both glyphs alive, this is the arc's first
PERMANENT two-type coexistence on the bare 1-D ring — night 4
concluded overwrite competition there has no coexistence mechanism;
deception is one.

**4. Standing variation without a mutation operator.** Nights 5–6
maintained variation by an authored mutation law; here diversity is
self-sustaining through pattern-encoded infidelity — the system
generates and regulates its own variation supply, forever. In an
evolvability ledger, the parasite arms are the only worlds of the
arc that never lose the raw material for future selection.

## The law of the night

**Deception persists iff it is fueled by the order it attacks.**
The sign of the coupling between deception rate and the order
parameter decides everything: boundary-fueled deception (positive
feedback on disorder it creates, negative on its own food) starves;
order-fueled deception self-regulates into permanent coexistence.
Same law as parasitology's: obligate parasites that kill their host
lineage die out; those that crop it persist.

## Honest limits & hooks

- Parasite "virulence" is fixed at rule-multiplicity 50/50; a
  virulence sweep (weight on the deceptive pair) would map the
  coexistence window and look for an error-catastrophe edge
  (night-6's, now pattern-driven).
- Oscillations characterized by second-half sd only; period
  structure unexamined (spectral analysis on longer horizons).
- Ring 24 only in the main sweep. **CLOSED (paper gap,
  night11_gaps.py): at equal machinery density (1 head/24 cells,
  rings 24 vs 48) the parasite plateau is ring-intensive — rho
  0.19-0.27 at both sizes for m>=4, plain crystallizing at both.
  New corner: at m=2 a SINGLE polymerase cannot sustain the phase
  (collapse to a pure-s remnant, rho=0, s=1.00); two heads can
  (rho 0.16-0.20) — the phase has a machinery floor at the
  collapse edge.**
- The 2-D remove (codon table in matter, germline/soma) remains
  queued; tonight showed 1-D still had this much left in it.
- **CLOSED (growth-law audit, night10_exponent.py /
  night10-exponent-results.md): the coexistence is NOT parabolic
  ("survival of everybody") kinetics in disguise — births occur at
  x=0 (all via the deceptive pair; order-arm control: 0 in 2.07M
  extinct events), extinction is non-absorbing (up to 7,276
  resurrections/condition), minority production is cross-dominated
  (up to 8:1) with negative naive growth exponents, and no
  mesoscopic spatial refuges exist. Refinement: at m=2 the phase is
  a resurrection ecology — permanence of the mixture, not of
  uninterrupted lineages.**
