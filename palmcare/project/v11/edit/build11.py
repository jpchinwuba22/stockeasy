"""Video 6 v2 — "Honestly?": PalmCare Vitamin C Face Moisturiser, re-cut for the client round.
Cold open on her review (clip 6) -> the approved story body of video9h (orange burst hook .. hydration) -> her review
payoff with the glow cutaway -> the friends rooftop scene (clip 8, "secret" slip removed with a punch-in jump cut) ->
real box + jar on the marble pedestals (clip 9 composite) with "Made with healthy ingredients." -> end card + slogan.
The "face and neck" instruction is gone. Audio: her voice and the narrator lead, the score sits under them (sidechain
ducking keyed on every voice), mastered loud and even. Usage: build11.py -> base11.mov, then overlay11.py."""
import json
import os
import subprocess

import numpy as np
import soundfile as sf
from scipy.signal import resample_poly

D = "/tmp/claude-0/-home-user-stockeasy/ae1b3550-c976-5b71-9f6e-2d57965fb3f7/scratchpad/"
SR = 48000
UP = "scale=1080:1920:flags=lanczos,cas=0.5,setsar=1"
GRADE = ("eq=contrast=1.06:saturation=1.06,"
         "colorbalance=rs=0.025:gs=0.005:bs=-0.03:rm=0.03:gm=0.008:bm=-0.03:rh=0.015:bh=-0.015,"
         "curves=all='0/0.01 0.22/0.205 0.5/0.5 0.8/0.815 1/0.985',"
         "split[a][b];[b]gblur=sigma=28[g];[a][g]blend=all_mode=screen:all_opacity=0.06")   # same look as video9h
C6F = D + "v11/C6_realjar.mp4"            # clip 6 with the REAL jar in her hand (render6c.py), starts at src 0.0833
C6, C8, C9 = D + "v11/src/C6.mp4", D + "v11/src/C8.mp4", D + "v11/qa/C_P9.mp4"
GLOW = D + "v9/edit/C8.mp4"          # window close-up from the original shoot (glow cutaway)
BODY = D + "v9/edit/video9h.mp4"     # approved video 6 body, graphics included
EC = D + "v9/EC9b.mp4"
OFF = 0.0                            # client round 3: the jar-in-hand shots are out, the body opens the film again

# (source, src_in, src_out, flags)  — consecutive on the timeline
SHOTS = [(BODY, 0.0, 44.0, ""),                         # approved story body (orange burst hook .. hydration)
         (C8, 2.2, 5.0, "grade"),                       # friends: "My friends keep asking for my…"
         (C8, 5.26, 9.70, "grade,punch"),               #   jump cut + punch-in: "PalmCare Vitamin C Face Moisturiser. Trust me, get yours today!"
         (C9, 1.0, 9.75, ""),                           # real box + jar hero (long enough to land the end card on the score's ending)
         (EC, 0.0, 10.375, "")]                         # end card
STARTS = list(np.cumsum([0] + [round((b - a) * 24) / 24 for _, a, b, _ in SHOTS]))
TOTAL = STARTS[-1]
# dialogue pieces (source, src_in, src_out, timeline_at) and narration pieces
DLG = [(C8, 2.2, 5.0, STARTS[1]), (C8, 5.26, 9.62, STARTS[2])]
HEALTHY_AT = STARTS[3] + 0.9
SLOGAN_SRC, SLOGAN_AT = (61.38, 63.45), STARTS[4] + 1.5


def seg(k, src, a, b, fl):
    out = f"seg/{k:02d}.mp4"
    if os.path.exists(out) and not os.environ.get("FORCE"):
        return out
    dur = STARTS[k + 1] - STARTS[k]
    vf = [f"trim={a}:{a + dur + 0.05:.4f}", "setpts=PTS-STARTPTS", "fps=24", UP]
    if "punch" in fl:   # jump-cut punch-in, centred a little above her face line
        vf.append("crop=iw/1.12:ih/1.12:(iw-iw/1.12)/2:(ih-ih/1.12)*0.32,scale=1080:1920:flags=lanczos")
    if "grade" in fl:
        vf.append(GRADE)
    vf += [f"trim=0:{dur:.4f}", "setpts=PTS-STARTPTS", "format=yuv420p"]
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-filter_complex", "[0:v]" + ",".join(vf) + "[v]", "-map", "[v]",
                    "-an", "-c:v", "libx264", "-crf", "10", "-preset", "medium", out], check=True)
    return out


def load(path, a=None, b=None):
    if path.endswith(".wav"):
        x, sr = sf.read(path, dtype="float32", always_2d=True)
    else:
        r = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-vn", "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                           capture_output=True, check=True)
        x, sr = np.frombuffer(r.stdout, np.float32)[:, None], SR
    x = x.mean(1)
    if sr != SR:
        x = resample_poly(x, SR, sr).astype(np.float32)
    if a is not None:
        x = x[int(a * SR):int(b * SR)]
    return x.astype(np.float32)


def speech_rms(x):
    win = int(0.05 * SR)
    fr = np.array([np.sqrt(np.mean(x[i:i + win] ** 2)) for i in range(0, len(x) - win, win)])
    sel = fr[fr > fr.max() * 0.1]
    return 20 * np.log10(np.sqrt(np.mean(sel ** 2)) + 1e-9)


