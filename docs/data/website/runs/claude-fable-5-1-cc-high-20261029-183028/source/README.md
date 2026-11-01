# If Everyone Knew

A single-page, offline-capable site that teaches the seven skills that save the most lives
when someone nearby collapses, chokes, has a stroke, bleeds heavily, has a heart attack,
is unconscious but breathing, or is thinking about suicide. Plus eight one-minute cards
(seizure, anaphylaxis, overdose, drowning, burns, hypoglycaemia, heatstroke, handwashing),
a 10-scenario test, and a printable cheat sheet with a share message.

Each skill has: how to recognise it, numbered steps, a "don't" list, an interactive drill,
and a quick check. Drills include a 110 bpm CPR metronome with a tap-rate tester, branching
scenarios, a press-and-hold bleeding-pressure exercise, select-the-signs, put-in-order, and
pick-the-better-response. The emergency number adapts to a region picker (auto-guessed from
browser language).

Guidance follows AHA / ERC / Red Cross / Stop the Bleed. It is not a substitute for a
certified course.

## Files
- `index.html` — shell
- `main.js` — views and navigation (no framework, no storage)
- `lessons.js`, `regions.js` — content and emergency numbers
- `drills.js`, `util.js` — interactive components

## Develop
Serve the directory with any static server and open `index.html`.
Check bundling: `esbuild main.js --bundle --format=esm --outfile=/dev/null`
