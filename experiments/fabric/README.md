# fabric — learning inside the rewriting substrate

Status: research line, session 1–2 (2026-09-12). Branch `fabric`. Design
docs in `backlog/fabric/`, session narrative in `results.md`. This file
is the reader's guide to *what is built and why*, for someone who knows
the substrate and ordinary neural networks but not Tsetlin machines.

## 0. The problem, in the substrate's own terms

A zahradnice program is a set of rewriting rules. A rule fires at a cell
whose glyph matches its anchor, if the neighbourhood matches its LHS
pattern; among all applicable (cell, rule) pairs one is drawn with
probability proportional to the rule's weight, and its RHS is written.
Only glyphs are state. The trigger character of an event (a key in
`--input`) selects which rules are eligible, so **the input stream is a
free global broadcast**: one character reaches every cell at once.

A neural network needs three things the substrate does not obviously
have: a *weight* (a number a rule can act on), a *neuron* (a threshold
over a weighted sum), and *credit assignment* (telling a weight it was
wrong when the error appeared elsewhere). Everything below is one
answer to each, built only from glyphs, rules and the broadcast.

## 1. A weight is a glyph; a neuron is a random walk (`gen_fabric.py`)

**Weight.** A synapse is one cell. Its glyph is a signed small integer
(`.` = 0, `A..H` = +1..+8, `a..h` = −1..−8). A rule that reads the
synapse has the magnitude as its **header weight**, so the sampler sees
the glyph as a rate: the law maps glyph → probability, the glyph *is*
the parameter. Learning rewrites the glyph by ±1.

**Neuron.** A one-shot sampler unit would fire with P = s/(s+u+θ)
(s = mass of active positive synapses, u = active negative, θ = a
constant "refuse" rule). That is far too soft: evidence 5:4 gives
P = 0.53. The built neuron is a **drift-diffusion counter**: its glyph
is a state j ∈ (−K, K); each inference event moves it +1 (mass s) or −1
(mass u+θ); at +K it becomes `Y` (fired), at −K `N` (refused). By the
gambler's-ruin formula

    P(fire) = 1 / (1 + ((u+θ)/s)^K)

— a sigmoid in log-odds with gain K, bought with ~K events per decision
and 2K−1 glyphs. Because the state glyph is the rule's anchor, the
engine's rule index tries only the ~150 rules of the current state per
event; the total rule count (≈5k at K=16) costs nothing at run time.

**Protocol per sample** (all triggers are keys; no timing):

| phase | trigger | what happens |
|---|---|---|
| type | `0`/`1` ×8 | a write head walks the input row and writes `o`/`x` |
| infer | `i` × budget | the counter walks until decided |
| teach | `p` or `n` ×10 | the label. First event marks the neuron `+` (correct, score +1), `-` (missed) or `/` (false alarm); then every active synapse steps once toward the label (perceptron rule), consuming its input `x`→`X` so it cannot step twice |
| clear | `c` ×14 | activities blank, neuron to state 0, head replanted; synapses untouched |

Correctness is *scored*, so the engine's exactly accounted score is the
learning curve, and the trace reconciles synapse populations against
the final screen.

**Results** (8 inputs + bias, 3000 samples, 4 seeds, last quarter):
AND 0.97–0.99, random threshold functions 0.89–0.96, majority-of-8
0.80–0.83, XOR 0.50 (it must fail; one layer). Identical to the same
rule as plain arithmetic (`model_r01.py`) — the model is the control
that told a glyph collision apart from a weak rule.

## 2. Depth that learns: the Tsetlin-shaped fabric (`gen_tm.py`)

### 2.1 What a Tsetlin machine is, for a neural-network reader

A Tsetlin machine (Granmo 2018) is a one-hidden-layer network in which
every hidden unit is an **AND gate over a learnable subset of the input
literals** (each input bit x_i and its negation ¬x_i). Such a unit is
called a *clause*. Half the clauses vote for class 1, half against; the
output is the sign of the vote. There are no real numbers anywhere: each
(clause, literal) pair has a small counter — a *Tsetlin automaton* —
whose state says "include this literal" (upper half) or "exclude it"
(lower half). Learning moves these counters by ±1 with fixed
probabilities, depending on four bits: was the clause's vote wanted,
did the clause match, is the literal true, is it currently included.
That is the whole algorithm, and it is exactly the family of the
substrate's bandit chapter: policy = automaton states, update = ±1 on a
1-bit global signal, no gradient. It is competitive on MNIST (~98 %) and
is the closest published answer to the passage that started this line.

Its two feedback types, in words:

- **Type I** — the clause *should* vote (its class is the true one).
  If it matched: push true literals toward *include* with probability
  (S−1)/S, false ones toward *exclude* with 1/S (so the clause keeps
  matching this kind of sample and grows more specific). If it did not
  match: push everything toward *exclude* with 1/S (become general
  enough to match).
