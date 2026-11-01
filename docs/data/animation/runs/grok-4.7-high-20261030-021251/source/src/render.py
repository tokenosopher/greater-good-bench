#!/usr/bin/env python3
"""
Be Gentle — a ten-second film.

Everyone carries something other people cannot see. If the person about to
say the sharp thing pauses, looks, and chooses gentleness, both of them
are lighter — and that choice spreads.

The picture language is deliberate: triangles are harm, circles are care.
Sharp words leave the hand, stop in mid-air, and become light.
"""

import math
import subprocess
import sys
from pathlib import Path

W, H = 1280, 720
FPS = 24
NFRAMES = FPS * 10

ROOT = Path(__file__).resolve().parent.parent
TMP = ROOT / "tmp"
FRAMES = TMP / "frames"
OUT = ROOT / "output" / "be-gentle.mp4"

# Timeline (seconds)
A_X0, A_X1 = 488.0, 566.0
B_X = 746.0
WALK_END = 0.78

# Palette
SKY_TOP_0, SKY_TOP_1 = (12, 16, 32), (20, 22, 46)
SKY_MID_0, SKY_MID_1 = (22, 38, 72), (92, 70, 112)
SKY_HOR_0, SKY_HOR_1 = (40, 54, 92), (240, 164, 116)
GND_0, GND_1 = (16, 20, 38), (42, 32, 46)
GND_EDGE_0, GND_EDGE_1 = (36, 48, 78), (196, 122, 96)
FAR_0, FAR_1 = (24, 34, 64), (78, 58, 92)
A_0, A_1 = (154, 164, 186), (242, 202, 164)
B_0, B_1 = (176, 150, 156), (244, 206, 192)
RED = (212, 78, 68)
GOLD = (255, 214, 138)
GOLD2 = (255, 246, 220)
INK = (22, 16, 28)

CROWD = [
    # x, scale, cool, warm, slump0, phase, childish height already in scale
    (148, 0.56, (138, 164, 152), (228, 212, 180), 0.72, 0.2),
    (262, 0.44, (196, 164, 140), (240, 216, 196), 0.62, 1.4),
    (392, 0.70, (144, 136, 168), (228, 212, 236), 0.80, 2.1),
    (888, 0.68, (126, 152, 168), (220, 230, 238), 0.76, 0.6),
    (1018, 0.46, (196, 152, 152), (246, 216, 212), 0.66, 1.8),
    (1132, 0.58, (168, 160, 122), (238, 224, 184), 0.84, 2.6),
]


def clamp(v, a, b):
    return a if v < a else b if v > b else v


def lerp(a, b, t):
    return a + (b - a) * t


def ilerp(a, b, t):
    t = clamp(t, 0.0, 1.0)
    return tuple(lerp(a[i], b[i], t) for i in range(len(a)))


