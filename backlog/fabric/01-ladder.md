# The ladder: a hierarchy of experiments

Status: proposed 2026-09-12, none run. Each rung states what it tests,
the prediction, the kill criterion, what it needs (engine lifts from
`02-engine-lifts.md`, referenced as L-x), and a cost in sessions. A rung
that fails does not end the line; it names a structural obstruction,
which is a result (the route-3 doctrine).

Reading rule: tiers 0–3 are the **on-ramp** (recover known learning
results inside the substrate, exactly accounted); tier 4 is **what only
this substrate can ask**; tier 5 is **scale**, on the GPU sibling. The
on-ramp should be climbed fast; the sessions belong to tiers 4–5.

Common protocol for every supervised rung (zero engine change):

```
per sample:  0/1…  type the input bits (a write head walks the input row)
             i…    inference phase: immediate trigger, fed until quiescent
             +|−   teacher: the true label (one char per class) — or reward sign
             l…    learning phase, fed until quiescent
             c…    clear activities (not synapses) for the next sample
```

The teacher never touches a synapse. Correctness is *scored*: a rule
matching "output cell for class k fired ∧ label glyph k present" scores
+1, so the engine's exactly-accounted score is the learning curve, and
trace replay reconciles synapse populations against the final screen
exactly as `bandit_stats.py` does today. Seeds ×6 minimum; report
ranges, not means.

---

## Tier 0 — the perceptron in glyphs (1 session)

**R0.1 Bit perceptron.** Layout A collapsed to one layer: k=8 input
cells, one output neuron, 8 synapse cells with signed magnitude glyphs
(N=4), refuse weight θ. Learning rule = perceptron/Tsetlin: on teacher
`+` with output `0` → every synapse whose input fired steps +1; on `-`
with output `1` → steps −1; otherwise nothing. Task: majority-of-8 and
random linearly separable threshold functions; inputs drawn uniformly.
- *Prediction:* converges to ≥95% accuracy within a few hundred
  samples; mistake count finite and comparable to the perceptron bound
  scaled by the sampler's noise floor (θ sets an ε that never anneals,
  as B did in the bandit).
- *Kill:* no better than chance after 10⁴ samples on majority-of-8 ⇒
  the glyph-as-weight / weight-as-rate encoding is broken; fix the
  representation before anything deeper.
- *Needs:* generator `gen_fabric.py`; L-A (episode protocol) or
  over-feeding; nothing else.

**R0.2 XOR must fail.** Same fabric on XOR-of-2 embedded in 8 bits.
Recorded as the control that motivates depth; also measures the
substrate's *failure signature* (does the policy oscillate, or settle
on a 75% solution?).

**R0.3 Contextual bandit and coarse coding** (already catalogued in
`bandit-results.md`). Not strictly on this ladder, but cheapest possible
check of two things the ladder relies on: a state-indexed weight
(reversal becomes addressing — prediction from the notes) and shared
features pooling data (tile coding). Half a session, on the existing
bandit generator.

---

## Tier 1 — depth without credit assignment (1–2 sessions)

**R1.1 CA reservoir + learned readout (ReCA in glyphs).** Between the
input row and a tier-0 readout, insert bands running a *fixed* rewriting
rule — a 1-D elementary CA (rule 90 / 110 in a band with a few rules
each) or a random rule table — for a few sweeps; the readout learns
over the expanded state. Tasks: XOR, 3-bit parity, the 5-bit memory
task of the reservoir literature.
- *Prediction:* XOR and parity become learnable with no credit
  assignment at all; accuracy rises with reservoir width/depth up to a
  plateau. This is the literal "cellular automaton as hidden layer".
- *Kill:* no gain over R0.2 at any width ⇒ the readout's stochastic
  linear unit cannot exploit the expansion; revisit §2 of foundations
  (θ, magnitude range).
- *Needs:* nothing new.

**R1.2 Unsupervised layers with competition (Hebb + WTA).** Hidden
synapses learn by co-activity (deposit when pre∧post fire) with a
confiscation rule implementing lateral competition (a neighbour that
fired eats a token of one that did not); only the top layer is
supervised. Krotov–Hopfield in glyphs.
- *Prediction:* modest gain over R1.1 on bitmap tasks (4×4 shapes),
  none on parity.
- *Needs:* nothing new; rule count ~2× R1.1.

**R1.3 Learning by keeping (supermask in matter).** Synapse magnitudes
are **rolled once at init and never change** (they are laws: rule
weights); the only learnable bit is whether the synapse *exists*.
Learning = keep/kill with a global reward on the bus: a synapse whose
pre∧post fired on a rewarded sample is kept (or re-created if dead), on
a punished sample killed with probability p. This is edge-popup /
supermask learning, and it is the through-line of the kept paper
("selection sees only what someone can keep") applied to a network.
- *Prediction:* a sufficiently over-provisioned random fabric contains
  a mask that solves XOR/parity, and the keep/kill rule finds it;
  required width grows with task difficulty.
