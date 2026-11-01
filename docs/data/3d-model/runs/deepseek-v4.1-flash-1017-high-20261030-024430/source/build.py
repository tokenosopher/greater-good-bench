"""
PALE BLUE DOT / THE OVERVIEW
A procedural Earth built entirely in Blender.

Concept: the single most perspective-changing object ever seen by human eyes.
A portrait of the only home we have: no borders, one thin atmosphere, one moon.
"""
import bpy
import bmesh
import math
import os
import numpy as np
from mathutils import Vector

ROOT = os.getcwd()
TEX = os.path.join(ROOT, "tex")
OUT = os.path.join(ROOT, "output")
os.makedirs(TEX, exist_ok=True)
os.makedirs(OUT, exist_ok=True)

W, H = 2048, 1024
rng = np.random.default_rng(20261030)

# ----------------------------------------------------------------------------
# helpers
# ----------------------------------------------------------------------------

def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def periodic_up(grid, h, w):
    """bilinear upsample of a coarse field, periodic in x"""
    gh, gw = grid.shape
    xs = np.linspace(0.0, gw, w, endpoint=False)
    x0 = np.floor(xs).astype(np.int32)
    x1 = (x0 + 1) % gw
    fx = (xs - x0).astype(np.float32)
    rows = grid[:, x0] * (1.0 - fx)[None, :] + grid[:, x1] * fx[None, :]
    ys = np.linspace(0.0, gh - 1.0, h)
    y0 = np.floor(ys).astype(np.int32)
    y1 = np.minimum(y0 + 1, gh - 1)
    fy = (ys - y0).astype(np.float32)
    return rows[y0] * (1.0 - fy)[:, None] + rows[y1] * fy[:, None]


def fbm(seed, octaves=6, base_w=6, base_h=3, h=H, w=W, gain=0.5):
    r = np.random.default_rng(seed)
    out = np.zeros((h, w), np.float32)
    amp = 1.0
    norm = 0.0
    for o in range(octaves):
        gw = base_w * (2 ** o)
        gh = max(2, base_h * (2 ** o))
        g = r.normal(size=(gh, gw)).astype(np.float32)
        out += amp * periodic_up(g, h, w)
        norm += amp
        amp *= gain
    out /= norm
    out -= out.min()
    out /= max(out.max(), 1e-6)
    return out


def box_blur(a, rx, ry=None):
    if ry is None:
        ry = rx
    h, w = a.shape
    # horizontal wrap
    pad = np.pad(a, ((0, 0), (rx, rx)), mode="wrap")
    c = np.cumsum(pad, axis=1, dtype=np.float64)
    c = np.concatenate([np.zeros((h, 1)), c], axis=1)
    a = (c[:, 2 * rx + 1:] - c[:, :-(2 * rx + 1)]) / (2 * rx + 1)
    # vertical edge
    pad = np.pad(a, ((ry, ry), (0, 0)), mode="edge")
    c = np.cumsum(pad, axis=0, dtype=np.float64)
    c = np.concatenate([np.zeros((1, w)), c], axis=0)
    a = (c[2 * ry + 1:, :] - c[:-(2 * ry + 1), :]) / (2 * ry + 1)
    return a.astype(np.float32)


def save_image(name, arr, colorspace="sRGB", alpha=False, path=None):
    """arr is (H, W, 3) float or (H, W, 4) if alpha"""
    h, w = arr.shape[:2]
    if arr.shape[2] == 3:
        a = np.concatenate([arr, np.ones((h, w, 1), np.float32)], axis=2)
    else:
        a = arr
    img = bpy.data.images.new(name, width=w, height=h, alpha=True)
    img.colorspace_settings.name = colorspace
    if alpha:
        img.alpha_mode = "STRAIGHT"
    img.pixels.foreach_set(np.ascontiguousarray(a, dtype=np.float32).ravel())
    img.filepath_raw = path
    img.file_format = "PNG"
    img.save()
    return img


# ----------------------------------------------------------------------------
# clear scene
# ----------------------------------------------------------------------------
for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)
for col in list(bpy.data.collections):
    bpy.data.collections.remove(col)
for block in (bpy.data.meshes, bpy.data.materials, bpy.data.images,
              bpy.data.lights, bpy.data.cameras, bpy.data.curves):
    for b in list(block):
        try:
            block.remove(b)
        except Exception:
            pass

scene = bpy.context.scene

# ----------------------------------------------------------------------------
# earth land mask
# ----------------------------------------------------------------------------
lon2d = (np.arange(W, dtype=np.float32) + 0.5)[None, :] / W * 360.0 - 180.0
lat2d = (np.arange(H, dtype=np.float32) + 0.5)[:, None] / H * 180.0 - 90.0
lat_abs = np.abs(lat2d)

