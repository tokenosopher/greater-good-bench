// "Be the Heartbeat" — a 10-second, loopable hands-only CPR lesson.
// Software renderer: every shape is a signed-distance function drawn into a float canvas.
// Usage:
//   node src/render.js frames <first> <last>   -> raw rgb24 frames on stdout
//   node src/render.js still <seconds> <out.ppm>
'use strict';
const fs = require('fs');
const { Font } = require('./font.js');

const W = 1280, H = 720, FPS = 30;
const BPM = 110, BEAT = 60 / BPM;          // compressions: 110 per minute (guideline: 100-120)
const DUR = 18 * BEAT;                     // 18 beats -> 9.82 s, so the loop stays on tempo
const NFRAMES = Math.floor(DUR * FPS);     // 294 frames = 9.8 s

// ---------- timeline (seconds) ----------
const SWEEP_X0 = 120, SWEEP_V = 900;       // ECG trace head
const QRS_X = [150, 480];
const VF_X0 = 600, VF_X1 = 850;
const T_FALL0 = 0.82, T_FALL1 = 1.24;
const T_ASK0 = 0.86, T_ASK1 = 1.95;
const T_RESC0 = 1.45, T_RESC1 = 1.95;
const T_CALL0 = 1.98, T_CALL1 = 3.10;
const T_LEAN0 = 2.80, T_LEAN1 = 3.12;
const FIRST_BEAT = 6;                      // first compression bottoms out on beat 6 (3.27 s)
const T_PUSH0 = 3.14, T_SUBB = 5.36, T_PUSH1 = 7.56;
const T_END0 = 7.62;

// ---------- palette ----------
const hex = h => [parseInt(h.slice(1, 3), 16) / 255, parseInt(h.slice(3, 5), 16) / 255, parseInt(h.slice(5, 7), 16) / 255];
const C = {
  bgTop: hex('#0d0f25'), bgBot: hex('#1c1a42'), bgGlow: hex('#33287a'),
  ink: hex('#12132c'),
  line: hex('#3b3d70'),
  coral: hex('#ff5964'), coralHot: hex('#ffb0a8'),
  alive: hex('#f3eeff'), aliveShade: hex('#cdc5e6'),
  down: hex('#b4aed0'), downShade: hex('#8f89b0'),
  still: hex('#55516f'),
  you: hex('#ffc145'), youShade: hex('#e39a2c'),
  white: hex('#ffffff'), soft: hex('#c8c4ea'),
  phone: hex('#f6f3ff'), screen: hex('#3fe0a5'),
};

// ---------- math helpers ----------
const clamp = (x, a = 0, b = 1) => x < a ? a : x > b ? b : x;
const lerp = (a, b, t) => a + (b - a) * t;
const mix = (a, b, t) => [lerp(a[0], b[0], t), lerp(a[1], b[1], t), lerp(a[2], b[2], t)];
const sstep = (a, b, x) => { const t = clamp((x - a) / (b - a)); return t * t * (3 - 2 * t); };
const easeOut = t => 1 - Math.pow(1 - clamp(t), 3);
const easeInOut = t => { t = clamp(t); return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2; };
const gauss = (u, s) => Math.exp(-(u * u) / (2 * s * s));

// ---------- canvas + coverage layer ----------
const cv = new Float32Array(W * H * 3);
const L = new Float32Array(W * H);
let dx0 = W, dy0 = H, dx1 = 0, dy1 = 0;

// Draw an SDF into the coverage layer (max-combined => clean unions).
function sdf(x0, y0, x1, y1, fn, weight = 1, soft = 0) {
  x0 = Math.max(0, Math.floor(x0)); y0 = Math.max(0, Math.floor(y0));
  x1 = Math.min(W, Math.ceil(x1)); y1 = Math.min(H, Math.ceil(y1));
  if (x1 <= x0 || y1 <= y0) return;
  if (x0 < dx0) dx0 = x0; if (y0 < dy0) dy0 = y0; if (x1 > dx1) dx1 = x1; if (y1 > dy1) dy1 = y1;
  for (let y = y0; y < y1; y++) {
    for (let x = x0, i = y * W + x0; x < x1; x++, i++) {
      const d = fn(x + 0.5, y + 0.5);
      let c = soft ? (d <= 0 ? 1 : Math.exp(-(d * d) / (soft * soft))) : (d <= -0.5 ? 1 : d >= 0.5 ? 0 : 0.5 - d);
      c *= weight;
      if (c > L[i]) L[i] = c;
    }
  }
}
// Composite the layer onto the canvas with a colour, then clear it.
function flush(col, alpha = 1, add = false) {
  for (let y = dy0; y < dy1; y++) {
    for (let x = dx0, i = y * W + dx0; x < dx1; x++, i++) {
      const a = L[i] * alpha;
      if (a > 0) {
        const j = i * 3;
        if (add) { cv[j] += col[0] * a; cv[j + 1] += col[1] * a; cv[j + 2] += col[2] * a; }
        else { cv[j] += (col[0] - cv[j]) * a; cv[j + 1] += (col[1] - cv[j + 1]) * a; cv[j + 2] += (col[2] - cv[j + 2]) * a; }
        L[i] = 0;
      }
    }
  }
  dx0 = W; dy0 = H; dx1 = 0; dy1 = 0;
}

