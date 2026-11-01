#!/usr/bin/env python3
"""Render 'A Little Space' — a ten-second, word-light animation about de-escalation.
All artwork and sound are generated here; no external assets are required.
"""
from __future__ import annotations
import argparse
import concurrent.futures
import math
import os
from pathlib import Path
import random
import shutil
import struct
import subprocess
import wave

ROOT = Path(__file__).resolve().parent.parent
WORK = ROOT / ".render"
OUT = ROOT / "output"
W, H, FPS, DURATION = 1280, 720, 30, 10


def clamp(x, lo=0.0, hi=1.0):
    return max(lo, min(hi, x))


def smooth(a, b, t):
    x = clamp((t - a) / (b - a))
    return x * x * (3 - 2 * x)


def ease_out(a, b, t):
    x = clamp((t - a) / (b - a))
    return 1 - (1 - x) ** 3


def lerp(a, b, p):
    return a + (b - a) * p


def fmt(x):
    return f"{x:.2f}".rstrip("0").rstrip(".")


def mix_hex(a, b, p):
    av = tuple(int(a[i:i+2], 16) for i in (1, 3, 5))
    bv = tuple(int(b[i:i+2], 16) for i in (1, 3, 5))
    return "#" + "".join(f"{round(lerp(x, y, p)):02x}" for x, y in zip(av, bv))


def character(side, calm, t):
    """A simple, expressive figure. side=-1 is left, +1 is right."""
    left = side == -1
    color = "#ef806f" if left else "#65b8c4"
    shadow = "#bd5b55" if left else "#448b9c"
    cx = (420 if left else 860) + (10 * (1-calm) * (-side))
    cy = 246 + 2 * math.sin(t * 2.2 + (0 if left else 1.7)) * (1-calm)
    # Anger is a small inward lean, not a caricature.
    lean = (1-calm) * (5 if left else -5)
    parts = [f'<g aria-label="{"person pausing" if left else "person responding"}">']
    parts.append(f'<ellipse cx="{cx}" cy="522" rx="139" ry="15" fill="#050b14" opacity=".28"/>')
    # Body and shoulder line relax as the hands open.
    shoulder_y = lerp(343, 356, calm)
    body = (f'M {cx-139} 520 Q {cx-126} {shoulder_y+12} {cx-49} {shoulder_y} '
            f'Q {cx} {shoulder_y-18} {cx+49} {shoulder_y} '
            f'Q {cx+126} {shoulder_y+12} {cx+139} 520 Z')
    parts.append(f'<path d="{body}" fill="{color}"/>')
    parts.append(f'<path d="M {cx-130} 520 Q {cx-115} 403 {cx-67} 378 Q {cx-100} 455 {cx-86} 520 Z" fill="{shadow}" opacity=".28"/>')
    # Neck.
    parts.append(f'<path d="M {cx-27} 306 L {cx-24} 349 Q {cx} 366 {cx+24} 349 L {cx+27} 306 Z" fill="{color}"/>')
    # Head, with a tiny nose giving each person a direction.
    parts.append(f'<g transform="rotate({lean} {cx} {cy})">')
    parts.append(f'<circle cx="{cx}" cy="{cy}" r="65" fill="{color}"/>')
    nose_x = cx + (63 if left else -63)
    if left:
        nose = f'M {nose_x-3} {cy-2} L {nose_x+17} {cy+10} L {nose_x-3} {cy+17} Z'
        ex = cx + 31
    else:
        nose = f'M {nose_x+3} {cy-2} L {nose_x-17} {cy+10} L {nose_x+3} {cy+17} Z'
        ex = cx - 31
    parts.append(f'<path d="{nose}" fill="{color}"/>')
    # Eyes shift from a tense slash to a quiet, level curve.
    eye_y = cy - 12
    if left:
        d = f'M {ex-8} {eye_y+lerp(4,0,calm)} Q {ex} {eye_y-2} {ex+8} {eye_y+lerp(-1,0,calm)}'
    else:
        d = f'M {ex-8} {eye_y+lerp(-1,0,calm)} Q {ex} {eye_y-2} {ex+8} {eye_y+lerp(4,0,calm)}'
    parts.append(f'<path d="{d}" fill="none" stroke="#142033" stroke-width="6" stroke-linecap="round"/>')
    # A restrained mouth change: tight line -> neutral -> almost-smile.
    mx = cx + (34 if left else -34)
    my = cy + 34
    curve = lerp(-3, 4, calm)
    parts.append(f'<path d="M {mx-8} {my} Q {mx} {my+curve} {mx+8} {my}" fill="none" stroke="#142033" stroke-width="4" stroke-linecap="round" opacity=".8"/>')
    parts.append('</g>')
    # Arm closest to the other person. It lowers and opens at a different time for each person.
    if left:
        sx, sy = cx+65, 386
        ex = lerp(cx+112, cx+88, calm)
        ey = lerp(445, 459, calm)
        hx, hy = lerp(570, 584, calm), lerp(374, 431, calm)
        direction = 1
    else:
        sx, sy = cx-65, 386
        ex = lerp(cx-112, cx-88, calm)
        ey = lerp(445, 459, calm)
        hx, hy = lerp(710, 696, calm), lerp(374, 431, calm)
        direction = -1
    parts.append(f'<path d="M {sx} {sy} Q {ex} {ey} {hx} {hy}" fill="none" stroke="{shadow}" stroke-width="48" stroke-linecap="round" stroke-linejoin="round"/>')
    parts.append(f'<path d="M {sx} {sy-4} Q {ex} {ey-5} {hx} {hy-3}" fill="none" stroke="{color}" stroke-width="34" stroke-linecap="round" stroke-linejoin="round"/>')
    # Fist crossfades into an open palm with clearly separated fingers.
    parts.append(f'<g opacity="{fmt(1-calm)}"><circle cx="{hx}" cy="{hy}" r="23" fill="{color}"/>')
    parts.append(f'<path d="M {hx-13} {hy-3} L {hx+13} {hy-3}" stroke="{shadow}" stroke-width="3" opacity=".65"/></g>')
    parts.append(f'<g opacity="{fmt(calm)}" transform="translate({hx} {hy}) scale({direction} 1)">')
    parts.append(f'<ellipse cx="0" cy="0" rx="20" ry="23" fill="{color}"/>')
    for x, y, length in [(-12,-17,19),(-3,-21,23),(7,-20,22),(15,-14,17)]:
        parts.append(f'<path d="M {x} {y+8} L {x} {y-length+8}" stroke="{color}" stroke-width="8" stroke-linecap="round"/>')
    parts.append(f'<path d="M -14 6 Q -29 1 -26 -10" fill="none" stroke="{color}" stroke-width="9" stroke-linecap="round"/>')
    parts.append('</g></g>')
    return "".join(parts)


