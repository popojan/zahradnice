# Closed-loop Life steering via prefix replay — first results

*2026-08-21 · step 3 of the plan in `backlog/research/research-rl-ai.md` §9.
No engine changes.*

## Setup

`greedy.py` drives `programs/life-steer.cfg` closed-loop without any
streaming interface: seeded single-threaded runs are bit-deterministic
(force via `--trace /dev/null`; see friction journal F7), so "observe →
act" is implemented as "re-run the whole prefix + candidate action +
300-tick lookahead, read the final score, commit the argmax". This is
the O(T²) interim path the research notes describe under gap G1; at
~1500 events/s it costs ~16 s per greedy episode (6 candidates evaluated
as parallel engine processes per decision).

Episode: 400 warmup ticks, 10 decisions ({wait, w, a, s, d, toggle} at
60-tick gaps), 300-tick settle. Score = life.cfg's native birth(+1)/
death(−1) flux minus 1 per toggle. All policies emit identical-length
trigger strings, so scores are comparable per seed.

## Results (8 seeds)

| policy | mean score | per-seed |
|---|---|---|
| passive (never act) | −4.1 | −7 −4 −5 −6 −4 +1 −4 −4 |
| random | −5.2 | −6 −4 −9 −5 −9 +1 −4 −6 |
| greedy (1-step lookahead) | **−2.2** | −2 0 −5 0 −4 +1 −3 −5 |

Paired greedy−passive differences: +5 +4 0 +6 0 0 +1 −1 (4 wins, 3
ties, 1 loss). n=8 is small; the ordering greedy > passive > random is
consistent but not yet statistically strong.

## Reading

- **The loop closes.** A policy can observe (via score), act (via
  keys), and improve on both baselines with zero engine changes. That
  was the point of step 3.
- **Random < passive** — the −1 toggle penalty plus chaotic dynamics
  make blind intervention strictly harmful. The reward design (uniform
  action cost; kill cost = physics death penalty, so euthanasia can't
  be farmed) behaves as intended.
- **Greedy is appropriately lazy**: 66/80 chosen actions are "wait".
  When it acts it prefers *movement*, which is free — and movement is
  not a no-op here: hovering pins the bracketed cell and both
  horizontal neighbours' edge columns, and departure resets the vacated
  block's scan phase. The policy is exploiting an **uncosted
  intervention channel** (the observer effect) that the reward design
  didn't price. Options if this becomes a problem: cost movement keys,
  or accept it as part of the game's physics. Toggles were chosen
  rarely (2/80) but appear in the winning episodes.

## Costs / limits

- Prefix replay is quadratic: 10 decisions ≈ 100 s CPU (16 s wall)
  per greedy episode. Fine for bandit-scale studies; a streaming step
  mode (gap G1) is the upgrade path for anything sequential-deep.
- Single-threaded dynamics are ~4–5× slower per tick than the
  multi-threaded interactive program, so episode horizons here are
  short relative to what a human sees playing
  `./zahradnice programs/life-steer.cfg`.

## Next (if continued)

- More seeds + longer horizons for statistical weight; track
  intervention counts per policy in the CSV.
- Price movement (e.g. −1 per move at higher birth reward) and re-run —
  does greedy still beat passive when the observer effect costs?
- Gap G1 (stdin step mode) once the O(T²) wall actually hurts.

---

# Round 2 — mover diagnostic + observer tax (same day)

## Mover diagnostic (unpriced cfg)

`greedy-mover` = the same oracle lookahead restricted to {wait, w, a, s,
d} — toggles removed. Result: mean −2.4 vs full greedy's −2.2, with
*character-identical* action strings on 7 of 8 seeds. Essentially all of
greedy's edge over passive flowed through the free movement/hover
channel (mechanical pinning plus, more deeply, free trajectory rerolls —
in a chaotic system any free action forks the future, and a
deterministic-lookahead agent picks the best fork).

## Observer tax

Pricing is rate-based, not per-keypress: at long horizons only reward
*rates* survive in the average-reward criterion, so the correct price on
the observer effect is a rate on *pinning*, not a charge on transit. New
slow trigger `h`; a rule fires −1 only while the cursor pins a **live**
cell (parking on dead ground is free). Rate is tuned by cadence — the
harness injects `h` every 60th tick (`--tax-every`), interactively
`#timing h 1000` — so no fractional scores are ever needed. The
per-move stochastic alternative (weighted duplicate headers, expected
−0.2/move) and the deterministic ×5-scaling fallback are documented in
the cfg comment but not enabled.

Validated by prefix A/B: `h` on a dead-hover is a no-op; on a live
hover exactly −1.

## Results under tax (8 seeds, cadence 60)

