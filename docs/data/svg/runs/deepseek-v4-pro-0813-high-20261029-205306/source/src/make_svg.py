#!/usr/bin/env python3
"""Generate a 'pale blue dot' Earth SVG carrying the Golden Rule.

build_svg(t) returns the SVG for animation time t in [0,1].
"""
import math
import random

W, H = 1920, 1080
CX, CY = 960, 420
R = 310  # earth radius

random.seed(42)

# ---------- star field (deterministic, with twinkle phase) ----------
_stars = []
for _ in range(700):
    x = random.uniform(0, W)
    y = random.uniform(0, H)
    r = random.uniform(0.4, 1.7)
    o = random.uniform(0.15, 0.95)
    d = math.hypot(x - CX, y - CY)
    if d < R + 45:
        continue
    phase = random.uniform(0, 2 * math.pi)
    speed = random.uniform(0.5, 1.5)
    _stars.append((x, y, r, o, phase, speed))


def stars(t=1.0):
    out = []
    for (x, y, r, o, phase, speed) in _stars:
        tw = 0.72 + 0.28 * math.sin(2 * math.pi * (t * speed + phase))
        op = o * tw
        out.append(
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.2f}" fill="#ffffff" '
            f'opacity="{op:.3f}"/>'
        )
    return "\n".join(out)


# ---------- continents (stylized, orthographic-ish, centered on Atlantic) ----------
continents = [
    # North America
    "M -205 -150 C -175 -185 -120 -195 -85 -180 C -60 -170 -55 -150 -70 -135 "
    "C -95 -120 -120 -125 -140 -110 C -155 -100 -160 -80 -150 -65 "
    "C -140 -50 -120 -55 -105 -60 C -95 -70 -80 -75 -70 -60 "
    "C -60 -45 -70 -30 -90 -25 C -110 -20 -130 -30 -150 -40 "
    "C -170 -50 -195 -60 -210 -80 C -220 -100 -220 -130 -205 -150 Z",
    # Greenland
    "M -120 -200 C -100 -210 -70 -205 -60 -190 C -55 -175 -70 -170 -85 -175 "
    "C -100 -180 -115 -190 -120 -200 Z",
    # South America
    "M -120 40 C -100 20 -80 15 -60 25 C -45 35 -40 55 -50 75 "
    "C -60 95 -70 120 -65 150 C -60 180 -50 210 -45 235 "
    "C -42 250 -50 255 -58 250 C -70 240 -80 220 -85 195 "
    "C -90 170 -100 140 -110 110 C -120 85 -125 60 -120 40 Z",
    # Europe
    "M -10 -120 C 5 -135 25 -130 35 -115 C 45 -100 40 -85 30 -80 "
    "C 20 -75 10 -80 5 -90 C 0 -100 -5 -110 -10 -120 Z",
    # Africa
    "M -30 -60 C -10 -70 10 -65 25 -50 C 40 -35 45 -15 40 5 "
    "C 35 25 30 50 25 80 C 22 100 20 120 15 140 "
    "C 12 155 5 160 -2 155 C -10 145 -15 125 -18 100 "
    "C -22 75 -25 50 -28 20 C -30 -5 -32 -35 -30 -60 Z",
    # Asia
    "M 40 -130 C 70 -150 110 -155 145 -140 C 175 -125 195 -100 200 -70 "
    "C 205 -40 195 -15 175 -5 C 160 5 150 0 145 -15 "
    "C 140 -30 130 -40 115 -45 C 100 -50 85 -45 75 -35 "
    "C 65 -25 60 -10 55 -20 C 50 -35 45 -60 40 -80 "
    "C 35 -100 35 -115 40 -130 Z",
    # India / SE Asia
    "M 120 -20 C 135 -10 140 5 135 20 C 130 35 120 40 112 30 "
    "C 105 20 108 5 115 -5 C 118 -12 120 -18 120 -20 Z",
    # Australia
    "M 150 90 C 170 80 195 85 205 100 C 215 115 210 135 195 145 "
    "C 180 155 160 150 150 135 C 140 120 140 100 150 90 Z",
]


def continent_paths():
    out = []
    for p in continents:
        out.append(
            f'<path d="{p}" fill="#5aa84a" stroke="#3c7a30" stroke-width="1.5" opacity="0.95"/>'
        )
    return "\n".join(out)


def clouds():
    out = []
    for (cx, cy, rx, ry, rot, op) in [
        (-120, -80, 90, 22, -15, 0.5),
        (40, -40, 110, 20, 10, 0.45),
        (-60, 60, 80, 18, 20, 0.4),
        (120, 40, 90, 18, -10, 0.45),
        (0, 120, 100, 20, 5, 0.4),
        (-160, 20, 70, 16, -25, 0.4),
        (80, -110, 80, 18, 15, 0.45),
    ]:
        out.append(
            f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="#ffffff" '
            f'opacity="{op}" transform="rotate({rot} {cx} {cy})"/>'
        )
    return "\n".join(out)


