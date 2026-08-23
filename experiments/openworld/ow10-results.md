# OW-10 — the arithmetic of the world

Date: 2026-08-23. Driver `ow10_arith.py`; raw `ow10_arith.csv`;
1,200 runs, exact 1,200/1,200. Prompted by the question whether O7
("small worlds elect underdogs") is a Farey/denominator-resolution
effect, and whether ring-size divisibility (smooth vs prime) is
load-bearing.

## A — primes sit exactly on the curve

β-win rate at w=1, adjacent sizes sharing one drive:

| N | P(β) | note |
|---|---|---|
| 23 (prime) | 0.295 | extra cell →α: 0.270, →β: 0.320 |
| 24 | 0.325 | fair start expressible |
| 25 | 0.340 | extra →α: 0.340, →β: 0.340 |
| 47 (prime) | 0.075 | extra →α: 0.080, →β: 0.070 |
| 48 | 0.115 | |
| 49 | 0.135 | extra →α: 0.140, →β: 0.130 |

No prime anomaly: 23 and 47 interpolate smoothly. The data even
decompose the two N-channels: *within* a triplet (fixed drive)
P(β) **rises** with N — that is the per-cell wound-rate dilution,
not size itself; *across* doublings at matched per-cell wounds it
falls 0.325 → 0.115 — the drift suppression. Both channels smooth
in N; divisibility is a false channel for these stochastic
dynamics (P1 confirmed). The one-cell start handicap is at most a
~0.05 swing at N=23 (≈1σ at this n, right direction) and
undetectable from N=25 up (P2 weaker than pre-registered). The
standing exception class from the nights arc is unchanged:
deterministic cycles aliasing against periodic drive strides —
absent here because the jump chain launders commensurability.

## B — the separatrix is an absolute count, not a rational share

Conditional drift μ(b/N) by decile of β-share at w=1:

```
N=24: -.012 -.008 -.005 -.005 -.005 -.003 -.007 -.005 -.008 +.042
N=48: -.006 -.003 -.004 -.006 -.007 -.008 -.013 -.006 +.000 -.003
```

At N=24 the drift flips **strongly positive in the top decile**
(+0.042): once α's remnant is down to ~2 cells, the feedback
switches sides. At N=48 the same share (top decile ≈ 5 remnant
cells) still fights — no flip. So the bistable structure is real
(P3 confirmed) but its separatrix sits at a fixed **absolute
remnant size** (a few cells), not at a fixed rational share: the
positive-drift zone shrinks like 1/N in share space. The underdog's
task is ~N/2 − 3 lattice steps against adverse drift, which is the
measured exponential suppression.

## Reading, in the Farey vocabulary

O7 is not "the world cannot express the share where the transition
happens." The share never settles; it walks on the lattice
{0, 1/N, …, 1} until absorption, and N is not the precision of a
computed ratio but the length of the ladder. Where denominators DO
carry load is **authored structure**: a fair 1/2 start needs 2|N,
the four-law melee needed 4|N — expressibility of rationals
constrains initial conditions, while the dynamics launders
arithmetic through stochasticity. And the load-bearing integers of
the dynamics turn out to be small **numerators** — absolute
remnant counts of 2–3 cells — not denominators.
