#!/usr/bin/env python3
"""Minimal PNG decoder (stdlib only) + sanity checks for the Pale Blue Dot render."""
import struct, sys, zlib

def decode_png(path):
    with open(path, "rb") as f:
        data = f.read()
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    pos = 8
    width = height = None
    bitdepth = colortype = None
    idat = b""
    while pos < len(data):
        ln, typ = struct.unpack(">I4s", data[pos:pos+8])
        chunk = data[pos+8:pos+8+ln]
        if typ == b"IHDR":
            width, height, bitdepth, colortype = struct.unpack(">IIBB", chunk[:10])
        elif typ == b"IDAT":
            idat += chunk
        pos += 12 + ln
    assert bitdepth == 8, f"bitdepth {bitdepth}"
    raw = zlib.decompress(idat)
    if colortype == 6:      # RGBA
        nch, bpp = 4, 4
    elif colortype == 2:    # RGB
        nch, bpp = 3, 3
    else:
        raise ValueError(f"colortype {colortype}")
    stride = width * bpp
    # un-filter
    out = bytearray()
    prev = bytearray(stride)
    ptr = 0
    for y in range(height):
        ftype = raw[ptr]; ptr += 1
        line = bytearray(raw[ptr:ptr+stride]); ptr += stride
        if ftype == 1:  # Sub
            for i in range(bpp, stride):
                line[i] = (line[i] + line[i-bpp]) & 0xFF
        elif ftype == 2:  # Up
            for i in range(stride):
                line[i] = (line[i] + prev[i]) & 0xFF
        elif ftype == 3:  # Average
            for i in range(stride):
                a = line[i-bpp] if i >= bpp else 0
                line[i] = (line[i] + (a + prev[i]) // 2) & 0xFF
        elif ftype == 4:  # Paeth
            for i in range(stride):
                a = line[i-bpp] if i >= bpp else 0
                b = prev[i]
                c = prev[i-bpp] if i >= bpp else 0
                p = a + b - c
                pa, pb, pc = abs(p-a), abs(p-b), abs(p-c)
                pred = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                line[i] = (line[i] + pred) & 0xFF
        out += line
        prev = line
    return width, height, nch, bytes(out)

def px(img, x, y):
    w, h, nch, buf = img
    x, y = int(x), int(y)
    if not (0 <= x < w and 0 <= y < h):
        return None
    i = (y * w + x) * nch
    return tuple(buf[i:i+3])

if __name__ == "__main__":
    img = decode_png(sys.argv[1] if len(sys.argv) > 1 else "pale-blue-dot.svg.png")
    w, h, nch, _ = img
    print(f"decoded {w}x{h} ({nch}ch)")

    def lum(p): return sum(p[:3]) / 3

    # 1. corners dark
    for name, (x, y) in {"top-left": (30, 30), "top-right": (w-30, 30),
                          "bottom-right": (w-30, h-30)}.items():
        print(f"{name:13s} rgb={px(img, x, y)}")

    # 2. beam: sample along perpendicular across the dot position (947,555)
    #    beam axis at dot: direction (-1200,1000)/len -> unit (-0.768, 0.640)
    #    perpendicular: (0.640, 0.768)
    dx, dy = 947, 555
    print("beam cross-section luminance at dot row (offset -> lum):")
    for off in (-400, -250, -120, -60, 0, 60, 120, 250, 400):
        p = px(img, dx + 0.640*off, dy + 0.768*off)
        print(f"  {off:+5d}: {lum(p):6.1f}  rgb={p}")

    # 3. the dot: bright blueish pixel vs neighbors
    center = px(img, dx, dy)
    near = px(img, dx - 150, dy + 120)
    print(f"dot center rgb={center}  nearby space rgb={near}")
    print(f"dot is bluish: B > R ? {center[2] > center[0]}")

    # 4. text: count light pixels in the quote area (x 112-1000, y 700-980)
    count = 0
    for y in range(700, 980, 4):
        for x in range(112, 1050, 4):
            if lum(px(img, x, y)) > 120:
                count += 1
    print(f"light text pixels (sampled): {count}  (expect several hundred)")

    # 5. header
    hdr = [lum(px(img, x, 118)) for x in range(112, 500, 6)]
    print(f"header row max lum: {max(hdr):.0f} (gold text should be >100)")
