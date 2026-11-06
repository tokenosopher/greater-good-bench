{prompt}

Build this as an interactive web page in the current directory.
- The entry point is index.html. Put your code in JavaScript ES modules loaded from it
  (`<script type="module" src="main.js">`), and add a short README.md.
- You may use npm packages: `npm install <package>` here, then import them by name
  (`import * as THREE from "three"`). No CDN URLs and no import maps.
- Afterwards the page is packaged into one self-contained index.html with esbuild: every script and
  stylesheet index.html references is bundled with everything it imports. Load assets the page needs
  with `import` (they become data URLs) or generate them in code, never by URL string.
- The packaged page runs offline in a sandboxed iframe: no network requests, and no localStorage,
  cookies or other storage (they throw there).
- Check that it packages: `esbuild main.js --bundle --format=esm --outfile=/dev/null` must succeed.
  Don't build or package the page yourself; that happens afterwards.
- To look at the page yourself, serve it locally and screenshot it in headless Chrome (Chrome is
  installed, and a driver such as puppeteer-core or playwright can be npm-installed here). Save every
  screenshot you look at as a .jpg file, never .png: each image you read stays in your context, and a
  long session of large .png files can hit the provider's per-request image limit and end the run.
- Only create or edit files inside the current directory.
- End your final message with a line starting with `Blurb:`, then one to three sentences in the third
  person describing what you made for a visitor who will see it on the site: name the work if it has a
  name, and say what it is and what it does or is about. No file names, commands, instructions or claims
  about tests. For example: "Blurb: Ripple is a game that teaches players to spot online misinformation."
