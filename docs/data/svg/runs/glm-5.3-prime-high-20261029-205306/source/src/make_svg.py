#!/usr/bin/env python3
"""
Pale Blue Dot — an SVG homage to Carl Sagan's meditation on Earth as
"a mote of dust suspended in a sunbeam", paired with a call to kindness.

Generates a 1600x1000 SVG starfield with a diagonal sunbeam and a tiny
pale blue dot (Earth). Uses only basic SVG features (gradients, shapes,
text — no filters) so it renders consistently everywhere.

Also emits a square-declared "render variant" (same content, square
viewport) that Quick Look letterboxes correctly, letting us rasterize
an aspect-correct PNG on macOS via qlmanage + a center crop.
"""

import math
import random
import sys

random.seed(7)

W, H = 1600, 1000

# ---------------------------------------------------------------- helpers
def circle(cx, cy, r, fill, opacity=1.0):
    return (f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.2f}" '
            f'fill="{fill}" opacity="{opacity:.3f}"/>')

# ---------------------------------------------------------------- background
bg = f'''
  <radialGradient id="bgVignette" cx="42%" cy="36%" r="90%">
    <stop offset="0%"  stop-color="#141a28"/>
    <stop offset="55%" stop-color="#0b0f1a"/>
    <stop offset="100%" stop-color="#05070d"/>
  </radialGradient>
  <rect width="{W}" height="{H}" fill="url(#bgVignette)"/>'''

# ---------------------------------------------------------------- sunbeam
# Beam axis runs from just off the top-right corner toward lower-left.
A = (1660, -60)
B = (430, 1000)
axis = (B[0] - A[0], B[1] - A[1])
alen = math.hypot(*axis)
ux, uy = axis[0] / alen, axis[1] / alen          # unit direction
px, py = -uy, ux                                   # unit perpendicular
halfw = 330                                         # beam half-width

p1 = (A[0] + px * halfw, A[1] + py * halfw)
p2 = (A[0] - px * halfw, A[1] - py * halfw)
p3 = (B[0] - px * halfw, B[1] - py * halfw)
p4 = (B[0] + px * halfw, B[1] + py * halfw)

# a wider, fainter halo around the beam
whalf = halfw * 1.8
q1 = (A[0] + px * whalf, A[1] + py * whalf)
q2 = (A[0] - px * whalf, A[1] - py * whalf)
q3 = (B[0] - px * whalf, B[1] - py * whalf)
q4 = (B[0] + px * whalf, B[1] + py * whalf)

beam = f'''
  <linearGradient id="beamGrad" x1="{0.5 - 0.640 * 0.5:.4f}" y1="{0.5 - 0.768 * 0.5:.4f}"
                   x2="{0.5 + 0.640 * 0.5:.4f}" y2="{0.5 + 0.768 * 0.5:.4f}">
    <stop offset="0%"   stop-color="#f7ecc9" stop-opacity="0"/>
    <stop offset="36%"  stop-color="#f7ecc9" stop-opacity="0.02"/>
    <stop offset="50%"  stop-color="#faf1d4" stop-opacity="0.21"/>
    <stop offset="64%"  stop-color="#f7ecc9" stop-opacity="0.02"/>
    <stop offset="100%" stop-color="#f7ecc9" stop-opacity="0"/>
  </linearGradient>
  <linearGradient id="beamWide" x1="{0.5 - 0.640 * 0.5:.4f}" y1="{0.5 - 0.768 * 0.5:.4f}"
                   x2="{0.5 + 0.640 * 0.5:.4f}" y2="{0.5 + 0.768 * 0.5:.4f}">
    <stop offset="0%"   stop-color="#e9ddc0" stop-opacity="0"/>
    <stop offset="50%"  stop-color="#e9ddc0" stop-opacity="0.07"/>
    <stop offset="100%" stop-color="#e9ddc0" stop-opacity="0"/>
  </linearGradient>
  <polygon points="{q1[0]:.0f},{q1[1]:.0f} {q2[0]:.0f},{q2[1]:.0f}
                   {q3[0]:.0f},{q3[1]:.0f} {q4[0]:.0f},{q4[1]:.0f}"
           fill="url(#beamWide)"/>
  <polygon points="{p1[0]:.0f},{p1[1]:.0f} {p2[0]:.0f},{p2[1]:.0f}
                   {p3[0]:.0f},{p3[1]:.0f} {p4[0]:.0f},{p4[1]:.0f}"
           fill="url(#beamGrad)"/>'''

