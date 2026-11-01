# Generate procedural textures for "One Home - Pale Blue Dot"
# Continents rasterized from hand-written coarse lat/lon polygons -> stylized Earth.
import os, math
import numpy as np
import bpy

BASE = '~/dev/art-crit-runs/2026-10-30-024430-3d-model/glm-5.3-prime-high-20261030-024430/work'
TEX = os.path.join(BASE, 'textures')
os.makedirs(TEX, exist_ok=True)

TWO_PI = 2.0 * math.pi

# ---------------------------------------------------------------- helpers
def _noise(shape, res, seed):
    h, w = shape
    gy, gx = res
    rng = np.random.default_rng(seed)
    grid = rng.random((gy, gx)).astype(np.float32)
    ys = (np.arange(h) + 0.5) / h * gy
    xs = (np.arange(w) + 0.5) / w * gx
    yi = np.floor(ys).astype(int); xi = np.floor(xs).astype(int)
    yf = (ys - yi)[:, None]; xf = (xs - xi)[None, :]
    yf = yf * yf * (3 - 2 * yf); xf = xf * xf * (3 - 2 * xf)
    y0 = (yi % gy)[:, None]; y1 = ((yi + 1) % gy)[:, None]
    x0 = (xi % gx)[None, :]; x1 = ((xi + 1) % gx)[None, :]
    g00 = grid[y0, x0]; g01 = grid[y0, x1]
    g10 = grid[y1, x0]; g11 = grid[y1, x1]
    return (g00 * (1 - xf) + g01 * xf) * (1 - yf) + (g10 * (1 - xf) + g11 * xf) * yf

def fbm(shape, res, octaves, seed, gain=0.5, lac=2):
    total = np.zeros(shape, np.float32); amp = 1.0; norm = 0.0
    for o in range(octaves):
        total += amp * _noise(shape, (int(res[0] * lac ** o), int(res[1] * lac ** o)), seed + o * 101)
        norm += amp; amp *= gain
    return total / norm

def blur(a, r=2, passes=2):
    for _ in range(passes):
        shape = a.shape
        h, w = shape[0], shape[1]
        pad = [(r, r), (r, r)] + [(0, 0)] * (a.ndim - 2)
        ap = np.pad(a, pad, mode='wrap')
        out = np.zeros_like(a)
        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                idx0 = slice(r + dy, r + dy + h)
                idx1 = slice(r + dx, r + dx + w)
                out += ap[(idx0, idx1) + (slice(None),) * (a.ndim - 2)]
        a = out / float((2 * r + 1) ** 2)
    return a

def smoothstep(a, lo, hi):
    t = np.clip((a - lo) / (hi - lo), 0.0, 1.0)
    return t * t * (3 - 2 * t)

# ------------------------------------------------------------ land masks
W, H = 1024, 512
lons = (np.arange(W) + 0.5) / W * 360.0 - 180.0
lats = 90.0 - (np.arange(H) + 0.5) / H * 180.0
LON, LAT = np.meshgrid(lons, lats)

def poly(verts):
    m = np.zeros(LON.shape, bool)
    n = len(verts)
    for i in range(n):
        x1, y1 = verts[i]; x2, y2 = verts[(i + 1) % n]
        if y1 == y2: continue
        cond = (y1 > LAT) != (y2 > LAT)
        if not cond.any(): continue
        xin = x1 + (LAT - y1) * (x2 - x1) / (y2 - y1)
        m ^= cond & (LON < xin)
    return m

def ell(cx, cy, rx, ry):
    return (((LON - cx) / rx) ** 2 + ((LAT - cy) / ry) ** 2) <= 1.0

def cap(a, b, r):
    ax, ay = a; bx, by = b
    vx, vy = bx - ax, by - ay
    L2 = vx * vx + vy * vy
    t = np.clip(((LON - ax) * vx + (LAT - ay) * vy) / L2, 0.0, 1.0)
    dx = LON - (ax + t * vx); dy = LAT - (ay + t * vy)
    return (dx * dx + dy * dy) <= r * r

