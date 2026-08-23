# EW-5 — the self-reproduction kernel (F4, the description rung live)

Date: 2026-08-23, session 10. Registrations: ew-design.md §EW-5
(P5-1..4 + Amendment 7, all pre-sweep). Driver: ew5.py; data:
ew5_runs.csv (600 runs, zero exactness failures). Verdict up front:
**a machine system that maintains itself by translating a matter
description that encodes the machinery — the translator included —
outlives every ablation of the loop.** Constructed machines are
live the moment they are written; the standing machinery at the end
of a kernel run is ~26 population-turnovers away from the seeded
machines, every generation flowing through the description.

## Setup

ROWS=6: tape / fuel (idle) / CODE / machinery / regulatory. The
translator Ω shares the machinery row with copiers under the same
exclusion, reading the code row above ((−1,0)) while copiers read
the regulatory row below ((+1,0)) — message and genome. EXECUTE:
read codon, build its product east into emptiness, land beyond it
(codon b → Π, codon w → Ω, the self-reference); DRIFT at weight
0.1 keeps convoys deadlock-free. Both machine types decay
(ε_d 0.005); nothing else builds machines — homeostasis flows
only through translation. Description: b codons at even cols,
w at 0/6/12/18; seeds 8 Π + 4 Ω at codon+1. Uniform-α matter,
EW-4's wound economy (cad 4, M 5, EST 200, BLOCKS 200), byte q =
one description wound. 100 seeds/arm.

## Results

| arm | survived | built Π / Ω (mean) | final machinery Π / Ω | final codons |
|---|---|---|---|---|
| kernel | **77/100** | 222 / 93 | 13.2 / 5.0 | 12.0 |
| no-executor | 0/100 | 0 / 0 | 0.0 / 0.0 | 12.0 |
| no-w | 10/100 | 47 / 0 | 0.4 / 0.0 | 12.0 |
| q16 | 8/100 | 125 / 58 | 0.2 / 0.0 | 0.0 |
| q8 | 0/100 | 87 / 37 | 0.0 / 0.0 | 0.0 |
| q4 | 1/100 | 65 / 26 | 0.0 / 0.0 | 0.0 |

- **P5-1 HELD**: the kernel reaches machinery turnover steady state
  — 315 constructions per run against 12 seeded machines and
  ~equal decays; final machinery (18.2) exceeds the seed count;
  77% of worlds alive at a horizon where every other configuration
  is dead or dying. Rebuild-into-emptiness places machines exactly
  where death made room.
- **P5-2 HELD exactly**: without an executor the description is
  inert matter — zero constructions in 100 runs, machinery decays
  to nothing, the world dies (EW-4's faithful endgame, now with
  the recipe for salvation written above it and nothing able to
  read it). The seed constructor is irreducible — von Neumann's
  given.
- **P5-3 HELD, the kernel claim**: survival ordering 77 > 10 > 0.
  The kernel and no-w arms differ in ONE codon type: whether the
  description encodes the translator itself. Without w, translators
  decay unreplaced, rebuild capacity is transient (47 Π built while
  they lasted, then collapse). The self-reference codon is worth 67
  points of survival: machinery that rebuilds its rebuilder
  outlasts machinery that does not.
- **P5-4 HELD directionally, with the registered saturation
  caveat**: all three description-wound doses collapse survival
  (8/0/1 vs 77) because uniform erasure of a 12-codon description
  saturates fast — the dose is effectively the description's time
  of death, and the graded signal shows in lifetime construction
  counts, monotone in dose (125 / 87 / 65). Every lost codon is a
  permanent machinery hole; D-repair (description replication,
  EW-6) is the registered next increment. Note the q16 arm builds
  MORE than no-w despite dying almost as often — machinery health
  tracks the description's lifespan, not its own.

## What the kernel closes, and what it does not

Closed: the full loop machinery→(reads matter)→machinery, with all
three earned channels inherited — the description is inherited by
machinery (EW-1/3 copiers stamp the genome), mutable by machinery
(EW-4), and its execution is a matter economy (EW-2's pricing
applies unchanged, idle here). The world's machine population is
now a PHENOTYPE of a matter string: change the string (q wounds,
no-w) and the machinery, the law inheritance it powers, and the
world's survival change with it.

Not closed, stated plainly: the description does not replicate
(a wounded codon is never repaired; heredity of D itself is EW-6 —
transcription exists since P2 but is not integrated with promotion
of daughters to working descriptions); the codon TABLE remains
frozen law (the honest residue, one level up); placement semantics
(codon at j builds at j+1) is authored geometry; and the first
translator is given, not assembled.
