#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
mkdir -p .build output
swiftc -O -module-cache-path .build/ModuleCache src/render.swift -o .build/render
python3 src/sound.py
.build/render | ffmpeg -hide_banner -loglevel warning -y -f rawvideo -pixel_format rgba -video_size 960x1080 -framerate 30 -i pipe:0 -i .build/sound.wav -map 0:v -map 1:a -c:v libx264 -preset slow -crf 24 -maxrate 1300k -bufsize 2600k -pix_fmt yuv420p -c:a aac -b:a 80k -t 10 -movflags +faststart output/make-room.mp4
.build/render still 8.8 output/make-room.jpg
