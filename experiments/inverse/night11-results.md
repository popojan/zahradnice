# Inverse emergence, night 11: compartments vs the order-fueled parasite — the classical remedy inverts

The classical answer to parasites is compartmentalization: isolate,
grow, pool, re-inoculate — between-group variance plus differential
contribution suppresses what within-group competition cannot
(stochastic corrector; transient compartmentalization). Every model
in that literature assumes a replicase, a parasite that hurts
compartment growth, and free compartments. Night 11 ran the
classical protocol against night-10's order-fueled parasite.
Driver `night11.py`, data `night11_tc.csv`; chem {paraonly, plain}
× structure {bulk4, 2×24, 4×12, 8×6, bulk8; total capacity 48,
machinery matched} × m {8, 2} × mix {none, scr, chk} × 24 seeds
= 912 runs, all exact, 57 s wall.

Setup innovations (all cfg/harness-side, law identical everywhere):
compartments are screen ROWS — rule bodies are single-row, so rows
are strictly isolated column-torus rings that still pay from ONE
serialized event budget; damage lands matter-proportionally across
rows. Transient compartmentalization is the harness's pipette: every
1500 events, contents are pooled and re-dealt (scr = multiset
scatter, composition heritable but order not; chk = contiguous
chunks, runs partially heritable; none = pure isolation), heads
re-placed. Between-episode state surgery is exact via a builder
nonterminal (`B`, dedicated trigger bytes) that rewrites the screen
cell-by-cell from the input protocol; every episode trace-replays
byte-for-byte.

Predictions stated before running: (a) L6 inversion — compartments
maintain or raise the parasite band; (b) group selection has nothing
to grip, and at collapse regime cov(contribution, ρ) goes POSITIVE
(the parasite is a matter-benefactor); (c) scramble pooling
transmits no order, so TC cannot select on the phase regardless.

## Findings

**1. Compartments never suppress the parasite; at collapse they
feed it.** At m=8, compartmentalization alone is statistically flat
(Δρ −0.005..−0.008 vs matched bulk, |t| ≤ 1.5). At m=2 the effect
INVERTS with a dose-response in compartment count: 2×24 flat
(+0.001), 4×12 **ρ 0.239 vs bulk 0.185 (+0.054, t≈8.4)**, 8×6
**ρ 0.224 vs bulk-8-heads 0.166 (+0.058, t≈12)**. Per-seed
distributions unimodal (aggregation-trap check passed). The
classical anti-parasite remedy, applied to an order-fueled
matter-benefactor parasite, raises parasite density by ~30%
relative.

**2. Mechanism: compartments rescue the commons, and the parasite
rides the commons.** At m=2 compartments massively heal the tape:
4×12 holds 15.2 cells vs bulk's 9.7 (+58%, t≈18); 8×6 holds 22.7 vs
14.6 (+56%, t≈40) — pinning one head per small ring guarantees
repair coverage that a bulk ring loses when its heads drift into
one sector. But protection is not selective: more matter and longer
maintained runs are exactly the parasite's fuel (per-capita
gap-context sites +22% at 8×6 vs bulk8). Because the parasite is a
matter-benefactor (night-10 finding 3), "save the commons" and
"suppress the parasite" are the same knob turned opposite ways.

**3. Group selection grips — backwards.** The stochastic
corrector's engine (between-compartment variance × differential
contribution at pooling) is present and running: at m=2 the
selection differential on the phase variable, S = ρ̄_contribution-
weighted − ρ̄, is POSITIVE in every compartmented mixing condition
(c4x12 scr +0.0154, t≈8.8, 24/24 seeds; c8x6 chk +0.0215, t≈17.9,
24/24) — parasitized compartments hold MORE matter and contribute
MORE to the pool. Classical TC selection actively favors infection.
At m=8, S ≈ ±0.001: matter-neutrality leaves group selection
nothing to grip — prediction (b) in both regimes.

**4. Mixing is a disorder pump, not a selector.** Scramble pooling
RAISES ρ at m=8 (+0.031, t≈5.7, sawtooth: each episode re-coarsens
at drift −0.18/episode but never fully returns) — and it does so
even in bulk, i.e. the effect is the disturbance itself, not
compartment selection. Chunk pooling ≈ no mixing throughout. Whether
composition alone (scr) or run structure too (chk) is group-
heritable makes no detectable difference — consistent with
prediction (c): there is nothing group-heritable that selection
wants to act against, and the differential it does apply points the
wrong way.

**5. The resurrection ecology scales as expected.** Per-run
resurrections at m=2: bulk 41–101, 2×24 300, 4×12 754, 8×6 1110 —
small rings churn through local extinction-rebirth constantly (the
influx-stabilized phase from the night-10 addendum, now per
compartment). Plain-chemistry controls: ρ ≈ 0 everywhere (the
world crystallizes with or without compartments and mixing), and at
collapse the parasite arms hold MORE matter than plain (15.2 vs 8.9
at 4×12 m=2) — the matter-benefactor result reproduced under
compartments.

## The law of the night

**Group selection cannot suppress a parasite that pays its rent.**
Compartment-level selection acts on the coupling between parasite
load and compartment contribution; its sign is the sign of that
coupling, not an intrinsic property of compartmentalization. A
growth-costly parasite is suppressed (the classical literature's
regime); a matter-benefactor parasite is AMPLIFIED, and every
commons-rescuing side effect of compartments (machinery pinning,
order concentration) feeds it further, because by L6 its expression
is fueled by exactly the order that health produces. The classical
result is the special case where virulence is positive.

## Honest limits & hooks

- One mixing period only (E=1500); the T_mix window sweep (very
  short vs very long epochs) remains open — though with S > 0,
  more frequent selection should amplify, not rescue.
- Inoculum size fixed by dilution (pool/K, cap n−1); the
  stochastic-corrector small-inoculum corner (high variance,
  assortment load) untested.
- The scr ρ-elevation at m=8 is partly transient (post-mix
  relaxation within episodes); the robust claim is "never below
  bulk-none anywhere in the sweep", which holds in all 30 parasite
  conditions.
- Germline/soma second-row arm (Takeuchi-style symmetry breaking,
  drift-mediated) deferred — it is a different mechanism from
  walls and deserves its own night.
- Walls as paid matter (budget-priced containment) not tested here
  — compartments were geometric (free); the budget-cost angle
  remains the identified follow-up.
- cov in 'none' arms is a single end-state snapshot (noisy,
  c4x12-none t≈0.1); the causal claim rests on the mixing arms,
  where pooling actually applies the differential.
