# Related work — positioning the λc(#threads) study (survey 2026-08-21)

Question: is "conflict-excluded stochastic batching shifts critical
behaviour, although every batch is serializable" already claimed
somewhere? Three neighbouring literatures were checked; none owns this
exact corner, and each supplies a piece of the framing.

## 1. Asynchronous CA / α-synchronism (rates, not batches)

- Fatès, *A guided tour of asynchronous cellular automata*, JCA 2014
  ([arXiv:1406.0792](https://arxiv.org/abs/1406.0792)) — the survey of
  update-scheme sensitivity.
- Fatès, *Asynchronism induces second-order phase transitions in
  elementary cellular automata*, JCA 2009; *Directed percolation
  phenomena in asynchronous elementary CA*, ACRI 2006
  ([hal-00016420](https://inria.hal.science/hal-00016420)) — nine ECA
  rules show DP-class transitions as the synchrony *rate* α varies.
- Blok & Bergersen, *Synchronous versus asynchronous updating in the
  Game of Life*, PRE 1999 — α_c ≈ 0.911 for async Life.
- Hinrichsen, *Nonequilibrium critical phenomena and phase transitions
  into absorbing states*, Adv. Phys. 2000 — DP universality reference.

Their control parameter is a per-cell iid update *probability*. Ours is
a batch size with state-dependent, conflict-driven membership — a
different family. Fatès' protocol (order parameter, critical exponents)
is the methodology to borrow.

## 2. Parallel kinetic Monte Carlo (the closest quantitative neighbour)

- Martínez et al., *Synchronous parallel kMC*, J. Comput. Phys. 2008;
  billion-atom critical 3D Ising validation, J. Comput. Phys. 2010
  ([ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S002199911000608X))
  — *exact* parallel kMC via chessboard sublattices + null events;
  explicitly validated at criticality (bias within statistical error).
- SPPARKS' approximate SSL algorithm
  ([IOPscience 2023](https://iopscience.iop.org/article/10.1088/1361-651X/accc4b))
  — ignore-boundary-conflict schemes with a tunable accuracy knob.
- Arampatzis, Katsoulakis et al., *Hierarchical fractional-step
  approximations and parallel kMC*
  ([arXiv:1105.4673](https://arxiv.org/abs/1105.4673)) — parallel kMC
  as operator splitting, with observable-focused error quantification.

This community knows batching biases dynamics and either fixes it
(chessboard + proper clocks) or quantifies it (splitting error). The
Zahradnice `#threads` scheme is a *third* variant none of them study as
such: sample-without-replacement, conflict-*excluded* batches drawn
from the stale pre-batch state, with no rate correction — i.e. what a
naive "transactional" parallel rule engine actually implements.
Serializability holds by construction, yet the measure shifts; our
λc(N) curve is that bias's macroscopic signature.

## 3. Update schedules in Boolean automata networks (deterministic)

- Aracena et al., *On the robustness of update schedules in Boolean
  networks* (2009) — update digraphs, equivalence classes of
  block-sequential schedules; limit cycles are schedule-sensitive.
- Demongeot, Noual, Sené, *Block-sequential update schedules and
  Boolean automata circuits* ([DMTCS](https://dmtcs.episciences.org/2762)).
- Perrot, Sené, Tapin, *Complexity of Boolean automata networks under
  block-parallel update modes*, SAND 2024
  ([arXiv:2402.06294](https://arxiv.org/abs/2402.06294)); *Foundations
  of block-parallel automata networks*
  ([arXiv:2503.04591](https://arxiv.org/abs/2503.04591)).

Rich theory of how *prescribed, deterministic* block schedules change
attractors and complexity. Our batches are stochastic and geometry-
driven (membership decided at runtime by footprint collisions), and the
lens is statistical (critical points), not attractor/complexity theory.

## 4. Stochastic graph rewriting (the same formalism family)

- Behr, Danos, Garnier, *Stochastic mechanics of graph rewriting*,
  LICS 2016 ([ACM](https://dl.acm.org/doi/10.1145/2933575.2934537));
  Behr & Krivine, *Rewriting theory for the life sciences* (CTMC
  semantics for Kappa/MØD, [arXiv:2003.09395](https://arxiv.org/abs/2003.09395)).
- Boy de la Tour, *Parallel independence in attributed graph rewriting*
  ([arXiv:2102.02366](https://arxiv.org/abs/2102.02366)) and the
  concurrency-theorem line — the *state-level* commutation theory
  (Local Church–Rosser): exactly our serializability argument, done
  properly and categorically.
- KaSim's exact Gillespie-style simulation with incremental propensity
  updates (Boutillier et al.).

Rule-based CTMC frameworks are *event-sequential by definition*;
parallel independence is used for causality analysis, not to justify
batched simulation. Nobody here asks what conflict-excluded batching
does to the sampled distribution.

## Also adjacent, cite in passing

- τ-leaping (Gillespie 2001; Cao et al. leap-size control): batches
  many reactions from frozen propensities *without* conflict exclusion,
  with an explicit error theory. Our scheme is its conflict-excluded,
  uncorrected cousin. *(Standard results; verify exact citations when
  writing.)*
- Game engines' checkerboard/chunked CA updates (e.g. Noita's Falling
  Everything engine, GDC 2019 talk) — the same conflict-avoidance
  batching deployed at scale where only appearance matters; a good
  motivation anecdote for "this scheme is what practitioners write".

## Verdict

The specific claim — **state-serializable, conflict-excluded stochastic
batching is not distribution-faithful, with a measurable shift of a
DP-class critical point as the batch bound grows** — appears unclaimed.
The paper should be framed as bridging (1) α-synchronism's phenomenon,
(2) parallel-KMC's exact/approximate dichotomy (our scheme is the
common third case), and (4) rewriting theory's parallel independence
(which licenses only state-safety, not measure-safety). Strongest
sharpening available: an analytical 2-site/small-cluster batch model
reproducing the direction and order of the λc shift.