- **Type II** — the clause should *not* vote. If it matched: include
  one currently-excluded literal that is *false* here, with
  probability 1 (the clause will fail on this sample from now on). If
  it did not match: nothing.

### 2.2 The knobs

| knob | meaning | effect |
|---|---|---|
| **C** | number of clauses (hidden AND units); half positive, half negative polarity | capacity and redundancy. XOR needs 2+2 clauses in principle; 8–16 in practice because learning finds them stochastically. Parity-3 needs 8 three-literal clauses; the model wants C≈64 |
| **S** | Granmo's *specificity*: include prob (S−1)/S, exclude prob 1/S. **Not a resolution**: a literal gets included when its frequency among the clause's matches exceeds 1/S | how many literals a clause keeps. Small S = general clauses (few literals): right for XOR among six irrelevant bits (S=2 gave 0.96–0.99). Large S = specific clauses. Roughly, a literal true in ≥ (S−1)/S of the samples a clause sees gets included |
| **N** | automaton states per action (2N states per literal) | inertia against noise in the feedback. N=4 let one XOR run collapse; N=8 and 12 are fine — more never hurt |
| **K** | gain of the readout counter (§1) | sharpness of the vote; K=4/8/16 gave 0.93/0.97/0.98 on XOR — more never hurt, costs events |
| **θ** | base down-mass of the readout | the vote's threshold; θ=1 |
| **Q** | feedback probability when the prediction was *right* (always 1 when wrong) | our stand-in for the TM's margin-based feedback probability (T−v)/2T, which needs the vote as a number; Q=0.1 |
| NIN | input bits | 8 in every experiment so far |

### 2.3 How it is laid out in glyphs

Per clause three rows; the whole thing is one tall screen (`--screen`).

```
row 1    #  _ _ _ _ _ _ _ _  |                   typing head > walks here, writes o/x
row A    t u u t t u t u   u t t u u t u t       literal values: cols 1..8 = x_i, cols 10..17 = ¬x_i
row B  1 h A h h A A h A | h h h h h h h h       clause output (1/0) at col 0; automata a..h excluded, A..H included
row H                                            feedback head row (empty between samples)
  … (A/B/H repeated per clause) …
last   ⡀                                         readout counter at col 0 (state glyph; Y fired / N refused; + - / marker)
```

| phase | trigger | rules do |
|---|---|---|
| type | `0`/`1` ×8 | the head writes the bit into row 1 **and the literal values into every clause's row A** (one tall RHS) |
| evaluate | `i` ×(C+2) | a clause output `1` becomes `0` if some *included* automaton sits under an untrue literal (`u`). One event per failing clause; clauses with no failing literal stay `1` |
| readout | `o` ×budget | the counter walks: +1 per matched positive clause, −1 per matched negative, θ down |
| teach | `p`/`n` ×1 | marks the readout `+`/`-`/`/` and **plants one feedback head per clause** in row H, its glyph encoding (feedback type, right/wrong). Type = f(label, polarity) is decided at generation time per row |
| feedback | `f` ×(19C+5) | each head reads its clause's output on the first step, then walks east over the automata; at each automaton it reads the literal above and applies the Type I/II table as a pair of competing rules, **step** (weight π/(1−π)) versus **skip** (weight 1). The walk makes every automaton update at most once per sample for free |
| clear | `c` ×(C+4) | clause outputs back to `1`, readout to state 0, typing head replanted |
| test | `P`/`N` ×1 instead of `p`/`n` | the *silent teacher*: marks and scores the readout, plants no heads — the sample is evaluated, not learned from. `fabric_run.py --holdout 0.5 --test-every 4` draws every fourth sample from 128 inputs the fabric never trains on |

Probabilities are rule weights: a step with probability π against a
skip of weight 1 needs weight π/(1−π); π = 1 is a large weight with no
skip rule. All randomness is the engine's sampler.

### 2.4 Results (8 inputs, 6000 samples, last 1500, 3 seeds)

| task | C=8, S=4 | C=8, S=2 | C=16, S=4 | C=16, S=2 |
|---|---|---|---|---|
| XOR of bits 1,2 (6 irrelevant) | 0.79–0.85 | 0.87–0.92 | 0.85–0.97 | **0.96–0.99** |
| AND | 0.95 | | | |
| majority-of-8 | 0.78–0.79 | | | |
| parity-3 | model: needs C≈64 (0.74–0.77 at 20k samples); fabric run in progress | | | |

Held out (train on 128 of the 256 inputs, test on the other 128, C=16):
XOR at S=2 scores 0.96–0.98 on **unseen** inputs, no gap; S=32 falls
to chance on unseen inputs; random labels are at chance unseen and
0.55–0.60 seen (16 clauses cannot memorise) — S is the generalisation
dial, C the capacity. Parity-3 with C=64: 0.69–0.77 at 20k samples.

