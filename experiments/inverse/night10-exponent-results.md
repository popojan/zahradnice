# Night-10 addendum: the growth-law audit — parabolic coexistence excluded

The literature audit (paper/related-work.md, sweep 2) flagged the
strongest rival explanation for night-10's permanent two-type
coexistence: sub-exponential ("parabolic") replicator kinetics, where
per-capita growth declining in OWN abundance yields
survival-of-everybody with no compartments and no space (Szathmáry &
Gladkih 1989; Paczkó, Szathmáry & Szilágyi 2024, stochastic
constant-N — uncomfortably close to our ring). It also demanded a
covert-spatial-structure check (Boerlijst-style refuges). This
addendum answers both. Driver `night10_exponent.py`, data
`night10_exponent.csv` + `night10_exponent_bins.csv`; arms
order/para/paraonly × m {8,4,2} × 32 seeds = 288 runs, all exact,
14.5 s wall.

The two mechanisms differ in signatures they cannot share. Parabolic
growth is still *autocatalytic*: production of glyph g requires
existing g (rate ∝ x_g^p, p<1, through own abundance), so x_g = 0 is
absorbing. Fuel coupling is *cross-production*: the deceptive pair
writes g out of the OTHER glyph's run context, so production of the
minority is independent of its own abundance and x_g = 0 is not
absorbing. The order arm (honest pair — identical gap-site geometry,
own-glyph writes) is the built-in control with no cross channel.

## Findings

**1. Births at zero: the rival is dead on structural grounds.** In
the parasite arms, glyphs are born while their type is EXTINCT —
80/688/11,290 birth-glyphs at x=0 in para (m=8/4/2), 54/512/14,552
in paraonly — and every single one comes through the deceptive pair
(base and honest-pair births at x=0 are structurally zero, and
measure zero). The order arm: 0 births at x=0 across 2,067,884
extinct-glyph exposure events. No k·x^p law produces births at
x = 0.

**2. Extinction is not absorbing — the phase is a resurrection
ecology.** Resurrections (x_g 0→positive): paraonly m=2 7,276 across
32/32 runs (mean extinct spell ≈34 events), para m=2 5,645 (32/32,
≈44 ev), m=4 256–344 (32/32), m=8 27–40 (17–22 of 32, spells ≈60–70
ev). Order arm: 0 resurrections anywhere — extinction absorbing
exactly as autocatalytic kinetics demands. This sharpens night-10's
claim: at heavy damage the "permanent coexistence" is permanence of
the MIXTURE, not of uninterrupted lineages — at m=2 the minority
glyph is outright extinct ~16% of glyph-time and is always re-seeded
out of the survivor's own order. At m=8 extinction is rare and the
influx acts as a stabilizing floor under near-continuous coexistence.

**3. The influx is measured and one character wide.** While a glyph
is extinct, the majority machinery holds 0.10–0.16 gap-context sites
per sample (production propensity for the extinct type, para arms) —
while the extinct type's own channels hold exactly 0.00. The order
arm holds comparable gap sites (0.03–0.21) that produce nothing but
the majority glyph: same site kinetics, opposite fate. The write
TARGET — the one flipped character of night 10 — decides absorbing
monoculture vs regenerating mixture; the kinetic shape decides
nothing.

**4. Minority production is cross-dominated, and a growth-law fit
would be qualitatively wrong.** Share-binned birth decomposition:
in the lowest own-share bins the deceptive pair out-produces the
base channel up to ~8:1 (para m=4: 49.2 vs 6.4 births/1k exposure;
paraonly m=2: 130.6 vs 24.9), and the cross-share of minority births
rises with damage to 0.61–0.77; the dpair channel falls monotonically
as own share rises while base rises — the crossover the fuel
mechanism predicts. The naive exponent p_naive (log birth rate vs
log own abundance, the fit a parabolic analysis would run) comes out
0.71 to −0.64 — NEGATIVE in the parasite arms at m≤4, impossible for
any x^p autocatalysis: production falls with own abundance because
own abundance is the complement's order deficit. (The exponent is
additionally confounded by tape fullness — order m=2 fits −0.22 —
one more reason growth-law fits mislead in this substrate.)

**5. No covert mesoscopic structure (audit defense 2).** Minority
occupancy between samples: best-circular-shift overlap excess over
permutation null +0.03..+0.09, drift concentration R 0.24–0.63,
minority run length 1.5–2.8 vs shuffled null 1.2–1.5. The structure
that exists is micro-scale and fully accounted for: the pair write
itself deposits 2-cell runs, and the eastward polymerase walk
advects patterns. Nothing at the scale of traveling-wave refuges —
and decisively, a refuge cannot protect a type that is extinct: the
phase persists through ~250k extinct events per condition at m=2 by
re-creation, not protection.

## The statement for the paper

The parasite phase is **influx-stabilized, not growth-law-
stabilized**: the minority is produced out of the majority's order
at a rate independent of its own abundance; extinction is not
absorbing; no autocatalytic kinetics — parabolic included — can
mimic a positive birth rate at zero. Against plain mutation–selection
balance (the other influx-shaped classic): the influx here is not a
per-replication error rate — it is conditioned on the ordered runs
it then corrupts (night-10's mutator, fueled by boundaries instead,
starved in the same worlds), which is what makes the supply
self-regulating rather than parameter-set.

## Honest limits

- Ring 24 only (the night-10 main sweep geometry); the night-11
  gaps run showed the plateau is ring-intensive, but the exponent
  audit was not repeated at ring 48.
- Spatial nulls use K=6 permutations at every 11th sample —
  adequate for the effect sizes seen (excess ≲0.09), not for
  detecting subtle long-range order.
- p_naive is reported to document what a growth-law fit WOULD see;
  it is a diagnostic of model misfit, not an estimate of anything.
