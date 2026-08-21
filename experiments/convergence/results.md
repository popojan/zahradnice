# Contact process on the Zahradnice engine — first sweep results

*2026-08-21 · step 1 of the plan in `backlog/research/research-rl-ai.md` §9.
No engine changes; stock `zahradnice-headless`.*

## Setup

`contact.cfg`: infected sites `A` spread into empty 4-neighbours (weight
`WI` per applicable (site, neighbour) pair) and recover to empty (weight
`WR` per site). Control parameter λ = WI/WR. Single seed `^Acc` on a
16×32 toroidal field (`--screen 17,32`; row 0 is status). All-empty is
absorbing — every rule anchors on `A`, so after extinction no rule
applies and the stderr event count *is* the extinction step. Score is
wired as +1 per infection / −1 per recovery, so `score = population − 1`
and `score == −1` flags extinction. Single-threaded, `--seed` sweep.

This maps onto the standard 2D contact process, whose critical
per-neighbour infection/recovery ratio is λc ≈ 0.412 (directed
percolation universality class) — the discretely-sampled analogue of the
Blok & Bergersen async-Life story the research notes point at (§2.2).

## Results

Coarse sweep (`./sweep.sh 30 20000 > results.csv`, WR=8):

| λ | n | survive% (20k budget) | ext. median | ext. mean | ext. max |
|---|---|---|---|---|---|
| 0.125 | 30 | 0.0 | 1 | 2.7 | 17 |
| 0.250 | 30 | 0.0 | 3 | 6.7 | 31 |
| 0.375 | 30 | 0.0 | 3 | 25.6 | 497 |
| 0.500 | 30 | 33.3 | 3 | 6.0 | 31 |
| 0.625 | 30 | 46.7 | 3 | 5.9 | 25 |
| 0.750 | 30 | 63.3 | 1 | 4.1 | 25 |
| 1.000 | 30 | 80.0 | 2 | 6.0 | 25 |

Focused sweep (`WR=16 WI_LIST="5 6 7 8 9 10" ./sweep.sh 50 20000 >
results-fine.csv`):

| λ | n | survive% | ext. median | ext. mean | ext. max |
|---|---|---|---|---|---|
| 0.3125 | 50 | 0.0 | 3 | 23.0 | 289 |
| 0.3750 | 50 | 0.0 | 3 | 27.1 | 497 |
| 0.4375 | 50 | 14.0 | 3 | 62.5 | 797 |
| 0.5000 | 50 | 38.0 | 3 | 4.8 | 31 |
| 0.5625 | 50 | 40.0 | 3 | 5.1 | 25 |
| 0.6250 | 50 | 50.0 | 3 | 4.7 | 25 |

## Reading

- **A survival phase transition exists and is where theory says it
  should be.** Survival probability is 0 up to λ = 0.375 and lifts off
  between 0.375 and 0.4375, bracketing the contact-process λc ≈ 0.412.
  The engine's weight-proportional sampling over applicable (site, rule)
  pairs behaves like the jump chain of the corresponding interacting
  particle system — weights really are semantics (§1 of the research
  notes).
- **Critical slowing-down is visible.** The extinction-time tail
  (mean/max over extinct runs) peaks at the threshold — mean 62.5 and
  max 797 at λ = 0.4375, versus ~5/≤31 both deep below and above it.
  Above threshold, extinct runs are the branching-process early deaths
  (the seed fails before establishing), which is why their times stay
  small; the slow deaths live only near criticality. This is the
  qualitative Fatès signature: convergence time diverging at a critical
  parameter.
- **Median vs mean.** The median extinction time stays ~3 everywhere
  because it is dominated by immediate seed deaths (first few events);
  the class signal is in the upper tail, not the centre.

## Caveats

- "Survival" means surviving a 20 000-event budget on a finite 512-cell
  torus. The all-empty state is the only absorbing one, so every run is
  doomed in the infinite-time limit; what we measure is the
  quasi-stationary regime, which is the standard finite-size protocol.
- Events count *applied rules*, i.e. the embedded jump chain — one event
  is one site update, not one parallel sweep. Comparisons with
  synchronous-CA time scales need a ÷population conversion.
- Single initial seed conditions everything on early survival; a
  half-filled initial field would measure relaxation instead of
  establishment. Both are interesting; only the first was run.

## Next (if continued)

- More seeds (200+) at λ ∈ [0.39, 0.47] to estimate λc properly, and
  extinction-time distributions (not just moments) for the
  convergence-class fit.
- Field-size scan (16², 32², 64²) for finite-size scaling of the
  transition — the actual directed-percolation test.
- The `#threads N` variant of the same sweep: does the conservative
  conflict-detection parallelism shift the effective λc? This is the
  §2.2 question in its sharpest form.

---

# Round 2 — the `#threads` variant (same day)

