const actions = [
  {
    id: 'plant-dinner',
    title: 'One plant-powered dinner',
    kicker: 'MAKE IT A HABIT',
    description: 'Swap one meal you already planned. No new shopping list and no perfect diet—just a delicious plate that asks less of the planet.',
    time: 20, cost: 10, impact: 'Medium', styles: ['quiet', 'together'],
    co2: 4.6, money: 3.4, minutes: 40, material: 0.9,
    art: 'plate', regionNote: {
      'south-asia': 'Swap one grain or curry with a locally abundant seasonal vegetable.',
      'east-asia': 'Make one familiar rice bowl a veggie-forward bowl with what you already have.',
      'west-africa': 'Lean on a seasonal staple you already buy and add a locally grown vegetable.'
    }
  },
  {
    id: 'car-free',
    title: 'One car-free errand',
    kicker: 'RECLAIM A LITTLE TIME',
    description: 'Walk, cycle, or take transit for one nearby errand. The side benefits include cleaner air, a calmer mind, and money left in your pocket.',
    time: 20, cost: 0, impact: 'High', styles: ['quiet', 'together'],
    co2: 3.2, money: 2.1, minutes: 42, material: 0,
    art: 'wheel'
  },
  {
    id: 'repair',
    title: 'Repair before replacing',
    kicker: 'KEEP GOOD THINGS GOING',
    description: 'Choose one item you were ready to discard, then mend, clean, repair, or swap it instead. Extending a thing’s life is practical climate action.',
    time: 20, cost: 0, impact: 'High', styles: ['quiet', 'bold'],
    co2: 3.8, money: 64, minutes: 18, material: 8.2,
    art: 'wrench'
  },
  {
    id: 'skill',
    title: 'Pass on one useful skill',
    kicker: 'KNOWLEDGE IS A PUBLIC GOOD',
    description: 'Teach one neighbor a practical thing you know—how to fix a bike, cook a meal, use a tool, or navigate local services.',
    time: 60, cost: 0, impact: 'High', styles: ['together'],
    co2: 0.1, money: 0, minutes: 45, material: 0,
    art: 'people'
  },
  {
    id: 'food-waste',
    title: 'Rescue one good meal',
    kicker: 'SAVE FOOD BEFORE IT WASTES',
    description: 'Make a “use first” box from what is already in your kitchen and turn it into dinner. Good food deserves to be eaten.',
    time: 5, cost: 0, impact: 'Medium', styles: ['quiet', 'together'],
    co2: 2.8, money: 13, minutes: 10, material: 2.4,
    art: 'bowl'
  },
  {
    id: 'cleanup',
    title: 'Clean up one shared place',
    kicker: 'START WHERE YOUR FEET ARE',
    description: 'Pick up a short stretch of a street, park, river, or school route. Invite one person or make it a ten-minute ritual.',
    time: 20, cost: 0, impact: 'Medium', styles: ['together', 'bold'],
    co2: 0.2, money: 0, minutes: 25, material: 1.6,
    art: 'spark'
  },
  {
    id: 'garden',
    title: 'Grow one useful thing',
    kicker: 'SHADE, FOOD, COMPANY',
    description: 'Grow a herb, vegetable, or flower in a pot, window box, or shared plot. Start with one plant; care is the point.',
    time: 60, cost: 15, impact: 'High', styles: ['together', 'bold'],
    co2: 1.4, money: 0, minutes: 60, material: 0.3,
    art: 'plant'
  },
  {
    id: 'buy-less',
    title: 'Make one purchase wait',
    kicker: 'PAUSE BEFORE THE MARKET',
    description: 'Choose one thing you planned to buy and wait 24 hours. Then borrow, rent, repair, or skip it if it still feels necessary.',
    time: 5, cost: 0, impact: 'High', styles: ['quiet', 'bold'],
    co2: 8.4, money: 28, minutes: 10, material: 4,
    art: 'clock'
  },
  {
    id: 'check-in',
    title: 'One meaningful check-in',
    kicker: 'CARE IS A PRACTICE',
    description: 'Ask someone nearby how they are—and make time to really listen. Ask for what you need too; care works both ways.',
    time: 5, cost: 0, impact: 'Medium', styles: ['quiet', 'together'],
    co2: 0, money: 0, minutes: 20, material: 0,
    art: 'heart'
  }
];

const state = {
  time: 20,
  money: 20,
  style: 'quiet',
  region: 'global',
  currentAction: actions[0],
  actionOffset: 0,
  plan: [],
  simAction: actions[0].id,
  people: 100,
  frequency: 4
};

const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];
const formatNumber = (value) => new Intl.NumberFormat('en-US', { maximumFractionDigits: 0 }).format(Math.round(value));

