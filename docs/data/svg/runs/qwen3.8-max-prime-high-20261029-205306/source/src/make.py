#!/usr/bin/env python3
"""THE SHARED BREATH -- a breathing guide for everyone, everywhere.

One parametric scene, two outputs:
  * an animated, self-contained SVG (SMIL, loops every 10 s), and
  * the exact same scene sampled per-frame and rasterised into an MP4.

The piece: a warm sphere of light swells for five seconds and settles for five
-- coherent breathing, six breaths a minute, the rhythm that steadies a heart.
Around it, a ring of small lights: one for each of us, pulsing with the same
breath, the wave passing slowly round the world. The caption states the plain,
true fact the circle is made of: every person on Earth is breathing right now.

Usage:
  python3 make.py svg   OUT.svg
  python3 make.py still OUT.svg [t]
  python3 make.py frame OUT.svg t
"""
import math
import random
import sys

import font

PERIOD = 10.0          # one full breath: 5 s in, 5 s out
W = H = 1200.0
CX, CY = 600.0, 572.0
R0 = 182.0             # orb radius at full inhale
RMIN = 0.72            # scale at full exhale
RING_R = 366.0
N_DOTS = 120
N_STARS = 120
BASE_T = 3.6           # value used for the static (non-animating) fallback

TAU = math.tau


# ---------------------------------------------------------------- timelines
def s_of(t):
    """Breath curve: 0 at empty, 1 at full, smooth at both ends."""
    return 0.5 * (1.0 - math.cos(TAU * (t % PERIOD) / PERIOD))


def scale_of(t):
    return RMIN + (1.0 - RMIN) * s_of(t)


def _smooth(u):
    u = min(1.0, max(0.0, u))
    return u * u * (3.0 - 2.0 * u)


def phase_in(t):
    """Opacity of the word IN (OUT is its complement)."""
    t = t % PERIOD
    if 0.2 <= t <= 4.8:
        return 1.0
    if 4.8 < t < 5.2:
        return 1.0 - _smooth((t - 4.8) / 0.4)
    if 5.2 <= t <= 9.8:
        return 0.0
    if t > 9.8:
        return _smooth((t - 9.8) / 0.4)
    return _smooth((t + 0.2) / 0.4)


def phase_out(t):
    return 1.0 - phase_in(t)


def dot_b(i, t):
    """Brightness of person-light i: mostly in unison, with a slow wave
    travelling once around the ring per breath."""
    delay = (i / N_DOTS) * PERIOD
    return 0.50 * s_of(t) + 0.50 * s_of(t - delay)


def star_op(k, t):
    base, per, ph = STARS[k]
    return base * (0.55 + 0.45 * math.sin(TAU * t / per + ph))


_rnd = random.Random(20261029)
STARS = []
while len(STARS) < N_STARS:
    x = _rnd.uniform(0, W)
    y = _rnd.uniform(0, H)
    d = math.hypot(x - CX, y - CY)
    vis = min(1.0, max(0.12, (d - 240.0) / 260.0))
    STARS.append((_rnd.uniform(0.22, 0.80) * vis,
                  _rnd.choice((2.5, 5.0, 10.0)),
                  _rnd.uniform(0, TAU)))
STAR_XY = []
_rnd2 = random.Random(77)
while len(STAR_XY) < N_STARS:
    STAR_XY.append((_rnd2.uniform(0, W), _rnd2.uniform(0, H)))
STAR_R = [_rnd2.uniform(0.7, 2.0) for _ in range(N_STARS)]


# ------------------------------------------------------------------ emitter
class E:
    """Emits an attribute either as a fixed value or as a SMIL timeline."""

    def __init__(self, animated, t=0.0, n=24):
        self.animated = animated
        self.t = t
        self.n = n
        self.attrs = []
        self.anims = []

    def a(self, name, fn, delay=0.0, n=None, fmt="%.4f", dur=PERIOD):
        n = n or self.n
        if self.animated:
            vals = ";".join(fmt % fn(i * dur / n) for i in range(n + 1))
            kt = ";".join("%.5f" % (i / n) for i in range(n + 1))
            self.attrs.append('%s="%s"' % (name, fmt % fn((BASE_T - delay) % dur)))
            self.anims.append(
                '<animate attributeName="%s" values="%s" keyTimes="%s" dur="%gs" '
                'begin="%gs" calcMode="linear" repeatCount="indefinite"/>'
                % (name, vals, kt, dur, delay - dur))
        else:
            self.attrs.append('%s="%s"' % (name, fmt % fn(self.t - delay)))
        return self

    def s(self, name, v, fmt=None):
        self.attrs.append('%s="%s"' % (name, (fmt % v) if fmt else v))
        return self

    def open(self, tag, close=False):
        a = " ".join(self.attrs)
        if close and not self.anims:
            return "<%s %s/>" % (tag, a)
        return "<%s %s>%s" % (tag, a, "".join(self.anims) + ("</%s>" % tag if close else ""))


