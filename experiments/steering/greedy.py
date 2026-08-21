#!/usr/bin/env python3
"""Greedy closed-loop steering of programs/life-steer.cfg via
deterministic prefix replay (research-rl-ai.md §9, step 3).

No engine changes: relies on --seed determinism under forced
single-threading (--trace /dev/null; see friction journal F7). Each
decision point re-runs the whole episode prefix plus one candidate
action plus a lookahead horizon of ticks, reads the final score from
stderr, and commits the argmax action (ties prefer doing nothing).
O(decisions^2) engine work per episode -- the cost of closed-loop
interaction without a streaming step mode (research-rl-ai.md gap G1).

Policies: greedy (1-step lookahead), random, passive (never acts).
All three produce identical-length trigger strings, so final scores
are directly comparable per seed.
"""
import argparse
import random
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BIN = ROOT / "zahradnice"
CFG = ROOT / "programs" / "life-steer.cfg"
ACTIONS = "Twasde"  # T = do nothing this slot


def run(input_str, seed, want_dump=False):
    p = subprocess.run(
        [str(BIN), "--headless", str(CFG), "--seed", str(seed),
         "--screen", "24,80", "--trace", "/dev/null", "--input", input_str],
        capture_output=True, text=True)
    m = re.search(r"final score=(-?\d+)", p.stderr)
    if not m:
        sys.exit(f"engine output not understood: {p.stderr!r}")
    score = int(m.group(1))
    if want_dump:
        return score, p.stdout.splitlines()
    return score


# --- burst mode: the cursor acts only in frozen time (no ticks inside a
# burst) and parks on its dead spawn block between decisions, so the
# machine never observes it in transit; residual impact = one frozen
# dead home cell + RNG consumption (see results.md round 4).
BR, BC = 11, 20  # block grid: rows 1..22 in 2-row blocks, 80 cols in 4-col


def parse_blocks(dump):
    """Return (phase, digit, cursor) grids from a screen dump."""
    phase, digit, cur = {}, {}, None
    for R in range(BR):
        for C in range(BC):
            r0 = 1 + 2 * R
            line = dump[r0] if r0 < len(dump) else ""

            def at(col):
                return line[col] if col < len(line) else " "
            phase[R, C] = at(4 * C + 2)
            digit[R, C] = at(4 * C + 1)
            if at(4 * C) == ">":
                cur = (R, C)
    return phase, digit, cur


def bfs_path(phase, src, dst):
    """Key string moving the cursor src->dst over resting blocks (torus)."""
    from collections import deque
    prev = {src: (None, "")}
    q = deque([src])
    while q:
        cell = q.popleft()
        if cell == dst:
            keys = []
            while prev[cell][0] is not None:
                cell, k = prev[cell]
                keys.append(k)
            return "".join(reversed(keys))
        R, C = cell
        for dR, dC, k in ((0, 1, "d"), (0, -1, "a"), (1, 0, "s"), (-1, 0, "w")):
            nxt = ((R + dR) % BR, (C + dC) % BC)
            if nxt not in prev and (phase.get(nxt) == "b" or nxt == dst):
                prev[nxt] = (cell, k)
                q.append(nxt)
    return None


REVKEY = {"d": "a", "a": "d", "s": "w", "w": "s"}


def burst_candidates(seed, prefix, rng, k=5):
    """Sample k toggleable reachable blocks; return [(burst_string, label)]."""
    _, dump = run(prefix, seed, want_dump=True)
    phase, digit, cur = parse_blocks(dump)
    if cur is None:
        return []
    pool = [b for b in phase
            if phase[b] == "b" and digit[b] in "01" and b != cur]
    rng.shuffle(pool)
    out = []
    for b in pool:
        path = bfs_path(phase, cur, b)
        if path is None:
            continue
        back = "".join(REVKEY[c] for c in reversed(path))
        out.append((path + "e" + back, f"{b[0]},{b[1]}"))
        if len(out) >= k:
            break
    return out


