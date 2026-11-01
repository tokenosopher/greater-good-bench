'use strict';

/**
 * High-Performance Linear-Light HDR 2D SDF & Vector Renderer
 * Uses Float32Array linear RGB accumulation buffer with filmic tone mapping
 * and anti-aliased Signed Distance Field (SDF) primitives.
 */

class HDRCanvas {
  constructor(width, height) {
    this.width = width;
    this.height = height;
    this.buf = new Float32Array(width * height * 3);
    this.out = new Uint8Array(width * height * 3);

    // Precompute sRGB lookup table for fast linear -> sRGB conversion
    this.lutSize = 4096;
    this.srgbLut = new Uint8Array(this.lutSize);
    for (let i = 0; i < this.lutSize; i++) {
      // Filmic curve + gamma 2.2
      const x = (i / (this.lutSize - 1)) * 2.5; // map [0, 2.5] HDR range
      // ACES-like filmic curve
      const a = 2.51, b = 0.03, c = 2.43, d = 0.59, e = 0.14;
      const mapped = Math.min(1.0, Math.max(0.0, (x * (a * x + b)) / (x * (c * x + d) + e)));
      const srgb = Math.pow(mapped, 1.0 / 2.2);
      this.srgbLut[i] = Math.min(255, Math.max(0, Math.round(srgb * 255)));
    }
  }

  clear(r, g, b) {
    const buf = this.buf;
    const n = buf.length;
    for (let i = 0; i < n; i += 3) {
      buf[i] = r;
      buf[i + 1] = g;
      buf[i + 2] = b;
    }
  }

  /**
   * Render rich vertical + radial atmospheric background
   */
  drawBackground(topRGB, bottomRGB, centerGlowRGB, glowX, glowY, glowRadius) {
    const { width, height, buf } = this;
    const invH = 1.0 / height;
    const invR2 = 1.0 / (glowRadius * glowRadius);

    let idx = 0;
    for (let y = 0; y < height; y++) {
      const ty = y * invH;
      const br = topRGB[0] + (bottomRGB[0] - topRGB[0]) * ty;
      const bg = topRGB[1] + (bottomRGB[1] - topRGB[1]) * ty;
      const bb = topRGB[2] + (bottomRGB[2] - topRGB[2]) * ty;
      const dy2 = (y - glowY) * (y - glowY);

      for (let x = 0; x < width; x++) {
        const dx = x - glowX;
        const d2 = (dx * dx + dy2) * invR2;
        const g = Math.exp(-d2 * 1.5);
        buf[idx] = br + centerGlowRGB[0] * g;
        buf[idx + 1] = bg + centerGlowRGB[1] * g;
        buf[idx + 2] = bb + centerGlowRGB[2] * g;
        idx += 3;
      }
    }
  }

  /**
   * Blend a pixel at (x, y) in linear space.
   * mode = 'alpha' (standard over) or 'add' (HDR additive glow)
   */
  blendPixel(x, y, r, g, b, alpha, additive = 0.0) {
    if (alpha <= 0.0005) return;
    const idx = (y * this.width + x) * 3;
    const buf = this.buf;
    const invA = 1.0 - alpha * (1.0 - additive);
    buf[idx] = buf[idx] * invA + r * alpha;
    buf[idx + 1] = buf[idx + 1] * invA + g * alpha;
    buf[idx + 2] = buf[idx + 2] * invA + b * alpha;
  }

