#!/usr/bin/env python3
"""Render 'Kindness is contagious' — a constellation of lights assembling into a heart.

Pure standard-library Python. Streams raw RGB24 frames to stdout (pipe mode)
so ffmpeg can encode them directly, or writes selected preview frames to disk.

Usage:
    python3 render.py                 # stream all frames as raw RGB24 to stdout
    python3 render.py --preview 90,140,200,235   # write preview_fNNNN.raw files
"""

import math
import random
import sys

# ----------------------------------------------------------------------------
# Canvas / timing
# ----------------------------------------------------------------------------
W, H = 1280, 720
FPS = 24
DUR = 10.0
TOTAL = int(FPS * DUR)  # 240 frames

# Palette
BG_TOP = (11, 15, 34)
BG_BOT = (20, 26, 54)
WARM = (255, 203, 106)       # heart / sparks gold
WARMW = (255, 235, 205)      # warm white (lines, text, ripples)
COOL = (132, 168, 226)       # cool blue dust
HEART_GLOW = (255, 158, 84)  # big warm glow

HEART_CX, HEART_CY = 640.0, 300.0


def clamp01(x):
    if x < 0.0:
        return 0.0
    if x > 1.0:
        return 1.0
    return x


def mix(a, b, t):
    return a + (b - a) * t


def ease_out_cubic(x):
    x = clamp01(x)
    return 1.0 - (1.0 - x) ** 3


def ease_in_out(x):
    x = clamp01(x)
    return x * x * (3.0 - 2.0 * x)


# ----------------------------------------------------------------------------
# Background (static): vertical gradient + distant warmth + vignette
# ----------------------------------------------------------------------------
def build_background():
    buf = bytearray(W * H * 3)
    cx, cy = HEART_CX, HEART_CY
    for y in range(H):
        row = y * W * 3
        g = y / (H - 1)
        br = int(mix(BG_TOP[0], BG_BOT[0], g))
        bg = int(mix(BG_TOP[1], BG_BOT[1], g))
        bb = int(mix(BG_TOP[2], BG_BOT[2], g))
        for x in range(W):
            # distant warmth toward center
            dx = (x - cx) / 210.0
            dy = (y - cy) / 190.0
            wf = math.exp(-(dx * dx + dy * dy))
            # vignette
            nx = (x - W / 2) / (W / 2)
            ny = (y - H / 2) / (H / 2)
            v = 1.0 - 0.22 * (nx * nx + ny * ny)
            r = br * v + HEART_GLOW[0] * wf * 0.10
            g_ = bg * v + HEART_GLOW[1] * wf * 0.09
            b = bb * v + HEART_GLOW[2] * wf * 0.08
            i = row + x * 3
            buf[i] = int(r) if r < 255 else 255
            buf[i + 1] = int(g_) if g_ < 255 else 255
            buf[i + 2] = int(b) if b < 255 else 255
    return buf


# ----------------------------------------------------------------------------
# Radial glow sprites (precomputed at several brightness levels)
# ----------------------------------------------------------------------------
def make_glow(half, sigma, color, levels, thresh=0.015):
    """Return (offs3, Rs, Gs, Bs) where each of Rs/Gs/Bs is a list-per-level."""
    cr, cg, cb = color
    px = []
    for dy in range(-half, half + 1):
        yy = dy * dy
        for dx in range(-half, half + 1):
            d2 = yy + dx * dx
            f = math.exp(-d2 / (2.0 * sigma * sigma))
            if f < thresh:
                continue
            px.append(((dy * W + dx) * 3, f))
    offs3 = [o for o, _ in px]
    Rs, Gs, Bs = [], [], []
    nm1 = levels - 1
    for L in range(levels):
        s = L / nm1
        R, G, B = [], [], []
        for _, f in px:
            v = cr * f * s
            R.append(int(v) if v < 255 else 255)
            v = cg * f * s
            G.append(int(v) if v < 255 else 255)
            v = cb * f * s
            B.append(int(v) if v < 255 else 255)
        Rs.append(R)
        Gs.append(G)
        Bs.append(B)
    return offs3, Rs, Gs, Bs