// ---------- shapes ----------
function capsule(ax, ay, bx, by, r, grow = 0, weight = 1, soft = 0) {
  const R = r + grow, m = R + 2 + soft * 2.2;
  const ex = bx - ax, ey = by - ay, ee = ex * ex + ey * ey || 1e-9;
  sdf(Math.min(ax, bx) - m, Math.min(ay, by) - m, Math.max(ax, bx) + m, Math.max(ay, by) + m, (x, y) => {
    const px = x - ax, py = y - ay;
    const h = clamp((px * ex + py * ey) / ee);
    const qx = px - ex * h, qy = py - ey * h;
    return Math.sqrt(qx * qx + qy * qy) - R;
  }, weight, soft);
}
function circle(cx, cy, r, grow = 0, weight = 1, soft = 0) {
  const R = r + grow, m = R + 2 + soft * 2.2;
  sdf(cx - m, cy - m, cx + m, cy + m, (x, y) => Math.hypot(x - cx, y - cy) - R, weight, soft);
}
function ring(cx, cy, r, th, weight = 1) {
  const m = r + th + 2;
  sdf(cx - m, cy - m, cx + m, cy + m, (x, y) => Math.abs(Math.hypot(x - cx, y - cy) - r) - th / 2, weight);
}
function arc(cx, cy, r, aMid, aHalf, th, weight = 1) {
  const m = r + th + 2, cm = Math.cos(aMid), sm = Math.sin(aMid);
  const ex = Math.cos(aHalf) * r, ey = Math.sin(aHalf) * r;
  sdf(cx - m, cy - m, cx + m, cy + m, (x, y) => {
    const px = x - cx, py = y - cy;
    const qx = px * cm + py * sm, qy = Math.abs(-px * sm + py * cm);   // rotate so arc is centred on +x
    const ang = Math.atan2(qy, qx);
    return (ang <= aHalf ? Math.abs(Math.hypot(qx, qy) - r) : Math.hypot(qx - ex, qy - ey)) - th / 2;
  }, weight);
}
function rrect(cx, cy, hw, hh, r, rot = 0, grow = 0, weight = 1) {
  const m = Math.hypot(hw, hh) + grow + 2, c = Math.cos(rot), s = Math.sin(rot);
  sdf(cx - m, cy - m, cx + m, cy + m, (x, y) => {
    const px = x - cx, py = y - cy;
    const qx = Math.abs(px * c + py * s) - (hw - r), qy = Math.abs(-px * s + py * c) - (hh - r);
    return Math.hypot(Math.max(qx, 0), Math.max(qy, 0)) + Math.min(Math.max(qx, qy), 0) - r - grow;
  }, weight);
}
function heart(cx, cy, size, sx = 1, sy = 1, grow = 0, weight = 1, soft = 0) {
  const m = size * 1.3 + grow + 2 + soft * 2.2;
  sdf(cx - m, cy - m, cx + m, cy + m, (x, y) => {
    let px = Math.abs((x - cx) / (size * sx)), py = (cy - y) / (size * sy) + 0.56;
    let d;
    if (py + px > 1) d = Math.hypot(px - 0.25, py - 0.75) - Math.SQRT2 / 4;
    else {
      const k = 0.5 * Math.max(px + py, 0);
      d = Math.sqrt(Math.min(px * px + (py - 1) * (py - 1), (px - k) * (px - k) + (py - k) * (py - k))) * Math.sign(px - py);
    }
    return d * size - grow;
  }, weight, soft);
}

