"""Video 7 (The PalmCare Collection) original Nigerian Afrobeats score on the Afro-luxe sample engine: 104 BPM Afrobeats kit, shekere-style shaker, conga, a pitch-bending talking drum built from a real drum sample, highlife nylon-guitar riff, syncopated bass and piano stabs. Built from the engine of the original premium "Afro-luxe" score for PalmCare Video 3, played with real recorded instruments (tonejs-instruments
and Tone.js drum samples, CC-BY 3.0): grand piano, cello and violin section, contrabass, harp, nylon guitar, electric
bass, acoustic kit and bongos. 120 BPM grid (bar = 2 s), D major, warm and cinematic over a gentle Afro groove.
Sections follow the edit: sunrise intro (strings + piano, no drums) -> REVEAL 1 -> wash groove (nylon highlife guitar,
Afro piano, bass, light kit + bongos) -> build -> REVEAL 2 -> lotion (strings join, fuller) -> UV lift -> END CARD
(resolving strings, piano and harp, groove thins, fades). Usage: afroluxe.py TOTAL HIT1 HIT2 HIT3 -> music_v4c.wav"""
import glob
import os
import re
import sys

import numpy as np
import soundfile as sf
from scipy.signal import butter, fftconvolve, resample_poly, sosfilt

SR = 48000
TOTAL, HITS = float(sys.argv[1]), [float(x) for x in sys.argv[2:]]
BEAT = 60 / 104
BAR = 4 * BEAT
S16 = BEAT / 4
N = int(TOTAL * SR)
SMP = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "samples")
rng = np.random.default_rng(5)
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


BANKS = {k: instrument(k) for k in ("piano", "cello", "violin", "contrabass", "harp", "guitar-nylon", "bass-electric")}


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

buses = {k: np.zeros((N, 2), np.float32) for k in ("piano", "strings", "gtr", "bass", "harp", "drums", "perc", "fx")}


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


# ---------- harmony: D major Afro-pop loop (Dmaj9 - Bm9 - Gmaj9 - A7sus) ----------
CH = [(38, [57, 61, 64, 66, 69]), (35, [57, 62, 64, 66, 69]), (31, [55, 59, 62, 66, 69]), (33, [57, 62, 64, 67, 71])]
DROP, REVEAL, FIN, EC = HITS                     # beat drop, hero reveal, finale, end card
BARS = int(np.ceil(TOTAL / BAR))


def sect(t):
    if t < DROP: return "hook"
    if t < REVEAL: return "verse"
    if t < REVEAL + 6.9: return "reveal"
    if t < FIN: return "body"
    if t < EC: return "finale"
    return "end"


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


for bar in range(BARS):
    t0 = bar * BAR
    root, ch = CH[bar % 4]
    s = sect(t0 + 0.01)
    fade_end = t0 >= TOTAL - 3.0
    if fade_end:
        continue
    full = s in ("reveal", "finale", "end")
    # ---- drums: Afrobeats kit (kick 1, 2-and-a-half, 3-and; rim on 2 and 4 with a clap layer on 4)
    if s != "hook":
        for st in (0, 6, 8, 11):                              # Afrobeats bounce kick
            put("drums", KICK * (0.72 if st in (0, 8) else 0.50), t0 + st * S16, 0)
        for st in (4, 12):                                    # clap layer on 2 and 4
            put("drums", filt(SNARE, 1500, "high") * 0.36, t0 + st * S16, 0.1)
            put("drums", filt(SNARE, 900, "high") * (0.26 if full else 0.18), t0 + st * S16 + 0.012, -0.1)
        STICK = filt(SNARE, 3500, "high")[: int(0.06 * SR)] * np.linspace(1, 0, int(0.06 * SR)) ** 2
        for st in (0, 3, 6, 10, 12):                          # tresillo sticks (the Naija groove)
            put("perc", STICK * 0.30, t0 + st * S16, 0.5)
    # ---- shekere-style shaker 16ths, accented on the off-beats
    for e in range(16):
        acc = 0.20 if e % 4 == 2 else (0.11 if e % 2 else 0.07)
        if s == "hook":
            acc *= 0.6 + 0.4 * (t0 / DROP)
        put("perc", SHAKE * acc, t0 + e * S16, 0.45)
    # ---- conga / bongo pattern
    if s != "hook":
        for st, b, v in ((3, BONGO_H, 0.22), (6, BONGO_L, 0.20), (11, BONGO_H, 0.18), (14, BONGO_L, 0.22), (15, BONGO_H, 0.12)):
            put("perc", b * v, t0 + st * S16, -0.4)
    # ---- syncopated bass
    if s != "hook":
        for st, m, v in ((0, root, 0.70), (3, root, 0.40), (6, root, 0.50), (8, root + 7, 0.50), (11, root + 5, 0.40), (14, root + 12, 0.36)):
            put("bass", note("bass-electric", m, 0.40, v, 0.12), t0 + st * S16, 0)
            n_ = int(0.38 * SR); tt_ = np.arange(n_) / SR
            sub = np.sin(2 * np.pi * 440 * 2 ** ((m - 12 - 69) / 12) * tt_) * np.exp(-tt_ / 0.22) * v * 0.55
            put("bass", sub.astype(np.float32), t0 + st * S16, 0)
    # ---- Afro-pop piano: off-beat chord stabs carry the harmony (no guitar, no strings)
    pv = 0.10 if s == "hook" else (0.20 if full else 0.13)
    for st in (2, 6, 10, 14) if s != "hook" else (6, 14):
        for m in ch[1:4]:
            put("piano", note("piano", m + 12, 0.22, pv, 0.25), t0 + st * S16, 0.15)
    # ---- warm synth pad underneath (soft detuned saws, low-passed) in place of the string section
    put("strings", pad([root + 24, ch[1], ch[2], ch[3]], BAR + 0.3, 0.07 if s != "hook" else 0.09), t0, 0)

