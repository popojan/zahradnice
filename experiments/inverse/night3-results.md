# Inverse emergence, night 3: the repair phase diagram

Night 2 asked *whether* minimal self-repair exists (yes, k=2,
damage-as-signal). Night 3 maps *how much* damage those mechanisms
sustain: 100 pokes at interval m (one poke per m+1 events,
m ∈ {0,1,2,3,5,8,12,20,40}), rings 6 and 12, 6 seeds, then a 400-event
quiet window — does the pre-damage behaviour re-establish? Subjects:
the 16 verified dynamic repairers, the k=1 static repairer
`A>A.writeA`, the flip-flop as doomed control. Driver `night3.py`,
measurement `analyzers.sustain_verdict`, data `night3_sustain.csv`.
1,944 runs, all trace↔dump exact, 11.0 ms/run, 5.2 s wall (jobs=8).

## Findings

**1. Minimal repairers tolerate near-saturation damage.** The
adjacent-respawn family recovers 6/6 seeds down to m=1–2 — one to two
working events per wound. The survival cliff is sharp and
ring-INDEPENDENT: the archetype `A>B.writeA|B>A.req~` flips from
0/6 at m=1 to 6/6 at m=2 on both rings. Matter balance reads
directly: a poke erases one cell per block while at most one
productive write per event rebuilds; damage claiming ~1/2 of the
event budget starves regrowth, ~1/3 is survivable. Collapse is a
budget-share threshold, not a geometry effect — the night-1/Peak-B
theme (all processes pay from one event measure) showing up
uninvited in an ecology question.

**2. The night-2 taxonomy predicts the phase diagram.** The two
walk-to-wound mechanisms (night-2 repair medians 9–11 vs 3–6) are
exactly the two fragile ones: m\*=8 on ring 6 and never 6/6 on ring
12 — their healing time scales with the lap, so the fixed recovery
window fails on the larger ring. Adjacent-respawn m\* does not move
with ring size. Mechanism structure, measured on 6 cells, predicted
robustness on 12: the taxonomy is doing real explanatory work.

**3. Damage breeds walkers (the night's discovery).** Sampled head
counts for the archetype (ring 12): meanA = 1.25 at m=40, rising
monotonically to **2.96 at m=3** — sustained wounding maintains ~3
concurrent walkers, each wound spawning a head via the handler rule,
heads merging on collision. Fragmentation reproduction (the
planarian motif): population = wounding rate vs merge rate, and
**replication-like dynamics emerge from repair + environment with no
copy primitive and no search for it** — this fell out of a phase
sweep of mechanisms selected only for self-repair. On the road to
the summit question (self-copying without a copy primitive) this
reorders the plan: multiplication is already in hand; what's missing
is heredity (variants that breed true), which is a composition
experiment, not a needle-in-haystack search.

**4. "Alive but altered" is its own phase.** The fragile family at
high damage on ring 12 survives 6/6 but restores behaviour only
~3/6: it lacks a merge mechanism, so damage-induced proliferation is
irreversible and the post-damage attractor is a permanent multi-head
gas — a changed identity, not death. Recovery-of-class and survival
separate cleanly in the data.

**5. Baselines behave.** The blind spawner survives even m=1
(heavily eroded, meanA 2.16 of 6, full recovery after); the
flip-flop dies at every rate; m=0 (pokes with no working events
between) kills everything — no mechanism in F2 repairs with zero
event budget, as the shared-measure argument requires.

## Honest limits

- One damage model (uniform point deletion) and one geometry family
  (rings 6/12); "budget-share threshold" is measured at two ring
  sizes, argued but not proven general.
- Recovery is judged in a fixed 400-event window; walk-to-wound
  mechanisms on large rings might recover in longer windows (their
  failure is *slowness*, not impossibility).
- Head counts are sampled at poke instants (pre-poke states), a
  slight undercount of the between-poke maximum.

## Night-4 shaped question

Heredity: two walker variants (distinct trail glyphs), shared
damage-driven proliferation — do lineages breed true under wounding,
and does differential repair speed become selection? That is natural
selection assembled from three verified mechanisms (repair,
proliferation, variation) in ~6 rules — a composition experiment
with exact accounting, and simultaneously a showpiece program
(the experiment IS a watchable ecology).