// ---------- text ----------
const SYS = '/System/Library/Fonts/', SUP = SYS + 'Supplemental/';
const FONT_HEAVY = Font.load([
  [SYS + 'Avenir Next Condensed.ttc', 'Avenir Next Condensed Heavy'],
  [SUP + 'DIN Condensed Bold.ttf', null], [SUP + 'Arial Narrow Bold.ttf', null], [SUP + 'Arial Bold.ttf', null],
]);
const FONT_DEMI = Font.load([
  [SYS + 'Avenir Next Condensed.ttc', 'Avenir Next Condensed Demi Bold'],
  [SUP + 'DIN Condensed Bold.ttf', null], [SUP + 'Arial Narrow Bold.ttf', null], [SUP + 'Arial Bold.ttf', null],
]);
const maskCache = new Map();
function textMask(font, str, size, tracking) {
  const key = font.name + '|' + str + '|' + size + '|' + tracking;
  if (!maskCache.has(key)) maskCache.set(key, font.mask(str, size, tracking));
  return maskCache.get(key);
}
function blit(m, left, baseline, col, alpha, scale, pvx, pvy) {
  // mask origin (pen start, baseline) sits at (left, baseline); scaled about (pvx, pvy)
  const mx0 = left - m.ox, my0 = baseline - m.oy;
  const X0 = Math.max(0, Math.floor(pvx + (mx0 - pvx) * scale)), X1 = Math.min(W, Math.ceil(pvx + (mx0 + m.w - pvx) * scale));
  const Y0 = Math.max(0, Math.floor(pvy + (my0 - pvy) * scale)), Y1 = Math.min(H, Math.ceil(pvy + (my0 + m.h - pvy) * scale));
  for (let Y = Y0; Y < Y1; Y++) {
    const v = (Y + 0.5 - pvy) / scale + pvy - my0 - 0.5;
    const vi = Math.floor(v), vf = v - vi;
    if (vi < -1 || vi >= m.h) continue;
    for (let X = X0; X < X1; X++) {
      const u = (X + 0.5 - pvx) / scale + pvx - mx0 - 0.5;
      const ui = Math.floor(u), uf = u - ui;
      if (ui < -1 || ui >= m.w) continue;
      const s = (xx, yy) => (xx < 0 || yy < 0 || xx >= m.w || yy >= m.h) ? 0 : m.data[yy * m.w + xx];
      const a = (s(ui, vi) * (1 - uf) + s(ui + 1, vi) * uf) * (1 - vf) + (s(ui, vi + 1) * (1 - uf) + s(ui + 1, vi + 1) * uf) * vf;
      if (a > 0.002) {
        const j = (Y * W + X) * 3, k = a * alpha;
        cv[j] += (col[0] - cv[j]) * k; cv[j + 1] += (col[1] - cv[j + 1]) * k; cv[j + 2] += (col[2] - cv[j + 2]) * k;
      }
    }
  }
}
// runs: [{ s, font, size, col, track, gap }] laid out left to right, centred on cx.
function measure(runs) {
  let w = 0;
  for (const r of runs) { r.m = textMask(r.font, r.s, r.size, r.track || 0); w += r.m.width + (r.gap || 0); }
  return w;
}
function text(runs, cx, baseline, alpha = 1, scale = 1, pivotY = null) {
  if (alpha <= 0.003) return;
  const total = measure(runs);
  let x = cx - total / 2;
  const pvy = pivotY === null ? baseline - runs[0].size * 0.35 : pivotY;
  for (const r of runs) {
    x += (r.gap || 0);
    blit(r.m, x, baseline, r.col, alpha * (r.alpha === undefined ? 1 : r.alpha), scale, cx, pvy);
    x += r.m.width;
  }
}

// ---------- background ----------
const bg = new Float32Array(W * H * 3);
const dither = new Float32Array(W * H);
(function buildBg() {
  let seed = 12345;
  const rnd = () => { seed = (seed * 1664525 + 1013904223) >>> 0; return seed / 4294967296; };
  for (let y = 0; y < H; y++) {
    for (let x = 0; x < W; x++) {
      const i = y * W + x, j = i * 3;
      const g = sstep(0, 1, y / H);
      const r2 = Math.pow((x - 640) / 760, 2) + Math.pow((y - 560) / 420, 2);
      const glow = Math.exp(-r2 * 1.6) * 0.55;
      const vig = 1 - 0.38 * sstep(0.35, 1.25, Math.hypot((x - 640) / 640, (y - 360) / 360) * 0.8);
      for (let k = 0; k < 3; k++) bg[j + k] = (lerp(C.bgTop[k], C.bgBot[k], g) + C.bgGlow[k] * glow * 0.6) * vig;
      dither[i] = (rnd() + rnd() - 1) * 0.6 / 255;
    }
  }
})();

