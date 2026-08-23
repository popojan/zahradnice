# Related work & novelty audit — The Subtraction Ladder (paper #2)

Date: 2026-08-22 (post-publication, pre-journal). Method: four parallel
literature sweeps — (1) rewriting/string-chemistry ALife substrates,
(2) replicator–parasite–compartment theory, (3) selection-without-fitness
formal theory, (4) field map + venues. Each entry tagged
PRIOR-ART / PARALLEL / SUPPORTS / CONTRADICTS / CITE-FOR-CONTEXT and
[verified] (abstract fetched) vs [recalled] (assistant training knowledge —
re-verify before citing).

Status: all four sweeps complete.

## Executive verdicts (claims of the paper vs the literature)

| Claim | Verdict | Closest prior art |
|---|---|---|
| Damage breeds multiplication (repair + wounds → fragmentation-proliferation, no copy primitive) | **Novel as a composite**; four partial precedents, none derived from *enumerated minimal* repair rules, none unsearched-for | Growing NCA planarian cut (Mordvintsev 2020, trained rule); amyloid/prion fragmentation (Knowles 2009); Gray–Scott spot division (Pearson 1993); SDSR/evoloop dissolution (Sayama 1999) |
| Exhaustive rule-census method | **Partial precedent** — claim the scope (complete rule-set families vs repair/heredity predicates in a driven async substrate), not the method | Adams, Zenil, Davies & Walker 2017 (exhaustive small-CA census vs OEE predicates); Wolfram ECA; Varetto 1993 & Banzhaf 1993 (object-space censuses) |
| L1 Expression (variation inert without damage; wound = selection + transcription) | **Partial precedent under other names**; novel as a formal law identifying the *same event* as both | Cryptic genetic variation (Rutherford & Lindquist 1998; Paaby & Rockman 2014); stress-induced mutagenesis (Galhardo 2007); seed banks (Lennon & Jones 2011) |
| L2 Contest (rate under selection iff contested under one clock) | **Substantially a rediscovery** — it is soft selection (Wallace 1975) + Eigen's constant organization; demote to "the shared-event-budget substrate makes soft selection *exact* and provable (bit-identical, not merely weak)" | Wallace 1975 (soft selection); Eigen 1971 (constant organization); Bertram & Masel 2019; GSPN conflict-vs-concurrency (Ajmone Marsan 1984); Hindersin & Traulsen 2015 |
| L3 Structural fitness (events-per-outcome is fitness, all weights equal) | **Known in substance in digital evolution, novel as formal law** — Avida fitness = merit/gestation is events-per-outcome verbatim; our additions: no organism boundary, no scheduler, all weights equal, derived not designed | Avida (Ofria & Wilke 2004); Tierra SlicePow parsimony (Ray 1991); Pross DKS (chemistry cousin) |
| L4 Residence (dwell excess = selection differential → composition fixation) | **Apparently novel as the composed chain**; each link known separately; state the sign-flipping axiom (damage must be dwell-blind) | TASEP slow-bond queueing (MacDonald 1968; Janowsky & Lebowitz 1992); persister cells (Balaban 2004); duplex-decay protection (Scheuring & Szathmáry 2001); foils: Spiegelman's monster, codon-optimality mRNA decay |
| L5 Heredity (heritable = what reading changes in what machinery WRITES) | **Novel as criterion, not as intuition** — position as the answer to Vasas et al. 2010 ("no template copying ⇒ no evolution") | Vasas, Szathmáry & Santos 2010 (the objection L5 answers); Takeuchi & Kaneko 2019/2025 (informatic asymmetry); Szathmáry & Maynard Smith 1995 (limited/unlimited heredity); von Neumann; Kolchinsky & Wolpert 2018; Cotler et al. 2025 |
| L6 Deception (order-fueled parasitism → permanent coexistence) | **Novel as a stated law in the replicator literature; NOT novel as a principle** — frequency-dependent deception is textbook signaling theory. Claim: substrate instantiation + order/disorder dichotomy + no mutation operator anywhere | Searcy & Nowicki 2005 (signaling); Colizzi & Hogeweg 2016 (mirror arrow: disorder-fueled); Ikegami & Hashimoto 1995 (active mutation); Zaman et al. 2014 |
| Permanent 1-D no-compartment coexistence | **Phenomenon class known, mechanism + substrate plausibly novel.** Known routes: 2-D self-organization, compartments, hyperparasites, parabolic growth, Tierra (oscillatory). Unclaimed: fuel-coupling feedback, no-copy-primitive substrate, phase at all damage rates. **Defenses 1+2 EXECUTED 2026-08-23** (night10_exponent.py, night10-exponent-results.md): parabolic rival EXCLUDED — births at x=0 (all deceptive-pair; order-arm control 0/2.07M), non-absorbing extinction (up to 7,276 resurrections), cross-dominated minority production, negative naive exponents; no mesoscopic spatial refuges (overlap excess ≤0.09, run length ≈ pair-write scale). Coexistence is influx-stabilized (influx ∝ complement's order, self-regulating — distinct from mutation balance where influx ∝ abundance). Remaining defense: the Tierra paragraph (writing, at next paper revision) | Maynard Smith 1979 (the foil); Szathmáry & Gladkih 1989 + Paczkó et al. 2024 (parabolic rival, now excluded); Bansho et al. 2016 (bulk death vs compartment oscillation); Boerlijst & Hogeweg 1991; Ray 1991 |
| NESS certified by measured probability current | **Partial precedent; apparently first inside an ALife substrate's configuration space** | RPS game experiments (Wang, Xu & Zhou 2014); entropy production of cyclic games (Andrae 2010); landscape-flux (Li/Wang 2011; Xu et al. PNAS 2021) |
| Non-monotone P(rescue) in mutation rate | **KNOWN** — exactly Anciaux et al. 2019 (rescue → lethal mutagenesis crossover, optimal U). Reframe as emergent reproduction in a fitness-function-free substrate; omitting the cite would be a priority error | Anciaux, Lambert, Ronce, Roques & Martin 2019, Evolution |
| Shared event budget as *the* contested resource (time itself contested) | **Apparently novel as explicit framing** — mechanism exists verbatim in GSPN race semantics and Gillespie SSA but never given a selective interpretation; Hubbell's zero-sum drift uses the budget to null selection instead | GSPN (Ajmone Marsan 1984); Gillespie 1976/77; Hubbell 2001; Ackley MFM (events free, not contested) |

Error catastrophe: standard (Eigen 1971); distinguish informational error
threshold from demographic lethal mutagenesis (Bull, Sanjuán & Wilke 2007)
when describing ours (ours is load-driven death = closer to lethal
mutagenesis). "Survival of the flattest" (Wilke et al. 2001) is the
digital-evolution phenomenology cite.

## Sweep 1 — rewriting substrates & digital-life chemistries

### Nearest relatives

- **Stringmol** (Hickinbotham, Clark, Stepney; semantic closure: Clark,
  Hickinbotham & Stepney, J. R. Soc. Interface 2017) — executable-string
  chemistry, evolved replicase-template systems and a universal-constructor
  architecture. PARALLEL: closest living relative; has explicit copy opcode
  and per-molecule programs vs our uniform grid-local rules. [recalled/corroborated]
- **Hickinbotham, Stepney & Hogeweg 2021** (bioRxiv 2021.02.25.432891,
  "Nothing in evolution makes sense except in the light of parasitism";
  also R. Soc. Open Sci. 8:210441) — parasites arise immediately (short
  strings copied faster); replicators evolve to *slow down replication*;
  extinction prevented only by compartments or spatial patterning; parasites
  drive complexity. PARALLEL + the consensus backdrop our 1-D coexistence
  contradicts. [verified]
- **Stepney & Hickinbotham, ALIFE 2021** ("What is a Parasite?") —
  operational definitions of emergent parasitism/hypercycles; align our L6
  terminology with theirs. [verified]
- **Hutton 2002** (Artif. Life 8:341, Squirm3; + 2007 cells) — emergent
  template replicators from random soup; **periodic half-floods (external
  mass damage) sustain evolution**. PRIOR-ART for damage-as-driver in a
  rewriting chemistry; copy is built into the reaction set. [verified]
- **Rasmussen et al. 1990** (Physica D 42, Coreworld; + 1991) — 1-D noisy
  computational substrate, "computational free energy" metered to
  instructions; cooperative copy/split structures through seven epochs.
  PRIOR-ART for 1-D emergent structures under continuous noise + execution
  resource as selective medium. [verified]
- **Pargellis Amoeba** (1996–2017, incl. Artif. Life 23:318) — spontaneous
  replicator generation from random opcode soups (~1e-4), then compaction.
  CITE-FOR-CONTEXT; uses instruction-set copy machinery. [verified]
- **Agüera y Arcas et al. 2024** (arXiv:2406.19108, "Computational Life",
  BFF) — self-replicators from random soups, no fitness landscape, even
  zero background mutation. PARALLEL; BFF has copy-between-heads primitive.
  [verified]
- **Knierim et al. 2026** (arXiv:2607.01483, BFF self-critique) — simple
  mutation random walks find replicators as fast as soup interaction;
  methodological-caution ally for census-over-anecdote. [verified]
- **Kruszewski & Mikolov 2020/21** (Artif. Life 27:277, combinatory
  chemistry) — emergent self-reproducing recursive expressions; duplication
  inherent in S/K calculus, no damage drive, no census. PARALLEL. [verified]
- **Fontana & Buss AlChemy** (already cited) — add the facet: they had to
  *ban copiers* (identity functions) to see organizations — mirror image of
  our "no copy primitive and none needed". [recalled]

### Loops, CA, repair

- **Chou & Reggia 1997** (Physica D 110:252) — self-replicating loops
  emerge from random densities under fixed uniform rules. PRIOR-ART for
  unseeded emergence in our A1/A4 spirit; rules hand-designed, copy by
  signal machinery. [verified] Counterpoint: **Lohn & Reggia 1997** — GA
  *search* over rule space (foil for census). [recalled]
- **Sayama 1999 evoloop; Salzberg, Antony & Sayama 2004; Sayama & Nehaniv
  2025 review** (Artif. Life 31:81) — structural dissolution (death/damage
  state) is what unfroze Langton loops and enabled evolution; collisions =
  variation source. PRIOR-ART for damage-as-enabler; no multiplication
  *from repair*. [verified]
- **Toom 1980; Gács 1986/2001** — eroder rules and 1-D reliable CA:
  minimal self-repair under continuous noise; majority/hierarchy-based, not
  damage-as-signal; nothing multiplies. PRIOR-ART sharpening our repair
  census novelty. [verified]
- **Cotler, Hongler & Hudcová 2025** (arXiv:2510.08342) — Turing-universal
  CA that cannot sustain nontrivial self-replication; formal separation of
  computation from replication. SUPPORTS. [verified]
- **Adams, Zenil, Davies & Walker 2017** (Sci. Rep. 7:997) — exhaustive
  small-CA enumeration against formal OEE predicates; closest
  methodological match to our census. PRIOR-ART (method). [verified]
- **Varetto 1993** (Typogenetics: "systematic constructive enumeration" of
  self-replicating strands); **Banzhaf 1993** (complete N=4 binary-string
  reaction network) — object-space censuses. PRIOR-ART (method, object
  space). [verified via secondary]

### Multiplication without a copy primitive

- **Pearson 1993** (Science 261:189) + **Lee et al. 1994** (Nature 369:215)
  — Gray–Scott spot division: replication as growth instability of a driven
  dissipative structure. PRIOR-ART (driver is feed/decay, not damage). [verified]
- **Zwicker et al. 2017** (Nat. Phys. 13:408, active droplets) — growth →
  shape instability → division; no informational copying. PRIOR-ART. [verified]
- **Mordvintsev et al. 2020** (Distill, Growing Neural CA) — damage-trained
  regenerating rule; planarian cut into three → three whole organisms.
  **Closest single precedent for damage-breeds-multiplication**; differences
  to state: gradient-trained rule (thousands of parameters) vs censused
  minimal rules; engineered demonstration vs unsearched-for corollary; no
  sustained wound drive or ecology. [verified]
- **Knowles et al. 2009** (Science 326:1533; prion fragmentation) — amyloid
  proliferation *because* filaments break: damage is the multiplication
  step. PRIOR-ART physical-world analogue. [recalled — verify before citing]
- **Ono & Ikegami 1999/2000** (JTB 206:243) — lattice protocells:
  membrane maintenance (repair) and division from the same metabolism.
  PARALLEL. [verified]

### Concept anchors

- **Kolchinsky & Wolpert 2018** (Interface Focus 8:20180041) — semantic
  information = syntactic correlation causally necessary for viability
  under counterfactual scrambling. Nearest formal neighbor of L5 (define
  the meaningful part by what its *use* changes). [verified]
- **Szathmáry & Gladkih 1989; Scheuring & Szathmáry 2001** — parabolic
  growth → survival-of-everybody (non-spatial coexistence); duplex decay =
  structural-dwell protection tipping selection outcomes. PRIOR-ART for
  L2-adjacent coexistence theory and an L4 antecedent. [verified]
- **Wilke, Wang, Ofria, Lenski & Adami 2001** (Nature 412:331, survival of
  the flattest). CITE-FOR-CONTEXT (error catastrophe phenomenology). [verified]
- **Dittrich & Speroni di Fenizio 2007** (chemical organization theory) —
  standard vocabulary for "self-maintaining configuration". [verified]
- **Andersen, Flamm, Merkle & Stadler** (MØD graph-grammar chemistry) —
  rewriting-as-chemistry toolkit; strategy-driven exhaustive network
  expansion as distant census cousin. [verified]
- Biology cluster for L1: **Rutherford & Lindquist 1998** (Hsp90
  capacitor); **Paaby & Rockman 2014** (cryptic variation); **Galhardo,
  Hastings & Rosenberg 2007** (stress-induced mutagenesis); **Lennon &
  Jones 2011** (microbial seed banks). [recalled]

## Sweep 3 — selection without fitness functions; execution-model theory

### Digital-evolution implicit fitness (L3)

- **Ray 1991** (Tierra) — CPU-time economy; the *time-slicing policy is a
  selection knob*: equal slices → parsimony pressure; size-proportional →
  pressure vanishes. What the scheduler contests determines what selection
  sees. PRIOR-ART for L3 and half of the shared-budget framing. [verified]
- **Ofria & Wilke 2004** (Artif. Life 10:191, Avida) — fitness =
  merit/gestation, gestation = instructions per offspring: events-per-
  outcome verbatim, but with per-organism virtual CPUs and an external
  merit scheduler. PRIOR-ART (L3). [verified]

### Asynchronous updating as physics (A3)

- **Huberman & Glance 1993** (PNAS 90:7716) — async updating erases
  Nowak–May spatial cooperation entirely. Canonical proof serialization
  flips an evolutionary outcome. SUPPORTS A3's load-bearing status. [verified]
- **Fatès 2014** (arXiv:1406.0792, guided tour of async CA; subsumes
  Schönfisch & de Roos 1999, Ingerson & Buvel 1984) — update discipline
  changes dynamics qualitatively; nobody treats the event budget as a
  *selective resource*. CITE-FOR-CONTEXT + confirms the gap. [verified]
- **Istrate, Marathe & Ravi 2008** (adversarial scheduling in evolutionary
  games) — scheduler as object of study, but robustness not selection.
  PARALLEL. [verified]
- **Ackley & Cannon 2011/2016** (Movable Feast Machine) — ALife substrate
  whose physics is a serialized random event stream; events free/uniform,
  never contested. PARALLEL. [verified]

### Stochastic-process precedents (A3, L2)

- **Ajmone Marsan, Conte & Balbo 1984** (ACM TOCS 2:93; + 1995 book) —
  **GSPN race semantics: weighted one-transition-per-event choice = our A3
  verbatim, published 1984**, with embedded-chain theory and the
  conflict-vs-concurrency distinction (non-conflicting rates don't affect
  untimed behavior) = L2's formal skeleton. PRIOR-ART. [verified]
- **Gillespie 1976/77** — SSA: one reaction per event, chosen by propensity
  share; jump chain depends only on shares. PRIOR-ART (execution model). [recalled]
- **Moran 1958** — one-event-at-a-time population model; uniform rate
  rescaling leaves the jump chain invariant (special case of L2). [recalled]
- **Danos/Feret/Fontana/Harmer/Krivine Kappa; Behr, Danos & Garnier 2020**
  (arXiv:2003.09395) — stochastic graph rewriting with CTMC semantics:
  activity = rate × embeddings, next event by share. The standard
  stochastic semantics for rule-based biology; our novelty is what is
  *derived* from the jump chain as sole clock. PRIOR-ART. [verified]
- **Freund 2005; Ibarra et al. 2004** — sequential-mode P systems (one
  rule per step) studied for computational power only, never selection.
  CITE-FOR-CONTEXT. [verified]
- **Bertram & Masel 2019** — when constant-relative-fitness descriptions
  are valid: absolute rate differences not affecting competitive share are
  invisible. Population genetics' own L2. SUPPORTS/PARALLEL. [verified]
- **Melbinger, Cremer & Frey 2010** (PRL 105:178101) — which traits
  selection sees depends on how the global constraint enters the event
  structure. SUPPORTS (L2). [verified]
- **Hindersin & Traulsen 2015** (PLoS Comput Biol 11:e1004437) — Bd vs dB
  microstructure of the single event flips amplifier/suppressor status of
  almost all graphs. SUPPORTS — selection lives in where the contest sits
  inside the event. [verified]
- **Hubbell 2001** — zero-sum ecological drift: strict shared event budget
  used to *assume away* selection. PRIOR-ART (budget), inverse use. [recalled]

### Residence/dwell (L4)

- **MacDonald, Gibbs & Pipkin 1968** (Biopolymers 6:1) — TASEP invented
  for ribosome traffic; slow sites queue upstream. PRIOR-ART (raw
  mechanism). [recalled]
- **Janowsky & Lebowitz 1992/94; Basu–Sidoravicius–Sly** — slow-bond TASEP
  density/current results. PARALLEL: TASEP is about conserved-particle
  currents; L4's chain (dwell → shielding from dwell-blind damage →
  heritable composition fixation) is not in that literature. [verified]
