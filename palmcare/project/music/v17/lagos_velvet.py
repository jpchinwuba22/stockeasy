"""Video 7 (Glow Routine) score, take 2: "Lagos Velvet", a mellow Afro-R&B / alte groove, deliberately unlike the
Afrobeats bounce of the other product video: no shekere, no talking drum, no flute. Finger snaps, a soft rim click and
a sparse deep kick, a sliding sub bass, tremolo electric-piano chords (real piano, filtered), cello swells and a sparse
harp motif, moody D minor (Dm9 - Bbmaj7 - Gm9 - A7sus). 92 BPM to keep the edit grid: product placements every three
beats, routine lineups, end card. Real recorded instruments (tonejs-instruments + Tone.js drum samples, CC-BY 3.0).
Usage: lagos_velvet.py TOTAL OUT.wav"""
import glob
import os
import re
import sys

import numpy as np
import soundfile as sf
from scipy.signal import butter, fftconvolve, resample_poly, sosfilt

SR = 48000
TOTAL = float(sys.argv[1])
BEAT = 60 / 92
BAR = 4 * BEAT
S16 = BEAT / 4
N = int(TOTAL * SR)
SMP = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "samples")
rng = np.random.default_rng(77)
PC = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


def filt(x, fc, kind, order=2):
    return sosfilt(butter(order, fc, kind, fs=SR, output="sos"), x, axis=0)


def load(path):
    x, sr = sf.read(path, dtype="float32", always_2d=True)
    x = x.mean(1)
    if sr != SR:
        x = resample_poly(x, SR, sr).astype(np.float32)
    nz = np.nonzero(np.abs(x) > 0.003)[0]
    return x[nz[0]:] if len(nz) else x


def instrument(name):
    bank = {}
    for f in glob.glob(f"{SMP}/ti/samples/{name}/*.wav"):
        m = re.fullmatch(r"([A-G])(s?)(\d)\.wav", os.path.basename(f))
        if m:
            bank[12 * (int(m.group(3)) + 1) + PC[m.group(1)] + (1 if m.group(2) else 0)] = load(f)
    return bank


BANKS = {k: instrument(k) for k in ("piano", "cello", "violin", "contrabass", "harp", "guitar-nylon", "bass-electric", "flute")}


def note(inst, midi, dur, vel=1.0, rel=0.25):
    """A pitched note from the nearest recorded sample (resampled, so at most a few semitones away); held notes
    are looped over their steady middle with crossfades; release fade at the end."""
    bank = BANKS[inst]
    k = min(bank, key=lambda m: abs(m - midi))
    x = bank[k]
    ratio = 2 ** ((midi - k) / 12)
    if abs(ratio - 1) > 1e-4:
        up, dn = int(round(1000 / ratio)), 1000
        x = resample_poly(x, up, dn).astype(np.float32)
    need = int((dur + rel) * SR)
    if len(x) < need and inst in ("cello", "violin", "contrabass"):
        a, b = int(len(x) * 0.35), int(len(x) * 0.8)
        loop = x[a:b]
        cf = min(int(0.08 * SR), len(loop) // 3)
        cur = x[:b].copy()
        while len(cur) < need:
            tail = cur[-cf:] * np.linspace(1, 0, cf) + loop[:cf] * np.linspace(0, 1, cf)
            cur = np.concatenate([cur[:-cf], tail, loop[cf:]])
        x = cur
    x = x[:need].copy()
    r = int(rel * SR)
    if len(x) > r:
        x[-r:] *= np.linspace(1, 0, r) ** 1.5
    return x * vel


def drum(path):
    return load(f"{SMP}/ta/drum-samples/{path}")


KICK, SNARE, HAT = drum("acoustic-kit/kick.mp3"), drum("acoustic-kit/snare.mp3"), drum("acoustic-kit/hihat.mp3")
TOM = drum("acoustic-kit/tom3.mp3")
BONGO_H, BONGO_L = drum("Bongos/tom1.mp3"), drum("Bongos/tom2.mp3")
SHAKE = filt(HAT, 6000, "high") * 0.6

buses = {k: np.zeros((N, 2), np.float32) for k in ("piano", "strings", "gtr", "bass", "harp", "drums", "perc", "fx", "lead", "keys")}


def put(bus, x, t, pan=0.0, g=1.0):
    i = int(round(t * SR))
    if i >= N or i < -len(x):
        return
    if i < 0:
        x, i = x[-i:], 0
    x = x[: N - i]
    l, r = np.sqrt(0.5 * (1 - pan)), np.sqrt(0.5 * (1 + pan))
    buses[bus][i:i + len(x), 0] += x * l * g
    buses[bus][i:i + len(x), 1] += x * r * g


def pad(midis, dur, vel):
    """Warm analog-style pad: three slightly detuned saws per note, low-passed, slow attack and release."""
    n = int((dur + 0.4) * SR)
    tt = np.arange(n) / SR
    y = np.zeros(n, np.float32)
    for m in midis:
        f0 = 440 * 2 ** ((m - 69) / 12)
        for dt in (-0.12, 0.0, 0.11):
            ph = (tt * f0 * 2 ** (dt / 12)) % 1.0
            y += (2 * ph - 1).astype(np.float32)
    y = filt(y, 900, "low", 4)
    env = np.minimum(1, tt / 0.35) * np.clip((dur + 0.4 - tt) / 0.4, 0, 1)
    return (y * env / (3 * len(midis)) * vel * 3).astype(np.float32)


def boom(dur, vel, f0=49.0):
    """Sub impact (sine with a pitch drop) instead of a bowed contrabass hit."""
    tt = np.arange(int(dur * SR)) / SR
    f = f0 * (1 + 1.2 * np.exp(-tt / 0.05))
    return (np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt / (dur / 3)) * vel).astype(np.float32)



