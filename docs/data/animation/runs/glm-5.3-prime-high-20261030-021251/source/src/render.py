#!/usr/bin/env python3
"""
"PALE BLUE DOT" - a 10 second animation.

A slow zoom out from a living, rotating Earth to a single pale dot
hanging in the dark, carrying a message about our only home.

Pure Python (stdlib only) + ffmpeg. No external packages.

Usage:
    python3 src/render.py frame <index> <out.ppm>   # render single frame
    python3 src/render.py audio <out.wav>           # synthesize soundtrack
    python3 src/render.py video <out.mp4>           # render full animation
"""

import math
import random
import struct
import subprocess
import sys
import wave

FFMPEG = "ffmpeg"

# ---------------- frame / timeline constants ----------------
W, H = 800, 450
FPS = 24
NFRAMES = 240
DUR = NFRAMES / FPS          # 10.0 s
CX, CY = 400, 247            # earth center
TEXT_SCALE = 3
TEXT_Y = 385

# ---------------- world land map (72 x 36 cells, 5 deg each) ----------------
# Hand-tuned coarse equirectangular map; col = (lon+180)/5, row = (90-lat)/5
MAP_ROWS = [
    [],                                                          #  87.5N
    [(14, 21), (25, 31)],                                       #  82.5
    [(12, 22), (24, 32), (37, 38), (55, 56)],                   #  77.5
    [(10, 23), (25, 32), (40, 68)],                              #  72.5
    [(2, 23), (26, 32), (39, 70)],                               #  67.5
    [(2, 24), (26, 31), (38, 70)],                               #  62.5
    [(2, 25), (35, 36), (39, 70)],                               #  57.5
    [(8, 26), (34, 37), (38, 70)],                               #  52.5
    [(9, 26), (35, 68)],                                         #  47.5
    [(9, 26), (32, 36), (38, 39), (40, 46), (47, 62), (63, 64)],  #  42.5
    [(10, 25), (32, 35), (38, 38), (40, 61), (62, 63)],          #  37.5
    [(11, 25), (34, 49), (50, 62)],                              #  32.5
    [(14, 17), (22, 22), (34, 45), (45, 53), (54, 61)],          #  27.5
    [(14, 17), (22, 23), (34, 54), (55, 60)],                    #  22.5
    [(15, 19), (22, 24), (33, 46), (44, 48), (50, 54), (55, 59), (60, 61)],  # 17.5
    [(18, 19), (24, 28), (33, 47), (44, 47), (50, 53), (55, 58), (60, 61)],  # 12.5
    [(21, 31), (33, 46), (50, 51), (56, 57), (60, 61)],          #   7.5
    [(22, 30), (33, 48), (56, 60), (64, 66)],                    #   2.5
    [(23, 30), (34, 45), (56, 61), (63, 66)],                    #  -2.5
    [(23, 29), (34, 44), (57, 61), (63, 67)],                    #  -7.5
    [(24, 29), (35, 43), (59, 66)],                              # -12.5
    [(25, 29), (35, 43), (44, 45), (58, 66)],                    # -17.5
    [(25, 28), (36, 42), (44, 45), (58, 66)],                    # -22.5
    [(26, 28), (36, 41), (59, 65)],                              # -27.5
    [(27, 28), (37, 40), (60, 64)],                              # -32.5
    [(27, 28), (63, 64), (69, 70)],                              # -37.5
    [(27, 28), (63, 64), (69, 71)],                              # -42.5
    [(27, 28), (69, 70)],                                        # -47.5
    [(27, 28)],                                                  # -52.5
    [],                                                          # -57.5
    [(24, 25)],                                                  # -62.5
    [(3, 26), (32, 66)],                                         # -67.5
    [(1, 71)],                                                   # -72.5
    [(0, 71)], [(0, 71)], [(0, 71)],                             # -77.5 .. -87.5
]
assert len(MAP_ROWS) == 36