def smooth(t):
    t = clamp(t, 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def smoother(t):
    t = clamp(t, 0.0, 1.0)
    return t * t * t * (t * (t * 6.0 - 15.0) + 10.0)


def ease_out(t):
    t = clamp(t, 0.0, 1.0)
    return 1.0 - (1.0 - t) ** 3


def interval(t, t0, t1):
    return clamp((t - t0) / (t1 - t0), 0.0, 1.0)


def kf(t, keys):
    if t <= keys[0][0]:
        return keys[0][1]
    if t >= keys[-1][0]:
        return keys[-1][1]
    for (t0, v0), (t1, v1) in zip(keys, keys[1:]):
        if t0 <= t <= t1:
            u = smooth((t - t0) / (t1 - t0)) if t1 != t0 else 1.0
            return lerp(v0, v1, u)
    return keys[-1][1]


def rgb(c):
    return "#{:02x}{:02x}{:02x}".format(
        max(0, min(255, int(round(c[0])))),
        max(0, min(255, int(round(c[1])))),
        max(0, min(255, int(round(c[2])))),
    )


def rand(i, s=0):
    x = math.sin(i * 127.1 + s * 311.7) * 43758.5453
    return x - math.floor(x)


def hill_y(x):
    n = (x - 640.0) / 860.0
    return 552.0 + n * n * 42.0


def camera(t):
    z = kf(t, [(0.0, 1.40), (0.8, 1.50), (2.05, 1.56), (3.4, 1.50), (5.1, 1.40), (7.2, 1.18), (10.0, 1.14)])
    # Follow the pair, then settle centered.
    ax = lerp(A_X0, A_X1, smooth(interval(t, 0.0, WALK_END)))
    mid = (ax + B_X) * 0.5
    cx = kf(t, [(0.0, mid), (1.2, 656.0), (5.0, 656.0), (8.0, 648.0), (10.0, 646.0)])
    cy = kf(t, [(0.0, 458.0), (2.2, 452.0), (5.4, 448.0), (8.0, 438.0), (10.0, 434.0)])
    amp = 1.0 - smooth(interval(t, 6.4, 7.4))
    cx += math.sin(t * 0.37) * 2.2 * amp
    cy += math.cos(t * 0.29) * 1.4 * amp
    return cx, cy, z


def blink(t, t0, dur=0.16):
    u = (t - t0) / dur
    if 0.0 <= u <= 1.0:
        return math.sin(u * math.pi)
    return 0.0


def scene(t):
    """All animated quantities for time t."""
    dawn = smooth(interval(t, 4.55, 7.15))
    anger = kf(t, [(0.55, 0.0), (1.45, 1.0), (2.15, 1.0), (3.15, 0.0), (10.0, 0.0)])
    see = smooth(interval(t, 2.05, 3.05))
    opened = smooth(interval(t, 2.85, 3.65))
    warmth_a = smooth(interval(t, 3.15, 5.6))
    warmth_b = smooth(interval(t, 4.9, 6.3))
    lift = smooth(interval(t, 4.85, 6.05))
    walk_u = smooth(interval(t, 0.0, WALK_END))
    walk_speed = math.sin(clamp(t / WALK_END, 0, 1) * math.pi) if t < WALK_END + 0.12 else 0.0

    flinch = 0.0
    if 1.62 <= t <= 2.08:
        flinch = math.sin((t - 1.62) / 0.46 * math.pi) * 16.0

    close = smooth(interval(t, 5.3, 6.7))
    a_x = lerp(A_X0, A_X1, walk_u) + close * 10
    b_x = B_X + flinch - close * 14
    a_slump = lerp(0.18, 0.02, warmth_a) + anger * 0.08
    b_slump = lerp(0.92, 0.08, lift)
    a_lean = anger * 12.0 * (1.0 - opened) + opened * 3.0
    # lean is degrees, positive = toward screen right
    b_lean = -flinch * 0.25 + lerp(-4.0, 1.5, lift)

    return {
        "t": t,
        "dawn": dawn,
        "anger": anger,
        "see": see,
        "opened": opened,
        "warmth_a": warmth_a,
        "warmth_b": warmth_b,
        "lift": lift,
        "walk_speed": walk_speed,
        "a_x": a_x,
        "b_x": b_x,
        "a_slump": a_slump,
        "b_slump": b_slump,
        "a_lean": a_lean,
        "b_lean": b_lean,
        "fade": smooth(interval(t, 0.0, 0.28)),
        "text1": smooth(interval(t, 6.35, 7.05)),
        "dot": smooth(interval(t, 6.95, 7.45)),
        "text2": smooth(interval(t, 7.25, 8.0)),
        "crowd": smooth(interval(t, 5.05, 6.15)),
    }


def rotate(x, y, ox, oy, deg):
    a = math.radians(deg)
    ca, sa = math.cos(a), math.sin(a)
    dx, dy = x - ox, y - oy
    return ox + dx * ca - dy * sa, oy + dx * sa + dy * ca


def layout_body(cx, foot_y, scale, slump, lean):
    s = scale
    hip_y = foot_y - 34.0 * s
    body_rx = 21.0 * s
    body_h = (80.0 - slump * 28.0) * s
    body_bot = hip_y + 4.0 * s
    body_top = body_bot - body_h
    head_r = 22.5 * s
    # A heavy slump sinks the head into the shoulders.
    head_cy = body_top - head_r * 0.28 + slump * 16.0 * s
    head_cx = cx + slump * 2.0 * s
    shoulder_y = body_top + body_rx * 0.85
    # Rotate upper body around hip for lean.
    def R(x, y):
        return rotate(x, y, cx, hip_y, lean)

    head = R(head_cx, head_cy)
    sh_l = R(cx - body_rx * 0.78, shoulder_y)
    sh_r = R(cx + body_rx * 0.78, shoulder_y)
    chest = R(cx, body_top + body_h * 0.42)
    body_top_c = R(cx, body_top)
    return {
        "cx": cx,
        "foot_y": foot_y,
        "hip_y": hip_y,
        "s": s,
        "body_rx": body_rx,
        "body_top": body_top,
        "body_bot": body_bot,
        "head": head,
        "head_r": head_r,
        "sh_l": sh_l,
        "sh_r": sh_r,
        "chest": chest,
        "body_top_c": body_top_c,
        "lean": lean,
        "slump": slump,
    }


def capsule_path(cx, top, bot, rx):
    # Stadium / capsule. top is the top of the shape.
    if bot - top < rx * 2.2:
        rx = max(2.0, (bot - top) * 0.42)
    return (
        f"M {cx - rx:.1f},{top + rx:.1f} "
        f"A {rx:.1f},{rx:.1f} 0 0 1 {cx + rx:.1f},{top + rx:.1f} "
        f"L {cx + rx:.1f},{bot - rx:.1f} "
        f"A {rx:.1f},{rx:.1f} 0 0 1 {cx - rx:.1f},{bot - rx:.1f} Z"
    )


def face_marks(head, r, look_x, look_y, eye_open, brow_anger, brow_sad, smile, s):
    hx, hy = head
    # Local scale so features stay readable but proportional.
    fs = max(s, 0.85)
    ex = 7.2 * fs
    ey = hy - 1.5 * fs + look_y * 1.4 * fs
    lx = look_x * 1.5 * fs
    ly = look_y * 1.6 * fs
    eh = max(0.45, 3.15 * fs * eye_open)
    ew = 3.15 * fs
    parts = []
    ink = rgb(INK)
    sclera = "#f7f3ec"
    for sgn in (-1, 1):
        cx = hx + sgn * ex
        parts.append(
            f'<ellipse cx="{cx:.1f}" cy="{ey:.1f}" rx="{ew:.1f}" ry="{eh:.1f}" fill="{sclera}"/>'
        )
        parts.append(
            f'<circle cx="{cx + lx:.1f}" cy="{ey + ly * 0.4:.1f}" r="{2.05 * fs:.2f}" fill="{ink}"/>'
        )
        parts.append(
            f'<circle cx="{cx + lx - 0.8 * fs:.1f}" cy="{ey + ly * 0.4 - 0.75 * fs:.1f}" r="{0.55 * fs:.2f}" fill="#fff" opacity="0.9"/>'
        )
    # Brows. Kindness is an arch with the outer end high — never inner-brow-up,
    # which reads as worry. Anger drops the inner end. Sadness drops the outer.
    by = hy - 9.0 * fs
    bw = 6.8 * fs
    peace = clamp(1.0 - brow_anger - brow_sad * 0.75, 0.0, 1.0)
    for sgn in (-1, 1):
        outer_x = hx + sgn * (ex + bw * 0.15)
        inner_x = hx + sgn * (ex - bw * 0.9)
        # Peace: a soft arch, outer end a little high. Not angled down at the nose.
        y_outer = by + brow_sad * 3.6 * fs - peace * 1.1 * fs
        y_inner = by + 0.4 * fs + brow_anger * 4.4 * fs - brow_sad * 1.4 * fs - peace * 0.5 * fs
        mid_x = (outer_x + inner_x) / 2
        mid_y = min(y_outer, y_inner) - (0.8 + peace * 1.5) * fs
        parts.append(
            f'<path d="M {outer_x:.1f},{y_outer:.1f} Q {mid_x:.1f},{mid_y:.1f} {inner_x:.1f},{y_inner:.1f}" '
            f'fill="none" stroke="{ink}" stroke-width="{1.5 * fs:.2f}" stroke-linecap="round" opacity="0.78"/>'
        )
    # Mouth — wide enough that a frown and a kindness both read at a glance.
    my = hy + 9.0 * fs
    mw = 7.0 * fs
    # Positive smile bows the mouth down in the middle (corners up). Y grows downward.
    curve = smile * 9.0 * fs
    parts.append(
        f'<path d="M {hx - mw:.1f},{my:.1f} Q {hx:.1f},{my + curve:.1f} {hx + mw:.1f},{my:.1f}" '
        f'fill="none" stroke="{ink}" stroke-width="{1.5 * fs:.2f}" stroke-linecap="round" opacity="0.82"/>'
    )
    return "".join(parts)


def draw_person(cx, foot_y, scale, color, slump, lean, face_dir, arm, walk_swing, look, expression, extras=True):
    """
    face_dir: +1 faces screen-right (gesture arm is the right arm).
    arm: dict with keys pose in 0..1 for down->point->open, and point_amt, open_amt.
    look: look_x, look_y
    expression: eye_open, brow_anger, brow_sad, smile
    """
    lay = layout_body(cx, foot_y, scale, slump, lean)
    s = lay["s"]
    col = rgb(color)
    dark = rgb(ilerp(color, INK, 0.22))
    light = rgb(ilerp(color, (255, 250, 244), 0.22))
    parts = []

    # Legs (stable, not leaned)
    swing = walk_swing
    hip_l = (cx - 8.0 * s, lay["hip_y"] - 6 * s)
    hip_r = (cx + 8.0 * s, lay["hip_y"] - 6 * s)
    foot_l = (cx - 12.0 * s + swing, foot_y)
    foot_r = (cx + 12.0 * s - swing, foot_y)
    sw = 8.0 * s
    for (x0, y0), (x1, y1) in ((hip_l, foot_l), (hip_r, foot_r)):
        parts.append(
            f'<line x1="{x0:.1f}" y1="{y0:.1f}" x2="{x1:.1f}" y2="{y1:.1f}" '
            f'stroke="{dark}" stroke-width="{sw:.1f}" stroke-linecap="round"/>'
        )

    # Body capsule, then rotate via a group around the hip.
    # Drawn in unrotated space and wrapped so the gradient stays simple.
    body = capsule_path(cx, lay["body_top"], lay["body_bot"], lay["body_rx"])
    # Highlight ellipse in unrotated space
    hx = cx - 5 * s
    hy = lay["body_top"] + 18 * s
    parts.append(
        f'<g transform="rotate({lean:.2f},{cx:.2f},{lay["hip_y"]:.2f})">'
        f'<path d="{body}" fill="{col}" stroke="{dark}" stroke-width="{1.1 * s:.2f}" stroke-opacity="0.35"/>'
        f'<ellipse cx="{hx:.1f}" cy="{hy:.1f}" rx="{7.5 * s:.1f}" ry="{12 * s:.1f}" fill="#fff" opacity="0.10"/>'
        f'</g>'
    )

    # Arms
    point_amt = arm.get("point", 0.0)
    open_amt = arm.get("open", 0.0)
    down = (16.0 * s, 38.0 * s)
    point = (62.0 * s, 1.0 * s)
    offer = (46.0 * s, 22.0 * s)
    # Blend down -> point -> offer
    # point_amt and open_amt are independent crossfades from the hanging pose.
    def blend_pose():
        # Start at down, push toward point by point_amt, then toward offer by open_amt.
        x = lerp(down[0], point[0], point_amt)
        y = lerp(down[1], point[1], point_amt)
        x = lerp(x, offer[0], open_amt)
        y = lerp(y, offer[1], open_amt)
        bend = lerp(16.0 * s, 5.0 * s, point_amt)
        bend = lerp(bend, 24.0 * s, open_amt)
        return x, y, bend

    gx, gy, bend = blend_pose()
    # Gesture arm is toward face_dir. Other arm hangs, with a little life.
    hang_x, hang_y = 14.0 * s, 40.0 * s
    if face_dir >= 0:
        g_sh = lay["sh_r"]
        o_sh = lay["sh_l"]
        g_hand = (g_sh[0] + gx, g_sh[1] + gy)  # already in world? sh is rotated, gx is screen-right offset
        # gx is a screen-right distance. Good for face_dir > 0.
        o_hand = (o_sh[0] - hang_x, o_sh[1] + hang_y)
    else:
        g_sh = lay["sh_l"]
        o_sh = lay["sh_r"]
        g_hand = (g_sh[0] - gx, g_sh[1] + gy)
        o_hand = (o_sh[0] + hang_x, o_sh[1] + hang_y)

    def arm_line(sh, hand, bend_px, width):
        mx = (sh[0] + hand[0]) / 2
        my = (sh[1] + hand[1]) / 2 + bend_px
        return (
            f'<path d="M {sh[0]:.1f},{sh[1]:.1f} Q {mx:.1f},{my:.1f} {hand[0]:.1f},{hand[1]:.1f}" '
            f'fill="none" stroke="{col}" stroke-width="{width:.1f}" stroke-linecap="round"/>'
        )

    parts.append(arm_line(o_sh, o_hand, 14.0 * s, 6.2 * s))
    parts.append(arm_line(g_sh, g_hand, bend if face_dir else bend, 6.6 * s))

    # Hands
    if extras:
        # Pointing triangle fades out as the palm circle fades in.
        tri_op = clamp(point_amt * (1.0 - open_amt), 0, 1)
        palm_op = open_amt
        # A point is one finger, not a claw. Sharpness belongs to the
        # words in the air, which stay separate from the hand.
        if tri_op > 0.02:
            ang = 0 if face_dir > 0 else math.pi
            palm = g_hand
            tip = (palm[0] + math.cos(ang) * 16.0 * s, palm[1] + math.sin(ang) * 1.5 * s)
            tc = rgb(ilerp(color, RED, 0.45))
            parts.append(
                f'<circle cx="{palm[0]:.1f}" cy="{palm[1]:.1f}" r="{4.6 * s:.1f}" fill="{tc}" opacity="{tri_op:.3f}"/>'
            )
            parts.append(
                f'<line x1="{palm[0]:.1f}" y1="{palm[1]:.1f}" x2="{tip[0]:.1f}" y2="{tip[1]:.1f}" '
                f'stroke="{tc}" stroke-width="{3.4 * s:.2f}" stroke-linecap="round" opacity="{tri_op:.3f}"/>'
            )
        if palm_op > 0.35:
            parts.append(
                f'<circle cx="{g_hand[0]:.1f}" cy="{g_hand[1]:.1f}" r="{7.2 * s:.1f}" fill="{col}" '
                f'stroke="{rgb(GOLD)}" stroke-width="{1.2 * s:.2f}" stroke-opacity="{0.7 * palm_op:.2f}" opacity="{palm_op:.3f}"/>'
            )
        elif tri_op < 0.4:
            parts.append(
                f'<circle cx="{g_hand[0]:.1f}" cy="{g_hand[1]:.1f}" r="{4.4 * s:.1f}" fill="{col}"/>'
            )
        parts.append(
            f'<circle cx="{o_hand[0]:.1f}" cy="{o_hand[1]:.1f}" r="{4.0 * s:.1f}" fill="{col}"/>'
        )

    # Head
    hr = lay["head_r"]
    hx, hy = lay["head"]
    parts.append(
        f'<circle cx="{hx:.1f}" cy="{hy:.1f}" r="{hr:.1f}" fill="{light}" stroke="{dark}" stroke-width="{1.05 * s:.2f}" stroke-opacity="0.28"/>'
    )
    # Soft cheek volume
    parts.append(
        f'<ellipse cx="{hx - 6 * s:.1f}" cy="{hy - 6 * s:.1f}" rx="{8 * s:.1f}" ry="{6 * s:.1f}" fill="#fff" opacity="0.12"/>'
    )
    if extras:
        parts.append(
            face_marks(
                lay["head"],
                hr,
                look[0] * face_dir if False else look[0],
                look[1],
                expression[0],
                expression[1],
                expression[2],
                expression[3],
                s,
            )
        )
    else:
        # Distant people: two quiet eyes, enough to be a person.
        ink = rgb(INK)
        for sgn in (-1, 1):
            parts.append(
                f'<circle cx="{hx + sgn * 5.5 * s:.1f}" cy="{hy - 1 * s:.1f}" r="{1.5 * s:.2f}" fill="{ink}" opacity="0.75"/>'
            )

    return "".join(parts), lay, g_hand


def burden(x, y, scale, seen, lift):
    """A heavy stone on the shoulders. Dark and wide, so it reads against
    the night, then rises and rounds into light. Never a halo.
    """
    s = scale
    if lift > 0.9:
        return ""
    fade = 1.0 - smooth(interval(lift, 0.45, 0.88))
    rise = ease_out(lift) * 86 * s
    # A boulder, round and heavy, sitting ON them — not a ring around them.
    rx = lerp(36, 14, lift) * s
    ry = lerp(32, 14, lift) * s
    yy = y - rise
    dark_op = ((1.0 - lift) ** 1.1) * fade
    parts = []
    if dark_op > 0.04:
        parts.append(
            f'<ellipse cx="{x:.1f}" cy="{yy + 3:.1f}" rx="{rx:.1f}" ry="{ry:.1f}" fill="#161222" opacity="{0.96 * dark_op:.3f}"/>'
        )
        # A second lobe so it reads as a stone, not a perfect halo-circle.
        parts.append(
            f'<ellipse cx="{x + 10 * s:.1f}" cy="{yy - 6 * s:.1f}" rx="{rx * 0.62:.1f}" ry="{ry * 0.58:.1f}" '
            f'fill="#1c1730" opacity="{0.9 * dark_op:.3f}"/>'
        )
        # Moonlight on the crown, shade in the belly — it has mass.
        parts.append(
            f'<ellipse cx="{x - rx * 0.15:.1f}" cy="{yy - ry * 0.28:.1f}" rx="{rx * 0.48:.1f}" ry="{ry * 0.32:.1f}" '
            f'fill="#c9d2ea" opacity="{0.16 * dark_op:.3f}"/>'
        )
        parts.append(
            f'<ellipse cx="{x:.1f}" cy="{yy + ry * 0.35:.1f}" rx="{rx * 0.62:.1f}" ry="{ry * 0.28:.1f}" '
            f'fill="#07060e" opacity="{0.28 * dark_op:.3f}"/>'
        )
    # The light inside, dim until someone looks, then it is what remains.
    inner = lerp(0.18, 0.7, seen)
    inner = lerp(inner, 1.0, lift)
    ir = lerp(6.5, 12.0, max(seen * 0.5, lift)) * s
    ic = ilerp((170, 176, 196), GOLD, max(seen * 0.55, lift))
    parts.append(
        f'<circle cx="{x:.1f}" cy="{yy:.1f}" r="{ir * 2.2:.1f}" fill="{rgb(ic)}" '
        f'opacity="{(0.10 + inner * 0.22) * fade:.3f}" filter="url(#glowsm)"/>'
    )
    parts.append(
        f'<circle cx="{x:.1f}" cy="{yy:.1f}" r="{ir:.1f}" fill="{rgb(ic)}" opacity="{(0.28 + inner * 0.6) * fade:.3f}"/>'
    )
    # When the stone is seen, warm light sits on it — illumination, not a ring.
    if seen > 0.05 and lift < 0.8:
        parts.append(
            f'<ellipse cx="{x:.1f}" cy="{yy:.1f}" rx="{rx * 0.8:.1f}" ry="{ry * 0.7:.1f}" '
            f'fill="{rgb(GOLD)}" opacity="{0.10 * seen * (1 - lift):.3f}" filter="url(#glowsm)"/>'
        )
    return "".join(parts)


def shard_polygon(x, y, ang, length, width, color, opacity):
    tip = (x + math.cos(ang) * length, y + math.sin(ang) * length)
    b1 = (x + math.cos(ang + 2.45) * width, y + math.sin(ang + 2.45) * width)
    b2 = (x + math.cos(ang - 2.45) * width, y + math.sin(ang - 2.45) * width)
    return (
        f'<polygon points="{tip[0]:.1f},{tip[1]:.1f} {b1[0]:.1f},{b1[1]:.1f} {b2[0]:.1f},{b2[1]:.1f}" '
        f'fill="{color}" opacity="{opacity:.3f}"/>'
    )


def build_svg(t):
    st = scene(t)
    dawn = st["dawn"]
    cam = camera(t)
    cx, cy, z = cam

    sky_top = rgb(ilerp(SKY_TOP_0, SKY_TOP_1, dawn))
    sky_mid = rgb(ilerp(SKY_MID_0, SKY_MID_1, dawn))
    sky_hor = rgb(ilerp(SKY_HOR_0, SKY_HOR_1, dawn))
    gnd = rgb(ilerp(GND_0, GND_1, dawn))
    gnd_edge = rgb(ilerp(GND_EDGE_0, GND_EDGE_1, dawn))
    far = rgb(ilerp(FAR_0, FAR_1, dawn * 0.85))
    far2 = rgb(ilerp((18, 26, 52), (120, 78, 96), dawn * 0.7))

    o = []
    o.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">'
    )
    o.append(
        "<defs>"
        '<linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0%" stop-color="{sky_top}"/>'
        f'<stop offset="52%" stop-color="{sky_mid}"/>'
        f'<stop offset="100%" stop-color="{sky_hor}"/>'
        "</linearGradient>"
        '<linearGradient id="gnd" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0%" stop-color="{gnd_edge}"/>'
        f'<stop offset="22%" stop-color="{gnd}"/>'
        f'<stop offset="100%" stop-color="{rgb(ilerp(GND_0, (24, 18, 28), dawn))}"/>'
        "</linearGradient>"
        '<radialGradient id="horz" cx="50%" cy="50%" r="50%">'
        '<stop offset="0%" stop-color="#ffb27a" stop-opacity="0.95"/>'
        '<stop offset="45%" stop-color="#e88878" stop-opacity="0.35"/>'
        '<stop offset="100%" stop-color="#e88878" stop-opacity="0"/>'
        "</radialGradient>"
        '<radialGradient id="pool" cx="50%" cy="50%" r="50%">'
        '<stop offset="0%" stop-color="#ffd7a0" stop-opacity="0.55"/>'
        '<stop offset="60%" stop-color="#ffb080" stop-opacity="0.16"/>'
        '<stop offset="100%" stop-color="#ffb080" stop-opacity="0"/>'
        "</radialGradient>"
        '<radialGradient id="vig" cx="50%" cy="45%" r="72%">'
        f'<stop offset="0%" stop-color="#000" stop-opacity="0"/>'
        f'<stop offset="58%" stop-color="#000" stop-opacity="0"/>'
        f'<stop offset="100%" stop-color="#000" stop-opacity="{lerp(0.62, 0.38, dawn):.3f}"/>'
        "</radialGradient>"
        '<linearGradient id="scrim" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0%" stop-color="#070910" stop-opacity="0"/>'
        '<stop offset="28%" stop-color="#070910" stop-opacity="0.18"/>'
        '<stop offset="100%" stop-color="#070910" stop-opacity="0.82"/>'
        "</linearGradient>"
        '<filter id="glow" x="-80%" y="-80%" width="260%" height="260%">'
        '<feGaussianBlur stdDeviation="7"/>'
        "</filter>"
        '<filter id="glowsm" x="-80%" y="-80%" width="260%" height="260%">'
        '<feGaussianBlur stdDeviation="3.5"/>'
        "</filter>"
        '<filter id="ts" x="-15%" y="-40%" width="130%" height="200%">'
        '<feDropShadow dx="0" dy="1.4" stdDeviation="2.0" flood-color="#05060c" flood-opacity="0.6"/>'
        "</filter>"
        '<mask id="moon">'
        '<rect width="100%" height="100%" fill="black"/>'
        '<circle cx="1092" cy="104" r="27" fill="white"/>'
        '<circle cx="1104" cy="96" r="22" fill="black"/>'
        "</mask>"
        "</defs>"
    )

    # Sky (screen space)
    o.append(f'<rect width="{W}" height="{H}" fill="url(#sky)"/>')
    # Horizon glow sits in the world so it warms the ground line, but a screen-space
    # version keeps the grade stable. Draw it in world group below.

    # Stars and moon, fixed in the sky (infinity).
    star_fade = 1.0 - dawn * 0.88
    if star_fade > 0.03:
        for i in range(16):
            sx = 40 + rand(i, 4) * 1200
            sy = 24 + rand(i, 5) * 250
            r = 0.7 + rand(i, 6) * 1.5
            tw = 0.55 + 0.45 * math.sin(t * 1.7 + i * 1.3)
            o.append(
                f'<circle cx="{sx:.1f}" cy="{sy:.1f}" r="{r:.2f}" fill="#eef2ff" opacity="{star_fade * tw * 0.85:.3f}"/>'
            )
        # A few cross-shaped brighter stars
        for i in range(4):
            sx = 80 + rand(i, 8) * 1080
            sy = 36 + rand(i, 9) * 180
            r = 3.2 + rand(i, 10) * 2.2
            op = star_fade * (0.35 + 0.25 * math.sin(t * 1.2 + i))
            o.append(
                f'<path d="M {sx:.1f},{sy - r:.1f} Q {sx:.1f},{sy:.1f} {sx + r:.1f},{sy:.1f} '
                f'Q {sx:.1f},{sy:.1f} {sx:.1f},{sy + r:.1f} Q {sx:.1f},{sy:.1f} {sx - r:.1f},{sy:.1f} '
                f'Q {sx:.1f},{sy:.1f} {sx:.1f},{sy - r:.1f} Z" fill="#f7f4ff" opacity="{op:.3f}"/>'
            )
    moon_op = lerp(0.92, 0.08, dawn)
    o.append(
        f'<circle cx="1092" cy="104" r="27" fill="#f6f1e6" opacity="{moon_op:.3f}" mask="url(#moon)"/>'
    )

    # World
    o.append(
        f'<g transform="translate({W / 2:.1f},{H / 2:.1f}) scale({z:.4f}) translate({-cx:.2f},{-cy:.2f})">'
    )

    # Far soft hills — rounded, never sharp. Sharpness is reserved for harm.
    o.append(f'<ellipse cx="380" cy="500" rx="460" ry="150" fill="{far}"/>')
    o.append(f'<ellipse cx="980" cy="512" rx="500" ry="160" fill="{far2}"/>')
    o.append(
        f'<ellipse cx="660" cy="488" rx="240" ry="70" fill="{rgb(ilerp(FAR_0, (160, 110, 110), dawn * 0.55))}" opacity="0.85"/>'
    )

    # Horizon warmth behind the near hill
    if dawn > 0.01:
        o.append(
            f'<ellipse cx="650" cy="520" rx="{520 + dawn * 80:.0f}" ry="{90 + dawn * 30:.0f}" '
            f'fill="url(#horz)" opacity="{dawn * 0.75:.3f}"/>'
        )

    # Near ground
    steps = 28
    x0, x1 = -180.0, 1500.0
    d = [f"M {x0:.1f},820", f"L {x0:.1f},{hill_y(x0):.1f}"]
    for i in range(1, steps + 1):
        x = x0 + (x1 - x0) * i / steps
        d.append(f"L {x:.1f},{hill_y(x):.1f}")
    d.append(f"L {x1:.1f},820 Z")
    o.append(f'<path d="{" ".join(d)}" fill="url(#gnd)"/>')
    # Thin warm lip on the hill crest
    lip = [f"M {x0:.1f},{hill_y(x0):.1f}"]
    for i in range(1, steps + 1):
        x = x0 + (x1 - x0) * i / steps
        lip.append(f"L {x:.1f},{hill_y(x):.1f}")
    o.append(
        f'<path d="{" ".join(lip)}" fill="none" stroke="{gnd_edge}" stroke-width="2.2" opacity="0.7"/>'
    )

    # Shared pool of light on the ground, born at the moment of contact.
    pool = st["lift"]
    if pool > 0.01:
        o.append(
            f'<ellipse cx="{(st["a_x"] + st["b_x"]) / 2:.1f}" cy="{hill_y(650) + 2:.1f}" '
            f'rx="{70 + pool * 150:.1f}" ry="{16 + pool * 22:.1f}" fill="url(#pool)" opacity="{pool * 0.9:.3f}"/>'
        )

    # Drifting motes
    for i in range(10):
        mx = (rand(i, 12) * 1500 + t * (6 + rand(i, 13) * 10)) % 1500 - 80
        my = 300 + rand(i, 14) * 240 + math.sin(t * 0.6 + i) * 8
        mo = 0.04 + dawn * 0.08
        o.append(
            f'<circle cx="{mx:.1f}" cy="{my:.1f}" r="{1.1 + rand(i, 15):.2f}" fill="#ffe6c0" opacity="{mo:.3f}"/>'
        )

    # --- figures ---
    a_color = ilerp(A_0, A_1, st["warmth_a"])
    a_color = ilerp(a_color, RED, st["anger"] * 0.26)
    b_color = ilerp(B_0, B_1, st["warmth_b"])

    # Expressions. Peace has to read as peace — soft brow, visible small smile.
    a_eye = kf(t, [(0, 0.78), (1.3, 0.66), (1.6, 0.52), (2.35, 1.0), (4.8, 0.8), (10, 0.74)])
    a_eye *= 1.0 - 0.88 * blink(t, 2.28)
    a_brow_a = st["anger"] * (1.0 - st["see"] * 0.85)
    a_brow_s = 0.0
    a_smile = kf(t, [(0, 0.05), (1.45, -0.9), (2.2, -0.15), (3.35, 0.45), (5.9, 0.78), (10, 0.8)])
    a_look_x = kf(t, [(0, 0.45), (1.2, 1.0), (10, 0.8)])
    a_look_y = kf(t, [(0, 0.15), (1.5, 0.05), (2.15, -0.15), (2.85, -0.55), (4.2, -0.05), (10, -0.08)])

    b_eye = kf(t, [(0, 0.36), (1.6, 0.34), (1.85, 0.55), (4.7, 0.4), (6.1, 0.8), (10, 0.76)])
    b_eye *= 1.0 - 0.8 * blink(t, 5.2)
    b_brow_a = 0.0
    b_brow_s = lerp(0.95, 0.0, st["lift"])
    b_smile = lerp(-0.85, 0.82, st["lift"])
    b_look_x = -0.85
    b_look_y = lerp(0.9, -0.12, st["lift"])

    swing = math.sin(t * 9.2) * 11.0 * st["walk_speed"]

    a_arm = {"point": st["anger"] * (1.0 - st["opened"]), "open": st["opened"]}
    # The gift is given. Arms come home. The ending is rest, not a pose.
    if t > 5.05:
        settle = smooth(interval(t, 5.15, 6.45))
        a_arm["open"] = lerp(a_arm["open"], 0.0, settle)
        a_arm["point"] = lerp(a_arm["point"], 0.0, settle)

    b_receive = smooth(interval(t, 4.75, 5.35)) * (1.0 - smooth(interval(t, 5.45, 6.4)))
    b_arm = {"point": 0.0, "open": b_receive * 0.55}

    # Shadows
    def shadow(x, fy, s, darkness, warmth):
        col = rgb(ilerp((10, 12, 24), (80, 40, 30), warmth))
        o.append(
            f'<ellipse cx="{x:.1f}" cy="{fy + 2:.1f}" rx="{22 * s + darkness * 8:.1f}" ry="{6.5 * s:.1f}" '
            f'fill="{col}" opacity="{0.28 + darkness * 0.12:.3f}"/>'
        )

    # Crowd (behind the pair). Fade in as the world widens.
    crowd_op = st["crowd"]
    lanterns = []  # collected and drawn in front later

    def wake_u(x, phase):
        # The wave waits until we can see them still carrying something.
        dist = abs(x - 656.0)
        t0 = 6.2 + dist * 0.00155 + phase * 0.04
        return smooth(interval(t, t0, t0 + 0.95))

    if crowd_op > 0.01:
        for i, (x, s, cool, warm, sl0, phase) in enumerate(CROWD):
            wu = wake_u(x, phase)
            col = ilerp(cool, warm, wu)
            sl = lerp(sl0, 0.08, wu)
            fy = hill_y(x)
            face = 1 if x < 650 else -1
            shadow(x, fy, s, (1 - wu) * 0.6, wu * dawn)
            # A small stone on each of them — the same burden, still unshared.
            lay_c = layout_body(x, fy, s, sl, 0)
            stone = (1.0 - wu)
            rx = max(11.0, 15.0 * s)
            ry = rx * 0.86
            wx = lay_c["head"][0]
            wy = lay_c["head"][1] - lay_c["head_r"] - ry - 4
            if stone > 0.04:
                o.append(
                    f'<ellipse cx="{wx:.1f}" cy="{wy:.1f}" rx="{rx:.1f}" ry="{ry:.1f}" '
                    f'fill="#1b1730" opacity="{0.92 * stone * crowd_op:.3f}"/>'
                )
                o.append(
                    f'<circle cx="{wx:.1f}" cy="{wy - 1:.1f}" r="{rx * 0.28:.1f}" fill="#d4d0e4" '
                    f'opacity="{0.4 * stone * crowd_op:.3f}"/>'
                )
            svg, _, _ = draw_person(
                x, fy, s, col, sl, face * -2.0 * (1 - wu), face,
                {"point": 0.0, "open": wu * 0.3},
                0.0,
                (face * 0.3, lerp(0.4, -0.1, wu)),
                (lerp(0.45, 0.8, wu), 0.0, lerp(0.5, 0.05, wu), lerp(-0.2, 0.3, wu)),
                extras=False,
            )
            o.append(f'<g opacity="{crowd_op:.3f}">{svg}</g>')
            if wu > 0.02:
                # Lantern rising from this person
                rise = ease_out(wu) * (70 + s * 40)
                bob = math.sin(t * 1.3 + phase) * 3.5 * smooth(interval(wu, 0.7, 1.0))
                lanterns.append((wx, wy - rise + bob, 5.5 * s + 3.5, wu * crowd_op, phase))

    # Main pair shadows
    shadow(st["a_x"], hill_y(st["a_x"]), 1.0, st["anger"] * 0.3, st["warmth_a"])
    shadow(st["b_x"], hill_y(st["b_x"]), 1.0, (1 - st["lift"]) * 0.55, st["warmth_b"])

    # B's burden — wide, heavy, unmistakable, sitting on the shoulders.
    b_foot = hill_y(st["b_x"])
    b_scale = lerp(0.95, 1.03, st["lift"])
    b_lay_preview = layout_body(st["b_x"], b_foot, b_scale, st["b_slump"], st["b_lean"])
    # Resting on the crown, almost all of the mass in the sky above the head.
    w_x = b_lay_preview["head"][0]
    w_y = b_lay_preview["head"][1] - b_lay_preview["head_r"] - 18 * b_scale

    # A's private ember position (chest), used as the source of shards and the gift.
    a_foot = hill_y(st["a_x"])

    # Draw B then A so A's reaching arm reads in front.
    b_svg, b_lay, b_hand = draw_person(
        st["b_x"], b_foot, b_scale, b_color, st["b_slump"], st["b_lean"], -1,
        b_arm, 0.0,
        (b_look_x, b_look_y),
        (b_eye, b_brow_a, b_brow_s, b_smile),
        extras=True,
    )
    o.append(b_svg)

    a_svg, a_lay, a_hand = draw_person(
        st["a_x"], a_foot, 1.02, a_color, st["a_slump"], st["a_lean"], 1,
        a_arm, swing,
        (a_look_x, a_look_y),
        (a_eye, a_brow_a, a_brow_s, a_smile),
        extras=True,
    )
    o.append(a_svg)
    # Stone drawn over the crown so it sits ON the person, not as a ring behind them.
    if st["lift"] < 0.92:
        o.append(burden(w_x, w_y, b_scale, st["see"], st["lift"]))

    # Ember / gift light. Continuous object: chest -> hand -> across to the weight.
    chest = a_lay["chest"]
    # Release moment
    release = 3.72
    arrive = 4.95
    hard_core = t >= 2.7
    if t < 2.7:
        ember_p = chest
        ember_r = 5.0 + st["anger"] * 4.0 + math.sin(t * 6.5) * st["anger"] * 0.8
        ember_col = RED
        ember_op = st["anger"] * 0.42
    elif t < release:
        u = smooth(interval(t, 2.75, release))
        ember_p = (lerp(chest[0], a_hand[0], u), lerp(chest[1], a_hand[1] - 6, u))
        ember_r = lerp(11.0, 13.5, u)
        ember_col = ilerp(RED, GOLD, u)
        ember_op = 0.9
    else:
        u = smoother(interval(t, release, arrive))
        p0 = a_hand
        # Target: the weight's heart
        p2 = (w_x, w_y)
        p1 = ((p0[0] + p2[0]) / 2, min(p0[1], p2[1]) - 62)
        ou = 1.0 - u
        ember_p = (
            ou * ou * p0[0] + 2 * ou * u * p1[0] + u * u * p2[0],
            ou * ou * p0[1] + 2 * ou * u * p1[1] + u * u * p2[1],
        )
        ember_r = lerp(13.5, 18.0, u)
        ember_col = GOLD
        ember_op = 1.0
        if t > arrive:
            # Absorbed into the lifting light; the lantern takes over.
            ember_op = 1.0 - smooth(interval(t, arrive, arrive + 0.35))

    if ember_op > 0.03:
        o.append(
            f'<circle cx="{ember_p[0]:.1f}" cy="{ember_p[1]:.1f}" r="{ember_r * 2.4:.1f}" '
            f'fill="{rgb(ember_col)}" opacity="{ember_op * 0.40:.3f}" filter="url(#glow)"/>'
        )
        if hard_core:
            o.append(
                f'<circle cx="{ember_p[0]:.1f}" cy="{ember_p[1]:.1f}" r="{ember_r:.1f}" '
                f'fill="{rgb(ilerp(ember_col, GOLD2, 0.55))}" opacity="{ember_op:.3f}"/>'
            )

    # Sharp words. They leave the mouth, stop in the open gap, and never land.
    if 0.95 < t < 4.0:
        origin = (a_lay["head"][0] + 16, a_lay["head"][1] + 6)
        # The open air between the fingertip and the other person.
        gap_x = (a_lay["chest"][0] + 86 + b_lay["chest"][0] - 36) * 0.5
        for i in range(4):
            delay = i * 0.07
            travel = ease_out(interval(t, 1.12 + delay, 1.85 + delay))
            dissolve = smooth(interval(t, 2.6 + delay * 0.35, 3.45 + delay * 0.25))
            if travel <= 0.01:
                continue
            y_spread = (i - 1.5) * 18
            x = lerp(origin[0] + 18, gap_x + (i - 1.5) * 7, travel)
            y = lerp(origin[1], a_lay["chest"][1] + y_spread, travel)
            ang = (i - 1.5) * 0.22 + math.sin(t * 1.4 + i) * 0.15
            sharp_op = (1.0 - dissolve) * clamp(travel * 3.5, 0, 1) * 0.92
            soft_op = dissolve * (1.0 - smooth(interval(t, 3.15, 3.85)))
            rise = dissolve * dissolve * 42
            if sharp_op > 0.03:
                col = rgb(ilerp((220, 96, 78), (255, 186, 130), i * 0.1))
                o.append(shard_polygon(x, y - rise * 0.1, ang, 9 + (i % 2) * 2, 4.6, col, sharp_op))
            if soft_op > 0.03:
                o.append(
                    f'<circle cx="{x:.1f}" cy="{y - rise:.1f}" r="{4.2 + i * 0.3:.1f}" '
                    f'fill="{rgb(GOLD)}" opacity="{soft_op:.3f}"/>'
                )

    # A brief ripple where the stone becomes light. It does not linger.
    if 4.88 < t < 5.35:
        burst_y = w_y - ease_out(st["lift"]) * 30
        for k, t0 in enumerate((4.9, 5.02)):
            u = interval(t, t0, t0 + 0.32)
            if 0 < u < 1:
                rr = 6 + ease_out(u) * (34 + k * 14)
                op = (1.0 - u) * 0.55
                o.append(
                    f'<circle cx="{w_x:.1f}" cy="{burst_y:.1f}" r="{rr:.1f}" fill="none" '
                    f'stroke="{rgb(GOLD2)}" stroke-width="{1.8 - u:.2f}" opacity="{op:.3f}"/>'
                )

    # Pause ripple at the moment of stopping the sharp thing
    if 2.05 < t < 2.55:
        u = interval(t, 2.06, 2.48)
        rr = 8 + ease_out(u) * 42
        op = (1.0 - u) * 0.4
        px, py = a_lay["head"]
        o.append(
            f'<circle cx="{px:.1f}" cy="{py:.1f}" r="{rr:.1f}" fill="none" '
            f'stroke="#f2efe8" stroke-width="1.5" opacity="{op:.3f}"/>'
        )

    # Lantern born from B's weight, and a smaller one from A's chest.
    def draw_lantern(x, y, r, op, phase):
        if op < 0.03:
            return
        bob_op = op
        o.append(
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r * 2.4:.1f}" fill="{rgb(GOLD)}" opacity="{bob_op * 0.35:.3f}" filter="url(#glow)"/>'
        )
        o.append(
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{rgb(GOLD2)}" opacity="{bob_op:.3f}"/>'
        )
        # tiny warm core
        o.append(
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r * 0.35:.1f}" fill="#fff" opacity="{bob_op * 0.8:.3f}"/>'
        )

    if st["lift"] > 0.35:
        # Continue upward from where the stone has already risen.
        risen = ease_out(min(st["lift"], 1.0)) * 70 * b_scale
        extra = ease_out(smooth(interval(st["lift"], 0.4, 1.0))) * 52
        bob = math.sin(t * 1.25) * 4.0 * smooth(interval(st["lift"], 0.7, 1))
        lantern_op = smooth(interval(st["lift"], 0.4, 0.82))
        draw_lantern(w_x, w_y - risen - extra + bob, 11.0, lantern_op, 0.0)
        rise2 = ease_out(smooth(interval(t, 5.2, 6.55))) * 100
        bob2 = math.sin(t * 1.4 + 1.2) * 3.5 * smooth(interval(t, 6.1, 6.9))
        draw_lantern(a_lay["chest"][0], a_lay["chest"][1] - rise2 + bob2, 7.2, smooth(interval(t, 5.2, 6.15)), 1.0)

    for lx, ly, lr, lop, ph in lanterns:
        draw_lantern(lx, ly, lr, lop, ph)

    # Gentle chest-glow once they are at peace, so the hold is alive.
    if st["warmth_a"] > 0.4:
        pulse = 0.75 + 0.25 * math.sin(t * 1.6)
        o.append(
            f'<circle cx="{a_lay["chest"][0]:.1f}" cy="{a_lay["chest"][1]:.1f}" r="{10 * pulse:.1f}" '
            f'fill="{rgb(GOLD)}" opacity="{st["warmth_a"] * 0.18:.3f}" filter="url(#glowsm)"/>'
        )
    if st["warmth_b"] > 0.4:
        pulse = 0.75 + 0.25 * math.sin(t * 1.6 + 0.8)
        o.append(
            f'<circle cx="{b_lay["chest"][0]:.1f}" cy="{b_lay["chest"][1]:.1f}" r="{10 * pulse:.1f}" '
            f'fill="{rgb(GOLD)}" opacity="{st["warmth_b"] * 0.18:.3f}" filter="url(#glowsm)"/>'
        )

    o.append("</g>")

    # Vignette, scrim, words — screen space, steady.
    o.append(f'<rect width="{W}" height="{H}" fill="url(#vig)"/>')

    scrim_op = max(st["text1"], st["text2"])
    if scrim_op > 0.01:
        o.append(
            f'<rect x="0" y="468" width="{W}" height="252" fill="url(#scrim)" opacity="{scrim_op:.3f}"/>'
        )

    if st["text1"] > 0.01:
        rise = (1.0 - st["text1"]) * 10
        o.append(
            f'<text x="640" y="{562 + rise:.1f}" text-anchor="middle" '
            f'font-family="Avenir Next, Helvetica Neue, Helvetica, sans-serif" '
            f'font-size="29" font-weight="400" letter-spacing="0.6" fill="#f6f1ea" '
            f'opacity="{st["text1"] * 0.96:.3f}" filter="url(#ts)">'
            f'Everyone is carrying something</text>'
        )
        o.append(
            f'<text x="640" y="{602 + rise:.1f}" text-anchor="middle" '
            f'font-family="Iowan Old Style, Georgia, serif" font-style="italic" '
            f'font-size="34" fill="#f3e6d4" opacity="{st["text1"]:.3f}" filter="url(#ts)">'
            f'you cannot see.</text>'
        )
    if st["dot"] > 0.01:
        pulse = 0.85 + 0.15 * math.sin(t * 2.2)
        o.append(
            f'<circle cx="640" cy="630" r="{11 * pulse:.1f}" fill="{rgb(GOLD)}" opacity="{st["dot"] * 0.28:.3f}" filter="url(#glowsm)"/>'
        )
        o.append(
            f'<circle cx="640" cy="630" r="{3.4 * pulse:.1f}" fill="{rgb(GOLD2)}" opacity="{st["dot"]:.3f}"/>'
        )
    if st["text2"] > 0.01:
        rise = (1.0 - st["text2"]) * 12
        o.append(
            f'<text x="640" y="{688 + rise:.1f}" text-anchor="middle" '
            f'font-family="Iowan Old Style, Georgia, serif" font-style="italic" '
            f'font-size="58" fill="#ffe6bc" opacity="{st["text2"]:.3f}" filter="url(#ts)">'
            f'Be gentle.</text>'
        )

    fade = 1.0 - st["fade"]
    if fade > 0.01:
        o.append(f'<rect width="{W}" height="{H}" fill="#07080e" opacity="{fade:.3f}"/>')

    o.append("</svg>")
    return "".join(o)


