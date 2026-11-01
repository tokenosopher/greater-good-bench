# Greater Good Bench

Greater Good Bench is a benchmark of what AI models make for the greater good, measured by people rather than by a score.

A public benchmark that asks frontier AI models one question: **can they make something that, if everyone saw, read,
used, played or watched it, would improve the world for the greatest number of people?** What gets measured in AI gets
optimized, and nobody measures this yet, so this starts measuring it.

v1 is deliberately simple: generate, verify, and show the outputs side by side. There are six tasks, one page each:

| Page | The model makes | Kind |
|---|---|---|
| SVG | an SVG image | `media` |
| Website | a web page | `web` |
| 3D model | a Blender model (`.glb`) with renders | `blender` |
| Game | a Godot game, playable in the browser | `godot` |
| Animation | a short video (10 s cap) | `media` |
| Essay | a piece of writing | `text` |

The prompts, the model set and the exact command for each page are in [prompts/README.md](prompts/README.md)
(the prompts there are placeholders until the owner supplies the final ones).

- **No automated judging.** No LLM judge, no score, no rubric: the ranking is the owner's own ranking plus community
  votes, next to every run's full transcript, time, tokens and cost.
- **The harness is part of the result.** Every run records the harness (the agent program) that produced it, with its
  tools and effort level, and comparisons only make sense between comparable harness configs: the same harness, tools
  and limits for every model on a page.
- **Only the newest frontier models**, run at the effort levels the batch names.

**Live site:** https://tokenosopher.github.io/greater-good-bench/ (GitHub Pages, from `main:/docs`; there the votes
and the request form fall back to GitHub's new-issue page). Cloudflare is the planned home, for community votes and a
custom domain: [DEPLOY.md](DEPLOY.md) is the step-by-step checklist.

## Based on art-crit

