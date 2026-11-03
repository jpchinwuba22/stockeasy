"""Original energetic, premium Afro-house score for PalmCare Video 3 (120 BPM, G minor, bar = 2 s, 57 s), fully
synthesised (no samples, no copyrighted material). Punchy four-on-floor kick, layered claps, crisp 16th hats and open
hats, tuned congas/bongos and shaker, a syncopated sub + saw bass, wide detuned chord stabs that pump with the kick,
and a bright marimba-pluck hook. Drops land on the edit's impacts (6 / 24 / 45 s) with risers, snare-roll builds and
a deep impact; the end card (45-57 s) keeps the groove and fades. -> music_v4b.wav"""
import numpy as np
import soundfile as sf
from scipy.signal import butter, fftconvolve, sosfilt

SR, T, BPM = 48000, 57.0, 120
BEAT = 60 / BPM
S16 = BEAT / 4
N = int(T * SR)
HITS = [6.0, 24.0, 45.0]
rng = np.random.default_rng(7)
L = np.zeros((N, 2), np.float32)


def filt(x, fc, kind, order=2):
    return sosfilt(butter(order, fc, kind, fs=SR, output="sos"), x, axis=0)


def put(buf, x, t, pan=0.0, g=1.0):
    i = int(round(t * SR))
    if i >= N or i + len(x) <= 0:
        return
    x = x[: N - i]
    lr = np.stack([x * np.sqrt(0.5 * (1 - pan)), x * np.sqrt(0.5 * (1 + pan))], 1) * g * np.sqrt(2)
    buf[i:i + len(x)] += lr.astype(np.float32)


def env_ad(n, a, d):
    t = np.arange(n) / SR
    return np.minimum(1, t / max(a, 1e-4)) * np.exp(-t / d)


def hz(m):
    return 440 * 2 ** ((m - 69) / 12)


# ---------- instruments ----------
def kick():
    n = int(0.42 * SR); t = np.arange(n) / SR
    f = 46 + 120 * np.exp(-t / 0.035)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.20)
    click = filt(rng.standard_normal(n), 3000, "high") * np.exp(-t / 0.004) * 0.35
    return np.tanh(1.6 * (body + click)) * 0.62


def clap():
    n = int(0.35 * SR); t = np.arange(n) / SR
    nz = filt(filt(rng.standard_normal(n), 900, "high"), 7000, "low")
    e = sum(np.exp(-np.clip(t - k * 0.009, 0, None) / 0.006) * (t >= k * 0.009) for k in range(3))
    e = e + np.exp(-t / 0.09) * 0.6
    return nz * e * 0.5


def hat(open_=False):
    n = int((0.22 if open_ else 0.05) * SR); t = np.arange(n) / SR
    nz = filt(rng.standard_normal(n), 7500, "high")
    return nz * np.exp(-t / (0.07 if open_ else 0.012)) * (0.28 if open_ else 0.22)


def shaker():
    n = int(0.07 * SR); t = np.arange(n) / SR
    return filt(rng.standard_normal(n), 5000, "high") * np.minimum(1, t / 0.015) * np.exp(-t / 0.02) * 0.14


def drum(f0, d, g):
    n = int(d * 3 * SR); t = np.arange(n) / SR
    f = f0 * (1 + 0.35 * np.exp(-t / 0.02))
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / d) * g


def snare():
    n = int(0.18 * SR); t = np.arange(n) / SR
    return (filt(rng.standard_normal(n), 1500, "high") * np.exp(-t / 0.05) * 0.4
            + np.sin(2 * np.pi * 190 * t) * np.exp(-t / 0.04) * 0.3)


def saw(f, n, det=0.0):
    t = np.arange(n) / SR
    ph = (f * (1 + det) * t + rng.random()) % 1.0
    return 2 * ph - 1


def stab(notes, dur, bright=2600):
    n = int(dur * SR)
    x = np.zeros(n)
    for m in notes:
        for det in (-0.011, -0.004, 0.0, 0.005, 0.012):
            x += saw(hz(m), n, det)
    x = filt(x / (len(notes) * 5), bright, "low")
    return x * env_ad(n, 0.004, dur * 0.45) * 0.55


def pad(notes, dur):
    n = int(dur * SR)
    x = np.zeros(n)
    for m in notes:
        for det in (-0.006, 0.0, 0.007):
            x += saw(hz(m), n, det)
    x = filt(x / (len(notes) * 3), 1400, "low")
    t = np.arange(n) / SR
    return x * np.minimum(1, t / 0.4) * np.minimum(1, (dur - t) / 0.4) * 0.35


