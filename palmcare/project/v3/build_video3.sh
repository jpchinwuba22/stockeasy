#!/usr/bin/env bash
# Assemble PalmCare Video 3 ("Shadow & Light") at 1080x1920.
# Usage: build_video3.sh OUT.mp4 [MUSIC.mp3]   (no music -> silent music bed, for scoring)
set -euo pipefail
cd "$(dirname "$0")"
U=/root/.claude/uploads/ae1b3550-c976-5b71-9f6e-2d57965fb3f7
C1="$U/c576f5a8-Woman_turning_face_into_light_20261022081204.mp4"
C2="$U/782b20af-Serum_drop_falling_and_splashing_20261022081415.mp4"
C3="$U/fe59b967-Skincare_campaign_film_applying___20261022081558.mp4"
C4="$U/41122a72-Woman_walking_and_speaking_20261022081943.mp4"
OUT=$1
MUS=${2:-}
PF=../fonts/Playfair-Medium.ttf
PI=../fonts/Playfair-Italic.ttf
MO=../fonts/Montserrat-Medium.ttf
TOTAL=34.4

UP="scale=1080:1920:flags=lanczos,setsar=1,fps=24"
# Brighter, luminous warm grade: lifted shadows, gentle contrast, light vignette.
G="eq=contrast=1.04:brightness=0.025:saturation=1.10:gamma=1.07,curves=all='0/0.035 0.5/0.56 1/1',colorbalance=rs=0.04:bs=-0.05:rm=0.03:bm=-0.04:rh=0.02:bh=-0.03,vignette=PI/8,noise=alls=2:allf=t"
# Camera move on a clip: upscale 2x, eased zoom z0->z1 with pan dx,dy (output px) over the segment.
# $1 z0 $2 z1 $3 dx $4 dy $5 dur $6 ease(o=ease-out, s=smooth)
MV() {
  local P="min(1\,on/($5*24))"
  local E; if [[ $6 == o ]]; then E="(1-pow(1-$P\,3))"; else E="($P*$P*(3-2*$P))"; fi
  echo "scale=2160:3840:flags=lanczos,zoompan=z='$1+($2-$1)*$E':x='iw/2-(iw/zoom/2)+$3*2*$E':y='ih/2-(ih/zoom/2)+$4*2*$E':d=1:s=1080x1920:fps=24,setsar=1"
}
# Whip transitions: directional motion blur on the last/first frames of a cut.
WO() { echo "dblur=angle=$2:radius=28:enable='gte(t,$1-0.125)'"; }
WI() { echo "dblur=angle=$1:radius=28:enable='lt(t,0.125)'"; }
# Kinetic title: fade in with a 24px rise, hold, fade out before the cut. $1 text $2 font $3 size $4 y-fraction $5 start $6 end
TT() { echo "drawtext=fontfile=$2:text='$1':fontsize=$3:fontcolor=${7:-white}:x=(w-tw)/2:y=h*$4+24*(1-min(1\,max(0\,(t-$5)/0.35))):shadowcolor=black@${8:-0.5}:shadowx=0:shadowy=3:alpha='if(lt(t,$5),0,if(lt(t,$5+0.35),(t-$5)/0.35,if(lt(t,$6-0.25),1,max(0,($6-t)/0.25))))'"; }
FLASH_OUT() { echo "fade=out:st=$1:d=0.12:color=0xFFE2B8"; }
FLASH_IN="fade=in:st=0:d=0.14:color=0xFFE2B8"
SRC="setpts=PTS-STARTPTS,setsar=1,fps=24"

# Timeline (s): 0 eyes | 2.6 shadows | 5.0 drop | 7.0 VITA C+ | 9.6 splash | 12.25 press | 13.6 swatch |
# 15.4 GLOWSHIELD | 17.8 macro | 19.2 no white cast | 21.6 duo | 24.8 walk | 27.0 sun | 28.4 line | 31.0 card -> 34.4
VF="
[0:v]trim=0.04:2.64,$SRC,$(MV 1.00 1.16 0 -30 2.6 o),$G,$(TT 'Lagos sun.' $PI 110 0.70 0.5 2.6),$(WO 2.6 0)[s1];
[0:v]trim=3.0:5.4,$SRC,$(MV 1.14 1.00 0 40 2.4 s),$G,$(WI 0),$(TT 'M E E T   Y O U R   M A T C H' $MO 46 0.74 0.2 2.4),$(WO 2.4 90)[s2];
[1:v]trim=0.1:2.1,$SRC,$(MV 1.00 1.20 0 60 2.0 s),$G,$(WI 90),$(FLASH_OUT 1.88)[s3];
[4:v]$SRC,$FLASH_IN,$(TT 'V I T A   C +   S E R U M' $MO 50 0.845 0.3 2.6 0x3B2213 0),$(TT 'Ultra-active vitamin C' $PI 46 0.885 0.55 2.6 0x3B2213 0),$(WO 2.6 0)[s4];
[1:v]trim=3.05:5.7,$SRC,$(MV 1.00 1.28 0 30 2.65 o),$G,$(WI 0)[s5];
[1:v]trim=8.6:9.95,$SRC,$(MV 1.10 1.00 -20 0 1.35 o),$G,$(WO 1.35 0)[s6];
[12:v]$SRC,$(WI 0)[s7];
[5:v]$SRC,$(TT 'G L O W S H I E L D' $MO 54 0.845 0.25 2.4 0x3B2213 0),$(TT 'SPF 50+  ·  PA++++  ·  Broad-spectrum' $PI 42 0.885 0.5 2.4 0x3B2213 0)[s8];
[6:v]$SRC,$(WO 1.4 90)[s9];
[2:v]trim=7.0:9.4,$SRC,$(MV 1.22 1.00 0 -40 2.4 o),$G,$(WI 90),$(TT 'N O   W H I T E   C A S T' $MO 52 0.62 0.3 2.4),$(FLASH_OUT 2.28)[s10];
[7:v]$SRC,$FLASH_IN,$(TT 'Serum  +  SPF.  Every morning.' $PI 50 0.88 0.6 3.2 0x3B2213 0),$(FLASH_OUT 3.08)[s11];
[3:v]trim=0.2:2.4,$SRC,$(MV 1.00 1.12 0 -20 2.2 s),$G,$FLASH_IN[s12];
[3:v]trim=3.2:4.6,$SRC,$(MV 1.04 1.16 0 -30 1.4 o),$G[s13];
[3:v]trim=5.9:8.5,$SRC,$(MV 1.00 1.07 0 -10 2.6 s),$G[s14];
[8:v]scale=1188:2112,zoompan=z='1+0.0006*on':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=1080x1920:fps=24,setsar=1,fade=in:st=0:d=0.35,format=yuv420p[s15];
[s1][s2][s3][s4][s5][s6][s7][s8][s9][s10][s11][s12][s13][s14][s15]concat=n=15:v=1:a=0[v]"

