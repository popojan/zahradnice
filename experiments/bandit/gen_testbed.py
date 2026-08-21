#!/usr/bin/env python3
"""Generate the env+agent testbed — zero engine changes, composition
via #include (which the engine has had all along).

Layout:
  env-core.cfg    the ENVIRONMENT as an include library: field, the
                  action space (base blooms, reward-tagged: x pays
                  under season 'a', y under 'b'), wilt, controls.
                  No learning anywhere. Running it via agent-null =
                  the random-policy baseline.
  lri-rules.cfg   the L_R-I learning rules as a second-level library:
                  exploration-deposit, catalytic readout+deposit,
                  decay. (Linear reward-inaction automaton.)
  agent-null.cfg  #! + include env                  (random baseline)
  agent-lri.cfg   #! + include env + include lri    (reward-inaction)
  agent-lrp.cfg   #! + env + lri + confiscation     (reward-penalty)

Agents are additive rule mass on the same environment — swapping the
agent swaps only which extra rules exist; the environment file is
byte-identical underneath all three. Note agent-lri/lrp carry their
own paying-bloom mass (the deposit bootstrap), so their exploration
floor is 2x agent-null's base — agents are compared to each other on
identical mass (lri vs lrp differ only by confiscation); null is the
env-only control.
"""
from pathlib import Path

B = 0.05
C = 0.5
W = 1
D = 0.03
PUN = 0.5
ARMS = {"x": ("⠋", "2"), "y": ("⠙", "5")}
SEASONS = {"a": "x", "b": "y"}
HERE = Path(__file__).parent


def g(v):
    return f"{v:g}"


def write(name, lines):
    (HERE / name).write_text("\n".join(lines) + "\n")
    n = sum(1 for l in lines if l.startswith("="))
    print(f"wrote {name} ({n} rule headers)")


env = []
A = env.append
A("# ENVIRONMENT include library: seasons-and-flowers bandit world.")
A("# Defines the field, the action space and the reward function;")
A("# contains no learning. Season = the input trigger char (a/b).")
A("#control q quit")
A("#timing a 0")
A("")
A("^.**")
A("")
A("# the action space, reward-tagged: x pays under a, y under b")
for season, paid in SEASONS.items():
    for arm, (tok, fg) in ARMS.items():
        A(f"==.{season}{arm}{fg}0   {1 if arm == paid else 0} {g(B)}")
        A("@.@@")
A("")
A("# wilt: flowers clear, actions repeat")
for arm in ARMS:
    for season in SEASONS:
        A(f"=={arm}{season}.70   0 {g(W)}")
        A("@@@")
A("")
A("# watcher quit carrier")
A("=q.q.")
A("@@@")
write("env-core.cfg", env)

lri = []
A = lri.append
A("# AGENT include library: linear reward-inaction learning rules.")
A("# Policy = token masses; the scoring rewrite deposits the token.")
for season, paid in SEASONS.items():
    arm = paid
    tok, fg = ARMS[arm]
    A(f"# exploration-deposit ({arm} under {season})")
    A(f"==.{season}{arm}{fg}0   1 {g(B)}")
    A(f"@.@@{tok}")
    for oarm, (otok, ofg) in ARMS.items():
        pays = oarm == paid
        score = 1 if pays else 0
        dep = otok if pays else ""
        for body in ([f"{otok}@.@@{dep}"], [otok, f"@.@@{dep}"],
                     [f"@.@@{dep}", otok]):
            A(f"==.{season}{oarm}{ofg}0   {score} {g(C)}")
            lri.extend(body)
A("")
A("# forgetting")
for arm, (tok, fg) in ARMS.items():
    for season in SEASONS:
        A(f"=={tok}{season}.70   0 {g(D)}")
        A("@@@")
write("lri-rules.cfg", lri)

write("agent-null.cfg", [
    "#! agent-null  reward={score} steps={steps}",
    "#help random baseline: environment only | a/b season | q quit",
    "#threads 1",
    "#include env-core.cfg",
])

write("agent-lri.cfg", [
    "#! agent-lri  reward={score} steps={steps}",
    "#help reward-inaction automaton | a/b season | q quit",
    "#threads 1",
    "#include env-core.cfg",
    "#include lri-rules.cfg",
])

lrp = [
    "#! agent-lrp  reward={score} steps={steps}",
    "#help reward-penalty automaton (MENACE confiscation) | q quit",
    "#threads 1",
    "#include env-core.cfg",
    "#include lri-rules.cfg",
    "# confiscation: a failed advised attempt eats its adviser",
]
for season, paid in SEASONS.items():
    for arm, (tok, fg) in ARMS.items():
        if arm != paid:
            lrp.append(f"==.{season}{arm}{fg}0   0 {g(PUN)}")
            lrp.append(f"@{tok}@@.")
write("agent-lrp.cfg", lrp)