# ---------------------------------------------------------------- stars
stars = []
for _ in range(1200):
    x = random.uniform(0, W)
    y = random.uniform(0, H)
    r = random.uniform(0.4, 1.4)
    o = random.uniform(0.25, 0.85)
    tint = random.random()
    fill = "#cfe0ff" if tint < 0.18 else ("#ffe9d0" if tint > 0.94 else "#ffffff")
    stars.append(circle(x, y, r, fill, o))

for _ in range(26):
    x = random.uniform(0, W)
    y = random.uniform(0, H)
    r = random.uniform(1.8, 2.8)
    glow_r = r * random.uniform(5, 8)
    stars.append(circle(x, y, glow_r, "#b9cdf2", 0.06))
    stars.append(circle(x, y, r * 2.4, "#b9cdf2", 0.16))
    stars.append(circle(x, y, r, "#ffffff", 0.95))

# ---------------------------------------------------------------- the dot
t = 0.58
DX, DY = A[0] + axis[0] * t, A[1] + axis[1] * t

dot = f'''
  <radialGradient id="dotGrad" cx="38%" cy="34%" r="75%">
    <stop offset="0%"  stop-color="#eaf6ff"/>
    <stop offset="30%" stop-color="#8fb8dd"/>
    <stop offset="70%" stop-color="#3f6f9e"/>
    <stop offset="100%" stop-color="#22456a"/>
  </radialGradient>
  {circle(DX, DY, 58, "#6f9fc8", 0.05)}
  {circle(DX, DY, 34, "#6f9fc8", 0.09)}
  {circle(DX, DY, 18, "#7fadd6", 0.16)}
  {circle(DX, DY, 6.5, "url(#dotGrad)")}'''

# ---------------------------------------------------------------- text
quote_lines = [
    "Look again at that dot.",
    "That's here. That's home. That's us.",
    "Every human being who ever was",
    "lived out their lives on it \u2014",
    "on a mote of dust suspended in a sunbeam.",
]

TX, TY, LH, FS = 112, 668, 47, 32

quote_tspans = "\n".join(
    f'    <tspan x="{TX}" dy="{0 if i == 0 else LH}">{line}</tspan>'
    for i, line in enumerate(quote_lines)
)

text = f'''
  <text x="{TX}" y="{TY}" xml:space="preserve"
        font-family="Georgia, 'Times New Roman', Times, serif"
        font-size="{FS}" font-style="italic" fill="#e9e4d8" letter-spacing="0.5">
{quote_tspans}
  </text>
  <text x="{TX}" y="{TY + 5 * LH + 44}"
        font-family="Georgia, 'Times New Roman', Times, serif"
        font-size="26" fill="#e6c67f" letter-spacing="1">Be kind to one another. Everyone you meet is fighting a hard battle.</text>'''

header = f'''
  <text x="{TX}" y="112"
        font-family="Georgia, 'Times New Roman', Times, serif"
        font-size="23" fill="#e0bd72" letter-spacing="10">PALE BLUE DOT</text>
  <text x="{TX}" y="142"
        font-family="Georgia, 'Times New Roman', Times, serif"
        font-size="15" fill="#77808d" letter-spacing="2">after Carl Sagan, 1994</text>'''

label = f'''
  <text x="{DX:.0f}" y="{DY + 44:.0f}" text-anchor="middle"
        font-family="Georgia, 'Times New Roman', Times, serif"
        font-size="16" font-style="italic" fill="#9fb2c8">you are here</text>'''

# ---------------------------------------------------------------- assemble
body = f'''
  <title>Pale Blue Dot</title>
  <desc>Earth as a mote of dust suspended in a sunbeam, after Carl Sagan.
A starfield with one diagonal shaft of light and a single pale blue dot,
with Sagan's meditation and a call to kindness.</desc>
{bg}
{beam}
  <g>
    {"".join(stars)}
  </g>
{dot}
{label}
{header}
{text}
'''

main_svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
{body}
</svg>
'''

# render variant: square declared size, same viewBox -> Quick Look letterboxes
# the 16:10 content into a square, which we then center-crop after rasterizing.
render_svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{H}" height="{H}" viewBox="0 0 {W} {H}">
{body}
</svg>
'''

with open("pale-blue-dot.svg", "w") as f:
    f.write(main_svg)
with open("render-variant.svg", "w") as f:
    f.write(render_svg)

print(f"wrote pale-blue-dot.svg ({len(main_svg)} bytes), render-variant.svg")
print(f"dot at ({DX:.0f},{DY:.0f})  |  quote baselines {TY}..{TY + 4*LH}, kindness baseline {TY + 5*LH + 44}")
