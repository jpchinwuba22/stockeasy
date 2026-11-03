"""Video 7 score: "Naija Bounce", upbeat Afrobeats (Afro-pop):, an original Afro-Amapiano beat in the style trending in Nigerian ads (log drums,
four-on-the-floor, shekere shaker, talking-drum calls, a catchy flute hook, Afro piano stabs, electric bass), played
with real recorded instruments (tonejs-instruments + Tone.js drum samples, CC-BY 3.0). 112 BPM, Bb minor.
Built to the edit's beat grid: 4-beat pickup (log drum on every product-rush cut + riser), DROP on the PalmCare title,
groove through the three sets (talking-drum call into each), half-time pack section with hits on every pack, riser into
the collection finale, lighter end-card groove that resolves. Usage: naija_glow.py TOTAL OUT.wav"""
import glob
import os
import re
import sys

import numpy as np
import soundfile as sf
from scipy.signal import butter, fftconvolve, resample_poly, sosfilt

SR = 48000
TOTAL = float(sys.argv[1])
BEAT = 60 / 112
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

buses = {k: np.zeros((N, 2), np.float32) for k in ("piano", "strings", "gtr", "bass", "harp", "drums", "perc", "fx", "lead")}


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


# upbeat Afro-pop in F major: F - Dm - Bb - C (bright, happy), tresillo Afrobeats groove
CH = [(41, [65, 69, 72, 76]), (38, [62, 65, 69, 72]), (46, [62, 65, 70, 74]), (48, [64, 67, 72, 76])]
HOOK = [(0, 81, 0.3), (0.5, 84, 0.3), (1.0, 81, 0.3), (1.5, 79, 0.45), (2.0, 77, 0.3), (2.5, 79, 0.3), (3.0, 81, 0.8)]
GTR = [77, 81, 84, 81, 79, 81, 84, 88]                         # highlife guitar 16th-note arpeggio (transposed per chord)
TOTB = int(np.ceil(TOTAL / B4))
put("fx", boom(1.2, 0.8, 52), at(1))                          # the gold drop hits
for k in range(6):                                            # one hit per colour pop
    put("drums", KICK * 0.8, at(1 + 0.5 * k))
    put("drums", clap(0.55), at(1 + 0.5 * k) + 0.002, 0.1 if k % 2 else -0.1)
    put("perc", BONGO_H * 0.5 if k % 2 else BONGO_L * 0.55, at(1 + 0.5 * k) + 0.25 * B4, 0.3)