`THREADS=N ./sweep.sh` reruns the identical grid with the engine's
multi-rule execution: up to N non-conflicting rules sampled without
replacement per step *from the same pre-batch state* — the engine's
native synchrony knob. Extinction is still measured in applied rules
(jump events), so columns are comparable across N.

Survival % (50 seeds, 20k-event budget; T1 column from results-fine.csv,
same seeds and grid):

| λ | T=1 | T=2 | T=4 | T=8 |
|---|---|---|---|---|
| 0.3750 | 0 | 0 | 0 | 0 |
| 0.4375 | 14 | 18 | **6** | **0** |
| 0.5000 | 38 | 44 | 44 | 42 |
| 0.6250 | 50 | 64 | 62 | 60 |

Extinction-time tails at λ = 0.4375: mean/max grow from 62/797 (T=1) to
~820–930 / 12k–15k (T≥2) — order-of-magnitude longer near-critical
transients.

Reading: **the near-critical point is suppressed by batch parallelism —
effective λc shifts upward with thread count.** At λ = 0.4375 survival
dies from 14% to 0% as N goes 1→8, while comfortably supercritical
ratios are barely affected (and T=2 mildly *helps* at 0.625). Mechanism
consistent with synchrony: within a batch, events are sampled from stale
state, so e.g. two adjacent recoveries can co-fire and extinguish a
small cluster that sequential sampling would have let re-spread — the
establishment phase is variance-dominated and batching raises variance.
This is the engine-native analogue of Blok & Bergersen's async/sync
distinction, answering §2.2's open question in first approximation: yes,
there is a parallelism-dependent shift, it is measurable with the stock
harness, and it comes with giant near-critical transients (some "extinct"
runs at T≥2 die only after 12–15k events, close to the budget — a finer
study should raise `--max-steps`).

---

# Round 3 — finer λ grid (same day)

`WR=32 WI_LIST="12 13 14 15 16" ./sweep.sh 200 50000 > results-fine2.csv`
(single-threaded, 200 seeds, 50k-event budget):

| λ | n | survive% | ext. median | ext. mean | ext. max |
|---|---|---|---|---|---|
| 0.3750 | 200 | 0.0 | 3 | 76.9 | 3693 |
| 0.4062 | 200 | 0.5 | 3 | **525.2** | 12501 |
| 0.4375 | 200 | 15.5 | 3 | 70.7 | 3073 |
| 0.4688 | 200 | 26.5 | 3 | 18.6 | 505 |
| 0.5000 | 200 | 31.5 | 1 | 12.0 | 265 |

Liftoff is pinned between 0.4062 and 0.4375, tightly bracketing the
theoretical λc ≈ 0.412, and the extinction-time tail peaks exactly at
the last subcritical point — the cleanest critical-slowing-down
signature so far. (Data predates the candidate-order engine fix; that
fix changes per-seed trajectories, not statistics.)

---

# Round 4 — λc(N) curves (100 seeds, 50k budget, deterministic engine)

`THREADS=N PAR=8/N WR=32 WI_LIST="13 14 15 16 17 18" ./sweep.sh 100
50000 > results-lN.csv`, all four N on the candidate-order-fixed engine
(every run replayable). Survival %:

| λ | N=1 | N=2 | N=4 | N=8 |
|---|---|---|---|---|
| 0.4062 | 0 | 0 | 0 | 0 |
| 0.4375 | 17 | 14 | **1** | **0** |
| 0.4688 | 27 | 34 | 36 | **5** |
| 0.5000 | 35 | 41 | 45 | 41 |
| 0.5312 | 41 | 45 | 50 | 52 |
| 0.5625 | 46 | 59 | 55 | 56 |

The giant-transient marker (mean/max extinction time of extinct runs)
tracks the moving critical point:

| N | transient peak at λ | mean / max there |
|---|---|---|
| 1 | 0.4062 | 1067 / 32051 |
| 2 | 0.4375 | 1176 / 47351 |
| 4 | 0.4375 | 1624 / 25729 |
| 8 | 0.4688 | 3927 / 47937 |

Reading:

- **The effective critical point moves monotonically upward with batch
  bound N**: the 10%-survival crossing sits near 0.43 (N=1,2), ~0.45
  (N=4), ~0.48 (N=8), and the critical-slowing-down peak walks with it.
- **The shift is critical-region-specific, not a uniform handicap.**
  Deep in the supercritical phase batching mildly *helps* (0.5312+:
  41→52% from N=1 to N=8). Two competing effects: batches co-fire
  correlated recoveries that kill small clusters during establishment
  (raising the establishment barrier), while established populations
  spread slightly faster per event under batching. A serialisable
  scheme thus reshapes the phase diagram non-uniformly — the sharpest
  version of the paper's claim.
- Budget caveat: at N=8, λ=0.4688 the extinct-run mean is ~3.9k with
  max ~48k against a 50k cap — some "survivors" there are likely slow
  deaths; the λc(N) fit should treat that point as censored or re-run
  with a larger budget.
