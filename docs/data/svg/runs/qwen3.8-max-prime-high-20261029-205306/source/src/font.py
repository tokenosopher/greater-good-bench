"""A tiny geometric single-stroke vector font.

Glyphs are defined as polylines inside a cell where the cap line is y=0 and the
baseline is y=1, so they can be scaled to any size and stroked with round caps.
Because the glyphs are geometry (not a font file), the artwork renders
identically everywhere -- no font install, no text substitution, and it can be
rasterised for video with plain librsvg.
"""
import math


def _arc(cx, cy, rx, ry, a0, a1, n=30):
    """Points along an ellipse arc. Angles in degrees, y axis flipped (screen)."""
    pts = []
    for i in range(n + 1):
        a = math.radians(a0 + (a1 - a0) * i / n)
        pts.append((cx + rx * math.cos(a), cy - ry * math.sin(a)))
    return pts


def _ell(cx, cy, rx, ry, n=54):
    return _arc(cx, cy, rx, ry, 90, 450, n)


def _dot(x, y):
    # zero-length stroke + round linecap == a round dot
    return [(x, y), (x + 1e-4, y)]


G = {}  # char -> (advance width, [subpath, ...])


def _g(ch, w, *subs):
    G[ch] = (w, [list(map(tuple, s)) for s in subs])


# ------------------------------------------------------------------ letters
_g('A', 0.74, [(0, 1), (0.37, 0), (0.74, 1)], [(0.145, 0.64), (0.595, 0.64)])
_g('B', 0.66,
   [(0, 1), (0, 0), (0.34, 0)] + _arc(0.34, 0.255, 0.30, 0.255, 90, -90, 26) + [(0.34, 0.51), (0, 0.51)],
   [(0, 0.51), (0.37, 0.51)] + _arc(0.37, 0.755, 0.29, 0.245, 90, -90, 26) + [(0.37, 1), (0, 1)])
_g('C', 0.74, _arc(0.37, 0.5, 0.37, 0.5, 52, 308, 44))
_g('D', 0.72, [(0, 1), (0, 0), (0.30, 0)] + _arc(0.30, 0.5, 0.42, 0.5, 90, -90, 40) + [(0.30, 1), (0, 1)])
_g('E', 0.60, [(0.60, 0), (0, 0), (0, 1), (0.60, 1)], [(0, 0.505), (0.50, 0.505)])
_g('F', 0.58, [(0.58, 0), (0, 0), (0, 1)], [(0, 0.505), (0.48, 0.505)])
_g('G', 0.76, _arc(0.38, 0.5, 0.38, 0.5, 48, 312, 44) + [(0.663, 0.75), (0.663, 0.53), (0.44, 0.53)])
_g('H', 0.68, [(0, 0), (0, 1)], [(0.68, 0), (0.68, 1)], [(0, 0.5), (0.68, 0.5)])
_g('I', 0.10, [(0.05, 0), (0.05, 1)])
_g('J', 0.50, [(0.42, 0), (0.42, 0.70)] + _arc(0.235, 0.70, 0.185, 0.30, 0, -172, 24))
_g('K', 0.66, [(0, 0), (0, 1)], [(0.64, 0), (0.02, 0.545)], [(0.20, 0.40), (0.66, 1)])
_g('L', 0.56, [(0, 0), (0, 1), (0.56, 1)])
_g('M', 0.86, [(0, 1), (0, 0), (0.43, 0.66), (0.86, 0), (0.86, 1)])
_g('N', 0.70, [(0, 1), (0, 0), (0.70, 1), (0.70, 0)])
_g('O', 0.78, _ell(0.39, 0.5, 0.39, 0.5))
_g('P', 0.64, [(0, 1), (0, 0), (0.31, 0)] + _arc(0.31, 0.27, 0.33, 0.27, 90, -90, 28) + [(0.31, 0.54), (0, 0.54)])
_g('Q', 0.78, _ell(0.39, 0.5, 0.39, 0.5), [(0.48, 0.72), (0.82, 1.06)])
_g('R', 0.66,
   [(0, 1), (0, 0), (0.31, 0)] + _arc(0.31, 0.27, 0.33, 0.27, 90, -90, 28) + [(0.31, 0.54), (0, 0.54)],
   [(0.28, 0.54), (0.66, 1)])
_g('S', 0.62,
   _arc(0.31, 0.25, 0.29, 0.25, 28, 270, 32) +
   _arc(0.31, 0.75, 0.29, 0.25, 90, -152, 32))
_g('T', 0.64, [(0, 0), (0.64, 0)], [(0.32, 0), (0.32, 1)])
_g('U', 0.68, [(0, 0), (0, 0.52)] + _arc(0.34, 0.52, 0.34, 0.48, 180, 360, 30) + [(0.68, 0.52), (0.68, 0)])
_g('V', 0.72, [(0, 0), (0.36, 1), (0.72, 0)])
_g('W', 1.02, [(0, 0), (0.235, 1), (0.51, 0.30), (0.785, 1), (1.02, 0)])
_g('X', 0.68, [(0, 0), (0.68, 1)], [(0.68, 0), (0, 1)])
_g('Y', 0.70, [(0, 0), (0.35, 0.52), (0.70, 0)], [(0.35, 0.52), (0.35, 1)])
_g('Z', 0.62, [(0, 0), (0.62, 0), (0, 1), (0.62, 1)])