// ---------- scene geometry ----------
const S = 1.2;                 // figure scale
const G = 628;                 // ground line y
const PX = 900;                // victim's heels (pivot of the fall)
const HAND_X = PX - 250 * S;   // middle of the chest once lying down
const HEART_H = 246;           // heart height along the body (base units)
const PHONE_REST = [PX - 500 * S + 4, G - 39];
const PHONE_W = 19, PHONE_H = 37;   // half sizes

const beatTime = k => k * BEAT;
// compression depth 0..1, peaks exactly on each beat from FIRST_BEAT onward
function depth(t) {
  const u = (t - beatTime(FIRST_BEAT)) / BEAT + 0.5;
  if (u < 0) return 0;
  const p = u - Math.floor(u);
  return Math.pow(Math.sin(Math.PI * p), 2.4);
}

function fallAngle(t) {
  // radians from vertical; ends at 90deg (flat on their back)
  const pre = sstep(0.5, 0.8, t) * (1 - sstep(0.8, 0.9, t)) * 0.05 * Math.sin((t - 0.5) * 21);
  const u = clamp((t - T_FALL0) / (T_FALL1 - T_FALL0));
  let a = Math.pow(u, 2.3) * Math.PI / 2;
  if (t > T_FALL1) { const v = t - T_FALL1; a -= 0.085 * Math.exp(-v / 0.09) * Math.abs(Math.sin(v * Math.PI / 0.17)); }
  return a + pre;
}

// victim: local (lx forward, h up along the body) -> world, resting on the ground
function vpt(a, lx, h, r) {
  const c = Math.cos(a), s = Math.sin(a);
  const x = PX + (lx * c - h * s) * S;
  const y = G - (h * c + lx * s) * S;
  return [x, Math.min(y, G - r * S)];
}

// ECG trace drawn by the sweeping head during the opening (px above the baseline)
function ecg(x) {
  let y = 0;
  for (const q of QRS_X) {
    const u = x - q;
    y += 9 * gauss(u + 52, 13) - 13 * gauss(u + 11, 4.5) + 92 * gauss(u, 5.5) - 26 * gauss(u - 11, 5) + 17 * gauss(u - 62, 19);
  }
  const env = sstep(VF_X0, VF_X0 + 40, x) * (1 - sstep(VF_X0 + 60, VF_X1, x));
  y += env * 24 * (Math.sin(x * 0.115) + 0.6 * Math.sin(x * 0.243 + 1.3) + 0.45 * Math.sin(x * 0.39 + 2.1));
  return y;
}
// pulse packets that every compression sends down the line
function pulseMask(x) { return Math.max(1 - sstep(PHONE_REST[0] - 76, PHONE_REST[0] - 34, x), sstep(PX + 36, PX + 86, x)); }
function pulse(x, t) {
  let y = 0, w = 0;
  const k1 = Math.floor(t / BEAT);
  for (let k = Math.max(FIRST_BEAT, k1 - 3); k <= k1; k++) {
    const age = t - beatTime(k);
    if (age < 0) continue;
    const u = Math.abs(x - HAND_X) - (240 + 580 * age);
    if (u > 80 || u < -150) continue;
    const dec = Math.exp(-age * 0.9);
    y += dec * (72 * gauss(u, 6) - 15 * gauss(u + 13, 5) - 20 * gauss(u - 13, 5) + 13 * gauss(u + 62, 18));
    w = Math.max(w, dec * Math.max(gauss(u + 20, 55), 0));
  }
  return [y, w];
}