  /**
   * Anti-aliased SDF Circle (filled and/or stroked, with optional HDR glow)
   */
  drawCircle(cx, cy, radius, color, alpha = 1.0, glowRadius = 0.0, glowIntensity = 0.5, additive = 0.0) {
    const { width, height, buf } = this;
    const pad = Math.ceil(radius + glowRadius + 2);
    const x0 = Math.max(0, Math.floor(cx - pad));
    const x1 = Math.min(width - 1, Math.ceil(cx + pad));
    const y0 = Math.max(0, Math.floor(cy - pad));
    const y1 = Math.min(height - 1, Math.ceil(cy + pad));

    const [cr, cg, cb] = color;
    const hasGlow = glowRadius > 0.5;
    const invGlow = hasGlow ? 1.0 / glowRadius : 0;

    for (let y = y0; y <= y1; y++) {
      const dy = y - cy;
      const dy2 = dy * dy;
      let rowIdx = (y * width + x0) * 3;
      for (let x = x0; x <= x1; x++) {
        const dx = x - cx;
        const dist = Math.sqrt(dx * dx + dy2) - radius;

        let a = 0.0;
        let isAdd = additive;
        if (dist <= 0.75) {
          // Smooth anti-aliased edge
          const core = dist < -0.75 ? 1.0 : (0.75 - dist) / 1.5;
          a = core * alpha;
        }
        if (hasGlow && dist > -glowRadius && dist < glowRadius) {
          const gd = Math.max(0, dist) * invGlow;
          const g = Math.exp(-gd * gd * 3.5) * glowIntensity * alpha;
          a = Math.min(1.0, a + g);
          if (dist > 0.75) isAdd = 1.0;
        }

        if (a > 0.001) {
          const invA = 1.0 - a * (1.0 - isAdd);
          buf[rowIdx] = buf[rowIdx] * invA + cr * a;
          buf[rowIdx + 1] = buf[rowIdx + 1] * invA + cg * a;
          buf[rowIdx + 2] = buf[rowIdx + 2] * invA + cb * a;
        }
        rowIdx += 3;
      }
    }
  }

  /**
   * Anti-aliased Ring / Arc (supports partial startAngle..endAngle in radians)
   */
  drawArc(cx, cy, radius, thickness, startAngle, endAngle, color, alpha = 1.0, glowRadius = 0.0, additive = 0.0) {
    const { width, height, buf } = this;
    const halfT = thickness * 0.5;
    const pad = Math.ceil(radius + halfT + glowRadius + 3);
    const x0 = Math.max(0, Math.floor(cx - pad));
    const x1 = Math.min(width - 1, Math.ceil(cx + pad));
    const y0 = Math.max(0, Math.floor(cy - pad));
    const y1 = Math.min(height - 1, Math.ceil(cy + pad));

    const [cr, cg, cb] = color;
    const span = Math.max(0, endAngle - startAngle);
    const fullCircle = span >= Math.PI * 1.999;
    const midAngle = startAngle + span * 0.5;
    const cosHalfSpan = Math.cos(Math.min(Math.PI, span * 0.5));
    const cosMid = Math.cos(midAngle);
    const sinMid = Math.sin(midAngle);
    const capX1 = cx + Math.cos(startAngle) * radius;
    const capY1 = cy + Math.sin(startAngle) * radius;
    const capX2 = cx + Math.cos(endAngle) * radius;
    const capY2 = cy + Math.sin(endAngle) * radius;

    const hasGlow = glowRadius > 0.5;
    const invGlow = hasGlow ? 1.0 / glowRadius : 0;

    for (let y = y0; y <= y1; y++) {
      const dy = y - cy;
      let rowIdx = (y * width + x0) * 3;
      for (let x = x0; x <= x1; x++) {
        const dx = x - cx;
        const r = Math.sqrt(dx * dx + dy * dy);
        // Quick radial reject
        const radialDist = Math.abs(r - radius) - halfT;
        if (radialDist > glowRadius + 1.5) {
          rowIdx += 3;
          continue;
        }

        let sdf = radialDist;
        if (!fullCircle && r > 0.001) {
          // Check if angle is within [startAngle, endAngle]
          // Dot product with midAngle vector
          const ux = dx / r;
          const uy = dy / r;
          const dot = ux * cosMid + uy * sinMid;
          if (dot < cosHalfSpan) {
            // Distance to rounded endpoints
            const d1 = Math.hypot(x - capX1, y - capY1) - halfT;
            const d2 = Math.hypot(x - capX2, y - capY2) - halfT;
            sdf = Math.min(d1, d2);
          }
        }

        let a = 0.0;
        let isAdd = additive;
        if (sdf <= 0.75) {
          const core = sdf < -0.75 ? 1.0 : (0.75 - sdf) / 1.5;
          a = core * alpha;
        }
        if (hasGlow && sdf < glowRadius) {
          const gd = Math.max(0, sdf) * invGlow;
          const g = Math.exp(-gd * gd * 3.5) * 0.55 * alpha;
          a = Math.min(1.0, a + g);
          if (sdf > 0.75) isAdd = 1.0;
        }

        if (a > 0.001) {
          const invA = 1.0 - a * (1.0 - isAdd);
          buf[rowIdx] = buf[rowIdx] * invA + cr * a;
          buf[rowIdx + 1] = buf[rowIdx + 1] * invA + cg * a;
          buf[rowIdx + 2] = buf[rowIdx + 2] * invA + cb * a;
        }
        rowIdx += 3;
      }
    }
  }

