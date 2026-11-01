// "Wash your hands" — a wordless 10-second film.
// Dirty hands -> water -> soap -> scrub while counting to 20 -> rinse -> clean.

const R = require('./raster');
const { circle, ellipse, capsule, rrect, arc, polygon, blob, grow, union, intersect } = R;

const W = 1080, H = 1080;
const INK = '#2B2F3A';
const SKIN = '#D29A6C', SKIN_BACK = '#C48A5C', SKIN_LINE = '#A86E44';
const SLEEVE = '#3F7FBF', CUFF = '#6FA4DA';
const S = 1.18; // hand scale
const WATER = '#4FB3E8', WATER_HI = '#CDEEFF';

// ---------- helpers ----------
const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
const lerp = (a, b, k) => a + (b - a) * k;
const smooth = (a, b, t) => { const k = clamp((t - a) / (b - a)); return k * k * (3 - 2 * k); };
const easeOutBack = k => { k = clamp(k); const c = 1.70158; return 1 + (c + 1) * (k - 1) ** 3 + c * (k - 1) ** 2; };
const easeIn = k => clamp(k) ** 2;
// 0 -> 1 -> 0 bump between a and b
const bump = (a, b, t) => (t < a || t > b) ? 0 : Math.sin(Math.PI * (t - a) / (b - a));
// 0 -> 1 envelope: ramps up at a, down at b
const env = (a, b, ramp, t) => smooth(a, a + ramp, t) * (1 - smooth(b - ramp, b, t));

function rng(seed) {
  let s = seed >>> 0;
  return () => { s = (s * 1664525 + 1013904223) >>> 0; return s / 4294967296; };
}

// ---------- hand geometry (local space, right hand, palm toward viewer, thumb at +x) ----------
const FINGERS = [ // [baseX, baseY, tipX, tipY, radius]
  [-50, -28, -84, -128, 19], // pinky
  [-17, -44, -32, -180, 21], // ring
  [16, -48, 18, -200, 22],   // middle
  [50, -40, 68, -168, 21],   // index
];
const THUMB = [[46, 58, 102, 4, 26], [102, 4, 132, -50, 23]];

function toWorld(h, lx, ly) {
  const c = Math.cos(h.rot), s = Math.sin(h.rot), k = S * (h.s || 1), x = lx * h.mir * k, y = ly * k;
  return [h.x + x * c - y * s, h.y + x * s + y * c];
}
function capL(h, ax, ay, bx, by, r) {
  const [Ax, Ay] = toWorld(h, ax, ay), [Bx, By] = toWorld(h, bx, by);
  return capsule(Ax, Ay, Bx, By, r * S * (h.s || 1));
}
function rrectL(h, cx, cy, hw, hh, rad) {
  const [X, Y] = toWorld(h, cx, cy);
  const k = S * (h.s || 1);
  return rrect(X, Y, hw * k, hh * k, rad * k, h.rot);
}
function arcL(h, cx, cy, ra, rb, mid, ap) {
  const [X, Y] = toWorld(h, cx, cy);
  const m = Math.atan2(Math.sin(mid), Math.cos(mid) * h.mir) + h.rot;
  return arc(X, Y, ra * S * (h.s || 1), rb, m, ap);
}

// A crease drawn where two overlapping shapes meet (their distance bisector),
// limited to the inside of both and stopping `depth` px into the palm.
function crease(a, b, palm, depth) {
  const [fa, ba] = a, [fb] = b, [fp] = palm;
  return [(x, y) => {
    const da = fa(x, y), db = fb(x, y);
    return Math.max(Math.abs(da - db) * 0.5 - 1.4, Math.max(da, db) + 3, -fp(x, y) - depth);
  }, ba];
}