EURASIA = [
    (-9,43),(-9,37),(-1,37),(3,42),(10,44),(16,43),(20,42),(24,38),(28,36),(36,36),(35,33),
    (33,30),(34.5,27.5),(36.5,24),(38.5,20),(40.5,16),(43,12.5),(48,14),(52,16.5),(58.5,20.5),
    (56.3,26),(51,28),(48.5,29.5),(50,29.8),(56,26.8),(59,25.3),(62,25.2),(66,25),(68,23),
    (70,21),(72.8,19),(74.5,15),(76,10),(77.5,8.1),(80.3,13.5),(82,17),(86,20.5),(89,21.6),
    (92,21.5),(94,18),(96,15),(98.5,10),(100.5,5),(103.5,1.4),(103.5,4),(104.5,9),(105,10.5),
    (107,11),(109,13),(109.3,16),(107,19),(108,21),(112,22),(117,23),(119,25),(121.8,31),
    (120.5,34),(122,37.5),(124.5,38.5),(126.3,34.8),(129.8,36),(129.5,38.5),(130.5,42.3),
    (132.5,43),(135,44),(137,47.5),(140,53),(137,55),(142,54),(155,51),(157,54),(160,56),
    (164,60),(170,60),(176,64),(178,66),(177,68),(170,70),(160,70),(150,72),(140,73),(130,72),
    (120,73),(110,74),(105,77),(100,76),(95,75),(90,75),(85,74),(80,73),(75,72),(70,72),
    (68,69),(66,68),(60,69),(55,66),(44,66),(40,64),(37,65),(33,66),(31,70),(28,71),(25,71),
    (20,70),(15,68),(12,65),(9,63),(7,61),(8,58),(8,55),(6,53),(4,52),(0,49),(-2,47),(-2,43),
]

AFRICA = [
    (-5.9,35.8),(-9.5,32),(-13,27),(-16,21),(-17.5,14.7),(-15,11),(-12,8),(-8,5),(-4,5.2),(1,6),
    (3,6.3),(6,4.3),(9,4),(9.5,0),(9.5,-2),(12,-6),(13,-12),(11.8,-17),(11.5,-22),(12,-26),
    (14.5,-26.5),(16.5,-28.5),(18.3,-32),(18.4,-34.3),(20,-34.8),(22,-34),(25.5,-34),(27,-33),
    (28,-32.5),(31,-29.5),(33,-26),(35,-22),(35.5,-18),(37,-15),(39,-10),(40,-5),(40.5,-2),
    (41.5,0),(43,4),(48,7),(51,10),(51.5,11.8),(47.5,11),(44,10.5),(43,11.5),(41.5,12.5),
    (39.5,14),(37.5,17),(35.5,21),(34,25),(33,28),(32.7,31.2),(25,31.8),(20,30.5),(19,30.3),
    (15,32),(11,33.5),(10,34),(10,37),(5,36.8),(2,36),(0,35.8),(-2,35.2),
]

NAM = [
    (-168,65.5),(-166,61),(-162,58),(-158,56.5),(-152,58.5),(-146,60),(-140,59.5),(-136,57.5),
    (-131,53.5),(-127,50.5),(-125,48.5),(-124.5,44),(-122,38),(-121,34.5),(-117,32.8),(-114,29),
    (-112,26),(-110,23.5),(-108,24),(-106,22),(-105,20.5),(-103,18.7),(-100,17.5),(-96,15.5),
    (-93,15),(-90,13.8),(-87,13),(-85,11.5),(-83,9.5),(-80,8.5),(-78,8),(-81.5,9),(-83,10.5),
    (-83.5,12),(-86,13.5),(-87.5,15.8),(-88.5,17.5),(-88,19.5),(-86.5,21.3),(-87,21.5),
    (-90,21.3),(-91.9,18.7),(-94,18.2),(-96,19),(-97.5,22),(-97.5,25),(-96,28),(-94,29.5),
    (-90,29.2),(-84,30),(-83,29),(-81.5,25.5),(-80.1,25.2),(-80,26.8),(-81,30.5),(-79,33),
    (-76,34.5),(-75.5,35.2),(-74,38.5),(-71,41.5),(-70,41.5),(-68,44.3),(-66.9,44.2),
    (-65.5,45.5),(-63,44),(-60.5,46),(-64,49),(-58,50.5),(-61,55),(-64.5,58.5),(-70,60),
    (-77,62.5),(-80,64),(-82,66),(-90,68.5),(-100,68.5),(-115,69),(-128,69.5),(-140,70),
    (-155,71),(-162,68.5),(-166,68.5),
]

