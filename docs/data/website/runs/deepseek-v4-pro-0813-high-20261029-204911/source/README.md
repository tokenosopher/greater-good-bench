# A Little Better

A calm, private, fully offline web toolkit built around one idea: **if everyone got
a little clearer, a little plainer, and a little kinder, a great deal of confusion
and harm would simply not happen.**

The page has no accounts, no trackers, no network requests, and no storage of any
kind — everything you type lives only in the open tab. It is meant to be copied,
translated, and shared freely.

## The four tools

1. **Plain Words** — paste any text and get its reading level, word/sentence stats,
   and gentle suggestions (long sentences, filler, big words, passive voice). One
   click rewrites common jargon into plain language. Clear writing widens the circle
   of people who can understand and be helped by an idea.

2. **Decision Compass** — a six-step, in-private walk through any hard choice:
   name the decision and what matters, list who is affected, list options, weigh
   who gains and who loses, then pass two honesty tests (the universality test and
   the one-year test). It ends by producing a written case you can copy and act on.

3. **Kind Speech** — before sending a message you might regret, run it through three
   lenses (true? necessary? kind?) and get specific flags for the exact patterns
   that turn a message into a wound instead of a bridge.

4. **The Ripple** — pick one tiny daily kindness and a timeframe, and watch a
   compounding chart show what a single ordinary act repeated becomes. Because
   kindness is a habit, not a mood.

## Why these four

Of the many ways to improve the world, these target the highest-leverage,
most-deployable changes: better decisions, clearer communication, and kinder
defaults. They cost nothing, need no infrastructure, and work in every language
and at any literacy level once translated.

## Build / run

- Entry point: `index.html` (loads `styles.css` and `main.js` as an ES module).
- Everything is dependency-free vanilla JavaScript — no CDN, no fetch, no storage.
- Verify it bundles cleanly:

  ```
  esbuild main.js --bundle --format=esm --outfile=/dev/null
  ```

- Serve locally to preview:

  ```
  npx serve .   # or: python3 -m http.server
  ```

## Privacy & accessibility notes

- No `localStorage`, `sessionStorage`, cookies, or network calls anywhere.
- Semantic tabs (ARIA `tablist`), skip link, keyboard navigation, `prefers-reduced-motion`,
  and a full dark mode via `prefers-color-scheme`.