function drawHand(cv, h, skin) {
  // sleeve (mostly hidden behind the sink)
  cv.fill(...grow(rrectL(h, 0, 320, 72, 100, 22), 5), INK);
  cv.fill(...rrectL(h, 0, 320, 72, 100, 22), SLEEVE);
  const palm = rrectL(h, 0, 18, 74, 84, 44);
  const wrist = capL(h, 0, 60, 0, 190, 50);
  const fingers = FINGERS.map(f => capL(h, ...f));
  const thumb = union(THUMB.map(f => capL(h, ...f)));
  const all = union([palm, wrist, thumb, ...fingers]);
  cv.fill(...grow(all, 5), INK);
  cv.fill(...all, skin);
  // finger creases
  for (let i = 0; i < 3; i++) cv.fill(...crease(fingers[i], fingers[i + 1], palm, 14), INK, 0.9);
  cv.fill(...crease(thumb, palm, palm, 1e9), SKIN_LINE, 0.9);
  // palm lines
  cv.fill(...arcL(h, 62, 78, 70, 2, -2.55, 0.62), SKIN_LINE, 0.85);
  cv.fill(...arcL(h, 10, 70, 82, 2, -1.75, 0.42), SKIN_LINE, 0.7);
  // cuff
  cv.fill(...grow(rrectL(h, 0, 222, 64, 20, 14), 5), INK);
  cv.fill(...rrectL(h, 0, 222, 64, 20, 14), CUFF);
}

// Random points that lie on the hand (local coordinates).
function handPoints(seed, n, margin = 6) {
  const r = rng(seed), pts = [];
  while (pts.length < n) {
    if (r() < 0.55) {
      pts.push([lerp(-60, 60, r()), lerp(-30, 85, r())]);
    } else {
      const f = r() < 0.15 ? THUMB[1] : FINGERS[Math.floor(r() * 4)];
      const k = lerp(0.15, 0.9, r());
      pts.push([lerp(f[0], f[2], k) + (r() - 0.5) * margin, lerp(f[1], f[3], k)]);
    }
  }
  return pts;
}

// ---------- choreography ----------
const POSE = {
  apartL: { x: 330, y: 600, rot: -0.12 }, apartR: { x: 750, y: 600, rot: 0.12 },
  centerL: { x: 478, y: 600, rot: 0.38 }, centerR: { x: 602, y: 600, rot: -0.38 },
};
const SCRUB = [3.0, 7.0];
const WATER_ON = [[1.15, 2.3], [7.0, 7.95]];

function centered(t) { return smooth(1.3, 1.9, t) * (1 - smooth(7.95, 8.5, t)); }

function pose(t) {
  const c = centered(t);
  const L = { mir: -1 }, Rh = { mir: 1 };
  for (const k of ['x', 'y', 'rot']) {
    L[k] = lerp(POSE.apartL[k], POSE.centerL[k], c);
    Rh[k] = lerp(POSE.apartR[k], POSE.centerR[k], c);
  }
  // enter from below
  const rise = 460 * (1 - easeOutBack(t / 0.75));
  L.y += rise; Rh.y += rise * 1.08;
  // scrubbing: hands slide against each other
  const A = 40 * env(SCRUB[0], SCRUB[1], 0.25, t);
  const s = Math.sin(2 * Math.PI * 2.4 * (t - SCRUB[0]));
  Rh.x += A * s; Rh.y -= A * 0.55 * s; Rh.rot += 0.0016 * A * s;
  L.x -= A * s; L.y += A * 0.55 * s; L.rot += 0.0016 * A * s;
  // rinse: turning under the water
  const r = env(7.0, 7.95, 0.15, t) * Math.sin(2 * Math.PI * 2.2 * (t - 7.0));
  L.y += 10 * r; Rh.y -= 10 * r; L.rot += 0.06 * r; Rh.rot += 0.06 * r;
  // final: gentle happy sway
  const f = smooth(8.4, 8.9, t);
  const sw = Math.sin(2 * Math.PI * 0.9 * (t - 8.4));
  L.rot -= 0.05 * f * sw; Rh.rot -= 0.05 * f * sw;
  L.y -= 12 * f; Rh.y -= 12 * f;
  return { L, R: Rh };
}

