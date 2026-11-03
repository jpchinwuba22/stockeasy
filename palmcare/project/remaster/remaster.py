"""Louder series master (-11.5 LUFS target): gentle compression, two-pass linear loudnorm, oversampled true-peak limiter.
Re-muxes the new audio under the untouched picture of the full and mobile files. Usage: remaster.py NAME"""
import json
import os
import shutil
import subprocess
import sys

FIN = "/tmp/claude-0/-home-user-stockeasy/ae1b3550-c976-5b71-9f6e-2d57965fb3f7/scratchpad/PalmCare_Final/"
TMP = "/tmp/claude-0/-home-user-stockeasy/ae1b3550-c976-5b71-9f6e-2d57965fb3f7/scratchpad/remaster/"
name = sys.argv[1]
full, mob = FIN + name + ".mp4", FIN + name + "_mobile.mp4"
src = TMP + name + "_src.wav"
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", full, "-vn", "-c:a", "pcm_s24le", "-ar", "48000", src], check=True)
PRE = "acompressor=threshold=-20dB:ratio=2.5:attack=8:release=120:makeup=3dB"
r = subprocess.run(["ffmpeg", "-hide_banner", "-i", src, "-af", PRE + ",loudnorm=I=-11:TP=-1.5:LRA=7:print_format=json", "-f", "null", "-"],
                   capture_output=True, text=True).stderr
j = json.loads(r[r.rindex("{"):r.rindex("}") + 1])
af = (PRE + f",loudnorm=I=-11:TP=-1.5:LRA=7:measured_I={j['input_i']}:measured_TP={j['input_tp']}:measured_LRA={j['input_lra']}"
      f":measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true,"
      "aresample=192000,alimiter=limit=0.79:attack=2:release=60:level=false,aresample=48000")
loud = TMP + name + "_loud.wav"
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-af", af, "-c:a", "pcm_s16le", loud], check=True)
for f, br in ((full, "256k"), (mob, "192k")):
    bak = FIN + "previous_versions/std_minus14/" + os.path.basename(f)
    if not os.path.exists(bak):
        shutil.copy2(f, bak)
    out = TMP + os.path.basename(f)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", bak, "-i", loud, "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", br,
                    "-movflags", "+faststart", "-shortest", out], check=True)
    shutil.move(out, f)
    m = subprocess.run(["ffmpeg", "-hide_banner", "-i", f, "-af", "loudnorm=print_format=summary", "-f", "null", "-"], capture_output=True, text=True).stderr
    li = [l.strip() for l in m.splitlines() if "Input Integrated" in l or "Input True Peak" in l]
    d = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f], capture_output=True, text=True).stdout.strip()
    print(os.path.basename(f), d, *li)
