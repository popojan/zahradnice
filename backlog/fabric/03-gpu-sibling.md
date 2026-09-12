# The GPU sibling: a minimal synchronous rewriting fabric

Status: proposed 2026-09-12. Not started. This answers the user's
"should we leave the repo and try something minimal in this style on a
GPU?" — recommendation: **not yet, and not by leaving.** Stay in the
repo through tier 3 (cheap, exact, everything already instrumented);
start the sibling at the first *scale-limited* question (R5.x, or a
tier-4 rung that needs thousands of replicas); keep the cfg family as
the shared language so the repo remains the spec-authoring and
exactness oracle (the §13 doctrine: discover here, validate the kernel
against replay, then let the kernel earn the big runs).

Hardware note (2026-09-12): the machine this was written on has an
Intel UHD 620 and a CPU-only torch; the RTX 4070 mentioned in
`research-rl-ai.md` §11 is another box. A torch prototype runs on both,
which is a reason to prototype in torch first.

## 1. Why the sibling is legitimate for this line and not for the nights

§11.3 was right: batching one derivation shifts the physics of
jump-chain models. The fabric's CA-family (foundations §3) is
schedule-independent *by construction* (write-once, decided-input
gating, anchor-only writes), so a full synchronous sweep produces the
same outcome distribution as one-cell-per-event Zahradnice. The sibling
is not an approximation of the substrate; for this family it is the
same machine, faster. R5.0 proves it before anything else runs there.

## 2. Data model

- State: integer tensor `S[B, Z, H, W]` — `B` replicas, `Z` planes
  (activity, synapse rows, backward channel, gates…), `uint8` glyph ids.
  Layers can be bands in `H` exactly as in the repo, or planes in `Z`;
  the transpiler chooses.
- Rule: `(anchor, pattern, rhs, weight, phase)`; a pattern is a list of
  `(dz, dy, dx, class)` where class is a glyph, a glyph set (the repo's
  `!`/`%`/`&` resolve to sets), or — beyond the cfg — a **count**
  constraint `count(set, neighbourhood) ⋈ k`. Counts are the one
  primitive the cfg cannot state and a deterministic threshold neuron
  needs; they are also how Life-like totalistic rules are written, so
  the sibling generalises both Zahradnice bodies and classical CAs.
- Global scalar per replica: the phase/bus character.

## 3. Step

For one phase character:
1. For every rule, a match mask `M_r[B, Z, H, W]` from equality tests on
   shifted views (`torch.roll` on the torus — the repo's wrap for free)
   and, for counts, a convolution with a 0/1 kernel.
2. Per cell, sample one applicable rule ∝ weight (Gumbel-max over
   `log(w_r) · M_r`, or exact categorical), with a "no rule" outcome
   when nothing matches.
3. Write the anchor glyph. Synchronously, whole tensor. No conflicts
   exist because every rule writes only its anchor.
4. Repeat until no mask is true anywhere in the replica (quiescence),
   at most `Z·H` sweeps; report sweeps per phase.

Schedule knob for research: `α` = fraction of cells allowed to update
per sweep (α-asynchrony; α=1 synchronous; α→0 Zahradnice). For the
CA-family the outcome distribution must be α-invariant — a built-in
self-test.

## 4. Learning on the sibling

Every learning rule of tiers 1–3 is a rule in the same table, keyed by
a phase character, so nothing changes. What the sibling adds:
- **Replicas** (`B` in the thousands): Monte Carlo inference by vote;
  seed-variance curves for free; the R5.3 learnability-vs-size sweep is
  one call.
- **Evolution strategies / perturbation** over matter: perturb synapse
  planes across replicas, evaluate reward, move the population toward
  the rewarded perturbations — the family that is hopeless on one CPU
  and native here (R5.1).
- **Determinism**: seeded Philox-style generation per replica; a run
  is reproducible from `(seed, table, α)` like a trace is.

## 5. Validation contract (R5.0)

Take the tier-0 and tier-1 cfgs; transpile (L-F); run the same seeded
sample sequence in Zahradnice (one cell per event, `--trace`) and in the
sibling (synchronous). Because inference is a sample, compare
*distributions*: per-cell firing frequencies over ≥10³ replicas vs the
same over ≥10³ seeded Zahradnice runs, and the learning curve within
seed variance. A deterministic sub-family (θ=0, no stochastic units)
must agree **bit-exactly** on fixpoints — that is the assertion in the
test suite.

## 6. Size of the thing

- torch prototype: ~300 lines (loader for the transpiled table, step,
  quiescence loop, replica batching, the α knob, tests against the
  repo's dumps). One session.
- CUDA kernel: only if the torch version is memory-bandwidth-bound on
  the R5.2/R5.3 sweeps; a rule table with ≤10³ rules over ≤10⁷ cells
  per replica is well inside a 12 GB card either way.
- Rendering: none needed; a glyph plane dumps to text exactly like the
  repo's `--dump-screen`, so the fabric stays *visible* (foundations
  §5(ii)). `backlog/research/pixel-rendering.md` covers a pixel view if
  one is ever wanted for the interactive case.

## 7. Where it would live

A sibling repository (the user's call), with this backlog directory
as its founding document and `tests/fabric/` here holding the cfgs and
dumps it validates against. The repo keeps: the language, the
generators, the exactness tooling, the on-ramp results. The sibling
keeps: scale. If the sibling ever needs a primitive the cfg cannot
say beyond counts, that is the signal to revisit L-C/L-D in the repo
rather than to fork the language.
