"""Hands-only CPR in ten seconds. Renders frames in pure Python and pipes them to ffmpeg.

usage: python3 make.py            -> output/hands_only_cpr.mp4 + output/hands_only_cpr_poster.png
       python3 make.py still T    -> /tmp/still.jpg of the frame at time T (for checking)
"""
import os, sys, subprocess
from math import cos, pi, sin
from font import Font
from raster import Canvas, hexcol, lerp_col

W, H, FPS, DUR = 1280, 720, 30, 9.9
BPM = 110
T_PUSH = 2.6               # compressions start

BG = hexcol('#0E1626')
INK = hexcol('#F5F2EC')
MUTED = hexcol('#8FA0B8')
RED = hexcol('#E8414B')
PATIENT = hexcol('#D5DEEB')
PATIENT_DK = hexcol('#AEBDD3')
RESCUER = hexcol('#F4A261')
RESCUER_DK = hexcol('#D9823F')
GROUND = hexcol('#273650')
PANEL = hexcol('#141F33')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
font = Font('/System/Library/Fonts/Helvetica.ttc', want_name='Helvetica Bold')


def ease(t):
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 3


def fade(t, start, dur=0.4):
    """Returns (alpha, slide_offset) for an element appearing at `start`."""
    e = ease((t - start) / dur)
    return e, (1 - e) * 14


def compression(t):
    """(depth 0..1, push index) at time t."""
    if t < T_PUSH:
        return 0.0, -1
    phase = (t - T_PUSH) * BPM / 60.0
    n = int(phase)
    frac = phase - n
    # quick push down, slightly slower release
    if frac < 0.42:
        d = (1 - cos(pi * frac / 0.42)) / 2
    else:
        d = (1 + cos(pi * (frac - 0.42) / 0.58)) / 2
    return d, n


def draw_figures(c, t, alpha):
    depth, n = compression(t)
    gy = 600                                  # ground
    push = 20 * depth                         # chest travel in px
    # ground line
    c.rrect(40, gy, 600, gy + 5, 2.5, GROUND, alpha)

    # ---- rescuer (behind patient) ----
    hx = 312                                  # hands x (centre of chest)
    hy = 505 + push                           # top of chest
    sx, sy = hx + 6, hy - 215                 # shoulder: straight arms, directly above hands
    hipx, hipy = 492, 448
    c.capsule(hipx, hipy, hipx, 582, 28, RESCUER_DK, alpha)                   # thigh (kneeling)
    c.capsule(hipx, hipy, sx, sy, 28, RESCUER, alpha)                         # torso leaning over
    c.circle(sx - 30 - 8 * depth, sy - 46, 32, RESCUER, alpha)                # head
    c.capsule(sx + 10, sy + 6, hx + 12, hy - 6, 12, RESCUER_DK, alpha)        # far arm
    c.capsule(sx - 8, sy + 8, hx - 4, hy - 6, 12, RESCUER, alpha)             # near arm
    c.rrect(hx - 30, hy - 20, hx + 26, hy + 4, 9, RESCUER_DK, alpha)          # stacked hands
    c.rrect(hx - 26, hy - 12, hx + 30, hy + 4, 8, RESCUER, alpha)

    # ---- patient lying on the ground ----
    c.circle(150, 556, 42, PATIENT, alpha)                                    # head
    c.capsule(186, 562, 212, 562, 13, PATIENT_DK, alpha)                      # neck
    c.capsule(430, 568, 575, 573, 27, PATIENT, alpha)                         # legs
    c.rrect(575, 548, 596, 598, 9, PATIENT_DK, alpha)                         # foot
    c.rrect(205, hy, 440, gy, 34, PATIENT, alpha)                             # torso / chest
    c.capsule(250, 585, 330, 588, 11, PATIENT_DK, alpha)                      # arm by the side

    # push ripple around the hands
    if n >= 0:
        phase = ((t - T_PUSH) * BPM / 60.0) % 1.0
        if phase < 0.6:
            k = phase / 0.6
            c.ring(hx, hy - 8, 30 + 60 * k, 4, RED, alpha * (1 - k) * 0.8)


