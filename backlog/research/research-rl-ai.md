# Zahradnice — Research & RL/AI Backlog

> Consolidated notes from exploratory design conversations (Aug 2025 – Jun 2026).
> Intended to live in the backlog directory and be referenced by Claude Code.
> **Nothing here is a commitment.** Each item is tagged with an honest status so
> that ideas can be told apart from things that actually run.

**Status tags**
- `[LIVE]` — exists in the engine today
- `[NEAR]` — small, well-understood step from what exists
- `[DESIGN]` — worked out on paper, not built
- `[SPEC]` — speculative, interesting, unproven
- `[PARKED]` — deliberately deferred, with a reason

---

## 0. Why Zahradnice is an unusual substrate

Three properties, all of which fall out of the existing design rather than being
bolted on:

1. **Reward is native.** Rules already carry a `<score>` field. Reward is a side
   effect of a rewriting step, not an external evaluation function bolted onto a
   simulator. Reward is therefore *local, spatial, and compositional* — it is
   emitted where and when a rule fires.
2. **No global clock.** Rule application is asynchronous and weighted-random.
   This is not "a deterministic CA plus noise" — the non-determinism is part of
   the semantics. A correct Zahradnice program must be correct *for every legal
   application order*.
3. **Grammar-level expressiveness.** Type-0 rewriting power with spatial context
   means the environment's "physics" is itself a first-class, editable,
   inspectable artifact — a text file, not compiled code.

The consequence: an agent inside Zahradnice can be made of *the same stuff as the
environment*. That is the through-line of everything below.

---

## 1. Weights are semantics, not perturbation

`[LIVE]` — the most important conceptual point, and the easiest to get wrong.

In most CA/RL work, stochasticity is added to a deterministic system to study
robustness. In Zahradnice the weighted, unordered rule selection *is* the
execution model. There is no underlying deterministic trace being perturbed.

**Practical consequence for program authors:** a program is only correct if it is
correct under all interleavings the weights admit. "It works with seed 42" is not
a correctness argument. This is closer to writing lock-free concurrent code than
to writing a CA rule table.

**Consequence for theory:** classical period analysis does not transfer. On a
finite `K^(w·h)` state space a deterministic system must cycle with period
≤ `K^(w·h) − 1`. Under genuine non-determinism a state can have many successors,
so a trajectory can revisit states with different futures; trajectory length
before *behavioural* repetition is effectively unbounded. This places the system
outside the standard async-CA equivalence results (Nehaniv 2004 shows async
networks can *emulate* synchronous ones — Zahradnice is interesting precisely
where it is *not* an emulation).

---

## 2. Theoretical program

### 2.1 Convergence classification `[NEAR]`
Fatès classifies async CA convergence as logarithmic / linear / quadratic /
exponential / non-converging. **Open question: which class(es) do Zahradnice
programs fall into, and does the answer depend on weight ratios?**

Minimal experiment (cheap, entirely in existing syntax):

```
#threads 1
#grid 8 8
^Acc

# 2-symbol system with adjustable non-determinism
=ATAB 0 3   # A→B (weight 3)
=ATAA 0 1   # A→A (weight 1)
=BTBA 0 1   # B→A
```

Sweep the weight ratio, measure steps-to-first-repetition over many seeds, plot
the distribution. Requires only the existing `--seed` CLI parameter.

### 2.2 Phase transitions `[DESIGN]`
Blok & Bergersen found a critical synchrony rate α_c ≈ 0.911 for async Game of
Life (directed percolation universality class in 2+1D). Zahradnice's analogue of
α is not a synchrony rate but the `#threads` count combined with the weight
distribution. **Open question: is there a critical parallelism/weight ratio at
which the async Life variant changes qualitative regime?** Phase-transition-like
behaviour has already been observed informally in the working Life
implementation — worth pinning down with numbers.

### 2.3 Framing the formalism `[SPEC]`
Standard grammar hierarchies fit awkwardly: fixed topology, replacement rather
than insertion/deletion, spatial neighbourhood constraints. Candidate framings
floated: *spatial replacement grammars*, *grid-constrained rewriting systems*,
*asynchronous spatial rewriting*. No formalisation attempted; deliberately.

