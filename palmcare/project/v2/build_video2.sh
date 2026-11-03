#!/usr/bin/env bash
# Assemble PalmCare Video 2 (Citrus Ritual) at 1080x1920.
# Usage: build_video2.sh OUT.mp4 MUSIC.mp3 [VO.mp3 "start1,end1,at1;start2,end2,at2;..."]
set -euo pipefail
cd "$(dirname "$0")"
U=/root/.claude/uploads/ae1b3550-c976-5b71-9f6e-2d57965fb3f7
C1="$U/552f2c00-Woman_applying_skincare_product_20261022065128.mp4"
C2="$U/4c59152d-Woman_stepping_out_of_shower_20261022065305.mp4"
C3="$U/4c1401c3-Skincare_commercial_applying_lotion_20261022065614.mp4"
C4="$U/c1aee56b-Woman_speaking_on_rooftop_20261022070024.mp4"
OUT=$1
MUS=$2
VO=${3:-}
VOMAP=${4:-}
SFX=../sfx/shimmer.mp3
PF=../fonts/Playfair-Medium.ttf
PI=../fonts/Playfair-Italic.ttf
MO=../fonts/Montserrat-Medium.ttf

UP="scale=1080:1920:flags=lanczos,setsar=1,fps=24"
G="eq=contrast=1.05:saturation=1.10:gamma=0.99,colorbalance=rs=0.04:gs=0.01:bs=-0.05:rm=0.03:bm=-0.04:rh=0.03:bh=-0.04,vignette=PI/6,noise=alls=3:allf=t"
LT() { echo "drawtext=fontfile=$PF:text='$1':fontsize=74:fontcolor=white:x=(w-tw)/2:y=h*0.80:shadowcolor=black@0.45:shadowx=0:shadowy=3:alpha='min(1,t/0.4)',drawbox=x=iw*0.42:y=ih*0.858:w=iw*0.16:h=2:color=white@0.8:t=fill,drawtext=fontfile=$MO:text='$2':fontsize=30:fontcolor=white:x=(w-tw)/2:y=h*0.868:shadowcolor=black@0.45:shadowx=0:shadowy=2:alpha='min(1,t/0.5)'"; }
WOUT() { echo "fade=out:st=$1:d=0.14:color=white"; }
WIN="fade=in:st=0:d=0.16:color=white"

# Timeline: a 0 | b 2.8 | c 5.6 | d 8.6 | e 11.5 | f 14.3 | g 15.55 | hero 18.45 | walk 25.85 | line 29.75 | card 33.99-37.59
VF="
[0:v]trim=0.1:2.9,setpts=PTS-STARTPTS,$UP,$G,drawtext=fontfile=$PI:text='The Ritual After':fontsize=84:fontcolor=white:x=(w-tw)/2:y=h*0.13:shadowcolor=black@0.4:shadowx=0:shadowy=3:alpha='if(lt(t,0.3),0,if(lt(t,0.9),(t-0.3)/0.6,if(lt(t,2.2),1,max(0,(2.8-t)/0.6))))',fade=in:st=0:d=0.35[a];
[0:v]trim=3.1:5.9,setpts=PTS-STARTPTS,$UP,$G,$(LT 'Citrus Vitamin Glow' 'BODY WASH')[b];
[0:v]trim=6.1:9.1,setpts=PTS-STARTPTS,$UP,$G[c];
[1:v]trim=7.0:9.9,setpts=PTS-STARTPTS,$UP,$G[d];
[2:v]trim=0.1:2.9,setpts=PTS-STARTPTS,$UP,$G,$(LT 'Molecular Glow' 'BODY LOTION')[e];
[2:v]trim=3.05:4.3,setpts=PTS-STARTPTS,$UP,$G[f];
[2:v]trim=7.05:9.95,setpts=PTS-STARTPTS,$UP,$G,$(WOUT 2.76)[g];
[4:v]setpts=PTS-STARTPTS,setsar=1,fps=24,$WIN,$(WOUT 7.26)[h];
[3:v]trim=1.0:4.9,setpts=PTS-STARTPTS,$UP,$G,$WIN[i];
[3:v]trim=4.96:9.2,setpts=PTS-STARTPTS,$UP,$G[j];
[5:v]scale=1188:2112,zoompan=z='1+0.0006*on':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=1080x1920:fps=24,setsar=1,fade=in:st=0:d=0.35,format=yuv420p[k];
[a][b][c][d][e][f][g][h][i][j][k]concat=n=11:v=1:a=0[v]"