# -------------------------------------------------------------------- scene
def scene(animated, t=0.0):
    e = lambda **kw: E(animated, t, **kw)
    p = []

    # ---- sky
    p.append('<rect width="%g" height="%g" fill="url(#sky)"/>' % (W, H))
    p.append('<circle cx="930" cy="210" r="520" fill="url(#neb1)"/>')
    p.append('<circle cx="210" cy="1010" r="560" fill="url(#neb2)"/>')

    # ---- stars
    for k in range(N_STARS):
        x, y = STAR_XY[k]
        el = e(n=12)
        el.s("cx", x, "%.1f").s("cy", y, "%.1f").s("r", STAR_R[k], "%.2f")
        el.s("fill", "#CFE3EE")
        el.a("opacity", lambda u, k=k: star_op(k, u))
        p.append(el.open("circle", close=True))

    p.append('<rect width="%g" height="%g" fill="url(#vig)"/>' % (W, H))

    # ---- the ring of everyone
    p.append('<circle cx="%g" cy="%g" r="%g" fill="none" stroke="#FFFFFF" '
             'stroke-opacity="0.05"/>' % (CX, CY, RING_R))
    for i in range(N_DOTS):
        ang = -math.pi / 2 + TAU * i / N_DOTS
        x = CX + RING_R * math.cos(ang)
        y = CY + RING_R * math.sin(ang)
        delay = (i / N_DOTS) * PERIOD
        g = e(n=16)
        g.a("opacity", lambda u, d=delay: 0.22 + 0.78 * (0.50 * s_of(u) + 0.50 * s_of(u - d)))
        p.append(g.open("g"))
        gl = e(n=16)
        gl.s("cx", x, "%.2f").s("cy", y, "%.2f").s("fill", "url(#dotglow)")
        gl.a("r", lambda u, d=delay: 3.5 + 9.0 * (0.50 * s_of(u) + 0.50 * s_of(u - d)))
        p.append(gl.open("circle", close=True))
        c = e(n=16)
        c.s("cx", x, "%.2f").s("cy", y, "%.2f").s("fill", "#FFD9A8")
        c.a("r", lambda u, d=delay: 1.2 + 1.8 * (0.50 * s_of(u) + 0.50 * s_of(u - d)))
        p.append(c.open("circle", close=True))
        p.append("</g>")

    # ---- the breath (orb), scaled about its centre
    p.append('<g transform="translate(%g,%g)">' % (CX, CY))
    grp = e(n=28)
    if animated:
        vals = ";".join("%.5f" % scale_of(i * PERIOD / 28) for i in range(29))
        kt = ";".join("%.5f" % (i / 28) for i in range(29))
        grp.attrs.append('transform="scale(%.5f)"' % scale_of(BASE_T))
        grp.anims.append('<animateTransform attributeName="transform" type="scale" '
                         'values="%s" keyTimes="%s" dur="%gs" calcMode="linear" '
                         'repeatCount="indefinite"/>' % (vals, kt, PERIOD))
    else:
        grp.attrs.append('transform="scale(%.5f)"' % scale_of(t))
    p.append(grp.open("g"))

    gl = e()
    gl.s("r", R0 * 1.78, "%.2f").s("fill", "url(#glow)")
    gl.a("opacity", lambda u: 0.55 + 0.45 * s_of(u))
    p.append(gl.open("circle", close=True))

    for r, col, base, wdt in ((R0 * 1.20, "#FFD9A8", 0.30, 1.6),
                              (R0 * 1.44, "#9FD9D2", 0.20, 1.2),
                              (R0 * 1.72, "#7FB8C8", 0.13, 1.0)):
        h = e()
        h.s("r", r, "%.2f").s("fill", "none").s("stroke", col).s("stroke-width", wdt, "%.2f")
        h.a("stroke-opacity", lambda u, b=base: b * (0.30 + 0.70 * s_of(u)))
        p.append(h.open("circle", close=True))

    p.append('<circle r="%g" fill="url(#orb)"/>' % R0)
    rim = e()
    rim.s("r", R0, "%.2f").s("fill", "none").s("stroke", "#FFEFD2").s("stroke-width", "1.5")
    rim.a("stroke-opacity", lambda u: 0.25 + 0.30 * s_of(u))
    p.append(rim.open("circle", close=True))
    for r, base in ((R0 * 0.42, 0.16), (R0 * 0.66, 0.10)):
        ir = e()
        ir.s("r", r, "%.2f").s("fill", "none").s("stroke", "#7A4030").s("stroke-width", "1")
        ir.a("stroke-opacity", lambda u, b=base: b * (0.4 + 0.6 * s_of(u)))
        p.append(ir.open("circle", close=True))
    p.append("</g></g>")

    # ---- words inside the orb
    p.append(font.text("BREATHE", 19, 0.34, CY - 64, CX, "#7A4238",
                       width_ratio=0.09, opacity=0.85))
    for word, fn in (("IN", phase_in), ("OUT", phase_out)):
        el = e(n=40)
        d, _ = font.path_d(word, 62, 0.18, CY + 26, CX)
        el.s("d", d).s("fill", "none").s("stroke", "#5E2F2B")
        el.s("stroke-width", 62 * 0.085, "%.3f")
        el.s("stroke-linecap", "round").s("stroke-linejoin", "round")
        el.a("stroke-opacity", lambda u, f=fn: 0.95 * f(u))
        p.append(el.open("path", close=True))

    # ---- titles and caption
    p.append(font.text("THE SHARED BREATH", 33, 0.26, 104, CX, "#F3E7D3",
                       width_ratio=0.075, opacity=0.95))
    p.append(font.text("5 SECONDS IN \u00b7 5 SECONDS OUT", 18, 0.22, 150, CX,
                       "#93A3B8", width_ratio=0.08, opacity=0.85))
    p.append(font.text("EVERY PERSON ON EARTH IS BREATHING RIGHT NOW.", 25, 0.12,
                       1030, CX, "#EAD9C0", width_ratio=0.08, opacity=0.92))
    p.append(font.text("YOU ARE NOT ALONE.", 17, 0.30, 1082, CX, "#8CA0B4",
                       width_ratio=0.08, opacity=0.80))
    return "".join(p)


