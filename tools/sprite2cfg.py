#!/usr/bin/env python3
"""sprite2cfg.py - spritesheet animation row -> zahradnice .cfg.

For each frame transition, every cell inside the body bbox is fully
specified (a literal glyph or `~`). Transitions chain non-terminals
A -> F0 -> F1 -> ... -> FN-1 -> F0.

Motion (--shift-x N != 0):
  Header field 3 = `~` (erases the LHS-anchor screen cell). The next
  non-terminal is placed as a literal body cell at body col cq+N
  (screen offset +N from @3 == screen anchor). The figure pixels in
  the RHS region are shifted by +N body columns so they render at the
  new anchor position. The toroidal wrap (engine-level wrap_col)
  carries the figure off the right edge back to the left.
"""
from __future__ import annotations
import argparse
from pathlib import Path
from PIL import Image

FRAME_NONTERMS = list("YZWXURSV")  # avoids B/M/T (timing) + reserved keys
DEFAULT_RAMP = " .,:-+oxX"          # body-safe: avoids * ~ @ & ! % $


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("png", type=Path, help="spritesheet PNG (RGBA)")
    p.add_argument("--row", type=int, default=11, help="sheet row (default 11 = walk-east)")
    p.add_argument("--frame-size", type=int, nargs=2, default=[64, 64],
                   metavar=("W", "H"))
    p.add_argument("--frames", type=int, nargs="+", default=list(range(1, 9)),
                   help="frame column indices (default: 1..8)")
    p.add_argument("--width", type=int, default=18, help="output cell width")
    p.add_argument("--cell-aspect", type=float, default=2.0,
                   help="terminal cell H:W ratio")
    p.add_argument("--ramp", type=str, default=DEFAULT_RAMP)
    p.add_argument("--alpha-threshold", type=int, default=64)
    p.add_argument("--timing", type=int, default=120, help="ms per frame")
    p.add_argument("--title", type=str, default="lpc-walk")
    p.add_argument("--shift-x", type=int, default=0,
                   help="cols to shift per frame (1 = walk right, -1 = left)")
    p.add_argument("--trigger", type=str, default="T",
                   help="trigger char for frame transitions (T = auto tick, "
                        "letter = keypress; #timing emitted only for T)")
    p.add_argument("--floor", type=str, default="",
                   help="single char to paint as floor (e.g. '_'); empty = none")
    p.add_argument("-o", "--out", type=Path, required=True)
    return p.parse_args()


def extract_frames(im, row, fw, fh, indices):
    return [im.crop((i * fw, row * fh, (i + 1) * fw, (row + 1) * fh))
            for i in indices]


def union_bbox(frames, alpha_thresh):
    bb = None
    for f in frames:
        alpha = f.split()[-1].point(lambda v: 255 if v > alpha_thresh else 0)
        fb = alpha.getbbox()
        if fb is None:
            continue
        bb = fb if bb is None else (
            min(bb[0], fb[0]), min(bb[1], fb[1]),
            max(bb[2], fb[2]), max(bb[3], fb[3]))
    return bb


def downsample(frame, bbox, target_w, target_h, ramp, alpha_thresh):
    crop = frame.crop(bbox)
    px = crop.load()
    sw, sh = crop.size
    cw, ch = sw / target_w, sh / target_h
    non_space = ramp.lstrip(" ") or ramp
    grid = [[" "] * target_w for _ in range(target_h)]
    visible = [[False] * target_w for _ in range(target_h)]
    for r in range(target_h):
        for c in range(target_w):
            x0, y0 = int(c * cw), int(r * ch)
            x1, y1 = max(x0 + 1, int((c + 1) * cw)), max(y0 + 1, int((r + 1) * ch))
            n = sl = sa = 0
            for y in range(y0, y1):
                for x in range(x0, x1):
                    pr, pg, pb, pa = px[x, y]
                    sl += (pr + pg + pb) // 3
                    sa += pa
                    n += 1
            if n == 0:
                continue
            if sa / n < alpha_thresh:
                continue
            t = 1.0 - (sl / n) / 255.0
            idx = max(0, min(len(non_space) - 1,
                             int(t * (len(non_space) - 1) + 0.5)))
            grid[r][c] = non_space[idx]
            visible[r][c] = True
    return grid, visible


