# Agent guide: art-crit

Start here if you're an agent picking up this repo with no prior context. **Keep this file current:** when
you change how something works, add a command, or learn a gotcha the hard way, update the relevant section
in the same commit.

## What this is

**This repo is a fork: Greater Good Bench** (repo `tokenosopher/greater-good-bench`), a public benchmark asking
frontier models whether they can make something that, if everyone saw, read, used, played or watched it, would
improve the world for the greatest number of people: what gets measured in AI gets optimized, so this starts
measuring it. Six pages (SVG, website, 3D model, game, animation, essay; `prompts/README.md` has the prompts, the
`frontier` set and the exact commands), run through art-crit unchanged, with no automated judging: the ranking is the
owner's own plus community votes. Only what visitors see was rebranded (titles, logo, home copy, `SITE_NAME` in
`docs/assets/dom.js`); the CLI, package, config, `docs/` layout and Cloudflare paths keep the art-crit names (ADR-0037).
Everything below is the upstream art-crit's guide, still accurate for the code; where it names fenderog.com or
`fenderog/art-crit` as the live site and repo, those are the upstream's. This fork is live on GitHub Pages at
https://tokenosopher.github.io/greater-good-bench/ (from `main:/docs`); Cloudflare (votes, a custom domain) is set up by
following `DEPLOY.md`, and the site's address lives only in `cloudflare/wrangler.jsonc` (routes + `vars`) and, for the
local video tools, `[site] url` in `art-crit.toml`.

