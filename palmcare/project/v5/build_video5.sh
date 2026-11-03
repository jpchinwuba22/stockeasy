#!/usr/bin/env bash
# Assemble PalmCare Video 5 ("After Dark") at 1080x1920.
# Usage: VO=vo.mp3 VOSEG="start,end,delay[,tempo];..." build_video5.sh OUT.mp4 MUSIC
set -euo pipefail
cd "$(dirname "$0")"
OUT=$1
MUS=$2
CS=../fonts/Cormorant-SemiBold.ttf
CI=../fonts/Cormorant-Italic.ttf
JM=../fonts/Jost-Medium.ttf
JR=../fonts/Jost-Regular.ttf
TOTAL=32.85

UP="scale=1080:1920:flags=lanczos,unsharp=5:5:0.55:5:5:0,setsar=1,fps=24"
# Night grade: deep plum shadows, rose highlights, rich (never lifted) skin.
GN="eq=contrast=1.07:saturation=1.08:gamma=0.99,colorbalance=rs=0.02:gs=-0.01:bs=0.04:rm=0.02:bm=0.01:rh=0.02:bh=-0.01,curves=all='0/0.015 0.25/0.22 0.5/0.5 0.75/0.79 1/0.98',vignette=PI/5,noise=alls=3:allf=t"
# Dawn grade: warm golden morning.
GD="eq=contrast=1.05:saturation=1.08:gamma=1.0,colorbalance=rs=0.04:gs=0.01:bs=-0.04:rm=0.03:bm=-0.03:rh=0.04:bh=-0.04,curves=all='0/0.02 0.5/0.52 1/0.98',vignette=PI/6,noise=alls=3:allf=t"
SRC="setpts=PTS-STARTPTS,setsar=1,fps=24"
MV() {
  local P="min(1\,on/($5*24))"
  local E; if [[ $6 == o ]]; then E="(1-pow(1-$P\,3))"; else E="($P*$P*(3-2*$P))"; fi
  echo "scale=2160:3840:flags=lanczos,zoompan=z='$1+($2-$1)*$E':x='iw/2-(iw/zoom/2)+$3*2*$E':y='ih/2-(ih/zoom/2)+$4*2*$E':d=1:s=1080x1920:fps=24,setsar=1"
}
WO() { echo "dblur=angle=$2:radius=26:enable='gte(t,$1-0.125)'"; }
WI() { echo "dblur=angle=$1:radius=26:enable='lt(t,0.125)'"; }
FLASH_OUT() { echo "fade=out:st=$1:d=0.12:color=0xFFD9E4"; }
FLASH_IN="fade=in:st=0:d=0.16:color=0xFFD9E4"
DIP_IN="fade=in:st=0:d=0.35:color=black"
# Kinetic title. $1 text $2 font $3 size $4 y-frac $5 start $6 end [$7 colour] [$8 shadow alpha]
TT() { echo "drawtext=fontfile=$2:text='$1':fontsize=$3:fontcolor=${7:-white}:x=(w-tw)/2:y=h*$4+22*(1-min(1\,max(0\,(t-$5)/0.4))):shadowcolor=black@${8:-0.55}:shadowx=0:shadowy=2:alpha='if(lt(t,$5),0,if(lt(t,$5+0.4),(t-$5)/0.4,if(lt(t,$6-0.25),1,max(0,($6-t)/0.25))))'"; }
# Editorial clock stamp at the top of frame. $1 text $2 start $3 end
CLK() { echo "drawtext=fontfile=$JM:text='$1':fontsize=38:fontcolor=0xFFE4EC:x=(w-tw)/2:y=h*0.075:shadowcolor=black@0.6:shadowx=0:shadowy=2:alpha='if(lt(t,$2),0,if(lt(t,$2+0.2),(t-$2)/0.2,if(lt(t,$3-0.15),0.92,max(0,($3-t)/0.15))))'"; }
CAP() { TT "$1" $JR 48 0.80 $2 $3 white 0.75; }
ROSE=0xF6C4CF