  /**
   * Anti-aliased Tapered Capsule (line from (ax, ay) with radius rA to (bx, by) with radius rB)
   * Great for limbs, torso segments, bronchioles, lightning, and typography strokes.
   */
  drawCapsule(ax, ay, bx, by, rA, rB, color, alpha = 1.0, glowRadius = 0.0, additive = 0.0) {
    const { width, height, buf } = this;
    const maxR = Math.max(rA, rB) + glowRadius + 2;
    const x0 = Math.max(0, Math.floor(Math.min(ax, bx) - maxR));
    const x1 = Math.min(width - 1, Math.ceil(Math.max(ax, bx) + maxR));
    const y0 = Math.max(0, Math.floor(Math.min(ay, by) - maxR));
    const y1 = Math.min(height - 1, Math.ceil(Math.max(ay, by) + maxR));

    const vx = bx - ax;
    const vy = by - ay;
    const len2 = vx * vx + vy * vy;
    const invLen2 = len2 > 1e-6 ? 1.0 / len2 : 0.0;
    const [cr, cg, cb] = color;
    const hasGlow = glowRadius > 0.5;
    const invGlow = hasGlow ? 1.0 / glowRadius : 0;

    for (let y = y0; y <= y1; y++) {
      const wy = y - ay;
      let rowIdx = (y * width + x0) * 3;
      for (let x = x0; x <= x1; x++) {
        const wx = x - ax;
        const t = Math.min(1.0, Math.max(0.0, (wx * vx + wy * vy) * invLen2));
        const px = ax + t * vx;
        const py = ay + t * vy;
        const r = rA + (rB - rA) * t;
        const sdf = Math.hypot(x - px, y - py) - r;

        if (sdf > glowRadius + 0.8) {
          rowIdx += 3;
          continue;
        }

        let a = 0.0;
        let isAdd = additive;
        if (sdf <= 0.75) {
          const core = sdf < -0.75 ? 1.0 : (0.75 - sdf) / 1.5;
          a = core * alpha;
        }
        if (hasGlow && sdf < glowRadius) {
          const gd = Math.max(0, sdf) * invGlow;
          const g = Math.exp(-gd * gd * 3.5) * 0.5 * alpha;
          a = Math.min(1.0, a + g);
          if (sdf > 0.75) isAdd = 1.0;
        }

        if (a > 0.001) {
          const invA = 1.0 - a * (1.0 - isAdd);
          buf[rowIdx] = buf[rowIdx] * invA + cr * a;
          buf[rowIdx + 1] = buf[rowIdx + 1] * invA + cg * a;
          buf[rowIdx + 2] = buf[rowIdx + 2] * invA + cb * a;
        }
        rowIdx += 3;
      }
    }
  }

  /**
   * Draw smooth polyline / spline with tapered radius or constant radius
   */
  drawPath(points, radiusFn, color, alpha = 1.0, glowRadius = 0.0, additive = 0.0) {
    const n = points.length;
    if (n < 2) return;
    for (let i = 0; i < n - 1; i++) {
      const t0 = i / (n - 1);
      const t1 = (i + 1) / (n - 1);
      const r0 = typeof radiusFn === 'function' ? radiusFn(t0, i) : radiusFn;
      const r1 = typeof radiusFn === 'function' ? radiusFn(t1, i + 1) : radiusFn;
      this.drawCapsule(
        points[i][0], points[i][1],
        points[i + 1][0], points[i + 1][1],
        r0, r1, color, alpha, glowRadius, additive
      );
    }
  }

