# OW-1 — allele calibration of the gated uberprogram (F3)

Date: 2026-08-23. Driver `ow1.py`; compiler `gen_gated.py`; raw
verdicts `ow1_calibration.csv`. Verdict up front: **PASS on all
three stages — the gated uberprogram with a uniform regulatory row
is the same stochastic process as the plain-compiled genotype**, at
a measured union tax of ~1 µs/event per ~25 union rules of gated-off
law at ring-6 matter density.

## Claim under test

P0 established the mechanism; OW-1 tests the exactness claim behind
the whole open-world design: under a uniform allele row, every rule
in the union either passes its gate everywhere (the allele's own
rules) or fails it everywhere, so the applicable (rule, locus) set —
and hence the weighted sampling distribution — is *identical* to the
plain night-2 compilation at every reachable state. Any statistical
divergence is a geometry bug.

## Setup

Alleles = 4 censused F2 genotypes: α `A>A.writeA` (blind spawner,
the unique k=1 static repairer), β `A>B.writeA|B>A.req~` (the
dynamic-repair archetype), γ `A>B.writeA` (trail walker, night-2's
seed-lottery MIXED case), δ `A>A.self` (fixed point, dies to one
poke). Union = 4 rules; γ's rule is co-owned by β → one `%` header
(field-6-OR-7), the rest `&` singletons. Harness pokes appended
ungated, exactly night 2's. Protocol, geometry, classifier, verdict
logic: night 2's, unchanged (`T*200 + 3×[p+T*200]`, ring 6).

Init needs zero engine work: tape `^Auc` (row 1), regulatory row
`^<glyph>l*` (bottom row) — the (−1,0) gate read reaches it through
the toroidal wrap.

## Results

**Stage A — distributional calibration** (200 seeds × 2 arms × 4
genotypes = 1,600 runs; trace↔dump exact accounting on every run in
both arms: 1,600/1,600):

| allele | plain | gated | modal z |
|---|---|---|---|
| α | REPAIR 200/200 | REPAIR 200/200 | 0.00 |
| β | REPAIR 200/200 | REPAIR 200/200 | 0.00 |
| γ | REPAIR 122, DIED 78 | REPAIR 116, DIED 84 | +0.61 |
| δ | DIED 200/200 | DIED 200/200 | 0.00 |

Bonus fidelity check: the plain arm at seeds 1–3 reproduces
night-2's published γ verdict verbatim (DIED, DIED, REPAIR) — the
calibration target is literally the night-2 run, re-executed.

**Stage B — forced-trajectory identity.** β and γ have singleton
applicable sets in the intact phase, so the no-poke trajectory is
forced. Plain and gated tape rows agree **step-for-step over all
201 states, with different RNG seeds per arm** (6/6 pairs) — the
sharpest possible form of the exactness claim: the gated arm cannot
even use randomness to differ.

**Stage C — the union tax** (marginal µs/event, T×20000 vs T×100,
median of 3):

| ring | plain (1 rule) | gated-4 | gated-96 |
|---|---|---|---|
| 6 | 0.49 | 0.92 | 5.6 |
| 64 | 1.08 | 5.5 | 43.1 |

The 96-rule union (all of F2 as singleton alleles, worst case: one
rule live, 95 dead) costs ~40× plain at ring 64 — scan cost scales
with matter instances × union rules, with the gate cell failing
fast. Absolute numbers stay practical: 10⁶ events ≈ 43 s in the
worst case measured. The design doc's flagged perf question is
answered: measure again only if unions grow into the hundreds.

## What OW-1 buys the arc

1. The uberprogram is a **faithful multiplexer of censused laws**:
   every allele's night-2 verdict is reproduced from inside the
   union. The open world's law space is calibrated ground.
2. `gen_gated.py` is the F3 compiler: allele → `&`/`%` headers over
   shared bodies, `gated_idx_map` for replay; exact accounting works
   unchanged because calibration never writes gates (`writes()` is
   gate-free).
3. Family separation holds: `gen_family.py` untouched; F3 results
   never contaminate nights-1.0 claims.

## Answered session-1 question

"M2 currency first or currency-free calibration?" — currency-free
calibration, done here. Fuel tokens stay out until the selection
experiments (OW-2/3) have a story; currency remains night-12's axis.

## Exit → OW-2

Selection among laws: heterogeneous allele rows (blocks of different
alleles on one ring), wounds striking both rows, and the
load-bearing control — no allele-copy rules (gate row only erodes,
inheritance absent) vs treatment (one copy rule per allele, priced
per symbol as the engine demands). Question: does allele occupancy
show a reproducible selection differential, and does winning
correlate with censused repair grade?
