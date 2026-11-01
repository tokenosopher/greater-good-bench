"""Tiny anti-aliased RGB rasteriser (standard library only)."""
import struct, zlib
from math import sqrt, floor, ceil
from font import add_span, spans_to_runs


def hexcol(s):
    s = s.lstrip('#')
    return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16))


def lerp_col(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


class Canvas:
    S = 4  # vertical subsamples

    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.bg = bytes(bg)
        self.buf = bytearray(self.bg * (w * h))

    def clear(self):
        self.buf[:] = self.bg * (self.w * self.h)

    # ---- core compositing ---------------------------------------------
    def _runs(self, runs, color, alpha, ox=0, oy=0):
        buf = self.buf; w = self.w; h = self.h
        cb = bytes(color)
        r, g, b = color
        for y, x0, x1, cov in runs:
            y += oy
            if y < 0 or y >= h:
                continue
            x0 += ox; x1 += ox
            if x0 < 0: x0 = 0
            if x1 > w: x1 = w
            if x1 <= x0:
                continue
            a = cov * alpha
            base = (y * w + x0) * 3
            n = x1 - x0
            if a >= 0.995:
                buf[base:base + 3 * n] = cb * n
            elif a > 0.003:
                for i in range(base, base + 3 * n, 3):
                    buf[i] += int((r - buf[i]) * a)
                    buf[i + 1] += int((g - buf[i + 1]) * a)
                    buf[i + 2] += int((b - buf[i + 2]) * a)

    def fill_convex(self, span_fn, ymin, ymax, color, alpha=1.0):
        S = self.S
        y0 = max(0, floor(ymin)); y1 = min(self.h - 1, ceil(ymax))
        for y in range(y0, y1 + 1):
            d = {}
            for s in range(S):
                sp = span_fn(y + (s + 0.5) / S)
                if sp:
                    add_span(d, sp[0], sp[1])
            if d:
                self._runs(spans_to_runs(d, y, S), color, alpha)

    # ---- shapes ---------------------------------------------------------
    def circle(self, cx, cy, r, color, alpha=1.0):
        def span(y):
            dy = y - cy
            if abs(dy) >= r:
                return None
            hw = sqrt(r * r - dy * dy)
            return (cx - hw, cx + hw)
        self.fill_convex(span, cy - r, cy + r, color, alpha)

    def ring(self, cx, cy, r, thick, color, alpha=1.0):
        """Ring drawn as a convex-per-row pair: approximate with two spans."""
        ri = r - thick
        S = self.S
        y0 = max(0, floor(cy - r)); y1 = min(self.h - 1, ceil(cy + r))
        for y in range(y0, y1 + 1):
            d = {}
            for s in range(S):
                ys = y + (s + 0.5) / S
                dy = ys - cy
                if abs(dy) >= r:
                    continue
                hw = sqrt(r * r - dy * dy)
                if abs(dy) < ri:
                    hi = sqrt(ri * ri - dy * dy)
                    add_span(d, cx - hw, cx - hi); add_span(d, cx + hi, cx + hw)
                else:
                    add_span(d, cx - hw, cx + hw)
            if d:
                self._runs(spans_to_runs(d, y, S), color, alpha)

    def rrect(self, x0, y0, x1, y1, r, color, alpha=1.0):
        r = min(r, (x1 - x0) / 2, (y1 - y0) / 2)
        def span(y):
            if y <= y0 or y >= y1:
                return None
            if y < y0 + r:
                dy = y0 + r - y
            elif y > y1 - r:
                dy = y - (y1 - r)
            else:
                return (x0, x1)
            hw = sqrt(max(0.0, r * r - dy * dy))
            return (x0 + r - hw, x1 - r + hw)
        self.fill_convex(span, y0, y1, color, alpha)

    def capsule(self, ax, ay, bx, by, r, color, alpha=1.0):
        dx, dy = bx - ax, by - ay
        L = sqrt(dx * dx + dy * dy)
        if L < 1e-6:
            return self.circle(ax, ay, r, color, alpha)
        ux, uy = dx / L, dy / L
        nx, ny = -uy, ux
        def span(y):
            c = []
            for sgn in (1, -1):
                ox, oy = ax + nx * r * sgn, ay + ny * r * sgn
                if abs(uy) > 1e-9:
                    t = (y - oy) / uy
                    if 0 <= t <= L:
                        c.append(ox + t * ux)
            for px, py in ((ax, ay), (bx, by)):
                d = y - py
                if abs(d) < r:
                    hw = sqrt(r * r - d * d)
                    c.append(px - hw); c.append(px + hw)
            if not c:
                return None
            return (min(c), max(c))
        self.fill_convex(span, min(ay, by) - r, max(ay, by) + r, color, alpha)

    def polygon(self, pts, color, alpha=1.0):
        """Convex polygon."""
        n = len(pts)
        def span(y):
            xs = []
            for i in range(n):
                x0, y0 = pts[i]; x1, y1 = pts[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
            if len(xs) < 2:
                return None
            return (min(xs), max(xs))
        self.fill_convex(span, min(p[1] for p in pts), max(p[1] for p in pts), color, alpha)

    def heart(self, cx, cy, size, color, alpha=1.0):
        r = size * 0.5
        self.circle(cx - r * 0.55, cy - r * 0.35, r * 0.62, color, alpha)
        self.circle(cx + r * 0.55, cy - r * 0.35, r * 0.62, color, alpha)
        self.polygon([(cx - r * 1.1, cy - r * 0.2), (cx + r * 1.1, cy - r * 0.2),
                      (cx, cy + r * 1.0)], color, alpha)

    # ---- text -----------------------------------------------------------
    def text(self, font, s, x, y, px, color, alpha=1.0, align='left', spacing=0.0):
        """Draw string with baseline at y. Returns width."""
        items = []
        cx = 0.0
        for ch in s:
            g = font.gid(ch)
            runs, adv = font.glyph_runs(g, px)
            items.append((runs, cx))
            cx += adv + spacing * px
        width = cx - spacing * px
        if align == 'center':
            x -= width / 2
        elif align == 'right':
            x -= width
        if alpha <= 0.003:
            return width
        for runs, off in items:
            self._runs(runs, color, alpha, int(round(x + off)), int(round(y)))
        return width

    def text_width(self, font, s, px, spacing=0.0):
        cx = 0.0
        for ch in s:
            cx += font.glyph_runs(font.gid(ch), px)[1] + spacing * px
        return cx - spacing * px

    # ---- output ---------------------------------------------------------
    def png_bytes(self):
        w, h = self.w, self.h
        raw = bytearray()
        row = w * 3
        for y in range(h):
            raw.append(0)
            raw += self.buf[y * row:(y + 1) * row]
        def chunk(t, d):
            c = struct.pack('>I', len(d)) + t + d
            return c + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
        return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0))
                + chunk(b'IDAT', zlib.compress(bytes(raw), 9)) + chunk(b'IEND', b''))