function drawTrace(t) {
  // faint ground / baseline
  sdf(0, G - 2, W, G + 6, (x, y) => Math.abs(y - (G + 1.5)) - 1.5);
  flush(C.line, 1);

  const STEP = 3;
  // opening: monitor trace with a sweeping head
  const fadeOpen = 1 - sstep(0.95, 1.24, t);
  if (fadeOpen > 0.003) {
    const head = SWEEP_X0 + SWEEP_V * t;
    const pts = [];
    for (let x = 0; x <= Math.min(W, head); x += STEP) pts.push([x, G + 1.5 - ecg(x)]);
    if (head < W) pts.push([head, G + 1.5 - ecg(head)]);
    for (const pass of [1, 0]) {
      for (let i = 0; i + 1 < pts.length; i++) {
        const [ax, ay] = pts[i], [bx, by] = pts[i + 1];
        const trail = lerp(0.55, 1, clamp(1 - (head - ax) / 900));
        if (pass) capsule(ax, ay, bx, by, 2.5, 0, 0.30 * trail, 9); else capsule(ax, ay, bx, by, 2.6, 0, trail);
      }
      flush(C.coral, fadeOpen, !!pass);
    }
    if (head < W + 20) {
      const hy = G + 1.5 - ecg(head);
      circle(head, hy, 5, 0, 0.5, 14); flush(C.coral, fadeOpen, true);
      circle(head, hy, 5.5); flush(C.coralHot, fadeOpen);
    }
  }
  // CPR: pulses travelling out from the chest
  if (t > beatTime(FIRST_BEAT) - 0.05) {
    const pts = [];
    for (let x = 0; x <= W; x += STEP) {
      const m = pulseMask(x);
      if (m <= 0) { pts.push(null); continue; }
      const [y, w] = pulse(x, t);
      pts.push([x, G + 1.5 - y * m, w * m]);
    }
    for (const pass of [1, 0]) {
      for (let i = 0; i + 1 < pts.length; i++) {
        const a = pts[i], b = pts[i + 1];
        if (!a || !b) continue;
        const w = Math.max(a[2], b[2]);
        if (w < 0.01) continue;
        if (pass) capsule(a[0], a[1], b[0], b[1], 2.5, 0, 0.32 * w, 9); else capsule(a[0], a[1], b[0], b[1], 2.6, 0, Math.min(1, w * 1.5));
      }
      flush(C.coral, 1, !!pass);
    }
  }
}

function drawVictim(t) {
  const a = fallAngle(t);
  const f = clamp(a / (Math.PI / 2));
  const dim = sstep(0.62, 1.3, t);
  const body = mix(C.alive, C.down, dim), shade = mix(C.aliveShade, C.downShade, dim);
  const spread = 15 * (1 - sstep(0.1, 0.9, f));
  const hip = vpt(a, 0, 176, 20);
  const fb = vpt(a, -spread, 20, 20), ff = vpt(a, spread, 20, 20);
  // far leg
  capsule(hip[0], hip[1], fb[0], fb[1], 20 * S); flush(shade);
  // near leg, torso, head
  capsule(hip[0], hip[1], ff[0], ff[1], 20 * S);
  const t0 = vpt(a, 0, 182, 36), t1 = vpt(a, 0, 290, 36);
  capsule(t0[0], t0[1], t1[0], t1[1], 36 * S);
  const hd = vpt(a, 0, 371, 36);
  circle(hd[0], hd[1], 36 * S);
  flush(body);
  // arm resting along the side
  const s0 = vpt(a, -12 * (1 - f), 286, 14), s1 = vpt(a, -10 * (1 - f), 184, 14);
  capsule(s0[0], s0[1], s1[0], s1[1], 14 * S, 3); flush(shade);
  capsule(s0[0], s0[1], s1[0], s1[1], 14 * S); flush(body);

  // the heart
  const hp = vpt(a, 9, HEART_H, 36);
  const d = depth(t);
  let live = 1 - sstep(0.55, 0.9, t);                         // stops
  let sc = 1, sx = 1, sy = 1;
  for (const q of QRS_X) { const tq = (q - SWEEP_X0) / SWEEP_V; if (t >= tq) sc += 0.3 * Math.exp(-(t - tq) / 0.09); }
  if (t > 0.5 && t < 0.9) sc += 0.07 * Math.sin(t * 95) * (1 - sstep(0.7, 0.9, t));   // fibrillation
  if (t > beatTime(FIRST_BEAT) - BEAT / 2) { live = 0.12 + 0.88 * d; sy = 1 - 0.34 * d; sx = 1 + 0.18 * d; }
  const hs = 16.5 * S * sc;
  const hy = hp[1] + d * 21;
  if (live > 0.02) { heart(hp[0], hy, hs, sx, sy, 0, 0.55 * live, 16); flush(C.coral, 1, true); }
  heart(hp[0], hy, hs, sx, sy);
  flush(mix(C.still, C.coral, live));
  return { hp, d };
}

function ik(sx, sy, tx, ty, l1, l2) {
  let dx = tx - sx, dy = ty - sy, d = Math.hypot(dx, dy) || 1e-6;
  const dd = Math.min(d, l1 + l2 - 0.01);
  const a = (l1 * l1 - l2 * l2 + dd * dd) / (2 * dd);
  const h = Math.sqrt(Math.max(l1 * l1 - a * a, 0));
  const ux = dx / d, uy = dy / d;
  let nx = -uy, ny = ux; if (nx < 0) { nx = -nx; ny = -ny; }      // elbow bends back toward the body (right)
  return [sx + ux * a + nx * h, sy + uy * a + ny * h, sx + ux * dd, sy + uy * dd];
}

