# Common Ground

A short, complete game about listening, interests, and solutions that include
everyone. You chair three difficult conversations. Each side has a public
position and hidden needs underneath it. Your job is not to split the
difference — it is to find proposals that let both sides keep what they are
actually afraid of losing.

**The premise:** if everyone played this, the world would improve because more
people would practice three learnable habits:

1. Hearing the interest behind a position.
2. Treating attention as a resource that must be shared.
3. Looking for solutions that meet both fears before dividing a scarce thing.

The game is a rehearsal for those habits, not a lecture about them.

## Running it

Requires **Godot 4.7.2** (the project targets the GL Compatibility renderer and
does not use threads, so it is ready for a web export).

From this directory:

```bash
godot --path .
```

Or open `project.godot` in the Godot editor and press **F5**.

To verify the project loads cleanly without opening a window:

```bash
godot --headless --path . --editor --quit
```

## How to play

- **Listen** on either side. This reveals one hidden need and raises that
  side's goodwill. The other side loses a little goodwill: attention is finite.
- **Read the fear** on each card. Genuine bridges protect both sides' fears at
  once.
- **Connect** one revealed need from each side, then press *Find Common Ground*.
  Some pairs are real synergies. Others look fair but leave one need unmet, and
  cost goodwill.
- **Reassure** spends a turn restoring goodwill without revealing anything.
  Sometimes keeping someone at the table is the work.
- If either side's goodwill reaches zero, they walk out.
- Bring **all six needs** onto common ground before round 14 ends.

There are three chapters, each about five minutes. Progress is not saved; the
whole game is designed for one sitting.

**Controls:** mouse or touch, plus keyboard navigation (`Tab`/`Shift+Tab` to
focus, `Enter`/`Space` to activate, `Esc` to close dialogs or leave the table).

## What is in here

- `main.tscn` — the single entry scene.
- `scripts/main.gd` — screens, game rules, and UI wiring.
- `scripts/data.gd` — all scenario writing and the field guide.
- `scripts/party_panel.gd`, `scripts/interest_card.gd`,
  `scripts/trust_meter.gd` — the table UI.
- `scripts/background.gd` — the painted landscape, drawn entirely in code.
- `scripts/audio.gd` — tiny UI tones synthesized at runtime.
- `scripts/ui_kit.gd` — palette, type, and style helpers.
- `icon.svg` — the project icon.

No external assets, downloads, fonts, or plugins are used. Everything visual is
drawn with Godot controls and `_draw`, and every sound is generated from a sine
wave at startup.