# Ambient from the clips (quiet), her line at full level
# Each clip's own sound, cut exactly with its picture and de-clicked, so water/skin/rooftop air
# change with the shot. Hero section (7.4167s) is silent here; the music and shimmers carry it.
AS() { echo "[$1:a]atrim=$2:$3,asetpts=PTS-STARTPTS,aresample=48000,aformat=channel_layouts=stereo,afade=t=in:d=0.06,afade=t=out:st=$(python3 -c "print(round($3-$2-0.08,3))"):d=0.08[$4]"; }
AF="
$(AS 0 0.1 2.9 m1);$(AS 0 3.1 5.9 m2);$(AS 0 6.1 9.1 m3);$(AS 1 7.0 9.9 m4);
$(AS 2 0.1 2.9 m5);$(AS 2 3.05 4.3 m6);$(AS 2 7.05 9.95 m7);
anullsrc=r=48000:cl=stereo,atrim=0:7.4167[m8];
$(AS 3 1.0 4.9 m9);
[m1][m2][m3][m4][m5][m6][m7][m8][m9]concat=n=9:v=0:a=1,volume=0.32,apad=whole_dur=37.6[amb];
[3:a]atrim=4.96:9.2,asetpts=PTS-STARTPTS,aresample=48000,aformat=channel_layouts=stereo,adelay=29767|29767,apad=whole_dur=37.6[line];
[7:a]aresample=48000,aformat=channel_layouts=stereo,volume=0.45,asplit=5[x1][x2][x3][x4][x5];
[x1]adelay=18400|18400[f1];[x2]adelay=20320|20320[f2];[x3]adelay=22240|22240[f3];[x4]adelay=25810|25810[f4];[x5]adelay=33960|33960[f5]"
SPEECH="[line]"
NSP=1
if [[ -n "$VO" ]]; then
  IFS=';' read -ra parts <<<"$VOMAP"
  AF+=";[8:a]aresample=48000,aformat=channel_layouts=stereo,asplit=${#parts[@]}$(for k in "${!parts[@]}"; do echo -n "[s$k]"; done)"
  for k in "${!parts[@]}"; do
    IFS=',' read -r s e at <<<"${parts[$k]}"
    ms=$(python3 -c "print(int($at*1000))")
    AF+=";[s$k]atrim=$s:$e,asetpts=PTS-STARTPTS,adelay=$ms|$ms[l$k]"
    SPEECH+="[l$k]"
    NSP=$((NSP + 1))
  done
fi
if [[ $NSP -gt 1 ]]; then AF+=";${SPEECH}amix=inputs=$NSP:normalize=0:duration=longest,asplit=2[speech][key]"; else AF+=";${SPEECH}asplit=2[speech][key]"; fi
AF+=";
[6:a]aresample=48000,aformat=channel_layouts=stereo,atrim=0:37.6,volume=${MUSVOL:-0.9},afade=t=in:st=0:d=0.4,apad=whole_dur=37.6[mus];
[mus][key]sidechaincompress=threshold=0.03:ratio=5:attack=25:release=400[duck];
[amb][speech][duck][f1][f2][f3][f4][f5]amix=inputs=8:normalize=0:duration=first,atrim=0:37.59,loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[aout]"

INPUTS=(-i "$C1" -i "$C2" -i "$C3" -i "$C4" -i hero2_full.mp4 -loop 1 -framerate 24 -t 3.6 -i endcard2.jpg -i "$MUS" -i "$SFX")
[[ -n "$VO" ]] && INPUTS+=(-i "$VO")
ffmpeg -v error -y "${INPUTS[@]}" -filter_complex "$VF;$AF" -map "[v]" -map "[aout]" \
  -c:v libx264 -crf 17 -preset slow -pix_fmt yuv420p -c:a aac -b:a 192k -movflags +faststart "$OUT"
ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT"
