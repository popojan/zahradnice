# Foundations: a rewriting fabric that learns

Status: design, 2026-09-12. Nothing here has run. Every claim marked
*prediction* is falsifiable by a rung of `01-ladder.md`.

## 0. The sentence this line answers

Wolfram (*What Is ChatGPT Doing*, closing section on neural nets; the
user read the Czech translation) says, paraphrased: a neural net is a
flexible "computing fabric" of many simple identical parts that can be
*incrementally modified* to learn from examples; today the modification
uses calculus on real numbers, but precision clearly does not matter
(8 bits or fewer); for bit-parallel systems like cellular automata "it
has never been clear how to do this kind of incremental modification,
but there is no reason to think it isn't possible"; it may even be
*easier* in complicated cases than in simple ones; and something closer
to *progressive rewriting of the network itself* might ultimately beat
fixed-topology weight tuning.

Three of those four claims are already evidence in this repo:

| Wolfram's claim | what the repo has |
|---|---|
| incremental modification of a bit-parallel fabric | `experiments/bandit`: policy = token masses, learning = deposit in the same rewrite that scores, forgetting = decay; MENACE / L_R-P automaton in 25+2 rules, exactly accounted |
| precision does not matter | tokens are unary; Braille gives an 8-bit visible register per cell; nothing real-valued anywhere |
| rewriting the network itself | the open-world arc: law alleles as gate glyphs in matter; synapses would be cells, and cells can be created and destroyed by rules |
| easier in complicated cases | **untested** — the one claim this line can turn into a measurement (rung R5.3) |

