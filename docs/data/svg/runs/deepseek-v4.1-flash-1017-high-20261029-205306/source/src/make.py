#!/usr/bin/env python3
"""Generate "Kindness ripples" — an animated SVG poster, a still, and a loop video.

Everything is drawn from scratch with plain Python; rsvg-convert rasterises the
SVG and ffmpeg encodes the frames.  No external assets.
"""

import math
import os
import random
import shutil
import subprocess

W, H = 1200, 1500
CX, CY = 600.0, 840.0          # centre of the water surface / impact point
T = 8.0                        # loop length (seconds)
IMP = 1.15                     # moment the drop hits the water
N = 120                        # SMIL samples over the loop
SAMPLES = [T * i / (N - 1) for i in range(N)]

SERIF = ("Iowan Old Style, Palatino Linotype, Palatino, Georgia, "
         "'Times New Roman', serif")
SANS = "Avenir Next, Helvetica Neue, Arial, sans-serif"

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(HERE, "output")
PREVIEW = os.path.join(HERE, "preview")


# ----------------------------------------------------------------- helpers ---
def smoothstep(a, b, x):
    if b == a:
        return 0.0 if x < a else 1.0
    u = min(1.0, max(0.0, (x - a) / (b - a)))
    return u * u * (3 - 2 * u)


def lerp(a, b, u):
    return a + (b - a) * u


def fmt(v, nd=2):
    return f"{v:.{nd}f}"


def animate(name, fn, nd=2, samples=SAMPLES):
    vals = ";".join(fmt(fn(t), nd) for t in samples)
    kts = ";".join(f"{t / T:.4f}" for t in samples)
    return (f'<animate attributeName="{name}" values="{vals}" '
            f'keyTimes="{kts}" dur="{T}s" repeatCount="indefinite"/>')


# ------------------------------------------------------------------- scene ---
def drop_state(t):
    """(y, rx, ry, opacity, trail_opacity) of the falling drop."""
    if t >= IMP:
        return None
    p = t / IMP
    y = lerp(250.0, CY, p * p)
    rx = 7.0 * (1 - 0.30 * p ** 4)
    ry = 10.5 * (1 + 1.15 * p ** 4)
    op = smoothstep(0.0, 0.14, t)
    trail = 0.45 * p ** 1.4
    return y, rx, ry, op, trail


def flash_state(t):
    if t < IMP:
        return 0.0, 0.0
    dt = t - IMP
    op = math.exp(-dt / 0.20)
    grow = 1 - math.exp(-dt / 0.09)
    return op, grow


RINGS = []
_RING_COLS = ["#ffd9a8", "#ffc287", "#d8ece6", "#b9e4de"]
for _i in range(7):
    RINGS.append((
        IMP + _i * 0.34,          # birth
        4.80,                     # life
        512.0 + _i * 12.0,        # max radius
        0.60 * (0.93 ** _i),      # opacity
        _RING_COLS[_i % 4],
        3.0 - _i * 0.16,          # stroke width
    ))


def ring_state(t, ring):
    t0, life, rmax, op0, _, _ = ring
    u = (t - t0) / life
    if u <= 0.0 or u >= 1.0:
        return 0.0, 0.0, 0.0, 0.0
    e = 1 - (1 - u) ** 2.5
    rx = lerp(22.0, rmax, e)
    ry = rx * 0.255
    op = op0 * (1 - u) ** 1.15 * smoothstep(0.0, 0.05, u)
    sw = 0.55 + (ring[5] - 0.55) * (1 - u) ** 1.4
    return rx, ry, op, sw


SPLASH = [
    # vx, vy, radius
    (-150.0, -340.0, 3.2),
    (-55.0, -455.0, 2.4),
    (35.0, -500.0, 2.0),
    (120.0, -400.0, 2.9),
    (205.0, -320.0, 2.2),
    (-235.0, -280.0, 1.8),
    (250.0, -250.0, 1.6),
    (-105.0, -390.0, 1.7),
]


