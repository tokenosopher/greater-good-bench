# Steady Hands

*One ordinary day. Five moments where the nearest person is you.*

A first-aid game. Most people who die of a cardiac arrest, a blocked airway, a
stroke or a bad bleed do so in the minutes before professional help arrives,
surrounded by people who would help if they knew how. Steady Hands puts those
minutes in your hands, five times in one day:

| Time  | Moment         | What you practise                                              |
|-------|----------------|----------------------------------------------------------------|
| 07:40 | The Park       | Cardiac arrest: check, delegate, chest compressions, AED       |
| 12:30 | The Café       | Choking: back blows and abdominal thrusts                      |
| 15:10 | Tea at Rosa's  | Stroke: Face, Arms, Speech, Time - and a recognition drill     |
| 17:15 | The Ride Home  | Severe bleeding: direct pressure, add don't lift               |
| 19:50 | The Kitchen    | Burns: 20 minutes of cool running water, and what not to use   |

Each moment mixes quick decisions with a hands-on part (keeping a 100-120/min
compression rhythm, timing firm blows, holding pressure, keeping water cool),
then ends with a short "remember" card. Finish the day to get a pocket card.

## Run

Requires Godot 4.7 (standard build, no .NET needed).

    godot --path .

or open the folder in the Godot editor and press F5. The project uses the
Compatibility (OpenGL) renderer and no threads, so it exports to the web as is.

## Controls

Mouse or touch for everything. Optional keys:

- `Space` / `Enter` - continue, chest compressions, back blows, hold pressure
- `1`-`4` - pick an answer
- `Left` / `Right` (or `A` / `D`) - water temperature
- Number keys - dial the phone
- `M` - sound on/off, `Esc` - back to the title

On the title screen, set the emergency number used where you live; the game
uses it throughout.

## Notes

- Everything is generated in code: no image, font or audio files, no plugins.
- Guidance follows current international resuscitation / Red Cross first-aid
  guidelines in general terms. It is not medical advice and no substitute for
  a hands-on course - which the game tells you to go and take.
- Dev flags (after `--`): `--auto` plays itself through, `--only=N` starts at
  moment N (0-4), `--speed=X` sets the time scale.
