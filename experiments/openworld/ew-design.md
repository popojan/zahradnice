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

## EW-6 — description replication and healing (registered session 11)

EW-5's registered gap: a wounded codon never heals, so the machine
population is a phenotype with a countdown (q-dose collapse). EW-6
gives the description heredity and repair via two-copy redundancy.
Geometry: EW-5's stack with row 2 = BACKUP row (tape 1, backup 2,
code 3, mach 4, reg 5). New machine, the transcriptase Φ, on the
machinery row (shared habitat, same exclusion/decay), with two
symmetric rule groups, one header per codon each:
BACKUP — read the codon above ((−1,0)), write it into an empty
backup slot at (−2,0), advance east; RESTORE — read the backup at
(−2,0), write it into an EMPTIED code cell at (−1,0) (the heal),
advance east. Plus the standard weight-0.1 drift. The q-wound
rules anchor on codon glyphs wherever they stand, so q wounds
BOTH copies uniformly; a column's content is lost only when both
copies die between Φ visits (classic redundancy reliability).
The codon table gains `t` → Φ: the machine that heals the
description is itself encoded in the description — E10's
self-reference extended to the repair layer. D layout (ring 24,
even cols): w at 0/6/12/18, t at 8/20, b at the remaining six;
machines seeded at codon+1 (4 Ω, 2 Φ, 6 Π; density 1/2).
Constants otherwise EW-5's (cad 4, M 5, EST 200, BLOCKS 200,
ε_d 0.005, drift 0.1); the EST phase doubles as the initial
backup pass (Φ fills the empty backup row before wounds begin).
Arms (100 seeds each): healed (no q), healed-q16/q8/q4, bare-q8
(no Φ, no t codons — the EW-5 configuration under q8), no-t-q8
(Φ seeded but no t codon: the repair machinery decays
unreplaced). Predictions:
  P6-1 (healing): healed-q8 survival is at least half of the
    healed no-q rate — against EW-5's 0/100 at q8. Description
    wounds stop being lethal when the description can be copied
    back.
  P6-2 (the machine is the healer): bare-q8 reproduces EW-5's
    collapse (~0).
  P6-3 (infrastructure tax): healed (no q) ≤ EW-5 kernel's 77/100
    (backup machinery crowds the habitat and dilutes the C
    lottery), and the tax buys robustness: healed-q8 ≫ bare-q8.
  P6-4 (self-reference again): no-t-q8 lands between bare-q8 and
    healed-q8 — repair capacity is transient when the repairer is
    not encoded (E10 at the repair layer).
Metrics: survival, alive, machinery Π/Ω/Φ, constructions by
type, restores and backups performed, codons standing (code row
and backup row separately), exact accounting.

## EW-7 — the codon table into matter (registered session 11)

The last authored mapping. In EW-5/6 the translation table (codon
→ product) is header content: matter spells constructions, but
what the spelling MEANS is frozen. EW-7 moves the mapping's
existence, locality, and persistence into matter, by the F3 gate
move applied to translation: the frozen table holds the SPACE of
mappings — one translation body per table glyph, with the glyph as
a literal read from a TABLE row — and matter selects which mapping
is live, column by column. There is no global anything in this
substrate (A1): even a “universal” code must be physically
instantiated at every column where it is used, and its uniformity
is a maintained condition, not a given — which is precisely the
experiment.

Geometry (ROWS=6): tape 1, code 2, TABLE 3, mach 4, reg 5. The
translator reads the codon at (−2,0) and the table glyph at
(−1,0) (contiguous body); execute/build/land as in EW-5. Two
authored tables live in the frozen rule set: table `1` = {b→Π,
w→Ω}; table `2` = the swap {b→Ω, w→Π} (compiled in every arm;
worlds without `2` on screen never fire it — the space of
mappings is the honest residue). New machine, the table-copier Ξ
(mach row, same exclusion): read the table glyph below, copy it
east into an EMPTIED table cell, advance; plus drift. Ξ is
IMMORTAL and seeded at two empty even-column slots (registered
scaffolding — the x-codon closure “the code encodes the machine
that maintains the code” is the named next increment, as is the
table-1-vs-table-2 mosaic competition, evolution of the genetic
code proper). Byte r erases one uniformly random table glyph.
World otherwise = EW-5 kernel exactly (ring 24, D = w×4 + b×8,
8 Π + 4 Ω seeds, ε_d 0.005, cad 4, M 5, EST 200, BLOCKS 200,
p wounds), 100 seeds/arm. Arms: live (uniform table-1, no r);
no-code (table row EMPTY); wounded (r every 4th block, no Ξ);
maintained (same r, Ξ×2). Predictions:
  P7-1 (inert when whole): live ≈ EW-5 kernel (|z| ≤ 2 against
    77/100) — an intact uniform code changes nothing.
  P7-2 (the code must exist): no-code performs ZERO constructions
    and collapses to the no-executor endgame — translation
    without a physically present mapping is not slow, it is
    absent.
  P7-3 (per-column code death): wounded-code survival collapses
    as table cells erode; every lost cell silences translation at
    that column, and machinery decays unreplaced there.
  P7-4 (maintained universality): with Ξ, survival is restored to
    at least half of live — code uniformity is maintainable by a
    machine at wound rates that kill the unmaintained code.