def splash_state(t, s):
    vx, vy, r = s
    dt = t - IMP
    if dt < 0:
        return None
    x = CX + vx * dt
    y = CY + vy * dt + 0.5 * 1500.0 * dt * dt
    op = smoothstep(0.0, 0.04, dt) * (1.0 - smoothstep(0.26, 0.52, dt))
    return x, y, r, op


rng = random.Random(20261029)
STARS = []
for i in range(84):
    STARS.append((
        rng.uniform(28, W - 28),
        rng.uniform(48, 745),
        rng.uniform(0.55, 1.9),
        rng.uniform(0.10, 0.52),
        i % 4,
    ))

STAR_PHASE = [0.0, 1.7, 3.3, 4.9]


def star_group_op(t, g):
    return 0.80 + 0.20 * math.sin(2 * math.pi * t / T + STAR_PHASE[g])


MOTES = []
mrng = random.Random(5)
for i in range(10):
    MOTES.append((
        mrng.uniform(330, 870),
        mrng.uniform(610, 930),
        mrng.uniform(0.9, 2.0),
        mrng.uniform(0.10, 0.30),
        mrng.uniform(0, 2 * math.pi),
        mrng.uniform(3.0, 8.0),
    ))


def mote_pos(t, m):
    x, y, r, op, ph, amp = m
    return (x + amp * math.sin(2 * math.pi * t / T + ph),
            y + amp * 0.7 * math.cos(2 * math.pi * t / T + ph * 1.3),
            op * (0.75 + 0.25 * math.sin(2 * math.pi * t / T * 2 + ph)))