# Timeline: 0 moon portrait | 2.7 candle | 4.4 pat dry | 6.2 drop | 7.8 HERO | 10.6 press | 11.25 cheek |
# 12.75 label macro | 14.35 sleep | 16.65 night time-lapse | 18.65 dawn wake | 20.65 curtains | 22.75 mirror |
# 24.05 her line | 27.35 END CARD -> 32.85
VF="
[0:v]trim=0.15:2.85,$SRC,$UP,$(MV 1.00 1.12 0 -20 2.7 s),$GN,$DIP_IN,$(CLK '10\:47 PM' 0.2 2.6),$(TT 'A F T E R   D A R K' $CS 84 0.70 0.45 2.6),$(WO 2.7 0)[s1];
[0:v]trim=3.1:4.8,$SRC,$UP,$(MV 1.08 1.18 30 0 1.7 o),$GN,$(WI 0)[s2];
[0:v]trim=6.3:8.1,$SRC,$UP,$(MV 1.04 1.12 0 -20 1.8 s),$GN[s3];
[1:v]trim=0.55:2.15,$SRC,$UP,$(MV 1.05 1.16 0 30 1.6 s),$GN,$(FLASH_OUT 1.48)[s4];
[4:v]$SRC,$(TT 'DERMALUXE PRO' $JM 56 0.835 0.55 2.8 white 0.7),$(TT 'Hydrating Night Repair Serum' $CI 56 0.878 0.8 2.8 $ROSE 0.7),$(WO 2.8 0)[s5];
[1:v]trim=3.05:3.7,$SRC,$UP,$(MV 1.10 1.04 0 0 0.65 o),$GN,$(WI 0)[s6];
[1:v]trim=6.1:7.6,$SRC,$UP,$(MV 1.12 1.20 -30 -60 1.5 s),$GN,$(CAP 'Balance  ·  Clarify  ·  Deeply hydrate' 0.1 1.5),$(WO 1.5 90)[s7];
[5:v]$SRC,$(WI 90),$(TT 'Niacinamide  ·  Zinc PCA  ·  Salicylic Acid' $JM 40 0.86 0.2 1.6 white 0.75)[s8];
[2:v]trim=0.2:2.5,$SRC,$UP,$(MV 1.00 1.10 0 -20 2.3 s),$GN,$DIP_IN,$(CLK '11\:58 PM' 0.2 2.25),$(TT 'while you sleep.' $CI 76 0.78 0.5 2.3 white 0.7)[s9];
[2:v]trim=3.0:7.0,setpts=(PTS-STARTPTS)*0.5,$SRC,$UP,$(MV 1.04 1.14 20 0 2.0 s),$GN,$(CLK '1\:30 AM' 0.0 0.5),$(CLK '3\:15 AM' 0.5 1.0),$(CLK '4\:50 AM' 1.0 1.5),$(CLK '5\:58 AM' 1.5 2.0),fade=out:st=1.85:d=0.15:color=0xFFE8C8[s10];
[2:v]trim=7.0:9.0,$SRC,$UP,$(MV 1.06 1.00 0 0 2.0 o),$GD,fade=in:st=0:d=0.3:color=0xFFE8C8,$(CLK '6\:30 AM' 0.15 1.95)[s11];
[3:v]trim=0.4:2.5,$SRC,$UP,$(MV 1.00 1.10 0 -20 2.1 s),$GD,$(WO 2.1 0)[s12];
[3:v]trim=3.0:4.3,$SRC,$UP,$(MV 1.28 1.32 -70 -30 1.3 s),$GD,$(WI 0)[s13];
[3:v]trim=5.4:8.7,$SRC,$UP,$(MV 1.08 1.15 0 -30 3.3 s),$GD,$(FLASH_OUT 3.18)[s14];
[6:v]$SRC,format=yuv420p[s15];
[s1][s2][s3][s4][s5][s6][s7][s8][s9][s10][s11][s12][s13][s14][s15]concat=n=15:v=1:a=0[v]"