def tdrum(midi_shift, curve, dur, vel):
    """Talking drum: a real bongo hit re-pitched along a time-varying bend (semitones over time)."""
    x = BONGO_L if midi_shift < 0 else BONGO_H
    n = int(dur * SR)
    tt = np.arange(n) / SR
    semis = np.interp(tt, np.linspace(0, dur, len(curve)), curve) + midi_shift
    rate = 2 ** (semis / 12)
    pos = np.cumsum(rate)
    pos = pos[pos < len(x) - 1]
    y = np.interp(pos, np.arange(len(x)), x).astype(np.float32)
    y *= np.linspace(1, 0.2, len(y))
    return y * vel


def put_td(t, kind, vel=0.5):
    pats = {"call": [(0, [0, 3, 3], 0.35), (0.29, [3, -2, -4], 0.45), (0.58, [0, 5, 2], 0.3)],
            "roll": [(k * 0.072, [k * 0.6, k * 0.6 - 1], 0.18) for k in range(10)],
            "lick": [(0, [2, 5, 0], 0.4), (0.43, [0, -3], 0.3), (0.72, [5, 7, 3], 0.4)]}
    for dt, cv, d in pats[kind]:
        put("perc", tdrum(-1, cv, d, vel), t + dt, 0.15)

B4 = BEAT
def at(b):
    return b * B4


def logdrum(midi, dur, vel):
    tt = np.arange(int(dur * SR)) / SR
    f0 = 440 * 2 ** ((midi - 69) / 12)
    f = f0 * (1 + 1.6 * np.exp(-tt / 0.028))
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt / (dur * 0.5))
    x += 0.32 * np.sin(2 * np.pi * np.cumsum(f * 2.0) / SR) * np.exp(-tt / 0.05)
    return (np.tanh(2.6 * x) * 0.5 * vel).astype(np.float32)


def clap(vel):
    tt = np.arange(int(0.3 * SR)) / SR
    env = sum(np.exp(-np.clip(tt - d, 0, None) / 0.011) * (tt >= d) for d in (0, 0.01, 0.021)) + 0.5 * np.exp(-tt / 0.1)
    return (filt(filt(rng.standard_normal(len(tt)), 900, "high"), 7500, "low") * env * 0.33 * vel).astype(np.float32)



B4 = BEAT
def at(b):
    return b * B4


