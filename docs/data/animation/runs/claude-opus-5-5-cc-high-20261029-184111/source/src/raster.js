// Tiny SDF rasterizer: every shape is a signed-distance function evaluated
// only inside its bounding box, with 1px analytic anti-aliasing.

function hex(c) {
  const n = parseInt(c.slice(1), 16);
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
}

class Canvas {
  constructor(w, h) {
    this.w = w; this.h = h;
    this.buf = new Float32Array(w * h * 3);
  }

  fill(sdf, box, color, alpha = 1) {
    if (alpha <= 0.002) return;
    const [r, g, b] = typeof color === 'string' ? hex(color) : color;
    const x0 = Math.max(0, Math.floor(box[0])), y0 = Math.max(0, Math.floor(box[1]));
    const x1 = Math.min(this.w, Math.ceil(box[2])), y1 = Math.min(this.h, Math.ceil(box[3]));
    const buf = this.buf, w = this.w;
    for (let y = y0; y < y1; y++) {
      const py = y + 0.5;
      for (let x = x0; x < x1; x++) {
        const d = sdf(x + 0.5, py);
        if (d >= 0.5) continue;
        let a = d <= -0.5 ? 1 : 0.5 - d;
        a *= alpha;
        const i = (y * w + x) * 3;
        buf[i] += (r - buf[i]) * a;
        buf[i + 1] += (g - buf[i + 1]) * a;
        buf[i + 2] += (b - buf[i + 2]) * a;
      }
    }
  }

  toBytes() {
    const out = Buffer.alloc(this.w * this.h * 3);
    for (let i = 0; i < out.length; i++) out[i] = Math.max(0, Math.min(255, Math.round(this.buf[i])));
    return out;
  }
}

// ---- distance functions (all return a closure + bbox) ----

function circle(cx, cy, r) {
  return [(x, y) => Math.hypot(x - cx, y - cy) - r, [cx - r - 2, cy - r - 2, cx + r + 2, cy + r + 2]];
}

function ellipse(cx, cy, rx, ry, rot = 0) {
  const c = Math.cos(rot), s = Math.sin(rot), m = Math.max(rx, ry);
  return [(x, y) => {
    const dx = x - cx, dy = y - cy;
    const u = (dx * c + dy * s) / rx, v = (-dx * s + dy * c) / ry;
    const k = Math.hypot(u, v);
    return (k - 1) * Math.min(rx, ry);
  }, [cx - m - 2, cy - m - 2, cx + m + 2, cy + m + 2]];
}

function capsule(ax, ay, bx, by, r) {
  const ex = bx - ax, ey = by - ay, ee = ex * ex + ey * ey || 1e-9;
  return [(x, y) => {
    const wx = x - ax, wy = y - ay;
    const t = Math.max(0, Math.min(1, (wx * ex + wy * ey) / ee));
    return Math.hypot(wx - ex * t, wy - ey * t) - r;
  }, [Math.min(ax, bx) - r - 2, Math.min(ay, by) - r - 2, Math.max(ax, bx) + r + 2, Math.max(ay, by) + r + 2]];
}

function rrect(cx, cy, hw, hh, rad, rot = 0) {
  const c = Math.cos(rot), s = Math.sin(rot), R = Math.hypot(hw, hh);
  rad = Math.min(rad, hw, hh);
  return [(x, y) => {
    const dx = x - cx, dy = y - cy;
    const u = Math.abs(dx * c + dy * s) - hw + rad, v = Math.abs(-dx * s + dy * c) - hh + rad;
    return Math.hypot(Math.max(u, 0), Math.max(v, 0)) + Math.min(Math.max(u, v), 0) - rad;
  }, [cx - R - 2, cy - R - 2, cx + R + 2, cy + R + 2]];
}

// Arc of radius ra and half-thickness rb, centred on direction `mid` (radians,
// screen space), spanning +-ap. Round caps.
function arc(cx, cy, ra, rb, mid, ap) {
  const dx0 = Math.cos(mid), dy0 = Math.sin(mid);
  const sx = Math.sin(ap), sy = Math.cos(ap);
  const R = ra + rb + 2;
  return [(x, y) => {
    const px = x - cx, py = y - cy;
    const along = px * dx0 + py * dy0;
    const perp = Math.abs(px * dy0 - py * dx0);
    if (sy * perp > sx * along) return Math.hypot(perp - sx * ra, along - sy * ra) - rb;
    return Math.abs(Math.hypot(px, py) - ra) - rb;
  }, [cx - R, cy - R, cx + R, cy + R]];
}

function polygon(pts) {
  let x0 = 1e9, y0 = 1e9, x1 = -1e9, y1 = -1e9;
  for (const [x, y] of pts) { x0 = Math.min(x0, x); y0 = Math.min(y0, y); x1 = Math.max(x1, x); y1 = Math.max(y1, y); }
  const n = pts.length;
  return [(x, y) => {
    let d = (x - pts[0][0]) ** 2 + (y - pts[0][1]) ** 2, s = 1;
    for (let i = 0, j = n - 1; i < n; j = i, i++) {
      const ex = pts[j][0] - pts[i][0], ey = pts[j][1] - pts[i][1];
      const wx = x - pts[i][0], wy = y - pts[i][1];
      const t = Math.max(0, Math.min(1, (wx * ex + wy * ey) / (ex * ex + ey * ey)));
      const bx = wx - ex * t, by = wy - ey * t;
      d = Math.min(d, bx * bx + by * by);
      const c1 = y >= pts[i][1], c2 = y < pts[j][1], c3 = ex * wy > ey * wx;
      if ((c1 && c2 && c3) || (!c1 && !c2 && !c3)) s = -s;
    }
    return s * Math.sqrt(d);
  }, [x0 - 2, y0 - 2, x1 + 2, y1 + 2]];
}

// Wobbly blob: circle whose radius ripples with n bumps.
function blob(cx, cy, r, amp, n, phase) {
  const R = r * (1 + amp) + 2;
  return [(x, y) => {
    const dx = x - cx, dy = y - cy;
    const rr = r * (1 + amp * Math.sin(n * Math.atan2(dy, dx) + phase));
    return (Math.hypot(dx, dy) - rr) * 0.8;
  }, [cx - R, cy - R, cx + R, cy + R]];
}

// Grow (or shrink) a shape: used for outlines.
function grow([f, b], k) {
  return [(x, y) => f(x, y) - k, [b[0] - k, b[1] - k, b[2] + k, b[3] + k]];
}

function union(shapes) {
  const fs = shapes.map(s => s[0]);
  const b = [1e9, 1e9, -1e9, -1e9];
  for (const s of shapes) { b[0] = Math.min(b[0], s[1][0]); b[1] = Math.min(b[1], s[1][1]); b[2] = Math.max(b[2], s[1][2]); b[3] = Math.max(b[3], s[1][3]); }
  return [(x, y) => { let d = 1e9; for (const f of fs) { const v = f(x, y); if (v < d) d = v; } return d; }, b];
}

function intersect([fa, ba], [fb]) {
  return [(x, y) => Math.max(fa(x, y), fb(x, y)), ba];
}

module.exports = { Canvas, hex, circle, ellipse, capsule, rrect, arc, polygon, blob, grow, union, intersect };