Metrics: survival, alive, machinery counts, constructions, table
cells standing, repairs by Ξ, exact accounting.
  **Amendment 8 (post-smoke, pre-sweep): keepers must keep
  moving.** At drift 0.1 the maintained arm died (0/5) WITH a
  perfectly repaired code (49.6 repairs, 23.6/24 cells): two
  slow immortal keepers are standing obstacles in the machinery
  traffic — their parking columns are translator landing slots,
  and construction fell 60% (EW-6's maintenance-rent law,
  amplified by immortality). Registered fix: keeper drift weight
  1.0 (fast transit; 8-seed scan: Ξ×2 drift 1.0 → 5/8 with
  builds restored to 233 and table 19.6/24 — fast keepers trade
  a little repair latency for the traffic they stop blocking).

## EW-8 — the code's keeper, and the frozen accident (registered
session 12)

Two of EW-7's named residues in one world: (i) the x-codon
closure — the code encodes the machine that maintains the code;
(ii) the table-mosaic competition — does selection freeze the
code? Geometry: EW-7's stack at ring 32 (the EW-6 lesson: three
machine species need b×10). D (even cols): w at 0/10/20, x at
4/14/24, b at the remaining ten; seeds at codon+1 (3 Ω, 3 Ξ,
10 Π). Tables in frozen law: T1 = {b→Π, w→Ω, x→Ξ}, T2 = the b/w
swap with x→Ξ conserved (code maintenance is universal across
codes, like translation's core). Keepers are MORTAL (ε_d 0.005
like all machinery) and rebuilt only by translation of x. Byte r
= one table wound; p wounds as always; cad 4, M 5, EST 200,
BLOCKS 200, 100 seeds/arm.

