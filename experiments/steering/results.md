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