So the question is not *whether* a rewriting substrate can learn — that is
answered — but whether the mechanism **composes** (depth), **assigns
credit** (the wall the bandit never had to face), and **scales** (the
wall Zahradnice's serial jump chain always faces). This document fixes
the vocabulary and the design principles; the ladder sequences the
tests.

## 1. Vocabulary: neurons, synapses, layers as matter

Everything below is a *cell* holding a *glyph*. Only glyphs are
matchable (colours and `$`-memory are display/restore channels — §13(c)
of `research-rl-ai.md`), so all compute-state is spelled in characters.

- **Activity cell** (neuron). Glyphs: `?` undecided, `1` fired, `0`
  refused. Within one inference phase a neuron is *write-once*: rules
  anchor only on `?`, and write `1` or `0` exactly once.
- **Synapse cell**. One cell, physically adjacent to its pre-neuron and
  its post-neuron. Its glyph is a signed small integer — the weight —
  spelled as a glyph family (e.g. Braille `⠁⠃⠇⠏` for +1..+4 and another
  row of the block for −1..−4; or two token species as in the bandit).
  A synapse with magnitude *k* contributes to its post-neuron through a
  rule whose **header weight is k**: the law maps glyph → rate, the
  glyph *is* the parameter. Learning rules rewrite the glyph by ±1.
  This is a Tsetlin automaton per synapse (a counter with include/
  exclude semantics), the same object as the bandit's token count with
  the count folded into one cell.
- **Layer**. A geometric band of the screen: an activity row (or block
  row), then synapse rows, then the next activity row. "Stacked
  screens" is literally a tall screen (`--screen R,C`) with bands;
  inter-layer rules are vertical bodies spanning a band. Connectivity
  is therefore **local** (a neuron sees the synapses in its window,
  which see the pre-neurons in *their* window): the fabric is
  convolutional by construction, dense connectivity does not exist, and
  receptive fields grow with depth. That is a feature, not a
  limitation to apologise for — it is what makes every rule O(1) and
  the whole thing parallel.
- **Phase**. The trigger character of the event. Rules are keyed by
  trigger, so *the input stream selects the active rule subset*:
  `i` = inference rules, `+`/`-` (or `r`) = teacher/reward rules, `c` =
  clear-for-next-sample rules, `0`/`1` = "type the next input bit".
  The user's "one rule set learns, another (subset) infers" is exactly
  this, zero engine change. The trigger is also the fabric's **global
  broadcast bus**: one character reaches every cell at zero cost. In
  neuroscience terms it is the neuromodulator of a three-factor rule;
  in Tsetlin-machine terms it is the team feedback. Anything the
  teacher knows (label, reward sign, phase) can ride it.
- **Quiescence**. "No rule applicable" is already engine-detected
  (`idle_timeout_ms`); headless it needs G6 (feed-until-quiescence) or
  over-feeding of the phase trigger. "Inference is done when nothing
  applies" — the user's definition — is the write-once design's natural
  halting condition: it halts when no `?` remains.

### Layout A (one hidden layer, kernel width 3)

```
row r    : A0  A0  A0  A0  A0  A0     input activity   (typed in via triggers 0/1)
row r+1  : S-  S-  S-  S-  S-  S-     synapse for input at column offset −1
row r+2  : S0  S0  S0  S0  S0  S0     synapse for input at column offset  0
row r+3  : S+  S+  S+  S+  S+  S+     synapse for input at column offset +1
row r+4  : A1  A1  A1  A1  A1  A1     hidden activity
row r+5..: (repeat)                    … output row, and beside it the label row
```

The neuron at `(r+4, c)` reads pre-neuron `(r, c+d)` and synapse
`(r+2+d, c)` in one vertical body — two read cells, five rows tall.
The synapse at `(r+2+d, c)` reads pre `(r, c+d)` and post `(r+4, c)` in
its learning rule. Body geometry beyond 4 cells is fine for the engine
(the ≤4-cell window was the nights' *family* constraint, not a law of
the machine). A generator lays this out; `zahradnice-check explain`
verifies it.

## 2. The neuron's nonlinearity is the sampler

*Amended 2026-09-12 after R0.1:* the unit below is too soft to be a
neuron (5:4 evidence gives P=0.53). The built neuron is a
**drift-diffusion counter**: a state glyph walks ±1 with the masses
below and decides at ±K, so P(fire) = 1/(1+((u+θ)/s)^K) — gambler's
ruin turns linear odds into a sigmoid of gain K, at the price of ~K
events per decision and 2K−1 glyphs (the rule index makes the state the
anchor, so the rule count does not cost scan time). The rest of this
section describes the one-step unit for the record.

*Pointer, not a plan:* the fixed ±K barriers are textbook biased
gambler's ruin (one line). If decision-time control is ever wanted —
bounds that collapse toward a deadline instead of a hard budget — the
walk meets a *sloped* barrier and its hitting probabilities become
lattice-path survival problems; the machinery for those (fair-coin
survival under a Beatty barrier, Sparre Andersen, Cramér tilting for
the biased case) is worked out in the orbit repository's
`docs/papers/lattice-paths-beatty-barrier.tex`. Same family, not
needed for fixed K.

A neuron with satisfied (pre fired ∧ synapse +k) pairs of total mass
*s* = Σk, inhibitory pairs of mass *u*, and a constant "refuse" rule of
weight θ fires with probability

    P(fire) = s / (s + u + θ)

— a saturating, Michaelis–Menten-shaped transfer, stochastic, with θ the
threshold. It is a nonlinearity, so depth composes nonlinearly (the
reservoir/XOR rungs test exactly this). It is *not* a step or a
sigmoid: mass-action adds, it does not exponentiate. Consequences:

- Inference is a **sample**, not a value. Repeating inference = Monte
  Carlo; on the GPU sibling, thousands of replicas vote for free.
- A deterministic threshold is expressible (count into a Braille
  register with a one-shot cascade, then compare) at a rule cost the
  GPU sibling avoids by having a `count` primitive. Do not build it in
  Zahradnice unless a rung demands it.
- Signed weights come from two rule families feeding *s* and *u*; the
  synapse glyph's sign selects the family.

## 3. Design principle: decided-input gating ⇒ schedule independence

This is the load-bearing idea of the whole line and the reason the GPU
port is legitimate.

The nights and λc(N) work established that Zahradnice's physics is the
*serial* jump chain, and that any parallel batching of one derivation
**shifts the trajectory measure** (§11.3: "just run the rules on
fragments quietly changes the physics"). A learner, however, does not
need the jump chain. Require of the fabric's rule family:

1. **Write-once per phase.** In a phase, each cell is rewritten at most
   once, along a fixed order (`?` → `0|1`; synapse glyph → glyph±1).
2. **Decided-input gating.** A neuron's rules match only when every
   input they read is *decided* (`0`/`1`, never `?`). A synapse's
   learning rule matches only when both its neurons are decided and the
   phase glyph is present.
3. **Anchor-writes only** (CA semantics): the RHS writes the anchor
   cell. The bandit's "deposit east in the same rewrite" becomes two
   rules — the neuron fires, the synapse cell *sees* pre∧post∧phase and
   updates itself — with the correlation preserved because the phase
   broadcast is global.

Under 1–3 the outcome distribution of a phase is **independent of the
schedule**: conditional on being selected, a neuron samples fire/refuse
∝ masses that depend only on its (already decided) inputs, so the joint
law is a product in topological order, whatever interleaving — one cell
per event (Zahradnice), *N* non-conflicting per step (`#threads`), a
checkerboard sweep, or a full synchronous sweep on a GPU. The
distortion documented for the contact process **cannot occur by
construction**. Corollary: on a GPU, inference is *L* synchronous sweeps
for *L* layers, learning one to *L* sweeps — a stochastic integer
forward pass, which is how this family should be understood at its
fixed-topology limit (see §6, "what the restriction forbids").

A static checker for 1–3 (`zahradnice-check confluent`, lift L-E in
`02-engine-lifts.md`) is the portability contract between the repo and
the sibling.

## 4. Credit assignment: the landscape, ranked for this substrate

The bandit was cheap because reward and parameter coincide in one
rewrite. A layered fabric separates them; the whole difficulty of the
line is delivering "you were wrong" to a cell that was not where the
error showed. Candidate families, ordered by fit (details and
citations in `04-related-work.md`):

| family | needs | substrate fit | rung |
|---|---|---|---|
| no credit at all: fixed random depth + learned readout (reservoir, ReCA) | nothing | perfect; the rewriting layers *are* a CA reservoir | R1.1 |
| unsupervised local + supervised top (Hebb + competition) | local co-activity, WTA via confiscation | good; rule cost moderate | R1.2 |
| learning by keeping: fixed random weights, learned mask (supermask / edge-popup) | present/absent bit per synapse, global reward | perfect; "selection sees only what someone can keep" literally | R1.3 |
| three-factor Hebb + eligibility trace, delayed reward | hidden channel per cell (pair cell / Braille bit) | good; the catalogued "hard valuable one" | R2.1 |
| direct feedback alignment via broadcast | per-cell fixed random class affinity glyph; per-class error sign on the trigger bus | very good; the transposed matrix becomes a *glyph rolled at init* | R2.2 |
| Forward-Forward (positive/negative phase, per-layer goodness) | phase bit on the bus; negative samples from the harness | very good; no backward pass at all | R2.3 |
| **spatial sign-backprop**: error *sign* wavefront through synapse cells | nothing beyond locality | uniquely good — see below | R3.1 |
| equilibrium propagation / contrastive Hebb | energy-based symmetric dynamics, two settles | plausible, exotic; quiescence = "settled" | R3.2 |
| perturbation / evolution strategies | many replicas | poor on one CPU, excellent on the GPU sibling | R5.1 |
| arithmetic backprop | real-valued nonlocal gradient | CPU emulator — keep rejected (§13(a)) | — |

**Why spatial sign-backprop is the substrate's own gift.** The
weight-transport problem of backprop is that the backward pass needs
Wᵀ, which the brain (and any local fabric) cannot access. In a spatial
fabric the synapse is **one cell adjacent to both of its neurons**: the
same cell that carried the forward contribution can copy its
post-neuron's error sign into a backward channel its pre-neuron reads.
Symmetry is geometry, not a matrix. What remains is 1-bit error
(sign-only, stochastic accumulation by mass-action) gated by the
pre-neuron's own activity (the ReLU derivative, known locally). Sign-
symmetric and 1-bit-error backprop are both known to train real
networks to near-backprop accuracy; here they cost a wavefront of ~L
sweeps per sample and zero nonlocal machinery. §13's "backprop = CPU
emulator" verdict was about real-valued nonlocal gradients; this is
neither, and the ladder tests it as its own rung rather than assuming
it.

## 5. Economics, honestly

- Zahradnice: ~2.1k events/s generic matcher; 96-rule union 43 µs/event
  at ring 64. Layout A with 8 inputs, N=4 magnitudes: ~250 generated
  rules; ~30 events per supervised sample ⇒ ~70 samples/s ⇒ 10⁴ samples
  in minutes. Tiers 0–3 at toy scale (8–64 inputs, 1–3 layers, boolean
  functions, 4×4 / 8×8 bitmaps, ≤10 classes) are **cheap and exactly
  accounted** here — this is where mechanisms get *trusted*.
- MNIST-class (28×28, 60k samples, ≥3 layers) is 10⁶–10⁷ events per
  epoch per replica: hours per epoch here, seconds on a GPU. That is
  the hand-off point, and the CA-family contract (§3) is what makes the
  hand-off lossless.
- Run-time will *never* compete with tensor kernels (3–5 orders, §13);
  the payoff is elsewhere: (i) an asynchronous, clockless, multiplier-
  free, bit-level learning fabric — the niche of Tsetlin-machine
  hardware, in-materio computing and neuromorphic fabrics, where a
  global clock and a transposed matrix are exactly what you cannot
  have; (ii) every parameter is a visible glyph — the network *is* the
  screen; (iii) the questions of §6.

## 6. What the restriction forbids — and why that is the point

At the fixed-topology, DAG, phase-separated limit the fabric **is** a
quantized stochastic MLP with a local learning rule. Recovering known
results there (tiers 0–3) is validation, not the contribution. The
contribution lives in what a tensor MLP cannot express and a rewriting
fabric gets for free:

1. **Structural plasticity.** A synapse is a cell; rules can create,
   move and delete cells. Growing connections where error persists and
   pruning idle ones is *the same kind of rule* as changing a weight —
   Wolfram's "progressive network rewriting" with no special machinery.
2. **Architecture as matter.** Gate glyphs (the open-world trick) make
   the effective law per region a property of the state: one fabric can
   run Hebbian rules in one band and sign-backprop in another, and
   selection can choose between learning laws (the garden, reprised).
3. **Non-DAG inference.** Nothing forces layers: recurrent, wave-like
   settling to consensus (self-classifying patterns) is just another
   rule set with the same halting condition.
4. **One process.** The bandit's poster rule — read policy, act, score,
   learn in one rewrite — has no phase boundary. A fabric that learns
   *while* inferring, online, with no episodes, is the natural end
   state and has no tensor analogue.

The ladder climbs the on-ramp quickly precisely so that the sessions
are spent on 1–4.
