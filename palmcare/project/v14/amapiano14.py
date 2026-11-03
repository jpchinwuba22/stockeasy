"""Original Amapiano score for the Vitamin C ad (synthesised from scratch, no samples, no copyrighted material):
112 BPM, A minor. Log drum (pitch-gliding sine bass, saturated), soft four-on-the-floor kick, rimshot/clap on 2 & 4,
16th shaker, jazzy Rhodes-style chord stabs (Am9 - Fmaj7 - Dm9 - E7sus), airy pad and a whistle hook.
Arrangement follows the edit: filtered intro under the street dialogue -> DROP on the first product cut -> groove under
the review -> lift into the hero -> end-card outro. Usage: amapiano14.py TOTAL DROP HERO END -> amapiano14.wav"""
import sys

import numpy as np
import soundfile as sf
from scipy.signal import butter, fftconvolve, sosfilt

SR = 48000
TOTAL, DROP, HERO, END = map(float, sys.argv[1:5])
BPM = 112
B = 60 / BPM
S16 = B / 4
N = int(TOTAL * SR)
rng = np.random.default_rng(14)
out = {k: np.zeros((N, 2), np.float32) for k in ("drums", "log", "keys", "pad", "lead", "fx")}


def lp(x, fc, o=2):
    return sosfilt(butter(o, fc, "low", fs=SR, output="sos"), x, axis=0)


def hp(x, fc, o=2):
    return sosfilt(butter(o, fc, "high", fs=SR, output="sos"), x, axis=0)


def put(bus, x, t, pan=0.0, g=1.0):
    i = int(round(t * SR))
    if i >= N or i + len(x) <= 0:
        return
    if i < 0:
        x, i = x[-i:], 0
    n = min(len(x), N - i)
    l, r = np.cos((pan + 1) * np.pi / 4) * 1.414, np.sin((pan + 1) * np.pi / 4) * 1.414
    x = x[:n] * g
    if x.ndim == 1:
        out[bus][i:i + n, 0] += x * l
        out[bus][i:i + n, 1] += x * r
    else:
        out[bus][i:i + n] += x


def mtof(m):
    return 440 * 2 ** ((m - 69) / 12)


def tt(d):
    return np.arange(int(d * SR)) / SR


def kick(v=1.0):
    t = tt(0.45)
    f = 48 + 110 * np.exp(-t / 0.03)
    return np.tanh(2.2 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.16)) * v * 0.8


def logdrum(m, d=0.42, v=1.0):
    t = tt(d)
    f0 = mtof(m)
    f = f0 * (1 + 1.6 * np.exp(-t / 0.035))
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / (d * 0.55))
    x += 0.35 * np.sin(2 * np.pi * np.cumsum(f * 2.01) / SR) * np.exp(-t / 0.07)      # the woody "knock"
    return np.tanh(2.6 * x) * 0.55 * v


def rim(v=1.0):
    t = tt(0.18)
    x = hp(rng.standard_normal(len(t)), 1800) * np.exp(-t / 0.025) * 0.6
    x += np.sin(2 * np.pi * 1750 * t) * np.exp(-t / 0.02) * 0.4
    return x * v


def clap(v=1.0):
    t = tt(0.35)
    env = np.zeros(len(t))
    for d in (0, 0.011, 0.022):
        env += np.exp(-np.clip(t - d, 0, None) / 0.012) * (t >= d)
    env += 0.5 * np.exp(-t / 0.12)
    return lp(hp(rng.standard_normal(len(t)), 900), 7000) * env * 0.35 * v


def shaker(v=1.0):
    t = tt(0.07)
    return hp(rng.standard_normal(len(t)), 6000) * np.exp(-t / 0.018) * 0.22 * v


def rhodes(m, d, v=1.0):
    t = tt(d)
    f = mtof(m)
    mod = np.sin(2 * np.pi * f * t) * 1.4 * np.exp(-t / 0.4)
    x = np.sin(2 * np.pi * f * t + mod) * np.exp(-t / 1.1) * (1 - np.exp(-t / 0.004))
    x += 0.15 * np.sin(2 * np.pi * 2 * f * t) * np.exp(-t / 0.3)
    rel = int(0.08 * SR)
    x[-rel:] *= np.linspace(1, 0, rel)
    return x * 0.16 * v


def pad(ms, d, v=1.0):
    t = tt(d)
    x = np.zeros(len(t))
    for m in ms:
        for det in (-0.08, 0.0, 0.08):
            ph = 2 * np.pi * mtof(m + det) * t
            x += 2 * (ph / (2 * np.pi) % 1) - 1
    x = lp(x, 1400) / (3 * len(ms))
    a = int(0.6 * SR)
    env = np.ones(len(t)); env[:a] = np.linspace(0, 1, a); env[-a:] *= np.linspace(1, 0, a)
    return x * env * 0.22 * v


