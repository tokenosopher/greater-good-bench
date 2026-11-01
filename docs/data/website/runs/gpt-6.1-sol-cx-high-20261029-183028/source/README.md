# a little good

A warm, offline-friendly guide to small acts of kindness for people, the planet, your community, and yourself.

Filter twelve practical actions by cause and available time, open a step-by-step guide, save ideas to your good list, or mark an action complete. The list and progress are held only in memory for the current visit. There are no accounts, network calls, analytics, or browser storage.

The entry point is `index.html`, which loads `main.js` as an ES module. Both stylesheets are referenced from the HTML for packaging. Fonts are embedded as data, and the original SVG illustrations are generated in JavaScript. Font licenses are included in `fonts.css`. Install dependencies with `npm install`.

Bundle verification: `esbuild main.js --bundle --format=esm --outfile=/dev/null`.

For local development, run `npm run dev`. No build output is required in this directory.