def build_map():
    g = [[0] * 72 for _ in range(36)]
    for r, ranges in enumerate(MAP_ROWS):
        for c0, c1 in ranges:
            for c in range(c0, min(71, c1) + 1):
                g[r][c] = 1
    # smooth to land fraction (wrap in longitude)
    s = [[0.0] * 72 for _ in range(36)]
    for j in range(36):
        jm = j - 1 if j > 0 else 0
        jp = j + 1 if j < 35 else 35
        for i in range(72):
            tot = 0.0
            for dj in (jm, j, jp):
                for di in ((i - 1) % 72, i, (i + 1) % 72):
                    tot += g[dj][di]
            s[j][i] = tot / 9.0
    return g, s


LANDGRID, SMAP = build_map()


# ---------------- clouds (value noise, 144 x 72) ----------------
def _sample(lat, u, v, nw, nh):
    x = u * nw
    i0 = int(x) % nw
    i1 = (i0 + 1) % nw
    fx = x - int(x)
    fx1 = 1.0 - fx
    y = v * (nh - 1)
    j0 = int(y)
    j1 = j0 + 1 if j0 < nh - 1 else j0
    fy = y - j0
    fy1 = 1.0 - fy
    return (lat[j0][i0] * fx1 + lat[j0][i1] * fx) * fy1 + \
           (lat[j1][i0] * fx1 + lat[j1][i1] * fx) * fy


def build_clouds():
    random.seed(5)
    L1 = [[random.random() for _ in range(13)] for _ in range(6)]
    L2 = [[random.random() for _ in range(25)] for _ in range(12)]
    L3 = [[random.random() for _ in range(49)] for _ in range(24)]
    grid = [[0.0] * 144 for _ in range(72)]
    for j in range(72):
        v = (j + 0.5) / 72.0
        latd = 90.0 - (j + 0.5) * 2.5
        alat = abs(latd)
        fall = 1.0 - 0.55 * (alat / 90.0) ** 2
        row = grid[j]
        for i in range(144):
            u = i / 144.0
            val = (_sample(L1, u, v, 12, 6) +
                   0.5 * _sample(L2, u, v, 24, 12) +
                   0.25 * _sample(L3, u, v, 48, 24)) / 1.75
            c = (val - 0.42) * 3.4
            if c < 0.0:
                c = 0.0
            elif c > 1.0:
                c = 1.0
            row[i] = c * 0.9 * fall
    return grid


CLOUD = build_clouds()


# ---------------- night-side city lights ----------------
def build_cities():
    random.seed(11)
    weights = []
    for r in range(36):
        w = 0.6
        if 5 <= r <= 16:
            w = 2.2
        if 8 <= r <= 12:
            w = 3.5
        if 13 <= r <= 14:
            w = 3.0
        if 20 <= r <= 22:
            w = 0.8
        if r >= 29:
            w = 0.0
        weights.append(int(w * 10))
    pool = []
    for r in range(36):
        pool.extend([r] * weights[r])
    cities = []
    while len(cities) < 700:
        r = random.choice(pool)
        c = random.randrange(72)
        if not LANDGRID[r][c]:
            continue
        lat = math.radians(87.5 - 5 * r + random.uniform(-2.4, 2.4))
        lon = math.radians(-180 + 5 * c + random.uniform(-2.4, 2.4))
        b = 0.35 + 0.65 * random.random() ** 1.6
        ph = random.random() * 6.283
        cities.append((lat, lon, b, ph))
    return cities


CITIES = build_cities()


# ---------------- starfield ----------------
def build_stars():
    random.seed(42)
    stars = []
    for _ in range(340):
        sx = random.randrange(W)
        sy = random.randrange(H)
        b = 0.2 + 0.8 * random.random() ** 1.6
        ph = random.random() * 6.283
        tint = random.random()
        if tint < 0.12:
            c = (200, 215, 255)
        elif tint < 0.20:
            c = (255, 230, 200)
        else:
            c = (255, 255, 255)
        stars.append((sx, sy, b, ph, c))
    return stars


