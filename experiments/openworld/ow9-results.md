# OW-9 — consolidation: the cliff dissolves, the ledger convicts

Date: 2026-08-23. Driver `ow9.py` (+ ring-96 supplement, appended);
raw data `ow9_cliff.csv`, `ow9_ledger.csv`; 2,560 runs, exact
accounting 2,560/2,560. Three opens from OW-7/8 closed; two of my
own pre-registrations corrected by the data; one new law. Verdict
up front: **there is no cliff — the free duel is a smooth selection
curve read through finite-size drift, and β's wins at ring 24 were
substantially luck (its w=1 win probability decays geometrically
with ring size: 0.325 → 0.120 → 0.017). The mix inversion is
confirmed at the ledger level as a redistribution of total spending
power toward the repairer. And the harvest α-lean has a mechanism:
an economy selects among laws by WHICH INVASION CHANNELS IT FUNDS —
harvest never feeds a wound, and wounds are β's only route in.**

## A — the fine-gridded "cliff" (α-share vs β mover weight w)

| w | ring 24 (200 s) | ring 48 (100 s) | ring 96 (60 s) |
|---|---|---|---|
| 1.00 | 0.675 | 0.880 | 0.983 |
| 1.05 | 0.600 | 0.750 | 0.950 |
| 1.10 | 0.405 | 0.700 | 0.950 |
| 1.15 | 0.310 | 0.600 | 0.950 |
| 1.20 | 0.270 | 0.450 | 0.817 |
| 1.25 | 0.190 | 0.450 | 0.883 |
| w* | **1.076** | **~1.18** | **> 1.25** |

Corrections and readings:

1. **OW-8's "cliff" was coarse gridding.** At ring 24 the descent
   0.675 → 0.190 is steep but smooth (max slope ≈ 4 share-units
   per weight-unit around w*); no discontinuity. A1 (w* = 1.08 ±
   0.02) confirmed exactly; the bifurcation language is retired.
2. **A2 refuted, better story found.** The transition does not
   sharpen at fixed w* with size — the whole curve shifts up and
   right. At w=1, β's win probability falls ~geometrically with
   ring size (0.325, 0.120, 0.017 per doubling), the signature of
   a **biased frontier random walk**: β's ring-24 wins are the
   fixation tail of drift against a mean disadvantage. Any w*
   measured at finite size is drift-shifted; the deterministic
   compensation weight exceeds 1.25 and grows with L. Consequence
   for the whole arc: the free-matter duel's "66:34" is a
   small-world number — in the large-world limit the stamp-budget
   favorite simply wins.

## B — the mix-inversion spend ledger (decided runs, k=2)

| eco | n | α spends | β spends | α repair / β repair | looted α / β |
|---|---|---|---|---|---|
| rain | 105 | 14,282 | 12,293 | 5,931 / 5,693 | 387 / 245 |
| mix | 58 | 5,984 | 6,791 | 2,760 / **3,672** | 206 / 228 |
| harvest | 60 | 9,726 | 5,573 | 3,861 / 2,550 | 228 / **5** |

- **B1 as formulated was wrong**: both laws spend carrion tokens in
  the same *proportion* (g-share ≈ 0.42 each). The bounty is not in
  the composition — it is in the totals: mix flips the spend share
  (α 0.537 → 0.468) and the repair share (0.510 → 0.429); the
  wound-fed half redirects purchasing power to wherever repair
  happens, and β does the repairing.
- **B2 confirmed**: the quarter-1 carrion-capture leader wins ~80%
  of decided mix duels (α-leader 19:6, β-leader 27:6) — early
  bounty capture predicts the war.
- **B3 confirmed**: looting is α's tool under rain (387:245) and
  the edge vanishes under mix (206:228).

## C — the harvest α-lean: mechanism found (not the one predicted)

The pro-cyclical hypothesis (C1/C2) is **refuted at k=2**: feeds
sit at the influx cap (~63/quarter) for every surviving world
regardless of alive-count — income is influx-limited, not
capture-limited, so "income follows matter" never binds. Spend
totals of survivors are equal across economies (C3 moot).

The ledger's own clue is sharper: under harvest, **β's looted
spends collapse to 0.08/run (from 2.3/run under rain, ×28) while
α's are unchanged (3.7 → 3.8/run)**. Reason: β conquers through
wounds — a frontier hole is repaired from β's side, and under rain
the hole's banked token becomes the prize; harvest *never feeds a
hole*, so β's conquests are unsubsidized and yield no booty. α
conquers by overwriting living matter, which harvest happily keeps
funding. Cross-confirmed from the other side: mix, which adds
wound-feeding, restores β's loot parity, lifts its repair share,
and inverts the duel.

**The law of the night: an economy selects among laws by which
invasion channels it funds.** Feed the standing crop and you arm
the overwriter; feed the wounds and you arm the repairer.

## Predictions scored

A1 ✓ (w* = 1.076). A2 ✗ twice over (size-dependent w*, drift not
sharpening — replaced by the frontier-drift reading). B1 ✗ as
formulated (composition equal; totals shift). B2 ✓. B3 ✓. C1/C2 ✗
(income at cap). C3 moot. Two of seven pre-registrations survived
contact intact — the instruments are doing their job.

## Honest limits

The drift reading rests on three sizes and win-rates, not a direct
frontier-walk measurement; the invasion-channel law is inferred
from the loot ledger plus the mix cross-check — the interventional
killer test (an economy feeding ONLY frontier holes should maximally
arm β) is designed but not run; ledger quarters are normalized per
lifespan, so cross-fate income-rate comparisons are approximate;
decided-run pooling carries survivorship weighting.

## Exit

Opens worth their own nights: the frontier-subsidy intervention
(the invasion-channel law's decisive test); a direct frontier-walk
instrument (position of the α/β boundary over time → drift vs
selection decomposition); deterministic-parity weight estimate.
The paper #3 spine now spans P0 → OW-9.
