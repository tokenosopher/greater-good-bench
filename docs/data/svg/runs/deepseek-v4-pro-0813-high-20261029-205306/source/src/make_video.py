#!/usr/bin/env python3
"""Render an animated version of the Earth/Golden-Rule SVG into an mp4."""
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(__file__))
from make_svg import build_svg

FPS = 24
DURATION = 8.0
N = int(FPS * DURATION)  # 192 frames
W, H = 1920, 1080

FRAME_DIR = "/tmp/earth_frames"
os.makedirs(FRAME_DIR, exist_ok=True)

svg_path = "/tmp/earth_frame.svg"

for i in range(N):
    t = i / (N - 1)
    svg = build_svg(t)
    with open(svg_path, "w") as f:
        f.write(svg)
    png = os.path.join(FRAME_DIR, f"frame_{i:04d}.png")
    subprocess.run(
        ["rsvg-convert", "-w", str(W), "-h", str(H), svg_path, "-o", png],
        check=True,
    )

print(f"rendered {N} frames")

# encode
subprocess.run(
    [
        "ffmpeg", "-y", "-loglevel", "error",
        "-framerate", str(FPS),
        "-i", os.path.join(FRAME_DIR, "frame_%04d.png"),
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-crf", "22", "-preset", "slow",
        "-movflags", "+faststart",
        "output/earth.mp4",
    ],
    check=True,
)
print("wrote output/earth.mp4")
