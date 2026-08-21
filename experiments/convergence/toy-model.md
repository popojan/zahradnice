# The 2-site toy model: batch extinction in closed form

*Paper #1's analytical piece: the smallest system where conflict-
excluded batching provably changes an absorbing-state outcome, with
the direction and size of the measured λc(N) shift.*

## Setup

An isolated 2-cluster of infected sites A₁A₂ (horizontally adjacent)
in an empty sea, contact-process rules: per-site recovery weight `wr`,
per-(site, empty-neighbour) infection weight `wi`, λ = wi/wr. On the
square lattice two adjacent sites share no common 4-neighbours, so the
pre-batch candidates are:

- R₁, R₂ — recoveries (weight wr each; footprint = own cell),
- I₁ⱼ, I₂ⱼ — three infections per site (weight wi; footprint = anchor
  cell + target cell).

Conflict structure: Rᵢ conflicts with every Iᵢⱼ (shared anchor cell)
and with nothing else; infections of the same site conflict with each
other; the two sites' candidate groups are mutually conflict-free.

## Batched resolution (engine semantics, N ≥ 2)

The engine draws candidates weight-proportionally without replacement,
discarding any that conflict with an already-selected one, until N
selections or exhaustion. Weighted sampling without replacement is an
exponential race (each candidate an independent Exp(weight) clock), so
the *relative* order within each site's group is independent of the
other group's. Site *i* resolves to **recovery** iff Rᵢ's clock beats
its own three infections:

    P(site resolves to recovery) = wr / (wr + 3·wi)

and the two sites resolve **independently**. Once both recoveries are
selected, every remaining infection conflicts with one of them, so the
batch is exactly {R₁, R₂}: the cluster is dead. Hence

    P_batch(cluster dies in one batch) = [ wr / (wr + 3wi) ]²
                                       = [ 1 / (1 + 3λ) ]²

## Sequential resolution (N = 1)

Death without growth needs two consecutive events: first any recovery
(prob 2wr / (2wr + 6wi) = 1/(1+3λ)), which *frees a cell* — the
survivor now has **four** empty neighbours — then the survivor's
recovery against four infections:

    P_seq(dies in two events) = [ 1 / (1 + 3λ) ] · [ 1 / (1 + 4λ) ]

## The shift

    P_batch / P_seq = (1 + 4λ) / (1 + 3λ)  >  1   for all λ > 0.

| λ | P_seq | P_batch | ratio |
|---|---|---|---|
| 0.25 | 0.2857 | 0.3265 | 1.143 |
| 0.4125 (≈λc) | 0.1710 | 0.2007 | 1.174 |
| 0.50 | 0.1333 | 0.1600 | 1.200 |
| 1.00 | 0.0500 | 0.0625 | 1.250 |

**Mechanism, in one sentence: batch members resolve against the stale
pre-batch state, so the second site's recovery competes against only
its three original infections — sequential dynamics would have opened
a fourth escape route (the freed cell) between the two deaths.**
Batching removes the cluster's self-rescue channel; establishment gets
harder; the effective critical point moves up — the direction and
rough size (tens of percent at near-critical λ) of the measured λc(N)
shift.

Null control: for a **single** site the group structure is trivial and
P_batch = P_seq — the batch effect is an *interaction* effect, entering
at cluster size 2. This is why the supercritical bulk (where clusters
are large and self-rescue is marginal) is barely affected, and mildly
helped, while establishment is suppressed: the shift is
critical-region-specific.

## Engine validation

Protocol: seed A, grow the 2-cluster with a one-shot keypress rule,
then resolve it (a) in one batch (`#threads 8`, one `T`), (b) in two
sequential events (`#threads 1`, `TT`); count extinct outcomes over
many seeds at wr=8, wi=4 (λ=0.5). Prediction: 0.160 vs 0.133.

Measured (5000 seeds each): see the appendix below, filled in from the
validation runs.
