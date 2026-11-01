# Common Ground

Common Ground is an interactive civic-action tool that helps people choose one realistic way to improve their week, then shows how consistent local actions can add up at community scale.

## Run locally

Serve the directory with any static server, for example:

```bash
python3 -m http.server 8000
```

Then open `http://localhost:8000`. The production bundle can be checked with:

```bash
esbuild main.js --bundle --format=esm --outfile=/dev/null
```

## Features

- Personal action matcher based on available time, budget, and preferred style
- Optional regional context for more locally relevant suggestions
- A personal “good week” planner with copy-to-clipboard support
- Interactive collective-impact simulator with household, block, neighborhood, and city scale
- Transparent, directional assumptions and no accounts, storage, analytics, or network calls
- Responsive, accessible, reduced-motion-aware interface

The impact figures are deliberately labeled as illustrative estimates. The tool is intended to prompt reflection and action, not to function as formal carbon or financial accounting.