This is a fork of [art-crit](https://github.com/fenderog/art-crit) by fenderog, a crit for LLMs that runs visual and
spatial prompts across models and shows the results side by side (live at https://fenderog.com/art-crit/). The CLI,
the site, the kinds, rankings, votes and harnesses are all art-crit's: this fork changes what the site asks, not how it
works. The command is still `art-crit`, and everything below is art-crit's own usage, kept as it is.

This repo is two things: the `art-crit` CLI in `src/art_crit/` (plain Python, stdlib only) and the
site in `docs/` (plain JS, no viewer build step, hosted on Cloudflare Pages). The CLI
writes files to `docs/`; the site renders them. A small deploy build compresses the shared Godot
engine to fit Pages' file-size limit. [SPEC.md](SPEC.md) is the full contract.
[AGENTS.md](AGENTS.md) is where coding agents should start.

## What you'll see on the site

- **Home:** one card per prompt — called a *page* — labeled Game, Vector, or Web, with its models and run count.
- **Page:** the prompt, the exact brief the agents saw, a summary (cheapest, fastest, fewest
  tokens, how many passed checks, total spend), a gallery for Vector pages, and a sortable runs
  table. Effort is a meter, best numbers get a star, your own ranking comes first. Click a row
  to play the game or open the files. On phones the table collapses into cards.
- **Run:** the output front and center, quick links to the same prompt's other runs, stats in
  context ("cheapest of 11"), and tabs for transcript, source, and metrics. The transcript shows
  every tool call with errors and edits called out. Tabs are linkable (`#transcript`).
- **Compare:** all runs for a prompt in one grid, with outputs, key numbers, and stars for the best.

Safety notes, briefly: games only start when you click, inside a sandboxed frame. Fullscreen
uses the same sandbox via `play.html`. Model-made SVGs render as images only, so embedded scripts
never run. The viewer ships its own assets (including the Markdown parser) and runs under a
same-origin CSP. Light and dark mode both work.

## Run a benchmark

```sh
uv run art-crit run "a spinning low-poly windmill in a small field" -m openai-codex/gpt-6-sol:low..high
```

That spins up one agent per model × effort level, in parallel, on your machine. When they finish,
their work is packaged and checked where a check exists. Failures and timeouts are kept too —
they're part of the comparison. Each run is published as it lands: imported, committed and pushed to
`main` (Cloudflare Pages builds on each push), so a long batch fills up the live site while it runs.
Pass `--no-publish` to import locally only and push later with `art-crit publish`.
If any jobs have problems, a final summary lists each model/effort, the failure stage and reason, and
where to find its full logs. This includes timeouts, output/verification failures, and unrecovered publishing errors.

A few things worth knowing:

- `-m MODEL[:LEVELS]` repeats. Levels look like `low,high`, `low..max`, `all`, or `off`.
  Leave the suffix off and you get every level except `off`. `-e LEVELS` sets the fallback for
  models without one.
- Leave `-m`/`--set` out (or add `-i/--pick` to select on top of them) and it asks before planning:
  pick a harness, then its models, then the levels for each one. In the model list, numbers select and
  any other text is a fuzzy search (`claudeop55`, `g6sol`) that filters and renumbers the list. A catalog
  with more than 20 models is not printed up front: search first (listings show at most 20 matches), or
  type `list` if you really want the whole catalog.
  The picks become ordinary `-m` specs, so the plan and the up-front validation are exactly the same.
- Models and levels are validated up front, so a typo fails before you spend anything.
  `art-crit models [SEARCH]` shows what's available.
- You'll see the plan and confirm it. `-n/--dry-run` prints the plan and stops.
  `-y/--yes` skips the prompt for scripts.
- Useful flags: `-p/--page` (alias `--slug`: the page slug, default taken from `--title` if given, else the prompt; for an existing page it reuses the page's prompt, kind and references), `-t/--title`, `-j N` (how many agents at once),
  `-T/--timeout 30m`, `-b/--brief FILE` (your own brief template, `{prompt}` is your prompt),
  `-R/--ref FILE` (a file in the project's `references/` folder, e.g. `--ref robie.jpg`; repeatable; each agent gets a copy in `./references/` and the brief points to it; the files are published with the page and shown as thumbnails beside the prompt. Adding runs with `--page` reuses the page's published reference files, so a "use the reference image" prompt can't run without one — pass `--ref` to replace that set),
  `--no-publish` (publishing each run is the default). `art-crit run -h` has the full list.
- Ctrl-C stops everything. `art-crit run --resume <batch dir>` picks up a batch without
  redoing finished agents.

Each agent starts in an empty `<run id>/work/` folder under `[run].dir`
(`~/dev/art-crit-runs` by default, configured in `art-crit.toml`) and gets your prompt verbatim
plus the fixed brief for that task type in `src/art_crit/kinds/<kind>.md`.

### Other agent harnesses

Default harness is [pi](https://github.com/earendil-works/pi). Prefix with `claude-code:` to use
[Claude Code](https://claude.com/claude-code) instead — you can mix both in one batch to compare
harnesses head to head:

```sh
uv run art-crit run "a voxel horse" -m claude-code:claude-opus-5-5:high -m openai-codex/gpt-6-sol:high
uv run art-crit models --harness claude-code
```

Claude Code models are `claude-fable-5-1`, `claude-opus-5-5`, `claude-sonnet-5-5`,
`claude-sonnet-5`, and `claude-haiku-4-5` (`fable`, `opus`, `sonnet`, `haiku` work as shorthand),
at low, medium, high, xhigh, or max. Runs are single agents with file and shell tools only —
no subagents, web access, skills, scheduling, CLAUDE.md, memory, plugins, hooks, or MCP servers.
It uses your login, and cost is Claude Code's API-price estimate, subscription included.

[Antigravity CLI](https://www.agy.dev/docs/cli/headless/) (`agy`), [Grok Build](https://github.com/xai-org/grok-build) (`grok`), Muse Code (`muse`), Codex (`codex`) and OpenRouter's [Ori](https://openrouter.ai/ori) (`ori`) can also run headlessly:

```sh
uv run art-crit models -H agy gemini
uv run art-crit models -H grok-build grok-4.7
uv run art-crit models -H muse-code muse-spark
uv run art-crit models -H codex gpt-6
uv run art-crit models -H ori deepseek      # OpenRouter's catalog, live
uv run art-crit run --kind media "draw a circle" -m agy:gemini-3.8-flash:high -m grok-build:grok-4.7:low
uv run art-crit run --kind media "draw a circle" -m muse-code:muse-spark-1.3-contributor:high
uv run art-crit run --kind media "draw a circle" -m codex:gpt-6-sol:high
uv run art-crit run --kind media "draw a circle" -m ori:deepseek/deepseek-v4.1-flash:high
```

Agy's model slugs already encode effort: `agy:gemini-3.8-flash:high` selects `gemini-3.8-flash-high`. Agy does not report cost (shown as 0, **unknown**, not free). Grok reports cost when the server supplies it; a missing cost is also shown as 0. Grok disables subagents and web and restricts built-in tools; MCP meta-tools may still load from your configuration. Agy does not offer a safe-mode/tool allowlist, so for strict comparisons run it with an isolated CLI profile. Muse Code runs without approval prompts or sandbox but with web tools and background reminder agents off; for models with published [Meta API rates](https://dev.meta.ai/docs/pricing-rate-limits), cost is an API-equivalent estimate marked `~` (not subscription spend). Muse Wonder Full and Wonder Contributor have no published API rate: their cost uses Wonder Standard's rate as a **proxy**, marked `≈` (not Full's real price). Models with no known rate show 0, meaning unknown, not free. Re-import older Muse run directories to estimate their already-recorded token usage. Its model list is the catalog `muse` caches (open `/model` in `muse` to refresh it), and its transcript appears when the run finishes, so live progress shows 0 until then. Codex runs with approvals and sandbox bypassed and your `~/.codex` config/rules ignored; its model list comes live from `codex debug models` (the `ultra` effort tier isn't offered, it isn't one of art-crit's levels), and it does not report cost (0, **unknown**, not free). Ori runs its own runtime agent against OpenRouter's models: any slug from OpenRouter's catalog (image/video models excepted) at `off`, `minimal`, `low`, `medium`, `high`, `xhigh` or `max` when the model takes a reasoning effort (`off` only otherwise), with OpenRouter's own cost recorded. It also loads your `~/.ori` configuration (MCP servers included), so for strict comparisons run it with isolated Ori configuration.

### Pinning an OpenRouter provider

For `openrouter/` models, `@slug` locks the run to a specific upstream provider, so you can put
the same model on two providers on the same page:

```sh
uv run art-crit run "a voxel horse" -m openrouter/deepseek/deepseek-v4.1-flash@deepinfra/fp8:low \
                   -m openrouter/deepseek/deepseek-v4.1-flash@fireworks:low
```

Slugs are OpenRouter endpoint tags, variants included (`deepinfra/fp8`, `fireworks/us`). Find them with
`curl -s https://openrouter.ai/api/v1/models/<model id>/endpoints`. Comma-separate to let OpenRouter
choose within your list (`@deepinfra,fireworks`). Pinning disables fallbacks, so the name on the run
is what actually served it — recorded in the model name (`…flash@deepinfra`, shown as a `via …` chip)
and in `route.requested` / `route.served` on the Metrics tab. Works in `-m`, `--set`, and set files;
`@` anywhere else is an error.

On cost: OpenRouter runs report what OpenRouter actually charged per response, not pi's estimate.
pi prices every OpenRouter call at one catalog rate, which ran 2–7× low in practice. Both figures
are on the Metrics tab (`route.cost_usd`, `route.pi_cost_usd`) alongside what served the run
(`route.served`). With BYOK (your own provider key), the reported cost is just OpenRouter's fee.

### Add runs to an existing page

Grab the page slug from its URL (or `uv run art-crit list`), confirm the model ID and levels, then
pass `--page` and skip the prompt — the page's prompt and kind carry over:

```sh
uv run art-crit models deepseek
uv run art-crit run --dry-run --page an-svg-of-a-chair-holding -m openrouter/deepseek/deepseek-v4.1-flash:low
uv run art-crit run --page an-svg-of-a-chair-holding -m openrouter/deepseek/deepseek-v4.1-flash:low
uv run art-crit serve
uv run art-crit publish -m "Add DeepSeek run to chair page"
```

Real runs cost money; `--dry-run` is free. Bare `-m` means all levels except `off`. Existing runs,
the title, and your rankings are left alone; new runs arrive unranked, and re-importing a run ID
replaces that run. A page has one prompt, so passing a different one is refused — use
`--change-prompt` if you're deliberately rewriting it for the whole page.

### Model sets

If you reuse the same lineup, save it once and pass `--set NAME` (or `-s`):

```toml
# art-crit.toml
[sets]
cheap = ["openai-codex/gpt-6-luna:minimal,low", "openrouter/deepseek/deepseek-v4.1-flash:low..high"]
```

```sh
uv run art-crit run "a windmill" --set cheap
```

Entries take the same form as `-m`. `--set` also accepts a file (one `MODEL[:LEVELS]` per line,
`#` for comments). Sets compose with each other and with `-m`; `-e` fills in entries missing levels.

### The five kinds of pages

**Godot games** (`--kind godot`, the default) get exported to a web build and booted in headless
Chrome to prove they run. The engine (~38 MB) lives once in `docs/engines/` and is shared, so each
run adds only a few hundred KB.

**Vector: images and video** (`--kind media`):

```sh
uv run art-crit run --kind media "a pelican riding a bicycle, as a hand-written SVG" -m openai-codex/gpt-6-sol
```

The agent drops results in `./output/`: images (`.png .jpg .jpeg .webp .gif .svg`) and/or video
(`.mp4 .webm .mov`). Anything else there is ignored, though text files are kept as source. Limits
are 8 files, 2 MB each after processing, 10 seconds per video. The *how* is up to your prompt
("hand-written SVG", "use Python", …). The brief lists this machine's tools from `[run].tools` in
`art-crit.toml`, with versions. Afterward, rasters and video go through ffprobe and SVGs through an XML
parse; videos are trimmed to 10 s, re-encoded to H.264 mp4 if needed, and given a poster frame, and
oversized non-GIF rasters become JPEG. Good files still publish when others fail; per-file problems
appear on the run, and verification fails if any image or video is unreadable or over the limits.

**Web pages** (`--kind web`):

```sh
uv run art-crit run --kind web "a running voxel horse with three.js" -m openai-codex/gpt-6-sol
```

The agent writes `index.html` plus ES modules, `npm install`s what it needs (three.js, …), and imports
packages by name. esbuild then bundles local module scripts, stylesheets, and their imports, and inlines
local classic scripts as data URLs to preserve their globals — leaving you with a single `index.html`
(max 20 MB). Remote URLs and import maps stay untouched, but the check loads the page offline in the
same sandboxed frame the site uses. Anything fetched from outside, or any need for localStorage, fails
verification. `node_modules/` never ships.

**Blender models** (`--kind blender`):

```sh
uv run art-crit run --kind blender "a low-poly fox sitting on a rock" -m claude-code:opus:high -m openai-codex/gpt-6-sol:high
```

Each run gets its own windowless Blender, and the agent works in it through the official
[Blender MCP server](https://projects.blender.org/lab/blender_mcp): it runs `bpy` code, searches the API docs, and
renders to check its work. It saves a `.glb` of the model (≤ 15 MB, no Draco/meshopt compression) and renders (`.png`/`.jpg`)
in `./output/`. Renders go through the media checks, and the `.glb` must be a glTF 2.0 binary the viewer can read.
On the site a model is a "View in 3D" button over its render that opens an orbit/zoom/pan view (three.js). Every
harness can run it: pi, Claude Code, Codex and Grok get the server per run; agy and Muse only read a global MCP
config, so each holds one permanent `art-crit-blender` entry (a proxy that has no tools outside art-crit runs). The first batch installs the
add-on into `~/.cache/art-crit/` (your own Blender isn't touched) and fetches the server with `uvx`.

**Text** (`--kind text`):

```sh
uv run art-crit run --kind text "a short essay on why chairs have four legs" -m openai-codex/gpt-6-sol
```

The agent writes one Markdown file in `./output/` (any `.md` name, at most 200 KB, UTF-8); anything else there is
ignored, and notes or drafts kept outside `./output/` are published as source. The file is published as is (cleaned
and secret-scanned like source) and the site renders it as a readable page with its own Markdown renderer: raw HTML
stays visible text and nothing in it runs. Cards show the title and an excerpt instead of a picture. No tools are needed.

One kind per page: you can't add a Vector prompt to a Godot page, and so on.

## Rank runs

Rankings are yours, done in the browser:

```sh
uv run art-crit serve        # open http://localhost:8000, pick a page
```

Under `art-crit serve`, each runs-table row gets a picker (– or 1st, 2nd, …, ties fine). It saves to
`docs/data/<page>/ranking.json` as you go. `art-crit publish` puts it online read-only: ranked runs
sort first and show 🥇🥈🥉 (then #4, #5…) across the page, gallery, compare, and run views. The live
site can't write rankings — only your local `art-crit serve` can.

## Choose the thumbnails

The home page and cards pick pictures by default (a page's cover is one of its highest-effort runs; a run's
thumbnail is its first image). To override one, open a run page under `art-crit serve`: each image has **Use as run
thumbnail** and **Use as page cover** toggles (a game or page only has the cover toggle). Pressing a pressed toggle
clears it. Choices go to `docs/data/<page>/covers.json` (overrides only, so everything you don't set keeps its default);
`art-crit publish` puts them online.

## Request a prompt

The home page's top bar has a **Request a prompt** button: write the task, pick its kind and add an optional note.
On the deployed site, after signing in with GitHub, the request becomes an issue on `tokenosopher/greater-good-bench` labeled `prompt request`
([ADR-0030](adr/0030-lanes-design-and-prompt-requests-as-issues.md); setup under *Prompt requests* below). Anywhere
else (or before that setup) the button opens GitHub's own new-issue form with everything filled in.

The classic home page (`classic/index.html`, under `art-crit serve`) still keeps the older local list: requests saved
in `requests.json` beside `docs/`, gitignored and never published, each with the exact `uv run art-crit run …`
command to make it a page.

## Watch a run in progress

Under `art-crit serve` (only), the home page gets a **Runs (local)** link to a monitor of the batches in
`[run].dir`: every run's state, live cost/tokens/tool calls, its prompt, the files it has written and its
transcript so far. It refreshes every two seconds while something is running. A **Stop** button on a running
run kills that agent's process group and marks the run failed. None of this reaches the published site.

## Import runs

`art-crit run` imports its batch when it finishes. To re-publish a run or batch — say after `art-crit rm`:

```sh
uv run art-crit import ~/dev/art-crit-runs/2026-09-29-171151-create-a-rubik-s-cube-in-3js   # a batch
uv run art-crit import ~/dev/art-crit-runs/<batch>/<run id>                                  # one run
uv run art-crit serve                  # preview at http://localhost:8000, served like Pages
uv run art-crit publish -m "voxel horse: gpt-6-sol"
```

Options: `--page SLUG` overrides the recorded page, `--title` sets its title, `--dry-run` previews
without writing, `--redact` masks secrets instead of aborting, `--allow-threads` permits threaded
Godot exports (fullscreen-only playback).

Every import cleans first: hidden reasoning blobs and machine-specific keys go, home and volume paths
get rewritten per `[clean]` in `art-crit.toml`, then everything is secret-scanned. A hit stops the import
before anything is written.

## Retry failed runs

`art-crit retry <page>` runs the page's failed runs again: the same harness, model and effort, with the
page's own prompt, kind and references, published as each one finishes. A failed run is deleted once its
retry works; if the retry fails too, the old run stays and the command exits 1. Name run ids to retry only those
(`art-crit retry <page> <run-id>`), and use `-n` first to see the plan. Takes `-y`, `-j`, `-T` and `--no-publish` like `run`.

## Make videos for social media

`art-crit video <page> <run-id> <run-id> ...` (2 to 12 runs) writes animated vertical (1080x1920) and landscape videos that
compare them, cut for short-form feeds: a hook (every output on a moving wall, "6 AI models. Same prompt." and the prompt
typing out), then each run springing in with its number, model, effort meter and time, tokens and cost counting up (plus a
FASTEST / CHEAPEST / PRICIEST / SLOWEST sticker where one stands out), then "Place your vote on art-crit" over a
numbered grid of everyone (your #1 rank, if you ranked them, gets a crown). A synthesized beat and sound effects follow
the cuts (`--no-sound` for a silent track, to add a platform sound instead). Games and 3D models are recorded playing and
turning, SVGs and images get a slow zoom, and a run's own video plays. Pick layouts with `-l reveal|grid|wide` (default
all three) and the seconds per run with `-d` (default 4). Files go to `videos/<page>/`
(git-ignored, never published), and the command prints the site's compare link for the post (under `[site] url` in
`art-crit.toml`, which is also the address the vote cards show). Needs ffmpeg and
Playwright with Chrome (`uv tool install --editable '.[verify]'`).

**Video studio** (`art-crit serve`, then `http://127.0.0.1:8000/studio.html`, also linked from the home page and from each
compare page with its runs filled in): design one video in the browser. Pick a template (Head to head, Line-up, Wipe,
Effort ladder, Countdown, Grid montage), fill its slots with runs from any prompt, add title, question, section, vote or
credits cards in four looks, choose music (upbeat, lo-fi, cinematic or none) and whether to show labels, time and cost,
preview the timing, then Render. Renders appear under the settings with a preview and a download; the files go to
`videos/studio/`.

## Other commands

- `art-crit list` — pages and their runs.
- `art-crit rm <page> [<run>]` — delete a run, or a whole page.
- `art-crit rename <page> <new-slug> [-t TITLE]` — move a page. The title follows only if it came
  from the old slug, unless you pass `-t`.
- `art-crit rebuild` — regenerate indexes, drop unused engines.
- `art-crit publish [-m MSG]` — commit `docs/` and push. Cloudflare Pages builds from `main`.

Publishing to this site needs write access — otherwise you'll get a permission error. Without it,
fork and open a pull request.

## Cloudflare deployment

**For this fork, follow [DEPLOY.md](DEPLOY.md)**: it is the ordered checklist with the exact commands. The examples in
this section are the upstream art-crit's (`fenderog.com/art-crit`, a path on an apex domain, Pages project `art-crit`,
repo `fenderog/art-crit`). Here the site's address is set in one place, `cloudflare/wrangler.jsonc` (`routes` plus the
`vars` `SITE_PREFIX`, `PAGES_URL` and `GITHUB_REPO`); `SITE_PREFIX` is `""` for a host of its own (the default, a
placeholder `bench.example.com`) or a path like `/bench`. Read `/art-crit/` below as `<SITE_PREFIX>/`. The local video
tools take the same address from `[site] url` in `art-crit.toml`. The prompt-request issues go to `GITHUB_REPO`
(`REPO_ISSUES` in `docs/assets/lanes/request.js` for the fallback).

Cloudflare Pages follows `main` of `fenderog/art-crit` (project `art-crit`). Set its build command
to `python3 cloudflare/prepare.py`, output directory to `cloudflare-dist`, and root to the repo root.
The build copies `docs/` and compresses the shared Godot WASM for Pages' 25 MiB/file limit.
To validate locally: `python3 cloudflare/prepare.py` (output is gitignored). `art-crit publish`
then pushes new data to GitHub, which triggers a Pages deployment automatically.

Pages doesn't support a custom-domain **path**, and Pages can't stream the engine, so `cloudflare/router.mjs` runs as a
Worker on the address in `wrangler.jsonc` (upstream: only `fenderog.com/art-crit` and `fenderog.com/art-crit/*`),
stripping the prefix and streaming the
engine decompressed; it also supports video range requests for Safari, and serves everything under `data/` (model-made
games, pages and SVGs) with the viewer's iframe sandbox as a CSP header, so a raw output URL opened directly can't act on
the site's origin. Its config is `cloudflare/wrangler.jsonc`; redeploy the router after edits with
`npx wrangler deploy --config cloudflare/wrangler.jsonc` (Wrangler login required). The apex
has proxied DNS for the routes but no website at `/`. The Pages subdomain isn't meant for playing
Godot games. See [ADR-0021](adr/0021-cloudflare-pages-subpath.md) for the rationale.

### Community votes (one-time setup)

Visitors can sign in with GitHub and give results a heart and one gold, silver and bronze medal per page
([ADR-0022](adr/0022-community-votes.md)). Votes live in a Cloudflare D1 database behind the same Worker. Until this
is set up the Worker answers 503 on `/art-crit/api/*` and the site simply shows no vote controls.

1. **GitHub OAuth App** (GitHub → Settings → Developer settings → OAuth Apps → New): homepage
   `https://fenderog.com/art-crit/`, callback URL `https://fenderog.com/art-crit/api/callback`. Generate a client secret.
2. **Database**: `npx wrangler d1 create art-crit-votes`, then paste the printed `database_id` into
   `cloudflare/wrangler.jsonc` and uncomment its `d1_databases` block.
3. **Tables**: `npx wrangler d1 execute art-crit-votes --remote --config cloudflare/wrangler.jsonc --file cloudflare/schema.sql`
4. **Secrets** (each prompts for the value): `npx wrangler secret put GITHUB_CLIENT_ID --config cloudflare/wrangler.jsonc`,
   then the same for `GITHUB_CLIENT_SECRET` (from step 1) and `SESSION_SECRET` (any long random string, for example
   `openssl rand -base64 48`; changing it signs everyone out).
5. **Deploy**: `npx wrangler deploy --config cloudflare/wrangler.jsonc`.

Check it with `curl 'https://fenderog.com/art-crit/api/votes?p=<slug>'` (JSON totals, not 503). Only GitHub ids are
stored. Look at votes with `npx wrangler d1 execute art-crit-votes --remote --command 'SELECT * FROM medals'`, and back
them up with `npx wrangler d1 export art-crit-votes --remote --output votes.sql`: they are not in git. GitHub accounts
are free, so if votes are ever stuffed, add a Cloudflare rate-limiting rule for `/art-crit/api/*`. Votes appear only on
`fenderog.com/art-crit/`, not under `art-crit serve` or the old GitHub Pages URL.

To upgrade after a change to `cloudflare/schema.sql`, run step 3 again and then step 5, in that order: an older Worker keeps
working on a newer schema, but not the other way round. The schema is safe to re-apply; it recounts the tallies.

### Prompt requests (one-time setup, after votes)

The Worker opens the issues with a bot token, never the visitor's own account. Until it has one, the form falls back
to GitHub's prefilled new-issue page.

1. **Token**: GitHub → Settings → Developer settings → Fine-grained tokens → Generate. Repository access: only
   `fenderog/art-crit`. Permissions: **Issues: Read and write** (nothing else).
2. **Label** (optional, GitHub creates it on first use otherwise): `gh label create "prompt request" -R fenderog/art-crit`.
3. **Secret**: `npx wrangler secret put GITHUB_ISSUES_TOKEN --config cloudflare/wrangler.jsonc`.
4. **Tables and deploy**: run steps 3 and 5 of the votes setup again (the schema adds `prompt_requests`).

Each signed-in user can send 5 requests a day, and the whole site 50 (counted in D1). The rate-limiting rule below
covers `api/request` too.

### Rate limiting (recommended)

GitHub accounts are free, so put a limit in front of the writes. It runs before the Worker, so blocked requests cost nothing.
Check whether one exists with `cf rulesets list -z fenderog.com` (a `http_ratelimit` phase ruleset). To add it from the
CLI in one go (a Free zone requires `cf.colo.id` among the characteristics):

```sh
cf rulesets entrypoint update http_ratelimit -z fenderog.com --name "art-crit rate limits" --rules '[{"action":"block","description":"art-crit votes writes","enabled":true,"expression":"(http.host eq \"fenderog.com\" and starts_with(http.request.uri.path, \"/art-crit/api/\") and not (http.request.method eq \"GET\" and http.request.uri.path eq \"/art-crit/api/votes\"))","ratelimit":{"characteristics":["ip.src","cf.colo.id"],"period":10,"requests_per_period":30,"mitigation_timeout":10}}]'
```

Or in the Cloudflare dashboard open `fenderog.com` → Security → WAF → Rate limiting rules → Create rule (the menu has moved
before; search for "rate limiting"), and set:

- Rule name: `art-crit votes writes`
- Expression (Edit expression), which leaves the cheap `GET api/votes` read alone:
  `(http.host eq "fenderog.com" and starts_with(http.request.uri.path, "/art-crit/api/") and not (http.request.method eq "GET" and http.request.uri.path eq "/art-crit/api/votes"))`
- Characteristics: IP. Requests: 30. Period: 10 seconds. Action: Block. Duration: 10 seconds. (A Free zone only offers
  these 10-second options and a single rule; Workers Paid is account-level and doesn't change the zone's plan.)

Check it: `for i in $(seq 60); do curl -s -o /dev/null -w '%{http_code} ' -X POST https://fenderog.com/art-crit/api/logout; done`.
You should see `403` (the Worker refusing a request without the site's Origin) and then `429` once the limit trips.

## Requirements

- [uv](https://docs.astral.sh/uv/) — run everything as `uv run art-crit ...`. For a bare `art-crit`,
  install once from the repo root: `uv tool install --editable '.[verify]'`. It stays linked to
  this checkout, so edits apply without reinstalling. Commands act on the current directory (or `--root`).
- [pi](https://github.com/earendil-works/pi) for default runs; [Claude Code](https://claude.com/claude-code)
  (`claude`, logged in) for `claude-code:` models; `agy` for `agy:`, `grok` for `grok-build:`, `muse` (logged in) for `muse-code:` models, `codex` (logged in) for `codex:` models and `ori` (logged in with `ori login`) for `ori:` models.
- `godot` on PATH with matching web export templates (games).
- `ffmpeg` + `ffprobe` on PATH (media).
- `esbuild` + `npm` on PATH (web): `brew install esbuild node`.
- `blender` 5.1+ and `uvx` on PATH, plus ffmpeg (blender). The MCP add-on and server are fetched on first use.
- Google Chrome + Playwright for browser checks and viewer tests (`pip install art-crit[verify]`,
  already in dev deps). Without Playwright, browser checks are skipped and `output.verified`
  comes back null rather than false.

## Tests

```sh
uv run pytest    # CLI (art-crit run uses fake harnesses, so no model spend), media checks,
                 # viewer in Playwright on installed Chrome, ranking, Godot export checks
```