### 2.4 Expressiveness `[NEAR]`
What CA can be simulated, at what overhead? Already known: traditional CA need
multiple grammar steps per CA step (e.g. clockwise neighbourhood scanning using
grid symbols as counters). The atomic-vs-multi-step neighbourhood counting
trade-off has been explored in the Life implementation and is the concrete data
point to generalise from.

---

## 3. RL: a four-level ladder

Deliberately ordered by increasing weirdness. Each level is worth doing on its
own; each is a prerequisite for the next.

### Level 0 — External agent through key triggers `[NEAR]`

The engine already distinguishes automatic `B/M/T` time-step triggers from
key-press triggers. Anything driving keys — human, script, policy network — is an
agent. Reward comes free from rule scores.

**Canonical first experiment: Conway's Life steering with a cursor.**

```
^Ccc                # cursor at centre

=CuC~               # move up
=CdC~               # move down
=ClC~               # move left
=CrC~               # move right

=Cf~A~ -1           # flip empty→alive at cursor, intervention penalty
=CfAf~ -1           # flip alive→empty at cursor, intervention penalty

# Life rules carry the objective directly:
#   birth   +1
#   death   -1
#   survive  0
```

Why this is the right first target:
- No external population counter needed — the objective is expressed *in the
  rules*, which is the whole design philosophy.
- The cursor makes it a genuine sequential-decision problem (move / act / wait),
  with spatial attention as an explicit, learnable thing.
- It is control of a chaotic system under an intervention budget — a real RL
  problem, not a toy.

**What's missing to actually run it:** see §6.

### Level 1 — Embodied agent as a grid symbol `[DESIGN]`

The agent stops being an external cursor and becomes a non-terminal living in the
grid, perceiving only its own context neighbourhood. Movement is just rewriting —
the agent is wherever its symbol is.

The asymmetry that makes this attractive:
- **Black box for the agent** — local neighbourhood only, no global state, no
  broadcast channel. It does not know the laws of physics it lives under.
- **Glass box for the observer** — full grammar and full derivation available for
  analysis.

This mirrors biology and makes coordination results meaningful rather than
artefacts of privileged information.

### Level 2 — Agent *as a subset of the ruleset* `[DESIGN]`

The formalisation that came out of the multi-agent discussion:

```
R_total = R_env ∪ R_1 ∪ R_2 ∪ … ∪ R_n
```

Each agent `A_i` is a rule portfolio `R_i` plus a spatial extent `P_i`. A rule
`r ∈ R_i` is applicable when the normal Zahradnice conditions hold **and** its
LHS position intersects `P_i` (or a looser zone of influence). Agents may modify
`R_i`; they may never touch `R_env`.

**Safety constraints** — the "agents must not be able to repeal physics" problem.
Four complementary restriction families, all expressible as static checks on
candidate rules:

| Constraint | Mechanism | Maps to |
|---|---|---|
| Spatial scope | max LHS/RHS extent (e.g. radius ≤ 3) | rule body geometry |
| Symbol partitioning | agents may only write into an agent-owned alphabet | non-terminal char sets |
| Conservation laws | rule must preserve counts of protected symbols | static analysis of body |
| Layer separation | agents confined to their own z-order layers | `<z-order-char>` (already in the language) |
| Weight bounds | clamp agent-settable weights | `<weight>` field |

The z-order and symbol-partition constraints are nearly free — the language
already has the machinery.

**Reward structure** — the preferred design is a shared global reward `G_t`
(promoting cooperation, and making self-replication *consequential* rather than
free) blended with a local per-agent term `L_i,t` as the individual improvement
signal:

```
r_i,t = α · G_t + β · L_i,t
```

- α > β → cooperation dominates
- α < β → tragedy of the commons; agents defect

A sharper variant replaces the global term with a *counterfactual* one: what
would `G_t` have been had agent *i* not acted? That rewards causal contribution
rather than mere presence, and directly addresses credit assignment. It is
expensive (requires counterfactual rollouts) and is a later refinement.