| policy | untaxed | taxed |
|---|---|---|
| passive | −4.1 | −3.8 |
| random | −5.2 | **−9.1** |
| greedy | −2.2 | −2.2 |
| greedy-mover | −2.4 | −2.2 |

- **The tax works on naive policies**: random collapses (it wanders onto
  live cells and parks); passive is untouched (its cursor idles on the
  dead spawn block). The price lands exactly where the externality is.
- **The oracle dodges it**: greedy's mean is unchanged, its action
  strings are identical to mover's on all 8 seeds (zero toggles chosen),
  and it simply avoids being on live cells at `h` moments — it knows the
  cadence and sees the future. Movement is free, so evasion is free.
- Conclusion: rate-pricing is the right shape for agents *without* a
  rollout oracle (the setting that matters for learning); against
  deterministic-lookahead baselines no price on a free action space can
  bind, because the oracle re-optimizes around any of them. The honest
  fix for oracle baselines is randomized evaluation (deny the exact
  future), not a bigger tax.
- Toggles at −1 were never chosen by lookahead in either round; if
  toggling should be part of optimal play, the ×5 economy (birth +5,
  toggle −5, keeping integers) gives finer room to make it worthwhile.

---

# Round 3 — the rule-neutral cursor (same day)

Round 2's cursor violated a principle worth making explicit: the cursor
may perturb *scheduling* (async semantics leaves it free) and RNG
consumption, but must never make the field deviate from Life's rules.
Normalize-on-departure did deviate: it aborted in-flight scans and could
manufacture blocks the machine never produces.

