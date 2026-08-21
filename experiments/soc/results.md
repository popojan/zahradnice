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
per octave from 1 to 2047 — approximately flat per octave across three
decades on this first run, cutoff at system size.

## Correction: the robustness scan says "self-organized" was overclaimed

A 250k-event run (534 episodes) and a sprout-weight scan falsified the
first reading. The user's challenge ("are you sure the
self-organization is there — maybe the trees just grow fast enough?")
identified exactly the axis that should not matter under SOC and does:

| sprout weight | episodes | med / p90 / max | shape |
|---|---|---|---|
| 30 | 799 | 9 / 124 / 649 | broad, cutoff well below system size (sub-critical flavour) |
| 100 (250k) | 534 | 15 / 576 / 1539 | **bimodal**: small-fire peak, valley at 16–63, second mass 128–1023 |
| 300 | ~44 | megafires to 8191 — 4× the field | megafire cycling; sizes > field ⇒ cells regrow and re-burn within one episode |

The distribution shape slides smoothly with the growth rate; the flat
histogram at sprout 100 sits at a *tuned crossover*, and even there the
long run shows the quasi-periodic-megafire signature once statistics
accumulate. **Defensible claim: DS-family fire dynamics with
parameter-dependent avalanche regimes are expressible in ~11 rules —
not demonstrated SOC.** What would settle it: field-size scaling (under
SOC the cutoff tracks L at fixed weights; under tuning it tracks the
timescale ratio θ), much larger θ (blocked by the integer weight floor
at the time of the scan — see below), and a proper τ fit. Fairness
note: canonical DS-FFM's own SOC status is disputed (Grassberger 2002;
Pruessner & Jensen), so even a perfect mapping inherits a contested
pedigree.

`firestats.py` computes all numbers from any trace.

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

## Scaling runs (post fractional-weights engine feature)

The two falsification axes, now cheap thanks to decimal weights
(lightning 0.001 without inflating anything):

- **Field size ↑ at fixed θ=100** (65×128 = 8192 cells, 250k events):
  the regime changes instead of scaling — 12 completed episodes, 43
  fires alive at trace end, "episodes" up to 46 008 burns (5.6× the
  field: cells regrow and re-burn inside one never-ending fire).
  Lightning mass grows with tree count, fires overlap, the system
  slides into continuous burning. The cutoff does **not** track L;
  DS-style scaling would need θ to grow with L (the double limit).
- **θ ↑ at fixed L** (θ=1000, 33×64, 250k events): 411 clean episodes,
  same bimodal fingerprint (valley at 8–31, second mass 512–2047,
  max 1717), heavier megafire tail. More separation alone does not
  produce scale-invariance.

Conclusion unchanged and now two-axis-tested: at terminal-accessible
scales this is parameter-dependent avalanche phenomenology with
quasi-periodic megafires — a good expressiveness result for the
grammar, not a demonstration of SOC.
