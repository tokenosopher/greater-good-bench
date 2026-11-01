# Regenerate starfield with larger, brighter stars (visible at render res)
import os, math
import numpy as np
import bpy

BASE = '~/dev/art-crit-runs/2026-10-30-024430-3d-model/glm-5.3-prime-high-20261030-024430/work'
TWO_PI = 2.0 * math.pi
SH, SW = 1024, 2048

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
    return (grid[y0, x0] * (1 - xf) + grid[y0, x1] * xf) * (1 - yf) + \
           (grid[y1, x0] * (1 - xf) + grid[y1, x1] * xf) * yf

def fbm(shape, res, octaves, seed):
    total = np.zeros(shape, np.float32); amp = 1.0; norm = 0.0
    for o in range(octaves):
        total += amp * _noise(shape, (int(res[0] * 2 ** o), int(res[1] * 2 ** o)), seed + o * 101)
        norm += amp; amp *= 0.5
    return total / norm

theta = (np.arange(SH) + 0.5) / SH * math.pi
phi = (np.arange(SW) + 0.5) / SW * TWO_PI
TH, PH = np.meshgrid(theta, phi, indexing='ij')
sz = np.cos(TH); s_ = np.sin(TH)
sx = s_ * np.cos(PH); sy = s_ * np.sin(PH)
n = np.array([0.35, 0.55, 0.76]); n = n / np.linalg.norm(n)
dot = sx * n[0] + sy * n[1] + sz * n[2]
band = np.exp(-(dot / 0.10) ** 2)
sky = np.zeros((SH, SW, 3), np.float32)
mw = fbm((SH, SW), (6, 12), 5, 55)
sky[..., 0] = band * (0.05 + 0.13 * mw)
sky[..., 1] = band * (0.05 + 0.12 * mw)
sky[..., 2] = band * (0.07 + 0.14 * mw)

rng = np.random.default_rng(7)

def add_star(u1, u2, bright, tint, rad):
    zz = 2 * u1 - 1
    ph = u2 * TWO_PI
    rr = math.sqrt(max(0.0, 1 - zz * zz))
    col = int((ph / TWO_PI) * SW) % SW
    row = int((math.acos(max(-1, min(1, zz))) / math.pi) * SH) % SH
    R = int(math.ceil(rad * 3))
    for dy in range(-R, R + 1):
        for dx in range(-R, R + 1):
            d2 = dx * dx + dy * dy
            if d2 > R * R: continue
            w = math.exp(-d2 / (2.0 * rad * rad))
            r = (row + dy) % SH; cc = (col + dx) % SW
            for k in range(3):
                sky[r, cc, k] += bright * w * tint[k]

for i in range(3800):
    add_star(rng.random(), rng.random(), 0.25 + 0.9 * rng.random() ** 4,
             (1, 1, 1) if rng.random() > 0.2 else (0.74, 0.83, 1.0), 1.3)
# dense band stars
for i in range(6000):
    u1 = u2 = None
    for _try in range(10):
        u1, u2 = rng.random(), rng.random()
        zz = 2 * u1 - 1
        rr = math.sqrt(max(0.0, 1 - zz * zz))
        d = rr * math.cos(u2 * TWO_PI) * n[0] + rr * math.sin(u2 * TWO_PI) * n[1] + zz * n[2]
        if abs(d) < 0.11:
            break
    add_star(u1, u2, 0.15 + 0.6 * rng.random() ** 3, (1.0, 0.98, 0.95), 1.1)
# hero stars with halo
for i in range(26):
    add_star(rng.random(), rng.random(), 2.0 + 1.6 * rng.random(), (1.0, 0.97, 0.92), 2.6)

sky = np.clip(sky, 0, 1).astype(np.float32)
img = bpy.data.images.get('starfield')
if img:
    bpy.data.images.remove(img)
img = bpy.data.images.new('starfield', width=SW, height=SH, alpha=True, float_buffer=False)
img.colorspace_settings.name = 'sRGB'
img.pixels[:] = np.concatenate([sky, np.ones((SH, SW, 1), np.float32)], axis=2).ravel()
img.file_format = 'PNG'
img.filepath_raw = os.path.join(BASE, 'textures', 'starfield.png')
img.save()
result = {'saved': True}