  /**
   * Draw anti-aliased filled polygon (with optional soft feather edge)
   */
  drawPolygon(pts, color, alpha = 1.0, feather = 1.2, additive = 0.0) {
    const { width, height, buf } = this;
    const n = pts.length;
    if (n < 3) return;

    let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
    for (let i = 0; i < n; i++) {
      const [px, py] = pts[i];
      if (px < minX) minX = px;
      if (px > maxX) maxX = px;
      if (py < minY) minY = py;
      if (py > maxY) maxY = py;
    }

    const pad = Math.ceil(feather + 2);
    const x0 = Math.max(0, Math.floor(minX - pad));
    const x1 = Math.min(width - 1, Math.ceil(maxX + pad));
    const y0 = Math.max(0, Math.floor(minY - pad));
    const y1 = Math.min(height - 1, Math.ceil(maxY + pad));

    const [cr, cg, cb] = color;
    const invFeather = 1.0 / Math.max(0.5, feather);

    for (let y = y0; y <= y1; y++) {
      let rowIdx = (y * width + x0) * 3;
      for (let x = x0; x <= x1; x++) {
        // Compute signed distance to polygon
        let inside = false;
        let minDist2 = Infinity;

        for (let i = 0, j = n - 1; i < n; j = i++) {
          const xi = pts[i][0], yi = pts[i][1];
          const xj = pts[j][0], yj = pts[j][1];

          const intersect = ((yi > y) !== (yj > y)) &&
            (x < (xj - xi) * (y - yi) / (yj - yi + 1e-12) + xi);
          if (intersect) inside = !inside;

          const vx = xj - xi, vy = yj - yi;
          const l2 = vx * vx + vy * vy;
          const t = l2 > 1e-6 ? Math.min(1.0, Math.max(0.0, ((x - xi) * vx + (y - yi) * vy) / l2)) : 0.0;
          const dx = x - (xi + t * vx);
          const dy = y - (yi + t * vy);
          const d2 = dx * dx + dy * dy;
          if (d2 < minDist2) minDist2 = d2;
        }

        const sdf = (inside ? -1.0 : 1.0) * Math.sqrt(minDist2);
        if (sdf < feather) {
          const cov = Math.min(1.0, Math.max(0.0, 0.5 - sdf * invFeather));
          const a = cov * alpha;
          if (a > 0.001) {
            const invA = 1.0 - a * (1.0 - additive);
            buf[rowIdx] = buf[rowIdx] * invA + cr * a;
            buf[rowIdx + 1] = buf[rowIdx + 1] * invA + cg * a;
            buf[rowIdx + 2] = buf[rowIdx + 2] * invA + cb * a;
          }
        }
        rowIdx += 3;
      }
    }
  }

  /**
   * Convert HDR float buffer to 8-bit sRGB Uint8Array with subtle vignette and dither
   */
  toSRGB() {
    const { width, height, buf, out, srgbLut, lutSize } = this;
    const scale = (lutSize - 1) / 2.5;
    const cx = width * 0.5;
    const cy = height * 0.5;
    const invMaxR2 = 1.0 / (cx * cx + cy * cy);

    let idx = 0;
    for (let y = 0; y < height; y++) {
      const dy2 = (y - cy) * (y - cy);
      for (let x = 0; x < width; x++) {
        const dx = x - cx;
        // Subtle cinematic vignette (max 18% darkening at extreme corners)
        const vig = 1.0 - 0.18 * ((dx * dx + dy2) * invMaxR2);
        // Tiny hash dither to prevent 8-bit gradient banding
        const dither = (((x * 13 + y * 37) & 7) - 3.5) * 0.0005;

        const r = Math.max(0, (buf[idx] * vig + dither) * scale);
        const g = Math.max(0, (buf[idx + 1] * vig + dither) * scale);
        const b = Math.max(0, (buf[idx + 2] * vig + dither) * scale);

        out[idx] = srgbLut[Math.min(lutSize - 1, r | 0)];
        out[idx + 1] = srgbLut[Math.min(lutSize - 1, g | 0)];
        out[idx + 2] = srgbLut[Math.min(lutSize - 1, b | 0)];
        idx += 3;
      }
    }
    return out;
  }
}

module.exports = { HDRCanvas };
