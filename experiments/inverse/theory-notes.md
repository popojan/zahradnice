# Theory notes (written while the author proofreads v2)

Derivations and probe results feeding paper v3. Probes:
`night12_probes.py` (+ inline fine-sampling variant, reproduced
below), data `night12_language.csv`.

## 1. L4 derived: equilibrium composition = fixed point of the residence map

Setting: tape-world stationarity. Deaths (pokes) remove visible
genes composition-uniformly. Births (repairs) write the gene the
machinery covers; decompose by where that covered value came from:

- channel (a), freshly inherited: the head picked the gene up at
  the hole's west flank an instant earlier — the written value is
  composition-distributed, contributing x_s per birth;
- channel (b), carried: the value rode through the head's dwell
  (or reseeds the world after deep collapse) — the written value is
  residence-distributed, contributing R_s(x) per birth.

With λ ∈ (0,1] the channel-(b) share and birth flux balancing
death flux (stationary tape), the composition equation is

    d(x_s)/dt ∝ λ R_s(x) + (1−λ) x_s − x_s  =  λ (R_s(x) − x_s),

so for ANY λ>0 the equilibrium is

    x* = R_s(x*)  — the fixed point of the residence map,

independent of the channel mix. The channel weights, which section
9.3 of v2 flagged as underived, CANCEL. What remains substrate-side
is only: deaths uniform over visible matter; births
machinery-covered; mean-field evaluation of R at prevailing x.

Verification (all measured cells, night 9-B):

| cell | R (residence) | x (share) | |R−x| |
|---|---|---|---|
| dwell 2, m=8 | 0.55 | 0.52 | 0.03 |
| dwell 3, m=8 | 0.68 | 0.69 | 0.01 |
| dwell 2, m=2 | 0.62 | 0.62 | 0.00 |
| dwell 3, m=2 | 0.69 | 0.69 | 0.00 |

v3 action: upgrade §9.3 from "measured, decomposed, not derived"
to this derivation; the open item shrinks to deriving R itself
(the residence map's shape) from dwell and damage rate.

## 2. L2 as a proposition about critical pairs

Proposition (schedule invisibility). In a weighted stochastic
rewriting system, suppose that between consecutive external events
(i) every pair of enabled rule instances is non-overlapping (no
shared cells — hence no critical pairs), and (ii) each inter-event
phase normalizes in finitely many applications. Then the state at
every external-event boundary is independent of the rule weights:
non-overlapping applications commute, so by Newman's lemma the
inter-event normal form is unique, and weights can only permute
the path to it. Corollary: any outcome functional is
weight-invariant — selection cannot act. Conversely, weight
sensitivity requires overlapping redexes (a genuine critical
pair), i.e. two processes contesting the same cells.

Measured instance of the hypothesis-side: night 9-D uncontested
arms, bit-identical outcomes across handicaps (every wound heals
before the next lands = inter-event normalization; single claimant
per wound = no critical pairs). Measured instance of the
converse: the contested arm's 24/24. Night 4's mover/handler
dichotomy is the same statement with the mover as a persistent
critical pair (heads contest cells at every event) and the
handler as a critical-pair-free rule.

v3 action: add to §9 (theory) + one sentence in related work
(semi-Thue framing; the L2 proof idea is rewriting-theoretic).

## 3. Probe P1: the stationary language sits above order-1 Markov

Question (from the v2 discussion): is the parasite phase's
stationary word distribution finite-order-Markov ("rational"), or
does the phenomenon climb the weighted-language hierarchy?
Method: 32 seeds x {para, paraonly} x m {8,4}, ring 24, final-half
samples; run-length histograms vs the geometric null at measured
rho; connected correlation C(d) vs the order-1 Markov prediction
(1−2 rho)^d.

Results, consistent across all four cells:

- run lengths: singletons suppressed (e.g. 0.27 observed vs 0.34
  geometric), length-2 runs enriched (0.27 vs 0.23) — the
  pair-codon writes wrong copies IN PAIRS and the stationary word
  keeps that signature. The language remembers its grammar.
- correlations: C(1) matches Markov by construction, then the
  measured C(d) collapses far faster and turns NEGATIVE around
  d = 3–5 (deepest −0.157 at paraonly m=4). An order-1 Markov
  measure has C(d) = (1−2 rho)^d ≥ 0 for rho<1/2, so the phase is
  PROVABLY not order-1. The negative lobe means liquid-like
  short-range order with a characteristic domain scale (~2–3
  cells) set by pair-writing against coarsening.

Verdict: the parasite phase climbs at least one level of the
hierarchy, and the climb is mechanistic — the codon's write
signature is recoverable from stationary word statistics alone.

## 4. Probe P2: the circulating current exists — under the sampling grid

At the paper's standard 50-apply sampling, time-reversal asymmetry
of (rho, run-length) is null (|t| < 0.8 in 10 of 12 cells) — and
that null was an aliasing artifact, in a rhyme with the arc's
absorbing-state lesson. Resampling every 5 applies, in the
(rho, tape) plane, m=4, 32 seeds:

    para:      A(tau=1) t = −10.5;  decays to n.s. by tau≈8 (40 applies)
    paraonly:  A(tau=1) t = −9.3;   REVERSES: +2.4 at tau=4,
               +5.0 at tau=8, +5.2 at tau=16

Detailed balance is decisively violated: the parasite phase is a
genuine non-equilibrium steady state with measurable circulating
probability current. paraonly shows two nested, counter-rotating
loops at different timescales (fast poke-repair micro-cycle;
slow order-build/corruption macro-cycle); adding the honest codon
(para) suppresses the slow loop. A reversible (detailed-balance)
grammar cannot have a parasite phase of this kind.

v3 actions: replace "stochastic limit cycle" with the measured
current (numbers above); add the aliasing caveat to the methods
lessons; the two-timescale structure is a new open observable
(period estimation needs finer, longer series).

## 5. v3 edit queue (accumulated during proofreading)

1. Abstinence sentence sharpened: the law has NO VARIABLES — every
   write is a law-constant; copying must be assembled as an
   alphabet case-split carried through matter (Ω(alphabet) rules +
   a carrier state), which is why one-symbol edits yield
   systematic miscopying (night 10's premise).
2. Semi-Thue framing paragraph (related work): 1-D worlds =
   stochastic rewriting on circular words; walls = end markers;
   the mapping breaks at 2-D (graph rewriting) — scope marker.
3. §9.3: L4 upgraded to the fixed-point derivation (item 1 above).
4. §9 addition: the critical-pair proposition (item 2 above).
5. Movement IV + honest limits: current measured, aliasing lesson
   (item 4 above); language-order result (item 3) as a short
   subsection or note.
6. "Two rules, read slowly" STAYS (author's decision).
