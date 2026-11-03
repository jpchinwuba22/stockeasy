#!/usr/bin/env bash
# Assemble PalmCare Video 4 ("Still Water") at 1080x1920.
# Usage: build_video4.sh OUT.mp4 [MUSIC]   (no music -> silent bed, e.g. for scoring)
set -euo pipefail
cd "$(dirname "$0")"
OUT=$1
MUS=${2:-}
CI=../fonts/Cormorant-Italic.ttf
CM=../fonts/Cormorant-Medium.ttf
JL=../fonts/Jost-Light.ttf
JM=../fonts/Jost-Medium.ttf
TOTAL=37.0

# 720p clips -> 1080x1920, lanczos with a touch of sharpening for crisp skin texture.
UP="scale=1080:1920:flags=lanczos,unsharp=5:5:0.55:5:5:0,setsar=1,fps=24"
# Grade: cool aqua shadows, warm skin highlights, rich (never lifted/lightened) skin, gentle S-curve.
G="eq=contrast=1.06:saturation=1.07:gamma=1.0,colorbalance=rs=-0.03:gs=0.01:bs=0.03:rh=0.03:bh=-0.03,curves=all='0/0.02 0.25/0.23 0.5/0.51 0.75/0.78 1/0.98',vignette=PI/7,noise=alls=3:allf=t"
# Golden-hour grade for the rooftop scenes.
GW="eq=contrast=1.06:saturation=1.10:gamma=0.99,colorbalance=rs=0.04:gs=0.01:bs=-0.04:rm=0.03:bm=-0.03:rh=0.05:gh=0.01:bh=-0.05,curves=all='0/0.02 0.5/0.51 1/0.98',vignette=PI/6,noise=alls=3:allf=t"
SRC="setpts=PTS-STARTPTS,setsar=1,fps=24"
# Camera move: eased zoom z0->z1 with pan (dx,dy output px). $6 o=ease-out s=smooth
MV() {
  local P="min(1\,on/($5*24))"
  local E; if [[ $6 == o ]]; then E="(1-pow(1-$P\,3))"; else E="($P*$P*(3-2*$P))"; fi
  echo "scale=2160:3840:flags=lanczos,zoompan=z='$1+($2-$1)*$E':x='iw/2-(iw/zoom/2)+$3*2*$E':y='ih/2-(ih/zoom/2)+$4*2*$E':d=1:s=1080x1920:fps=24,setsar=1"
}
WO() { echo "dblur=angle=$2:radius=26:enable='gte(t,$1-0.125)'"; }
WI() { echo "dblur=angle=$1:radius=26:enable='lt(t,0.125)'"; }
FLASH_OUT() { echo "fade=out:st=$1:d=0.12:color=0xEAF8F6"; }
FLASH_IN="fade=in:st=0:d=0.16:color=0xEAF8F6"
# Kinetic title: fade + 22px rise. $1 text $2 font $3 size $4 y-frac $5 start $6 end [$7 colour] [$8 shadow alpha]
TT() { echo "drawtext=fontfile=$2:text='$1':fontsize=$3:fontcolor=${7:-white}:x=(w-tw)/2:y=h*$4+22*(1-min(1\,max(0\,(t-$5)/0.4))):shadowcolor=black@${8:-0.45}:shadowx=0:shadowy=2:alpha='if(lt(t,$5),0,if(lt(t,$5+0.4),(t-$5)/0.4,if(lt(t,$6-0.25),1,max(0,($6-t)/0.25))))'"; }
# Caption (subtitle for the voiceover), lower third, light sans with a soft shadow.
CAP() { TT "$1" ../fonts/Jost-Regular.ttf 48 0.80 $2 $3 white 0.75; }
INK=0x0E4248