SAM = [
    (-78,8.5),(-77,10.5),(-71.5,11.8),(-64,10.5),(-61,9.5),(-60,8),(-54,5.5),(-51,4),(-50,0),
    (-48,-1),(-44,-2.8),(-38,-4),(-34.8,-6.8),(-35,-8),(-37,-11),(-39,-14),(-40.5,-20),
    (-42,-23),(-48,-25.5),(-52,-31),(-56,-34.5),(-58,-36),(-57.5,-38),(-62,-39),(-65,-41),
    (-63,-45),(-67,-46),(-68.5,-50),(-69,-52),(-68.5,-54.5),(-70,-55.5),(-74,-53),(-74.5,-50),
    (-75.5,-47),(-73.5,-44),(-73,-40),(-71.5,-35),(-70.5,-30),(-70.3,-25),(-70.5,-20),
    (-72.5,-17),(-76.3,-13.5),(-78.5,-9),(-81,-6),(-80.5,-3.5),(-80,0),(-77.5,3),
]

GREENLAND = [
    (-45,60),(-52,64),(-55,68),(-58,72),(-60,76),(-50,82),(-30,83),(-20,82),(-22,76),(-20,70),
    (-28,68),(-40,63),
]

AUSTRALIA = [
    (114,-22),(122,-17),(130,-12),(132,-11),(136,-12),(137,-16),(139,-17),(142,-11),(145,-15),
    (147,-19),(150,-23),(153,-27),(150,-35),(146,-39),(140,-38),(136,-35),(131,-32),(124,-33),
    (118,-35),(115,-34),(115,-30),(113,-26),
]

land = np.zeros(LON.shape, bool)
for p in (EURASIA, AFRICA, NAM, SAM, GREENLAND, AUSTRALIA):
    land |= poly(p)

# Antarctica + peninsula
land |= (LAT < -70.0)
land |= cap((-58,-64),(-63,-70),2.0)

# islands
land |= ell(46.8,-19,3.5,7.0)            # Madagascar
land |= ell(-2,54,3.0,4.3)               # Great Britain
land |= ell(-8,53.3,2.0,1.6)             # Ireland
land |= cap((131,31.5),(140.5,35.5),1.6) # Japan
land |= cap((140,37),(145,43.3),1.4)     # Japan north
land |= ell(121,23.7,1.0,1.6)            # Taiwan
land |= ell(109.8,19.2,1.2,1.2)          # Hainan
land |= cap((98,1.5),(106,-5),2.2)       # Sumatra
land |= cap((105,-6.5),(114,-7.8),1.2)   # Java
land |= ell(114,0.5,4.5,3.5)             # Borneo
land |= ell(121,-2,2.5,3.0)              # Sulawesi
land |= cap((132,-2),(148,-9),2.5)       # New Guinea
land |= ell(121.5,16.5,1.5,2.0)          # Luzon
land |= ell(125,7.5,2.0,1.8)             # Mindanao
land |= ell(80.7,7.8,1.3,1.6)            # Sri Lanka
land |= cap((-84,22.3),(-76,20.3),1.1)   # Cuba
land |= ell(-71,18.9,2.0,1.0)            # Hispaniola
land |= ell(-18.5,65,3.0,1.5)            # Iceland
land |= cap((142.5,50),(143,54),1.0)     # Sakhalin
land |= cap((54,70.5),(68,76),0.9)       # Novaya Zemlya
land |= ell(17,78.5,4.0,2.5)             # Svalbard
land |= ell(-72,69.5,8.0,3.0)            # Baffin
land |= ell(-110,71.5,5.0,2.5)           # Victoria Isl
land |= ell(-80,79.5,5.0,3.0)            # Ellesmere
land |= ell(-88,75,3.0,1.5)              # Devon
land |= ell(-55.5,48.5,2.5,1.8)          # Newfoundland
land |= ell(146,-42,2.5,2.0)             # Tasmania
land |= cap((173,-35),(178,-38),1.3)     # NZ north
land |= cap((167,-46),(171,-44),1.3)     # NZ south
land |= cap((-114,31),(-110,23.5),1.2)   # Baja

