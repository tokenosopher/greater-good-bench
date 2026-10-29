# Prompts

The six pages of mtwabp bench, one prompt file each. **The prompts here are placeholders**: the owner supplies the
final ones before the first real run. Each file is passed to `art-crit run` whole (`-f`), so it should hold the prompt
and nothing else. A page has one prompt: to change it after its first run, pass `--change-prompt`.

| Page (slug) | Title | Kind | Prompt file | Note |
|---|---|---|---|---|
| `svg` | SVG | `media` | [svg.md](svg.md) | Shown as an image (`<img>`); hand-written SVG or generated, the prompt decides. |
| `website` | Website | `web` | [website.md](website.md) | Packaged into one offline `index.html` with esbuild; checked in the site's sandbox. |
| `3d-model` | 3D model | `blender` | [3d-model.md](3d-model.md) | A `.glb` plus renders, made in a per-run windowless Blender through its MCP server. |
| `game` | Game | `godot` | [game.md](game.md) | Exported to a web build and boot-checked in headless Chrome. |
| `animation` | Animation | `media` | [animation.md](animation.md) | A video, capped at 10 s (trimmed if longer). The owner may still switch this page to `web` (an animation in the browser, no length cap): change `--kind` before the first run, since a page keeps its kind. |
| `essay` | Essay | `text` | [essay.md](essay.md) | The `text` kind (ADR-0036): one Markdown file, rendered on the site. |

## Models

`--set frontier` (`[sets]` in `art-crit.toml`): the newest frontier models, all through pi's OpenRouter provider, so
every model runs under the same harness configuration. The entries carry no effort level; `-e high` sets one level
for the whole batch.

- `openrouter/anthropic/claude-fable-5.1`
- `openrouter/anthropic/claude-opus-5.5`
- `openrouter/openai/gpt-6-astra-pro`
- `openrouter/openai/gpt-6.1-sol-pro`
- `openrouter/google/gemini-4-argon`
- `openrouter/meta/muse-wonder`
- `openrouter/meta/muse-spark-open`
- `openrouter/deepseek/deepseek-v4.1-flash-1017`
- `openrouter/deepseek/deepseek-v4-pro-0813`

Check that pi knows them all before the first batch (`uv run art-crit models openrouter/`): one unknown model
fails planning for the whole set. A model live on OpenRouter but missing from pi's catalog can be bridged as
AGENTS.md describes (pi gotchas).

## Commands

Run from the repo root. Each page's dry run prints the plan (nine runs) and spends nothing; the second command is the
real batch, which asks for confirmation and then publishes each run as it lands (`--no-publish` to keep it local).
`-T 2h` is the per-agent timeout and `-j 4` the number of agents at once (both also the `[run]` defaults).

**Real runs cost money.** They need pi installed and logged into OpenRouter (`OPENROUTER_API_KEY`), plus each kind's
tools: `ffmpeg` + `ffprobe` for media (SVG, Animation), `esbuild` + `npm` for the website, `blender` 5.1+ and `uvx` for
the 3D model, `godot` with matching web export templates for the game.

### SVG

```sh
uv run art-crit run --dry-run --kind media -p svg -t "SVG" --set frontier -e high -T 2h -j 4 -f prompts/svg.md
uv run art-crit run --kind media -p svg -t "SVG" --set frontier -e high -T 2h -j 4 -f prompts/svg.md
```

### Website

```sh
uv run art-crit run --dry-run --kind web -p website -t "Website" --set frontier -e high -T 2h -j 4 -f prompts/website.md
uv run art-crit run --kind web -p website -t "Website" --set frontier -e high -T 2h -j 4 -f prompts/website.md
```

### 3D model

```sh
uv run art-crit run --dry-run --kind blender -p 3d-model -t "3D model" --set frontier -e high -T 2h -j 4 -f prompts/3d-model.md
uv run art-crit run --kind blender -p 3d-model -t "3D model" --set frontier -e high -T 2h -j 4 -f prompts/3d-model.md
```

### Game

```sh
uv run art-crit run --dry-run --kind godot -p game -t "Game" --set frontier -e high -T 2h -j 4 -f prompts/game.md
uv run art-crit run --kind godot -p game -t "Game" --set frontier -e high -T 2h -j 4 -f prompts/game.md
```

### Animation

```sh
uv run art-crit run --dry-run --kind media -p animation -t "Animation" --set frontier -e high -T 2h -j 4 -f prompts/animation.md
uv run art-crit run --kind media -p animation -t "Animation" --set frontier -e high -T 2h -j 4 -f prompts/animation.md
```

### Essay

```sh
uv run art-crit run --dry-run --kind text -p essay -t "Essay" --set frontier -e high -T 2h -j 4 -f prompts/essay.md
uv run art-crit run --kind text -p essay -t "Essay" --set frontier -e high -T 2h -j 4 -f prompts/essay.md
```

To add runs to a page later (another model, another level), pass `--page <slug>` without a prompt: the page's
prompt and kind carry over (see the main README, *Add runs to an existing page*).
