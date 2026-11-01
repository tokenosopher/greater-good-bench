import { ACTIONS, CATEGORIES, CATEGORY_COLORS } from './data.js';
import { isSelected, toggleAction, subscribe } from './portfolio.js';
import { int } from './format.js';

const state = { filter: 'All', sort: 'leverage' };

export function initAtlas() {
  const grid = document.querySelector('#atlas-grid');
  const filtersEl = document.querySelector('#filters');
  const sortEl = document.querySelector('#sort');
  if (!grid) return;

  // filters
  const counts = { All: ACTIONS.length };
  ACTIONS.forEach((a) => { counts[a.category] = (counts[a.category] || 0) + 1; });

  CATEGORIES.forEach((cat) => {
    const b = document.createElement('button');
    b.type = 'button';
    b.className = 'chip' + (cat === 'All' ? ' is-active' : '');
    b.dataset.cat = cat;
    b.textContent = `${cat} ${counts[cat] || 0}`;
    b.addEventListener('click', () => {
      state.filter = cat;
      [...filtersEl.children].forEach((c) => c.classList.toggle('is-active', c === b));
      render();
    });
    filtersEl.append(b);
  });

  sortEl.addEventListener('change', () => {
    state.sort = sortEl.value;
    render();
  });

  function sortActions(list) {
    const s = state.sort;
    return [...list].sort((a, b) => {
      if (s === 'effort') return a.effort - b.effort || b.leverage - a.leverage;
      if (s === 'qaly') return b.qaly - a.qaly || b.leverage - a.leverage;
      if (s === 'co2') return b.co2 - a.co2 || b.leverage - a.leverage;
      if (s === 'animals') return b.animals - a.animals || b.leverage - a.leverage;
      return b.leverage - a.leverage;
    });
  }

  function metrics(a) {
    const chips = [];
    if (a.qaly > 0) chips.push(`<span class="metric"><b>${a.qaly >= 10 ? int(a.qaly) : a.qaly.toFixed(1)}</b> healthy yrs</span>`);
    if (a.co2 > 0) chips.push(`<span class="metric"><b>${a.co2 >= 10 ? int(a.co2) : a.co2.toFixed(1)}</b> t CO2e</span>`);
    if (a.animals > 0) chips.push(`<span class="metric"><b>${int(a.animals)}</b> animals</span>`);
    if (!chips.length) chips.push('<span class="metric neg">systemic — not quantified</span>');
    return chips.join('');
  }

  function costLabel(c) {
    return ['Free', '$', '$$', '$$$'][c] || '$';
  }

  function effortDots(n) {
    return `<span class="effort" title="Effort: ${n} of 3" aria-label="Effort ${n} of 3">${
      [1, 2, 3].map((i) => `<i class="${i <= n ? 'on' : ''}"></i>`).join('')
    }</span>`;
  }

  function render() {
    const list = sortActions(state.filter === 'All' ? ACTIONS : ACTIONS.filter((a) => a.category === state.filter));
    grid.innerHTML = list.map((a) => {
      const color = CATEGORY_COLORS[a.category] || 'var(--lime)';
      const selected = isSelected(a.id);
      return `
        <article class="card${selected ? ' is-selected' : ''}" data-id="${a.id}">
          <div class="card-top">
            <span class="card-cat"><i class="cat-dot" style="background:${color}"></i>${a.category}</span>
            <button class="add-btn${selected ? ' is-on' : ''}" data-add="${a.id}"
              aria-pressed="${selected}" aria-label="${selected ? 'Remove' : 'Add'} ${a.title} to your portfolio">
              ${selected ? '✓' : '+'}
            </button>
          </div>
          <h3>${a.title}</h3>
          <p class="card-blurb">${a.blurb}</p>
          <div class="card-detail">
            <div>
              <p><b>Why it works.</b> ${a.why}</p>
              <p><b>How to start.</b> ${a.how}</p>
              <p class="src">Source: ${a.source}</p>
            </div>
          </div>
          <div class="card-metrics">${metrics(a)}</div>
          <div class="card-actions">
            <span class="evidence" data-level="${a.evidence}"><i></i>${a.evidence} evidence</span>
            <button class="detail-toggle" data-detail="${a.id}" aria-expanded="false">Why this works +</button>
          </div>
          <div class="card-foot">
            <span>Effort ${effortDots(a.effort)}</span>
            <span>Cost ${costLabel(a.cost)}</span>
          </div>
        </article>`;
    }).join('');
  }

  // event delegation
  grid.addEventListener('click', (e) => {
    const add = e.target.closest('[data-add]');
    if (add) {
      toggleAction(add.dataset.add);
      return;
    }
    const det = e.target.closest('[data-detail]');
    if (det) {
      const card = det.closest('.card');
      const open = card.classList.toggle('is-open');
      det.setAttribute('aria-expanded', open ? 'true' : 'false');
      det.textContent = open ? 'Close −' : 'Why this works +';
    }
  });

  // selection changes from the portfolio side (e.g. clear all)
  subscribe(() => {
    grid.querySelectorAll('.card').forEach((card) => {
      const on = isSelected(card.dataset.id);
      card.classList.toggle('is-selected', on);
      const btn = card.querySelector('[data-add]');
      if (btn) {
        btn.classList.toggle('is-on', on);
        btn.setAttribute('aria-pressed', on ? 'true' : 'false');
        btn.textContent = on ? '✓' : '+';
        btn.setAttribute('aria-label', `${on ? 'Remove' : 'Add'} ${card.querySelector('h3').textContent} ${on ? 'from' : 'to'} your portfolio`);
      }
    });
  });

  render();
}