def blit(buf, cx, cy, offs3, R, G, B):
    base = (int(cy) * W + int(cx)) * 3
    n = len(offs3)
    for i in range(n):
        j = base + offs3[i]
        a = buf[j] + R[i]
        buf[j] = a if a < 256 else 255
        j += 1
        a = buf[j] + G[i]
        buf[j] = a if a < 256 else 255
        j += 1
        a = buf[j] + B[i]
        buf[j] = a if a < 256 else 255


# ----------------------------------------------------------------------------
# Heart geometry
# ----------------------------------------------------------------------------
def heart_point(t):
    s, c = math.sin(t), math.cos(t)
    x = 16.0 * s * s * s
    y = 13.0 * c - 5.0 * math.cos(2 * t) - 2.0 * math.cos(3 * t) - math.cos(4 * t)
    return x, y


def build_heart_dots(rng):
    scale = 14.2
    dots = []  # (tx, ty, sx, sy, dist, phase, ai_index)
    outline = []
    n_out = 122
    for k in range(n_out):
        t = 2.0 * math.pi * k / n_out
        x, y = heart_point(t)
        jitter = rng.uniform(0.985, 1.015)
        outline.append((x * jitter, y * jitter))
    for k in range(40):
        t = rng.uniform(0, 2 * math.pi)
        x, y = heart_point(t)
        rr = math.sqrt(rng.random()) * 0.82
        outline.append((x * rr, y * rr))
    for (x, y) in outline:
        tx = HEART_CX + x * scale
        ty = HEART_CY - y * scale
        dist = math.hypot(x * scale, y * scale)
        sx = rng.uniform(90, W - 90)
        sy = rng.uniform(90, H - 90)
        dots.append([tx, ty, sx, sy, dist, rng.uniform(0, 2 * math.pi)])
    dots.sort(key=lambda d: d[4])
    return dots


# ----------------------------------------------------------------------------
# 5x7 pixel font (only the letters we need)
# ----------------------------------------------------------------------------
FONT = {
    'A': ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    'C': ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    'D': ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    'E': ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    'G': ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    'I': ("11111", "00100", "00100", "00100", "00100", "00100", "11111"),
    'K': ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    'N': ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    'O': ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    'P': ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    'S': ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    'T': ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    'U': ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
}


def text_dots(s, cell, x0, y0):
    """Return list of [gx, gy, ci, c] for every lit pixel of message s."""
    out = []
    ci = 0
    for ch in s:
        if ch == ' ':
            ci += 1
            continue
        g = FONT[ch]
        for r, row in enumerate(g):
            for c, bit in enumerate(row):
                if bit == '1':
                    out.append([x0 + (ci * 6 + c) * cell + cell / 2,
                                y0 + r * cell + cell / 2, ci, c])
        ci += 1
    return out


def text_width(s, cell):
    return len(s) * 6 * cell


MSG = "KINDNESS IS CONTAGIOUS"
SUB = "PASS IT ON"


