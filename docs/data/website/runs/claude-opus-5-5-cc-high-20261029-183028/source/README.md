# The Ten-Minute Lifesaver

An interactive, offline page that teaches the ten emergency skills an ordinary
bystander is most likely to need, the ones that turn "someone was there" into
"someone was saved". Each skill takes about a minute and ends with a hands-on practice.

| # | Skill | Practice |
|---|-------|----------|
| 1 | Know your emergency number | Country lookup + what to say first |
| 2 | Hands-only CPR | Rhythm trainer: tap at 100–120/min (optional metronome) |
| 3 | Choking | Put the steps in order |
| 4 | Stroke (F.A.S.T.) | Smile demo + scenarios |
| 5 | Heart attack | Scenarios, including less typical signs |
| 6 | Severe bleeding | Press and hold, and don't let go |
| 7 | Burns | Do / Don't myth sorter |
| 8 | Dehydration (ORS) | Mix 1 L water + 6 tsp sugar + ½ tsp salt |
| 9 | Drowning | Spot the swimmer who is actually drowning |
| 10 | Asking about suicide | Choose what to say in a conversation |

Also included: an **🚨 Emergency** quick guide (always in the top bar) with condensed
steps and a 110/min CPR pulse, six everyday safety habits, a printable take-away card,
a "pass it on" multiplier, and a copyable message to share.

## Running

Open `index.html` through any static server. It's plain ES modules (`main.js`) and
`style.css`, with no runtime dependencies. It checks that it packages with:

```
esbuild main.js --bundle --format=esm --outfile=/dev/null
```

Nothing is stored or sent: progress is kept in memory only, and the page makes no
network requests.

## Files

- `main.js`: page layout, progress, emergency overlay, finish section
- `lessons.js`: all lesson content (edit here to translate or localize)
- `components.js`: reusable quiz, sorter, sequence and dialogue widgets
- `widgets.js`: custom practices (CPR trainer, bleeding, ORS, drowning, stroke faces, numbers)

## Caveat

The content follows widely used guidance (WHO, Red Cross/Red Crescent, AHA, ERC), but it
is not a substitute for hands-on training, and local protocols differ. Figures are rounded
global estimates.
