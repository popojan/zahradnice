# forest-evo: the route-3 worth-estimate POC (time-boxed, 2026-08-21)

Question: can selection acting on state tune an effective parameter
(mean flammability) to the environment, all in-grammar, no optimizer?
Design: two species, growth/flammability trade-off (c: fast, p=0.8;
d: slow, p=0.2), same cfg run under calm vs fiery lightning regimes
(environment = input mix of `l` triggers).

## What the box produced: five structural lessons in ~90 minutes

1. **Ratchet dominance.** With only a growth/flammability trade-off,
   fire-resistance is dominant under ANY fire regime: d never loses
   ground, c's losses are catastrophic per strike. 16/16 fixations.
2. **Event-time rarity is an illusion at saturation.** A weight-based
   lightning knob fails: once the field saturates, lightning is the
   only applicable rule and fires with certainty regardless of weight.
   In a jump chain "rare" is relative to co-applicable mass. Remedy:
   environment as input composition (own trigger char) — the
   drive-in-quiescence pattern again. (False negative #5.)
3. **Vegetative-only reproduction is an absorbing trap.** One
   supercritical burn of the connected continent = permanent
   extinction. Seed rain (rare spontaneous sprouting) is the minimal
   immigration that breaks it — serotiny, discovered by necessity.
4. **Winner-flips need a mortality asymmetry.** Fire-resistance must
   pay rent (d natural mortality) — the competition–colonization
   trade-off structure. Only then did environments differentiate.
5. **Visibility bias** (user observation): ignition probability is
   species-equal; what differs is spread — a d-strike dies as one
   invisible cell, a c-strike becomes a visible blaze.

## Final data (60k + 150k events, 33×64)

- Fiery (strike every 200 ticks): d dominates in all runs
  (c share 3–16%).
- Calm (every 4000): contested, bistable, long transients — c share
  ranges 0.5% to 54% by seed; mean c share ≈ 3× the fiery worlds'.

Directional environmental selection: demonstrated. Clean deterministic
winner-flip: not within this box (larger fields / longer runs /
sharper trade-offs would be next).

## Verdict for route 3

**Positive, with the qualification that the flip is directional, not
clean.** The strongest signal is not the matrix but the process: the
substrate acted as a *mechanism microscope* — each structural force
(immigration, mortality cost, disturbance regime) is one to three
rules, each hypothesis-to-measurement cycle took minutes, and every
failure produced a named, transferable insight rather than noise.
Route 3's deeper agenda (heritable trait ladders, reward-correlated
capacities) looks tractable on this evidence, and so far required NO
new engine features — input-mix triggers, fractional weights, and
fill seeds covered everything. The one engine lift route 3 may
eventually motivate: score-conditioned rules (a global-signal gate),
which remains the deliberate, unbuilt option.

Also fun: `l` throws lightning interactively. The storm is a key.

Milestone 2 (heritable trait ladder, same day): see ladder-results.md
— the 5-rung ladder turned the directional flip into a graded,
monotone environmental response, revealed as a driven relaxation
oscillation on the trait axis.