def rasterize(svg, png_path):
    png_path = str(png_path)
    r = subprocess.run(
        ["rsvg-convert", "-w", str(W), "-h", str(H), "-o", png_path],
        input=svg.encode("utf-8"),
        capture_output=True,
    )
    if r.returncode != 0:
        err = Path(png_path).with_suffix(".svg")
        err.write_text(svg)
        raise RuntimeError(f"rsvg failed: {r.stderr.decode()[:400]} (svg at {err})")


def render_preview(t, jpg_path, width=880):
    jpg_path = Path(jpg_path)
    jpg_path.parent.mkdir(parents=True, exist_ok=True)
    png = jpg_path.with_suffix(".png")
    rasterize(build_svg(t), png)
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(png), "-vf", f"scale={width}:-1", "-q:v", "3", str(jpg_path)],
        check=True,
        capture_output=True,
    )
    png.unlink(missing_ok=True)
    print(jpg_path)


def render_one(i):
    svg = build_svg(i / FPS)
    path = FRAMES / f"{i:04d}.png"
    rasterize(svg, path)
    return i


def render_all():
    from concurrent.futures import ProcessPoolExecutor

    FRAMES.mkdir(parents=True, exist_ok=True)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    # Clear old frames
    for p in FRAMES.glob("*.png"):
        p.unlink()
    print(f"rendering {NFRAMES} frames...")
    done = 0
    with ProcessPoolExecutor(max_workers=8) as ex:
        for i in ex.map(render_one, range(NFRAMES), chunksize=2):
            done += 1
            if done % 24 == 0 or done == NFRAMES:
                print(f"  {done}/{NFRAMES}")
    print("encoding...")
    subprocess.run(
        [
            "ffmpeg", "-y",
            "-framerate", str(FPS),
            "-i", str(FRAMES / "%04d.png"),
            "-c:v", "libx264",
            "-tune", "animation",
            "-pix_fmt", "yuv420p",
            "-crf", "18",
            "-preset", "slow",
            "-movflags", "+faststart",
            str(OUT),
        ],
        check=True,
    )
    print(OUT)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "preview":
        render_preview(float(sys.argv[2]), sys.argv[3])
    elif len(sys.argv) > 1 and sys.argv[1] == "previews":
        times = [float(x) for x in sys.argv[2:]]
        for t in times:
            render_preview(t, TMP / f"preview-{t:.2f}.jpg")
    else:
        render_all()