STARS = build_stars()


# ---------------- faint background nebula (precomputed once) ----------------
def build_bg():
    random.seed(9)
    bg = bytearray(W * H * 3)
    blobs = []
    for _ in range(7):
        bx = random.uniform(0, W)
        by = random.uniform(0, H)
        s = random.uniform(160, 420)
        a = random.uniform(4, 10)
        col = (random.uniform(7, 15), random.uniform(9, 18), random.uniform(18, 36))
        blobs.append((bx, by, 2.0 * s * s, a, col))
    exp = math.exp
    raw = bytearray(W * H * 3)
    peak = 1e-9
    for y in range(H):
        for x in range(W):
            r = g = b = 0.0
            for (bx, by, s2, a, (cr, cg, cb)) in blobs:
                d2 = (x - bx) ** 2 + (y - by) ** 2
                v = a * exp(-d2 / s2)
                r += cr * v
                g += cg * v
                b += cb * v
            if b > peak:
                peak = b
            i = (y * W + x) * 3
            raw[i] = min(255, int(r))
            raw[i + 1] = min(255, int(g))
            raw[i + 2] = min(255, int(b))
    # normalize to a very faint tint (blue channel peaks ~ 26)
    k = 26.0 / peak
    for i in range(len(raw)):
        if raw[i]:
            raw[i] = int(raw[i] * k)
    bg = raw
    for y in range(H):
        rowb = y * W * 3
        for x in range(W):
            d = (x * 7 + y * 13) % 3 - 1      # tiny dither vs banding
            i = rowb + x * 3
            bg[i] = min(255, max(0, bg[i] + d))
            bg[i + 1] = min(255, max(0, bg[i + 1] + d))
            bg[i + 2] = min(255, max(0, bg[i + 2] + d))
    return bg


BG = build_bg()