AS() { echo "[$1:a]atrim=$2:$3,asetpts=PTS-STARTPTS,aresample=48000,aformat=channel_layouts=stereo,afade=t=in:d=0.05,afade=t=out:st=$(python3 -c "print(round($3-$2-0.07,3))"):d=0.07[$4]"; }
SIL() { echo "anullsrc=r=48000:cl=stereo,atrim=0:$1[$2]"; }
VOSEGS() {
  local i=0 out="[7:a]aresample=48000,highpass=f=80,equalizer=f=250:t=q:w=1.2:g=-2,equalizer=f=3500:t=q:w=1.5:g=2.5,deesser=i=0.35,acompressor=threshold=-22dB:ratio=3:attack=8:release=120:makeup=3dB,aformat=channel_layouts=stereo,asplit=4[v1][v2][v3][v4];"
  IFS=';' read -ra SEGS <<< "$VOSEG"
  for seg in "${SEGS[@]}"; do
    i=$((i+1)); IFS=',' read -r st en dl tp <<< "$seg"; local ms=$(python3 -c "print(int(round($dl*1000)))")
    local tf=""; [[ -n "${tp:-}" ]] && tf=",atempo=$tp"
    out+="[v$i]atrim=$st:$en,asetpts=PTS-STARTPTS$tf,afade=t=in:d=0.03,adelay=$ms|$ms[l$i];"
  done
  echo "${out%;};"
}
AF="
$(AS 0 0.15 2.85 a1);$(AS 0 3.1 4.8 a2);$(AS 0 6.3 8.1 a3);$(AS 1 0.55 2.15 a4);$(SIL 2.8 a5);$(SIL 0.65 a6);$(SIL 1.5 a7);$(SIL 1.6 a8);
$(AS 2 0.2 2.5 a9);$(SIL 2.0 a10);$(AS 2 7.0 9.0 a11);$(AS 3 0.4 2.5 a12);$(AS 3 3.0 4.3 a13);
[a1][a2][a3][a4][a5][a6][a7][a8][a9][a10][a11][a12][a13]concat=n=13:v=0:a=1,volume=0.35,apad=whole_dur=$TOTAL[amb];
[3:a]atrim=5.4:8.7,asetpts=PTS-STARTPTS,aresample=48000,aformat=channel_layouts=stereo,afade=t=in:d=0.05,afade=t=out:st=3.2:d=0.1,volume=1.2,adelay=24050|24050,apad=whole_dur=$TOTAL[line];
$(VOSEGS)
[line][l1][l2][l3][l4]amix=inputs=5:normalize=0:duration=longest,apad=whole_dur=$TOTAL,asplit=2[speech][key];
[8:a]aresample=48000,aformat=channel_layouts=stereo,volume=0.75,asplit=2[r1][r2];
[r1]adelay=7550|7550[x1];[r2]adelay=12550|12550[x2];
[9:a]aresample=48000,aformat=channel_layouts=stereo,volume=0.85,adelay=27300|27300[x3];
[10:a]aresample=48000,aformat=channel_layouts=stereo,atrim=${MUSOFF:-0},asetpts=PTS-STARTPTS,atrim=0:$TOTAL,volume=${MUSVOL:-0.9},afade=t=out:st=$(python3 -c "print($TOTAL-0.8)"):d=0.8,apad=whole_dur=$TOTAL[mus];
[mus][key]sidechaincompress=threshold=0.015:ratio=8:attack=20:release=500:makeup=1[duck];
[amb][speech][duck][x1][x2][x3]amix=inputs=6:normalize=0:duration=first,atrim=0:$TOTAL,loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[aout]"

ffmpeg -v error -y -i C1.mp4 -i C2.mp4 -i C3.mp4 -i C4.mp4 -i hp_reveal.mp4 -i hp_macro.mp4 -i endcard5.mp4 -i "$VO" -i sfx_reveal5.mp3 -i sfx_card5.mp3 -i "$MUS" \
  -filter_complex "$VF;$AF" -map "[v]" -map "[aout]" \
  -c:v libx264 -crf 17 -preset slow -pix_fmt yuv420p -c:a aac -b:a 192k -movflags +faststart "$OUT"
ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT"
