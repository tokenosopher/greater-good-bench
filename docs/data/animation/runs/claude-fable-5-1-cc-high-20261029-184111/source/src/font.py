"""Minimal TrueType (.ttf/.ttc) parser + glyph rasteriser, standard library only."""
import struct
from math import floor, ceil


class Font:
    def __init__(self, path, face_index=0, want_name=None):
        with open(path, 'rb') as f:
            self.data = f.read()
        d = self.data
        offsets = [0]
        if d[:4] == b'ttcf':
            n = struct.unpack('>I', d[8:12])[0]
            offsets = list(struct.unpack('>%dI' % n, d[12:12 + 4 * n]))
        chosen = offsets[face_index]
        if want_name:
            for off in offsets:
                tables = self._read_tables(off)
                if want_name.lower() in self._full_name(tables).lower():
                    chosen = off
                    break
        self.tables = self._read_tables(chosen)
        t = self.tables
        head = t['head']
        self.upem = struct.unpack('>H', d[head + 18:head + 20])[0]
        self.loc_long = struct.unpack('>h', d[head + 50:head + 52])[0] == 1
        self.nglyphs = struct.unpack('>H', d[t['maxp'] + 4:t['maxp'] + 6])[0]
        hhea = t['hhea']
        self.ascent, self.descent = struct.unpack('>hh', d[hhea + 4:hhea + 8])
        self.nhm = struct.unpack('>H', d[hhea + 34:hhea + 36])[0]
        self.cmap = self._read_cmap()
        self._cache = {}

    def _read_tables(self, off):
        d = self.data
        n = struct.unpack('>H', d[off + 4:off + 6])[0]
        tables = {}
        for i in range(n):
            rec = off + 12 + 16 * i
            tag = d[rec:rec + 4].decode('latin1')
            toff, tlen = struct.unpack('>II', d[rec + 8:rec + 16])
            tables[tag] = toff
        return tables

    def _full_name(self, tables):
        d = self.data
        base = tables['name']
        count, strof = struct.unpack('>HH', d[base + 2:base + 6])
        out = ''
        for i in range(count):
            r = base + 6 + 12 * i
            pid, eid, lid, nid, ln, so = struct.unpack('>HHHHHH', d[r:r + 12])
            if nid == 4 and not out:
                s = d[base + strof + so:base + strof + so + ln]
                out = s.decode('utf-16-be' if pid in (0, 3) else 'mac-roman', 'replace')
        return out

    def _read_cmap(self):
        d = self.data
        base = self.tables['cmap']
        n = struct.unpack('>H', d[base + 2:base + 4])[0]
        best = None
        for i in range(n):
            pid, eid, off = struct.unpack('>HHI', d[base + 4 + 8 * i:base + 12 + 8 * i])
            fmt = struct.unpack('>H', d[base + off:base + off + 2])[0]
            if fmt in (4, 12) and (best is None or (pid == 3 and eid in (1, 10))):
                best = base + off
        m = {}
        fmt = struct.unpack('>H', d[best:best + 2])[0]
        if fmt == 4:
            segx2 = struct.unpack('>H', d[best + 6:best + 8])[0]
            seg = segx2 // 2
            ends = struct.unpack('>%dH' % seg, d[best + 14:best + 14 + segx2])
            starts = struct.unpack('>%dH' % seg, d[best + 16 + segx2:best + 16 + 2 * segx2])
            deltas = struct.unpack('>%dh' % seg, d[best + 16 + 2 * segx2:best + 16 + 3 * segx2])
            ro_base = best + 16 + 3 * segx2
            ros = struct.unpack('>%dH' % seg, d[ro_base:ro_base + segx2])
            for i in range(seg):
                for c in range(starts[i], min(ends[i], 0xFFFF) + 1):
                    if ros[i] == 0:
                        g = (c + deltas[i]) & 0xFFFF
                    else:
                        addr = ro_base + 2 * i + ros[i] + 2 * (c - starts[i])
                        g = struct.unpack('>H', d[addr:addr + 2])[0]
                        if g:
                            g = (g + deltas[i]) & 0xFFFF
                    if g:
                        m[c] = g
        else:
            ngroups = struct.unpack('>I', d[best + 12:best + 16])[0]
            for i in range(ngroups):
                s, e, g = struct.unpack('>III', d[best + 16 + 12 * i:best + 28 + 12 * i])
                for c in range(s, e + 1):
                    m[c] = g + c - s
        return m

    def gid(self, ch):
        return self.cmap.get(ord(ch), 0)

    def advance(self, g):
        d = self.data
        i = min(g, self.nhm - 1)
        return struct.unpack('>H', d[self.tables['hmtx'] + 4 * i:self.tables['hmtx'] + 4 * i + 2])[0]

    def _glyph_range(self, g):
        d = self.data
        loca = self.tables['loca']
        if self.loc_long:
            a, b = struct.unpack('>II', d[loca + 4 * g:loca + 4 * g + 8])
        else:
            a, b = struct.unpack('>HH', d[loca + 2 * g:loca + 2 * g + 4])
            a, b = a * 2, b * 2
        return self.tables['glyf'] + a, self.tables['glyf'] + b

    def outline(self, g, depth=0):
        """Return list of contours; each contour is list of (x, y, on_curve) in font units."""
        d = self.data
        a, b = self._glyph_range(g)
        if b <= a:
            return []
        nc = struct.unpack('>h', d[a:a + 2])[0]
        p = a + 10
        if nc >= 0:
            ends = struct.unpack('>%dH' % nc, d[p:p + 2 * nc])
            p += 2 * nc
            il = struct.unpack('>H', d[p:p + 2])[0]
            p += 2 + il
            npts = ends[-1] + 1 if nc else 0
            flags = []
            while len(flags) < npts:
                fl = d[p]; p += 1
                flags.append(fl)
                if fl & 8:
                    rep = d[p]; p += 1
                    flags.extend([fl] * rep)
            xs = []; v = 0
            for fl in flags:
                if fl & 2:
                    dx = d[p]; p += 1
                    v += dx if fl & 16 else -dx
                elif not fl & 16:
                    v += struct.unpack('>h', d[p:p + 2])[0]; p += 2
                xs.append(v)
            ys = []; v = 0
            for fl in flags:
                if fl & 4:
                    dy = d[p]; p += 1
                    v += dy if fl & 32 else -dy
                elif not fl & 32:
                    v += struct.unpack('>h', d[p:p + 2])[0]; p += 2
                ys.append(v)
            contours = []
            s = 0
            for e in ends:
                contours.append([(xs[i], ys[i], bool(flags[i] & 1)) for i in range(s, e + 1)])
                s = e + 1
            return contours
        # composite
        contours = []
        while True:
            flags, gi = struct.unpack('>HH', d[p:p + 4]); p += 4
            if flags & 1:
                a1, a2 = struct.unpack('>hh', d[p:p + 4]); p += 4
            else:
                a1, a2 = struct.unpack('>bb', d[p:p + 2]); p += 2
            sa = sd = 1.0; sb = sc = 0.0
            if flags & 8:
                sa = sd = struct.unpack('>h', d[p:p + 2])[0] / 16384; p += 2
            elif flags & 0x40:
                sa, sd = [v / 16384 for v in struct.unpack('>hh', d[p:p + 4])]; p += 4
            elif flags & 0x80:
                sa, sb, sc, sd = [v / 16384 for v in struct.unpack('>hhhh', d[p:p + 8])]; p += 8
            dx, dy = (a1, a2) if flags & 2 else (0, 0)
            if depth < 4:
                for c in self.outline(gi, depth + 1):
                    contours.append([(sa * x + sc * y + dx, sb * x + sd * y + dy, on) for x, y, on in c])
            if not flags & 0x20:
                break
        return contours

    def glyph_runs(self, g, px, S=4):
        """Rasterise glyph at px pixels/em. Returns (runs, adv_px) where runs is a list of
        (y, x0, x1, cov) with y measured downward from the baseline, cov in 0..1."""
        key = (g, px)
        if key in self._cache:
            return self._cache[key]
        scale = px / self.upem
        polys = []
        for c in self.outline(g):
            pts = [(x * scale, -y * scale, on) for x, y, on in c]
            if not pts:
                continue
            # ensure start on-curve
            if not pts[0][2]:
                if pts[-1][2]:
                    pts = [pts[-1]] + pts[:-1]
                else:
                    mx = (pts[0][0] + pts[-1][0]) / 2; my = (pts[0][1] + pts[-1][1]) / 2
                    pts = [(mx, my, True)] + pts
            poly = []
            n = len(pts)
            i = 0
            cur = pts[0]
            poly.append((cur[0], cur[1]))
            prev_off = None
            for k in range(1, n + 1):
                x, y, on = pts[k % n]
                if on:
                    if prev_off is None:
                        poly.append((x, y))
                    else:
                        poly.extend(_quad(poly[-1], prev_off, (x, y)))
                        prev_off = None
                else:
                    if prev_off is not None:
                        mid = ((prev_off[0] + x) / 2, (prev_off[1] + y) / 2)
                        poly.extend(_quad(poly[-1], prev_off, mid))
                    prev_off = (x, y)
            if prev_off is not None:
                poly.extend(_quad(poly[-1], prev_off, (pts[0][0], pts[0][1])))
            polys.append(poly)
        runs = rasterize_polys(polys, S)
        res = (runs, self.advance(g) * scale)
        self._cache[key] = res
        return res


