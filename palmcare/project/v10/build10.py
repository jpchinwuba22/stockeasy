"""Video 7 — "The PalmCare Collection". Beat-locked (104 BPM) assembly: lineup hook -> three body-care sets (real
bottles composited on the cleaned Flow plates) -> the serum packs -> GlowShield -> Vitamin C box + jar -> lineup end
card. Narration (af_heart) placed phrase by phrase; the Afrobeats score ducks under the voice; mastered loud and even.
Usage: build10.py -> base10.mov + vo10_words.json (then overlay10.py)"""
import json
import os
import re
import subprocess

import numpy as np
import soundfile as sf
from scipy.signal import resample_poly

D = "/tmp/claude-0/-home-user-stockeasy/ae1b3550-c976-5b71-9f6e-2d57965fb3f7/scratchpad/"
SR, FPS = 48000, 24
BEAT = 60 / 104


def T(b):
    return round(b * BEAT * FPS) / FPS


# (file, src_in, start_beat, flags)
SHOTS_B = [("L_hook.mp4", 0.0, 0, ""),
           ("C_P1.mp4", 0.40, 12, ""),
           ("C_P2.mp4", 0.40, 28, ""),
           ("C_P3.mp4", 0.40, 44, ""),
           (D + "v6/PS_vitac.mp4", 0.6, 60, ""),
           (D + "v6/PS_n10.mp4", 0.6, 66, ""),
           (D + "v6/PS_derma.mp4", 0.6, 72, ""),
           (D + "v8/PS_glow.mp4", 0.4, 78, ""),
           (D + "v9/PR.mp4", 0.6, 90, ""),
           ("L_end.mp4", 0.0, 100, "")]
END_B = 118
STARTS = [T(b) for _, _, b, _ in SHOTS_B] + [T(END_B)]
TOTAL = STARTS[-1]
VO_PLACE = [(0, 0, 3.75), (0, 1, 4.85),
            (1, 0, 7.3), (1, 1, 10.9), (1, 2, 14.1),
            (2, 0, 16.5), (2, 1, 19.8), (2, 2, 22.6),
            (3, 0, 25.7), (3, 1, 30.05), (3, 2, 32.5),
            (4, 0, 34.85), (4, 1, 36.05), (4, 2, 38.4), (4, 3, 41.6),
            (5, 0, 45.4), (5, 1, 49.15),
            (6, 0, 52.4),
            (7, 0, 58.0), (7, 1, 59.8),
            (8, 0, 61.9)]
LINES = D + "tts/v10_heart"
MUSIC = D + "music/v10/music_v10.wav"


def speech_rms(x):
    win = int(0.05 * SR)
    fr = np.array([np.sqrt(np.mean(x[i:i + win] ** 2)) for i in range(0, len(x) - win, win)])
    sel = fr[fr > fr.max() * 0.1]
    return 20 * np.log10(np.sqrt(np.mean(sel ** 2)) + 1e-9)


def make_vo():
    meta = json.load(open(f"{LINES}/lines.json"))
    lines = []
    for m in meta:
        x, sr = sf.read(f"{LINES}/" + m["file"].split("/")[-1], dtype="float32")
        x = resample_poly(x, SR, sr).astype(np.float32)
        x *= 10 ** ((-19 - speech_rms(x)) / 20)
        lines.append((x, m["phrases"]))
    mix = np.zeros(int(TOTAL * SR), np.float32)
    words = []
    for li, pi, at in VO_PLACE:
        x, phr = lines[li]
        text, s, e = phr[pi]
        a, b = max(0, int((s - 0.03) * SR)), min(len(x), int((e + 0.12) * SR))
        seg = x[a:b].copy()
        f = int(0.012 * SR)
        seg[:f] *= np.linspace(0, 1, f)
        seg[-int(0.05 * SR):] *= np.linspace(1, 0, int(0.05 * SR))
        i0 = int((at - (s - a / SR)) * SR)
        mix[i0:i0 + len(seg)] += seg[:len(mix) - i0]
        ws = text.split()
        wts = np.array([len(re.sub(r"[^A-Za-z0-9]", "", w)) + 2 for w in ws], float)
        edges = at + (e - s) * np.concatenate([[0], np.cumsum(wts) / wts.sum()])
        for w, p, q in zip(ws, edges[:-1], edges[1:]):
            words.append({"text": w, "start": round(p, 3), "end": round(q, 3)})
    sf.write("vo10.wav", np.clip(mix, -1, 1), SR, subtype="PCM_24")
    json.dump({"words": words}, open("vo10_words.json", "w"), indent=1)


def seg(k, src, st, dur):
    out = f"seg10/{k:02d}.mp4"
    if os.path.exists(out) and not os.environ.get("FORCE"):
        return out
    vf = f"trim={st}:{st + dur + 0.05:.4f},setpts=PTS-STARTPTS,fps=24,scale=1080:1920:flags=lanczos,setsar=1,trim=0:{dur:.4f},setpts=PTS-STARTPTS,format=yuv420p"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-filter_complex", f"[0:v]{vf}[v]", "-map", "[v]", "-an",
                    "-c:v", "libx264", "-crf", "10", "-preset", "medium", out], check=True)
    return out


def main():
    os.makedirs("seg10", exist_ok=True)
    files = [seg(k, src, st, STARTS[k + 1] - STARTS[k]) for k, (src, st, _, _) in enumerate(SHOTS_B)]
    make_vo()
    n = len(files)
    vf = "".join(f"[{k}:v]settb=1/24,setpts=PTS-STARTPTS,fps=24,setsar=1[q{k}];" for k in range(n)) + \
        "".join(f"[q{k}]" for k in range(n)) + f"concat=n={n}:v=1:a=0,trim=0:{TOTAL},format=yuv420p[v]"
    af = [f"[{n}:a]highpass=f=70,equalizer=f=250:t=q:w=1.2:g=-1.5,equalizer=f=3500:t=q:w=1.5:g=2.5,"
          f"acompressor=threshold=-22dB:ratio=2.5:attack=10:release=150:makeup=2dB,asplit=2[voice][key0]",
          "[key0]aformat=channel_layouts=mono[key]",
          f"[{n + 1}:a]aresample=48000,volume=0.62,aformat=channel_layouts=mono,atrim=0:{TOTAL}[mus]",
          "[mus][key]sidechaincompress=threshold=0.012:ratio=9:attack=8:release=380:knee=4[duck]",
          f"[voice][duck]amix=inputs=2:normalize=0,atrim=0:{TOTAL},aformat=channel_layouts=stereo,"
          "acompressor=threshold=-18dB:ratio=2:attack=15:release=200,aresample=48000[aout]"]
    cmd = ["ffmpeg", "-v", "error", "-y"]
    for f in files:
        cmd += ["-i", f]
    cmd += ["-i", "vo10.wav", "-i", MUSIC, "-filter_complex", vf + ";" + ";".join(af), "-map", "[v]", "-map", "[aout]",
            "-c:v", "libx264", "-crf", "12", "-preset", "medium", "-pix_fmt", "yuv420p", "-c:a", "pcm_s24le", "base10.mov"]
    subprocess.run(cmd, check=True)
    print("TOTAL", TOTAL, [round(s, 3) for s in STARTS])


if __name__ == "__main__":
    main()
