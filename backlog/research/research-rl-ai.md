# Zahradnice — Research & RL/AI Backlog

> Consolidated notes from exploratory design conversations (Aug 2025 – Jun 2026).
> Intended to live in the backlog directory and be referenced by Claude Code.
> **Nothing here is a commitment.** Each item is tagged with an honest status so
> that ideas can be told apart from things that actually run.

> **Revision 2 (2026-08-21).** The verbatim web export is preserved as the
> previous commit of this file (branch `research`). This revision fact-checks
> every claim against the codebase — the export was written against a stale
> picture of the engine, predating the May-2026 tooling wave (headless mode,
> trace/replay/stats, `zahradnice-check`, the genlib generator stack). The
> largest corrections: §6's "gaps to close" were mostly closed months ago;
> every inline rule example was rewritten into real, engine-validated syntax
> (the originals would not parse); and the z-order layer no longer exists in
> the language (`backlog/completed/z-order-removal.md`), which changes the
> Level-2 safety story. All corrections are integrated in place.

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
2. **No global clock — with one precision.** Rule application is weighted-random
   over all applicable (rule, site) pairs. The non-determinism is part of the
   semantics, not noise added to a deterministic system. *Precision:* the engine
   does have a global, serial trigger scheduler — the main loop fires one
   trigger per iteration (a `#timing` char or a keypress), and only one timing
   trigger is served per iteration even when several are due
   (GRAMMAR-pitfalls #10). The asynchrony lives entirely in *which site and
   which rule* fire for that trigger, and — in multi-threaded mode — in *how
   many* non-conflicting rules fire per step (`#threads N` applies up to N
   simultaneously, which is a genuine semantic change, not an optimisation).
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

**Practical consequence for experimenters** (new): a seeded single-threaded run
*is* deterministic and bit-for-bit replayable — `--seed` plus `#threads 1`
(or `--trace`, which forces single-threading) gives exact reproducibility, and
`--replay` re-derives any recorded run. Multi-threaded runs are not
schedule-deterministic even with a fixed seed. So the experimental methodology
is: explore multi-threaded, measure single-threaded.

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

Minimal experiment — *the original sketch here used wrong syntax and misread
`#grid`; the version below parses and runs* (validated headless 2026-08-21):

```
#! A/B convergence toy
#threads 1
#timing T 0

^Acc

==ATB78   0 3
@@@
==ATA78   0 1
@@@
==BTA78   0 1
@@@
```

Corrections baked in:
- Rule headers are positional: `=`, sound (`=` = silence), LHS, trigger, RHS,
  fore, back — and the `<score> <weight>` tail must start at **column 10**, so
  short headers need padding (`==ATB78␣␣␣0 3`). A single space fails silently
  (GRAMMAR-pitfalls #20). Verify with `zahradnice-check explain CFG --line N`.
- Every rule needs a body (`@@@` for in-place replacement).
- `#grid W H` does **not** set the board size — it sets the alignment
  granularity of toroidal wrapping (default 1/1). Board size comes from the
  terminal, or from `--screen R,C` in headless mode (default 24×80). An 8×8
  arena is `--screen 8,8`; row 0 is reserved for the status line.

Run protocol:

```sh
./zahradnice-headless conv-ab.cfg --seed $s --screen 8,8 \
    --input "$(printf 'T%.0s' {1..1000})" --trace run$s.trace >/dev/null
```

The v2 trace logs, per applied rule: step, cumulative score, trigger source,
trigger, LHS char, position (r,c), and the rule head — enough to reconstruct
the full trajectory (or `--replay` it). What it does *not* log is a per-step
screen-state hash, so "steps to first state repetition" currently means
reconstructing states via replay. A per-line state hash in the trace would
reduce that to a `sort | uniq`-style script — see gap G4 in §6.

Sweep the weight ratio, measure steps-to-first-repetition over many seeds, plot
the distribution.

### 2.2 Phase transitions `[DESIGN → first data]`

> **Update 2026-08-21:** first measurement done — the contact-process
> sweep (`experiments/convergence/results.md`, Round 2) shows the
> effective critical ratio shifting upward with `#threads`: survival at
> λ = 0.4375 drops 14% → 0% as N goes 1 → 8, with order-of-magnitude
> longer near-critical transients. The engine's batch parallelism is a
> real synchrony knob with measurable critical behaviour.
Blok & Bergersen found a critical synchrony rate α_c ≈ 0.911 for async Game of
Life (directed percolation universality class in 2+1D). Zahradnice's analogue of
α is not a synchrony rate but the `#threads` count combined with the weight
distribution — `#threads 1` is the fully-async extreme; large N approaches
(but never reaches) synchronous update, bounded by conflict detection. **Open
question: is there a critical parallelism/weight ratio at which the async Life
variant changes qualitative regime?** Phase-transition-like behaviour has
already been observed informally in the working Life implementation
(`programs/life.cfg`) — worth pinning down with numbers. The `{parallel}`
status-line telemetry (fraction of steps that applied >1 rule) is a free order
parameter candidate.

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

### Level 0 — External agent through key triggers `[NEAR — closer than the export assumed]`

The engine already distinguishes automatic timing triggers from key-press
triggers, and — since May 2026 — a byte stream can drive both uniformly:
`--headless --input STR` (or `@PATH`, or stdin) feeds one trigger per byte, and
the run reports `final score=N` on stderr plus a final `--dump-screen` frame.
Anything producing that byte stream — human, script, policy network — is an
agent. Reward comes free from rule scores.

**Canonical first experiment: Conway's Life steering with a cursor.**

The original sketch's rules would not parse. The corrected, engine-validated
cursor (movement + toggle with intervention penalty; run 2026-08-21, score
telemetry confirmed):

```
#! cursor toy
#threads 1
^Ccc

# movement: rep `~` erases the old cell, the literal C is written at the
# offset cell. Both @-anchors overlay the *matched* position; writes are
# relative to the third @.
==Cd~78
@@@C
==Ca~78
@@C@
==Cw~78
@
@
C
@
==Cs~78
@
@
@
C

# toggle the cell right of the cursor: `&` matches header ctx (field 6),
# RHS `&` writes ctxrep (field 7); −1 intervention penalty per flip
==CfC78~o -1
@&@@&
==CfC78o~ -1
@&@@&
```

Design point the sketch missed: **the cursor occupies a grid cell**, so a naive
cursor destroys the pattern it steers. The engine's idiom for "overlay without
destroying" is `#transient <chars>` plus `$` memory-restore (GRAMMAR-pitfalls
#5, #18): declare `#transient C`, move with `rep = $` so the vacated cell is
restored from local memory. The toy above sidesteps this by acting on the
neighbour cell; a real Life-steering cfg should use the transient idiom.

Why this is the right first target:
- No external population counter needed — the objective is expressed *in the
  rules* (birth +1, death −1, survive 0), which is the whole design philosophy.
- The cursor makes it a genuine sequential-decision problem (move / act / wait),
  with spatial attention as an explicit, learnable thing.
- It is control of a chaotic system under an intervention budget — a real RL
  problem, not a toy.
- `programs/life.cfg` already exists; the cursor is an include away.

**What's missing to actually run it:** far less than the export claimed. Open-
loop episodes (fixed action string → final score) run today with zero engine
work. Closed-loop (observe → act) has an interim path that also needs zero
engine work: because seeded single-threaded runs are deterministic, a policy
can re-run the episode prefix plus one candidate action and read the score/
frame — O(T²) per episode, fine for short episodes and greedy/bandit policies.
The one real engine gap is a streaming step mode; see §6, gap G1.

### Level 1 — Embodied agent as a grid symbol `[DESIGN]`

The agent stops being an external cursor and becomes a non-terminal living in the
grid, perceiving only its own context neighbourhood. Movement is just rewriting —
the agent is wherever its symbol is.

The asymmetry that makes this attractive:
- **Black box for the agent** — local neighbourhood only, no global state, no
  broadcast channel. It does not know the laws of physics it lives under.
- **Glass box for the observer** — full grammar and full derivation available for
  analysis (and, since May 2026, full per-step traces, per-rule stats, memory
  snapshots and watched-cell logs — the glass box has instruments now).

This mirrors biology and makes coordination results meaningful rather than
artefacts of privileged information.

An embodied agent also gets one more sense than the export knew about: the `$`
local-memory mechanism (documented in GRAMMAR.v2.md §Local memory) gives each
cell a saved struct, and `#transient` controls what is remembered. An agent with
a per-cell memory slot is a meaningfully different creature from a purely
reactive one.

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
*Corrected:* the export listed z-order layer separation as a free constraint;
**z-order was removed from the language** (rule headers are 8 field chars, no
layer char — see `backlog/completed/z-order-removal.md`). The layering role was
absorbed by `#transient` + memory-restore, which is an overlay mechanism, not an
access-control boundary. The remaining families, all expressible as static
checks on candidate rules:

| Constraint | Mechanism | Maps to |
|---|---|---|
| Spatial scope | max LHS/RHS extent (e.g. radius ≤ 3) | rule body geometry — `zahradnice-check explain` already decodes exactly this |
| Symbol partitioning | agents may only write into an agent-owned alphabet | non-terminal char sets; the strongest free constraint |
| Conservation laws | rule must preserve counts of protected symbols | static analysis of body — natural `zahradnice-check` extension |
| Weight bounds | clamp agent-settable weights | `<weight>` field |

Symbol partitioning does most of the work z-order was supposed to do, and the
static-check infrastructure to enforce these now exists as a codebase seam
(`src/check/check.cpp` links the real parser, so checks see rules exactly as
the engine does).

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
expensive (requires counterfactual rollouts) — though less so than the export
assumed: deterministic seeded replay means a counterfactual is "replay the
trace with agent *i*'s rules disabled", which the existing trace/replay
machinery nearly supports. Still a later refinement.

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
   **Cheapest genuinely interesting thing to try** — and partially prototyped
   already: `programs/archived/ants.cfg` exists (parked, not polished).
3. **Mutable weights, fixed structure.** Rule *structure* is immutable; rule
   *weights* adapt from score feedback. The policy — the distribution over
   applicable rules — shifts. Directly analogous to a fixed neural architecture
   with learned weights, or a fixed reflex arc with modulated synaptic strength.

Route 3 has an elegant closure property: **the weight update can itself be a
rule.** A core meta-rule reinforcing the last-fired rule on positive score turns
learning into more physics. Weight registers become symbols in the derivation.
No external optimiser anywhere in the loop.

This is the single highest-value speculative item in this document. It preserves
closure, requires no reflective layer, and is far less ambitious than §4. Note
it does require engine work — runtime-mutable weights (§6 gap G3); today weights
are fixed at parse time.

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
  degrades gracefully instead of exploding. (With one sharp edge discovered
  since: stray non-rule lines are silently appended to the previous rule's body
  and kill it — GRAMMAR-pitfalls #19. "Graceful degradation" is real but has
  action-at-a-distance failure modes; a mutation chemistry would need to respect
  file hygiene.)

**Why it is parked:**
- Two matching domains: the grid has spatial adjacency, grammar files have
  line/text structure. Meta-rules need different matching semantics — uniformity
  breaks at the implementation level.
- Recursion trap: if meta-rules live in grammar files, can they rewrite
  themselves? A protected kernel is needed, which costs the elegance.
- Zahradnice's rule syntax is rich. Encoding it spatially needs either a
  simplified Baba-like agent grammar or a hidden-layer/subcell representation.

**A middle path that did not exist when this was written:** the repo now has a
generator stack (`src/gen/genlib` + tetris/snake/walker/animation generators) —
rules are emitted by typed C++ builders, not hand-written text. That opens a
tractable variant of reflection: **mutate generator parameters, not cfg text.**
The variation space is structured by construction (a piece set, a neighbourhood
radius, a weight table), invalid mutants are mostly unrepresentable, and the
robust parser remains as the last-resort safety net rather than the primary
one. Evolvability-over-parameters loses the closure elegance (the optimiser is
outside the derivation) but keeps the designer-controlled-chemistry property,
and is buildable this year rather than someday.

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
  memory** — stable still-life patterns *plus the engine's actual per-cell
  memory* (`$` restore, `#transient`); **associative recall** — rules that fire
  on partial pattern matches.
- **Pattern recognition** — the context-matching machinery is already a template
  matcher: `&` (equals ctx), `!` (not-equals ctx), `%` (ctx or ctxrep), `?`
  (any), `*` (LHS char), `$` (saved memory), `#` (out-of-screen), `~` (empty).
  The export omitted `!` and `%`; GRAMMAR.v2.md documents all of them. One
  constraint that shapes designs: each rule has a *single* ctx/ctxrep pair
  shared by every `&`/`!`/`%` cell in its body (GRAMMAR-pitfalls #3) —
  heterogeneous conditions decompose into multiple rules.
- **Swarm primitives** — pheromone deposition and decay are two-rule idioms
  (see `programs/archived/ants.cfg` for a first pass).

Value here is demonstrative rather than scientific: it shows the language is
expressive enough to make "intelligence-shaped" behaviour legible.

---

## 6. Mapping to the actual codebase

*This section was the most stale part of the export — it predated the May-2026
tooling wave. Rewritten against the code.*

### Already there

| Capability | Feature | Notes |
|---|---|---|
| Reward channel | `<score>` per rule | positional tail: number must start at header col 10 (pitfalls #20); check with `zahradnice-check explain` |
| Stochastic policy | `<weight>` per rule | intrinsic semantics, see §1 |
| Action interface | trigger char per rule | any key; headless `--input` feeds one trigger per byte, keys and timing chars uniformly |
| Multi-scale time | `#timing <char> <ms>` | per-program, any chars; **no built-in defaults** — B/M/T is convention, not engine behaviour |
| Sync/async knob | `#threads` | 0 = auto (default), 1 = one rule/step; N = up to N non-conflicting rules/step; `--trace` forces 1 |
| Topology | toroidal wrap; `#grid W H` = alignment granularity (not board size) | board size: terminal, or `--screen R,C` headless (default 24×80; row 0 = status) |
| Reproducibility | `--seed` | deterministic when single-threaded; `--replay` re-derives recorded runs bit-for-bit |
| Episode reset | bare `^` (clear at load); `#control x restart` / `c clear` at runtime | engine actions fire only via a carrier rule whose sound char is the control char (pitfalls #17) |
| Curriculum / level flow | `#program`, `#control t return`, call stack | derivation state flows between programs — still the most underrated asset here |
| Local memory | `$` restore + `#transient` | now documented (GRAMMAR.v2.md §Local memory); inspect with `--mem-snapshot`, `--trace-cell` |
| Parallelism telemetry | `{parallel}` status template var | usable order-parameter for §2.2 |
| **Headless batch** | `--headless --input STR/@PATH/@- --max-steps N` | final score on stderr; `zahradnice-headless` is a 76 KB curses/SDL-free binary (see HEADLESS.md) |
| **Observation export** | `--dump-screen` (txt/ansi, stdout or file); `--replay-snapshot S1,S2,…` | final frame per run; at-step frames via replay |
| **Trajectory logging** | `--trace` (v2 format) | per applied rule: step, cumulative score, source, trigger, LHS, (r,c), rule head (see TRACING.md) |
| **Per-rule stats** | `--stats` | rule-level fire counts per program |
| **Static analysis** | `zahradnice-check explain / why` | decoded rule geometry; dynamic match diagnostics against a screen dump |
| **Golden tests** | `make test` / `make update-tests` over `tests/` | seeded headless input → expected screen; the divergence-corpus pattern of §7, already running |
| **Generator stack** | `src/gen/genlib` + tetris/snake/walker/animation generators | cfg files as compiled artifacts; the substrate for §4's middle path |

### Gaps that remain (renumbered; the export's 1–6 are done or scripted)

- **G1 — Closed-loop step mode.** `--input` is open-loop: the whole trigger
  string is fixed before the run. An RL policy needs observe→act cycling.
  Interim, zero-engine-work: deterministic prefix-replay (re-run prefix +
  candidate action, read score/frame; O(T²) per episode). Proper fix: a
  headless mode that reads trigger bytes from stdin *incrementally* and emits
  frame + score after each event. `headless_runner.cpp` already has the loop;
  this is dozens of lines, not a subsystem.
- **G2 — Per-step frame streaming.** `--dump-screen` is final-frame only;
  `--replay-snapshot` needs a recorded trace. A `--dump-every N` (or G1, which
  subsumes it) closes this. Note the frame format is already the §7 cell-buffer
  contract in embryo.
- **G3 — Runtime rule mutation** (Level 2+/§3 route 3). Weights and rules are
  fixed at parse time. Needed for mutable-weight learning; explicitly *not*
  file-rewriting. Unchanged from the export; still the largest engine lift.
- **G4 — State hash in trace.** One field per `apply` line makes §2.1's
  repetition detection a text-processing job instead of a replay job. Tiny.
- **G5 — Seed-sweep harness.** Still a per-experiment shell/Python script; the
  `make test` loop is the template. Script-level, not engine-level.
- **G6 — Feed-until-quiescence.** Timing-saturated programs (`#timing T 0`)
  need "run until no rule fires" semantics for clean episode ends; known
  deferred item (`backlog` memory: build only when the friction recurs —
  §2.1-style experiments may be exactly that recurrence).
- **G7 — Multithreaded seed-determinism.** Multi-threaded runs diverge
  under identical seed+input (batch size / RNG consumption is
  timing-dependent), which blocks replay and prefix-diff debugging of MT
  runs. Note this is a determinism gap, not a correctness gap: conflict
  detection makes every MT batch equivalent to some sequential
  interleaving, so no illegal states arise — only the *distribution*
  over legal trajectories shifts (measurably: see the λc(#threads)
  result in experiments/convergence). Bounded fix: sample the batch
  sequentially from a dedicated PRNG, apply in parallel (disjoint
  footprints commute), keep worker threads RNG-free.

### Documentation gaps

Largely closed since the export: GRAMMAR.v2.md (draft) covers `!`, `%`, local
memory and `#transient`; GRAMMAR-pitfalls.md holds 20 engine quirks with
symptoms and fixes; HEADLESS.md and TRACING.md cover the tooling. GRAMMAR.md
(v1) still carries its old TODO list — consolidation of v1/v2 remains open, and
`#` as implicit screen boundary is still only documented as a context char.

---

## 7. Engine divergence (context, not research)

Two implementations exist and have drifted: the C/C++ canonical engine
(`popojan/zahradnice`) and the Bevy/Rust remake (`popojan/zero`). Sharing code
across the language boundary is rarely worth it for a hobby project; the right
seam is a **shared contract** — GRAMMAR.md as the language spec both target,
plus a stable description of the cell buffer the renderer consumes.

Cheap divergence detection: a small corpus of sample programs run through both
engines with a fixed seed, compared frame-by-frame on the resulting grid. *The
C++ half of this now exists:* `make test` runs seeded headless input scripts
and diffs plain-text screen dumps against golden files (`tests/`). Pointing the
Rust engine at the same corpus and dump format is the whole remaining work.

This overlaps directly with gap G2 above — the observation-export format *is*
the cell buffer contract. Building it once pays for both.

If a Steam release ever becomes concrete, the canonical-engine question resolves
itself at that moment (terminal C/C++ is the better authoring environment; Bevy
is the better distribution artifact). Until then, loose coupling through the spec
is what buys the option to defer.

---

## 8. Standing backlog items

- **Gravity as a complex sample program.** Masses emit "graviton" symbols;
  emission count scales with mass; gravitons decay with distance; bodies move
  against the gradient of the flux they encounter. The finite propagation speed
  is *more* physically faithful than instantaneous Newtonian gravity — and the
  toroidal topology produces genuinely strange orbital mechanics, including a
  field interfering with itself the long way round. *Status correction: a first
  implementation exists* — `programs/archived/gravity.cfg` +
  `gravity-setup.cfg` (parked). It uses **6 hexagonal graviton directions**,
  not the 8 the export described. Good stress test for long-range spatial
  coordination; reviving it starts from a working artifact, not a blank page.
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

*Rewritten: the export's step 1 ("headless mode + observation export + score
readout") shipped in May 2026. The critical path now starts at the experiments
themselves.*

Dependency order, cheapest-first, each step falsifiable on its own:

1. **§2.1 convergence toy** — the validated cfg above + a seed-sweep script
   (gap G5) + optionally the trace state-hash (G4). Pure theory, no agents, no
   engine changes beyond an optional one-field addition. An afternoon to first
   plot.
2. **Level 0 Life steering, open-loop** — bolt the validated cursor onto
   `programs/life.cfg` with `#transient` overlay; random and scripted policies
   via `--input`; score distributions across seeds. Also playable interactively
   — the fun test is free.
3. **Closed-loop via prefix-replay** — a small Python harness around
   `zahradnice-headless` doing greedy/bandit action selection by deterministic
   re-runs. Proves the observe→act loop end-to-end with zero engine work, and
   tells us whether G1 is worth building.
4. **G1 step mode** — only if (3) says yes. Then a real gym-style wrapper.
5. **Stigmergic agents** (Level 3 route 2) — revive `archived/ants.cfg`;
   cheapest genuinely emergent behaviour.
6. **Level 1 embodied agent**, local perception only.
7. **Rule-as-meta-rule weight adaptation** (Level 3 route 3) — needs G3; the
   closure result.
8. **Level 2 multi-agent** with symbol-partition safety constraints (the
   z-order constraint is gone; partitioning carries it).
9. **Reflective layer** — only if 1–8 have made it feel necessary; consider the
   genlib-parameter middle path (§4) first.

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