# policy name -> (action set, uses lookahead). greedy-mover isolates the
# free-movement channel: same oracle lookahead as greedy, toggles removed.
POLICIES = {
    "passive": ("T", False),
    "random": (ACTIONS, False),
    "greedy": (ACTIONS, True),
    "greedy-mover": ("Twasd", True),
}
BURST_POLICIES = ("burst-greedy", "burst-random")


def episode_burst(seed, policy, warmup, decisions, gap, horizon, tax_every,
                  rng):
    prefix = ticks(warmup, 0, tax_every)
    acts = []
    for _ in range(decisions):
        cands = burst_candidates(seed, prefix, rng)
        chosen = ""      # WAIT
        label = "."
        if policy == "burst-greedy" and cands:
            pos = len(prefix)
            options = [("", ".")] + cands
            with ThreadPoolExecutor(max_workers=len(options)) as ex:
                scores = list(ex.map(
                    lambda o: run(
                        prefix + o[0] + ticks(horizon, pos + len(o[0]),
                                              tax_every), seed),
                    options))
            best = max(range(len(options)),
                       key=lambda i: (scores[i], options[i][0] == ""))
            chosen, label = options[best]
        elif policy == "burst-random" and cands:
            chosen, label = rng.choice([("", ".")] + cands)
        acts.append(label)
        pos = len(prefix)
        prefix += chosen + ticks(gap, pos + len(chosen), tax_every)
    return run(prefix + ticks(horizon, len(prefix), tax_every), seed), \
        ";".join(acts)


def ticks(n, pos, every):
    """n idle ticks starting at global char position pos; every `every`-th
    position carries the observer-tax trigger h instead of T (0 = off).
    Keeping the cadence a function of absolute position makes candidate
    evaluations and the committed trajectory share identical tax timing."""
    s = "".join("h" if every and (pos + i) % every == every - 1 else "T"
                for i in range(n))
    return s


def episode(seed, policy, warmup, decisions, gap, horizon, tax_every, rng):
    action_set, lookahead = POLICIES[policy]
    prefix = ticks(warmup, 0, tax_every)
    acts = []
    for _ in range(decisions):
        pos = len(prefix)
        if lookahead:
            with ThreadPoolExecutor(max_workers=len(action_set)) as ex:
                scores = list(ex.map(
                    lambda a: run(
                        prefix + a + ticks(horizon, pos + 1, tax_every), seed),
                    action_set))
            a = max(zip(scores, (c == "T" for c in action_set), action_set))[2]
        elif len(action_set) > 1:
            a = rng.choice(action_set)
        else:
            a = action_set
        acts.append(a)
        prefix += a + ticks(gap, pos + 1, tax_every)
    return run(prefix + ticks(horizon, len(prefix), tax_every), seed), \
        "".join(acts)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=8)
    ap.add_argument("--warmup", type=int, default=400)
    ap.add_argument("--decisions", type=int, default=10)
    ap.add_argument("--gap", type=int, default=60)
    ap.add_argument("--horizon", type=int, default=300)
    ap.add_argument("--tax-every", type=int, default=60,
                    help="observer-tax cadence in ticks (0 = no tax)")
    ap.add_argument("--policies", default="passive,random,greedy,greedy-mover",
                    help="comma-separated subset of: "
                         + ",".join(list(POLICIES) + list(BURST_POLICIES)))
    args = ap.parse_args()

    print("policy,seed,score,actions")
    totals = {}
    for policy in args.policies.split(","):
        for seed in range(1, args.seeds + 1):
            rng = random.Random(seed)
            ep = episode_burst if policy in BURST_POLICIES else episode
            score, acts = ep(seed, policy, args.warmup,
                             args.decisions, args.gap, args.horizon,
                             args.tax_every, rng)
            totals.setdefault(policy, []).append(score)
            print(f"{policy},{seed},{score},{acts}", flush=True)
    for policy, scores in totals.items():
        mean = sum(scores) / len(scores)
        print(f"# {policy}: mean={mean:+.1f} scores={scores}",
              file=sys.stderr)


if __name__ == "__main__":
    main()