POLYS = {}

POLYS["north_america"] = [
    (-168, 65), (-160, 70), (-150, 70), (-140, 70), (-130, 70), (-124, 72),
    (-115, 73), (-105, 72), (-95, 73), (-85, 73), (-80, 72), (-75, 68),
    (-70, 65), (-65, 60), (-60, 55), (-55, 50), (-60, 47), (-67, 45),
    (-70, 42), (-74, 40), (-76, 35), (-81, 31), (-80, 25), (-82, 25),
    (-84, 30), (-89, 29), (-94, 29), (-97, 26), (-98, 22), (-105, 20),
    (-105, 18), (-100, 16), (-95, 15), (-92, 14), (-88, 16), (-85, 13),
    (-83, 8), (-79, 9), (-77, 12), (-82, 15), (-86, 20), (-90, 21),
    (-95, 22), (-97, 25), (-105, 25), (-110, 30), (-114, 32), (-120, 34),
    (-124, 40), (-124, 48), (-130, 54), (-140, 60), (-150, 58), (-158, 56),
    (-165, 60),
]

POLYS["greenland"] = [
    (-45, 60), (-55, 62), (-58, 68), (-55, 75), (-45, 82), (-30, 83),
    (-20, 78), (-22, 72), (-30, 68), (-40, 62),
]

POLYS["south_america"] = [
    (-81, 8), (-77, 8), (-72, 12), (-62, 10), (-52, 5), (-50, 0),
    (-44, -2), (-35, -5), (-38, -12), (-40, -20), (-48, -25), (-53, -34),
    (-57, -38), (-62, -40), (-65, -45), (-68, -50), (-70, -55), (-75, -52),
    (-73, -45), (-73, -38), (-72, -30), (-70, -20), (-75, -15), (-80, -6),
    (-81, 0), (-79, 5),
]

POLYS["africa"] = [
    (-17, 15), (-16, 20), (-10, 26), (0, 30), (10, 33), (20, 32),
    (30, 31), (33, 28), (35, 22), (38, 18), (43, 12), (51, 12),
    (51, 5), (48, 0), (41, -5), (40, -10), (40, -15), (35, -20),
    (32, -26), (28, -33), (20, -35), (18, -32), (15, -25), (12, -18),
    (9, -1), (5, 5), (0, 5), (-8, 4), (-10, 7), (-13, 9),
]

POLYS["eurasia"] = [
    (-9, 37), (-9, 43), (-2, 43), (0, 49), (3, 51), (7, 53), (10, 57),
    (6, 58), (5, 61), (10, 64), (15, 68), (22, 70), (30, 70), (40, 67),
    (50, 68), (60, 69), (70, 72), (80, 73), (90, 76), (100, 77),
    (110, 74), (120, 73), (130, 72), (140, 72), (150, 70), (160, 70),
    (170, 66), (180, 66), (180, 60), (170, 60), (162, 58), (158, 54),
    (155, 50), (150, 45), (140, 45), (135, 48), (130, 42), (125, 38),
    (122, 30), (120, 25), (115, 22), (108, 21), (105, 18), (100, 13),
    (98, 8), (95, 15), (90, 22), (88, 21), (85, 20), (80, 15), (77, 8),
    (73, 15), (70, 20), (67, 25), (62, 25), (58, 23), (55, 20), (52, 18),
    (50, 25), (48, 30), (45, 38), (40, 42), (35, 36), (30, 36), (28, 41),
    (24, 40), (20, 40), (15, 38), (12, 45), (8, 44), (5, 43), (0, 40),
    (-5, 36),
]

POLYS["australia"] = [
    (113, -22), (114, -34), (118, -35), (129, -32), (135, -35), (141, -38),
    (146, -39), (150, -37), (153, -28), (153, -25), (146, -19), (142, -11),
    (137, -12), (130, -11), (125, -14), (122, -18),
]

POLYS["madagascar"] = [(43, -12), (50, -15), (50, -25), (45, -25), (43, -20)]
POLYS["japan"] = [(130, 31), (135, 34), (140, 35), (142, 40), (145, 44),
                  (142, 45), (139, 40), (136, 37), (131, 33)]
