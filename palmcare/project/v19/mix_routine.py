"""Sunlit Routine soundtrack: laid-back Afrobeats (afro_sun.py), a soft set-down 'tock' as each product lands on the
table, a light slide swish as products are swapped, shimmers on the two routine lineups and the end card, and the
narrator's slogan on the end card. Mastered to -12 LUFS. Usage: mix_routine.py OUT.wav"""
import json, subprocess, sys
import numpy as np, soundfile as sf
from scipy.signal import butter, sosfilt
D = "/tmp/claude-0/-home-user-stockeasy/ae1b3550-c976-5b71-9f6e-2d57965fb3f7/scratchpad/"
FPS, B = 24, 60 / 92
bf = lambda b: round(b * B * FPS)
beats = [1] + [3] * 6 + [4] + [3] * 5 + [4, 9]
kinds = ["open"] + ["place"] * 6 + ["lineup"] + ["place"] * 5 + ["lineup", "end"]
cb = np.concatenate([[0], np.cumsum(beats)])
ST = [bf(b) / FPS for b in cb]
TOTAL = ST[-1]
SR = 48000; N = int((TOTAL + 0.5) * SR)
rng = np.random.default_rng(92)
bp = lambda x, lo, hi: sosfilt(butter(2, [lo, hi], "band", fs=SR, output="sos"), x)
def place(buf, x, at, g=1.0):
    i = int(at * SR); n = min(len(x), N - i)
    if n > 0: buf[i:i+n] += x[:n] * g
sfx = np.zeros(N, np.float32)
def tock(g=0.3):
    n = int(0.25*SR); t = np.arange(n)/SR
    x = np.sin(2*np.pi*np.cumsum(140*(1+0.6*np.exp(-t/0.01)))/SR)*np.exp(-t/0.05) + bp(rng.standard_normal(n), 800, 4000)*np.exp(-t/0.008)*0.5
    return (x*g).astype(np.float32)
def swish(g=0.08):
    n = int(0.3*SR); t = np.linspace(0, 1, n)
    return (bp(rng.standard_normal(n), 1200, 6000) * np.sin(np.pi*t)**2 * g).astype(np.float32)
def shimmer(dur=1.4, k=8, g=0.08):
    n = int(dur*SR); x = np.zeros(n)
    for j in range(k):
        s0 = int(rng.uniform(0, dur*0.5)*SR); f = rng.choice([2637, 3136, 3520, 3951, 4699]); tt = np.arange(n-s0)/SR
        x[s0:] += np.sin(2*np.pi*f*tt)*np.exp(-tt/0.25)
    return (x/k*3*g).astype(np.float32)
for k, kd in enumerate(kinds):
    if kd == "place":
        place(sfx, swish(0.06), ST[k] + 7/FPS)                  # lift the old one out
        place(sfx, swish(0.06), ST[k] + 16/FPS)                 # bring the new one in
        place(sfx, tock(), ST[k] + 28/FPS)                      # set down
    if kd == "lineup": place(sfx, shimmer(1.2, 6, 0.07), ST[k] + 0.05)
    if kd == "end": place(sfx, shimmer(1.6, 8, 0.08), ST[k] + 0.1)
EC = ST[kinds.index("end")]
r = subprocess.run(["ffmpeg", "-v", "error", "-ss", "61.38", "-i", D+"v9/edit/vo9.wav", "-t", "2.07", "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True, check=True)
vo = np.frombuffer(r.stdout, np.float32).copy(); vo *= 10**((-17 - 20*np.log10(np.sqrt(np.mean(vo[np.abs(vo) > 0.01]**2))+1e-9))/20)
voice = np.zeros(N, np.float32); place(voice, vo, EC + 0.65)
sf.write("sfx_r.wav", sfx, SR, subtype="PCM_24"); sf.write("voice_r.wav", voice, SR, subtype="PCM_24")
subprocess.run([D+"venv/bin/python", D+"music/v17/lagos_velvet.py", f"{TOTAL+0.05}", "music_r.wav"], check=True)
af = ("[0:a]highpass=f=80,acompressor=threshold=-22dB:ratio=3:attack=6:release=140:makeup=2dB,asplit=2[v][k0];[k0]aformat=channel_layouts=mono[key];"
      f"[1:a]aresample=48000,volume=0.9,atrim=0:{TOTAL}[m];[m][key]sidechaincompress=threshold=0.015:ratio=6:attack=6:release=300[duck];"
      f"[2:a]aformat=channel_layouts=stereo[s];[v]aformat=channel_layouts=stereo[vv];[vv][duck][s]amix=inputs=3:normalize=0,atrim=0:{TOTAL}[pre]")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", "voice_r.wav", "-i", "music_r.wav", "-i", "sfx_r.wav", "-filter_complex", af, "-map", "[pre]", "-c:a", "pcm_s24le", "pre_r.wav"], check=True)
r = subprocess.run(["ffmpeg", "-hide_banner", "-y", "-i", "pre_r.wav", "-af", "loudnorm=I=-12:TP=-1.5:LRA=9:print_format=json", "-f", "null", "-"], capture_output=True, text=True).stderr
j = json.loads(r[r.rindex("{"):])
af2 = (f"loudnorm=I=-12:TP=-1.5:LRA=9:measured_I={j['input_i']}:measured_TP={j['input_tp']}:measured_LRA={j['input_lra']}"
       f":measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true,aresample=192000,alimiter=limit=0.8:attack=2:release=60:level=false,aresample=48000")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", "pre_r.wav", "-af", af2, "-c:a", "pcm_s24le", sys.argv[1]], check=True)
print("total", TOTAL, "EC", EC)
