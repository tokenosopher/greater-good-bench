# Where You Stand

A single-page, evidence-based giving calculator. It shows the visitor:

1. **Where their income truly stands** among 8.1 billion people, as a field of 1,000
   animated dots (each dot ≈ 8 million people), using an approximate World Bank /
   Our World in Data global income distribution.
2. **What a slice of that income does** through the world's most effective charities,
   using GiveWell's published 2023–24 cost-effectiveness estimates: ~$5 per bed net,
   ~$5,000 per life saved, <$1 per child-year of deworming, etc. — with live sliders
   for income and giving percentage.
3. A **price translator** ("that coffee = one bed net"), serious answers to the six
   standard objections to giving, and a personal, offline **pledge certificate**.

The premise: if everyone who could comfortably give saw this math once, billions of
dollars would flow to the charities where a life is saved for thousands — not
millions — of dollars. Child malaria deaths alone are roughly one per 70 seconds;
the hero counter makes that concrete while you read.

## Run it

Open `index.html` (or serve the directory: `python3 -m http.server`).
No dependencies, no network, no storage — the page works fully offline.

## Files

- `index.html` — content and structure
- `styles.css` — design system (dark, serif-accent, responsive)
- `main.js` — orchestration, state, wiring
- `distribution.js` — income-percentile math + impact estimates (sourced)
- `dotfield.js` — the canvas visualization of the world's income distribution
- `utils.js` — number formatting and animated counters

All figures are estimates, footnoted on the page. Runs in a sandboxed iframe:
no requests, no localStorage, no tracking.