# lakes / seas to subtract
water = np.zeros(LON.shape, bool)
water |= ell(51,42,2.5,5.0)              # Caspian
water |= ell(34,43,5.0,2.0)              # Black Sea
water |= ell(51.8,27.5,3.5,1.8)          # Persian Gulf
water |= ell(119,38.7,1.5,1.0)           # Bohai
water |= ell(100.5,11,3.0,2.0)           # Gulf of Thailand
water |= ell(-88.5,47.7,3.5,1.2)         # L. Superior
water |= cap((-86.5,45.5),(-86,42),1.2)  # L. Michigan
water |= ell(-82.5,44.8,2.2,1.3)         # L. Huron
water |= ell(-81.5,42.3,2.2,0.7)         # L. Erie
water |= ell(-77.5,43.6,1.7,0.7)         # L. Ontario
water |= cap((104,52),(109,55.5),0.6)    # Baikal
water |= ell(-85,59.5,8.0,6.0)           # Hudson Bay
water |= cap((-112.8,31.8),(-109.5,23.2),1.0)  # Gulf of California
land &= ~water

# smooth coastlines
landf = blur(land.astype(np.float32), r=2, passes=2)
land_s = landf > 0.35

# ------------------------------------------------------------ earth color
e  = fbm((H, W), (6, 12), 5, 7)      # broad variation
e2 = fbm((H, W), (16, 32), 4, 11)    # fine detail
abslat = np.abs(LAT)

snow = land_s & (abslat > 61.0 + 10.0 * (e2 - 0.5))
desert = land_s & ~snow & (
    (((abslat > 12) & (abslat < 32)) & (((LON > -17) & (LON < 78)) | ((LON > -115) & (LON < -95)))) |
    ((LON > 112) & (LON < 154) & (LAT > -38) & (LAT < -11)) |
    ((LON > 14) & (LON < 26) & (LAT > -30) & (LAT < -15)) |
    ((LON > -72) & (LON < -66) & (LAT > -25) & (LAT < -17)) |
    ((LON > 76) & (LON < 90) & (LAT > 18) & (LAT < 28))
)

snow_w = blur(snow.astype(np.float32), 1, 1)
des_w  = blur(desert.astype(np.float32), 1, 1)

# green base tint by latitude
t_trop = np.array([0.09, 0.28, 0.09])
t_temp = np.array([0.17, 0.34, 0.13])
t_bor  = np.array([0.14, 0.23, 0.12])
w_t = np.clip(1.0 - abslat / 10.0, 0, 1)[..., None]
w_b = np.clip((abslat - 45.0) / 15.0, 0, 1)[..., None]
green = t_trop * w_t + t_temp * (1 - w_t) * (1 - w_b) + t_bor * w_b
green = green * (0.75 + 0.5 * e[..., None]) + 0.04 * (e2[..., None] - 0.5)

col_desert = np.array([0.80, 0.68, 0.45]) * (0.88 + 0.28 * e2[..., None])
col_snow   = np.array([0.90, 0.93, 0.97]) * (0.90 + 0.16 * e2[..., None])

landcol = green * (1 - des_w[..., None] - snow_w[..., None]).clip(0, 1) \
        + col_desert * des_w[..., None] + col_snow * snow_w[..., None]
landcol = np.clip(landcol, 0, 1)