- *Kill:* fails where R1.1 succeeds at equal size.
- *Needs:* nothing new. This rung is also the cheapest possible bridge
  to the GPU sibling (the mask is one bit per synapse).

---

## Tier 2 — credit by broadcast: the three-factor family (1–2 sessions)

**R2.1 Eligibility traces and delayed reward.** Pair cells (`#grid 2 1`):
left = activity, right = trace glyph that a firing writes and that
decays over inference events. Reward arrives *n* events late on the
bus; the learning rule deposits only where a trace survives.
- *Prediction:* the bandit generalises to delayed reward; the maximal
  bridgeable delay scales with trace decay, measured as a curve.
- *Needs:* nothing new (pair cells exist). This is the catalogued "hard
  valuable one" from the bandit chapter and unblocks any RL-style task.

**R2.2 Direct feedback alignment on the bus.** Each hidden cell carries
a fixed random *affinity glyph* per class (rolled at init — the random
feedback matrix, one entry per cell). After inference, the teacher
emits per class one bus char meaning "class k's output error is
+/−/0"; a hidden synapse updates iff its post-neuron's affinity to k
matches the sign and the pre fired. The harness computes the output
error signs from the dump; the error *transport* is the bus.
- *Prediction:* two-layer fabric learns XOR/parity and 8×8 few-class
  bitmaps clearly better than R1.1 at equal size.
- *Kill:* no better than R1.3 ⇒ broadcast credit does not beat keeping;
  the line then rests on R1.3 + R3.1.
- *Needs:* nothing new; harness reads the output row (dump) between
  phases — L-A makes that one call.

**R2.3 Forward-Forward in glyphs.** Label is embedded in the input row;
positive samples carry the true label, negative samples a wrong one.
Bus char `+`/`-` sets the phase; every layer's synapses step toward
higher "goodness" (more fired cells) on `+` and lower on `-`, purely
locally, with cell saturation as the layer normalisation. No backward
pass, no output error at all.
- *Prediction:* works on 8×8 few-class bitmaps; slower than R2.2.
- *Needs:* nothing new; negative-sample generation in the harness.

---

## Tier 3 — credit by geometry (1–2 sessions)

**R3.1 Spatial sign-backprop.** The output row compares itself to the
label (label glyphs planted beside the output row by the teacher, or
delivered on the bus): each output cell writes an error glyph `↑`/`↓`
or none. Then a *backward phase*: a synapse cell adjacent to a
post-neuron carrying an error copies the sign into its backward
channel (pair cell, right half) if its magnitude is above a floor; a
pre-neuron that fired and sees error signs in its outgoing synapses
adopts the majority sign by mass-action (write-once, so the backward
wave is also schedule-independent); a synapse with a decided error on
its post and a fired pre steps its magnitude against the error. One
wavefront per sample, ~L sweeps.
- *Prediction:* strictly better than R2.2 at depth ≥3; learns 8×8
  ten-class bitmaps to >90% with a 3-layer fabric.
- *Kill:* fails to beat R2.2 at depth 3 ⇒ 1-bit stochastic error is
  too noisy at this scale; the line keeps DFA/FF and moves on.
- *Needs:* pair cells for the backward channel (exists); nothing else.
  This rung tests the claim in foundations §4 that weight transport is
  free in a spatial fabric — the substrate's most distinctive
  contribution to the credit-assignment question.

**R3.2 Energy-based settle/nudge (optional).** A symmetric, recurrent
fabric settled freely, then with the output clamped; synapses update
by the difference of local co-activity between the two settles
(contrastive Hebbian / equilibrium propagation). Quiescence is
literally "settled". Only if R3.1 disappoints or the non-DAG rungs of
tier 4 want a principled recurrent learner.

---

## Tier 4 — what only a rewriting fabric can ask (2–4 sessions)

