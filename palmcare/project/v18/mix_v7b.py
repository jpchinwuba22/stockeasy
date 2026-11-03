"""Video 7 soundtrack: the Naija Glow beat, a whoosh / whip on every cut, splashes on the milk and citrus sets, a
shimmer on the title and finale, sparkles on the hero glints, and the narrator's slogan on the end card only.
Mastered to -11.5 LUFS. Usage: mix_v7.py OUT.wav"""
import json, subprocess, sys
import numpy as np, soundfile as sf
from scipy.signal import butter, sosfilt
D = "/tmp/claude-0/-home-user-stockeasy/ae1b3550-c976-5b71-9f6e-2d57965fb3f7/scratchpad/"
FPS, BPM = 24, 112
B = 60 / BPM
bf = lambda b: round(b * B * FPS)
beats = [1, 3, 4] + [4] * 6 + [2] + [3] * 4 + [4, 4, 12]
kinds = ["drop", "pops", "title"] + ["prod"] * 6 + ["card"] + ["serum"] * 5 + ["finale", "end"]
cb = np.concatenate([[0], np.cumsum(beats)])
ST = [bf(b) / FPS for b in cb]
TOTAL = ST[-1]
SR = 48000; N = int((TOTAL + 0.5) * SR)
rng = np.random.default_rng(70)
bp = lambda x, lo, hi: sosfilt(butter(2, [lo, hi], "band", fs=SR, output="sos"), x)
def place(buf, x, at, g=1.0):
    i = int(at * SR); n = min(len(x), N - i)
    if n > 0: buf[i:i+n] += x[:n] * g
sfx = np.zeros(N, np.float32)
def whoosh(d=0.36, g=0.16):
    n = int(d*SR); t = np.linspace(0, 1, n); x = rng.standard_normal(n)
    return ((bp(x, 300, 1500)*(1-t) + bp(x, 1500, 7000)*t) * np.sin(np.pi*t)**2 * g).astype(np.float32)
def tick(g=0.12):
    n = int(0.08*SR); t = np.arange(n)/SR
    return (bp(rng.standard_normal(n), 2500, 9000) * np.exp(-t/0.012) * g).astype(np.float32)
def shimmer(dur=1.4, k=8, g=0.1):
    n = int(dur*SR); x = np.zeros(n)
    for j in range(k):
        s0 = int(rng.uniform(0, dur*0.5)*SR); f = rng.choice([2637, 3136, 3520, 3951, 4699, 5274]); tt = np.arange(n-s0)/SR
        x[s0:] += np.sin(2*np.pi*f*tt)*np.exp(-tt/0.25)
    return (x/k*3*g).astype(np.float32)
def splash(g=0.5):
    n = int(1.0*SR); t = np.arange(n)/SR; x = bp(rng.standard_normal(n), 400, 5000)*np.exp(-t/0.14)*0.6
    for _ in range(12):
        s0 = int(rng.uniform(0.02, 0.8)*SR); bl = int(0.05*SR); tb = np.arange(bl)/SR
        f = rng.uniform(500, 1300)*(1+3*tb/0.05); b = np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-tb/0.015)*rng.uniform(0.1, 0.2)
        x[s0:s0+bl] += b[:max(0, min(bl, n-s0))]
    return (x*g).astype(np.float32)
def drip(g=0.3):                                               # liquid plink as the serum droplet hits
    n = int(0.35*SR); t = np.arange(n)/SR
    f = 700 * (1 + 2.5 * t / 0.35)
    return (np.sin(2*np.pi*np.cumsum(f)/SR) * np.exp(-t/0.06) * g).astype(np.float32)
def swoosh(g=0.2):                                             # liquid wave wipe
    n = int(0.5*SR); t = np.linspace(0, 1, n); x = rng.standard_normal(n)
    w = bp(x, 200, 900)*(1-t) + bp(x, 900, 5000)*t
    return (w * np.sin(np.pi*t)**1.5 * g).astype(np.float32)
