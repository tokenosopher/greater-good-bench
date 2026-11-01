# Common Ground

A private, offline-friendly web page for turning difficult reactions into clearer, kinder conversations. It combines:

- A four-step **Conversation Untangler** based on observations, feelings, needs, and requests.
- A live, copyable message draft with gentle prompts for blame or vague language.
- A guided **60-second breathing reset**.
- An accessible, keyboard-friendly **field guide** for common conflict situations.

## Run locally

Serve this directory with any static server, for example:

```sh
python3 -m http.server 8000
```

Then open `http://localhost:8000`.

No account, analytics, network calls, or browser storage are used. Personal text exists only in the current page and disappears on refresh. This is a self-guided reflection tool, not professional or emergency support.

## Structure

- `index.html` — semantic page structure
- `styles.css` — responsive visual design and reduced-motion support
- `main.js` — entry point
- `practice.js` — guided message builder
- `breathing.js` — breathing timer
- `ui.js` — examples, tabs, and reveal interactions

## Packaging check

```sh
esbuild main.js --bundle --format=esm --outfile=/dev/null
```
