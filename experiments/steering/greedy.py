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


def run(input_str, seed):
    p = subprocess.run(
        [str(BIN), "--headless", str(CFG), "--seed", str(seed),
         "--screen", "24,80", "--trace", "/dev/null", "--input", input_str],
        capture_output=True, text=True)
    m = re.search(r"final score=(-?\d+)", p.stderr)
    if not m:
        sys.exit(f"engine output not understood: {p.stderr!r}")
    return int(m.group(1))


def episode(seed, policy, warmup, decisions, gap, horizon, rng):
    prefix = "T" * warmup
    acts = []
    for _ in range(decisions):
        if policy == "greedy":
            with ThreadPoolExecutor(max_workers=len(ACTIONS)) as ex:
                scores = list(ex.map(
                    lambda a: run(prefix + a + "T" * horizon, seed), ACTIONS))
            a = max(zip(scores, (c == "T" for c in ACTIONS), ACTIONS))[2]
        elif policy == "random":
            a = rng.choice(ACTIONS)
        else:
            a = "T"
        acts.append(a)
        prefix += a + "T" * gap
    return run(prefix + "T" * horizon, seed), "".join(acts)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=8)
    ap.add_argument("--warmup", type=int, default=400)
    ap.add_argument("--decisions", type=int, default=10)
    ap.add_argument("--gap", type=int, default=60)
    ap.add_argument("--horizon", type=int, default=300)
    args = ap.parse_args()

    print("policy,seed,score,actions")
    totals = {}
    for policy in ("passive", "random", "greedy"):
        for seed in range(1, args.seeds + 1):
            rng = random.Random(seed)
            score, acts = episode(seed, policy, args.warmup,
                                  args.decisions, args.gap, args.horizon, rng)
            totals.setdefault(policy, []).append(score)
            print(f"{policy},{seed},{score},{acts}", flush=True)
    for policy, scores in totals.items():
        mean = sum(scores) / len(scores)
        print(f"# {policy}: mean={mean:+.1f} scores={scores}",
              file=sys.stderr)


if __name__ == "__main__":
    main()
