#!/usr/bin/env bash
# Assemble PalmCare Video 6 ("Tropical Glow") at 1080x1920: graded picture -> base6.mp4, full mix -> mix6.wav.
# Captions, pop-ups and titles are added afterwards by overlay6.py.
# Usage: build_video6.sh MUSIC
set -euo pipefail
cd "$(dirname "$0")"
MUS=$1
TOTAL=37.6

UP="scale=1080:1920:flags=lanczos,unsharp=5:5:0.55:5:5:0,setsar=1,fps=24"
# Tropical gold grade: warm honey highlights, soft teal-green shadows, rich (never lifted/lightened) skin.
G="eq=contrast=1.06:saturation=1.08:gamma=0.99,colorbalance=rs=0.02:gs=0.0:bs=-0.03:rm=0.03:gm=0.01:bm=-0.03:rh=0.03:bh=-0.04,curves=all='0/0.015 0.25/0.235 0.5/0.505 0.75/0.775 1/0.985',vignette=PI/6,noise=alls=3:allf=t"
# Golden-hour beach: warm the blue sky slightly so it sits with the rest of the film.
GB="eq=contrast=1.06:saturation=1.07:gamma=0.99,colorbalance=rs=0.05:gs=0.01:bs=-0.05:rm=0.04:bm=-0.04:rh=0.04:bh=-0.05,curves=all='0/0.015 0.5/0.505 1/0.985',vignette=PI/6,noise=alls=3:allf=t"
SRC="setpts=PTS-STARTPTS,setsar=1,fps=24"
MV() {
  local P="min(1\,on/($5*24))"
  local E; if [[ $6 == o ]]; then E="(1-pow(1-$P\,3))"; else E="($P*$P*(3-2*$P))"; fi
  echo "scale=2160:3840:flags=lanczos,zoompan=z='$1+($2-$1)*$E':x='iw/2-(iw/zoom/2)+$3*2*$E':y='ih/2-(ih/zoom/2)+$4*2*$E':d=1:s=1080x1920:fps=24,setsar=1"
}
WO() { echo "dblur=angle=$2:radius=26:enable='gte(t,$1-0.125)'"; }
WI() { echo "dblur=angle=$1:radius=26:enable='lt(t,0.125)'"; }
FLASH_OUT() { echo "fade=out:st=$1:d=0.12:color=0xFFF0D6"; }
FLASH_IN="fade=in:st=0:d=0.16:color=0xFFF0D6"
DIP_IN="fade=in:st=0:d=0.35:color=black"

# Timeline: 0 drone | 2.6 face | 4.6 TROPICAL GLOW reveal | 7.4 gel macro | 9.4 lather | 11.2 rinse | 13.2 rack focus |
# 15.4 DERMALIGHT reveal | 18.2 lotion macro | 20.0 arm | 22.0 window smile | 24.2 beach walk | 26.4 braids |
# 27.9 her line | 30.4 END CARD -> 37.6
VF="
[0:v]trim=0.0:2.6,$SRC,$UP,$(MV 1.00 1.16 0 30 2.6 s),$G,$DIP_IN[s1];
[1:v]trim=0.2:2.2,$SRC,$UP,$(MV 1.02 1.12 0 -20 2.0 s),$G,$(FLASH_OUT 1.88)[s2];
[4:v]$SRC,$FLASH_IN,$(WO 2.8 90)[s3];
[1:v]trim=3.1:5.1,$SRC,$UP,$(MV 1.00 1.12 0 10 2.0 o),$G,$(WI 90)[s4];
[1:v]trim=6.0:7.8,$SRC,$UP,$(MV 1.06 1.14 -20 -10 1.8 s),$G,$(WO 1.8 0)[s5];
[0:v]trim=3.0:5.0,$SRC,$UP,$(MV 1.08 1.14 -40 0 2.0 s),$G,$(WI 0)[s6];
[0:v]trim=6.05:8.25,$SRC,$UP,$(MV 1.00 1.07 0 -20 2.2 s),$G,$(FLASH_OUT 2.08)[s7];
[5:v]$SRC,$FLASH_IN,$(WO 2.8 90)[s8];
[2:v]trim=0.5:2.3,$SRC,$UP,$(MV 1.04 1.12 0 0 1.8 o),$G,$(WI 90)[s9];
[2:v]trim=4.7:6.7,$SRC,$UP,$(MV 1.06 1.12 -20 -20 2.0 s),$G[s10];
[2:v]trim=7.3:9.5,$SRC,$UP,$(MV 1.00 1.08 0 -20 2.2 s),$G,$(WO 2.2 0)[s11];
[3:v]trim=0.1:2.3,$SRC,$UP,$(MV 1.00 1.08 0 -10 2.2 s),$GB,$(WI 0),$(WO 2.2 0)[s12];
[3:v]trim=3.1:4.6,$SRC,$UP,$(MV 1.04 1.10 0 -10 1.5 o),$GB,$(WI 0)[s13];
[3:v]trim=4.9:7.4,$SRC,$UP,$(MV 1.00 1.06 0 -20 2.5 s),$GB,$(FLASH_OUT 2.38)[s14];
[6:v]$SRC,format=yuv420p[s15];
[s1][s2][s3][s4][s5][s6][s7][s8][s9][s10][s11][s12][s13][s14][s15]concat=n=15:v=1:a=0[v]"