def pluck(m, dur=0.5):
    n = int(dur * SR); t = np.arange(n) / SR
    f = hz(m)
    mod = np.sin(2 * np.pi * f * 3.5 * t) * 2.2 * np.exp(-t / 0.05)       # FM marimba / kalimba bite
    return np.sin(2 * np.pi * f * t + mod) * np.exp(-t / 0.22) * 0.32


def bassnote(m, dur):
    n = int(dur * SR); t = np.arange(n) / SR
    f = hz(m)
    sub = np.sin(2 * np.pi * f * t)
    top = filt(saw(f, n), 700, "low") * 0.4
    e = np.minimum(1, t / 0.005) * np.minimum(1, (dur - t) / 0.02).clip(0, 1)
    return np.tanh(1.3 * (sub * 0.8 + top)) * e * 0.55


# ---------- arrangement ----------
CH = [(55, [67, 70, 74, 77]),   # Gm7   (G Bb D F)
      (51, [67, 70, 74, 75]),   # Ebmaj7 (Eb G Bb D) voiced around the top
      (58, [65, 69, 70, 74]),   # Bbmaj7 (Bb D F A)
      (53, [65, 69, 72, 75])]   # F7    (F A C Eb)
BARS = int(np.ceil(T / (4 * BEAT)))
drums, music, bassb, hook = (np.zeros((N, 2), np.float32) for _ in range(4))
K, C, H, HO, SH, SN = kick(), clap(), hat(), hat(True), shaker(), snare()
CONGA_H, CONGA_L, BONGO = drum(330, 0.09, 0.30), drum(220, 0.12, 0.32), drum(520, 0.06, 0.22)


def sect(t):
    if t < 6: return "intro"
    if t < 24: return "drop1"
    if t < 45: return "drop2"
    return "end"


def build(t0):
    return any(h - 1.5 <= t0 < h for h in HITS)          # last 3 beats before an impact: break + snare roll


for bar in range(BARS):
    t_bar = bar * 4 * BEAT
    root, notes = CH[bar % 4]
    s = sect(t_bar + 0.01)
    for st in range(16):
        t = t_bar + st * S16
        if t >= T:
            break
        sw = 0.012 if st % 2 else 0.0                         # light Afro swing on the off 16ths
        b = build(t)
        if s == "intro":
            if t >= 2.0 and st % 2 == 1:
                put(drums, SH, t + sw, 0.3, 0.6 + 0.4 * t / 6)
            if t >= 4.0 and st in (3, 6, 11, 14):
                put(drums, CONGA_L if st in (6, 14) else CONGA_H, t + sw, -0.35)
            continue
        if s == "end" and t > 55.0:
            continue
        if not b:
            if st % 4 == 0:
                put(drums, K, t, 0, 1.0)
            if st in (4, 12):
                put(drums, C, t, 0, 0.9)
            put(drums, H, t + sw, 0.25, 0.95 if st % 4 == 2 else 0.55)
            if st % 4 == 2:
                put(drums, HO, t, -0.2, 0.8)
            put(drums, SH, t + sw, 0.45, 0.7)
            if st in (3, 6, 10, 11, 14):
                put(drums, {3: CONGA_H, 6: CONGA_L, 10: BONGO, 11: CONGA_H, 14: CONGA_L}[st], t + sw, -0.4)
            if s == "drop2" and st in (7, 15):
                put(drums, BONGO, t + sw, 0.5, 0.8)
    # snare-roll builds (16ths into 32nds, rising), then a one-beat gap before the impact
    for h in HITS:
        if t_bar <= h - 2.0 < t_bar + 4 * BEAT:
            for k, tt in enumerate(np.arange(h - 2.0, h - 0.5, S16 / 2)):
                put(drums, SN, tt, 0.1 * (-1) ** k, 0.25 + 0.75 * (k / 24) ** 1.5)
    # chords: wide stabs that pump; a soft pad in the intro and under the end card
    if s == "intro":
        put(music, pad([n - 12 for n in notes] + notes[:2], 4 * BEAT), t_bar, 0, 0.9)
        if t_bar >= 2.0:
            for st, n in zip((0, 3, 6, 8, 11, 14), (79, 77, 74, 77, 79, 82)):
                put(hook, filt(pluck(n), 1600 + 300 * t_bar, "low"), t_bar + st * S16, 0.2 * (-1) ** st, 0.7)
    else:
        for st, ln in ((2, 0.18), (6, 0.18), (10, 0.18), (13, 0.12), (14, 0.22)):
            t = t_bar + st * S16
            if build(t) or t >= 55.5:
                continue
            put(music, stab(notes, ln * 2.2, 3200 if s == "drop2" else 2400), t, -0.3 if st % 4 else 0.3, 0.85)
        put(music, pad(notes, 4 * BEAT), t_bar, 0, 0.45 if s == "end" else 0.3)
    # bass: syncopated Afro-house line
    if s != "intro" and t_bar < 55.5:
        for st, iv, ln in ((0, 0, 0.30), (3, 0, 0.18), (6, 7, 0.22), (8, 12, 0.18), (10, 0, 0.30), (13, 10, 0.18), (14, 7, 0.22)):
            t = t_bar + st * S16
            if not build(t):
                put(bassb, bassnote(root - 24 + iv, ln), t, 0, 1.0)
    # hook: bright marimba-pluck motif (two-bar call/answer); fuller in drop 2 and the end card
    if s in ("drop1", "drop2", "end") and t_bar < 55.5:
        top = notes[-1] + 12
        motif = [(0, top), (2, top - 3), (3, top - 5), (6, top - 3), (8, top), (11, top + 2), (14, top - 2)] if bar % 2 == 0 \
            else [(0, top - 5), (3, top - 3), (6, top - 7), (10, top - 5), (12, top - 3)]
        for st, n in motif:
            t = t_bar + st * S16
            if build(t):
                continue
            g = 0.55 if s == "drop1" else 0.75
            put(hook, pluck(n), t, 0.25 * (-1) ** st, g)
            if s != "drop1":
                put(hook, pluck(n + 12, 0.3), t + 0.003, -0.25 * (-1) ** st, g * 0.35)

