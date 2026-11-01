export function fmt(n, decimals = 0) {
  const v = decimals ? Number(n.toFixed(decimals)) : Math.round(n);
  return v.toLocaleString('en-US');
}

export function fmtBig(n) {
  if (n >= 1e9) return `${(n / 1e9).toFixed(n / 1e9 >= 10 ? 1 : 2)} billion`;
  if (n >= 1e6) return `${(n / 1e6).toFixed(n / 1e6 >= 10 ? 0 : 1)} million`;
  if (n >= 1e4) return `${Math.round(n / 1e3)},000`;
  return Math.round(n).toLocaleString('en-US');
}

export function fmtRank(n) {
  if (n >= 1e6) return `${(n / 1e6).toFixed(n / 1e6 >= 10 ? 0 : 1)} million`;
  return Math.round(n).toLocaleString('en-US');
}

export function fmtMoney(n) {
  if (n >= 10000) return `$${(Math.round(n / 100) * 100).toLocaleString('en-US')}`;
  return `$${Math.round(n).toLocaleString('en-US')}`;
}

const easeOutCubic = (t) => 1 - Math.pow(1 - t, 3);

export function animateNumber(el, to, { decimals = 0, formatter = (v) => fmt(v, decimals), duration = 500 } = {}) {
  if (el._tween) cancelAnimationFrame(el._tween);
  const from = typeof el._value === 'number' ? el._value : 0;
  if (matchMedia('(prefers-reduced-motion: reduce)').matches || from === to) {
    el._value = to;
    el.textContent = formatter(to);
    return;
  }
  const start = performance.now();
  const step = (now) => {
    const t = Math.min(1, (now - start) / duration);
    const v = from + (to - from) * easeOutCubic(t);
    el.textContent = formatter(v);
    if (t < 1) {
      el._tween = requestAnimationFrame(step);
    } else {
      el._value = to;
      el._tween = null;
    }
  };
  el._tween = requestAnimationFrame(step);
}
