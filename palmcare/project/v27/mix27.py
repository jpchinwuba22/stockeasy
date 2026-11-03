"""V6 Remotion cut soundtrack: dialogue from the clips, the review voice over the application shot, the narrator's
slogan on the end card, the original Amapiano score re-arranged to the new cut (drop on the jar, lift into the hero,
end card), whooshes on every cut, a juicy burst + shimmer on the end card, loudness -11.5 LUFS.
Usage: mix17.py WITH_APPLY(0|1) OUT.wav"""
import json, subprocess, sys
import numpy as np, soundfile as sf
from scipy.signal import butter, sosfilt
D = "/tmp/claude-0/-home-user-stockeasy/ae1b3550-c976-5b71-9f6e-2d57965fb3f7/scratchpad/"
WITH, OUT = sys.argv[1] == "1", sys.argv[2]
TL = json.load(open(D + "remo/src/timeline.json"))
shots = TL["shots"]
fr = [round(s["dur"] * 24) for s in shots]
st = np.concatenate([[0], np.cumsum(fr)]) / 24
S = {s["id"]: st[k] for k, s in enumerate(shots)}
TOTAL = st[-1]
SR = 48000; N = int(TOTAL * SR) + SR
def load(p, a, b):
    r = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{a}", "-i", p, "-t", f"{b-a}", "-vn", "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True, check=True)
    return np.frombuffer(r.stdout, np.float32).copy()
def lvl(x):
    w = int(0.05 * SR); f = np.array([np.sqrt(np.mean(x[i:i+w]**2)) for i in range(0, len(x)-w, w)]); s = f[f > f.max()*0.1]
    return 20*np.log10(np.sqrt(np.mean(s**2)) + 1e-9)
def place(buf, x, at, fi=0.02, fo=0.08, g=1.0):
    x = x.copy() * g; x[:int(fi*SR)] *= np.linspace(0, 1, int(fi*SR)); x[-int(fo*SR):] *= np.linspace(1, 0, int(fo*SR))
    i = int(at*SR); n = min(len(x), N-i); buf[i:i+n] += x[:n]
voice = np.zeros(N, np.float32)
for p, a, b, at in ((D+"remo/public/hook1.mp4", 0.55, 7.09, S["hook"]), (D+"remo/public/present1.mp4", 0.35, 10.0, S["present"]),
                    (D+"remo/public/apply1.mp4", 1.25, 9.5, S["applyA"])):
    x = load(p, a, b); x *= 10**((-19 - lvl(x))/20); place(voice, x, at)
if False:
    x, sr = sf.read(D + "tts/v17_heart/L1.wav"); x = x.astype(np.float32)
    if sr != SR:
        x = load(D + "tts/v17_heart/L1.wav", 0, len(x)/sr)
    x *= 10**((-20 - lvl(x))/20); place(voice, x, S["hero"] + 2.6)
v9 = load(D + "v9/edit/vo9.wav", 61.38, 63.45); v9 *= 10**((-19 - lvl(v9))/20); place(voice, v9, S["heroend"] + 3.0 + 0.5)
sf.write(D + "v27/mix/voice.wav", voice, SR, subtype="PCM_24")
rng = np.random.default_rng(17); sfx = np.zeros(N, np.float32)
bp = lambda x, lo, hi: sosfilt(butter(2, [lo, hi], "band", fs=SR, output="sos"), x)
for c in [S[k] for k in ("jar", "present", "scoop", "heroend")]:
    n = int(0.4*SR); t = np.linspace(0, 1, n); x = rng.standard_normal(n)
    w = (bp(x, 300, 1500)*(1-t) + bp(x, 1500, 6500)*t) * np.sin(np.pi*t)**2 * 0.15
    place(sfx, w.astype(np.float32), c - 0.22, 0.005, 0.01)
def shimmer(at, dur=1.4, k=8, g=0.10):
    n = int(dur*SR); x = np.zeros(n)
    for j in range(k):
        s0 = int(rng.uniform(0, dur*0.5)*SR); f = rng.choice([2637, 3136, 3520, 3951, 4699, 5274]); tt = np.arange(n-s0)/SR
        x[s0:] += np.sin(2*np.pi*f*tt)*np.exp(-tt/0.25)
    place(sfx, (x/k*3*g).astype(np.float32), at, 0.005, 0.2)