// Germs, foam bubbles, water droplets and sparkles — all attached to hands.
const GERM_SPOTS = {
  R: [[-28, 10], [30, 55], [18, -150], [-38, -120], [66, -130], [104, -8]],
  L: [[22, 30], [-30, 62], [-6, -170], [55, -108], [-74, -100], [118, -36]],
};
const GERM_COLORS = ['#6CC04A', '#9B6BDB', '#4FB59A', '#E0A030', '#6CC04A', '#9B6BDB'];
const GERMS = [];
['L', 'R'].forEach((side, si) => GERM_SPOTS[side].forEach((p, i) => GERMS.push({
  side, p, size: 21 + ((i * 7 + si * 3) % 4) * 3, color: GERM_COLORS[(i + si * 2) % 6],
  born: 0.45 + 0.09 * (i * 2 + si), seed: i * 1.7 + si * 4.1,
})));
// pop order interleaves both hands across the scrub
{
  const order = [7, 0, 9, 2, 11, 4, 6, 1, 10, 3, 8, 5];
  order.forEach((g, k) => { GERMS[g].pop = 3.45 + k * 0.27; });
}

function makeBubbles(seed, side) {
  const r = rng(seed + 99);
  return handPoints(seed, 64).map(p => ({
    side, p, r: lerp(10, 30, r() ** 1.5), born: lerp(2.6, 4.6, r()), wob: r() * 6.28,
    drop: lerp(7.05, 7.7, r()), vx: (r() - 0.5) * 160,
  }));
}
const BUBBLES = { L: makeBubbles(11, 'L'), R: makeBubbles(23, 'R') };
const DROPS = { L: handPoints(5, 11, 0), R: handPoints(8, 11, 0) };
const SPARKS = {
  L: [[-30, 20, 0], [10, -175, 0.25], [-70, -110, 0.5], [110, -40, 0.15]],
  R: [[30, 30, 0.35], [-20, -170, 0.05], [72, -150, 0.45], [-80, -80, 0.6]],
};
// a few free bubbles that float up while scrubbing
const FLOATERS = (() => {
  const r = rng(77), out = [];
  for (let i = 0; i < 14; i++) out.push({ t0: lerp(3.4, 6.6, r()), x: lerp(440, 640, r()), r: lerp(7, 15, r()), vx: (r() - 0.5) * 80 });
  return out;
})();

function drawGerm(cv, x, y, s, color, t, seed, alpha = 1) {
  const ph = t * 5 + seed;
  y += 3 * Math.sin(t * 7 + seed);
  const body = blob(x, y, s, 0.13, 7, ph);
  cv.fill(...grow(body, 3.5), INK, alpha);
  cv.fill(...body, color, alpha);
  // spots
  cv.fill(...circle(x - s * 0.45, y + s * 0.42, s * 0.12), INK, 0.18 * alpha);
  cv.fill(...circle(x + s * 0.5, y + s * 0.28, s * 0.09), INK, 0.18 * alpha);
  // angry eyes + brows + frown
  for (const sx of [-1, 1]) {
    cv.fill(...circle(x + sx * s * 0.32, y - s * 0.1, s * 0.26), '#FFFFFF', alpha);
    cv.fill(...circle(x + sx * s * 0.28, y - s * 0.06, s * 0.12), INK, alpha);
    cv.fill(...capsule(x + sx * s * 0.56, y - s * 0.5, x + sx * s * 0.12, y - s * 0.3, s * 0.07 + 0.6), INK, alpha);
  }
  cv.fill(...arc(x, y + s * 0.62, s * 0.3, s * 0.06 + 0.6, -Math.PI / 2, 0.75), INK, alpha);
}

function drawBubble(cv, x, y, r, alpha = 1) {
  cv.fill(...grow(circle(x, y, r), 2.5), '#8CC8E6', alpha);
  cv.fill(...circle(x, y, r), '#F7FCFF', alpha);
  cv.fill(...arc(x, y, r * 0.62, Math.max(1, r * 0.08), -2.35, 0.5), '#BFE3F5', alpha);
  cv.fill(...circle(x + r * 0.38, y - r * 0.38, r * 0.16), '#FFFFFF', alpha);
}