731 rules for C=8, 851 for C=16 — the count does not grow with C.
15–33k events/s on one core; ~200 events per sample at C=8.

### 2.5 Two lessons that shaped the design

**Replicate data, not rules.** The first edition anchored feedback on
the automata and read the clause output, the literal and the readout's
marker at offsets that depended on the clause's row: 23,765 rules,
~600 events/s — rules × C, dry-runs × C². The edition above copies the
literal values into every clause row and carries the feedback in a
walking head, so every rule reads at fixed offsets: 731 rules, 20×
faster. This is weight sharing; the engine's rule index rewards it and
the GPU sibling requires it.

**A wildcard-trigger rule is a process that runs in every phase.** The
heads were first keyed to `?` and stole one-shot events — a typing bit
consumed by a head step is lost, the head never reaches the end of the
row, the next clear plants a second head. Now each process has its own
trigger and the harness asserts one marking and one head plant per
sample. Phases must be disjoint rule sets, or a phase must be able to
finish before the next begins.

### 2.6 Glyph legend

`#` row marker · `_` untyped input · `>` typing head · `o`/`x` input
bit 0/1 · `|` separator · `t`/`u` literal true/untrue · `1`/`0` clause
matched/failed · `a..h` automaton excluded (1..8) · `A..H` included
(9..16) · `{ } ( )` planted feedback head (Type I wrong/right, Type II
wrong/right) · `5 6 7 8 9 : ; <` walking head (type × right/wrong ×
clause output) · Braille U+2830.. readout counter states · `Y`/`N`
fired/refused · `+ - /` correct / missed / false alarm.

## 3. Tools

- `fabric_run.py CFG --task xor --n 6000 --seed 1 --screen 53,20 --phases i:18,o:120,T:1,f:310,c:20` —
  headless driver: generates samples, types them, feeds the phases,
  reads outcomes from the trace, prints windowed accuracy and the final
  screen row of interest. Tasks: `and maj xor par3 thr rand` (`rand` = a seeded random labelling
  of all inputs, the memorisation test). `--holdout F --test-every k`
  gives train/test accuracy separately via the silent teacher.
- `model_r01.py`, `model_r31.py`, `model_tm.py` — the same rules as
  plain arithmetic. Rule of the line: **a rung is built in glyphs only
  after its model learns**, and a glyph result is trusted only when it
  matches its model.
- `sibling/torchfab.py CFG --screen R,C --replicas B --task xor --n N` —
  a replica-parallel engine in torch that runs the *same cfg* with the
  engine's semantics (one weighted draw per replica per event). Its cfg
  parser is checked against `zahradnice-check explain`
  (`--explain-check 60`). CPU: ~5k events/s across 32 replicas (Python
  overhead per step); intended for a CUDA box, where thousands of
  replicas cost the same per step. Validation against zahradnice on
  C=8 S=4 XOR, 1500 samples: windowed means 0.55/0.65/0.68/0.71/0.73/0.74
  (32 replicas) vs 0.53/0.64/0.68/0.70/0.71/0.74 (4 seeds); last-quarter
  mean 0.739 [0.59–0.85] vs 0.736 [0.58–0.86]. Same machine.

## 4. What did not work, and why it is recorded

Sign-backprop through binary counter units (error sign copied back
through the synapse cells, ±1 steps) does not bootstrap even in
arithmetic: with binary units every hidden unit is pushed toward the
same impossible target, and the output weights random-walk around ±1.
The output layer alone learns XOR to 99 % from ideal hidden features, so
the failure is feature discovery. Frozen random hidden units with a
learned readout and re-rolling of unused units reach 0.65–0.73 on
8-input XOR (model). Details in `results.md`.

## 5. Reproduce

```sh
make zahradnice-headless zahradnice-check          # from the repo root
cd experiments/fabric
K=16 OUT=fabric-r01-k16.cfg python3 gen_fabric.py
python3 fabric_run.py fabric-r01-k16.cfg --task and --n 3000 --seed 1 --phases i:300,T:10,c:14
C=16 S=2 OUT="fabric-tm-C=16-S=2.cfg" python3 gen_tm.py
python3 fabric_run.py "fabric-tm-C=16-S=2.cfg" --task xor --n 6000 --seed 1 --screen 53,20 --phases i:18,o:120,T:1,f:310,c:20
python3 sibling/torchfab.py "fabric-tm-C=8-S=4.cfg" --screen 29,20 --replicas 32 --n 1500 --explain-check 60
```

Watch one live: `./zahradnice "experiments/fabric/fabric-tm-C=8-S=4.cfg"`
needs a terminal ≥ 28 rows; press `b`, then type bits and phases by hand.
