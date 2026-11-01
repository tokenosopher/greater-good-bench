#!/bin/bash
# Shared look: warm haze + two-scale bloom + vignette + grain.
# usage: grade.sh <main.png> <amb.png> <out.jpg> [extra_out_w]
set -e
A="${1:?main}"
B="${2:?amb}"
O="${3:?out}"
SC="${4:-1000}"
ffmpeg -y -loglevel error -i "$A" -i "$B" -filter_complex "\
[1:v]scale=1920:1080:flags=bicubic,format=rgb24[amb];\
[0:v]format=rgb24[main];\
[main][amb]blend=all_mode=addition:all_opacity=1.0[base];\
[base]split=3[f][g1][g2];\
[g1]lutrgb=r='clip((val-70)*2.2,0,255)':g='clip((val-70)*2.2,0,255)':b='clip((val-70)*2.2,0,255)',gblur=sigma=9[b1];\
[g2]lutrgb=r='clip((val-55)*1.9,0,255)':g='clip((val-55)*1.9,0,255)':b='clip((val-55)*1.9,0,255)',gblur=sigma=38[b2];\
[f][b1]blend=all_mode=addition:all_opacity=0.8:shortest=1[c1];\
[c1][b2]blend=all_mode=addition:all_opacity=0.8:shortest=1[c2];\
[c2]format=rgb24,vignette=angle=PI/3.7,noise=alls=4:allf=t+u,scale=$SC:-2" -q:v 4 "$O"
