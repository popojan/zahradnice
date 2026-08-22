#!/usr/bin/env python3
"""Behaviour predicates for the inverse search, night 1.

Input per run: the engine's --trace (every applied rule with anchor
position) + --dump-screen (final screen, ground truth). The state
trajectory is reconstructed in Python from the genotype's own
semantics (gen_family.reqs/writes) and the final reconstructed state
is checked EXACTLY against the dump — the house trace<->screen
accounting pattern. A mismatch is a pipeline bug, never tolerated.

Classification of a run (horizon H = number of input trigger bytes):

  ABSORBED_EMPTY   applies stalled before H, no A/B left on screen
  ABSORBED_FROZEN  applies stalled before H, matter present but dead
  FIXED            ran to H, state eventually constant (period 1)
  TRANSLATION      ran to H, sustained cycle p>=2, population vector
                   constant over the cycle (the walker class)
  POP_OSC          ran to H, sustained cycle p>=2, population vector
                   varies over the cycle (the flip-flop class)
  APERIODIC        ran to H, no sustained cycle within the horizon

"Applies stalled => absorbed forever" is sound in this family: with a
single trigger and state unchanged by a no-op event, applicability is
a deterministic function of state, so the first no-op repeats forever.

"Sustained cycle" is empirical per run: smallest p such that the
trajectory is p-periodic from some transient i to the horizon, with
at least two full periods observed (n - i + 1 >= 2p).

The two candidate oscillator predicates whose minima the calibration
separates:
  P_state  class in {TRANSLATION, POP_OSC}  (global state recurs)
  P_pop    class == POP_OSC                 (populations oscillate)
"""
import gen_family


def parse_trace(path):
    """[(lhs, idx, ro, co, trig)] for apply events, in order."""
    out = []
    with open(path) as f:
        for line in f:
            if line.startswith("apply\t"):
                p = line.rstrip("\n").split("\t")
                out.append((p[5], int(p[6]), int(p[7]), int(p[8]), p[4]))
    return out


def parse_dump(path, rows, cols):
    """Playfield rows 1..rows-1 as padded strings (row 0 = status)."""
    with open(path) as f:
        lines = f.read().split("\n")
    field = lines[1:rows]
    field += [""] * ((rows - 1) - len(field))
    return [l[:cols].ljust(cols) for l in field]


def replay(rules, s0, applies, cols, extra=()):
    """State trajectory [s0, s1, ..., sn] as lists of row strings."""
    imap = gen_family.idx_map(rules, extra)
    grid = [list(row) for row in s0]
    states = ["\n".join(s0)]
    for lhs, idx, ro, co, _trig in applies:
        rule = imap[(lhs, idx)]
        for dc, ch in gen_family.writes(rule):
            grid[ro - 1][(co + dc) % cols] = ch
        states.append("\n".join("".join(r) for r in grid))
    return states


def pop(state):
    return (state.count("A"), state.count("B"))


