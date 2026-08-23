# EW-4 — miscopy rescues the world (F4, earning the mutation channel)

Date: 2026-08-23, session 9. Registrations: ew-design.md §EW-4
(P4-1..4; constants smoke-tuned and recorded before the sweep).
Driver: ew4.py; data: ew4_runs.csv (500 runs, zero exactness
failures). Verdict up front: **the mutation channel is earned —
law novelty exists only as machine error, exercised only through
repair traffic, dosed by machine fidelity, and load-bearing for
whole-world survival.** One registered sub-claim failed and its
replacement finding is the arc's abundance law recursed: the
rescuer's advantage is self-limiting.

## Setup

Ring 24, all-α start (α = spawner only); allele μ (spawner + build)
exists nowhere and is reachable ONLY through a sloppy copier
stamping the wrong allele at a repair site. Machinery bootstrapped
density 1/2, decaying (ε_d 0.01), unreplenished unless μ arises and
funds building. Drive: b + (T C⁴)*200 + 200 × (p + (T C⁴)*5).
Arms (100 seeds each): faithful (Π, ε=0), sloppy ε ∈
{0.01, 0.05, 0.2} (π; build also writes π), nowound (π, ε=0.05,
no pokes). Rescue = final alive ≥ 12 and machinery present.

## Results

| arm | rescued | μ discovered | median discovery (apply) | alive | copiers |
|---|---|---|---|---|---|
| faithful | 0/100 | 0/100 | — | 0.0 | 0.0 |
| sloppy ε=0.01 | 4/100 | 5/100 | 1482 | 0.8 | 0.9 |
| sloppy ε=0.05 | 13/100 | 17/100 | 1252 | 2.4 | 2.7 |
| sloppy ε=0.2 | 40/100 | 42/100 | 1158 | 7.5 | 8.6 |
| nowound | 0/100 | 0/100 | — | 24.0 | 0.0 |

- **P4-1 HELD**: without machine error the world always dies —
  faithful machinery decays, wounds freeze, erosion consumes the
  tape, 0/100 survivors. Perfect copying is lethal in a wounded
  world whose only builder is undiscovered.
- **P4-2 HELD (main claim)**: rescue occurs only in sloppy arms and
  scales far beyond the faithful arm's zero. **Discovery is nearly
  sufficient**: P(rescue | μ discovered) = 4/5, 13/17, 40/42 —
  establishment is close to deterministic; the bottleneck is the
  mutational event itself. **Registered sub-claim FAILED**: rescued
  worlds do NOT end μ-majority (9/40 at ε=0.2; mean gates α 12.8 vs
  μ 9.7, machinery near-saturated at 21.6). Replacement finding,
  and it is the arc's own law recursed: once μ's funding makes
  machinery abundant, EW-3's saturation invariance kicks in — the
  public good goes global, α free-rides, annexation stops favouring
  the funder. The rescuer's advantage is SELF-LIMITING: rescue
  returns the world to the abundant regime, erasing the scarcity
  that selected for funding. Stable funder + free-rider
  commensalism, not fixation (negative frequency dependence of the
  builder — the night-10/petri motif at the law level).
- **P4-3 HELD**: rescue is dose-monotone in ε (4 → 13 → 40 of 100)
  and discovery accelerates (median apply 1482 → 1252 → 1158).
- **P4-4 HELD**: no wounds → no repair traffic → zero μ stamps in
  100 runs (the world survives trivially but cannot evolve).
  Mutation is repair-coupled: mutagenesis is a metabolic service,
  exercised exactly where inheritance is exercised.

## What EW-4 adds to the summit

The miscopy channel now lives in matter end to end: the mutation
RATE is a property of which machines stand where (a destroyable
population — the faithful arm is the world with its mutagenesis
machinery removed, and it cannot evolve at all); the mutation
OPPORTUNITY is repair traffic (wound economy); and the mutation
PAYOFF closes the first full matter→law→matter loop — the sloppy
copier's error creates the lineage that funds copiers. O3 said
evolvability is matter-bound; EW-4 sharpens it: evolvability is
MACHINE-borne, and a world that loses its sloppy machines loses
its future.

Honest limits: fidelity is still not heritable through a machine
lineage (copier replication remains deferred; the trait rides the
law lineage via which machine type builders fund); ε and the Π/π
distinction stay authored; rescue was tested against one superior
allele, not an open search space.
