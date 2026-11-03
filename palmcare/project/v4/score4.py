"""Video 4 score ("Still Water"): an airy luxury Afro-soul bed synthesised to the edit.
Lush pad, FM electric piano, sub bass, soft kick/shaker/log-drum groove entering on the first product
reveal (6.2s), water-like bell shimmer, a lift for the duo shot and a held final chord over the end card.
Usage: score4.py OUT.wav [TOTAL_SECONDS]"""
import sys
import wave

import numpy as np

SR = 48000
TOTAL = float(sys.argv[2]) if len(sys.argv) > 2 else 37.0
GROOVE, CARD = 6.2, 32.4
BAR = (CARD - GROOVE) / 9          # nine bars between the first reveal and the end card
BEAT = BAR / 4
T0 = GROOVE - 2 * BAR              # downbeat grid origin
rng = np.random.default_rng(4)
N = int(TOTAL * SR)
out = np.zeros((N, 2))


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


# D major colour: Dmaj9, Bm11, Gmaj9(#11), A6sus — two bars each, MIDI voicings
CHORDS = [[50, 57, 61, 64, 66, 69], [47, 54, 57, 62, 64, 66], [43, 50, 54, 57, 61, 64], [45, 52, 57, 59, 62, 66]]
ROOTS = [38, 35, 31, 33]


def chord_at(t):
    k = int(max(0.0, t - T0) // (2 * BAR)) % 4
    return CHORDS[k], ROOTS[k]


def env(n, a, r, sus=1.0):
    e = np.ones(n) * sus
    na, nr = int(a * SR), int(r * SR)
    if na:
        e[:na] = np.linspace(0, sus, na)
    if nr:
        e[-nr:] *= np.linspace(1, 0, nr)
    return e


def add(sig, t, pan=0.0, gain=1.0):
    i = int(t * SR)
    if i >= N:
        return
    sig = sig[: N - i] * gain
    out[i:i + len(sig), 0] += sig * (1 - pan) ** 0.5
    out[i:i + len(sig), 1] += sig * (1 + pan) ** 0.5


def lowpass(x, cutoff):
    a = np.exp(-2 * np.pi * cutoff / SR)
    y = np.empty_like(x)
    acc = 0.0
    for i in range(len(x)):  # tiny loops only (short notes)
        acc = (1 - a) * x[i] + a * acc
        y[i] = acc
    return y


def lp_fast(x, cutoff, passes=2):
    """Cheap smoothing low-pass via moving average (vectorised)."""
    w = max(1, int(SR / cutoff / 2))
    k = np.ones(w) / w
    for _ in range(passes):
        x = np.convolve(x, k, mode="same")
    return x


# ---- pad: detuned saw stack, slow swells, per two-bar chord ----
def pad(notes, dur):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    s = np.zeros(n)
    for m in notes:
        for det in (-0.07, 0.0, 0.07):
            f = hz(m + det)
            ph = (tt * f + rng.random()) % 1.0
            s += (2 * ph - 1) * 0.5 + np.sin(2 * np.pi * f * tt) * 0.5
    s = lp_fast(s / (len(notes) * 3), 1400)
    return s * env(n, dur * 0.35, dur * 0.4)


t = T0 - 2 * BAR
while t < TOTAL:
    notes, _ = chord_at(max(t, T0))
    dur = 2 * BAR + 1.2
    g = 0.16 if t < GROOVE else 0.20
    if t >= CARD - 0.5:
        dur = TOTAL - t + 0.1
    add(pad(notes, dur), max(0.0, t), pan=0.0, gain=g)
    t += 2 * BAR


# ---- FM electric piano ----
def rhodes(m, dur, vel=1.0):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    f = hz(m)
    idx = 2.2 * np.exp(-tt * 5.0) + 0.3
    s = np.sin(2 * np.pi * f * tt + idx * np.sin(2 * np.pi * f * tt)) * np.exp(-tt * 1.6)
    s += 0.25 * np.sin(2 * np.pi * 2 * f * tt) * np.exp(-tt * 4)
    return s * env(n, 0.004, 0.3) * vel


def ep_chord(t, notes, vel):
    for k, m in enumerate(notes[1:]):
        add(rhodes(m + 12 if m < 55 else m, 1.6, vel), t + k * 0.012, pan=-0.3 + 0.12 * k, gain=0.12)


bar = 0
t = T0
while t < CARD:
    notes, root = chord_at(t)
    if t >= GROOVE - 0.01:
        ep_chord(t, notes, 1.0)
        ep_chord(t + 2.5 * BEAT, notes, 0.7)
    elif t >= 0:
        ep_chord(t, notes, 0.6)
    t += BAR
# final held chord on the end card
for k, m in enumerate([62, 66, 69, 73, 76]):
    add(rhodes(m, 4.5, 1.0), CARD + 0.05 + k * 0.03, pan=-0.3 + 0.15 * k, gain=0.09)


# ---- sub bass ----
def sub(m, dur):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    return np.sin(2 * np.pi * hz(m) * tt) * env(n, 0.02, 0.25)


t = GROOVE
while t < CARD:
    _, root = chord_at(t)
    add(sub(root, BEAT * 1.6), t, gain=0.17)
    add(sub(root, BEAT * 0.8), t + 2.5 * BEAT, gain=0.12)
    add(sub(root + 7, BEAT * 0.8), t + 3.5 * BEAT, gain=0.09)
    t += BAR
add(sub(38, 4.4), CARD, gain=0.16)


# ---- drums ----
def kick():
    n = int(0.45 * SR)
    tt = np.arange(n) / SR
    f = 48 + 90 * np.exp(-tt * 28)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 7)