# -------------------------------------------------------------------- svg ---
def build_svg(t, animated=False):
    """Render the scene.  Static when animated=False, SMIL-driven otherwise."""
    def val(name, fn, nd=2):
        return animate(name, fn, nd) if animated else fmt(fn(t), nd)

    # Base values for the animated file: a composed, ring-filled moment so the
    # poster still reads if a viewer ignores SMIL.
    bt = 2.7 if animated else t
    bd = drop_state(bt)
    bflash_op, bflash_grow = flash_state(bt)

    out = []
    out.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
        f'viewBox="0 0 {W} {H}" role="img" '
        f'aria-label="A drop falls into dark water, sending warm ripples outward. '
        f'The words read: A small act. Kindness ripples. One kind thing, passed on, '
        f'can travel further than you will ever see. Pass it on.">'
    )
    out.append('<title>Kindness ripples</title>')
    out.append('<desc>A single drop falls into still, dark water. Rings of light '
               'spread far beyond the point of impact. Text: one kind thing, '
               'passed on, can travel further than you will ever see.</desc>')
    out.append('<defs>')
    out.append(
        '<radialGradient id="bg" cx="50%" cy="56%" r="78%">'
        '<stop offset="0" stop-color="#153641"/>'
        '<stop offset="0.42" stop-color="#0b1e27"/>'
        '<stop offset="1" stop-color="#04090d"/>'
        '</radialGradient>'
    )
    out.append(
        '<radialGradient id="sheen" cx="50%" cy="50%" r="50%">'
        '<stop offset="0" stop-color="#a8e3da" stop-opacity="0.16"/>'
        '<stop offset="0.55" stop-color="#6fb9b4" stop-opacity="0.06"/>'
        '<stop offset="1" stop-color="#6fb9b4" stop-opacity="0"/>'
        '</radialGradient>'
    )
    out.append(
        '<radialGradient id="glow" cx="50%" cy="50%" r="50%">'
        '<stop offset="0" stop-color="#ffe3b8" stop-opacity="0.60"/>'
        '<stop offset="0.30" stop-color="#ffbe7e" stop-opacity="0.24"/>'
        '<stop offset="1" stop-color="#ff9d54" stop-opacity="0"/>'
        '</radialGradient>'
    )
    out.append(
        '<radialGradient id="flash" cx="50%" cy="50%" r="50%">'
        '<stop offset="0" stop-color="#fff8e8" stop-opacity="0.95"/>'
        '<stop offset="0.45" stop-color="#ffd9a0" stop-opacity="0.55"/>'
        '<stop offset="1" stop-color="#ffb877" stop-opacity="0"/>'
        '</radialGradient>'
    )
    out.append(
        '<radialGradient id="dropg" cx="38%" cy="30%" r="70%">'
        '<stop offset="0" stop-color="#fffdf4"/>'
        '<stop offset="0.55" stop-color="#ffe4b8"/>'
        '<stop offset="1" stop-color="#f0a860"/>'
        '</radialGradient>'
    )
    out.append(
        '<linearGradient id="ringWarm" x1="0" y1="0" x2="1" y2="1">'
        '<stop offset="0" stop-color="#fff1d6" stop-opacity="1"/>'
        '<stop offset="0.32" stop-color="#ffd6a2" stop-opacity="0.90"/>'
        '<stop offset="0.66" stop-color="#ffb877" stop-opacity="0.60"/>'
        '<stop offset="1" stop-color="#8ec9c2" stop-opacity="0.26"/>'
        '</linearGradient>'
    )
    out.append(
        '<linearGradient id="ringCool" x1="0" y1="0" x2="1" y2="1">'
        '<stop offset="0" stop-color="#f4fcf9" stop-opacity="0.95"/>'
        '<stop offset="0.38" stop-color="#c9eae4" stop-opacity="0.80"/>'
        '<stop offset="0.74" stop-color="#9ad4cd" stop-opacity="0.50"/>'
        '<stop offset="1" stop-color="#6aa8a3" stop-opacity="0.22"/>'
        '</linearGradient>'
    )
    out.append(
        '<linearGradient id="trail" gradientUnits="userSpaceOnUse" '
        'x1="0" y1="210" x2="0" y2="840">'
        '<stop offset="0" stop-color="#ffd9a8" stop-opacity="0"/>'
        '<stop offset="1" stop-color="#ffd9a8" stop-opacity="0.85"/>'
        '</linearGradient>'
    )
    out.append(
        '<radialGradient id="vig" cx="50%" cy="47%" r="74%">'
        '<stop offset="0.52" stop-color="#02060a" stop-opacity="0"/>'
        '<stop offset="1" stop-color="#02060a" stop-opacity="0.62"/>'
        '</radialGradient>'
    )
    out.append(
        '<filter id="soft" x="-40%" y="-40%" width="180%" height="180%">'
        '<feGaussianBlur stdDeviation="16"/></filter>'
    )
    out.append(
        '<filter id="ringGlow" x="-20%" y="-60%" width="140%" height="220%">'
        '<feGaussianBlur stdDeviation="3.2"/></filter>'
    )
    out.append('</defs>')

    # background
    out.append(f'<rect width="{W}" height="{H}" fill="url(#bg)"/>')

    # stars (four groups, gently twinkling out of phase)
    for g in range(4):
        op = star_group_op(bt if animated else t, g)
        if animated:
            out.append('<g opacity="1">' +
                       animate("opacity", lambda tt, g=g: star_group_op(tt, g), 3))
        else:
            out.append(f'<g opacity="{op:.3f}">')
        for (x, y, r, o, gg) in STARS:
            if gg != g:
                continue
            out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.2f}" '
                       f'fill="#e8f4f2" fill-opacity="{o:.3f}"/>')
        out.append('</g>')

    # faint pool of light on the water
    out.append(f'<ellipse cx="{CX}" cy="{CY}" rx="860" ry="300" fill="url(#sheen)" '
               f'opacity="0.55"/>')

    # ambient / impact glow
    if animated:
        glow_attr = animate(
            "opacity",
            lambda tt: 0.09 + 0.34 * flash_state(tt)[0], 3)
        out.append(f'<ellipse cx="{CX}" cy="{CY}" rx="320" ry="106" '
                   f'fill="url(#glow)" opacity="0.09">{glow_attr}</ellipse>')
    else:
        out.append(f'<ellipse cx="{CX}" cy="{CY}" rx="320" ry="106" '
                   f'fill="url(#glow)" opacity="{0.09 + 0.34 * bflash_op:.3f}"/>')

    # the rings: a soft luminous under-painting plus crisp crests
    glow_parts, crisp_parts = [], []
    for ring in RINGS:
        t0, life, rmax, op0, colour, w0 = ring
        rx, ry, op, sw = ring_state(bt if animated else t, ring)
        grad = "ringWarm" if colour in ("#ffd9a8", "#ffc287") else "ringCool"
        base = (f'cx="{CX}" cy="{CY}" rx="{fmt(rx)}" ry="{fmt(ry)}" '
                f'fill="none" stroke="url(#{grad})"')
        if animated:
            rx_a = animate("rx", lambda tt, r=ring: ring_state(tt, r)[0], 2)
            ry_a = animate("ry", lambda tt, r=ring: ring_state(tt, r)[1], 2)
            op_a = animate("opacity", lambda tt, r=ring: ring_state(tt, r)[2], 3)
            sw_a = animate("stroke-width", lambda tt, r=ring: ring_state(tt, r)[3], 2)
            gsw_a = animate("stroke-width",
                            lambda tt, r=ring: ring_state(tt, r)[3] * 3.4, 2)
            gop_a = animate("opacity",
                            lambda tt, r=ring: ring_state(tt, r)[2] * 0.55, 3)
            glow_parts.append(
                f'<ellipse {base} stroke-width="{fmt(sw * 3.4)}" '
                f'opacity="{op * 0.55:.3f}">{rx_a}{ry_a}{gop_a}{gsw_a}</ellipse>')
            crisp_parts.append(
                f'<ellipse {base} stroke-width="{fmt(sw)}" opacity="{op:.3f}">'
                f'{rx_a}{ry_a}{op_a}{sw_a}</ellipse>')
        else:
            glow_parts.append(
                f'<ellipse {base} stroke-width="{fmt(sw * 3.4)}" '
                f'opacity="{op * 0.55:.3f}"/>')
            crisp_parts.append(
                f'<ellipse {base} stroke-width="{fmt(sw)}" opacity="{op:.3f}"/>')
    out.append('<g filter="url(#ringGlow)">' + "".join(glow_parts) + '</g>')
    out.append('<g>' + "".join(crisp_parts) + '</g>')

    # warm core that lingers after the impact
    if animated:
        out.append(
            f'<ellipse cx="{CX}" cy="{CY}" rx="78" ry="19" fill="url(#glow)" opacity="0.16">'
            f'{animate("opacity", lambda tt: 0.07 + 0.32 * math.exp(-max(0.0, tt - IMP) / 1.6), 3)}'
            f'</ellipse>')
    else:
        core_op = 0.07 + 0.32 * math.exp(-max(0.0, (bt if animated else t) - IMP) / 1.6)
        out.append(f'<ellipse cx="{CX}" cy="{CY}" rx="78" ry="19" '
                   f'fill="url(#glow)" opacity="{core_op:.3f}"/>')

    # splash droplets
    for s in SPLASH:
        st = splash_state(bt if animated else t, s)
        if st is None:
            continue
        x, y, r, op = st
        if animated:
            cx_a = animate("cx", lambda tt, s=s: (splash_state(tt, s) or (0, 0, 0, 0))[0], 2)
            cy_a = animate("cy", lambda tt, s=s: (splash_state(tt, s) or (0, 0, 0, 0))[1], 2)
            op_a = animate("opacity", lambda tt, s=s: (splash_state(tt, s) or (0, 0, 0, 0))[3], 3)
            out.append(
                f'<circle cx="{fmt(x)}" cy="{fmt(y)}" r="{r:.2f}" fill="#ffe6bf" '
                f'opacity="{op:.3f}">{cx_a}{cy_a}{op_a}</circle>')
        else:
            out.append(
                f'<circle cx="{fmt(x)}" cy="{fmt(y)}" r="{r:.2f}" fill="#ffe6bf" '
                f'opacity="{op:.3f}"/>')

    # motes drifting in the glow
    for m in MOTES:
        x, y, op = mote_pos(bt if animated else t, m)
        if animated:
            cx_a = animate("cx", lambda tt, m=m: mote_pos(tt, m)[0], 2)
            cy_a = animate("cy", lambda tt, m=m: mote_pos(tt, m)[1], 2)
            op_a = animate("opacity", lambda tt, m=m: mote_pos(tt, m)[2], 3)
            out.append(
                f'<circle cx="{fmt(x)}" cy="{fmt(y)}" r="{m[2]:.2f}" fill="#ffd9a8" '
                f'opacity="{op:.3f}">{cx_a}{cy_a}{op_a}</circle>')
        else:
            out.append(
                f'<circle cx="{fmt(x)}" cy="{fmt(y)}" r="{m[2]:.2f}" fill="#ffd9a8" '
                f'opacity="{op:.3f}"/>')

    # impact flash
    if animated:
        out.append(
            f'<ellipse cx="{CX}" cy="{CY}" rx="18" ry="4" fill="url(#flash)" opacity="0">'
            f'{animate("rx", lambda tt: 18 + 30 * flash_state(tt)[1], 1)}'
            f'{animate("ry", lambda tt: (18 + 30 * flash_state(tt)[1]) * 0.23, 1)}'
            f'{animate("opacity", lambda tt: flash_state(tt)[0] * 0.9, 3)}'
            f'</ellipse>')
    elif bflash_op > 0.001:
        frx = 18 + 30 * bflash_grow
        out.append(
            f'<ellipse cx="{CX}" cy="{CY}" rx="{fmt(frx)}" ry="{fmt(frx * 0.27)}" '
            f'fill="url(#flash)" opacity="{bflash_op * 0.9:.3f}"/>')

    # falling drop + its trail
    if animated:
        out.append(
            f'<line x1="{CX}" y1="240" x2="{CX}" y2="240" stroke="url(#trail)" '
            f'stroke-width="2" stroke-linecap="round" opacity="0">'
            f'{animate("y1", lambda tt: (drop_state(tt) or (0, 0, 0, 0, 0))[0] - 130, 1)}'
            f'{animate("y2", lambda tt: (drop_state(tt) or (0, 0, 0, 0, 0))[0] - 12, 1)}'
            f'{animate("opacity", lambda tt: (drop_state(tt) or (0, 0, 0, 0, 0))[4], 3)}'
            f'</line>')
        out.append(
            f'<ellipse cx="{CX}" cy="250" rx="7" ry="10.5" fill="url(#dropg)" opacity="0">'
            f'{animate("cy", lambda tt: (drop_state(tt) or (0, 0, 0, 0, 0))[0], 2)}'
            f'{animate("rx", lambda tt: (drop_state(tt) or (0, 0, 0, 0, 0))[1], 2)}'
            f'{animate("ry", lambda tt: (drop_state(tt) or (0, 0, 0, 0, 0))[2], 2)}'
            f'{animate("opacity", lambda tt: (drop_state(tt) or (0, 0, 0, 0, 0))[3], 3)}'
            f'</ellipse>')
    else:
        ds = drop_state(t)
        if ds:
            y, rx, ry, op, trail = ds
            out.append(
                f'<line x1="{CX}" y1="{y - 130:.1f}" x2="{CX}" y2="{y - 12:.1f}" '
                f'stroke="url(#trail)" stroke-width="2" stroke-linecap="round" '
                f'opacity="{trail:.3f}"/>')
            out.append(
                f'<ellipse cx="{CX}" cy="{y:.2f}" rx="{rx:.2f}" ry="{ry:.2f}" '
                f'fill="url(#dropg)" opacity="{op:.3f}"/>')

    # vignette
    out.append(f'<rect width="{W}" height="{H}" fill="url(#vig)"/>')

    # ----------------------------------------------------------------- text --
    out.append(f'<g font-family="{SANS}" text-anchor="middle">')
    out.append(f'<line x1="576" y1="176" x2="624" y2="176" stroke="#ffd9a8" '
               f'stroke-opacity="0.45" stroke-width="1"/>')
    out.append(f'<text x="{CX}" y="216" font-size="16.5" letter-spacing="7.5" '
               f'fill="#e5cdae" fill-opacity="0.72" font-weight="500">A SMALL ACT</text>')
    out.append('</g>')

    # headline, with a warm halo behind it
    out.append(
        f'<text x="{CX}" y="1118" text-anchor="middle" font-family="{SERIF}" '
        f'font-size="92" fill="#ffcf9a" fill-opacity="0.30" filter="url(#soft)">'
        f'Kindness <tspan font-style="italic">ripples.</tspan></text>')
    out.append(
        f'<text x="{CX}" y="1118" text-anchor="middle" font-family="{SERIF}" '
        f'font-size="92" fill="#f7ecdc">Kindness '
        f'<tspan font-style="italic" fill="#ffd2a2">ripples.</tspan></text>')

    out.append(
        f'<g font-family="{SANS}" text-anchor="middle" fill="#d5e6e2">'
        f'<text x="{CX}" y="1194" font-size="27" fill-opacity="0.80" '
        f'letter-spacing="0.4">One kind thing, passed on, can travel</text>'
        f'<text x="{CX}" y="1236" font-size="27" fill-opacity="0.80" '
        f'letter-spacing="0.4">further than you will ever see.</text>'
        f'</g>')

    out.append(f'<line x1="548" y1="1348" x2="652" y2="1348" stroke="#ffd9a8" '
               f'stroke-opacity="0.28" stroke-width="1"/>')
    out.append(
        f'<text x="{CX}" y="1394" text-anchor="middle" font-family="{SANS}" '
        f'font-size="15" letter-spacing="8" fill="#e5cdae" fill-opacity="0.58">'
        f'PASS IT ON</text>')

    out.append('</svg>')
    return "\n".join(out)