def draw_text(c, t):
    x = 630
    tx = x + 64
    # headline
    a, dy = fade(t, 0.25)
    c.text(font, 'Someone collapses and', x, 92 + dy, 44, INK, a)
    c.text(font, "isn't breathing normally?", x, 142 + dy, 44, INK, a)

    # step 1
    a, dy = fade(t, 1.1)
    c.circle(x + 22, 224 + dy, 24, RED, a)
    c.text(font, '1', x + 22, 236 + dy, 32, INK, a, align='center')
    c.text(font, 'CALL', tx, 237 + dy, 35, RED, a)
    c.text(font, 'your emergency number.', tx + c.text_width(font, 'CALL ', 35), 237 + dy, 35, INK, a)
    c.text(font, 'Put the phone on speaker.', tx, 273 + dy, 25, MUTED, a)

    # step 2
    a, dy = fade(t, T_PUSH)
    c.circle(x + 22, 344 + dy, 24, RED, a)
    c.text(font, '2', x + 22, 356 + dy, 32, INK, a, align='center')
    c.text(font, 'PUSH', tx, 357 + dy, 35, RED, a)
    c.text(font, 'hard and fast', tx + c.text_width(font, 'PUSH ', 35), 357 + dy, 35, INK, a)
    c.text(font, 'on the centre of the chest, arms straight.', tx, 393 + dy, 25, MUTED, a)

    # tempo line with beat dots
    a, dy = fade(t, 4.6)
    depth, n = compression(t)
    for i in range(8):
        dx = tx + 10 + i * 34
        on = n >= 0 and i <= (n % 8)
        if on and i == n % 8:
            c.circle(dx, 452 + dy, 9 + 5 * depth, RED, a)
        elif on:
            c.circle(dx, 452 + dy, 9, RED, a)
        else:
            c.ring(dx, 452 + dy, 9, 2.5, MUTED, a)
    c.text(font, 'About 2 pushes every second.', tx, 502 + dy, 30, INK, a)
    c.text(font, "Don't stop until help arrives.", tx, 538 + dy, 30, INK, a)

    # outro
    a, dy = fade(t, 7.4)
    beat = 3 * sin(((t - T_PUSH) * BPM / 60.0) * 2 * pi) if t > T_PUSH else 0
    c.heart(x + 22, 624 + dy, 32 + beat, RED, a)
    c.text(font, 'Hands-only CPR can double', tx, 612 + dy, 26, INK, a)
    c.text(font, 'their chance of survival.', tx, 644 + dy, 26, INK, a)
    c.text(font, 'No training needed. You can do this.', tx, 680 + dy, 24, RED, a)


def frame(c, t):
    c.clear()
    a, _ = fade(t, 0.0, 0.5)
    draw_figures(c, t, a)
    draw_text(c, t)


def main():
    out = os.path.join(ROOT, 'output')
    os.makedirs(out, exist_ok=True)
    c = Canvas(W, H, BG)
    if len(sys.argv) > 1 and sys.argv[1] == 'still':
        frame(c, float(sys.argv[2]))
        open('/tmp/still.png', 'wb').write(c.png_bytes())
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', '/tmp/still.png', '-q:v', '3', '/tmp/still.jpg'])
        return
    nframes = int(DUR * FPS)
    mp4 = os.path.join(out, 'hands_only_cpr.mp4')
    ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
                           '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                           '-c:v', 'libx264', '-preset', 'slow', '-crf', '20', '-pix_fmt', 'yuv420p',
                           '-movflags', '+faststart', mp4], stdin=subprocess.PIPE)
    for i in range(nframes):
        frame(c, i / FPS)
        ff.stdin.write(c.buf)
        if i % 30 == 0:
            print(f'frame {i}/{nframes}', flush=True)
    ff.stdin.close()
    ff.wait()
    frame(c, DUR)   # final poster frame
    open(os.path.join(out, 'hands_only_cpr_poster.png'), 'wb').write(c.png_bytes())
    print('done')


if __name__ == '__main__':
    main()
