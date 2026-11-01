#!/usr/bin/env python3
"""Render the four beats and crossfade them into a short silent film.

The still poster is the lasting image. The film is the act of looking:
a stranger in the dark, then the room, then the street, then the words.
"""

import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(__file__))
from build_poster import build, ROOT

TMP = "/tmp/someone-is-home-frames"
OUT = os.path.join(ROOT, "output", "someone-is-home.mp4")
WIDTH = 900


def main():
    os.makedirs(TMP, exist_ok=True)
    beats = [
        ("dark", dict(face=0.42, window=0.0, crowd=0.0, text=0.0)),
        ("seen", dict(face=1.0, window=1.0, crowd=0.0, text=0.0)),
        ("all", dict(face=1.0, window=1.0, crowd=1.0, text=0.0)),
        ("words", dict(face=1.0, window=1.0, crowd=1.0, text=1.0)),
    ]
    pngs = []
    for name, kw in beats:
        svg = os.path.join(TMP, f"{name}.svg")
        png = os.path.join(TMP, f"{name}.png")
        with open(svg, "w", encoding="utf-8") as f:
            f.write(build(**kw))
        subprocess.check_call(["rsvg-convert", "-w", str(WIDTH), svg, "-o", png])
        pngs.append(png)
        print("rendered", name)

    # 9.8s: dark, then the room, then every person, then the words, held long enough to read.
    fc = (
        "[0][1]xfade=transition=fade:duration=1.8:offset=1.8[a];"
        "[a][2]xfade=transition=fade:duration=1.4:offset=4.6[b];"
        "[b][3]xfade=transition=fade:duration=1.4:offset=6.6,format=yuv420p[v]"
    )
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-framerate", "24", "-t", "4.0", "-i", pngs[0],
        "-loop", "1", "-framerate", "24", "-t", "4.0", "-i", pngs[1],
        "-loop", "1", "-framerate", "24", "-t", "4.0", "-i", pngs[2],
        "-loop", "1", "-framerate", "24", "-t", "4.5", "-i", pngs[3],
        "-filter_complex", fc,
        "-map", "[v]",
        "-r", "24",
        "-t", "9.8",
        "-c:v", "libx264",
        "-crf", "20",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        OUT,
    ]
    subprocess.check_call(cmd)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
