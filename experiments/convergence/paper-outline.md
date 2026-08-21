# Paper #1 outline — every section mapped to an existing artifact

Working title: *State-serializable is not distribution-faithful:
conflict-excluded batching shifts absorbing-state critical points.*
Target: AUTOMATA / ACRI / JCA-class venue (per §10 of the research
notes and the who-benefits scoping in `related-work.md`).

| section | content | artifact (done ✓ / pending) |
|---|---|---|
| 1 Introduction | transactional batching is what practitioners write; serializability is its usual justification; we show the surviving measure shift has qualitative consequences near criticality | `related-work.md` who-benefits ✓ |
| 2 The update scheme | weighted sampling w/o replacement from stale state + conflict exclusion; serializability proof sketch (disjoint footprints commute, apply never re-validates) | research notes G7 entry ✓ |
| 3 Mechanism | 2-site closed form: P_batch/P_seq = (1+4λ)/(1+3λ); stale state removes the self-rescue channel; null at size 1 ⇒ interaction effect ⇒ critical-region-specific | `toy-model.md` ✓ (incl. engine validation within 1σ) |
| 4 Contact process results | λc(N): survival curves, transient peaks walking with N; supercritical mild enhancement | `results-l*-v2.csv` (post-footprint-fix; pending completion) + `results.md` rounds 2–4 ✓ |
| 5 Second process | SIR/isotropic percolation: pc(N) shift of the outbreak transition | `sir.cfg` ✓, `results-sir-n1.csv` ✓, n8 pending |
| 6 Implementation-sensitivity aside | the phantom-footprint episode: two implementations of "conflict-excluded batching" (spec-true vs body-walk) give different measures — the bias family is bigger than one scheme; also the toy model as a validation probe for engines | commit 725ef8b + `toy-model.md` appendix ✓ |
| 7 Related work | α-synchronism, parallel KMC (exact vs approximate), BN update schedules, stochastic rewriting parallel independence | `related-work.md` ✓ (verify τ-leaping citations) |
| 8 Reproducibility | 76 KB dependency-free engine, deterministic replay, one-command sweeps | HEADLESS.md, `sweep.sh`, `sweep-sir.sh` ✓ |

Still missing for submission quality:
- λc(N) v2 curves complete + a finite-size point (one larger field).
- Proper τ/exponent fits with binning and errors (replace octave-ratio
  eyeballing); ~200 lines of analysis script.
- SIR pc(N) shift quantified (logistic fit of P(large) vs p per N).
- Literature pass verification for the τ-leaping / PDES citations.
- Optional strengthening: k-site generalization of the toy model, or
  a mean-field ODE for the batch dynamics.