def _sustained_period(states):
    """Smallest p with a p-periodic tail covering >= 2 periods; returns
    (p, transient_i) or None. Fast path: first exact recurrence."""
    n = len(states) - 1
    seen = {}
    first = None
    for t, s in enumerate(states):
        if s in seen:
            first = (seen[s], t - seen[s])
            break
        seen[s] = t
    if first:
        i, p = first
        if n - i + 1 >= 2 * p and all(
                states[t] == states[t + p] for t in range(i, len(states) - p)):
            return p, i
    for p in range(1, n // 2 + 1):
        bad = [t for t in range(len(states) - p) if states[t] != states[t + p]]
        i = (max(bad) + 1) if bad else 0
        if n - i + 1 >= 2 * p:
            return p, i
    return None


def classify(states, horizon):
    """-> (class, period, transient)."""
    n = len(states) - 1
    if n < horizon:
        empty = not any(c in "AB" for c in states[-1])
        return ("ABSORBED_EMPTY" if empty else "ABSORBED_FROZEN", None, n)
    sp = _sustained_period(states)
    if sp is None:
        return ("APERIODIC", None, None)
    p, i = sp
    if p == 1:
        return ("FIXED", 1, i)
    pops = {pop(states[t]) for t in range(i, i + p)}
    cls = "POP_OSC" if len(pops) > 1 else "TRANSLATION"
    return (cls, p, i)


P_STATE = frozenset(["TRANSLATION", "POP_OSC"])


def p_state(classes):
    return all(c in P_STATE for c in classes)


def p_pop(classes):
    return all(c == "POP_OSC" for c in classes)


# --- night 2: self-repair under point deletion ------------------------
#
# Protocol per run: T*h_est (establish), then `rounds` x [p + T*h_rec].
# Byte 'p' fires a harness rule erasing one weight-uniform random
# matter cell; on non-empty state it always applies, so poke applies
# (trig 'p' in the trace) are reliable segment delimiters. Segments
# are classified with the night-1 classifier; the repair question is
# whether every post-damage segment re-establishes the pre-damage
# (class, period).

GOOD_PRE = frozenset(["FIXED", "TRANSLATION", "POP_OSC"])
DYNAMIC = frozenset(["TRANSLATION", "POP_OSC"])


def repair_verdict(states, applies, h_est, h_rec, rounds):
    """-> dict: pre=(cls, period), rounds=[(cls, period), ...],
    outcome in {REPAIR, DEGRADED, DIED, PRE_FAIL, POKE_ACTIVATED},
    pokes_landed, fixed_identical (FIXED pre only: recovered state
    equals pre-poke state)."""
    pokes = [j for j, a in enumerate(applies) if a[4] == "p"]
    j1 = pokes[0] if pokes else len(applies)
    pre_cls, pre_p, _ = classify(states[:j1 + 1], h_est)
    segs = []
    for r, j in enumerate(pokes):
        end = pokes[r + 1] if r + 1 < len(pokes) else len(applies)
        cls, p, _ = classify(states[j + 1:end + 1], h_rec)
        segs.append((cls, p))
    out = {"pre": (pre_cls, pre_p), "rounds": segs,
           "pokes_landed": len(pokes), "fixed_identical": None}
    if pre_cls not in GOOD_PRE:
        if len(pokes) == rounds and segs and all(
                c in DYNAMIC for c, _ in segs):
            out["outcome"] = "POKE_ACTIVATED"
        else:
            out["outcome"] = "PRE_FAIL"
        return out
    if len(pokes) < rounds:
        out["outcome"] = "DIED"
        return out
    if pre_cls == "FIXED":
        out["fixed_identical"] = all(
            states[pokes[r + 1] if r + 1 < len(pokes) else len(applies)]
            == states[j1] for r in range(len(pokes)))
    if all(c == pre_cls and p == pre_p for c, p in segs):
        out["outcome"] = "REPAIR"
    elif any(c.startswith("ABSORBED") for c, _ in segs):
        out["outcome"] = "DIED"
    else:
        out["outcome"] = "DEGRADED"
    return out


def sustain_verdict(states, applies, h_est, h_final):
    """Night 3: sustained bombardment. Protocol: establish, then many
    [p + T*m] blocks, then a T*h_final recovery window. Returns pre
    behaviour, damage tolerated, population statistics sampled at the
    instant before each poke, and whether the pre behaviour
    re-establishes once the bombardment stops."""
    pokes = [j for j, a in enumerate(applies) if a[4] == "p"]
    j1 = pokes[0] if pokes else len(applies)
    pre_cls, pre_p, _ = classify(states[:j1 + 1], h_est)
    pops = [pop(states[j]) for j in pokes]
    jlast = pokes[-1] if pokes else j1
    fin_cls, fin_p, _ = classify(states[jlast + 1:], h_final)
    alive = any(c in "AB" for c in states[-1])
    n = len(pops)
    return {
        "pre": (pre_cls, pre_p),
        "pokes_landed": len(pokes),
        "alive": alive,
        "final": (fin_cls, fin_p),
        "recovered": alive and fin_cls == pre_cls and fin_p == pre_p,
        "meanA": sum(a for a, b in pops) / n if n else 0.0,
        "meanB": sum(b for a, b in pops) / n if n else 0.0,
        "min_total": min((a + b for a, b in pops), default=0),
        "max_total": max((a + b for a, b in pops), default=0),
    }
