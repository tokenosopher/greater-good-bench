#!/bin/sh
# Renders ./output/be-the-heartbeat.mp4 (needs node + ffmpeg; fonts are read from macOS system fonts).
set -e
cd "$(dirname "$0")"
mkdir -p output tmp
node src/audio.js tmp/audio.wav
node src/render.js frames 0 9999 | ffmpeg -hide_banner -loglevel error -y \
  -f rawvideo -pix_fmt rgb24 -s 1280x720 -r 30 -i - -i tmp/audio.wav \
  -c:v libx264 -preset veryslow -crf 19 -pix_fmt yuv420p -profile:v high -g 60 \
  -color_primaries bt709 -color_trc bt709 -colorspace bt709 \
  -vf "scale=out_color_matrix=bt709:out_range=tv" \
  -c:a aac -b:a 128k -shortest -movflags +faststart output/be-the-heartbeat.mp4
rm -rf tmp
