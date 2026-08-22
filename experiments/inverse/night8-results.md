# Inverse emergence, night 8: closing the loop — what it takes for a sequence to program its copier

Chemistry: night 7's tape commons (9 uniform rules) plus ONE uniform
codon template at a time, glyph-symmetric, weight 1. Three arms,
same seeds (paired inits), ring 24, s0=0.5, m {∞, 8, 4, 2}, 64
seeds: 768 runs, all exact, 136 ms/run, 32 s wall. Driver
`night8.py`, data `night8_codon.csv`.

- **base** — the night-7 null, no codon.
- **boost** (the WHEN-codon) — a head reading a run (west neighbour
  = covered glyph) gains a second, co-applicable repair rule for a
  hole east: repair mass doubles at run sites. Changes when holes
  close; never what fills them.
- **pair** (the WHAT-codon) — a head reading a run repairs 2-cell
  gaps with TWO copies in one event. Changes the written content:
  double replication yield per event at run-adjacent wounds.

Watch it: `./zahradnice demos/inverse/codon.cfg` (pair-codon world).

## Findings

**1. The null is itself a discovery: the tape self-organizes.**
With no codon at all, damage + copy-local repair homogenize the
genome dramatically (mean run 2.2→8.9 at m=8; max runs ~22 of 24
cells). Every repair copies the west flank into the hole, extending
a run; gap bursts fill with a single flank gene. Passive dynamics
alone are a strong pattern-ratchet — any codon claim must beat this
null, measured, not assumed.

**2. The WHEN-codon is read constantly and does nothing.** Boost
carries 40–43% of all repairs, yet at 64 seeds every paired
differential is statistically zero (runmean +0.40, t=0.68; tape
+0.31…0.72, t≤1.4; m=2 slightly negative). Reason, understood
before the powered rerun confirmed it: at any given hole, base and
boost write the SAME glyph — fill identity is fixed by geometry
(the west flank), so the codon modulates only timing, and hole-fill
identity is timing-independent in this chemistry. (The 16-seed
pilot showed seductive positive diffs that evaporated at 64 —
power discipline logged.)

**3. The WHAT-codon is read rarely and changes everything.** Pair
fires in only 9–21% of repairs, yet every differential is
first-order (paired vs base, n=64):

| m | Δ mean run | Δ tape |
|---|---|---|
| 8 | +1.07 (t=2.0) | +0.52 (t=2.4) |
| 4 | +0.75 (t=3.8) | **+3.00 (t=4.1)** — commons +28% |
| 2 | +0.20 (t=3.6) | **+1.49 (t=4.1)** — collapse regime +60% |

Run patterns are read by the machinery (context match), the reading
changes WHAT is written (two copies per event), and the written
copies extend the very pattern that was read. **The loop
pattern → machine behaviour → pattern is closed, and it carries
selective consequence.** It even pushes back the night-7 collapse
boundary: content-programming partially rescues the commons at m=2.

**4. Composition stays glyph-symmetric throughout** (s-share
tracks the damage regime, not the arm): what is selected is an
order parameter of the SEQUENCE (homogeneity), not a glyph — f-runs
and s-runs benefit identically, as the symmetric template demands.

## The law of the night

**A sequence programs its copier only if reading it changes the
written content; changing the schedule is invisible.** Demonstrated
in both directions under identical seeds: frequency of reading is
irrelevant (40% vs 15%); consequence of reading is everything.
Corollary for the summit: heritable information is exactly that
part of pattern which, when read, alters what the machinery writes
— everything else is decoration, however often the machinery
touches it.

## Honest limits & night-9 hooks

- The codon TEMPLATE is still law-side (uniform and glyph-symmetric,
  but its semantics are authored). The remaining remove: codon
  semantics themselves in matter — a codon table the tape can
  rewrite. That likely spends the spare dimension (a germline/
  codon-table row; the brainstormed channel uses).
- Both codons here are honest (write true copies). Deceptive
  variants — a codon writing the OTHER glyph (mutator/parasite
  sequences exploiting pair-yield) — are the natural night-9
  ecology, and the first place open-ended dynamics could appear.
- Effects measured at one ring size and one s0. **Collapse boundary
  CLOSED (night 9, C): fine m-grid puts base collapse at m*≈3.5 and
  pair at m*≈2.5 — the content-codon buys one full damage step.**
