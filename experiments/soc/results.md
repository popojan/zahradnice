# Self-organized criticality in the grammar — forest-fire probe

*2026-08-21 · the "route 3 rerouted" experiment: adaptation without an
external optimizer via state-mediated rates (research-rl-ai.md §3), on
the stock engine. Also a live case study in false negatives — the
user's question "which 10 rules? can a flawed design fake a negative?"
was answered empirically three times in one afternoon.*

## Design

Drossel–Schwabl forest fire in ~11 rules: ground `g` fills the field
once (self-terminating spread — the life.cfg trick: you cannot anchor
on emptiness, so emptiness becomes a symbol), trees sprout from ground
uniformly (`==gTc`), lightning ignites a tree (`==cTA`, weight 1 — the
integer floor), fire spreads into adjacent trees (`==ATA`), burnout
returns fire to ground (`==ATg`). Timescale separation entirely by
weight ratios: burn = burnout (5000) ≫ sprout (100) ≫ lightning (1).
Score: +1 sprout, −1 burnout ⇒ score = live cells. Watcher controls:
`r` reseed, `q` quit.

## The three false negatives (and how each was caught)

1. **v1: vegetative growth** (trees spread from tree frontiers,
   contact-process style). Every run went extinct at every weight
   ratio. A mid-run dump showed why: frontier growth densifies the
   forest into one solid percolating cluster with no interior
   firebreaks — the first strike spans everything. Structural,
   weight-independent — a property of the *mapping*, not the
   substrate: DS-FFM requires site-wise regrowth anywhere, which is
   what keeps density below the percolation threshold. (Bonus trap on
   the way: `#include` with an absolute path fails silently — the
   first "stall" was a wrapper running with zero life rules;
   `zahradnice-check why`'s rule census exposed it in one call.)
2. **The measurement pipeline can fake a negative too**: the first
   fire-episode analyzer counted lightning as the only fire birth,
   forgetting burn-spread births — fire-alive went negative and two
   different regimes both read as "1 episode". The corrected
   accounting flipped the verdict on the same trace file.
3. **Display ≠ state** (caught by the user watching live): burnout
   wrote ground with transparent background, inheriting the fire's
   saved yellow — scorched land stayed fire-coloured forever and the
   plain looked perpetually ablaze. Explicit black backgrounds fixed
   it (GRAMMAR-pitfalls #16's trail mechanism).

Interim regime between fixes: with burnout ≪ burn and fast sprouting,
the system sat in a *continuously burning* phase (a percolating flame
front chasing regrowth — 645 fires alive at trace end) rather than
DS-FFM's separated avalanches. Diagnosed from rule totals, fixed by
burnout = burn and slower sprouting.

## Result (60k events, 33×64 field = 2048 cells, seed 7)

112 completed fire episodes, 0 fires alive at end (clean separation):

| metric | value |
|---|---|
| size min / median / mean | 1 / 14 / 168 |
| p90 / max | 614 / 1393 |

Log2 histogram of fire sizes: 27, 11, 14, 5, 7, 7, 7, 7, 13, 12, 2
per octave from 1 to 2047 — **approximately flat per octave across
three decades**, i.e. density ~ 1/s, with the cutoff at system size
(max fire = 68% of the field). A power-law-shaped avalanche
distribution with **no parameter tuned to criticality** — the weights
only encode timescale separation; the near-critical tree density is
maintained by the dynamics' own negative feedback (sprout mass ∝
ground count, lightning exposure ∝ tree count).

A 250k-event run for better statistics is recorded alongside
(`firestats.py` computes the numbers from any trace).

## What this says about "learning without an external optimizer"

Encouraging, concretely: effective-rate self-tuning via state (not via
G3 weight mutation) is expressible today, and the flagship phenomenon
of that family — self-organized criticality — appears on the second
honest attempt. The false-negative danger the user raised is real
(three instances in one session) but manageable, because the substrate
is a glass box: every failure had a mechanistic signature reachable in
minutes with dumps, rule censuses, and traces. Methodological rule
adopted: **calibrate the mapping against a model with known behaviour
before reading any negative as a substrate limit** (the contact
process's λc ≈ 0.412 played that role for the convergence study; DS-FFM
plays it here).

Engine wish flagged (not yet must-have): the integer weight floor —
lightning cannot go below weight 1, so rarity is bought by inflating
every other weight. Fractional weights or a `#weightscale` denominator
would be the clean fix if this line deepens.

## Next (if continued)

- Exponent fit (τ) with proper binning + larger fields (finite-size
  scaling of the cutoff); compare against DS-FFM's τ ≈ 1.1–1.2.
- The *learning* step: make sprout/ignition gating depend on
  reward-correlated local state (score-emitting rules already mark
  where flux happens) — adaptation shaped by the native reward channel,
  still with no optimizer anywhere.
- `#threads N` variant: does batching shift the avalanche exponent the
  way it shifted λc? (Ties the SOC line back to paper #1.)