# Timeline (s): 0 face | 2.6 ripple (slow-mo) | 4.3 dropper | 6.2 N10 | 8.8 palms | 10.8 cheek macro |
# 13.4 N10 label | 14.8 cream | 16.8 JAR | 19.4 apply | 20.9 mirror | 22.7 duo | 25.7 walk | 28.0 profile |
# 29.5 her line | 32.4 end card -> 37.0
VF="
[0:v]trim=0.15:2.75,$SRC,$UP,$(MV 1.00 1.10 0 -20 2.6 s),$G,$(TT 'Still water.' $CI 96 0.70 0.35 1.55),$(TT 'Even skin.' $CI 96 0.70 1.6 2.6),$(WO 2.6 0)[s1];
[0:v]trim=3.25:4.27,setpts=(PTS-STARTPTS)/0.6,minterpolate=fps=24:mi_mode=mci:mc_mode=aobmc:vsbmc=1,$SRC,$UP,$(MV 1.04 1.14 -20 0 1.7 o),$G,$(WI 0)[s2];
[1:v]trim=0.55:2.45,$SRC,$UP,$(MV 1.04 1.14 0 30 1.9 s),$G,$(FLASH_OUT 1.78)[s3];
[4:v]$SRC,$FLASH_IN,$(TT 'N10 NIACINAMIDE SERUM' $JM 50 0.845 0.35 2.6 $INK 0),$(TT 'Advanced EvenTone Care' $CI 52 0.885 0.6 2.6 $INK 0),$(WO 2.6 0)[s4];
[1:v]trim=3.15:5.15,$SRC,$UP,$(MV 1.10 1.00 0 -20 2.0 o),$G,$(WI 0),$(CAP 'Advanced even-tone care' 0.1 2.0)[s5];
[1:v]trim=6.2:8.8,$SRC,$UP,$(MV 1.06 1.14 -40 0 2.6 s),$G,$(CAP 'Hydration  ·  Radiance  ·  Refined pores' 0.15 2.5),$(WO 2.6 90)[s6];
[5:v]$SRC,$(WI 90),$(WO 1.4 0)[s7];
[2:v]trim=0.35:2.35,$SRC,$UP,$(MV 1.00 1.12 0 -30 2.0 o),$G,$(WI 0),$(FLASH_OUT 1.88)[s8];
[6:v]$SRC,$FLASH_IN,$(TT 'VITAMIN C FACE MOISTURISER' $JM 46 0.845 0.35 2.6 $INK 0),$(TT 'Hydrating  ·  Tone refining' $CI 52 0.885 0.6 2.6 $INK 0)[s9];
[2:v]trim=3.05:4.55,$SRC,$UP,$(MV 1.08 1.00 0 0 1.5 o),$G[s10];
[2:v]trim=7.1:8.9,$SRC,$UP,$(MV 1.00 1.08 20 0 1.8 s),$G,$(CAP 'Hydrated.  Refined.  Even.' 0.1 1.8),$(FLASH_OUT 1.68)[s11];
[7:v]$SRC,$FLASH_IN,$(TT 'Serum, then moisturiser.' $CI 62 0.855 0.45 3.0 $INK 0),$(TT 'E V E R Y   S I N G L E   D A Y' $JM 34 0.905 0.75 3.0 $INK 0),$(FLASH_OUT 2.88)[s12];
[3:v]trim=0.25:2.55,$SRC,$UP,$(MV 1.00 1.10 0 -20 2.3 s),$GW,$FLASH_IN[s13];
[3:v]trim=3.15:4.65,$SRC,$UP,$(MV 1.04 1.12 -20 0 1.5 o),$GW[s14];
[3:v]trim=5.0:7.9,$SRC,$UP,$(MV 1.10 1.17 0 -30 2.9 s),$GW,$(CAP 'Even tone. Every single day.' 0.25 2.85)[s15];
[8:v]$SRC,format=yuv420p[s16];
[s1][s2][s3][s4][s5][s6][s7][s8][s9][s10][s11][s12][s13][s14][s15][s16]concat=n=16:v=1:a=0[v]"

