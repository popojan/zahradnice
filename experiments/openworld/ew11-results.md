# EW-11 — walls are linkage: the unit of selection, re-earned (F4)

Date: 2026-08-25, session 13. Registrations: ew-design.md §EW-11
(P11-1..4 + Amendment 11, pre-sweep). Driver: ew11.py; data:
ew11_runs.csv (400 runs, zero exactness failures). Verdict up
front: **walls do create units of selection — and the first thing
sector-level selection did with the evolvability trait was invert
the registered prediction: in a walled world with migration, the
fittest genome is the one that does not mutate but lives
downstream of one that does.** The organism re-enters the arc as
paid containment; its first lesson is that evolvability is best
outsourced.

## Setup

Ring 64, four sectors of 16 behind full-column walls (glyph `|`
on every row — spawner variants, stamps, translation, and walks
all blocked with zero new rules). Per-sector genome on the code
row: codon b → faithful copier, codon p → sloppy copier
(law-miscopy ε = 0.2); w → translator (self-reference). Alleles:
α = the fragile lottery walker, μ = the robust dynamic repairer,
reachable ONLY by machine error. Sparse tape seeding makes a
growth phase where stamps — and hence miscopies — happen.
Amendment 11's two instrument findings, registered pre-sweep:
sealed walls deadlock (an east-only machinery economy in a
bounded sector is a TERMINAL CONVEYOR — the ring's wrap was
load-bearing; fixed by wall_hop, machines only, weight 0.05:
genome and law stay home, machinery migrates rarely), and island
extinction (a 15-cell isolated matter population is a
metapopulation island — the open ring survives the same wounds by
recolonization rescue; wound schedule rescaled M 10, horizon 120).

## Results (100 seeds/arm; per-sector survival = alive ≥ 7 of 15)

| arm | sloppy sectors | faithful sectors | discovery in sloppy |
|---|---|---|---|
| walls-faithful | — | **0/400** (no discoveries ever) | — |
| walls-sloppy | 64/400 | — | 1.00 |
| walls-mixed | 16/200, μ 3.8 | **37/200, μ 4.9** | 1.00 (n=100) |
| open-mixed | 200/200, μ 7.3 | 200/200, μ 7.3 | 1.00 (n=100) |

- **P11-1 HELD, absolutely**: in full isolation the faithful
  genome is a death sentence — 0 of 400 sectors, because without
  machine error the robust allele is unreachable — while sloppy
  islands convert their own copying mistakes into rescue 16% of
  the time. At the unit level, evolvability is not a luxury; it
  is the only exit.
- **P11-4 HELD perfectly**: all 300 first-discoveries across the
  sweep originated in sloppy-genome sectors (trace-attributed by
  column).
- **P11-3 HELD**: the open world socializes everything — both
  region types survive 200/200 with identical matter and
  identical μ; there is no unit, so there is nothing for
  selection to compare. EW-9's commons, re-measured.
- **P11-2 FAILED — inverted, and the inversion is the finding**:
  with walls AND migration, faithful sectors outlive the sloppy
  sectors that save them (37 vs 16 of 200, z ≈ 3.1) and end with
  MORE of the rescue allele than its discoverers (μ 4.9 vs 3.8).
  Mechanism: hops are east-only, so every faithful sector sits
  downstream of a sloppy one and receives occasional itinerant
  mutators — a low-dose mutagenesis visit that plants μ and moves
  on — after which faithful machinery MAINTAINS the gift without
  back-mutation. The sloppy sector pays full-dose churn forever:
  at ε = 0.2 every restamp erodes its own μ-land (mutation-
  selection balance caps the discoverer's benefit). The spatial
  version of the mutator-hitchhiking-then-purge dynamics of real
  bacterial populations, derived: **the discoverer pays, the
  neighbour keeps.**

## What EW-11 answers, and the through-line completed

The question was whether linkage changes anything qualitative.
Three answers, all measured: (1) walls create UNITS — a bounded
sector's description, machinery, law, and matter succeed or fail
together, and unit-level selection differentials exist where
lineage-level selection saw nothing (EW-9) and recognition had to
be authored (EW-10); (2) units bring their own new physics —
island extinction and recolonization rescue emerged unbidden, and
the terminal-conveyor deadlock showed the ring's wrap had been a
hidden axiom; (3) the six-mask law gains its sharpest corollary:
selection sees only what someone can keep — and a genome KEEPS a
gift best by not being the kind of genome that churns it.
Evolvability, even when it is the only exit (0/400 without it),
is outsourced the moment migration allows: the stable division of
labour is a mutagenic minority servicing faithful neighbours.
Night 7 deleted the organism; EW-11 buys it back with walls and
finds that the first thing organisms do is specialize.

Honest limits: hop is east-only (every faithful sector is
downstream of a sloppy one by construction — the layout makes the
outsourcing maximally available; a bidirectional or randomized
layout would dose it); the migration rate (0.05) and ε (0.2) are
single points — the inversion should flip back at low ε (less
self-churn) or zero migration (P11-1 shows it must); sector
populations are small and extinction-dominated; the genome's
fidelity codons are two-valued. The natural next dose axes are
named, not run: ε sweep (find the churn threshold where
discoverers keep their own gifts), hop-rate sweep (the linkage-
decay curve), and genome evolution proper (let miscopy rewrite
the p/b codons themselves — the mutation rate's mutation, in
matter).
