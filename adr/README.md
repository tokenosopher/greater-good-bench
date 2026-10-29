# Architecture decision records

Why art-crit is built the way it is. Each record covers one decision, the alternatives that were turned
down, and what the decision costs.

This folder sits at the repo root and not under `docs/`, because everything in `docs/` is published to
GitHub Pages.

## How these docs fit together

- **SPEC.md**: the contract. It says *what* the system does.
- **adr/**: *why* it does it that way.
- **AGENTS.md**: how to work in the repo, plus the gotchas.

Gotchas (Playwright sleep, `append(null)`, Safari Range requests...) aren't decisions, so they stay in AGENTS.md.

## Writing one

Copy `template.md` to `NNNN-short-title.md` using the next number, and add it to the index below.

- A record's status is Proposed, Accepted, Superseded by NNNN, or Deprecated.
- Don't rewrite an accepted record when the decision changes. Write a new one and mark the old one superseded.
  Small factual updates, such as a renamed file, are fine.
- If a record backs a rule in AGENTS.md, point to it from that rule, like "(ADR-0004)".

## Index

| # | Decision | Status |
|---|---|---|
| [0001](0001-static-site-on-github-pages.md) | Static site on GitHub Pages, no backend | Superseded by 0021 |
| [0002](0002-lean-stack.md) | Lean stack: stdlib-only CLI, vanilla JS, no build step | Accepted |
| [0003](0003-repo-is-the-database.md) | The repo is the database; `docs/data` is generated | Accepted |
| [0004](0004-sandbox-untrusted-output.md) | Untrusted model output is always sandboxed | Accepted |
| [0005](0005-clean-and-secret-scan-fail-closed.md) | Clean and secret-scan before publishing, fail closed | Accepted |
| [0006](0006-one-kind-per-page.md) | A page is one prompt with one kind | Accepted |
| [0007](0007-pi-session-format-is-canonical.md) | pi's session format is canonical; harnesses convert into it | Accepted |
| [0008](0008-godot-nothreads-and-engine-dedupe.md) | Godot: no-threads web export, engine deduped by hash | Accepted |
| [0009](0009-agents-run-as-local-processes.md) | Agents run as local processes, not in a VM | Accepted |
| [0010](0010-rankings-are-local-only.md) | Rankings are written only locally; the site is read-only | Accepted |
| [0011](0011-publish-pushes-to-main.md) | `art-crit publish` pushes to `main`, no PR flow | Accepted |
| [0012](0012-asset-cache-busting.md) | Asset cache-busting | Proposed |
| [0013](0013-web-kind-packaged-with-esbuild.md) | Web pages are packaged into one file with esbuild | Accepted |
| [0014](0014-openrouter-upstream-routing.md) | Pin the OpenRouter upstream provider per run (`MODEL@upstream`) | Accepted |
| [0015](0015-viewer-csp-and-local-markdown.md) | Local Markdown token rendering, CSP and sandboxed fullscreen | Accepted |
| [0016](0016-page-json-includes-runs.md) | One page.json includes ranked runs | Accepted |
| [0017](0017-run-directory-is-the-unit-of-work.md) | The run directory is the unit of work; the effort-run format is retired | Accepted |
| [0018](0018-one-kind-interface-and-an-output-record.md) | One Kind interface; `state` is the agent's, `output` is the kind step's | Accepted |
| [0019](0019-publish-each-run-as-it-finishes.md) | `art-crit run` publishes each run as it finishes (default) | Accepted |
| [0020](0020-renamed-to-art-crit.md) | Renamed from llm-bench to art-crit | Accepted |
| [0021](0021-cloudflare-pages-subpath.md) | Cloudflare Pages on a domain subpath with compressed engine | Accepted |
| [0022](0022-community-votes.md) | Community votes: GitHub sign-in, hearts and medals in D1 behind the Worker | Accepted |
| [0023](0023-muse-code-reads-its-exported-session.md) | Muse Code: the session is `muse export`ed after `exec`, not read from `--json` | Accepted |
| [0024](0024-prompt-requests-are-local.md) | Prompt requests are local: `art-crit serve` keeps them outside `docs/` | Partly superseded by [0030](0030-lanes-design-and-prompt-requests-as-issues.md) |
| [0025](0025-blender-kind-through-the-official-mcp.md) | Blender kind: a windowless Blender per run, driven through the official MCP server | Accepted |
| [0026](0026-reference-images-are-published.md) | Reference images are published beside the page, shown as sidebar thumbnails | Accepted |
| [0027](0027-local-run-monitor.md) | A local run monitor in `art-crit serve`, and stopping a run with a file | Accepted |
| [0028](0028-page-runs-reuse-the-pages-references.md) | A `--page` batch reuses the page's published references | Accepted |
| [0029](0029-thumbnails-cache-headers-and-module-preload.md) | Import-time thumbnails, cache headers for run files, module preloads | Accepted |
| [0030](0030-lanes-design-and-prompt-requests-as-issues.md) | The lanes design for home, page and compare; prompt requests become GitHub issues | Accepted |
| [0031](0031-retry-is-a-cli-command-over-run-page.md) | Retry is a CLI command that reuses `run --page` and replaces a failed run once its retry works | Accepted |
| [0032](0032-social-videos-are-local.md) | Social videos are made locally with ffmpeg and headless Chrome, from the CLI or the local compare page | Accepted (cards: superseded by [0033](0033-videos-are-rendered-frame-by-frame.md); panel: by [0034](0034-video-studio-is-a-local-page.md)) |
| [0033](0033-videos-are-rendered-frame-by-frame.md) | Social videos are drawn frame by frame by an animated page in Chrome, with a synthesized sound track | Accepted |
| [0034](0034-video-studio-is-a-local-page.md) | The video studio is a local page that designs a video and renders it with the frame-by-frame scene | Accepted |
| [0035](0035-ori-runs-its-own-runtime-from-jsonl.md) | Ori: its own runtime agent from its JSONL stream, models from OpenRouter's live catalog | Accepted |
| [0036](0036-text-kind.md) | The text kind: one Markdown file, rendered by the viewer's own markdown.js | Accepted |
| [0037](0037-fork-for-mtwabp-bench.md) | Fork art-crit as mtwabp bench, changing what the site asks rather than how it works | Accepted |