POLYS["uk"] = [(-5, 50), (-5, 54), (-3, 58), (0, 58), (-1, 54), (-2, 51)]
POLYS["ireland"] = [(-10, 52), (-6, 52), (-6, 55), (-10, 55)]
POLYS["iceland"] = [(-24, 65), (-14, 66), (-14, 64), (-22, 63)]
POLYS["sri_lanka"] = [(80, 9), (82, 8), (81, 6), (80, 7)]
POLYS["cuba"] = [(-85, 22), (-80, 23), (-74, 20), (-78, 20), (-84, 21)]
POLYS["hispaniola"] = [(-74, 20), (-68, 19), (-69, 17), (-74, 18)]
POLYS["new_guinea"] = [(131, -1), (141, -3), (147, -8), (141, -9), (133, -4)]
POLYS["sumatra"] = [(95, 5), (105, -6), (103, -5), (100, 0)]
POLYS["java"] = [(105, -6), (114, -8), (114, -9), (105, -7)]
POLYS["borneo"] = [(109, 2), (117, 4), (119, -3), (112, -4), (109, -1)]
POLYS["sulawesi"] = [(120, 1), (125, 1), (125, -5), (120, -5)]
POLYS["philippines"] = [(120, 18), (124, 18), (126, 10), (122, 6), (120, 10), (118, 14)]
POLYS["nz_north"] = [(173, -35), (178, -38), (174, -41), (171, -38)]
POLYS["nz_south"] = [(170, -42), (174, -41), (171, -46), (167, -46)]

HOLES = {
    "red_sea": [(32.6, 29.8), (33.7, 29.8), (43.6, 12.4), (42.4, 11.6)],
    "black_sea": [(28, 41), (32, 42), (36, 42), (40, 43), (41, 45), (38, 47),
                  (34, 46), (30, 46), (28, 43)],
    "caspian": [(47, 37), (50, 38), (53, 40), (54, 44), (52, 47), (48, 46), (47, 42)],
    "persian_gulf": [(48, 30), (51, 30), (57, 25), (56, 23), (52, 26), (49, 29)],
}

land = np.zeros((H, W), np.float32)


def fill_poly(poly, value):
    n = len(poly)
    for j in range(H):
        lat = -90.0 + (j + 0.5) / H * 180.0
        xs = []
        for k in range(n):
            x1, y1 = poly[k]
            x2, y2 = poly[(k + 1) % n]
            if (y1 > lat) != (y2 > lat):
                xs.append(x1 + (lat - y1) * (x2 - x1) / (y2 - y1))
        if not xs:
            continue
        xs.sort()
        for a, b in zip(xs[0::2], xs[1::2]):
            i0 = int((a + 180.0) / 360.0 * W)
            i1 = int((b + 180.0) / 360.0 * W)
            i0 = max(0, min(W, i0))
            i1 = max(0, min(W, i1))
            if i1 > i0:
                land[j, i0:i1] = value


for name, poly in POLYS.items():
    fill_poly(poly, 1.0)

# Antarctica: a wavy cap
ant_lat = -66.5 + 3.5 * np.sin(np.radians(lon2d) * 2.0 + 0.8) + 2.0 * np.cos(np.radians(lon2d) * 5.0)
land[lat2d < ant_lat] = 1.0

for name, poly in HOLES.items():
    fill_poly(poly, 0.0)

# close the dateline seam in the mask
land[:, -3:] = land[:, :3]

land = box_blur(land, 1)
land = smoothstep(0.44, 0.56, land)

# ----------------------------------------------------------------------------
# earth colour / clouds / normal / roughness
# ----------------------------------------------------------------------------
n1 = fbm(101, 6, 4, 2)          # continental / climate
n2 = fbm(102, 6, 8, 4)          # medium
n3 = fbm(103, 5, 24, 12)        # fine
n4 = fbm(104, 4, 3, 2)          # very large

deep = np.array([0.008, 0.040, 0.130], np.float32)
mid = np.array([0.012, 0.115, 0.255], np.float32)
shallow = np.array([0.030, 0.245, 0.345], np.float32)
trench = np.array([0.003, 0.012, 0.055], np.float32)

depth = 0.55 * n1 + 0.45 * n2
ocean = trench[None, None, :] * (1 - depth[..., None]) + mid[None, None, :] * depth[..., None]
ocean = ocean * (1 - 0.45 * smoothstep(0.0, 1.0, n3)[..., None]) + deep[None, None, :] * 0.45 * n3[..., None]

coast = np.clip(4.0 * land * (1.0 - land), 0.0, 1.0)
coast_broad = np.clip(4.0 * box_blur(land, 5) * (1.0 - box_blur(land, 5)), 0.0, 1.0)
shelf = np.clip(0.42 * coast + 0.42 * coast_broad * (1.0 - land), 0.0, 0.82)
ocean = ocean * (1 - shelf[..., None]) + shallow[None, None, :] * shelf[..., None] * (0.45 + 0.55 * n2[..., None])

