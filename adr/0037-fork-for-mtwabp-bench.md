# 0037. Fork art-crit as mtwabp bench, changing what the site asks rather than how it works

- Status: Accepted
- Date: 2026-10-29

## Context

art-crit (github.com/fenderog/art-crit) runs a prompt across LLM agents and shows what each one made side by side,
with its transcript, cost and checks, ranked by the owner and voted on by visitors. This fork uses it for one question:
can frontier models make something that, if everyone saw, read, used, played or watched it, would improve the world for
the greatest number of people? What gets measured in AI gets optimized, and nobody measures this yet, so the fork
starts measuring it. v1 is meant to be simple: generate, verify, show the outputs side by side.

The upstream already does almost all of that, and keeps changing. The smaller the fork's diff, the easier it is to
take the upstream's fixes.

## Decision

The fork is a new site on the unchanged tool:

- **Rebranded for visitors only.** Window titles, the logo, the home page's intro and the "Request a prompt" copy name
  the site with its working name, "mtwabp bench" (one place per file: `SITE_NAME` in `docs/assets/dom.js`, each HTML
  file's `<title>` and logo `alt`, `docs/assets/logo.svg`). Prompt requests open issues on `tokenosopher/mtwabp-bench`.
- **Kept as it is:** the CLI name (`art-crit`, package, `art-crit.toml`, `ART_CRIT_*`, `docs/` layout, Cloudflare
  paths), the kinds, the owner's ranking, community votes, and the harnesses. The upstream's published pages were
  removed (`art-crit rm` + `rebuild`); the site starts empty.
- **Six pages**, one per task, with prompts in `prompts/` and the commands in `prompts/README.md`: SVG (`media`),
  Website (`web`), 3D model (`blender`), Game (`godot`), Animation (`media`, 10 s video cap) and Essay (`text`).
- **One model set**, `frontier` in `art-crit.toml`: the newest frontier models through pi's OpenRouter provider, the
  effort level set per batch with `-e`, so every model on a page runs under the same harness configuration. A run
  records its harness and tools, and only comparable configurations are compared.

## Alternatives considered

- **Rename the CLI and package too**: a cleaner name everywhere, but every upstream change would then conflict, for
  nothing a visitor sees.
- **An automated judge (an LLM grading each output against a rubric), or scores**: out of scope. The question is the
  kind a score hides; v1 shows the work and lets the owner and visitors judge it.
- **Custom harnesses tuned per model**: out of scope. Comparing models needs the same harness and tools for all of
  them; a model's best custom setup is a different benchmark.
- **Keep the upstream's pages**: they answer a different question, and they are 700 MB the fork doesn't need.

## Consequences

- Merging upstream changes stays easy; the fork's own changes are copy, the logo, `prompts/`, the `frontier` set and
  the request repo.
- The README's Cloudflare section still holds the upstream's domain, project and repo, to be replaced when the owner
  deploys. Until then there is no live site.
- `art-crit video` and the video studio still put the upstream's `fenderog.com/art-crit` on their vote cards
  (`SITE_URL`/`SITE_NAME` in `video.py`, the card defaults in `studio.py`); change them once the fork has an address.
- Open questions, owned by the owner:
  - **Animation format**: a `media` video (as set up now, 10 s cap) or a `web` page (an animation in the browser, no
    length cap).
  - **Web access for agents**: whether runs may search or fetch from the web, and how a harness would be set up for it
    the same way for every model.
  - **A theory-of-change note per model**: whether each run should also write down how its output would improve the
    world, shown beside it.
  - **Cost budget per batch**: how much a batch of nine models may spend, which decides the effort levels and how many
    pages run at once.
