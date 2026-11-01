import { animateNumber, int, lives } from './format.js';

const SVG_NS = 'http://www.w3.org/2000/svg';
const MAX_PER_RING = 420;

export function initRipple() {
  const svg = document.querySelector('#ripple-svg');
  if (!svg) return;

  const peopleInput = document.querySelector('#people');
  const depthInput = document.querySelector('#depth');
  const peopleOut = document.querySelector('#people-out');
  const depthOut = document.querySelector('#depth-out');
  const badge = document.querySelector('#ripple-badge');
  const peopleEl = document.querySelector('#ripple-people');
  const moneyEl = document.querySelector('#ripple-money');
  const qalyEl = document.querySelector('#ripple-qaly');
  const livesEl = document.querySelector('#ripple-lives');

  const people = () => Number(peopleInput.value);
  const depth = () => Number(depthInput.value);

  function setFill(input) {
    const min = Number(input.min) || 0;
    const max = Number(input.max) || 100;
    const pct = ((Number(input.value) - min) / (max - min)) * 100;
    input.style.setProperty('--fill', `${pct}%`);
  }

  function totalReach() {
    const p = people();
    const d = depth();
    let sum = 0;
    let level = 1;
    for (let i = 1; i <= d; i++) {
      level *= p;
      sum += level;
    }
    return { sum, p, d };
  }

  function orbit(n, radius, levelSeed) {
    const pts = [];
    const step = Math.max(1, Math.ceil(n / MAX_PER_RING));
    const shown = Math.ceil(n / step);
    for (let i = 0; i < shown; i++) {
      const idx = i * step;
      const angle = (idx / n) * Math.PI * 2 - Math.PI / 2 + levelSeed * 0.6;
      const jitter = (hash(idx + levelSeed * 97) - 0.5) * 7;
      pts.push({
        x: 300 + Math.cos(angle) * (radius + jitter),
        y: 300 + Math.sin(angle) * (radius + jitter),
        i: idx,
      });
    }
    return pts;
  }

  function render() {
    const { sum, p, d } = totalReach();
    peopleOut.textContent = String(p);
    depthOut.textContent = String(d);
    setFill(peopleInput);
    setFill(depthInput);

    badge.textContent = `${int(sum)} PEOPLE`;
    animateNumber(peopleEl, sum, (v) => int(v), 550);
    animateNumber(moneyEl, sum * 100, (v) => '$' + int(v), 550);
    animateNumber(qalyEl, sum, (v) => int(v), 550);
    animateNumber(livesEl, sum / 45, (v) => '≈ ' + (v >= 10 ? int(v) : v.toFixed(1)), 550);

    svg.innerHTML = '';

    // faint guide rings
    for (let k = 1; k <= d; k++) {
      const ring = document.createElementNS(SVG_NS, 'circle');
      ring.setAttribute('cx', '300');
      ring.setAttribute('cy', '300');
      ring.setAttribute('r', String(60 + k * 44));
      ring.setAttribute('fill', 'none');
      ring.setAttribute('stroke', 'rgba(241,239,229,0.07)');
      ring.setAttribute('stroke-dasharray', '2 6');
      svg.append(ring);
    }

    let level = 1;
    const colors = ['#d8f26b', '#a9df76', '#7ce0cf', '#8fc7cf', '#f0a35e', '#ef8b7c'];
    for (let k = 1; k <= d; k++) {
      level *= p;
      const radius = 60 + k * 44;
      const pts = orbit(level, radius, k);
      const baseR = Math.max(1.5, 6.2 - k * 0.7);
      const dotR = level > MAX_PER_RING ? baseR * 0.72 : baseR;
      pts.forEach((pt, idx) => {
        const c = document.createElementNS(SVG_NS, 'circle');
        c.setAttribute('cx', pt.x.toFixed(2));
        c.setAttribute('cy', pt.y.toFixed(2));
        c.setAttribute('r', '0');
        c.setAttribute('fill', colors[(k - 1) % colors.length]);
        c.setAttribute('opacity', '0');
        svg.append(c);
        setTimeout(() => {
          c.setAttribute('r', String(dotR));
          c.setAttribute('opacity', String(0.42 + (k === 1 ? 0.5 : 0.28)));
        }, Math.min(600, k * 55 + idx * 0.5));
      });
    }

    // center: you
    const halo = document.createElementNS(SVG_NS, 'circle');
    halo.setAttribute('cx', '300');
    halo.setAttribute('cy', '300');
    halo.setAttribute('r', '22');
    halo.setAttribute('fill', 'rgba(216,242,107,0.1)');
    svg.append(halo);

    const you = document.createElementNS(SVG_NS, 'circle');
    you.setAttribute('cx', '300');
    you.setAttribute('cy', '300');
    you.setAttribute('r', '7');
    you.setAttribute('fill', '#d8f26b');
    svg.append(you);

    const label = document.createElementNS(SVG_NS, 'text');
    label.setAttribute('x', '300');
    label.setAttribute('y', '272');
    label.setAttribute('text-anchor', 'middle');
    label.setAttribute('fill', '#a5a598');
    label.setAttribute('font-family', 'SFMono-Regular, Menlo, monospace');
    label.setAttribute('font-size', '9');
    label.setAttribute('letter-spacing', '2');
    label.textContent = 'YOU';
    svg.append(label);
  }

  peopleInput.addEventListener('input', render);
  depthInput.addEventListener('input', render);
  render();
}

function hash(n) {
  const x = Math.sin(n * 127.1 + 311.7) * 43758.5453;
  return x - Math.floor(x);
}
