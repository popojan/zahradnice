# EW — the earned family (F4): machinery that earns the channels

Date: 2026-08-23, session 8 of the open-world arc. Design doc +
pre-registrations, written BEFORE any run. Parent question: paper #3
("Law Made of Matter") authored three channels — inheritance of
regulation (stamps ride matter creation), its miscopying (mutant
headers), and its price (fuel reads). The paper's honest-limits
section flags the summit explicitly: machinery that EARNS these
channels instead of being granted them. This family is the climb.

## What "earned" means operationally

In F3 every channel is exercised unconditionally by the rule table:
a matter-creating rule stamps its allele at no agent's expense,
miscopy is a header weight, price is a header read. Nothing in the
world can lose, gain, relocate, or degrade a channel.

F4 keeps the channels' POSSIBILITY in frozen law (the von Neumann
separation: physics permits copying) but moves their EXERCISE into
matter: whether, where, how fast, how faithfully, and at what cost
regulation is inherited depends on a population of copier cells that
must be built, fed, and can die. The claim to be earned is not "the
rule table contains no copy rules" — it is that channel throughput,
fidelity, location, and cost are carried by matter subject to the
same selection, wounds, and economy as everything else. The rung
above (rule-encodings read from matter by an interpreter — content,
not just activation) stays on the ladder, untouched here.

## F4 axioms (delta against F3)

