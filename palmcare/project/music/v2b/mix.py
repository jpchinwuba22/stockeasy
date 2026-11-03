"""Mix the Afro-soul stems -> music.wav (48 kHz, 60 s). Warm and calm: intro opens from a soft low-pass, gentle
glue compression, airy shimmer swells (no hits) into the two product reveals and the end card, long fade out."""
import numpy as np
import soundfile as sf
from scipy.signal import butter, sosfilt

SR, T = 48000, 57.0
N = int(T * SR)
REVEALS = [6.0, 24.0, 45.0]
rng = np.random.default_rng(5)


def load(n):
    x, sr = sf.read(f"{n}.wav", dtype="float32")
    out = np.zeros((N, 2), np.float32)
    out[:min(N, len(x))] = x[:N]
    return out


def lp(x, fc):
    return sosfilt(butter(2, fc, "low", fs=SR, output="sos"), x, axis=0)


def hp(x, fc):
    return sosfilt(butter(2, fc, "high", fs=SR, output="sos"), x, axis=0)


gain = {"drums": 0.75, "perc": 0.6, "rhodes": 0.8, "bass": 0.85, "guitar": 0.5, "kalimba": 0.65, "pad": 0.55}
mix = sum(load(k) * g for k, g in gain.items())
t = np.arange(N) / SR
# intro: muffled -> open over the cold open (0-6 s)
ramp = np.clip(t / 6.0, 0, 1)[:, None] ** 1.5
mix = np.where(t[:, None] < 6.0, lp(mix, 1200) * (1 - ramp) + mix * ramp, mix).astype(np.float32)
# gentle glue: soft-knee compression by envelope
env = lp(np.abs(mix).mean(1), 8)
g = np.where(env > 0.25, (0.25 / np.maximum(env, 1e-6)) ** 0.35, 1.0)
mix *= g[:, None]


def swell(t_end, dur=1.6):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    air = hp(rng.standard_normal(n), 5000) * 0.25
    shimmer = sum(np.sin(2 * np.pi * f * tt + rng.uniform(0, 6)) for f in (1396.9, 2093.0, 2793.8)) / 3 * 0.35
    y = (air + shimmer) * (tt / dur) ** 2.5
    y[-int(0.08 * SR):] *= np.linspace(1, 0, int(0.08 * SR))
    tail = int(1.2 * SR)                                         # soft bloom after the reveal
    tt2 = np.arange(tail) / SR
    bloom = sum(np.sin(2 * np.pi * f * tt2) for f in (698.5, 1046.5, 1396.9)) / 3 * np.exp(-tt2 / 0.5) * 0.25
    out = np.concatenate([y, bloom])
    return np.stack([out, out], 1).astype(np.float32), int((t_end - dur) * SR)


for r in REVEALS:
    s, i0 = swell(r)
    seg = s[: N - i0]
    mix[i0:i0 + len(seg)] += seg * 0.55
mix[int(54.0 * SR):] *= np.linspace(1, 0, N - int(54.0 * SR))[:, None] ** 1.5
mix *= 0.89 / np.abs(mix).max()
sf.write("music.wav", mix, SR, subtype="PCM_24")
print("ok")
