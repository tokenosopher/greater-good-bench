import {
  CAUSES,
  MIX_PRESETS,
  HEALTH_COST_PER_QALY,
  CLIMATE_COST_PER_TONNE,
  ANIMAL_COST_PER_ANIMAL,
  YEARS_PER_LIFE,
} from './data.js';
import { animateNumber, int, compact, money, usd, tonnes, lives, clamp } from './format.js';

const DEFAULT_MIX = { health: 60, climate: 25, animals: 15 };

export function initLab() {
  const budget = document.querySelector('#budget');
  if (!budget) return;

  const budgetOut = document.querySelector('#budget-out');
  const mixEl = document.querySelector('#mix');
  const legend = document.querySelector('#allocation-legend');
  const qalyOut = document.querySelector('#qaly-out');
  const livesOut = document.querySelector('#lives-out');
  const co2Out = document.querySelector('#co2-out');
  const co2Sub = document.querySelector('#co2-sub');
  const animalsOut = document.querySelector('#animals-out');
  const animalsSub = document.querySelector('#animals-sub');
  const per100Out = document.querySelector('#per100-out');
  const seg = {
    health: document.querySelector('#seg-health'),
    climate: document.querySelector('#seg-climate'),
    animals: document.querySelector('#seg-animals'),
  };

  let mix = { ...DEFAULT_MIX };
  let value = Number(budget.value);

  // Build the three cause sliders
  const rows = {};
  CAUSES.forEach((cause) => {
    const row = document.createElement('div');
    row.className = 'mix-row';

    const name = document.createElement('span');
    name.className = 'mix-name';
    name.innerHTML = `<i class="mix-dot" style="background:${cause.color}"></i>${cause.name}`;

    const input = document.createElement('input');
    input.type = 'range';
    input.min = '0';
    input.max = '100';
    input.step = '1';
    input.value = String(Math.round(mix[cause.id]));
    input.setAttribute('aria-label', `${cause.name} share of giving`);
    input.dataset.cause = cause.id;
    input.style.setProperty('--accent', cause.color);

    const val = document.createElement('span');
    val.className = 'mix-val';
    val.textContent = Math.round(mix[cause.id]) + '%';

    row.append(name, input, val);
    mixEl.append(row);
    rows[cause.id] = { input, val };
  });

  function setFill(input) {
    const min = Number(input.min) || 0;
    const max = Number(input.max) || 100;
    const v = Number(input.value);
    const pct = ((v - min) / (max - min)) * 100;
    input.style.setProperty('--fill', `${pct}%`);
  }

  function setShare(id, raw) {
    const v = clamp(Number(raw), 0, 100);
    const others = CAUSES.map((c) => c.id).filter((k) => k !== id);
    const rest = 100 - v;
    const otherSum = others.reduce((s, k) => s + mix[k], 0);
    mix[id] = v;
    if (otherSum <= 0.0001) {
      others.forEach((k) => { mix[k] = rest / others.length; });
    } else {
      others.forEach((k) => { mix[k] = (mix[k] / otherSum) * rest; });
    }
    // guard against float drift
    const total = CAUSES.reduce((s, c) => s + mix[c.id], 0);
    if (total > 0) {
      const f = 100 / total;
      CAUSES.forEach((c) => { mix[c.id] *= f; });
    }
    syncMixUI();
    update();
  }

  function syncMixUI() {
    CAUSES.forEach((c) => {
      const { input, val } = rows[c.id];
      input.value = String(Math.round(mix[c.id]));
      val.textContent = Math.round(mix[c.id]) + '%';
      setFill(input);
    });
  }

  function setMixPreset(key) {
    mix = { ...MIX_PRESETS[key] };
    syncMixUI();
    update();
    document.querySelectorAll('#mix-presets .chip').forEach((b) => {
      b.classList.toggle('is-active', b.dataset.mix === key);
    });
  }

  // Bind sliders
  Object.values(rows).forEach(({ input }) => {
    input.addEventListener('input', () => {
      document.querySelectorAll('#mix-presets .chip').forEach((b) => b.classList.remove('is-active'));
      setShare(input.dataset.cause, input.value);
    });
  });

  document.querySelectorAll('#mix-presets .chip').forEach((btn) => {
    btn.addEventListener('click', () => setMixPreset(btn.dataset.mix));
  });
  document.querySelector('#reset-mix').addEventListener('click', () => {
    mix = { ...DEFAULT_MIX };
    syncMixUI();
    update();
    document.querySelectorAll('#mix-presets .chip').forEach((b) => b.classList.remove('is-active'));
  });

  document.querySelectorAll('#budget-presets .chip').forEach((btn) => {
    btn.addEventListener('click', () => {
      budget.value = btn.dataset.budget;
      value = Number(budget.value);
      setFill(budget);
      update();
      document.querySelectorAll('#budget-presets .chip').forEach((b) => {
        b.classList.toggle('is-active', b === btn);
      });
    });
  });

  budget.addEventListener('input', () => {
    value = Number(budget.value);
    setFill(budget);
    update();
    document.querySelectorAll('#budget-presets .chip').forEach((b) => b.classList.remove('is-active'));
  });

  function update() {
    const total = CAUSES.reduce((s, c) => s + mix[c.id], 0) || 1;
    const share = {};
    CAUSES.forEach((c) => { share[c.id] = mix[c.id] / total; });

    const healthMoney = value * share.health;
    const climateMoney = value * share.climate;
    const animalMoney = value * share.animals;

    const qaly = healthMoney / HEALTH_COST_PER_QALY;
    const co2 = climateMoney / CLIMATE_COST_PER_TONNE;
    const animalCount = animalMoney / ANIMAL_COST_PER_ANIMAL;
    const lifeCount = qaly / YEARS_PER_LIFE;
    const per100 = (share.health / HEALTH_COST_PER_QALY) * 100;

    budgetOut.textContent = usd(value);
    animateNumber(qalyOut, qaly, (v) => (v >= 10 ? int(v) : v.toFixed(1)));
    animateNumber(co2Out, co2, tonnes);
    animateNumber(animalsOut, animalCount, (v) => (v >= 100000 ? compact(v) : int(v)));
    animateNumber(per100Out, per100, (v) => (v < 0.1 ? v.toFixed(2) : v.toFixed(1)) + ' yr');

    if (lifeCount >= 0.01) {
      const perLife = healthMoney / lifeCount;
      livesOut.textContent = `≈ ${lives(lifeCount)} lives — one life for every ${usd(Math.round(perLife / 100) * 100)} of health giving`;
    } else {
      livesOut.textContent = 'Move the budget to begin — every $100 is about a healthy year.';
    }

    co2Sub.textContent = co2 >= 0.05
      ? `≈ ${(co2 / 1.6).toFixed(1)} transatlantic flights avoided`
      : '≈ a short car trip';

    animalsSub.textContent = animalCount >= 1
      ? `≈ ${int(animalCount)} animals out of cages for a year`
      : 'no animal-welfare allocation yet';

    seg.health.style.width = (share.health * 100).toFixed(2) + '%';
    seg.climate.style.width = (share.climate * 100).toFixed(2) + '%';
    seg.animals.style.width = (share.animals * 100).toFixed(2) + '%';

    legend.innerHTML = CAUSES.map((c) => {
      const amount = value * share[c.id];
      return `<span><i style="background:${c.color}"></i>${c.name} ${Math.round(share[c.id] * 100)}% · ${usd(amount)}</span>`;
    }).join('');

    // sync the "per $100" equivalent lines for transparency
    if (co2 >= 0.05) {
      co2Sub.title = `${int(co2)} tonnes CO2e`;
    }
  }

  setFill(budget);
  syncMixUI();
  setMixPreset('balanced');
  const defaultBudget = document.querySelector('#budget-presets [data-budget="1000"]');
  if (defaultBudget) defaultBudget.classList.add('is-active');
}

// expose for the portfolio summary if needed
export { DEFAULT_MIX };
