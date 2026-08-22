#!/usr/bin/env python3
"""Family F1 for the night-1 calibration inverse (inverse emergence:
given a behaviour predicate, find the minimal rule-set producing it).

F1 is deliberately tiny and 1-D: all rule geometry lives on the init
row, so the universe is a ring of `cols` cells (toroidal wrap). The
genotype is a SET of rules drawn from a finite menu M; admissibility
is by construction (everything the compiler emits parses and has
well-formed geometry). Stratified enumeration over k = |genotype|
gives provable minimality *within F1*.

Menu M (42 rules): lhs in {A,B} x rep in {A,B,~} x shape in
  self      @@@       rewrite anchor to rep
  write(X)  @@@X      rewrite anchor to rep, write X at east neighbour
  req(C)    @C@@      rewrite anchor to rep, require C at east neighbour
with X, C in {A,B,~} ('~' = space). Trigger is always 'T', weight 1,
init is a single A at centre (^Acc) — note the init deliberately
breaks A<->B relabelling symmetry (a B-only grammar is unreachable
dead matter), so no symmetry quotient is applied.

This module is the single source of truth for BOTH directions:
compile_cfg() emits the .cfg the engine runs, and reqs()/writes()
give the same rule's semantics to the Python trace-replay in
analyzers.py. The replay is validated per-run against the engine's
own --dump-screen (exact accounting), so a semantics drift between
the two is caught, not silently trusted.
"""
from collections import namedtuple
from itertools import combinations

TRIG = "T"
LHS = "AB"
REP = "AB~"
ARG = "AB~"

Rule = namedtuple("Rule", "lhs rep kind arg")  # kind: self|write|req


def menu():
    rules = []
    for lhs in LHS:
        for rep in REP:
            rules.append(Rule(lhs, rep, "self", None))
            for a in ARG:
                rules.append(Rule(lhs, rep, "write", a))
                rules.append(Rule(lhs, rep, "req", a))
    return rules


def head(rule):
    return "==" + rule.lhs + TRIG + rule.rep


def body(rule):
    if rule.kind == "self":
        return "@@@"
    if rule.kind == "write":
        return "@@@" + rule.arg
    return "@" + rule.arg + "@@"


def rule_id(rule):
    tail = "" if rule.arg is None else rule.arg
    return f"{rule.lhs}>{rule.rep}.{rule.kind}{tail}"


def canonical(rules):
    return tuple(sorted(rules))


def genotype_id(rules):
    return "|".join(rule_id(r) for r in canonical(rules))


def compile_cfg(rules, name):
    lines = [f"#!{name}", "#threads 1", "^Acc"]
    for r in canonical(rules):
        lines.append(head(r))
        lines.append(body(r))
    return "\n".join(lines) + "\n"


def idx_map(rules):
    """(lhs, idx) -> Rule, matching the engine's per-lhs parse-order
    indexing of R[lhs] for a cfg emitted by compile_cfg."""
    m, per = {}, {}
    for r in canonical(rules):
        i = per.get(r.lhs, 0)
        m[(r.lhs, i)] = r
        per[r.lhs] = i + 1
    return m


def _ch(c):
    return " " if c == "~" else c


def reqs(rule):
    """LHS cells beyond the anchor: [(dcol, char)]."""
    return [(1, _ch(rule.arg))] if rule.kind == "req" else []


def writes(rule):
    """RHS cells: [(dcol, char)], anchor first."""
    w = [(0, _ch(rule.rep))]
    if rule.kind == "write":
        w.append((1, _ch(rule.arg)))
    return w


def stratum(k):
    """All k-subsets of the menu, canonical order."""
    return [canonical(c) for c in combinations(menu(), k)]


if __name__ == "__main__":
    m = menu()
    print(f"menu size {len(m)}, k=1 stratum {len(stratum(1))}, "
          f"k=2 stratum {len(stratum(2))}")
    print(compile_cfg([Rule('A', 'B', 'self', None),
                       Rule('B', 'A', 'self', None)], "flipflop"))