function sparkle(cv, x, y, s, color, alpha = 1) {
  if (s <= 0.5) return;
  const pts = [];
  for (let i = 0; i < 32; i++) {
    const a = (i / 32) * Math.PI * 2;
    const k = Math.pow(Math.abs(Math.cos(2 * a)), 6);
    const rr = s * (0.22 + 0.78 * k);
    pts.push([x + Math.cos(a) * rr, y + Math.sin(a) * rr]);
  }
  cv.fill(...polygon(pts), color, alpha);
}

function heartShape(cx, cy, s) {
  const pts = [];
  for (let i = 0; i < 72; i++) {
    const a = (i / 72) * Math.PI * 2;
    const x = 16 * Math.sin(a) ** 3;
    const y = -(13 * Math.cos(a) - 5 * Math.cos(2 * a) - 2 * Math.cos(3 * a) - Math.cos(4 * a));
    pts.push([cx + x * s, cy + y * s]);
  }
  return polygon(pts);
}

// Seven-segment digits with rounded strokes.
const SEG = { a: [0, 0, 1, 0], b: [1, 0, 1, 0.5], c: [1, 0.5, 1, 1], d: [0, 1, 1, 1], e: [0, 0.5, 0, 1], f: [0, 0, 0, 0.5], g: [0, 0.5, 1, 0.5] };
const DIGITS = ['abcdef', 'bc', 'abged', 'abgcd', 'fgbc', 'afgcd', 'afgedc', 'abc', 'abcdefg', 'abcdfg'];
function drawNumber(cv, n, cx, cy, h, color, alpha = 1) {
  const s = String(n), w = h * 0.5, gap = h * 0.28, th = h * 0.1;
  const total = s.length * w + (s.length - 1) * gap;
  let x0 = cx - total / 2;
  for (const ch of s) {
    for (const k of DIGITS[+ch]) {
      const [a, b, c, d] = SEG[k];
      cv.fill(...capsule(x0 + a * w, cy - h / 2 + b * h, x0 + c * w, cy - h / 2 + d * h, th), color, alpha);
    }
    x0 += w + gap;
  }
}

// ---------- background (precomputed) ----------
let BG = null;
function background(cv) {
  if (BG) { cv.buf.set(BG); return; }
  const [r0, g0, b0] = R.hex('#FFF4E2'), [r1, g1, b1] = R.hex('#FBE6C8');
  for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
    const k = clamp(Math.hypot(x - 540, y - 560) / 820);
    const i = (y * W + x) * 3;
    cv.buf[i] = lerp(r0, r1, k); cv.buf[i + 1] = lerp(g0, g1, k); cv.buf[i + 2] = lerp(b0, b1, k);
  }
  // subtle wall tiles
  for (let x = 60; x < W; x += 160) cv.fill(...rrect(x, 540, 1.5, 600, 1), '#EBD9BC', 0.7);
  for (let y = 40; y < H; y += 160) cv.fill(...rrect(540, y, 600, 1.5, 1), '#EBD9BC', 0.7);
  BG = Float32Array.from(cv.buf);
}

// ---------- water ----------
function waterSpan(t) {
  for (const [on, off] of WATER_ON) {
    if (t < on || t > off + 0.6) continue;
    const top = 236 + Math.max(0, t - off) * 2600;
    const bot = 236 + (t - on) * 2600;
    return { top, bot, on };
  }
  return null;
}

