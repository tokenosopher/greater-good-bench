#!/bin/bash
# Build "call someone." end to end.
#   1. render the light field (python, stdlib only) -> build.mp4 + amb/0000..0287.png
#   2. grade: warm haze + two-scale bloom + vignette + grain
#   3. two title cards
set -e
cd "$(dirname "$0")/.."
mkdir -p output tmp

echo "== render =="
rm -rf amb
python3 src/art.py build.mp4

# shared look ---------------------------------------------------------------
# [amb] is the coarse warm-haze field (120x68) upscaled to the frame.
# bloom = highlight-thresholded, blurred, added back at two scales.
GRADE="\
[1:v]fps=30,scale=1920:1080:flags=bicubic,format=rgb24[amb];\
[0:v]format=rgb24[main];\
[main][amb]blend=all_mode=addition:all_opacity=1.0[base];\
[base]split=3[f][g1][g2];\
[g1]lutrgb=r='clip((val-70)*2.2,0,255)':g='clip((val-70)*2.2,0,255)':b='clip((val-70)*2.2,0,255)',gblur=sigma=9[b1];\
[g2]lutrgb=r='clip((val-55)*1.9,0,255)':g='clip((val-55)*1.9,0,255)':b='clip((val-55)*1.9,0,255)',gblur=sigma=38[b2];\
[f][b1]blend=all_mode=addition:all_opacity=0.8:shortest=1[c1];\
[c1][b2]blend=all_mode=addition:all_opacity=0.8:shortest=1[c2];\
[c2]format=rgb24,vignette=angle=PI/3.7,noise=alls=3:allf=t+u[v]"

echo "== grade video =="
ffmpeg -y -loglevel error -i build.mp4 -f image2 -i amb/%04d.png \
  -filter_complex "$GRADE" -map "[v]" -t 9.6 \
  -c:v libx264 -preset slow -crf 21 -pix_fmt yuv420p -movflags +faststart \
  output/call_someone.mp4

echo "== stills =="
python3 src/art.py stills 2.05,3.50,8.40 >/dev/null
for pair in "2.05:0062:reach" "3.50:0105:spreading" "8.40:0252:title"; do
  t=${pair%%:*}; rest=${pair#*:}; frame=${rest%%:*}; name=${rest##*:}
  ffmpeg -y -loglevel error -i still_$t.png -f image2 -i amb/$frame.png \
    -filter_complex "$GRADE" -map "[v]" -frames:v 1 -q:v 2 tmp/poster_$name.jpg
  cp tmp/poster_$name.jpg "output/call_someone_$name.jpg"
done

ls -la output/
