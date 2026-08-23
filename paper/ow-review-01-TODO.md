# TODO from ow-review-01 ("Law Made of Matter", paper #3)

Derived 2026-08-23 from `paper/ow-review-01.txt`. The review file is
partially garbled (truncated lines in M4, M5, mediums 2/5/6, minor);
items marked [reconstructed] carry my reading of the intent.
Ordering: the one substantive error first, then the two v4-discipline
regressions, then bookkeeping, then mediums/minors. Items marked
[compute] need runs or scripts, not just prose.

## Must fix (substantive)

- [x] **T1 (M1) — rescope the coexistence claim.** §5: "…where the
  parent arc proved lineages on shared matter never coexist" misstates
  night 4's theorem (scoped to pure overwrite competition) and
  contradicts night 10's flagship (permanent parasite coexistence on
  the bare ring). One-clause fix: "…where the parent arc proved pure
  overwrite competitors never coexist", optionally adding the night-10
  contrast (that coexistence needed deception-order coupling; this one
  needs only self-made substrate niches). *Effort: 5 min.*

## Restore the v4 disciplines

- [x] **T2 (M2) — "Statistics, stated once" paragraph.** Import the
  nights-v4 pattern (design, tests, CI convention, multiplicity
  stance, nothing fitted) into §3's method notes. Concretely:
  two-proportion z on shares; binomial SE for win rates; per-cell n
  stated at every table; pre-registered predictions scored, no
  correction for multiplicity, failures reported.
  *Effort: 30 min.*
- [x] **T2a — n and intervals for §7's table** (100/100/60 per cell by
  ring); quantify the ring-96 wobble (0.817 vs 0.883, n=60 each,
  z≈1.0 → noise) in one sentence.
- [x] **T2b — w*_det with its error.** [compute] Propagate the μ(w)
  SEs through the zero crossing in `ow9_frontier.csv`
  (≈ 1.16 ± 0.05 by quick propagation — compute properly and print
  from the script so the number is regenerable). *Effort: 20 min.*
- [x] **T3 (M3) — four figures.** [compute] Write
  `experiments/openworld/fig_ow.py` (house pattern: fig_nights.py),
  emitting into `paper/figs/`:
  1. §9 dose–response (α-share and DEAD vs wound-fed fraction) — the
     headline causal result;
  2. §7 war sigmoid, three ring sizes on one axis;
  3. §6 ε × wound phase map (two heat panels: rescue, retention);
  4. the B-mirror niche construction as an ASCII-native space–time /
     final-state rendering (re-run walker2 survivor seed 20, sample
     tape+gates at intervals; nights Figure-1 style `\begtt` block is
     acceptable and cheapest). *Effort: 2–3 h, the largest item.*

## Bookkeeping reconciliations (M4) [reconstructed]

- [x] **T4a — run-count ledger vs abstract.** Ledger primary rows sum
  to 12,432; the 1,180 "certifications" row is re-runs of earlier
  cells — mark it "(re-runs, not additional cells)" and align the
  abstract ("about 12,400 primary runs plus 1,180 certification
  re-runs, zero mismatches"). While there: add ledger lines for
  `ow10_arith.py` (1,200) and `ow11_coupled.py` (480) — see T10 —
  and re-total. *Effort: 15 min.*
- [x] **T4b — O1's "800/800".** The control arm is 8 pairings × 50 =
  400/400 (800 was the OW-2 sweep total across both arms). Fix O1
  and check no other law row inherits the slip. *Effort: 5 min.*
- [x] **T4c — §4 table n vs 200-seed text splits.** Caption the table
  "50 seeds per cell" and keep the sentence noting the two key
  pairings were re-run at 200 seeds (it exists; make the linkage
  explicit). *Effort: 5 min.*

## Naming and framing

- [x] **T5 (M5) — rename the null allele.** ε collides with the
  mutation rate ε in a paper whose thesis includes "mutation as a
  rule weight". Use β′ throughout the text/tables (reviewer's
  alternative: η), with one parenthetical noting the driver's glyph
  is ε so the CSVs stay traceable. *Effort: 15 min.*
- [x] **T6 (M6) — the deflation paragraph.** One explicit paragraph
  (end of §2 or §3): the skeptic's "it's just a second matter track
  with an extra context read" is affirmed as the thesis — the
  identity theorem is what makes 'law' operationally non-vacuous
  (each glyph selects an exactly censused physics), and the 1-bit
  gate is the first rung of descriptions-with-content. Collect the
  existing scattered material; add nothing new. *Effort: 20 min.*

