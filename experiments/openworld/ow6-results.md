# OW-6 — M2: currency. Expansion pays rent (F3)

Date: 2026-08-23. Driver `ow6.py`; raw data `ow6_solo.csv`,
`ow6_duel.csv`, `ow6_climb.csv`; 740 runs, exact accounting
740/740, zero engine changes. Verdict up front: **the pre-registered
inversion is refuted, with a better finding in its place. Scarcity
neutralizes the spendthrift's edge to an exact tie but never
inverts it — because the hoard is lootable and the economy taxes
the specialist more. Wealth then amplifies α beyond its free-matter
dominance (0.66 → 0.98): a token anywhere in the generalist's
territory is spendable, while the walker can spend only under its
head. And the economy reshapes evolution: under scarcity the
evolved world becomes pluralistic (α, β, and even γ endpoints);
under wealth it is monistically α.**

## Mechanism (all in matter)

Fourth row: tape (1), **fuel** (2), regulatory (3, via wrap). Token
`o` on slot `.`; feed rule `.`→`o` on byte `f` (influx k = f-bytes
per drive block; chemostat saturation for free — a full row feeds
no further). **M2 pricing**: every matter-creating rule
requires-and-consumes the token below its anchor (`o` at (+1,0) in
LHS, `.` written back); conversion rules (β's handler) are free.
Fuel row starts primed. Wounds strike tape and gates, never fuel.

Structural asymmetry the pricing creates: α (every A applicable)
can spend any token under its territory; β's mover spends only the
token under its head — β's land hoards fuel that wounds unlock
locally (the handler mints a head exactly where the savings sit).

## Results

**A — solo viability** (30 seeds): at k=0 everything dies, α
included — *unpaid repair is no repair*. At k=2 the thrift ranking
is **β 27/30 > α 16/30** (γ, δ: 0/30 at every k — fuel does not
fix non-repair). At k=8 both repairers 30/30.

**B — the priced duel** (α vs β, 60 seeds):

| k | α | β | DEAD | α-share | standing fuel α / β |
|---|---|---|---|---|---|
| 1 | 0 | 0 | 60 | — | 4.3 / 4.4 |
| 2 | 22 | 22 | 16 | **0.500** | 2.2 / 3.1 |
| 4 | 55 | 5 | 0 | 0.917 | 3.2 / 2.1 |
| 8 | 59 | 1 | 0 | 0.983 | 4.8 / 0.9 |
| 16 | 59 | 1 | 0 | **0.983** | 8.0 / 0.6 |

Two reversals of intuition, one honest confirmation:

1. **Scarcity equalizes but does not invert** (22:22 exact tie at
   k=2, against the pre-registered β-win). β's thrift (stage A)
   does not convert into competitive victory because **the hoard is
   lootable**: α invades a β locus, captures its law — and the
   token parked below it. Savings without defense fund the raider.
   Watch β's standing fuel collapse (3.1 → 0.6) as k grows.
2. **Wealth amplifies the spendthrift beyond the free world.**
   Unpriced, α's share was 0.66 (OW-5); priced-and-flush it is
   0.98. Under pricing, painting budgets are set by *catchment*:
   fuel falls uniformly, α's entire territory collects, β collects
   on ~one cell. The economy taxes the specialist walker more than
   the generalist spammer — the opposite of what "pricing spam"
   was expected to do.
3. k=1 is below the metabolic floor for any law here (60/60 dead).

**C — the priced climb** (γ-start, ε=0.01, 40 seeds):

| k | survive | dominants |
|---|---|---|
| 2 (scarce) | 19/40 | **α 11, β 6, γ 2** |
| 16 (flush) | 36/40 | **α 36** |

The economy reshapes the evolutionary outcome: flush worlds are
monistically α (36/36 survivors); scarce worlds are pluralistic —
β is a genuine evolutionary endpoint in a third of survivors, and
even the lottery walker persists twice. Scarcity flattens the
peak; wealth sharpens it. (Consistent with the duel: at k=2 the
α–β contest is a coin flip, so history decides.)

## Laws of the night

- **Repair must be paid**: an unpaid repairer is a frozen one, and
  frozen means dead under wounds (k=0, 120/120 dead).
- **Thrift is a solo virtue, not a competitive one**: the ranking
  β>α at scarce solo viability coexists with α≥β in every duel.
- **Catchment beats efficiency once wealth flows**: whoever can
  spend anywhere converts influx to expansion fastest, and
  expansion captures the rival's savings. Night-11's "parasite
  that pays its rent" gains a sibling: *the hoarder who cannot
  defend the vault*.

## Honest limits

One ring, one wound rate, feed spatially uniform (targeted/local
feeding is an obvious next axis and could genuinely invert the
duel — a catchment equalizer); handler kept free by the
matter-creation criterion (pricing conversion too is a separate
arm); the k=2 duel tie is at 16/60 world-death — survivorship
conditioning applies; ROWS=4 geometry differs from the free-matter
baseline it is compared to.

## Exit

The arc now has its economy. Nearest next candidates: local/earned
feeding (fuel written where work happened — closes the
metabolism loop and may invert the duel); pricing conversion;
energy damage (wounds on the fuel row — design-doc open question
4); and the paper-#3 spine now spanning P0→OW-6.

Watch it live: `./zahradnice demos/openworld/lawrent.cfg` — tokens
rain, α burns them on sight, β banks them under its trail, and the
frontier decides who owns the vault.
