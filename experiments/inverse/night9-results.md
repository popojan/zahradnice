# Inverse emergence, night 9: consolidation — four open questions closed

Housekeeping night: the open questions left standing in the night
4/7/8 docs, each closed with the cheapest decisive measurement.
Driver `night9.py` (sections A–D, 512 runs + the fine-grid rows,
all exact, ~60 s wall); data `night9_{drift,dwell,boundary,
contested}.csv`. One new body shape: `westclaim` (`~@@X@` — require
hole west, write into it; RHS cells between the boundary and RHS
anchor carry negative offsets — first use of that corner of the
spec).

## A. Night-7's "s-rise at m=8" — dissolved

At 4× horizon (96k events, 16 seeds) the s-share settles
0.52 → 0.50 → 0.50 → 0.50 by quarters: the night-7 "rise"
(0.35→0.52 in 24k) was **relaxation to the glyph-symmetric
equilibrium** from an s-depleted init (head placement converts
covered cells), not selection. Windowed drift confirms mean
reversion: E[Δs] negative in low-tape windows (t=−2.5, −3.5),
positive just below full tape (t=+3.9), zero at equilibrium. No
mystery remains.

## B. Residence theory — confirmed, and upgraded to a law

A 3-stroke `s` (extra settle state V, dwell 3 vs 2) raises
machinery residence on s and the equilibrium follows it almost
exactly, in every cell:

| arm | m | residence(s) | s-share (lastq) | tape |
|---|---|---|---|---|
| s2 | 8 | 0.55 | 0.52 | 18.1 |
| s3 | 8 | **0.68** | **0.69** | 15.0 |
| s2 | 2 | 0.62 | 0.62 | 2.4 |
| s3 | 2 | 0.69 | 0.69 | 1.9 |

**Equilibrium composition ≈ machinery residence distribution** —
and at dwell 3 this holds in a LIVING commons (m=8, tape 15/24), so
the tragedy of the commons exists after all, with a threshold in
structural cost: dwell 2 is compositionally neutral, dwell 3
selects slowness outright, and the commons pays (tape −17%). The
night-7 story ("shelter only matters in collapse") was the k=2
special case.

## C. Codon-dependent collapse boundary — one damage step of robustness

Fine grid m ∈ {2,3,4,5,6,8}, 64 seeds (mean tape / collapsed≤6
fraction): base dies between m=4 and m=3 (0.23 → 0.67 collapsed);
pair between m=3 and m=2 (0.02 → 0.72). The content-codon buys the
commons one full damage step (m* ≈ 3.5 → ≈ 2.5), extending
night 8's rescue observation into a measured boundary shift.

## D. Contested repair — the night-4 missing cell, filled

No movers: two static tissues B/D on the ring (random-mixed init);
every hole adjacent to tissue is claimed west→east (`reqwrite ~X`),
and in the CONTESTED arm also east→west (`westclaim`). Handicap
wd on D's claim weights; m=4; 24 paired seeds:

| arm | wd=1 | wd=0.5 | wd=0.25 |
|---|---|---|---|
| uncontested | 0.61→0.67, 16/24 | identical | identical |
| contested | 0.61→0.88, 21/24 | 0.61→**1.00, 24/24** | 0.61→**1.00, 24/24** |

(cells: B-share init→lastq, D-extinctions/24.) Uncontested, the
handicap is invisible in the strongest possible sense — the three
wd values give **bit-identical outcomes**, because at m=4 every
hole heals before the next poke lands, so claim weights only
permute healing order and fill identity is geometry's. Contested,
the SAME handicap is lethal: 24/24 extinction at wd≤0.5. Night 4's
law now has both cells measured with the same trait and magnitudes:
**a rate is selectable exactly when two parties race for the same
resource; otherwise weight is schedule, and schedule is invisible**
— the night-8 content/timing law and the night-4 contested-rates
law are the same law seen from two sides.

Two side notes from D: at parity (wd=1) the majority still fixates
beyond its share (21/24 from 0.61) — coarsening favours the
majority through minority-island extinction, a voter-model-like
amplification worth remembering; and the walls idiom (`^Wu*` etc.,
verified this session) makes chambered variants of this arena
buildable when needed.

## Ledger of remaining opens

- Head-density confound (night 7): **scoped (night11_gaps.py)** —
  at equal density the living-commons results are ring-robust;
  collapse-REMNANT composition depends on absolute machinery count
  (remnant ~ covered glyphs), so those claims are stated
  per-configuration in the paper.
- Codon-table-in-matter and deceptive codons: promoted to night-10
  candidates with a clean slate; everything else from nights 1–8 is
  either closed or explicitly superseded.