# Each clip's own sound cut with its picture (de-clicked); product shots are silent here.
AS() { echo "[$1:a]atrim=$2:$3,asetpts=PTS-STARTPTS,aresample=48000,aformat=channel_layouts=stereo,afade=t=in:d=0.05,afade=t=out:st=$(python3 -c "print(round($3-$2-0.07,3))"):d=0.07[$4]"; }
SIL() { echo "anullsrc=r=48000:cl=stereo,atrim=0:$1[$2]"; }
AF="
$(AS 0 0.04 2.64 a1);$(AS 0 3.0 5.4 a2);$(AS 1 0.1 2.1 a3);$(SIL 2.6 a4);$(AS 1 3.05 5.7 a5);$(AS 1 8.6 9.95 a6);$(SIL 1.8 a7);
$(SIL 2.4 a8);$(SIL 1.4 a9);$(AS 2 7.0 9.4 a10);$(SIL 3.2 a11);$(AS 3 0.2 2.4 a12);$(AS 3 3.2 4.6 a13);
[a1][a2][a3][a4][a5][a6][a7][a8][a9][a10][a11][a12][a13]concat=n=13:v=0:a=1,volume=0.4,apad=whole_dur=$TOTAL[amb];
[3:a]atrim=5.9:8.5,asetpts=PTS-STARTPTS,aresample=48000,aformat=channel_layouts=stereo,afade=t=in:d=0.05,afade=t=out:st=2.5:d=0.1,volume=1.15,adelay=28400|28400,apad=whole_dur=$TOTAL[line];
[9:a]aresample=48000,aformat=channel_layouts=stereo,asplit=4[v1][v2][v3][v4];
[v1]atrim=0:2.5,asetpts=PTS-STARTPTS,adelay=600|600[l1];
[v2]atrim=2.6:8.2,asetpts=PTS-STARTPTS,adelay=7150|7150[l2];
[v3]atrim=8.4:13.45,asetpts=PTS-STARTPTS,adelay=15550|15550[l3];
[v4]atrim=13.55:16.04,asetpts=PTS-STARTPTS,adelay=31450|31450[l4];
[line][l1][l2][l3][l4]amix=inputs=5:normalize=0:duration=longest,apad=whole_dur=$TOTAL,asplit=2[speech][key];
[10:a]aresample=48000,aformat=channel_layouts=stereo,volume=0.55,asplit=3[h1][h2][h3];
[h1]adelay=0|0[x1];[h2]adelay=19000|19000[x2];[h3]adelay=30850|30850[x3];
[11:a]aresample=48000,aformat=channel_layouts=stereo,volume=0.6,asplit=5[g1][g2][g3][g4][g5];
[g1]adelay=6700|6700[y1];[g2]adelay=13300|13300[y5];[g3]adelay=15100|15100[y2];[g4]adelay=17500|17500[y3];[g5]adelay=21300|21300[y4]"
if [[ -n "$MUS" ]]; then
  AF+=";[13:a]aresample=48000,aformat=channel_layouts=stereo,atrim=0:$TOTAL,volume=${MUSVOL:-0.95},afade=t=out:st=$(python3 -c "print($TOTAL-1.2)"):d=1.2,apad=whole_dur=$TOTAL[mus]"
else
  AF+=";anullsrc=r=48000:cl=stereo,atrim=0:$TOTAL[mus]"
fi
AF+=";[mus][key]sidechaincompress=threshold=0.03:ratio=5:attack=25:release=400[duck];
[amb][speech][duck][x1][x2][x3][y1][y2][y3][y4][y5]amix=inputs=11:normalize=0:duration=first,atrim=0:$TOTAL,loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[aout]"

INPUTS=(-i "$C1" -i "$C2" -i "$C3" -i "$C4" -i hc_vitac.mp4 -i hc_glow.mp4 -i hc_macro.mp4 -i hc_duo.mp4
        -loop 1 -framerate 24 -t 3.4 -i endcard3.jpg -i v3_vo.mp3 -i sfx_hit.mp3 -i sfx_reveal.mp3 -i hc_glowrev.mp4)
[[ -n "$MUS" ]] && INPUTS+=(-i "$MUS")
ffmpeg -v error -y "${INPUTS[@]}" -filter_complex "$VF;$AF" -map "[v]" -map "[aout]" \
  -c:v libx264 -crf 17 -preset slow -pix_fmt yuv420p -c:a aac -b:a 192k -movflags +faststart "$OUT"
ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT"
