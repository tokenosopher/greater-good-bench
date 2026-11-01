# Ripple: A Kindness Game

A tiny, self-contained cooperative village simulator built in **Godot 4.7.2**.

## The idea

If everyone played one game, which one would improve the world for the most people?
This game's answer is a lesson, not a gimmick:

- **Kindness is contagious.** Helping one villager lifts everyone around them.
- **Mutual aid returns to you.** A happy community recharges your "Care", so the
  more you help, the more you *can* help.
- **Greed is a shared loss.** You *may* hoard for a quick personal boost, but it
  wounds the whole town — including you — and makes trust harder to rebuild.

The goal is to nurture the village into a **Beloved Community** and keep it there.

## Controls

| Key | Action |
|-----|--------|
| Arrow keys / WASD | Move the helper |
| Space | Help the villager you're standing on (kindness + ripple) |
| X (or G) | Hoard (greed) — watch the consequences |
| R | Restart |
| Esc | Back to the intro screen |

## Run it

Requires Godot 4.7.x with the GL Compatibility renderer.

```sh
# Run the game
godot --path .

# Or run the editor / import check headlessly
godot --headless --path . --editor --quit
```

## Export notes

- **Renderer:** `gl_compatibility` (set in `project.godot`) — required for web/WebGL 2.
- **No threads are used** in the game code. For a web export, make sure the export
  preset has **Thread Support disabled** (a single-threaded build that does not
  require `SharedArrayBuffer`).
- **Fully self-contained:** everything (grid, villagers, faces, UI, hearts, ripples)
  is drawn procedurally in code. No external assets, downloads, or plugins.

## What "winning" teaches

Real-world research mirrors the game's loop. Cooperation, trust, and generosity are
what maintain the commons everyone relies on; defection and greed quietly deplete
them. The game inverts the usual power fantasy: your *only* meaningful lever is
how much you give away — and that is exactly why the whole village thrives.