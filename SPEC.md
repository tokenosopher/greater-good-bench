# art-crit spec

This repo is both the CLI (`src/art_crit/`) and the static site (`docs/`, published on Cloudflare Pages
at `https://fenderog.com/art-crit/`). The CLI writes JSON and files into `docs/data/` and `docs/engines/`,
and the viewer pages fetch that JSON in the browser. Cloudflare's build copies `docs/` to
`cloudflare-dist/` and compresses Godot WASM files to fit Pages' 25 MiB asset limit; the viewer itself
has no build step. See Deployment below.

Guiding rule: **simple and lean.** The CLI is standard-library Python only (argparse, json, hashlib,
tomllib, http.server, subprocess). The site is vanilla JS ES modules, with one pinned, vendored dependency
(`marked` for Markdown tokenization). No frameworks and no bundler.

## Vocabulary

- **Page**: one prompt or task, such as `voxel-horse`.
- **Run**: one model × effort level attempt at a page's task, kept in one directory (`<batch>/<run id>/`, see
  "Run directory"). `art-crit import` publishes it to the site.
- **Kind**: what a page's runs produce. `godot` = a Godot project, published as a playable web build;
  `media` (shown as "Vector" in the UI) = image and/or video files; `web` = a web page (HTML + ES modules + npm packages), published as one
  self-contained `index.html` packaged with esbuild; `blender` = a `.glb` model and/or renders made in a Blender of
  the run's own through the official Blender MCP server, the model shown in an interactive 3D viewer; `text` = one
  Markdown file, rendered by the viewer as a readable page. Every run of a page has the page's kind.

## Site layout (the data contract between the CLI and the viewer)

```
docs/
  .nojekyll                     # still used by the old GitHub Pages URL
  index.html                      # home: list of pages            (reads data/pages.json)
  page.html?p=<slug>              # one page: runs table + gallery (reads data/<slug>/page.json)
  run.html?p=<slug>&r=<run_id>    # one run: tabs Game | Transcript | Source | Metrics
  compare.html?p=<slug>[&r=<id>,<id>]   # side by side: all runs of the page, or just the listed ones
  play.html?p=<slug>&r=<run_id>   # one run's output alone, full window (the compare cards' pop-out target)
  assets/                         # shared JS/CSS
  engines/<sha12>/godot.wasm      # deduplicated Godot engine files, one dir per unique engine
  engines/<sha12>/godot.js
  engines/<sha12>/godot.audio.worklet.js
  engines/<sha12>/godot.audio.position.worklet.js
  data/
    pages.json                    # [PageSummary]
    <slug>/page.json              # Page
    <slug>/references/<file>      # optional: the page's --ref files, shown as thumbnails on page.html (ADR-0026)
    <slug>/ranking.json           # optional: {"ranks": {"<run id>": 1, ...}, "updated": "<iso>"}, the owner's ranking (see Ranking)
    <slug>/covers.json            # optional, the owner's cover overrides: thumbs, page, covers (see Covers)
    <slug>/runs/<run_id>/
      run.json                    # Run
      thumb.jpg                   # optional (godot, web): the verify screenshot at most 800 px wide (ADR-0029;
                                  # thumb.png, the screenshot itself, when ffmpeg couldn't make it)
      game/index.html, index.pck, index.png, index.icon.png, index.apple-touch-icon.png   # godot
      media/<file>, media/<name>.poster.jpg, media/<name>.thumb.jpg                       # media, blender (+ media/<name>.glb)
      game/index.html             # web: the packaged page, one file (cleaned and secret-scanned like source)
      text/text.md                # text: the Markdown, as the agent wrote it (cleaned and secret-scanned like source)
      session/conversation.json   # cleaned (see Cleaning)
      session/stderr.txt          # optional, cleaned
      source/...                  # project files the model wrote
```

All paths inside JSON are **relative to the run directory** (for Run) or to `docs/` (for PageSummary.thumb).

### PageSummary (element of `data/pages.json`)
```json
{ "slug": "voxel-horse", "title": "Voxel horse", "kind": "godot", "n_runs": 3,
  "models": ["openai-codex/gpt-6-sol"], "updated": "2026-09-26T07:15:57Z",
  "thumb": "data/voxel-horse/runs/gpt-6-sol-high-20260926-001158/thumb.jpg" }
```
`thumb` is taken from the most recent run that has a cover picture (`cover`, else `thumb`; see Covers), or `null`.

### Page (`data/<slug>/page.json`)
```json
{ "slug": "voxel-horse", "title": "Voxel horse", "kind": "godot",
  "prompt": "<contents of prompt.md, the originating prompt; refreshed on every import>",
  "final_prompt": "<the full brief each run received: first user message of the cleaned transcript; null if none>",
  "references": ["robie.jpg"],   // --ref files in data/<slug>/references/, listed by name; key absent when none
  "created": "2026-09-26T07:12:42Z", "updated": "2026-09-26T07:15:57Z",
  "runs": ["<Run with rank; see below>"] }
```
`references` is derived from the `references/` directory by `rebuild` (an import replaces the whole set), and the
viewer shows image files as thumbnails in page.html's details sidebar (`<img>` only, click to expand; ADR-0026).
They are also an *input* to later batches: a `--page` run whose prompt says "use the reference image" stages the
page's published copies, so adding runs can't silently leave the model with no image (ADR-0028).

### Run (`run.json`, and each element of `page.json.runs`)
```json
{
  "id": "gpt-6-sol-high-20260926-001158",
  "page": "voxel-horse",
  "model": "openai-codex/gpt-6-sol",
  "effort": "high",
  "kind": "godot",
  "started_at": "2026-09-26T07:12:42Z",
  "batch": "2026-09-26-001158-voxel-horse",
  "harness": { "name": "pi", "version": "0.87.1" },
  "state": "complete",
  "error": null,
  "route": null,
  "tools": { "allowed": { "builtin": null, "mcp": {} }, "used": { "bash": 9, "write": 6, "read": 1 } },
  "metrics": {
    "duration_ms": 196192, "cost_usd": 0.146, "tool_calls": 16, "turns": 17,
    "tokens_total": 32732, "tokens_input": 25280, "tokens_output": 7452,
    "tokens_reasoning": 3073, "tokens_cache_read": 105984
  },
  "thumb": "thumb.jpg",
  "output": { "kind": "godot", "entry": "game/index.html", "engine": "41560f8755ed",
             "godot": "4.7.2.stable.official.ed1daf0bf", "threads": false,
             "ok": true, "verified": true, "error": null },
  "session": { "conversation": "session/conversation.json", "stderr": "session/stderr.txt" },
  "source": { "root": "source/", "files": ["README.md", "project.godot", "scenes/main.tscn", "scripts/main.gd"] }
}
```
- `output`, `session`, `source` and `thumb` can each be `null`.
- `rank` exists only in `page.json.runs` (never in `run.json`): the run's rank from `ranking.json`, or `null`.
- `cover` exists only in `page.json.runs`, and only for a run named in `covers.json`'s `covers` (see Covers); `page.json.cover` ({run, image}) is the owner's pick of the page's home-page picture. A run's `thumb` there can be overridden by `covers.json` too, and then the run has `thumb_override: true`.
- `kind` is the page's kind (runs imported before kinds existed have none; the viewer treats that as `godot`). Importing
  into a page of another kind is an error. `batch` = the batch directory's name (runs published before run
  directories hold the old model directory's name).
- **`state`, `output.ok`, `output.verified`: three questions, three places.** `state` is only what the agent did:
  `queued | running | complete | failed | timeout`; `error` is the agent's error (harness exit, timeout, an assistant
  `stopReason: error`, or a note that a pinned OpenRouter run was served outside its upstreams). `output.ok` /
  `output.error` are what the kind step made of the work (Godot export, packaging, media normalization): a run
  whose export failed is `state: complete` with `output: {kind, ok: false, error: "Godot export failed: …",
  verified: null}`. `output.verified` is whether the check passed (booted, loaded offline, files readable), `null`
  when it wasn't run. `output` is `null` only when the agent didn't complete (there was nothing to export).
