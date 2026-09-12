#!/usr/bin/env python3
"""torchfab.py -- a replica-parallel rewriting engine in torch that runs zahradnice
.cfg programs with the engine's own semantics: per replica, one applicable
(cell, rule) pair per event, chosen with probability proportional to rule weight,
then its RHS written. B replicas advance in lock-step; each has its own RNG
stream, its own input bits and labels. No curses, no sounds, no `$`, no includes.

usage: torchfab.py CFG --screen R,C --replicas B --task xor --n 3000 --seed 1
                   --phases i:10,o:80,T:1,f:160,c:12 [--device cuda] [--explain-check K]
"""
import argparse, os, random, subprocess, sys, time
import torch

# ---------------------------------------------------------------- cfg parser
DC, EQ, NEQ, EQ2, SPACE = 0, 1, 2, 3, 4      # LHS cell modes

class Rule:
    __slots__ = ("lhs", "key", "rep", "ctx", "ctxrep", "score", "weight", "line",
                 "lhs_cells", "rhs_cells", "head")
    def __init__(self):
        self.lhs_cells = []; self.rhs_cells = []

def parse_cfg(path):
    text = open(path, encoding="utf-8").read().split("\n")
    seeds = []; rules = []
    heads = []; body = []; body_started = False
    def flush():
        nonlocal heads, body, body_started
        if heads:
            b = list(body)
            while b and b[-1] == "": b.pop()
            for h, ln in heads: rules.append(process(h, ln, b))
        heads = []; body = []; body_started = False
    for i, line in enumerate(text, 1):
        if line.startswith("#"): continue
        if line.startswith("^"):
            seeds.append(line); continue
        if line.startswith("="):
            if body_started: flush()
            heads.append((line, i)); continue
        if heads:
            if not body_started and line == "": continue      # leading blank rows are dropped
            body_started = True; body.append(line)
    flush()
    return seeds, rules

def process(head, line, body):
    r = Rule(); r.head = head.rstrip(); r.line = line
    f = lambda i, d: head[i] if len(head) > i and head[i] != " " else d
    r.lhs = f(2, "s"); r.key = f(3, "?"); r.rep = head[4] if len(head) > 4 else " "
    if r.key == "~": r.key = " "
    ctx = f(7, None); ctxrep = head[8] if len(head) > 8 else " "
    if ctx in ("?", None): r.ctx = None
    elif ctx == "~": r.ctx = " "
    elif ctx == "*": r.ctx = r.lhs
    else: r.ctx = ctx
    if ctxrep == "*": r.ctxrep = r.lhs
    elif ctxrep == "~": r.ctxrep = " "
    else: r.ctxrep = ctxrep                      # " " = no-op write
    tail = head[10:].split() if len(head) > 10 else []
    r.score = int(tail[0]) if tail else 0
    r.weight = float(tail[1]) if len(tail) > 1 else 1.0
    if r.weight <= 0: r.weight = 1.0
    ats = [(ri, ci) for ri, row in enumerate(body) for ci, ch in enumerate(row) if ch == "@"]
    assert len(ats) == 3, (head, body)
    (ro, co), (rm, cm), (rq, cq) = ats
    horizontal = cq > co
    for ri, row in enumerate(body):
        for ci, ch in enumerate(row):
            if ch == " " or (ri, ci) == (rm, cm): continue
            in_lhs = (ci < cm) if horizontal else (ri < rm)
            in_rhs = (ci > cm) if horizontal else (ri > rm)
            if in_lhs:
                dr, dc = ri - ro, ci - co
                if ch == "@": continue                          # the anchor: matched by selection
                if ch == "~": r.lhs_cells.append((dr, dc, SPACE, 0, 0))
                elif ch == "&": r.lhs_cells.append((dr, dc, EQ, r.ctx, 0) if r.ctx is not None else (dr, dc, -1, 0, 0))
                elif ch == "!": r.lhs_cells.append((dr, dc, NEQ, r.ctx, 0) if r.ctx is not None else (dr, dc, DC, 0, 0))
                elif ch == "%": r.lhs_cells.append((dr, dc, EQ2, r.ctx, r.ctxrep) if r.ctx is not None else (dr, dc, EQ, r.ctxrep, 0))
                elif ch == "*": r.lhs_cells.append((dr, dc, EQ, r.lhs, 0))
                else: r.lhs_cells.append((dr, dc, EQ, ch, 0))
            elif in_rhs:
                dr, dc = ri - rq, ci - cq
                if ch == "@":
                    if r.rep == "~": r.rhs_cells.append((dr, dc, " "))
                    elif r.rep != " ": r.rhs_cells.append((dr, dc, r.rep))
                elif ch == "~": r.rhs_cells.append((dr, dc, " "))
                elif ch == "&":
                    if r.ctxrep != " ": r.rhs_cells.append((dr, dc, r.ctxrep))
                elif ch == "*": r.rhs_cells.append((dr, dc, r.lhs))
                elif ch == "$": raise SystemExit("$ restore is not supported: line %d" % line)
                else: r.rhs_cells.append((dr, dc, ch))
    return r

