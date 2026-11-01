# call someone.

A 9.6-second animation about the cheapest, most universal, most evidence-backed
intervention there is: reaching out to another person.

## The idea

Almost every human on earth can do one thing today that measurably improves
their life and someone else's, costs nothing, needs no infrastructure, no
permission, no money, and scales to everyone: **contact with another person**.
Social connection is one of the strongest known predictors of health and
longevity; isolation is as harmful as smoking. It is also contagious in the
good direction — warmth passed to one person tends to travel on.

So the film reduces the world to its smallest true picture: a dark field of
faint blue lights, one for each of us. Threads between them are already there —
we just cannot see them lit. One light reaches across a gap. The thread catches,
a spark crosses, and warmth runs person to person until there is nowhere left
in the frame that is cold. The world does not become different; it becomes warm.
Then the only lines in the film arrive:

> **call someone.**

No narration, no statistics, no language in the picture until the last second —
so the image can work for anyone, and the invitation is one everybody can
accept before the credits would have rolled.

## Structure (9.6 s, 30 fps, 1920×1080)

| time | beat |
|---|---|
| 0.0–1.1 | a cold world: hundreds of faint blue lights, half-visible threads, slow breathing |
| 1.15 | one light pulses — it notices |
| 1.6–2.3 | a warm thread reaches across the gap, a spark at its tip |
| 2.32 | contact: a breath of light expands, two lights flare and settle into warmth |
| 2.3–6.2 | warmth spreads outward through the web, spark to spark, cold blue retreating to the edges |
| 5.9 | the light nearest to us — the one bottom-right — catches and floods the frame |
| 6.2–9.6 | the whole field is warm, breathing together; the world settles down to listen |
| 7.45–9.6 | the words arrive |

## Files

- `output/call_someone.mp4` — the film (1080p, 9.6 s, 1.2 MB)
- `output/call_someone_reach.jpg` — the reach (2.05 s)
- `output/call_someone_spreading.jpg` — the warmth travelling (3.50 s)
- `output/call_someone_title.jpg` — the title card (8.40 s)

## How it is made

Everything is generated from scratch with the Python standard library and
ffmpeg — no packages, no assets, no images downloaded. That constraint shapes
the whole pipeline:

- **`src/art.py`** — the world and the renderer.
  - ~75 "souls" (well-separated lights that carry the visible threads, k-nearest
    neighbours, connected), ~260 "dust" (everyone further off), and one hero
    light in the near field.
  - Light is accumulated additively into three 8-bit *energy* buffers per frame
    (byte saturation, no float framebuffers), then pushed through a per-frame
    filmic tone curve baked into a 256-entry LUT — so exposure, warm tint and
    the final "settle" are one C-speed `bytes.translate` per channel.
  - Glows are pre-computed sprites quantised by warmth (20 steps × 7 sizes), so
    cold → warm is a cross-fade of two light sources rather than a colour swap.
  - Arrival times form a noisy, organic front expanding from the point of
    contact; a spark is animated along each thread when both of its ends light.
  - A coarse 120×68 warm-haze field is rendered per frame (the air itself
    warming) and upscaled in ffmpeg.
- **`src/font.py`** — a minimal TrueType reader (`.ttc` aware, `cmap` 4/12,
  quadratic `glyf` outlines) plus an antialiased scanline rasteriser, because
  this ffmpeg has no `drawtext`. The title is set in Avenir Light, letter-spaced
  and drawn in the same additive light as everything else.
- **`src/pngutil.py`** — PNG writer (only used for inspection frames / the haze).
- **`src/make.sh`** — the whole build: render → grade → the three cards.
  The grade adds the warm haze layer, a two-scale highlight bloom, a vignette
  and fine grain, all in ffmpeg.
- **`src/grade.sh`** — the same look applied to a single still, for checking.

Rebuild everything (about a minute):

```sh
bash src/make.sh
```
