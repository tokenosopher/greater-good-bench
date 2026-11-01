"""Minimal TrueType/OpenType reader + antialiased rasteriser (stdlib only).

Supports: .ttf, .ttc collections, quadratic glyf outlines, cmap formats 4/12.
No hinting, no kerning -- just clean outlines rasterised with 4x vertical
supersampling, which is plenty for a glowing title card.
"""
import struct


class TTF:
    def __init__(self, path, index=0):
        with open(path, 'rb') as f:
            self.data = f.read()
        d = self.data
        tag = d[:4]
        if tag == b'ttcf':
            n = struct.unpack('>I', d[8:12])[0]
            offs = struct.unpack('>%dI' % n, d[12:12 + 4 * n])
            base = offs[index]
        else:
            base = 0
        numTables = struct.unpack('>H', d[base + 4:base + 6])[0]
        self.tables = {}
        for i in range(numTables):
            o = base + 12 + 16 * i
            tg = d[o:o + 4].decode('latin-1')
            off, ln = struct.unpack('>II', d[o + 8:o + 16])
            self.tables[tg] = (off, ln)

        head = self.tables['head'][0]
        self.unitsPerEm = struct.unpack('>H', d[head + 18:head + 20])[0]
        self.locaLong = struct.unpack('>h', d[head + 50:head + 52])[0] == 1

        maxp = self.tables['maxp'][0]
        self.numGlyphs = struct.unpack('>H', d[maxp + 4:maxp + 6])[0]

        hhea = self.tables['hhea'][0]
        self.numHMetrics = struct.unpack('>H', d[hhea + 34:hhea + 36])[0]
        self.ascender = struct.unpack('>h', d[hhea + 4:hhea + 6])[0]
        self.descender = struct.unpack('>h', d[hhea + 6:hhea + 8])[0]

        self._cmap = self._pick_cmap()
        self._cache = {}

    # ---------------------------------------------------------------- cmap
    def _pick_cmap(self):
        d = self.data
        cm = self.tables['cmap'][0]
        n = struct.unpack('>H', d[cm + 2:cm + 4])[0]
        best = None
        for i in range(n):
            pid, eid, off = struct.unpack('>HHI', d[cm + 4 + 8 * i:cm + 12 + 8 * i])
            sub = cm + off
            fmt = struct.unpack('>H', d[sub:sub + 2])[0]
            if fmt in (4, 12):
                score = (fmt == 12, pid == 3)
                if best is None or score > best[0]:
                    best = (score, fmt, sub)
        return (best[1], best[2])

    def glyph_index(self, ch):
        d = self.data
        fmt, sub = self._cmap
        cp = ord(ch)
        if fmt == 12:
            ngroups = struct.unpack('>I', d[sub + 12:sub + 16])[0]
            lo, hi = 0, ngroups - 1
            while lo <= hi:
                mid = (lo + hi) // 2
                o = sub + 16 + 12 * mid
                s, e, g = struct.unpack('>III', d[o:o + 12])
                if cp < s:
                    hi = mid - 1
                elif cp > e:
                    lo = mid + 1
                else:
                    return g + cp - s
            return 0
        # format 4
        segX2 = struct.unpack('>H', d[sub + 6:sub + 8])[0]
        seg = segX2 // 2
        endO = sub + 14
        startO = endO + segX2 + 2
        deltaO = startO + segX2
        rangeO = deltaO + segX2
        for i in range(seg):
            end = struct.unpack('>H', d[endO + 2 * i:endO + 2 * i + 2])[0]
            if cp <= end:
                start = struct.unpack('>H', d[startO + 2 * i:startO + 2 * i + 2])[0]
                if cp < start:
                    return 0
                delta = struct.unpack('>h', d[deltaO + 2 * i:deltaO + 2 * i + 2])[0]
                ro = struct.unpack('>H', d[rangeO + 2 * i:rangeO + 2 * i + 2])[0]
                if ro == 0:
                    return (cp + delta) & 0xFFFF
                gpos = rangeO + 2 * i + ro + 2 * (cp - start)
                g = struct.unpack('>H', d[gpos:gpos + 2])[0]
                return (g + delta) & 0xFFFF if g else 0
        return 0

    def advance(self, gid):
        d = self.data
        hmtx = self.tables['hmtx'][0]
        i = min(gid, self.numHMetrics - 1)
        return struct.unpack('>H', d[hmtx + 4 * i:hmtx + 4 * i + 2])[0]

    # ------------------------------------------------------------- outlines
    def contours(self, gid):
        """Return list of contours; each contour = list of (x, y, onCurve)."""
        if gid in self._cache:
            return self._cache[gid]
        d = self.data
        loca = self.tables['loca'][0]
        glyf = self.tables['glyf'][0]
        if self.locaLong:
            o0, o1 = struct.unpack('>II', d[loca + 4 * gid:loca + 4 * gid + 8])
        else:
            o0, o1 = struct.unpack('>HH', d[loca + 2 * gid:loca + 2 * gid + 4])
            o0, o1 = o0 * 2, o1 * 2
        if o1 <= o0:
            self._cache[gid] = []
            return []
        p = glyf + o0
        nc = struct.unpack('>h', d[p:p + 2])[0]
        if nc < 0:
            self._cache[gid] = []  # composite glyph: unused here
            return []
        ends = list(struct.unpack('>%dH' % nc, d[p + 10:p + 10 + 2 * nc]))
        q = p + 10 + 2 * nc
        ilen = struct.unpack('>H', d[q:q + 2])[0]
        q += 2 + ilen
        npts = ends[-1] + 1 if ends else 0
        flags = []
        while len(flags) < npts:
            f = d[q]
            q += 1
            flags.append(f)
            if f & 8:
                r = d[q]
                q += 1
                flags.extend([f] * r)
        xs = []
        v = 0
        for f in flags:
            if f & 2:
                dv = d[q]
                q += 1
                v += dv if f & 16 else -dv
            elif not f & 16:
                v += struct.unpack('>h', d[q:q + 2])[0]
                q += 2
            xs.append(v)
        ys = []
        v = 0
        for f in flags:
            if f & 4:
                dv = d[q]
                q += 1
                v += dv if f & 32 else -dv
            elif not f & 32:
                v += struct.unpack('>h', d[q:q + 2])[0]
                q += 2
            ys.append(v)
        out = []
        s = 0
        for e in ends:
            out.append([(xs[i], ys[i], bool(flags[i] & 1)) for i in range(s, e + 1)])
            s = e + 1
        self._cache[gid] = out
        return out