# ----------------------------------------------------------------------------
# Frame renderer
# ----------------------------------------------------------------------------
def setup(rng):
    bg = build_background()
    # glow sprites
    dot_warm = make_glow(16, 3.0, WARM, 40)
    dot_cool = make_glow(5, 1.6, COOL, 24)
    dot_ww = make_glow(3, 1.4, WARMW, 24)      # text / ripple
    line_w = make_glow(2, 1.0, WARMW, 14)      # connecting lines
    big = make_glow(130, 66.0, HEART_GLOW, 18)
    heart_dots = build_heart_dots(rng)

    # ambient dust
    dust = []
    for _ in range(70):
        dust.append([rng.uniform(0, W), rng.uniform(0, H),
                     rng.uniform(0, 2 * math.pi), rng.uniform(0.25, 0.85),
                     rng.uniform(0.3, 1.2)])
    # text dot layouts
    cell_main = 7
    xm = (W - text_width(MSG, cell_main)) / 2
    main_td = text_dots(MSG, cell_main, xm, 556)
    cell_sub = 5
    xs = (W - text_width(SUB, cell_sub)) / 2
    sub_td = text_dots(SUB, cell_sub, xs, 628)

    # neighbor pairs from final heart positions (connected constellation)
    pairs = []
    n = len(heart_dots)
    for i in range(n):
        xi, yi = heart_dots[i][0], heart_dots[i][1]
        for j in range(i + 1, n):
            xj, yj = heart_dots[j][0], heart_dots[j][1]
            if abs(xi - xj) > 100 or abs(yi - yj) > 100:
                continue
            if (xi - xj) ** 2 + (yi - yj) ** 2 < 104 ** 2:
                pairs.append((i, j))
    return (bg, dot_warm, dot_cool, dot_ww, line_w, big, heart_dots, dust,
            pairs, main_td, sub_td)


# timeline constants
T0 = 1.2          # ripple starts
TEND = 6.1        # ripple reaches far edge of heart
BEATS = (6.95, 8.35)

_rng = random.Random(20261030)
BG, DOTW, DOTC, DOTWW, LINEW, BIG, HEART, DUST, PAIRS, MAINTD, SUBTD = setup(_rng)


def ring_points(cx, cy, r):
    n = max(6, int(r * 0.35))
    pts = []
    for k in range(n):
        a = 2 * math.pi * k / n
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def heartbeat(t):
    v = 0.0
    for b in BEATS:
        d = (t - b) / 0.14
        v += math.exp(-d * d)
    return v