function drawTap(cv, t) {
  const open = Math.max(env(1.0, 2.35, 0.18, t), env(6.85, 8.0, 0.18, t));
  const metal = '#A9B6C3', hi = '#E6EDF3';
  // lever handle
  const a = lerp(-1.75, -0.75, open);
  const lx = 540 + Math.cos(a) * 86, ly = 120 + Math.sin(a) * 86;
  cv.fill(...grow(capsule(540, 120, lx, ly, 13), 5), INK);
  cv.fill(...capsule(540, 120, lx, ly, 13), '#E2575E');
  const pipe = rrect(540, 40, 26, 100, 10), head = rrect(540, 170, 62, 36, 24), nozzle = rrect(540, 218, 22, 20, 7);
  const all = union([pipe, head, nozzle]);
  cv.fill(...grow(all, 5), INK);
  cv.fill(...all, metal);
  cv.fill(...capsule(500, 160, 580, 160, 6), hi, 0.9);
  cv.fill(...capsule(530, -20, 530, 120, 5), hi, 0.8);
  cv.fill(...grow(circle(540, 120, 15), 5), INK);
  cv.fill(...circle(540, 120, 15), '#E2575E');
}

function drawStream(cv, t, endY) {
  const sp = waterSpan(t);
  if (!sp) return null;
  const top = sp.top, bot = Math.min(sp.bot, endY);
  if (bot <= top) return null;
  const segs = [];
  for (let y = top; y < bot; y += 24) {
    const y2 = Math.min(bot, y + 24);
    const x1 = 540 + 3 * Math.sin(y * 0.045 - t * 28), x2 = 540 + 3 * Math.sin(y2 * 0.045 - t * 28);
    segs.push(capsule(x1, y, x2, y2, 13));
  }
  const s = union(segs);
  cv.fill(...s, WATER, 0.92);
  cv.fill(...capsule(535, top + 8, 535, bot - 8, 3), WATER_HI, 0.9);
  return { top, bot, on: sp.on, hitting: sp.bot >= endY };
}

function drawSplash(cv, t, endY, sp) {
  if (!sp || !sp.hitting || endY > 800) return;
  const r = rng(4242);
  for (let i = 0; i < 70; i++) {
    const birth = sp.on + 0.1 + i * 0.025, life = 0.45;
    const vx = (r() - 0.5) * 560, vy = -lerp(120, 380, r()), size = lerp(4, 9, r());
    const age = t - birth;
    if (age < 0 || age > life) continue;
    // only while the stream is still flowing at birth
    const flowing = waterSpan(birth);
    if (!flowing || flowing.top > endY - 10) continue;
    const x = 540 + vx * age, y = endY + vy * age + 1400 * age * age;
    const a = 1 - age / life;
    cv.fill(...circle(x, y, size * (0.6 + 0.4 * a)), WATER, 0.9 * a);
  }
}

function drawSink(cv) {
  const basin = rrect(540, 1030, 510, 120, 60);
  cv.fill(...grow(basin, 5), INK);
  cv.fill(...basin, '#FFFFFF');
  cv.fill(...rrect(540, 1010, 470, 6, 6), '#E3EEF5');
  const rim = rrect(540, 912, 520, 18, 18);
  cv.fill(...grow(rim, 5), INK);
  cv.fill(...rim, '#EEF4F8');
  cv.fill(...capsule(80, 906, 1000, 906, 3.5), '#FFFFFF');
}

function drawSoap(cv, t) {
  if (t < 2.15 || t > 3.45) return;
  let x, y, rot;
  if (t < 2.6) { const k = easeOutBack((t - 2.15) / 0.45); x = lerp(1220, 640, k); y = lerp(500, 560, k); rot = lerp(0.6, -0.15, k); }
  else if (t < 3.05) { const p = 2 * Math.PI * 3 * (t - 2.6); x = 600 + 70 * Math.sin(p) + 40; y = 555 + 25 * Math.cos(p); rot = -0.15 + 0.15 * Math.sin(p); }
  else { const k = easeIn((t - 3.05) / 0.4); x = lerp(640, 1250, k); y = lerp(580, 330, k); rot = lerp(-0.15, 0.8, k); }
  const bar = rrect(x, y, 66, 38, 24, rot);
  cv.fill(...grow(bar, 5), INK);
  cv.fill(...bar, '#FF8FAB');
  const c = Math.cos(rot), s = Math.sin(rot);
  cv.fill(...rrect(x - 8 * c + 12 * s, y - 8 * s - 12 * c, 40, 9, 9, rot), '#FFC4D3');
  drawBubble(cv, x + 50 * c - 30 * s, y + 50 * s + 30 * c, 12);
  drawBubble(cv, x - 40 * c - 34 * s, y - 40 * s + 34 * c, 9);
}

