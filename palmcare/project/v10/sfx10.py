"""Video 7 sound design, synthesised (no third-party samples): air whooshes through every cut, liquid splashes and
bubbles on the milk / citrus / gel sets, sparkles on the hero glints, a deep sub hit on each pack reveal, a riser into
the collection finale with an impact and shimmer, a soft shimmer under the opening title. -> sfx10.wav"""
import numpy as np
import soundfile as sf
from scipy.signal import butter, sosfilt

from show10 import FINALE, SHOTS, STARTS, TOTAL

SR = 48000
N = int(TOTAL * SR)
rng = np.random.default_rng(21)
out = np.zeros((N, 2), np.float32)


def bp(x, lo, hi, order=2):
    return sosfilt(butter(order, [lo, hi], "band", fs=SR, output="sos"), x)


def put(x, at, pan=0.0, g=1.0):
    i = int(at * SR)
    if i < 0:
        x, i = x[-i:], 0
    n = min(len(x), N - i)
    if n <= 0:
        return
    l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
    out[i:i + n, 0] += x[:n] * l * g
    out[i:i + n, 1] += x[:n] * r * g


def whoosh(dur=0.42):
    n = int(dur * SR)
    t = np.linspace(0, 1, n)
    x = rng.standard_normal(n)
    env = np.sin(np.pi * t) ** 2.2
    lo = bp(x, 300, 1400) * (1 - t) + bp(x, 1400, 6000) * t          # sweep low -> high through the cut
    return (lo * env * 0.5).astype(np.float32)


def splash(dur=0.9):
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = bp(rng.standard_normal(n), 400, 5000) * np.exp(-t / 0.12) * 0.55
    for _ in range(9):                                                  # bubbles: tiny rising blips
        s = rng.uniform(0.05, dur - 0.15)
        bl = int(0.05 * SR)
        tb = np.arange(bl) / SR
        f = rng.uniform(500, 1300) * (1 + 3 * tb / 0.05)
        b = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tb / 0.015) * rng.uniform(0.08, 0.18)
        i = int(s * SR)
        x[i:i + bl] += b[:max(0, min(bl, n - i))]
    return x.astype(np.float32)


def sparkle(dur=0.8, notes=6):
    n = int(dur * SR)
    x = np.zeros(n)
    for k in range(notes):
        s = int(rng.uniform(0, dur * 0.6) * SR)
        f = rng.choice([2637, 3136, 3520, 3951, 4699, 5274])
        ln = n - s
        tt = np.arange(ln) / SR
        x[s:] += np.sin(2 * np.pi * f * tt) * np.exp(-tt / 0.18) * 0.09
    return x.astype(np.float32)


def sub_hit(dur=1.4):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = 48 * (1 + 1.5 * np.exp(-t / 0.04))
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.35) * 0.8
    x += bp(rng.standard_normal(n), 1500, 7000) * np.exp(-t / 0.02) * 0.25
    return x.astype(np.float32)


def riser(dur=2.0):
    n = int(dur * SR)
    t = np.linspace(0, 1, n)
    x = bp(rng.standard_normal(n), 800, 7000) * t ** 3 * 0.35
    f = 220 + 660 * t ** 2
    x += np.sin(2 * np.pi * np.cumsum(f) / SR) * t ** 2 * 0.06
    return x.astype(np.float32)


put(sparkle(1.6, 10), 0.25, 0.0, 0.8)                                  # opening title shimmer
for k in range(1, len(STARTS) - 1):
    c = STARTS[k]
    kind = SHOTS[k][0]
    put(whoosh(), c - 0.21, rng.uniform(-0.5, 0.5), 0.55)
    if kind in ("wide", "hero"):
        put(splash(), c + 0.02, rng.uniform(-0.3, 0.3), 0.45 if kind == "hero" else 0.6)
    if kind in ("hero", "pack"):
        put(sparkle(), c + 0.12, rng.uniform(-0.4, 0.4), 0.7)
    if kind == "pack":
        put(sub_hit(), c, 0.0, 0.6)
put(riser(2.0), FINALE - 2.0, 0.0, 0.7)
put(sub_hit(2.0), FINALE, 0.0, 0.9)
put(sparkle(2.4, 16), FINALE + 0.05, 0.0, 0.9)
sf.write("sfx10.wav", np.clip(out, -1, 1), SR, subtype="PCM_24")
print("sfx", round(TOTAL, 3))
