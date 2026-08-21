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


# policy name -> (action set, uses lookahead). greedy-mover isolates the
# free-movement channel: same oracle lookahead as greedy, toggles removed.
POLICIES = {
    "passive": ("T", False),
    "random": (ACTIONS, False),
    "greedy": (ACTIONS, True),
    "greedy-mover": ("Twasd", True),
}


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
                    help="comma-separated subset of: " + ",".join(POLICIES))
    args = ap.parse_args()

    print("policy,seed,score,actions")
    totals = {}
    for policy in args.policies.split(","):
        for seed in range(1, args.seeds + 1):
            rng = random.Random(seed)
            score, acts = episode(seed, policy, args.warmup,
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