def edge(x, fi=0.015, fo=0.06):
    x = x.copy()
    x[:int(fi * SR)] *= np.linspace(0, 1, int(fi * SR))
    x[-int(fo * SR):] *= np.linspace(1, 0, int(fo * SR))
    return x


def place(buf, x, at):
    i = int(round(at * SR))
    n = min(len(x), len(buf) - i)
    buf[i:i + n] += x[:n]


def audio():
    N = int(TOTAL * SR)
    vo, dlg, mus = np.zeros(N, np.float32), np.zeros(N, np.float32), np.zeros(N, np.float32)
    # narration: approved body narration (shifted), "Made with healthy ingredients," and the slogan, all af_heart
    v9 = load(D + "v9/edit/vo9.wav")
    place(vo, edge(v9[:int(44.0 * SR)]), OFF)
    meta = json.load(open(D + "tts/v10_heart/lines.json"))
    l8 = load(D + "tts/v10_heart/L8.wav")
    _, s, e = meta[7]["phrases"][0]
    hx = l8[int(max(0, s - 0.03) * SR):int((e + 0.12) * SR)]
    hx *= 10 ** ((-19 - speech_rms(hx)) / 20)
    place(vo, edge(hx), HEALTHY_AT - 0.03)
    place(vo, edge(v9[int(SLOGAN_SRC[0] * SR):int(SLOGAN_SRC[1] * SR)]), SLOGAN_AT - (61.5 - SLOGAN_SRC[0]))
    # her voice: each piece levelled to the narration's speech level, then cleaned in the mix chain
    for src, a, b, at in DLG:
        x = load(src, a, b)
        x *= 10 ** ((-19 - speech_rms(x)) / 20)
        place(dlg, edge(x, 0.02, 0.08), at)
    # score: the approved video 6 score under the body/end (shifted), a soft low-passed bed under the cold open
    m = load(D + "music/v9/music_v9.wav")
    place(mus, m, OFF)
    bed = m[int(48.0 * SR):int((48.0 + OFF + 0.4) * SR)].copy()
    bed[:int(0.4 * SR)] *= np.linspace(0, 1, int(0.4 * SR))
    bed[-int(0.4 * SR):] *= np.linspace(1, 0, int(0.4 * SR))
    if OFF > 0:
        place(mus, bed * 0.55, 0.0)
    sf.write("vo11.wav", vo, SR, subtype="PCM_24")
    sf.write("dlg11.wav", dlg, SR, subtype="PCM_24")
    sf.write("mus11.wav", mus, SR, subtype="PCM_24")


def main():
    os.makedirs("seg", exist_ok=True)
    files = [seg(k, *s) for k, s in enumerate(SHOTS)]
    audio()
    n = len(files)
    vf = "".join(f"[{k}:v]settb=1/24,setpts=PTS-STARTPTS,fps=24,setsar=1[q{k}];" for k in range(n)) + \
        "".join(f"[q{k}]" for k in range(n)) + f"concat=n={n}:v=1:a=0,trim=0:{TOTAL},format=yuv420p[v]"
    T = TOTAL
    af = [f"[{n}:a]highpass=f=70,equalizer=f=250:t=q:w=1.2:g=-1.5,equalizer=f=3500:t=q:w=1.5:g=2.5,"
          f"acompressor=threshold=-22dB:ratio=2.5:attack=10:release=150:makeup=2dB[vo0]",
          f"[{n + 1}:a]highpass=f=85,afftdn=nf=-30,equalizer=f=300:t=q:w=1.0:g=-2,equalizer=f=3200:t=q:w=1.4:g=2.5,"
          f"deesser=i=0.3,acompressor=threshold=-22dB:ratio=3:attack=8:release=140:makeup=2dB[dl0]",
          "[vo0][dl0]amix=inputs=2:normalize=0,asplit=2[voice][key0]",
          "[key0]aformat=channel_layouts=mono[key]",
          f"[{n + 2}:a]volume=0.62,aformat=channel_layouts=mono[mus]",
          "[mus][key]sidechaincompress=threshold=0.012:ratio=9:attack=8:release=380:knee=4[duck]",
          f"[voice][duck]amix=inputs=2:normalize=0,atrim=0:{T},aformat=channel_layouts=stereo,"
          f"acompressor=threshold=-18dB:ratio=2:attack=15:release=200,aresample=48000[aout]"]
    cmd = ["ffmpeg", "-v", "error", "-y"]
    for f in files:
        cmd += ["-i", f]
    cmd += ["-i", "vo11.wav", "-i", "dlg11.wav", "-i", "mus11.wav", "-filter_complex", vf + ";" + ";".join(af),
            "-map", "[v]", "-map", "[aout]", "-c:v", "libx264", "-crf", "12", "-preset", "medium", "-pix_fmt", "yuv420p",
            "-c:a", "pcm_s24le", "base11.mov"]
    subprocess.run(cmd, check=True)
    print("TOTAL", TOTAL, "STARTS", [round(s, 3) for s in STARTS])


if __name__ == "__main__":
    main()
