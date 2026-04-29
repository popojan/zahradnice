#!/usr/bin/env python3
"""zahradnice tetris piece generator.

Phase 1: piece-spec data + ASCII visualiser (--viz flag).
Phase 2: cfg emission for spawn / fall / freeze / lateral / rotation.

Coordinate convention
---------------------
Each orientation: list of (row, col) piece-cell positions inside its bounding
box, top-left at (0, 0). 'anchor' is the top-leftmost OCCUPIED piece-cell —
becomes the LHS rule anchor in the emitted cfg. 'pivot' is the rotation pivot
piece-cell (SRS-like). Each piece-cell occupies 2 terminal cols × 1 terminal
row (#grid 2 1 convention).

Body-layout convention (matches the hand-written I-piece rules):
  spawn / lateral / rotation -> horizontal body (LHS left, RHS right)
  fall / freeze              -> vertical body   (LHS above, RHS below)
"""

import argparse


PIECES = {
    'I': {
        'glyph': 'I',
        'colour': 'cyan',
        'orientations': [
            {'name': 'H', 'cells': [(0, 0), (0, 1), (0, 2), (0, 3)],
             'anchor': (0, 0), 'pivot': (0, 1)},
            {'name': 'V', 'cells': [(0, 0), (1, 0), (2, 0), (3, 0)],
             'anchor': (0, 0), 'pivot': (1, 0)},
        ],
        'spawn': 0,
        'rotation_chain': [0, 1],
    },
    'T': {
        'glyph': 'T',
        'colour': 'magenta',
        'orientations': [
            {'name': 'T0', 'cells': [(0, 1), (1, 0), (1, 1), (1, 2)],
             'anchor': (0, 1), 'pivot': (1, 1)},
            {'name': 'T1', 'cells': [(0, 0), (1, 0), (1, 1), (2, 0)],
             'anchor': (0, 0), 'pivot': (1, 0)},
            {'name': 'T2', 'cells': [(0, 0), (0, 1), (0, 2), (1, 1)],
             'anchor': (0, 0), 'pivot': (0, 1)},
            {'name': 'T3', 'cells': [(0, 1), (1, 0), (1, 1), (2, 1)],
             'anchor': (0, 1), 'pivot': (1, 1)},
        ],
        'spawn': 0,
        'rotation_chain': [0, 1, 2, 3],
    },
}


# ---------- Geometry ----------

def to_terminal_cells(orientation):
    """Piece-cells -> set of terminal-cell offsets relative to terminal anchor.
    Terminal anchor is the LEFT terminal cell of the anchor piece-cell."""
    ar, ac = orientation['anchor']
    cells = set()
    for (r, pc) in orientation['cells']:
        for dc in (0, 1):
            cells.add((r - ar, (pc - ac) * 2 + dc))
    return cells


def shift(cells, dr, dc):
    return {(r + dr, c + dc) for r, c in cells}


def below_2col_aligned(orientation):
    """One cell per piece-cell-pair directly below the piece (left terminal col).
    Compatible with the 2-col-aligned blocking optimisation: any frozen block
    or wall fills a piece-cell-pair, so checking the left terminal col of each
    pair below is sufficient for freeze sub-rules."""
    cells = to_terminal_cells(orientation)
    even_cols = sorted({c for _, c in cells if c % 2 == 0})
    out = []
    for c in even_cols:
        max_r = max(r for r, cc in cells if cc in (c, c + 1))
        out.append((max_r + 1, c))
    return out


def below_all(orientation):
    """ALL terminal cells directly below the piece, one per occupied col.
    Used for the fall rule's LHS empty-checks."""
    cells = to_terminal_cells(orientation)
    cols = {c for _, c in cells}
    out = set()
    for c in cols:
        max_r = max(r for r, cc in cells if cc == c)
        out.add((max_r + 1, c))
    return out


def pivot_terminal_offset(orientation):
    """Terminal-col offset of pivot from anchor, using the LEFT col of pivot piece-cell."""
    ar, ac = orientation['anchor']
    pr, pc = orientation['pivot']
    return (pr - ar, (pc - ac) * 2)