def snap(vel):
    tt = np.arange(int(0.16 * SR)) / SR
    x = filt(filt(rng.standard_normal(len(tt)), 1800, "high"), 6500, "low") * (np.exp(-tt / 0.012) + 0.25 * np.exp(-tt / 0.05))
    x += 0.25 * np.sin(2 * np.pi * 1100 * tt) * np.exp(-tt / 0.01)
    return (x * 0.5 * vel).astype(np.float32)


def sub(midi, dur, vel, slide_to=None):
    tt = np.arange(int(dur * SR)) / SR
    f0 = 440 * 2 ** ((midi - 69) / 12)
    f = np.full(len(tt), f0)
    if slide_to is not None:
        f1 = 440 * 2 ** ((slide_to - 69) / 12)
        k = int(len(tt) * 0.7)
        f[k:] = f0 + (f1 - f0) * np.linspace(0, 1, len(tt) - k) ** 2
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) + 0.18 * np.sin(4 * np.pi * np.cumsum(f) / SR)
    env = np.minimum(1, tt / 0.01) * np.exp(-tt / (dur * 0.9))
    env[-int(0.04 * SR):] *= np.linspace(1, 0, int(0.04 * SR))
    return (np.tanh(1.6 * x) * env * 0.55 * vel).astype(np.float32)


def epiano(midis, dur, vel):
    """electric-piano colour: real piano voicing, low-passed, slow tremolo, soft attack"""
    y = None
    for j, m in enumerate(midis):
        n = note("piano", m, dur, vel, 0.3)
        y = n if y is None else (np.pad(y, (0, max(0, len(n) - len(y)))) + np.pad(n, (0, max(0, len(y) - len(n)))))
    tt = np.arange(len(y)) / SR
    y = filt(y, 2600, "low") * (1 - 0.22 * (0.5 + 0.5 * np.sin(2 * np.pi * 4.6 * tt)))
    return (y * np.minimum(1, tt / 0.012)).astype(np.float32)


CH = [(38, [60, 64, 65, 69, 72]), (34, [58, 62, 65, 69, 70]), (31, [58, 62, 65, 67, 70]), (33, [57, 61, 62, 64, 67])]   # Dm9 Bbmaj7 Gm9 A7sus
HARP = [74, 77, 81, 79]
TOTB = int(np.ceil(TOTAL / B4))
put("harp", note("harp", 74, 1.6, 0.32, 0.8), 0.05, 0.2)           # the light comes up
for k, m in enumerate([62, 65, 69]):
    put("strings", note("cello", m, at(1.2), 0.22, 0.6), 0.0, -0.2 + 0.2 * k)