# hook: riser into the drop, talking-drum call; impacts on the burst, the drop, the reveal, the finale, the end card
n = int(DROP * SR)
noise = rng.standard_normal(n).astype(np.float32)
riser = filt(noise, [800, 7000], "band") * np.linspace(0, 1, n) ** 3 * 0.10
put("fx", riser, 0.0, 0)
put_td(0.05, "call", 0.55)
put_td(DROP - 0.75, "roll", 0.45)
for h in (0.0, DROP, REVEAL, FIN, EC):
    put("fx", boom(2.2, 0.75), h, 0)
    put("drums", KICK * 0.8, h, 0)
    for m in (50, 57, 62, 66):
        put("fx", note("piano", m, 2.5, 0.28, 2.0), h, 0)
for h in (REVEAL, FIN, EC):
    put_td(h - 0.75, "roll", 0.4)
put_td(EC + 4 * BAR, "lick", 0.5)
BEAT_HITS = [16, 22, 28, 32, 38, 44, 48, 54, 60, 64, 68, 72, 78]      # v7 showcase: every hero product cut gets its hit
for b in BEAT_HITS:
    put("drums", KICK * 0.7, b * BEAT, 0)
    put("fx", boom(1.2, 0.35), b * BEAT, 0)
for g in (10.1, 19.9, 29.1, 40.3, 53.4):                     # talking-drum licks between the sets
    put_td(g, "lick", 0.5)
for k in range(11):                                           # each of the 11 products lands on its own hit
    w = 0.25 + k * BEAT / 2
    put("drums", KICK * 0.55, w, 0)
    put("perc", tdrum(-1, [3 + (k % 3), 0], 0.28, 0.5), w, 0.1)

# ---------- mix: reverb sends, balance, glue ----------
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


# clean the low-mids per instrument so the mix stays clear and airy (and leaves room for the voice)
buses["strings"] = filt(buses["strings"], 170, "high")
buses["piano"] = biquad(filt(buses["piano"], 110, "high"), "peak", 300, -4.0, 0.9)
buses["gtr"] = filt(buses["gtr"], 160, "high")
buses["harp"] = filt(buses["harp"], 140, "high")
buses["bass"] = biquad(buses["bass"], "peak", 220, -5.0, 1.0)
hall = sum(buses[k] * g for k, g in (("piano", 0.5), ("strings", 0.8), ("harp", 0.8), ("gtr", 0.3), ("fx", 0.4), ("perc", 0.15)))
mix = (buses["piano"] * 0.85 + buses["strings"] * 0.8 + buses["gtr"] * 0.8 + buses["bass"] * 0.5 + buses["harp"] * 0.8
       + buses["drums"] * 0.95 + buses["perc"] * 1.0 + buses["fx"] * 0.7 + filt(reverb(hall, 2.6), 200, "high") * 0.35)
mix = filt(mix, 35, "high")
mix = biquad(mix, "peak", 280, -4.5, 0.7)                 # de-mud
mix = biquad(mix, "peak", 2600, -5.0, 0.8)                # carve room for the voice
mix = biquad(mix, "peak", 1100, -2.5, 0.9)
mix = biquad(mix, "high", 8000, 3.0, 0.7)                 # gentle air
env = filt(np.abs(mix).mean(1), 6, "low")
g = np.where(env > 0.22, (0.22 / np.maximum(env, 1e-6)) ** 0.4, 1.0)
mix *= g[:, None]
ft = int((TOTAL - 3.0) * SR)
mix[ft:] *= np.linspace(1, 0, N - ft)[:, None] ** 1.3
mix *= 0.89 / np.abs(mix).max()
sf.write(sys.argv[0].replace("afrobeats10b.py", "music_v10b.wav"), mix, SR, subtype="PCM_24")
print("ok", BARS, "bars", {k: len(v) for k, v in BANKS.items()})
