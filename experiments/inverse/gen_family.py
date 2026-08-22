#!/usr/bin/env python3
"""Grammar families for the inverse-emergence search: F1 (menu, night
1 calibration) and F2 (menu2, night 2 self-repair), plus the harness
poke rules (point deletion as fixed law).

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

# kind: self|write|req|reqwrite; arg is None (self), one char (write/req)
# or two chars CX (reqwrite: require C east, write X east). trig 'T' for
# all genotype rules; harness rules (poke) use their own trigger. w is
# the engine rule weight (sampling bias; replay-irrelevant).
Rule = namedtuple("Rule", "lhs rep kind arg trig w", defaults=("T", 1))


def menu():
    """F1 menu (night 1): 42 rules, east-only, no combined shape."""
    rules = []
    for lhs in LHS:
        for rep in REP:
            rules.append(Rule(lhs, rep, "self", None))
            for a in ARG:
                rules.append(Rule(lhs, rep, "write", a))
                rules.append(Rule(lhs, rep, "req", a))
    return rules


def menu2():
    """F2 menu (night 2): F1 + the combined require+write shape
    (`@C@@X`: fire only when east is C, and write X east) — the
    context-dependent write that repair logic needs. 96 rules."""
    rules = menu()
    for lhs in LHS:
        for rep in REP:
            for c in ARG:
                for x in ARG:
                    rules.append(Rule(lhs, rep, "reqwrite", c + x))
    return rules


def poke_rules(glyphs="AB"):
    """Harness law, not part of any genotype: byte 'p' erases one
    weight-uniformly random matter cell (any listed glyph)."""
    return [Rule(g, "~", "self", None, "p") for g in glyphs]


def head(rule):
    h = "==" + rule.lhs + rule.trig + rule.rep
    if rule.w != 1:
        # header fields are positional (omission = truncation only), so
        # a score/weight tail needs the full field block: fg bg ctx ctxrep
        h += f"78   0 {rule.w:g}"
    return h


def body(rule):
    if rule.kind == "self":
        return "@@@"
    if rule.kind == "write":
        return "@@@" + rule.arg
    if rule.kind == "req":
        return "@" + rule.arg + "@@"
    if rule.kind == "reqwrite":
        return "@" + rule.arg[0] + "@@" + rule.arg[1]
    if rule.kind == "wreqwrite":
        # arg = WCX: require W west and C east, write X east
        return rule.arg[0] + "@" + rule.arg[1] + "@@" + rule.arg[2]
    # gapwrite, arg = WX: require W west + holes at +1,+2; write XX
    return rule.arg[0] + "@~~@@" + rule.arg[1] * 2


def rule_id(rule):
    tail = "" if rule.arg is None else rule.arg
    wtag = "" if rule.w == 1 else f"*{rule.w:g}"
    return f"{rule.lhs}>{rule.rep}.{rule.kind}{tail}{wtag}"


def canonical(rules):
    return tuple(sorted(rules))


def genotype_id(rules):
    return "|".join(rule_id(r) for r in canonical(rules))


def compile_cfg(rules, name, extra=(), init="^Acc"):
    """Genotype rules in canonical order, then harness rules (extra)
    verbatim — so genotype (lhs, idx) pairs are independent of the
    harness and harness rules take the trailing per-lhs indices.
    init may hold several ^-lines separated by newlines."""
    lines = [f"#!{name}", "#threads 1"] + init.split("\n")
    for r in list(canonical(rules)) + list(extra):
        lines.append(head(r))
        lines.append(body(r))
    return "\n".join(lines) + "\n"


def idx_map(rules, extra=()):
    """(lhs, idx) -> Rule, matching the engine's per-lhs parse-order
    indexing of R[lhs] for a cfg emitted by compile_cfg."""
    m, per = {}, {}
    for r in list(canonical(rules)) + list(extra):
        i = per.get(r.lhs, 0)
        m[(r.lhs, i)] = r
        per[r.lhs] = i + 1
    return m


def _ch(c):
    return " " if c == "~" else c


def reqs(rule):
    """LHS cells beyond the anchor: [(dcol, char)]."""
    if rule.kind == "req":
        return [(1, _ch(rule.arg))]
    if rule.kind == "reqwrite":
        return [(1, _ch(rule.arg[0]))]
    if rule.kind == "wreqwrite":
        return [(-1, _ch(rule.arg[0])), (1, _ch(rule.arg[1]))]
    if rule.kind == "gapwrite":
        return [(-1, _ch(rule.arg[0])), (1, " "), (2, " ")]
    return []


def writes(rule):
    """RHS cells: [(dcol, char)], anchor first."""
    w = [(0, _ch(rule.rep))]
    if rule.kind == "write":
        w.append((1, _ch(rule.arg)))
    elif rule.kind == "reqwrite":
        w.append((1, _ch(rule.arg[1])))
    elif rule.kind == "wreqwrite":
        w.append((1, _ch(rule.arg[2])))
    elif rule.kind == "gapwrite":
        w += [(1, _ch(rule.arg[1])), (2, _ch(rule.arg[1]))]
    return w


def stratum(k, m=None):
    """All k-subsets of a menu (default F1), canonical order."""
    return [canonical(c) for c in combinations(m or menu(), k)]


if __name__ == "__main__":
    m, m2 = menu(), menu2()
    print(f"F1 menu {len(m)} (k=1 {len(stratum(1))}, k=2 {len(stratum(2))}); "
          f"F2 menu {len(m2)} (k=1 {len(stratum(1, m2))}, "
          f"k=2 {len(stratum(2, m2))})")
    print(compile_cfg([Rule('A', 'B', 'self', None),
                       Rule('B', 'A', 'self', None)], "flipflop"))
