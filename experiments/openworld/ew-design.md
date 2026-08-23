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

**EW-2 machinery economy.** Original registration: copiers priced,
dose–response of fuel influx vs law velocity (P2-1), starvation
reversion (P2-2), placement steering (P2-3). P2-1's bandwidth
dose–response was absorbed by EW-1's cadence sweep (time-priced
bandwidth). **Concrete fuel protocol (registered session 9, before
ew2.py ran):** 5 playfield rows — tape 1, MARKER 2, fuel 3,
machinery 4, regulatory 5 (all toroidal relations preserved; the
copier's fuel read (−1,0) lands on row 3). Copying costs one fuel
token `o` at the copier's own column, consumed back to the `.`
background; walks stay free; machinery is ETERNAL (no decay/build —
EW-3 owned demography; this isolates the fuel economy). The marker
row is static: `<` over the left half, `>` over the right; feed
rules anchored on markers drop `o` at (+1,0) under a weight-uniform
random marker of their half — so WHERE fuel lands is set by drive
byte composition (f = left, g = right): O9's instrument pointed at
the inheritance channel. Fuel is positional: a copy can occur only
at a fueled column, so stamps can leak at most one cell east of the
fed region (the stamp lands at anchor+1). Uniform-α world, ring 24,
copiers density 1/2, cad 4, EST 100, M 10, BLOCKS 150, feed 2
tokens after each wound, 100 seeds/arm. Arms: starve (no feed),
left (ff), right (gg), both (fg). Predictions:
  P2-2' (starve): ZERO copy events ever; wounds freeze; the world
    erodes toward the EW-3 none-arm endgame — an unpaid channel is
    an absent channel.
  P2-3' (steering): copy events anchor exclusively in fed columns
    (unfed-half copies = 0 exactly, up to the registered ≤1-cell
    stamp leak); the fed half stays alive/active, the unfed half
    approaches the starve arm; left and right arms mirror; both-arm
    symmetric.
Metrics per run: per-half copy counts (by anchor column), per-half
alive/active/`?`, fuel standing per half, exact accounting.
  **Amendment 5 (post-smoke, pre-sweep): the pass rule.** With
  eternal machinery the smoke run deadlocked: a wound repair can
  re-de-regulate the gate under a standing copier, which then can
  neither copy (no template) nor walk (guard wants a stamped
  target); east-only exclusion jams the whole convoy behind it and
  the economy dies. EW-3/EW-4 never saw this because mortal
  machinery melts jams (mortality is a jam-clearing service — noted
  as a finding in its own right). Fix, registered here: copiers may
  PASS — step east over an unstamped (`?`) locus without stamping
  it (literal `?` body cell, no ctx conflict); repair of a ?-run
  then proceeds west→east as templates become available. Also
  fixed pre-sweep: the world bootstrap now anchors on a dedicated
  glyph at reg col 0 (`^Zll`), pinning the marker halves to
  absolute columns (the smoke's random-α anchor rotated the layout
  against the analysis halves).
  **Amendment 6 (post-smoke, pre-sweep): two horizons.** The fixed
  smoke showed the steering claim holding exactly (0 unfed-half
  copies) but BOTH single-fed arms dead at the 150-block horizon,
  fed half included: east-only regrowth on a ring means a dead arc
  is not a static frontier but a PURSUER — wounds at the fed half's
  west edge cannot be repaired (west neighbour dead), so death
  advances at the wound rate and eventually laps the ring. The
  alive-contrast of P2-3' is therefore transient. Registered
  measurement: every arm runs at BOTH horizons, 60 blocks
  (mid-game, where the fed/unfed contrast should be visible) and
  150 (endgame). The pursuit itself is reported as a finding
  (an economy fed locally cannot survive embedded in a dead world
  under one-handed regrowth).

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

**EW-4 miscopy rescues the world (earning the mutation channel).**
Registered 2026-08-23 session 9, replacing the earlier
evolvable-fidelity sketch (copier replication stays deferred; the
machine trait is inherited through the LAW lineage instead: the
builder allele decides which machine type it funds). Setup: ring
24; allele α = spawner only, allele μ = spawner + build-copier;
world starts all-α with machinery bootstrapped at density 1/2 and
decaying (ε_d) — μ exists NOWHERE and is reachable only through a
sloppy copier's miscopy at a repair site. If μ is discovered before
the bootstrap machinery dies, μ-land funds new machinery, becomes
self-sustaining, and annexes the frozen α-land (EW-3 scarce
dynamics); if not, the world erodes to death (EW-3 none-arm
endgame). Machine error is thereby the world's ONLY source of law
novelty, and its evolvability lives in a destroyable matter
population. This is the first full matter→law→matter closure: the
sloppy copier's errors create the lineage that feeds copiers.
Arms: faithful (bootstrap Π, ε=0), sloppy ×3 (bootstrap π, ε ∈
{0.01, 0.05, 0.2}; build writes π — arm-uniform machine type),
nowound control (π, ε=0.05, drive without pokes). Constants
(smoke-tuned BEFORE the registered sweep; tuning scan over
ε_d ∈ {0.001,0.003,0.01} × M ∈ {5,10} at the middle dose put the
race where the dose curve spreads — 10-seed rescue rates 0/4/7 of
10 across the three ε doses): cad 4, M 5, EST 200, BLOCKS 200,
ε_d 0.01, 100 seeds/arm. Predictions:
  P4-1 (faithful): machinery decays; wounds freeze; the world
    erodes toward death — no rescue, ever (μ unreachable).
  P4-2 (sloppy, directional): rescue (final alive ≥ ring/2 AND
    copiers ≥ 1) occurs in a substantial fraction of seeds and
    vastly exceeds the faithful arm; rescued worlds end
    μ-majority.
  P4-3 (dose): rescue probability increases with ε across
    {0.01, 0.05, 0.2} (time-to-first-μ decreases).
  P4-4 (repair coupling): with no wounds there is no repair
    traffic, hence no `?` targets, hence ZERO μ ever — mutation is
    repair-coupled (mutagenesis is a metabolic service, exercised
    only where inheritance is exercised).
Metrics per run: rescue flag, final alive, gates α/μ/`?`, copiers,
apply-index of first μ stamp (mutant-header write onto a non-μ
gate), exact accounting.

## P2 probe — the description rung (registered session 9)

The ladder's next rung above the earned channels: descriptions with
CONTENT — an interpreter in frozen law reading rule-encodings from
matter (the von Neumann move). The affordable kernel, noticed while
building F4: the (ctx, ctxrep) header pair IS a codon table. Three
mechanics, all reusing proven geometry, probed in one cfg
(`p2_interpreter_probe.cfg`, screen 8×14; code row 3, heads row 2,
product row 1, daughter-strand row 4):

1. **Translation (execution)**: constructor head Ω reads the code
   glyph below itself (`&` LHS, ctx) and writes the ENCODED product
   above itself (`&` RHS, ctxrep), advancing east under exclusion.
   Codon table registered: A→A (matter), b→Π (a MACHINE — the
   description encodes machinery). One header per codon; the
   description is matter; the table stays law-side (the honest
   limit, now one level up).
2. **Transcription (heredity)**: strand-copier Π reads the code
   glyph below itself and writes it to a `?` slot on the daughter
   row below the code row ((+2,0)) — string replication with no
   offset constant, semiconservative-shaped. The machine codon is
   copied UNINTERPRETED (von Neumann's duality: the same
   description is executed by one machine and blindly copied by
   another).
3. **Mutagenesis of descriptions**: sloppy transcriptase π carries
   (A,b)/(b,A) headers at ε=0.25 — a flipped codon in the daughter
   changes what a future translation CONSTRUCTS, machine glyphs
   included; mutation reaches machinery through its description
   (composition with mechanic 1 is transitive and is not re-probed).

Exit criteria: (i) product row = codon-mapped image of the code
string, including a constructed Π; (ii) translator stalls at
end-of-tape (extra byte no-ops); (iii) daughter strand = faithful
copy under Π, ε-flipped under π across seeds; (iv) parked machines
jam successors (exclusion) until erased — phases must clear the
track (v byte); (v) event accounting reconciles. The full
self-reproduction loop (translate the transcriptase's own
description, integrate constructed machines into a living F4 world)
is the NEXT experiment, not this probe.

## EW-5 — the self-reproduction kernel (registered session 10)

The description rung goes live: constructed machines must WORK, and
the description must encode the machinery that executes it.
Geometry (ROWS=6): tape 1, fuel 2 (unused — the price channel is
earned and rests), CODE 3, machinery 4, regulatory 5. All F4
relations preserved (tape reads reg at toroidal (−1,0) and mach at
(−2,0); copiers read reg at (+1,0)). The translator Ω lives ON the
machinery row — shared habitat with copiers under the same
exclusion; the two machine types read different rows (Ω the code
row at (−1,0), Π the regulatory row at (+1,0)): message and genome.

Translator law (one body + codon-table headers, gen_earned.
translator_rules): EXECUTE — read codon c below, require (0,+1)
and (0,+2) empty, write product(c) at (0,+1), land at (0,+2); a
built Π is a live copier the moment it is written, and codon w →
Ω is the self-reference (machine begets machine through the
description). DRIFT — unconditional advance-1 at weight 0.1
(deadlock-free passage over full slots and junk; execution becomes
statistical, the ring's circulation catches missed codons next
lap). Both machine types decay (ε_d, byte C). Translation builds
only into emptiness — rebuild happens exactly where death made
room: machinery HOMEOSTASIS through the description.

World: ring 24, uniform α spawner, p wounds (matter), EW-4's
economy (cad 4, M 5, EST 200, BLOCKS 200, ε_d 0.01, 100
seeds/arm). Description D on the code row: codon at even col j
builds the machine at j+1 — `b` (→Π) everywhere except `w` (→Ω)
at cols 6 and 18. Seeds: Π at the other odd cols (10) + Ω at 7,
19. Description wounds: byte q erases one random codon (b/w).
Arms:
  kernel      — full D, 10 Π + 2 Ω, decay both, p wounds;
  no-executor — same D, 12 Π, NO Ω (nothing reads the
                description; conservative extra 2 copiers);
  no-w        — D all-b (no self-reference codon), 10 Π + 2 Ω;
  q-dose      — kernel + one q per wound block.
Predictions:
  P5-1 (kernel): machinery reaches turnover steady state —
    construction events ≫ seeded machines, both product types;
    survival ≫ no-executor at the same decay.
  P5-2 (no-executor): zero constructions ever; machinery decays
    to nothing; the world dies (EW-4's faithful endgame). The
    seed constructor is irreducible — von Neumann's given.
  P5-3 (ORDERING, the kernel claim): kernel > no-w > no-executor
    in survival and final machinery. Without the w codon,
    translators decay unreplaced and rebuild capacity is
    transient: the self-reference codon is load-bearing —
    machinery that rebuilds its rebuilder outlasts machinery
    that does not.
  P5-4 (q-dose): survival degrades under description wounds;
    every lost codon is a permanent machinery hole (no D-repair
    in EW-5 — description replication is the registered next
    increment, EW-6).
Metrics per run: survival (alive ≥ 12 AND machinery ≥ 1), alive,
active, final copiers/translators, construction counts per product
type, exact accounting.
  **Amendment 7 (smoke-tuned, pre-sweep).** At the registered
  ε_d 0.01 / 2 w-codons the kernel died everywhere: the translator
  population (n=2) is a gambler's ruin, and its extinction takes
  the rebuild chain with it. Tuning scan (8 seeds, kernel vs no-w):
  ε_d 0.005 with w at {0,6,12,18} gives kernel 6/8 vs no-w 1/8;
  ε_d 0.0025 destroys the separation (no-w 6/8 — translators
  outlive the horizon on seed capital, the self-reference codon
  never gets to matter). Registered constants: ε_d 0.005, w-codons
  ×4 at cols 0/6/12/18 (Ω seeds at 1/7/13/19, Π at the other 8 odd
  cols). The q-dose arm becomes a THREE-POINT dose: one description
  wound every 16th / 8th / 4th block (12 / 25 / 50 q bytes; the
  12-codon description saturates fast under uniform erasure, so
  even q16 erodes most of it — the dose is effectively
  time-of-death of the description).

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
