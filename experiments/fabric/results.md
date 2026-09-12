# fabric — session 1 results (2026-09-12)

Question of the day: could a rewriting substrate learn with depth, using
only local rules and a one-character broadcast bus? Verdict after one
session: **yes for the Tsetlin-shaped fabric** (XOR with six irrelevant
inputs learned to 96–99 %), **no for naive sign-backprop** (does not
bootstrap in its own arithmetic model), and the perceptron in glyphs is
faithful to its model to the percent. Nothing here is tuned; every number
is a first run.

Files: `gen_fabric.py` (R0.1), `gen_tm.py` (Tsetlin fabric), `fabric_run.py`
(headless harness: types samples, feeds phases, reads outcomes from the
trace), `model_r01.py` / `model_r31.py` / `model_tm.py` (the same rules as
plain arithmetic — the control that separates "substrate is wrong" from
"rule is weak"), `sweep-*.txt` (raw runs).

## R0.1 — the perceptron in glyphs

Design departure from the backlog: a mass-action unit fires with
P = s/(s+u+θ), which is far too soft (5:4 evidence gives 53 %). The
neuron is therefore a **drift-diffusion counter**: a state glyph walks
±1 with up-mass s (active inputs × positive synapse magnitudes, as rule
weights) and down-mass u+θ; it decides at ±K. Gambler's ruin turns the
sampler's linear odds into a sigmoid of gain K in log-odds:
P(fire) = 1/(1+((u+θ)/s)^K). The rule index makes the state the anchor,
so 2K−1 states × 9 inputs × 8 magnitudes × 2 signs (≈5k rules at K=16)
cost ~145 dry-runs per event.

Protocol per sample (all keys, no timing): type 8 bits with a write
head (`0`/`1`), `i`×budget (walk), `p`/`n`×10 (teacher: mark + one
perceptron step per active synapse, write-once by consuming the input),
`c`×14 (clear). ~100 events per sample, **~90–150k events/s**.

| task (8 inputs) | K=8 | K=16 | K=32 | arithmetic model (K=16) |
|---|---|---|---|---|
| AND | 0.90–0.94 | **0.97–0.99** | 0.96–0.98 | 0.98–0.99 |
| random threshold | 0.87–0.90 | 0.89–0.96 | 0.91–0.95 | 0.92–0.95 |
| majority-of-8 | 0.76–0.79 | 0.80–0.83 | 0.82–0.83 | 0.81–0.83 |
| XOR (control) | 0.48–0.52 | 0.50–0.51 | 0.49–0.53 | — |

(4 seeds, 3000 samples, accuracy over the last 750.) Substrate ≡ model.
The 80 %-on-AND first result was a glyph collision (`f` was both the
false-alarm marker and synapse −6; the clear rule then turned a synapse
into a rogue neuron) — found by comparing against the model, fixed by
renaming markers to `+ - /`. Undecided walks at K=32 (~25 % within a
300-event budget) show the random-walk cost near the boundary.

## Depth, attempt 1 — sign-backprop: does not bootstrap (model only)

Two-layer fabric, hidden units and output as counters, hidden "todo" =
output error × sign of the outgoing synapse, gated by the unit's own
activity, unit steps. In arithmetic: **50 % on 2-input XOR** for every
variant tried — random init, nonzero output weights, one-unit-per-error
credit, lower step probability, exploration floor, reward-modulated
(REINFORCE-style) instead of sign. The output layer alone learns XOR to
99 % from ideal hidden features, so the failure is feature discovery:
with binary units and ±1 steps every hidden unit is pushed toward the
same impossible target (XOR itself), collapses to OR, and the output
weights random-walk around ±1. Real-valued shadow weights are what make
this family work elsewhere; the substrate's honest version of a shadow
weight is a finer counter with small step probability, which did not
rescue it at 40k samples. **Not built in glyphs; R3.1's kill criterion is
met at the model level** for this rule. The geometry claim (weight
transport is free) is untouched — the rule is the problem.

Frozen random hidden units + learned readout (R1.1/R1.3) work only with
large random magnitudes and re-rolling of unused units: 2-input XOR
77–95 %, 8-input XOR 65–73 % (model, H=32, re-roll every 1000).

## Depth, attempt 2 — the Tsetlin-shaped fabric: learns XOR

