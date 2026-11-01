import struct, zlib, sys

def load_png(path):
    data = open(path, 'rb').read()
    assert data[:8] == b'\x89PNG\r\n\x1a\n'
    pos = 8
    idat = b''
    w = h = bitd = ctype = None
    while pos < len(data):
        ln = struct.unpack('>I', data[pos:pos+4])[0]
        typ = data[pos+4:pos+8]
        chunk = data[pos+8:pos+8+ln]
        if typ == b'IHDR':
            w, h, bitd, ctype, comp, filt, inter = struct.unpack('>IIBBBBB', chunk)
            assert bitd == 8 and ctype == 6 and inter == 0, (bitd, ctype, inter)
        elif typ == b'IDAT':
            idat += chunk
        pos += 12 + ln
    raw = zlib.decompress(idat)
    stride = w * 4
    out = bytearray(h * stride)
    prev = bytearray(stride)
    p = 0
    for y in range(h):
        f = raw[p]; p += 1
        line = bytearray(raw[p:p+stride]); p += stride
        if f == 0:
            pass
        elif f == 1:
            for i in range(4, stride):
                line[i] = (line[i] + line[i-4]) & 255
        elif f == 2:
            for i in range(stride):
                line[i] = (line[i] + prev[i]) & 255
        elif f == 3:
            for i in range(stride):
                a = line[i-4] if i >= 4 else 0
                line[i] = (line[i] + (a + prev[i]) // 2) & 255
        elif f == 4:
            for i in range(stride):
                a = line[i-4] if i >= 4 else 0
                b = prev[i]
                c = prev[i-4] if i >= 4 else 0
                pp = a + b - c
                pa, pb, pc = abs(pp-a), abs(pp-b), abs(pp-c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                line[i] = (line[i] + pr) & 255
        out[y*stride:(y+1)*stride] = line
        prev = line
    return w, h, bytes(out)

if __name__ == '__main__':
    path = sys.argv[1]
    w, h, px = load_png(path)
    def sample(lat, lon):
        row = int((90 - lat) / 180 * h) % h
        col = int((lon + 180) / 360 * w) % w
        i = (row * w + col) * 4
        return tuple(px[i:i+3])
    print('size', w, h)
    nz = sum(1 for i in range(0, len(px), 4) if px[i] != 0)
    print('nonzero-R pixels:', nz, '/', w*h)
    for name, la, lo in [('Congo',0,20),('Amazon',-5,-60),('USA',40,-100),('India',22,78),
                         ('Australia',-28,134),('Sahara',23,10),('Greenland',72,-40),
                         ('Antarctica',-80,0),('Pacific',0,-140),('Atlantic',30,-40)]:
        print(name, sample(la, lo))
