#!/bin/sh
set -eu
cd "$(dirname "$0")"
mkdir -p output
build=$(mktemp -d .render.XXXXXX)
trap 'rm -rf "$build"' EXIT
clang -O2 -fobjc-arc -framework Foundation -framework CoreGraphics -framework CoreText src/post.m -o "$build/post"
python3 src/score.py "$build/sound.wav"
"$build/post" | ffmpeg -hide_banner -loglevel error -y -f rawvideo -pixel_format bgra -video_size 1080x810 -framerate 24 -i - -i "$build/sound.wav" -c:v libx264 -preset slow -crf 19 -maxrate 1850k -bufsize 2200k -pix_fmt yuv420p -colorspace bt709 -color_primaries bt709 -color_trc bt709 -vf scale=out_color_matrix=bt709 -c:a aac -b:a 80k -movflags +faststart -metadata title="Return to Source" output/return-to-source.mp4
