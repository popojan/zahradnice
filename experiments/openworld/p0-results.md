# P0 — gate mechanics probe (open-world line, M1-A0)

Date: 2026-08-23. Session 1 of the open-world arc. Design source:
`backlog/research/substrate-mismatches.md` §M1-A0 (gated uberprogram).
Verdict up front: **all exit criteria PASS, zero engine changes** —
law-subsets-in-matter is mechanically expressible under a frozen rule
table, and the compiler encoding for OW-1 is settled (`&`/`%` gates
with the allele in header fields 6/7).

## Question

Can a regulatory row parallel to the tape gate rules per locus —
rule fires iff its gate glyph sits at (−1,0) — with gates readable,
writable, and erasable by rules themselves, all under A4 (the rule
table never changes; only which of it matter permits)?

## Design

One probe cfg (`p0_gate_probe.cfg`), one bootstrap rule that
atomically renders eleven loci (gate row above, tape row below) plus
a rate-test pair, then hand-scripted trigger phases:

| locus | tape | gate | expectation |
|---|---|---|---|
| L1 | A | `g` | t converts A→B (literal ASCII gate) |
| L2 | A | — | stays A (gate absent) |
| L3 | A | `Γ` | t converts A→D (non-ASCII gate glyph) |
| L4 | A | `h` | stays A (wrong glyph — specificity, not mere occupancy) |
| L5 | P | — | m writes gate g (matter→law ON), t→Q, t→R (gate persists), e erases gate (matter→law OFF), t must NOT fire R→W |
| L6/L7/L8 | v | `Γ`/`g`/`h` | `&`-gate, allele in header field 6, two headers share one body: Γ and g convert to V, h stays |
| L9/L10/L11 | w | `g`/`Γ`/`h` | `%`-gate, one header, field-6-OR-field-7 disjunction: g and Γ convert to Z, h stays |
| rate | x,y | `g`,`Γ` | x carries TWO gated idempotent rules, y ONE; r-events split 2:1 |

Run: `./zahradnice-headless experiments/openworld/p0_gate_probe.cfg
--seed 7 --screen 10,28 --input "b tttttttt m tt e ttt r×60"`
(spaces for readability; the actual string is contiguous) with
`--trace`/`--stats`.

## Results

Final screen (dump), exactly the predicted state:

```
g Γh ΓghgΓh
BADARVVvZZw
gΓ
xy
```

- **Gating & specificity**: L1→B, L3→D applied once each; L2 (no
  gate) and L4 (wrong glyph `h`) never converted. Gate matching is
  exact-glyph, not occupancy.
- **Non-ASCII gates**: `Γ` (U+0393) works as gate glyph in body
  literals AND in header fields 6/7; trace/stats render it legibly.
- **Law mutation, both directions**: `PmP` wrote gate g above L5
  (RHS cell above the anchor — matter enabling law), P→Q→R then ran
  on the enabled law with the gate persisting (chromatin-like);
  `ReR` erased the gate; afterwards `RtW` was **considered 3×,
  applicable 0×, applied 0×** — the clean negative. An accidental
  positive control from a mis-typed first run: with a third t fed
  *before* the erase, R→W fired legitimately (gate still present).
- **The OW-1 compiler encoding**: a literal gate glyph lives in the
  *body*, which stacked headers share — so literal gates cannot vary
  per header. The `&` cell solves it: gate = `&` at (−1,0), allele in
  header field 6 → **one shared body, one header per allele** (L6 via
  ctx=Γ, L7 via ctx=g, both applied once; L8 rejected). `%` gives a
  **two-allele disjunction in a single header** (field 6 OR field 7:
  L9, L10 converted; L11 rejected). F2 rules leave fields 6/7 unused,
  so the allele channel is free.
- **Sampling**: 60 r-events split x:y = 37:23 (expected 40:20,
  binomial sd ±3.7) — weight-proportional global sampling over the
  applicable (rule, locus) set, with gated-off rules simply absent
  from the pool. Stacked identical headers are two distinct rules
  (idx 0/1, 18+19 applies). This is the mechanism behind the
  distributional-exactness claim OW-1 will assert: uniform gates ⇒
  applicable sets identical to the plain-compiled genotype.
- **Event accounting**: 71 applied = 1 bootstrap + 6 conversions +
  1 write + 2 advance + 1 erase + 0 blocked + 60 rate; no-op inputs
  don't count as steps. Deterministic under `--seed`.

## Geometry facts settled (via `zahradnice-check explain`)

1. Horizontal bodies assign off-row cells to LHS/RHS **by column vs
   the boundary column**: a cell above the `@1` column reads at
   (−1,0); a cell above the `@3` column writes at (−1,0). One
   horizontal rule can therefore read a gate, rewrite the tape, and
   rewrite the gate — the full M1-A0 loop in one body.
2. Vertical bootstrap bodies render arbitrary multi-row pictures
   relative to `@3`; rows starting with `#`/`^`/`=` remain the only
   layout hazard (none hit here).

## Deviations from the M1-A0 sketch (design doc should be read with these)

- The doc's "2^N gate subsets" is per-*world*, not per-locus: a locus
  has ONE gate cell, so per-locus law is glyph→subset — the **law
  allele** model (each glyph names a censused genotype). Confirmed as
  the honest minimal shape; multi-row gate stacks remain the later
  lift if per-locus subsets are ever needed.
- `%` caps per-header disjunction at 2 alleles; a rule shared by k
  alleles costs ⌈k/2⌉ headers over one body. Linear, fine.

## Exit

P0 PASSES. Next: OW-1 — gated compiler over an allele set of 3–5
censused F2 genotypes in `gen_family.py`, replay support in
`analyzers.py` (gate cell in `reqs()`), calibration against night-2
verdicts under uniform gates, and the dry-run cost measurement for
the ~100-rule union. Live-mode fidelity is not in question for this
line (no program switching; headless is the instrument of record).
