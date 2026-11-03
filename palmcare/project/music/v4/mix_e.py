"""Energised mix: the Afro-soul stems + the drive layer and log drum, white-noise risers into each reveal, a deep
impact (sub boom + bright crack + reverb tail) on each reveal, glue compression -> music_e.wav."""
import numpy as np
import soundfile as sf
from scipy.signal import butter, sosfilt
SR, T = 48000, 57.0
N = int(T * SR)
HITS = [6.0, 24.0, 45.0]
rng = np.random.default_rng(3)


def load(n):
    x, _ = sf.read(f"{n}.wav", dtype="float32")
    o = np.zeros((N, 2), np.float32); o[:min(N, len(x))] = x[:N]; return o


def filt(x, fc, kind):
    return sosfilt(butter(2, fc, kind, fs=SR, output="sos"), x, axis=0)


gain = {"drums": 0.6, "perc": 0.6, "rhodes": 0.7, "bass": 0.75, "guitar": 0.5, "kalimba": 0.75, "pad": 0.55, "drive": 1.0, "logdrum": 0.95}
mix = sum(load(k) * g for k, g in gain.items())
t = np.arange(N) / SR
ramp = np.clip(t / 6.0, 0, 1)[:, None] ** 2                     # intro opens from a filtered hush into the first hit
mix = np.where(t[:, None] < 6.0, filt(mix, 900, "low") * (1 - ramp) + mix * ramp, mix).astype(np.float32)
for h in HITS:                                                   # risers
    d = 2.6; n = int(d * SR); tt = np.arange(n) / SR
    noise = rng.standard_normal(n)
    out = np.zeros(n)
    for k in range(8):                                           # sweep the band upward
        seg = slice(k * n // 8, (k + 1) * n // 8)
        out[seg] = filt(noise, 800 + 1100 * k, "high")[seg]
    out *= (tt / d) ** 3 * 0.35
    i0 = int((h - d) * SR)
    mix[i0:i0 + n] += np.stack([out, out], 1).astype(np.float32)
    # impact
    m = int(2.5 * SR); tt = np.arange(m) / SR
    boom = np.sin(2 * np.pi * (55 * tt - 18 * tt ** 2)) * np.exp(-tt / 0.45) * 0.9
    crack = filt(rng.standard_normal(m), 2500, "high") * np.exp(-tt / 0.06) * 0.5
    tail = filt(rng.standard_normal(m), 3000, "high") * np.exp(-tt / 0.9) * 0.08
    imp = boom + crack + tail
    j0 = int(h * SR)
    seg = imp[: N - j0]
    mix[j0:j0 + len(seg)] += np.stack([seg, seg * 0.96], 1).astype(np.float32)
env = filt(np.abs(mix).mean(1), 10, "low")                       # glue
g = np.where(env > 0.3, (0.3 / np.maximum(env, 1e-6)) ** 0.4, 1.0)
mix *= g[:, None]
mix[int(54.5 * SR):] *= np.linspace(1, 0, N - int(54.5 * SR))[:, None] ** 1.5
mix *= 0.89 / np.abs(mix).max()
sf.write("music_v4.wav", mix, SR, subtype="PCM_24")
print("ok")