rz = np.arange(int(at(4) * SR)) / SR
put("fx", (filt(rng.standard_normal(len(rz)), 1800, "high") * (rz / rz[-1]) ** 3 * 0.3).astype(np.float32), 0)
put_td(at(3), "roll", 0.55)
put("fx", boom(1.6, 0.9), at(4))
for bar in range(1, TOTB // 4 + 1):
    b0 = bar * 4
    t0 = at(b0)
    if t0 >= TOTAL:
        break
    root, voic = CH[bar % 4]
    face = 32 <= b0 < 48                                       # serum section: same bounce, lighter, no hook
    end = b0 >= 54
    rise = 46 <= b0 < 50
    for kb in (0, 1.5, 3, 3.5 if bar % 2 else None):           # Afrobeats kick: tresillo + pickup
        if kb is not None:
            put("drums", KICK * (0.8 if face else 1.0), at(b0 + kb))
    for k in (1, 3):                                           # snare + clap backbeat
        put("drums", SNARE * (0.35 if face else 0.5), at(b0 + k), 0.05)
        put("drums", clap(0.6 if face else 0.85), at(b0 + k), -0.1)
    for rb in (0.75, 2.25, 2.75):                              # syncopated rim clicks
        put("perc", BONGO_H * 0.3, at(b0 + rb), 0.35)
    for s_ in range(16):                                       # shekere 16ths, accented & swung
        put("perc", SHAKE * (0.65 if s_ % 4 == 2 else 0.4 if s_ % 2 else 0.25), at(b0 + s_ / 4) + (0.018 if s_ % 2 else 0), 0.3 if s_ % 4 else -0.25)
    for s_ in range(8):
        put("perc", HAT * (0.28 if s_ % 2 else 0.18), at(b0 + s_ / 2), -0.15)
    for k, (cb, lo) in enumerate(((0.5, 1), (1.25, 0), (2.0, 1), (2.5, 0), (3.25, 1))):     # congas
        put("perc", (BONGO_L if lo else BONGO_H) * 0.42, at(b0 + cb), -0.35 if lo else 0.35)
    for kb, semi, d in ((0, 0, 0.9), (1.5, 0, 0.5), (2.0, 7, 0.4), (3.0, 5, 0.5), (3.5, 7, 0.4)):   # syncopated bass
        put("bass", note("bass-electric", root - 12 + 12 + semi, B4 * d, 0.6, 0.08), at(b0 + kb))
    if not face:
        for s_ in range(16):                                   # highlife guitar riff
            m = GTR[s_ % 8] + (root - 41)
            while m > 90: m -= 12
            put("gtr", note("guitar-nylon", m, B4 * 0.3, 0.42 if s_ % 2 == 0 else 0.3, 0.06), at(b0 + s_ / 4) + 0.006, 0.4)
    for off in (0.5, 1.5, 2.5, 3.5):                           # off-beat piano skank
        for j, m in enumerate(voic):
            put("piano", note("piano", m, B4 * 0.35, 0.42 if face else 0.5, 0.08), at(b0 + off) + j * 0.006, -0.3 + 0.2 * j)
    if (not face and not rise and bar % 2 == 1) or (end and bar % 2 == 0):    # the flute hook
        for off, m, d in HOOK:
            put("lead", note("flute", m, d * B4 * 1.6, 0.45, 0.12), at(b0 + off), 0.2)
    if face:
        put("strings", note("cello", root + 12, B4 * 3.8, 0.28, 0.4), t0, -0.2)
    if bar % 2 == 0 and not face:
        put_td(at(b0 + 3), "lick", 0.5)
# talking-drum calls into each set and the packs; hits on every pack; riser into the finale
for b in (7, 15, 23, 31):
    put_td(at(b), "call", 0.55)
for b in (8, 12, 16, 20, 24, 28):
    put("fx", boom(0.9, 0.45), at(b))                         # every product lands on a hit
for b in (34, 37, 40, 43, 46):
    put("harp", note("harp", 82, 1.2, 0.35, 0.6), at(b) + 6 / 24, 0.2)
for b in (34, 37, 40, 43, 46):
    put("fx", boom(1.2, 0.7), at(b))
rz = np.arange(int(at(4) * SR)) / SR
put("fx", (filt(rng.standard_normal(len(rz)), 1500, "high") * (rz / rz[-1]) ** 3 * 0.28).astype(np.float32), at(46))
put("fx", boom(1.8, 1.0, 44), at(50))
for j, m in enumerate([58, 61, 65, 70, 73]):
    put("strings", note("violin" if m > 62 else "cello", m, at(4), 0.3, 0.8), at(50), -0.3 + 0.15 * j)
for k, m in enumerate([70, 73, 77, 80, 82, 85, 89]):
    put("harp", note("harp", m, 1.0, 0.4, 0.5), at(50) + k * 0.06, -0.4 + 0.12 * k)
put("fx", boom(1.6, 0.8), at(54))
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
hall = buses["piano"] * 0.45 + buses["strings"] * 0.8 + buses["harp"] * 0.9 + buses["lead"] * 0.6 + buses["fx"] * 0.3 + buses["perc"] * 0.12
mix = (buses["piano"] * 0.8 + buses["strings"] * 0.8 + buses["lead"] * 0.85 + buses["bass"] * 0.85 + buses["harp"] * 0.8
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