def build_svg(t=1.0):
    # text fade-in over first 25% of the animation
    fade = min(1.0, t / 0.25)
    fade = fade * fade * (3 - 2 * fade)  # smoothstep
    # subtle zoom
    zoom = 1.0 + 0.05 * t
    # atmosphere pulse
    pulse = 1.0 + 0.02 * math.sin(2 * math.pi * t)

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
  <defs>
    <radialGradient id="space" cx="50%" cy="42%" r="75%">
      <stop offset="0%" stop-color="#0a1226"/>
      <stop offset="55%" stop-color="#050a18"/>
      <stop offset="100%" stop-color="#01030a"/>
    </radialGradient>
    <radialGradient id="ocean" cx="38%" cy="35%" r="75%">
      <stop offset="0%" stop-color="#4f9fe0"/>
      <stop offset="45%" stop-color="#1f6fb8"/>
      <stop offset="80%" stop-color="#0b3f7a"/>
      <stop offset="100%" stop-color="#062a52"/>
    </radialGradient>
    <radialGradient id="atmo" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="#3f8fd8" stop-opacity="0"/>
      <stop offset="70%" stop-color="#3f8fd8" stop-opacity="0"/>
      <stop offset="88%" stop-color="#5aa8e8" stop-opacity="0.55"/>
      <stop offset="100%" stop-color="#5aa8e8" stop-opacity="0"/>
    </radialGradient>
    <radialGradient id="glow" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="#4f9fe0" stop-opacity="0.35"/>
      <stop offset="100%" stop-color="#4f9fe0" stop-opacity="0"/>
    </radialGradient>
    <linearGradient id="terminator" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#000000" stop-opacity="0"/>
      <stop offset="52%" stop-color="#000000" stop-opacity="0"/>
      <stop offset="100%" stop-color="#000000" stop-opacity="0.5"/>
    </linearGradient>
    <radialGradient id="vignette" cx="50%" cy="50%" r="72%">
      <stop offset="0%" stop-color="#000000" stop-opacity="0"/>
      <stop offset="100%" stop-color="#000000" stop-opacity="0.55"/>
    </radialGradient>
    <radialGradient id="sun" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="#f6dca6" stop-opacity="0.16"/>
      <stop offset="100%" stop-color="#f6dca6" stop-opacity="0"/>
    </radialGradient>
    <clipPath id="earthclip">
      <circle cx="{CX}" cy="{CY}" r="{R}"/>
    </clipPath>
  </defs>

  <rect width="{W}" height="{H}" fill="url(#space)"/>

  <!-- sun glow (off-screen light source, upper-left) -->
  <circle cx="120" cy="90" r="560" fill="url(#sun)"/>

  {stars(t)}

  <!-- atmosphere glow -->
  <circle cx="{CX}" cy="{CY}" r="{(R+70)*pulse:.1f}" fill="url(#glow)"/>
  <circle cx="{CX}" cy="{CY}" r="{(R+16)*pulse:.1f}" fill="url(#atmo)"/>

  <!-- earth -->
  <g transform="translate({CX},{CY}) scale({zoom}) translate({-CX},{-CY})">
    <g clip-path="url(#earthclip)">
      <circle cx="{CX}" cy="{CY}" r="{R}" fill="url(#ocean)"/>
      <g transform="translate({CX},{CY})">
        {continent_paths()}
        {clouds()}
      </g>
      <!-- terminator shading (night side, lower-right) -->
      <circle cx="{CX}" cy="{CY}" r="{R}" fill="url(#terminator)"/>
      <!-- specular highlight -->
      <ellipse cx="{CX-R*0.45}" cy="{CY-R*0.5}" rx="{R*0.55}" ry="{R*0.4}" fill="#ffffff" opacity="0.10" transform="rotate(-25 {CX-R*0.45} {CY-R*0.5})"/>
    </g>
  </g>

  <!-- vignette -->
  <rect width="{W}" height="{H}" fill="url(#vignette)"/>

  <!-- divider -->
  <g opacity="{fade:.3f}">
    <line x1="{W/2-220}" y1="800" x2="{W/2-14}" y2="800" stroke="#5aa8e8" stroke-width="1" opacity="0.5"/>
    <line x1="{W/2+14}" y1="800" x2="{W/2+220}" y2="800" stroke="#5aa8e8" stroke-width="1" opacity="0.5"/>
    <circle cx="{W/2}" cy="800" r="4" fill="#5aa8e8" opacity="0.8"/>
  </g>

  <!-- text -->
  <g opacity="{fade:.3f}">
    <text x="{W/2}" y="866" text-anchor="middle" font-family="Georgia, 'Times New Roman', serif" font-size="64" fill="#f2f6fb" letter-spacing="1">Treat others as you would like to be treated.</text>
    <text x="{W/2}" y="930" text-anchor="middle" font-family="'Avenir Next', 'Helvetica Neue', Helvetica, sans-serif" font-size="30" font-weight="300" fill="#9fb4cc" letter-spacing="3">THE ONE RULE SHARED BY EVERY FAITH AND CULTURE ON EARTH</text>
    <text x="{W/2}" y="1005" text-anchor="middle" font-family="'PingFang SC','Heiti SC','Hiragino Sans','SF Arabic','DecoType Naskh','Devanagari MT','Avenir Next','Helvetica Neue',sans-serif" font-size="24" fill="#7d93ad" letter-spacing="1">己所不欲，勿施于人&#160;&#160;·&#160;&#160;أحب لأخيك ما تحب لنفسك&#160;&#160;·&#160;&#160;दूसरों के साथ वैसा ही करो जैसा तुम चाहते हो&#160;&#160;·&#160;&#160;Trata a los demás como quieres ser tratado</text>
  </g>
</svg>'''


if __name__ == "__main__":
    import os
    os.makedirs("output", exist_ok=True)
    svg = build_svg(1.0)
    with open("output/earth.svg", "w") as f:
        f.write(svg)
    print("wrote output/earth.svg")