def rotation_anchor_shift(from_o, to_o):
    """When rotating from_o -> to_o, the screen pivot stays put. Compute the
    delta the screen anchor moves by."""
    fpr, fpc = pivot_terminal_offset(from_o)
    tpr, tpc = pivot_terminal_offset(to_o)
    return (fpr - tpr, fpc - tpc)


# ---------- Body / header builders ----------

def header(field1, trigger, field3=' ', field6=None, field7=None):
    """Assemble a header. Fields not specified default per spec."""
    if field6 is not None or field7 is not None:
        # Need to fill all fields up to 7.
        fg = '7'
        bg = '8'
        f6 = field6 if field6 is not None else ' '
        f7 = field7 if field7 is not None else ' '
        return f'=={field1}{trigger}{field3}{fg}{bg}{f6}{f7}'
    return f'=={field1}{trigger}{field3}'


def _safe_indent(body_str):
    """If any body line starts with #/^/=, indent every line by one space."""
    lines = body_str.split('\n')
    if any(line and line[0] in '#^=' for line in lines):
        return '\n'.join(' ' + line for line in lines)
    return body_str


def render_body_vertical(lhs, rhs):
    """LHS above boundary row, RHS below. lhs/rhs: dicts {(dr, dc): char}."""
    all_offsets = list(lhs.keys()) + list(rhs.keys()) + [(0, 0)]
    min_dc = min(dc for _, dc in all_offsets)
    max_dc = max(dc for _, dc in all_offsets)
    C = -min_dc  # body col where the anchor sits

    # LHS region row span (include anchor at dr=0).
    lhs_drs = [dr for dr, _ in lhs.keys()] + [0]
    lhs_min_dr = min(lhs_drs)
    lhs_max_dr = max(lhs_drs)
    R_a = -lhs_min_dr  # anchor at body row R_a

    boundary_row = R_a + lhs_max_dr + 1

    # RHS region row span.
    rhs_drs = [dr for dr, _ in rhs.keys()] + [0]
    rhs_min_dr = min(rhs_drs)
    rhs_max_dr = max(rhs_drs)
    R_b = boundary_row + 1 - rhs_min_dr

    nrows = R_b + rhs_max_dr + 1
    ncols = C + max_dc + 1

    grid = [[' '] * ncols for _ in range(nrows)]
    for (dr, dc), ch in lhs.items():
        grid[R_a + dr][C + dc] = ch
    grid[R_a][C] = '@'
    grid[boundary_row][C] = '@'
    for (dr, dc), ch in rhs.items():
        grid[R_b + dr][C + dc] = ch
    grid[R_b][C] = '@'

    body = '\n'.join(''.join(row).rstrip() for row in grid)
    return _safe_indent(body)


def render_body_horizontal(lhs, rhs):
    """LHS left of boundary col, RHS right. lhs/rhs: dicts {(dr, dc): char}."""
    all_offsets_lhs = list(lhs.keys()) + [(0, 0)]
    all_offsets_rhs = list(rhs.keys()) + [(0, 0)]

    lhs_drs = [dr for dr, _ in all_offsets_lhs]
    lhs_dcs = [dc for _, dc in all_offsets_lhs]
    R_a = -min(lhs_drs)
    C_a = -min(lhs_dcs)
    lhs_max_col = C_a + max(lhs_dcs)

    boundary_col = lhs_max_col + 1

    rhs_drs = [dr for dr, _ in all_offsets_rhs]
    rhs_dcs = [dc for _, dc in all_offsets_rhs]
    R_b = R_a  # both anchors on same body row simplifies
    # If RHS has rows above row 0 and LHS doesn't, may need to bump R_a.
    if R_b + min(rhs_drs) < 0:
        bump = -(R_b + min(rhs_drs))
        R_a += bump
        R_b += bump
    C_b = boundary_col + 1 - min(rhs_dcs)

    nrows = max(R_a + max(lhs_drs), R_b + max(rhs_drs)) + 1
    ncols = max(lhs_max_col, C_b + max(rhs_dcs)) + 1

    grid = [[' '] * ncols for _ in range(nrows)]
    for (dr, dc), ch in lhs.items():
        grid[R_a + dr][C_a + dc] = ch
    grid[R_a][C_a] = '@'
    grid[R_a][boundary_col] = '@'
    for (dr, dc), ch in rhs.items():
        grid[R_b + dr][C_b + dc] = ch
    grid[R_b][C_b] = '@'

    body = '\n'.join(''.join(row).rstrip() for row in grid)
    return _safe_indent(body)


