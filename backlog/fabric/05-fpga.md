# FPGA: the fabric in silicon (parked, detailed)

Status: **parked 2026-09-12** at the user's request — recorded in full so
it can be picked up without re-deriving anything; the current flow
(zahradnice + torch sibling on the RTX box) is not to be interrupted by
it. Nothing here is started. Prices are approximate from memory and
must be checked before buying.

## 0. Verdict up front

- **Not now.** The RTX path answers every open question of the line
  (scale, learnability-vs-size, deeper fabrics) faster and for free.
- **Worth doing later for three reasons only**: (a) it is the literal
  "computing fabric" — a demo of learning in silicon with no
  multiplier, no gradient and no CPU is the most convincing artefact
  this line can produce; (b) energy per sample and latency are the one
  axis where a bit-fabric beats a GPU by orders of magnitude, and they
  can only be measured on hardware; (c) play — the user's stated
  motive, which is a legitimate trigger on this line.
- **Zero-cost first stage.** HDL generated from the same generator
  family as `gen_tm.py`, simulated and validated against zahradnice and
  the torch sibling. The board is the last step, not the first.

## 1. What maps to what

The Tsetlin-shaped fabric (`experiments/fabric/README.md` §2) is already
a circuit description. Per clause:

| fabric element | hardware element | size (rough) |
|---|---|---|
| literal automaton (state 1..2N, glyph `a..h`/`A..H`) | ⌈log₂ 2N⌉-bit up/down counter + "included" = MSB; feedback logic = a few gates fed by (type, right/wrong, clause out, literal, included) and one random bit | ~8–12 LUT4, 4 FF for N=8 |
| clause output (`1`/`0`) | AND over (¬included ∨ literal) for all 2·NIN literals — a LUT tree | ~NIN/2 LUTs |
| readout counter (Braille state glyph, K) | popcount of positive clause outputs minus negative, compared with θ; the stochastic counter can stay (an LFSR-driven walk) or be replaced by the exact sign, which is what inference wants | ~C LUTs |
| teacher / phase triggers (`p n i o f c`) | a tiny state machine sequencing evaluate → vote → feedback → next sample | negligible |
| feedback head walking east | **disappears**: all automata of a clause update in the same clock cycle. Exact by the schedule-independence contract (each update depends only on values decided before the phase) — the head was a serialization for the CPU engine | — |
| step-vs-skip rule weights π/(1−π) | compare an LFSR word with a constant threshold (π·2^w) per automaton or per clause; (S−1)/S, 1/S and Q become three constants | 1 LFSR per clause (or per row of automata), 16–32 bits |
| typing the input | input register loaded from the host or from on-board memory | NIN FF |
| exact accounting (score, trace) | a score counter; the "trace" is the UART log of predictions | negligible |

So one automaton ≈ 10 LUTs; a clause with 16 literals ≈ 170 LUTs; the
whole XOR fabric (C=16) ≈ 3k LUTs. One sample per ~3 clock cycles
(evaluate, vote, feedback) at 25–100 MHz ⇒ **10⁷ samples/s**: the
8-input XOR that takes 40 s in zahradnice trains in about a
millisecond. That is the demo.

## 2. Sizing: what a hobby board can and cannot do

Rule of thumb: LUT count ≈ 10 × (number of automata) for a fully
parallel *learning* fabric; a *trained* fabric compiles to far less.

| task | automata (literals × clauses) | parallel learning fabric | inference (compiled, trained) |
|---|---|---|---|
| XOR / parity-3 / 8-bit toys, C ≤ 64 | 16 × 64 = 1k | ~10k LUT — any ECP5 board; C ≤ 16 fits an iCE40 UP5K | trivial |
| 8×8 bitmaps, 10 classes, C = 200 | 128 × 200 = 26k | ~260k LUT — **too big for hobby boards**; time-multiplexed: yes | ~10k LUT, fits |
| MNIST 28×28 binarised, C = 1000 (≈95–97 %) | 1568 × 1000 = 1.57M | ~12M LUT — **no FPGA on earth as a flat fabric** (the largest are ~4M); state alone is 6 Mbit | **fits a hobby ECP5**: a trained clause keeps ~1–5 % of its literals, so 1000 clauses ≈ 10–20k LUT of AND-trees plus a popcount; or time-multiplexed from BRAM on an iCE40 at kHz–MHz image rates |
| MNIST *learning*, time-multiplexed | automata in external RAM (OrangeCrab 128 MB DDR3, ULX3S 32 MB SDRAM); per sample stream ~0.4–0.8 MB of automata through a small update pipeline | plausible at **~100–500 samples/s** (memory-bound), i.e. an epoch in minutes — comparable to a CPU Tsetlin machine, not to the GPU; real engineering (memory controller, pipelining) | — |

So the earlier warning was too blunt: *inference* on MNIST is
comfortable on a hobby board; *learning* on MNIST is not a flat fabric
but is possible time-multiplexed, and it is the flat fabric that carries
the "computing fabric" point. The honest hardware home of the flat
learning fabric at MNIST scale is an ASIC or a datacenter FPGA.

The LLM-on-FPGA reports (FlightLLM on an Alveo U280, LLaMA-class models
on Versal/Agilex, small quantised models on a Kria KV260) run on
datacenter or high-end SoC boards costing from ~€300 (Kria, slow tiny
models) to €3–15k, with weights streamed from HBM/DDR — a different
league and a different design (a matrix engine, not a fabric).