- `output` carries its own `kind` and the kind's fields (see Kinds): `godot` = `entry`, `engine`, `godot`, `threads`;
  `web` = `entry`, `bytes`, `esbuild`; `media` = `items`, each `{type: "image"|"video", path: "media/<file>", width,
  height, bytes}` plus, for a video, `duration_s, poster: "media/<name>.poster.jpg", transcoded` and `trimmed: true`
  when it was cut to 10 s (width/height can be `null` for an SVG without a size), and `thumb: "media/<stem>.thumb.jpg"`
  for a raster image or a video (a JPEG at most 800 px wide made at import from the image or the poster, ADR-0029; an
  SVG has none); `blender` = `items` like media, plus
  `{type: "model", path: "media/<name>.glb", bytes, meshes, triangles, animations}` for a model; `text` = `text:
  "text/text.md"`, `bytes`, `words` (whitespace-separated), `title` (the first `# ` heading as plain text, or `null`) and
  `excerpt` (the first ~300 characters as plain text, the title left out, cut at a word with "…"), both read from the
  cleaned file. So `output` has three shapes: `entry` (a game or page), `items` (a gallery) and `text`. Paths are relative to the run
  directory. `thumb` = `thumb.jpg` (the verify step's first screenshot, at most 800 px wide; `thumb.png`, the screenshot
  itself, when ffmpeg couldn't make it) for godot and web; for media and blender the first item's `thumb`, or the first
  image's path or video's poster when no item has one; `null` for text (cards show the title and excerpt instead). `art-crit rebuild` backfills missing thumbnails of published
  runs from their files and rewrites those `run.json`. Model-written text (SVGs, the packaged page) is cleaned and secret-scanned like
  source. The run's `source` never includes `node_modules/`; for media it holds only text files of at most 512 KB,
  and `output/` only for the files there that aren't media (a generator script kept in `./output/`).
- `id` = `<model name after the last "/", lowercased>-<effort>-<YYYYMMDD-HHMMSS of the batch>`, with `-cc` after the
  model for Claude Code runs; URL/filesystem-safe: a pinned OpenRouter route (`@…`, which can contain `/` itself) is split
  off first and appended as `-via-<route>`, e.g. `…flash@deepinfra/fp8` → `deepseek-v4.1-flash-via-deepinfra-fp8-low-20261001-101500`;
  anything else outside `[a-z0-9.-]` becomes `-`. It is also the run directory's name; two runs of a batch with one id
  are refused before anything starts.
- `harness` = the agent program and its version; `metrics` as in "Metrics". `metrics.cost_estimated: true` is present for Muse Code API-equivalent estimates (not subscription charges); `metrics.cost_estimate_proxy: "meta/muse-wonder-1.0"` also appears when Wonder Standard's API rate is used as a proxy for an unpriced Wonder variant.
- `tools` = `{"allowed": {"builtin": [...] | null, "mcp": {<server>: {"allowed": [...], "hidden": [...]}}}, "used": {<tool>: calls}}`:
  `allowed.builtin` is the list art-crit passes the harness (`null` = the harness's own defaults, not restricted by name),
  `mcp` the run's MCP servers (kind-supplied, per run) with the tools offered and the ones hidden; `used` counts the calls in the
  transcript by name (MCP tools as `mcp__<server>__<tool>`), most-called first. Runs published before this field have no `tools`.
  The run page's sidebar shows it as a "Tools" section (allowed tools as chips, bold count = calls, hidden ones struck through).
- `route` = what the harness reports about routing, for a pi `openrouter/` run, else `null`:
  `{"requested": {"only": [...], "allow_fallbacks": false}, "served": [...], "cost_usd": 0.00085, "pi_cost_usd": 0.00038}`.
  `requested` is `null` for an unpinned run (OpenRouter chose the upstream); the rest is recorded either way.
  `served` = the upstreams that served the run, in order, as OpenRouter names them ("DeepInfra", "AtlasCloud").
  They're matched to the requested slugs by `upstream_key()` (lowercase alphanumerics of the name, and of the slug
  before its `/variant`: `atlas-cloud/fp8` and "AtlasCloud" → `atlascloud`); one outside `requested.only` is appended
  to `error`. `cost_usd` = what OpenRouter charged (the sum of each response's `usage.cost`), `null` when no response
  reported one; `pi_cost_usd` = pi's own estimate. For an OpenRouter run `metrics.cost_usd` is `cost_usd` when present:
  pi prices every OpenRouter call at one catalog rate whatever upstream served it (≈ 2–7× too low on real runs).

## Run directory (what `art-crit run` writes and `art-crit import` publishes)

```
<run.dir>/<YYYY-MM-DD-HHMMSS>-<page slug>/      # a batch
  batch.json  prompt.md                         # the batch's record (see Resume) and the originating prompt
  <run id>/                                     # one run
    run.json                                    # the run's record: the Run above, minus rank, thumb, session and source;
                                                #   output = {kind, ok, error, verified} (null until the kind step ran)
    work/                                       # the agent's working dir, empty at start; nothing else is ever written here
    harness/                                    # session file(s), stdout (events.jsonl), stderr.txt, brief.md, route.jsonl,
                                                #   conversation.json (the session in pi's format), stop (a local monitor
                                                #   stop request, ADR-0027): never published except the transcript and a
                                                #   non-empty stderr
    output/                                     # what the kind made: Godot export (+ verification/), the packaged page
                                                #   (+ verification/), or normalized media + manifest.json
```
`art-crit import` takes one run directory or a batch directory and publishes each run: cleans and secret-scans, copies
`run.json` (adding `thumb`, `output`'s kind fields, `session` and `source`), `harness/conversation.json` as
`session/conversation.json`, `work/` as `source/` and the kind's `output/`, then rebuilds. It returns the paths it wrote
(`data/<slug>/`, its run directories, `data/pages.json`, any new `engines/<sha12>/`), which is what `art-crit run`
hands to `cmd_publish`: a run's commit holds that run's files, not whatever else the working copy has staged or edited. The page slug is the run's
`page` (`--page` overrides it); the title = the slug with dashes turned into spaces and the first letter capitalized.
The page's prompt is the batch directory's `prompt.md`. Effort-run folders (`fe-model-effort-fanout/1`) are no longer read.

## Godot engine dedupe (proven in `../spike/build.py`)

1. The engine files are `index.wasm`, `index.js`, `index.audio.worklet.js`, `index.audio.position.worklet.js`.
   sha12 = the first 12 hex characters of sha256 over the four files' bytes, concatenated in that order.
2. If `docs/engines/<sha12>/` doesn't exist, copy them there as `godot.wasm`, `godot.js`, `godot.audio.worklet.js`, `godot.audio.position.worklet.js`.
3. Copy the other export files (except `export-manifest.json`, `verification/`, and the engine files) from `output/` into `runs/<id>/game/`.
4. Rewrite `game/index.html`. `rel` = the relative path from the game dir to `docs/engines/<sha12>/godot`:
   - `<script src="index.js"></script>` → `<script src="{rel}.js"></script>`
   - in `const GODOT_CONFIG = {...};`: `executable` = rel, **`mainPack` = "index.pck"** (required), and rename the
     `fileSizes` key `index.wasm` → `{rel}.wasm`.
5. Refuse an export with `threads: true` (from export-manifest.json, or `const GODOT_THREADS_ENABLED = true` in the html)
   with a clear error, unless `--allow-threads` is given. With the flag, store `"threads": true`.
6. `verification/frame-1.png` → `runs/<id>/thumb.jpg` (`media.write_thumb`, at most 800 px wide; copied as `thumb.png` when ffmpeg can't).

## Cleaning (always runs on text files before they are written to docs/)

1. Remove every `thinkingSignature` key and every `encrypted_content` key, at any depth (a `thinkingSignature`
   value may be a JSON string that contains `encrypted_content`; dropping the whole key is enough).
2. Rewrite path prefixes in all strings: the user's home dir → `~`, plus extra rewrites from `art-crit.toml`:
   ```toml
   [clean]
   rewrite = { "/Volumes/M2SSD" = "<vol>" }
   ```
3. Drop these keys at any depth: `pid`, `completionOwnerId`, `sessionId`, `sessionFile`, `sessionRoot`, `launchContractDigest`.
4. Secret scan over the cleaned text of every published file (the transcript, stderr, source files, SVGs and the packaged page).
   Patterns: `sk-[A-Za-z0-9_-]{20,}`, `ghp_[A-Za-z0-9]{30,}`, `github_pat_[A-Za-z0-9_]{30,}`, `gho_[A-Za-z0-9]{30,}`,
   `AKIA[0-9A-Z]{16}`, `xox[baprs]-[A-Za-z0-9-]{10,}`, `-----BEGIN [A-Z ]*PRIVATE KEY-----`,
   `(?i)(api[_-]?key|secret|token|password)["'\s:=]+[A-Za-z0-9_\-/+]{24,}`.
   Any hit aborts the import **before anything is written**. The error prints file:line and the match masked
   (first 4 characters + `…`). With `--redact`, each match is replaced with `[REDACTED]` and the import continues.
5. Image data (the base64 `data` of `{type: "image"}` blocks in session JSON) is set aside before steps 2 and 4 and
   put back after: it's binary, so rewrites could corrupt it and the scan finds random matches (`AKIA…`) in it.
   Data that isn't plain base64 stays in place and is scanned. Before cleaning, every image in `conversation.json` over
   48 KB (decoded) without a `sourceMimeType` becomes an ≤ 800 px JPEG (`media.thumbnail`), recorded as `{mimeType:
   "image/jpeg", sourceMimeType: <original type>, bytes: <original size>}` (no `data` without ffmpeg), so an agent
   reading its renders doesn't publish each one in full (pi keeps the whole file as base64; a 10-read run was 15 MB).
   The run directory keeps the originals.
6. JSONL files are cleaned line by line. Source files, stderr, SVGs and the packaged page get steps 2 and 4 only.

## CLI (`art-crit`, run from the repo root, or pass `-C/--root`)

```
art-crit import <run-dir | batch-dir> [-p/--page/--slug SLUG] [-t/--title TEXT] [-r/--redact] [-a/--allow-threads] [-n/--dry-run]
art-crit list                      # pages and their runs
art-crit rm <slug> [<run_id>] [-f/--failed] [-y/--yes]   # remove a run (or a whole page); --failed removes every failed run instead, then rebuild
art-crit rename <slug> <new> [-t/--title TEXT]   # move a page to a new slug (rewrites each run.json `page`), then rebuild
art-crit retry <slug> [<run_id>...] [-y/--yes] [-n/--dry-run] [-j N] [-T/--timeout D] [--no-publish]   # run failed runs again (see Retry)
art-crit video <slug> <run_id>... [-l/--layout reveal|grid|wide]... [-d/--seconds N] [--no-sound] [-o/--out DIR]   # social-media videos of 2-12 runs (see Social videos)
art-crit rebuild                   # regenerate page.json + pages.json from runs/*/run.json; delete engines no run references
art-crit serve [-p/--port 8000]    # serve docs/ locally: Access-Control-Allow-Origin: *, .wasm as application/wasm, NO COOP/COEP headers
                                #   plus the local-only ranking, prompt-request, run-monitor and video-studio APIs (see
                                #   Ranking, Prompt requests, Run monitor, Video studio); accept queue 64 for concurrent ES modules
art-crit publish [-m MSG]          # git add + git commit -- docs (only those paths) && git push (Cloudflare Pages builds main)
art-crit run ...                   # run agents locally, then import (see "Running benchmarks")
art-crit models [SEARCH] [-H/--harness pi|claude-code|agy|grok-build|muse-code|codex|ori]   # models the harness can run; with SEARCH also their effort levels
```
Every long option has a single-dash short form (shown as `-p/--page`); the short forms are listed with each command.
- `import` is idempotent. Re-importing the same directory replaces runs with the same id.
- `import` prints a short summary per run: id, engine stored or reused, bytes written, paths rewritten, secret hits.
- `--failed` removes runs where the agent didn't finish (`state`), the kind step failed (`output.ok`) or the check failed (`output.verified`); it lists them with the reason and asks first unless `-y/--yes`.
- `--dry-run` does all the work, including the secret scan, in a temp dir and writes nothing to docs/.
- Errors go to stderr with a non-zero exit code, and there are no tracebacks for expected errors.

## Running benchmarks (`art-crit run`)

Runs one prompt through one or more models × effort levels on this machine with a **harness** (the agent program;
pi or Claude Code), turns each run's work into its kind's output and verifies it, then imports everything into one page.

```
art-crit run PROMPT | -f/--prompt-file FILE
    -k, --kind godot|media|web|blender what the agents produce (default: the existing page's kind, else godot); must match it
    -m, --model MODEL[@UPSTREAMS][:LEVELS]  repeatable. UPSTREAMS: comma-separated OpenRouter provider slugs, as
                        OpenRouter lists a model's endpoints, variants included (`deepinfra/fp8`, `fireworks/us`)
                        (pi `openrouter/` models only, e.g. `openrouter/deepseek/deepseek-v4.1-flash@deepinfra/fp8:low`);
                        pinned with fallbacks off, recorded as part of the model name. LEVELS: "low,high" | "low..max" (range in LEVEL_ORDER, keeping only supported levels)
                        | "all" (every supported level except off) | explicit "off". No suffix = "all".
    -s, --set SET       repeatable: a model set, either a NAME from art-crit.toml [sets] or a FILE with one
                        MODEL[@UPSTREAMS][:LEVELS] per line (# comments, blank lines ignored). Its entries are added before
                        the -m specs, exactly as if given with -m. An unknown name that isn't a file is an error
                        listing the defined sets.
    -e, --effort LEVELS default LEVELS for every model without a suffix (-m or set entry)
    -i, --pick          pick harnesses, models (by number or a fuzzy search) and levels interactively (implied when no -m/--set is given; needs a tty)
    -p, --page, --slug SLUG
                        add to this page (default: slug of --title if given, else of the prompt's first 6 words; max 40
                        chars). For an existing page, PROMPT can be left out: its prompt (page.json) and kind are reused,
                        and so are its published references (data/<slug>/references/), unless this batch passes its own
                        --ref (ADR-0028).
    -c, --change-prompt allow a PROMPT that differs from the existing page's (after path cleaning); without it that's
                        an error, since every import replaces the page's prompt for all its runs
    -t, --title TEXT    page title (default: from slug, as for import). Without --page/--slug it also names the slug
    -b, --brief FILE    use this brief template instead of the built-in one ({prompt} is substituted)
    -R, --ref FILE      a reference file, a path under <root>/references/ (repeatable); must exist. It is copied into the batch
                        and every run's work/references/, and the brief (not the page's prompt) lists ./references/<name>.
                        Import publishes the batch's copies to data/<slug>/references/ for the viewer (ADR-0026).
                        The copies are never published as source. `--page` on a page that has published references
                        adopts them as this batch's refs (--ref replaces that set; ADR-0028), and the plan prints them
    -j N                max agents at once (default [run].parallel or 8)
    -T, --timeout DUR   per agent, "30m" / "90s" / "1h" (default [run].timeout or 30m)
    -y, --yes           don't ask for confirmation
    -n, --dry-run       print the plan and exit
    -P, --publish       import and `art-crit publish` each run as it finishes (the default)
    --no-publish        only import at the end; push later with `art-crit publish`
art-crit run -r/--resume DIR  finish an interrupted batch (see Resume)
```
`LEVEL_ORDER = off, minimal, low, medium, high, xhigh, max`. Every requested level is checked against the harness's
list for that model **before anything starts**; an unknown model or unsupported level is an error that names the
supported levels (pi silently clamps unsupported levels, so this check is what keeps labels honest).

With no `-m`/`--set` (or with `-i/--pick`, which adds to the specs already given), and only on a tty, `art-crit run`
asks interactively (`src/art_crit/picker.py`): a numbered **harness menu** (empty = pi, the default), then that
harness's models, then a levels prompt per picked model (default `all`, accepting the same LEVELS syntax). In the
model list, numbers, ranges or `all` select from the listing shown; any other text is an **fzf-style fuzzy search**
(letters and digits in order, separators ignored, so `claudeop55` and `g6sol` match; hits that start a word and runs
of consecutive hits rank higher) that re-lists just its matches, renumbered, and an empty answer brings the full list
back (or picks nothing while it is shown). A catalog of more than 20 models is not listed before the first answer:
the prompt asks for a search, every listing shows at most 20 matches (with the number of further matches named),
and `list` lists the whole catalog on purpose; clearing a search on such a catalog returns to that search prompt
rather than printing it. The picks become ordinary harness-prefixed `-m` specs, so planning
validates them exactly like a hand-typed spec. A harness whose model list can't be read, and a model whose levels
can't be, are reported and skipped; a selection and a levels spec are re-asked until they parse. On a non-tty (e.g. a
script), no `-m`/`--set` is the usual error.

`art-crit.toml`:
```toml
[run]
dir = "~/dev/art-crit-runs"   # where batch directories go (never inside ~/dev/effort-runs)
parallel = 8
timeout = "30m"
tools = ["python3 (standard library only)", "node (no npm packages)", "ffmpeg", "ffprobe"]   # listed in the brief

[sets]   # each a list of "MODEL[@UPSTREAMS][:LEVELS]" strings (anything else is an error)
cheap = ["openai-codex/gpt-6-luna:minimal,low", "openrouter/deepseek/deepseek-v4.1-flash:low..high"]
```

`art-crit.toml` is parsed in one place: `art_crit.config.Config.load(root)` in `cli.main` exposes `.rewrites` (`[clean]`),
`.run` (dir, parallel, timeout, tools) and `.sets`, and is passed to the importer and runner. One run's inputs
are a `art_crit.config.RunRequest` (prompt, kind, page, title, model specs/sets, effort, brief, parallel, timeout,
publish, change_prompt); it round-trips through JSON and is stored in `batch.json`, so a `--resume` (or, later, a
website-started run) replays the same fields. It is validated when built (kind, parallel >= 1, a parseable timeout),
so bad input fails before a batch dir exists; `from_dict` ignores unknown keys. A malformed `art-crit.toml` is a
plain error for every command.

### Flow
1. **Plan**: resolve models + levels (asking on a tty when none were given, see `-i/--pick`), print the harness (name + version), page (new/existing), prompt, the numbered
   model × effort list and the batch dir. Ask `Start? [y/N]` (stdin not a tty and no `--yes` → error). `--dry-run` stops after printing.
2. **Batch dir**: `<run.dir>/<YYYY-MM-DD-HHMMSS>-<page slug>/` with `batch.json`, `prompt.md` and one run directory per
   model × effort (see "Run directory"). Run ids are assigned here from the batch's start time; each run's `state` in
   `batch.json` starts `queued`.
3. **Brief**: the kind's `src/art_crit/kinds/<kind>.md` with `{prompt}` replaced by the prompt verbatim and `{tools}` by the
   installed tools from `[run].tools` (each `"name note"`, e.g. `"python3 (standard library only)"`, listed as
   `name version note`; tools not on PATH are left out with a note). The same text for every run.
   Saved as `harness/brief.md`, never in the agent's working dir.
4. **Agents** (threads + subprocess, at most `-j` at once). Working dir = `<run>/work/` (empty at start); the harness's
   scratch is `<run>/harness/`, kept outside the working dir so the agent's project stays clean. Timeout → kill the
   process group, state `timeout`.
5. **Collect** (per run, when its agent exits): write `harness/conversation.json` (the session as a JSON array; each
   `toolResult` message carries `durationMs`, the tool's duration: from the assistant entry that called it to the
   result entry for pi, from the `tool_use` event to the `tool_result` event for Claude Code) and `run.json` (the
   run's record with `output: null`; see Run). `batch.json`'s state for the run becomes the record's `state`.
6. **Output** (per run, only when `state` is `complete`, and when `output` is missing or not `ok`): the kind's
   `finalize(work, output/)` makes the publishable output, `verify(output/)` checks it (when `finalize` succeeded), and
   `run.json`'s `output` becomes `{kind, ok, error, verified}`. A step that fails leaves `state` alone. See Kinds.
7. **Import**: `art-crit import` the batch directory with `--page` (and `--title` for a new page), then print where to
   preview (`art-crit serve`). Publishing each run is the default: right after its step 6 it is imported and pushed
   on its own (`Publisher`, one run at a time: an import rewrites page.json, and a push must never see a half-written
   run directory), so the live site fills up while the batch still runs; the batch's own import at the end is then
   skipped. `--no-publish` imports the batch once at the end and prints `art-crit publish` instead of pushing.
   Only runs that couldn't be published (a secret hit, a failed push — reported as a `note:`) fall back to it:
   it retries them and exits non-zero.

Progress: on a tty a table (model, effort, state, elapsed, turns, tokens, cost) redrawn every 2s, read from each
session file as it grows; otherwise one line per state change. The states are the agent's (queued, running, complete,
failed, timeout) plus transient labels of the output step (exporting, packaging, processing, verifying, then done, or
"no output" when it failed); the labels are never written to `batch.json`.

After progress and import/publish finish, a **failure summary** on stderr lists affected runs in plan order
(id, harness, model and effort), their agent/timeout, output or verification reasons, and the batch path for
full records/logs. It also lists unrecovered per-run import/push failures; a successful final retry clears those.
Successful runs and skipped checks are omitted. The same summary works on `--resume` and includes completed
failures on Ctrl-C, without treating queued/interrupted jobs as failed. Existing states and exit codes are unchanged.
Verification reports from every kind are saved locally at `output/verification/verify-report.json` for diagnostics
(including on resume). A verifier exception is saved as `{ok: null, error: "could not run verification: …"}`:
reported as a check problem, not an agent failure, and `output.verified` stays null. These reports are not published.

### Kinds (`src/art_crit/kinds/`)

A kind is one class registered in `KINDS` (like `HARNESSES`); the runner and the importer never branch on a kind's name.
```python
class Kind:
    name: str; tools: tuple; tools_hint: str; activity: str; serial: bool   # tools must be on PATH before a batch starts;
                                                                            # serial: finalize runs one at a time
    needs_mcp: bool                                     # runs need MCP servers: only harnesses with supports_mcp
    def brief(self) -> str                              # the template text (kinds/<name>.md)
    def prepare(self) -> None                           # one-time setup before a batch's agents start (CritError if not)
    def agent_session(self, work_dir, harness_dir)      # context manager, up exactly as long as one agent: yields the
                                                        # run's MCP servers {name: {command, args, env, hidden}} or None
    def finalize(self, work_dir, out_dir) -> (bool, str | None)    # export / package / normalize -> (ok, error)
    def verify(self, out_dir) -> dict | None            # {ok, ...} or None when it can't be checked here
    def stage(self, out_dir, run_dir, ctx) -> Staged    # the output into the run's published dir; Staged(fields, thumb, engine)
    def keep_source(self, rel, path) -> bool            # whether a work file is published as source
```
- **godot** (`Godot`): `finalize` = **Export**: write `export_presets.cfg` into the project (preset "Web", nothreads), run
  `godot --headless --path <work> --export-release Web <abs output>/index.html`, then check `index.html`, `index.js`,
  `index.wasm`, `index.pck` exist and are non-empty (Godot can exit 0 after failing), and write `export-manifest.json`
  (`godot`, `threads: false`, `template`, `exportedAt`). Failure → `ok: false`, `error = "Godot export failed: <last log line>"`.
  `verify` = serve the export, open it in Chrome with the swiftshader flags, wait for Godot to remove `#status` (≤ 30s), take
  `verification/frame-1.png`, wait 1.2s, take `frame-2.png`; `verify-report.json` = `{ok, booted, framesDiffer,
  consoleErrors, pageErrors}` with `ok = booted and framesDiffer and no pageErrors`. `stage` = the engine dedupe below.
- **web** (`Web`; `esbuild` and `npm` on PATH): `finalize` = **Package**: read `work/index.html` and inline what it references
  (`bundle_html()`): each local `<script type="module">` (with `src` or inline) is bundled by `esbuild --bundle
  --format=esm --minify` with everything it imports, npm packages from `node_modules/` included, and imported assets
  (images, models, audio, fonts) become data: URLs; each local `<link rel="stylesheet">` is bundled into a `<style>`; a
  classic `<script src>` is kept verbatim as a `data:text/javascript` URL (bundling would turn its globals into
  locals). `</script`/`</style` inside inlined code is escaped. Remote URLs, import maps and other script types are
  left alone for verify to catch. A `src`/`href` must name a file inside the work dir. Write `output/index.html` (≤ 20 MB)
  and `package-manifest.json` (`esbuild` version, `bytes`, `packagedAt`). Failure → `ok: false`, `error = "packaging
  failed: <reason>"` (e.g. `esbuild: Could not resolve "./x.js"`). `verify` = serve `output/`, load `index.html` inside
  `verification/frame.html`, an iframe sandboxed exactly like the site's (`allow-scripts allow-pointer-lock`, so storage
  APIs throw), with every request except those two pages aborted and recorded; wait for `document.readyState ==
  "complete"` (≤ 30s) and 1.2s more, then take the two frames. The report adds `blockedRequests`, and `ok = booted and no
  pageErrors and no blockedRequests` (a static page is fine, so frames needn't differ). `stage` copies the page to
  `game/index.html` (cleaned like source). Both Chrome checks are one helper (`browser.verify_page`); Playwright is an
  optional dependency (`pip install art-crit[verify]`), and verification is skipped with a note when it's missing.
- **media** (`Media`; `ffmpeg` and `ffprobe` on PATH): `finalize` checks every media file in `work/output/` (sorted, flattened as
  `a-b.png` for `a/b.png`, at most 8) into `output/`. Images (`.png .jpg .jpeg .webp .gif`) must be readable by ffprobe;
  one over 2 MB is re-encoded as JPEG (a GIF isn't). SVGs must parse as XML with an `<svg>` root (size from width/height
  or viewBox) and be ≤ 2 MB. Videos (`.mp4 .webm .mov`) must have a duration; one that isn't H.264/yuv420p mp4, is over
  10 s or over 2 MB is re-encoded (`libx264`, `-t 10`, max 1280 wide, CRF 26 → 32 → 38 until it fits). Each video gets a
  `.poster.jpg` at 30% of its length. A file that is none of those types isn't output at all: it's skipped without an
  error (a model that keeps its generator script in `./output/` shouldn't fail the step), and `output/` holding no media
  file at all is the error `no image or video files in ./output/`. Unreadable files and name clashes are errors. `manifest.json` =
  `{ok, items, errors}` with `ok` = at least one item and no errors. `ok` of the step = at least one item was kept;
  `error` = the manifest's errors (joined with `; `, the first 200 characters, the kept files are still published);
  `verify` = the manifest's `ok`. `keep_source`: text files of at most 512 KB; `output/` only for the files there that
  aren't media (the script that made them), never the images or videos themselves.
- **blender** (`Blender`, a `Media` with one more handler; `blender` 5.1+, `uvx`, `ffmpeg`, `ffprobe` on PATH; `needs_mcp`):
  `prepare` installs the official Blender Lab MCP add-on (v1.0.3, sha256-pinned zip) into an art-crit-owned Blender user dir
  (`~/.cache/art-crit/blender-mcp-1.0.3/`, passed as `BLENDER_USER_RESOURCES`; the user's own Blender is never touched) and
  fetches the MCP server (`uvx --from git+https://projects.blender.org/lab/blender_mcp.git@<pinned commit>#subdirectory=mcp
  blender-mcp`; not `uvx blender-mcp`, a different PyPI project) into uv's cache. `agent_session` starts `blender -b
  --online-mode --command blender_mcp --port N` (the add-on's background server; `--online-mode` because the add-on asks for
  network access) in the run's `work/` on a free port (up to 3 tries, ≤ 60 s each), logs to `harness/blender.log`, yields
  `{"blender": {command: "uvx", args, env: {BLENDER_MCP_PORT: N}, hidden: [the 3 screenshot and 4 jump_to_* tools, which
  need a window]}}` and kills Blender's process group when the agent ends. A Blender that won't start fails the run
  (`state: failed`), not the batch. `finalize` = the media step with `.glb` added: the file must be a glTF 2.0 binary
  (magic, version 2, length = file size, a JSON chunk, `asset.version` 2.x, at least one scene), ≤ 15 MB, and need no
  extension the viewer can't decode (`KHR_draco_mesh_compression`, `EXT_meshopt_compression`, `KHR_texture_basisu` in
  `extensionsRequired`); the item records `meshes`, `triangles` (mode-4 primitives: index count or POSITION count / 3) and
  `animations`. No media file at all is the error `no render or .glb files in ./output/`. `verify` and `stage` are the
  media kind's (a `.glb` is copied as is; it is binary, so never source).
- **text** (`Text`; nothing on PATH, activity "checking"): `finalize` takes the `.md` files in `work/output/` (sorted,
  flattened names like media's; anything else there is ignored): none is the error `no Markdown file in ./output/`, more
  than one is an error naming them. The one file must be UTF-8, at most 200 KB (`MAX_BYTES`) and hold a non-blank line;
  it is written to `output/text.md` with `manifest.json` = `{ok, bytes, words, title, errors}`. `verify` re-reads
  `output/text.md` with the same checks (`{ok, bytes, words}`; there is no browser step). `stage` writes `text/text.md`
  through `ctx.write_text` (cleaned and secret-scanned like source) and reads `bytes`, `words`, `title` and `excerpt`
  from that cleaned copy; no thumbnail. `keep_source`: text files of at most 512 KB, never anything under `output/` (the
  Markdown is the output). See ADR-0036.

### Metrics (from the session log, the same numbers pi-subagents reported)
Over assistant messages: `turns` = count; `tool_calls` = number of `toolCall` content blocks; `tokens_input/output/
reasoning/cache_read` = sums of `usage.<field>`; `tokens_total = input + output`; `cost_usd` = sum of
`usage.cost.total`. `duration_ms` = wall clock of the harness process. `state = failed` when the process exits non-zero, there is no
session file, or the last assistant message has `stopReason: "error"`; `error` = what the agent itself reported
(`metrics.error_message`, e.g. Ori's failure message) or, failing that, the last non-empty stderr line (the first 200 characters).

### Harness interface (`src/art_crit/harness.py`)
Harnesses: `pi` (the default), `claude-code`, `agy` (Antigravity CLI), `grok-build`, `muse-code`, `codex` and `ori` (OpenRouter's Ori CLI). A `-m` spec picks one with a prefix: `HARNESS:MODEL[:LEVELS]`
(no prefix, or `pi:`, = pi), in `-m`, `--set` entries and set files alike, so one batch can mix harnesses. Each run
records its harness; batch.json has `harnesses: {name: version}`. The run ids of non-pi harnesses put the harness tag after
the model (`claude-opus-5-5-cc-high-20260928-154152`), so one model under two harnesses never collides.
```python
class Harness:           # one per agent program
    name: str; tag: str                                 # tag: "" for pi, "cc"/"agy"/"gb"/"mc"/"cx"/"ori" for the others
    def version(self) -> str | None
    def models(self) -> list[str]
    def resolve(self, model) -> str                     # alias -> id (identity by default)
    def levels(self, model) -> list[str]                # supported effort levels, in LEVEL_ORDER
    def display_model(self, model) -> str               # the model name recorded for the run
    def split_spec(self, rest) -> (str, list | None)    # "MODEL@UPSTREAMS:LEVELS" -> ("MODEL:LEVELS", upstreams)
    def pinned(self, model, upstreams) -> str           # the model argument ("model@a,b"); only pi accepts upstreams
    supports_mcp: bool                                  # pi, claude-code, codex, grok-build, ori
    def command(self, model, level, brief, session_dir, mcp=None) -> list[str]  # mcp: the kind's servers for this run only
    def env(self, model=None, harness_dir=None) -> dict | None  # the agent's environment (None = inherit)
    def session_file(self, session_dir) -> Path | None  # the raw session in harness/ (never published)
    def session_entries(self, session_dir, brief, level) -> list  # the session in pi's format -> conversation.json
    def metrics(self, session_dir, level) -> dict | None          # parse_session()'s shape; tolerates a growing file
    def finish(self, harness_dir, model, metrics) -> dict         # final touches from the scratch dir (pi: the OpenRouter route
                                                                  # and cost); `notes` join the run's error, `extra` fields join the run
```
Pi: `pi --version`; `pi --list-models` (parse the table); levels via `pi --mode rpc --no-session --model M -ne -ns -np -nc`
sending `{"type":"get_available_thinking_levels"}` and reading the matching response;
command = `pi -p --mode json --model M:LEVEL --session-dir DIR -ne -ns -np -nc BRIEF` (no user extensions, skills,
prompt templates or AGENTS.md, so runs are reproducible); session file = the `*.jsonl` in DIR that isn't pi's stdout (`events.jsonl`).
With MCP servers (blender), pi's built-in MCP support (which `-ne` leaves out, and which has no per-run config flag) is
loaded with `-e builtin:mcp --approve`: the servers go in `work/.pi/mcp.json` (`exposure: "direct"`, `timeout: 600`), a
project config that `--approve` trusts for this run only, and the hidden tools go to `--exclude-tools`. `.pi/` is never
published as source. Codex gets them as `-c mcp_servers.<name>.{command,args,env,disabled_tools,tool_timeout_sec=600,
startup_timeout_sec=60}` overrides. agy and muse-code read MCP servers only from the user's global config (measured: muse
ignores a project `.muse/settings.json`, and `--trust-workspace` would turn on its sub-agents), so each gets one permanent
`art-crit-<name>` entry there (`install_proxy_entries`: `~/.gemini/config/mcp_config.json` with `timeoutSeconds: 600` and
`tools: {<visible tool>: {eager: true}}`, since agy declares a tool up front only when named that way; `~/.config/muse/
settings.json` with `type: "stdio", mode: "optional"`; other entries and keys kept, written only when changed, a config
with comments or muse's legacy `mcp_servers` key refused). The entry runs `python3 ~/.cache/art-crit/mcp_proxy.py <name>`
(a stdlib copy of `src/art_crit/mcp_proxy.py`), started by the harness in the run's `work/`: it reads the run's servers
from `<run>/harness/art-crit-mcp.json` (written per run; not an env var, because muse passes MCP servers only an allowlist
of the environment), runs that server, relays stdio line by line and drops the `hidden` tools from `tools/list`.
Outside an art-crit run there is no such file and the proxy is an MCP server with no tools, so the user's own sessions
see nothing. grok-build writes `work/.grok/config.toml` (a project config, never published as source) whose server
runs the same proxy (Grok has no field that hides tools) and runs grok with `GROK_FOLDER_TRUST=0` (project servers
start only in a trusted folder, and `--trust` would record every run dir in `~/.grok/trusted_folders.toml`). Grok's
models reach MCP tools only through its `search_tool`/`use_tool` meta-tools. ori gets the run's servers in
`work/.ori/mcp.json` (a workspace config it merges for the run; each server needs `type: "stdio"`), and it has no
per-server tool filter, so nothing is hidden there and `tools.mcp.<server>.hidden` is recorded empty. Ori also merges the
user's own `~/.ori/mcp.json` and `./mcp.json`, which art-crit can't turn off: run it with isolated Ori configuration for
strict comparisons. Transcripts name every MCP call
`mcp__<server>__<tool>` (agy's `call_mcp_tool` and muse's `mcp__art_crit_<server>__<tool>` are converted). The planning
check still refuses a harness without `supports_mcp` for a kind that needs MCP.
Every `openrouter/` run adds `-e src/art_crit/pi_ext/openrouter_routing.ts` (explicit `-e` paths still load under
`-ne`) and sets `ART_CRIT_ROUTE_LOG=<harness dir>/route.jsonl` in that run's environment. A pinned run (`MODEL@slug`)
passes the base id to `--model` and also sets `ART_CRIT_OPENROUTER_ROUTING={"only": [...], "allow_fallbacks": false}`
(never inherited from art_crit's own environment), which the extension merges into the request's
`provider` field. The extension logs, per response (generation id), `{id, provider}` from its first stream chunk and
`{id, cost}` from the final chunk's `usage.cost`; the run records `route` from that log (see Run). The upstream is part of the recorded model name
(`openrouter/…/flash@deepinfra`), so two upstreams are separate rows; run ids use `-via-`.

Claude Code (`claude`): version = first word of `claude --version`. Models come from a table in the harness (there's no
listing command), mirroring the CLI's own alias table: `claude-fable-5-1`, `claude-opus-5-5`, `claude-opus-5`,
`claude-opus-4-8`, `claude-opus-4-7`, `claude-opus-4-6`, `claude-sonnet-5-5`, `claude-sonnet-5`, `claude-sonnet-4-6`,
`claude-haiku-5-5`, plus the aliases fable/opus/sonnet/haiku (each the newest of its family, `sonnet` = `claude-sonnet-5-5`);
runs are recorded as `anthropic/<id>`. Levels are low, medium, high, xhigh, max (no minimal/off), but only the ones the
model actually takes: the CLI silently clamps a level it doesn't accept (measured: `--effort xhigh` on the two `*-4-6`
models sends `effort=high`), so those are listed without xhigh, and a model that ignores effort entirely (e.g.
`claude-haiku-4-5`) isn't listed at all. Command = `claude -p --model ID --effort LEVEL --output-format stream-json --verbose --safe-mode
--permission-mode bypassPermissions --no-session-persistence --tools=Bash,Read,Write,Edit,Glob,Grep
--disallowed-tools=Agent,Task --disable-slash-commands -- BRIEF`: one direct agent with only the core file and shell
tools (like pi: no sub-agents, web, scheduling, messaging or skills), none of the user's CLAUDE.md, memory, plugins,
hooks or MCP servers (login still works), and nothing saved to the user's session history. With MCP servers (blender), `--safe-mode`
becomes `--setting-sources=` (it drops `--mcp-config`, measured) and `--mcp-config=<harness>/mcp.json --strict-mcp-config` is added,
with the kind's hidden tools appended to `--disallowed-tools` as `mcp__<server>__<tool>`; `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1`
and `MCP_TOOL_TIMEOUT=600000` are always set, so the system prompt matches safe mode's except for the server's tools. `CLAUDECODE` and
`CLAUDE_CODE_*` are removed from its environment (art-crit may itself run inside Claude Code). The stdout stream-json is
the session; its raw events carry account/session details, so they're not published (for any harness). Conversion to pi's format:
assistant events are merged by message id (the stream emits one per content block, each repeating the usage) and
become assistant messages (text; thinking only when non-empty, print mode usually omits it; `tool_use` → `toolCall`
with Bash/Write/Edit/MultiEdit/Read mapped to pi's bash/write/edit/read names and argument shapes, file paths made
relative to the run dir; other tools keep their name and input); `tool_result` blocks become `toolResult` messages (text blocks joined into one text block; each image block becomes
`{type: "image", mimeType: "image/jpeg", data: <≤320px JPEG thumbnail made with ffmpeg>, sourceMimeType, bytes}`,
without `data` when ffmpeg is missing or fails, never the original ~500 KB image);
messages keep the stream event's `timestamp` (a merged message its first event's; the session entry and the brief the
first one in the stream); the brief is the first user message; an error result adds a final assistant message with `stopReason: "error"`.
Sub-agent events (`parent_tool_use_id` set) are skipped. Metrics: turns = top-level assistant API messages, tool
calls = their `tool_use` blocks; tokens from the final `result.usage` (the stream's per-message usage is a snapshot
taken before output is written and undercounts it; it's only summed while the run is still going), reasoning =
`result.usage.output_tokens_details.thinking_tokens`; cost = `result.total_cost_usd` (Claude Code's estimate at API
prices, also on a subscription); failed = `result.is_error` (error = `result.result`).
Agy (`agy`): models come from `agy models`, grouping the effort-suffixed slugs (`gemini-3.8-flash-high` → `gemini-3.8-flash:high`). The selected slug is passed with `--model`, **not** separately overridden with `--effort`. Runs use the underlying model vendor prefix (`google/`, `anthropic/`, `openai/` where recognizable), rather than grouping all models as Antigravity. Command uses `-p BRIEF --output-format stream-json --dangerously-skip-permissions --disable-slash-commands`. Stateless headless mode produces `init`, `step_update`, and `result` NDJSON. Tool steps are emitted once on `DONE` (not again on `ACTIVE`); agent response deltas are concatenated in order. The final result's usage supplies tokens (including `thinking_tokens`); cost is unavailable and recorded as 0, not a measured price. Non-success results fail the run. Agy currently has no documented equivalent of Claude Code's `--safe-mode` or tool allowlist: the headless session may load user configuration/tools. Runs should use an isolated CLI profile for reproducibility.

Grok Build (`grok`): models are intersected with `grok models`; effort menus for known models are in `GrokBuild.MODELS` (update when the CLI changes, as `grok models` doesn't list levels). Command uses `-p BRIEF --model ID --reasoning-effort LEVEL --output-format streaming-messages-json --always-approve --verbatim --tools run_terminal_cmd,read_file,write_file,search_replace,grep,list_dir --disallowed-tools Agent --disable-web-search --no-subagents`. The stream's Messages-compatible `assistant`/`user`/`result` events reuse the Claude Code converter. Final result usage has `reasoning_tokens`, and cost is `total_cost_usd` when supplied; under pool/OAuth it can be missing (0 in the current numeric run schema means **unreported**, not free). Grok's MCP meta-tools may still be enabled by the user's configuration, even with `--tools`; run with isolated configuration for strict comparisons.

Muse Code (`muse`): models and levels come from the catalog `muse` caches in `~/.local/share/muse/model-catalog/*.json` (`rows[].model_id` with `reasoning_effort_variants[].tier`, hidden `-contributor` rows included, image models skipped), refreshed only when the Muse TUI fetches it; the `MuseCode.MODELS` table is the fallback without a cache. The recorded model is `meta/<id>`. Command: `bash -c` running `muse exec --json --session-id ID --model M --reasoning-effort L --disable-approval --disable-sandbox --disable-web-tools --disable-reminders --no-foreign-personal-context -- BRIEF`, then `muse export --session ID --out harness/export.json` whatever `exec`'s exit code was (exec's own `--json` stdout, `events.jsonl`, carries no tool calls or usage). `export.json` is the session: its `events` are records whose `runtime.session` payloads of `kind: run` hold `reasoning_committed`, `assistant_message_committed`, `assistant_tool_calls_committed` (`tool_calls[{call_id, name, args}]`), `tool_result_batch_committed`, `model_completed` (`usage`) and `terminal` events; only runs with a `top_level_turn.run_origin` fact count. Conversion: one assistant message per model call (thinking, text, toolCalls, usage); `bash`/`write_file`/`edit_file`/`read_file` become pi's `bash`/`write`/`edit`/`read`; tool durations are exact (the `tool_batch.effect` start and end per call); timestamps from the records' `recorded_at` (µs). Metrics: turns = `model_completed` events, tokens summed over their usage with `input` = `input_tokens` - cache read/write (Muse's include them), reasoning = `reasoning_tokens`; `cost_usd` for models with published [Meta Model API prices](https://dev.meta.ai/docs/pricing-rate-limits) is `(input + cacheWrite) * input_rate + cacheRead * cached_rate + output * output_rate`, divided by 1M (reasoning is already in output). It is marked `metrics.cost_estimated: true`: API-equivalent, **not** actual subscription spend. Supported: Wonder 1.0 Standard ($4/$0.20/$20 per million uncached/cached/output), Spark 1.2/1.3 Standard ($1.25/$0.15/$4.25) and Spark 1.2/1.3 Contributor ($0.10/$0.002/$0.20). Muse Wonder Full and Wonder Contributor have no published API rate: they use Wonder Standard's rate as a **proxy**, marked `metrics.cost_estimate_proxy: "meta/muse-wonder-1.0"` (≈ in the viewer). Unknown models remain 0 (**unknown**, not free). The rates are pinned in `MuseCode.API_PRICES` and require updating when Meta changes pricing. Re-importing a legacy Muse run with `harness/export.json` calculates its estimate without modifying the archived batch run.json. Failed = no `terminal` event or one that is not `completed` (error = its `reason`).

Codex (`codex`): version = second word of `codex --version` (`codex-cli X`). Models and levels come from `codex debug models` (`models[].slug` with `supported_reasoning_levels[].effort`, `visibility: list` rows only; `ultra` is dropped because it isn't in LEVEL_ORDER), cached per harness instance; runs are recorded as `openai/<slug>`. Command = `codex exec --json --ephemeral --ignore-user-config --ignore-rules --skip-git-repo-check --dangerously-bypass-approvals-and-sandbox -m ID -c model_reasoning_effort="LEVEL" BRIEF`: one direct agent, no approvals or sandbox (like the other harnesses), no user config or execpolicy rules, and nothing persisted to `~/.codex/sessions`. The stdout JSONL stream is the session. Conversion to pi's format: only `item.completed` items count (`item.started`/`item.updated` are the same item in flight); `reasoning` -> thinking, `agent_message` -> text, each tool item (`command_execution` -> pi's `bash` with the command, `file_change`, `mcp_tool_call`, `collab_tool_call`, `web_search`) becomes one assistant `toolCall` plus its `toolResult` (`command_execution`'s output is `aggregated_output`, failed when its status isn't `completed` or its exit code is non-zero); a `turn.completed` flushes the pending assistant message with that turn's usage. The stream carries no timestamps and no model id, so entries have neither. Metrics: turns = `turn.started` count (at least the completed ones), tool calls = completed tool items, tokens summed over `turn.completed` usage with `input` = `input_tokens` - cached - cache-write (Codex's includes cached ones), reasoning = `reasoning_output_tokens`; cost is not reported (0 = **unreported**, not free); failed = a `turn.failed`/`error` event or no completed turn (error = its message).

Ori (`ori`): OpenRouter's Ori CLI, running its own runtime agent (`ori code`, pinned with `--harness ori` so the
user's default harness can't change what a run is). Models are OpenRouter's, fetched live from its public catalog
(`https://openrouter.ai/api/v1/models`, no credential; `fetch_json` is the one place art-crit reads the network) and
cached per harness instance: every model that outputs text, image/video models skipped. Levels are
`off, minimal, low, medium, high, xhigh, max` for a model advertising `reasoning_effort`, and `off` alone otherwise
(like a non-reasoning model under pi), with art-crit's `off` passed as Ori's `--reasoning-effort none`. Runs are
recorded as the bare OpenRouter slug (`deepseek/deepseek-v4.1-flash`), which is what the viewer groups by vendor.
Command = `ori code --harness ori --output jsonl --approvals self-drive --model ID --reasoning-effort LEVEL -p BRIEF`
(the default approvals mode, spelled out; no sandbox or approval prompts, like the other harnesses). The stdout JSONL
stream is the session: each line is `{kind: "event", event}` whose event is a `runtime.event` wrapping the agent's own
event (`audit.event` lines aren't part of the session), and the last line is `{kind: "result", ok, sessionId, error}`.
Conversion to pi's format: `reasoning.delta`/`assistant.text.delta` deltas join into one assistant message per flush,
`tool.started` becomes a `toolCall` block, its `tool.succeeded`/`tool.failed` one `toolResult` message (with the
event's own `durationMs` when present, else computed from the timestamps), a failed turn or session a final assistant
message with `stopReason: "error"`. Metrics: turns = settled turns, tool calls = `tool.started` events, tokens and cost
from the turn results' usage (`inputTokens` excludes the cache read/write ones, `cost_usd` is the usage's `costUsd`, OpenRouter's
own charge — reasoning tokens aren't reported, so 0); failed = a failed turn/session, a result line with `ok: false`,
or no turn that ever settled (error = its `failure.message`, else the result's `error.message`). Ori also records each
session in its own workspace (`~/.ori/...`), which art-crit doesn't read.

Future harnesses and a VM runner plug in here and at "start one agent" in `runner.py`; a container executor mounts one run directory.

### Ctrl-C
Kills every running agent's process group, marks those runs `queued` in batch.json, prints the `--resume` command, exits 130.

### Stopping one run (`harness/stop`, the local monitor's Stop button)
Each agent runs in its own process group, so only the `art-crit run` process that started it can kill it. It waits for
the agent in `wait_agent()`, checking once a second for `<run>/harness/stop`: if the file is there, it kills the group and
the run is collected as `failed` with `error: "stopped from the local monitor"` (see Run monitor, ADR-0027). A timeout
uses the same loop and `outcome: "timeout"`. Nothing else writes that file.

### Resume
`batch.json` = `{prompt, kind, page, title, title_is_explicit, harnesses, brief, request, created, runs: [{id, harness, model,
model_arg, level, state}]}`, updated on every state change (`model` = what the site shows, `model_arg` = the harness's id).
`--resume DIR` reads it and, per run: `queued`/`running` → start the agent again (its run directory is emptied first); a
finished agent is never rerun. Then the output step for a `complete` run whose `output` is missing or not `ok` (so a failed
export is retried), and import. Failed and timed-out runs stay as they are. A batch written by an art-crit that grouped runs by
model (no `id` in its runs) can't be resumed.

### Retry
`art-crit retry <slug> [run_id...]` runs a page's failed runs again (failed in any of the three senses of `run_failed`; with
no ids, every failed run on the page; naming a run that didn't fail is an error). Per failed run it builds the same
`harness:model:level` spec (`retry_spec`: the model id the harness lists under the run's recorded display name, plus the
`@upstream` pin of a pinned OpenRouter run) and starts one ordinary `art-crit run --page <slug>` batch, so the page's prompt,
kind and references are reused and each new run is imported and pushed as it finishes. Afterwards a failed run is removed
when a new run with the same harness, model and effort is good (then one rebuild and one commit,
`art-crit retry: <slug> (replaced N failed runs)`, unless `--no-publish`); a failed run whose retry also failed stays, is listed
as `still failed` and the exit code is 1. "Good" means a newer run of the same harness, model and effort that isn't failed, so
that is also checked before starting: a failed run that already has one (a manual re-run, or a retry that was interrupted) is
replaced without running again, and failed runs of one harness/model/effort (several timeouts) share one new run and are all
replaced by it. Ctrl-C still replaces whatever its finished runs fixed. Without run ids, a run whose model the harness no
longer offers is skipped with a warning (it stays, exit 1); with ids it is an error. Declining the confirmation changes
nothing. `--dry-run` prints the batch plan and changes nothing. A retry costs money like any run.

## Ranking

The page owner ranks runs in the browser; there is no CLI command for it. Only `art-crit serve` can save a ranking
(GitHub Pages is static), so the published site shows rankings read-only.

- `art-crit serve` answers `GET api/local` → `{"rank": true, "cover": true, "requests": true, "runs": true, "video": true}` (`video` = the video studio) and `PUT api/rank?p=<slug>` with body
  `{"ranks": {"<run id>": <int>|null, ...}}`. It validates the slug (`[a-z0-9][a-z0-9-]*`, page must exist), that every
  id is a run of the page, and that each rank is a whole number from 1 to the number of runs (ties allowed; `null`
  = unranked), writes `data/<slug>/ranking.json`, then rebuilds. Errors are `400 {"error": ...}`.
- Cross-site writes are refused: the request must be `Content-Type: application/json` (so another site can't send it
  without a CORS preflight, which the server doesn't answer) → else 415, a loopback `Host` (127.0.0.1, localhost or ::1;
  a DNS-rebinding site sends its own name in both Host and Origin) → else 403, and an `Origin` header, when present, must
  match the `Host` → else 403.

## Covers

The home page and the run cards show defaults: a page's cover is one of its highest-effort runs, and a media/blender run's
`thumb` is just its first image, which can show the subject from behind. `data/<slug>/covers.json` holds the owner's
**overrides only** (with none set, the defaults apply):

```json
{ "thumbs": { "<run id>": "media/front.thumb.jpg" },
  "page":   { "run": "<run id>", "image": "media/front.thumb.jpg" },
  "covers": { "<run id>": "media/front.thumb.jpg" | false } }
```

- `thumbs`: a run's main thumbnail (its card, table row and `thumb`). `rebuild` applies it to `page.json.runs[].thumb`
  and marks that run `thumb_override: true` (the run page shows a pressed toggle only for a real override, not for the
  default `thumb`); `run.json` is untouched.
- `page`: the page's home-page picture (a run, and one of its images; `image` defaults to the run's thumbnail, which is
  all a game or page has). `rebuild` copies it to `page.json.cover` and `pages.json`'s `thumb`; the home page's tile and
  the slideshow's first slide use it instead of choosing. A failed run can't be the page's cover (the pick is ignored).
- `covers`: hand-edited, home-page only: a path swaps the picture the default choice would use for that run, `false`
  keeps the run out of the default choice (e.g. its only picture shows a character from behind).
- Paths are relative to the run and must exist; entries for runs or files that are gone are ignored. A covers.json that
  isn't a JSON object is reported by `rebuild` (a warning) and ignored; `api/cover` refuses to write over it. A `thumbs` or
  `covers` that isn't an object counts as empty.

`art-crit serve` writes `thumbs` and `page` for you: `PUT api/cover?p=<slug>` with `{"thumb": {"run", "path"|null}}`
and/or `{"page": {"run", "image"?}|null}` (null clears); same loopback / same-origin / JSON checks as `api/rank`, `run`
must be a run of the page, `path` and `image` must be an image file inside that run's directory, and the file's other keys are kept. The run page then shows
"Use as run thumbnail" and "Use as page cover" toggles on each image (a game or page: "Use as page cover" only), only when
`api/local` says `cover: true`. Publishing is the usual `art-crit publish`.

## Social videos

`art-crit video <slug> <run_id>...` makes MP4s of 2 to 12 runs of a page, one per layout, for posting (the
**Video studio** below makes one video of your own design, from the browser). They are made on this machine and never published: the default folder is
`<root>/videos/<slug>/` (git-ignored, outside `docs/`), named `<UTC stamp>-<slug>-<layout>.mp4`. The command prints the
files and the site's compare link for those runs, to paste into the post. Needs ffmpeg + ffprobe and Playwright with Chrome
(`.[verify]`); failed runs can't be included.

- **Layouts** (`-l`, repeatable, default all three), each `hook` → runs → `finale`: `reveal` 1080x1920, each run in turn
  (`-d` seconds each); `grid` 1080x1920, every run at once in numbered tiles that land one after another, then a spotlight
  that steps through them; `wide` 1920x1080, like `reveal` with the caption in a panel beside the picture.
  H.264, 30 fps, AAC sound (`video_sound.py`: a 120 bpm beat with a soft tock on each cut, pops and ticks on what lands and
  counts, a ding for the pick; `--no-sound` / `"sound": false` = a silent track, which platforms still expect).
- **The motion** (`scene/scene.js`, timings in `video.TIMING`): the `hook` (3 s; its first frame is already the cover) shows a
  tilted, drifting wall of every run's clip, the site's logo (`assets/logo.svg`, in its dark-mode colours: the scene is
  opened with a dark colour scheme; the logo also tops each run's bar and the grid), a headline (`N AI models. Same prompt.`, or `<model> / N effort levels.` when
  every run is one model) and the prompt typing into a bubble (whitespace collapsed, at most 600 characters). A run's turn:
  its card springs in with motion blur and whips out at the end; its number badge, vendor icon and name, effort meter and
  time / tokens / cost (counting up) follow, with a story-style progress bar, the run counter and the prompt at the top.
  With 3+ runs, one sticker each goes to the runs that stand out (`video.stickers`: FASTEST, CHEAPEST, PRICIEST, SLOWEST, in
  that order; unreported costs don't count). The `finale` (4.5 s): every run as a numbered tile (`video.tile_boxes`), "Place
  your vote", "on <logo> ↓" (→ when wide) and the site pill; if any of the runs has an owner's rank, the best-ranked one
  gets a crown and the line becomes "My pick: #n. What's yours?". Names are the site's own (`runs.js`: `prettyModelName`, vendor names,
  icons and hues).
- **One source clip per run** (`-d`, 2 to 20 seconds, default 4, silent, 1080x1080, used by every layout): its video if it has
  one; else its 3D model, recorded in the run page's own viewer while it is orbited; else its images (up to 3, the owner's
  thumbnail pick first) with a slow zoom. A game or page is recorded in `play.html` (the site's sandbox), clicked and played
  with a few key presses. A recording that fails falls back to the run's pictures (said in the progress output).
- **Rendering** (ADR-0033): each clip is cut into JPEG frames (full and half size), and each layout is drawn frame by frame by
  `scene/scene.html` in a GPU Chrome: `renderFrame(f)` is a pure function of the frame number, then a CDP screenshot is piped
  into ffmpeg with the sound. The scene, its `plan-<layout>.json` and the frames are served from the job's temp folder, with
  `assets/` linked to `docs/assets/`; the scene has a strict CSP and puts every string from a run or prompt in with
  `textContent`. Model-made SVGs are only drawn through an `<img>` in Chrome (ADR-0004).
- The scene's helpers (easing, posing, frames, the logo, a run's caption, the glow) are `scene/motion.js`, shared with the
  video studio's scene.

## Video studio

`docs/studio.html` (`assets/studio/studio.js` + `studio.css`; ADR-0034) makes one video of your own design: a template, its
slots filled with runs from any page, text cards between them, and settings. It only works under `art-crit serve` (it asks
`api/local` for `video`; elsewhere it says it runs locally), and the lanes home (and the classic one) link to it there. The
lanes compare page links "Make a video of these runs in the video studio" to `studio.html?p=<slug>&r=<ids>`, which picks a
template for that many runs (2 → Head to head, 3 or more → Reveal, the first twelve) and fills its slots in order. A new
studio starts like `art-crit video`'s reveal: the Reveal template with a Hook card first and a Finale card last, time and
cost on. Same requirements and output rules as `art-crit video`; files go to `<root>/videos/studio/<UTC stamp>-<template>.mp4`.

- **Templates** (`studio.TEMPLATES`): `art-crit video`'s three layouts: `reveal` (9:16, 2 to 12 runs, default 4, one after
  another, numbered), `grid` (9:16, 2 to 12, all at once: the grid's header with the opening's lines and the shared prompt,
  numbered tiles landing one after another, then the spotlight stepping through them) and `wide` (16:9, 2 to 12, one after
  another with the caption beside the card); then `duel` Head to head (16:9, Left / Right, all at once), `lineup` Line-up (16:9, 3 or 4,
  numbered, all at once), `wipe` (16:9, Model A / Model B in one square; the divider sweeps from A to B, then settles at
  the spec's `wipe` %), `ladder` Effort ladder (9:16, low / medium / high / max, one after another), `countdown` (9:16, #5 to
  #1, one after another), `montage` Grid montage (1:1, 6 numbered tiles; after they land they dim and the first title card's
  heading comes up over them). One-after-another templates draw each run like `art-crit video`'s `reveal` (or `wide`, in 16:9):
  card, badge, a sticker where one stands out (`video.stickers`, 3+ runs), the caption with the effort meter, counting
  numbers when "time and cost" is on, a progress bar and the run's page title.
- **Cards** (`studio.CARDS`): Hook and Finale are `art-crit video`'s opening and closing, drawn by the same code
  (`scene/parts.js`), always on the glow, over the runs in the slots: the Hook's headline is its heading and subtitle, or
  else `N AI models. / Same prompt.` (`<model> / N effort levels.` for one model; `N prompts.` when the slots come from
  several pages), and the prompt types into a bubble only when every slot shares one; the Finale's question is its heading
  (default "Place your vote"), the line under it its subtitle (default "on <logo> ↓"), its pill its link, and the crown
  goes on the best-ranked run only when every slot is from one page (ranks are per page). Then Title, Question, Section,
  Vote (with a link chip) and Credits, each with a heading (≤ 90), an optional subtitle (≤ 280; vote and finale cards also
  a link ≤ 60), a look (`studio.LOOKS`: Glow = the videos' dark background with a drifting glow, Dark, Purple, Peach,
  Light) and 2, 3 or 5 seconds; at most 12. A card's `at` is how many result blocks play before it (all-at-once templates have one block), so a
  large `at` means the end. Rendered: the look's colour opens as a circle, the heading's words rise in, the subtitle and the
  link chip follow; the video's opening card is complete on its first frame (the cover). Light looks invert the logo's ink.
- **Settings**: seconds for each still (2, 3, 5), seconds for each recording of a game, page or 3D model (4, 6, 8;
  default 4, `art-crit video`'s pace), what happens when moving results differ in length (`together`: each stops
  on its last frame; `stretch`: each is slowed to fill the block; `loop`), music (`none` = a silent track, `upbeat`,
  `lofi`, `cinematic`; sound effects come with the music), labels (model + effort on each result) and time and cost.
- **Lengths** (`studio.clip_seconds`): a still plays the still length; a video its own (2 to 10 s); a game, web page or 3D
  model the recording length (recorded for that long). An all-at-once block lasts as long as its longest result.
- **The spec** (`studio.check_spec`): `{template, count?, slots: [{page, run}|null], cards: [{id, type, heading, sub, link,
  look, secs, at}], still, record, sync, music, labels, metrics, wipe}` (`metrics` defaults to true, `record` to 4). A render needs every slot filled with a run that didn't
  fail; the same run may fill two slots (recorded once). The page keeps the spec in `localStorage` between visits.
- **The page** (the design's "Video studio" artboard): 1 · template cards with a small diagram, format, slot count and how
  they play; 2 · a preview of the frame (the runs' thumbnails in the template's layout, or the card at the playhead, or the
  card being edited; a Hook or Finale card is sketched: its headline over the runs' pictures, or its question over
  numbered tiles) with back/play/forward, a scrubber and speed, the wipe position for the wipe; the timeline (a block
  per segment, sized by length, click to jump or edit a card), "Add a card", the card editor (heading, subtitle, link,
  look, length, earlier/later, delete, done); the settings panel and Render; then "Your renders": renders under way (their
  step) or failed (Dismiss), then every video in `videos/studio/`, newest first, with the video, Download and Delete
  (after a confirm). Each render writes `<name>.json` beside its MP4 (title, template, format, slots, length) for this
  list; an older video without one is listed by its file name. The result picker is a modal dialog listing every run that didn't fail, filtered by prompt, type, vendor and
  effort, grouped like the page's lanes: one row per model ("Vendor – Model", vendors and models by name), its runs by
  prompt and then effort.
- **Local API** (`art-crit serve` only, like `api/rank`: loopback `Host`, same-origin, JSON; reads carry no CORS headers):
  `GET api/studio` → `studio.catalog()` (templates, looks, cards, choices, limits); `POST api/studio/plan` with a spec (empty
  slots allowed) → `{segments: [{type: card|slots|slot, start, secs, card?, slot?}], total, slots: [{type, secs}|null],
  labels}` (the preview's timeline, the same `studio.timeline` the render uses); `POST api/video` with `{"studio": spec}`
  checks it (400 with the reason) and starts a background render, one at a time → `{"job": id}`; `GET api/video?job=<id>`
  → `{job, state: running|done|failed, step, files, error, title, template, format, slots, length, started}`;
  `GET api/video/jobs` → `{jobs: [running or failed renders, newest first], renders: studio.renders(root)}`;
  `GET api/video/file?name=<file>` serves one of those `renders` (nothing else); `POST api/video/delete` with
  `{"name": file}` deletes a listed video and its `.json` (`studio.delete_render`), with `{"job": id}` dismisses a
  finished or failed render from the server's memory (400 for anything else).

## Prompt requests

Ideas for new pages (ADR-0030). The lanes home page (`index.html`) has a **Request a prompt** button in the top bar
(`docs/assets/lanes/request.js`) that opens a modal form: prompt (10–4000 chars), kind (one of `KIND_UI`'s, shown by
label), note (optional, ≤ 1000). Submitting posts `{prompt, kind, note}` to `POST api/request` (see Community votes):

- `201 {"number", "url"}`: the form says which issue it became, linked (only a URL under the repo's issues is linked).
- `401`: the draft goes to `sessionStorage`, the visitor signs in (`api/login?return=<this page>#request`), and the
  form reopens with the draft on the way back.
- `404`, `503`, a non-JSON answer or a network error (no request API: `art-crit serve`, a static host, a Worker not
  yet configured): the form opens `https://github.com/fenderog/art-crit/issues/new` in a new tab with the same title,
  body and label the Worker would use, for the visitor to submit there.
- anything else: the API's `error` is shown under the form.

The issue: title `Prompt request: <first line, ≤ 80 chars>`, label `prompt request`, body `**Kind:** <label>
(`--kind <id>`)`, the prompt and the note each in a fenced `text` block longer than any backtick run inside them (so
GitHub shows them verbatim: no mentions, links or Markdown), and the requester's login in code formatting.

The older local list stays on the classic home page (`classic/index.html`, ADR-0024): under `art-crit serve` only,

- `GET api/requests` → `{"requests": [...], "sets": [...]}` (`sets`: the names in art-crit.toml `[sets]`).
- `PUT api/requests` with `{"add": {"prompt", "kind", "title"?, "note"?, "set"?}}` or `{"remove": "<id>"}` →
  `{"requests": [...]}`. `prompt` is required (≤ 4000 chars), `kind` one of the registered kinds, `title` ≤ 120,
  `note` ≤ 1000, `set` a name from `[sets]`; text is trimmed and empty optional fields are dropped. Each request gets
  an `id` (8 hex chars) and `created` (UTC). Errors are `400 {"error": ...}`; same write checks as the ranking API.
- Stored in `requests.json` next to `docs/` (gitignored), never under `docs/`, so no publish step can push it.
- `requests.js` shows a "Request a prompt" button in the classic hero that opens a modal form (prompt, kind,
  title, model set, note, and a live preview of the command), and a "Requested prompts" list, newest first, each
  card with its `uv run art-crit run -k KIND [-t TITLE] [-s SET] 'PROMPT'` command (POSIX-quoted), Copy and Remove.

- `rebuild` copies each run's rank into `page.json.runs` (`rank`, `null` when unranked) and drops `ranking.json` entries
  for runs that no longer exist (e.g. after `art-crit rm`).
- The viewer only asks `api/local` when served from localhost; when it answers, the page shows a rank picker per row.

## Run monitor

`art-crit serve` (only) shows what `art-crit run` is doing on this machine, live: every batch under `[run].dir`,
newest first, with each run's state, metrics, prompt, files and transcript, and a Stop button for a running agent
(ADR-0027). The published site has no `api/runs`, so `monitor.html` and the home page's "Runs (local)" link do nothing there.

- `GET api/runs` → `{"dir": "<[run].dir>", "batches": [{batch, page, kind, title, prompt, created, runs: [...]}]}`: the
  newest 30 batches, each run `{id, harness, model, level, state, metrics, output, error, started_at, activity_ms,
  published}`. A `running` run has no `run.json` yet, so its metrics come from the growing session file (each harness's
  own parser, the one the CLI's progress table uses) and `duration_ms` is the run directory's age; `activity_ms` is how
  long since the agent last wrote to `harness/`. `published` says whether the site already has that run. Batch dirs from
  before run ids existed (no `id` in their runs) are left out.
- `GET api/run?b=<batch>&r=<run id>` → that row plus `prompt`, `brief`, `files.work`/`files.output` (`{name, bytes}`,
  capped at 200 files each) and `transcript` (pi-format entries, ready for `renderTranscript()`): the finished
  `harness/conversation.json`, or the running run's session converted live, with `live` and `truncated` flags.
- The monitor's transcript is deliberately light: image blocks become `[image omitted here]` and strings are cut at
  4000 characters (a live pi session keeps a base64 copy of every image the agent looked at; one real run reached
  15 MB), and at most the last 400 entries are sent. A run's own page has the full transcript.
- `POST api/stop` with `{"batch": ..., "run": ...}` → writes `<batch>/<run id>/harness/stop`; `400 {"error": ...}`
  unless that run is `running` right now. `art-crit serve` doesn't own the agent process, so it only asks: the
  `art-crit run` process that started the agent checks for that file once a second, kills the agent's process group and
  records the run as `failed` with `error: "stopped from the local monitor"` (ADR-0027). Same write checks as the
  ranking API; a re-run's `rd.reset()` deletes a left-over stop file.
- The monitor's reads need a loopback `Host` too and are answered **without** `Access-Control-Allow-Origin`, so
  another website can't read the runs even by pointing a script at 127.0.0.1.
- The page (`monitor.html` + `assets/monitor.js`) polls `api/runs` every 2 seconds while something is queued or running
  (and the tab is visible): the batches on the left, the selected run on the right with a state chip, stat tiles, the
  prompt and the brief it got, `work/`/`output/` file lists and the transcript. Rendering is `el()`/`textContent` like
  the rest of the viewer.

## Community votes

Visitors signed in with GitHub can give each result a heart and hand out one gold, one silver and one bronze medal per
page (ADR-0022). Votes and prompt requests (ADR-0030) are the only things the published site writes; the owner's ranking
above stays local. The API is
`cloudflare/votes.mjs`, served by the Worker at `/art-crit/api/*`, storing in D1 (`cloudflare/schema.sql`).

Tables: `hearts(page, run, user_id)`, primary key all three. `medals(page, user_id, medal, run)` with `medal` in
`gold|silver|bronze`, primary key `(page, user_id, medal)` and `UNIQUE (page, user_id, run)`: one of each medal per user
per page, each on a different result. `user_id` is the GitHub numeric id; logins and tokens are never stored.

`prompt_requests(user_id, at, issue)` counts prompt requests (unix seconds, the issue number), indexed by `(user_id, at)`
and `(at)`; the text is never stored, only the issue on GitHub has it.

`tallies(page, run, hearts, gold, silver, bronze)` holds the running totals and is maintained only by four triggers on
`hearts` and `medals`, so every write keeps it exact, atomically. Showing a page therefore reads one `tallies` row per
run plus the viewer's own votes, looked up by `(page, user_id)`: the cost of a view does not grow with the number of
votes. The last statement of `schema.sql` recounts every tally from the votes, so re-applying the schema repairs any
drift and counts votes cast before the table existed. Apply the schema before deploying a Worker that needs it.

| Request | Answer |
|---|---|
| `GET api/login?return=<path>` | 302 to GitHub's authorize URL (no scopes; `redirect_uri` = `api/callback`). Sets the login-state cookie. `return` is kept only if it is a page of this site, else `/art-crit/`. |
| `GET api/callback?code&state` | Checks `state` against the login-state cookie, exchanges the code, reads the GitHub profile, drops the token, sets the session cookie, 302 to the saved page. A declined sign-in returns there with no session; a bad or expired state is 400, GitHub failing 502. |
| `POST api/logout` | Clears the session cookie. |
| `GET api/votes?p=<slug>` | `{"user": {"login"}\|null, "totals": {"<run id>": {"hearts", "gold", "silver", "bronze"}}, "mine": {"hearts": ["<run id>"], "gold": "<run id>"\|null, "silver", "bronze"}\|null}`. `totals` has an entry for every run of the page, `mine` is `null` signed out. Public, `Cache-Control: no-store`. |
| `PUT api/heart` `{"p", "run", "on": true\|false}` | Adds or removes the user's heart; idempotent. Answers like `GET api/votes`. |
| `PUT api/medal` `{"p", "medal", "run": "<id>"\|null}` | Puts the user's medal on `run` (`null` takes it back). In one transaction it removes that medal's old result and any other medal the user had on `run`. Answers like `GET api/votes`. |
| `POST api/request` `{"prompt", "kind", "note"?}` | Opens a GitHub issue on `fenderog/art-crit` (see Prompt requests) with `GITHUB_ISSUES_TOKEN`, a fine-grained token with Issues: write on that repo; answers `201 {"number", "url"}`. Body ≤ 8 KiB; `prompt` 10–4000 chars after trimming, `kind` one of `media`/`godot`/`web`/`blender`, `note` ≤ 1000 (400 otherwise). 5 per user and 50 site-wide per rolling 24 h (429). GitHub refusing is 502 and counts nothing; without the token 503. |

Cookies are `__Secure-` prefixed, `HttpOnly; Secure; SameSite=Lax`, `Path=/art-crit/api/`: the session (30 days) and the
login state (10 minutes) are JSON payloads signed with HMAC-SHA-256 (`SESSION_SECRET`) and typed so one can't stand in for
the other. Writes (`PUT`, `POST`) need a valid session (401), an `Origin` header equal to the request's own origin (403;
sandboxed game frames send `null`), `Content-Type: application/json` (415), a body under 2 KiB (8 KiB for `api/request`) (413), and for votes a page and run
that exist in the published `page.json` (404 for the page, which must come back as `application/json`, 400 for the run
or a bad slug/medal/flag). Errors are
`{"error": ...}`; no response sets CORS headers. Without D1 and the three secrets (`GITHUB_CLIENT_ID`,
`GITHUB_CLIENT_SECRET`, `SESSION_SECRET`) every route but 404 answers 503.

Viewer (`docs/assets/votes.js`): `loadVotes(slug)` fetches `api/votes` alongside `page.json` (4 s timeout) and returns a
store, or `null` when the API doesn't answer (static hosts, `art-crit serve`), in which case no vote UI is drawn. The
header shows `@login · Sign out` or `Sign in with GitHub` (`renderAuth`). `voteBar(store, runId)` is a labelled
"Community" row of `♡/♥ n` and `🥇 n 🥈 n 🥉 n` buttons (`aria-pressed` = yours, a count only when above 0). Signed out, a
click goes to `api/login` and comes back to the same URL; signed in, it writes and every bar of the page redraws from the
answer, since a medal moves between results. A failed write shows `not saved: <reason>`. The bar is on grid and compare
cards (inside the metrics row, at its bottom so the rows line up across cards, and so a card stays three grid rows), on the run page under the stat tiles, and in a table
row's expanded detail. It is separate from the owner's `rank-chip`.

## Deployment

The `art-crit` Pages project follows GitHub `fenderog/art-crit`'s `main` branch. Build command:
`python3 cloudflare/prepare.py`; output directory: `cloudflare-dist` (project root: repo root).
`art-crit publish` commits and pushes `docs/`; that push triggers Pages. Run the build locally to
check upload limits before publishing. `docs/` remains the source of truth and the local server uses
it directly; `cloudflare-dist/` is gitignored. Each `engines/<sha12>/godot.wasm` is gzip-compressed
as `godot.wasm.gz` with a deterministic header. Files over 25 MiB after staging abort the build.

Pages custom domains cannot mount at a path. A separate `art-crit-router` Worker (configured in
`cloudflare/wrangler.jsonc`, code in `cloudflare/router.mjs`) handles only
`fenderog.com/art-crit` and `fenderog.com/art-crit/*`. It redirects the bare path to the slash
and fetches static files from `art-crit.pages.dev` with `/art-crit` removed. For engine `.wasm`
URLs it fetches the `.wasm.gz` Pages asset and streams the decompressed bytes with
`Content-Type: application/wasm` and `Access-Control-Allow-Origin: *` (the iframe's origin is
opaque). Pages ignores MP4 `Range` requests, so the Worker synthesizes HTTP 206 responses for
normalized videos (≤2 MiB) to support Safari. Every response under `data/` (model-made games, packaged pages, SVGs)
carries `Content-Security-Policy: sandbox allow-scripts allow-pointer-lock`, the viewer's iframe sandbox as a header: a
direct visit to a raw output URL gets an opaque origin too, so it can't use the site's cookies or call the votes API
(ADR-0004). `docs/404.html` makes Pages answer missing paths with 404 instead of `index.html` + 200 (it is plain, with no
assets, because it is served at any depth). `docs/_headers` is Pages' cache policy (ADR-0029): run directories
(`/data/:slug/runs/*`) `max-age=86400, stale-while-revalidate=604800`, `assets/vendor/*` and `engines/*` a year and
`immutable`; everything else keeps Pages' `max-age=0, must-revalidate` (the viewer's own scripts have no cache-busting,
ADR-0012). The Worker passes these headers through. No other path is routed; static requests forward no visitor credentials. `/art-crit/api/*` is the
votes API (see Community votes). The apex has a
proxied DNS record to make Worker routes active, but no site at `/`. GitHub Pages can stay online
at its old URL during migration; the Pages subdomain isn't the supported URL for playing games.

## Viewer (docs/)

### Lanes design (index.html, page.html, compare.html; ADR-0030)

The three main views are the lanes design: `docs/assets/lanes/{index,page,compare,common,lane,request}.js` and
`lanes.css` (layered on `style.css`). They reuse the shared modules below, so rendering, sandboxing and votes behave as
described there. The previous views live unchanged in `docs/classic/` (`<base href="../">`; base-uri `'self'` there),
and each lanes page links to its classic counterpart ("classic view").

- **Home**: a compact hero; the newest prompt as a featured card whose picture is a slideshow (crossfade every 4.5 s,
  paused on hover/focus, in background tabs and under reduced motion) of up to four runs from different models (then
  vendors) at the page's highest effort level, then the next level down; its prompt in a handwritten system font. Then
  "All prompts": kind filter pills with counts and image-first tiles. Each prompt's cover is one of its highest-effort
  runs that made its output, avoiding models (then vendors) already used for an earlier cover. Covers never face away
  from the viewer: a run's picture can be swapped or dropped in `covers.json` (see Covers).
- **Page**: a strip with the page thumbnail, title, kind, counts, the prompt (two lines) and a "View final prompt"
  modal (with reference images), plus Cheapest/Fastest/Fewest-tokens tiles; sticky vendor/effort filter pills and an
  effort sort (`?vendor=`, `?effort=`, `?sort=effort-desc`); one lane per model ("Vendor – Model"), vendors by best rank
  then name, runs by effort. A lane slides by whole cards with ‹ › and can be dragged (with momentum, no snapping;
  drags never start on a 3D stage, form control or a video's controls). Cards (320 px) show the output uncropped at
  the card's width (every card in a lane equally tall, the picture at the top), a 44 px checkbox, the thumbnail pill
  at the bottom of the media area, the model, effort, time/tokens/cost (best in green), and the vote row ("Your vote:",
  inactive without the vote API). A click anywhere on the media opens the run (videos show their poster without
  controls on cards). Checked runs fill a bottom tray (thumbnail, model, vendor · effort, remove) with "Compare in
  detail →" from two runs.
- **Compare** (`?p=<slug>&r=<id>,<id>…`, at least two): back link, title, the page line, prompt and final-prompt modal,
  winner pills, and one equal-height column per run: the output uncropped, vendor logo, model, effort, vote buttons,
  and Time/Tokens/Cost bars scaled to the largest value (best in green; an unreported cost is "n/a").

All four page views use `loadPage(slug)` in dom.js: one fetch of `page.json`, which includes
`runs` sorted by started_at then effort order with ranks applied. `run.json` stays the rebuild source of truth;
`art-crit list` reads `page.json.runs`. Rebuild removes legacy `results.json`. The loader owns missing-page
parameters and fetch-error messages; run/play find their run by id in `page.runs`.

All five viewer documents enforce a meta CSP: `default-src 'self'; script-src 'self'; style-src 'self';
img-src 'self' data:; media-src 'self'; connect-src 'self'; frame-src 'self'; object-src 'none';
base-uri 'none'`. page, run and compare (the three that can show a 3D model) add `blob:` to `img-src` and `connect-src`:
three.js's GLTFLoader decodes a .glb's embedded textures through blob: URLs the page itself creates. Dynamic styles use CSSOM properties. The transcript lazily loads local Marked 15.0.12
and renders lexer tokens to DOM nodes with textContent, never innerHTML. Raw HTML stays visible text;
links permit only HTTP(S), and remote Markdown images stay alt text to avoid outside requests.

Shared conventions: runs are ordered by model, then effort from minimal to max (`EFFORTS` in runs.js), not
alphabetically. Effort is shown as a pill whose text is just the level, with a 6-step meter. Model ids show the model
name in bold and the provider prefix quietly (`modelLabel()`). Runs are grouped by vendor with a faint tint and a thin
stripe in the vendor's hue on table rows (page.html) and compare cards (`vendorOf()`/`vendorAttrs()`: the first segment of the
model id up to `-`, or the second after `openrouter/`; sets `data-vendor` and `--vh`). It is color only, so it works under any
sort; runs of one vendor sit together in the default model order. "Best" means the lowest cost, duration or total tokens
among runs that made their output (`!isFailed()`: neither a failed agent nor a failed output step ever wins; a cost of 0
is unreported and never wins), only when at least two runs compete (`rankBy()`); it's marked in green
with ★. Styling is one token set on `:root` (light) redefined under `prefers-color-scheme: dark`, system fonts only.

Your ranking (`run.rank`) is shown as 🥇🥈🥉 then `#4`, `#5`… (`rankLabel()`/`rankChip()`): in the runs table's Rank
column, on gallery cards, compare cards and the run title. When any run of a page is ranked, the table
sorts by rank by default, and the gallery and compare order ranked runs first (`byRankThenModel()`). Under `art-crit serve`
(`canEditRanks()`), the Rank column holds a `<select>` (– or 1…N) per row, and each change saves the whole page's ranking
(`saveRanks()`), with a status line next to the run count; a failed save reverts the select and shows the error. Data
JSON is fetched with `cache: "no-cache"` so a saved ranking or a new publish is never hidden by the browser cache.

All output rendering goes through one function, `renderOutput(run, base, opts)` in output.js (the click-to-play frame, the
immediate sandboxed frame, the media gallery, or the "no output" message, with the kind step's own error above it) and
one `KIND_UI` table (chip label, tab label, no-output text and failure badge per kind); page, run, compare and play all call
them. Any output with an `entry` is shown in the sandbox, so a new kind needs no viewer code. An output with `text`
(the text kind) is Markdown: cards (`compact`) show its `title` and `excerpt` as text in a 4:3 tile linking to the run
(nothing is fetched), the run page reads it in full, and anything else (the lanes compare columns, expanded table rows)
shows the full article in a scrollable box. It is rendered only by `renderMarkdown()` (raw HTML stays text, ADR-0015),
never through innerHTML or a frame; `isPlayable()` is false for it and cards have no ↗ pop-out. A text page has no
picture, so the lanes home shows its highest-effort run's text tile instead.

Wherever a run is one of many (home cards, the runs table and grid, compare cards, the click-to-play overlay) the viewer
shows thumbnails: `run.thumb`, and on a media card each item's `thumb` (`mediaElement(..., {compact: true})`); the run
page's gallery shows the files themselves (ADR-0029). Each HTML page's head lists `<link rel="modulepreload">` for every
module its script imports, directly or indirectly (plus the transcript modules run.html and monitor.html import on
demand; never the three.js bundle), so the module graph loads in one round trip; `tests/test_cli_site.py` derives the
lists from the `import` statements and fails when they drift.

- **classic/index.html** (the previous home, ADR-0030): cards per page (thumb, a Game/Vector chip, title, one icon per model vendor (OpenRouter's provider icons, vendored under `assets/vendor/icons/`; its models on hover), n_runs, updated date) → page.html. Under `art-crit serve`, also the prompt requests (see Prompt requests) and a "Runs (local)" link to monitor.html (see Run monitor).
- **classic/page.html**: title, a details sidebar with a meta line (kind, n runs, n models), the Prompt (prompt.md) and a collapsed Final prompt,
  then **highlights**: the cheapest, fastest and fewest-tokens run among those that made their output (each links to it; a cost of 0 means unreported and never ranks) plus verified count, failed
  count and total spend. Then a runs table (thumb, rank, model, effort, harness,
  verified ✓/✗ (`output.verified`), run at (the run's `started_at`, local time, year on hover; in the phone cards a line under the metrics), duration, tokens total/reasoning, cost, tool calls). Harness shows "pi 0.87.1" (name only
  when version is null, "–" when missing).
  A `media` page also has a **Gallery** above the table: one card per run (its thumb, effort, model, cost, duration,
  "N files" when more than one), linking to the run. Expanding a media row shows its outputs. A run whose `state` isn't `complete`
  shows a red `failed`/`timeout` badge in the Verified cell (and a red edge on its row), and its expanded row shows `error`. A completed run
  whose output step failed shows a red "export failed" / "packaging failed" / "output failed" badge there instead of a check mark, still counts
  as completed in the highlights, and its expanded row shows `output.error` above "No playable build recorded for this run.".
  The table is sortable (default: model, then effort), numeric columns are right-aligned with a thin bar under the value
  scaled to the column max, the best completed value in duration / tokens / cost is starred, and every header has a help
  tooltip (shown after 0.5s). Clicking a row expands it and boots that run's game inline; clicking again removes it.
  The Harness cell shows the name with the version small underneath. At ≤720px the table turns into a list of cards
  (headers become sort chips; harness and reasoning tokens are hidden). Above that it never scrolls horizontally: the full
  table fits the 1240px page, and below it columns hide by priority: Reasoning at ≤1199px, Harness and Tool calls at ≤959px, the thumbnail at ≤799px. Model, Effort, Run at, Verified, Duration and Cost (plus
  the rank, caret and Tokens) always stay; hidden metrics are on the run page's Metrics tab and in compare.
  (`.table-wrap` keeps `overflow-x: auto` as a safety net only.) Model names with a pinned upstream wrap inside their cell.
- **run.html**: a header with model and effort; a collapsible details sidebar (as on page.html) with the provider, stat tiles (cost, duration, tokens, output tokens, tool calls, turns) each with the run's
  rank among the page's runs that made their output ("cheapest of 6", "3rd of 6"), a line with verified (`output.verified`), harness,
  started (plus the failed/timeout badge for the agent and an "export failed" / "packaging failed" / "output failed"
  badge when the output step failed), and the agent's `error`. Then tabs (the open tab is kept in the URL hash, e.g. `#transcript`; Transcript and
  Source show a count):
  - *Game*: click-to-play overlay (shows thumb). On click it inserts
    `<iframe sandbox="allow-scripts allow-pointer-lock" allow="fullscreen; autoplay; gamepad">` pointing at `output.entry`.
    There's also an "Open full screen ↗" link (link to `play.html`, which boots it in the sandbox).
  - *Transcript*: renders `session.conversation`. System prompt collapsed. User text. For each assistant message:
    thinking (collapsed, toggle "show thinking"), text (markdown), and toolCall blocks paired with their toolResult by
    `toolCallId`. Tool display: `bash` → command + output, `write` → path + content, `edit` → path + old/new blocks,
    `read`/`ls` → args + output. Any block past 20 lines or 4000 characters starts collapsed behind a toggle: output ("Output (N lines)"),
    a written file ("File (N lines)"), an edit's diff, other tools' arguments, and a bash command (its first line shown).
    An image in a tool result is shown as an `<img>` thumbnail (a data: URL, only for
    jpeg/png/gif/webp with plain base64 data, never SVG) captioned `[image: <type>, N KB]`, never as text.
    `isError` gets a ✗ badge. Show `+m:ss` since session start (the clock time on hover) and per-message token usage. A tool's duration is the `durationMs` on its `toolResult` message (when present). Filter buttons: all / tool calls / errors.
  - *Output* (instead of Game, for a `media` run): every `output.items` entry as a captioned figure (file name, size, duration,
    bytes, a `download` link), one per row at its recorded `width`×`height` (never wider than the page). Images, **SVGs included**, are only ever shown with `<img>` (which never runs an
    SVG's scripts), never inlined or put in an object/embed/iframe, and never linked for viewing on this origin.
    Videos use `<video controls preload="none">` with the poster, and never autoplay. A `model` item (blender) is a
    "View in 3D" button over the run's first render; the click loads the vendored three.js bundle
    (`assets/vendor/three-gltf.min.js`, three 0.186.1: GLTFLoader, OrbitControls, RoomEnvironment) once and the .glb into
    a 4:3 orbit/zoom/pan view (`model.js`, rendered on demand, animations looped; its WebGL context is freed when the card
    is redrawn). Its caption adds the triangle count. Galleries are chosen by `output.items`, not by kind name.
  - *Page* (instead of Game, for a `web` run): the packaged page with click-to-play, in the same sandboxed iframe as games.
  - *Read* (instead of Game, for a `text` run, chosen by `output.text`): the Markdown fetched (`getText`, `no-cache`) and
    rendered by `renderMarkdown()` into an `<article class="prose">` at a ~70ch measure, with the word count, size and a
    `download` link under it. markdown.js is loaded with a dynamic `import()` on first use. No full-screen link (nothing
    to play) and no cover buttons (no picture).
  - *Source*: a file list, and clicking a file shows it in a `<pre>`. The first code file opens right away.
  - *Metrics*: all metrics as a table of raw values (with a readable form beside durations, costs and big counts,
    including Harness, State, Error and the output's ok / verified / error), plus links to download the raw session files.
- **classic/compare.html**: one card per run (all runs of the page by default), laid out as a grid of ~380px columns that wraps
  into rows (3 across at desktop width, 1 on phones, never sideways scrolling), ordered by model then effort. Each card has
  the model, its effort pill (plus the failed/timeout badge), one line with harness, duration, tokens and cost (the best
  among the shown runs starred), and its game with click-to-play (each column boots independently, never automatically),
  or for a `media`/`blender` run one output as the hero with a strip of thumbnails that swap it (a video or 3D model is the
  hero when there is one; the Play all button is hidden when there are no games and never opens 3D views). An image hero links to the run page (`a.media-link`); a video hero doesn't, so a click plays it. page.html's
  Grid view draws the same cards (`renderRunGrid()`).
  Cards are subgrids spanning three grid rows (heading, metrics, output), so those line up across a row even when a metrics line wraps.
  Cards are grouped by vendor (`groupByVendor()`, `vendorOf()`): a section per vendor with a quiet header (name from
  `VENDOR_NAMES`/`vendorName()`, run count, thin rule in the vendor's hue), always shown, even with a single vendor. Within a
  group the order is `byRankThenModel()`; groups go by their best rank, then unranked groups by name. Each group is its own
  grid, so the subgrid rows line up per group. The ★ best values are still computed across all shown runs, and `&r=` only
  limits which runs (and so which groups) appear. `#columns` holds the groups, not the cards.
  A card with output also has a small ↗ button (`a.popout`, next to the effort pill) that opens `play.html` for that run in a
  separate popup window (`window.open(..., "popup,noopener,width=1280,height=800")`); middle/cmd-click falls back to the
  `href` and opens a tab. It never carries `data-play`, so Play all ignores it.
- **play.html**: one run's output alone. A 36px bar (model, effort pill, state badge, "Run page →" link to run.html) above
  the output, which fills the rest of the window: for `godot`/`web` runs one `sandboxedGame()` iframe that boots immediately
  (opening the window was the click), for `media` runs `mediaGallery()` (videos still don't autoplay). A run's `error` is
  shown above the output; a missing/unknown `p`/`r` or a run without output shows a message. Never links or embeds the raw entry URL.
- **monitor.html**: local only (see Run monitor), reached from the "Runs (local)" link the home page adds under
  `art-crit serve`. On the published site (or any plain file server) it shows a "local only" note and makes no requests.
- Everything renders from the JSON. There are no per-page HTML files. It must work under a sub-path (`/art-crit/`),
  so use only relative URLs. It supports dark mode via `prefers-color-scheme`, has readable defaults, and has no frameworks.

## Tests (`uv run pytest`)

- CLI: unit tests plus an end-to-end import of a small synthetic batch directory (run directories with `run.json`,
  `work/`, `harness/`, `output/`). The fixture uses tiny fake engine
  files and a real Godot `index.html` template, and covers dedupe, the html rewrite, cleaning, the secret abort and
  redaction, idempotency, rm, and rebuild.
- Viewer: Playwright (Python, `channel="chrome"`, which uses the installed Google Chrome, so no browser download)
  against `art-crit serve` on a fixture site. It covers each page rendering without console errors, click-to-play inserting
  a sandboxed iframe, the transcript's tool calls and error badges, and compare with 3 runs. A `media` fixture page
  (`art`: an SVG with an embedded script, a PNG and a 1 s mp4) covers the gallery, the Output tab (the SVG's script
  never runs, videos don't autoplay), expanded rows and compare. A routed `blender` page (a one-triangle .glb and a PNG,
  in a Chrome with SwiftShader WebGL) covers the click-to-view card (nothing loads before the click) and the run page.
  Also covered: effort-order sorting, the highlights (a failed run never wins "cheapest"), best-value stars, the run
  page ranks, the linkable tab hash and the Source tab opening its first file.
- `art-crit run`: a fake `pi` (a Python script put first on PATH by the test) that answers `--version`, `--list-models`,
  the RPC levels request, and `-p` runs by writing a canned session file and a tiny project; env vars make it fail,
  hang, or exit non-zero. Covers level parsing (`all`, ranges, explicit lists, off excluded by default, unsupported
  level → error before anything starts), the plan/confirmation, `-j`, timeout, failed runs being imported, metrics
  against the real voxel-horse `high/session.jsonl` numbers (when present), and `--resume` not rerunning finished
  agents (and retrying a failed output step), a toy kind defined in a test running end to end, and the run directory layout. For a media brief the fake pi writes `./output/` (SVG, PNG and an ffmpeg-made mp4) plus a script and a
  leftover binary frame; with `FAKE_PI_BAD_OUTPUT` it adds an unreadable PNG (the step's error) and a text file in
  `./output/` (published as source, not an error). `tests/test_media.py` checks the media step on ffmpeg-generated inputs (trim + re-encode,
  oversized image → JPEG, bad files, empty output, too many files, name clashes, non-media files being skipped); media tests are skipped without
  ffmpeg. `tests/test_blender.py` covers the .glb check, the per-run Blender session against a fake `blender`
  (tests/fixtures/fake_pi/blender, which only listens on its port), each harness's MCP flags, harnesses without MCP being
  refused, and a full blender run (the fake pi records the `.pi/mcp.json` it got and writes a .glb + PNG; with
  `FAKE_PI_BLENDER_LIVE=1` it drives the real Blender MCP server instead, a manual end-to-end check without a model).
  A slow test (skipped without `godot`) exports a tiny real project. No test calls a real model.
  For a web brief the fake pi writes `index.html`, `main.js`, `style.css` and a fake npm package in `node_modules/`.
  `tests/test_web_kind.py` (skipped without esbuild) packages pages with the real esbuild (module + inline module +
  classic scripts, stylesheets, imported assets, `</script>` escaping, remote/importmap left alone, missing imports and
  paths outside the project), and verifies offline in the sandbox (a remote fetch and localStorage both fail it).
  For a text brief the fake pi writes `./output/essay.md` (plus `notes.md` outside it; `FAKE_PI_BAD_TEXT` adds a second
  .md). `tests/test_text.py` covers finalize (none, two files, oversized, undecodable, blank), verify, title, words and
  excerpt, staging from the cleaned copy, `keep_source`, and a full `run --kind text` (plus rebuild, list, rm and the
  one-kind-per-page check). A routed `text` page in test_web.py covers the run page's article (a raw `<script>` stays
  text and never runs), the excerpt tiles on the home and page cards, and compare reading each text in full.
