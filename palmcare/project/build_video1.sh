#!/usr/bin/env bash
# Assemble PalmCare Video 1 (Cacao Ritual) at 1080x1920 from the generated clips,
# the product hero, voiceover, music and SFX.
set -euo pipefail
cd "$(dirname "$0")"
U=/root/.claude/uploads/ae1b3550-c976-5b71-9f6e-2d57965fb3f7
SH="$U/6b8991f1-Woman_applying_skincare_lather_i__20261021214523.mp4"
WH="$U/7988fac5-Woman_holding_bottle_smiling_20261021213655.mp4"
L1="$U/84607086-Woman_applying_skincare_lotion_20261021224931.mp4"
L2="$U/21f3ccc5-Woman_applying_luxury_skincare_l__20261021225451.mp4"
C4="$U/c69425a0-Woman_speaking_into_camera_20261021230419.mp4"
HERO=hero/hero_full.mp4
VO=vo/vo1_take1.mp3
MUS=music/v1_music_B.mp3
SFX=sfx/shimmer.mp3
OUT=${1:-video1_v6.mp4}

SERIF=/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf
SANS=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf
UP="scale=1080:1920:flags=lanczos,setsar=1,fps=24"
G="eq=contrast=1.06:saturation=1.12:gamma=0.98,colorbalance=rs=0.05:gs=0.01:bs=-0.05:rm=0.04:bm=-0.04:rh=0.02:bh=-0.03,vignette=PI/5"
LT() { echo "drawbox=x=0:y=ih*0.80:w=iw:h=ih*0.11:color=black@0.35:t=fill,drawtext=fontfile=$SERIF:text='$1':fontsize=66:fontcolor=white:x=(w-tw)/2:y=h*0.815,drawtext=fontfile=$SANS:text='$2':fontsize=34:fontcolor=white@0.9:x=(w-tw)/2:y=h*0.866"; }
SEG() { echo "[$1:v]trim=$2:$3,setpts=PTS-STARTPTS,$UP${4:+,$4}[$5]"; }

# Timeline (seconds): shower 0-7.5 | wash 7.5-11 | palm 11-11.95 | rub 11.95-13.45 | swirl 13.45-16.3
# forearm 16.3-19.15 | shoulder 19.15-22.05 | hero 22.05-26.85 | line 26.85-31.65 | end card 31.65-35.05
ffmpeg -v error -y -i "$SH" -i "$WH" -i "$L1" -i "$L2" -i "$HERO" -i "$C4" \
  -f lavfi -i "color=c=0xF3EDE4:s=1080x1920:d=3.4:r=24" -i "$VO" -i "$MUS" -i "$SFX" \
  -filter_complex "
