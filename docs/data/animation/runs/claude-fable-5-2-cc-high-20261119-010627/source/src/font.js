// Minimal TrueType (.ttf / .ttc, glyf outlines) parser + exact-area glyph rasterizer.
// No dependencies. Only what this project needs: cmap, hmtx, kern (format 0), glyf.
'use strict';
const fs = require('fs');

class Font {
  constructor(buf, offset) {
    this.b = buf;
    const numTables = buf.readUInt16BE(offset + 4);
    this.t = {};
    for (let i = 0; i < numTables; i++) {
      const p = offset + 12 + i * 16;
      this.t[buf.toString('latin1', p, p + 4)] = { off: buf.readUInt32BE(p + 8), len: buf.readUInt32BE(p + 12) };
    }
    if (!this.t.glyf) throw new Error('no glyf table');
    const head = this.t.head.off;
    this.unitsPerEm = buf.readUInt16BE(head + 18);
    this.locFormat = buf.readInt16BE(head + 50);
    this.numGlyphs = buf.readUInt16BE(this.t.maxp.off + 4);
    const hhea = this.t.hhea.off;
    this.ascent = buf.readInt16BE(hhea + 4);
    this.descent = buf.readInt16BE(hhea + 6);
    this.numHM = buf.readUInt16BE(hhea + 34);
    this._cmap();
    this._kern();
    this.cache = new Map();
    this.name = this._name();
  }

  static faces(path) {
    const buf = fs.readFileSync(path);
    const out = [];
    if (buf.toString('latin1', 0, 4) === 'ttcf') {
      const n = buf.readUInt32BE(8);
      for (let i = 0; i < n; i++) {
        try { out.push(new Font(buf, buf.readUInt32BE(12 + i * 4))); } catch (e) { /* CFF face etc. */ }
      }
    } else {
      try { out.push(new Font(buf, 0)); } catch (e) { /* ignore */ }
    }
    return out;
  }

  // Find a face by (sub)name in a list of candidate files; first hit wins.
  static load(candidates) {
    for (const [path, want] of candidates) {
      if (!fs.existsSync(path)) continue;
      const faces = Font.faces(path);
      const f = faces.find(f => !want || f.name === want) || null;
      if (f) return f;
    }
    throw new Error('no usable font found');
  }

  _name() {
    const t = this.t.name; if (!t) return '';
    const b = this.b, o = t.off, n = b.readUInt16BE(o + 2), so = o + b.readUInt16BE(o + 4);
    let best = '';
    for (let i = 0; i < n; i++) {
      const r = o + 6 + i * 12;
      const pid = b.readUInt16BE(r), nid = b.readUInt16BE(r + 6);
      const len = b.readUInt16BE(r + 8), off = b.readUInt16BE(r + 10);
      if (nid !== 4) continue;
      const raw = b.subarray(so + off, so + off + len);
      if (pid === 1) best = best || raw.toString('latin1');
      else { let s = ''; for (let k = 0; k + 1 < raw.length; k += 2) s += String.fromCharCode(raw.readUInt16BE(k)); best = s; }
    }
    return best;
  }

  _cmap() {
    const b = this.b, o = this.t.cmap.off, n = b.readUInt16BE(o + 2);
    let sub = -1, score = -1;
    for (let i = 0; i < n; i++) {
      const pid = b.readUInt16BE(o + 4 + i * 8), eid = b.readUInt16BE(o + 6 + i * 8);
      const so = o + b.readUInt32BE(o + 8 + i * 8), fmt = b.readUInt16BE(so);
      let s = -1;
      if (fmt === 12 && (pid === 0 || (pid === 3 && eid === 10))) s = 3;
      else if (fmt === 4 && (pid === 0 || (pid === 3 && eid === 1))) s = 2;
      if (s > score) { score = s; sub = so; }
    }
    if (sub < 0) throw new Error('no usable cmap');
    this.map = new Map();
    const fmt = b.readUInt16BE(sub);
    if (fmt === 4) {
      const segX2 = b.readUInt16BE(sub + 6);
      const endO = sub + 14, startO = endO + segX2 + 2, deltaO = startO + segX2, rangeO = deltaO + segX2;
      for (let i = 0; i < segX2; i += 2) {
        const end = b.readUInt16BE(endO + i), start = b.readUInt16BE(startO + i);
        const delta = b.readInt16BE(deltaO + i), ro = b.readUInt16BE(rangeO + i);
        for (let c = start; c <= end && c < 0xffff; c++) {
          let g;
          if (ro === 0) g = (c + delta) & 0xffff;
          else { g = b.readUInt16BE(rangeO + i + ro + (c - start) * 2); if (g) g = (g + delta) & 0xffff; }
          if (g) this.map.set(c, g);
        }
      }
    } else {
      const ng = b.readUInt32BE(sub + 12);
      for (let i = 0; i < ng; i++) {
        const p = sub + 16 + i * 12, s = b.readUInt32BE(p), e = b.readUInt32BE(p + 4), g = b.readUInt32BE(p + 8);
        if (s > 0x2fff) continue;
        for (let c = s; c <= e && c <= 0x2fff; c++) this.map.set(c, g + c - s);
      }
    }
  }