green = np.array([0.065, 0.185, 0.052], np.float32)
lush = np.array([0.115, 0.300, 0.075], np.float32)
olive = np.array([0.220, 0.255, 0.100], np.float32)
desert = np.array([0.58, 0.455, 0.255], np.float32)
rock = np.array([0.30, 0.255, 0.20], np.float32)
snow = np.array([0.93, 0.95, 0.985], np.float32)

t = smoothstep(0.25, 0.8, 0.55 * n2 + 0.45 * n1)
veg = green[None, None, :] * (1 - t[..., None]) + lush[None, None, :] * t[..., None]
veg = veg * (0.7 + 0.55 * n3[..., None])
veg = veg * (1 - 0.35 * smoothstep(0.4, 0.9, n4)[..., None]) + olive[None, None, :] * 0.35 * smoothstep(0.4, 0.9, n4)[..., None]

des = np.exp(-((lat_abs - 24.0) / 13.0) ** 2) * (0.35 + 0.85 * n1)
des *= 1.0 - 0.85 * np.exp(-(lat2d / 10.0) ** 2)
des = np.clip(des * 0.92, 0, 1)
landcol = veg * (1 - des[..., None]) + desert[None, None, :] * des[..., None]

ridge = 1.0 - np.abs(2.0 * n2 - 1.0)
mount = smoothstep(0.62, 0.92, ridge) * smoothstep(0.15, 0.75, n1)
landcol = landcol * (1 - 0.75 * mount[..., None]) + rock[None, None, :] * 0.75 * mount[..., None]
landcol *= (0.74 + 0.52 * n3[..., None])

ice_sea = smoothstep(68.0, 80.0, lat_abs + 10.0 * (n1 - 0.5))
ice_ant = smoothstep(55.0, 66.0, -lat2d + 8.0 * (n1 - 0.5))
ice_land = smoothstep(60.0, 71.0, lat_abs + 10.0 * (n1 - 0.5))
ice = np.clip(np.maximum(np.maximum(ice_sea, ice_ant), ice_land * land), 0, 1)
snowy = np.clip(ice + mount * 0.55 * smoothstep(45.0, 60.0, lat_abs), 0, 1)

col = ocean * (1 - land[..., None]) + landcol * land[..., None]
col = col * (1 - snowy[..., None]) + snow[None, None, :] * snowy[..., None]

# a touch of blue in the polar oceans, a touch of life glow in the tropics
col = np.clip(col, 0, 1)
base_img = save_image("earth_basecolor", col, "sRGB", path=os.path.join(TEX, "earth_basecolor.png"))

# ---- normal map from a height field ----
elev = land * (0.55 + 0.45 * n2) + 0.22 * mount * land + 0.015 * n3
elev = box_blur(elev, 1)
hx = (np.roll(elev, 1, axis=1) - np.roll(elev, -1, axis=1)) * 0.5
hy = (np.roll(elev, 1, axis=0) - np.roll(elev, -1, axis=0)) * 0.5
strength = 42.0
nx = -hx * strength
ny = -hy * strength
nz = np.ones_like(nx)
ln = np.sqrt(nx * nx + ny * ny + nz * nz)
nrm = np.stack([nx / ln, ny / ln, nz / ln], axis=2) * 0.5 + 0.5
nrm = np.clip(nrm, 0, 1)
save_image("earth_normal", nrm, "Non-Color", path=os.path.join(TEX, "earth_normal.png"))

# ---- roughness: smooth ocean, rough land, glossy ice ----
rough = np.where(land > 0.5, 0.66, 0.28).astype(np.float32)
rough = np.where(snowy > 0.5, 0.40, rough)
rough = box_blur(rough, 1)
save_image("earth_rough", np.repeat(rough[..., None], 3, axis=2), "Non-Color",
           path=os.path.join(TEX, "earth_roughness.png"))

# ---- clouds ----
c1 = fbm(201, 7, 5, 3)
c2 = fbm(202, 6, 14, 7)
c3 = fbm(203, 5, 40, 20)
cl = 0.55 * c1 + 0.30 * c2 + 0.15 * c3
# stretch the clouds a little along the trades
cl = box_blur(cl, 3, 1)
band = 0.72 + 0.28 * np.abs(np.sin(np.radians(lat2d) * 3.0 + 0.4))
alpha = smoothstep(0.565, 0.735, cl * (0.85 + 0.30 * band))
alpha *= 0.78
alpha *= 0.72 + 0.28 * smoothstep(0.25, 0.80, c3)
alpha = np.clip(alpha + 0.022 * smoothstep(0.50, 0.90, c2), 0, 0.85)
cloud_rgba = np.ones((H, W, 4), np.float32)
cloud_rgba[..., 3] = alpha
save_image("earth_clouds", cloud_rgba, "sRGB", alpha=True,
           path=os.path.join(TEX, "earth_clouds.png"))

