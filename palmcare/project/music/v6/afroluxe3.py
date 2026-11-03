"""Original premium "Afro-luxe" score for PalmCare Video 3, played with real recorded instruments (tonejs-instruments
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
TOTAL, HITS = float(sys.argv[1]), [float(x) for x in sys.argv[2:6]]
BEAT = 0.5
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


# ---------- harmony: D major, warm and hopeful ----------
#            Bm9                 Gmaj7               D/F#                A(sus)
CH = [(47, [59, 62, 66, 69, 73]), (43, [59, 62, 66, 67, 71]), (42, [57, 62, 66, 69, 74]), (45, [57, 61, 64, 69, 71])]
H1, H2, H3, H4 = HITS
BARS = int(np.ceil(TOTAL / BAR))


def sect(t):
    if t < H1: return "intro"      # hook: three drops
    if t < H2: return "wash"       # sunrise / Vita C+ (warm gold groove)
    if t < H3: return "lotion"     # daylight / N10 (brighter, fuller)
    if t < H4: return "night"      # midnight / DermaLuxe Pro (calm, dreamy)
    return "end"


def near_hit(t, pre=1.5):
    return any(h - pre <= t < h for h in HITS)


for bar in range(BARS):
    t0 = bar * BAR
    root, ch = CH[bar % 4]
    s = sect(t0 + 0.01)
    fade_end = t0 >= TOTAL - 4.0
    # ---- strings: slow, warm sustained pads under everything (cello low, violins airy and quiet)
    sv = {"intro": 0.45, "wash": 0.42, "lotion": 0.42, "night": 0.40, "end": 0.55}[s]
    for m in (root - 12 + 24, ch[1] - 12):
        put("strings", note("cello", m, BAR + 0.4, sv), t0, -0.35, 1.0)
    if bar % 2 == 0 or s == "end":
        for m in (ch[2] + 12, ch[3] + 12):
            put("strings", note("violin", m, 2 * BAR + 0.4, sv * 0.55), t0, 0.35, 1.0)
    # ---- deep, soft low end: one long contrabass note per bar
    if s != "intro" and not fade_end:
        put("bass", note("contrabass", root - 12, BAR + 0.2, 0.5), t0, 0)
    # ---- piano: sparse, spacious notes (no rhythm section); a little brighter by day, darker at night
    if not fade_end:
        pat = {"intro": ((6, 2), (10, 3), (14, 1)), "wash": ((0, -1), (6, 2), (12, 3)), "lotion": ((0, -1), (4, 3), (8, 2), (12, -1)),
               "night": ((0, 1), (8, 2)), "end": ((0, -1), (8, 2))}[s]
        oct_ = {"intro": 12, "wash": 12, "lotion": 24, "night": 12, "end": 12}[s]
        for k, (st, idx) in enumerate(pat):
            t = t0 + st * S16
            if near_hit(t, 0.4) or (bar == 0 and st < 6):
                continue
            put("piano", note("piano", ch[idx] + oct_, 2.2, 0.34 if s != "night" else 0.28, 1.8), t, 0.25 * (-1) ** k)
    else:
        for m in ch:
            put("piano", note("piano", m, 3.0, 0.35, 2.0), t0, 0)
    # ---- harp: gentle rising arpeggio every other bar (night: every bar, softer)
    if (s in ("wash", "lotion") and bar % 2 == 1) or s == "night":
        arp = [ch[0] + 12, ch[1] + 12, ch[2] + 12, ch[3] + 12, ch[1] + 24]
        for k, m in enumerate(arp):
            put("harp", note("harp", m, 1.4, 0.20 if s == "night" else 0.24, 1.2), t0 + 1.0 + k * 0.12, -0.3 + 0.15 * k)

# ---------- hook: a bright "drop" accent on each of the three opening shots ----------
for k, t in enumerate((0.25, 2.25, 4.25)):
    for m in (86, 93):
        put("harp", note("harp", m - 2 * k, 1.5, 0.55, 1.2), t, (-0.4, 0.0, 0.4)[k])
    put("fx", note("piano", 38 + (0, 5, 7)[k], 2.0, 0.6, 1.5), t, 0)

# ---------- reveals: harp glissando + tom swell into each hit, a deep piano/contrabass impact on it ----------
for h in HITS:
    scale = [62, 64, 66, 69, 71, 74, 76, 78, 81, 83, 86, 88]
    for k, m in enumerate(scale):
        put("harp", note("harp", m, 1.2, 0.35 + 0.04 * k, 1.0), h - 1.2 + k * 0.09, -0.3 + 0.05 * k)
    for m in (38, 50, 57, 62, 66, 69):
        put("fx", note("piano", m, 3.5, 0.5, 2.5), h, 0)
    put("fx", note("contrabass", 38, 3.0, 0.9), h, 0)
    # reversed piano swell into the hit
    sw = note("piano", 74, 2.0, 0.5, 1.5)
    rv = fftconvolve(sw, rng.standard_normal(int(1.6 * SR)) * np.exp(-np.arange(int(1.6 * SR)) / SR / 0.5))[: int(2.0 * SR)]
    rv = (rv / (np.abs(rv).max() + 1e-9) * 0.35)[::-1].astype(np.float32)
    put("fx", rv, h - len(rv) / SR, 0)

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
       + buses["drums"] * 0.75 + buses["perc"] * 1.1 + buses["fx"] * 0.7 + filt(reverb(hall, 2.6), 200, "high") * 0.35)
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
sf.write("music_v6b.wav", mix, SR, subtype="PCM_24")
print("ok", BARS, "bars", {k: len(v) for k, v in BANKS.items()})