function rescuerPose(t) {
  const slide = (1 - easeOut((t - T_RESC0) / (T_RESC1 - T_RESC0))) * 640;
  const u = easeInOut((t - T_LEAN0) / (T_LEAN1 - T_LEAN0));           // 0 kneeling upright, 1 over the chest
  const d = depth(t);
  const hipx = HAND_X + 80 * S + slide, hipy = G - 97 * S;
  const knee = [hipx + 7 * S, G - 20 * S], toe = [hipx + 86 * S, G - 18 * S];
  // hands on the chest
  const cx = HAND_X, cy = G - 83 * S + d * 21 * S;
  // shoulder when compressing: straight arms, shoulders above the hands
  const r0 = 115 * S, r1 = 100 * S;
  const ddx = cx - hipx, ddy = cy - hipy, dd = Math.hypot(ddx, ddy);
  const aa = (r0 * r0 - r1 * r1 + dd * dd) / (2 * dd), hh = Math.sqrt(Math.max(r0 * r0 - aa * aa, 0));
  const s1x = hipx + ddx / dd * aa - ddy / dd * hh, s1y = hipy + ddy / dd * aa + ddx / dd * hh;
  const ang1 = Math.atan2(s1x - hipx, -(s1y - hipy));                  // from vertical
  const settle = 0.03 * (1 - easeOut((t - T_RESC0) / 0.75));           // lean into the slide
  const ang0 = -0.10 - settle * 4;
  const ang = lerp(ang0, ang1, u);
  const sh = [hipx + Math.sin(ang) * r0, hipy - Math.cos(ang) * r0];
  const hang = lerp(ang0 - 0.14, ang1 + 0.40, u);                                  // head tips forward to look down
  const head = [sh[0] + Math.sin(hang) * 75 * S, sh[1] - Math.cos(hang) * 75 * S];
  // hands
  const phoneHand = [sh[0] - 72 * S, sh[1] - 6 * S];
  const restHand = [sh[0] - 10 * S, sh[1] + 94 * S];
  const lift = Math.sin(Math.PI * u) * 26 * S;
  const h1 = [lerp(phoneHand[0], cx, u), lerp(phoneHand[1], cy, u) - lift * 0.3];
  const h2 = [lerp(restHand[0], cx, u), lerp(restHand[1], cy, u) - lift];
  return { hip: [hipx, hipy], knee, toe, sh, head, h1, h2, phoneHand, u, slide };
}

function drawRescuer(t, p) {
  if (t < T_RESC0) return;
  const parts = grow => {
    capsule(p.knee[0], p.knee[1], p.toe[0], p.toe[1], 17 * S, grow);
    capsule(p.hip[0], p.hip[1], p.knee[0], p.knee[1], 21 * S, grow);
    capsule(p.hip[0], p.hip[1], p.sh[0], p.sh[1], 34 * S, grow);
    circle(p.head[0], p.head[1], 36 * S, grow);
  };
  const arm = (h, grow) => {
    const e = ik(p.sh[0], p.sh[1], h[0], h[1], 50 * S, 50 * S);
    capsule(p.sh[0], p.sh[1], e[0], e[1], 14 * S, grow);
    capsule(e[0], e[1], e[2], e[3], 14 * S, grow);
    circle(e[2], e[3], 17.5 * S, grow);
  };
  const O = 5;
  // far arm
  arm(p.h2, O); flush(C.ink);
  arm(p.h2, 0); flush(C.youShade);
  // body
  parts(O); flush(C.ink);
  parts(0); flush(C.you);
  // near arm
  arm(p.h1, O); flush(C.ink);
  arm(p.h1, 0); flush(C.you);
}

