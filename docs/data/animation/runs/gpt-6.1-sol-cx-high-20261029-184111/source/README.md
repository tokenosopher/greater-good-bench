# Make someone's day lighter

A ten-second animated invitation to offer help, accept help, and pass it on.
A heavy circle becomes a sun as a community shares its weight.

Finished files:
- `output/day-lighter.mp4` — 1080 × 1080, 30 fps, 10 seconds, H.264 + AAC.
- `output/day-lighter.jpg` — matching poster, taken from the finished video.

## Rebuild

On macOS, from this directory:

```sh
./src/build.sh
```

Requires the system Swift compiler, Python 3, and ffmpeg. No packages, downloads,
or external artwork are used. Core Graphics draws the illustration; Core Text
sets Baskerville and Avenir Next. All movement is procedural. The original
bell-and-pad score is synthesized with Python's standard library.

`src/render.swift` contains the complete illustration and animation.
`src/sound.py` synthesizes the score. `src/build.sh` encodes the deliverables.
Temporary rendering files are removed after the build.