function actionIllustration(action) {
  const art = {
    plate: '<div class="shape plate"></div><div class="shape leaf"></div><div class="shape steam"></div>',
    wheel: '<div class="shape bike-wheel wheel-a"></div><div class="shape bike-wheel wheel-b"></div><div class="shape bike-frame"></div>',
    wrench: '<div class="shape wrench-head"></div><div class="shape wrench-handle"></div><div class="shape screw"></div>',
    people: '<div class="shape person person-a"></div><div class="shape person person-b"></div><div class="shape person person-c"></div>',
    bowl: '<div class="shape bowl-shape"></div><div class="shape bowl-leaf"></div><div class="shape bowl-grain"></div>',
    spark: '<div class="shape spark-shape"></div><div class="shape spark-dot dot-a"></div><div class="shape spark-dot dot-b"></div>',
    plant: '<div class="shape plant-pot"></div><div class="shape plant-stem"></div><div class="shape plant-leaf leaf-a"></div><div class="shape plant-leaf leaf-b"></div>',
    clock: '<div class="shape clock-face"></div><div class="shape clock-hand"></div>',
    heart: '<div class="shape heart-shape"></div><div class="shape heart-dot dot-a"></div><div class="shape heart-dot dot-b"></div>'
  };
  return art[action.art] || art.plate;
}

function scoreAction(action) {
  let score = 0;
  const timeFit = Math.abs(action.time - state.time);
  const costFit = action.cost <= state.money ? 30 : -80;
  const styleFit = action.styles.includes(state.style) ? 45 : 0;
  score += 100 - timeFit * 1.3 + costFit + styleFit;
  if (action.time <= state.time && action.cost <= state.money) score += 25;
  return score;
}

function chooseRecommendation() {
  const eligible = actions.filter((action) => action.time <= state.time && action.cost <= state.money);
  const pool = eligible.length ? eligible : actions.filter((action) => action.cost === 0);
  const ranked = [...pool].sort((a, b) => scoreAction(b) - scoreAction(a));
  state.currentAction = ranked[0];
  renderRecommendation();
}

function renderRecommendation() {
  const action = state.currentAction;
  $('#action-number').textContent = `ACTION ${String(actions.indexOf(action) + 1).padStart(2, '0')}`;
  $('#action-kicker').textContent = action.kicker;
  $('#action-title').textContent = action.title;
  let description = action.description;
  if (state.region !== 'global' && action.regionNote?.[state.region]) {
    description = action.regionNote[state.region];
  }
  $('#action-description').textContent = description;
  $('#action-time').textContent = action.time;
  $('#action-cost').textContent = action.cost === 0 ? '$0' : `$${action.cost}`;
  $('#action-impact').textContent = action.impact;
  $('#action-illustration').innerHTML = actionIllustration(action);
}

function chooseAlternate() {
  const alternatives = actions.filter((action) => action.id !== state.currentAction.id);
  alternatives.sort((a, b) => scoreAction(b) - scoreAction(a));
  const top = alternatives.slice(0, 4);
  state.currentAction = top[state.actionOffset % top.length];
  state.actionOffset += 1;
  renderRecommendation();
}

function showToast(message) {
  const toast = $('#toast');
  toast.textContent = message;
  toast.classList.add('show');
  window.clearTimeout(showToast.timer);
  showToast.timer = window.setTimeout(() => toast.classList.remove('show'), 2600);
}

function addToPlan() {
  const action = state.currentAction;
  if (state.plan.some((item) => item.id === action.id)) {
    showToast('That action is already in your good week.');
    return;
  }
  state.plan.push(action);
  renderPlan();
  $('#my-week').scrollIntoView({ behavior: 'smooth', block: 'center' });
  showToast('Added. Your good week just got a little lighter.');
}

function renderPlan() {
  const list = $('#plan-list');
  list.innerHTML = '';
  $('#week-count').textContent = state.plan.length;
  $('#week-empty').hidden = state.plan.length > 0;
  $('#week-footer').hidden = state.plan.length === 0;

  state.plan.forEach((action, index) => {
    const item = document.createElement('li');
    item.className = 'plan-item';
    item.innerHTML = `
      <span class="plan-number">${index + 1}</span>
      <div><h3>${action.title}</h3><p>${action.time} min · ${action.cost === 0 ? 'No cost' : `Up to $${action.cost}`} · ${action.kicker.toLowerCase()}</p></div>
      <button type="button" aria-label="Remove ${action.title}">×</button>
    `;
    $('button', item).addEventListener('click', () => {
      state.plan = state.plan.filter((entry) => entry.id !== action.id);
      renderPlan();
      showToast('Removed from your plan.');
    });
    list.appendChild(item);
  });
}

async function copyPlan() {
  const text = ['MY GOOD WEEK', ...state.plan.map((action, index) => `${index + 1}. ${action.title} — ${action.time} min, ${action.cost ? `up to $${action.cost}` : 'no cost'}`), '', 'Small actions. Shared scale.'].join('\n');
  try {
    await navigator.clipboard.writeText(text);
    showToast('Your plan was copied. Share it with someone nearby.');
  } catch {
    const area = document.createElement('textarea');
    area.value = text;
    area.style.position = 'fixed';
    area.style.opacity = '0';
    document.body.appendChild(area);
    area.select();
    const copied = document.execCommand('copy');
    area.remove();
    showToast(copied ? 'Your plan was copied.' : 'Your plan is ready above.');
  }
}