A structural observation registered up front, because it shapes
the predictions: in this world machinery is unpriced by matter
and mixes eastward around the ring, so a locally dysfunctional
code's cost (wrong build ratios) is borne GLOBALLY — the bad
code is a commons polluter, and local selection should have
nothing to grip (night-11's lesson recurring at the code level).

Arms: baseline (pure T1, no r); closure (pure T1, r/4); no-x
(x cols become b, keepers seeded but unreplaceable, r/4); pure2
(all T2, no r); mosaic (half T1, half T2, r/4). Predictions:
  P8-1 (closure): survival(closure) ≫ survival(no-x) — the loop
    “the code encodes the code's keeper” holds table maintenance
    up under wounds once keepers are mortal.
  P8-2 (the dialect): pure-2 COLLAPSES toward the no-code class:
    the swapped code turns the same description into ten
    translators and three copiers — D and code are co-adapted,
    and the code's content matters exactly through the
    description written in its dialect.
  P8-3 (the frozen accident): the mosaic boundary drifts WITHOUT
    directional bias (final T1 share centered on 0.5 across
    seeds): machinery mixing makes the bad code's cost global,
    so selection cannot remove it — the code fixes by drift.
    (Measurement honestly powered: two boundaries, ~50 table
    wounds; mean share with CI is the registered statistic.)
  P8-4 (the commons): mosaic survival lands between the pure
    arms, near the global-ratio expectation — everyone pays for
    half the world's dialect error.
Metrics: survival, alive, machinery by type, builds by product,
keeper repairs, table composition (T1 share), exact accounting.

## EW-9 — heritable machine-lineage fidelity (registered session 12)

The last residue: fidelity has so far ridden the LAW lineage
(which machine type builders fund); EW-9 makes it a heritable
trait of machine lineages and asks whether the world selects its
own mutation rate. New rule (gen_earned.copier_replicate):
a copier SPLITS — writes its own glyph east into an empty slot,
keeping itself — at weight w_r, **gated on standing over living
law** (a `%` cell on the regulatory row below: the machine
reproduces only where the law it maintains is alive). This
gating is the load-bearing design decision, registered with its
reason: without it, a sloppy machine's damage is a commons cost
(machinery mixes; demography is decoupled from work) and
fidelity is invisible to selection — the recurring lesson of
EW-8/night-11. With it, machine fitness = local law health.

World: EW-5 geometry, ring 24, uniform-α start; NO builds, NO
translation — machinery demography is replication − decay only
(Π faithful and π sloppy at ε=0.05 breed true; no Π↔π switch:
pure lineage competition from a 50/50 seed, 6+6 at density 1/2).
Copy/walk/pass as usual for BOTH types on byte C; replication
weight w_r smoke-tuned (target standing density ~1/2, logistic
via slot exclusion — a full row gridlocks). Three environments
(arms), p wounds M 5 except where stated:
  neutral — mutant stamp target ν has α's EXACT law under
    another glyph (the EW-1 neutral-pair trick): miscopy is
    consequence-free.
  deleterious — mutant target d owns NO rules: a d-stamped locus
    is dead law; sloppy machines poison their own pasture.
  beneficial — mutant target μ = spawner + night-2-style wound
    handler (dynamic repair, superior under the wound regime);
    only sloppy machines can create μ, and machines standing
    over the μ-land they made breed on it.
Predictions:
  P9-1 (neutral): lineage share drifts — final Π share centered
    on 0.5.
  P9-2 (deleterious): the faithful lineage wins — mutation load
    is machine-lineage-selectable once reproduction is gated on
    the machine's own work.
  P9-3 (beneficial): the sloppy lineage persists or wins, and
    world survival correlates with π presence — the mutation
    rate the world keeps is the one its environment pays for.
Metrics: final Π/π counts and share, α/ν/d/μ gate composition,
alive, survival, exact accounting; 100 seeds/arm.
  **Amendment 9 (pre-run): the nurture spectrum.** The registered
  beneficial target (spawner + wound handler) confounds matter
  dynamics with machine selection. Refinement: ALL mutant targets
  carry α's exact matter law (spawner) — except d, which carries
  none — and differ ONLY in machine-nurture, the weight of the
  replication gate over that allele: d = 0 (machines cannot breed
  over dead law), α and ν = 1, μ = 2 (a law that feeds machinery
  twice as well — the EW-3 builder phenotype translated into the
  replication economy). One axis, no confounds: P9-2/3 become
  "machine lineages evolve their fidelity toward the pasture
  their errors plant." Replication is per-allele-gated (`&` on
  the regulatory row below, weight w_r × nurture), machines split
  east into empty slots, w_r smoke-tuned for standing density
  near 1/2.
  **Amendment 10 (post-scan, pre-sweep): mass normalization and
  power.** At ε=0.05 selection events are ~3 per run and drift
  swamps everything. Worse, the naive sloppy machine carries MORE
  total copy mass (faithful 1 + mutant ε), and copies are moves:
  under exclusion the restless queue more and breed less (east
  slot full) — a mobility-fecundity confound that tilted even the
  NEUTRAL arm toward the faithful lineage (0.63 at 16 seeds).
  Fix: the sloppy machine's faithful headers carry weight 1−ε, so
  total copy mass is 1.0 for both lineages and per-copy error is
  exactly ε (gen_earned.copier_copy faith_w). Registered sweep
  constants: ε = 0.2, w_r = 0.02; the registered statistics are
  the per-arm mean faithful-share against 0.5 AND the between-arm
  contrasts (deleterious vs neutral, beneficial vs neutral) at
  100 seeds.

## EW-10 — linkage, or what selection-for-evolvability needs
(registered session 12)

EW-9's asymmetry law (costs private, gifts public) is biology's
own verdict on second-order selection — not a defect but a
derivation. What real mutator dynamics have that EW-9's world
lacks is LINKAGE: the mutator allele rides the genome its errors
improve, so the gift is cotransmitted. EW-10 supplies linkage in
its two separable forms and asks whether either turns selection
FOR evolvability on:
  spatial linkage (VISCOSITY) — walk and pass weights drop 1 →
    0.1: machines stay near their birthplace, offspring are born
    east-adjacent onto the parent's plantings, and the
    lineage–pasture association decays slowly instead of within
    a few laps of the ring;
  recognitional linkage (KIN pasture) — the μ-nurture replicate
    rule belongs to π ONLY (full excludability: Π cannot breed
    over μ-land at all). The linkage is authored in this arm, and
    that is the point: the experiment tests whether linkage
    rescues second-order selection, not whether linkage
    self-assembles (that is the next revocation, named at the
    end).
2×2 arms (public/kin × normal/viscous), EW-9's constants
(ε 0.2, w_r 0.02, mass-normalized), 6+6 seeds, 100 seeds/arm;
EW-9's neutral (0.499) and beneficial-public (0.492) anchor the
drift line. Plus the strongest form, INVASION FROM ZERO: arms
invade-public and invade-kin seed 12 faithful machines and add a
rare symmetric fidelity switch Π↔π (σ = 0.001, self-rewrite on
byte C, ~5 switch events per run — low enough that switching
alone cannot equilibrate shares): does the mutator lineage,
created only by the switch, invade through the kin channel?
Predictions:
  P10-1 (kin): π wins decisively (share_f ≪ 0.5) — privatize the
    gift and selection FOR evolvability turns on.
  P10-2 (viscous, public pasture): π gains over the EW-9 public
    baseline but less than kin — spatial linkage partially
    privatizes what recognition privatizes fully.
  P10-3 (interaction): viscous+kin strongest for π.
  P10-4 (invasion): invade-kin ends π-majority from an all-Π
    start; invade-public stays near the switch balance — the
    mutator invades exactly when linkage exists.