  _kern() {
    this.kern = new Map();
    const t = this.t.kern; if (!t) return;
    const b = this.b; let o = t.off;
    if (b.readUInt16BE(o) !== 0) return;
    const nT = b.readUInt16BE(o + 2); o += 4;
    for (let i = 0; i < nT; i++) {
      const len = b.readUInt16BE(o + 2), cov = b.readUInt16BE(o + 4);
      if ((cov >> 8) === 0 && (cov & 1)) {
        const np = b.readUInt16BE(o + 6);
        for (let k = 0; k < np; k++) {
          const p = o + 14 + k * 6;
          this.kern.set(b.readUInt16BE(p) * 65536 + b.readUInt16BE(p + 2), b.readInt16BE(p + 4));
        }
      }
      o += len;
    }
  }

  advance(g) {
    const o = this.t.hmtx.off;
    return this.b.readUInt16BE(o + Math.min(g, this.numHM - 1) * 4);
  }

  _loca(g) {
    const o = this.t.loca.off, b = this.b;
    return this.locFormat ? [b.readUInt32BE(o + g * 4), b.readUInt32BE(o + g * 4 + 4)]
      : [b.readUInt16BE(o + g * 2) * 2, b.readUInt16BE(o + g * 2 + 2) * 2];
  }

  // Returns contours as arrays of flattened [x, y] points in font units (y up).
  glyph(g, depth = 0) {
    if (this.cache.has(g)) return this.cache.get(g);
    const b = this.b, [s, e] = this._loca(g);
    let contours = [];
    if (e > s && depth < 6) {
      let p = this.t.glyf.off + s;
      const nc = b.readInt16BE(p); p += 10;
      if (nc >= 0) {
        const ends = []; for (let i = 0; i < nc; i++) { ends.push(b.readUInt16BE(p)); p += 2; }
        const np = nc ? ends[nc - 1] + 1 : 0;
        p += 2 + b.readUInt16BE(p);
        const flags = [];
        while (flags.length < np) {
          const f = b[p++]; flags.push(f);
          if (f & 8) { let r = b[p++]; while (r--) flags.push(f); }
        }
        const xs = [], ys = []; let v = 0;
        for (let i = 0; i < np; i++) {
          const f = flags[i];
          if (f & 2) { const d = b[p++]; v += (f & 16) ? d : -d; } else if (!(f & 16)) { v += b.readInt16BE(p); p += 2; }
          xs.push(v);
        }
        v = 0;
        for (let i = 0; i < np; i++) {
          const f = flags[i];
          if (f & 4) { const d = b[p++]; v += (f & 32) ? d : -d; } else if (!(f & 32)) { v += b.readInt16BE(p); p += 2; }
          ys.push(v);
        }
        let start = 0;
        for (let c = 0; c < nc; c++) {
          const pts = [];
          for (let i = start; i <= ends[c]; i++) pts.push({ x: xs[i], y: ys[i], on: !!(flags[i] & 1) });
          start = ends[c] + 1;
          if (pts.length >= 2) contours.push(flatten(pts));
        }
      } else {
        let more = true;
        while (more) {
          const fl = b.readUInt16BE(p), gi = b.readUInt16BE(p + 2); p += 4;
          let dx, dy;
          if (fl & 1) { dx = b.readInt16BE(p); dy = b.readInt16BE(p + 2); p += 4; } else { dx = b.readInt8(p); dy = b.readInt8(p + 1); p += 2; }
          let a = 1, bb = 0, c = 0, d = 1;
          const f2 = () => { const r = b.readInt16BE(p) / 16384; p += 2; return r; };
          if (fl & 8) { a = d = f2(); } else if (fl & 0x40) { a = f2(); d = f2(); } else if (fl & 0x80) { a = f2(); bb = f2(); c = f2(); d = f2(); }
          for (const ct of this.glyph(gi, depth + 1)) contours.push(ct.map(([x, y]) => [a * x + c * y + dx, bb * x + d * y + dy]));
          more = !!(fl & 0x20);
        }
      }
    }
    this.cache.set(g, contours);
    return contours;
  }

  // Lay out a string. Returns { contours (px, y down, baseline at y=0, x from 0), width }.
  layout(str, size, tracking = 0) {
    const sc = size / this.unitsPerEm;
    const out = []; let x = 0, prev = 0;
    for (const ch of str) {
      const g = this.map.get(ch.codePointAt(0)) || 0;
      if (prev) x += (this.kern.get(prev * 65536 + g) || 0) * sc;
      for (const ct of this.glyph(g)) out.push(ct.map(([px, py]) => [x + px * sc, -py * sc]));
      x += this.advance(g) * sc + tracking;
      prev = g;
    }
    return { contours: out, width: x - tracking };
  }