# ----------------------------------------------------------------------------
# moon texture
# ----------------------------------------------------------------------------
MW, MH = 1024, 512
mw_lon = (np.arange(MW, dtype=np.float32) + 0.5)[None, :] / MW * 360.0 - 180.0
mw_lat = (np.arange(MH, dtype=np.float32) + 0.5)[:, None] / MH * 180.0 - 90.0
mw_abs = np.abs(mw_lat)
mn = fbm(301, 6, 6, 3, h=MH, w=MW)
mn2 = fbm(302, 5, 20, 10, h=MH, w=MW)
moon_v = 0.44 + 0.10 * (mn - 0.5) + 0.05 * (mn2 - 0.5)

# dark maria
for (cx, cy, r, d) in [(230, 330, 110, 0.16), (330, 380, 80, 0.14), (120, 300, 60, 0.10),
                       (420, 300, 55, 0.10), (700, 350, 90, 0.13), (600, 280, 45, 0.08)]:
    xx = (np.arange(MW)[None, :] - cx) / r
    yy = (np.arange(MH)[:, None] - cy) / r
    rr = np.sqrt(xx * xx + yy * yy)
    fall = np.exp(-(rr ** 4) * 2.0)
    moon_v -= d * fall * (0.6 + 0.4 * mn2)

# craters
cr = np.random.default_rng(777)
for i in range(90):
    cx = cr.uniform(0, MW)
    cy = cr.uniform(0, MH)
    r = cr.uniform(3, 26) * (1.0 + 2.0 * cr.random() ** 3)
    x1 = int(max(0, cx - 2 * r)); x2 = int(min(MW, cx + 2 * r))
    y1 = int(max(0, cy - 2 * r)); y2 = int(min(MH, cy + 2 * r))
    if x2 <= x1 or y2 <= y1:
        continue
    xx = (np.arange(x1, x2)[None, :] - cx) / r
    yy = (np.arange(y1, y2)[:, None] - cy) / r
    rr = np.sqrt(xx * xx + yy * yy)
    floor = -0.10 * np.exp(-(rr ** 2) * 2.2)
    rim = 0.11 * np.exp(-((rr - 0.92) ** 2) / 0.035)
    moon_v[y1:y2, x1:x2] += (floor + rim) * (0.7 + 0.5 * cr.random())
moon_v = np.clip(moon_v, 0.03, 0.95)
moon_col = np.stack([moon_v * 1.00, moon_v * 0.985, moon_v * 0.955], axis=2)
save_image("moon_basecolor", moon_col, "sRGB", path=os.path.join(TEX, "moon_basecolor.png"))

# ----------------------------------------------------------------------------
# starfield environment (render only)
# ----------------------------------------------------------------------------
SW, SH = 4096, 2048
stars = np.zeros((SH, SW, 3), np.float32)
slon = (np.arange(SW, dtype=np.float32) + 0.5)[None, :] / SW * 360.0 - 180.0
slat = (np.arange(SH, dtype=np.float32) + 0.5)[:, None] / SH * 180.0 - 90.0
band = np.exp(-((slat - 20.0 * np.sin(np.radians(slon) * 1.3 + 0.6)) / 13.0) ** 2)
milky = band * (0.45 + 0.55 * fbm(401, 6, 8, 4, h=SH, w=SW))
stars += milky[..., None] * np.array([0.030, 0.036, 0.052], np.float32)
# faint dust
dust = fbm(402, 5, 18, 9, h=SH, w=SW)
stars += (dust[..., None] ** 3) * band[..., None] * np.array([0.04, 0.035, 0.03], np.float32)

srng = np.random.default_rng(9090)
nstars = 24000
sx = srng.integers(0, SW, nstars)
sy = srng.integers(0, SH, nstars)
bright = (srng.random(nstars) ** 3.2) * 1.4 + 0.05
warm = srng.random(nstars)
for i in range(nstars):
    x = int(sx[i]); y = int(sy[i])
    b = bright[i]
    if warm[i] < 0.18:
        c = np.array([1.0, 0.82, 0.62], np.float32)
    elif warm[i] > 0.88:
        c = np.array([0.65, 0.80, 1.0], np.float32)
    else:
        c = np.array([1.0, 0.98, 0.94], np.float32)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            w = 1.0 if (dx == 0 and dy == 0) else (0.42 if abs(dx) + abs(dy) == 1 else 0.18)
            yy = (y + dy) % SH
            xx = (x + dx) % SW
            stars[yy, xx] = np.maximum(stars[yy, xx], c * b * w)
