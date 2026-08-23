# P1 — copier mechanics probe (earned family, F4)

Date: 2026-08-23, session 8. Design + pre-registration:
`ew-design.md`. Verdict up front: **all 8 exit criteria PASS on the
first run, zero engine changes** — the earned-inheritance mechanic
(matter de-regulates, only machinery re-regulates) is expressible
under the frozen rule table, and the F4 compiler encoding is
settled.

## Run

`./zahradnice-headless experiments/openworld/p1_copier_probe.cfg
--seed 7 --screen 8,16 --input "bddtttccsssw" --trace --stats`

Final screen, exactly the pre-registered prediction (π stamps are
the run's stochastic content):

```
AA  A       FFFF     tape (row 1)
Π  Π     π Θ         machinery (row 6 = toroidal (-2,0) from tape)
ααααβ αββββαα?α?     regulatory (row 7)
```

10 events = 12 input bytes − the 2 pre-registered no-ops (build
into an occupied slot; copy into a β-stamped target).

## Criteria

1. **(−2,0) toroidal geometry** — bootstrap rendered the machinery
   row from a row-1 anchor; build wrote Π to (−2,0); copy rules
   anchored on row 6 read/write the regulatory row at (+1,·). PASS.
2. **Build** — d#1 applied once (A@0: gate α, empty slot); d#2
   applied 0 (slot now holds the built Π — self-limiting). Stats:
   applied 1 / applicable 1 / considered 6 — A@1 (slot occupied by
   Π) and A@4 (gate β vs ctx α) never applicable. PASS.
3. **Copy chains and stops** — Π@1 stamped α at reg@2 and advanced,
   then used the just-stamped cell as template for reg@3 (chaining);
   t#3 no-op at the β-stamped target (header (α,α): applicable 2 of
   6 considered; header (β,β): 0 of 6). PASS.
4. **Creation de-regulates; frontier stalls** — F@12 wrote F@13 +
   `?` over a live β gate; F@14 wrote F@15 + `?` over an empty gate;
   the fresh F@13 (gate `?`) was considered 3× and never applicable:
   growth halts one cell past the stamped region until a copier
   arrives. This stall is the load-bearing F4 dynamic. PASS.
5. **Miscopy is a machine trait** — π's mutant headers ((α,β),
   (β,α), w=0.25) fired alongside faithful ones; across 11 seeds ×
   3 copies: 7/33 template-flips = 0.212 vs expected ε/(1+ε) = 0.2
   (binomial sd 0.07). Seed 7 shows a miscopy breeding true (βββ);
   seed 8 shows back-mutation (βαβ). PASS.
6. **Walk** — Θ stepped east over a stamped locus exactly once under
   w (applied 1/1/1); `%` (allele disjunction) as the walk guard
   works. PASS.
7. **`?` as ordinary literal** — matched in LHS (copy's target
   requirement) and written in RHS (creation, over allele and over
   empty). PASS.
8. **Accounting** — final dump matches the cell-level prediction;
   stats event count and per-rule applied/applicable/considered all
   reconcile. (Full trace-replay exactness moves to the EW-1 driver,
   as with P0 → OW-1.) PASS.

## Design facts settled for the compiler

- **Copy body** (one shared body, headers = the F3 (ctx, ctxrep)
  stamp channel re-anchored on the machine):

  ```
  ==Πt~78αα        one header per allele; sloppy copier adds
  @~@@Π            (g,g') headers at weight ε
  &?  &
  ```

  `&` LHS at (+1,0) = template read; `?` LHS at (+1,+1) = target
  must be unstamped; `~` LHS at (0,+1) = destination slot empty
  (TASEP exclusion); RHS: field-3 `~` vacates, Π advances, `&`
  writes ctxrep = the stamp. Score/weight tails at wchar position
  10 after the 9-char field block, as in F3.
- **Exclusion gridlock**: a machinery row filled solid cannot move
  OR copy (every destination slot is occupied). "Saturated copiers"
  arms must seed density 1/2, not 1.
- **Walkers outrun their law**: a trail-walker allele de-regulates
  the cell it moves into, so it stalls after one step unless a
  copier chases the fork. Copier throughput rate-limits matter
  motion — the earned channel's time tax is structural, not just
  lottery dilution.
- **Erasure still leaves ghosts**: only creation writes `?`; wounds
  keep F3's ecological-inheritance ghosts. Conquest de-regulates,
  death does not.

## Exit

P1 PASSES. Next: `gen_earned.py` (F4 compiler: unstamped gated
family emission + copier law + machinery bootstrap), then EW-1
(necessity + conditional equivalence, pre-registrations P1-1..P1-3
in ew-design.md).