Architecture (Granmo's Tsetlin machine, simplified): C clauses, each a
row of 2×8 literal automata (state 1..16 as glyphs `a..h` excluded,
`A..H` included); a clause outputs 1 iff every included literal is true;
half the clauses vote positive, half negative; the readout is the R0.1
counter over clause outputs. Feedback (Type I / II) is the automaton
family's own: ±1 steps with probabilities (s−1)/s and 1/s, encoded as
**step-vs-skip rule weights** π/(1−π) : 1. The fabric approximation of
the TM's margin-based feedback probability is "always when wrong, with
probability Q=0.1 when right".

Two editions, one lesson:
- **Edition 1**: feedback rules anchored on automata, reading the
  clause output, the literal and the neuron's marker at clause-specific
  offsets → 23,765 rules, ~600 events/s (rules × C, dry-runs × C²).
  Killed after 11 minutes.
- **Edition 2 (translation-invariant)**: typing writes each bit's
  literal values into every clause's own literal row; the teacher plants
  one *feedback head* per clause whose glyph encodes (type, right/wrong)
  and, after reading the clause output on its first step, walks east
  over the automata applying the step/skip pair at fixed offsets
  (−2,0)/(−1,0). Write-once for free (the head passes once), no phase-bit
  alphabet, no per-automaton clear. → **731 rules for C=8, 851 for C=16,
  independent of C; 12k events/s (C=8), 6.5k (C=16).**

Rule of thumb earned: **a rule family must read at offsets that do not
depend on which copy of the structure it serves**; replicate the data
(the literal rows) rather than the rules. Equivalent to weight sharing.

Results (6000 samples, accuracy over the last 1500, 3 seeds, 8 inputs,
`sweep-tm2.txt`; protocol verified per sample — see the bug below):

| task | C=8, S=4 | C=8, S=2 | C=16, S=4 | C=16, S=2 | model (C=8/16, S=4) |
|---|---|---|---|---|---|
| XOR (2 relevant, 6 irrelevant) | 0.79–0.85 | 0.87–0.92 | 0.85–0.97 | **0.96–0.99** | 0.74–0.87 / — |
| AND | 0.95 | — | — | — | — |
| majority-of-8 | 0.78–0.79 | — | — | — | 0.85 (C=16) |
| parity-3 | — | — | 0.51–0.55 (pre-fix run) | — | 0.53–0.60 (C=16); 0.74–0.77 (C=64, 20k) |

A C=16, S=2 learning curve (windows of 1500): 0.81 → 0.92 → 0.93 → 0.96.
Events per sample ≈ 200 (C=8) / 360 (C=16); **15–33k events/s** on one
core, so a 6000-sample run is 40–150 s. Undecided readouts 1–7 %.

### The bug the harness check now guards against

The first edition of the walking head used the wildcard trigger `?`, so
heads also moved on typing, evaluation and clear events — and *stole*
them: a typing event that advances a head instead of the typing head
loses that bit for good (one byte, one event). Because the build rule
planted no typing head, sample 1 had empty literal rows, its heads
stalled, and from then on stalled heads accumulated, stole events, and
duplicated typing heads. Symptom: a teacher phase of 320 events applying
17. Diagnosis: the `zahradnice-check why` tool on a dump (it listed the
stuck heads as matching) plus per-phase apply counts from the trace.
Fix: heads move only on their own trigger `f`; the build plants the
first typing head; the harness asserts one marking and one head-plant
per sample. Lesson for the family: **a wildcard-trigger rule is a
process that runs in every phase**; phases must be disjoint rule sets
or a phase must be able to finish before the next begins.

## What this says about the backlog

- Tier 0 done and faithful. The neuron is a counter, not a mass-action
  unit — `00-foundations.md` §2 should be amended.
- Tier 1/2: the first depth that works is **Tsetlin-shaped**: clauses as
  conjunctions (a rule body *is* a conjunction), automata as the tokens
  of the bandit chapter, feedback as competing rule weights, a 1-bit
  bus. R3.1 (sign-backprop) is demoted until a rule that bootstraps
  exists in the model; the model is the gate for every future rung.
- Performance rule: translation invariance (data replication over rule
  replication). The engine's rule index rewards it; the GPU sibling
  requires it.
- Native cost ledger: perceptron 5k generated rules (state × input ×
  magnitude), Tsetlin fabric 731 rules for any C, ~200 events/sample.

## Next

1. Parity-3 with C=64 (model says ~75 % at 20k samples) — cost is
   linear in C events, constant in rules.
2. Structural plasticity on the Tsetlin fabric: re-roll clauses that
   never match / never vote (the model's re-roll trick, R4.1 flavour).
3. Convolutional clauses (a clause reads a 3×3 window at every
   position = the same rule at every anchor, which the engine gives for
   free) → 8×8 bitmaps, then the GPU sibling.
4. Contextual bandit / delayed reward on the same harness (R0.3, R2.1).

## Sensitivity probe (C=8, XOR, 6000 samples, 2 seeds; untuned baseline S=4, Q=0.1 gave 0.79–0.82)

| variant | accuracy |
|---|---|
| Q=0 (feedback only when wrong) | 0.75, 0.89 |
| Q=0.3 | 0.76, 0.76 |
| **S=2** (greedier literal inclusion) | **0.89, 0.92** (pre-fix) |
| S=8 | 0.65, 0.77 |

S is the lever: at S=2 the 8-clause fabric matches the 16-clause one at
S=4; the model predicts 0.96–0.98 for C=16, S=2 (fabric runs below).
Parity-3 does not benefit from S=2 in the model (0.49–0.51) — it needs
clauses, not greed.

## Sibling validation (session 2)

`sibling/torchfab.py` runs the same cfg with the engine's semantics
(one weighted (cell, rule) draw per replica per event); its parser is
checked against `zahradnice-check explain` (60/60 rules). On the C=8,
S=4 fabric, XOR, 1500 samples: 32 torch replicas give last-quarter
accuracy 0.739 [0.587–0.851]; zahradnice on 4 seeds gives 0.736
[0.584–0.856]; the six windowed means agree to ±0.01 throughout
(`sibling/validate-tm8.txt`). CPU throughput 5.2k events/s across the
32 replicas (≈6 ms per step of Python overhead), so the sibling is a
replica machine for the CUDA box, not a single-run accelerator.

## Train/test discipline and the capacity knob (session 2)

Until here every run sampled the whole 8-bit input space with
replacement (256 inputs, ~23 visits each in 6000 samples), so "accuracy"
mixed memorisation with generalisation. Added: a **silent teacher**
(triggers `P`/`N` mark and score the readout but plant no feedback
heads), a **holdout split** of the input space (`--holdout 0.5`: 128
inputs never trained on; `--test-every 4`: every fourth sample is drawn
from them and scored silently), and a **random-labels task** (`rand`: a
seeded random labelling of all 256 inputs — the memorisation ceiling
test, Zhang et al. 2017 in miniature). C=16, 6000 samples, two seeds
(`sweep-holdout.txt`):

| task | S | train (last quarter) | **test, unseen inputs** |
|---|---|---|---|
| XOR | 2 | 0.98, 0.97 | **0.98, 0.96** |
| XOR | 8 | 0.77, 0.82 | 0.77, 0.76 |
| XOR | 32 | 0.61, 0.59 | 0.51, 0.53 |
| threshold fn | 2 | 0.89, 0.86 | 0.80, 0.81 |
| threshold fn | 8 | 0.90, 0.87 | 0.76, 0.78 |
| random labels | 2 / 8 / 32 | 0.56 / 0.60 / 0.55 | 0.49 / 0.49 / 0.49 |

Reading: at S=2 the XOR fabric generalises to inputs it never saw with
no gap at all — its clauses are the two-literal rules decoded in
`learned-xor-C16-S2-s2.screen`, which cover unseen inputs exactly like
seen ones. Large S makes clauses near-minterms: with 16 of them the
function is no longer covered (train falls to 0.6) and unseen inputs
drop to chance — the memorisation regime, entered before the capacity
to memorise exists. Threshold functions with weights ±1/±2 are not
small DNFs, so 16 clauses approximate them with a ~0.1 gap. Random
labels are at chance on unseen inputs by construction and at 0.55–0.60
on seen ones: 16 clauses cannot memorise 64 positive minterms.
**S is the capacity-versus-generalisation dial; C is the capacity.**
The C=64 random-label runs (S=8, S=32, 4000 samples) are the capacity
test proper — `sweep-holdout-c64.txt`.

Parity-3, C=64, S=4, 20 000 samples, full-space protocol: 0.766 and
0.693 (model predicted 0.74–0.77); 1370 events per sample, 6.1k
events/s, 75 minutes per run — the line's first scale-limited result.