save_image("stars", np.clip(stars, 0, 1), "sRGB", path=os.path.join(TEX, "stars.png"))

# reload from disk so the exporter and renderer both use file-backed images
def load_img(fn, name, cs="sRGB"):
    im = bpy.data.images.load(os.path.join(TEX, fn))
    im.name = name
    im.colorspace_settings.name = cs
    return im

img_base = load_img("earth_basecolor.png", "EarthBase")
img_norm = load_img("earth_normal.png", "EarthNormal", "Non-Color")
img_rough = load_img("earth_roughness.png", "EarthRough", "Non-Color")
img_cloud = load_img("earth_clouds.png", "EarthClouds")
img_moon = load_img("moon_basecolor.png", "MoonBase")
img_stars = load_img("stars.png", "Stars")

# ----------------------------------------------------------------------------
# geometry
# ----------------------------------------------------------------------------

def uv_sphere(name, radius, segments, rings, img_uv=None):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings, radius=radius,
                                         location=(0, 0, 0))
    ob = bpy.context.object
    ob.name = name
    me = ob.data
    me.name = name
    me.shade_smooth()
    # explicit equirectangular UVs with seam correction
    uvl = me.uv_layers.new(name="UVMap")
    for poly in me.polygons:
        idx = list(poly.loop_indices)
        us = []
        for li in idx:
            v = me.vertices[me.loops[li].vertex_index].co
            u = math.atan2(v.y, v.x) / (2 * math.pi) + 0.5
            w = math.asin(max(-1.0, min(1.0, v.z / radius))) / math.pi + 0.5
            uvl.data[li].uv = (u, w)
            us.append(u)
        if max(us) - min(us) > 0.5:
            for li in idx:
                uv = uvl.data[li].uv
                if uv.x < 0.5:
                    uv.x += 1.0
    return ob


earth = uv_sphere("Earth", 1.0, 256, 128)
clouds = uv_sphere("Clouds", 1.008, 192, 96)
atmo = uv_sphere("Atmosphere", 1.045, 128, 64)
moon = uv_sphere("Moon", 0.22, 96, 48)
moon.location = (-2.20, 1.00, 1.00)

# earth / cloud rotation: Africa/Europe toward camera, 23.4 degree axial tilt
for ob, zrot in ((earth, -105.0), (clouds, -101.0), (atmo, -105.0)):
    ob.rotation_euler = (0.0, math.radians(-23.4), math.radians(zrot))
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
    ob.select_set(False)

# ----------------------------------------------------------------------------
# materials
# ----------------------------------------------------------------------------

