# Paper #2 outline — "Ten nights": evolution from uniform law in a shared-measure rewriting substrate

Working title options:
- *The Subtraction Ladder: what must be law for evolution, measured by deletion*
- *Ten Nights of Inverse Emergence: repair, heredity, and parasitism in eleven rules*

Positioning: paper #2 of three. #0 (substrate companion) carries the
language/engine; cited for all substrate detail. #1 (batching vs
criticality) separate. Audience: ALife. Every claim passes the
translation test: stated for asynchronous stochastic rewriting under
a shared event measure; zahradnice named as instrument.

## Abstract (skeleton)

Question: how much of evolution must be written into physical law,
and how much is matter? Method: an inverse-emergence pipeline
(admissible-by-construction rule families, stratified exhaustion,
exact event-level accounting) over a 1-D toroidal rewriting substrate
in which all processes pay from one event budget. Result: ten
experiments that successively delete authored ingredients — mechanism
libraries, rate dials, lineages, mutation operators, fitness
functions, copy primitives — ending in worlds of 9–13 uniform rules
that exhibit selection, heredity, dormancy, rescue, error
catastrophe, tragedy of the commons, parasitism, and permanent
coexistence, none of them named in the law. Six laws (below) as the
enumerated contributions.

## The six laws (boxed through the paper; each restated substrate-free)

L1 EXPRESSION. Stored variation is inert without damage: wounding is
   simultaneously selection pressure and the transcription mechanism
   that turns pattern into behaviour. (N5: 144/144 no-birth controls;
   N7: frozen ledger; N8, N10 echoes.)
   Substrate-free: in machinery-mediated copying systems, variation
   enters phenotype space only through repair events.
L2 CONTEST. Selection acts on contested rates only; an uncontested
   rate is a schedule, and schedule is invisible. (N4: mover 240/240
   vs handler nil; N9-D: bit-identical vs 24/24; unified with L5.)
   Substrate-free: a rate parameter is selectable iff two processes
   race for the same resource under one clock.
L3 STRUCTURAL FITNESS. The shared event budget is itself a fitness
   function: mechanisms differing only in events-per-outcome differ
   in fitness with all weights equal. (N6 ladder; N3 collapse.)
L4 RESIDENCE. Equilibrium composition tracks the machinery's
   residence distribution; structural dwell above threshold selects
   slowness even in a healthy commons. (N7; N9-B: dwell-3 s-share
   0.69 living commons; equilibrium ≈ residence in all cells.)
L5 HEREDITY. Heritable information is exactly the part of pattern
   whose reading changes what the machinery writes; reading frequency
   is irrelevant. (N8: WHEN-codon 40% of repairs, zero effect;
   WHAT-codon 9–21%, first-order.)
L6 DECEPTION. Deception persists iff fueled by the order it attacks:
   boundary-fueled infidelity starves on its own success; order-
   fueled infidelity self-regulates into permanent coexistence.
   (N10: mutator vs deceptive pair.)

## Structure

1. Introduction
   - The question (law-side minimum of evolution), the substrate in
     one page (jump-chain rewriting, shared measure, laws/matter
     boundary), the instrument argument + translation test.
   - The subtraction-ladder figure: ingredient x night matrix
     (mechanism library / weights / lineages / mutation op / fitness
     fn / copy primitive / fidelity — each crossed out at its night).
2. Method
   - Family compilers, admissibility by construction; stratified
     exhaustion => "minimum within family F" claim semantics.
   - Exact accounting: trace->state replay checked byte-exact against
     engine dumps; headline: every replayed run of the arc (~25k)
     exact.
   - Controls: adversarial verify (held-out seeds, horizons, ring
     sizes); three-arm same-seed design; three-probe mechanism
     attribution (birth ledger / death ledger / state-conditioned
     residence); power discipline (the 16->64 seed lesson, reported).
   - Cost ledger table: runs, ms/run, wall per night; laptop-scale.
3. Movement I — Minimal mechanisms (N1–3)
   - Census method + predicate-dependent minima (P_state k*=1 torus
     walker, P_pop k*=2 proven by exhaustion); M4 scaffold as first
     structure-construction.
   - Self-repair: static k*=1, dynamic k*=2; damage-as-signal
     universal (16/16 mover+handler decomposition).
   - Phase diagram: budget-share collapse (~1/3 event share),
     taxonomy predicts ring scaling, damage-breeds-walkers
     (fragmentation reproduction), alive-but-altered.
4. Movement II — Evolution assembled (N4–6)
   - Trail-as-genome; dormancy/seed bank (resurrection 21/24).
   - The selection dichotomy => L2.
   - Mutation: adaptation 288/288, arrow 0/288, L1 controls.
   - Stroke ladder => L3; leapfrog 2:1, clonal interference,
     evolutionary rescue (non-monotone in mu), error catastrophe.
5. Movement III — The author dissolved (N7–8)
   - Tape commons: 9 uniform rules; per-event flows neutral (both
     ledgers ~1.00); selection in state structure; collapse regime;
     residence => L4 (with N9-B dwell-3 upgrade).
   - Closing the loop: null self-homogenization; WHEN vs WHAT codons
     => L5; codon buys one damage step (N9-C boundary).
   - Honest epistemics thread: N7 prediction refuted by probe 1;
     N9-A dissolving N7's apparent selection.
