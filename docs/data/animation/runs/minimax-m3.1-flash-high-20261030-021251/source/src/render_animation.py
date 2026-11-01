#!/usr/bin/env python3
"""Render a frame-by-frame vector animation to PNG, then encode it as an MP4."""
from __future__ import annotations

import math
import os
import random
import subprocess
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "build"
FRAMES = BUILD / "frames"
OUT = ROOT / "output"
W, H = 960, 540
FPS = 30
DURATION = 10.0
N = int(FPS * DURATION)

random.seed(12)
OUT.mkdir(exist_ok=True)
if BUILD.exists():
    shutil.rmtree(BUILD)
FRAMES.mkdir(parents=True)


def clamp(x, lo=0.0, hi=1.0):
    return max(lo, min(hi, x))


def ease(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


def smooth(a, b, t):
    return ease((t - a) / (b - a))


def alpha(t, a, b, fade=0.45):
    if t < a or t > b:
        return 0.0
    return smooth(a, a + fade, t) * (1 - smooth(b - fade, b, t))


def mix(c1, c2, t):
    t = clamp(t)
    return tuple(round(a + (b - a) * t) for a, b in zip(c1, c2))


def rgba(c, a=1.0):
    return f"rgba({c[0]},{c[1]},{c[2]},{a:.3f})"


# Seven stylised neighbours arranged along a gentle arc.
PEOPLE = [
    (112, 351, 0.92, "#E9A678", "#F06D5E"),
    (230, 302, 1.00, "#8C583F", "#39B8AD"),
    (352, 274, 0.96, "#F1C6A5", "#F4B942"),
    (481, 265, 1.06, "#C98761", "#8A79D1"),
    (610, 276, 0.98, "#F4D4B6", "#4E9BE8"),
    (732, 310, 1.02, "#6F4637", "#EE6C9B"),
    (842, 356, 0.90, "#DFA77E", "#43B99A"),
]

# A distant crowd: (x, y, scale, colour)
CROWD = []
for row, count in [(432, 22), (472, 25), (506, 29)]:
    for i in range(count):
        x = 30 + (i + (0.38 if row % 2 else 0)) * (900 / max(1, count - 1))
        y = row + random.uniform(-8, 8)
        sc = random.uniform(0.22, 0.36)
        colour = random.choice(["#3D6C91", "#456A88", "#6E7098", "#3F827E", "#8B637C"])
        CROWD.append((x, y, sc, colour))

STARS = [(random.uniform(20, 940), random.uniform(20, 380), random.uniform(0.6, 2.0), random.uniform(0.08, 0.45)) for _ in range(55)]


def person(x, y, sc, skin, shirt, glow=0.0, arm=0.0):
    # Minimal, friendly pictogram. arm > 0 points the next gift to the right.
    g = max(0.0, glow)
    halo = ""
    if g > 0:
        halo = f'''<circle cx="0" cy="-50" r="58" fill="none" stroke="#FFD166" stroke-width="3" opacity="{0.62*g:.3f}"/>
        <circle cx="0" cy="-50" r="69" fill="none" stroke="#FFD166" stroke-width="1" opacity="{0.23*g:.3f}"/>
        <circle cx="0" cy="-38" r="48" fill="#FFD166" opacity="{0.10*g:.3f}" filter="url(#softGlow)"/>'''
    return f'''<g transform="translate({x:.1f},{y:.1f}) scale({sc:.3f})">{halo}
      <path d="M-21 18 Q0 7 21 18 L27 58 Q0 69 -27 58 Z" fill="{shirt}"/>
      <path d="M-9 58 L-10 92 Q0 96 10 92 L9 58" fill="#17213D"/>
      <path d="M-16 91 Q-20 97 -11 99 L0 99 L0 91" fill="#111A31"/>
      <path d="M16 91 Q20 97 11 99 L0 99 L0 91" fill="#111A31"/>
      <circle cx="0" cy="-36" r="21" fill="{skin}"/>
      <path d="M-20 -40 Q-19 -66 3 -64 Q24 -62 21 -37 Q10 -52 -20 -40" fill="#20253B" opacity=".9"/>
      <path d="M-14 22 Q-31 34 -30 48" fill="none" stroke="{skin}" stroke-width="10" stroke-linecap="round"/>
      <path d="M14 22 Q27 31 31 43" fill="none" stroke="{skin}" stroke-width="10" stroke-linecap="round"/>
      <path d="M14 22 Q{29+8*arm:.1f} {8-22*arm:.1f} {43+9*arm:.1f} {2-26*arm:.1f}" fill="none" stroke="{skin}" stroke-width="10" stroke-linecap="round"/>
    </g>'''


def svg(t):
    # The gift moves from neighbour to neighbour from t=1.05 to 5.45.
    start = 1.05
    hop = 0.62
    travel = start + hop * (len(PEOPLE) - 1) + 0.25
    active = -1
    prev_active = -1
    pos = PEOPLE[0][:2]
    if t < travel:
        k = (t - start) / hop
        active = max(0, min(len(PEOPLE) - 2, int(k)))
        f = k - active
        p0 = PEOPLE[active]
        p1 = PEOPLE[active + 1]
        f = ease(f)
        x = p0[0] + (p1[0] - p0[0]) * f
        y = p0[1] + (p1[1] - p0[1]) * f - 30 * math.sin(math.pi * f)
        pos = (x, y - 72 * ((p0[2] + p1[2]) / 2))
        prev_active = active
    elif t < travel + 0.5:
        active = len(PEOPLE) - 1
        pos = (PEOPLE[-1][0], PEOPLE[-1][1] - 72 * PEOPLE[-1][2])

    # A quiet opening title.
    intro_a = alpha(t, 0.15, 1.55, 0.45)
    # Final title is fully readable for its final hold.
    # The closing message enters smoothly, then holds for a clear final beat.
    final_a = smooth(6.65, 7.30, t)
    scene_dark = 0.54 * final_a

    out = []
    out.append(f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
    <defs>
      <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0" stop-color="#08162B"/><stop offset=".52" stop-color="#111C38"/><stop offset="1" stop-color="#17162F"/>
      </linearGradient>
      <radialGradient id="warm"><stop offset="0" stop-color="#FFE9A8" stop-opacity=".95"/><stop offset=".26" stop-color="#FFD166" stop-opacity=".7"/><stop offset="1" stop-color="#FFD166" stop-opacity="0"/></radialGradient>
      <radialGradient id="cool"><stop offset="0" stop-color="#7FE9DD" stop-opacity=".65"/><stop offset="1" stop-color="#7FE9DD" stop-opacity="0"/></radialGradient>
      <linearGradient id="line" x1="0" y1="0" x2="1" y2="0"><stop stop-color="#F4B942"/><stop offset=".5" stop-color="#7FE9DD"/><stop offset="1" stop-color="#EF71A8"/></linearGradient>
      <filter id="glow" x="-200%" y="-200%" width="400%" height="400%"><feGaussianBlur stdDeviation="7" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
      <filter id="softGlow" x="-100%" y="-100%" width="300%" height="300%"><feGaussianBlur stdDeviation="18"/></filter>
    </defs>''')
    out.append(f'<rect width="{W}" height="{H}" fill="url(#bg)"/>')

    # Soft atmospheric light.
    out.append(f'<ellipse cx="480" cy="300" rx="430" ry="300" fill="url(#cool)" opacity="{0.12 + 0.05*math.sin(t*1.4):.3f}"/>')
    out.append(f'<ellipse cx="480" cy="460" rx="500" ry="120" fill="#060B1C" opacity=".38"/>')
    for x, y, r, a in STARS:
        tw = 0.72 + 0.28 * math.sin(t * 1.8 + x * .03)
        out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="#DDEBFF" opacity="{a*tw:.3f}"/>')

    # Crowd appears gradually in the final phase.
    crowd_a = smooth(5.25, 7.25, t)
    if crowd_a > 0:
        for x, y, sc, col in CROWD:
            out.append(f'<g transform="translate({x:.1f},{y:.1f}) scale({sc:.3f})" opacity="{crowd_a*.72:.3f}">'
                       f'<circle cx="0" cy="-18" r="9" fill="#D6A783"/><path d="M-10 -7 Q0 -13 10 -7 L13 22 Q0 27 -13 22Z" fill="{col}"/></g>')

    # The shared path behind the foreground neighbours.
    path = "M 112 351 C 220 250 330 215 481 265 C 625 205 750 255 842 356"
    reveal = clamp((t - 0.85) / 4.9)
    out.append(f'<path d="{path}" fill="none" stroke="#2B4161" stroke-width="3" stroke-linecap="round"/>')
    out.append(f'<path d="{path}" fill="none" stroke="url(#line)" stroke-width="4" stroke-linecap="round" pathLength="1" stroke-dasharray="1" stroke-dashoffset="{1-reveal:.4f}" opacity=".8" filter="url(#glow)"/>')

    # People, with a warm halo after they receive the gift.
    for i, (x, y, sc, skin, shirt) in enumerate(PEOPLE):
        lit = 0.0
        if t >= start + i * hop - .12:
            lit = smooth(start + i * hop - .12, start + i * hop + .55, t)
        # First person briefly reaches toward the second.
        arm = 0.0
        if i == 0:
            arm = math.sin(math.pi * clamp((t - .55) / .85))
        elif i == len(PEOPLE) - 2:
            arm = math.sin(math.pi * clamp((t - (start + i*hop) + .1) / .85))
        out.append(person(x, y, sc, skin, shirt, lit, arm))

    # Gift orb and trailing light.
    if t >= start - .3 and t <= travel + .75:
        x, y = pos
        out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="36" fill="url(#warm)" opacity=".9"/>')
        out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="11" fill="#FFF4C7" filter="url(#glow)"/>')
        # Three fading echoes along the recent path.
        for j, age in enumerate((0.08, 0.17, 0.27)):
            tt = t - age
            if tt >= start and tt <= travel:
                k = (tt - start) / hop
                ai = max(0, min(len(PEOPLE) - 2, int(k)))
                ff = ease(k - ai)
                p0, p1 = PEOPLE[ai], PEOPLE[ai + 1]
                ex = p0[0] + (p1[0] - p0[0]) * ff
                ey = p0[1] + (p1[1] - p0[1]) * ff - 30 * math.sin(math.pi * ff)
                ey -= 72 * ((p0[2] + p1[2]) / 2)
                out.append(f'<circle cx="{ex:.1f}" cy="{ey:.1f}" r="{6-j*1.4:.1f}" fill="#FFD166" opacity="{.30-j*.08:.3f}"/>')

    # After the chain, the spark branches upward into a constellation.
    branch = smooth(5.35, 7.0, t)
    if branch > 0:
        out.append(f'<path d="M842 284 C790 210 710 150 620 118 C500 76 330 95 210 150" fill="none" stroke="#FFD166" stroke-width="2.2" stroke-dasharray="5 10" opacity="{branch*.55:.3f}"/>')
        for j in range(28):
            tt = j / 27
            bx = 842 - 632 * tt
            by = 284 - 150 * math.sin(tt * math.pi * .82) - 34 * math.sin(tt * math.pi * 2)
            out.append(f'<circle cx="{bx:.1f}" cy="{by:.1f}" r="{2.2 + 1.4*math.sin(j*.9):.1f}" fill="#FFE39A" opacity="{branch*(.35+.25*math.sin(j*1.7)**2):.3f}"/>')

    # Opening label.
    if intro_a > 0:
        out.append(f'<g opacity="{intro_a:.3f}" transform="translate(480 77)">'
                   f'<circle cx="-73" cy="-1" r="4" fill="#FFD166"/><text x="0" y="7" text-anchor="middle" font-family="Arial,Helvetica,sans-serif" font-size="18" font-weight="700" letter-spacing="5" fill="#DDE8FA">A GOOD DEED</text>'
                   f'<circle cx="73" cy="-1" r="4" fill="#FFD166"/></g>')

    # Mid-scene beat.
    mid_a = alpha(t, 4.55, 5.95, .45)
    if mid_a > 0:
        out.append(f'<text x="480" y="72" text-anchor="middle" font-family="Arial,Helvetica,sans-serif" font-size="24" font-weight="700" letter-spacing="5" fill="#DCE9FA" opacity="{mid_a:.3f}">BECOMES A RIPPLE</text>')

    # Final title card layered over the widened, connected scene.
    if final_a > 0:
        out.append(f'<rect width="{W}" height="{H}" fill="#071124" opacity="{scene_dark:.3f}"/>')
        out.append(f'<g opacity="{final_a:.3f}">')
        out.append(f'<circle cx="480" cy="188" r="4" fill="#FFD166" opacity=".95"/>')
        out.append(f'<text x="480" y="280" text-anchor="middle" font-family="Arial,Helvetica,sans-serif" font-size="72" font-weight="800" letter-spacing="7" fill="#FFF9EC">PASS IT ON.</text>')
        out.append(f'<text x="480" y="326" text-anchor="middle" font-family="Arial,Helvetica,sans-serif" font-size="24" font-weight="400" letter-spacing="1" fill="#C8D7EC">One good act starts a ripple.</text>')
        out.append(f'<g transform="translate(480 379)">')
        out.append(f'<rect x="-177" y="-25" width="354" height="50" rx="25" fill="#FFD166"/>')
        out.append(f'<text x="0" y="7" text-anchor="middle" font-family="Arial,Helvetica,sans-serif" font-size="18" font-weight="800" letter-spacing="2.5" fill="#10182B">DO ONE GOOD THING TODAY</text>')
        out.append(f'</g></g>')

    out.append('</svg>')
    return "\n".join(out)


def render_svg(data: str, dest: Path):
    svg_path = BUILD / "current.svg"
    svg_path.write_text(data, encoding="utf-8")
    subprocess.run([
        "rsvg-convert", "-w", str(W), "-h", str(H), "-o", str(dest), str(svg_path)
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def main():
    print(f"Rendering {N} frames…")
    for i in range(N):
        t = i / FPS
        render_svg(svg(t), FRAMES / f"frame_{i:04d}.png")
        if (i + 1) % 30 == 0:
            print(f"  {i+1}/{N}")

    mp4 = OUT / "pass-it-on.mp4"
    subprocess.run([
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-framerate", str(FPS), "-i", str(FRAMES / "frame_%04d.png"),
        "-c:v", "libx264", "-preset", "slow", "-crf", "25", "-pix_fmt", "yuv420p",
        "-movflags", "+faststart", "-an", str(mp4)
    ], check=True)

    # A small, social-friendly poster made from the final hold frame.
    poster = OUT / "pass-it-on-poster.jpg"
    subprocess.run([
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(mp4),
        "-ss", "8.4", "-frames:v", "1", "-q:v", "3", str(poster)
    ], check=True)
    print(mp4, mp4.stat().st_size)
    print(poster, poster.stat().st_size)


if __name__ == "__main__":
    main()
