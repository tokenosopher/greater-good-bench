"""call someone.  --  a 9.6 second animation.

A dark world made of hundreds of faint blue lights. One of them reaches out
across a gap. Warmth travels thread to thread, person to person, until there
is nowhere left in the frame that is cold.

Pure stdlib: additive light accumulation in 8-bit energy buffers, a filmic
tone curve baked into per-frame LUTs, raw rgb24 frames piped to ffmpeg.
"""
import os
import math
import random
import subprocess
import sys

sys.path.insert(0, 'src')
from font import TTF, text_polygons, rasterize
from pngutil import write_png

W, H = 1920, 1080
FPS = 30
DUR = 9.6
NF = int(round(DUR * FPS))

T_PULSE = 1.15      # A notices
T_SHOOT = 1.62      # the thread leaves A
T_CATCH = 2.32      # contact
T_ALL = 6.20        # the last light
T_TITLE = 7.45      # the words arrive

TAU = math.pi * 2
ENERGY = 96.0
SPR_Q = 20
SIZES = [8, 11, 15, 20, 27, 38, 54]
GW, GH = 120, 68      # ambient haze grid
AMB_R, AMB_G, AMB_B = 72, 31, 11   # peak of the warm air


def clamp(x, a=0.0, b=1.0):
    return a if x < a else (b if x > b else x)


