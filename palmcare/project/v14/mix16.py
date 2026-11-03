"""Soundtrack for edit14: her dialogue + the stranger (from the clips), the narrator's slogan on the end card, the
Amapiano score ducked under every voice, whooshes on the cuts, mastered loud and even -> mix16.wav"""
import json
import subprocess
import sys

import numpy as np
import soundfile as sf
from scipy.signal import butter, sosfilt

sys.argv = [sys.argv[0], "x"]
from edit16 import EC, STARTS, TOTAL, V, D   # noqa: E402

SR = 48000
N = int(TOTAL * SR)


def load(path, a, b):
    r = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{a}", "-i", path, "-t", f"{b - a}", "-vn", "-ac", "1", "-ar", str(SR),
                        "-f", "f32le", "-"], capture_output=True, check=True)
    return np.frombuffer(r.stdout, np.float32).copy()


def lvl(x):
    w = int(0.05 * SR)
    fr = np.array([np.sqrt(np.mean(x[i:i + w] ** 2)) for i in range(0, len(x) - w, w)])
    sel = fr[fr > fr.max() * 0.1]
    return 20 * np.log10(np.sqrt(np.mean(sel ** 2)) + 1e-9)


def place(buf, x, at, fi=0.02, fo=0.06):
    x = x.copy()
    x[:int(fi * SR)] *= np.linspace(0, 1, int(fi * SR))
    x[-int(fo * SR):] *= np.linspace(1, 0, int(fo * SR))
    i = int(at * SR)
    n = min(len(x), N - i)
    buf[i:i + n] += x[:n]


voice = np.zeros(N, np.float32)
for src, a, b, at in ((V + "src/D.mp4", 1.80, 5.62, STARTS[0]), (V + "src/D.mp4", 6.30, 9.40, STARTS[1]),
                      (V + "src/E.mp4", 0.00, 10.0, STARTS[5])):
    x = load(src, a, b)
    x *= 10 ** ((-19 - lvl(x)) / 20)
    place(voice, x, at)
v9 = load(D + "v9/edit/vo9.wav", 61.38, 63.45)
v9 *= 10 ** ((-19 - lvl(v9)) / 20)
place(voice, v9, EC + 1.5 - (61.5 - 61.38))
sf.write("voice16.wav", voice, SR, subtype="PCM_24")

rng = np.random.default_rng(3)
sfx = np.zeros(N, np.float32)
for c in STARTS[1:-1]:                                   # air whoosh through each cut
    n = int(0.36 * SR)
    t = np.linspace(0, 1, n)
    x = rng.standard_normal(n)
    lo = sosfilt(butter(2, [300, 1500], "band", fs=SR, output="sos"), x)
    hi = sosfilt(butter(2, [1500, 6500], "band", fs=SR, output="sos"), x)
    w = (lo * (1 - t) + hi * t) * np.sin(np.pi * t) ** 2 * 0.14
    place(sfx, w.astype(np.float32), c - 0.2, 0.005, 0.01)
sf.write("sfx16.wav", sfx, SR, subtype="PCM_24")

af = ("[0:a]highpass=f=80,afftdn=nf=-30,equalizer=f=300:t=q:w=1:g=-2,equalizer=f=3200:t=q:w=1.4:g=3,"
      "acompressor=threshold=-22dB:ratio=3:attack=6:release=140:makeup=2dB,asplit=2[v][k0];"
      "[k0]aformat=channel_layouts=mono[key];"
      f"[1:a]aresample=48000,volume=0.78,aformat=channel_layouts=mono,atrim=0:{TOTAL}[m];"
      "[m][key]sidechaincompress=threshold=0.012:ratio=9:attack=6:release=350:knee=4[duck];"
      "[2:a]volume=1.0[s];"
      f"[v][duck][s]amix=inputs=3:normalize=0,atrim=0:{TOTAL},aformat=channel_layouts=stereo[pre]")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", "voice16.wav", "-i", "amapiano16.wav", "-i", "sfx16.wav", "-filter_complex", af,
                "-map", "[pre]", "-c:a", "pcm_s24le", "pre16.wav"], check=True)
r = subprocess.run(["ffmpeg", "-hide_banner", "-y", "-i", "pre16.wav", "-af", "acompressor=threshold=-20dB:ratio=2:attack=20:release=250,"
                    "loudnorm=I=-11.5:TP=-1.5:LRA=9:print_format=json", "-f", "null", "-"], capture_output=True, text=True).stderr
j = json.loads(r[r.rindex("{"):])
af2 = (f"acompressor=threshold=-20dB:ratio=2:attack=20:release=250,loudnorm=I=-11.5:TP=-1.5:LRA=9:measured_I={j['input_i']}"
       f":measured_TP={j['input_tp']}:measured_LRA={j['input_lra']}:measured_thresh={j['input_thresh']}:offset={j['target_offset']}"
       ":linear=true,aresample=192000,volume=1.0,alimiter=limit=0.79:attack=2:release=60:level=false,aresample=48000")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", "pre16.wav", "-af", af2, "-c:a", "pcm_s24le", "mix16.wav"], check=True)
r = subprocess.run(["ffmpeg", "-hide_banner", "-i", "mix16.wav", "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
print([l.strip() for l in r.splitlines()[-12:] if "I:" in l or "Peak" in l])
