# The Commons

A small, self-contained Godot 4.7.2 game about two skills that improve the world for the greatest number of people:

1. **The Commons (cooperation)** — an iterated public-goods game against four archetypal neighbours (reciprocator, unconditional giver, free-rider, grudger) over 20 rounds. Players discover that cooperation-with-accountability beats both defection and naive generosity — the math behind taxes, climate treaties, open source, and every shared resource.
2. **The Aid Office (effectiveness)** — a budget-allocation game where shiny options underperform boring, well-evidenced ones. Teaches cost-effectiveness comparison, evidence quality, diminishing returns, benchmarking against cash, and the value of buying information — compressed versions of real lessons from global health and effective-giving research.

## Running

Open the project in Godot 4.7.2 and press **F5** (Play), or from the command line:

```
godot --path .
```

Headless sanity check:

```
godot --headless --path . --editor --quit
```

## Exporting for web

The project uses the `gl_compatibility` renderer and no thread support, so it is web-export ready. Export with the Web platform preset (don't enable threads) and host the resulting build.

## Contents

- `main.tscn` — main scene (a single Control node; all UI is built in code)
- `scripts/main.gd` — shell, navigation, intro
- `scripts/cooperate.gd` — the public-goods game
- `scripts/aid.gd` — the allocation game

No external assets, plugins, or downloads. Everything is generated in code.