def smoothstep(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


def ease_out(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def hash2(ix, iy, seed=0):
    n = (ix * 374761393 + iy * 668265263 + seed * 1442695040888963407) & 0xFFFFFFFF
    n = (n ^ (n >> 13)) * 1274126177 & 0xFFFFFFFF
    return ((n ^ (n >> 16)) & 0xFFFFFF) / float(0xFFFFFF)


def vnoise(x, y, seed=0):
    ix, iy = math.floor(x), math.floor(y)
    fx, fy = x - ix, y - iy
    ux, uy = smoothstep(fx), smoothstep(fy)
    a = hash2(ix, iy, seed)
    b = hash2(ix + 1, iy, seed)
    c = hash2(ix, iy + 1, seed)
    d = hash2(ix + 1, iy + 1, seed)
    return (a * (1 - ux) + b * ux) * (1 - uy) + (c * (1 - ux) + d * ux) * uy


def fbm(x, y, seed=0, oct=3):
    s, amp, tot = 0.0, 1.0, 0.0
    for o in range(oct):
        s += amp * vnoise(x * (2 ** o), y * (2 ** o), seed + o * 17)
        tot += amp
        amp *= 0.5
    return s / tot


# -------------------------------------------------------------------- world
class World:
    """Lights = people.  'souls' carry threads; 'dust' is everyone further off."""

    def __init__(self, seed=11):
        rnd = random.Random(seed)

        # --- inhabited regions, drawn as loose clumps along soft filaments
        pts = []
        clumps = []
        for _ in range(11):
            cx = rnd.uniform(W * 0.02, W * 0.98)
            cy = rnd.uniform(-H * 0.06, H * 1.06)
            sx = rnd.uniform(70, 210)
            sy = rnd.uniform(60, 190)
            n = rnd.randint(14, 34)
            clumps.append((cx, cy, sx, sy, n))
        want = []
        for cx, cy, sx, sy, n in clumps:
            for _ in range(n):
                a = rnd.uniform(0, TAU)
                r = math.sqrt(rnd.random())
                want.append((cx + math.cos(a) * r * sx * 1.7,
                             cy + math.sin(a) * r * sy * 1.7))
        for _ in range(120):
            want.append((rnd.uniform(-50, W + 50), rnd.uniform(-50, H + 50)))
        rnd.shuffle(want)

        # --- souls: well separated, they are the ones we can follow
        souls = []
        tries = 0
        while len(souls) < 74 and tries < 40000:
            tries += 1
            x = rnd.uniform(-30, W + 30)
            y = rnd.uniform(-30, H + 30)
            if abs(x - W * 0.5) < 390 and abs(y - H * 0.84) < 130:
                continue
            ok = True
            for p in souls:
                if (p['x'] - x) ** 2 + (p['y'] - y) ** 2 < 132 ** 2:
                    ok = False
                    break
            if ok:
                souls.append(self._mk(rnd, x, y, 'soul'))
        # --- dust: everything else, everywhere
        dust = []
        for x, y in want:
            if len(dust) >= 330:
                break
            if abs(x - W * 0.5) < 340 and abs(y - H * 0.84) < 105:
                continue
            ok = True
            for p in dust:
                if (p['x'] - x) ** 2 + (p['y'] - y) ** 2 < 46 ** 2:
                    ok = False
                    break
            if ok:
                dust.append(self._mk(rnd, x, y, 'dust'))
        self.souls = souls
        self.dust = dust
        self.nodes = souls + dust
        # the one nearest to us
        hero = self._mk(rnd, W * 0.775, H * 0.545, 'hero')
        hero['br'] = 1.0
        self.hero = hero
        self.nodes.append(hero)

        # --- threads between souls: a loose web of acquaintance
        N = len(souls)
        eset = set()
        for i, a in enumerate(souls):
            d = sorted(((math.hypot(a['x'] - b['x'], a['y'] - b['y']), j)
                        for j, b in enumerate(souls) if j != i))
            for dd, j in d[:3]:
                if dd < 430:
                    eset.add((min(i, j), max(i, j)))
        parent = list(range(N))

        def find(a):
            while parent[a] != a:
                parent[a] = parent[parent[a]]
                a = parent[a]
            return a

        for a, b in eset:
            ra, rb = find(a), find(b)
            if ra != rb:
                parent[ra] = rb
        comps = {}
        for i in range(N):
            comps.setdefault(find(i), []).append(i)
        if len(comps) > 1:
            reps = [c[0] for c in comps.values()]
            for k in range(1, len(reps)):
                best = None
                for u in reps[:k]:
                    for v in reps[k:]:
                        dd = math.hypot(souls[u]['x'] - souls[v]['x'],
                                        souls[u]['y'] - souls[v]['y'])
                        if best is None or dd < best[0]:
                            best = (dd, u, v)
                eset.add((min(best[1], best[2]), max(best[1], best[2])))

        self.edges = []
        for a, b in sorted(eset):
            na, nb = souls[a], souls[b]
            L = math.hypot(na['x'] - nb['x'], na['y'] - nb['y'])
            self.edges.append({'a': a, 'b': b, 'L': L,
                               'jit': rnd.uniform(0.86, 1.20),
                               'bow': rnd.uniform(-0.13, 0.13) * L,
                               't0': None, 't1': None})
        self._pick_origin(rnd)
        self._solve(rnd)

    # ------------------------------------------------------------- helpers
    def _mk(self, rnd, x, y, kind):
        dep = clamp((fbm(x / 560.0, y / 560.0, seed=3, oct=3) - 0.28) / 0.46)
        if kind == 'soul':
            cls = 4 + (1 if rnd.random() < 0.55 + 0.4 * dep else 0)
        else:
            cls = int(clamp(round(1.0 + 2.4 * (dep ** 1.4) + rnd.uniform(-0.9, 0.7)), 0, 3))
        return {
            'x': x, 'y': y, 'kind': kind, 'dep': dep, 'cls': cls,
            'br': 0.55 + 0.55 * dep,
            'ph': rnd.uniform(0, TAU),
            'fr': rnd.uniform(0.18, 0.5),
            'arr': 0.0, 'root': False,
        }

    def _pick_origin(self, rnd):
        target = (W * 0.38, H * 0.44)
        A = min(self.souls, key=lambda n: math.hypot(n['x'] - target[0], n['y'] - target[1]))
        cands = []
        for n in self.souls:
            if n is A:
                continue
            d = math.hypot(n['x'] - A['x'], n['y'] - A['y'])
            if 230 < d < 420:
                cands.append((abs(d - 330), n))
        cands.sort(key=lambda c: c[0])
        B = cands[0][1]
        self.A, self.B = A, B
        A['root'] = True
        B['root'] = True

    def _solve(self, rnd):
        A, B = self.A, self.B
        ox, oy = (A['x'] + B['x']) * 0.5, (A['y'] + B['y']) * 0.5
        self.origin = (ox, oy)
        dmax = max(math.hypot(n['x'] - ox, n['y'] - oy) for n in self.nodes)
        span = T_ALL - T_CATCH
        for n in self.nodes:
            d = math.hypot(n['x'] - ox, n['y'] - oy) / dmax
            # the front is not a circle: local weather bends it
            wob = (fbm(n['x'] / 230.0, n['y'] / 230.0, seed=41, oct=3) - 0.5)
            ns = 0.55 if n['kind'] == 'dust' else 0.34
            n['arr'] = T_CATCH + span * (clamp(d) ** 0.92 + wob * ns * 0.55) \
                + rnd.uniform(-0.07, 0.07)
        A['arr'] = T_CATCH
        B['arr'] = T_CATCH
        self.hero['arr'] = T_ALL - 0.30
        for n in self.nodes:
            n['arr'] = max(n['arr'], T_CATCH)
        # sparks run along the threads: from whoever lights first to the other
        for e in self.edges:
            na, nb = self.souls[e['a']], self.souls[e['b']]
            e['t1'] = max(na['arr'], nb['arr'])
            e['dur'] = 0.28 + e['L'] / 2400.0
            e['t0'] = e['t1'] - e['dur']
            e['from_b'] = nb['arr'] < na['arr']
            e['spark'] = abs(na['arr'] - nb['arr']) < 1.05


def build_ambient_offsets(nodes):
    """For each node: (cell index, weight) list for the wide warm haze."""
    sig = 4.6
    rad = int(sig * 2.6)
    kern = []
    for dy in range(-rad, rad + 1):
        for dx in range(-rad, rad + 1):
            w = math.exp(-(dx * dx + dy * dy) / (2 * sig * sig))
            if w > 0.02:
                kern.append((dx, dy, w))
    out = []
    for n in nodes:
        cx = n['x'] / (W / GW)
        cy = n['y'] / (H / GH)
        lst = []
        for dx, dy, w in kern:
            gx = int(round(cx)) + dx
            gy = int(round(cy)) + dy
            if 0 <= gx < GW and 0 <= gy < GH:
                lst.append((gy * GW + gx, w))
        out.append(lst)
    return out


def bez(x0, y0, cx, cy, x1, y1, u):
    a = (1 - u) ** 2
    b = 2 * u * (1 - u)
    c = u * u
    return (a * x0 + b * cx + c * x1, a * y0 + b * cy + c * y1)


# ------------------------------------------------------------------ sprites
def build_sprites():
    COOL = (0.22, 0.44, 0.92)
    WARM = (1.00, 0.52, 0.20)
    out = {}
    for cls, R in enumerate(SIZES):
        soft = cls < 4          # the ones further off are out of focus
        hot_scale = 0.0 if soft else 1.0
        for q in range(SPR_Q + 1):
            f = q / SPR_Q
            px = []
            for dy in range(-R, R + 1):
                for dx in range(-R, R + 1):
                    u2 = (dx * dx + dy * dy) / float(R * R)
                    if u2 > 1.0:
                        continue
                    u = math.sqrt(u2)
                    if soft:
                        amp = math.exp(-(u / 0.42) ** 2) * 0.60 * (1.0 - u * u) ** 1.3
                    else:
                        core = math.exp(-(u / 0.15) ** 2)
                        halo = math.exp(-(u / 0.34) ** 2)
                        wide = math.exp(-(u / 0.80) ** 2) * (0.16 + 0.34 * f)
                        amp = 0.52 * core + 0.42 * halo + wide
                        amp *= (1.0 - u * u) ** 0.9
                    cr = amp * ((1 - f) * COOL[0] + f * WARM[0])
                    cg = amp * ((1 - f) * COOL[1] + f * WARM[1])
                    cb = amp * ((1 - f) * COOL[2] + f * WARM[2])
                    h = f * math.exp(-(u / 0.11) ** 2) * 1.0 * hot_scale
                    cr += h
                    cg += h
                    cb += h * 0.96
                    px.append((dy * W + dx, int(cr * ENERGY + 0.5),
                               int(cg * ENERGY + 0.5), int(cb * ENERGY + 0.5)))
            offs = [p[0] for p in px]
            out[(cls, q)] = (px, min(offs), max(offs))
    return out


SPRITES = build_sprites()


def _hero_sprites():
    R = 165
    out = []
    for q in range(9):
        f = q / 8.0
        px = []
        for dy in range(-R, R + 1):
            for dx in range(-R, R + 1):
                u2 = (dx * dx + dy * dy) / float(R * R)
                if u2 > 1.0:
                    continue
                u = math.sqrt(u2)
                amp = (math.exp(-(u / 0.24) ** 2) * 0.30
                       + math.exp(-(u / 0.62) ** 2) * (0.16 + 0.10 * f))
                amp *= (1.0 - u * u) ** 1.1
                cr = amp * ((1 - f) * 0.22 + f * 1.0)
                cg = amp * ((1 - f) * 0.44 + f * 0.50)
                cb = amp * ((1 - f) * 0.92 + f * 0.17)
                h = f * math.exp(-(u / 0.055) ** 2) * 1.0
                px.append((dy * W + dx, int((cr + h) * ENERGY + 0.5),
                           int((cg + h * 0.92) * ENERGY + 0.5),
                           int((cb + h * 0.84) * ENERGY + 0.5)))
        offs = [p[0] for p in px]
        out.append((px, min(offs), max(offs)))
    return out


HERO = _hero_sprites()


def _spark():
    px = []
    for dy in range(-13, 14):
        for dx in range(-13, 14):
            u2 = (dx * dx + dy * dy) / 169.0
            if u2 <= 1:
                a = math.exp(-u2 * 3.2) * (1 - u2) ** 0.6 * ENERGY * 1.9
                px.append((dy * W + dx, int(a), int(a * 0.70), int(a * 0.44)))
    offs = [p[0] for p in px]
    return (px, min(offs), max(offs))


SPARK = _spark()


def blit(r, g, b, sprite, cx, cy, k):
    px, lo, hi = sprite
    if cx < 0 or cy < 0 or cx >= W or cy >= H:
        return
    base = cy * W + cx
    if base + lo < 0 or base + hi >= W * H:
        return
    if k >= 0.999:
        for off, wr, wg, wb in px:
            i = base + off
            v = r[i] + wr
            r[i] = v if v < 255 else 255
            v = g[i] + wg
            g[i] = v if v < 255 else 255
            v = b[i] + wb
            b[i] = v if v < 255 else 255
    else:
        for off, wr, wg, wb in px:
            i = base + off
            v = r[i] + int(wr * k + 0.5)
            r[i] = v if v < 255 else 255
            v = g[i] + int(wg * k + 0.5)
            g[i] = v if v < 255 else 255
            v = b[i] + int(wb * k + 0.5)
            b[i] = v if v < 255 else 255


# --------------------------------------------------------------- base plate
def build_plate():
    r = bytearray(W * H)
    g = bytearray(W * H)
    b = bytearray(W * H)
    for y in range(H):
        t = y / (H - 1.0)
        for x in range(W):
            n = fbm(x / 430.0, y / 430.0, seed=11, oct=3)
            n2 = fbm(x / 120.0, y / 120.0, seed=29, oct=2)
            v = 1.1 + 5.0 * (t ** 2.2) + 4.6 * (n ** 2.2) + 1.2 * n2
            i = y * W + x
            r[i] = int(v * 0.60)
            g[i] = int(v * 0.78)
            b[i] = int(v * 1.32)
    return r, g, b


PLATE = build_plate()


# --------------------------------------------------------------------- text
class Title:
    def __init__(self, text, path='/System/Library/Fonts/Avenir.ttc', index=6,
                 target_w=850, baseline=0.215):
        f = TTF(path, index)
        polys, adv, _ = text_polygons(f, text, tracking=f.unitsPerEm * 0.055)
        scale = adv / float(target_w)
        xs = [x for p in polys for x, _ in p]
        ys = [y for p in polys for _, y in p]
        oy = H * (1 - baseline)
        ox = W / 2.0 - (min(xs) + max(xs)) / 2.0 / scale
        pad = 30
        self.y0 = max(0, int(oy - max(ys) / scale) - pad)
        self.y1 = min(H, int(oy - min(ys) / scale) + pad)
        cov = rasterize(polys, W, self.y1 - self.y0, ox, oy - self.y0, scale, ss=3)
        self.n = len(cov)
        self.steps = []
        for s in range(33):
            k = s / 32.0
            lay = bytearray(self.n)
            for i in range(self.n):
                c = cov[i]
                if c:
                    lay[i] = int(c * k)
            self.steps.append(lay)

    def stamp(self, img, k, dy=0):
        s = int(round(clamp(k) * 32))
        if s <= 0:
            return
        lay = self.steps[s]
        hh = self.y1 - self.y0
        for yy in range(hh):
            ty = self.y0 + yy + dy
            if ty < 0 or ty >= H:
                continue
            row = ty * W
            lo = yy * W
            for x in range(W):
                c = lay[lo + x]
                if c:
                    p = (row + x) * 3
                    v = img[p] + c
                    img[p] = v if v < 255 else 255
                    v = img[p + 1] + int(c * 0.93)
                    img[p + 1] = v if v < 255 else 255
                    v = img[p + 2] + int(c * 0.79)
                    img[p + 2] = v if v < 255 else 255


# ---------------------------------------------------------------- tone curve
def build_lut(exposure, warm):
    lr = bytearray(256)
    lg = bytearray(256)
    lb = bytearray(256)
    for v in range(256):
        x = v / 255.0
        y = 1.0 - math.exp(-x * 2.75)
        y = y ** 0.90 * exposure
        z = 255.0 * (y * (1.0 + 0.08 * warm) + 0.0012)
        lr[v] = 0 if z < 0 else (255 if z > 255 else int(z))
        z = 255.0 * (y * (1.0 + 0.01 * warm) + 0.0012)
        lg[v] = 0 if z < 0 else (255 if z > 255 else int(z))
        z = 255.0 * (y * (1.0 - 0.06 * warm) + 0.0016)
        lb[v] = 0 if z < 0 else (255 if z > 255 else int(z))
    return lr, lg, lb


# ------------------------------------------------------------------- render
class Renderer:
    def __init__(self, world, title):
        self.w = world
        self.title = title
        self.amb_off = build_ambient_offsets(world.nodes)

    def cam(self, t):
        z = 1.0 + 0.05 * ease_out(t / DUR)
        return (z, W * 0.5 + 14.0 * math.sin(t * 0.21),
                H * 0.5 + 9.0 * math.cos(t * 0.16))

    def project(self, x, y, cam, dep=0.5):
        z, cx, cy = cam
        par = 0.35 + 0.75 * dep
        return (W * 0.5 + (x - W * 0.5) * z + (cx - W * 0.5) * 0.5 * z * par,
                H * 0.5 + (y - H * 0.5) * z + (cy - H * 0.5) * 0.5 * z * par)

    def thread(self, r, g, b, x0, y0, x1, y1, frac, k, col, bow, taper=True):
        dx, dy = x1 - x0, y1 - y0
        L = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / L, dx / L
        cx = (x0 + x1) / 2 + nx * bow
        cy = (y0 + y1) / 2 + ny * bow
        n = max(2, int(L))
        lim = int(frac * n)
        vr = int(col[0] * k + 0.5)
        vg = int(col[1] * k + 0.5)
        vb = int(col[2] * k + 0.5)
        if vr == vg == vb == 0:
            return
        for i in range(lim + 1):
            u = i / n
            x = int((1 - u) ** 2 * x0 + 2 * u * (1 - u) * cx + u * u * x1)
            y = int((1 - u) ** 2 * y0 + 2 * u * (1 - u) * cy + u * u * y1)
            if x < 1 or y < 1 or x >= W - 1 or y >= H - 1:
                continue
            f = 1.0
            if taper:
                f = 0.30 + 0.70 * min(1.0, u * 7.0, (1.0 - u) * 7.0)
            o = y * W + x
            for oo, ww in ((0, 1.0), (W, 0.75)):
                p = o + oo
                ar = int(vr * f * ww)
                ag = int(vg * f * ww)
                ab = int(vb * f * ww)
                if ar:
                    v = r[p] + ar
                    r[p] = v if v < 255 else 255
                if ag:
                    v = g[p] + ag
                    g[p] = v if v < 255 else 255
                if ab:
                    v = b[p] + ab
                    b[p] = v if v < 255 else 255

    def ring(self, r, g, b, cx, cy, rad, k, col):
        """A soft expanding breath of light."""
        n = max(64, int(rad * 2.4))
        for o, ww in ((-2.2, 0.18), (-1.1, 0.45), (0.0, 1.0), (1.1, 0.45), (2.2, 0.18)):
            rr = rad + o * (1.0 + rad * 0.004)
            a = k * ww
            dr = int(col[0] * a * 60 + 0.5)
            dg = int(col[1] * a * 60 + 0.5)
            db = int(col[2] * a * 60 + 0.5)
            if not (dr or dg or db):
                continue
            for i in range(n):
                t = i / n * TAU
                x = int(cx + math.cos(t) * rr)
                y = int(cy + math.sin(t) * rr)
                if x < 1 or y < 1 or x >= W - 1 or y >= H - 1:
                    continue
                q = y * W + x
                v = r[q] + dr
                r[q] = v if v < 255 else 255
                v = g[q] + dg
                g[q] = v if v < 255 else 255
                v = b[q] + db
                b[q] = v if v < 255 else 255

    def render(self, t):
        r = bytearray(PLATE[0])
        g = bytearray(PLATE[1])
        b = bytearray(PLATE[2])
        cam = self.cam(t)
        wd = self.w

        # ---------- the web between the souls
        for e in wd.edges:
            na, nb = wd.souls[e['a']], wd.souls[e['b']]
            x0, y0 = self.project(na['x'], na['y'], cam, na['dep'])
            x1, y1 = self.project(nb['x'], nb['y'], cam, nb['dep'])
            dep = (na['dep'] + nb['dep']) * 0.5
            bow = e['bow'] * cam[0]
            if t >= e['t0']:
                f = clamp((t - e['t0']) / max(1e-3, e['t1'] - e['t0']))
                if f >= 1.0:
                    kk = 6.0 + 4.5 * dep
                    kk *= 0.88 + 0.12 * math.sin(t * 1.3 + e['a'] * 1.7)
                    self.thread(r, g, b, x0, y0, x1, y1, 1.0, kk,
                                (1.0, 0.44, 0.20), bow)
                else:
                    self.thread(r, g, b, x0, y0, x1, y1, f, 13.0 + 7.0 * dep,
                                (1.0, 0.76, 0.60), bow)
                    if e['spark']:
                        L = e['L'] or 1.0
                        mx = (x0 + x1) / 2 - (y1 - y0) / L * bow
                        my = (y0 + y1) / 2 + (x1 - x0) / L * bow
                        u = 1.0 - f if e['from_b'] else f
                        tx, ty = bez(x0, y0, mx, my, x1, y1, u)
                        blit(r, g, b, SPARK, int(tx), int(ty), 0.55)
            else:
                self.thread(r, g, b, x0, y0, x1, y1, 1.0, 2.6 + 2.6 * dep,
                            (0.38, 0.54, 1.0), bow, taper=False)

        # ---------- the first reach
        A, B = wd.A, wd.B
        ax, ay = self.project(A['x'], A['y'], cam, A['dep'])
        bx, by = self.project(B['x'], B['y'], cam, B['dep'])
        if t >= T_SHOOT:
            f = ease_out((t - T_SHOOT) / (T_CATCH - T_SHOOT))
            L = math.hypot(bx - ax, by - ay) or 1.0
            nx, ny = -(by - ay) / L, (bx - ax) / L
            bow = 30.0 * cam[0]
            mx = (ax + bx) / 2 + nx * bow
            my = (ay + by) / 2 + ny * bow
            self.thread(r, g, b, ax, ay, bx, by, f,
                        34.0 if f < 1 else 9.0, (1.0, 0.62, 0.34), bow,
                        taper=False)
            if f < 1:
                u = f
                tx = (1 - u) ** 2 * ax + 2 * u * (1 - u) * mx + u * u * bx
                ty = (1 - u) ** 2 * ay + 2 * u * (1 - u) * my + u * u * by
                blit(r, g, b, SPARK, int(tx), int(ty), 1.0)

        # ---------- A's small pulse before the reach
        if T_PULSE <= t < T_PULSE + 1.05:
            u = (t - T_PULSE) / 1.05
            self.ring(r, g, b, ax, ay, 6 + 130 * ease_out(u),
                      0.5 * (1 - u) ** 1.7, (0.85, 0.78, 1.0))

        # ---------- contact
        if t >= T_CATCH:
            u = t - T_CATCH
            if u < 1.3:
                self.ring(r, g, b, (ax + bx) / 2, (ay + by) / 2,
                          12 + 330 * ease_out(u / 1.3),
                          0.55 * (1 - u / 1.3) ** 1.8, (1.0, 0.64, 0.38))
            if u < 1.1:
                fl = (1 - u / 1.1) ** 2.0
                blit(r, g, b, HERO[5], int((ax + bx) / 2), int((ay + by) / 2),
                     0.75 * fl)
                # the two of them flare, then settle into their new warmth
                for qx, qy in ((ax, ay), (bx, by)):
                    blit(r, g, b, SPARK, int(qx), int(qy), 1.15 * fl)
            if u < 1.0:
                blit(r, g, b, SPARK, int(ax), int(ay), (1 - u) ** 2 * 1.3)

        # ---------- everyone
        post = clamp((t - T_ALL) / 1.6)
        pulse = 0.5 - 0.5 * math.cos((t - T_ALL) * TAU / 2.7) if post > 0 else 0.0
        for n in wd.nodes:
            tt = t - n['arr']
            if tt <= 0:
                w = 0.0
                flash = 0.0
            else:
                w = 1 - math.exp(-tt / 0.17)
                flash = math.exp(-tt / 0.32) * 0.55
            flick = 0.86 + 0.14 * math.sin(t * n['fr'] * TAU + n['ph'])
            px, py = self.project(n['x'], n['y'], cam, n['dep'])
            q = int(round(clamp(w) * SPR_Q))
            inten = (1.0 + flash) * n['br'] * flick
            if w > 0.001:
                inten *= 1.0 + 0.20 * pulse * post
            if n['root']:
                inten *= 1.25
            cold = 0.46 if n['kind'] == 'soul' else 0.30
            k = inten * (cold + (1 - cold) * min(1.0, w * 4.0))
            if n['kind'] == 'dust':
                k *= 0.44
            blit(r, g, b, SPRITES[(n['cls'], q)], int(px), int(py), k)

        # ---------- embers
        if t > T_ALL - 1.9:
            ea = clamp((t - (T_ALL - 1.9)) / 1.9)
            for i in range(70):
                ph = hash2(i, 3, 91)
                sp = 10 + 22 * hash2(i, 7, 13)
                x = (hash2(i, 11, 5) * W * 1.1 + t * (7 - 12 * ph)) % W
                y = H + 30 - (t * sp + ph * H * 1.8) % (H + 70)
                kk = ea * (0.20 + 0.16 * math.sin(t * 1.9 + ph * 21))
                blit(r, g, b, SPRITES[(1, 13)], int(x), int(y), kk)
        # ---------- the light nearest to us
        h = self.w.hero
        tt = t - h['arr']
        wv = 0.0 if tt <= 0 else 1 - math.exp(-tt / 0.22)
        hx, hy = self.project(h['x'], h['y'], cam, 1.0)
        q = int(round(clamp(wv) * 8))
        blit(r, g, b, HERO[q], int(hx), int(hy),
             (0.34 + 0.80 * min(1.0, wv * 3.0)) * (1.0 + 0.16 * pulse * post))
        if tt > 0 and tt < 2.4:
            u = min(1.0, tt / 2.0)
            self.ring(r, g, b, hx, hy, 30 + 620 * ease_out(u),
                      0.42 * (1 - u) ** 1.5, (1.0, 0.66, 0.40))

        # ---------- the warmth in the air (coarse field, upscaled later)
        acc = [0.0] * (GW * GH)
        for idx, n in enumerate(wd.nodes):
            tt = t - n['arr']
            if tt <= 0:
                continue
            wv = (1 - math.exp(-tt / 0.35)) ** 1.8
            if n['kind'] == 'dust':
                wv *= 0.45
            if n['kind'] == 'root':
                pass
            if n['root']:
                wv *= 1.5
            if n['kind'] == 'hero':
                wv *= 3.0
            if wv < 0.004:
                continue
            for cell, wt in self.amb_off[idx]:
                acc[cell] += wv * wt
        amb = bytearray(GW * GH * 3)
        for i, v in enumerate(acc):
            if v <= 0.0:
                continue
            e = 1.0 - math.exp(-v * 0.075)
            rv = int(e * AMB_R)
            gv = int(e * AMB_G)
            bv = int(e * AMB_B)
            amb[3 * i] = 255 if rv > 255 else rv
            amb[3 * i + 1] = 255 if gv > 255 else gv
            amb[3 * i + 2] = 255 if bv > 255 else bv
        return r, g, b, cam, amb


def exposure_at(t):
    e = 1.0
    if t > T_ALL:
        e -= 0.06 * smoothstep((t - T_ALL) / 1.6)
    e *= 1.0 - 0.17 * smoothstep((t - T_TITLE) / 1.5)
    return e


def to_rgb(r, g, b, t):
    exp = exposure_at(t)
    warm = 0.45 + 0.55 * smoothstep((t - T_CATCH) / (T_ALL - T_CATCH))
    lr, lg, lb = build_lut(exp, warm)
    out = bytearray(W * H * 3)
    out[0::3] = bytes(r).translate(lr)
    out[1::3] = bytes(g).translate(lg)
    out[2::3] = bytes(b).translate(lb)
    return out


def main():
    world = World()
    title = Title('call someone.')
    ren = Renderer(world, title)
    args = sys.argv[1:]

    if args and args[0] == 'stills':
        for t in [float(x) for x in args[1].split(',')]:
            r, g, b, cam, amb = ren.render(t)
            img = to_rgb(r, g, b, t)
            k = clamp((t - T_TITLE) / 1.55)
            if k > 0:
                title.stamp(img, smoothstep(k), int(round(9 * (1 - smoothstep(k)))))
            write_png('still_%.2f.png' % t, W, H, img)
            write_png('amb_%03d.png' % int(round(t * FPS)), GW, GH, amb)
            print('still', t)
        return

    out = args[0] if args else 'build.mp4'
    os.makedirs('amb', exist_ok=True)
    cmd = ['ffmpeg', '-y', '-loglevel', 'error',
           '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '%dx%d' % (W, H),
           '-r', str(FPS), '-i', '-',
           '-c:v', 'libx264', '-preset', 'slow', '-crf', '14',
           '-pix_fmt', 'yuv420p', '-movflags', '+faststart', out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(NF):
        t = i / FPS
        r, g, b, cam, amb = ren.render(t)
        img = to_rgb(r, g, b, t)
        k = clamp((t - T_TITLE) / 1.55)
        if k > 0:
            title.stamp(img, smoothstep(k), int(round(9 * (1 - smoothstep(k)))))
        write_png('amb/%04d.png' % i, GW, GH, amb)
        p.stdin.write(bytes(img))
        if i % 30 == 0:
            print('frame', i, '/', NF, flush=True)
    p.stdin.close()
    p.wait()
    print('done')


if __name__ == '__main__':
    main()
