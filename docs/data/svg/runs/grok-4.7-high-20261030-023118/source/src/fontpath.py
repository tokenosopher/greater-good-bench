"""Minimal TrueType outliner: ASCII text to SVG paths. No dependencies."""

import struct
from dataclasses import dataclass


def _u16(data, off):
    return struct.unpack_from(">H", data, off)[0]


def _i16(data, off):
    return struct.unpack_from(">h", data, off)[0]


def _u32(data, off):
    return struct.unpack_from(">I", data, off)[0]


@dataclass
class Font:
    data: bytes
    tables: dict
    units: int
    glyph_id: callable
    num_glyphs: int
    loca: list
    advances: list
    lsbs: list
    kern: dict


def _tables(data, start):
    num = _u16(data, start + 4)
    tables = {}
    off = start + 12
    for _ in range(num):
        tag = data[off : off + 4].decode("latin1")
        tables[tag] = (_u32(data, off + 8), _u32(data, off + 12))
        off += 16
    return tables


def _slice(data, tables, tag):
    off, length = tables[tag]
    return data[off : off + length], off


def _parse_cmap(data, tables):
    raw, base = _slice(data, tables, "cmap")
    num = _u16(raw, 2)
    best = None
    for i in range(num):
        plat, enc, offset = struct.unpack_from(">HHI", raw, 4 + i * 8)
        fmt = _u16(raw, offset)
        # Prefer Unicode BMP or full, then Windows Unicode BMP.
        score = -1
        if plat == 0 and fmt in (4, 12):
            score = 3
        elif plat == 3 and enc == 1 and fmt == 4:
            score = 2
        elif plat == 3 and enc == 10 and fmt == 12:
            score = 3
        if score > (best[0] if best else -1):
            best = (score, fmt, offset)
    if not best:
        raise RuntimeError("no usable cmap")
    _, fmt, offset = best
    if fmt == 4:
        return _cmap4(raw, offset)
    if fmt == 12:
        return _cmap12(raw, offset)
    raise RuntimeError(f"unsupported cmap format {fmt}")


def _cmap4(raw, offset):
    seg_count = _u16(raw, offset + 6) // 2
    p = offset + 14
    end_count = struct.unpack_from(f">{seg_count}H", raw, p)
    p += seg_count * 2 + 2
    start_count = struct.unpack_from(f">{seg_count}H", raw, p)
    p += seg_count * 2
    id_delta = struct.unpack_from(f">{seg_count}h", raw, p)
    p += seg_count * 2
    range_off_pos = p
    id_range = struct.unpack_from(f">{seg_count}H", raw, p)

    def glyph_id(code):
        for i in range(seg_count):
            if start_count[i] <= code <= end_count[i]:
                if id_range[i] == 0:
                    return (code + id_delta[i]) & 0xFFFF
                pos = range_off_pos + i * 2 + id_range[i] + (code - start_count[i]) * 2
                g = _u16(raw, pos)
                if g == 0:
                    return 0
                return (g + id_delta[i]) & 0xFFFF
        return 0

    return glyph_id


def _cmap12(raw, offset):
    n = _u32(raw, offset + 12)
    groups = []
    p = offset + 16
    for _ in range(n):
        start, end, glyph = struct.unpack_from(">III", raw, p)
        groups.append((start, end, glyph))
        p += 12

    def glyph_id(code):
        lo, hi = 0, len(groups) - 1
        while lo <= hi:
            mid = (lo + hi) // 2
            start, end, glyph = groups[mid]
            if code < start:
                hi = mid - 1
            elif code > end:
                lo = mid + 1
            else:
                return glyph + (code - start)
        return 0

    return glyph_id


def _parse_loca(data, tables, units_head, num_glyphs):
    head, _ = _slice(data, tables, "head")
    loc_format = _i16(head, 50)
    loca_raw, _ = _slice(data, tables, "loca")
    loca = []
    if loc_format == 0:
        for i in range(num_glyphs + 1):
            loca.append(_u16(loca_raw, i * 2) * 2)
    else:
        for i in range(num_glyphs + 1):
            loca.append(_u32(loca_raw, i * 4))
    return loca