# ---------- Per-rule emission ----------

def emit_spawn(piece, orientation):
    """R + H above + footprint empty -> piece. Anchor cell becomes piece glyph
    (since the anchor IS the leftmost piece-cell)."""
    cells = to_terminal_cells(orientation)
    siblings = cells - {(0, 0)}
    glyph = piece['glyph']

    lhs = {(-1, 0): 'H'}
    for c in siblings:
        lhs[c] = '~'
    rhs = {c: glyph for c in siblings}

    return header('R', 'f', glyph) + '\n' + render_body_horizontal(lhs, rhs)


def emit_fall(piece, orientation):
    old = to_terminal_cells(orientation)
    new = shift(old, 1, 0)
    erase = old - new - {(0, 0)}
    write = new - old
    glyph = piece['glyph']

    lhs = {c: glyph for c in old - {(0, 0)}}
    for c in below_all(orientation):
        lhs[c] = '~'
    rhs = {c: '~' for c in erase}
    for c in write:
        rhs[c] = glyph

    return header(glyph, 'g', '~') + '\n' + render_body_vertical(lhs, rhs)


def emit_freeze(piece, orientation):
    """One sub-rule per piece-cell-pair below (left terminal col of pair)."""
    cells = to_terminal_cells(orientation)
    glyph = piece['glyph']
    rules = []
    for below_cell in below_2col_aligned(orientation):
        lhs = {(-1, 0): '~'}  # R-write room
        for c in cells - {(0, 0)}:
            lhs[c] = glyph
        lhs[below_cell] = '%'

        rhs = {(-1, 0): 'R'}
        for c in cells - {(0, 0)}:
            rhs[c] = '#'

        body = render_body_vertical(lhs, rhs)
        rules.append(header(glyph, 'g', '#', field6='H', field7='#') + '\n' + body)
    return rules


def emit_lateral(piece, orientation, dc):
    """dc: +/-2. Anchor cell content depends on whether (0,0) lands inside new piece."""
    old = to_terminal_cells(orientation)
    new = shift(old, 0, dc)
    glyph = piece['glyph']
    field3 = glyph if (0, 0) in new else '~'

    erase_cells = old - new
    write_cells = new - old

    lhs = {c: glyph for c in old - {(0, 0)}}
    for c in write_cells:  # new positions must be empty
        lhs[c] = '~'
    rhs = {}
    for c in erase_cells - {(0, 0)}:
        rhs[c] = '~'
    for c in write_cells:
        rhs[c] = glyph

    trigger = 'a' if dc < 0 else 'd'
    return header(glyph, trigger, field3) + '\n' + render_body_horizontal(lhs, rhs)


def emit_rotation(piece, from_o, to_o, trigger):
    from_cells = to_terminal_cells(from_o)
    sh = rotation_anchor_shift(from_o, to_o)
    to_cells_in_from = shift(to_terminal_cells(to_o), sh[0], sh[1])
    glyph = piece['glyph']
    field3 = glyph if (0, 0) in to_cells_in_from else '~'

    erase_cells = from_cells - to_cells_in_from
    write_cells = to_cells_in_from - from_cells

    lhs = {c: glyph for c in from_cells - {(0, 0)}}
    for c in write_cells:
        lhs[c] = '~'
    rhs = {}
    for c in erase_cells - {(0, 0)}:
        rhs[c] = '~'
    for c in write_cells:
        rhs[c] = glyph

    return header(glyph, trigger, field3) + '\n' + render_body_horizontal(lhs, rhs)


# ---------- Top-level orchestration ----------