6. Movement IV — Ecology without an author (N10, N9-D)
   - Mutator starvation; the parasite phase (rho ~ 0.2 plateau,
     stochastic limit cycle, sd rising with damage).
   - Matter-benefactor / information-corruptor; first permanent
     coexistence on the bare ring; self-sustaining variation => L6.
   - Contested repair (N9-D) as L2's second cell, presented here.
   - NEW (gap experiment): ring-size scaling at equal machinery
     density — does the parasite phase persist at 2x ring?
7. The phenomena ledger (signature table; see below).
8. Limits
   - 1-D, small rings, two-glyph genomes; codon templates still
     law-side; head placement constraints (density note); negative
     results as results (WHEN-codon, mutator, handler).
9. Related work: AlChemy, Tierra/Avida (replication authored vs never
   primitive here), EvCA (search over laws vs over matter), async CA
   (Fates; Blok-Bergersen), voter models, Eigen error catastrophe &
   hypercycle/parasite problem, Bell-Gonzalez rescue, seed-bank
   ecology, Lenski LTEE (rescue/interference analogies).
10. Outlook: 2-D removes (codon table in matter; compartments now
    that a parasite exists), virulence sweep, the summit question
    status (multiplication+heredity+variation+selection present;
    self-copying structures = composition ahead).

## The phenomena ledger (draft; final numbers from result docs)

| phenomenon | night | world (rules) | designed or emerged |
|---|---|---|---|
| oscillator minima, predicate-dependent | 1 | F1 (1–2) | census (exhaustive) |
| scaffold-context mechanism (M4) | 1 | F1 (2) | emerged in census |
| dynamic self-repair | 2 | F2 (2) | discovered by exhaustion |
| damage-as-signal regeneration | 2 | F2 (2) | emerged as ONLY route (16/16) |
| viability threshold (budget share) | 3 | F2 (2) | emerged |
| fragmentation reproduction | 3 | F2 (2) | emerged, unsearched |
| heredity + breed-true | 4 | lineage (4) | composed |
| seed bank, dormancy, resurrection | 4 | lineage (4) | emerged |
| drift, gambler's-ruin fixation | 4 | lineage (4) | emerged |
| selection on contested rates | 4,9 | lineage (4–6) | law, both cells measured |
| adaptation with an arrow | 5 | lineage (6) | 288/288 vs 0/288 |
| genotype/phenotype + expression | 5 | lineage (6) | emerged (L1) |
| mutation–selection balance | 5 | lineage (6) | emerged |
| adaptive walk, leapfrog, interference | 6 | ladder (15) | emerged |
| evolutionary rescue | 6 | ladder (15) | emerged |
| error catastrophe | 6 | ladder (15) | emerged |
| commons collapse; shelter | 7 | tape (9) | emerged (prediction refuted) |
| tragedy of commons (dwell threshold) | 9 | tape (9) | emerged |
| self-organized homogenization | 8 | tape (9) | emerged null |
| sequence-programmed replication | 8 | tape (11) | template designed, effect measured |
| parasitism; host–parasite cycle | 10 | tape (11–13) | emerged |
| permanent coexistence, no niches | 10 | tape (13) | emerged |
| self-sustaining variation | 10 | tape (13) | emerged |

## The world zoo (notation-unifying table)

| world | nights | matter | law size | init | damage |
|---|---|---|---|---|---|
| census worlds F1/F2 | 1–3 | A,B | 1–2 (+2 poke) | single A | point deletion, trigger p |
| lineage worlds | 4–6 | heads A/C/E…, trails B/D/F, primed G/H/I | 4–15 (+pokes) | 1–2 heads | point deletion |
| tape world | 7–10 | genes f/s; heads F/S/W(/V) | 9 base + 2 per codon (+2 poke) | random tape + heads | point deletion, tape-only |

## Figures/tables plan (all regenerable from experiments/inverse CSVs)

F1 subtraction-ladder matrix (ingredient x night).
T1 cost ledger (per night: runs, ms/run, wall, exactness).
T2 night-2 mechanism census (4 classes).
T3 night-3 phase table (m x survival/recovery).
T4 selection dichotomy table (N4) + contested completion (N9-D).
T5 ladder outcomes (N6: winners/paths/rescue).
T6 residence law table (N7+N9-B, equilibrium vs residence).
T7 WHEN/WHAT codon paired differentials (N8).
T8 parasite phase (N10: rho by arm x m; + scaling gap result).
T9 phenomena ledger. T10 world zoo.

## Gaps to close pre-TeX

1. Parasite ring scaling at EQUAL machinery density (24:1 head vs
   48:2 heads, both 1/24) x m {8,4,2} x arms {plain,para,paraonly}.
   Also settles/scopes the N7 head-density confound.
2. World-zoo + translation-test passes: in this outline (done above).
3. Everything else: no further experiments needed; 240/240- and
   288/288-margin results need no re-powering.