**R4.1 Structural plasticity.** Synaptogenesis and pruning as rules:
an empty synapse slot adjacent to a persistently erroneous post-neuron
sprouts a synapse of random sign; a synapse that has not participated
in a rewarded sample for many samples decays to empty. Topology is now
matter. Measure: does a *sparse* grown fabric reach R3.1's accuracy
with fewer live synapses, and does growth track error spatially
(Wolfram's "progressive network rewriting", measured).

**R4.2 Architecture as matter, selection over learners.** Gate glyphs
select which learning law a band runs (open-world encoding). Garden
reprise: bands running different laws (keeping, DFA, sign-backprop,
none) compete for a shared reward economy; reproduction copies a band's
gate configuration. Prediction from the garden: the winning law depends
on error cost and environment switching rate; look for a Baldwin
regime where a plastic law is invaded by a fixed one after the task
stabilises.

**R4.3 Non-DAG inference: consensus classification.** Self-classifying
patterns: every cell of an input shape must end up carrying the
shape's class, through local message rules only, with quiescence as
consensus; learning by any tier-2/3 rule. The NCA version of this task
exists (trained by backprop through time); this one has no calculus.

**R4.4 Phase-free online learning.** Remove the episode protocol
entirely: inputs stream in, the bus carries reward when it arrives,
inference and learning rules coexist (the bandit's poster rule
generalised to a fabric). Measure continual-learning behaviour: the
bandit showed proactive interference and a plasticity crossover; does
a fabric show catastrophic forgetting, and does spatial memory ecology
(ruins are fertile) mitigate or worsen it?

---

## Tier 5 — scale, and the Wolfram bet (GPU sibling; see `03-gpu-sibling.md`)

**R5.0 Port and validate.** Implement the CA-family (foundations §3) as
a synchronous sweep engine (torch prototype, CUDA later); prove
bit-exact agreement with Zahradnice on the *fixpoint distributions* of
the tier-0/1 fabrics from the same cfgs (transpiler or hand port, L-F).
Go/no-go for the sibling: it must reproduce a Zahradnice learning curve
within seed variance.

**R5.1 Replica ensembles.** Thousands of replicas: Monte Carlo
inference by vote; evolution-strategies / perturbation learning over
matter (the family that is hopeless on one CPU and natural here).

**R5.2 A benchmark in the room.** Binarised MNIST, 3-layer fabric, the
best of tiers 1–3 as the learning law. Target ≥90% with every parameter
a visible glyph — not to beat Tsetlin machines (~98%), DFA, or FF, but
to be *in the same table* with a substrate that has no multiplier, no
clock and no transposed matrix.

**R5.3 The Wolfram bet, measured.** "Incremental modification may be
easier in complicated cases than in simple ones." Fix the task and the
learning law; sweep fabric width and depth; measure the fraction of
random initial fabrics (seeds) that reach criterion. Prediction (from
lottery-ticket/supermask results): learnability rises sharply with
size — possibly a transition, which the phase-transition tooling from
`experiments/convergence` is built to locate. A negative result (flat
or falling) is equally publishable: it would say the conjecture fails
for stochastic bit-fabrics at this scale.

**R5.4 Time-as-depth vs space-as-depth.** Same law, once as *L* stacked
bands (untied, pipelinable: layer *l* processes sample *t* while layer
*l+1* processes *t−1* — a systolic array with light-cone causality)
and once as one band iterated *L* times (tied, NCA-style). Measure
accuracy and throughput; the pipelined form is the "maximal
parallelism at inference" answer.

---

## Decision points

1. **After R0.1** — representation works? If not, nothing else matters.
2. **After tier 1 + R2.2** — which credit family carries the line:
   keeping (R1.3), broadcast (R2.2/R2.3), or geometry (R3.1)? Pick by
   accuracy-per-rule and by what tier 4 needs (structural plasticity
   composes most naturally with keeping and with sign-backprop).
3. **After R3.1** — do we need the GPU yet? Only when a tier-4 question
   is scale-limited (R5.3 certainly is). Until then the repo's exactness
   is worth more than speed.
4. **After R5.0** — does the sibling host the science, with the repo as
   spec authoring and exactness oracle? Recommended answer: yes, and
   the cfg family stays the shared language so nothing authored is
   lost.

## Suggested order (first four sessions)

1. R0.1 + R0.2 + generator (representation, protocol, harness).
2. R1.1 + R1.3 (depth by reservoir; learning by keeping).
3. R2.2 + R3.1 (broadcast vs geometry, head to head on the same task).
4. R4.1 (structural plasticity) — the first question no MLP can ask —
   and the R5.0 go/no-go.

---

## Status 2026-09-12 (session 1) — see `experiments/fabric/results.md`

- **R0.1 done, faithful.** The neuron is a drift-diffusion counter
  (gambler's ruin gives a sigmoid of gain K), not the mass-action unit
  of foundations §2. AND 0.97–0.99, random threshold 0.89–0.96,
  majority 0.80–0.83; substrate ≡ arithmetic model.
- **R0.2 done**: XOR 0.50, as required.
- **R3.1 demoted**: naive sign-backprop with binary units and ±1 steps
  does not bootstrap even in arithmetic (every hidden unit is pushed to
  solve XOR alone). The geometry claim stands; the rule does not. A
  rung is now built in glyphs only after its arithmetic model learns.
- **R1.1/R1.3 partial (model only)**: frozen random hidden units +
  readout + re-rolling unused units — 8-input XOR 0.65–0.73.
- **New rung, executed: the Tsetlin-shaped fabric** (clauses as
  conjunction rows of include/exclude automata, feedback as step-vs-skip
  rule weights, 1-bit bus): **8-input XOR 0.96–0.99 with 16 clauses (S=2), 0.87–0.92 with 8**,
  731–851 rules independent of C after the translation-invariant
  rewrite (edition 1: 23k rules, 600 ev/s; edition 2: 12k ev/s).
  Parity-3 not yet (needs ~64 clauses per the model). A wildcard-trigger
  head stole typing events until keyed to its own trigger — phases must
  be disjoint rule sets.
- Rule earned: **replicate data, not rules** — a family must read at
  clause-independent offsets (weight sharing); the rule index and the
  GPU sibling both depend on it.
- Next: parity-3 at C=64; clause re-rolling (structural plasticity);
  convolutional clauses on 8×8 bitmaps; then the sibling.
