// A field of 1,000 dots: each dot is ~8.1 million people, sorted by income
// (poorest top-left... actually row-major, poorest first). Recolors in a wave
// radiating from "you" whenever your percentile changes.

const N = 1000;
const POOR = [92, 116, 152, 0.35];
const RICH = [245, 178, 91, 0.65];
const YOU = [255, 255, 255, 1];

export class DotField {
  constructor(canvas) {
    this.canvas = canvas;
    this.ctx = canvas.getContext('2d');
    this.dots = [];
    this.userIndex = -1;
    this.waveStart = -1;
    this.reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
    this._resize = () => this.layout();
    addEventListener('resize', this._resize);
    this.layout();
    this._loop = (t) => this.frame(t);
    requestAnimationFrame(this._loop);
  }

  layout() {
    const dpr = Math.min(2, devicePixelRatio || 1);
    const w = Math.max(240, this.canvas.clientWidth || this.canvas.parentElement.clientWidth);
    const cols = w < 480 ? 40 : 50;
    const rows = N / cols;
    const pad = 8;
    const gapX = (w - pad * 2) / cols;
    const gapY = gapX * 1.25;
    const h = gapY * rows + pad * 2;
    this.canvas.width = Math.round(w * dpr);
    this.canvas.height = Math.round(h * dpr);
    this.canvas.style.height = `${h}px`;
    this.ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    this.radius = Math.max(1.5, Math.min(4, gapX * 0.28));
    this.dots = Array.from({ length: N }, (_, i) => ({
      x: pad + ((i % cols) + 0.5) * gapX,
      y: pad + (Math.floor(i / cols) + 0.5) * gapY,
      phase: Math.random() * Math.PI * 2,
      // current and target colors
      c: [...POOR],
      t: [...POOR],
    }));
  }

  setPercentile(p) {
    const idx = Math.min(N - 1, Math.max(0, Math.round((p / 100) * N)));
    for (let i = 0; i < N; i++) {
      const target = i < idx ? POOR : i === idx ? YOU : RICH;
      this.dots[i].t = target;
      if (this.reduced) this.dots[i].c = target;
    }
    this.userIndex = idx;
    this.waveStart = performance.now();
  }

  frame(now) {
    const ctx = this.ctx;
    ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
    const k = this.waveStart > 0 ? ((now - this.waveStart) / 700) * N : Infinity;
    for (let i = 0; i < N; i++) {
      const d = this.dots[i];
      // wave progress for this dot: 0 -> 1
      const dist = Math.abs(i - this.userIndex);
      const prog = this.reduced ? 1 : Math.min(1, Math.max(0, (k - dist) / 60));
      for (let ch = 0; ch < 4; ch++) {
        d.c[ch] += (d.t[ch] - d.c[ch]) * (prog === 1 ? 1 : 1 - Math.pow(1 - prog, 3));
      }
      const [r, g, b, a] = d.c;
      const shimmer = this.reduced ? 1 : 0.82 + 0.18 * Math.sin(now * 0.0012 + d.phase);
      const rad = i === this.userIndex ? this.radius * (1.6 + 0.5 * Math.sin(now * 0.005)) : this.radius;
      ctx.beginPath();
      ctx.arc(d.x, d.y, rad, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(${r | 0},${g | 0},${b | 0},${(a * shimmer).toFixed(3)})`;
      ctx.fill();
    }
    requestAnimationFrame(this._loop);
  }

  destroy() {
    removeEventListener('resize', this._resize);
  }
}
