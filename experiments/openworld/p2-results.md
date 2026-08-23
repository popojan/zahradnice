# P2 — the description rung (interpreter probe)

Date: 2026-08-23, session 9. Registration: ew-design.md §P2.
Verdict up front: **all 5 exit criteria PASS on the first run,
zero engine changes** — descriptions with content are mechanically
expressible under the frozen rule table. The (ctx, ctxrep) header
pair, which F3 used to stamp and F4's copier used to inherit, is a
CODON TABLE when re-aimed across rows: translation, transcription,
and mutagenesis of descriptions all come from the same proven
geometry.

## Run

`./zahradnice-headless experiments/openworld/p2_interpreter_probe.cfg
--seed 7 --screen 8,14 --input "bttttssssvuxxxxx" --stats`

Final screen (rows: product / heads / code / daughter):

```
 AΠAΠ
     Ω     π
>AbAb  AAAA
 AbAb  AbAA
```

15 events = 16 bytes − the pre-registered end-of-tape no-op.

## Criteria

1. **Translation, machine codon included** — Ω walked the S1
   description ">AbAb" and wrote its codon-mapped image on the
   product row: A→A, b→Π. The world's first machine CONSTRUCTED
   FROM A DESCRIPTION: the glyph Π appears because matter one row
   below says `b`, through a frozen codon table (one header per
   codon; ctx = codon, ctxrep = product). PASS.
2. **End-of-tape stall** — the 5th x byte no-oped (code cell empty
   under Ω; screen-space reads as `~`, matching no codon). PASS.
3. **Transcription + mutagenesis** — faithful Π strand-copied S1 to
   the daughter row exactly, INCLUDING the uninterpreted machine
   codon b (the copy/interpret duality: one machine executes the
   description another blindly copies). Sloppy π transcribed S2
   with per-symbol flips: 7/36 across 9 seeds = 0.194 vs expected
   ε/(1+ε) = 0.2 — independent per symbol, since transcription
   reads the original template, not the daughter. A flipped codon
   changes what a future translation constructs (composition with
   criterion 1 is transitive). PASS.
4. **Track discipline** — the parked transcriptase blocks the
   translator's path under exclusion until erased (the registered
   v phase); the probe's phase order proves the jam and its
   clearing. PASS.
5. **Accounting** — event count and final screen reconcile with the
   phase-level prediction cell for cell. PASS.

## What this settles for the next experiment

The description rung is affordable: strand-copying needs no offset
constant (daughter row at (+2,0)); the codon table is the honest
law-side residue, now one level up from F3's gates (matter no
longer just ACTIVATES law per place — it SPELLS constructions,
machinery included). The next experiment — not this probe — is the
self-reproduction kernel: integrate constructed machines into a
living F4 world (a built Π must actually copy), let a description
encode the transcriptase itself, and ask what selection does to a
world whose machinery flows through copyable, mutable, priced
descriptions. That experiment inherits every earned channel:
descriptions are inherited by machinery (EW-1/3), mutated by
machinery (EW-4), and will be priced (EW-2).