def whistle(m, d, v=1.0):
    t = tt(d)
    vib = 1 + 0.006 * np.sin(2 * np.pi * 5.5 * t) * np.clip(t / 0.25, 0, 1)
    x = np.sin(2 * np.pi * np.cumsum(mtof(m) * vib) / SR)
    env = np.clip(t / 0.04, 0, 1) * np.exp(-t / (d * 0.8))
    return x * env * 0.12 * v


CH = [([57, 60, 64, 67, 71], 45), ([53, 57, 60, 64], 41), ([50, 53, 57, 60, 64], 38), ([52, 57, 59, 62], 40)]   # Am9 Fmaj7 Dm9 E7sus
LOG = [(0, 0), (0.75, 0), (1.5, 7), (2.5, 3), (3.25, 5)]          # beat offsets in the bar, semitone offsets from root
bar = 4 * B
nbar = int(np.ceil(TOTAL / bar))
for b in range(nbar):
    t0 = b * bar
    chord, root = CH[b % 4]
    intro = t0 < DROP - 1e-6
    outro = t0 >= END
    for k in range(4):                                             # kick: soft four-on-the-floor (half-time in the intro)
        if not intro or k % 2 == 0:
            put("drums", kick(0.7 if intro else 1.0), t0 + k * B)
    for k in (1, 3):
        put("drums", rim(0.8), t0 + k * B, 0.15)
        if not intro:
            put("drums", clap(0.9), t0 + k * B, -0.1)
    for s in range(16):
        put("drums", shaker(1.0 if s % 2 else 0.55), t0 + s * S16 + (0.012 if s % 2 else 0), 0.35 if s % 4 else -0.25)
    if not intro:                                                  # the log drum: the Amapiano signature
        for off, semi in LOG:
            put("log", logdrum(root + semi - 12, 0.38 + 0.1 * (semi == 0), 1.0 if not outro else 0.7), t0 + off * B)
    for k, off in enumerate((0.5, 1.75, 2.5, 3.5)):                # Rhodes stabs on the off-beats
        for j, m in enumerate(chord):
            put("keys", rhodes(m, B * (0.9 if k < 3 else 1.6), 0.8 if intro else 1.0), t0 + off * B + j * 0.006, -0.3 + 0.15 * j)
    put("pad", pad(chord[:3], bar + 0.3, 0.8 if intro else 1.0), t0)
    if not intro and (b % 2 == 1):                                 # whistle hook every second bar
        for off, m, d in ((0, 76, 0.4), (0.5, 79, 0.4), (1.0, 76, 0.3), (1.5, 74, 0.9)):
            put("lead", whistle(m, d), t0 + off * B, 0.2)

# FX: riser into the drop and the hero, impacts on drop / hero / end card
def riser(d):
    t = tt(d)
    x = hp(rng.standard_normal(len(t)), 1200) * (t / d) ** 3 * 0.25
    return x + np.sin(2 * np.pi * np.cumsum(300 + 900 * (t / d) ** 2) / SR) * (t / d) ** 2 * 0.05


def impact():
    t = tt(1.6)
    f = 40 * (1 + 1.4 * np.exp(-t / 0.05))
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.45) * 0.9


for h in (DROP, HERO, END):
    put("fx", riser(1.6), h - 1.6)
    put("fx", impact(), h)

# mix: the intro (under the street dialogue) is filtered, everything opens up on the drop
def verb(x, d=1.6):
    n = int(d * SR)
    t = np.arange(n) / SR
    ir = rng.standard_normal((n, 2)) * np.exp(-t / (d / 6))[:, None]
    ir = lp(ir, 6000); ir /= np.sqrt((ir ** 2).sum(0))
    return np.stack([fftconvolve(x[:, c], ir[:, c])[:N] for c in range(2)], 1)


g = {"drums": 0.9, "log": 1.0, "keys": 0.85, "pad": 0.7, "lead": 0.7, "fx": 0.8}
mix = sum(out[k] * g[k] for k in out)
mix += verb(out["keys"] + out["lead"] + out["drums"] * 0.3) * 0.25
i_drop = int(DROP * SR)
intro = lp(mix[:i_drop], 900)
fade = np.linspace(0, 1, min(int(0.25 * SR), i_drop))[:, None]
mix[:i_drop] = intro
mix[i_drop - len(fade):i_drop] = intro[-len(fade):] * (1 - fade) + mix[i_drop - len(fade):i_drop] * fade
fo = int(1.5 * SR)
mix[-fo:] *= np.linspace(1, 0, fo)[:, None]
mix = np.tanh(mix * 1.2) / np.tanh(1.2)
mix /= np.abs(mix).max() + 1e-9
sf.write(sys.argv[0].replace("amapiano14.py", "amapiano14.wav"), (mix * 0.89).astype(np.float32), SR, subtype="PCM_24")
print("ok", TOTAL)
