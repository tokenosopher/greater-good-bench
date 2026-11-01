# Make room

A ten-second animated illustration about extending a small act of care to another person. An umbrella widens to cover two people; the gesture travels outward through a neighborhood. The closing invitation is **Notice. Ask. Listen.**

Finished files:

- `output/make-room.mp4` — 960 × 1080, 30 fps, 10 seconds, with original synthesized music.
- `output/make-room.jpg` — companion poster, taken from the final scene.

All illustrations, motion, typography, and music are generated locally. No downloaded assets or third-party packages are used.

## Rebuild

On macOS, with Swift, Python 3, and FFmpeg available:

```sh
./src/build.sh
```

`src/render.swift` draws the animation with Core Graphics and Core Text, using the macOS Baskerville and Avenir Next fonts. It streams raw frames directly to FFmpeg, so no frame sequence is left on disk. `src/sound.py` synthesizes the soundtrack using only the Python standard library. Build intermediates live in `.build/`, which can be deleted after rendering.
