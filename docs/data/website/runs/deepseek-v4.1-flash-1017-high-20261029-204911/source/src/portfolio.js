import { ACTION_BY_ID, YEARS_PER_LIFE } from './data.js';
import { animateNumber, int, compact, lives, tonnes, animals } from './format.js';

const SCALES = [
  { label: 'Just me', value: 1 },
  { label: '×1,000', value: 1000 },
  { label: '×1M', value: 1e6 },
  { label: '×1B', value: 1e9 },
  { label: 'Everyone', value: 8e9 },
];

const state = {
  selected: new Set(['give1000', 'talk']),
  scale: 0,
};

const listeners = new Set();
export const subscribe = (fn) => { listeners.add(fn); return () => listeners.delete(fn); };
const emit = () => listeners.forEach((fn) => fn());

export const isSelected = (id) => state.selected.has(id);

export function toggleAction(id) {
  if (!ACTION_BY_ID[id]) return;
  if (state.selected.has(id)) state.selected.delete(id);
  else state.selected.add(id);
  emit();
}

export function removeAction(id) {
  state.selected.delete(id);
  emit();
}

export function clearActions() {
  state.selected.clear();
  emit();
}

let wired = false;

export function initPortfolio() {
  const panel = document.querySelector('#portfolio-panel');
  if (!panel) return;

  const empty = document.querySelector('#portfolio-empty');
  const content = document.querySelector('#portfolio-content');
  const countEl = document.querySelector('#portfolio-count');
  const scaleRow = document.querySelector('#scale-row');
  const qalyEl = document.querySelector('#p-qaly');
  const livesEl = document.querySelector('#p-lives');
  const co2El = document.querySelector('#p-co2');
  const co2Sub = document.querySelector('#p-co2-sub');
  const animalsEl = document.querySelector('#p-animals');
  const animalsSub = document.querySelector('#p-animals-sub');
  const summaryEl = document.querySelector('#portfolio-summary');
  const copyBtn = document.querySelector('#copy-summary');
  const clearBtn = document.querySelector('#clear-portfolio');

  // scale buttons
  SCALES.forEach((s, i) => {
    const b = document.createElement('button');
    b.type = 'button';
    b.textContent = s.label;
    b.addEventListener('click', () => {
      state.scale = i;
      syncScale();
      render();
    });
    b.dataset.scale = String(i);
    scaleRow.append(b);
  });

  function syncScale() {
    [...scaleRow.children].forEach((b, i) => {
      b.classList.toggle('is-active', i === state.scale);
      b.setAttribute('aria-pressed', i === state.scale ? 'true' : 'false');
    });
  }

  function totals() {
    let qaly = 0, co2 = 0, animalCount = 0;
    for (const id of state.selected) {
      const a = ACTION_BY_ID[id];
      if (!a) continue;
      qaly += a.qaly || 0;
      co2 += a.co2 || 0;
      animalCount += a.animals || 0;
    }
    const m = SCALES[state.scale].value;
    return {
      qaly: qaly * m,
      co2: co2 * m,
      animals: animalCount * m,
      raw: { qaly, co2, animals: animalCount },
      multiplier: m,
      count: state.selected.size,
    };
  }

  function fmtBig(n, kind) {
    if (n >= 1e6) return compact(n);
    if (kind === 'qaly') return n >= 100 ? int(n) : n.toFixed(1);
    if (kind === 'co2') return compact(n) + ' t';
    return animals(n);
  }

  function summaryText(t) {
    const names = [...state.selected].map((id) => ACTION_BY_ID[id]?.title).filter(Boolean);
    if (!names.length) return '—';
    const verb = names.length === 1 ? 'action' : 'actions';
    let s = `I'm committing to ${names.length} ${verb}: ${names.join('; ')}.`;
    s += ` Together they add up to about ${int(t.raw.qaly)} healthy years, ${int(t.raw.co2)} tonnes of CO2e avoided and ${int(t.raw.animals)} animals spared each year.`;
    if (state.scale === SCALES.length - 1) {
      const pop = 8e9;
      s += ` At the scale of everyone alive, that is ${(t.qaly / pop).toFixed(1)} healthy years, ${(t.co2 / pop).toFixed(1)} tonnes of CO2e and ${Math.round(t.animals / pop)} animals per person on Earth.`;
    } else if (state.scale > 0) {
      s += ` At ${SCALES[state.scale].label}, that becomes ${fmtBig(t.qaly, 'qaly')} healthy years, ${fmtBig(t.co2, 'co2')} of CO2e and ${fmtBig(t.animals, 'animals')} animals.`;
    }
    s += ' Estimates, not guarantees — and a reason to start.';
    return s;
  }

  function render() {
    const t = totals();
    const emptyNow = t.count === 0;
    empty.hidden = !emptyNow;
    content.hidden = emptyNow;
    countEl.textContent = `${t.count} ${t.count === 1 ? 'action' : 'actions'}`;

    if (emptyNow) return;

    animateNumber(qalyEl, t.qaly, (v) => fmtBig(v, 'qaly'));
    animateNumber(co2El, t.co2, (v) => fmtBig(v, 'co2'));
    animateNumber(animalsEl, t.animals, (v) => fmtBig(v, 'animals'));

    if (t.multiplier >= 8e9) {
      const pop = 8e9;
      livesEl.textContent = `≈ ${(t.qaly / pop).toFixed(1)} healthy years for every person on Earth`;
      co2Sub.textContent = `≈ ${(t.co2 / pop).toFixed(1)} t per person on Earth`;
      animalsSub.textContent = `≈ ${Math.round(t.animals / pop)} animals per person on Earth`;
    } else {
      livesEl.textContent = `≈ ${lives(t.qaly / YEARS_PER_LIFE)} lives, at 45 healthy years each`;
      co2Sub.textContent = `≈ ${compact(t.co2 / 4.6)} cars off the road for a year`;
      animalsSub.textContent = 'per year, mostly from diet and advocacy';
    }
    summaryEl.textContent = summaryText(t);
  }

  syncScale();
  render();
  subscribe(render);

  clearBtn.addEventListener('click', () => {
    clearActions();
  });

  if (!wired) {
    wired = true;
    copyBtn.addEventListener('click', async () => {
      const text = summaryEl.textContent;
      try {
        await navigator.clipboard.writeText(text);
        const old = copyBtn.textContent;
        copyBtn.textContent = 'Copied ✓';
        setTimeout(() => { copyBtn.textContent = old; }, 1800);
      } catch {
        const ta = document.createElement('textarea');
        ta.value = text;
        ta.style.position = 'fixed';
        ta.style.opacity = '0';
        document.body.append(ta);
        ta.select();
        let ok = false;
        try { ok = document.execCommand('copy'); } catch { ok = false; }
        ta.remove();
        copyBtn.textContent = ok ? 'Copied ✓' : 'Select the text above to copy';
        setTimeout(() => { copyBtn.textContent = 'Copy summary'; }, 2200);
      }
    });
  }
}