## Medium

- [x] **T7 (med 1) — two-niche stability criterion.** State it:
  final-state at the 10.8k-event horizon, one run of five walker2
  survivors. [compute] Strengthen if cheap: re-run that seed at 4×
  horizon; report "persistent at 43k events" or soften to
  "persistent at horizon" honestly. *Effort: 20 min.*
- [x] **T8 (med 2) — the 0/4-arm "replication".** [reconstructed]
  [compute] The identical 55/5/0 counts are same-seed re-runs
  through the mix compiler whose carrion feed rule is
  trigger-filtered before gathering — i.e. bit-identical by
  construction, a pipeline identity check, not an independent draw.
  Verify once (diff a seed-1 trace between ow6 duel k=4 and dose
  c=0), then say exactly that in §9. *Effort: 20 min.*
- [x] **T9 (med 3) — pre-registration scoreboard.** Compact appendix
  table: prediction, verdict (held / failed / partial), section where
  scored — covering OW-4 P1–P4, OW-5 Q1–Q4 + D1–D5, OW-6/7 R-set,
  OW-8/9 A/B/C. Makes "roughly half failed" auditable. *Effort:
  30 min.*
- [x] **T10 (med 6) — appendix completeness.** [reconstructed] State
  the toroidal gate read explicitly for both layouts (3-row: tape
  row 1 reads bottom row via wrap; 4-row: tape 1, fuel 2, regulatory
  3); add the ow10/ow11 ledger lines so the Honest-Limits coupling
  claim is traceable (pairs with T4a). *Effort: 10 min.*
- [x] **T11 (med 4) — abstract scoping.** "a 62-event mutation
  budget" → "a median 62-event mutation budget (under one wound
  protocol)". *Effort: 2 min.*
- [x] **T12 (med 5) — two related-work candidates.** [reconstructed]
  Verify then cite: Banzhaf's artificial regulatory networks
  (regulation evolved, but under an external GA) and Ilachinski &
  Halpern's structurally dynamic CA (lattice–rule coupling itself
  dynamic). Needs a web check of years/venues per the house
  audit rule (never cite from memory); then two bib entries + one
  contrast sentence in §12. *Effort: 30 min incl. verification.*

## Minor

- [x] **T13 — §6 mutant-ledger sentence**: separate what holds by
  construction (uniform mutant targets per fire) from what the
  pooled landing distribution measures. One clause.
- [x] **T14 — join the multi-line `\cite` key list** (fontana94…
  hickinbotham21) onto one line; it resolves but is fragile.
- [x] **T15 — wall-clock line**: one sentence in §3 for parity with
  the nights cost table (the whole arc's engine time is minutes on a
  laptop; compute the actual sum from the drivers' printed walls).

## Not in the review, queued by it

- [x] **T16 — rebuild + re-read pass** after all of the above
  (optex, two passes, zero warnings beyond known missing-field
  ones), and re-check every number touched by T4 against the CSVs.

## Execution notes (2026-08-23, all 16 done)

- T2b: the per-seed calculation gives **w*_det = 1.147 ± 0.017**
  (supersedes the pooled quick estimate 1.16; printed by fig_ow.py).
- T7: extended replays of the two-niche run: partition at 11k,
  spawner monoculture at 16k, walker REVERSAL at 22k, world dead by
  ~33k — "stable" replaced by the slow-war account in §5.
- T8: verified — playfields bit-identical 3/3 seeds (the mix
  compiler's wound-fed rule is trigger-filtered before gathering);
  §9 now calls it a pipeline identity check.
- T12: both references verified by web search (Banzhaf 2003 GPTP
  ch. 4 pp. 43–62 Kluwer; Ilachinski & Halpern 1987 Complex
  Systems 1(3) 503–527) and added to the shared bib.
- Scoreboard tally: 11 held / 10 failed / 5 partial-or-refined.
- New committed artifacts: fig_ow.py, ow9_dose.py (+CSV),
  paper/figs/ow-{dose,sigmoid,phase}.pdf + ow-niche.tex.
- The tex and bib remain uncommitted pending user review (house
  rule); rebuilt clean, 0 errors, 0 overfulls, 12 pages.
