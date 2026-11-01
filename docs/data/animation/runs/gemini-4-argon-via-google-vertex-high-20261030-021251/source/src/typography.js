'use strict';

/**
 * Crisp Geometric Vector Font Renderer
 * Coordinates are normalized in x: [0..1], y: [0..1] (0 = top, 1 = bottom).
 */

function arcPts(cx, cy, rx, ry, a0, a1, steps = 12) {
  const pts = [];
  for (let i = 0; i <= steps; i++) {
    const a = a0 + (a1 - a0) * (i / steps);
    pts.push([cx + Math.cos(a) * rx, cy + Math.sin(a) * ry]);
  }
  return pts;
}

const GLYPHS = {
  'A': { w: 0.76, s: [[[0.04, 1], [0.38, 0], [0.72, 1]], [[0.15, 0.66], [0.61, 0.66]]] },
  'B': {
    w: 0.72, s: [
      [[0.08, 0], [0.08, 1]],
      [[0.08, 0], [0.42, 0], ...arcPts(0.42, 0.24, 0.24, 0.24, -Math.PI / 2, Math.PI / 2, 8), [0.08, 0.48]],
      [[0.08, 0.48], [0.45, 0.48], ...arcPts(0.45, 0.74, 0.26, 0.26, -Math.PI / 2, Math.PI / 2, 8), [0.08, 1]]
    ]
  },
  'C': { w: 0.74, s: [arcPts(0.41, 0.5, 0.34, 0.5, 0.28 * Math.PI, 1.72 * Math.PI, 14)] },
  'D': {
    w: 0.76, s: [
      [[0.08, 0], [0.08, 1]],
      [[0.08, 0], [0.36, 0], ...arcPts(0.36, 0.5, 0.35, 0.5, -Math.PI / 2, Math.PI / 2, 12), [0.08, 1]]
    ]
  },
  'E': { w: 0.64, s: [[[0.56, 0], [0.08, 0], [0.08, 1], [0.56, 1]], [[0.08, 0.48], [0.48, 0.48]]] },
  'F': { w: 0.60, s: [[[0.55, 0], [0.08, 0], [0.08, 1]], [[0.08, 0.48], [0.46, 0.48]]] },
  'G': {
    w: 0.78, s: [
      [...arcPts(0.41, 0.5, 0.34, 0.5, -0.22 * Math.PI, -1.75 * Math.PI, 14), [0.70, 0.5], [0.42, 0.5]]
    ]
  },
  'H': { w: 0.74, s: [[[0.08, 0], [0.08, 1]], [[0.66, 0], [0.66, 1]], [[0.08, 0.48], [0.66, 0.48]]] },
  'I': { w: 0.28, s: [[[0.14, 0], [0.14, 1]]] },
  'J': { w: 0.56, s: [[[0.46, 0], [0.46, 0.72], ...arcPts(0.26, 0.72, 0.20, 0.28, 0, Math.PI, 8)]] },
  'K': { w: 0.70, s: [[[0.08, 0], [0.08, 1]], [[0.62, 0], [0.08, 0.52]], [[0.24, 0.38], [0.64, 1]]] },
  'L': { w: 0.58, s: [[[0.08, 0], [0.08, 1], [0.54, 1]]] },
  'M': { w: 0.90, s: [[[0.06, 1], [0.12, 0], [0.45, 0.62], [0.78, 0], [0.84, 1]]] },
  'N': { w: 0.76, s: [[[0.08, 1], [0.08, 0], [0.68, 1], [0.68, 0]]] },
  'O': { w: 0.82, s: [arcPts(0.41, 0.5, 0.35, 0.5, 0, Math.PI * 2, 16)] },
  'P': {
    w: 0.68, s: [
      [[0.08, 0], [0.08, 1]],
      [[0.08, 0], [0.40, 0], ...arcPts(0.40, 0.26, 0.25, 0.26, -Math.PI / 2, Math.PI / 2, 9), [0.08, 0.52]]
    ]
  },
  'Q': {
    w: 0.82, s: [
      arcPts(0.41, 0.5, 0.35, 0.5, 0, Math.PI * 2, 16),
      [[0.46, 0.64], [0.78, 1.02]]
    ]
  },
  'R': {
    w: 0.72, s: [
      [[0.08, 0], [0.08, 1]],
      [[0.08, 0], [0.40, 0], ...arcPts(0.40, 0.25, 0.25, 0.25, -Math.PI / 2, Math.PI / 2, 9), [0.08, 0.50]],
      [[0.36, 0.50], [0.66, 1]]
    ]
  },
  'S': {
    w: 0.68, s: [[
      ...arcPts(0.35, 0.25, 0.26, 0.25, -0.15 * Math.PI, -1.22 * Math.PI, 8),
      ...arcPts(0.35, 0.74, 0.27, 0.26, -0.35 * Math.PI, 0.88 * Math.PI, 9)
    ]]
  },
  'T': { w: 0.68, s: [[[0.02, 0], [0.66, 0]], [[0.34, 0], [0.34, 1]]] },
  'U': {
    w: 0.74, s: [[
      [0.08, 0], [0.08, 0.66],
      ...arcPts(0.37, 0.66, 0.29, 0.34, Math.PI, 0, 10),
      [0.66, 0]
    ]]
  },
  'V': { w: 0.72, s: [[[0.04, 0], [0.36, 1], [0.68, 0]]] },
  'W': { w: 0.96, s: [[[0.04, 0], [0.25, 1], [0.48, 0.28], [0.71, 1], [0.92, 0]]] },
  'X': { w: 0.70, s: [[[0.06, 0], [0.64, 1]], [[0.64, 0], [0.06, 1]]] },
  'Y': { w: 0.68, s: [[[0.04, 0], [0.34, 0.50], [0.64, 0]], [[0.34, 0.50], [0.34, 1]]] },
  'Z': { w: 0.66, s: [[[0.06, 0], [0.60, 0], [0.06, 1], [0.60, 1]]] },
  '0': { w: 0.72, s: [arcPts(0.36, 0.5, 0.29, 0.5, 0, Math.PI * 2, 16)] },
  '1': { w: 0.44, s: [[[0.08, 0.22], [0.26, 0], [0.26, 1]]] },
  '2': {
    w: 0.66, s: [[
      ...arcPts(0.33, 0.26, 0.25, 0.26, -Math.PI * 0.9, Math.PI * 0.22, 9),
      [0.06, 1], [0.60, 1]
    ]]
  },
  '3': {
    w: 0.66, s: [
      arcPts(0.32, 0.24, 0.24, 0.24, -Math.PI * 0.85, Math.PI * 0.5, 9),
      arcPts(0.32, 0.74, 0.26, 0.26, -Math.PI * 0.5, Math.PI * 0.85, 9)
    ]
  },
  '8': {
    w: 0.70, s: [
      arcPts(0.35, 0.24, 0.24, 0.24, 0, Math.PI * 2, 12),
      arcPts(0.35, 0.74, 0.27, 0.26, 0, Math.PI * 2, 12)
    ]
  },
  '%': {
    w: 0.82, s: [
      arcPts(0.20, 0.22, 0.14, 0.18, 0, Math.PI * 2, 10),
      [[0.66, 0.04], [0.16, 0.96]],
      arcPts(0.62, 0.78, 0.14, 0.18, 0, Math.PI * 2, 10)
    ]
  },
  '+': { w: 0.60, s: [[[0.30, 0.22], [0.30, 0.78]], [[0.06, 0.50], [0.54, 0.50]]] },
  '-': { w: 0.50, s: [[[0.08, 0.50], [0.42, 0.50]]] },
  '·': { w: 0.36, s: [[[0.18, 0.49], [0.18, 0.51]]] },
  ':': { w: 0.34, s: [[[0.17, 0.28], [0.17, 0.30]], [[0.17, 0.72], [0.17, 0.74]]] },
  ' ': { w: 0.46, s: [] }
};

