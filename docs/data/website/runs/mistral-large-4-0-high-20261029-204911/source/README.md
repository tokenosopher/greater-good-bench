# The Good Multiplier

An interactive, fully offline web page about the most cost-effective, evidence-backed
ways money can improve lives — malaria nets, deworming, vitamin A, direct cash transfers,
safe water, vaccines — and what would happen if everyone on Earth gave a little to them.

## Run it

Serve this directory and open `index.html`, e.g.:

```
python3 -m http.server 8000
# then visit http://localhost:8000/
```

## Structure

- `index.html` — entry point; loads `styles.css` and `main.js` (ES module).
- `main.js` — UI wiring: sliders, animated counters, quiz, accordion, pledge calculator, share/copy.
- `model.js` — the cost-effectiveness data and all math (scenario + personal pledge).
- `globe.js` — three.js hero globe (point-cloud Earth, arcs flowing toward regions of need).
- `styles.css` — all styling; system fonts only, no external assets.

## Notes

- Dependencies: `three` (npm). No CDNs, no import maps, no network requests, no storage —
  the page works offline in a sandboxed iframe.
- Verify it bundles: `npx esbuild main.js --bundle --format=esm --outfile=/dev/null`
- All figures are approximate published estimates (GiveWell, J-PAL/IPA RCTs, Cochrane,
  DCP3, World Bank, OECD, SIPRI, WHO) and are labeled as rough ranges in the UI.