# ocean
ocean_deep = np.array([0.012, 0.07, 0.19]) + 0.05 * (e[..., None] - 0.5)
coast = blur(land_s.astype(np.float32), 3, 2)
shallow = np.array([0.05, 0.30, 0.48])
oceancol = ocean_deep * (1 - coast[..., None] * 0.8) + shallow * coast[..., None] * 0.8
# sea ice at poles
ice_f = smoothstep(abslat, 73.0, 79.0) * (0.7 + 0.3 * e2)
icecol = np.array([0.90, 0.94, 0.98]) * (0.85 + 0.2 * e2[..., None])
oceancol = oceancol * (1 - ice_f[..., None]) + icecol * ice_f[..., None]

diffuse = np.where(land_s[..., None], landcol, oceancol).astype(np.float32)

# roughness map
rough = np.where(land_s, 0.85, 0.32).astype(np.float32)
rough = np.where(desert, 0.9, rough)
rough = np.where(snow, 0.55, rough)
rough = np.where(ice_f > 0.5, 0.5, rough)
rough = np.clip(rough + 0.12 * (e2 - 0.5), 0.05, 1.0).astype(np.float32)

# upscale 2x for finer coastlines
def up2(a):
    a2 = np.repeat(np.repeat(a, 2, axis=0), 2, axis=1)
    return blur(a2, 1, 1).astype(np.float32)

diffuse2 = np.clip(up2(diffuse), 0, 1)
rough2 = np.clip(up2(rough), 0, 1)

def save_img(name, arr, path, colorspace='sRGB', gray=False):
    if arr.ndim == 2:
        arr = np.stack([arr] * 3, axis=-1)
    if gray and arr.shape[2] >= 3:
        arr = arr[..., :1]
    h, w = arr.shape[:2]
    arr = arr.astype(np.float32)
    if arr.shape[2] == 1:
        arr = np.repeat(arr, 3, axis=2)
    if arr.shape[2] == 3:
        a = np.ones((h, w, 1), np.float32)
        arr = np.concatenate([arr, a], axis=2)
    img = bpy.data.images.new(name, width=w, height=h, alpha=True, float_buffer=False)
    img.colorspace_settings.name = colorspace
    img.pixels[:] = arr.ravel()
    img.file_format = 'PNG'
    img.filepath_raw = path
    img.save()
    return img

save_img('earth_diffuse', diffuse2, os.path.join(TEX, 'earth_diffuse.png'), 'sRGB')
save_img('earth_rough', rough2, os.path.join(TEX, 'earth_rough.png'), 'Non-Color', gray=True)

# ------------------------------------------------------------ clouds
c = fbm((H, W), (8, 16), 6, 21)
mod = fbm((H, W), (3, 6), 3, 33)
ca = smoothstep(c, 0.53, 0.72) * (0.45 + 0.75 * mod)
clouds = np.ones((H, W, 4), np.float32)
clouds[..., 3] = np.clip(ca, 0, 0.92)
save_img('earth_clouds', clouds, os.path.join(TEX, 'earth_clouds.png'), 'sRGB')

# ------------------------------------------------------------ moon
MH, MW = 512, 256
mlons = (np.arange(MW) + 0.5) / MW * 360.0 - 180.0
mlats = 90.0 - (np.arange(MH) + 0.5) / MH * 180.0
MLON, MLAT = np.meshgrid(mlons, mlats)
g = 0.55 + 0.4 * fbm((MH, MW), (10, 20), 5, 41)
maria = np.zeros((MH, MW), bool)
for cx, cy, rx, ry in [(15,15,28,16),(-20,-2,34,18),(40,-12,22,12),(65,8,20,12),(-65,25,14,10),(0,40,30,10)]:
    maria |= (((MLON - cx) / rx) ** 2 + ((MLAT - cy) / ry) ** 2) <= 1.0
mf = blur(maria.astype(np.float32), 2, 2)
g = g * (1.0 - 0.45 * mf)
rng = np.random.default_rng(99)
n_cr = 420
for _ in range(n_cr):
    cx = rng.uniform(-180, 180); cy = rng.uniform(-90, 90)
    r = rng.uniform(1.5, 9.0)
    if abs(cy) > 88: continue
    d = np.sqrt((MLON - cx) ** 2 + (MLAT - cy) ** 2)
    core = d < r * 0.65
    rim = (d >= r * 0.7) & (d < r)
    g = g * (1 - 0.10 * core) + 0.10 * rim