# ---------- sidechain pump (music + bass duck on every kick) ----------
t = np.arange(N) / SR
ph = (t % BEAT) / BEAT
pump = 1 - 0.55 * np.exp(-ph / 0.18)
pump = np.where(t < 6.0, 1.0, pump)
for h in HITS:                                              # no pumping during the break before each impact
    pump = np.where((t >= h - 1.5) & (t < h), 1.0, pump)
music *= pump[:, None]
bassb *= pump[:, None] ** 0.6


# ---------- reverb (send) ----------
def reverb(x, dur=1.6, g=0.25):
    n = int(dur * SR); tt = np.arange(n) / SR
    ir = rng.standard_normal((n, 2)) * np.exp(-tt / (dur / 5))[:, None]
    ir = filt(ir, 6000, "low")
    ir /= np.sqrt((ir ** 2).sum(0))
    return np.stack([fftconvolve(x[:, c], ir[:, c])[:N] for c in range(2)], 1).astype(np.float32) * g


music = music + reverb(music, 1.8, 0.35)
hook = hook + reverb(hook, 1.4, 0.45)
drums = drums + reverb(filt(drums, 400, "high"), 0.9, 0.12)

mix = drums * 1.0 + music * 1.25 + bassb * 0.5 + hook * 1.5
# intro: filtered hush opening into the first drop
ramp = np.clip(t / 6.0, 0, 1)[:, None] ** 2
mix = np.where(t[:, None] < 6.0, filt(mix, 700, "low") * (1 - ramp) + mix * ramp, mix).astype(np.float32)

# risers + impacts
for h in HITS:
    d = 2.0; n = int(d * SR); tt = np.arange(n) / SR
    nz = rng.standard_normal(n)
    out = np.zeros(n)
    for k in range(10):
        seg = slice(k * n // 10, (k + 1) * n // 10)
        out[seg] = filt(nz, 600 + 1200 * k, "high")[seg]
    out *= (tt / d) ** 3 * 0.30
    put(mix, out, h - d, 0, 1.0)
    m = int(2.8 * SR); tt = np.arange(m) / SR
    boom = np.sin(2 * np.pi * (58 * tt - 16 * tt ** 2)) * np.exp(-tt / 0.5) * 0.95
    crack = filt(rng.standard_normal(m), 2500, "high") * np.exp(-tt / 0.05) * 0.5
    tail = filt(rng.standard_normal(m), 3500, "high") * np.exp(-tt / 1.1) * 0.10
    put(mix, np.tanh(boom + crack + tail), h, 0, 1.0)

# master: gentle glue + fade
env = filt(np.abs(mix).mean(1), 8, "low")
g = np.where(env > 0.28, (0.28 / np.maximum(env, 1e-6)) ** 0.45, 1.0)
mix *= g[:, None]
mix[int(54.5 * SR):] *= np.linspace(1, 0, N - int(54.5 * SR))[:, None] ** 1.5
mix *= 0.89 / np.abs(mix).max()
sf.write("music_v4b.wav", mix, SR, subtype="PCM_24")
print("ok", BARS, "bars")
