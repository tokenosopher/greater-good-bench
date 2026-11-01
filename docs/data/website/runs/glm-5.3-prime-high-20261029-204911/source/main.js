import { WORLD_POP, percentileForIncome, computeImpact } from './distribution.js';
import { DotField } from './dotfield.js';
import { fmt, fmtBig, fmtRank, fmtMoney, animateNumber } from './utils.js';

const state = { income: 45000, pct: 5 };

const $ = (sel) => document.querySelector(sel);

/* ---------------- hero: malaria counter ---------------- */
(() => {
  const el = $('#malaria-count');
  const start = Date.now();
  const tick = () => {
    const deaths = Math.floor((Date.now() - start) / 1000 / 70);
    animateNumber(el, deaths, { duration: 300 });
  };
  tick();
  setInterval(tick, 1000);
})();

/* ---------------- where you stand ---------------- */
const dots = new DotField($('#dots'));

const incomeInput = $('#income-input');
const incomeSlider = $('#income-slider');

const sliderToIncome = (t) => 500 * Math.pow(2000, t / 100); // 500 .. 1,000,000
const incomeToSlider = (v) => (Math.log(v / 500) / Math.log(2000)) * 100;

function setIncome(v, fromSlider = false) {
  state.income = Math.max(500, Math.min(2000000, Math.round(v) || 500));
  incomeInput.value = state.income.toLocaleString('en-US');
  if (!fromSlider) incomeSlider.value = incomeToSlider(state.income).toFixed(2);
  update();
}

incomeSlider.addEventListener('input', () => setIncome(sliderToIncome(+incomeSlider.value), true));
incomeInput.addEventListener('change', () => setIncome(parseInt(String(incomeInput.value).replace(/[^0-9]/g, ''), 10)));

/* ---------------- giving calculator ---------------- */
const pctSlider = $('#pct-slider');
pctSlider.addEventListener('input', () => {
  state.pct = +pctSlider.value;
  update();
});
$('#pledge-1').addEventListener('click', () => setPct(1));
$('#pledge-5').addEventListener('click', () => setPct(5));
$('#pledge-10').addEventListener('click', () => setPct(10));

function setPct(p) {
  state.pct = p;
  pctSlider.value = p;
  update();
  for (const btn of document.querySelectorAll('.pledge-btn'))
    btn.classList.toggle('active', +btn.dataset.pct === p);
}

/* ---------------- translator ---------------- */
const priceInput = $('#price-input');
priceInput.addEventListener('change', () => updateTranslator());
priceInput.addEventListener('input', () => updateTranslator());

function updateTranslator() {
  const p = Math.max(0.5, Math.min(100000, parseFloat(priceInput.value) || 20));
  const nets = p / 5;
  const deworm = p / 0.75;
  const lifeShare = (p / 5000) * 100;
  $('#tr-nets').textContent = fmt(nets, nets < 10 ? 1 : 0);
  $('#tr-people').textContent = fmt(nets * 2, nets * 2 < 10 ? 1 : 0);
  $('#tr-deworm').textContent = fmt(deworm, deworm < 10 ? 1 : 0);
  $('#tr-life').textContent = lifeShare >= 1 ? fmt(lifeShare) : lifeShare.toFixed(2);
}

/* ---------------- certificate ---------------- */
const nameInput = $('#name-input');
nameInput.addEventListener('input', () => update());

/* ---------------- master update ---------------- */
function update() {
  // ---- percentile ----
  const p = percentileForIncome(state.income);
  dots.setPercentile(p);
  animateNumber($('#richer-count'), (WORLD_POP * p) / 100, { formatter: fmtBig, duration: 600 });
  $('#richer-pct').textContent = p >= 99.9 ? '99.9+' : p.toFixed(1);
  $('#rank').textContent = fmtRank(WORLD_POP * (1 - p / 100));
  $('#stand-lead').textContent =
    p >= 90
      ? `You are richer than roughly ${fmtBig((WORLD_POP * p) / 100)} people.`
      : `You are richer than about ${p.toFixed(0)}% of humanity.`;

  // ---- impact ----
  const imp = computeImpact(state.income, state.pct);
  $('#donation-annual').textContent = fmtMoney(imp.annual);
  $('#pct-display').textContent = state.pct;
  const set = (sel, v, decimals = 0) => animateNumber($(sel), v, { decimals });
  const fmtLives = (v) => (v < 20 ? v.toFixed(1).replace(/\.0$/, '') : fmt(v));
  set('#r-lives-decade', imp.livesDecade, imp.livesDecade < 20 ? 1 : 0);
  set('#r-lives-40', imp.lives40, imp.lives40 < 20 ? 1 : 0);
  set('#r-nets', imp.nets, imp.nets < 10 ? 1 : 0);
  set('#r-protected', imp.protected, imp.protected < 10 ? 1 : 0);
  set('#r-deworm', imp.deworm, imp.deworm < 10 ? 1 : 0);
  set('#r-dalys', imp.dalysDecade, imp.dalysDecade < 10 ? 1 : 0);
  $('#r-dalys-note').textContent = `over a 40-year career: ${fmt(imp.dalys40)} years`;

  // ---- certificate ----
  $('#cert-name').textContent = (nameInput.value.trim() || 'A Person Who Read This Page');
  $('#cert-pct').textContent = state.pct;
  $('#cert-amount').textContent = fmtMoney(imp.annual);
  $('#cert-lives').textContent = imp.lives40 < 20
    ? imp.lives40.toFixed(1).replace(/\.0$/, '')
    : fmt(imp.lives40);

  updateTranslator();
}

/* ---------------- scroll reveal ---------------- */
const io = new IntersectionObserver(
  (entries) => {
    for (const e of entries) if (e.isIntersecting) e.target.classList.add('visible');
  },
  { threshold: 0.12 }
);
document.querySelectorAll('.reveal').forEach((el) => io.observe(el));

/* ---------------- init ---------------- */
setIncome(state.income);
setPct(5);
updateTranslator();