def emit_cfg(frames_data, anchor_rc, title, timing_ms, shift_x, floor,
             trigger) -> str:
    fig_h = len(frames_data[0][0])
    fig_w = len(frames_data[0][0][0])
    ar, ac = anchor_rc                          # anchor in figure-local coords
    n = len(frames_data)
    nt = FRAME_NONTERMS[:n]
    assert len(nt) == n, "not enough frame non-terminals"

    body_w = fig_w + abs(shift_x)               # 1 extra col for motion/erase

    def lhs_rows(prev_frame, is_bootstrap):
        prev_g, prev_v = (None, None) if prev_frame is None else prev_frame
        rows = []
        for r in range(fig_h):
            chars = []
            for c in range(body_w):
                if c < fig_w and prev_v is not None and prev_v[r][c]:
                    chars.append(prev_g[r][c])
                else:
                    chars.append("~")
            rows.append("".join(chars))
        if floor:                                   # dedicated floor row
            floor_row = []
            for c in range(body_w):
                if is_bootstrap:
                    floor_row.append("~")           # screen empty pre-bootstrap
                elif shift_x > 0 and c >= body_w - shift_x:
                    floor_row.append(" ")           # right trailing edge no-op
                elif shift_x < 0 and c < -shift_x:
                    floor_row.append(" ")           # left trailing edge no-op
                else:
                    floor_row.append(floor)
            rows.append("".join(floor_row))
        anchor_row = ["~"] * body_w
        anchor_row[ac] = "@"
        rows.append("".join(anchor_row))
        return rows

    def rhs_rows(cur_frame, next_nt_literal, this_shift):
        cur_g, cur_v = cur_frame
        rows = []
        for r in range(fig_h):
            chars = []
            for c in range(body_w):
                src_c = c - this_shift
                if 0 <= src_c < fig_w and cur_v[r][src_c]:
                    chars.append(cur_g[r][src_c])
                else:
                    chars.append("~")
            rows.append("".join(chars))
        if floor:
            rows.append(floor * body_w)             # solid floor paint
        anchor_row = ["~"] * body_w
        anchor_row[ac] = "@"
        if next_nt_literal is not None:
            pos = ac + this_shift
            if 0 <= pos < body_w:
                anchor_row[pos] = next_nt_literal
        rows.append("".join(anchor_row))
        return rows

    def emit_rule_body(prev_frame, cur_frame, next_nt_literal, this_shift,
                      is_bootstrap):
        lines = []
        lines += lhs_rows(prev_frame, is_bootstrap)
        lines.append(" " * ac + "@")            # boundary @2
        lines += rhs_rows(cur_frame, next_nt_literal, this_shift)
        return lines

    help_line = (f"#help {title}: walk cycle - SPACE pause - ESC quit"
                 if trigger == "T"
                 else f"#help {title}: press '{trigger}' to step - SPACE pause - ESC quit")
    out = [
        f"#! {title} {{parallel}}",
        help_line,
    ]
    if trigger == "T":
        out.append(f"#timing T {timing_ms}")
    out += [
        "#control ~ pause",
        "^Acc",
        "",
    ]

    # Bootstrap A -> F0: fires on first trigger (auto T tick, or first
    # keypress). In-place (no motion), field 3 = F0 letter. RHS uses
    # this_shift=0 so figure aligns with what subsequent LHSs expect.
    out.append(f"==A{trigger}{nt[0]}")
    out += emit_rule_body(None, frames_data[0], None, 0, is_bootstrap=True)
    out.append("")

    # Frame transitions Fi -> F(i+1).
    # Motion: field 3 = ~ (erase old anchor); next-nonterm literal in body
    # at +shift_x. With floor enabled the anchor row is below the floor, so
    # ~ leaves the old position empty (under-floor) rather than paving it.
    # Static: field 3 = next-nonterm letter (in-place replacement).
    for i in range(n):
        j = (i + 1) % n
        if shift_x != 0:
            head = f"=={nt[i]}{trigger}~"
            next_literal = nt[j]
        else:
            head = f"=={nt[i]}{trigger}{nt[j]}"
            next_literal = None
        out.append(head)
        out += emit_rule_body(frames_data[i], frames_data[j], next_literal,
                              shift_x, is_bootstrap=False)
        out.append("")

    return "\n".join(out) + "\n"


def main():
    a = parse_args()
    im = Image.open(a.png).convert("RGBA")
    fw, fh = a.frame_size
    frames = extract_frames(im, a.row, fw, fh, a.frames)
    bb = union_bbox(frames, a.alpha_threshold)
    if bb is None:
        raise SystemExit("no visible pixels in any frame")
    src_w, src_h = bb[2] - bb[0], bb[3] - bb[1]
    tw = a.width
    th = max(1, round((src_h / src_w) * tw / a.cell_aspect))
    grids = []
    for f in frames:
        g, v = downsample(f, bb, tw, th, a.ramp, a.alpha_threshold)
        grids.append((g, v))
    # Trim rows that are empty in every frame (top + bottom) so the floor
    # sits directly under the feet with no gap.
    visible_rows = {r for _, v in grids for r, row in enumerate(v) if any(row)}
    if visible_rows:
        first, last = min(visible_rows), max(visible_rows)
        grids = [(g[first:last + 1], v[first:last + 1]) for g, v in grids]
    if len(a.floor) > 1:
        raise SystemExit("--floor must be a single character")
    fig_h = len(grids[0][0])
    anchor = (fig_h, tw // 2)            # bottom-center of figure
    if len(a.trigger) != 1:
        raise SystemExit("--trigger must be a single character")
    cfg = emit_cfg(grids, anchor, a.title, a.timing, a.shift_x, a.floor,
                   a.trigger)
    a.out.write_text(cfg)
    body_w = tw + abs(a.shift_x)
    print(f"wrote {a.out}: {fig_h} fig rows x {body_w} cols, {len(grids)} "
          f"frames, shift={a.shift_x:+d}, floor={a.floor!r}, "
          f"trigger={a.trigger!r}, {len(cfg.splitlines())} lines")


if __name__ == "__main__":
    main()