function populateSimulator() {
  const select = $('#sim-action');
  select.innerHTML = actions.map((action) => `<option value="${action.id}">${action.title}</option>`).join('');
  select.value = state.simAction;
}

function updateSimulator() {
  const action = actions.find((entry) => entry.id === state.simAction);
  const events = state.frequency;
  const factor = state.people * events;
  $('#people-number').textContent = formatNumber(state.people);
  $('#co2-value').textContent = formatNumber(action.co2 * factor);
  $('#money-value').textContent = `$${formatNumber(action.money * factor)}`;
  $('#people-value').textContent = formatNumber(action.minutes * factor);
  $('#waste-value').textContent = formatNumber(action.material * factor);
  $('#frequency-caption').textContent = events === 1 ? 'THIS MONTH' : events === 4 ? 'EVERY WEEK' : 'THIS MONTH';
  const slider = $('#people-slider');
  const progress = (Number(slider.value) / Number(slider.max)) * 100;
  slider.style.background = `linear-gradient(to right, var(--coral) ${progress}%, rgba(23,58,53,.18) ${progress}%)`;
  $('#scale-fill').style.width = `${progress}%`;
  $('#scale-marker').style.left = `${progress}%`;
  let label = 'One person';
  let caption = 'At this scale, the effect starts with you.';
  if (state.people >= 100) { label = 'YOUR BLOCK'; caption = `At ${formatNumber(state.people)} people, this becomes visible on your block.`; }
  if (state.people >= 1000) { label = 'A NEIGHBORHOOD'; caption = `At ${formatNumber(state.people)} people, this can shift a neighborhood rhythm.`; }
  if (state.people >= 5000) { label = 'A CITY'; caption = `At ${formatNumber(state.people)} people, this starts to change a city.`; }
  if (state.people >= 10000) { label = 'A CITY'; caption = `At ${formatNumber(state.people)} people, a city-scale pattern is possible.`; }
  const labels = $$('.scale-labels span');
  labels.forEach((item) => { item.classList.toggle('active', item.textContent === label); });
  $('#scale-caption').textContent = caption;
}

function randomAction() {
  const pool = actions.filter((action) => action.time <= state.time && action.cost <= state.money);
  state.currentAction = pool[Math.floor(Math.random() * pool.length)];
  renderRecommendation();
  $('#builder').scrollIntoView({ behavior: 'smooth', block: 'start' });
  showToast('Here’s a good place to start.');
}

function bindControls() {
  $$('[data-time]').forEach((button) => button.addEventListener('click', () => {
    state.time = Number(button.dataset.time);
    $$('[data-time]').forEach((item) => item.classList.toggle('active', item === button));
    chooseRecommendation();
  }));
  $$('[data-money]').forEach((button) => button.addEventListener('click', () => {
    state.money = Number(button.dataset.money);
    $$('[data-money]').forEach((item) => item.classList.toggle('active', item === button));
    chooseRecommendation();
  }));
  $$('[data-style]').forEach((button) => button.addEventListener('click', () => {
    state.style = button.dataset.style;
    $$('[data-style]').forEach((item) => item.classList.toggle('active', item === button));
    chooseRecommendation();
  }));
  $('#region').addEventListener('change', (event) => {
    state.region = event.target.value;
    renderRecommendation();
    showToast(event.target.value === 'global' ? 'Recommendation kept broadly portable.' : 'Recommendation adapted to your context.');
  });
  $('#another-action').addEventListener('click', chooseAlternate);
  $('#add-action').addEventListener('click', addToPlan);
  $('#copy-plan').addEventListener('click', copyPlan);
  $$('.js-random').forEach((button) => button.addEventListener('click', randomAction));
}

function bindSimulator() {
  const peopleSteps = [10, 25, 50, 100, 250, 500, 1000, 2500, 5000, 10000];
  const slider = $('#people-slider');
  slider.max = String(peopleSteps.length - 1);
  slider.value = '3';
  slider.addEventListener('input', () => {
    state.people = peopleSteps[Number(slider.value)];
    updateSimulator();
  });
  $('#sim-action').addEventListener('change', (event) => {
    state.simAction = event.target.value;
    updateSimulator();
  });
  $$('[data-frequency]').forEach((button) => button.addEventListener('click', () => {
    state.frequency = Number(button.dataset.frequency);
    $$('[data-frequency]').forEach((item) => item.classList.toggle('active', item === button));
    updateSimulator();
  }));
}

bindControls();
bindSimulator();
populateSimulator();
chooseRecommendation();
renderPlan();
updateSimulator();