function phoneState(t, p) {
  // in the hand while calling, then set down by the head on speaker
  const u = easeInOut((t - (T_LEAN0 - 0.08)) / 0.42);
  const hx = p.phoneHand[0] - 4, hy = p.phoneHand[1] - 26;
  const x = lerp(hx, PHONE_REST[0], u), y = lerp(hy, PHONE_REST[1], u) - Math.sin(Math.PI * u) * 70;
  const big = 1 + 0.22 * sstep(T_CALL0 - 0.1, T_CALL0 + 0.15, t) * (1 - u);
  return { x, y, u, sc: big, rot: lerp(-0.12, 0, u) + Math.sin(Math.PI * u) * -0.5 };
}
function drawPhone(t, p) {
  if (t < T_RESC0) return;
  const ph = phoneState(t, p);
  const a = sstep(T_RESC0 + 0.25, T_RESC0 + 0.5, t);
  if (a <= 0) return;
  const hw = PHONE_W * ph.sc, hh = PHONE_H * ph.sc;
  // signal arcs
  const active = sstep(T_CALL0 - 0.05, T_CALL0 + 0.1, t);
  if (active > 0) {
    const quiet = lerp(1, 0.55, ph.u);
    for (let i = 0; i < 3; i++) {
      const ph01 = (((t * 1.9) - i / 3) % 1 + 1) % 1;
      const r = (hh + 4) + ph01 * 44 * ph.sc;
      const al = Math.sin(Math.PI * ph01) * 0.9 * active * quiet * a * (1 - 0.8 * Math.sin(Math.PI * ph.u));
      const dir = lerp(-2.5, -Math.PI / 2, ph.u);          // up-left while held, straight up on the ground
      arc(ph.x, ph.y, r, dir, 0.62, 4.2 * ph.sc);
      flush(C.screen, al);
    }
  }
  rrect(ph.x, ph.y, hw, hh, 7.5 * ph.sc, ph.rot, 4.5); flush(C.ink, a);
  rrect(ph.x, ph.y, hw, hh, 7.5 * ph.sc, ph.rot); flush(C.phone, a);
  rrect(ph.x, ph.y, hw - 4 * ph.sc, hh - 5 * ph.sc, 4 * ph.sc, ph.rot); flush(mix(C.ink, C.screen, 0.18 + 0.82 * active), a);
}

function badge(n, cx, cy, alpha, scale = 1) {
  if (alpha <= 0.003) return;
  circle(cx, cy, 33 * scale); flush(C.you, alpha);
  text([{ s: String(n), font: FONT_HEAVY, size: 50, col: C.ink }], cx, cy + 17.5, alpha, scale, cy);
}

function fadeIO(t, t0, t1, tin = 0.16, tout = 0.14) { return sstep(t0, t0 + tin, t) * (1 - sstep(t1 - tout, t1, t)); }

function drawText(t) {
  const TITLE_Y = 130, SUB_Y = 190;
  // 0. when
  {
    const a = fadeIO(t, T_ASK0, T_ASK1);
    const rise = (1 - easeOut((t - T_ASK0) / 0.3)) * 14;
    const a2 = sstep(T_ASK0 + 0.3, T_ASK0 + 0.46, t);
    const r1 = { s: 'COLLAPSED?', font: FONT_HEAVY, size: 76, col: C.white, track: 2 };
    const r2 = { s: 'NOT BREATHING?', font: FONT_HEAVY, size: 76, col: C.white, track: 2, gap: 34, alpha: a2 };
    text([r1, r2], 640, TITLE_Y + rise, a);
  }
  // 1. call
  {
    const a = fadeIO(t, T_CALL0, T_CALL1);
    const pop = 1 + 0.12 * (1 - easeOut((t - T_CALL0) / 0.25));
    const runs = [{ s: 'CALL', font: FONT_HEAVY, size: 104, col: C.white, track: 4 }];
    const w = measure(runs), bw = 66, gap = 26, total = bw + gap + w;
    badge(1, 640 - total / 2 + bw / 2, TITLE_Y - 37, a, pop);
    text(runs, 640 - total / 2 + bw + gap + w / 2, TITLE_Y, a, pop);
    const sa = a * sstep(T_CALL0 + 0.12, T_CALL0 + 0.3, t);
    const dot = { s: '·', font: FONT_HEAVY, size: 44, col: C.screen, track: 0, gap: 16 };
    const num = (s, g) => ({ s, font: FONT_DEMI, size: 44, col: C.soft, track: 3, gap: g });
    text([num('112', 0), dot, num('911', 16), { ...dot }, num('999', 16)], 640, SUB_Y + 6, sa);
  }
  // 2. push
  {
    const a = fadeIO(t, T_PUSH0, T_PUSH1);
    const d = depth(t);
    const pop = 1 + 0.12 * (1 - easeOut((t - T_PUSH0) / 0.25)) + 0.045 * d;
    const runs = [{ s: 'PUSH', font: FONT_HEAVY, size: 104, col: C.white, track: 4 }];
    const w = measure(runs), bw = 66, gap = 26, total = bw + gap + w;
    badge(2, 640 - total / 2 + bw / 2, TITLE_Y - 37, a, 1 + 0.12 * (1 - easeOut((t - T_PUSH0) / 0.25)));
    text(runs, 640 - total / 2 + bw + gap + w / 2, TITLE_Y, a, pop);
    const sub = (s, col) => ({ s, font: FONT_DEMI, size: 44, col, track: 3 });
    const aA = a * fadeIO(t, T_PUSH0 + 0.14, T_SUBB, 0.18, 0.14);
    text([sub('MIDDLE OF THE CHEST', C.soft)], 640, SUB_Y + 6 + (1 - easeOut((t - T_PUSH0 - 0.14) / 0.3)) * 10, aA);
    const aB = a * fadeIO(t, T_SUBB, T_PUSH1, 0.18, 0.14);
    const dot = { s: '·', font: FONT_HEAVY, size: 44, col: C.coral, track: 0, gap: 18 };
    text([sub('HARD AND FAST', C.soft), dot, { ...sub('2 A SECOND', C.you), gap: 18 }], 640, SUB_Y + 6 + (1 - easeOut((t - T_SUBB) / 0.3)) * 10, aB);
  }
  // 3. why
  {
    const a = sstep(T_END0, T_END0 + 0.2, t);
    const d = depth(t);
    const rise = (1 - easeOut((t - T_END0) / 0.35)) * 12;
    text([{ s: 'UNTIL HELP ARRIVES', font: FONT_DEMI, size: 44, col: C.soft, track: 4 }], 640, 82 + rise, a);
    const big = s => ({ s, font: FONT_HEAVY, size: 72, col: C.white, track: 2 });
    const a2 = a * sstep(T_END0 + 0.22, T_END0 + 0.42, t);
    text([big('YOUR HANDS ARE THEIR'), { ...big('HEARTBEAT'), col: C.coral, gap: 20 }], 640, 166 + rise, a2, 1 + 0.018 * d, 146);
  }
}

