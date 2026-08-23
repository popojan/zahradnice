# EW-6 — description replication and healing (F4)

Date: 2026-08-23, session 11. Registrations: ew-design.md §EW-6
(P6-1..4; ring/layout amendment below recorded pre-sweep). Driver:
ew6.py; data: ew6_runs.csv (700 runs, zero exactness failures).
Verdict up front: **healing works — with the transcriptase, deep
description wounding costs almost nothing (35–40/100 survival flat
across q16/q8 vs 39 unwounded) where the unhealed world collapses
(13/100, description annihilated). But the sweep's registered
self-reference prediction was REFUTED by a mechanism nobody
registered: the backup row is a wound DECOY, and at this damage
regime passive redundancy beats active repair.**

## Setup and the pre-sweep amendment

Geometry: tape / BACKUP / code / mach / reg. Transcriptase Φ on
the machinery row: BACKUP (codon → empty backup slot at (−2,0)),
RESTORE (backup → emptied code cell at (−1,0)), drift; codon t
encodes Φ. The q rules anchor on codon glyphs wherever they stand,
so both copies are wounded uniformly.
**Amendment (ring 24 → 32, pre-sweep)**: at ring 24 the repair
layer starved the world it archives — the smoke autopsy showed a
PERFECTLY healed two-copy description standing over a dead world
(reg row half-`?`, tape empty): t codons and Φ displaced copier
codons below the wound economy's needs. The repair layer costs
genome length and habitat, not just bandwidth (cadence 6/8 did
not help). Ring 32 gives b×10 + w×4 + t×2 with machinery density
preserved.

## Results (100 seeds/arm; internal baseline `bare` = no Φ, no t,
b×12)

| arm | survived | restores | codons code+backup (of 16+16) |
|---|---|---|---|
| bare (no q) | 88/100 | — | 16.0 + 0 |
| healed (no q) | 39/100 | 0 | 16.0 + 15.9 |
| healed-q16 | 40/100 | 4.1 | 13.3 + 13.4 |
| healed-q8 | 35/100 | 7.2 | 10.2 + 10.4 |
| healed-q4 | 20/100 | 9.6 | 3.1 + 2.9 |
| bare-q8 | 13/100 | — | 0.0 + 0.0 |
| no-t-q8 | **52/100** | 0.1 | 2.3 + 2.4 |

- **P6-1 HELD, stronger than registered**: healed-q8 (35) is not
  merely ≥ half of healed (39) — it is at parity, and healed-q16
  (40) is indistinguishable from unwounded. With replication and
  repair, description wounds at these rates cost nothing; without
  them (bare-q8) the description is annihilated (0.0 codons) and
  survival collapses to 13.
- **P6-2 HELD in direction, magnitude off**: bare-q8 collapses,
  but to 13/100 rather than EW-5's 0/100 — the richer ring-32
  world coasts longer on standing machinery after its description
  dies. Narrated, not hidden.
- **P6-3 HELD on both halves, with the tax far larger than
  registered**: the repair layer costs 49 points unwounded
  (39 vs 88 — two codon slots turned from copiers to
  transcriptase-support, plus Φ's habitat and lottery share), and
  buys robustness where wounds exist (35 vs 13 at q8).
- **P6-4 REFUTED — the wound decoy.** The registered ordering put
  no-t-q8 between bare-q8 and healed-q8; it landed ABOVE both
  (52). Mechanism, verified from traces: wounds anchor on codon
  glyphs wherever they stand, so once a backup exists, **45% of
  all description wounds land on the backup row** (measured 110 of
  246 in no-t, 113 of 250 in healed) — a sacrificial copy that
  absorbs damage at zero running cost. Both arms enjoy the decoy
  equally; no-t additionally keeps b×12 and sheds Φ's running
  cost after its seed machines decay, and at this regime the
  repair layer's rent (codon slots + lottery share, for 7.2
  restores) exceeds its marginal benefit over the decoy. At q4
  the ranking's logic predicts repair should eventually win
  (healed-q4 20/100 with 9.6 restores vs the decoy-only
  configuration untested at q4 — registered as the natural probe
  for whoever continues the dose).

## What EW-6 establishes

The description is no longer a phenotype with a countdown: it
replicates (backups), heals (restores), and — unregistered but
measured — its copies shield each other by existing. The layered
finding is the arc's economy laws climbing into the archive:
redundancy is nearly free and buys damage dilution; active repair
is expensive and buys exactness; and at moderate damage the
free thing wins. Real genomes know both answers (polyploidy and
repair enzymes); this substrate now prices them against each
other in 700 exactly-accounted runs.

Honest limits: promotion is shallow — the backup is a second copy
read only by Φ, not a full working description (translation reads
the code row only); the decoy effect depends on the wound rule
targeting glyph instances uniformly (a row-targeted wound channel
would kill the decoy and re-price repair — one more registered
follow-up); ring 32 numbers are not directly comparable to EW-5's
ring 24.
