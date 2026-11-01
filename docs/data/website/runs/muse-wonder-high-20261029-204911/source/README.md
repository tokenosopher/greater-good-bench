# 8 Billion Neighbors

A seven-minute interactive journey designed to do, at planetary scale, what
most improves life for the most people: make strangers feel like neighbors,
replace cynicism with common ground, calm one nervous system at a time, and
turn good intentions into one small, specific, completed act of kindness.

## What you do on the page

1. **Shrink the world** — Earth as a village of 100 people; tap facts
   (clean water, electricity, internet, literacy, vaccines) and watch the
   village change, including how much has quietly improved.
2. **Borrow another life** — meet composite neighbors from around the world,
   then reveal what you share with them.
3. **Find common ground** — guess how many people share four simple hopes
   before revealing the (very high) agreement, to counter false polarization.
4. **Breathe together** — a guided 4–2–6 breath alongside a live-feeling
   counter of humanity's breaths.
5. **Take a kindness mission** — pick where you are and how long you have;
   get a specific, scripted, completable act. Finish it and plant a flower
   in your kindness garden. A ripple calculator shows what happens if
   millions did the same weekly.
6. **Leave a light on** — choose one word for the world, add your star to a
   constellation, and copy a one-card take-away plan.

Progress across five milestones lights up in the header. No accounts, no
tracking, no storage — all state lives in memory and is forgotten on reload,
on purpose.

## Running it

Open `index.html` via any static server (e.g. `python3 -m http.server`) —
scripts are ES modules (`main.js`), styles in `style.css`, no dependencies
and no network requests. Bundling check:

```sh
esbuild main.js --bundle --format=esm --outfile=/dev/null
```

Figures are rounded global estimates (UN / World Bank / WHO / UNESCO / ITU,
~2024), labeled on-page as orientation rather than precision. Portraits are
composites, clearly labeled as such.
