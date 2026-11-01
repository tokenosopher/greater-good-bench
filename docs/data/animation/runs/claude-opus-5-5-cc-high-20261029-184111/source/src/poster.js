// Wordless printable poster: four steps from the film + "when" strip
// (after the toilet -> wash -> before eating).
// Usage: node src/poster.js out.png
const { spawn } = require('child_process');
const { Canvas, circle, ellipse, capsule, rrect, arc, polygon, grow, intersect, union } = require('./raster');
const { W, H, INK, SKIN, drawFrame, drawHand, drawBubble, drawNumber, sparkle } = require('./scene');

const PW = 1080, PH = 1350, STRIP = 1080;
const poster = new Canvas(PW, PH);
const scene = new Canvas(W, H);

// background
poster.fill(...rrect(PW / 2, PH / 2, PW, PH, 0), '#FFF4E2');

// 1. four steps, each frame downsampled 2x into a 540 tile
const STEPS = [2.0, 2.75, 5.3, 7.7];
STEPS.forEach((t, i) => {
  drawFrame(scene, t);
  const ox = (i % 2) * 540, oy = Math.floor(i / 2) * 540;
  for (let y = 0; y < 540; y++) for (let x = 0; x < 540; x++) {
    for (let c = 0; c < 3; c++) {
      const s = (j, k) => scene.buf[((y * 2 + k) * W + x * 2 + j) * 3 + c];
      poster.buf[((oy + y) * PW + ox + x) * 3 + c] = (s(0, 0) + s(1, 0) + s(0, 1) + s(1, 1)) / 4;
    }
  }
});
// tile separators + step numbers
poster.fill(...rrect(540, 540, 5, 540, 0), '#FFF4E2');
poster.fill(...rrect(540, 540, 540, 5, 0), '#FFF4E2');
STEPS.forEach((_, i) => {
  const cx = (i % 2) * 540 + 52, cy = Math.floor(i / 2) * 540 + 52;
  poster.fill(...grow(circle(cx, cy, 30), 4), '#FFFFFF');
  poster.fill(...circle(cx, cy, 30), INK);
  drawNumber(poster, i + 1, cx, cy, 30, '#FFFFFF');
});

// 2. "when" strip
poster.fill(...rrect(PW / 2, STRIP + 135, PW, 135, 0), '#FBE6C8');
poster.fill(...rrect(PW / 2, STRIP + 3, PW, 3, 0), INK);
const CY = STRIP + 135;

function badge(cx, fill) {
  poster.fill(...grow(circle(cx, CY, 100), 5), INK);
  poster.fill(...circle(cx, CY, 100), fill);
}

function arrow(x0, x1) {
  poster.fill(...capsule(x0, CY, x1 - 20, CY, 7), INK);
  poster.fill(...polygon([[x1 - 30, CY - 22], [x1 + 4, CY], [x1 - 30, CY + 22]]), INK);
}

// toilet (side view)
function toilet(cx, cy) {
  const tank = rrect(cx - 42, cy - 34, 20, 42, 8);
  const bowl = intersect(ellipse(cx + 10, cy - 6, 50, 44), rrect(cx + 10, cy + 30, 60, 36, 0));
  const base = rrect(cx + 2, cy + 50, 22, 18, 6);
  const seat = capsule(cx - 30, cy - 8, cx + 58, cy - 8, 8);
  for (const s of [base, tank, bowl, seat]) { poster.fill(...grow(s, 5), INK); poster.fill(...s, '#FFFFFF'); }
  poster.fill(...capsule(cx - 52, cy - 62, cx - 36, cy - 62, 4), '#A9B6C3');
}

// steaming bowl of food
function food(cx, cy) {
  const rice = intersect(circle(cx, cy + 6, 46), rrect(cx, cy - 30, 60, 36, 0));
  poster.fill(...grow(rice, 5), INK);
  poster.fill(...rice, '#FFFFFF');
  const bowl = intersect(ellipse(cx, cy + 6, 66, 52), rrect(cx, cy + 40, 70, 34, 0));
  poster.fill(...grow(bowl, 5), INK);
  poster.fill(...bowl, '#F2A541');
  poster.fill(...capsule(cx - 30, cy + 30, cx + 30, cy + 30, 4), '#F8C77A');
  for (const dx of [-24, 0, 24]) {
    const pts = [];
    for (let y = cy - 48; y >= cy - 98; y -= 5) pts.push([cx + dx + 7 * Math.sin((y - cy) * 0.13), y]);
    poster.fill(...union(pts.slice(1).map((q, j) => capsule(...pts[j], ...q, 3.5))), INK, 0.55);
  }
}

// clean soapy hand, clipped to its badge
function washIcon(cx) {
  const tmp = new Canvas(PW, PH);
  tmp.fill(...rrect(cx, CY, 110, 110, 0), '#CDEFEA');
  drawHand(tmp, { x: cx - 6, y: CY + 38, rot: 0.08, mir: 1, s: 0.42 }, SKIN);
  for (const [dx, dy, r] of [[-26, 30, 13], [-6, 44, 16], [18, 34, 11], [-40, 54, 10], [30, 56, 12]]) drawBubble(tmp, cx + dx, CY + dy, r);
  sparkle(tmp, cx + 52, CY - 62, 22, '#FFD84D');
  sparkle(tmp, cx - 50, CY - 30, 14, '#FFD84D');
  const [mask] = circle(cx, CY, 100);
  for (let y = CY - 101; y < CY + 101; y++) for (let x = cx - 101; x < cx + 101; x++) {
    const a = Math.max(0, Math.min(1, 0.5 - mask(x + 0.5, y + 0.5)));
    const i = (y * PW + x) * 3;
    for (let c = 0; c < 3; c++) poster.buf[i + c] += (tmp.buf[i + c] - poster.buf[i + c]) * a;
  }
}

badge(220, '#DDF5F1'); toilet(220, CY + 4);
arrow(338, 420);
badge(540, '#CDEFEA'); washIcon(540);
arrow(660, 742);
badge(860, '#DDF5F1'); food(860, CY + 8);

const p = spawn('ffmpeg', ['-y', '-hide_banner', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
  '-s', `${PW}x${PH}`, '-i', '-', '-frames:v', '1', process.argv[2]], { stdio: ['pipe', 'inherit', 'inherit'] });
p.stdin.end(poster.toBytes());