**Replication → population.** If an agent's core symbol can be replicated by its
own rules, clones share an identical ruleset. This is not a bug — it is best read
as a *single distributed agent* with many bodies, or as a population subject to
selection. Population limits need an explicit mechanism (energy budget, score
cost per replication) or the grid saturates.

### Level 3 — Learning without an external optimiser `[SPEC]`

The goal is *emergent* learning, not imposed learning. Three routes, in
increasing order of satisfaction and difficulty:

1. **External RL loop.** Zahradnice is just the simulator; a neural net observes
   and acts. Clean, standard, and unsatisfying — the interesting part happens
   outside the system.
2. **Stigmergic adaptation.** Agents deposit marks in the derivation; future
   behaviour responds to past traces. Memory is environmental, not internal.
   Powerful (this is ant colony optimisation), but not learning in the RL sense.
   **Cheapest genuinely interesting thing to try.**
3. **Mutable weights, fixed structure.** Rule *structure* is immutable; rule
   *weights* adapt from score feedback. The policy — the distribution over
   applicable rules — shifts. Directly analogous to a fixed neural architecture
   with learned weights, or a fixed reflex arc with modulated synaptic strength.

Route 3 has an elegant closure property: **the weight update can itself be a
rule.** A core meta-rule reinforcing the last-fired rule on positive score turns
learning into more physics. Weight registers become symbols in the derivation.
No external optimiser anywhere in the loop.

This is the single highest-value speculative item in this document. It preserves
closure, requires no reflective layer, and is far less ambitious than §4.

---

## 4. The reflective layer `[PARKED]`

**The idea:** treat program files as derivations too. Grammar ≈ code, derivation
≈ data — so let rules operate on rules. Mutation operators live in `R_env` and
rewrite `R_i`.

**Why it is attractive:**
- Closure: state = (grid, grammars); rules act on state; no external machinery.
- Uniformity: everything is symbol rewriting, at two scales.
- Precedent: Lisp reflection, self-modifying TMs, Tierra.
- **The robust parser is the killer feature.** Invalid rules don't crash — they
  simply never match and contribute nothing. Broken mutants are *introns*. The
  grammar file becomes a genome with coding and non-coding regions, and mutation
  degrades gracefully instead of exploding.

**Why it is parked:**
- Two matching domains: the grid has spatial adjacency, grammar files have
  line/text structure. Meta-rules need different matching semantics — uniformity
  breaks at the implementation level.
- Recursion trap: if meta-rules live in grammar files, can they rewrite
  themselves? A protected kernel is needed, which costs the elegance.
- Zahradnice's rule syntax is rich. Encoding it spatially needs either a
  simplified Baba-like agent grammar or a hidden-layer/subcell representation.

**Designed mutation operators** (structured variation, *not* random noise —
the environment author defines the chemistry):

```
=WeightMutate…    # ±1 to a rule weight
=TriggerSwap…     # change trigger char within an allowed set
=ContextFlip…     # swap one context character
=RuleDuplicate…   # copy a rule block with a small modification
=RuleDisable…     # comment a rule out (# prefix)
```

Designer-controlled knobs: mutation granularity, mutation rate (via meta-rule
weights), protected regions (no matching LHS), and the allowed variation space.
**Evolvability becomes a first-class tunable parameter** — one environment allows
only weight drift, another permits structural change, and the fitness-landscape
topology follows from that choice.

**Second-order evolvability** (the real prize, and properly speculative): agents
cannot rewrite the mutation operators, but they can influence *when* those
operators fire. Agent deposits a stress symbol when its score is low; a core
meta-rule raises mutation rate near stress symbols. The biological precedent is
exact — *E. coli* SOS response, where high-fidelity polymerase is swapped for
error-prone Pol IV/Pol V under starvation or DNA damage, raising mutation rates
100–1000×. The genes are fixed; activation is behavioural.

```
Behaviour (forage/starve)
  → cellular state (stress signals)
  → polymerase selection (meta-rule activation)
  → mutation rate
  → new variants
  → behaviour changes
```