  // Rasterize a string into an alpha mask (Float32Array) with padding.
  mask(str, size, tracking = 0) {
    const { contours, width } = this.layout(str, size, tracking);
    const pad = 3;
    const asc = Math.ceil(size * 1.05), desc = Math.ceil(size * 0.35);
    const w = Math.ceil(width) + pad * 2 + 2, h = asc + desc + pad * 2;
    const acc = new Float32Array(w * h + 4);
    const ox = pad, oy = pad + asc;
    for (const ct of contours) {
      for (let i = 0; i < ct.length; i++) {
        const a = ct[i], c = ct[(i + 1) % ct.length];
        edge(acc, w, h, a[0] + ox, a[1] + oy, c[0] + ox, c[1] + oy);
      }
    }
    const data = new Float32Array(w * h);
    let s = 0;
    for (let i = 0; i < w * h; i++) { s += acc[i]; const v = Math.abs(s); data[i] = v > 1 ? 1 : v; }
    return { data, w, h, ox, oy, width };
  }
}

function flatten(pts) {
  // Expand implied on-curve points, then subdivide quadratics.
  const n = pts.length, out = [];
  let first = pts.findIndex(p => p.on), startPt, i0;
  if (first < 0) { startPt = { x: (pts[0].x + pts[1].x) / 2, y: (pts[0].y + pts[1].y) / 2 }; i0 = 0; }
  else { startPt = pts[first]; i0 = first + 1; }
  let cur = startPt, ctrl = null;
  out.push([cur.x, cur.y]);
  const quad = (p0, c, p1) => {
    const steps = 10;
    for (let k = 1; k <= steps; k++) {
      const t = k / steps, u = 1 - t;
      out.push([u * u * p0.x + 2 * u * t * c.x + t * t * p1.x, u * u * p0.y + 2 * u * t * c.y + t * t * p1.y]);
    }
  };
  for (let k = 0; k < n; k++) {
    const p = pts[(i0 + k) % n];
    if (first >= 0 && k === n - 1) { /* p is the start point again */ }
    if (p.on) {
      if (ctrl) { quad(cur, ctrl, p); ctrl = null; } else out.push([p.x, p.y]);
      cur = p;
    } else {
      if (ctrl) { const mid = { x: (ctrl.x + p.x) / 2, y: (ctrl.y + p.y) / 2 }; quad(cur, ctrl, mid); cur = mid; }
      ctrl = p;
    }
  }
  if (ctrl) quad(cur, ctrl, startPt);
  return out;
}

// Signed-area accumulation of one edge (font-rs style). Mask is prefix-summed afterwards.
function edge(a, w, h, x0, y0, x1, y1) {
  if (y0 === y1) return;
  let dir = 1;
  if (y0 > y1) { dir = -1; let t = x0; x0 = x1; x1 = t; t = y0; y0 = y1; y1 = t; }
  const dxdy = (x1 - x0) / (y1 - y0);
  let x = x0;
  if (y0 < 0) x -= y0 * dxdy;
  const yEnd = Math.min(h, Math.ceil(y1));
  for (let y = Math.max(0, Math.floor(y0)); y < yEnd; y++) {
    const ls = y * w;
    const dy = Math.min(y + 1, y1) - Math.max(y, y0);
    const xn = x + dxdy * dy;
    const d = dy * dir;
    const xa = Math.min(x, xn), xb = Math.max(x, xn);
    const xaf = Math.floor(xa), xbc = Math.ceil(xb);
    if (xbc <= xaf + 1) {
      const xmf = 0.5 * (x + xn) - xaf;
      a[ls + xaf] += d - d * xmf;
      a[ls + xaf + 1] += d * xmf;
    } else {
      const s = 1 / (xb - xa);
      const x0f = xa - xaf;
      const a0 = 0.5 * s * (1 - x0f) * (1 - x0f);
      const x1f = xb - xbc + 1;
      const am = 0.5 * s * x1f * x1f;
      a[ls + xaf] += d * a0;
      if (xbc === xaf + 2) {
        a[ls + xaf + 1] += d * (1 - a0 - am);
      } else {
        const a1 = s * (1.5 - x0f);
        a[ls + xaf + 1] += d * (a1 - a0);
        for (let xi = xaf + 2; xi < xbc - 1; xi++) a[ls + xi] += d * s;
        const a2 = a1 + (xbc - xaf - 3) * s;
        a[ls + xbc - 1] += d * (1 - a2 - am);
      }
      a[ls + xbc] += d * am;
    }
    x = xn;
  }
}

module.exports = { Font };

if (require.main === module) {
  for (const p of process.argv.slice(2)) console.log(p, Font.faces(p).map(f => f.name));
}
