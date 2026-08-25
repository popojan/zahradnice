#!/usr/bin/env python3
"""F4 — the earned family (open-world line, the summit climb).

Paper #3 authored three channels: inheritance of regulation (stamps
ride matter creation), miscopy (mutant headers), price (fuel reads).
F4 moves their EXERCISE into matter (design + pre-registrations:
ew-design.md; mechanics probe: p1-results.md):

- matter motion DE-regulates: a creating rule writes `?` (unstamped
  marker) at the written column's gate — over live alleles and empty
  gates alike; an unstamped locus gates nothing (frontier stall);
- only machinery REregulates: a copier glyph on the machinery row
  reads the template allele below it (`&` LHS, ctx) and stamps it
  east (`&` RHS, ctxrep), advancing under TASEP exclusion — the F3
  stamp channel re-anchored on the machine;
- machinery is matter: built by a priced gated rule, mortal, and a
  competitor in the event lottery (the time tax is structural);
- fidelity is a machine trait: a sloppy copier carries the mutant
  headers; a faithful one does not.

Geometry (4 playfield rows, toroidal): tape=1, fuel=2, machinery=3,
regulatory=4. From the tape: gate at (-1,0), machinery at (-2,0),
fuel at (+1,0). From the machinery row: regulatory at (+1,0), fuel
at (-1,0) — matter expansion and law copying eat from the SAME row
(single-currency doctrine; the economy chooses between them).

Family-separation doctrine: gen_gated.py stays bit-stable for paper
#3; this module imports and never edits. Emission style mirrors
ow2.py's build_cfg: every helper returns (header(s), writes) so the
driver assembles cfg text and the replay imap side by side.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "inverse"))
import gen_family
import gen_gated

PLACE = "?"                     # unstamped-gate marker (literal in bodies)
FUEL, SPENT = "o", "."          # F3 pricing convention


# --- matter side: unstamped gated emission ---------------------------
#
# Conquest = CONTENT CHANGE (refinement forced by the idempotent-
# spawner idiom, see ew-design.md): a creating rule de-regulates
# exactly the cells whose matter content it changes. Matter is
# anonymous (the arc's organism-deletion doctrine) — rewriting A
# over A is no identity event, so the gate stands. The unconditional
# `write` kind splits into three mutually exclusive east-content
# variants (empty / same char / other matter); exactly one is
# applicable in any state, at the rule's own weight, so the split is
# lottery-equivalent to F3's single rule. `reqwrite` pins its east
# content already and needs no split; erasure never de-regulates
# (ghost gates: conquest de-regulates, death does not).

MATTER_CHARS = "AB"


def unstamped_head(rule, glyph, fore="7", back="8"):
    """Gate on `glyph`; the stamp channel (field 7) stays empty —
    matter no longer inherits regulation as a side effect."""
    h = "==" + rule.lhs + rule.trig + rule.rep + fore + back + glyph
    if rule.w != 1:
        h += f"  0 {rule.w:g}"        # pad ctxrep; tail at wchar pos 10
    return h


def _priced_row(cq, out):
    row2 = [" "] * (cq + 1)
    row2[0] = FUEL
    row2[cq] = SPENT
    return out + "\n" + "".join(row2)


def unstamped_groups(rule, glyph, priced=False, matter=MATTER_CHARS):
    """[(heads_with_writes, body), ...] for one gated F2 rule under
    earned inheritance. heads_with_writes = [(header, writes)]."""
    assert rule.kind in gen_gated.GATEABLE, f"ungateable kind {rule.kind}"
    h = unstamped_head(rule, glyph)
    base = [(0, dc, ch) for dc, ch in gen_family.writes(rule)]
    pay = priced and (gen_gated.creates(rule) or priced == "all")
    if rule.kind == "write" and rule.arg != "~":
        x = rule.arg
        out = []
        for c in ("~",) + tuple(matter):
            b = "@" + c + "@@" + x            # east pinned to c
            cq = 3
            row0 = [" "] * (cq + 2)
            row0[0] = "&"
            wr = list(base)
            if c != x:                        # content changes: conquer
                row0[cq + 1] = PLACE
                wr.append((-1, 1, PLACE))
            body = "".join(row0).rstrip() + "\n" + b
            if pay:
                body = _priced_row(cq, body)
                wr.append((1, 0, SPENT))
            out.append(([(h, wr)], body))
        return out
    b = gen_family.body(rule)
    cq = b.rindex("@")
    row0 = [" "] * (len(b) + 2)
    row0[0] = "&"
    wr = list(base)
    for dc, ch in gen_family.writes(rule):
        if dc and ch != " " and not (
                rule.kind == "reqwrite" and rule.arg[0] == rule.arg[1]):
            row0[cq + dc] = PLACE
            wr.append((-1, dc, PLACE))
    body = "".join(row0).rstrip() + "\n" + b
    if pay:
        body = _priced_row(cq, body)
        wr.append((1, 0, SPENT))
    return [([(h, wr)], body)]


# --- machinery side: the copier law ----------------------------------
#
# All helpers return ([(header, writes)], body): headers stack over
# the shared body; writes are [(drow, dcol, ch)] for the replay imap.

def copier_copy(glyph, alleles, eps=0, trig="T", priced=False,
                faith_w=1):
    """Read template below (ctx), require `?` east-below, stamp it
    (ctxrep), advance east into an empty slot. Faithful headers per
    allele; eps > 0 adds the mutant (g, g') headers — miscopy as a
    property of THIS machine glyph. faith_w < 1 normalizes the
    total copy mass of a sloppy machine (EW-9 Amendment 10: extra
    mutant headers otherwise make it MOVE more, and under exclusion
    the restless breed less — a mobility-fecundity confound)."""
    fuel_w = [(-1, 0, SPENT)] if priced else []
    heads = []
    for g in alleles:
        h = "==" + glyph + trig + "~78" + g + g
        if faith_w != 1:
            h += f" 0 {faith_w:g}"
        heads.append((h,
                      [(0, 0, " "), (0, 1, glyph), (1, 1, g)] + fuel_w))
    if eps:
        for g in alleles:
            for h in alleles:
                if h != g:
                    heads.append((f"=={glyph}{trig}~78{g}{h} 0 {eps:g}",
                                  [(0, 0, " "), (0, 1, glyph),
                                   (1, 1, h)] + fuel_w))
    body = "@~@@" + glyph + "\n&?  &"
    if priced:
        body = "o  .\n" + body
    return heads, body


def copier_walk(glyph, alleles, trig="T", w=1):
    """Step east over an already-stamped locus (`%`: allele pair per
    header, the odd or single allele doubled), excluding."""
    wr = [(0, 0, " "), (0, 1, glyph)]
    pairs = [(alleles[i], alleles[i + 1])
             for i in range(0, len(alleles) - 1, 2)]
    if len(alleles) % 2:
        pairs.append((alleles[-1], alleles[-1]))
    tail = f" 0 {w:g}" if w != 1 else ""
    heads = [("==" + glyph + trig + "~78" + a + b + tail, wr)
             for a, b in pairs]
    return heads, "@~@@" + glyph + "\n %"


def copier_pass(glyph, trig="T", w=1):
    """Step east over an UNSTAMPED (`?`) locus without stamping it —
    no template needed. Without this, a wound repair that
    re-de-regulates the gate under a standing copier deadlocks the
    whole east-only convoy behind it (EW-2 Amendment 5; mortal
    machinery masks the jam by melting it)."""
    h = "==" + glyph + trig + "~78"
    if w != 1:
        h += f"   0 {w:g}"
    return ([(h, [(0, 0, " "), (0, 1, glyph)])],
            "@~@@" + glyph + "\n ?")


def copier_decay(glyph, eps_d, trig="T"):
    return ([(f"=={glyph}{trig}~78   0 {eps_d:g}", [(0, 0, " ")])], "@@@")


def wall_hop(glyph, w=0.05, trig="T"):
    """EW-11 Amendment 11: cross a wall `|` into an empty cell two
    east, rarely. Without this, an east-only machinery economy in a
    bounded sector is a terminal conveyor — machines make one
    transit, pile at the wall, the pile grows back over the build
    sites, and translation dies (the ring's wrap was load-bearing).
    Only machines hop; stamps, matter, and law stay walled, so the
    genome stays home while machinery migrates — the island-model
    dial, and the linkage-decay rate."""
    return ([(f"=={glyph}{trig}~78   0 {w:g}",
              [(0, 0, " "), (0, 2, glyph)])],
            "@|~@@ " + glyph)


def copier_replicate(glyph, allele, w=0.05, trig="T"):
    """EW-9: a machine SPLITS — writes its own glyph east into an
    empty slot, keeping itself — gated on standing over the given
    live allele (`&` on the regulatory row below). The gating is
    load-bearing (Amendment 9): machine reproduction priced on the
    consequences of the machine's own work is what makes lineage
    traits like fidelity visible to selection; the per-allele
    weight is that allele's machine-nurture."""
    h = "==" + glyph + trig + glyph + "78" + allele + allele \
        + f" 0 {w:g}"
    return ([(h, [(0, 0, glyph), (0, 1, glyph)])],
            "@~@@" + glyph + "\n&")


def translator_tabled(glyph, tables, drift_w=0.1, trig="T"):
    """EW-7: the codon table read from matter. One execute body per
    table glyph s — s as a LITERAL at (−1,0), the codon at (−2,0)
    via ctx — with headers giving s's mapping. The frozen rule set
    holds the SPACE of mappings; matter selects which is live,
    column by column: even a universal code must be physically
    instantiated everywhere it is used."""
    groups = []
    for s, mapping in sorted(tables.items()):
        heads = [("==" + glyph + trig + "~78" + c + prod,
                  [(0, 0, " "), (0, 1, prod), (0, 2, glyph)])
                 for c, prod in sorted(mapping.items())]
        groups.append((heads, "&\n" + s + "\n@~~@@&" + glyph))
    groups.append(([(f"=={glyph}{trig}~78   0 {drift_w:g}",
                    [(0, 0, " "), (0, 1, glyph)])], "@~@@" + glyph))
    return groups


def table_copier(glyph, table_glyphs, drift_w=0.1, trig="T"):
    """EW-7: maintain code uniformity — copy the table glyph below
    ((−1,0)) east into an EMPTIED table cell, advancing; a single
    surviving cell can reseed the row west-to-east."""
    heads = [("==" + glyph + trig + "~78" + s + s,
              [(0, 0, " "), (0, 1, glyph), (-1, 1, s)])
             for s in sorted(table_glyphs)]
    repair = (heads, "&~  &\n@~@@" + glyph)
    drift = ([(f"=={glyph}{trig}~78   0 {drift_w:g}",
               [(0, 0, " "), (0, 1, glyph)])], "@~@@" + glyph)
    return [repair, drift]


def transcriptase_rules(glyph, codons, drift_w=0.1, trig="T"):
    """EW-6: two-copy description redundancy. BACKUP — copy the
    codon above ((−1,0)) into an empty backup slot at (−2,0);
    RESTORE — copy the backup at (−2,0) into an emptied code cell
    at (−1,0): the heal. One header per codon each; the wound rules
    anchor on codon glyphs wherever they stand, so both copies are
    wounded uniformly and content dies only when both copies of a
    column are lost between visits."""
    backup = ([("==" + glyph + trig + "~78" + c + c,
                [(0, 0, " "), (0, 1, glyph), (-2, 0, c)])
               for c in sorted(codons)],
              "~  &\n&\n@~@@" + glyph)
    restore = ([("==" + glyph + trig + "~78" + c + c,
                 [(0, 0, " "), (0, 1, glyph), (-1, 0, c)])
                for c in sorted(codons)],
               "&\n~  &\n@~@@" + glyph)
    drift = ([(f"=={glyph}{trig}~78   0 {drift_w:g}",
               [(0, 0, " "), (0, 1, glyph)])], "@~@@" + glyph)
    return [backup, restore, drift]


def translator_rules(glyph, codons, drift_w=0.1, trig="T"):
    """The description rung's executor (EW-5): read the codon below
    ((−1,0), ctx), build its product east ((0,+1), ctxrep), land
    beyond it ((0,+2)) — a built machine is live the moment it is
    written, and a codon encoding `glyph` itself is the von Neumann
    self-reference. Builds only into emptiness (homeostasis: rebuild
    where death made room). The weight-`drift_w` unconditional
    advance keeps the convoy deadlock-free past full slots and junk
    codons. codons: {codon_glyph: product_glyph}."""
    heads = [("==" + glyph + trig + "~78" + c + prod,
              [(0, 0, " "), (0, 1, prod), (0, 2, glyph)])
             for c, prod in sorted(codons.items())]
    execute = (heads, "&\n@~~@@&" + glyph)
    drift = ([(f"=={glyph}{trig}~78   0 {drift_w:g}",
               [(0, 0, " "), (0, 1, glyph)])], "@~@@" + glyph)
    return [execute, drift]


def build_rule(matter, allele, glyph, trig="T", priced=False, w=1):
    """Matter gated on `allele` writes a copier into an EMPTY slot at
    (-2,0) — machinery is born where its builders stand."""
    h = "==" + matter + trig + " 78" + allele
    if w != 1:
        h += f"  0 {w:g}"
    wr = [(-2, 0, glyph)]
    body = "~ " + glyph + "\n&\n@@@"
    if priced:
        body += "\no ."
        wr = wr + [(1, 0, SPENT)]
    return [(h, wr)], body


def bootstrap(allele, glyph, ring, density=2, trig="b"):
    """One-shot machinery seeding: anchored on any reg-row `allele`
    cell, writes a copier every `density` columns across the ring
    (toroidal wrap covers it regardless of the anchor column). A row
    filled solid gridlocks under exclusion — density >= 2."""
    cols = range(0, ring - ring % density, density)
    row0 = [" "] * (ring + 2)
    for k in cols:
        row0[2 + k] = glyph
    body = "".join(row0).rstrip() + "\n@@@"
    return ([("==" + allele + trig, [(-1, k, glyph) for k in cols])],
            body)


def assemble(name, init_lines, groups, extra=()):
    """cfg text + replay imap from [(heads_with_writes, body), ...];
    extra = plain gen_family rules (harness law), appended verbatim."""
    lines = [f"#!{name}", "#threads 1"] + list(init_lines)
    emis = []
    for heads, body in groups:
        for h, _w in heads:
            lines.append(h)
        lines.append(body)
        for h, w in heads:
            emis.append((h[2], w))
    for r in extra:
        lines.append(gen_family.head(r))
        lines.append(gen_family.body(r))
        emis.append((r.lhs, [(0, dc, ch) for dc, ch in
                             gen_family.writes(r)]))
    imap, per = {}, {}
    for lhs, w in emis:
        i = per.get(lhs, 0)
        imap[(lhs, i)] = w
        per[lhs] = i + 1
    return "\n".join(lines) + "\n", imap


if __name__ == "__main__":
    R = gen_family.Rule
    rules = [R("A", "A", "write", "A")]
    groups = []
    for r in rules:
        groups += unstamped_groups(r, "α")
    groups.append(copier_copy("Π", ["α"]))
    groups.append(copier_walk("Π", ["α"]))
    groups.append(bootstrap("α", "Π", 6))
    text, imap = assemble("demo", ["^Auc", "^αl*"], groups,
                          gen_family.poke_rules())
    print(text)
    for k, v in imap.items():
        print(k, v)