Even without full reflection, agents can influence evolvability *architecturally*:
avoiding or presenting mutable patterns (conservative vs exploratory genomes),
keeping redundant copies of critical rules, or favouring modular rule
organisation that limits cascading damage.

**If this is ever resumed, the starting question is:** *what is the minimal agent
grammar syntax that is both evolvable and expressive?* Baba Is You is the
existence proof that rules-as-environment is designable and playable — tiny
vocabulary, compositional `NOUN IS PROPERTY` syntax, immediate visual feedback,
and invalid sentences that harmlessly do nothing. It has a central clock;
Zahradnice would not, which is the interesting difference, not a problem.

---

## 5. Coding AI-like behaviour directly in the grammar `[SPEC]`

Separate from RL: use the grammar as a substrate for cognitive-architecture
primitives, with no learning at all.

- **Attention** — a symbol that migrates toward high-activity regions and
  amplifies rule application in its neighbourhood.
- **Working memory** — transient state parked in nearby cells; **long-term
  memory** — stable still-life patterns; **associative recall** — rules that fire
  on partial pattern matches.
- **Pattern recognition** — the context-matching machinery (`&`, `?`, `*`, `$`,
  `#`, `~`) is already a template matcher.
- **Swarm primitives** — pheromone deposition and decay are two-rule idioms.

Value here is demonstrative rather than scientific: it shows the language is
expressive enough to make "intelligence-shaped" behaviour legible.

---

## 6. Mapping to the actual codebase

### Already there (per `GRAMMAR.md`)

| Capability | Feature | Notes |
|---|---|---|
| Reward channel | `<score>` per rule | reward is spatial and compositional |
| Stochastic policy | `<weight>` per rule | intrinsic semantics, see §1 |
| Action interface | trigger char in rule header | any key = a discrete action |
| Multi-scale time | `B` / `M` / `T` + `#timing` | 500/50/0 ms defaults |
| Sync/async knob | `#threads` | 1 = one rule/step; N = up to N non-conflicting |
| Topology | `#grid`, toroidal wrapping | finite state space for analysis |
| Reproducibility | `--seed` CLI parameter | replay for trajectory studies |
| Agent/env separation | `<z-order-char>` layers | free safety constraint (§3, Level 2) |
| Episode reset | bare `^` (clear screen) | plus `x` reload |
| Curriculum / level flow | `#program`, `return`, call stack | derivation state flows between programs |
| Local memory | `$` context char | used in `flowers.cfg`; undocumented |
| Parallelism telemetry | `Steps: X (Y%)` status line | already a usable metric |

The `#program` mechanism is quietly the most underrated asset here: it gives
episode structure, curriculum progression, and compositional environments *with
preserved derivation state*, which is exactly what a level-based RL benchmark
needs.

### Gaps to close before any RL work is real

Ordered by how much they block Level 0.

1. **Headless / batch mode.** Run without a TTY, fixed step budget, exit code.
   Blocks every experiment in this document, including the pure-theory ones
   in §2.
2. **Programmatic action input.** Keys currently come from the terminal. Need
   stdin/pipe/socket injection so a policy can act. Small change, unblocks Level 0.
3. **Observation export.** Dump the cell buffer (chars + colors + z-order) per
   step in a machine-readable form. This is the *same artifact* the Bevy renderer
   consumes — so specifying it once serves both the RL work and the
   engine-divergence problem (§7).
4. **Score readout.** Expose the running score outside the status line.
5. **Trajectory logging.** Which rule fired where, per step. Needed for credit
   assignment, and for the period/convergence statistics in §2.1.
6. **Batch seed sweep harness.** A script, not an engine change.
7. *(Level 2+)* **Runtime rule mutation.** Load/modify rules in-memory with
   ruleset versioning, checkpoint/serialise only when needed. Explicitly *not*
   file-rewriting.

Items 1–3 are the whole critical path. They are also independently useful.