for k in range(1, 7):                                          # colour pops
    place(sfx, tick(0.16), ST[1] + (k - 1) * round(0.5 * B * FPS) / FPS)
place(sfx, splash(0.35), ST[1])                                 # the gold drop lands
place(sfx, shimmer(1.6, 10, 0.11), ST[2] + 0.05)
for k, kd in enumerate(kinds):
    if kd == "card": place(sfx, shimmer(1.2, 6, 0.09), ST[k] + 0.05); place(sfx, whoosh(0.5, 0.12), ST[k] - 0.2)
    if kd == "serum":
        place(sfx, whoosh(0.4, 0.13), ST[k] - 0.18)
        place(sfx, drip(), ST[k] + 6 / FPS)
        place(sfx, shimmer(0.9, 5, 0.08), ST[k] + 0.7)
    if kd in ("prod", "finale"):
        place(sfx, swoosh(), ST[k] - 0.25)
    if kd == "prod":
        place(sfx, splash(0.4), ST[k] + 7 / FPS)              # product lands on the podium
        place(sfx, shimmer(0.6, 4, 0.07), ST[k] + 0.6)
    if kd == "finale": place(sfx, shimmer(2.2, 14, 0.12), ST[k] + 0.05)
    if kd == "end": place(sfx, splash(0.6), ST[k] + 0.1); place(sfx, shimmer(1.6, 8, 0.1), ST[k] + 0.15)
EC = ST[kinds.index("end")]
r = subprocess.run(["ffmpeg", "-v", "error", "-ss", "61.38", "-i", D+"v9/edit/vo9.wav", "-t", "2.07", "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True, check=True)
vo = np.frombuffer(r.stdout, np.float32).copy(); vo *= 10**((-17 - 20*np.log10(np.sqrt(np.mean(vo[np.abs(vo) > 0.01]**2))+1e-9))/20)
voice = np.zeros(N, np.float32); place(voice, vo, EC + 0.7)
sf.write("sfx_v7.wav", sfx, SR, subtype="PCM_24"); sf.write("voice_v7.wav", voice, SR, subtype="PCM_24")
subprocess.run([D+"venv/bin/python", D+"music/v17/afro_bounce.py", f"{TOTAL+0.05}", "naija_v7.wav"], check=True)
af = ("[0:a]highpass=f=80,acompressor=threshold=-22dB:ratio=3:attack=6:release=140:makeup=2dB,asplit=2[v][k0];[k0]aformat=channel_layouts=mono[key];"
      f"[1:a]aresample=48000,volume=0.9,atrim=0:{TOTAL}[m];[m][key]sidechaincompress=threshold=0.015:ratio=6:attack=6:release=300[duck];"
      f"[2:a]aformat=channel_layouts=stereo[s];[v]aformat=channel_layouts=stereo[vv];[vv][duck][s]amix=inputs=3:normalize=0,atrim=0:{TOTAL}[pre]")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", "voice_v7.wav", "-i", "naija_v7.wav", "-i", "sfx_v7.wav", "-filter_complex", af, "-map", "[pre]", "-c:a", "pcm_s24le", "pre_v7.wav"], check=True)
r = subprocess.run(["ffmpeg", "-hide_banner", "-y", "-i", "pre_v7.wav", "-af", "loudnorm=I=-11.5:TP=-1.5:LRA=9:print_format=json", "-f", "null", "-"], capture_output=True, text=True).stderr
j = json.loads(r[r.rindex("{"):])
af2 = (f"loudnorm=I=-11.5:TP=-1.5:LRA=9:measured_I={j['input_i']}:measured_TP={j['input_tp']}:measured_LRA={j['input_lra']}"
       f":measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true,aresample=192000,alimiter=limit=0.79:attack=2:release=60:level=false,aresample=48000")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", "pre_v7.wav", "-af", af2, "-c:a", "pcm_s24le", sys.argv[1]], check=True)
print("total", TOTAL, "EC", EC)