def flatten(contour, steps=6):
    """Quadratic contour -> polygon (list of (x,y))."""
    pts = contour
    n = len(pts)
    if n == 0:
        return []
    # start point: first on-curve, else midpoint of 0 and last
    if pts[0][2]:
        start = (pts[0][0], pts[0][1])
        idx0 = 1
    else:
        prev = pts[-1]
        start = ((pts[0][0] + prev[0]) / 2, (pts[0][1] + prev[1]) / 2)
        idx0 = 0
    poly = [start]
    cur = start
    i = idx0
    seq = pts[idx0:] + pts[:idx0]
    k = 0
    while k < len(seq):
        x, y, on = seq[k]
        if on:
            poly.append((x, y))
            cur = (x, y)
            k += 1
        else:
            nxt = seq[(k + 1) % len(seq)]
            if nxt[2]:
                end = (nxt[0], nxt[1])
                k += 2
            else:
                end = ((x + nxt[0]) / 2, (y + nxt[1]) / 2)
                k += 1
            for s in range(1, steps + 1):
                u = s / steps
                a = (1 - u) * (1 - u)
                b = 2 * u * (1 - u)
                c = u * u
                poly.append((a * cur[0] + b * x + c * end[0],
                             a * cur[1] + b * y + c * end[1]))
            cur = end
    return poly


def text_polygons(font, text, tracking=0.0):
    """Layout text; returns (polygons, width, bbox) in font units, y up."""
    polys = []
    pen = 0.0
    for ch in text:
        gid = font.glyph_index(ch)
        for c in font.contours(gid):
            polys.append([(x + pen, y) for x, y in flatten(c)])
        pen += font.advance(gid) + tracking
    if polys:
        xs = [x for p in polys for x, _ in p]
        ys = [y for p in polys for _, y in p]
        bbox = (min(xs), min(ys), max(xs), max(ys))
    else:
        bbox = (0, 0, 0, 0)
    return polys, pen, bbox


def rasterize(polys, w, h, ox, oy, scale, ss=4):
    """Rasterise polygons into a w*h coverage buffer (bytearray, 0..255).

    Font space is y-up. Pixel position of font origin = (ox, oy).
    scale = font units per pixel.
    """
    # bucket edges by yf range for speed
    edges = []
    for poly in polys:
        m = len(poly)
        for i in range(m):
            ax, ay = poly[i]
            bx, by = poly[(i + 1) % m]
            if ay != by:
                if ay < by:
                    edges.append((ay, by, ax, (bx - ax) / (by - ay)))
                else:
                    edges.append((by, ay, bx, (ax - bx) / (ay - by)))
    edges.sort(key=lambda e: -e[0])
    cov = [0.0] * (w * h)
    ne = len(edges)
    for py in range(h):
        for ssy in range(ss):
            ysamp = py + (ssy + 0.5) / ss
            yf = (oy - ysamp) * scale
            xs = []
            for e in edges:
                if e[1] > yf >= e[0]:
                    xs.append(e[2] + (yf - e[0]) * e[3])
            if len(xs) < 2:
                continue
            xs.sort()
            row = py * w
            for i in range(0, len(xs) - 1, 2):
                pa = xs[i] / scale + ox
                pb = xs[i + 1] / scale + ox
                if pb <= 0 or pa >= w:
                    continue
                if pa < 0:
                    pa = 0.0
                if pb > w:
                    pb = float(w)
                xa = int(pa)
                xb = int(pb)
                if xa == xb:
                    cov[row + xa] += pb - pa
                    continue
                cov[row + xa] += (xa + 1) - pa
                for x in range(xa + 1, xb):
                    cov[row + x] += 1.0
                if xb < w:
                    cov[row + xb] += pb - xb
    out = bytearray(w * h)
    k = 255.0 / ss
    for i, c in enumerate(cov):
        if c:
            v = int(c * k + 0.5)
            out[i] = 255 if v > 255 else v
    return out
