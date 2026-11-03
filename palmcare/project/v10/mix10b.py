"""Video 7 v2 soundtrack: the re-scored showcase music (music_v10b.wav) with only two narration lines on the end card —
"Made with healthy ingredients," and the slogan — ducked under the voice, then mastered loud and even."""
import json
import subprocess

import numpy as np
import soundfile as sf
from scipy.signal import resample_poly

from show10 import EC, TOTAL

D = "/tmp/claude-0/-home-user-stockeasy/ae1b3550-c976-5b71-9f6e-2d57965fb3f7/scratchpad/"
SR = 48000
meta = json.load(open(D + "tts/v10_heart/lines.json"))
vo = np.zeros(int(TOTAL * SR), np.float32)
meet = json.load(open(D + "tts/v10b_heart/lines.json"))
for li, at in ((-1, 1.05), (7, EC + 0.55), (8, EC + 2.5)):
    src = D + ("tts/v10b_heart/L1.wav" if li < 0 else "tts/v10_heart/" + meta[li]["file"].split("/")[-1])
    x, sr = sf.read(src, dtype="float32")
    x = resample_poly(x, SR, sr).astype(np.float32)
    _, s, e = (meet[0] if li < 0 else meta[li])["phrases"][0]
    seg = x[int(max(0, s - 0.03) * SR):int((e + 0.12) * SR)]
    seg *= 10 ** ((-19 - 20 * np.log10(np.sqrt(np.mean(seg[np.abs(seg) > 0.01] ** 2)) + 1e-9)) / 20)
    seg[-int(0.05 * SR):] *= np.linspace(1, 0, int(0.05 * SR))
    i0 = int((at - 0.03) * SR)
    vo[i0:i0 + len(seg)] += seg
# the narrator's review as the products change (client round): whole recorded lines, each on its shot
for n, at in ((1, 7.35), (2, 16.55), (3, 25.8), (4, 35.05), (5, 45.25), (6, 48.7)):
    x, sr = sf.read(D + f"tts/v10c_heart/L{n}.wav", dtype="float32")
    x = resample_poly(x, SR, sr).astype(np.float32)
    x *= 10 ** ((-19 - 20 * np.log10(np.sqrt(np.mean(x[np.abs(x) > 0.01] ** 2)) + 1e-9)) / 20)
    x[-int(0.05 * SR):] *= np.linspace(1, 0, int(0.05 * SR))
    i0 = int((at - 0.03) * SR)
    vo[i0:i0 + len(x)] += x[:len(vo) - i0]
sf.write("vo10b.wav", vo, SR, subtype="PCM_24")
af = ("[2:a]volume=0.75,asplit=2[sfa][sfb];[0:a]highpass=f=70,equalizer=f=3500:t=q:w=1.5:g=2.5,acompressor=threshold=-22dB:ratio=2.5:attack=10:release=150:makeup=2dB,"
      "asplit=3[voice][k0][k1];[k0]aformat=channel_layouts=mono[key];[k1]aformat=channel_layouts=mono[key2];"
      f"[1:a]aresample=48000,volume=0.8,aformat=channel_layouts=stereo,atrim=0:{TOTAL}[mus];"
      "[mus][key]sidechaincompress=threshold=0.012:ratio=8:attack=8:release=380[duck];"
      "[sfa]aformat=channel_layouts=mono[sfm];[sfm][key2]sidechaincompress=threshold=0.015:ratio=6:attack=8:release=300[sfd];"
      "[sfd]aformat=channel_layouts=stereo[sfx];[sfb]anullsink;"
      f"[voice]aformat=channel_layouts=stereo[v2];[v2][duck][sfx]amix=inputs=3:normalize=0,atrim=0:{TOTAL}[pre]")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", "vo10b.wav", "-i", D + "music/v10/music_v10b.wav", "-i", "sfx10.wav", "-filter_complex", af,
                "-map", "[pre]", "-c:a", "pcm_s24le", "pre10b.wav"], check=True)
r = subprocess.run(["ffmpeg", "-hide_banner", "-y", "-i", "pre10b.wav", "-af", "acompressor=threshold=-20dB:ratio=2:attack=20:release=250,"
                    "loudnorm=I=-10:TP=-1.5:LRA=9:print_format=json", "-f", "null", "-"], capture_output=True, text=True).stderr
j = json.loads(r[r.rindex("{"):])
af2 = (f"acompressor=threshold=-20dB:ratio=2:attack=20:release=250,loudnorm=I=-10:TP=-1.5:LRA=9:measured_I={j['input_i']}"
       f":measured_TP={j['input_tp']}:measured_LRA={j['input_lra']}:measured_thresh={j['input_thresh']}:offset={j['target_offset']}"
       ":linear=true,aresample=192000,volume=1.18,alimiter=limit=0.79:attack=2:release=60:level=false,aresample=48000")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", "pre10b.wav", "-af", af2, "-c:a", "pcm_s24le", "mix10b.wav"], check=True)
r = subprocess.run(["ffmpeg", "-hide_banner", "-i", "mix10b.wav", "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
print([l.strip() for l in r.splitlines()[-12:] if "I:" in l or "Peak" in l])