- **Balaban et al. 2004** (Science 305:1622, persisters) — slowness as
  protection from activity-targeting damage; wet-biology analogue. [recalled]
- **Codon-optimality foils** [recalled — VERIFY SIGNS BEFORE CITING]:
  ribosome shielding of mRNA (Deana & Belasco 2005) has L4's sign;
  Presnyak et al. 2015 (Cell) has the opposite (slow codons destabilize —
  damage process coupled to dwell sensing). L4's sign holds only when
  damage is dwell-blind; evolved systems can invert it.
- **Mills, Peterson & Spiegelman 1967** (Spiegelman's monster) — under a
  pure copy-rate clock the fast-processed wins; the clean foil to state
  which axiom flips L4's sign. [recalled]
- **Pross 2004/2011 (DKS); Liu et al. 2022** (Angew. Chem., out-of-
  equilibrium replicator competition) — persistence-as-fitness; the 2022
  experiment shows slow replicator wins in closed vial, reverses under
  flow: an empirical contested-clock switch. PARALLEL (L3/L4). [verified]

### Nonequilibrium physics & NESS current

- **England 2013/2015; Perunov, Marsland & England 2016** — dissipation
  bounds program; orthogonal mechanism; note 2024 critique
  arXiv:2404.01130. CITE-FOR-CONTEXT. [verified]
- **Leddy, Lu & Dinner 2018** (J. Chem. Phys. 149:224105) — steady-state
  relative fitness of competing replicators from path entropies inside a
  NESS. PARALLEL (closest formal fitness-free NESS work). [verified]
- **Andrae, Cremer, Reichenbach & Frey 2010** (PRL 104:218102) — entropy
  production of cyclic population games. PARTIAL PRIOR-ART (NESS
  certification, via EP not current). [recalled]
- **Li, Wang & Wang 2011 (PLoS ONE 6:e17888); Xu et al. 2021 (PNAS 118:
  e2103779118); Wang 2015 (Adv. Phys. 64:1)** — landscape-flux: steady-
  state probability flux computed for eco-evolutionary models
  (low-dimensional density spaces, equation-based). PARTIAL PRIOR-ART. [verified]
- **Wang, Xu & Zhou 2014** (Sci. Rep. 4:5830) — measured persistent
  cycling/currents in human RPS experiments. PARTIAL PRIOR-ART. [verified]

### Error catastrophe & rescue

- **Eigen 1971** — error threshold. PRIOR-ART (standard). [recalled]
- **Bull, Sanjuán & Wilke 2007** (J. Virol. 81:2930) — lethal mutagenesis
  vs error threshold distinction; needed to say which ours is. [recalled]
- **Anciaux, Lambert, Ronce, Roques & Martin 2019** (Evolution 73:1517) —
  **P(rescue) non-monotone in mutation rate, exactly**; optimal U;
  rescue-to-lethal-mutagenesis crossover. PRIOR-ART — must cite; reframe
  our result as substrate-level emergence of their prediction. [verified]
  Background: Gonzalez & Bell; Orr & Unckless 2008/2014. [recalled]

## Consolidated must-cite shortlist (all four sweeps)

Tier 1 — omitting these would be a priority/foil error:

A. Maynard Smith 1979 — the "parasites always win well-mixed" foil.
B. Szathmáry & Gladkih 1989 + Paczkó et al. 2024 — parabolic-growth
   rival explanation; cite AND exclude empirically.
C. Anciaux et al. 2019 — non-monotone rescue is their prediction.
D. Wallace 1975 — L2 is soft selection; cite as rediscovery.
E. Vasas, Szathmáry & Santos 2010 — the objection the whole program
   answers; anchor for L5.
F. Szathmáry & Demeter 1987 — stochastic corrector; night-11 baseline.
G. Bansho et al. 2016 — empirical bulk-death vs compartment-oscillation.
H. Boerlijst & Hogeweg 1991 — canonical no-compartment spatial rescue.
I. Takeuchi & Hogeweg 2009 + 2012 review — the exact night-11
   experiment in a replicase substrate + the map of the space.
J. Ikegami & Hashimoto 1995 — active mutation; closest L6-mechanism
   precedent, currently absent from bibliography.
K. Searcy & Nowicki 2005 — L6's frequency-dependent core is signaling
   theory; defensive cite.
L. Blokhuis et al. 2018 + 2020 — night-11 design parameters and the
   error-threshold-relaxation template.

Tier 2 — sweeps 1+3 ranked list (substrates, method, laws):

1. Anciaux et al. 2019 — non-monotone rescue is their published prediction.
2. Ajmone Marsan, Conte & Balbo 1984 (+1995) — A3 exists verbatim as GSPN
   race semantics; conflict/concurrency = L2's skeleton.
3. Hickinbotham, Stepney & Hogeweg 2021 — nearest ALife neighbor; the
   consensus L6 contradicts; reviewers will expect it.
4. Hutton 2002 (Squirm3) — damage-sustained evolution in a rewriting
   chemistry.
5. Takeuchi & Hogeweg 2009 + Colizzi & Hogeweg 2016 — the 2-D-needed
   consensus to triangulate the parasite phase against.
6. Mordvintsev et al. 2020 (Growing NCA) — closest damage-breeds-
   multiplication precedent; differentiate trained vs censused.
7. Adams, Zenil, Davies & Walker 2017 — exhaustive census precedent.
8. Agüera y Arcas et al. 2024 + Knierim et al. 2026 — headline
   "replicators from nothing" + its self-critique; census as the stricter
   alternative.
9. Huberman & Glance 1993 — serialization flips evolutionary outcomes.
10. Hindersin & Traulsen 2015 — event microstructure decides selection.
11. Bertram & Masel 2019 — popgen's own contested-rates statement.
12. MacDonald 1968 + Janowsky & Lebowitz 1992 — dwell-queue physics
    behind L4.
13. Sayama 1999 + Sayama & Nehaniv 2025 — damage as enabler of CA
    evolution.
14. Pearson 1993 / Lee 1994 / Zwicker 2017 — division without copying as
    driven instability.
15. Scheuring & Szathmáry 2001 (+ Szathmáry & Gladkih 1989) — non-spatial
    coexistence + dwell protection antecedents.
16. Kolchinsky & Wolpert 2018 — nearest formal neighbor of L5.
17. Li/Wang 2011 + Xu et al. 2021 — flux-based NESS certification
    precedent; scopes our "first in ALife" claim.
18. Fatès 2014 — situates the async axiom.
19. Pross 2004/2011 + Liu et al. 2022 — persistence-as-fitness in
    chemistry with the slow-wins regime switch.
20. Chou & Reggia 1997 (+ Lohn & Reggia 1997) — emergence under fixed
    uniform rules; search-vs-census contrast.

## Sweep 2 — replicator–parasite–compartment theory

### A. Foundations

- **Eigen 1971** (Naturwissenschaften 58:465) — quasispecies, error
  threshold; his *constant organization* constraint (only relative rates
  matter in a size-constrained population) is the classical form of L2.
- **Eigen & Schuster 1977/78** — hypercycle; the target the parasite
  literature attacks. **Maynard Smith 1979** (Nature 280:445) — a
  parasite invades any well-mixed hypercycle. **The stated foil for our
  coexistence claim.** [verified citations]
- **Szathmáry & Maynard Smith 1995** (Nature 374:227) — major
  transitions; limited/unlimited heredity = standard vocabulary for L5
  (timing-only codons are non-heritable variation in their sense).
- **Bull, Sanjuán & Wilke 2007** — our error catastrophe is closer to
  lethal mutagenesis (death criterion) than Eigen's information
  threshold; cite to pre-empt terminology objection.

### B. Spatial self-organization rescues hosts (no compartments needed)

- **Boerlijst & Hogeweg 1991** (Physica D 48:17) — 2-D spiral waves make
  hypercycles parasite-resistant. Canonical no-compartment rescue; must
  show our bare ring is not a degenerate case. [verified]
- **Boerlijst, Lamers & Hogeweg 1993** — spatial organization selects
  for *reduced* virulence; the standard virulence axis for night 11.
- **Cronhjort 1995** (OLEB 25) — CA vs PDE versions differ fundamentally
  in parasite resistance; dimension- and substrate-dependence cuts both
  ways (defends 1-D as non-implied; invites the covert-structure
  objection). [verified]
- **Takeuchi & Hogeweg 2009** (PLoS CB 5:e1000542) — **head-to-head
  compartments vs spatial self-organization**: both stabilize via
  multilevel selection but drive opposite trends (wave fecundity vs
  vesicle longevity); compartments fail below a division-volume
  threshold (assortment load); sharp fittest→flattest transition in
  mutation rate. **The exact experiment night 11 proposes, in a
  replicase substrate.** [verified] (+ Hogeweg & Takeuchi 2003, part I.)
- **Takeuchi & Hogeweg 2012** (Phys. Life Rev. 9:219) — review mapping
  the whole comparison space; highest coverage per citation; its
  "information storage in dedicated templates" section is L5's home.
- **Takeuchi & Hogeweg 2008** (Biol. Direct 3:11) — parasites *promote*
  diversity (niche creation), system stabilizes upon parasite evolution
  — given pattern formation. PARALLEL.
- **Colizzi & Hogeweg 2016** (PLoS CB 12:e1004902) — parasites as "a
  degree of freedom … to enhance the evolvability of replicators";
  compartments declared unnecessary. Closest evolvability statement,
  but **opposite causal arrow**: parasite→empty space→host adaptation
  (disorder-fueled) vs our order-fueled. [verified]
- **Szabó, Scheuring, Czárán & Szathmáry 2002** (Nature 420:340) —
  limited dispersal shifts the selective optimum toward fidelity.
- **Czárán, Könnyű & Szathmáry 2015** (JTB 381:39, MCRS) — metabolic
  coupling + surface = another non-compartment coexistence route.

### C. Compartments beat parasites (stochastic corrector, transient comp.)

- **Szathmáry & Demeter 1987** (JTB 128:463) — **stochastic corrector**:
  stochastic assortment at division generates between-compartment
  variance; vesicle-level selection maintains what within-vesicle
  competition destroys. The compartment baseline for night 11.
  (+ Grey, Hutson & Szathmáry 1995 for formal boundary conditions.)
- **Matsumura et al. 2016** (Science 354:1293) — **transient**
  compartmentalization suffices (no evolved division machinery); TC
  selects ensembles incl. "a diversity of parasites that could serve as
  a source of opportunistic functionality" — independent support for
  parasites-as-evolvability. [verified]
- **Blokhuis, Lacoste, Nghe & Peliti 2018** (PRL 120:158101) — two
  control parameters: **relative amplification of the parasite** and
  **compartment size**. Night-11's sweep axes, verbatim. [verified]
- **Blokhuis et al. 2020** (JTB 487:110110) — diffusion-limited
  (asynchronous, high variance) vs replication-limited (synchronous,
  low variance) regimes; phase boundary in (relative growth,
  inoculation size, mutation rate); **TC relaxes the classical error
  threshold** — the headline shape night 11 could target. [verified]
- **Laurent, Peliti & Lacoste 2019** (Life 9:78) — minimal replicase +
  parasite under TC: escapes error catastrophe **and has a sustained-
  oscillation regime** — permanent host-parasite oscillation exists in
  a minimal model, but under TC with pooling, not on a bare ring.
- **Szilágyi et al. 2017** (Life 7:48) — review scoring model families
  on three criteria (information maintenance, ecological stability,
  evolutionary stability); adoptable scoring for our substrate.
- **Ono & Ikegami 2000** (JTB 206:243) — **the only work where the
  compartment wall is paid for by the system's own chemistry** — our
  exact situation (walls from the same event budget); they never test
  parasites. [verified]

### D. Experimental host-parasite replicator ecology (Ichihashi group)

- **Bansho et al. 2016** (PNAS 113:4045) — **bulk ⇒ parasite eradicates
  host; compartments ⇒ continuous oscillation** whose shape shifts as
  the host evolves. The sharpest empirical contrast: we claim bulk-like
  geometry giving the compartment-like outcome. [verified]
- **Furubayashi et al. 2020** (eLife 9:e56038) — clonal host →
  host-parasite ecosystem with arms race; parasitic RNA "adding a new
  genetic variation to the whole replicator ensemble". SUPPORTS L6's
  evolvability half. [verified]
- **Mizuuchi, Furubayashi & Ichihashi 2022** (Nat. Commun. 13:1460) —
  five-lineage network, frequencies "initially fluctuate and gradually
  stabilize" — empirical analogue of our stationary density band.
- **Kamiura, Mizuuchi & Ichihashi 2022** (PLoS CB 18:e1010709) — H →
  HP → HHP complexification route; parasites create niches.
- **Kanai & Ichihashi 2026** (MBE 43) — replicate populations under
  high/low parasite load: parasites accelerate between-population
  divergence, constrain within-population diversification. Cleanest
  design template (replicate seeds = replicate populations). [verified]

### E. Non-spatial non-compartment coexistence — RIVAL EXPLANATIONS

- **Szathmáry & Gladkih 1989** (JTB 138:55) + **Paczkó, Szathmáry &
  Szilágyi 2024** (eLife 13:e93208) — **parabolic growth ⇒ "survival of
  everybody"**: permanent coexistence, well-mixed, no compartments; the
  2024 paper does it stochastically at constant population size (close
  to our ring) and *also relaxes the error threshold*. **THE
  highest-risk objection to our coexistence claim**: our shared event
  budget makes per-type event rates sub-linear in abundance — a
  reviewer will ask if our coexistence is parabolic-growth coexistence
  in disguise. Must measure the effective growth exponent and exclude
  (or reframe). [verified]
- **Ray 1991/92 (Tierra)** — 1-D soup, no compartments, parasites +
  hyperparasites, Lotka–Volterra oscillations sustained long-term. The
  closest existing "1-D no-compartment coexistence"; distinguish in one
  paragraph: Tierra has explicit copy loop, per-organism CPU slices,
  mutation operator, lineage tags — we have none. [recalled]
- **Pirovino et al. 2025** (PLoS CB 21:e1012162) — well-mixed taming of
  parasites by *hyperparasites*; "integration of parasites into the
  host habitat rather than their separation" — philosophically aligned,
  mechanistically different (third catalytic tier). [verified]

### F. Parasites raising complexity/evolvability

- **Zaman, Meyer, Devangam, Bryson, Lenski & Ofria 2014** (PLoS Biol.
  12:e1002023) — Avida coevolution: parasites drive complexity AND
  host evolvability. Strongest quantitative precedent; L6 differs by
  naming the *condition* (order-fueled) and lacking a mutation
  operator. [verified]
- **Ikegami & Hashimoto 1995** (Artif. Life 2:305) — "**active
  mutation**": machines rewrite tapes, generating diversity
  endogenously without an imposed mutation operator; host/parasite-like
  roles. **Closest existing notion of machinery-writes-wrong-copies as
  endogenous variation** — our deceptive codon without the
  order-fueling analysis. Currently absent from our bibliography; cite.
- **Sayama 2004** (Artif. Life 10:83) — self-protection maintains
  diversity in replicating CA. Context.
- **Vimal, Mathis, Weimer & Forrest 2025** (arXiv:2509.03534) — AlChemy
  line active again: endogenous selection, no external fitness
  function. [verified]

### G. Heredity & contested rates (L5, L2) in this literature

- **Takeuchi, Hogeweg & Koonin 2011** (PLoS CB 7:e1002024) — dedicated
  templates evolve; DNA's advantage = *parasite resistance*, cost =
  slower cycle. SUPPORTS L5. [verified]
- **Takeuchi & Kaneko 2019** (Proc. R. Soc. B 286:20191359) +
  **2025** (Phil. Trans. B 380:20240296) — read/write (informatic)
  asymmetry emerges from multilevel conflict; the current framing L5
  will be compared against. They explain its *origin* under
  compartments; we use it as an operational criterion without.
- **Takeuchi, Kaneko & Hogeweg 2017** (Nat. Commun. 8:250) —
  germline/soma symmetry break: low-copy-number "genome" strand
  suppresses selfishness via drift; works only at intermediate cell
  size. **The night-11 second-row design, with a transplanted testable
  prediction.** [verified]
- **Takeuchi, Kaneko & Hogeweg 2016** (Proc. R. Soc. B 283:20153109) —
  "evolutionarily stable disequilibrium": stationary aggregate hides
  endless per-lineage oscillation — published precedent for our
  aggregation trap; also a methodological warning for the parasite
  band. [verified]
- **Vasas, Szathmáry & Santos 2010** (PNAS 107:1470) — **the standard
  argument that systems without template copying cannot evolve**
  (composomes lack evolvability). The explicit objection our whole
  program answers; citing it converts the no-copy-primitive axiom from
  oddity into positioned claim. **L5 is best framed as the answer to
  this paper.** (+ Vasas et al. 2012 "Evolution before genes" as the
  sympathetic precedent: attractor-based limited heredity — our
  seed-bank heredity's genus.) [verified]
- **Wallace 1975** (Evolution 29:465) — **soft selection**: fitness
  differences matter only relative to competitors in a shared
  density-constrained arena. **L2 is soft selection restated for a
  shared event budget — cite as rediscovery**; the novel part is the
  operational test (uncontested differences provably bit-identical,
  not merely weakly selected).
- **Searcy & Nowicki 2005** (*The Evolution of Animal Communication*)
  — deception persists only at frequencies where receivers still
  profit; self-limiting, stabilizes at intermediate-low frequency
  (also Batesian mimicry). **L6's frequency-dependent core is textbook
  signaling theory** — cite it, claim the substrate-level instantiation
  (no signaler/receiver agents, no fitness function) + the
  order/disorder dichotomy + the no-mutation-operator corollary.

### Sweep-2 verdicts

**Parasite coexistence**: not novel as phenomenon class; plausibly novel
as mechanism + substrate. Already known routes to permanent coexistence:
2-D spatial self-organization, compartments (theory + experiment),
hyperparasite tiers, **parabolic growth (incl. stochastic constant-N,
Paczkó 2024)**, and Tierra's 1-D oscillatory version. Genuinely
unclaimed: (a) no copy primitive/replicase/mutation operator/fitness
function, frozen table, parasite = one-character rule edit; (b) the
**fuel coupling** (parasite expression conditioned on the order it
destroys) as the stabilizing negative feedback — distinct from refuges,
group variance, density kinetics, and third tiers; (c) robustness at
ALL damage rates = a phase, not a tuned window. **Three required
defenses**: (1) measure effective growth exponent vs abundance to
exclude parabolic-growth-in-disguise — highest risk; (2) rule out /
quantify covert spatial structure on the ring (fronts, clusters);
(3) the explicit Tierra paragraph.

**L6**: novel as a stated law in the replicator/artificial-chemistry
literature (nobody frames parasite persistence as conditional on
host-generated order; Colizzi & Hogeweg have the mirror arrow). NOT
novel as a general principle — it is frequency-dependent deception from
signaling theory. Claim: substrate instantiation + the discriminating
dichotomy (order-fueled persists, disorder-fueled starves) + standing
variation with no mutation operator anywhere in the axioms.

**L5**: sharper operational restatement of informatic asymmetry
(Takeuchi–Kaneko) + limited/unlimited heredity (Szathmáry–Maynard
Smith); position as the answer to Vasas et al. 2010. Novel as a
criterion, not as an intuition.

**L2**: substantially a rediscovery (Wallace 1975 soft selection; Eigen
constant organization; flip side of parabolic coexistence). Demote to:
"the single-shared-event-budget substrate makes soft selection *exact*
and directly provable — uncontested rate differences are bit-identical,
not merely weak." Credibility gained exceeds novelty lost.

### Night-11 design brief (compartments vs the order-fueled parasite)

**EXECUTED 2026-08-23** (night11.py, night11-results.md; 912 runs
exact). Outcome: the ranked new-claim #3 (L6 inversion) LANDED —
compartments never suppress the parasite (flat at m=8), and at
collapse RAISE it (+0.054/+0.058, t≈8–12, dose-response in K), via
commons rescue (tape +56–58%) whose order/matter is parasite fuel;
the group-selection differential cov(contribution, ρ) is POSITIVE
at m=2 (t up to 18, 24/24 seeds) — classical TC selection favors
infection because the parasite is a matter-benefactor. Night law:
"group selection cannot suppress a parasite that pays its rent" —
the classical suppression result is the special case of positive
virulence. Claim #1 (Price partition) realized as the measured
S = ρ̄_w − ρ̄ differential; claims #2 (budget-priced walls) and the
germline/soma arm remain open follow-ups.

What the literature knows: (1) variance generation, not isolation, is
the mechanism (stochastic corrector); (2) compartment size has an
interior optimum (assortment load at small n, parasite ubiquity at
large n — Blokhuis 2018, Takeuchi & Hogeweg 2009); (3) compartments
may be transient (Matsumura 2016); (4) growth asynchrony determines
usable variance (Blokhuis 2020) — our asynchronous event budget
predicts the high-variance regime, verify don't assert; (5) space and
compartments drive opposite long-term trends; (6) compartments create
within-compartment selfishness, resolved by germline/soma symmetry
breaking at intermediate size (Takeuchi 2017/2019); (7) compartment-
level selection lowers realized virulence (Boerlijst 1993);
(8) empirically: bulk death vs compartment oscillation (Bansho 2016).
**Everything above assumes a replicase/copy primitive, a mutation-rate
parameter, and FREE compartments. Sole exception on cost: Ono &
Ikegami 2000 (self-paid membrane), who never test parasites.**

What would be NEW (ranked):
1. **Group selection without replicators** — a Price-style
   between/within-group decomposition favouring the host in a substrate
   with no copy primitive/fitness/mutation/lineage. Extends multilevel
   selection to non-replicators; answers Vasas 2010 directly.
2. **Compartments with an explicit budget price** — walls paid from the
   same event budget; publish the cost curve (wall-maintenance events
   vs parasite suppression + survival gained). Unmodelled anywhere.
3. **The inversion result if it happens**: L6 predicts compartments
   (more local order, longer runs, less mixing) may *feed* the
   order-fueled parasite while suppressing the disorder-fueled mutator
   — a direct contradiction of the field's default expectation and the
   sharpest available confirmation of L6. Design so this outcome is
   measurable, not conflated with failure.
4. **Error-threshold relaxation** (Blokhuis 2020's headline shape) in a
   copy-primitive-free substrate.

Sweep axes (adopt Blokhuis's verbatim): compartment size n (predict
non-monotone survival) × relative amplification a (deceptive/honest
event-rate ratio, measured = virulence axis); secondary: mixing period
T_mix (predict survival window), damage m (predict max benefit at
intermediate m), inoculation size. Report on the (n, a) plane to
overlay published phase boundaries.

Quantities: Price-equation partition of parasite-frequency change
(between vs within compartments — "compartments win iff between-group
covariance exceeds within-group"); between-compartment variance in
parasite fraction at each mixing event; asynchronous-vs-synchronous
growth regime check; assortment load (fraction of fresh compartments
with zero honest codons) explaining the small-n arm; realized virulence
over time (frozen table ⇒ no within-run virulence evolution — state
explicitly why Boerlijst-style attenuation is absent; add a
strain-competition arm with several table strengths as the honest
virulence-evolution analogue); stationary band per n; P(extinction)
per unit time.

Controls (each closes a named objection): (1) 2-D without walls —
essential, isolates dimensionality (Boerlijst/Colizzi); (2) sham
permeable walls — isolation vs cost/presence; (3) inert-symbol budget
control — budget drain vs compartmentalization; (4) matched-N 1-D ring
— population-size effects (defeats Paczkó-style N-dependence);
(5) no-parasite arm at every (n, T_mix) — pure wall cost; (6) replicate
seeds reported per-seed (Kanai & Ichihashi design; our aggregation
trap; Takeuchi 2016 as published precedent for stationary-aggregate-
hides-oscillation); (7) germline/soma second-row variant as a separate
arm from walls — different mechanism (drift-mediated), transplanted
prediction: works only at intermediate size.

## Sweep 4 — field map & venues

### Field map (who's who for minimal-substrate evolution, 2020–2026)

- **Hogeweg (Utrecht) / Takeuchi (now U. Auckland)** — spatial RNA-world
  replicator–parasite models, multilevel selection, compartments vs
  spatial self-organization. Closest thematic neighbors to the parasite
  phase. [verified]
- **Stepney & Hickinbotham (York)** — Stringmol; "What is a Parasite?"
  (ALIFE 2021); OEE detection work. Second-closest. [verified]
- **Sayama (Binghamton)** — Swarm Chemistry; Hash Chemistry as
  "minimalistic open-ended evolutionary system" (arXiv 2404.18027,
  2412.12790) — directly comparable minimal-substrate OEE. [verified]
- **Agüera y Arcas et al. (Google Paradigms of Intelligence)** —
  Computational Life / BFF (arXiv 2406.19108) + book *What Is Life?*;
  made "computational origin of life" a visible subfield. Our
  "no copy primitive in the axioms" framing speaks directly to this
  audience. [verified]
- **Adami & Ofria (MSU)** — Avida lineage. **Ikegami (Tokyo)** — massive
  ALife/autonomy. **Bert Wang-Chak Chan** — Lenia; was an *independent
  researcher* through the Lenia papers → ISAL Outstanding Publication
  2019 → Google; the field's flagship hobbyist success story and a
  direct template. [verified]
- **Sakana/MIT/OpenAI (ASAL, Artif. Life 31(3) 2025)** — foundation-model
  search for ALife; industrial energy entering the field. **Inria Flowers**
  — Flow-Lenia, curiosity-driven exploration. **Cross Labs (Witkowski,
  Kyoto)** — indie-friendly lab, Cross Roads talk series. **Levin (Tufts)**
  — adjacent (basal cognition). [verified/recalled mix]
- **OEE community (Taylor, Packard, Bedau, Channon, Standish)** —
  Artificial Life special issues 2016/2019/**2024 (30(3), Channon, Bedau,
  Packard, Taylor)** = institutional successor to Bedau et al. 2000 "Open
  Problems"; no standalone "Open Problems 2.0" exists as of 2026-08.
  [verified]

### Venue assessment (condensed; full details from sweep, marks preserved)

- **Artificial Life (MIT Press)** — flagship, excellent fit. Article
  6,000–12,000 words. **Explicit "Independent and new researchers"
  track**: one-page extended abstract in the cover letter answering 8
  questions (scope fit; research question; recent ALife work built on;
  novelty vs prior ALife work; why ALife-relevant rather than
  out-of-scope AI; method; results; who benefits) — applies when all
  authors are independent with no prior ALife-venue publication.
  [verified] $0 via subscription route (OA optional, ~US$1,350 dated
  figure). ORCID mandatory per author; data/code availability expected
  (our replayable event logs are a strong asset). Final format
  LaTeX/Word — **OpTeX not accepted; conversion cost at acceptance**.
  [verified] Regular ArtL articles are auto-accepted as orals at the
  next ALIFE conference. [verified for 2026]
- **ALIFE 2027 conference — PRAGUE, July 19–23, 2027** (2027.alife.org).
  Full papers 3–8 pages, MIT Press OA proceedings with DOI, $0
  publication; registration required (~US$300–600 typical [recalled]).
  Expected deadline ~late March 2027 (2026 cycle: Mar 30 → Apr 12,
  notification Jun 7). In the author's country — travel barrier gone.
  [verified]
- **Complex Systems (Wolfram, ed. Zenil)** — good fit ("simple
  components, complex behavior"); **$0 platinum OA, CC BY, no fees**;
  published then-independent Chan's Lenia (28(3), 2019). Lower
  visibility (IF ~1.2). [verified]
- **PLOS Computational Biology / PLOS Complex Systems** — good fit
  (Utrecht lineage publishes in PLOS CB); APC ~US$3,000+ with a formal
  fee-assistance/waiver program (apply at submission; discretionary for
  an unfunded Czech hobbyist). [verified program exists]
- **Physical Review E** — moderate fit (needs stat-phys framing: NESS
  currents, phase transitions); $0 subscription route; "inability to
  pay will not prevent publication". [verified]
- **J. R. Soc. Interface** — moderate; waivers not automatic for
  Czechia. **JTB/OLEB** — $0 subscription routes [recalled]. **Entropy
  (MDPI)** — APC ~CHF 2,600. **Adaptive Behavior** — weak fit.
- **arXiv** — endorsement needed per domain (nlin.AO / q-bio.PE /
  cs.NE); **as of Jan 21, 2026 institutional email no longer
  sufficient — unaffiliated authors must find an endorser who is an
  active arXiv author in that domain** (check "Which of these authors
  are endorsers?" on abstract pages of cited papers). [verified]
  **arXiv requires TeX source for TeX-produced papers and its pipeline
  may not process OpTeX/LuaTeX plain formats** [recalled — verify].
  Zenodo already provides the citable DOI, so arXiv is optional
  garnish, not infrastructure.

### The AI-co-authorship caveat (applies everywhere)

The Zenodo/GitHub release lists Claude (AI) as co-author. **Every
realistic peer-review venue prohibits AI authors**: MIT Press (governs
both ArtL and ISAL proceedings) [verified], PLOS/COPE [verified],
arXiv (2023 policy: "a computer program cannot… agree to arXiv's
terms") [verified], Elsevier/Springer/MDPI/SAGE [verified at publisher
level]. Consequence for any submission: human sole author; AI
contribution declared in (i) cover letter and (ii) a
Methods/Acknowledgments statement naming tool, version, and role.
The CC0 Zenodo record keeps its author line as-is (outside journal
jurisdiction), but the cover letter should proactively note the
difference so it reads as transparency, not inconsistency. Second
independent blocker at ArtL: ORCID required per author; an AI cannot
hold one. CC0 itself is not a blocker anywhere found (it maximally
permits relicensing); only [recalled] gray zone: a subscription
publisher wanting exclusivity over already-public-domain text —
disclose and let the editor rule.

### Recommendation (venue decision = user's, M8)

1. **ALIFE 2027 Prague as first target** — $0 publication, in-country,
   8-page limit forces the strongest-claims condensation, most
   independent-researcher-friendly community in science, comfortable
   runway (~March 2027 deadline).
2. **Artificial Life journal as the full-length home** — purpose-built
   independent-researcher on-ramp; frame the 8-question abstract around:
   Agüera y Arcas 2024 (emergence without fitness functions but *with*
   copy-capable instruction set), Takeuchi/Hogeweg + Stepney/
   Hickinbotham (parasite coexistence but in substrates with built-in
   replication), Sayama Hash Chemistry (minimalism). Q5 answer = the six
   substrate-free laws. Standard practice: extend the conference paper
   into the journal Article; say so in the cover letter.
3. **Complex Systems as $0 fallback** — Lenia precedent, tolerant of
   unconventional papers, lower visibility.

### Community entry points

- **ERA — Emerging Researchers in ALife** (alife.org/
  emerging-researchers-in-alife) — explicitly includes "independent
  scholar"; membership = joining their Discord. Best first door.
  [verified]
- **ALife Newsletter** (alife-newsletter.github.io/Newsletter) —
  bi-monthly, solicits short write-ups of recent work — realistic
  near-term way to put the Subtraction Ladder in front of the community
  without peer review. Mastodon @alifenewsletter@fediscience.org.
  [verified]
- **ISAL (alife.org)** — membership: journal archive access + ALIFE
  registration discount; fee roughly tens of USD/yr [recalled].
  **ISAL Discord** via ALife Newsletter ed. 16. [verified]
- **Cross Labs "Cross Roads"** — has hosted independent researchers
  (Chan). [verified precedent]
- **arXiv-endorsement / feedback allies**: Sayama, Hickinbotham/Stepney,
  Flow-Lenia authors, arXiv 2406.19108 authors — check endorser status
  per person. [verified arXiv presence]
