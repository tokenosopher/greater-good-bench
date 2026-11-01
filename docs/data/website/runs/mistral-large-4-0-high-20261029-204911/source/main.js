// The Good Multiplier — entry point.
import { initGlobe } from './globe.js';
import {
  POP, INTERVENTIONS, DEFAULT_ALLOC,
  computeScenario, computePledge, shares, fmt, money, fmtUnit,
} from './model.js';

const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => Array.from(document.querySelectorAll(sel));

/* ---------- hero globe ---------- */
const globeCanvas = $('#globe');
if (globeCanvas) initGlobe(globeCanvas);

/* ---------- nav scroll state ---------- */
const nav = $('#nav');
const onScroll = () => nav.classList.toggle('scrolled', window.scrollY > 12);
window.addEventListener('scroll', onScroll, { passive: true });
onScroll();

/* ---------- reveal on scroll ---------- */
const revealIO = new IntersectionObserver((entries) => {
  for (const e of entries) if (e.isIntersecting) { e.target.classList.add('in'); revealIO.unobserve(e.target); }
}, { threshold: 0.12 });
$$('.reveal').forEach((el) => revealIO.observe(el));

/* ---------- animated numbers ---------- */
const anims = new WeakMap();
function setNum(el, to, format, dur = 450) {
  const prev = anims.get(el);
  if (prev) cancelAnimationFrame(prev.raf);
  const from = prev ? prev.cur : 0;
  const start = performance.now();
  const step = (now) => {
    const t = Math.min(1, (now - start) / dur);
    const eased = 1 - Math.pow(1 - t, 3);
    const v = from + (to - from) * eased;
    el.textContent = format(v);
    if (t < 1) anims.set(el, { raf: requestAnimationFrame(step), cur: v });
    else anims.delete(el);
  };
  anims.set(el, { raf: requestAnimationFrame(step), cur: from });
}

/* hero stat strip count-up */
const statIO = new IntersectionObserver((entries) => {
  for (const e of entries) {
    if (!e.isIntersecting) continue;
    const el = e.target;
    statIO.unobserve(el);
    const to = parseFloat(el.dataset.count);
    const pre = el.dataset.prefix || '';
    const suf = el.dataset.suffix || '';
    setNum(el, to, (v) => pre + (Math.round(v * 10) / 10) + suf, 1400);
  }
}, { threshold: 0.4 });
$$('.stat-num').forEach((el) => statIO.observe(el));

/* ---------- shared state ---------- */
const state = {
  monthly: 1,               // $ per person per month (scenario)
  alloc: { ...DEFAULT_ALLOC },
  pledgeMonthly: 10,
  years: 10,
};

const ODA_YEAR = 220e9; // all government foreign aid, roughly, per year
const MILITARY_YEAR = 2.4e12;

function poolSub(pool) {
  const parts = [];
  if (pool > 0) {
    const x = pool / ODA_YEAR;
    parts.push(x >= 1
      ? `${trim1(x)}× all government foreign aid combined`
      : `${Math.round(x * 100)}% of all government foreign aid combined`);
    const m = pool / MILITARY_YEAR;
    parts.push(`${(m * 100).toFixed(m < 0.1 ? 1 : 0)}% of world military spending`);
  }
  return parts.join(' · ');
}
function trim1(x) { return (Math.round(x * 10) / 10).toString().replace(/\.0$/, ''); }

/* ---------- scenario ("The math") ---------- */
const amt = $('#amt'), amtOut = $('#amtOut');
const poolNum = $('#poolNum'), poolSubEl = $('#poolSub'), livesLine = $('#livesLine');
const outEls = { nets: $('#out-nets'), deworm: $('#out-deworm'), vita: $('#out-vita'), cash: $('#out-cash') };
const pctEls = { nets: $('#out-nets-pct'), deworm: $('#out-deworm-pct'), vita: $('#out-vita-pct'), cash: $('#out-cash-pct') };
const barEls = {};
$$('#allocBar span').forEach((s) => { barEls[s.dataset.bar] = s; });
const allocInputs = $$('input[data-alloc]');

function renderScenario() {
  amtOut.textContent = `$${state.monthly % 1 === 0 ? state.monthly : state.monthly.toFixed(2)} / month`;
  const sc = computeScenario(state.monthly, state.alloc);

  setNum(poolNum, sc.pool, (v) => money(v));
  poolSubEl.textContent = poolSub(sc.pool);

  for (const k of Object.keys(INTERVENTIONS)) {
    setNum(outEls[k], sc.units[k], (v) => fmtUnit(v), 380);
    pctEls[k].textContent = `${Math.round(sc.sh[k] * 100)}%`;
    if (barEls[k]) barEls[k].style.width = `${sc.sh[k] * 100}%`;
  }

  livesLine.innerHTML =
    `≈ <strong>${fmt(sc.livesLow)}–${fmt(sc.livesHigh)}</strong> lives saved per year ` +
    `<span class="fine">(rough, capacity-capped upper bound — see note below)</span>`;
}

amt.addEventListener('input', () => { state.monthly = parseFloat(amt.value); renderScenario(); renderPledge(); });
allocInputs.forEach((inp) => {
  inp.addEventListener('input', () => {
    state.alloc[inp.dataset.alloc] = parseFloat(inp.value);
    renderScenario();
    renderPledge();
  });
});

/* ---------- pledge ---------- */
const pAmt = $('#pAmt'), pYears = $('#pYears');
const pAmtOut = $('#pAmtOut'), pYearsOut = $('#pYearsOut');
const plTotal = $('#plTotal'), plSub = $('#plSub'), plList = $('#plList'), plLives = $('#plLives');
const statement = $('#statement'), copyBtn = $('#copyBtn');