def splash(at, g=0.55):
    n = int(1.0*SR); t = np.arange(n)/SR; x = bp(rng.standard_normal(n), 400, 5000)*np.exp(-t/0.14)*0.6
    for _ in range(14):
        s0 = int(rng.uniform(0.02, 0.8)*SR); bl = int(0.05*SR); tb = np.arange(bl)/SR
        f = rng.uniform(500, 1300)*(1+3*tb/0.05); b = np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-tb/0.015)*rng.uniform(0.1, 0.2)
        x[s0:s0+bl] += b[:max(0, min(bl, n-s0))]
    place(sfx, (x*g).astype(np.float32), at, 0.002, 0.2)
def sub(at, g=0.6):
    n = int(1.4*SR); t = np.arange(n)/SR; f = 46*(1+1.5*np.exp(-t/0.04))
    place(sfx, (np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-t/0.4)*g).astype(np.float32), at, 0.002, 0.3)
EC = S["heroend"] + 3.0
def pop(at, f0=900, g=0.22):
    n = int(0.14 * SR); t = np.arange(n) / SR
    f = f0 * (1 + 0.8 * np.exp(-t / 0.012))
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.035) + bp(rng.standard_normal(n), 2000, 7000) * np.exp(-t / 0.004) * 0.4
    place(sfx, (x * g).astype(np.float32), at, 0.001, 0.02)
for k, d in enumerate((1.15, 1.75, 2.35)):
    pop(S["jar"] + d, 820 + 120 * k)
pop(S["scoop"] + 0.3, 1100); shimmer(S["present"] + 0.3, 1.2, 6, 0.07); shimmer(S["prodB"], 1.0, 6, 0.08)
for k, at in enumerate((S["present"] + 2.55, S["present"] + 5.71, S["present"] + 6.77, S["applyA"] + 0.57, S["applyA"] + 1.41, S["prodB"] + 0.1)):
    pop(at, 760 + 70 * k, 0.17)
splash(S["jar"] + 0.05, 0.45); shimmer(S["jar"] + 0.3)
shimmer(S["heroend"] + 0.2, g=0.09); shimmer(S["heroend"] + 1.25, 0.9, 4, 0.08)
sub(EC - 0.1, 0.45); splash(EC - 0.05, 0.7); shimmer(EC + 0.1, 2.0, 12, 0.11); shimmer(EC + 3.0, 1.0, 5, 0.08)
sf.write(D + "v27/mix/sfx.wav", sfx, SR, subtype="PCM_24")
subprocess.run([D + "venv/bin/python", D + "music/v17/amapiano_luxe.py", f"{TOTAL + 0.05}", f"{S['jar']}", f"{S['heroend']}", f"{EC}", D + "v27/mix/music.wav"], check=True)
af = ("[0:a]highpass=f=80,afftdn=nf=-30,equalizer=f=300:t=q:w=1:g=-2,equalizer=f=3200:t=q:w=1.4:g=3,"
      "acompressor=threshold=-22dB:ratio=3:attack=6:release=140:makeup=2dB,asplit=2[v][k0];[k0]aformat=channel_layouts=mono[key];"
      f"[1:a]aresample=48000,volume=0.85,aformat=channel_layouts=mono,atrim=0:{TOTAL}[m];"
      "[m][key]sidechaincompress=threshold=0.012:ratio=9:attack=6:release=350:knee=4[duck];[2:a]volume=1.0[s];"
      f"[v][duck][s]amix=inputs=3:normalize=0,atrim=0:{TOTAL},aformat=channel_layouts=stereo[pre]")
P = D + "v27/mix/pre.wav"
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", D+"v27/mix/voice.wav", "-i", D+"v27/mix/music.wav", "-i", D+"v27/mix/sfx.wav", "-filter_complex", af, "-map", "[pre]", "-c:a", "pcm_s24le", P], check=True)
r = subprocess.run(["ffmpeg", "-hide_banner", "-y", "-i", P, "-af", "acompressor=threshold=-20dB:ratio=2:attack=20:release=250,loudnorm=I=-11.5:TP=-1.5:LRA=9:print_format=json", "-f", "null", "-"], capture_output=True, text=True).stderr
j = json.loads(r[r.rindex("{"):])
af2 = (f"acompressor=threshold=-20dB:ratio=2:attack=20:release=250,loudnorm=I=-11.5:TP=-1.5:LRA=9:measured_I={j['input_i']}:measured_TP={j['input_tp']}"
       f":measured_LRA={j['input_lra']}:measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true,aresample=192000,alimiter=limit=0.79:attack=2:release=60:level=false,aresample=48000")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", P, "-af", af2, "-c:a", "pcm_s24le", OUT], check=True)
print("total", TOTAL, {k: round(v, 3) for k, v in S.items()})
