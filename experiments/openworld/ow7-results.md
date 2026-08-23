# OW-7 — economies: which fuel regime favors which law? (F3, M2)

Date: 2026-08-23. Driver `ow7.py` (+ two supplementary energy
probes); raw data `ow7_duel.csv`, `ow7_energy.csv`, `ow7_climb.csv`;
~1,800 runs total, exact accounting on all. Verdict up front: **the
economy is a selective force with its own laws. The first
β-favoring economy exists — a disturbance-fed component under
writer-pays at scarcity flips the duel to the repairer (16:7) —
and the SAME feed under target-pays flips it to α (0.81): the
payment side decides who captures the disturbance dividend. Pure
carrion economies die under both payment schemes, by two different
traps. Mobile wealth favors the spender. Energy damage is, to first
order, nothing but influx subtraction.**

## The economies (all harness-rule variants, zero engine change)

rain (OW-6 baseline, feed anywhere empty) · harvest (feed only
under living matter, `%` context) · carrion (feed only under holes,
`&` ctx `~`) · diffuse (rain + token hops on byte `d`) · convpriced
(rain, β's handler pays too) · mix (½ rain + ½ carrion) — each also
crossed with the **payment side**: writer-pays (token below the
firing anchor, OW-6) vs target-pays `_t` (token below the written
cell — "eat at the worksite", a body reshape in `gen_gated`).

## Stage A — economy × duel (α vs β, 60 seeds)

| economy | k=2: α / β / DEAD (α-share) | k=8: α-share |
|---|---|---|
| rain | 22 / 22 / 16 (**0.500**) | 0.983 |
| harvest | 24 / 11 / 25 (0.686) | 1.000 |
| carrion | 0 / 0 / **60** | 0 / 0 / **60** |
| diffuse | 36 / 9 / 15 (**0.800**) | 1.000 |
| convpriced | 26 / 12 / 22 (0.684) | 1.000 |
| rain_t | 21 / 19 / 20 (0.525) | 1.000 |
| carrion_t | 0 / 0 / **60** | 0 / 0 / **60** |
| mix | **7 / 16** / 37 (**0.304**) | 0.917 |
| mix_t | 17 / 4 / 39 (0.810) | 0.950 |

1. **The inversion exists.** `mix` at scarcity is the first economy
   where β beats α (16:7, z=−1.9; every previous regime gave
   α ≥ 0.5). Reading: under writer-pays, a token under a hole is
   unreachable until the hole is *repaired* — the repairer's
   lineage inherits the granary. Half the influx thus becomes a
   repair bounty, and the repair specialist collects it. Note the
   regime is brutal (37/60 dead — effective upkeep is one rain
   token per block): the repairer wins at the edge of viability.
2. **The mirror.** `mix_t` — identical feed, target-pays — flips to
   α 0.810: when the hole's token is spendable by ANY writer
   reaching it, α's unconditional east-writes eat the carrion
   without ever having repaired anything. Who captures a
   disturbance dividend is set by the *payment geometry*, not by
   the feed geography.
3. **Pure carrion is unviable under both payment schemes, by
   different traps.** Writer-pays: the bootstrap trap — meals sit
   under holes, payers must pay from under themselves, nobody can
   reach the food (worlds starve while primed fuel lasts, then
   freeze and rot). Target-pays: the **granary-graveyard** — repair
   strokes are funded but *upkeep* (maintenance painting, gate
   re-stamping) earns nothing; gates erode unre-stamped, fires
   cease, and the world dies with its fuel row completely full.
   A disturbance economy cannot pay for peacetime.
4. **Mobile wealth favors the spender** (R3 confirmed): diffusion
   turns the k=2 tie into α 0.800 (z=+4.0) — β's savings
   random-walk out of the bank to wherever a spender waits.
5. **Pricing β's conversion breaks the tie for α** (R4 confirmed:
   0.684), and **payment side alone is neutral** (rain_t 0.525 —
   the clean control for everything above).
6. Harvest is *not* rain (R2 half-wrong): at scarcity it is deadlier
   (25/60) and α-leaning (0.686) — dead columns earn nothing, so
   damage shrinks the economy itself; mechanism of the α-lean
   unassigned.

## Stage B — energy damage (design-doc open question 4): a null

Dose ladder: at k=8, one token destroyed per block is absorbed
invisibly (all cells identical to pq). At k=2 it is total collapse
(240/240 dead — below the metabolic floor). The clean test is
**matched effective influx**: (k=4, pqr) vs (k=3, pq) — and they
are indistinguishable (duel 35:4 vs 35:5; solos 39–40/40 both).
**Energy damage is pure influx subtraction**; the pre-registered
hoarder-exposure differential (R5) is refuted at this scale. One
whisper survives: `r` finds a standing token 114/120 times in
α-worlds vs 118.6 in β-worlds — the just-in-time economy does
offer fewer targets, but the margin is economically irrelevant
here.

## Stage C — climbs (γ-start, ε=0.01, 40 seeds)

| economy | k=2 | k=16 |
|---|---|---|
| harvest | 13/40 survive: **β 7, α 6** | 36/40: α 36 |
| carrion_t | 0/40 | 0/40 |
| mix_t | 1/40 (β) | 34/40: α 34 |

Harvest at scarcity nudges the evolved constitution toward β
(7:6 vs rain's 11:6 in OW-6) — directionally consistent with
scarcity-pluralism, n too small to lean on. Flush economies are
monistically α everywhere. The carrion climbs confirm the
viability traps at every ε.

## Predictions scored

R1 vindicated in modified form (pure carrion unviable; the *mixed*
disturbance economy delivers the β-inversion). R2 half-wrong
(harvest deadlier and α-leaning at scarcity). R3, R4 confirmed.
R5 refuted by the matched design (subtraction, not exposure).
R6 redirected: the pure-carrion climb cannot run; harvest's climb
gives the directional β-shift instead.

## Honest limits

Mix inversion at heavy world-mortality (37/60) — survivorship
conditioning; its capture mechanism (repair bounty) is inferred
from the payment-side mirror, not from a spend ledger; harvest's
α-lean unexplained; climb pluralism shifts are small-n; single
ring, single wound mix throughout.

## Exit → OW-8

The duel dose-response: OW-5 saw 66:34 flip to 0:100 under a 4×
mover boost and to 100:0 under politeness — map the win-share
curve over continuous mover weight to see whether the law war has
a sharp threshold (bifurcation) or a smooth response, free-matter
and priced.