// ---------- frame ----------
function renderFrame(t) {
  const d = depth(t);
  // background: dims a touch when the heart stops, warms with every push
  const amb = 1 - 0.14 * sstep(0.6, 1.3, t) + 0.14 * sstep(3.2, 8, t);
  for (let i = 0; i < W * H * 3; i++) cv[i] = bg[i] * amb;
  if (d > 0.01) {
    circle(HAND_X, G - 40, 40, 0, 0.11 * d, 190); flush(C.coral, 1, true);
  }
  // a ring leaves the chest with each compression
  const k1 = Math.floor(t / BEAT);
  for (let k = Math.max(FIRST_BEAT, k1 - 1); k <= k1; k++) {
    const age = t - beatTime(k);
    if (age < 0 || age > 0.62) continue;
    const q = age / 0.62;
    ring(HAND_X, G - 60, 46 + 175 * easeOut(q), 4 * (1 - q) + 1.2); flush(C.coral, 0.5 * Math.pow(1 - q, 1.6));
  }
  drawTrace(t);
  drawVictim(t);
  const p = rescuerPose(t);
  drawRescuer(t, p);
  drawPhone(t, p);
  drawText(t);

  const out = Buffer.allocUnsafe(W * H * 3);
  for (let i = 0, n = W * H; i < n; i++) {
    const dz = dither[i], j = i * 3;
    for (let k = 0; k < 3; k++) {
      const v = (cv[j + k] + dz) * 255 + 0.5;
      out[j + k] = v < 0 ? 0 : v > 255 ? 255 : v | 0;
    }
  }
  return out;
}

module.exports = { W, H, FPS, BEAT, DUR, NFRAMES, FIRST_BEAT, QRS_X, SWEEP_X0, SWEEP_V, T_FALL1, T_CALL0, T_END0, renderFrame };

if (require.main === module) {
  const [mode, a, b] = process.argv.slice(2);
  if (mode === 'still') {
    const buf = renderFrame(parseFloat(a));
    fs.writeFileSync(b, Buffer.concat([Buffer.from(`P6\n${W} ${H}\n255\n`), buf]));
  } else if (mode === 'frames') {
    const f0 = parseInt(a), f1 = Math.min(parseInt(b), NFRAMES - 1);
    for (let f = f0; f <= f1; f++) fs.writeSync(1, renderFrame(f / FPS));
  } else if (mode === 'info') {
    console.log(JSON.stringify({ W, H, FPS, NFRAMES, DUR }));
  } else {
    console.error('usage: render.js frames <first> <last> | still <seconds> <out.ppm> | info');
    process.exit(1);
  }
}
