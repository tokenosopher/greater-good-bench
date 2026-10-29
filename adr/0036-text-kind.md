# 0036. The text kind: one Markdown file, rendered by the viewer's own markdown.js

- Status: Accepted
- Date: 2026-10-29
- Builds on: [0004](0004-sandbox-untrusted-output.md), [0015](0015-viewer-csp-and-local-markdown.md),
  [0018](0018-one-kind-interface-and-an-output-record.md).

## Context

Some prompts are about writing (an essay, a story, an explanation), and the four kinds all make something to look at:
a game, files, a page or a model. A written answer needs to be read side by side at a comfortable measure, and it is
model-written text that must not run anything on the site's origin.

## Decision

- **`text` is one more `Kind` class** (`kinds/text.py` + `text.md`): the agent saves exactly one `.md` file in
  `./output/` (≤ 200 KB, UTF-8, not blank). `finalize` checks it into `output/text.md`, `verify` re-reads it (there is no
  browser step), `stage` publishes `text/text.md` through `ctx.write_text`, so it is cleaned and secret-scanned like source.
  It needs no tools on PATH.
- **`output.text` is a third output shape** beside `entry` and `items`: `{text, bytes, words, title, excerpt}`. The
  viewer picks the rendering by that field, never by the kind's name, and `KIND_UI` gives the labels ("Text", "Read").
- **The viewer renders the Markdown with the existing `markdown.js`** into an `<article class="prose">`: Marked tokens
  turned into DOM nodes, raw HTML kept as visible text, only HTTP(S) links, no remote images (ADR-0015). It is loaded by
  a dynamic `import()` only where a text is read in full.
- **No thumbnail; the title and an excerpt go into `run.json` instead.** Cards (home, page lanes, classic compare) show
  them as text with no fetch; the run page reads the whole file, and the lanes compare page shows each whole text in a
  scrollable column. Both values are read from the *cleaned* published copy, because run.json itself isn't scanned.

## Alternatives considered

- **The web kind with an HTML essay**: works today, but every text would be an iframe in the sandbox with its own
  styling, no shared readable measure, no dark mode, a click-to-play overlay and a screenshot as its picture; and HTML
  invites scripts that the sandbox then has to contain. Markdown carries the structure and nothing that runs.
- **Rendering Markdown to HTML in Python at import** (a Markdown dependency, or a hand-written converter): breaks the
  stdlib-only rule, and the viewer would then have to insert model-derived HTML (innerHTML, which ADR-0015 forbids) or
  frame it. The viewer already has a vetted token renderer for transcripts.
- **A rendered image of the text as the thumbnail** (headless Chrome at import): an extra browser step for a picture of
  words that are unreadable at card size; the excerpt says more and costs nothing.
- **Letting the viewer fetch each card's file to make the excerpt**: one request per card on every page view, and the
  page would need the Markdown parser before anything shows.

## Consequences

- A text run needs no browser or tools, so it is the cheapest kind to run and verify.
- markdown.js now renders published output as well as transcripts; its supported tokens are a public surface (the
  `.prose` styles in style.css and lanes.css cover headings, lists, quotes, code and tables in light and dark).
- Features that need a picture (covers, the video studio, `art-crit video`) skip text runs: there is nothing to show, and
  `video.make_source` returns no clip for one.