**The rule-neutrality contract** (now implemented in life-steer.cfg):
movement is gated on the target block's visible phase-mirror cell
(`b` at c2), the brackets are `#transient`, and departure `$`-restores
the covered cells exactly. Covered cells are then never mid-i/s-phase,
hidden chars are guaranteed to satisfy the machine's guards the same way
the brackets do, and hovering becomes a pure pause with exact resume —
every reachable field state is a legal Life state. (The c2 mirror stays
`b` during the neighbour-count scan, so the cursor can enter scanning
blocks; still neutral — `$` resumes the paused scan exactly, and the
machine's scans are multi-tick non-atomic anyway.)

Testing the contract immediately paid off: a toggle+depart dump exposed
a **dual-anchor bug** — the cursor draws two `>` glyphs, the toggle rule
could anchor on the bottom one and write a row too low, into the
neighbouring block. Fixed with a `>`-at-(1,0) disambiguating body cell
(movement rules already had one); the tax rule had the same bug in a
sneakier form (both anchorings applicable with disjoint footprints =
possible double tax in multithreaded mode). Two earlier validations had
passed on a lucky 50/50 anchor draw.

## Results (8 seeds, tax cadence 60, rule-neutral cursor)

| policy | round 2 (deviating) | round 3 (neutral) |
|---|---|---|
| passive | −3.8 | −3.4 |
| random | −9.1 | −6.9 |
| greedy | −2.2 | **−1.2** |
| greedy-mover | −2.2 | **−1.2** |

Greedy still beats passive (+2.2 mean, action strings again identical to
mover's, zero toggles) — and now its entire edge is exercised through
provably rule-legal means: pausing cells (scheduling) and trajectory
selection (RNG). Steering an async CA without ever bending its laws is
possible, and profitable. The remaining open economy question is
unchanged: only randomized evaluation can make the oracle pay the tax.

---

# Round 4 — engine determinism fix + the zero-impact cursor question

## Candidate-order fix (engine)

Chasing MT nondeterminism for the closed loop found the real cause:
`Derivation::x` is an unordered map that parallel batches update in
thread-completion order, and the candidate gather iterated it directly —
the seeded RNG stream mapped onto a scheduling-dependent candidate
order. Two canonical `std::sort` calls fix it; multithreaded runs are
now bit-deterministic and the prefix-replay property holds in MT mode
(appending one keypress changes exactly one event). Consequences here:
the harness no longer needs `--trace /dev/null` to force determinism,
and per-seed trajectories differ from the CSVs recorded pre-fix
(statistics unaffected). The fix also exposed a single-thread-only
spawn race: the bootstrap chars (`o`, `+`, `)`) competed at weight 1
against the waking machine and could be bulldozed before converting;
they now carry weight 100 so the bootstrap completes before the
machine spreads.

## Can a cursor have ZERO execution impact (not even pausing)?

Analysis, for the record:

- **Not with any in-field character.** The cursor needs a matchable
  identity; the engine matches characters only; every field cell is
  read or written by the machine; therefore any identity glyph at
  least pauses its host block. Colours are invisible to matching (a
  colour-only highlight is free) but cannot carry identity. Off-field
  rows (status row 0, rows beyond the grid-aligned wrap area) are
  unreachable or broken for rule anchoring.
- **Burst protocol + home parking gets asymptotically close today,
  zero engine changes.** In headless/RL use the harness controls the
  trigger stream completely: execute every move/toggle burst with no
  machine ticks interleaved (the machine never observes the cursor in
  transit), and park the cursor between decisions on one designated
  home block kept dead. Residual impact: exactly one frozen-dead cell,
  constant and policy-independent (cancels in comparisons), plus RNG
  consumption — which is the accepted floor. Not available
  interactively (live timing interleaves ticks between keypresses).
- **Exact zero requires an engine-level positioned action** ("toggle
  cell (r,c)" as part of the G1 step-mode protocol), bypassing the
  grammar for Level-0 external agents. Legitimate at Level 0 — the
  agent is external by definition — and the in-grammar cursor remains
  the Level-1 embodied bridge.

---

# Round 5 — burst protocol: the cleanest observer (same day)

`greedy.py --policies burst-greedy,burst-random` implements the
zero-tick burst interface from round 4: at each decision the harness
takes a frame (the dump the engine already emits), builds the block
grid, BFS-routes the cursor from its dead home block through *resting*
blocks only, and compiles `walk + toggle + walk-back` with no machine
ticks inside — the machine never observes the cursor in transit. An
end-to-end audit of one 27-key burst showed score exactly −1 and **the
target's digit flip as the only changed block on the whole field**.
Side benefit: burst toggles always land on rest-phase blocks, so the
toggle-vs-paused-scan race is gone. Costs: longer input strings
(negligible), extra RNG consumption (the accepted channel), and
deterministic path-blocking — a mid-scan block stays blocked for the
whole burst, so some targets are unreachable at some instants (BFS
simply skips them). Not available in live interactive play, where
ticks flow between keypresses.

Action space per decision: WAIT or TOGGLE(one of 5 sampled reachable
cells). All engine-side; zero engine changes.

## Results (8 seeds, fixed engine, 10 decisions)

| policy | mean | per-seed |
|---|---|---|
| passive | −3.8 | −5 −7 −2 −1 −1 −5 −3 −6 |
| burst-random | **−10.6** | −11 −14 −8 −2 −12 −12 −12 −14 |
| burst-greedy | −3.0 | −2 −5 −2 −1 −3 −1 −4 −6 |

- **The free channel is gone and it shows.** Greedy's edge over passive
  collapses from +2.2 (round 3, wandering cursor) to +0.8 (3 wins, 3
  ties, 2 losses) — clean confirmation that most of the earlier
  "steering skill" was pause-positioning and free trajectory rerolls,
  not toggling. What remains is the true value of ±1-priced positioned
  interventions under a 1-step oracle: small at this horizon.
- **Positioned random intervention is much more destructive than
  wandering** (−10.6 vs round 3's −6.9): every burst action is now a
  real, priced, spatially-committed intervention.
- The interface prices exactly the causal channel and nothing else —
  this is the version of the benchmark worth building learning agents
  against. Open economy question, now sharp: at ×5 rewards
  (birth +5 / toggle −5) does a longer-horizon or learned policy make
  toggling pay?

## Design notes from discussion (baselines, starting states)

- **Starting configuration** (making explicit what the cfg encodes): 36
  `^oXX` seeds place alive blocks at *random grid-aligned positions*,
  so every `--seed` is a different soup (overlaps merge; ~30 distinct
  blocks typical), deterministic given the seed. The cursor spawns on a
  dead block at grid-aligned centre.
- **Budget-matched (yoked) random** is the better control for greedy:
  condition random's toggle count on the count greedy chose for the
  same seed, with random placement/timing. That decomposes greedy's
  edge into "how much to act" vs "where/when to act" — the current
  free-running random conflates both (it acts ~9× per episode, greedy
  ~1×). Standard yoked-control design; cheap since greedy's per-seed
  action counts are in the CSVs. Queued for the next measurement round.
- **1-step greedy over 5 sampled cells is a weak skyline**, not a
  baseline to beat — stronger references when this matters: full-cell
  candidate sets, multi-step lookahead / MCTS over burst actions, and
  randomized-evaluation variants (which also close the oracle loophole).
- **Empty-board episodes** ("zero score forever until the first
  intervention") are attractive — pure creation, no soup luck — but
  currently impossible for the in-grammar cursor: rest-gated movement
  and toggling need materialized blocks, and an empty field has none.
  Becomes natural with the G1 positioned-action API. The underlying
  question is worth keeping regardless: *which seeded patterns maximise
  birth flux in asynchronous Life* — async still-lifes, quasi-
  oscillators and their flux economies are an ALife question of
  independent interest.