def explain_check(cfg, rules, check_bin, k):
    """Compare our decoded geometry with `zahradnice-check explain` on k random rules."""
    rng = random.Random(0); bad = 0
    for r in rng.sample(rules, min(k, len(rules))):
        out = subprocess.run([check_bin, "explain", cfg, "--line", str(r.line)], capture_output=True, text=True).stdout
        m = set(); w = set(); sec = None
        for ln in out.splitlines():
            if ln.strip().startswith("matches"): sec = "m"; continue
            if ln.strip().startswith("writes"): sec = "w"; continue
            if sec and ln.strip().startswith("("):
                off = ln.strip().split(")")[0].strip("(")
                dr, dc = (int(x) for x in off.split(","))
                if "anchor char" in ln: continue
                (m if sec == "m" else w).add((dr, dc))
        ours_m = {(dr, dc) for dr, dc, mode, _, _ in r.lhs_cells}
        ours_w = {(dr, dc) for dr, dc, _ in r.rhs_cells}
        if m != ours_m or w != ours_w:
            bad += 1; print("MISMATCH line %d: explain m=%s w=%s ours m=%s w=%s" % (r.line, sorted(m), sorted(w), sorted(ours_m), sorted(ours_w)))
    print("explain-check: %d rules compared, %d mismatches" % (min(k, len(rules)), bad))
    return bad == 0