## 3. Boards (approximate street prices, verify)

| board | chip | logic | RAM | toolchain | ≈ price | fits |
|---|---|---|---|---|---|---|
| iCESugar / iCEStick class | Lattice iCE40 HX1K–UP5K | 1–5k LUT | none / 1 Mbit SPRAM | open (yosys, nextpnr-ice40, icestorm) | €30–60 | XOR toys, C ≤ 8 |
| **iCEBreaker** | iCE40 UP5K | 5.3k LUT | 1 Mbit SPRAM | open | €70–100 | XOR/parity, C ≤ 16; the cheapest sensible entry |
| **OrangeCrab 85F** | Lattice ECP5-85F | 84k LUT | 128 MB DDR3 | open (prjtrellis, nextpnr-ecp5) | €120–160 | C ≤ 500 flat; time-multiplexed MNIST learning |
| **ULX3S 85F** | ECP5-85F | 84k LUT | 32 MB SDRAM, HDMI, ESP32 wifi | open | €180–260 | same, plus a display for the demo |
| Digilent Arty A7-100T | Xilinx Artix-7 | 101k LC | 256 MB DDR3 | Vivado (free tier, heavy, proprietary) | €250–320 | same class; avoid unless Xilinx is wanted |
| Xilinx Kria KV260 | Zynq UltraScale+ SoC | 256k LC + ARM | 4 GB DDR4 | Vivado/Vitis | €250–350 | the "small ML demo" board; overkill and proprietary for this |
| Alveo U50 / U55C, Versal, Agilex | datacenter | 1–4M LC | HBM | vendor | €2.5k–15k+ | flat MNIST-scale learning fabric; not a hobby purchase |

Recommendation if and when: **OrangeCrab or ULX3S** (open toolchain,
enough logic for hundreds of clauses, external RAM for the multiplexed
path); iCEBreaker if the goal is only the XOR demo. All run from Fedora
with distro packages (`yosys`, `nextpnr`, `openFPGALoader`) plus
`amaranth` from pip. No Windows box needed; the RTX machine stays for
the GPU sibling.

## 4. How it connects and how it is driven

- **Programming**: USB; `openFPGALoader -b <board> fabric.bit`. Seconds.
- **Data link**: the same USB as a UART (FTDI/CDC), 115 200 baud to
  3 Mbaud. A sample is NIN bits + 1 label; a reply is the prediction
  and the running score. At 1 Mbaud that is ~10⁴ samples/s — the *link*
  is the bottleneck, not the fabric, so for throughput demos the dataset
  sits in BRAM/SDRAM and the board learns autonomously, reporting
  accuracy per 1000 samples.
- **Observability**: LEDs = the clause outputs or the readout; the
  ULX3S HDMI can show the automata grid as pixels — the fabric watched
  live, the way zahradnice is watched in a terminal.
- **Exactness**: with the LFSR seed fixed and the sample stream fixed,
  the hardware run is bit-reproducible; the same seed drives the
  simulator, so hardware ≡ simulation ≡ Python reference, bit for bit.

## 5. Plan (when triggered)

1. **HDL generator** `gen_tm_hdl.py` in Amaranth (Python HDL): modules
   `Automaton(N)`, `Clause(NIN, S, Q)`, `Vote(C, θ)` (exact sign and
   optional K-counter), `Feedback`, `LFSR`, `Sequencer`, `UartLink`.
   Parameters C, N, S, Q, NIN exactly as in `gen_tm.py`; polarity by
   clause index. One session.
2. **Simulation**: Amaranth's built-in simulator (pysim) for unit tests;
   Verilator/cocotb for full-fabric runs at speed. Validation contract:
   (a) fixed random bits ⇒ bit-exact agreement with a Python reference
   that consumes the same bits (`model_tm.py` extended to take a bit
   stream); (b) distributional agreement with zahradnice and torchfab on
   the C=8/16 XOR curves. One session.
3. **Board**: buy, flash, UART driver in Python (pyserial), rerun the
   XOR curves on hardware; then the demo (autonomous learning, LEDs /
   HDMI). One session plus shipping.
4. **Measurements only hardware gives**: energy per sample (a USB power
   meter suffices), latency, and the schedule experiment — the same
   fabric under a synchronous clock versus the CPU engine's one-event
   jump chain, which the contract says must agree.

## 6. Risks and honest limits

- LFSR randomness is fine for learning; do not use it for the exactness
  claim across platforms unless all platforms consume the same stream.
- The K-counter readout costs cycles; inference wants the exact sign.
  Keep both selectable.
- Truly clockless (asynchronous) logic is a research topic (NCL,
  delay-insensitive); a clocked fabric is the honest first version and
  is exact under the contract.
- Time-multiplexed learning is a memory-system project, not a fabric
  project; it should follow the GPU sibling's MNIST result, not precede it.
- IP: Tsetlin-machine hardware is commercialised (Literal Labs, Granmo
  group patents); a research demo is fine, anything beyond needs a look.

## 7. Trigger conditions

Pick this up when any of these holds: the torch sibling has produced a
fabric worth casting (a trained 8×8 or MNIST-class fabric); a question
needs energy/latency numbers; or the user wants the toy. Until then the
line's hardware story is a paragraph in `00-foundations.md` §5.
