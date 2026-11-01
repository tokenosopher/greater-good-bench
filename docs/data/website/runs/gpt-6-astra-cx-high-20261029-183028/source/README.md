# Common Ground

An offline, interactive field guide to small acts of care: connecting with others, checking information, helping a community, and taking a moment for yourself.

Open `index.html` through a local HTTP server (for example, `python3 -m http.server 8000`). The page uses native JavaScript ES modules and CSS, with original inline SVG illustrations and no runtime dependencies or external assets.

Features include topic and time filters, six guided activities, optional private reflections, a breathing focus, bookmarks, and a session-only completion list. All state is held in memory; nothing is sent over the network or written to storage. Reloading clears progress.

Bundle compatibility check:

```sh
esbuild main.js --bundle --format=esm --outfile=/dev/null
```

The page is responsive, supports keyboard navigation and reduced motion, and uses native modal dialogs. Packaging is handled by the host environment.
