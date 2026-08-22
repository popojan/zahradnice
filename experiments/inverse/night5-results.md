# Inverse emergence, night 5: mutation — evolution's arrow in six rules

Night 4 supplied heredity and located selection (contested rates
only). Night 5 adds the last ingredient, **in-run variation**, and
watches evolution run. Fixed law, six T-rules plus the poke harness:
slow lineage A/B (mover weight 0.5), fast lineage C/D (mover weight
1), equal handlers, and mutation as law — trail copying errors
`B↔D` at weight μ, paying from the same event budget as everything
else. Init is a single resident lineage; the other must *arise*.
Driver `night5.py`, data `night5_evolution.csv`; init {slow, fast} ×
damage interval m {∞, 16, 8, 4, 2} × μ {0.001, 0.003, 0.01} × 24
seeds = 720 runs of ~24k events, all trace↔dump exact, 226 ms/run,
34 s wall (jobs=8).

Watch it live: `./zahradnice demos/inverse/evolution.cfg` — green
resident, cyan specks of stored variation, a wound expresses one,
the sweep, then green flickers of back-mutation forever after.

## Findings

**1. Adaptation: 288/288.** Every slow-start run at every damage
rate ends with the fast mutant lineage in sustained majority
(last-quarter share 0.96–1.00). Median time to the first fast birth
falls with both knobs — from 1,887 events (m=16, μ=0.001) to 85
(m=2, μ=0.01) — and takeover follows ballistically (night 4's
mover selection doing the work).

**2. The arrow: 0/288 reversals.** Fast-start runs under the same
symmetric mutation law: slow mutants are born constantly (median 26,
up to 473 doomed lineages per run) and are eaten every time;
sustained slow share never exceeds ~0.04 (the mutation floor).
Same law, same flux, opposite fates — direction comes entirely from
selection on the contested rate.

**3. Stored variation is not expressed variation (the control).**
With no damage: 144/144 NO_BIRTH. Mutant trail accumulates to a
mutation-overwrite balance — up to 17% of the genome at μ=0.01 —
and sits there, invisible to selection, because expression requires
a wound: the handler only transcribes trail into a living head
beside a hole. Damage is simultaneously the selection pressure and
the *expression mechanism*; without it the population carries
variation but cannot evolve. (Measured flux is mass-proportional:
post-takeover the standing D-trail emits ~14× more back-mutations
than forward ones — pressure follows abundance.)

**4. The churn corner, and a classifier lesson.** At m=2, μ=0.01
the endpoint snapshot misclassified 3/48 runs (2 "holds" with
last-quarter mutant share 0.92–0.95; 1 "deleterious takeover" with
share 0.04): a third of the ring is holes at any instant there, and
end-state totals of ~15 cells fluctuate across the majority line.
Sustained share, not final snapshot, is the honest observable —
the same static-vs-dynamic-truth lesson the zen-scoring session
taught, recurring in an evolution experiment.

**5. Sampling-mass intuition fails politely.** While tuning the
demo, mutation fired 6× less than back-of-envelope predicted; the
stats file's `considered` column decomposed the applicable mass
exactly (mean 6.5 concurrent heads — proliferation — versus the
expected 1-2) and the observed count matched to within one event.
The engine's own accounting is the better calculator.

## The composed system

Rules for a complete evolving system, all discovered/verified in
nights 2–5, none designed for evolution per se:

| ingredient | rules | discovered |
|---|---|---|
| self-repair (mover+handler) | 2+2 | night 2 |
| multiplication under damage | 0 (emergent) | night 3 |
| heredity + dormant seed bank | 0 (trail = genome) | night 4 |
| selection (contested rate) | 0 (weight asymmetry) | night 4 |
| variation | 2 (mutation law) | night 5 |

Six T-rules, four poke rules, one init symbol: variation + heredity
+ selection + expression, with measured rates for every arrow.

## Honest limits

- One fitness axis (walk speed), two alleles, 1-D ring: this is
  evolution's minimal demonstration, not its study. No epistasis, no
  novel phenotypes — the mutant's advantage was authored into the
  law (weights), not discovered by the mutants.
- The summit question is exactly the next remove: can the *mechanism
  itself* (not a weight) be the heritable, mutable thing? That needs
  genotype encoded in matter richer than one glyph — pair cells or
  glyph-indexed rule families — where a trail pattern selects among
  behaviours. Filed as the night-6+ direction; the laws/matter
  boundary (§13) says how far that can go without touching laws.