Metrics: share_f, births per lineage, miscopies, switch events,
μ-land, survival, exact accounting.

## EW-11 — walls are linkage: the unit of selection, re-earned
(registered session 13)

EW-10's kin channel authored recognition; EW-11 buys the same
excludability with GEOMETRY. A full-column wall (glyph `|` on
tape, code, machinery, and regulatory rows at a boundary column)
isolates a sector with zero new rules: the spawner's east-content
variants match no wall, the copier cannot stamp across, the
translator cannot build onto or land past it, machines cannot
walk through. A sector then holds its own description, its own
machinery, its own law, and its own matter — and succeeds or
fails AS A UNIT. The claim under test: individuality is the
physical form of linkage, and with it, sector-level selection can
act on genome-encoded fidelity where lineage-level selection
failed (EW-9) and recognition had to be authored (EW-10). The
organism, deleted in night 7 as an authored ingredient, re-enters
earned — as containment.

World: ring 64, ROWS 6 (tape/fuel-idle/code/mach/reg), 4 sectors
of 16 (walls at cols 15/31/47/63). Per-sector genome on the code
row (even cols 0..12 within the sector): w-codons at 0 and 8
(translator self-reference), five machine codons at 2/4/6/10/12 —
`b` → faithful copier Π in FAITHFUL genomes, `p` → sloppy copier
π (law-miscopy ε = 0.2, mass-normalized) in SLOPPY genomes.
Codons stop two short of the wall so builds and landings stay
inside. Alleles: α = the lottery walker (A>B.writeA; night-2
MIXED/DIED — fragile), μ = the dynamic repairer (walker + wound
handler B>A.req~ — robust); only a sloppy machine can create μ
(miscopy α→μ, back-mutation μ→α at the same ε). Machinery
cadence 16 (EW-1's requirement for these dynamic alleles),
ε_d 0.005, M 5, EST 200, BLOCKS 200, 100 seeds/arm.

Arms: walls-mixed (2 sloppy-genome + 2 faithful-genome sectors,
alternating); open-mixed (identical layout, wall columns empty —
the leak control; sector bookkeeping by initial column ranges);
walls-faithful (4 faithful sectors — the baseline death rate);
walls-sloppy (4 sloppy sectors — the baseline rescue rate).
Predictions:
  P11-1 (calibration gradient): walls-sloppy sector survival ≫
    walls-faithful — the rescue channel (discover the robust
    allele by machine error) works at sector scale.
  P11-2 (THE UNIT CLAIM): in walls-mixed, sloppy-genome sectors
    outlive faithful-genome sectors by a wide margin — selection
    FOR evolvability at the sector level, with no recognition
    rule anywhere: the wall is the linkage.
  P11-3 (the leak control): in open-mixed the per-region gap
    collapses — μ-land, machinery, and law flow, the gift is
    socialized, and EW-9's verdict returns.
  P11-4 (attribution): μ first appears in sloppy-genome sectors
    (trace-attributable by column).
Metrics: per-sector alive, μ-gates, machinery, survival (sector
alive ≥ half its width); world survival; discovery attribution;
exact accounting.
  **Amendment 11 (post-smoke, pre-sweep): the hop, and island
  extinction.** Two instrument findings. (i) Sealed walls
  deadlock: an east-only machinery economy in a bounded sector is
  a TERMINAL CONVEYOR — machines make one transit, pile at the
  wall, the pile grows back over the build sites, translation
  dies; the ring's wrap was load-bearing for circulation.
  Registered fix: gen_earned.wall_hop — machines (only) cross a
  wall into an empty cell two east at weight 0.05; stamps, law,
  and matter stay walled, so the genome stays home while
  machinery migrates rarely (the island-model dial; migrating
  sloppy machines carry mutagenesis with them, so μ can appear in
  faithful sectors at migration-delayed rates — expected and
  informative). (ii) With machinery healthy and μ established,
  walled sectors still all died at the registered wound schedule:
  a 15-cell isolated matter population is a metapopulation island
  — extinction is absorbing (no spontaneous generation) and the
  open ring survives the same schedule by recolonization rescue.
  Real island biogeography, but it saturates the fidelity signal.
  Registered rescale: M 5 → 10, BLOCKS 200 → 120, where the
  8-seed scan gives sloppy 10/32 vs faithful 0/32 sector
  survival.

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
