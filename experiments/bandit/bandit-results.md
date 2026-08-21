# bandit: the route-3 summit — learning without an optimizer (2026-08-21)

The founding question of the route-3 chapter (research-rl-ai.md §3,
§14): can reward-coupled adaptation live entirely in state — no
optimizer, no runtime weight mutation, laws immutable? **Answer: yes,
demonstrated, with the economics of learning emerging unprogrammed.**

## Design (25 rules, `gen_bandit.py`)

Ground `.` blooms flowers x/y — the two arms. Season is *time, not
space*: the input trigger char (`a`/`b`) is the environment, and it
decides which arm pays. The poster rule of the chapter (one rewrite =
read policy + act + get reward + learn):

```
==.ax20   1 0.5
⠋@.@@⠋
```

— "under season `a`, a ground cell with an x-token west and ground
east blooms x, scores +1, and deposits a new x-token east." Policy =
token masses (mass-action); learning rule = deposit in the same
rewrite that scores; forgetting = token decay (D); exploration floor
= base bloom rate (B). The arms are exactly symmetric — same
geometry, same weights, no mortality channel at all — so any policy
shift is pure reward-following. `LEARN=0` strips only the deposit
cells: the control has identical physics with reward disconnected
from state. Parameters: B=0.05, C=0.5 (catalytic), W=1 (wilt),
D=0.03 (two manual tuning iterations: D=0.002 → reversal too slow,
token crowding at 60% of field).

All 24 runs reconcile exactly (trace-replayed flower/token
populations ≡ final screen glyphs).

## Results (33×64, 180k events, 6 seeds per arm)

**1. It learns, fast, and re-learns reliably.** Acquisition from
blank slate: policy 0.5 → 0.75 in 2k events (6/6 seeds). Correct-arm
policy in the tail of *every* season block: 0.87–0.96 (36/36
block×seed combinations). Reversal: correct-policy crosses 0.5 at
14.7k [14–16k] and 0.75 at 19.2k [17–21k] events (n=30 flips).
Unlearning is ~7× slower than learning — the old archive must decay
or be crowded out before the new one wins: proactive interference,
uninvited.

**2. Steady-state capture matches jump-chain theory quantitatively.**
Every event is something (bloom/wilt/decay), so perfect play captures
π/(2+π) of events as reward. Predicted at measured π≈0.90: 310/1000.
Measured learner block-tails: 304–324/1000. Control prediction
(π=0.5, no decay events): 250/1000; measured 251. A +25% steady-state
advantage over the non-learner.

**3. The economics of learning emerge, unprogrammed.** Net reward
over 180k events:

| season blocks | learner | control |
|---|---|---|
| 30k (5 reversals) | 40,697 | **45,095** |
| 90k (1 reversal) | **54,681** [54.5k..54.9k] | 45,070 [44.8k..45.3k] |

With frequent reversals the learner *loses* net — each flip costs
~15–19k events of wrong-way bias, worse than random. With one
reversal it wins by +21%, ranges non-overlapping. The control is
invariant to the schedule (as it must be). **Learning pays only when
the environment persists longer than the relearning time** — the
classic adaptive-value-of-learning condition (environmental
predictability / cost of plasticity), here as a measurement, not an
assumption.

## Lineage (this is MENACE, and that is the point)

The mechanism is not new — it is Michie's MENACE (1961): matchboxes
of coloured beads, policy = bead counts, move = draw a random bead,
reinforcement = add beads on a win (Gardner's hexapawn HER, 1962, is
the popular copy; modern kin: physical / in-materio learning). Per
the program's thesis (§13) novelty-of-mechanism was never the claim;
native cost and closure were. What is ours: (1) **closure** — MENACE
needed Michie's hands to move the beads after each game; here the
update is executed by the same rewrite that earns the reward, no
operator anywhere in the loop; (2) **the memory has ecology, not a
table** — spatial tokens gave us proactive interference, fertile
ruins and the learning-economics crossover, phenomena a lookup table
cannot host; (3) **one process** — play, exploration, learning,
forgetting and reward collection are a single jump chain, which is
why the π/(2+π) arithmetic exists and is met exactly. One gift back
from the lineage: MENACE also had *punishment* (bead confiscation on
a loss) — we only have passive decay, and unlearning is our 7×
slowest step. A confiscation rule (an unpaid bloom eats an adjacent
token, read-and-eat) is one line and targets exactly that; the
obvious next tweak if the chapter ever reopens.

## The 1961 amendment: punishment (added same day, user-directed)

MENACE's confiscation, implemented as promised — one rule per arm
(`bandit-punish.cfg`, PUN=0.5): the east lane becomes a ledger.
Deposit writes it on reward; an unpaid attempt advised by an east
token blooms (the failed try) and eats the adviser in the same
rewrite:

```
==.bx20   0 0.5
@⠋@@.
```

Results (6 seeds each, 12/12 exact):

| schedule | reward-inaction | **reward-penalty** | no-learning |
|---|---|---|---|
| 30k blocks | 40,697 | **52,332** [52.3..52.4k] | 45,095 |
| 90k blocks | 54,681 | **57,036** [56.9..57.1k] | 45,070 |

