# fabric — a rewriting substrate that learns

Status: research line opened 2026-09-12; nothing run yet. Name from
Wolfram's phrase for what a neural net is: a *computing fabric* of
simple identical parts that can be incrementally modified — and his
remark that for bit-parallel rewriting systems nobody knows how to do
the modification, "but there is no reason to think it isn't possible."

## The claim in one paragraph

Zahradnice already does the modification: the bandit chapter learned,
reversed, forgot and paid the price of plasticity with weights that are
tokens and no optimizer anywhere. What it never faced is *depth* —
credit assignment across layers — and *scale*. This line treats one
screen as one layer (it is a stochastic perceptron), stacks layers as
bands of a tall screen, keys inference and learning rule sets by the
trigger character (the fabric's free global broadcast bus), and
declares a rule family — write-once, decided-input-gated, anchor-only
writes — under which the outcome distribution is **independent of the
schedule**. That last property is what the nights arc proved the
substrate does *not* have in general; designing it in is what makes a
synchronous GPU port exact rather than a distortion, and is the line's
answer to "maximal parallelism at inference and learning".

## The ladder in one screen

| tier | question | rungs | where |
|---|---|---|---|
| 0 | is a glyph a weight? | perceptron in glyphs; XOR must fail | repo, 1 session |
| 1 | depth without credit | CA reservoir; Hebb+competition; **learning by keeping** (mask over fixed random laws) | repo, 1–2 |
| 2 | credit by broadcast | eligibility traces; direct feedback alignment on the bus; Forward-Forward | repo, 1–2 |
| 3 | credit by geometry | **spatial sign-backprop** — the synapse cell touches both neurons, so weight transport is free | repo, 1–2 |
| 4 | what only rewriting can ask | structural plasticity; architecture as matter + selection over learners; consensus inference; phase-free online learning | repo, 2–4 |
| 5 | scale, and the Wolfram bet | port & validate; replica ensembles; MNIST-class in the room; learnability vs size; pipelined depth | GPU sibling |

Tiers 0–3 are the on-ramp: recover known results, exactly accounted,
fast. The sessions belong to tiers 4–5.

## Recommendations made here (all reversible)

1. **Stay in the repo through tier 3.** Everything is cheap, exact and
   already instrumented; a supervised sample is ~30 events.
2. **Start the GPU sibling at the first scale-limited question**, not
   before, and never by abandoning the language: the cfg family is the
   spec, the sibling is the runtime, replay is the oracle. This laptop
   has no NVIDIA GPU; prototype in torch (runs on both boxes).
3. **Engine lifts are allowed but triggered**: the episode protocol
   (feed-until-quiescence + mid-run output read) is the one to build
   first; a confluence checker is the one that matters most; numeric
   glyph classes and a third dimension are deferred to the sibling.
4. **Bet on two credit families**: learning-by-keeping (it is the kept
   paper's through-line in a network) and spatial sign-backprop (the
   substrate's own gift). Broadcast families are the control group.

## Files

- `00-foundations.md` — vocabulary (neuron, synapse, layer, phase, bus,
  quiescence), the sampler as nonlinearity, the schedule-independence
  principle, the credit-assignment landscape ranked, economics, and
  what the restricted family forbids (the actual payoff).
- `01-ladder.md` — the rungs with predictions, kill criteria, costs,
  needs; decision points; first four sessions.
- `02-engine-lifts.md` — L-A…L-G, each with its trigger; the keep-
  rejected list.
- `03-gpu-sibling.md` — data model, step, learning, validation
  contract, size; when and where to start it.
- `05-fpga.md` — the fabric in silicon: what maps, sizing (hobby boards
  vs MNIST, learning vs inference), boards and prices, plan, triggers.
  Parked.
- `04-related-work.md` — Tsetlin machines, ReCA, supermasks, three-
  factor rules, DFA, Forward-Forward, sign-symmetry, NCAs, hardware
  niche; fit per rung; citations from memory, verify before use.

## Lineage inside the repo

`experiments/bandit` (learning in matter), `experiments/garden`
(selection over learners), `experiments/openworld` (law in matter via
gate glyphs), `backlog/research/research-rl-ai.md` §11 (GPU verdict
this line partly reverses, for a stated reason) and §13 (laws/matter
boundary — unchanged: weights are matter, laws stay frozen),
`backlog/research/substrate-mismatches.md` (why global scalars and
back-arrows stay rejected; the bus is a broadcast, not a reduction).
