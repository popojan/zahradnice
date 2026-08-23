# EW-3 — who pays for the polymerase (F4, the summit test)

Date: 2026-08-23, session 8. Registrations: ew-design.md §EW-3
(P3-1a..d + Amendment 4, both written before the corresponding
runs). Driver: ew3.py; data: ew3_runs.csv (1600 runs, zero
exactness failures). Verdict up front: **the inheritance channel is
EARNED — maintained by selection on the matter that funds it —
exactly where machinery is scarce relative to wound demand.** Where
machinery is abundant, funding it is selectively neutral (the
free-rider prior holds there), and gate dynamics are invariant to
who builds. Scarcity is not a nuisance parameter; it is the
condition under which the channel becomes visible to selection.

## Setup

Ring 24, two alleles with IDENTICAL matter law (spawner A>A.writeA);
α owns build-copier, β free-rides; machinery starts empty; copiers
decay; all territorial change is wound-mediated annexation from the
west (same-content writes never conquer, so no spontaneous war).
Arms: none / both / free / taxed (build on T: each build displaces
one of α's own matter events). Regimes (cad, M, ε_d): abundant
(16, 25, 0.05) × 200 seeds, mid (4, 10, 0.1) × 100, scarce
(1, 5, 0.2) × 100. Drive: paint + e + (T C^cad)*200 +
120 × (p + (T C^cad)*M).

## Results

z = sign test on α-vs-β win counts; gates/annexation are means.

| regime | arm | winners α:β | z(α−β) | gates α / β / ? | α holds of β-land | β holds of α-land |
|---|---|---|---|---|---|---|
| abundant | none | 76:77 | −0.08 | 6.0 / 6.0 / 11.9 | 0 | 0 |
| abundant | both | 84:83 | +0.08 | 11.7 / 12.3 / 0.0 | 5.2 | 5.5 |
| abundant | free | 83:85 | −0.15 | 11.7 / 12.3 / 0.0 | 5.1 | 5.5 |
| abundant | taxed | 100:79 | +1.57 | 12.4 / 11.4 / 0.1 | 5.6 | 5.0 |
| mid | free | 53:40 | +1.35 | 11.8 / 11.7 / 0.5 | 5.4 | 5.3 |
| mid | taxed | 40:51 | −1.15 | 11.4 / 11.6 / 1.0 | 5.8 | 5.8 |
| scarce | both | 49:45 | +0.41 | 10.2 / 9.3 / 4.5 | 5.2 | 4.8 |
| scarce | free | **99:1** | **+9.80** | **17.2 / 2.9 / 3.9** | **8.1** | **1.1** |
| scarce | taxed | **95:3** | **+9.29** | 17.5 / 3.6 / 2.9 | 8.2 | 1.4 |

- **P3-1a HELD**: no machinery → every repair freezes, freeze
  propagates as erosion, the tape dies entirely (alive 0/24), and
  the ghost gate composition is allele-symmetric. Law without
  machinery is a fossil record.
- **P3-1b HELD** in all three regimes: symmetric building = drift
  null (winners split within noise).
- **P3-1c (original, abundant) REFUTED — as re-registered in
  Amendment 4**: with bandwidth ≫ demand the public good is global;
  the free arm is indistinguishable from the symmetric arm. The
  measured **saturation invariance**: gate outcomes of `both` and
  `free` are bit-identical in 190/200 abundant seeds, 3/100 mid,
  0/100 scarce — machinery COMPOSITION is invisible to law when
  machinery is saturating, because the stamp content is always the
  west template; only stamp TIMING carries selective information,
  and timing only matters when scarce.
- **P3-1c' HELD**: the α advantage appears and grows with scarcity
  (z: −0.15 → +1.35 → +9.80). In the scarce regime α wins 99:1,
  holding 8.1/12 of β's original land against 1.1/12 lost. The
  mechanism is the registered one: an unstamped west neighbour
  cannot regrow the next wound, so unrepaired territory erodes;
  copiers are born over builders and decay in transit, so repair
  is local; the free-rider's land freezes, erodes, and is annexed
  from the west by the lineage that pays for law-copying.
- **P3-1d PARTIALLY HELD, with a finding**: the time tax never
  reverses the sign at scarcity (taxed 95:3, share ≈ free) — but
  in the MID regime taxed flips weakly negative (z=−1.15 vs free's
  +1.35): the tax bites exactly where the benefit is marginal.
  (Abundant taxed drifts weakly positive, z=+1.57, n.s. — noted,
  not interpreted.)

Survivorship note, reported faithfully: in the scarce free arm
α-land ends LESS alive than β-land (3.5 vs 5.9 of 12) — pokes
target living matter, so the lineage that keeps repairing keeps
absorbing wounds while the free-rider's frozen corpse is spared;
the winner metric is law (gates), and the erosion asymmetry between
ACTIVE lands (visible mid-run) resolves into this end-state
artifact. Same genre as OW-8's hoard-looting survivorship caveats.

## The summit verdict, stated

Paper #3's three channels were authored; EW-1 + EW-3 show what it
takes for the first of them to be earned: (i) move the channel's
exercise into a matter population (copiers) — EW-1 proves this
preserves the authored family as its infinite-bandwidth limit,
exactly, down to γ's seed-lottery mixture; (ii) make the machinery
scarce relative to demand — EW-3 proves selection then maintains
the machinery through the lineages that fund it, 99:1, robust to
paying for it in the world's scarcest currency (time). Abundance
neutralizes the channel; scarcity selects for it. This is O8's
scarcity law climbing one level: from wealth shaping evolution ON
the channels to scarcity deciding whether the channels themselves
are anyone's to keep.

Honest limits: the copy rules remain in frozen law (exercise
earned, possibility not — the interpreter rung stands); miscopy
(π) and fuel pricing were not exercised in EW-3; copier
replication/heredity (EW-4) untested; east-handed geometry breaks
annexation symmetry by construction (both alleles equally).