VOSEGS() {
  local i=0 out="[9:a]aresample=48000,highpass=f=80,equalizer=f=250:t=q:w=1.2:g=-2,equalizer=f=3500:t=q:w=1.5:g=2.5,deesser=i=0.35,acompressor=threshold=-22dB:ratio=3:attack=8:release=120:makeup=3dB,aformat=channel_layouts=stereo,asplit=5[v1][v2][v3][v4][v5];"
  IFS=';' read -ra SEGS <<< "$VOSEG"
  for seg in "${SEGS[@]}"; do
    i=$((i+1)); IFS=',' read -r st en dl <<< "$seg"; local ms=$(python3 -c "print(int(round($dl*1000)))")
    out+="[v$i]atrim=$st:$en,asetpts=PTS-STARTPTS,afade=t=in:d=0.03,adelay=$ms|$ms[l$i];"
  done
  echo "${out%;};"
}
AS() { echo "[$1:a]atrim=$2:$3,asetpts=PTS-STARTPTS,aresample=48000,aformat=channel_layouts=stereo,afade=t=in:d=0.05,afade=t=out:st=$(python3 -c "print(round($3-$2-0.07,3))"):d=0.07[$4]"; }
SIL() { echo "anullsrc=r=48000:cl=stereo,atrim=0:$1[$2]"; }
AF="
$(AS 0 0.15 2.75 a1);$(AS 0 3.25 4.95 a2);$(AS 1 0.55 2.45 a3);$(SIL 2.6 a4);$(AS 1 3.15 5.15 a5);$(AS 1 6.2 8.8 a6);$(SIL 1.4 a7);
$(AS 2 0.35 2.35 a8);$(SIL 2.6 a9);$(AS 2 3.05 4.55 a10);$(AS 2 7.1 8.9 a11);$(SIL 3.0 a12);$(AS 3 0.25 2.55 a13);$(AS 3 3.15 4.65 a14);
[a1][a2][a3][a4][a5][a6][a7][a8][a9][a10][a11][a12][a13][a14]concat=n=14:v=0:a=1,volume=0.35,apad=whole_dur=$TOTAL[amb];
[3:a]atrim=5.0:7.9,asetpts=PTS-STARTPTS,aresample=48000,aformat=channel_layouts=stereo,afade=t=in:d=0.05,afade=t=out:st=2.8:d=0.1,volume=1.2,adelay=29500|29500,apad=whole_dur=$TOTAL[line];
$(VOSEGS)
[line][l1][l2][l3][l4][l5]amix=inputs=6:normalize=0:duration=longest,apad=whole_dur=$TOTAL,asplit=2[speech][key];
[10:a]aresample=48000,aformat=channel_layouts=stereo,volume=0.7,asplit=4[r1][r2][r3][r4];
[r1]adelay=5650|5650[x1];[r2]adelay=12850|12850[x2];[r3]adelay=16250|16250[x3];[r4]adelay=22150|22150[x4];
[11:a]aresample=48000,aformat=channel_layouts=stereo,volume=0.8,adelay=32350|32350[x5]"
if [[ -n "$MUS" ]]; then
  AF+=";[12:a]aresample=48000,aformat=channel_layouts=stereo,atrim=${MUSOFF:-0},asetpts=PTS-STARTPTS,atrim=0:$TOTAL,volume=${MUSVOL:-0.9},afade=t=out:st=$(python3 -c "print($TOTAL-1.0)"):d=1.0,apad=whole_dur=$TOTAL[mus]"
else
  AF+=";anullsrc=r=48000:cl=stereo,atrim=0:$TOTAL[mus]"
fi
AF+=";[mus][key]sidechaincompress=threshold=0.015:ratio=8:attack=20:release=500:makeup=1[duck];
[amb][speech][duck][x1][x2][x3][x4][x5]amix=inputs=8:normalize=0:duration=first,atrim=0:$TOTAL,loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[aout]"

INPUTS=(-i C1.mp4 -i C2.mp4 -i C3.mp4 -i C4.mp4 -i hp_n10.mp4 -i hp_n10macro.mp4 -i hp_jar.mp4 -i hp_duo.mp4
        -i endcard4.mp4 -i "${VO:-v4_vo.mp3}" -i sfx_reveal4.mp3 -i sfx_card4.mp3)
[[ -n "$MUS" ]] && INPUTS+=(-i "$MUS")
ffmpeg -v error -y "${INPUTS[@]}" -filter_complex "$VF;$AF" -map "[v]" -map "[aout]" \
  -c:v libx264 -crf 17 -preset slow -pix_fmt yuv420p -c:a aac -b:a 192k -movflags +faststart "$OUT"
ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT"
