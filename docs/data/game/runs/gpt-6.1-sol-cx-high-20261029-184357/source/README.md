# Common Ground

A seven-day neighborhood strategy game about listening, mutual care, and sharing the work. Help six neighbors through a heatwave, using four hours each day.

## Run

Open `project.godot` in **Godot 4.7.2** and press **F5**, or run:

```sh
godot --path .
```

Click a neighbor to listen or help. Listening unlocks their own more effective plan for the whole week. Click **The Commons** to build lasting improvements. Each morning restores your hours and replenishes supplies; the night forecast shows the coming wellbeing loss.

Finish day seven with **everyone at 45+ wellbeing** and **at least two shared projects**. The game includes instructions, night previews, results, replay, and a sound toggle. There is no timer.

**Keys:** `1`–`6` select neighbors, `L` listen, `H` direct help, `P` their plan, `C` commons, `Space` review/end day, `F1` help, `Esc` return. `Tab` / `Shift+Tab` and `Enter` navigate controls. `R` replays from results.

## Verify

```sh
godot --headless --path . --editor --quit
godot --headless --path . --script res://checks/gameplay.gd
```

Self-contained procedural illustrations and synthesized sound; no external assets, plugins, or downloads. Uses **GL Compatibility** with no thread support enabled, suitable for a single-threaded web export. No export is included.