# ---------------------------------------------------------------- engine
class Fabric:
    def __init__(self, cfg, rows, cols, B, device, seed):
        self.seeds, self.rules = parse_cfg(cfg)
        self.R, self.C, self.B, self.dev = rows - 1, cols, B, device     # row 0 (status) excluded
        glyphs = {" "}
        for r in self.rules:
            glyphs.add(r.lhs)
            for _, _, mode, g1, g2 in r.lhs_cells:
                if isinstance(g1, str): glyphs.add(g1)
                if isinstance(g2, str): glyphs.add(g2)
            for _, _, g in r.rhs_cells: glyphs.add(g)
        for s in self.seeds:
            if len(s) > 1: glyphs.add(s[1])
        self.gid = {g: i for i, g in enumerate(sorted(glyphs, key=lambda g: (g != " ", g)))}
        assert self.gid[" "] == 0
        self.gen = torch.Generator(device="cpu").manual_seed(seed)
        self.grid = torch.zeros(B, self.R, self.C, dtype=torch.int64, device=device)
        self.score = torch.zeros(B, dtype=torch.int64, device=device)
        for s in self.seeds: self.plant(s)
        # rule tables per key: anchor glyph -> padded tensors
        self.tables = {}
        keys = {r.key for r in self.rules}
        for key in keys:
            if key == "?": continue
            self.tables[key] = self.build_table([r for r in self.rules if r.key in (key, "?")])
        self.wild = self.build_table([r for r in self.rules if r.key == "?"])

    def g(self, ch):
        return self.gid[ch]

    def plant(self, s):
        if len(s) == 1: self.grid.zero_(); return
        ch = s[1]; v = s[2] if len(s) > 2 else "c"; h = s[3] if len(s) > 3 else "c"
        rows = {"u": [0], "l": [self.R - 1], "c": [self.R // 2], "*": list(range(self.R))}.get(v, [self.R // 2])
        cols = {"l": [0], "r": [self.C - 1], "c": [self.C // 2], "*": list(range(self.C))}.get(h, [self.C // 2])
        for r in rows:
            for c in cols: self.grid[:, r, c] = self.g(ch)

    def build_table(self, rules):
        by_anchor = {}
        for r in rules: by_anchor.setdefault(self.g(r.lhs), []).append(r)
        table = {}
        for a, rs in by_anchor.items():
            K = max([len(r.lhs_cells) for r in rs] + [1]); W = max([len(r.rhs_cells) for r in rs] + [1])
            n = len(rs)
            L = torch.zeros(n, K, 5, dtype=torch.int64); L[:, :, 2] = DC
            Wt = torch.zeros(n, W, 3, dtype=torch.int64); Wt[:, :, 2] = -1
            wt = torch.zeros(n, dtype=torch.float64); sc = torch.zeros(n, dtype=torch.int64)
            for i, r in enumerate(rs):
                for j, (dr, dc, mode, g1, g2) in enumerate(r.lhs_cells):
                    if mode == -1: mode, g1 = EQ, -1                        # unset ctx: never matches
                    L[i, j] = torch.tensor([dr, dc, mode, self.g(g1) if isinstance(g1, str) else g1, self.g(g2) if isinstance(g2, str) else g2])
                for j, (dr, dc, gch) in enumerate(r.rhs_cells):
                    Wt[i, j] = torch.tensor([dr, dc, self.g(gch)])
                wt[i] = r.weight; sc[i] = r.score
            table[a] = (L.to(self.dev), Wt.to(self.dev), wt.to(self.dev), sc.to(self.dev), rs)
        return table

    def step(self, trig):
        """trig: list of B trigger chars. Applies one rule per replica where possible.
        Returns a list (len B) of the applied Rule or None."""
        applied = [None] * self.B
        dev = self.dev
        for key in set(trig):
            table = self.tables.get(key)
            if table is None: table = self.wild
            if not table: continue
            bsel = torch.tensor([i for i, t in enumerate(trig) if t == key], device=dev)
            cand_b, cand_r, cand_c, cand_w, cand_ref = [], [], [], [], []
            for a, (L, Wt, wt, sc, rs) in table.items():
                pos = (self.grid[bsel] == a).nonzero()                     # (P, 3): sub-b, r, c
                if pos.numel() == 0: continue
                P = pos.shape[0]; n, K = L.shape[0], L.shape[1]
                rr = (pos[:, 1].view(P, 1, 1) + L[:, :, 0].view(1, n, K)) % self.R
                cc = (pos[:, 2].view(P, 1, 1) + L[:, :, 1].view(1, n, K)) % self.C
                bb = bsel[pos[:, 0]].view(P, 1, 1).expand(P, n, K)
                v = self.grid[bb, rr, cc]                                   # (P, n, K)
                mode = L[:, :, 2].view(1, n, K); g1 = L[:, :, 3].view(1, n, K); g2 = L[:, :, 4].view(1, n, K)
                ok = (mode == DC) | ((mode == EQ) & (v == g1)) | ((mode == NEQ) & (v != g1)) \
                     | ((mode == EQ2) & ((v == g1) | (v == g2))) | ((mode == SPACE) & (v == 0))
                match = ok.all(dim=2)                                       # (P, n)
                idx = match.nonzero()                                       # (M, 2): p, rule
                if idx.numel() == 0: continue
                cand_b.append(bsel[pos[idx[:, 0], 0]]); cand_r.append(pos[idx[:, 0], 1]); cand_c.append(pos[idx[:, 0], 2])
                cand_w.append(wt[idx[:, 1]]); cand_ref.append((a, idx[:, 1]))
            if not cand_b: continue
            b = torch.cat(cand_b); r = torch.cat(cand_r); c = torch.cat(cand_c); w = torch.cat(cand_w)
            ref_a = torch.cat([torch.full((len(ix),), a, dtype=torch.int64, device=dev) for a, ix in cand_ref])
            ref_i = torch.cat([ix for _, ix in cand_ref])
            # one weighted draw per replica: keys (b) -> segmented sampling via Gumbel-max
            u = torch.rand(w.shape[0], generator=self.gen, dtype=torch.float64).to(dev)
            keyv = torch.log(w) - torch.log(-torch.log(u))                 # Gumbel-max ∝ w
            best = torch.full((self.B,), -float("inf"), dtype=torch.float64, device=dev)
            best = best.scatter_reduce(0, b, keyv, reduce="amax")
            win = (keyv == best[b]).nonzero().squeeze(1)
            # ties are measure-zero; keep first per replica anyway
            seen = set(); chosen = []
            for i in win.tolist():
                bi = int(b[i])
                if bi in seen: continue
                seen.add(bi); chosen.append(i)
            chosen = torch.tensor(chosen, device=dev)
            for i in chosen.tolist():
                bi, a, ri = int(b[i]), int(ref_a[i]), int(ref_i[i])
                L, Wt, wt, sc, rs = table[a]
                rule = rs[ri]; applied[bi] = rule
                rr0, cc0 = int(r[i]), int(c[i])
                for dr, dc, gch in Wt[ri].tolist():
                    if gch < 0: continue
                    self.grid[bi, (rr0 + dr) % self.R, (cc0 + dc) % self.C] = gch
                self.score[bi] += int(sc[ri])
        return applied

    def dump(self, b=0):
        inv = {v: k for k, v in self.gid.items()}
        return "\n".join("".join(inv[int(x)] for x in row).rstrip() for row in self.grid[b].tolist())

# ---------------------------------------------------------------- driver
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cfg"); ap.add_argument("--screen", default="6,16"); ap.add_argument("--replicas", type=int, default=8)
    ap.add_argument("--task", default="xor"); ap.add_argument("--n", type=int, default=1000); ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--nin", type=int, default=8); ap.add_argument("--phases", default="i:10,o:80,T:1,f:160,c:12")
    ap.add_argument("--win", type=int, default=250); ap.add_argument("--device", default="cpu")
    ap.add_argument("--explain-check", type=int, default=0); ap.add_argument("--check-bin", default=os.path.join(os.path.dirname(__file__), "../../../zahradnice-check"))
    ap.add_argument("--dump", action="store_true")
    a = ap.parse_args()
    rows, cols = (int(x) for x in a.screen.split(","))
    fab = Fabric(a.cfg, rows, cols, a.replicas, a.device, a.seed)
    print("%s: %d rules, %d glyphs, %d replicas on %s" % (a.cfg, len(fab.rules), len(fab.gid), a.replicas, a.device))
    if a.explain_check:
        ok = explain_check(a.cfg, fab.rules, a.check_bin, a.explain_check)
        if not ok: sys.exit(1)
    B, nin = a.replicas, a.nin
    rngs = [random.Random((a.seed * 1000 + b) * 7919 + 17) for b in range(B)]
    thr = []
    for rng in rngs:
        w = [rng.choice([-2, -1, 1, 2]) for _ in range(nin)]
        dots = sorted(sum(wi * ((x >> i) & 1) for i, wi in enumerate(w)) for x in range(1 << nin))
        thr.append((w, dots[len(dots) // 2]))
    def label(b, bits):
        if a.task == "maj": return int(sum(bits) > nin // 2)
        if a.task == "and": return bits[0] & bits[1]
        if a.task == "xor": return bits[0] ^ bits[1]
        if a.task == "par3": return bits[0] ^ bits[1] ^ bits[2]
        if a.task == "thr": w, bb = thr[b]; return int(sum(wi * bi for wi, bi in zip(w, bits)) > bb)
    phases = [(p.split(":")[0], int(p.split(":")[1])) for p in a.phases.split(",")]
    fab.step(["b"] * B)
    correct = torch.zeros(B, a.n, dtype=torch.bool)
    t0 = time.time(); events = 0
    for t in range(a.n):
        bits = [[rngs[b].randint(0, 1) for _ in range(nin)] for b in range(B)]
        ys = [label(b, bits[b]) for b in range(B)]
        for i in range(nin):
            fab.step([str(bits[b][i]) for b in range(B)]); events += 1
        s0 = fab.score.clone()
        for ch, cnt in phases:
            for _ in range(cnt):
                if ch == "T": fab.step(["p" if ys[b] else "n" for b in range(B)])
                else: fab.step([ch] * B)
                events += 1
        correct[:, t] = (fab.score - s0).cpu() > 0
        if (t + 1) % a.win == 0:
            acc = correct[:, t + 1 - a.win:t + 1].float().mean(dim=1)
            print("  samples %5d  acc mean %.3f  min %.3f  max %.3f  (%.0f ev/s across replicas)" %
                  (t + 1, acc.mean(), acc.min(), acc.max(), events * B / (time.time() - t0)), flush=True)
    acc = correct[:, -a.n // 4:].float().mean(dim=1)
    print("final (last quarter): mean %.3f  min %.3f  max %.3f  over %d replicas; %.1f s" % (acc.mean(), acc.min(), acc.max(), B, time.time() - t0))
    if a.dump: print(fab.dump(0))

if __name__ == "__main__":
    main()
