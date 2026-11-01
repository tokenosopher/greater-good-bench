// Data + math for The Good Multiplier.
// All figures are approximate, published, rounded estimates (see footer of index.html).

export const POP = 8.1e9; // people on Earth, ~2025

export const INTERVENTIONS = {
  nets:   { name: 'Malaria nets',        cost: 5.5,  mortality: true  },
  deworm: { name: 'Deworming children',  cost: 1.5,  mortality: false },
  vita:   { name: 'Vitamin A doses',     cost: 1.0,  mortality: true  },
  cash:   { name: 'Direct cash grants',  cost: 1000, mortality: false },
};

export const DEFAULT_ALLOC = { nets: 40, deworm: 25, vita: 15, cash: 20 };

// Lives saved per dollar, across the mortality-focused programs.
// High end: best-estimate ~$4,500/life (GiveWell, AMF). Low end: $45,000/life to allow
// for scale-up inefficiency, delivery costs and uncertainty.
const LIVES_PER_DOLLAR_HIGH = 1 / 4500;
const LIVES_PER_DOLLAR_LOW  = 1 / 45000;

// Real-world absorptive capacity: beyond roughly this much per year aimed at
// mortality-focused programs, marginal dollars do far less (logistics, price inflation,
// diminishing returns). So the lives estimate is capped — an upper bound, not a prediction.
export const MORT_CAP = 50e9;

export function shares(alloc) {
  const keys = Object.keys(INTERVENTIONS);
  const sum = keys.reduce((a, k) => a + Math.max(0, alloc[k] || 0), 0);
  const out = {};
  for (const k of keys) out[k] = sum > 0 ? Math.max(0, alloc[k] || 0) / sum : 0;
  return out;
}

function split(total, alloc) {
  const sh = shares(alloc);
  const units = {};
  let mortalityPool = 0;
  for (const k of Object.keys(INTERVENTIONS)) {
    units[k] = (total * sh[k]) / INTERVENTIONS[k].cost;
    if (INTERVENTIONS[k].mortality) mortalityPool += total * sh[k];
  }
  const effMort = Math.min(mortalityPool, MORT_CAP);
  return {
    sh, units,
    livesLow:  effMort * LIVES_PER_DOLLAR_LOW,
    livesHigh: effMort * LIVES_PER_DOLLAR_HIGH,
  };
}

// "If everyone on Earth gave $X/month" scenario.
export function computeScenario(monthlyPerPerson, alloc) {
  const pool = monthlyPerPerson * 12 * POP;
  return { pool, ...split(pool, alloc) };
}

// Personal pledge scenario.
export function computePledge(monthly, years, alloc) {
  const total = monthly * 12 * years;
  return { total, ...split(total, alloc) };
}

// Compact number formatting: 8100000000 -> "8.1B", 12345 -> "12.3K"
function trim(x) { return (Math.round(x * 10) / 10).toString().replace(/\.0$/, ''); }
export function fmt(n) {
  if (!isFinite(n)) return '—';
  const a = Math.abs(n);
  if (a >= 1e9) return trim(n / 1e9) + 'B';
  if (a >= 1e6) return trim(n / 1e6) + 'M';
  if (a >= 1e3) return trim(n / 1e3) + 'K';
  return (Math.round(n * 100) / 100).toString();
}
export function money(n) { return '$' + fmt(n); }

// Formatting for counts of things (nets, children, doses, households):
// big -> compact (7.1B), >=1 -> whole number (87), <1 -> 2 decimals (0.24).
export function fmtUnit(v) {
  if (!isFinite(v)) return '—';
  if (v === 0) return '0';
  const a = Math.abs(v);
  if (a >= 1000) return fmt(v);
  if (a >= 1) return String(Math.round(v));
  return v.toFixed(2);
}