A CLI (`art-crit`, Python) plus a static GitHub Pages site that shows what LLMs make for visual and spatial prompts,
side by side, for comparisons you judge by eye rather than by a score (the name is art school's "crit").

- **Page** = one prompt/task (e.g. `voxel-horse`).
- **Run** = one model × effort level attempt at that task.
- **Kind** = what a page's runs produce: `godot` (a project, published as a playable web build), `media`
  (shown as "Vector" in the UI; image/video files the agent saved in `./output/`), `web` (a page with ES modules + npm packages, packaged
  into one `index.html` with esbuild) or `blender` (a `.glb` + renders made in a per-run windowless Blender through
  the official Blender MCP server) or `text` (one Markdown file in `./output/`, rendered by the viewer's own
  markdown.js as a readable page; cards show its title and excerpt). One kind per page.

Each run has three parts: its output (a playable Godot web build, images/videos, or a packaged web page), the full agent
transcript with every tool call, and metrics (tokens, cost, duration).

- Repo: github.com/fenderog/art-crit (public). The site is built from `main:/docs` by Cloudflare Pages:
  https://fenderog.com/art-crit/ (old GitHub Pages URL: https://fenderog.github.io/art-crit/).
- **SPEC.md is the contract**: the data layout, the JSON schemas, cleaning, the CLI and the viewer. Read
  it before changing behavior, and update it together with the code.
- README.md is the user-facing usage.
- **adr/** records *why* things are built this way, plus the alternatives that were turned down. Check it before
  reversing a design choice, and add a record (from `adr/template.md`) when you make a new one. CLAUDE.md
  imports `adr/README.md`, so keep its index table current.

## Layout

```
src/art_crit/          CLI, standard library only (argparse, json, subprocess, tomllib, http.server)
  cli.py            argparse wiring: import, list, rm, rename, retry, rebuild, serve, publish, run, models
  config.py         art-crit.toml parsed once (`Config.load`) + `RunRequest` (the inputs of one `art-crit run`)
  retry.py          `art-crit retry`: failed runs of a page -> one `run --page` batch, then drop the ones that now work (ADR-0031)
  video.py          `art-crit video`: social-media videos of runs (ffmpeg + headless Chrome), local only (ADR-0032): source
                    clips -> JPEG frames -> a plan (timeline, `TIMING`, tiles, stickers) per layout -> frames drawn in Chrome
                    piped into ffmpeg (ADR-0033); scene/ = the animated pages that draw them (scene.js = the layouts,
                    studio.js = the studio's templates and cards, parts.js = the opening (hook) and closing (finale) both
                    use, motion.js = the helpers; imports docs' runs.js);
                    video_sound.py = the synthesized music styles + sound effects, cued from the same plan
  studio.py         the video studio (ADR-0034): `catalog()` (templates, looks, cards), `check_spec`, `timeline` (shared by
                    the page's preview through api/studio/plan and the render), `make_studio_video`
  importer.py       run directory (or a batch of them) -> docs/data/<page>/runs/<id>/ (clean, secret scan, then move)
  clean.py          session cleaning, path rewrites, secret scan/redact
  site.py           rebuild page.json (with runs) / pages.json (+ each run's rank from ranking.json), rm, list, engine GC
  serve.py          `art-crit serve` (GitHub-Pages-like) + the local-only APIs: PUT api/rank, GET/PUT api/requests
                    and the run monitor (GET api/runs, GET api/run, POST api/stop; see Run monitor, ADR-0027)
  harness.py        Harness interface + Pi, ClaudeCode, Agy, GrokBuild, MuseCode, Codex, Ori (streams -> pi-format session)
                    + metrics parsers
  runner.py         `art-crit run`: plan -> run agents in parallel -> collect -> kind step (finalize + verify) -> import;
                    `RunDir` = <batch>/<run id>/{run.json,work/,harness/,output/}; `wait_agent` waits for the running
                    agent, a timeout and `harness/stop` (the local monitor's Stop button) all kill its process group
  picker.py         no -m/--set (or -i/--pick): the interactive harness -> models -> levels menu; models are picked
                    by number or an fzf-style fuzzy search (`fuzzy_score`/`fuzzy_matches`); a catalog over LIST_LIMIT
                    (20) is not printed up front — search first, `list` only on purpose; the picks become ordinary
                    -m specs, so planning validates them like a hand-typed spec
  pi_ext/           art-crit-shipped pi extensions loaded with explicit `-e` (work under `-ne`):
                    `openrouter_routing.ts`, loaded for every OpenRouter run: logs the serving upstream + real
                    cost to `ART_CRIT_ROUTE_LOG`, and pins the upstream from `ART_CRIT_OPENROUTER_ROUTING` (`MODEL@slug`)
                    `openrouter_sticky_upstream.ts`, loaded for unpinned `openrouter/google/*` runs: pins every later
                    request to the upstream that served the first (Gemini thought signatures don't verify across upstreams)
  kinds/            one class per kind, registered in `KINDS` (ADR-0018): `Kind` = brief, tools, finalize, verify, stage
    godot.py        headless Godot export, boot check, engine dedupe + index.html rewrite
    media.py        check/normalize work/output/ files with ffprobe/ffmpeg -> output/manifest.json; also the thumbnail
                    helpers every kind and `rebuild` use (`write_thumb`, `add_thumbs`, `screenshot_thumb`; ADR-0029)
    web.py          inline the page's scripts/stylesheets with esbuild -> output/index.html (one file)
    blender.py      a Media with `.glb`: `prepare` installs the MCP add-on, `agent_session` = the run's own Blender
    text.py         one .md in work/output/ -> output/text.md + manifest.json; `stage` records title, words, excerpt (ADR-0036)
    <kind>.md       brief template per kind ({prompt}, and {tools} from [run].tools, are substituted)
  browser.py        the headless-Chrome check the godot and web kinds share (Playwright is optional, imported lazily)
docs/               the site: vanilla JS ES modules, no viewer build step, no framework
  index.html page.html compare.html = the lanes design (ADR-0030): assets/lanes/*.js + lanes.css, on the shared modules;
                    lanes/request.js = "Request a prompt" -> Worker api/request (a GitHub issue), else GitHub's prefilled form
  classic/          the previous index/page/compare (table, grid, rank editing, local requests), <base href="../">
  run.html play.html monitor.html, assets/*.js, assets/style.css
  studio.html       the video studio, local only (assets/studio/studio.js + studio.css; ADR-0034)
  _headers          Cloudflare Pages cache policy: run dirs a day, vendor + engines immutable (ADR-0029)
  assets/dom.js fmt.js runs.js output.js   shared helpers: DOM + fetch, formatting, run/rank/vendor helpers, and
                    output.js, which holds all sandbox-critical code (sandboxedGame, mediaElement, renderOutput, KIND_UI);
                    model.js = the .glb viewer (three.js bundle vendor/three-gltf.min.js, loaded on click);
                    help.js = the runs table's column tooltips; aside.js = the collapsible details sidebar of page/run.html; requests.js = local-only prompt requests; monitor.js = the local run monitor (polling, live metrics, Stop); transcript.js, markdown.js; votes.js = the community
                    hearts/medals store + vote bar (null without the API); one script per page
  data/<slug>/...   generated by the CLI; don't hand-edit (re-import instead)
  engines/<sha12>/  deduplicated Godot engines (~38 MB wasm each, stored once)
cloudflare/         Pages staging build (prepare.py) + subpath/engine streaming Worker (router.mjs, wrangler.jsonc: the
                    one place for the site's host, SITE_PREFIX ("" or "/path"), PAGES_URL and GITHUB_REPO);
                    votes.mjs = the Worker's <prefix>/api/* (GitHub sign-in, hearts, medals), schema.sql = its D1 tables
adr/                architecture decision records (not published: they're outside docs/)
tests/              pytest + Python Playwright; fixtures/fake_pi/{pi,claude} are fake harnesses;
                    js/ = node:test for the votes Worker over an in-memory SQLite (run by test_cloudflare.py)
art-crit.toml          [clean] path rewrites, [run] batch dir / parallel / timeout / tools listed in the brief,
                    [sets] named model sets for `art-crit run --set`, [site] url = the published address (video cards,
                    compare links)
```

## Commands

```sh
uv run python -m pytest -q            # all tests; must stay green
uv run art-crit serve --port 8000        # preview docs/ exactly like GitHub Pages
                                        # /monitor.html = live batches, transcripts and Stop (local only, ADR-0027)
uv run art-crit run --dry-run "prompt" -m openai-codex/gpt-6-sol:low   # plan only, no model calls
uv run art-crit run --dry-run --kind media "an SVG pelican" -m openai-codex/gpt-6-sol:low
uv run art-crit run --dry-run --kind web "a three.js horse" -m openai-codex/gpt-6-sol:low   # needs esbuild + npm
uv run art-crit run --dry-run --kind blender "a low-poly fox" -m claude-code:opus:low   # needs blender + uvx
uv run art-crit run --dry-run --kind text "an essay on chairs" -m openai-codex/gpt-6-sol:low   # one Markdown file, no tools
uv run art-crit run --dry-run "prompt" -m claude-code:opus:low --ref robbie.jpg   # a file from <root>/references/, copied into each run's work/references/
uv run art-crit run --dry-run "prompt" --set cheap   # a model set from art-crit.toml [sets] (or a file path)
uv run art-crit run --dry-run "prompt"                # no -m/--set: pick harness, models and levels interactively (-i/--pick)
uv run art-crit run --dry-run --page <slug> -m MODEL:LEVEL   # add runs to an existing page (reuses its prompt + kind)
uv run art-crit run --dry-run "prompt" -m openrouter/deepseek/deepseek-v4.1-flash@deepinfra:low   # pin the OpenRouter upstream
uv run art-crit models gpt-6             # models + effort levels from pi
uv run art-crit models --harness claude-code   # Claude Code's (from the table in harness.py)
uv run art-crit models --harness agy           # live agy models (effort is part of its slug)
uv run art-crit models --harness grok-build    # live grok models, effort menu from harness.py
uv run art-crit models --harness muse-code     # muse models + levels (a table in harness.py)
uv run art-crit models --harness codex         # codex models + levels (live from `codex debug models`)
uv run art-crit models --harness ori deepseek  # OpenRouter's catalog (fetched live: art-crit's only network read)
uv run art-crit run --dry-run "prompt" -m claude-code:opus:high -m openai-codex/gpt-6-sol:high   # mixed harnesses
uv run art-crit retry --dry-run <slug> [run-id]          # run a page's failed runs again (costs money without -n); replaces each one that now works
uv run art-crit video <slug> <run-id> <run-id> -d 3 -o tmp/vid     # social videos (ffmpeg + Chrome, no model)
                                        # /studio.html under `art-crit serve` = the video studio (design and render one video)
uv run art-crit import <run-dir|batch-dir> --page <slug>   # publish runs written by `art-crit run`
uv run art-crit run --no-publish "prompt" -m MODEL:LEVEL   # import locally only; run publishes each run by default (ADR-0019)
uv run art-crit publish -m "msg"         # commit + push docs/ only (Pages deploys in ~1 min); a run publishes just its own files
python3 cloudflare/prepare.py          # validate the Pages upload (<25 MiB per asset) locally
node --test tests/js/votes.test.mjs    # the votes API alone (needs node:sqlite, Node 22.13+)
cf pages deployments list --project-name art-crit   # Git-triggered deployment status
```

## Rules (don't break these)

- **Never modify `~/dev/effort-runs/`.** It holds the user's original runs and is read only (art-crit no longer reads
  that format). `art-crit run` writes to `~/dev/art-crit-runs/`. (ADR-0003, ADR-0017)
- **Never call a real model in tests.** `art-crit run` tests put `tests/fixtures/fake_pi/pi` first on PATH.
  A real `art-crit run` costs money: only do one when the user asks, use a cheap model and few levels, and
  point `--root` at a throwaway copy of the site so live data isn't touched. (ADR-0009)
- **Game iframes must never get `allow-same-origin`.** `sandboxedGame()` in `docs/assets/output.js` is the
  only place games are embedded. The compare cards' ↗ pop-out opens `play.html` (which uses it), never the raw
  entry URL; run and expanded-table fullscreen links also go through `play.html`. The Worker serves everything under
  `data/` with that sandbox as a CSP header (`router.mjs`), so a raw output URL opened directly gets an opaque origin
  too; keep its flags equal to `sandboxedGame()`'s. (ADR-0004)
- **Web pages are verified the way they're shown:** offline, inside the site's sandbox (`Web.verify`, `verify_page(..., sandboxed=True)`).
  Don't relax that to a plain page load; it's what guarantees a packaged page has no outside dependencies. (ADR-0013)
- **Model-made SVGs are only shown with `<img>`** (`mediaElement()` in output.js), which never runs their
  scripts. Never inline them, put them in object/embed/iframe, or link them for viewing on the site's origin
  (downloads use the `download` attribute). (ADR-0004)
- **Everything published is cleaned and secret-scanned first.** A hit aborts before anything is written
  (`--redact` masks instead). The repo is public: no real session files or personal paths in test
  fixtures. (ADR-0005)
- **Viewer dependencies:** third-party JS is vendored and pinned under `docs/assets/vendor/`, never loaded from a CDN
  (three.js is one prebuilt, committed esbuild bundle; the viewer itself still has no build step).
  Markdown uses `markdown.js` (loaded through the transcript), never `innerHTML`; dynamic styles use CSSOM properties
  because all five viewer documents enforce a same-origin CSP. (ADR-0015)
- **Hosting:** Git pushes to `main` trigger the Git-linked Cloudflare Pages project; `art-crit publish` still commits
  and pushes `docs/`. Publishing commits only the paths it publishes (`git commit -- <paths>`): a run's commit holds
  that run's files, so a pending edit or something staged elsewhere in the working copy never rides along. Only the
  address in `cloudflare/wrangler.jsonc` routes to the Worker (a whole host with `SITE_PREFIX = ""`, or `<prefix>` and
  `<prefix>/*`; upstream `/art-crit`), which strips the prefix and streams compressed Godot WASM from `PAGES_URL`.
  Never hard-code the prefix, host or repo in the Worker: they come from `env` (`siteConfig` in router.mjs). `docs/` remains the local source of truth. (ADR-0021)
- **Viewer data:** `page.json.runs` includes ranks; per-run `run.json` remains the source of truth. `rebuild` removes
  legacy `results.json`. All four page views use `loadPage()` for a single page-data request. (ADR-0016)
- **Kinds are classes, not branches.** The runner, importer and viewer never switch on a kind's name: a kind is one
  `Kind` subclass (`kinds/`), and the viewer shows any `output` with an `entry` through `renderOutput()` (the other two
  shapes: `items`, a gallery, and `text`, Markdown read as an article). Keep the
  three questions apart: `state`/`error` = the agent, `output.ok`/`output.error` = the kind step, `output.verified` = the
  check. A failed export is `state: complete` with `output.ok: false`. (ADR-0018)
- **Keep it lean.** Stdlib-only CLI, no JS frameworks or bundler for the viewer (Cloudflare's staging build only
  compresses oversized engines; esbuild only packages model-made web pages, ADR-0013, ADR-0021); the user checks for this. Prefer small
  functions and small diffs, and don't add dependencies without asking. (ADR-0002)
- **`--ref` files** live in `<root>/references/` (the user's own files): the batch dir and every run's
  `work/references/` get copies, the brief (not the page's prompt) lists them, and `importer.stage_source` skips
  `references/`. Import publishes the batch's copies to `docs/data/<slug>/references/` and the page sidebar shows
  the images as thumbnails (ADR-0026): never put them in anything but `<img>`, like model-made SVGs. `--page`
  adds runs to an existing page and adopts its published references (`runner.page_refs`) unless the batch passes
  its own `--ref` (ADR-0028), so a "use the reference image" prompt can't silently run with no image staged.
- **Prompt requests become GitHub issues** (ADR-0030): the lanes home posts to the Worker's `POST api/request`, which
  opens the issue with the `GITHUB_ISSUES_TOKEN` bot token (never the visitor's token), fences the untrusted text, and
  caps requests in D1 (`prompt_requests` keeps no text). Without that API the form opens GitHub's prefilled new-issue
  page. The classic home's local list (ADR-0024) still keeps `requests.json` beside `docs/`: never move it under `docs/`.
- **The run monitor is local only and never kills anything itself** (ADR-0027): `api/runs`/`api/run` need a loopback
  `Host` and are answered *without* `Access-Control-Allow-Origin` (never add it back for those two), the Stop button
  writes only `<run>/harness/stop`, and `runner.wait_agent` — in the process that owns the agent — is what kills its
  process group. The monitor's transcripts drop image blocks and clip long strings (`MONITOR_CLIP`, `MONITOR_ENTRIES`):
  a live pi session keeps a base64 copy of every image the agent read. It polls every 2s and rebuilds its panes, so it
  carries the reader's view itself (`show()`/`viewState()` in monitor.js: scroll, open `<details>`, and the transcript's
  node with its filter until the session grows): capture the state *before* building the new nodes, because building
  moves the cached transcript node out of the old tree and that zeroes its scroll and briefly shrinks the document.
- **Rankings are only written by `art-crit serve` on the user's machine** (`PUT api/rank`, which refuses cross-site
  writes and any non-loopback `Host`, against DNS rebinding); the Worker answers 404 for it. (ADR-0010)
- **Community votes and prompt-request issues are the only things the published site writes**, through the Worker's
  `/art-crit/api/*` (ADR-0022, ADR-0030). Writes need a session cookie *and* an `Origin` equal to the site's own; don't
  loosen either, add CORS headers to the API, or add another write path. Only GitHub ids are stored (never tokens), and votes are not in git.
  `tallies` is kept only by the triggers in `cloudflare/schema.sql`: never write it from the Worker. Apply the schema to D1
  *before* deploying a Worker that needs it (an older Worker runs on a newer schema, not the reverse).
- **Social videos stay local** (ADR-0032, ADR-0034): `art-crit video`, the video studio and `POST/GET api/video`, `GET api/studio`,
  `POST api/studio/plan`, `POST api/video/delete` write (and delete) only under `<root>/videos/` (outside `docs/`,
  git-ignored), the API follows the `api/rank` write checks and its GETs the monitor's (loopback `Host`, no CORS headers), and a
  file is served or deleted only by a name `studio.renders` lists (never a path from the request). Games are recorded through `play.html` (the sandbox), model-made SVGs only
  through an `<img>`, and the video scenes (and studio.html) put every string from a run, a prompt or a card in with
  `textContent` (they have strict CSPs). The studio's rules live in studio.py: the page asks for the timeline rather than
  computing its own, so preview and render can't disagree.
- **Per-run MCP config** (ADR-0025): a kind's MCP servers reach the agent through flags or files in the run's own
  dirs (`--mcp-config`, `-c mcp_servers.*`, `work/.pi/mcp.json` + `--approve`, `work/.grok/config.toml`,
  `work/.ori/mcp.json`), never `~/.pi`,
  `~/.claude`, `~/.codex` or `~/.grok`. The one exception, with the user's consent: agy and muse read MCP servers only
  globally, so `~/.gemini/config/mcp_config.json` and `~/.config/muse/settings.json` each hold a permanent
  `art-crit-blender` entry running `~/.cache/art-crit/mcp_proxy.py`, which is inert (no tools) outside a run. Tests point
  both configs and the cache at temp dirs (conftest); never write the real ones from a test.
  The blender add-on lives in `~/.cache/art-crit/`, never in the user's Blender. A .glb is shown only by `model.js`
  (three.js parses it; nothing in it runs).
- **Untrusted text** (model output, transcripts) goes through `textContent` or `renderMarkdown()`, which
  builds DOM nodes from Markdown tokens and permits only HTTP(S) links. Never use innerHTML with run data. (ADR-0004)
- Commit or push only when the user asks, or as part of a task they asked you to ship.

## Gotchas learned the hard way

- **Godot web:**
  - Nothreads export only: GitHub Pages can't send COOP/COEP headers. `mainPack = "index.pck"` must be
    set when the engine is loaded from `engines/`.
  - The headless export can exit 0 after failing, so check that the output files exist.
  - Headless Chrome needs `--enable-unsafe-swiftshader --use-angle=swiftshader` for WebGL.
  - Godot removes `#status` from the page once the game has booted; that's the boot signal.
- **Playwright:** poll with `page.wait_for_timeout`, not `time.sleep`; sleep starves Playwright's event
  processing. Under the viewer CSP, pass `() => …` functions to `wait_for_function`; bare expression strings
  trigger an `unsafe-eval` violation.
- **pi:**
  - `--model provider/id:level` silently clamps unsupported levels, and it reports levels for an unknown
    model instead of failing. `art-crit run` checks both against `pi --list-models` and the RPC levels query
    before starting.
  - Model ids can contain `:`, so levels are read from after the last colon.
  - art-crit keeps no list of pi models (Codex included): they come live from `pi --list-models`. New ones show up
    after `pi update --models` refreshes pi's catalog.
  - That catalog can lag OpenRouter, because pi.dev's overlay feeds it, not OpenRouter's live list: a model that is
    live upstream but missing from `pi --list-models` fails planning for a whole set (one unknown spec aborts all of
    it), while pi itself would accept it as a "custom model id" with a made-up level menu. Bridge it with a
    `providers.<name>.models` entry in `~/.pi/agent/models.json` that mirrors the sibling model's metadata (it adds
    to the provider's list, it doesn't replace it). It shadows the official entry for that id once the catalog
    catches up, so delete it then: `oss-frontier` carried `deepseek/deepseek-v4.1-flash-1017` that way for a day.
  - An `openai-codex` run can die on its first request with "Your authentication token has expired. Please try
    refreshing it." while the stored OAuth JWT is still days from its `exp`: `pi auth check` reports `ready` and
    pi therefore never refreshes it, and the ChatGPT backend answers 401 `token_expired` (reproduce with a curl
    POST to `https://chatgpt.com/backend-api/codex/responses` carrying the token). We hit it right after a Codex
    CLI re-login that morning (`~/.codex/auth.json` held a different auth session id). Force a refresh with
    `pi auth print-bearer-token --provider openai-codex --min-expiry 480h` (it exits 1 on the unmet min-expiry
    *after* persisting the new token) or `/login openai-codex`; art-crit's own `retry` then re-runs the batch.
  - `--mode json` stdout (`harness/events.jsonl`, never published; `Pi.session_file` skips it) is ~1 MB of `message_update` streaming snapshots and
    carries no timestamps, so tool durations come from the session entries' timestamps (`add_tool_durations`).
- **Claude Code's stream-json:** per-message `usage` is a snapshot taken before the output is written (output
  tokens ~1-5), so metrics come from the final `result` event; thinking text is empty in print mode; one
  assistant event per content block, all repeating the message's usage (merge by message id). Without
  `--tools=...` it offers ~25 tools (web, cron, push notifications, SendMessage...); keep the core-tools list.
  Variadic flags (`--tools`, `--disallowed-tools`) must use the `=` form and the brief goes after `--`, or
  the brief gets swallowed as a tool name.
- **Agy and Grok Build:** `agy models` lists effort-suffixed slugs; pass that slug as `--model` (not a separate
  `--effort` override). Grok's `models` lists ids but not effort menus: `GrokBuild.MODELS` mirrors the current
  catalog and must be updated as models change. Grok's `streaming-messages-json` reuses the Claude converter;
  Agy's `step_update` ACTIVE/DONE events need deduplication for tools. A response's text is many ACTIVE deltas plus a
  DONE event carrying the remainder (not a copy), so `convert_agy_stream` joins each response into one assistant message:
  one message per delta made every delta its own transcript turn (the log showed 160 "Assistant" turns for one answer). Neither CLI
  guarantees the same configuration isolation as Claude Code's `--safe-mode` (Grok's MCP meta-tools may remain).
  Agy has no cost field and Grok's server sometimes omits cost; 0 in a run can mean unreported, not free.
- **Muse Code (`muse exec`):** its `--json` stdout is a thin live stream (no tool calls, no usage), so `MuseCode.command`
  wraps `exec` in `bash -c` that runs `muse export --session ID --out harness/export.json` after the agent exits (ADR-0023).
  That export is the session (`session_file`); until the agent exits there is none, so live progress shows 0. `muse` has no
  list command: models and effort tiers come from the catalog it caches in `~/.local/share/muse/model-catalog/` (refreshed
  when the Muse TUI fetches it, e.g. opening `/model`; a new model is missing until then), with `MuseCode.MODELS` as the
  fallback when there's no cache. Tests point `CATALOG_DIR` at an empty dir (conftest) so they never read the real one. Tokens: Muse's
  `input_tokens` includes cached ones, so `input` = input - cache read/write. `MuseCode.finish` uses pinned Meta API rates for known models: `(input + cacheWrite) * uncached + cacheRead * cached + output * output`, divided by 1M; `metrics.cost_estimated` marks API-equivalent cost, not subscription spend. Wonder Full/Contributor use Wonder Standard as a marked proxy (`cost_estimate_proxy`); unknown models stay 0 (unreported). Re-import an old Muse run with its original `harness/export.json` to backfill its published cost without changing the archived run. Update `API_PRICES` when Meta changes rates. Only runs marked
  `top_level_turn.run_origin` count; the agent runs with `--disable-reminders` so no background agent adds usage. It
  runs with approval and sandbox off but the workspace untrusted (no `--yolo`: that also enables delegation); user-level
  Muse rules and skills may still load.
- **Codex (`codex exec --json`):** models/levels are live from `codex debug models` (`visibility: list` only;
  `ultra` is dropped, not in LEVEL_ORDER), cached per `Codex` instance because planning asks repeatedly. Only
  `item.completed` items count (`item.started`/`item.updated` repeat the item); the stream has no timestamps
  and no model id, so converted entries have neither. Effort goes via `-c model_reasoning_effort="LEVEL"`
  (there's no `--reasoning-effort` flag); cost is unreported (0). `codex model-profile show <anything>`
  echoes any name back, so it proves nothing about whether a model exists.
- **Ori (`ori code --output jsonl`):** OpenRouter's own CLI, run with `--harness ori` pinned, so a run is always Ori's
  runtime agent and not whatever harness the user's config defaults to. There's no `ori models` command: the model
  list is OpenRouter's public catalog, which `harness.fetch_json` fetches (the only network read in art-crit, cached per
  instance; tests monkeypatch it, `no_network` in conftest fails any other attempt). Levels come from each model's
  `supported_parameters`: `reasoning_effort` → the whole ladder, otherwise `off` only. The JSONL stream wraps every
  event twice (`{kind: "event", event: {type: "runtime.event", event: <agent event>}}`), so `ori_runtime_events`
  unwraps it; prose and reasoning arrive as deltas (joined) and the cost is OpenRouter's own. `ori mcp list` is the
  cheap way to check a run's `.ori/mcp.json` (each server needs `type: "stdio"`; the user's `~/.ori/mcp.json` and
  `./mcp.json` always merge in, and there is no per-server tool filter). Ori also mirrors its runtime log to stderr
  (harmless: the run's error comes from its own `result`/`tool.failed` message, which `run_agent` now prefers over
  the last stderr line). It records sessions in its own workspace (`~/.ori/global/.ori/...`), which art-crit never reads.
- **Model ids and levels of Claude Code aren't listed by any command:** the table lives in `ClaudeCode.MODELS`/
  `ALIASES` (harness.py), mirroring the CLI's own alias map; update it when models change. Levels are per model: the CLI
  silently clamps what a model doesn't take, and the recorded `thinking_level` is the *requested* one, so only list
  levels that really pass through. `*-4-6` drops `xhigh` (sends `high`); `claude-haiku-4-5` ignores `--effort` entirely.
  Check without paying for a call: point `ANTHROPIC_BASE_URL` at a local server that 400s and read
  `output_config.effort` out of the request body (the model catalog + the CLI's `xhigh_effort`/`max_effort` capability
  rules in its binary agree with this).
- **`-ne` still loads explicit `-e` extensions.** Per-run OpenRouter routing goes through the art-crit-shipped
  `pi_ext/openrouter_routing.ts` plus `ART_CRIT_OPENROUTER_ROUTING`/`ART_CRIT_ROUTE_LOG` env vars (never the global
  `models.json`, which would affect every pi session on the machine).
- **OpenRouter Gemini 400 "reasoning details to be preserved"** is misleading: pi (1.4.0) already resends
  `reasoning_details` verbatim. The real upstream error is "Corrupted thought signature": OpenRouter served a later
  request from another upstream (Vertex -> AI Studio after a 429). `pi_ext/openrouter_sticky_upstream.ts` fixes it.
  Pinning the set entry (`openrouter/google/gemini-4-argon@google-vertex`) avoids the question entirely; a response then
  names the upstream "Google", which `upstream_key` accepts as a prefix of `googlevertex`.
- **pi machine settings three OpenRouter models needed** (`~/.pi/agent/settings.json`, `~/.pi/agent/models.json`; both
  outside the repo, so a new machine needs them again): OpenRouter refuses a request whose *maximum* output can't be
  paid from the balance (`402 ... You requested up to 941808 tokens`), so models advertising ~1M output tokens (Gemini,
  Kimi, Muse) fail on a small balance unless `modelOverrides.<id>.maxTokens` caps them (64k here). Gemini can reason
  silently for more than pi's default `httpIdleTimeoutMs` (300000), which ends the run with "Network connection lost.";
  it is 1800000 here. Mistral Large 4 lists only `off, high` in pi's catalog although the API takes low/medium/high
  (a `thinkingLevelMap` override), and still answers `Provider finish_reason: error` at medium/high on real pages.
  The OpenRouter key is `providers.openrouter.apiKey = "!sed ... .env"` there rather than `OPENROUTER_API_KEY` in the
  environment: an agent that runs `env` would otherwise print the key into its transcript (the Mistral essay run did;
  the import's secret scan caught it and `--redact` masked it).
- **OpenRouter upstreams:** slugs contain `/` (`deepinfra/fp8`), so anything that takes "the model name after the
  last `/"` must split off `@route` first (`make_run_id`, `model_tag`, `modelParts()`). Responses name the upstream
  by display name ("AtlasCloud"), not slug: compare with `upstream_key()` (harness.py, where the whole route lives: `Pi.finish` reads `route.jsonl`). pi's cost for OpenRouter calls is a
  catalog estimate (2–7× too low on the first real routed runs); every OpenRouter run uses OpenRouter's `usage.cost` instead.
- **The run monitor skips old batch dirs** whose `runs` have no `id` (see `serve._batch_runs`): those predate run ids
  and have no run directories, so there is nothing to poll. Don't "fix" them by inventing ids.
- **`harness/stop` must stay a request, never a kill**: the monitor's server doesn't own the agent process, and a pid
  recorded anywhere could be reused. The runner polls for it once a second, so a timeout can overshoot by ≤1s.
- **Video scene (`scene/scene.js`):** a frame must be a pure function of its number: no CSS transitions/animations, timers or
  `Date`, or frames come out different on a slower machine. `pose()` sets `visibility` on each node it poses, and a
  `visibility: visible` child shows through a hidden parent, so a container must be posed too (only opacity hides children):
  The finale's headline was missing until its container was. Change a beat in `video.TIMING`, not as a literal in scene.js, so
  the sound cues stay on it. The cut sound (`video_sound.sound("cut")`) was a noise whoosh, which the owner found harsh, and a
  softer whoosh was still too much: keep sounds on cuts short, tonal and quieter than the kick. The renderer Chrome runs without the SwiftShader flags (about 5x faster per frame); the game
  recorder keeps them. Iterate on the look by rendering from cached clips and looking at frames (`ffmpeg -ss T -frames:v 1`).
  `pose()` also overwrites `filter`, so an element with its own CSS filter (the logo inverted on a light studio card) sits
  inside a posed wrapper. In studio.css, base rules for form controls use `:where()`: a plain `.st button` outranked the
  class colours and turned the white text on dark slots black.
- **Text runs (ADR-0036):** the title and excerpt in `run.json` are read from the *cleaned* `text/text.md` in `Text.stage`,
  never from work/: run.json itself isn't secret-scanned, so a value taken from the raw file could publish a home path.
  The viewer loads markdown.js (and Marked, 72 KB) with a dynamic `import()` only when a text is read in full, so cards
  and the home page never pay for it; a text has no thumbnail, so the lanes home shows a text tile for a page without a
  picture (`pickedText` in lanes/index.js), and `isPlayable()`/the ↗ pop-out leave texts out (nothing for play.html).
- **`replaceChildren()`/`append()` print `null` as text**; `el()` skips null children, so pass optional nodes
  through `el()` or `.filter(Boolean)`.
- **Tools recorded per run:** `Harness.tools(mcp)` (+ `BUILTIN_TOOLS` where the command names them) feeds `run.json.tools.allowed`;
  keep it in step with `command()` when a harness's `--tools`/MCP flags change. `null` builtin = unrestricted harness defaults
  (pi, agy, muse, codex). The sidebar's Tools section is `toolsSection()` in run.js.
- **Metrics from a pi session:** `tokens.total = input + output` (not `totalTokens`, which includes cache
  reads). Cost is the sum of `usage.cost.total` over assistant messages.
- **Run failure summary:** `runner.print_failure_summary` reads local run records after progress and publishing
  finish (also on resume/Ctrl-C). Keep agent, output, verification and publication errors distinct; skipped checks
  are not failures. `finish_output` saves all kind reports in `output/verification/verify-report.json`, including
  verifier exceptions (`ok: null`); this local diagnostic lets resume explain failures without changing run states.
- **Ctrl-C:** agents run with `start_new_session=True`, so Ctrl-C doesn't reach them. The runner kills
  their process groups itself. Keep the `live`/`interrupted` locking in `runner.execute` and `run_agent`.
- **Stale browser cache after a deploy** (Pages caches for 10 minutes) can pair new HTML with old JS and
  throw null errors. Hard refresh first. A cache-busting fix was drafted in a git stash, but the stash was lost
  when the repo was moved (2026-09-28); the options are in ADR-0012.
- **Compare groups by vendor:** `groupByVendor()`/`vendorName()`/`VENDOR_NAMES` (runs.js); `#columns` holds `.vendor-group` sections, each with its own `.compare-columns` grid, not cards. Stars stay computed over all shown runs.
- **A run card is exactly three grid rows** (heading, output, metrics; `.compare-col` is a 3-row subgrid so rows line up
  across a row of cards). A fourth child lands on top of the output and swallows its clicks; that is why the vote row lives
  inside `.compare-meta` with the metrics line (card.js).
- **Vote tests fake the API with `page.route("**/api/**")`** (`VoteApi` in test_web.py), which also catches the ranking
  probe `api/local`: anything it doesn't own must `route.fallback()`.
- **Vendor tint:** table rows and compare cards get `data-vendor` + `--vh` from `vendorOptions(model)` (runs.js); CSS turns
  that into a faint tint and stripe. Color only, so it survives any sort. New vendors get a hashed hue unless added to `VENDOR_HUES`.
- **Page width:** the runs table must fit without horizontal scroll at every width above 720px. page.html puts a
  collapsible details sidebar (meta, prompt, highlights; a drawer below 1024px) beside the runs, so the breakpoints are
  `@container runs` queries on the table's own width (`.page-main`), not the viewport: columns hide by priority
  (reasoning tokens, then harness + tool calls, then the thumbnail). Tests that need every column use a 1440px viewport. A new column
  needs a priority there and a re-run of `test_runs_table_never_scrolls_horizontally`. Measure with Playwright
  (`.table-wrap` clientWidth vs `table.scrollWidth`), never guess breakpoints. `.table-wrap { overflow-x: auto }` stays
  only as a safety net.
- **Covers are the owner's overrides** (`data/<slug>/covers.json`, SPEC.md Covers): `thumbs` (a run's main thumbnail), `page`
  (the home-page picture) and `covers`; with none set the viewer's default picks apply, so never turn an override into a
  requirement. They are set locally on the run page through `art-crit serve`'s `PUT api/cover` (like rankings, never on the
  published site) or by hand. A default cover should not show a character from behind: when a new run could become a page's
  cover (top effort level), look at its picture and add an override if needed. `coverOf()` (runs.js) is what the home page reads.
- **Provider icons** on the home cards are OpenRouter's, vendored in `docs/assets/vendor/icons/` (`VENDOR_ICONS` in runs.js,
  keyed by `vendorOf()`, which gives `z` for `z-ai` and `x` for `x-ai`). A new vendor shows its initial until one is added.
- **Runs table markup is load-bearing for the phone layout:** at ≤720px CSS turns rows into cards using each cell's
  `data-col`/`data-label`. A new column needs those attributes and a placement in the `@media (max-width: 720px)` block.
  The effort cell's text must stay exactly the level name (the meter is a CSS `::before`); tests read it.
- **Screenshots of every page type** (desktop/phone, light/dark) are a quick visual check after UI changes: Python
  Playwright with `channel="chrome"` and `color_scheme="dark"` on the context, against `art-crit serve`.
- **Thumbnails are made at import, 800 px JPEGs** (`media.write_thumb`; ADR-0029): `run.thumb` and each media item's `thumb`.
  Cards, tables and overlays show those; only the run page shows the file itself. JPEG has no alpha, so transparency is
  composited over white in `thumbnail()`. `rebuild` backfills missing ones (and turns an old full-size `thumb.png` into
  `thumb.jpg`), so expect it to touch `run.json` files the first time after a change like this; it never remakes existing ones.
  A test fixture whose `frame-1.png` isn't a real PNG gets `thumb.png` (the ffmpeg-less fallback), which is why the
  synthetic godot batch still expects it.
- **Each HTML head preloads its script's import closure** (`<link rel="modulepreload">`, ADR-0029). Adding an `import`
  to a viewer module fails `test_html_preloads_exactly_the_modules_its_script_imports`, which names the missing module;
  never preload `vendor/three-gltf.min.js` (640 KB, loaded on a click).
- **Cache headers live in `docs/_headers`** (Pages honours it for `Cache-Control`; it was only `Content-Encoding` it couldn't
  force). Don't give `assets/*.js` or `style.css` a long `max-age` until cache-busting exists (ADR-0012): it would pair
  new HTML with old scripts for everyone, not just the 10-minute Pages cache window.
- **Viewer data JSON is fetched with `cache: "no-cache"`** (`getJSON()`); without it the browser's heuristic cache
  showed stale results after saving a ranking (and after a publish).
- **Tests address table cells by `data-col`**, not position: adding a column (like Rank) shifted `nth()` indexes.
- **Web kind packaging:** a classic `<script src>` is inlined as a `data:` URL, not bundled: esbuild's IIFE output turns
  its top-level `var`s (globals other scripts use) into locals. Only module scripts are bundled.
- **Local server backlog:** the stdlib HTTP server's default accept queue is only 5. Chrome fetches many
  ES modules in parallel; overflow resets a module request (`net::ERR_CONNECTION_RESET`) and leaves the page
  on Loading… with no JS error. `serve._Server.request_queue_size` is 64; keep it above the module fanout. The `site`
  fixture in test_web.py needs the same (it was the source of flaky 30s "waiting for selector" timeouts), and its
  handler must silence `log_message` like `serve._Handler`: that server runs in a background thread, so its access
  logs escape pytest's capture and scramble the progress output on the shell.
  Published `docs/data/` is not a fixed test fixture; avoid tests asserting its run count or requiring
  live published games to remain unchanged.
- **Sync Playwright can't nest:** `test_web.py` keeps a session-wide browser open, so other tests that start Playwright
  (verify) run it in a worker thread (`in_thread()` in `test_web_kind.py`).
- **ffmpeg here has no WebP encoder** (it can decode WebP), so oversized images are re-encoded as JPEG.
- **`uv run` puts `.venv/bin` first on PATH**, so agents (and the brief's tool list) see the venv's python3,
  not Homebrew's. The user also has `art-crit` installed as an editable uv tool (`uv tool install --editable '.[verify]'`),
  which doesn't do that: a batch started with plain `art-crit run` sees the system python3. Agents working in this repo
  should keep using `uv run art-crit`.
- **Safari needs HTTP Range requests to play mp4.** Cloudflare Pages returned 200 (not 206) for a live MP4 Range
  request. The subpath Worker synthesizes 206 for our ≤2 MiB normalized videos; `art-crit serve` (Python's
  http.server) still doesn't support ranges, so preview videos in Chrome.
- **Pages answers a missing file with `index.html` and 200 unless `docs/404.html` exists.** Keep that file: without it the
  viewer and the votes API parse HTML as JSON (the API answered 500 for an unknown slug). It is plain (no assets) because
  it is served at any depth. HSTS and the API rate limit are zone settings, not code: check them with
  `cf zones settings get security_header -z fenderog.com` and `cf rulesets list -z fenderog.com`.
- **Cloudflare Pages limits files to 25 MiB:** `cloudflare/prepare.py` stages all Godot engines as deterministic
  `.wasm.gz`; `cloudflare/router.mjs` streams them decompressed at `.wasm` URLs. Pages `_headers` cannot be relied on
  to force `Content-Encoding: gzip` (confirmed by a live probe). The `cf` CLI manages Pages projects but `cf pages deploy`
  rejects legacy Pages uploads; use Git integration for Pages and Wrangler only for the Worker. The Cloudflare GitHub
  app must be authorized for this repo before creating a Git-linked Pages project. `.python-version` makes the first
  Cloudflare build compile Python 3.12 (can take a few minutes). (ADR-0021)
- **Blender kind:**
  - `--safe-mode` silently drops `--mcp-config` in Claude Code (its help says otherwise), so MCP runs use
    `--setting-sources=` + `--strict-mcp-config` + `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1` instead. Check what a model gets
    without paying: point `ANTHROPIC_BASE_URL` at a local server that 400s and read `tools`/`system` from the request.
  - pi's built-in MCP (pi 1.2.0) has no per-run config flag (a `--mcp-config` only appears when an extension such as
    `pi-mcp-adapter` adds one), and `-ne` leaves it out, hence `-e builtin:mcp` + `work/.pi/mcp.json` + `--approve`. MCP
    tools use `direct` exposure, not codemode, so pi's tool calls compare 1:1 with Claude Code's and Codex's. To see what a
    pi model gets, use a throwaway `PI_CODING_AGENT_DIR` with a fake provider; it needs `--offline` or it hangs on first-run setup.
  - With the 7 window-only tools hidden, pi and Claude Code both declare the same 19 `mcp__blender__*` tools (checked
    2026-10-15); pi also adds its 3 generic MCP resource tools.
  - The add-on needs `blender --online-mode` (it asks for network access to serve its socket); without it,
    `--command blender_mcp` exits with "Online access must be enabled".
  - `uvx blender-mcp` is the *third-party* ahujasid server on PyPI; the official one runs from
    `git+https://projects.blender.org/lab/blender_mcp.git@<commit>#subdirectory=mcp`. projects.blender.org's web pages
    answer bots with a Cloudflare challenge; git, the API (`/api/v1/repos/...`) and release downloads work.
  - In background mode the screenshot and `jump_to_*` tools answer "not available" (hidden); the render tools work.
  - `FAKE_PI_BLENDER_LIVE=1` with the fake pi on PATH runs the real Blender + MCP server through a whole `art-crit run`
    (point `--root` at a throwaway site copy): the cheapest full check after changing this kind.
  - The viewer's three.js bundle is one esbuild-minified module; rebuild it with the command in its header comment.
  - agy and muse MCP (measured 2026-10-15): agy passes its env to MCP servers but muse doesn't (fixed allowlist), hence
    the spec file beside work/. agy declares a tool up front only when `tools` names it with `eager: true` ("*" doesn't
    work); otherwise the model is told to view_file a schema under `~/.gemini/antigravity-cli/mcp/`. Muse ignores a project
    `.muse/settings.json` even with `--trust-workspace`, and that flag adds `subagent_*` tools: never use it.
  - Grok: project `.grok/config.toml` servers start only in a trusted folder (`grok mcp doctor` says "folder untrusted");
    `GROK_FOLDER_TRUST=0` ungates it per process. `disabled_tools` is an unknown field there (`grok inspect` warns).
    Grok also reads `~/.claude.json` and `.mcp.json` servers (compat sources), so the user's Claude MCP servers would
    reach grok runs. Pointing Grok's base URLs at a local sink breaks its model lookup; check with `grok mcp doctor`.
  - Agents `read` their renders to check them, and pi keeps each read image as base64 in the session (a real DeepSeek run:
    10 reads, a 15 MB conversation.json). The importer shrinks transcript images over 48 KB to 800 px JPEGs
    (`importer.shrink_images`); never publish them raw (Pages limits files to 25 MiB).

## Open ideas (not built)

- More harnesses: implement `Harness` in harness.py (convert its session to pi's format like
  `convert_claude_stream`), add it to `HARNESSES`, and a fake binary in tests/fixtures/fake_pi/.
- Running agents in a VM with the user's own image. Swap out the "start one agent" step in
  `runner.run_agent`.
- Native image/video models (gpt-image, Imagen, Veo, Sora...): not an agent loop, so they'd need a
  different kind of harness (one API call per run, e.g. via OpenRouter) that writes straight into
  `./output/`; the media step, import and viewer would then work unchanged.
- Asset cache-busting (ADR-0012).
- `art-crit publish` opening a pull request instead of pushing (for people without write access, or `--pr` for
  the owner), with a GitHub Action checking PRs only touch `docs/data/` + `docs/engines/`. Discussed and
  deliberately not built for now.
- Community votes are built (ADR-0022). Not built: sorting by votes, a Votes column in the runs table (the table shows
  the controls in each row's expanded detail), a rate limit inside the Worker (the recommended Cloudflare rule is in the README), an `art-crit` command to export votes into a backup.
- Arena-style A/B voting (blind head-to-head): a different mechanism from hearts and medals; would reuse the same
  Worker + D1.

## Working with this user

- They iterate on the UI by describing changes against the live site. Deploy, verify on the live site
  (Playwright against https://fenderog.com/art-crit/), then report.
- They like a short plan before bigger features, and want work to stay simple, lean and well tested.
- Scratch files go in `tmp/`, which is gitignored.