function drawTimer(cv, t) {
  const appear = easeOutBack((t - 2.8) / 0.4);
  if (appear <= 0.01) return;
  const p = clamp((t - SCRUB[0]) / (SCRUB[1] - SCRUB[0]));
  const done = t >= SCRUB[1];
  const sc = appear * (1 + 0.14 * bump(SCRUB[1], SCRUB[1] + 0.35, t) + 0.05 * bump(9.0, 9.4, t));
  const cx = 888, cy = 190, Rr = 92 * sc;
  cv.fill(...grow(circle(cx, cy, 110 * sc), 5), INK);
  cv.fill(...circle(cx, cy, 110 * sc), '#FFFFFF');
  cv.fill(...arc(cx, cy, Rr, 9 * sc, 0, Math.PI), '#EFE4D2');
  const col = done ? '#3DB54A' : '#2AAFA0';
  if (p > 0) cv.fill(...arc(cx, cy, Rr, 9 * sc, -Math.PI / 2 + p * Math.PI, p * Math.PI), col);
  // tick dots for each count
  for (let i = 0; i < 20; i++) {
    const a = -Math.PI / 2 + (i + 1) / 20 * 2 * Math.PI;
    if ((i + 1) / 20 <= p + 1e-6) cv.fill(...circle(cx + Math.cos(a) * Rr, cy + Math.sin(a) * Rr, 3 * sc), '#FFFFFF', 0.85);
  }
  const n = Math.max(1, Math.min(20, Math.ceil(p * 20)));
  const local = (t - SCRUB[0]) - (n - 1) * 0.2;
  const pop = t > SCRUB[0] && t < SCRUB[1] ? 1 + 0.18 * Math.max(0, 1 - local / 0.12) : 1;
  drawNumber(cv, n, cx, cy, 64 * sc * pop, done ? '#3DB54A' : INK);
}