def new_mat(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    out.location = (600, 0)
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (250, 0)
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return m, nt, bsdf


# Earth
mearth, nt, bsdf = new_mat("Earth")
tex = nt.nodes.new("ShaderNodeTexImage")
tex.image = img_base
tex.location = (-500, 200)
nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
tex.interpolation = "Linear"
tex.extension = "REPEAT"

nmap = nt.nodes.new("ShaderNodeNormalMap")
nmap.location = (-150, -180)
nmap.inputs["Strength"].default_value = 0.85
texn = nt.nodes.new("ShaderNodeTexImage")
texn.image = img_norm
texn.location = (-450, -180)
texn.interpolation = "Linear"
texn.extension = "REPEAT"
nt.links.new(texn.outputs["Color"], nmap.inputs["Color"])
nt.links.new(nmap.outputs["Normal"], bsdf.inputs["Normal"])

texr = nt.nodes.new("ShaderNodeTexImage")
texr.image = img_rough
texr.location = (-500, -450)
texr.interpolation = "Linear"
texr.extension = "REPEAT"
nt.links.new(texr.outputs["Color"], bsdf.inputs["Roughness"])
bsdf.inputs["Metallic"].default_value = 0.0
bsdf.inputs["IOR"].default_value = 1.33
try:
    bsdf.inputs["Coat Weight"].default_value = 0.08
except Exception:
    pass
earth.data.materials.append(mearth)

# Clouds
mcl, nt, bsdf = new_mat("Clouds")
t = nt.nodes.new("ShaderNodeTexImage")
t.image = img_cloud
t.location = (-500, 100)
t.interpolation = "Linear"
t.extension = "REPEAT"
nt.links.new(t.outputs["Color"], bsdf.inputs["Base Color"])
nt.links.new(t.outputs["Alpha"], bsdf.inputs["Alpha"])
bsdf.inputs["Roughness"].default_value = 0.9
bsdf.inputs["Metallic"].default_value = 0.0
try:
    bsdf.inputs["Emission Strength"].default_value = 0.02
    bsdf.inputs["Emission Color"].default_value = (1, 1, 1, 1)
except Exception:
    pass
mcl.surface_render_method = "DITHERED" if hasattr(mcl, "surface_render_method") else None
mcl.use_transparent_shadow = True
clouds.data.materials.append(mcl)
clouds.visible_shadow = False

# Atmosphere (exported: simple translucent shell)
matm, nt, bsdf = new_mat("Atmosphere")
bsdf.inputs["Base Color"].default_value = (0.20, 0.50, 1.0, 1)
bsdf.inputs["Roughness"].default_value = 0.5
bsdf.inputs["Alpha"].default_value = 0.055
bsdf.inputs["Emission Color"].default_value = (0.10, 0.35, 0.9, 1)
bsdf.inputs["Emission Strength"].default_value = 0.12
try:
    matm.surface_render_method = "BLENDED"
except Exception:
    try:
        matm.blend_method = "BLEND"
    except Exception:
        pass
matm.use_transparent_shadow = True
atmo.data.materials.append(matm)
atmo.visible_shadow = False

# Moon
mmoon, nt, bsdf = new_mat("Moon")
t = nt.nodes.new("ShaderNodeTexImage")
t.image = img_moon
t.location = (-500, 100)
nt.links.new(t.outputs["Color"], bsdf.inputs["Base Color"])
bsdf.inputs["Roughness"].default_value = 0.92
bsdf.inputs["Metallic"].default_value = 0.0
moon.data.materials.append(mmoon)

# Render-only atmosphere rim
rim = uv_sphere("AtmosphereGlow", 1.028, 128, 64)
rim.rotation_euler = (0.0, math.radians(-23.4), math.radians(-105.0))
bpy.context.view_layer.objects.active = rim
rim.select_set(True)
bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
rim.select_set(False)

mrim = bpy.data.materials.new("AtmoGlow")
mrim.use_nodes = True
nt = mrim.node_tree
for n in list(nt.nodes):
    nt.nodes.remove(n)
out = nt.nodes.new("ShaderNodeOutputMaterial")
out.location = (800, 0)
lw = nt.nodes.new("ShaderNodeLayerWeight")
lw.location = (-600, 0)
lw.inputs["Blend"].default_value = 0.5
ramp = nt.nodes.new("ShaderNodeValToRGB")
ramp.location = (-380, 0)
ramp.color_ramp.elements[0].position = 0.83
ramp.color_ramp.elements[0].color = (0, 0, 0, 1)
ramp.color_ramp.elements[1].position = 1.0
ramp.color_ramp.elements[1].color = (1, 1, 1, 1)
mid = ramp.color_ramp.elements.new(0.92)
mid.color = (0.30, 0.52, 1.0, 1)
nt.links.new(lw.outputs["Fresnel"], ramp.inputs["Fac"])
emis = nt.nodes.new("ShaderNodeEmission")
emis.location = (0, 100)
emis.inputs["Color"].default_value = (0.05, 0.25, 0.95, 1)
emis.inputs["Strength"].default_value = 0.65
trans = nt.nodes.new("ShaderNodeBsdfTransparent")
trans.location = (0, -160)
mix = nt.nodes.new("ShaderNodeMixShader")
mix.location = (300, 0)
nt.links.new(ramp.outputs["Color"], mix.inputs["Fac"])
nt.links.new(trans.outputs["BSDF"], mix.inputs[1])
nt.links.new(emis.outputs["Emission"], mix.inputs[2])
nt.links.new(mix.outputs["Shader"], out.inputs["Surface"])
rim.data.materials.append(mrim)
rim.visible_shadow = False

# ----------------------------------------------------------------------------
# lights, camera, world
# ----------------------------------------------------------------------------
sun_data = bpy.data.lights.new("Sun", "SUN")
sun_data.energy = 4.4
sun_data.color = (1.0, 0.96, 0.90)
sun_data.angle = math.radians(0.6)
sun = bpy.data.objects.new("Sun", sun_data)
scene.collection.objects.link(sun)
sun.location = (-4.4, -2.2, 3.2)
d = Vector((0, 0, 0)) - sun.location
sun.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()

fill_data = bpy.data.lights.new("Fill", "AREA")
fill_data.energy = 650.0
fill_data.color = (0.32, 0.55, 1.0)
fill_data.shape = "DISK"
fill_data.size = 7.0
fill = bpy.data.objects.new("Fill", fill_data)
scene.collection.objects.link(fill)
fill.location = (3.0, 3.5, 0.8)
d = Vector((0, 0, 0)) - fill.location
fill.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()

rim_fill_data = bpy.data.lights.new("RimFill", "AREA")
rim_fill_data.energy = 180.0
rim_fill_data.color = (1.0, 0.55, 0.30)
rim_fill_data.size = 2.0
rf = bpy.data.objects.new("RimFill", rim_fill_data)
scene.collection.objects.link(rf)
rf.location = (-4.5, 2.0, -1.5)
d = Vector((0, 0, 0)) - rf.location
rf.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()

# target
target = bpy.data.objects.new("Target", None)
scene.collection.objects.link(target)
target.location = (0, 0, 0.02)

cam_data = bpy.data.cameras.new("HeroCam")
cam_data.lens = 55
cam_data.sensor_width = 36
cam_data.clip_start = 0.05
cam_data.clip_end = 2000
cam = bpy.data.objects.new("HeroCam", cam_data)
scene.collection.objects.link(cam)
cam.location = (0.55, -5.55, 1.25)
tc = cam.constraints.new("TRACK_TO")
tc.target = target
tc.track_axis = "TRACK_NEGATIVE_Z"
tc.up_axis = "UP_Y"
scene.camera = cam

# world
world = bpy.data.worlds.new("Space")
world.use_nodes = True
wnt = world.node_tree
for n in list(wnt.nodes):
    wnt.nodes.remove(n)
wout = wnt.nodes.new("ShaderNodeOutputWorld")
wout.location = (400, 0)
wbg = wnt.nodes.new("ShaderNodeBackground")
wbg.location = (150, 0)
wbg.inputs["Strength"].default_value = 0.55
wenv = wnt.nodes.new("ShaderNodeTexEnvironment")
wenv.location = (-300, 0)
wenv.image = img_stars
wnt.links.new(wenv.outputs["Color"], wbg.inputs["Color"])
wnt.links.new(wbg.outputs["Background"], wout.inputs["Surface"])
scene.world = world

# ----------------------------------------------------------------------------
# render settings
# ----------------------------------------------------------------------------
scene.render.engine = "CYCLES"
scene.cycles.device = "GPU"
scene.cycles.samples = 96
scene.cycles.use_denoising = True
scene.cycles.use_adaptive_sampling = True
scene.cycles.adaptive_threshold = 0.02
scene.cycles.max_bounces = 6
scene.cycles.transparent_max_bounces = 8
scene.render.resolution_x = 1600
scene.render.resolution_y = 1200
scene.render.resolution_percentage = 100
scene.render.film_transparent = False
scene.render.image_settings.file_format = "JPEG"
scene.render.image_settings.quality = 92
scene.render.filepath = os.path.join(OUT, "the_overview.jpg")
scene.view_settings.view_transform = "AgX"
for look in ("AgX - Punchy", "AgX - Medium High Contrast", "AgX - Base Contrast"):
    try:
        scene.view_settings.look = look
        break
    except Exception:
        continue
scene.view_settings.exposure = 0.35

# compositor: soft bloom (Blender 5 node-group compositor)
for g in list(bpy.data.node_groups):
    if g.bl_idname == "CompositorNodeTree":
        bpy.data.node_groups.remove(g)
cnt = bpy.data.node_groups.new("Compositing", "CompositorNodeTree")
scene.compositing_node_group = cnt
cnt.interface.new_socket(name="Image", in_out="OUTPUT", socket_type="NodeSocketColor")
rl = cnt.nodes.new("CompositorNodeRLayers")
rl.location = (-400, 0)
glare = cnt.nodes.new("CompositorNodeGlare")
glare.location = (-100, 0)
try:
    glare.inputs["Type"].default_value = "Fog Glow"
    glare.inputs["Quality"].default_value = "High"
    glare.inputs["Threshold"].default_value = 1.15
    glare.inputs["Size"].default_value = 0.55
    glare.inputs["Strength"].default_value = 0.35
except Exception as e:
    print("glare", e)
comp = cnt.nodes.new("NodeGroupOutput")
comp.location = (300, 0)
cnt.links.new(rl.outputs["Image"], glare.inputs["Image"])
cnt.links.new(glare.outputs["Image"], comp.inputs["Image"])

# export selection
for ob in bpy.data.objects:
    ob.select_set(False)
for ob in (earth, clouds, atmo, moon):
    ob.select_set(True)
bpy.context.view_layer.objects.active = earth

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, "pale_blue_dot.blend"))
print("BUILD OK")
print("objects:", [o.name for o in scene.objects])
print("looks:", [l.name for l in bpy.types.ColorManagedViewSettings.bl_rna.properties['look'].enum_items] if False else "n/a")