def emit_piece(piece_letter):
    piece = PIECES[piece_letter]
    out = [f"# === {piece_letter}-piece ({piece['colour']}) ==="]
    out.append('# spawn')
    out.append(emit_spawn(piece, piece['orientations'][piece['spawn']]))
    for o in piece['orientations']:
        out.append(f"# {o['name']}: fall")
        out.append(emit_fall(piece, o))
        out.append(f"# {o['name']}: freeze ({len(below_2col_aligned(o))} sub-rules)")
        out.extend(emit_freeze(piece, o))
        out.append(f"# {o['name']}: lateral L/R")
        out.append(emit_lateral(piece, o, -2))
        out.append(emit_lateral(piece, o, +2))
    chain = piece['rotation_chain']
    if len(chain) >= 2:
        out.append("# rotations (CW: w; CCW: e)")
        for i, idx in enumerate(chain):
            from_o = piece['orientations'][idx]
            cw_idx = chain[(i + 1) % len(chain)]
            ccw_idx = chain[(i - 1) % len(chain)]
            if cw_idx == ccw_idx:
                # 2-orientation: stack w/e on the same body
                to_o = piece['orientations'][cw_idx]
                # Emit two headers + one body
                from_cells = to_terminal_cells(from_o)
                sh = rotation_anchor_shift(from_o, to_o)
                to_cells_in_from = shift(to_terminal_cells(to_o), sh[0], sh[1])
                glyph = piece['glyph']
                field3 = glyph if (0, 0) in to_cells_in_from else '~'
                erase_cells = from_cells - to_cells_in_from
                write_cells = to_cells_in_from - from_cells
                lhs = {c: glyph for c in from_cells - {(0, 0)}}
                for c in write_cells:
                    lhs[c] = '~'
                rhs = {}
                for c in erase_cells - {(0, 0)}:
                    rhs[c] = '~'
                for c in write_cells:
                    rhs[c] = glyph
                body = render_body_horizontal(lhs, rhs)
                out.append(f"# {from_o['name']} <-> {to_o['name']} (CW & CCW share body)")
                out.append(header(glyph, 'w', field3))
                out.append(header(glyph, 'e', field3) + '\n' + body)
            else:
                out.append(f"# {from_o['name']} -> {piece['orientations'][cw_idx]['name']} (CW)")
                out.append(emit_rotation(piece, from_o, piece['orientations'][cw_idx], 'w'))
                out.append(f"# {from_o['name']} -> {piece['orientations'][ccw_idx]['name']} (CCW)")
                out.append(emit_rotation(piece, from_o, piece['orientations'][ccw_idx], 'e'))
    return '\n'.join(out)


# ---------- ASCII visualiser (phase 1) ----------

def render_visualiser(orientation, glyph):
    cells = set(orientation['cells'])
    anchor = orientation['anchor']
    rows = max(r for r, _ in cells) + 1
    cols = max(c for _, c in cells) + 1
    lines = []
    for r in range(rows):
        chars = []
        for c in range(cols):
            if (r, c) == anchor:
                chars.append(glyph.lower())
            elif (r, c) in cells:
                chars.append(glyph)
            else:
                chars.append(' ')
        lines.append(''.join(chars))
    return lines


def viz():
    for letter, piece in PIECES.items():
        print(f"\n{letter} ({piece['colour']}):")
        blocks = [(o['name'], render_visualiser(o, piece['glyph'])) for o in piece['orientations']]
        max_h = max(len(b) for _, b in blocks)
        max_w = max(max((len(line) for line in b), default=0) for _, b in blocks)
        padded = []
        for name, block in blocks:
            lines = [line.ljust(max_w) for line in block]
            lines += [' ' * max_w] * (max_h - len(lines))
            padded.append((name, lines))
        gap = '   '
        print('  ' + gap.join(name.ljust(max_w) for name, _ in padded))
        for row in range(max_h):
            print('  ' + gap.join(b[row] for _, b in padded))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--viz', action='store_true', help='print ASCII visualisation only')
    p.add_argument('--piece', help='emit cfg for one piece (letter)')
    args = p.parse_args()

    if args.viz:
        viz()
        return
    if args.piece:
        print(emit_piece(args.piece))
        return
    # default: emit all pieces
    for letter in PIECES:
        print(emit_piece(letter))
        print()


if __name__ == '__main__':
    main()