def _parse_hmtx(data, tables, num_glyphs):
    hhea, _ = _slice(data, tables, "hhea")
    n_metrics = _u16(hhea, 34)
    raw, _ = _slice(data, tables, "hmtx")
    advances = []
    lsbs = []
    for i in range(n_metrics):
        advances.append(_u16(raw, i * 4))
        lsbs.append(_i16(raw, i * 4 + 2))
    last = advances[-1]
    extra = num_glyphs - n_metrics
    p = n_metrics * 4
    for i in range(extra):
        advances.append(last)
        lsbs.append(_i16(raw, p + i * 2))
    return advances, lsbs


def _parse_kern(data, tables):
    kern = {}
    if "kern" not in tables:
        return kern
    raw, _ = _slice(data, tables, "kern")
    if len(raw) < 4:
        return kern
    version, n_tables = struct.unpack_from(">HH", raw, 0)
    p = 4
    for _ in range(n_tables):
        if p + 6 > len(raw):
            break
        st_ver, length, coverage = struct.unpack_from(">HHH", raw, p)
        fmt = coverage & 0xFF
        if fmt == 0 and length >= 14:
            n_pairs = _u16(raw, p + 6)
            q = p + 14
            for _ in range(n_pairs):
                left, right, value = struct.unpack_from(">HHh", raw, q)
                kern[(left, right)] = value
                q += 6
        p += length
    return kern


def load_font(path):
    data = open(path, "rb").read()
    if data[:4] == b"ttcf":
        raise RuntimeError("TTC not supported; pass a single-face TTF")
    tables = _tables(data, 0)
    head, _ = _slice(data, tables, "head")
    units = _u16(head, 18)
    maxp, _ = _slice(data, tables, "maxp")
    num_glyphs = _u16(maxp, 4)
    glyph_id = _parse_cmap(data, tables)
    loca = _parse_loca(data, tables, units, num_glyphs)
    advances, lsbs = _parse_hmtx(data, tables, num_glyphs)
    kern = _parse_kern(data, tables)
    return Font(data, tables, units, glyph_id, num_glyphs, loca, advances, lsbs, kern)


def _glyph_contours(font, gid):
    if gid <= 0 or gid >= len(font.loca) - 1:
        return []
    start = font.loca[gid]
    end = font.loca[gid + 1]
    if end <= start:
        return []
    glyf, gbase = _slice(font.data, font.tables, "glyf")
    # loca offsets are relative to glyf table
    p = start
    n_contours = _i16(glyf, p)
    if n_contours < 0:
        return _composite_contours(font, glyf, p)
    if n_contours == 0:
        return []
    p += 10
    ends = [ _u16(glyf, p + i * 2) for i in range(n_contours) ]
    p += n_contours * 2
    inst_len = _u16(glyf, p)
    p += 2 + inst_len
    n_points = ends[-1] + 1
    flags = []
    while len(flags) < n_points:
        f = glyf[p]
        p += 1
        flags.append(f)
        if f & 0x08:
            rep = glyf[p]
            p += 1
            flags.extend([f] * rep)
    xs = []
    x = 0
    for f in flags:
        if f & 0x02:
            dx = glyf[p]
            p += 1
            if not (f & 0x10):
                dx = -dx
        elif f & 0x10:
            dx = 0
        else:
            dx = _i16(glyf, p)
            p += 2
        x += dx
        xs.append(x)
    ys = []
    y = 0
    for f in flags:
        if f & 0x04:
            dy = glyf[p]
            p += 1
            if not (f & 0x20):
                dy = -dy
        elif f & 0x20:
            dy = 0
        else:
            dy = _i16(glyf, p)
            p += 2
        y += dy
        ys.append(y)
    on = [(f & 1) != 0 for f in flags]
    contours = []
    s = 0
    for e in ends:
        contours.append(list(zip(xs[s : e + 1], ys[s : e + 1], on[s : e + 1])))
        s = e + 1
    return contours