def render_frame(f, buf):
    t = f / FPS

    # ---- wavefront ----
    maxd = HEART[-1][4]
    speed = maxd / (TEND - T0)
    wave = (t - T0) * speed if t > T0 else 0.0

    ow, or_, og, ob = DOTW
    ocw, ocr, ocg, ocb = DOTC
    for d in HEART:
        tx, ty, sx, sy, dist, phase = d
        ai = clamp01((wave - (dist - 70.0)) / 140.0)
        e = ease_out_cubic(ai)
        x = sx + (tx - sx) * e
        y = sy + (ty - sy) * e
        tw = 0.86 + 0.14 * math.sin(phase * 6.283 + t * 2.1)
        bright = (0.14 + 0.86 * ai) * tw * (1.0 + 0.16 * heartbeat(t) * ai)
        L = int(bright * 39.0 + 0.5)
        if L > 39:
            L = 39
        if L > 0 and 16 <= x <= W - 17 and 16 <= y <= H - 17:
            blit(buf, x, y, ow, or_[L], og[L], ob[L])

    # ---- ambient dust ----
    for s in DUST:
        x = s[0] + 3.0 * math.sin(t * 0.35 + s[2])
        y = s[1] + 3.0 * math.cos(t * 0.28 + s[2] * 1.7)
        tw = 0.70 + 0.30 * math.sin(t * 1.4 + s[2] * 3.0)
        b = s[3] * tw
        L = int(b * 23.0 + 0.5)
        if L > 0 and 6 <= x <= W - 7 and 6 <= y <= H - 7:
            blit(buf, x, y, ocw, ocr[L], ocg[L], ocb[L])

    # ---- connections ----
    lw, lr, lg, lb = LINEW
    for (i, j) in PAIRS:
        ai = clamp01((wave - (HEART[i][4] - 70.0)) / 140.0)
        aj = clamp01((wave - (HEART[j][4] - 70.0)) / 140.0)
        a = min(ai, aj)
        if a < 0.55:
            continue
        xi = HEART[i][0] if ai >= 1 else (HEART[i][2] + (HEART[i][0] - HEART[i][2]) * ease_out_cubic(ai))
        yi = HEART[i][1] if ai >= 1 else (HEART[i][3] + (HEART[i][1] - HEART[i][3]) * ease_out_cubic(ai))
        xj = HEART[j][0] if aj >= 1 else (HEART[j][2] + (HEART[j][0] - HEART[j][2]) * ease_out_cubic(aj))
        yj = HEART[j][1] if aj >= 1 else (HEART[j][3] + (HEART[j][1] - HEART[j][3]) * ease_out_cubic(aj))
        dx = xj - xi
        dy = yj - yi
        d = math.hypot(dx, dy)
        if d < 1:
            continue
        alpha = (1.0 - d / 150.0) * 0.55 * a
        steps = max(1, int(d / 4.0))
        L = int(alpha * 13.0 + 0.5)
        if L <= 0:
            continue
        for k in range(1, steps):
            u = k / steps
            blit(buf, xi + dx * u, yi + dy * u, lw, lr[L], lg[L], lb[L])

    # ---- big warm glow behind heart ----
    bw, br_, bg_, bb_ = BIG
    ga = clamp01((wave - 120.0) / (maxd - 120.0))          # grows as it assembles
    gtot = (0.25 + 0.75 * ga) * (0.9 + 0.30 * heartbeat(t + 0.06))
    L = int(clamp01(gtot) * 17.0 + 0.5)
    if L > 0:
        blit(buf, HEART_CX, HEART_CY, bw, br_[L], bg_[L], bb_[L])

    # ---- ripple rings ----
    tw_, tr_, tg_, tb_ = DOTWW
    if 5 < wave < 400:
        a = 1.0 if wave < 200 else (1.0 - (wave - 200) / 150.0)
        L = int(a * 18.0 + 0.5)
        if L > 0:
            for (rx, ry) in ring_points(HEART_CX, HEART_CY, wave):
                if 3 <= rx <= W - 4 and 3 <= ry <= H - 4:
                    blit(buf, rx, ry, tw_, tr_[L], tg_[L], tb_[L])
    # heartbeat ripples (kindness radiating outward)
    for b in BEATS:
        dt = t - b
        if 0 < dt < 1.7:
            r = 36.0 + dt * 240.0
            a = (1.0 - dt / 1.7) * 0.5
            L = int(a * 23.0 + 0.5)
            if L > 0:
                for (rx, ry) in ring_points(HEART_CX, HEART_CY, r):
                    if 3 <= rx <= W - 4 and 3 <= ry <= H - 4:
                        blit(buf, rx, ry, tw_, tr_[L], tg_[L], tb_[L])

    # ---- text ----
    def draw_text(td, t_start, stagger):
        for (gx, gy, ci, c) in td:
            ts = t_start + ci * stagger + c * 0.012
            vis = clamp01((t - ts) / 0.35)
            if vis <= 0:
                continue
            twi = 0.80 + 0.20 * math.sin(t * 2.0 + gx * 0.35 + gy * 0.7)
            L = int(vis * twi * 23.0 + 0.5)
            if L > 0:
                blit(buf, gx, gy, tw_, tr_[L], tg_[L], tb_[L])

    draw_text(MAINTD, 6.85, 0.05)
    draw_text(SUBTD, 8.05, 0.055)


def main():
    args = sys.argv[1:]
    if args and args[0] == '--preview' and len(args) > 1:
        idxs = [int(x) for x in args[1].split(',')]
        for idx in idxs:
            buf = bytearray(BG)
            render_frame(idx, buf)
            with open(f'preview_f{idx:04d}.raw', 'wb') as fo:
                fo.write(buf)
            print(f'wrote preview_f{idx:04d}.raw', file=sys.stderr)
        return
    out = sys.stdout.buffer
    for f in range(TOTAL):
        buf = bytearray(BG)
        render_frame(f, buf)
        out.write(buf)
    sys.stdout.flush()


if __name__ == '__main__':
    main()