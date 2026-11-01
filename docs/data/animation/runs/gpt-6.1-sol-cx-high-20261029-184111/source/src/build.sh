#!/bin/sh
# Run from the project root on macOS. Requires Swift, Python 3 and ffmpeg.
set -eu
mkdir -p .build output
trap 'rm -rf .build' EXIT
swiftc -O src/render.swift -o .build/render
python3 src/sound.py
.build/render | ffmpeg -y -hide_banner -loglevel warning \
  -f rawvideo -pixel_format rgba -video_size 1080x1080 -framerate 30 -i pipe:0 \
  -i .build/score.wav -map 0:v -map 1:a -t 10 \
  -c:v libx264 -preset slow -crf 24 -pix_fmt yuv420p \
  -c:a aac -b:a 96k -movflags +faststart \
  -metadata title="Make someone's day lighter" output/day-lighter.mp4
ffmpeg -y -hide_banner -loglevel error -ss 8 -i output/day-lighter.mp4 \
  -frames:v 1 -pix_fmt yuvj420p -q:v 2 output/day-lighter.jpg