DEFS = """
<defs>
<radialGradient id="sky" cx="0.5" cy="0.42" r="0.80">
<stop offset="0" stop-color="#101c2d"/><stop offset="0.45" stop-color="#0a1220"/>
<stop offset="1" stop-color="#04070d"/></radialGradient>
<radialGradient id="neb1" cx="0.5" cy="0.5" r="0.5">
<stop offset="0" stop-color="#12414a" stop-opacity="0.30"/>
<stop offset="0.6" stop-color="#0e2c3c" stop-opacity="0.12"/>
<stop offset="1" stop-color="#0e2c3c" stop-opacity="0"/></radialGradient>
<radialGradient id="neb2" cx="0.5" cy="0.5" r="0.5">
<stop offset="0" stop-color="#3a2140" stop-opacity="0.26"/>
<stop offset="0.6" stop-color="#241a34" stop-opacity="0.10"/>
<stop offset="1" stop-color="#241a34" stop-opacity="0"/></radialGradient>
<radialGradient id="vig" cx="0.5" cy="0.5" r="0.72">
<stop offset="0" stop-color="#000000" stop-opacity="0"/>
<stop offset="0.62" stop-color="#000000" stop-opacity="0"/>
<stop offset="1" stop-color="#000000" stop-opacity="0.50"/></radialGradient>
<radialGradient id="orb" cx="0.5" cy="0.5" r="0.5" fx="0.40" fy="0.34">
<stop offset="0" stop-color="#FFFCF2"/><stop offset="0.16" stop-color="#FFF1CD"/>
<stop offset="0.38" stop-color="#FFD79B"/><stop offset="0.60" stop-color="#F5AC74"/>
<stop offset="0.78" stop-color="#D97F5E"/><stop offset="0.90" stop-color="#A85450"/>
<stop offset="1" stop-color="#7C3A48"/></radialGradient>
<radialGradient id="glow" cx="0.5" cy="0.5" r="0.5">
<stop offset="0" stop-color="#FFCF96" stop-opacity="0.50"/>
<stop offset="0.30" stop-color="#F0A476" stop-opacity="0.22"/>
<stop offset="0.55" stop-color="#A66468" stop-opacity="0.10"/>
<stop offset="0.78" stop-color="#4E3A5C" stop-opacity="0.04"/>
<stop offset="1" stop-color="#000000" stop-opacity="0"/></radialGradient>
<radialGradient id="dotglow" cx="0.5" cy="0.5" r="0.5">
<stop offset="0" stop-color="#FFC98A" stop-opacity="0.55"/>
<stop offset="0.5" stop-color="#FFC98A" stop-opacity="0.18"/>
<stop offset="1" stop-color="#FFC98A" stop-opacity="0"/></radialGradient>
</defs>
"""

DESC = ("A breathing guide. A warm sphere of light swells for five seconds and "
        "settles for five; follow it and your breath slows to six a minute, the "
        "rhythm that steadies a heart. Around it a ring of small lights pulses "
        "with the same breath, one for each of us, the wave passing slowly round "
        "the world. The caption is the fact the circle is made of: every person "
        "on Earth is breathing right now.")


def document(animated, t=0.0):
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="1200" '
            'viewBox="0 0 1200 1200" role="img" aria-labelledby="t d">\n'
            '<title id="t">The Shared Breath</title>\n<desc id="d">%s</desc>\n'
            '%s%s</svg>\n' % (DESC, DEFS, scene(animated, t)))


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "svg":
        open(sys.argv[2], "w").write(document(True))
    elif cmd in ("still", "frame"):
        t = float(sys.argv[3]) if len(sys.argv) > 3 else BASE_T
        open(sys.argv[2], "w").write(document(False, t))