$(SEG 0 0.3 7.8 "$G,drawtext=fontfile=$SERIF:text='The Ritual After':fontsize=80:fontcolor=white:x=(w-tw)/2:y=h*0.12:alpha='if(lt(t,0.4),0,if(lt(t,1),(t-0.4)/0.6,if(lt(t,2),1,if(lt(t,2.5),(2.5-t)/0.5,0))))':shadowcolor=black@0.4:shadowx=3:shadowy=3,fade=in:st=0:d=0.4" v0);
$(SEG 1 1.5 5.0 "$G,$(LT 'Milky Hydro-Glow' 'MOISTURIZING BODY WASH')" v1);
$(SEG 2 2.0 2.95 "$G" v2);
$(SEG 2 3.05 4.55 "$G" v3);
$(SEG 3 0.1 2.95 "$G,$(LT 'Cacao and Collagen' 'BODY LOTION')" v4);
$(SEG 3 3.05 5.9 "$G" v5);
$(SEG 2 7.0 9.9 "hqdn3d=6:4:6:4,$G" v6);
[4:v]trim=0.3:1.6,setpts=PTS-STARTPTS,setsar=1[v7];
[4:v]trim=2.2:3.5,setpts=PTS-STARTPTS,setsar=1[v8];
[4:v]trim=5.05:7.25,setpts=PTS-STARTPTS,setsar=1[v9];
$(SEG 5 1.6 6.4 "eq=contrast=1.05:saturation=1.1,colorbalance=rs=0.04:bs=-0.04:rm=0.03:bm=-0.03,vignette=PI/5" v10);
[6:v]format=yuv420p,setsar=1,drawtext=fontfile=$SERIF:text='PalmCare':fontsize=117:fontcolor=0x8A4B22:x=(w-tw)/2:y=h*0.30,drawtext=fontfile=$SANS:text='THE RITUAL AFTER':fontsize=39:fontcolor=0x3A2A20:x=(w-tw)/2:y=h*0.39,drawtext=fontfile=$SANS:text='Milky Hydro-Glow Body Wash  +  Cacao and Collagen Body Lotion':fontsize=30:fontcolor=0x6B5444:x=(w-tw)/2:y=h*0.445,drawbox=x=iw*0.3:y=ih*0.52:w=iw*0.4:h=3:color=0x8A4B22@0.6:t=fill,drawtext=fontfile=$SANS:text='Shop A67, Kogi Plaza, BBA Market':fontsize=39:fontcolor=0x3A2A20:x=(w-tw)/2:y=h*0.56,drawtext=fontfile=$SANS:text='Trade Fair Complex, Lagos':fontsize=39:fontcolor=0x3A2A20:x=(w-tw)/2:y=h*0.595,drawtext=fontfile=$SANS:text='0809 361 2901   |   0903 055 5424':fontsize=45:fontcolor=0x8A4B22:x=(w-tw)/2:y=h*0.65,fade=in:st=0:d=0.4[v11];
[v0][v1][v2][v3][v4][v5][v6][v7][v8][v9][v10][v11]concat=n=12:v=1:a=0[v];

[0:a]atrim=0.3:7.8,asetpts=PTS-STARTPTS[a0];[1:a]atrim=1.5:5.0,asetpts=PTS-STARTPTS[a1];
[2:a]atrim=2.0:4.55,asetpts=PTS-STARTPTS[a2];[3:a]atrim=0.1:5.9,asetpts=PTS-STARTPTS[a3];
[2:a]atrim=7.0:9.9,asetpts=PTS-STARTPTS[a4];
[a0][a1][a2][a3][a4]concat=n=5:v=0:a=1,aresample=48000,aformat=channel_layouts=stereo,volume=0.3,apad=pad_dur=13[amb];
[5:a]atrim=1.6:6.4,asetpts=PTS-STARTPTS,aresample=48000,aformat=channel_layouts=stereo,adelay=26850|26850[line];

[7:a]aresample=48000,aformat=channel_layouts=stereo,asplit=4[s1][s2][s3][s4];
[s1]atrim=0:3.5,asetpts=PTS-STARTPTS,adelay=600|600[l1];
[s2]atrim=3.6:10.0,asetpts=PTS-STARTPTS,adelay=4300|4300[l2];
[s3]atrim=10.0:16.75,asetpts=PTS-STARTPTS,adelay=11600|11600[l3];
[s4]atrim=17.0:19.6,asetpts=PTS-STARTPTS,adelay=32000|32000[l4];
[9:a]aresample=48000,aformat=channel_layouts=stereo,volume=0.55,asplit=3[x1][x2][x3];
[x1]adelay=21900|21900[f1];[x2]adelay=23250|23250[f2];[x3]adelay=24550|24550[f3];
[amb][line][l1][l2][l3][l4]amix=inputs=6:normalize=0:duration=longest,asplit=2[speech][key];
[8:a]aresample=48000,aformat=channel_layouts=stereo,volume=0.5,afade=t=in:st=0:d=0.8,afade=t=out:st=32.4:d=1.6[mus];
[mus][key]sidechaincompress=threshold=0.03:ratio=6:attack=20:release=350[duck];
[speech][duck][f1][f2][f3]amix=inputs=5:normalize=0:duration=first,atrim=0:35.05,loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[a]
" -map "[v]" -map "[a]" -c:v libx264 -crf 17 -preset slow -pix_fmt yuv420p -c:a aac -b:a 192k -movflags +faststart "$OUT"
ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT"
