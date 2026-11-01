#!/usr/bin/env python3
"""
PAUSE. BREATHE. SEE EACH OTHER.
A 10-second, word-light animation for everyone.

Story in four beats:
  0.0-2.1  conflict: two people, jagged words between them
  2.1-4.7  pause:    one slow breath dissolves the shards
  4.7-7.2  connect:  frowns become smiles, a heart replaces the bolt
  7.2-10.0 ripple:   zoom out to a world that lights up, person by person

Frames are written as SVG (stdlib only), rasterised with rsvg-convert,
and encoded to MP4 with ffmpeg.
"""
import math, os, subprocess, shutil, sys

W, H, FPS, DUR = 960, 540, 24, 10
N = FPS * DUR
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRAMES = os.path.join(ROOT, "frames")
OUT = os.path.join(ROOT, "output", "pause-breathe-see-each-other.mp4")

# ---------- helpers ----------
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def ss(x):  # smoothstep of clamped x
    x = clamp(x); return x * x * (3 - 2 * x)
def between(t, a, b): return ss((t - a) / (b - a))
def fade(t, a, b, c, d):  # in a-b, out c-d
    return between(t, a, b) * (1 - between(t, c, d))
def lerp(a, b, k): return a + (b - a) * k
def hexrgb(h): return tuple(int(h[i:i+2], 16) for i in (1, 3, 5))
def mix(h1, h2, k):
    a, b = hexrgb(h1), hexrgb(h2)
    return "#%02x%02x%02x" % tuple(round(lerp(a[i], b[i], k)) for i in range(3))
def ease_out(x): x = clamp(x); return 1 - (1 - x) ** 3

# palettes
BG_DARK, BG_MID, BG_DAWN = "#131c2b", "#27455c", "#f7c873"
TEAL, AMBER, CORAL, PINK = "#3ec6b8", "#ffb347", "#ff6b5e", "#ff8fab"
CREAM = "#fff6e8"

def person(x, y, s, color, mood, eye_open, blink=0.0, flip=1):
    """mood: -1 angry/frowning .. +1 smiling. Returns SVG for one figure."""
    mk = ss((mood + 1) / 2)                            # 0 angry .. 1 calm
    brow_y = lerp(-28, -32, mk)
    inner = lerp(10, -1, mk)                           # angry: inner brows drop
    outer = lerp(-6, -1, mk)
    mouth_ctrl = lerp(-26, 30, mk)                     # frown -> smile
    eye_h = max(1.2, 9 * eye_open * (1 - blink))
    parts = [f'<g transform="translate({x:.1f},{y:.1f}) scale({s:.3f})">']
    # body / shoulders
    parts.append(f'<path d="M -62 118 Q -58 52 0 48 Q 58 52 62 118 Z" fill="{color}"/>')
    # head (no hair / features that belong to any one culture)
    parts.append(f'<circle cx="0" cy="0" r="52" fill="{CREAM}"/>')
    # brows: front-facing, symmetric — inner ends fall when angry
    parts.append(f'<path d="M -35 {brow_y+outer:.1f} L -12 {brow_y+inner:.1f}" stroke="#26303e" stroke-width="6" stroke-linecap="round"/>')
    parts.append(f'<path d="M 12 {brow_y+inner:.1f} L 35 {brow_y+outer:.1f}" stroke="#26303e" stroke-width="6" stroke-linecap="round"/>')
    # eyes
    parts.append(f'<ellipse cx="-20" cy="-8" rx="5.5" ry="{eye_h:.1f}" fill="#26303e"/>')
    parts.append(f'<ellipse cx="20" cy="-8" rx="5.5" ry="{eye_h:.1f}" fill="#26303e"/>')
    # cheeks appear as mood warms
    cheek = clamp((mood + 0.2) / 1.2) * 0.55
    parts.append(f'<circle cx="-32" cy="16" r="9" fill="{PINK}" opacity="{cheek:.2f}"/>')
    parts.append(f'<circle cx="32" cy="16" r="9" fill="{PINK}" opacity="{cheek:.2f}"/>')
    # mouth
    parts.append(f'<path d="M -18 26 Q 0 {26+mouth_ctrl:.1f} 18 26" fill="none" stroke="#26303e" stroke-width="6" stroke-linecap="round"/>')
    parts.append('</g>')
    return "".join(parts)