def scene(t):
    global_p = smooth(3.4, 6.4, t)
    left_calm = smooth(2.15, 3.65, t)
    right_calm = smooth(4.45, 5.85, t)
    fade = smooth(0, .65, t)
    calm = global_p
    bg = mix_hex("#111724", "#10272b", calm)
    red_opacity = (1-smooth(3.2, 5.25, t)) * fade
    crack_growth = ease_out(.15, 1.05, t)
    jitter = (1-smooth(2.15, 2.65, t)) * 4.0
    pts = []
    random.seed(41)
    phases = [random.random()*math.tau for _ in range(12)]
    for i in range(12):
        y = lerp(145, 517, i/11)
        base = [0, -14, 11, -20, 17, -9, 20, -17, 10, -12, 8, 0][i]
        x = 640 + base + math.sin(t*18 + phases[i]) * jitter
        # Grow from the middle in both directions.
        y = lerp(331, y, crack_growth)
        pts.append(f"{fmt(x)} {fmt(y)}")
    crack_d = "M " + " L ".join(pts)

    s = [f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
<defs>
  <radialGradient id="bg" cx="50%" cy="42%" r="75%"><stop offset="0" stop-color="{bg}"/><stop offset="1" stop-color="#080e19"/></radialGradient>
  <radialGradient id="warm"><stop stop-color="#f7c76b" stop-opacity=".18"/><stop offset="1" stop-color="#f7c76b" stop-opacity="0"/></radialGradient>
  <radialGradient id="anger"><stop stop-color="#ed615b" stop-opacity=".2"/><stop offset="1" stop-color="#ed615b" stop-opacity="0"/></radialGradient>
  <linearGradient id="bridge" x1="0" x2="1"><stop stop-color="#ef806f"/><stop offset=".5" stop-color="#f7cf78"/><stop offset="1" stop-color="#65b8c4"/></linearGradient>
  <filter id="soft" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="12"/></filter>
</defs>
<rect width="1280" height="720" fill="url(#bg)"/>
<ellipse cx="640" cy="340" rx="480" ry="370" fill="url(#anger)" opacity="{fmt(red_opacity)}"/>
<ellipse cx="640" cy="360" rx="570" ry="430" fill="url(#warm)" opacity="{fmt(calm)}"/>
''']
    # Quiet, fixed points give the background depth without visual noise.
    random.seed(9)
    for _ in range(54):
        x, y = random.randrange(45, 1235), random.randrange(35, 550)
        r = random.choice([.6, .8, 1.0, 1.3])
        s.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="#dbe7df" opacity=".1"/>')

    # The consequence of the pause travels beyond the two people.
    for i in range(3):
        rp = clamp((t - 5.55 - i*.45) / 2.25)
        if 0 < rp < 1:
            r = lerp(100, 600, ease_out(0, 1, rp))
            op = math.sin(math.pi*rp) * .22
            s.append(f'<ellipse cx="640" cy="385" rx="{fmt(r)}" ry="{fmt(r*.57)}" fill="none" stroke="#f6ce7d" stroke-width="2" opacity="{fmt(op)}"/>')

    # Ground and shared pool of light.
    s.append(f'<ellipse cx="640" cy="520" rx="{fmt(lerp(340,470,calm))}" ry="23" fill="#050b14" opacity=".22"/>')
    s.append(f'<path d="M 196 520 L 1084 520" stroke="#c9d7d0" stroke-width="1" opacity="{fmt(.08+.07*calm)}"/>')

    # Two expanding breaths from the person who chooses to pause.
    for start in (2.25, 2.95):
        p = clamp((t-start)/1.35)
        if 0 < p < 1:
            r = lerp(24, 102, ease_out(0, 1, p))
            s.append(f'<circle cx="420" cy="410" r="{fmt(r)}" fill="none" stroke="#f7cf78" stroke-width="3" opacity="{fmt((1-p)*.55)}"/>')

    # Fracture: it stops shaking before it disappears. The stillness matters.
    if red_opacity > .002:
        s.append(f'<path d="{crack_d}" fill="none" stroke="#fa665e" stroke-width="20" opacity="{fmt(.13*red_opacity)}" filter="url(#soft)"/>')
        s.append(f'<path d="{crack_d}" fill="none" stroke="#ff7669" stroke-width="6" stroke-linejoin="miter" opacity="{fmt(red_opacity)}"/>')
        # Small angular fragments make the conflict feel brittle rather than monstrous.
        random.seed(24)
        for i in range(10):
            side = -1 if i % 2 else 1
            x = 640 + side*random.randrange(24, 80)
            y = random.randrange(180, 500)
            fall = smooth(3.2, 5.1, t)
            yy = y + fall*fall*95
            rot = fall*side*55
            op = red_opacity * (1-fall*.6)
            s.append(f'<path d="M -4 -7 L 5 -2 L -2 7 Z" transform="translate({fmt(x)} {fmt(yy)}) rotate({fmt(rot)})" fill="#ff7669" opacity="{fmt(op)}"/>')

    # Characters remain present through the whole transformation.
    s.append(character(-1, left_calm, t))
    s.append(character(1, right_calm, t))

    # The bridge is drawn only after both hands have begun to open.
    bp = smooth(4.65, 6.25, t)
    if bp > 0:
        d = 'M 585 432 Q 640 365 695 432'
        s.append(f'<path d="{d}" pathLength="1" fill="none" stroke="#f6ca73" stroke-width="20" stroke-linecap="round" stroke-dasharray="1" stroke-dashoffset="{fmt(1-bp)}" opacity=".11" filter="url(#soft)"/>')
        s.append(f'<path d="{d}" pathLength="1" fill="none" stroke="url(#bridge)" stroke-width="7" stroke-linecap="round" stroke-dasharray="1" stroke-dashoffset="{fmt(1-bp)}"/>')
        # One quiet point travels back and forth: attention, not victory.
        if bp > .98:
            u = (math.sin((t-6.25)*2.1)+1)/2
            # Quadratic Bezier evaluation.
            x = (1-u)**2*585 + 2*(1-u)*u*640 + u*u*695
            y = (1-u)**2*432 + 2*(1-u)*u*365 + u*u*432
            s.append(f'<circle cx="{fmt(x)}" cy="{fmt(y)}" r="5" fill="#fff2bf"/>')

    # New growth is small and credible: not a magical explosion.
    plant = smooth(5.8, 7.35, t)
    if plant > 0:
        s.append(f'<g transform="translate(640 519) scale({fmt(plant)})">')
        s.append('<path d="M 0 0 Q -4 -39 0 -83" fill="none" stroke="#82c99b" stroke-width="6" stroke-linecap="round"/>')
        leaf_l = smooth(.25, .72, plant)
        leaf_r = smooth(.48, .95, plant)
        s.append(f'<g transform="translate(-1 -42) scale({fmt(leaf_l)})"><path d="M 0 0 Q -42 -36 -54 -4 Q -30 18 0 0 Z" fill="#82c99b"/><path d="M -4 -1 L -39 -7" stroke="#d0e7af" stroke-width="2" opacity=".6"/></g>')
        s.append(f'<g transform="translate(0 -67) scale({fmt(leaf_r)})"><path d="M 0 0 Q 39 -39 54 -9 Q 35 18 0 0 Z" fill="#a8d59b"/><path d="M 5 -2 L 39 -12" stroke="#e2edba" stroke-width="2" opacity=".6"/></g>')
        s.append('</g>')

    # Closing message. One sentence, then a memorable action.
    text_p = smooth(7.35, 8.25, t)
    if text_p > 0:
        dy = lerp(12, 0, ease_out(0, 1, text_p))
        s.append(f'<g opacity="{fmt(text_p)}" transform="translate(0 {fmt(dy)})" text-anchor="middle">')
        s.append('<text x="640" y="614" fill="#f2eee3" font-family="Arial, Helvetica, sans-serif" font-size="36" font-weight="400" letter-spacing=".2">A pause can change what happens next.</text>')
        s.append('<text x="640" y="660" fill="#f4ca77" font-family="Arial, Helvetica, sans-serif" font-size="14" font-weight="700" letter-spacing="4.2">BREATHE  ·  LISTEN  ·  RESPOND</text>')
        s.append('</g>')

    # A restrained opening cue; it disappears before the choice is made.
    intro = smooth(.35, .9, t) * (1-smooth(1.8, 2.35, t))
    if intro > 0:
        s.append(f'<text x="640" y="82" text-anchor="middle" fill="#d8deda" opacity="{fmt(intro*.65)}" font-family="Arial, Helvetica, sans-serif" font-size="13" font-weight="700" letter-spacing="5">BEFORE YOU REACT</text>')
    s.append(f'<rect width="1280" height="720" fill="#080e19" opacity="{fmt(1-fade)}" pointer-events="none"/>')
    s.append('</svg>')
    return "".join(s)


def render_one(i):
    svg = WORK / f"frame_{i:04d}.svg"
    png = WORK / f"frame_{i:04d}.png"
    svg.write_text(scene(i/FPS), encoding="utf-8")
    subprocess.run(["rsvg-convert", "-w", str(W), "-h", str(H), "-o", str(png), str(svg)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    svg.unlink()
    return i


def synth_audio(path):
    """A soft, original sound bed: tension -> breath -> warm resolution."""
    sr = 48000
    n = sr * DURATION
    rng = random.Random(71)
    frames = bytearray()
    # Bell partials are deliberately quiet; the animation works without sound too.
    bells = [(2.25, 523.25, .07), (2.98, 659.25, .045), (4.62, 392.0, .055),
             (5.82, 523.25, .06), (6.35, 659.25, .045), (7.45, 783.99, .04)]
    for i in range(n):
        t = i/sr
        calm = smooth(3.3, 6.5, t)
        # Filtered-looking deterministic air (smoothed noise), plus low tension.
        air = (rng.random()*2-1) * .0025
        tense = (1-calm) * smooth(.15, .8, t)
        drone = tense * (.022*math.sin(math.tau*55*t) + .012*math.sin(math.tau*58.27*t))
        pad_env = smooth(3.7, 6.3, t) * (1-smooth(9.25, 10, t))
        pad = pad_env * (.014*math.sin(math.tau*130.81*t) + .012*math.sin(math.tau*164.81*t) + .01*math.sin(math.tau*196*t))
        val = drone + pad + air
        for start, freq, amp in bells:
            dt = t-start
            if 0 <= dt < 2.5:
                env = (1-math.exp(-dt*45)) * math.exp(-dt*2.4)
                val += amp*env*(math.sin(math.tau*freq*dt) + .24*math.sin(math.tau*freq*2.01*dt))
        # The world's softest breath, used as a transition rather than a whoosh.
        for start in (2.15, 4.45):
            dt = t-start
            if 0 <= dt < 1.1:
                val += (rng.random()*2-1) * .007 * math.sin(math.pi*dt/1.1)**2
        master = smooth(0, .45, t) * (1-smooth(9.35, 10, t))
        left = clamp(val*master, -1, 1)
        right = clamp((val + .0015*math.sin(math.tau*261.6*t)*calm)*master, -1, 1)
        frames.extend(struct.pack('<hh', int(left*32767), int(right*32767)))
    with wave.open(str(path), 'wb') as wav:
        wav.setnchannels(2)
        wav.setsampwidth(2)
        wav.setframerate(sr)
        wav.writeframes(frames)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--stills', action='store_true', help='render selected review frames only')
    ap.add_argument('--frames', type=str, default='', help='comma-separated times for stills')
    ap.add_argument('--encode', action='store_true', help='encode already rendered frames')
    args = ap.parse_args()
    OUT.mkdir(exist_ok=True)
    WORK.mkdir(exist_ok=True)
    if args.stills:
        times = [float(x) for x in args.frames.split(',')] if args.frames else [1.5, 3.0, 5.5, 8.8]
        for idx, t in enumerate(times):
            svg = WORK / f"still_{idx}.svg"
            png = WORK / f"still_{idx}.png"
            svg.write_text(scene(t), encoding='utf-8')
            subprocess.run(['rsvg-convert', '-w', str(W), '-h', str(H), '-o', str(png), str(svg)], check=True)
            subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', str(png), '-q:v', '2', str(WORK / f"review_{idx}.jpg")], check=True)
        return
    if not args.encode:
        for p in WORK.glob('frame_*'):
            p.unlink()
        workers = min(8, os.cpu_count() or 4)
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
            for done, _ in enumerate(pool.map(render_one, range(FPS*DURATION)), 1):
                if done % 30 == 0:
                    print(f"Rendered {done}/{FPS*DURATION} frames", flush=True)
    audio = WORK / 'soundtrack.wav'
    synth_audio(audio)
    target = OUT / 'a_little_space.mp4'
    cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(FPS),
           '-i', str(WORK / 'frame_%04d.png'), '-i', str(audio),
           '-vf', 'noise=alls=2:allf=t+u', '-c:v', 'libx264', '-preset', 'slow', '-crf', '22',
           '-pix_fmt', 'yuv420p', '-af', 'volume=9dB', '-c:a', 'aac', '-b:a', '96k', '-t', str(DURATION),
           '-movflags', '+faststart', str(target)]
    subprocess.run(cmd, check=True)
    # A finished cover image, not an intermediate review frame.
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-ss', '8.8', '-i', str(target),
                    '-frames:v', '1', '-q:v', '2', str(OUT / 'a_little_space.jpg')], check=True)
    print(target)


if __name__ == '__main__':
    main()
