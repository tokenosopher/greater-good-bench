// A field of 800 dots: one for every ten million people alive.
// A slow wave of attention moves across them. Hover brings a few into focus.

import { clamp } from './format.js';

const COLS = 40;
const ROWS = 20;
const TOTAL = COLS * ROWS;

export function initHero() {
  const canvas = document.querySelector('#dotfield');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const wrap = canvas.parentElement;
  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  let w = 0;
  let h = 0;
  let dpr = 1;
  let dots = [];
  let running = false;
  let visible = true;
  let pointer = null;
  let t0 = performance.now();

  const rand = mulberry32(20261029);

  function resize() {
    const rect = wrap.getBoundingClientRect();
    w = Math.max(1, rect.width);
    h = Math.max(1, rect.height);
    dpr = Math.min(window.devicePixelRatio || 1, 2);
    canvas.width = Math.round(w * dpr);
    canvas.height = Math.round(h * dpr);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    layout();
  }

  function layout() {
    dots = [];
    const padX = 18;
    const padY = 16;
    const gw = w - padX * 2;
    const gh = h - padY * 2;
    for (let y = 0; y < ROWS; y++) {
      for (let x = 0; x < COLS; x++) {
        const px = padX + (gw * x) / (COLS - 1);
        const py = padY + (gh * y) / (ROWS - 1);
        dots.push({
          x: px,
          y: py,
          phase: rand() * Math.PI * 2,
          bias: rand(),
          r: 0.9 + rand() * 0.7,
        });
      }
    }
  }

  function draw(now) {
    if (!visible) {
      if (running) requestAnimationFrame(draw);
      return;
    }
    const t = (now - t0) / 1000;
    ctx.clearRect(0, 0, w, h);

    // two attention sources drifting slowly
    const ax = w * (0.5 + 0.34 * Math.sin(t * 0.19 + 0.7));
    const ay = h * (0.5 + 0.32 * Math.sin(t * 0.27 + 2.1));
    const bx = w * (0.5 + 0.3 * Math.sin(t * 0.14 + 4.0));
    const by = h * (0.5 + 0.34 * Math.cos(t * 0.21 + 1.3));
    const reach = Math.min(w, h) * 0.42;

    for (let i = 0; i < TOTAL; i++) {
      const d = dots[i];
      let glow = 0;
      let accent = 0;

      if (!reduced) {
        const da = Math.hypot(d.x - ax, d.y - ay);
        const db = Math.hypot(d.x - bx, d.y - by);
        const ga = Math.exp(-(da * da) / (2 * reach * reach * 0.16));
        const gb = Math.exp(-(db * db) / (2 * reach * reach * 0.2));
        glow = Math.max(ga, gb * 0.75);
        accent = gb > ga ? 1 : 0;
        // a little breathing so the field feels alive
        glow *= 0.75 + 0.25 * Math.sin(t * 0.8 + d.phase);
      } else {
        glow = d.bias > 0.86 ? 0.9 : 0.08;
      }

      if (pointer) {
        const dp = Math.hypot(d.x - pointer.x, d.y - pointer.y);
        const gp = Math.exp(-(dp * dp) / (2 * 46 * 46));
        if (gp > glow) {
          glow = gp;
          accent = 0.35;
        }
      }

      const baseAlpha = 0.11 + d.bias * 0.05;
      const r = d.r + glow * 1.7;

      if (glow > 0.04) {
        // soft halo
        ctx.beginPath();
        ctx.fillStyle = accent > 0.5
          ? `rgba(124, 224, 207, ${glow * 0.11})`
          : `rgba(216, 242, 107, ${glow * 0.12})`;
        ctx.arc(d.x, d.y, r + 5, 0, Math.PI * 2);
        ctx.fill();
      }

      ctx.beginPath();
      if (glow > 0.03) {
        const a = clamp(baseAlpha + glow * 0.95, 0, 1);
        ctx.fillStyle = accent > 0.5
          ? `rgba(124, 224, 207, ${a})`
          : `rgba(216, 242, 107, ${a})`;
      } else {
        ctx.fillStyle = `rgba(241, 239, 229, ${baseAlpha})`;
      }
      ctx.arc(d.x, d.y, r, 0, Math.PI * 2);
      ctx.fill();
    }

    if (running) requestAnimationFrame(draw);
  }

  resize();
  new ResizeObserver(resize).observe(wrap);

  if (reduced) {
    draw(performance.now());
  } else {
    running = true;
    requestAnimationFrame(draw);
  }

  wrap.addEventListener('pointermove', (e) => {
    const rect = wrap.getBoundingClientRect();
    pointer = { x: e.clientX - rect.left, y: e.clientY - rect.top };
  });
  wrap.addEventListener('pointerleave', () => { pointer = null; });

  document.addEventListener('visibilitychange', () => {
    visible = !document.hidden;
    if (visible && running && !reduced) requestAnimationFrame(draw);
  });

  const io = new IntersectionObserver(([entry]) => {
    visible = entry.isIntersecting && !document.hidden;
  }, { threshold: 0.05 });
  io.observe(wrap);
}

function mulberry32(a) {
  return function () {
    let t = (a += 0x6d2b79f5);
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