moon = np.clip(g, 0, 1)[..., None] * np.array([1.0, 0.98, 0.94], np.float32)
moon = moon[..., None][:, :, 0] * 1.0 if False else moon
moon = np.clip(moon, 0, 1)
save_img('moon_diffuse', moon.astype(np.float32), os.path.join(TEX, 'moon_diffuse.png'), 'sRGB')

# ------------------------------------------------------------ starfield
SH, SW = 1024, 2048
theta = (np.arange(SH) + 0.5) / SH * math.pi
phi = (np.arange(SW) + 0.5) / SW * TWO_PI
TH, PH = np.meshgrid(theta, phi, indexing='ij')
sz = np.cos(TH); s_ = np.sin(TH)
sx = s_ * np.cos(PH); sy = s_ * np.sin(PH)
n = np.array([0.35, 0.55, 0.76]); n = n / np.linalg.norm(n)
dot = sx * n[0] + sy * n[1] + sz * n[2]
band = np.exp(-(dot / 0.10) ** 2)
sky = np.zeros((SH, SW, 3), np.float32)
mw_noise = fbm((SH, SW), (6, 12), 5, 55)
sky[..., 0] = band * (0.035 + 0.10 * mw_noise)
sky[..., 1] = band * (0.035 + 0.09 * mw_noise)
sky[..., 2] = band * (0.050 + 0.11 * mw_noise)

rng = np.random.default_rng(7)
def add_star(u1, u2, bright, tint, rad=1.0):
    zz = 2 * u1 - 1
    ph = u2 * TWO_PI
    rr = math.sqrt(max(0.0, 1 - zz * zz))
    xx = rr * math.cos(ph); yy = rr * math.sin(ph)
    # column from phi, row from theta (matching grid above)
    col = int((ph / TWO_PI) * SW) % SW
    row = int((math.acos(max(-1, min(1, zz))) / math.pi) * SH) % SH
    for dy in range(-3, 4):
        for dx in range(-3, 4):
            d2 = dx * dx + dy * dy
            if d2 > 9: continue
            w = math.exp(-d2 / (2 * rad * rad))
            r = (row + dy) % SH; cc = (col + dx) % SW
            for k in range(3):
                sky[r, cc, k] += bright * w * tint[k]

n_stars = 4200
for i in range(n_stars):
    u1, u2 = rng.random(), rng.random()
    inband = abs(dot[rowcol]) if False else None
    bright = 0.15 + 0.85 * rng.random() ** 4
    tint = (1.0, 1.0, 1.0)
    t = rng.random()
    if t < 0.15: tint = (0.72, 0.82, 1.0)
    elif t < 0.25: tint = (1.0, 0.85, 0.68)
    add_star(u1, u2, bright, tint, 0.8)
# dense milky-way stars
n_band = 5200
for i in range(n_band):
    # sample along band: pick random point, accept if in band
    for _try in range(8):
        u1, u2 = rng.random(), rng.random()
        zz = 2 * u1 - 1; ph = u2 * TWO_PI
        rr = math.sqrt(max(0.0, 1 - zz * zz))
        xx = rr * math.cos(ph); yy = rr * math.sin(ph)
        d = xx * n[0] + yy * n[1] + zz * n[2]
        if abs(d) < 0.10:
            break
    bright = 0.1 + 0.5 * rng.random() ** 3
    add_star(u1, u2, bright, (1.0, 0.98, 0.95), 0.7)
# a few hero stars
for i in range(24):
    u1, u2 = rng.random(), rng.random()
    add_star(u1, u2, 2.2 + 1.5 * rng.random(), (1.0, 0.97, 0.92), 1.6)

sky = np.clip(sky, 0, 1).astype(np.float32)
save_img('starfield', sky, os.path.join(TEX, 'starfield.png'), 'sRGB')

result = {'saved': sorted(os.listdir(TEX))}
