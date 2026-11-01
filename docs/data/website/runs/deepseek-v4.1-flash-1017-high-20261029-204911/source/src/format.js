const nf = new Intl.NumberFormat('en-US');
const nf1 = new Intl.NumberFormat('en-US', { maximumFractionDigits: 1 });
const nf2 = new Intl.NumberFormat('en-US', { maximumFractionDigits: 2 });

export const clamp = (v, lo, hi) => Math.min(hi, Math.max(lo, v));
export const lerp = (a, b, t) => a + (b - a) * t;
export const easeOut = (t) => 1 - Math.pow(1 - t, 3);

export const int = (n) => nf.format(Math.round(n));

export function compact(n) {
  n = Math.abs(n);
  if (n >= 1e9) return trim(n / 1e9) + 'B';
  if (n >= 1e6) return trim(n / 1e6) + 'M';
  if (n >= 1e3) return trim(n / 1e3) + 'k';
  return trim(n);
}
function trim(n) {
  const s = n >= 100 ? n.toFixed(0) : n >= 10 ? n.toFixed(0) : n.toFixed(1);
  return s.replace(/\.0$/, '');
}

export function years(n) {
  if (n >= 1000) return compact(n) + ' yrs';
  if (n >= 100) return int(n) + ' yrs';
  if (n >= 10) return nf1.format(n) + ' yrs';
  return nf2.format(n) + ' yrs';
}

export const usd = (n) => '$' + int(n);

export function money(n) {
  if (n >= 1000) return '$' + compact(n);
  return '$' + int(n);
}

export function tonnes(n) {
  if (n >= 1000) return compact(n) + ' t';
  if (n >= 100) return int(n) + ' t';
  if (n >= 10) return nf1.format(n) + ' t';
  return nf2.format(n) + ' t';
}

export function animals(n) {
  if (n >= 1000) return compact(n);
  return int(n);
}

export function lives(n) {
  if (n >= 100) return compact(n);
  if (n >= 1) return nf1.format(n);
  return nf2.format(n);
}

// Animate a number from its current displayed value to a new one.
const running = new WeakMap();
export function animateNumber(el, to, format, duration = 650) {
  if (!el) return;
  const prev = running.get(el);
  const from = prev ? prev.value : (to === 0 ? 0 : 0);
  if (prev) cancelAnimationFrame(prev.raf);
  const start = performance.now();
  const state = { value: from, raf: 0 };
  running.set(el, state);

  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (reduced || duration === 0) {
    state.value = to;
    el.textContent = format(to);
    return;
  }

  const tick = (now) => {
    const t = clamp((now - start) / duration, 0, 1);
    const v = lerp(from, to, easeOut(t));
    state.value = v;
    el.textContent = format(v);
    if (t < 1) state.raf = requestAnimationFrame(tick);
  };
  state.raf = requestAnimationFrame(tick);
}