def mini_person(x, y, s, color, lit):
    c = color if lit else "#5b6b7d"
    o = 1.0 if lit else 0.55
    return (f'<g transform="translate({x:.1f},{y:.1f}) scale({s:.3f})" opacity="{o:.2f}">'
            f'<circle cx="0" cy="-14" r="11" fill="{CREAM}"/>'
            f'<path d="M -15 22 Q -13 -4 0 -4 Q 13 -4 15 22 Z" fill="{c}"/></g>')

def heart(x, y, s, color=PINK, opacity=1.0):
    return (f'<g transform="translate({x:.1f},{y:.1f}) scale({s:.3f})" opacity="{opacity:.2f}">'
            f'<path d="M 0 34 C -54 -4 -24 -44 0 -18 C 24 -44 54 -4 0 34 Z" fill="{color}"/></g>')

def frame_svg(t):
    e = []  # svg elements
    # ---- background: storm -> calm -> dawn ----
    warm = between(t, 2.0, 5.0)
    dawn = between(t, 7.0, 9.4)
    bg = mix(mix(BG_DARK, BG_MID, warm), BG_DAWN, dawn * 0.92)
    e.append(f'<rect width="{W}" height="{H}" fill="{bg}"/>')
    # sun rising in final beat
    if dawn > 0:
        sy = lerp(560, 118, ease_out(dawn))
        e.append(f'<circle cx="480" cy="{sy:.0f}" r="150" fill="#ffd98a" opacity="{0.35*dawn:.2f}"/>')
        e.append(f'<circle cx="480" cy="{sy:.0f}" r="86" fill="#ffe9b0" opacity="{0.55*dawn:.2f}"/>')
    # drifting soft dots (air / stars)
    for i in range(26):
        px = (i * 173 + 60) % W
        py = (i * 97 + 34) % 300 + math.sin(t * 0.7 + i) * 5
        col = CREAM if dawn < 0.6 else "#ffffff"
        e.append(f'<circle cx="{px}" cy="{py:.0f}" r="{2 + i % 3}" fill="{col}" opacity="{0.10 + 0.10 * ((i % 4) / 3):.2f}"/>')

    # ---- camera: zoom out in final beat ----
    zoom = between(t, 7.1, 8.7)
    cam_s = lerp(1.22, 0.34, ease_out(zoom))
    cam_y = lerp(268, 322, ease_out(zoom))   # main pair end standing on the globe
    shake = (1 - between(t, 0.0, 2.2)) * 3.0
    shx = math.sin(t * 43) * shake if t < 2.2 else 0
    shy = math.cos(t * 37) * shake * 0.6 if t < 2.2 else 0

    # ---- globe (revealed on zoom-out) ----
    gx, gy, gr = 480, 712, 348
    if zoom > 0:
        e.append(f'<circle cx="{gx}" cy="{gy}" r="{gr}" fill="#2e9db4" opacity="{zoom:.2f}"/>')
        e.append(f'<path d="M {gx-gr+40} {gy-190} Q {gx-90} {gy-260} {gx+30} {gy-205} Q {gx-40} {gy-150} {gx-gr+70} {gy-120} Z" fill="#57c98a" opacity="{zoom:.2f}"/>')
        e.append(f'<path d="M {gx+120} {gy-230} Q {gx+250} {gy-190} {gx+215} {gy-105} Q {gx+130} {gy-140} {gx+120} {gy-230} Z" fill="#57c98a" opacity="{zoom:.2f}"/>')
        e.append(f'<path d="M {gx-190} {gy-70} Q {gx-90} {gy-115} {gx-30} {gy-60} Q {gx-110} {gy-25} {gx-190} {gy-70} Z" fill="#7ed491" opacity="{zoom:.2f}"/>')

    # ---- world people around the globe, lit by the ripple ----
    world_cols = [TEAL, AMBER, CORAL, "#7ed491", "#b39df0", "#ff8fab", "#5db9e8"]
    positions = []
    for i, angdeg in enumerate(range(-168, -11, 13)):   # top arc of the globe
        a = math.radians(angdeg)
        positions.append((gx + math.cos(a) * (gr - 6), gy + math.sin(a) * (gr - 6), i))
    for i, (px, py, idx) in enumerate(positions):
        if zoom <= 0: break
        light_at = 7.9 + idx * 0.11 + abs(idx - 6) * 0.05
        lit = t > light_at
        pop = ease_out((t - light_at) / 0.35) if lit else 0
        e.append(mini_person(px, py - 16, 0.95 + 0.25 * pop, world_cols[idx % len(world_cols)], lit))
    # a few lower figures on the visible globe face
    for i, (dx, dy) in enumerate([(-215, -120), (215, -128), (-140, -55), (150, -52), (-255, -205), (262, -215)]):
        if zoom <= 0: break
        lit = t > 8.6 + i * 0.14
        e.append(mini_person(gx + dx, gy + dy, 0.85, world_cols[(i + 3) % len(world_cols)], lit))

    # ---- ripple rings from the main pair ----
    for k in range(3):
        rt = t - (7.55 + k * 0.65)
        if 0 < rt < 2.4 and zoom > 0.3:
            rr = ease_out(rt / 2.4) * 520
            e.append(f'<circle cx="480" cy="{cam_y-40:.0f}" r="{rr:.0f}" fill="none" stroke="{CREAM}" stroke-width="4" opacity="{(1-rt/2.4)*0.65:.2f}"/>')

    # ---- breath ring ----
    if 1.9 < t < 5.4:
        inhale = between(t, 2.2, 4.0)          # one slow in-breath
        exhale = between(t, 4.35, 5.3)
        br = lerp(70, 198, ease_out(inhale)) - 58 * exhale
        bo = fade(t, 1.9, 2.4, 4.9, 5.4) * 0.85
        e.append(f'<circle cx="480" cy="268" r="{br:.0f}" fill="none" stroke="#aef2e8" stroke-width="10" opacity="{bo:.2f}"/>')
        e.append(f'<circle cx="480" cy="268" r="{br*0.72:.0f}" fill="none" stroke="#ffe9b0" stroke-width="5" opacity="{bo*0.7:.2f}"/>')
        # breath dot that rides the ring
        e.append(f'<circle cx="480" cy="{268-br:.0f}" r="11" fill="#aef2e8" opacity="{bo:.2f}"/>')

    # ---- conflict shards & bolt (beat 1, dissolving in beat 2) ----
    conflict = 1 - between(t, 2.0, 3.1)
    if conflict > 0.01:
        flick = 0.75 + 0.25 * math.sin(t * 30)
        bolt_s = (1.55 + 0.14 * math.sin(t * 22)) * flick
        e.append(f'<g transform="translate(480,262) scale({bolt_s:.2f})" opacity="{conflict:.2f}">'
                 f'<polygon points="-8,-72 26,-14 6,-8 22,70 -30,2 -8,-4" fill="{CORAL}"/></g>')
        for i in range(10):
            a = i * 2.399 + 0.6                       # golden-angle scatter
            dist = 95 + (i % 4) * 30 + between(t, 2.0, 3.1) * 90
            fall = between(t, 2.0, 3.1) ** 2 * 120
            px, py = 480 + math.cos(a) * dist, 262 + math.sin(a) * dist * 0.8 + fall
            r = 7 + (i % 3) * 4
            rot = math.degrees(a) + t * 40 * (1 if i % 2 else -1)
            e.append(f'<g transform="translate({px:.0f},{py:.0f}) rotate({rot:.0f})" opacity="{conflict * (0.55 + 0.4 * ((i % 3)/2)):.2f}">'
                     f'<polygon points="0,{-r} {r},{r} {-r},{r}" fill="{CORAL if i%2 else AMBER}"/></g>')

    # ---- connection: heart + link between the pair (beats 3-4) ----
    connect = between(t, 4.7, 5.6)
    if connect > 0:
        pulse = 1 + 0.10 * math.sin((t - 5.6) * 5.2) * connect
        hx, hy = 480, lerp(268, cam_y - 52, ease_out(zoom))
        hs = lerp(1.15, 0.85, ease_out(zoom)) * pulse
        hy = lerp(hy, cam_y - 96, ease_out(zoom))
        e.append(heart(hx, hy - 6, hs * connect, PINK, connect))
        # little sprout of life above the heart, beat 3 only
        if zoom < 0.7:
            grow = between(t, 5.6, 6.6)
            e.append(f'<path d="M 480 {hy-52:.0f} Q 478 {hy-74:.0f} 480 {hy-96*grow:.0f}" fill="none" stroke="#57c98a" stroke-width="6" stroke-linecap="round" opacity="{connect*(1-zoom):.2f}"/>')
            e.append(f'<path d="M 480 {hy-84:.0f} Q {480-26*grow:.0f} {hy-102:.0f} {480-30*grow:.0f} {hy-84:.0f} Q {480-14*grow:.0f} {hy-74:.0f} 480 {hy-84:.0f} Z" fill="#7ed491" opacity="{grow*(1-zoom):.2f}"/>')
            e.append(f'<path d="M 480 {hy-84:.0f} Q {480+26*grow:.0f} {hy-102:.0f} {480+30*grow:.0f} {hy-84:.0f} Q {480+14*grow:.0f} {hy-74:.0f} 480 {hy-84:.0f} Z" fill="#57c98a" opacity="{grow*(1-zoom):.2f}"/>')

    # ---- the two main people ----
    calming = between(t, 2.2, 4.6)
    mood = lerp(-1, 1, ss(calming)) if t < 4.7 else 1.0
    eyes_closed = math.sin(clamp((t - 2.4) / 2.0) * math.pi) if 2.4 < t < 4.4 else 0.0
    eye_open = 1 - 0.92 * eyes_closed
    gap = lerp(175, 148, connect) + lerp(0, 26, zoom)   # step a little closer, then apart on globe
    lx, rx = 480 - gap, 480 + gap
    bob = math.sin(t * 2.0) * 3 * (0.3 + 0.7 * connect)
    e.append(f'<g transform="translate({shx:.1f},{shy:.1f})">')
    e.append(person(lx, cam_y + bob, cam_s, TEAL, mood, eye_open, flip=1))
    # second person calms a beat later — listening takes a moment
    mood2 = lerp(-1, 1, ss(between(t, 3.4, 5.6)))
    e.append(person(rx, cam_y - bob, cam_s, AMBER, mood2, max(eye_open, between(t, 4.4, 5.0)), flip=-1))
    e.append('</g>')
    # (connection in the final beat is carried by the heart + ripples,
    #  not a line — a long line across the globe read as a rope)

    # ---- words: three short, universal beats ----
    def caption(text, opacity, y, size=44, col=CREAM, spacing=10):
        if opacity <= 0.01: return ""
        return (f'<text x="480" y="{y}" font-family="Arial, Helvetica, sans-serif" font-size="{size}" '
                f'font-weight="700" letter-spacing="{spacing}" text-anchor="middle" fill="{col}" opacity="{opacity:.2f}">{text}</text>')
    e.append(caption("PAUSE", fade(t, 2.0, 2.5, 2.9, 3.3), 500))
    e.append(caption("BREATHE", fade(t, 3.5, 4.0, 4.9, 5.4), 500))
    e.append(caption("SEE EACH OTHER", fade(t, 5.5, 6.1, 7.3, 7.9), 500, size=38))
    # final card
    fin = between(t, 8.6, 9.3)
    e.append(caption("PAUSE · BREATHE · CARE", fin, 86, size=40, col="#26303e" if dawn > 0.5 else CREAM, spacing=6))
    e.append(caption("pass it on", fin * (0.75 + 0.25 * math.sin(t * 3) ** 2), 138, size=27,
                     col="#5c3208" if dawn > 0.5 else CREAM, spacing=4))

    # vignette
    e.append('<rect width="960" height="540" fill="url(#vg)"/>')
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">'
           f'<defs><radialGradient id="vg" cx="50%" cy="46%" r="78%">'
           f'<stop offset="72%" stop-color="#000" stop-opacity="0"/><stop offset="100%" stop-color="#000" stop-opacity="0.28"/>'
           f'</radialGradient></defs>' + "".join(e) + '</svg>')
    return svg

def main():
    if os.path.isdir(FRAMES): shutil.rmtree(FRAMES)
    os.makedirs(FRAMES); os.makedirs(os.path.dirname(OUT), exist_ok=True)
    for i in range(N):
        t = i / FPS
        p = os.path.join(FRAMES, f"{i:04d}.svg")
        with open(p, "w") as f: f.write(frame_svg(t))
        subprocess.run(["rsvg-convert", "-w", str(W), "-h", str(H), p,
                        "-o", os.path.join(FRAMES, f"{i:04d}.png")],
                       check=True, capture_output=True)
        if i % 48 == 0: print(f"frame {i}/{N}", flush=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS),
                    "-i", os.path.join(FRAMES, "%04d.png"),
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "19",
                    "-preset", "medium", "-movflags", "+faststart", OUT], check=True)
    print("wrote", OUT, os.path.getsize(OUT), "bytes")

if __name__ == "__main__":
    main()
