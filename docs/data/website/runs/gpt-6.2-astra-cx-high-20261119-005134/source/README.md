# Common Good

An illustrated, offline field guide to nine everyday acts of care. Browse by category or time, draw a random action, or save ideas for the current visit. Each action has a three-step checklist.

Open the page through a local static server. The entry point is `index.html`, which loads `main.js` as an ES module. Illustrations are drawn on canvas and the DM Sans font is embedded in the stylesheet. The font license is included in `FONT-LICENSE.txt`.

Saved actions and checklist progress stay in memory and reset on reload. No account, storage, or network services are used.

Check the JavaScript bundle with `esbuild main.js --bundle --format=esm --outfile=/dev/null`.