AS() { echo "[$1:a]atrim=$2:$3,asetpts=PTS-STARTPTS,aresample=48000,aformat=channel_layouts=stereo,afade=t=in:d=0.05,afade=t=out:st=$(python3 -c "print(round($3-$2-0.07,3))"):d=0.07[$4]"; }
SIL() { echo "anullsrc=r=48000:cl=stereo,atrim=0:$1[$2]"; }
VOSEGS() {
  local i=0 n out
  n=$(python3 -c "import timeline6 as t; print(len(t.VOSEG))")
  out="[7:a]aresample=48000,highpass=f=70,equalizer=f=250:t=q:w=1.2:g=-1.5,equalizer=f=3500:t=q:w=1.5:g=2,acompressor=threshold=-22dB:ratio=3:attack=8:release=120:makeup=3dB,aformat=channel_layouts=stereo,asplit=$n"
  for ((k=1; k<=n; k++)); do out+="[v$k]"; done
  out+=";"
  while IFS=',' read -r st en dl; do
    i=$((i+1)); local ms=$(python3 -c "print(int(round($dl*1000)))")
    out+="[v$i]atrim=$st:$en,asetpts=PTS-STARTPTS,afade=t=in:d=0.03,afade=t=out:st=$(python3 -c "print(round($en-$st-0.06,3))"):d=0.06,adelay=$ms|$ms[l$i];"
  done < <(python3 -c "import timeline6 as t; [print(f'{a},{b},{c}') for a,b,c in t.VOSEG]")
  local mix=""; for ((k=1; k<=i; k++)); do mix+="[l$k]"; done
  echo "${out}${mix}amix=inputs=$i:normalize=0:duration=longest,apad=whole_dur=$TOTAL[vo]"
}
AF="
$(AS 0 0.0 2.6 a1r);[a1r]volume=0.3[a1];$(AS 1 0.2 2.2 a2);$(SIL 2.8 a3);$(AS 1 3.1 5.1 a4);$(AS 1 6.0 7.8 a5);$(AS 0 3.0 5.0 a6);$(AS 0 6.05 8.25 a7);
$(SIL 2.8 a8);$(AS 2 0.5 2.3 a9);$(AS 2 4.7 6.7 a10);$(AS 2 7.3 9.5 a11);$(AS 3 0.1 2.3 a12);$(AS 3 3.1 4.6 a13);$(AS 3 0.1 2.6 a14);
[a1][a2][a3][a4][a5][a6][a7][a8][a9][a10][a11][a12][a13][a14]concat=n=14:v=0:a=1,volume=0.32,apad=whole_dur=$TOTAL[amb];
[8:a]atrim=4.9:7.4,asetpts=PTS-STARTPTS,aresample=48000,aformat=channel_layouts=stereo,highpass=f=80,equalizer=f=3000:t=q:w=1.5:g=1.5,acompressor=threshold=-22dB:ratio=2.5:attack=8:release=120:makeup=2dB,afade=t=in:d=0.05,afade=t=out:st=2.4:d=0.1,volume=1.15,adelay=27900|27900,apad=whole_dur=$TOTAL[line];
$(VOSEGS);
[vo][line]amix=inputs=2:normalize=0:duration=longest,apad=whole_dur=$TOTAL,asplit=2[speech][key];
[9:a]aresample=48000,aformat=channel_layouts=stereo,volume=0.7,asplit=2[r1][r2];
[r1]adelay=4550|4550[x1];[r2]adelay=15350|15350[x2];
[10:a]aresample=48000,aformat=channel_layouts=stereo,volume=0.8,adelay=30350|30350[x3];
[11:a]aresample=48000,aformat=channel_layouts=stereo,atrim=${MUSOFF:-0},asetpts=PTS-STARTPTS,atrim=0:$TOTAL,volume=${MUSVOL:-0.85},afade=t=in:d=0.6,afade=t=out:st=$(python3 -c "print($TOTAL-0.9)"):d=0.9,apad=whole_dur=$TOTAL[mus];
[mus][key]sidechaincompress=threshold=0.015:ratio=8:attack=20:release=450:makeup=1[duck];
[amb][speech][duck][x1][x2][x3]amix=inputs=6:normalize=0:duration=first,atrim=0:$TOTAL,loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[aout]"

ffmpeg -v error -y -i C2.mp4 -i C1.mp4 -i C3.mp4 -i C4.mp4 -i hp_trop.mp4 -i hp_derm.mp4 -i endcard6.mp4 \
  -i vo2/vo_new.wav -i line_sts.mp3 -i ../v4/sfx_reveal4.mp3 -i ../v4/sfx_card4.mp3 -i "$MUS" \
  -filter_complex "$VF;$AF" -map "[v]" -map "[aout]" \
  -c:v libx264 -crf 14 -preset slow -pix_fmt yuv420p -c:a pcm_s16le base6.mov
ffprobe -v error -show_entries format=duration -of csv=p=0 base6.mov