1. **Matter motion de-regulates.** A matter-creating rule writes its
   matter AND a literal `?` (unstamped marker) at the written
   column's gate cell — over empty gates and over live alleles alike
   (conquest de-regulates the conquered locus). No rule stamps an
   allele as a side effect of creating matter. Consequence: growth
   outruns law by exactly one cell and stalls — an unstamped locus
   gates nothing, so no rule anchors there.
   **Amendment (2026-08-23, post-P1 smoke run, pre-sweep): conquest
   = CONTENT CHANGE.** The unamended axiom collided with F2's
   idempotent-spawner idiom: a spawner re-fires its east write
   forever, and each re-fire re-de-regulated the cell a copier had
   just stamped — law thrashed unboundedly in every spawner world.
   The refinement: a creating rule de-regulates exactly the cells
   whose matter CONTENT it changes. Matter is anonymous (the arc's
   organism-deletion doctrine), so rewriting A over A is no identity
   event and the gate stands; A over B or A over void is conquest.
   Expressed by splitting the unconditional `write` kind into three
   mutually exclusive east-content variants (empty / same / other);
   exactly one is applicable in any state at the rule's own weight,
   so the split is lottery-equivalent to F3's single rule. reqwrite
   pins its east content and needs no split. Recorded before the
   EW-1 registered sweep ran; the smoke run that forced it is
   narrated in ew1-results.md.
   **Amendment 2 (same session, pre-sweep): machinery gets its own
   trigger byte.** With copy/walk on T, copiers eat the shared event
   budget and the night-2 classifier (whose ABSORBED detection
   compares matter events to the byte budget) reads every f4sat
   world as frozen. Per the house drive-composition pattern
   (pitfalls #22), the copier law fires on byte C and the drive is
   b + (TC)*H + rounds x (p + (TC)*H) for ALL arms — C no-ops where
   no copier rules exist, and trigger-filtered rules do not perturb
   the RNG stream (OW-9's bit-identity tool). Consequence, stated
   honestly: EW-1's time tax is an explicit cadence allocation, not
   emergent lottery competition; the shared-trigger competition
   returns as an EW-2 axis (sweep the T:C cadence — the bandwidth
   price of law-copying).
   **Amendment 3 (same session, pre-sweep): equivalence is a
   bandwidth limit.** At cadence 1:1, β and γ still PRE_FAIL: their
   matter WAITS on the copier (a fork cannot advance until stamped),
   matter T bytes no-op during waits, and the classifier reads
   starvation as absorption — machinery latency rate-limits matter
   throughput, which is the earned channel's signature, not a bug.
   Registered reformulation of P1-2: the authored channel (F3) is
   the infinite-bandwidth limit of the earned channel (F4). EW-1
   sweeps machinery cadence cad ∈ {1,2,4,8,16,32} (drive unit
   T + C*cad; ladder extended past 8 after 5-seed diagnostics showed
   β crossing from starvation 388–396/400 matter events at cad 8 to
   the exact F3 orbit — TRANSLATION period 6, transient 5 — at 16);
   prediction P1-2': per-allele night-2 outcome distributions
   approach F3's monotonically in cad; α (static repairer) matches
   already at cad 1; β/γ (dynamic, fork-chasing) require cad ≥ 16;
   δ (no creation) is cadence-invariant.
2. **Only machinery regulates.** A copier glyph on the machinery row
   (bottom−1; the tape reads it at toroidal (−2,0), the copier reads
   the regulatory row at (+1,0)) executes the one stamping act in
   the family: read the template allele below itself (`&` LHS, ctx =
   allele), require `?` below-right, write the allele there (`&`
   RHS, ctxrep), advance one cell right. One body; one header per
   allele — the F3 (ctx, ctxrep) stamp machinery re-anchored on the
   machine instead of on the matter.
3. **Machinery is matter.** Copiers are built by a priced, gated,
   allele-owned rule (matter pays fuel to write a copier at (−2,0),
   only into an empty slot); they die (decay rule and/or harness
   wounds); they occupy the event lottery — under A3's fixed event
   budget every copy event is a matter event not taken, so earned
   inheritance pays a time tax automatically, before any fuel price.
4. **Fidelity is a machine trait.** Faithful copier Π carries only
   (g, g) headers; sloppy copier π additionally carries (g, g′)
   mutant headers at weight ε. Which mutation rate a neighbourhood
   experiences is set by which machines stand there, not by law
   alone. (Honest regress: the Π↔π distinction and ε remain
   authored; one meta-level is lifted, the next is not.)
5. **Copying is directional and excluding.** Copiers advance east
   only and require the destination machinery slot empty (TASEP
   exclusion — copiers queue; the substrate's own lineage).

Walk rule (repositioning): a copier may step east over an
already-stamped locus (`%` cell, target gate ∈ allele set) — same
exclusion. A copier facing a void gate stalls.

## Geometry (ring worlds, unchanged screens)

Row 1 = tape. Row 2 = matter-fuel row (writer-pays, F3 pricing).
Bottom row = regulatory row ((−1,0) from tape, toroidal). Bottom−1 =
machinery row ((−2,0) from tape; (+1,0) from it is the regulatory
row). All reachable inside ordinary bodies; zero engine change; A4
literally intact.

## P1 probe — exit criteria (byte-level, one cfg, hand-scripted)

`p1_copier_probe.cfg`, screen 8×16, seeded, headless. Phases by
trigger byte: b bootstrap, d build ×2, t copy ×3, c creation ×2,
s sloppy-copy ×3, w walk ×1.

1. Bootstrap writes machinery row at (−2,Δ) and regulatory row at
   (−1,Δ) from a row-1 anchor in one horizontal body (toroidal wrap
   both rows).
2. Build: A gated α with empty (−2,0) writes Π there (d #1);
   d #2 is a no-op (slot now full — self-limiting); A over Π-slot
   and A gated β never fire (occupancy and specificity negatives).
3. Copy: Π with template α and `?` east-below stamps α and advances;
   chains (the just-stamped cell is the next template); stops dead
   at a β-stamped target (t #3 no-op).
4. Creation: F gated α with empty east writes F east + `?` at
   (−1,+1) — over a live β gate (de-regulation on conquest) and over
   an empty gate; the freshly created F (gate `?`) CANNOT create
   further — the frontier stall that makes copiers load-bearing.
5. Miscopy: π's mutant headers fire at ~ε/(1+ε) per copy (verified
   over seeds); faithful headers dominate.
6. Walk: Θ steps east over a stamped locus, excluding, and only
   under the walk trigger.
7. `?` behaves as an ordinary literal in LHS match and RHS write.
8. Exact accounting: trace-replay == dump on the probe run.

## Pre-registered experiments

**EW-1 necessity + conditional equivalence.** Arms: (a) F3 authored
stamps (control); (b) F4, machinery row saturated with free faithful
copiers, copy unpriced; (c) F4, zero copiers. Predictions:
(P1-1) arm (c): the regulatory row beyond the initially stamped
region never gains an allele; matter halts one cell past it; the
night-2 repair verdicts of every allele collapse to dead/frozen.
Earned-O1: law must be inherited BY MACHINERY to persist.
(P1-2) arm (b) reproduces arm (a)'s census verdicts per allele —
NOT event-for-event (copy events dilute the lottery; the time tax is
real and measured), but in final-outcome distribution given enough
events; report the event-inflation factor. (P1-3) exactness
(trace-replay == dump) holds in all arms, every run.

**EW-2 machinery economy.** Copiers priced (machinery-row fuel
consumed per copy... variant A) or build-priced only (variant B),
copiers mortal (decay ε_d). Dose–response: machinery-fuel influx vs
law-frontier velocity and allele survival. Predictions: (P2-1) law
velocity rises with machinery fuel and saturates at the matter
growth rate; (P2-2) at zero influx the world reverts to EW-1(c)
frozen-law death after standing copiers starve/decay; (P2-3) fuel
placement steers WHERE law gets copied (O9's dose–response
instrument pointed at the inheritance channel itself).

**EW-3 who pays for the polymerase (the summit test).** Two alleles
with IDENTICAL matter law (the spawner A>A.writeA); α owns the
build-copier rule, β does not (pure free-rider — copiers stamp
whatever template they stand on, no ancestry check). Because both
alleles' matter is the same character, the same-content variant
never conquers: ALL territorial change is wound-mediated (a poke
erases a locus; the west neighbour regrows it, de-regulating it to
`?`; a copier stamps it with the WEST template — annexation by
whoever sits west of a repaired wound, machinery permitting).
Concrete protocol (registered before ew3.py ran): ring 24, blocks
α = cols 0–11, β = 12–23 (ow2 builder cursor); machinery starts
EMPTY; build writes Π at (−2,0) into an empty slot, weight 1;
copiers decay at ε_d = 0.05 and copy/walk at weight 1 on byte C;
cadence 16 (the EW-1-calibrated bandwidth); drive = paint + e +
unit*200 + 120 × (p + unit*25), unit = T + C*16; 200 seeds/arm.
Arms: **none** (nobody builds — freeze baseline), **both** (α and β
both build — symmetric null), **free** (α builds, on C: building
costs no matter events), **taxed** (α builds, on T: each build
displaces one of α's own matter events — writer pays in time).
Predictions:
  P3-1a (none): machinery never exists; every repaired wound
    freezes at `?`; monotone `?` accumulation, allele-symmetric;
    no winner beyond drift.
  P3-1b (both): symmetric machinery; winners split 50/50 within
    binomial noise (drift null).
  P3-1c (free, DIRECTIONAL, the summit claim): α's final gate share
    exceeds β's, and α wins more runs than β (one-sided). Mechanism
    registered: copiers are born only over α, drift east-only, and
    decay in transit — the public good reaches β's west flank
    discounted and β's east flank barely at all, so α's east
    boundary annexes while β's annexation front freezes. If this
    holds, the inheritance channel is maintained by selection on
    the matter that funds it — the channel is EARNED. The
    adversarial prior is night-11's inversion (free-riding to
    parity); if β holds parity or wins, that is the registered
    tragedy verdict, equally reportable.
  P3-1d (taxed): α's gate share is lower than in (free) — the
    build tax — with the α>β sign preserved iff the spatial
    discount dominates the tax.
Metrics per run: winner by gate majority, final gate counts
(α/β/`?`), composition per INITIAL half (annexation direction),
copier count, tape alive, exact accounting.
  **Amendment 4 (post-smoke, pre-sweep): the scarcity extension.**
  The 5-seed smoke showed `both` and `free` bit-identical in gate
  outcomes (copier counts differ): stamp content is always the west
  template, so when bandwidth saturates demand, gate dynamics are
  invariant to machinery composition — the public good is global
  and P3-1c should FAIL in the abundant regime (registered
  expectation now: abundant = drift null for all machinery arms).
  The discriminating mechanism, visible in the smoke: an unstamped
  west neighbour cannot regrow the next wound, so freeze propagates
  as MATTER EROSION; scarce machinery makes repair local, and
  whoever funds machinery repairs faster and annexes eroded land.
  Extension sweep, registered before any full run: three regimes
  (cad, M units between wounds, ε_d, seeds) = abundant (16, 25,
  0.05, 200), mid (4, 10, 0.1, 100), scarce (1, 5, 0.2, 100) ×
  the four arms. Refined P3-1c': α's win surplus and gate share
  advantage over β appear and grow as machinery scarcity rises
  (scarce > mid > abundant ≈ 0), driven by differential erosion
  (alive-count asymmetry between the initial halves); P3-1b
  (both = drift null) should hold in every regime.

**EW-4 evolvable fidelity (deferred unless time permits).** Π vs π
with copier replication breeding true (needs a replication rule —
deferred with it), static vs wound-driven environments; does the
world select its own mutation rate (K-vs-k, error threshold
dose–response)?

## Instruments

Compiler `gen_earned.py` (family-separation doctrine: gen_gated.py
stays bit-stable for paper #3; F4 imports and re-uses, never edits).
Drivers ew1.py, ew2.py, ew3.py mirroring ow*.py: headless engine,
`--trace`/`--dump-screen`, per-run exact accounting via replay,
Pool-driven seed sweeps, CSVs beside the drivers, one results md
per stage, pre-registration verdicts stated against this file.

## Honest limits, stated up front

The copy rules exist eternally in frozen law — what is earned is
their exercise, not their possibility; content-bearing descriptions
(the interpreter) remain the next rung. Copying is east-only. The
Π/π distinction and ε are authored (second-order regress). The
machinery row is a separate habitat: copiers do not compete with
matter for tape space (a deliberate first instrument; the shared-
habitat ablation is queued). Replication of copiers is absent in
EW-1..3: copier demography is birth-by-matter + death only.
