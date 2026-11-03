#!/bin/bash
# Final exports for Video 2 (redo): master + mobile, cover embedded, true peak kept under -1 dBTP.
set -e
cd "$(dirname "$0")"
F=../PalmCare_Final
AF="aresample=192000,alimiter=limit=0.78:level=false:attack=2:release=40,aresample=48000"
COVER=../covers/PalmCare_02_Citrus_Molecular_cover.jpg
ffmpeg -v error -y -i video2b.mp4 -i mix2b.wav -i $COVER -map 0:v -map 1:a -map 2 -c:v copy -af "$AF" -c:a aac -b:a 256k \
  -c:v:1 copy -disposition:v:1 attached_pic -movflags +faststart $F/PalmCare_02_Citrus_Molecular.mp4
ffmpeg -v error -y -i video2b.mp4 -i mix2b.wav -i $COVER -map 0:v -map 1:a -map 2 -c:v:0 libx264 -crf 23 -preset slow -pix_fmt yuv420p \
  -af "$AF" -c:a aac -b:a 160k -c:v:1 copy -disposition:v:1 attached_pic -movflags +faststart $F/PalmCare_02_Citrus_Molecular_mobile.mp4
ls -la $F/PalmCare_02_Citrus_Molecular*.mp4