# ------------------------------------------------------------------- digits
_g('0', 0.66, _ell(0.33, 0.5, 0.33, 0.5))
_g('1', 0.34, [(0.02, 0.24), (0.20, 0.0), (0.20, 1.0)])
_g('2', 0.62, _arc(0.31, 0.32, 0.30, 0.32, 158, 22, 28) + [(0.02, 1.0), (0.60, 1.0)])
_g('3', 0.62,
   _arc(0.30, 0.26, 0.28, 0.26, 148, -58, 28) +
   _arc(0.30, 0.74, 0.29, 0.26, 58, -148, 28))
_g('4', 0.66, [(0.46, 1.0), (0.46, 0.0), (0.0, 0.68), (0.66, 0.68)])
_g('5', 0.62,
   [(0.58, 0.0), (0.08, 0.0)] + _arc(0.30, 0.66, 0.30, 0.34, 140, -140, 34))
_g('6', 0.62,
   _arc(0.33, 0.30, 0.30, 0.30, 66, 214, 28),
   _ell(0.31, 0.70, 0.30, 0.30))
_g('7', 0.62, [(0.02, 0.0), (0.62, 0.0), (0.24, 1.0)])
_g('8', 0.62, _ell(0.31, 0.27, 0.27, 0.27), _ell(0.31, 0.73, 0.30, 0.27))
_g('9', 0.62,
   _ell(0.31, 0.30, 0.30, 0.30),
   _arc(0.30, 0.70, 0.30, 0.30, -24, -176, 26))

# ------------------------------------------------------------- punctuation
_g(' ', 0.34)
_g('.', 0.16, _dot(0.08, 0.985))
_g(',', 0.20, [(0.115, 0.86), (0.045, 1.10)])
_g(':', 0.16, _dot(0.08, 0.30), _dot(0.08, 0.90))
_g('-', 0.46, [(0.06, 0.50), (0.40, 0.50)])
_g('\u2013', 0.62, [(0.04, 0.50), (0.58, 0.50)])          # en dash
_g('\u2014', 0.92, [(0.02, 0.50), (0.90, 0.50)])          # em dash
_g('\u00b7', 0.26, _dot(0.13, 0.47))                      # middle dot
_g('\u2019', 0.20, [(0.10, 0.02), (0.05, 0.24)])          # apostrophe
_g('!', 0.18, [(0.09, 0.0), (0.09, 0.66)], _dot(0.09, 0.985))
_g('?', 0.56,
   _arc(0.28, 0.28, 0.27, 0.28, 168, -22, 28) + [(0.28, 0.56), (0.28, 0.66)],
   _dot(0.28, 0.985))
_g('/', 0.50, [(0.02, 1.0), (0.48, 0.0)])
_g('(', 0.30, _arc(0.40, 0.5, 0.36, 0.62, 138, 222, 24))
_g(')', 0.30, _arc(-0.10, 0.5, 0.36, 0.62, -42, 42, 24))
G["'"] = G['\u2019']
G['`'] = G['\u2019']
G['\u2022'] = G['\u00b7']      # bullet -> middle dot


def measure(s, size, tracking=0.0):
    """Ink advance of a string in user units."""
    w = 0.0
    for ch in s:
        w += G[ch][0] * size + tracking * size
    return max(0.0, w - tracking * size)


def path_d(s, size, tracking, baseline_y, center_x, fmt="%.2f"):
    """Path data for a centred string. Returns (d, width)."""
    width = measure(s, size, tracking)
    x = center_x - width / 2.0
    parts = []
    for ch in s:
        adv, subs = G[ch]
        for sub in subs:
            cmds = []
            for i, (px, py) in enumerate(sub):
                X = fmt % (x + px * size)
                Y = fmt % (baseline_y - size * (1.0 - py))
                cmds.append(("M" if i == 0 else "L") + X + "," + Y)
            parts.append(" ".join(cmds))
        x += adv * size + tracking * size
    return " ".join(parts), width


def text(s, size, tracking, baseline_y, center_x, stroke, width_ratio=0.085,
         opacity=1.0, extra=""):
    """A centred stroked <path> element."""
    d, w = path_d(s, size, tracking, baseline_y, center_x)
    op = "" if opacity == 1.0 else f' stroke-opacity="{opacity:.3f}"'
    return (f'<path d="{d}" fill="none" stroke="{stroke}" '
            f'stroke-width="{size * width_ratio:.3f}" stroke-linecap="round" '
            f'stroke-linejoin="round"{op}{extra}/>')
