# Inverse emergence, night 7: the tape commons — de-novo selection, and where it actually lives

The summit-ridge remove: no engine library, no lineages, no mutation
operator, no dials, no authored fitness. NINE uniform rules: the
ring is a circular chromosome of genes f/s; eternal polymerase
heads (F/S/W) patrol it east — crossing f costs 1 event, crossing s
costs 2 (a settle stroke; structure, not weight). Pokes wound the
TAPE only. **The only replication in this universe is repair**: a
head beside a hole writes a copy of the gene it covers. Variation is
standing initial diversity (random tape); selection, if any, must
emerge from pattern dynamics nobody named. The game nobody authored:
f is a public good (speeds every head); s taxes the commons.

Driver `night7.py` (sweep: ring {24, 48} × s0 {0.25, 0.5} ×
m {∞, 8, 4, 2} × 16 seeds = 256 runs of ~24k events, all exact,
119 ms/run, 8 s wall), mechanism probes `night7_mech.py`, data
`night7_commons.csv`. Watch it: `./zahradnice demos/inverse/tape.cfg`.

## Headline: a damage-controlled phase boundary — but not the one predicted

- **m=∞** (control): replication ledger identically zero — the
  night-5 expression law again: no wounds, no copying, composition
  frozen. 64/64.
- **Light damage (m=8), living commons** (min_tape 12–21, tape
  mostly full): composition dynamics are slow and near-neutral with
  a slight f edge where the ring is large and s is rare (r48
  s0=0.25: s-share 0.20→0.18, f out-replicating 4.5:1 gross), and a
  moderate s rise elsewhere (mechanism open — see below).
- **Heavy damage (m=2): the commons collapses** and s "wins" the
  remnant everywhere (0.22→0.56 … 0.37→0.69).

## The mechanism result (the night's real finding)

Three discriminators, each measured against instantaneous
composition (`night7_mech.py`):

1. **Per-capita replication: neutral** (s/f ratio 0.98 at m=8, 1.00
   at m=2). Copying follows composition exactly.
2. **Per-capita death: neutral** (0.99, 1.00). Pokes are uniform on
   visible tape, and shelter-by-cover doesn't bias per-event rates
   measurably.
3. **So no per-event rate is biased — yet composition moves.** The
   drift lives in STATE structure, not event rates: at m=2 the
   system spends ~90% of its time in the lowest tape quartile
   (n=346k of ~382k sampled events) — a permanently collapsed
   commons — and there the machinery covers s 82% of the time
   (residence follows structural dwell: settling on s is an extra
   event, and covered genes are poke-immune). During the rare
   regrowth phases the picture inverts: heads cover f almost
   exclusively (P=0.02), and the one completed wipe→regrowth
   episode produced an all-f tape.

Reframed honestly: **heavy damage does not select s within a living
commons — it destroys the commons, and s survives as what the
machinery shelters.** The slow gene's advantage is not replication
but company: the polymerase lingers on it, and lingering is
protection. The last gene standing is the one the machine was
standing on. Meanwhile f is what rebuilds worlds — regrowth is
f-work — but at m=2 rebuilt tape is eaten before it matters.

This is a de-novo result in the intended sense: no rule, weight, or
lineage names any of it. It is also NOT the tragedy-of-the-commons I
predicted in the design notes (s spreading through a living tape by
burst replication — refuted by discriminator 1). Predicted wrong,
measured right.

## Open questions (named, not hidden)

- The moderate s rise at m=8 on ring 24 (0.35→0.52) with both
  per-event flows neutral: candidate = partial-collapse episodes
  (min_tape 12) importing the shelter effect transiently. Needs
  wipe-count statistics over longer horizons.
- Scaling of the shelter effect with the structural cost (a
  3-stroke s should raise residence further — testable with one
  glyph addition).
- Head density: r48 runs 3 heads/48 vs r24's 2/24 (init positions
  limit deterministic placement to l/c/r) — density is a lurking
  variable in the ring comparison.

## Arc position

Nights 2–6 built repair, proliferation, heredity, selection,
variation, structural fitness. Night 7 removed the last authored
ingredient (the mechanism library) and got: expression-requires-
damage (again), per-event neutrality with state-dependent selection,
and a collapse phase where survival = machinery residence. The
summit question (self-copying structures) now has its substrate:
this tape world already contains machinery-mediated copying of
passive information; the remaining climb is genomes whose PATTERN
programs the machinery that copies them — closing the loop from
tape to behaviour to tape. That is night 8+, and it lives entirely
in matter; the laws are done.