### Documentation gaps in `GRAMMAR.md`
Its own TODO lists: `!` and `%` in rule bodies, local memory (`flowers.cfg`), and
`#` as implicit screen boundary. Local memory in particular matters for agent
design — an agent with one memory slot is a meaningfully different thing from a
purely reactive one. Note that the theory work in §2 was explicitly planned to
*start without* memory, so this is a Level-1+ concern.

---

## 7. Engine divergence (context, not research)

Two implementations exist and have drifted: the C/C++ canonical engine
(`popoja/zahradnice`) and the Bevy/Rust remake (`popojan/zero`). Sharing code
across the language boundary is rarely worth it for a hobby project; the right
seam is a **shared contract** — `GRAMMAR.md` as the language spec both target,
plus a stable description of the cell buffer the renderer consumes.

Cheap divergence detection: a small corpus of sample programs run through both
engines with a fixed seed, compared frame-by-frame on the resulting grid.

This overlaps directly with gap #3 above — the observation-export format *is* the
cell buffer contract. Building it once pays for both.

If a Steam release ever becomes concrete, the canonical-engine question resolves
itself at that moment (terminal C/C++ is the better authoring environment; Bevy
is the better distribution artifact). Until then, loose coupling through the spec
is what buys the option to defer.

---

## 8. Standing backlog items

- **Gravity as a complex sample program.** Masses emit "graviton" symbols in all
  directions; emission count scales with mass; gravitons decay with distance;
  bodies move against the gradient of the flux they encounter. Directional
  gravitons (8 symbol variants) carry the direction information. The finite
  propagation speed is *more* physically faithful than instantaneous Newtonian
  gravity — and the toroidal topology produces genuinely strange orbital
  mechanics, including a field interfering with itself the long way round. Good
  stress test for long-range spatial coordination.
- **Genetic CA.** Cells carry inheritable "genes" (colour/HSV, modified
  birth-survival thresholds, or timing preferences in the async setting). Open
  design question: do *surviving* cells retain genes (stability) or re-inherit
  (rapid mixing)? Birth from three parents invites averaging, random selection,
  or crossover. Expected phenomena: genetic waves, lineage arms races, speciation
  in isolated regions.
- **L-systems as complementary paradigm.** L-systems model *individual plant
  development* (parallel rewriting of a 1D string, unfolded into space by turtle
  interpretation); Zahradnice models *garden ecology* (native 2D, fixed topology,
  replacement semantics, asynchronous). A hybrid developmental-ecological model —
  L-system-grown organisms interacting in a Zahradnice space — is the long-term
  theoretical tease. The framing it suggests is worth keeping: not "another CA
  variant" but a **spatial ecological programming language**, where programming
  is cultivation rather than engineering. Which is what the name says.

---

## 9. Suggested order of work

Nothing here needs to happen in a hurry, but this is the dependency order:

1. Headless mode + observation export + score readout (gaps 1–4). Unblocks
   everything, and doubles as the engine-divergence harness.
2. §2.1 convergence study — pure theory, no agents, tiny grids, existing syntax.
3. Level 0 Conway steering with an external policy. First real RL result.
4. Stigmergic agents (Level 3 route 2) — cheapest genuinely emergent behaviour.
5. Level 1 embodied agent, local perception only.
6. Rule-as-meta-rule weight adaptation (Level 3 route 3) — the closure result.
7. Level 2 multi-agent, with z-order and symbol-partition safety constraints.
8. Reflective layer — only if 1–7 have made it feel necessary.

---

## References

- Fatès, N. (2014/2017) — *Asynchronous cellular automata*: survey and tutorial;
  convergence classes.
- Blok, H. & Bergersen, B. (1999) — phase transitions in async Game of Life;
  α_c ≈ 0.911, directed percolation in 2+1D.
- Nehaniv, C. (2004) — *Asynchronous Automata Networks Can Emulate Any
  Synchronous Automata Network*; the equivalence result Zahradnice departs from.
- Lee, J. et al. (2004) — *Asynchronous game of life*; 8-state async equivalent.
- Lindenmayer, A. (1968) — L-systems.
- Ray, T. — Tierra (self-replicating code, digital evolution).
- Baba Is You — design proof that rules-as-environment is playable.