- Reversal to-0.5: 14.7k → **5.0k** (30/30 flips at the same sample);
  to-0.75: 19.2k → **7.7k**. Unlearning ~2.5× faster; active
  confiscation attacks exactly the proactive-interference step.
- Steady-state capture 322/1000 — unchanged, as predicted: in the
  correct regime punishment has nothing to eat.
- **The plasticity crossover moved left of 30k**: with punishment the
  learner beats the non-learner even on the fast schedule (+16%
  where reward-inaction lost by 10%). The 1961 recipe pays the cost
  of learning.
- The extinction burst, on schedule: in the first post-reversal
  window policy still reads 0.93 while the old archive crashes
  1216 → 358 — punishment blooms *are* attempts at the old arm, a
  surge of the extinguished behaviour before the cliff. Behaviourist
  textbook, uninvited.
- Untuned: PUN=0.5 was the first value tried; no claim of optimality.

Taxonomy note: this promotes the automaton from linear
reward-inaction to linear reward-penalty — see below.

## RL taxonomy

Not ε-greedy (no argmax anywhere), not UCB (no attempt counts, no
optimism — and hence *linear* regret on stationary problems), not
Thompson (a point-mass field, not a posterior; the ~1/√N demographic
readout noise is an uncalibrated cousin of posterior-width
exploration at best). The exact family: **probability matching on
additively-reinforced propensities with forgetting and a constant
exploration floor** — the Roth–Erev reinforcement model of
behavioral game theory ≡ a linear reward-inaction learning automaton
(Tsetlin; Narendra–Thathachar), promoted to reward-penalty by the
confiscation rule; behaviorally, Herrnstein's matching law. The
policy is *non-contextual* in a contextual world — tokens are
season-blind, only reward is season-gated — which is precisely why
reversal costs unlearning; season-indexed token species would store
π(a|s) MENACE-style (a box per state) and turn reversal into an
addressing switch. The exploration floor B is the ε-analog, never
annealed: its measured price is the 0.95 policy ceiling and the
310-vs-333 capture gap; its payoff is that reversals get discovered
at all — the right trade for a nonstationary world (the same reason
EXP3 keeps its γ).

## Honest limits

- Deposits go east only (bodies read tokens from W/N/S) — a spatial
  anisotropy; arms share it, so the readout is unbiased, but token
  chains drift eastward.
- "Ruins are fertile": a decaying token cluster has high perimeter
  and stays catalytically loud per token — old policies resist
  replacement beyond their mass (part of the 7× unlearning cost).
- Parameters were hand-tuned in two smoke iterations; no claim of
  optimality. The crossover block length was bracketed (30k, 90k),
  not resolved.
- Policy ceiling 0.95, not 1.0 — the exploration floor B is load-
  bearing (it is what discovers reversals) and caps exploitation:
  the exploration–exploitation trade-off, present by construction.

## The testbed: environment + swappable agents, zero engine change

The framework question ("can different policies be tested in the
same environment?") answered by composition — `#include`, which the
engine has had all along (`gen_testbed.py`): `env-core.cfg` is the
environment as a rule library (field, action space, reward function,
no learning); an agent is a top-level cfg adding its rule mass on
top: `agent-null` (env alone = random policy), `agent-lri` (env +
`lri-rules.cfg`), `agent-lrp` (env + lri + two confiscation rules,
nested include). Same schedule, same seeds, 30k blocks, 18/18 exact:

| agent | net reward |
|---|---|
| agent-null | 45,095 [44,964..45,305] |
| agent-lri | 42,549 (plasticity cost, reproduced) |
| agent-lrp | **53,840** [53.7k..54.0k] |

Bonus proof of shared-environment: agent-null's per-seed scores are
**bit-identical** to the monolithic `bandit-nolearn` runs — the
agent's never-applicable rules leave the jump chain untouched, so
differently-composed programs produce literally the same world.
Second tier for policies outside the mass-action family (UCB's
argmax, etc.): the deterministic prefix-replay loop
(`experiments/steering/greedy.py` pattern) — any external algorithm,
same environment, no engine change either.

Also catalogued as expressible (not run): **coarse coding** — token
species per overlapping season-feature (arcs on a season ring),
readout sums containing features, deposits split across them =
linear function approximation / tile coding in glyphs; answers the
context-cardinality/data-fragmentation trade by pooling through
shared features.

## Chapter verdict

Route 3's question is **answered in the affirmative**: reward-coupled
adaptation, acquisition, reversal, forgetting, exploration — all in
25 immutable rules on the stock engine, all exactly accounted, and
the phenomenon brings its own textbook theory out in the numbers
(jump-chain capture rates, proactive interference, the plasticity
crossover). Stigmergy (route 2) and mutable-weights (route 3)
coincided as predicted: the token is a pheromone; the pheromone is a
weight. Per §14, what remains for closing the chapter is the
synthesis document; the parked-with-conscience list stands.

Files: `gen_bandit.py` (B/C/W/D/LEARN/OUT), `bandit.cfg`,
`bandit-nolearn.cfg`, `bandit_stats.py`, `banditsweep.sh`
(BLOCK/TAG), `summary.csv`, `summary-long.csv`, per-run series.
Watchable: `./zahradnice experiments/bandit/bandit.cfg` — hold `b`
to change the season under its fingers.