function measureText(text, size, tracking = 0.24) {
  const str = text.toUpperCase();
  let totalW = 0;
  for (let i = 0; i < str.length; i++) {
    const g = GLYPHS[str[i]] || GLYPHS[' '];
    totalW += g.w * size;
    if (i < str.length - 1) totalW += tracking * size;
  }
  return totalW;
}

function drawText(canvas, text, x, y, size, color, alpha = 1.0, opts = {}) {
  const {
    align = 'center',
    tracking = 0.24,
    weight = 0.088,
    bgAlpha = 0.0,
    bgColor = [0.01, 0.02, 0.04],
    borderColor = null
  } = opts;

  if (alpha <= 0.01) return;

  const str = text.toUpperCase();
  const totalW = measureText(str, size, tracking);
  let curX = align === 'center' ? x - totalW * 0.5 : (align === 'right' ? x - totalW : x);
  const strokeR = Math.max(0.95, size * weight);

  // Optional sleek dark pill backdrop for contrast
  if (bgAlpha > 0.01) {
    const padX = size * 0.75;
    const padY = size * 0.48;
    const pillR = size * 0.5 + padY;
    const ax = curX + totalW * 0.5 - Math.max(0, totalW * 0.5 - size * 0.2);
    const bx = curX + totalW * 0.5 + Math.max(0, totalW * 0.5 - size * 0.2);
    const py = y + size * 0.5;
    if (borderColor) {
      canvas.drawCapsule(ax - padX * 0.4, py, bx + padX * 0.4, py, pillR + 1.5, pillR + 1.5, borderColor, alpha * bgAlpha * 0.65);
    }
    canvas.drawCapsule(ax - padX * 0.4, py, bx + padX * 0.4, py, pillR, pillR, bgColor, alpha * bgAlpha);
  }

  for (let i = 0; i < str.length; i++) {
    const ch = str[i];
    const g = GLYPHS[ch] || GLYPHS[' '];
    for (const stroke of g.s) {
      if (stroke.length === 2 && Math.hypot(stroke[0][0] - stroke[1][0], stroke[0][1] - stroke[1][1]) < 0.05) {
        const px = curX + stroke[0][0] * size;
        const py = y + stroke[0][1] * size;
        canvas.drawCircle(px, py, strokeR * 1.35, color, alpha, 0.0);
      } else {
        const pts = stroke.map(([gx, gy]) => [curX + gx * size, y + gy * size]);
        canvas.drawPath(pts, strokeR, color, alpha, 0.0, 0.0);
      }
    }
    curX += (g.w + tracking) * size;
  }
}

module.exports = { drawText, measureText };