def write_static_svg(path, t):
    with open(path, "w", encoding="utf-8") as f:
        f.write(build_svg(t, animated=False))


def main():
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(PREVIEW, exist_ok=True)

    # 1. animated SVG
    svg_path = os.path.join(OUT, "kindness-ripples.svg")
    import xml.dom.minidom
    animated_svg = build_svg(2.7, animated=True)
    xml.dom.minidom.parseString(animated_svg)  # fail loudly if malformed
    with open(svg_path, "w", encoding="utf-8") as f:
        f.write(animated_svg)
    print("wrote", svg_path, os.path.getsize(svg_path), "bytes")

    # 2. poster still (a composed moment, drop just landed)
    poster_svg = os.path.join(PREVIEW, "poster.svg")
    write_static_svg(poster_svg, 2.55)
    subprocess.run(["rsvg-convert", "-w", str(W), "-h", str(H),
                    "-o", os.path.join(PREVIEW, "poster.png"), poster_svg],
                   check=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i",
                    os.path.join(PREVIEW, "poster.png"), "-q:v", "2",
                    os.path.join(OUT, "kindness-ripples-poster.jpg")], check=True)
    print("wrote poster jpg")

    # 3. video frames
    frames = os.path.join(PREVIEW, "frames")
    if os.path.isdir(frames):
        shutil.rmtree(frames)
    os.makedirs(frames)
    fps = 30
    nframes = int(T * fps)
    vw, vh = 1080, 1350
    for i in range(nframes):
        t = i / fps
        sp = os.path.join(frames, "f.svg")
        write_static_svg(sp, t)
        subprocess.run(["rsvg-convert", "-w", str(vw), "-h", str(vh),
                        "-o", os.path.join(frames, f"f_{i:04d}.png"), sp],
                       check=True)
        if i % 30 == 0:
            print("frame", i, "/", nframes)

    mp4 = os.path.join(OUT, "kindness-ripples.mp4")
    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error", "-framerate", str(fps),
        "-i", os.path.join(frames, "f_%04d.png"),
        "-c:v", "libx264", "-preset", "slow", "-crf", "21",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart",
        "-vf", "scale=1080:1350", mp4], check=True)
    print("wrote", mp4, os.path.getsize(mp4), "bytes")


if __name__ == "__main__":
    main()
