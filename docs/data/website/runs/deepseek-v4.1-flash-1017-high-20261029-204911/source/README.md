# MULTIPLIER

**The most good you can do, ranked.**

An offline, single-page field guide to the highest-leverage actions available to an ordinary person — and a calculator for what those actions add up to when lots of people take them.

## What's inside

- **The exchange rate** — a blunt comparison of what money buys as a consumer good versus as global health.
- **Impact lab** — choose a yearly giving budget and a cause mix; see estimated healthy years, CO2e avoided and animals spared. The mix is adjustable and updates live.
- **The atlas** — 18 actions across money, lifestyle, body, voice and career, filterable and sortable by leverage, healthy years, emissions, animals or effort. Each card expands to explain why it works, how to start, and its source.
- **Your portfolio** — add actions from the atlas, then scale the result from one person to a town, a million people, a billion, or everyone. Includes a plain-text commitment summary with copy-to-clipboard (with a manual fallback).
- **The multiplier** — an interactive cascade showing how one conversation compounds through a network.
- **Method** — assumptions, ranges, sources, and an explicit statement of what the page is *not* claiming.

## Running it

```bash
python3 -m http.server 8765
# open http://localhost:8765
```

No build step is needed for local development. The page uses only ES modules and CSS.

## Packaging check

```bash
npx esbuild main.js --bundle --format=esm --outfile=/dev/null
```

## Structure

```
index.html      markup and copy
styles.css      all styling
main.js         entry point, wiring and reveal behaviour
src/data.js     interventions, actions, and all assumptions
src/lab.js      giving-budget calculator
src/atlas.js    action grid, filters and sorting
src/portfolio.js selection state and scaled totals
src/ripple.js   cascade visualisation
src/hero.js     the 800-dot canvas (one dot ≈ 10 million people)
src/format.js   number formatting and animation helpers
```

## Notes on the numbers

Every figure is a rounded midpoint estimate drawn from published cost-effectiveness research (GiveWell, 80,000 Hours, Project Drawdown, Animal Charity Evaluators, WHO, and others). Ranges are wide and context matters. The page intentionally keeps health years, tonnes of CO2e and animals as separate metrics rather than collapsing them into one false-precision score.

The page stores nothing, tracks nothing, makes no network requests, and works fully offline — including in a sandboxed iframe.

## Credits

Built as a public good. No ads, accounts or analytics.