def shaker(vel):
    n = int(0.09 * SR)
    s = rng.normal(0, 1, n)
    s = s - lp_fast(s, 5000, 1)
    return s * np.exp(-np.arange(n) / SR * 45) * vel


def log_drum(m):
    n = int(0.6 * SR)
    tt = np.arange(n) / SR
    f = hz(m) * (1 + 0.35 * np.exp(-tt * 30))
    return np.tanh(1.8 * np.sin(2 * np.pi * np.cumsum(f) / SR)) * np.exp(-tt * 6)


def rim():
    n = int(0.05 * SR)
    tt = np.arange(n) / SR
    return (np.sin(2 * np.pi * 1700 * tt) + rng.normal(0, 0.4, n)) * np.exp(-tt * 90)


t = GROOVE
b = 0
while t < CARD - 0.01:
    lift = 1.15 if 22.7 <= t < CARD else 1.0
    add(kick(), t, gain=0.30 * lift)
    add(kick(), t + 2 * BEAT, gain=0.24 * lift)
    for s16 in range(16):
        add(shaker(0.6 if s16 % 2 else 0.35), t + s16 * BEAT / 4, pan=0.35, gain=0.05 * lift)
    add(rim(), t + 1 * BEAT, pan=-0.2, gain=0.10)
    add(rim(), t + 3 * BEAT + BEAT / 2, pan=-0.2, gain=0.07)
    _, root = chord_at(t)
    if b % 2 == 1:
        add(log_drum(root + 12), t + 2.75 * BEAT, gain=0.16)
        add(log_drum(root + 19), t + 3.5 * BEAT, gain=0.12)
    t += BAR
    b += 1


# ---- water shimmer: soft bell arpeggios with echoes ----
def bell(m, dur=1.8):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    f = hz(m)
    return (np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(2 * np.pi * f * 2.76 * tt) * np.exp(-tt * 6)) * np.exp(-tt * 3.2) * env(n, 0.002, 0.2)


t = 0.3
k = 0
while t < TOTAL - 2:
    notes, _ = chord_at(max(t, T0))
    m = notes[(k * 3) % len(notes)] + 24
    for e, g in enumerate((1.0, 0.45, 0.2)):
        add(bell(m), t + e * BEAT * 0.75, pan=(0.6 if k % 2 else -0.6) * (1 if e % 2 == 0 else -1), gain=0.05 * g)
    t += BEAT * (1.5 if t < GROOVE else 1.0)
    k += 1

# ---- reverse swell into the end card ----
n = int(1.6 * SR)
sw = rng.normal(0, 1, n)
sw = lp_fast(sw, 2500) * np.linspace(0, 1, n) ** 3
add(sw, CARD - 1.6, gain=0.5)

# ---- reverb (FFT convolution with a decaying-noise impulse) ----
ir_n = int(2.6 * SR)
tt = np.arange(ir_n) / SR
ir = rng.normal(0, 1, (ir_n, 2)) * np.exp(-tt * 2.4)[:, None]
ir[:, 0] = lp_fast(ir[:, 0], 6000, 1)
ir[:, 1] = lp_fast(ir[:, 1], 6000, 1)
ir /= np.sqrt((ir ** 2).sum(axis=0))
L = 1 << int(np.ceil(np.log2(N + ir_n)))
wet = np.stack([np.fft.irfft(np.fft.rfft(out[:, c], L) * np.fft.rfft(ir[:, c], L), L)[:N] for c in range(2)], axis=1)
mix = out * 0.78 + wet * 0.45
# gentle fade in/out, soft limiting, normalise
mix *= np.clip(np.arange(N) / (0.8 * SR), 0, 1)[:, None]
mix *= np.clip((N - np.arange(N)) / (1.5 * SR), 0, 1)[:, None]
mix = np.tanh(mix / np.max(np.abs(mix)) * 1.4) * 0.89
pcm = (mix * 32767).astype(np.int16)
with wave.open(sys.argv[1], "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())
print("bpm", round(60 / BEAT, 2), "len", TOTAL)
