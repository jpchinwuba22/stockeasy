"""Mix the Afrobeats stems + sound design for Video 2 -> music_v2.wav (48 kHz stereo, 62 s).
Sub layer under kick and bass for a modern low end, intro low-pass opening, risers into each unveil, and a
lightning strike (crackle + thunder + sub boom) on each unveil downbeat. SFX are also written separately."""
import numpy as np
import soundfile as sf
from scipy.signal import butter, sosfilt

SR = 48000
BPM = 104
BEAT = 60 / BPM
DROPS = [16 * BEAT, 48 * BEAT, 88 * BEAT]           # unveils: Citrus, Molecular, end card
T = 62.0
N = int(T * SR)
rng = np.random.default_rng(3)


def load(name):
    x, sr = sf.read(f"{name}.wav", dtype="float32")
    assert sr == SR
    out = np.zeros((N, 2), np.float32)
    out[:min(N, len(x))] = x[:N]
    return out


def lp(x, fc, order=2):
    return sosfilt(butter(order, fc, "low", fs=SR, output="sos"), x, axis=0)


def hp(x, fc, order=2):
    return sosfilt(butter(order, fc, "high", fs=SR, output="sos"), x, axis=0)


def env(n, a, d):
    t = np.arange(n) / SR
    return np.minimum(1, t / max(a, 1e-4)) * np.exp(-t / d)


stems = {k: load(k) for k in ("drums", "perc", "bass", "keys", "guitar", "marimba", "pad")}
gain = {"drums": 1.0, "perc": 0.75, "bass": 0.95, "keys": 0.55, "guitar": 0.42, "marimba": 0.5, "pad": 0.32}
mix = np.zeros((N, 2), np.float32)
for k, x in stems.items():
    mix += x * gain[k]

# intro: keys + pad open from a muffled low-pass to full over bars 1-4 (blend dry/filtered)
t = np.arange(N) / SR
ramp = np.clip(t / DROPS[0], 0, 1)[:, None] ** 2
muff = lp(mix, 900)
mix = np.where(t[:, None] < DROPS[0], muff * (1 - ramp) + mix * ramp, mix).astype(np.float32)

# sub kick layer (sine 95 -> 42 Hz) on every kick of the full grooves
kick_steps = []
for bar in range(4, 26):
    ks = [0, 6, 12] if bar % 2 == 0 else [0, 6, 10, 14]
    if bar >= 24:
        ks = [0, 6, 12] if bar == 24 else [0]
    if bar in (11, 21):
        ks = [s for s in ks if s < 12]
    kick_steps += [(bar * 16 + s) * BEAT / 4 for s in ks]
L = int(0.32 * SR)
tt = np.arange(L) / SR
f = 42 + 53 * np.exp(-tt * 28)
sub = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 9)
for k in kick_steps:
    i = int(k * SR)
    seg = sub[: max(0, min(L, N - i))]
    mix[i:i + len(seg)] += (seg * 0.42)[:, None]


def riser(t_end, dur):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    noise = rng.standard_normal(n)
    # sweep a band-pass by mixing progressively brighter high-passed noise
    out = np.zeros(n)
    for k, fc in enumerate(np.geomspace(300, 9000, 12)):
        w = np.clip((tt / dur) * 12 - k, 0, 1) * np.clip(k + 2 - (tt / dur) * 12, 0, 1)
        out += hp(noise, fc, 2) * w
    tone = np.sin(2 * np.pi * np.cumsum(np.geomspace(180, 1400, n)) / SR) * 0.25
    y = (out * 0.5 + tone) * (tt / dur) ** 2.2
    y[-int(0.06 * SR):] *= np.linspace(1, 0, int(0.06 * SR))
    return np.stack([y, y], 1).astype(np.float32), int((t_end - dur) * SR)


def lightning(t0):
    n = int(3.2 * SR)
    tt = np.arange(n) / SR
    crack = np.zeros(n)
    for _ in range(26):                                       # crackle: dense bright clicks in the first 0.3 s
        c = int(abs(rng.normal(0, 0.09)) * SR)
        if c < n - 400:
            crack[c:c + 400] += rng.standard_normal(400) * np.exp(-np.arange(400) / 60) * rng.uniform(0.4, 1)
    crack = hp(crack, 2500, 2) * 0.9
    snap = hp(rng.standard_normal(n), 1200, 2) * env(n, 0.001, 0.05) * 0.8
    thunder = lp(rng.standard_normal(n), 220, 4) * env(n, 0.04, 1.1) * 3.2
    boom = np.sin(2 * np.pi * np.cumsum(30 + 40 * np.exp(-tt * 6)) / SR) * env(n, 0.003, 0.7) * 0.9
    y = crack + snap + thunder + boom
    left = y + np.concatenate([np.zeros(90), crack[:-90]]) * 0.3       # a touch of width on the crackle
    return np.stack([left, y], 1).astype(np.float32)


sfx = np.zeros((N, 2), np.float32)
for d in DROPS:
    r, i0 = riser(d - 0.08, 2.2)
    sfx[i0:i0 + len(r)] += r * 0.5
    lz = lightning(d)
    i = int(d * SR)
    sfx[i:i + len(lz)] += lz[: N - i] * 0.9
    # the beat drops out for the breath before the strike
    j0, j1 = int((d - 0.29) * SR), int(d * SR)
    fade = np.ones(N, np.float32)
    fade[j0:j1] = np.linspace(1, 0.15, j1 - j0)
    mix *= fade[:, None]

out = mix + sfx
out = np.tanh(out * 0.9) / 0.9                                  # soft clip the peaks
out[int(60.0 * SR):] *= np.linspace(1, 0, N - int(60.0 * SR))[:, None] ** 2
out *= 0.89 / np.abs(out).max()
sf.write("music_v2.wav", out, SR, subtype="PCM_24")
sf.write("sfx_v2.wav", (sfx * 0.89 / max(1e-6, np.abs(sfx).max())), SR, subtype="PCM_24")
print("drops at", [round(d, 3) for d in DROPS])