const PL_ICONS = { nets: '🦟', deworm: '💊', vita: '🍊', cash: '💵' };
const PL_LABEL = {
  nets: 'malaria nets',
  deworm: 'children dewormed for a year',
  vita: 'vitamin A doses',
  cash: 'households given a ~$1,000 grant',
};

function livesText(low, high) {
  if (high < 1) return `≈ ${low.toFixed(2)}–${high.toFixed(2)} lives directly`;
  return `≈ ${fmt(low)}–${fmt(high)} lives directly`;
}

function renderPledge() {
  pAmtOut.textContent = `$${state.pledgeMonthly} / month`;
  pYearsOut.textContent = `${state.years} year${state.years > 1 ? 's' : ''}`;
  const p = computePledge(state.pledgeMonthly, state.years, state.alloc);

  setNum(plTotal, p.total, (v) => money(v));
  plSub.textContent = `$${fmt(state.pledgeMonthly * 12)}/year, sustained for ${state.years} year${state.years > 1 ? 's' : ''}`;

  plList.innerHTML = Object.keys(INTERVENTIONS)
    .map((k) => `<li>${PL_ICONS[k]} <b>${fmtUnit(p.units[k])}</b> ${PL_LABEL[k]}</li>`)
    .join('');

  plLives.innerHTML = `Plausibly <strong>${livesText(p.livesLow, p.livesHigh)}</strong> over ${state.years} years <span class="fine">(rough range)</span>`;

  statement.textContent =
    `I pledge to give $${state.pledgeMonthly}/month for ${state.years} year${state.years > 1 ? 's' : ''} ` +
    `($${fmt(p.total)} total). At the most cost-effective programs, that’s roughly ${Object.keys(INTERVENTIONS)
      .map((k) => `${fmtUnit(p.units[k])} ${PL_LABEL[k]}`).join(', ')} — plausibly ${livesText(p.livesLow, p.livesHigh)}. ` +
    `Small money, moved well, does enormous good.`;
}

pAmt.addEventListener('input', () => { state.pledgeMonthly = parseFloat(pAmt.value); renderPledge(); });
pYears.addEventListener('input', () => { state.years = parseInt(pYears.value, 10); renderPledge(); });

/* ---------- copy buttons (clipboard guarded for sandboxed contexts) ---------- */
async function copyText(text, btn, doneLabel) {
  try {
    await navigator.clipboard.writeText(text);
    btn.textContent = doneLabel;
  } catch (e) {
    // Fallback: select the text so the user can copy manually.
    const r = document.createRange();
    r.selectNodeContents(btn.closest('.statement-box, .cta-row').querySelector('p, .lede') || btn);
    const s = window.getSelection();
    if (s) { s.removeAllRanges(); s.addRange(r); }
    btn.textContent = 'Text selected — press Ctrl/Cmd+C';
  }
  setTimeout(() => { btn.textContent = btn.dataset.label; }, 2200);
}
copyBtn.dataset.label = copyBtn.textContent;
copyBtn.addEventListener('click', () => copyText(statement.textContent, copyBtn, 'Copied ✓'));

const shareBtn = $('#shareBtn');
shareBtn.dataset.label = shareBtn.textContent;
shareBtn.addEventListener('click', () => {
  const text =
    `The most effective things money can buy in this world cost dollars, not millions. ` +
    `If everyone on Earth gave just $1/month to the best-evidenced charities, that’s ${money(12 * POP)} a year — ` +
    `about half of all government foreign aid — plausibly saving millions of lives. ` +
    `See the interactive math and make a pledge (nothing tracked, works offline).`;
  copyText(text, shareBtn, 'Copied ✓');
});

/* ---------- quiz ---------- */
const quizButtons = $$('#quiz .quiz-options button');
const quizResult = $('#quizResult');
const QUIZ_ANSWERS = {
  deworm: '✅ Correct — mass deworming is among the cheapest interventions per healthy life-year gained (a few dollars per DALY in DCP3 analyses). Nets and vitamin A save the most lives outright. The point: the spread between “good” and “great” uses of money is often 100×.',
  nets: 'Not quite — malaria nets save the most lives per dollar, but deworming averts more healthy life-years (DALYs) per $1,000. Both are excellent buys; the gap between them and typical spending is what matters.',
  vita: 'Not quite — vitamin A saves many lives cheaply, but deworming averts more healthy life-years per $1,000. Both are top-tier; the gap between them and typical spending is what matters.',
  schools: 'Not quite — school construction is valuable but far more expensive per life-year than deworming, nets or vitamin A. That’s the whole “multiplier” idea: same money, very different outcomes.',
};
quizButtons.forEach((b) => {
  b.addEventListener('click', () => {
    quizButtons.forEach((x) => { x.disabled = true; x.classList.add(x === b ? (b.dataset.pick === 'deworm' ? 'correct' : 'wrong') : 'wrong'); });
    quizResult.hidden = false;
    quizResult.textContent = QUIZ_ANSWERS[b.dataset.pick];
  });
});

/* ---------- objections accordion (one open at a time) ---------- */
const objs = $$('.obj');
objs.forEach((d) => d.addEventListener('toggle', () => {
  if (d.open) objs.forEach((o) => { if (o !== d) o.open = false; });
}));

/* ---------- footer year ---------- */
$('#year').textContent = String(new Date().getFullYear());

/* ---------- initial render ---------- */
renderScenario();
renderPledge();