def _quad(p0, p1, p2, steps=8):
    out = []
    for i in range(1, steps + 1):
        t = i / steps
        a = (1 - t) * (1 - t); b = 2 * (1 - t) * t; c = t * t
        out.append((a * p0[0] + b * p1[0] + c * p2[0], a * p0[1] + b * p1[1] + c * p2[1]))
    return out


def rasterize_polys(polys, S=4):
    """Non-zero winding scanline fill with S vertical subsamples and fractional
    horizontal coverage. Returns runs (y, x0, x1, cov)."""
    edges = []
    for poly in polys:
        n = len(poly)
        for i in range(n):
            x0, y0 = poly[i]; x1, y1 = poly[(i + 1) % n]
            if y0 == y1:
                continue
            edges.append((x0, y0, x1, y1))
    if not edges:
        return []
    ymin = floor(min(min(e[1], e[3]) for e in edges))
    ymax = ceil(max(max(e[1], e[3]) for e in edges))
    runs = []
    for y in range(ymin, ymax + 1):
        d = {}
        for s in range(S):
            ys = y + (s + 0.5) / S
            xs = []
            for x0, y0, x1, y1 in edges:
                if (y0 <= ys < y1) or (y1 <= ys < y0):
                    xs.append(((x0 + (ys - y0) * (x1 - x0) / (y1 - y0)), 1 if y1 > y0 else -1))
            if not xs:
                continue
            xs.sort()
            w = 0
            for i in range(len(xs) - 1):
                w += xs[i][1]
                if w != 0:
                    add_span(d, xs[i][0], xs[i + 1][0])
        if d:
            runs.extend(spans_to_runs(d, y, S))
    return runs


def add_span(d, xa, xb):
    if xb <= xa:
        return
    ia = floor(xa); ib = floor(xb)
    if ia == ib:
        c = xb - xa
        d[ia] = d.get(ia, 0.0) + c
        d[ia + 1] = d.get(ia + 1, 0.0) - c
    else:
        fa = 1.0 - (xa - ia); fb = xb - ib
        d[ia] = d.get(ia, 0.0) + fa
        d[ia + 1] = d.get(ia + 1, 0.0) + (1.0 - fa)
        d[ib] = d.get(ib, 0.0) + (fb - 1.0)
        d[ib + 1] = d.get(ib + 1, 0.0) - fb


def spans_to_runs(d, y, S):
    keys = sorted(d)
    cov = 0.0
    out = []
    for i in range(len(keys) - 1):
        cov += d[keys[i]]
        c = cov / S
        if c > 0.003:
            out.append((y, keys[i], keys[i + 1], min(c, 1.0)))
    return out
