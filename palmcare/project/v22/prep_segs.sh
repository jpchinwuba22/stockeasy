#!/bin/bash
# cut the clean shots out of the Flow clips, retime (slow-mo where useful), interpolate to 30 fps, upscale to 1080x1920
S=src; O=segs
MI="minterpolate=fps=30:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1"
UP="scale=1080:1920:flags=lanczos,unsharp=5:5:0.5"
cut () { # name src in dur speed [extra vf before scale]
  ffmpeg -v error -y -ss $3 -t $4 -i $S/$2.mp4 -an -vf "setpts=PTS/$5,$MI,${6:-null},$UP" -c:v libx264 -crf 12 -preset medium -pix_fmt yuv420p $O/$1.mp4
}
cut s01 c1 0.00 1.00 1.0 &
cut s02 c1 1.15 1.25 0.6 &
cut s03 c1 3.35 1.00 1.0 &
cut s04 c1 4.50 1.45 1.0 &
wait
cut s05 c2 0.00 1.25 1.0 &
cut s06 c2 1.30 0.95 0.7 &
cut s07 c2 2.30 1.05 1.0 &
cut s08 c3 0.00 1.45 0.7 &
wait
cut s09 c3 2.10 1.35 1.0 &
cut s10 c3 5.40 1.55 1.0 &
cut s11 c4 0.30 1.90 1.0 "crop=385:684:335:300" &
cut s16 c6 0.20 2.25 1.0 &
wait
ffmpeg -v error -y -i c7_fixed.mp4 -an -vf "setpts=PTS/0.75,$MI,$UP" -c:v libx264 -crf 12 -preset medium -pix_fmt yuv420p $O/s17.mp4
for f in $O/*.mp4; do echo $f $(ffprobe -v error -count_frames -select_streams v -show_entries stream=nb_read_frames,width,height -of csv=p=0 $f); done