# ---------------- 5x7 font (uppercase + punctuation) ----------------
GLYPHS = {
    'A': [".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    'B': ["####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."],
    'C': [".####", "#....", "#....", "#....", "#....", "#....", ".####"],
    'D': ["####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."],
    'E': ["#####", "#....", "#....", "####.", "#....", "#....", "#####"],
    'F': ["#####", "#....", "#....", "####.", "#....", "#....", "#...."],
    'G': [".###.", "#....", "#....", "#.###", "#...#", "#...#", ".###."],
    'H': ["#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    'I': ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "#####"],
    'K': ["#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"],
    'L': ["#....", "#....", "#....", "#....", "#....", "#....", "#####"],
    'M': ["#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"],
    'N': ["#...#", "##..#", "#.#.#", "#.#.#", "#..##", "#..##", "#...#"],
    'O': [".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    'P': ["####.", "#...#", "#...#", "####.", "#....", "#....", "#...."],
    'R': ["####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"],
    'S': [".####", "#....", "#....", ".###.", "....#", "....#", "####."],
    'T': ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."],
    'U': ["#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    'V': ["#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."],
    'W': ["#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"],
    'Y': ["#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."],
    ',': [".....", ".....", ".....", ".....", "..##.", "..##.", "..#.."],
    '.': [".....", ".....", ".....", ".....", ".....", "..##.", "..##."],
    "'": ["..#..", "..#..", ".....", ".....", ".....", ".....", "....."],
    '-': [".....", ".....", ".....", ".###.", ".....", ".....", "....."],
}


def _blur3(src, w, h):
    dst = bytearray(len(src))
    for y in range(h):
        ym = (y - 1) if y > 0 else 0
        yp = (y + 1) if y < h - 1 else h - 1
        rw, rmw, rpw = y * w, ym * w, yp * w
        for x in range(w):
            xm = (x - 1) if x > 0 else 0
            xp = (x + 1) if x < w - 1 else w - 1
            s = (src[rw + xm] + src[rw + x] + src[rw + xp] +
                 src[rmw + xm] + src[rmw + x] + src[rmw + xp] +
                 src[rpw + xm] + src[rpw + x] + src[rpw + xp])
            dst[rw + x] = s // 9
    return dst


TEXT_CACHE = {}


def get_mask(text):
    m = TEXT_CACHE.get(text)
    if m is not None:
        return m
    w = (6 * len(text) - 1) * TEXT_SCALE
    h = 7 * TEXT_SCALE
    mask = bytearray(w * h)
    xoff = 0
    for ch in text:
        if ch == ' ':
            xoff += 6 * TEXT_SCALE
            continue
        gl = GLYPHS.get(ch)
        if gl is None:
            raise KeyError("no glyph for %r" % ch)
        for gy in range(7):
            row = gl[gy]
            for gx in range(5):
                if row[gx] == '#':
                    for sy in range(TEXT_SCALE):
                        ybase = (gy * TEXT_SCALE + sy) * w
                        xo = xoff + gx * TEXT_SCALE
                        for sx in range(TEXT_SCALE):
                            mask[ybase + xo + sx] = 255
        xoff += 6 * TEXT_SCALE
    halo = mask
    for _ in range(4):
        halo = _blur3(halo, w, h)
    TEXT_CACHE[text] = (w, h, mask, halo)
    return TEXT_CACHE[text]


LINES = [
    ("EVERYONE YOU LOVE,", 0.8, 2.5),
    ("EVERYONE YOU HAVE EVER KNOWN,", 2.9, 4.6),
    ("EVERY HUMAN WHO HAS EVER LIVED -", 5.0, 6.7),
    ("LIVED HERE.", 7.1, 8.3),
    ("BE KIND. IT'S THE ONLY HOME WE'VE GOT.", 8.65, 9.9),
]


# ---------------- motion ----------------
def earth_R(fi):
    if fi < 120:
        return 400.0 - 2.8083 * fi
    r = 63.0 * math.exp(-0.0428 * (fi - 120))
    if fi > 190:
        tt = (fi - 190) / FPS
        r = 3.0 + 0.35 * (0.5 + 0.5 * math.sin(tt * 2.8))
    return r


# ---------------- drawing ----------------
LX, LY, LZ = -0.55, 0.35, 0.76   # light direction (from upper left)


def draw_stars(buf, t, gstar):
    sin = math.sin
    for (sx, sy, b, ph, (cr, cg, cb)) in STARS:
        tw = b * (0.78 + 0.22 * sin(t * 1.6 + ph)) * gstar
        if tw < 0.03:
            continue
        i = (sy * W + sx) * 3
        v = buf[i] + cr * tw
        buf[i] = 255 if v > 255 else (int(v) if v > 0 else 0)
        v = buf[i + 1] + cg * tw
        buf[i + 1] = 255 if v > 255 else (int(v) if v > 0 else 0)
        v = buf[i + 2] + cb * tw
        buf[i + 2] = 255 if v > 255 else (int(v) if v > 0 else 0)
        if b > 0.88 and tw > 0.3:
            for ox, oy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                xx = sx + ox
                yy = sy + oy
                if 0 <= xx < W and 0 <= yy < H:
                    j = (yy * W + xx) * 3
                    buf[j] = min(255, buf[j] + int(cr * tw * 0.35))
                    buf[j + 1] = min(255, buf[j + 1] + int(cg * tw * 0.35))
                    buf[j + 2] = min(255, buf[j + 2] + int(cb * tw * 0.35))


def draw_earth(buf, R, rot, t):
    invR = 1.0 / R
    R2 = R * R
    GR = R * 1.13
    GR2 = GR * GR
    x0 = max(0, int(CX - GR))
    x1 = min(W - 1, int(CX + GR) + 1)
    y0 = max(0, int(CY - GR))
    y1 = min(H - 1, int(CY + GR) + 1)
    base_b = rot * 0.2 + 36.0 + 720.0        # lon -> map col (multiple-of-72 offset)
    cloud_b = rot * 1.15 * 0.4 + 72.0 + 1440.0
    asin_, sqrt_ = math.asin, math.sqrt
    LXl, LYl, LZl = LX, LY, LZ

    for y in range(y0, y1):
        dy = y - CY
        ny = dy * invR
        ny2 = ny * ny
        north = -ny
        if -1.0 <= north <= 1.0:
            latd = asin_(north) * 57.2957795
        else:
            latd = 0.0          # row only touches the outer glow
        rowf = (90.0 - latd) * 0.2
        j0 = int(rowf)
        if j0 > 35:
            j0 = 35
        fy = rowf - j0
        fy1 = 1.0 - fy
        j1 = j0 + 1 if j0 < 35 else 35
        s0 = SMAP[j0]
        s1 = SMAP[j1]
        crowf = rowf * 2
        k0 = int(crowf)
        if k0 > 71:
            k0 = 71
        kfy = crowf - k0
        kfy1 = 1.0 - kfy
        k1 = k0 + 1 if k0 < 71 else 71
        c0 = CLOUD[k0]
        c1 = CLOUD[k1]

        # per-row surface colors (latitude bands)
        alat = latd if latd > 0 else -latd
        dw = math.exp(-((alat - 23.0) / 10.0) ** 2)
        if alat > 59.0:
            sw = min(1.0, (alat - 59.0) / 8.0)
        else:
            sw = 0.0
        lr = 52.0 + (168.0 - 52.0) * dw
        lg = 84.0 + (146.0 - 84.0) * dw
        lb = 52.0 + (100.0 - 52.0) * dw
        lr += (225.0 - lr) * sw
        lg += (232.0 - lg) * sw
        lb += (240.0 - lb) * sw
        orr, og, ob = 13.0, 34.0, 74.0
        if alat > 64.0:                        # frozen polar seas
            ow = min(1.0, (alat - 64.0) / 9.0)
            orr += (170.0 - orr) * ow
            og += (190.0 - og) * ow
            ob += (205.0 - ob) * ow

        rowstart = (y * W + x0) * 3
        for x in range(x0, x1):
            dx = x - CX
            r2 = dx * dx + dy * dy
            if r2 > GR2:
                continue
            if r2 <= R2:
                nx = dx * invR
                n2 = nx * nx + ny2
                z = sqrt_(1.0 - n2)
                lond = asin_(nx) * 57.2957795
                colf = lond * 0.2 + base_b
                i0 = int(colf)
                fx = colf - i0
                fx1 = 1.0 - fx
                i0 %= 72
                i1 = (i0 + 1) % 72
                land = (s0[i0] * fx1 + s0[i1] * fx) * fy1 + \
                       (s1[i0] * fx1 + s1[i1] * fx) * fy
                ccf = lond * 0.4 + cloud_b
                m0 = int(ccf)
                fcx = ccf - m0
                fcx1 = 1.0 - fcx
                m0 %= 144
                m1 = (m0 + 1) % 144
                cl = (c0[m0] * fcx1 + c0[m1] * fcx) * kfy1 + \
                     (c1[m0] * fcx1 + c1[m1] * fcx) * kfy
                if cl > 1.0:
                    cl = 1.0

                shade = nx * LXl + north * LYl + z * LZl
                if shade < -0.08:
                    day = 0.0
                elif shade > 0.12:
                    day = 1.0
                else:
                    d0 = (shade + 0.08) / 0.20
                    day = d0 * d0 * (3.0 - 2.0 * d0)
                lam = shade if shade > 0.0 else 0.0
                li = 0.05 + 0.95 * day * (0.35 + 0.65 * lam)

                if land > 0.35:
                    if land > 0.62:
                        la = 1.0
                    else:
                        q = (land - 0.35) / 0.27
                        la = q * q * (3.0 - 2.0 * q)
                    cr = orr + (lr - orr) * la
                    cg = og + (lg - og) * la
                    cb = ob + (lb - ob) * la
                else:
                    cr, cg, cb = orr, og, ob

                # per-pixel surface variation
                hz = (x * 2654435761 + y * 90533) & 255
                nvar = 0.90 + 0.0018 * hz
                cr *= nvar
                cg *= nvar
                cb *= nvar

                rv = cr * li + 3.0 * (1.0 - day)
                gv = cg * li + 5.0 * (1.0 - day)
                bv = cb * li + 12.0 * (1.0 - day)

                if cl > 0.02:                    # clouds
                    cw = cl * 0.85
                    clb = 0.10 + 0.90 * day
                    rv += (235.0 * clb - rv) * cw
                    gv += (242.0 * clb - gv) * cw
                    bv += (249.0 * clb - bv) * cw

                if n2 > 0.88:                    # atmospheric limb
                    hq = (n2 - 0.88) / 0.12
                    if hq > 1.0:
                        hq = 1.0
                    hq = hq * hq * (3.0 - 2.0 * hq)
                    hz = hq * 0.30 * (0.25 + 0.75 * day)
                    rv += (150.0 - rv) * hz
                    gv += (200.0 - gv) * hz
                    bv += (255.0 - bv) * hz

                i = rowstart + (x - x0) * 3
                buf[i] = 255 if rv > 255 else int(rv)
                buf[i + 1] = 255 if gv > 255 else int(gv)
                buf[i + 2] = 255 if bv > 255 else int(bv)
            else:
                # outer atmosphere glow
                ln = sqrt_(r2)
                a = (GR - ln) * invR / 0.13
                if a > 0.0:
                    a2 = a * a
                    ux = dx / ln
                    uy = dy / ln
                    lit = ux * LXl + uy * LYl
                    if lit < 0.0:
                        lit = 0.0
                    gb = a2 * (0.32 + 0.68 * lit) * 0.55
                    i = rowstart + (x - x0) * 3
                    v = buf[i] + 120.0 * gb
                    buf[i] = 255 if v > 255 else int(v)
                    v = buf[i + 1] + 180.0 * gb
                    buf[i + 1] = 255 if v > 255 else int(v)
                    v = buf[i + 2] + 255.0 * gb
                    buf[i + 2] = 255 if v > 255 else int(v)

    # night-side city lights
    if R > 25.0:
        rot_rad = math.radians(rot)
        cosr = math.cos(rot_rad)
        sinr = math.sin(rot_rad)
        sin_t = math.sin(t * 2.3)
        for (latr, lonr, b, ph) in CITIES:
            clt = math.cos(latr)
            slt = math.sin(latr)
            dlon = lonr - rot_rad
            vis = clt * math.cos(dlon)
            if vis <= 0.12:
                continue
            nxp = clt * math.sin(dlon)
            shade = nxp * LXl + slt * LYl + vis * LZl
            if shade > 0.02:
                continue
            nw = (0.02 - shade) * 7.0
            if nw > 1.0:
                nw = 1.0
            px = int(CX + nxp * R)
            py = int(CY - slt * R)
            if px < 0 or px >= W or py < 0 or py >= H:
                continue
            bb = b * nw * (0.8 + 0.2 * sin_t + 0.2 * math.sin(ph))
            i = (py * W + px) * 3
            buf[i] = min(255, buf[i] + int(255.0 * bb * 0.75))
            buf[i + 1] = min(255, buf[i + 1] + int(185.0 * bb * 0.75))
            buf[i + 2] = min(255, buf[i + 2] + int(105.0 * bb * 0.75))

    # soft halo as the world becomes a pale blue dot
    ga = (16.0 - R) / 11.0
    if ga > 0.0:
        if ga > 1.0:
            ga = 1.0
        pulse = 0.9 + 0.1 * math.sin(t * 2.8)
        sig = R * 1.5
        if sig < 3.0:
            sig = 3.0
        ext = sig * 3.0
        gx0 = max(0, int(CX - ext))
        gx1 = min(W - 1, int(CX + ext) + 1)
        gy0 = max(0, int(CY - ext))
        gy1 = min(H - 1, int(CY + ext) + 1)
        two_s2 = 2.0 * sig * sig
        gA = ga * pulse
        exp_ = math.exp
        for y in range(gy0, gy1):
            dy = y - CY
            rowb = y * W * 3
            for x in range(gx0, gx1):
                dx = x - CX
                g = exp_(-(dx * dx + dy * dy) / two_s2)
                if g < 0.02:
                    continue
                core = g * 0.55
                halo = g * 0.45
                i = rowb + x * 3
                v = buf[i] + (225.0 * core + 115.0 * halo) * gA
                buf[i] = 255 if v > 255 else int(v)
                v = buf[i + 1] + (240.0 * core + 175.0 * halo) * gA
                buf[i + 1] = 255 if v > 255 else int(v)
                v = buf[i + 2] + (255.0 * core + 255.0 * halo) * gA
                buf[i + 2] = 255 if v > 255 else int(v)


def draw_text(buf, text, alpha):
    if alpha <= 0.01:
        return
    w, h, mask, halo = get_mask(text)
    tx = CX - w // 2
    ty = TEXT_Y
    # subtitle scrim
    pad = 14
    sx0, sx1 = tx - pad, tx + w + pad
    sy0, sy1 = ty - pad, ty + h + pad
    a_s = 0.55 * alpha
    for y in range(max(0, sy0), min(H, sy1)):
        fy = min(1.0, y - sy0, sy1 - y) / 8.0
        if fy > 1.0:
            fy = 1.0
        if fy < 0.0:
            continue
        rowb = y * W * 3
        for x in range(max(0, sx0), min(W, sx1)):
            fx = min(1.0, x - sx0, sx1 - x) / 8.0
            if fx < 0.0:
                continue
            if fx > 1.0:
                fx = 1.0
            f = a_s * fy * fx
            if f < 0.01:
                continue
            keep = 1.0 - f
            i = rowb + x * 3
            buf[i] = int(buf[i] * keep)
            buf[i + 1] = int(buf[i + 1] * keep)
            buf[i + 2] = int(buf[i + 2] * keep)
    # glowing text
    for y in range(max(0, ty), min(H, ty + h)):
        oy = y - ty
        rowb = y * W * 3
        for x in range(max(0, tx), min(W, tx + w)):
            ox = x - tx
            o = oy * w + ox
            m = mask[o]
            hl = halo[o]
            if not m and not hl:
                continue
            add = alpha * 0.94 * m / 255.0
            hadd = alpha * (hl / 255.0)
            i = rowb + x * 3
            v = buf[i] + 255.0 * (add + 0.36 * hadd)
            buf[i] = 255 if v > 255 else int(v)
            v = buf[i + 1] + 255.0 * (add + 0.45 * hadd)
            buf[i + 1] = 255 if v > 255 else int(v)
            v = buf[i + 2] + 255.0 * (add + 0.62 * hadd)
            buf[i + 2] = 255 if v > 255 else int(v)


def render_frame(fi):
    t = fi / FPS
    buf = bytearray(BG)
    R = earth_R(fi)
    gstar = 0.35 + 0.65 * max(0.0, min(1.0, (160.0 - R) / 100.0))
    draw_stars(buf, t, gstar)
    rot = 5.0 - 0.30 * fi
    draw_earth(buf, R, rot, t)
    for (text, t0, t1) in LINES:
        a = min((t - t0) / 0.35, (t1 - t) / 0.35, 1.0)
        if a > 0.0:
            draw_text(buf, text, a)
    return buf


# ---------------- soundtrack ----------------
def make_wav(path):
    sr = 44100
    n = int(sr * DUR)
    TAU = 6.283185307179586
    partials = [   # (freq, amp, lfo_period, lfo_phase) - slow breathing drone on A
        (55.0, 0.150, 7.3, 0.0),
        (55.4, 0.085, 9.1, 2.1),
        (110.0, 0.100, 11.7, 4.0),
        (110.6, 0.050, 8.3, 1.2),
        (164.8, 0.040, 10.3, 3.3),
        (220.0, 0.026, 12.9, 5.2),
        (329.6, 0.011, 9.7, 0.7),
    ]
    bells = [(8.25, 440.0, 0.10), (8.85, 587.33, 0.065)]
    sin = math.sin
    exp_ = math.exp
    chunks = []
    for i in range(n):
        t = i / sr
        s = 0.0
        for (f, a, per, ph) in partials:
            s += a * (0.72 + 0.28 * sin(TAU * t / per + ph)) * sin(TAU * f * t)
        for (t0, f, a) in bells:
            dt = t - t0
            if dt > 0.0:
                e = exp_(-2.6 * dt)
                if e > 0.001:
                    atk = dt / 0.012
                    if atk > 1.0:
                        atk = 1.0
                    s += a * atk * e * (sin(TAU * f * dt) +
                                        0.45 * sin(TAU * 2.76 * f * dt) +
                                        0.18 * sin(TAU * 5.4 * f * dt))
        if t < 1.8:
            g = t / 1.8
            g = g * g * (3.0 - 2.0 * g)
        elif t > DUR - 0.9:
            g = (DUR - t) / 0.9
        else:
            g = 1.0
        v = s * g
        if v > 0.95:
            v = 0.95
        elif v < -0.95:
            v = -0.95
        chunks.append(struct.pack('<hh', int(v * 30000), int(v * 30000)))
    with wave.open(path, 'wb') as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(b''.join(chunks))


# ---------------- drivers ----------------
def write_ppm(path, buf):
    with open(path, 'wb') as f:
        f.write(b"P6\n%d %d\n255\n" % (W, H))
        f.write(bytes(buf))


def main():
    argv = sys.argv[1:]
    if not argv:
        print(__doc__)
        return
    mode = argv[0]
    if mode == "frame":
        fi = int(argv[1])
        write_ppm(argv[2], render_frame(fi))
    elif mode == "audio":
        make_wav(argv[1])
        print("wrote", argv[1])
    elif mode == "video":
        out = argv[1]
        audio = "src/audio.wav"
        print("synthesizing soundtrack ...", file=sys.stderr)
        make_wav(audio)
        cmd = [
            FFMPEG, '-y', '-loglevel', 'error',
            '-f', 'rawvideo', '-pix_fmt', 'rgb24',
            '-framerate', str(FPS), '-s', '%dx%d' % (W, H), '-i', '-',
            '-i', audio,
            '-c:v', 'libx264', '-preset', 'slow', '-crf', '25',
            '-vf', 'format=yuv420p,fade=t=in:st=0:d=0.7,fade=t=out:st=9.3:d=0.7',
            '-c:a', 'aac', '-b:a', '128k',
            '-shortest', '-movflags', '+faststart',
            out,
        ]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        import time
        t0 = time.time()
        for fi in range(NFRAMES):
            proc.stdin.write(bytes(render_frame(fi)))
            if fi % 24 == 0:
                dt = time.time() - t0
                print("frame %d/%d  (%.1fs elapsed)" % (fi, NFRAMES, dt),
                      file=sys.stderr, flush=True)
        proc.stdin.close()
        proc.wait()
        print("wrote", out, file=sys.stderr)
    else:
        print("unknown mode", mode)


if __name__ == "__main__":
    main()
