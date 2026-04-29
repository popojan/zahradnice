#!/usr/bin/env python3
"""zahradnice tetris piece generator — proof of concept.

Phase 1 (this file): piece-spec data + ASCII visualiser. No cfg emission yet.
The visualiser renders each orientation as ASCII art using the piece glyph;
the anchor cell (which becomes the LHS rule anchor in the emitted cfg) is
shown in lowercase so it's visible.

Phase 2: rule emission for spawn / fall / freeze / lateral / rotation.

Coordinate convention
---------------------
Each orientation is a list of (row, col) piece-cell positions within its
bounding box, top-left at (0, 0). The 'anchor' of an orientation is the
top-leftmost OCCUPIED cell — used as the LHS rule anchor in the emitted
cfg. Anchors can differ between orientations of the same piece (e.g. T0's
anchor at (0, 1) vs T2's at (0, 0)), which means some rotation rules
shift the screen anchor.

In the runtime engine each piece-cell occupies 2 terminal columns × 1
terminal row (the #grid 2 1 convention). Conversion between piece-cell
offsets and terminal-col offsets is the generator's job in Phase 2.

Run with: python3 scripts/tetris_generator.py
"""


PIECES = {
    'I': {
        'glyph': 'I',
        'colour': 'cyan',
        'orientations': [
            {'name': 'H', 'cells': [(0, 0), (0, 1), (0, 2), (0, 3)], 'anchor': (0, 0)},
            {'name': 'V', 'cells': [(0, 0), (1, 0), (2, 0), (3, 0)], 'anchor': (0, 0)},
        ],
        'spawn': 0,           # index into orientations[] for default spawn shape
        'rotation_chain': [0, 1],  # CW order; CCW is the reverse
    },
    'T': {
        'glyph': 'T',
        'colour': 'magenta',
        'orientations': [
            {'name': 'T0', 'cells': [(0, 1), (1, 0), (1, 1), (1, 2)], 'anchor': (0, 1)},
            {'name': 'T1', 'cells': [(0, 0), (1, 0), (1, 1), (2, 0)], 'anchor': (0, 0)},
            {'name': 'T2', 'cells': [(0, 0), (0, 1), (0, 2), (1, 1)], 'anchor': (0, 0)},
            {'name': 'T3', 'cells': [(0, 1), (1, 0), (1, 1), (2, 1)], 'anchor': (0, 1)},
        ],
        'spawn': 0,
        'rotation_chain': [0, 1, 2, 3],
    },
}


def render(orientation, glyph):
    """Return a list of strings showing the orientation's bounding box.
    Filled cells use the piece glyph; the anchor cell uses the glyph in
    lowercase so its position is visible. Empty cells render as space."""
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


def main():
    for letter, piece in PIECES.items():
        print(f"\n{letter} ({piece['colour']}):")
        # Render each orientation side-by-side; pad to common height/width.
        blocks = [(o['name'], render(o, piece['glyph'])) for o in piece['orientations']]
        max_h = max(len(b) for _, b in blocks)
        max_w = max(max((len(line) for line in b), default=0) for _, b in blocks)
        padded = []
        for name, block in blocks:
            lines = [line.ljust(max_w) for line in block]
            lines += [' ' * max_w] * (max_h - len(lines))
            padded.append((name, lines))
        # Print orientation names then the rendered blocks row by row.
        gap = '   '
        print('  ' + gap.join(name.ljust(max_w) for name, _ in padded))
        for row in range(max_h):
            print('  ' + gap.join(b[row] for _, b in padded))


if __name__ == '__main__':
    main()
