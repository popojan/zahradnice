# Related work, mapped onto the substrate

Status: 2026-09-12, written from memory — **verify every citation
before it enters a paper** (the literature-audit discipline of
`paper/related-work.md` applies). The point of this file is not
priority but *fit*: what each idea needs, and what the substrate
already gives it.

## The passage itself

- Wolfram, S. (2023). *What Is ChatGPT Doing … and Why Does It Work?*
  Closing remarks on neural nets: computing fabric of identical parts;
  calculus is incidental; 8 bits may suffice; bit-parallel systems
  (cellular automata) lack a known incremental-modification method
  "but there is no reason to think it isn't possible"; may be easier in
  complex cases; progressive network rewriting may beat weight tuning.

## Learning automata and bit-level learners (what the bandit already is)

- Michie, D. (1961). MENACE — matchboxes, beads, reinforcement by
  adding/confiscating beads. The bandit chapter's acknowledged lineage.
- Tsetlin, M. L. (1961/1973); Narendra & Thathachar (1974, 1989).
  *Learning automata*: L_R-I / L_R-P are exactly the bandit's two
  variants.
- Granmo, O.-C. (2018). *The Tsetlin Machine* (arXiv:1804.01508). Teams
  of Tsetlin automata learn conjunctive clauses over Boolean literals;
  Type I/II feedback is a global scalar plus local automaton state; bit-
  level, parallel, ASIC/FPGA implementations; ~98% MNIST. **Closest
  existing scalable answer to Wolfram's question.** Fit: a synapse glyph
  with ±1 learning rules *is* a Tsetlin automaton; the difference is
  that the substrate has geometry (spatial synapses, structural
  plasticity) where the TM has a fixed clause table and a central vote.
  Convolutional TM (Granmo et al. 2019) is the spatial variant to
  compare against at R5.2.
- Courbariaux, Hubara, et al. (2016). *Binarized Neural Networks*.
  1-bit weights and activations, but trained with real-valued shadow
  weights and the straight-through estimator — calculus by the back
  door. The fabric's token counts are low-precision shadow weights
  without the calculus.

## Depth without credit assignment

- Yilmaz, O. (2014). *Reservoir computing using cellular automata*
  (arXiv:1410.0162); Nichele & Molund (2017). *Deep reservoir computing
  using cellular automata* (arXiv:1703.02806). Elementary CAs (rule 90
  etc.) as reservoirs with a trained linear readout; competitive on
  5-bit memory tasks. Fit: R1.1 verbatim, with the readout learned by a
  MENACE rule instead of regression.
- Krotov, D. & Hopfield, J. J. (2019). *Unsupervised learning by
  competing hidden units* (PNAS). Local Hebbian rule with competition
  reaches near-backprop accuracy on MNIST with a supervised top layer.
  Fit: R1.2 — deposit on co-activity, confiscation as competition.
- Zhou, Lan, Liu, Yosinski (2019). *Deconstructing lottery tickets*
  (supermasks); Ramanujan et al. (2020). *What's hidden in a randomly
  weighted neural network?* (CVPR; edge-popup). A fixed random network
  contains a subnetwork, selected by a learned binary mask, that
  performs well. Fit: R1.3 — the mask is the only matter, magnitudes
  are laws; this is the "selection sees only what someone can keep"
  through-line of the kept paper, in a network.
- Frankle & Carbin (2019). *The lottery ticket hypothesis*. Background
  for the R5.3 prediction that learnability rises with size.

## Credit by broadcast

- Frémaux & Gerstner (2016). *Neuromodulated STDP and theory of
  three-factor learning rules* (Front. Neural Circuits). Local
  pre×post eligibility × global modulator. Fit: R2.1; the trigger bus
  is the modulator, the pair cell the eligibility trace.
- Williams (1992). REINFORCE; node/weight perturbation (Werfel, Xie,
  Seung 2005 on their scaling). The sampler is the perturbation source;
  variance grows with parameter count — the reason perturbation is a
  replica-ensemble method (R5.1), not a single-CPU one.
- Lillicrap et al. (2016). *Random synaptic feedback weights support
  error backpropagation* (Nat. Commun.) — feedback alignment; Nøkland
  (2016). *Direct feedback alignment* (NeurIPS) — error broadcast to
  every layer through a fixed random projection. Fit: R2.2 — the
  random projection is a glyph rolled at init per cell, the broadcast
  is the bus.
- Hinton (2022). *The Forward-Forward algorithm* (arXiv:2212.13345).
  Positive/negative passes, per-layer goodness, no backward pass. Fit:
  R2.3 — phase on the bus, goodness = fired-cell count, saturation as
  normalisation.

## Credit by geometry

- Liao, Leibo, Poggio (2016). *How important is weight symmetry in
  backpropagation?*; Xiao, Chen, Liao, Poggio (2018). *Biologically-
  plausible learning algorithms can scale to large datasets*
  (sign-symmetry). Feedback needs only the *sign* of the forward
  weight. Fit: R3.1 — in a spatial fabric the synapse cell is adjacent
  to both neurons, so sign symmetry is free; the remaining
  approximation is 1-bit stochastic error, which stochastic-rounding /
  low-bit-gradient results suggest tolerable.
- Scellier & Bengio (2017). *Equilibrium propagation* (Front. Comput.
  Neurosci.); Ackley, Hinton, Sejnowski (1985). Boltzmann machines;
  contrastive Hebbian learning (Movellan 1991; O'Reilly 1996). Two
  settles, local difference rule. Fit: R3.2 — quiescence is "settled";
  mass-action rates are linear, not Glauber-exponential, so the
  energy-function correspondence is approximate; optional rung.

## Rewriting the network

- Mordvintsev, Randazzo, Niklasson, Levin (2020). *Growing neural
  cellular automata* (Distill); Randazzo et al. (2020). *Self-
  classifying MNIST digits* (Distill). Local update rules, learned —
  but by backprop through time on a real-valued MLP per cell. The
  closest published relative of the fabric's *tasks* (R4.3) and the
  exact opposite of its *method*: Wolfram's objection (calculus) stands
  against NCAs and not against this line.
- Gilpin, W. (2019). *Cellular automata as convolutional neural
  networks* (Phys. Rev. E). Any CA is a small CNN; background for the
  transpiler and for why convolutions implement the sibling's matcher.
- Structural plasticity: Chklovskii, Mel, Svoboda (2004). *Cortical
  rewiring and information storage* (Nature) — capacity from wiring,
  not only weights. Fit: R4.1.
- Fatès (2014/2017), asynchronous CA; Nehaniv (2004) — already in
  `research-rl-ai.md`; relevant here only as the *contrast*: this line
  designs schedule-independence in, so the α-synchrony results become
  a self-test rather than a physics.

## Evolution of learning (tier 4 reprise)

- Dunlap & Stephens (2009, 2016) — evolution of learning under
  environmental predictability; Baldwin (1896); Hinton & Nowlan (1987).
  *How learning can guide evolution.* Fit: R4.2, the garden with
  classifiers.

## Hardware niche (why a clockless bit fabric is worth anything)

- Tsetlin-machine ASICs (Wheeldon et al. 2020, *Learning automata based
  energy-efficient AI hardware design for IoT*, Phil. Trans. R. Soc. A)
  — multiplier-free learning silicon; in-materio / physical learning
  (Stern & Murugan 2023, *Learning without neurons in physical systems*,
  Annu. Rev. Condens. Matter Phys.); asynchronous neuromorphic fabrics
  (Loihi, SpiNNaker) where a global clock and weight transport are the
  costly parts. Fit: foundations §5 — the substrate's light-cone
  causality is a design constraint these platforms share.
