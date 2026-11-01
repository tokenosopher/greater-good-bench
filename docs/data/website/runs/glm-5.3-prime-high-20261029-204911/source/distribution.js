// Approximate global personal-income distribution.
// Annual income in international (PPP-adjusted) dollars, synthesized from
// World Bank Poverty & Inequality Platform and Our World in Data (2019-2023).

export const WORLD_POP = 8_100_000_000;

// [percentile, annual income] — percentile = share of the world living on less.
const DIST = [
  [0, 0],
  [2, 210],
  [5, 320],
  [10, 420],
  [20, 700],
  [30, 1000],
  [40, 1600],
  [50, 2900],
  [60, 4400],
  [70, 6800],
  [80, 10500],
  [90, 21000],
  [95, 34000],
  [98, 60000],
  [99, 90000],
  [99.5, 140000],
  [99.9, 450000],
  [100, 3000000],
];

// Income at a given percentile, interpolating linearly in log(income).
export function incomeAtPercentile(p) {
  const q = Math.min(100, Math.max(0, p));
  for (let i = 1; i < DIST.length; i++) {
    const [p1, i1] = DIST[i - 1];
    const [p2, i2] = DIST[i];
    if (q <= p2) {
      if (i1 === 0) return (q / p2) * i2; // lowest bracket: linear
      const t = (Math.log(q || 1e-9) - Math.log(p1)) / (Math.log(p2) - Math.log(p1));
      return i1 * Math.pow(i2 / i1, t);
    }
  }
  return DIST[DIST.length - 1][1];
}

// Percentile (share of the world living on less) for a given income.
export function percentileForIncome(income) {
  if (income <= 0) return 0;
  let lo = 0, hi = 100;
  for (let k = 0; k < 60; k++) {
    const mid = (lo + hi) / 2;
    if (incomeAtPercentile(mid) < income) lo = mid;
    else hi = mid;
  }
  return (lo + hi) / 2;
}

// Cost-effectiveness estimates (see sources at bottom of the page).
export const IMPACT = {
  net: 5, // one insecticide-treated bed net (Against Malaria Foundation)
  life: 5000, // one death averted (GiveWell top-charity average, 2023-24)
  dalys: 150, // one year of healthy life (DALY) averted — conservative
  vita: 1.25, // one year of vitamin A for a child (Helen Keller Intl)
  deworm: 0.75, // one year of deworming for a child (Evidence Action)
  eyes: 50, // one cataract surgery restoring sight
};

export function computeImpact(income, pct) {
  const annual = (income * pct) / 100;
  const years = 40; // a full career of giving
  return {
    annual,
    nets: annual / IMPACT.net,
    protected: (annual / IMPACT.net) * 2,
    livesYear: annual / IMPACT.life,
    livesDecade: (annual * 10) / IMPACT.life,
    lives40: (annual * years) / IMPACT.life,
    dalysDecade: (annual * 10) / IMPACT.dalys,
    dalys40: (annual * years) / IMPACT.dalys,
    deworm: annual / IMPACT.deworm,
    vita: annual / IMPACT.vita,
    eyes: annual / IMPACT.eyes,
  };
}