// ---------- frame ----------
function drawFrame(cv, t) {
  background(cv);

  // soft glow behind the hands, blooms at the end
  const fin = smooth(8.3, 9.0, t);
  const glowR = 400 + 50 * fin + 12 * fin * Math.sin(2 * Math.PI * 1.1 * t);
  cv.fill(...circle(540, 580, glowR), '#CDEFEA', 0.9);
  cv.fill(...circle(540, 580, glowR * 0.72), '#DDF5F1', 0.7 * fin);

  // celebration rings
  for (const t0 of [8.55, 8.95, 9.35]) {
    const k = (t - t0) / 1.0;
    if (k > 0 && k < 1) cv.fill(...arc(540, 470, lerp(60, 430, Math.sqrt(k)), 5, 0, Math.PI), '#FF7A8C', 0.45 * (1 - k));
  }

  drawTap(cv, t);

  const P = pose(t);
  const c = centered(t);
  const endY = lerp(930, 372, smooth(0.35, 0.75, c));
  const stream = drawStream(cv, t, endY);

  const foamVis = smooth(2.55, 3.1, t);
  for (const side of ['L', 'R']) {
    const h = P[side];
    drawHand(cv, h, side === 'L' ? SKIN_BACK : SKIN);

    // water droplets on wet hands
    const wet = smooth(1.55, 1.9, t) * (1 - smooth(2.7, 3.2, t)) + env(7.05, 8.6, 0.3, t) * 0.8;
    if (wet > 0.01) DROPS[side].forEach(([lx, ly], i) => {
      const [x, y] = toWorld(h, lx, ly);
      const dy = ((t * 40 + i * 13) % 26);
      cv.fill(...ellipse(x, y + dy, 6, 8.5), WATER, 0.85 * wet);
      cv.fill(...circle(x - 2, y + dy - 3, 2.2), '#FFFFFF', 0.9 * wet);
    });

    // germs
    for (const g of GERMS) {
      if (g.side !== side) continue;
      const [x, y] = toWorld(h, ...g.p);
      let s = g.size * S * easeOutBack((t - g.born) / 0.3);
      if (t < g.born) continue;
      if (t >= g.pop) {
        const k = (t - g.pop) / 0.22;
        if (k < 1) {
          s *= k < 0.3 ? 1 + k : (1.3 * (1 - (k - 0.3) / 0.7));
          // burst
          for (let j = 0; j < 8; j++) {
            const a = j / 8 * 2 * Math.PI + g.seed, r0 = g.size * lerp(0.9, 2.2, k), r1 = r0 + g.size * 0.5 * (1 - k);
            cv.fill(...capsule(x + Math.cos(a) * r0, y + Math.sin(a) * r0, x + Math.cos(a) * r1, y + Math.sin(a) * r1, 3), '#FFFFFF', 1 - k);
          }
        } else s = 0;
        if (k > 0.2 && k < 2.2) sparkle(cv, x, y, 20 * bump(0.2, 2.2, k), '#FFFFFF', 0.95);
      }
      if (s > 0.5) drawGerm(cv, x, y, s, g.color, t, g.seed);
    }

    // foam
    if (foamVis > 0) for (const b of BUBBLES[side]) {
      const grown = smooth(b.born, b.born + 0.35, t);
      if (grown <= 0) continue;
      const wob = 1 + 0.07 * Math.sin(t * 9 + b.wob);
      if (t < b.drop) {
        const [x, y] = toWorld(h, ...b.p);
        drawBubble(cv, x, y, b.r * grown * wob);
      } else {
        // washed away: falls from where it was when the water hit it
        const [x0, y0] = toWorld(pose(b.drop), ...b.p);
        const age = t - b.drop, a = 1 - age / 0.55;
        if (a > 0) drawBubble(cv, x0 + b.vx * age, y0 + 900 * age * age + 60 * age, b.r * wob * (0.5 + 0.5 * a), a);
      }
    }

    // sparkles once clean
    for (const [lx, ly, ph] of SPARKS[side]) {
      const tt = t - 7.7 - ph;
      if (tt < 0) continue;
      const s = Math.max(0, Math.sin(Math.PI * ((tt % 1.1) / 1.1))) * 26;
      const [x, y] = toWorld(h, lx, ly);
      sparkle(cv, x, y, s, '#FFD84D');
      sparkle(cv, x, y, s * 0.45, '#FFFFFF');
    }
  }

  // floating soap bubbles while scrubbing
  for (const f of FLOATERS) {
    const age = t - f.t0;
    if (age < 0 || age > 1.3) continue;
    const a = age > 1.1 ? 1 - (age - 1.1) / 0.2 : 1;
    drawBubble(cv, f.x + f.vx * age + 10 * Math.sin(age * 6), 420 - 220 * age, f.r * (0.6 + 0.4 * Math.min(1, age * 4)), a);
  }

  drawSplash(cv, t, endY, stream);
  drawSoap(cv, t);
  drawSink(cv);
  drawTimer(cv, t);

  // heart
  const hs = easeOutBack((t - 8.45) / 0.45);
  if (hs > 0.01) {
    const beat = 1 + 0.08 * Math.max(0, Math.sin(2 * Math.PI * 1.1 * (t - 8.9))) ** 4;
    const s = 4.6 * hs * beat, hy = 470;
    const heart = heartShape(540, hy, s);
    cv.fill(...grow(heart, 5), INK);
    cv.fill(...heart, '#FF5D73');
    cv.fill(...ellipse(540 - 7.5 * s, hy - 5 * s, 3.2 * s, 2 * s, -0.6), '#FFFFFF', 0.75);
  }
}

module.exports = { W, H, INK, SKIN, drawFrame, drawHand, drawBubble, drawNumber, sparkle, heartShape };