for bar in range(0, TOTB // 4 + 1):
    b0 = bar * 4 + 1
    t0 = at(b0)
    if t0 >= TOTAL:
        break
    root, voic = CH[bar % 4]
    face = 23 <= b0 < 39
    end = b0 >= 43
    put("drums", KICK * 0.8, at(b0))                                 # sparse, deep kick: 1 and the "and" of 3
    put("drums", KICK * 0.55, at(b0 + 2.5))
    for k in (1, 3):                                                 # finger snaps on 2 & 4 + soft rim ghost
        put("perc", snap(1.0), at(b0 + k), 0.15)
        put("perc", BONGO_H * 0.18, at(b0 + k + 0.75), -0.3)
    for s_ in range(8):                                              # airy closed hat, swung 8ths, very quiet
        put("perc", HAT * (0.14 if s_ % 2 else 0.09), at(b0 + s_ / 2) + (0.03 if s_ % 2 else 0), 0.25)
    put("bass", sub(root - 12 + 12, B4 * 2.6, 0.9, slide_to=root - 12 + 12 + (7 if bar % 2 else 5)), t0)    # sliding sub
    put("bass", sub(root - 12 + 12, B4 * 1.2, 0.7), at(b0 + 2.75))
    put("keys", epiano(voic, B4 * 3.6, 0.42 if face else 0.5), t0 + 0.01, -0.1)      # tremolo e-piano chord
    put("keys", epiano(voic[1:4], B4 * 0.8, 0.3), at(b0 + 2.5), 0.15)               # answering stab
    if bar % 2 == 0 or end:                                          # cello swell under every other bar
        put("strings", note("cello", root + 12, B4 * 4, 0.24, 0.8), t0, -0.25)
    if face or end:                                                  # sparse harp motif on the face routine and end card
        for k, m in enumerate(HARP):
            put("harp", note("harp", m, 1.0, 0.28, 0.6), at(b0 + 0.5 + k * 0.75), 0.3)
for b in (19, 38):                                                   # lineups: a soft swell + low hit
    put("fx", boom(1.4, 0.45, 46), at(b))
    for k, m in enumerate([62, 69, 74]):
        put("strings", note("violin" if m > 66 else "cello", m, at(2), 0.18, 0.6), at(b) - 0.2, -0.2 + 0.2 * k)
for k, m in enumerate([74, 77, 81, 86]):                             # end card bloom
    put("harp", note("harp", m, 1.2, 0.34, 0.6), at(42) + k * 0.08, -0.3 + 0.2 * k)
put("fx", boom(1.8, 0.6, 44), at(42))

def reverb(x, dur, pre=0.02, damp=5000):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    ir = rng.standard_normal((n, 2)) * np.exp(-tt / (dur / 6.5))[:, None]
    ir = filt(ir, damp, "low")
    ir = np.concatenate([np.zeros((int(pre * SR), 2)), ir])
    ir /= np.sqrt((ir ** 2).sum(0))
    return np.stack([fftconvolve(x[:, c], ir[:, c])[:N] for c in range(2)], 1).astype(np.float32)


def biquad(x, kind, f0, gain_db, q=0.8):
    """RBJ peaking / shelving EQ."""
    A, w = 10 ** (gain_db / 40), 2 * np.pi * f0 / SR
    al, cw = np.sin(w) / (2 * q), np.cos(w)
    if kind == "peak":
        b = [1 + al * A, -2 * cw, 1 - al * A]; a = [1 + al / A, -2 * cw, 1 - al / A]
    else:
        sA = 2 * np.sqrt(A) * al
        sg = 1 if kind == "high" else -1
        b = [A * ((A + 1) + sg * (A - 1) * cw + sA), -2 * sg * A * ((A - 1) + sg * (A + 1) * cw), A * ((A + 1) + sg * (A - 1) * cw - sA)]
        a = [(A + 1) - sg * (A - 1) * cw + sA, 2 * sg * ((A - 1) - sg * (A + 1) * cw), (A + 1) - sg * (A - 1) * cw - sA]
    from scipy.signal import lfilter
    return lfilter(np.array(b) / a[0], np.array(a) / a[0], x, axis=0).astype(np.float32)

buses["strings"] = filt(buses["strings"], 170, "high")
buses["piano"] = biquad(filt(buses["piano"], 120, "high"), "peak", 300, -4.0, 0.9)
buses["harp"] = filt(buses["harp"], 140, "high")
buses["lead"] = filt(buses["lead"], 300, "high")
hall = buses["keys"] * 0.5 + buses["strings"] * 0.9 + buses["harp"] * 1.0 + buses["fx"] * 0.3 + buses["perc"] * 0.2
mix = (buses["keys"] * 0.9 + buses["strings"] * 0.85 + buses["bass"] * 0.95 + buses["harp"] * 0.8
       + buses["drums"] * 0.95 + buses["perc"] * 0.95 + buses["fx"] * 0.75 + filt(reverb(hall, 2.4), 200, "high") * 0.35)
mix = filt(mix, 32, "high")
mix = biquad(mix, "peak", 280, -4.0, 0.7)
mix = biquad(mix, "high", 8000, 2.5, 0.7)
env = filt(np.abs(mix).mean(1), 6, "low")
g = np.where(env > 0.24, (0.24 / np.maximum(env, 1e-6)) ** 0.45, 1.0)
mix *= g[:, None]
ft = int((TOTAL - 1.8) * SR)
mix[ft:] *= np.linspace(1, 0, N - ft)[:, None] ** 1.3
mix *= 0.89 / np.abs(mix).max()
sf.write(sys.argv[2], mix, SR, subtype="PCM_24")
print("ok", TOTAL)