def _composite_contours(font, glyf, p):
    # Walk composite glyph, applying translation (and simple scale if present).
    contours = []
    p += 10
    while True:
        flags = _u16(glyf, p)
        gid = _u16(glyf, p + 2)
        p += 4
        if flags & 0x01:  # ARG_1_AND_2_ARE_WORDS
            dx, dy = _i16(glyf, p), _i16(glyf, p + 2)
            p += 4
        else:
            dx = struct.unpack_from(">b", glyf, p)[0]
            dy = struct.unpack_from(">b", glyf, p + 1)[0]
            p += 2
        scale_x = scale_y = 1.0
        if flags & 0x08:  # WE_HAVE_A_SCALE
            scale_x = scale_y = _i16(glyf, p) / 16384.0
            p += 2
        elif flags & 0x40:  # WE_HAVE_AN_X_AND_Y_SCALE
            scale_x = _i16(glyf, p) / 16384.0
            scale_y = _i16(glyf, p + 2) / 16384.0
            p += 4
        elif flags & 0x80:  # WE_HAVE_A_TWO_BY_TWO
            p += 8  # ignore transform, still place by dx/dy
        for cont in _glyph_contours(font, gid):
            moved = [(px * scale_x + dx, py * scale_y + dy, on) for px, py, on in cont]
            contours.append(moved)
        if not (flags & 0x20):  # MORE_COMPONENTS
            break
    return contours


def _contour_path(contour, scale, ox, oy):
    if not contour:
        return ""
    pts = [(x, y, on) for x, y, on in contour]
    # Insert implied on-curve points between consecutive off-curve points.
    expanded = []
    n = len(pts)
    for i in range(n):
        expanded.append(pts[i])
        x1, y1, on1 = pts[i]
        x2, y2, on2 = pts[(i + 1) % n]
        if not on1 and not on2:
            expanded.append(((x1 + x2) / 2, (y1 + y2) / 2, True))
    # Rotate to an on-curve start.
    idx = next(i for i, p in enumerate(expanded) if p[2])
    expanded = expanded[idx:] + expanded[:idx]

    def tx(x, y):
        return ox + x * scale, oy - y * scale

    def fmt(x, y):
        return f"{x:.2f} {y:.2f}"

    sx, sy = tx(*expanded[0][:2])
    parts = [f"M {fmt(sx, sy)}"]
    i = 0
    m = len(expanded)
    # Walk until we have consumed every point once and closed.
    seen = 0
    while seen < m:
        j = (i + 1) % m
        if expanded[j][2]:
            x, y = tx(*expanded[j][:2])
            parts.append(f"L {fmt(x, y)}")
            i = j
            seen += 1
        else:
            cx, cy = tx(*expanded[j][:2])
            k = (j + 1) % m
            if expanded[k][2]:
                ex, ey = tx(*expanded[k][:2])
                end_i = k
            else:
                # Should not happen after implied-point insertion.
                mx = (expanded[j][0] + expanded[k][0]) / 2
                my = (expanded[j][1] + expanded[k][1]) / 2
                ex, ey = tx(mx, my)
                end_i = j  # stay; next loop handles k
            parts.append(f"Q {fmt(cx, cy)} {fmt(ex, ey)}")
            step = (end_i - i) % m
            i = end_i
            seen += step if step else m
        if i == 0:
            break
    parts.append("Z")
    return " ".join(parts)


def text_path(font, text, size, x, y, anchor="start", fill="#000", letter_spacing=0, extra=""):
    """Return an SVG <path> element. (x, y) is the anchor point on the baseline."""
    scale = size / font.units
    glyphs = []
    pen = 0.0
    prev = None
    for ch in text:
        gid = font.glyph_id(ord(ch))
        adv = font.advances[gid] if gid < len(font.advances) else font.units // 3
        k = 0
        if prev is not None:
            k = font.kern.get((prev, gid), 0)
        glyphs.append((gid, pen + k))
        pen += adv + k + letter_spacing * font.units / size
        prev = gid
    width = pen - (letter_spacing * font.units / size if text else 0)
    width_px = width * scale
    if anchor == "middle":
        origin = x - width_px / 2
    elif anchor == "end":
        origin = x - width_px
    else:
        origin = x
    d_parts = []
    for gid, gx in glyphs:
        contours = _glyph_contours(font, gid)
        ox = origin + gx * scale
        for cont in contours:
            d_parts.append(_contour_path(cont, scale, ox, y))
    d = " ".join(p for p in d_parts if p)
    return f'<path fill="{fill}" d="{d}" {extra}/>', width_px


def measure(font, text, size, letter_spacing=0):
    _, w = text_path(font, text, size, 0, 0, letter_spacing=letter_spacing)
    return w
