# Ripple — One Small Kindness at a Time

A cozy, complete 5-day village game for Godot **4.7.2**. The premise is simple:
if everyone practised *notice → pause → help well → pass it on* in real life,
the world would become kinder for a great many people. So this game lets you
practise exactly that.

## How to play

- **Move:** WASD or arrow keys
- **Interact / talk:** `E`, `Space`, or `Enter` (when near a ❗ bubble)
- Wander the village for five short days. Needs appear as timed bubbles:
  - **Talk** to villagers — choose how to respond. Listening properly,
    helping at someone else's pace, and making newcomers feel welcome
    work better than rushing or brushing people off.
  - **Fetch** items (walk over the glowing item, then bring it back).
  - **Tend the commons** — clear litter and water wilting garden plants.
- Thoughtful help raises village **Warmth**, blooms flowers, and *inspires*
  that villager: inspired villagers periodically help others on their own,
  creating **Ripples** you didn't have to perform yourself.
- Ignored needs expire and weigh the village down.
- Each evening, choose how to carry the day forward (rest, reflect, or
  message a friend) for a small next-day perk. After Day 5 you get your
  village's ending — plus one small real-world quest.

## Run it

1. Open Godot 4.7.2, choose **Import**, and select this folder's `project.godot`.
2. Press **Play** (F5). The main scene is `main.tscn`.

Or from a terminal:

```sh
godot --path .
```

Headless sanity check:

```sh
godot --headless --path . --editor --quit
```

## Technical notes

- Renderer: `gl_compatibility` (project + mobile), suitable for a web export.
- No thread support is enabled, and there are no export presets, plugins,
  downloads, or external assets — all art is drawn and all sounds are
  synthesized in code (`main.gd`). Everything is self-contained.
