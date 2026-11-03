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
    fade_end = t0 >= TOTAL - 4.5
    # ---- strings: sustained chord pads (cello low, violins high); swell in, bigger after reveal 2
    if s in ("intro", "lotion", "night", "end"):
        sv = {"intro": 0.55, "lotion": 0.5, "night": 0.62, "end": 0.7}[s]
        for m in (root - 12 + 24, ch[1] - 12):
            put("strings", note("cello", m, BAR + 0.3, sv), t0, -0.35, 1.0)
        for m in (ch[2] + 12, ch[3] + 12) if s != "intro" or bar >= 1 else ():
            put("strings", note("violin", m, BAR + 0.3, sv * 0.75), t0, 0.35, 1.0)
    # ---- piano
    if s in ("intro", "night"):
        for k, (st, m) in enumerate(((0, ch[-1] + 12), (6, ch[2] + 12), (10, ch[3] + 12), (14, ch[1] + 24))):
            if bar == 0 and st < 6:
                continue
            put("piano", note("piano", m, 1.6, 0.5, 1.2), t0 + st * S16, 0.2 * (-1) ** k)
    elif not fade_end:
        # Afro piano: off-beat chord stabs + a sparkle line on top
        for st in (2, 6, 10, 13):
            t = t0 + st * S16
            if near_hit(t, 0.6):
                continue
            for m in ch[1:4]:
                put("piano", note("piano", m, 0.22, 0.32, 0.12), t, -0.15)
        if s in ("lotion", "end"):
            for st, m in ((0, ch[-1] + 12), (3, ch[-2] + 12), (8, ch[-1] + 12), (11, ch[2] + 12)):
                put("piano", note("piano", m, 0.6, 0.30, 0.5), t0 + st * S16, 0.3)
    else:
        for m in ch:
            put("piano", note("piano", m, 3.0, 0.45, 2.0), t0, 0)
    # ---- nylon guitar: highlife arpeggio (wash + lotion)
    if s in ("wash", "lotion") and not fade_end:
        arp = [ch[0], ch[2], ch[3], ch[2] + 12, ch[3], ch[1] + 12, ch[3], ch[2]]
        for k, st in enumerate((0, 2, 3, 5, 8, 10, 11, 13)):
            t = t0 + st * S16
            if near_hit(t, 0.4):
                continue
            put("gtr", note("guitar-nylon", arp[k] , 0.45, 0.55 if st % 4 == 0 else 0.42, 0.25), t + 0.006 * (k % 2), 0.4)
    # ---- bass: round electric bass, syncopated (from reveal 1)
    if s == "night" and not fade_end:
        put("bass", note("contrabass", root - 12, BAR, 0.6), t0, 0)
    if s not in ("intro", "night") and not fade_end:
        for st, iv, ln in ((0, 0, 0.45), (3, 0, 0.2), (6, 7, 0.3), (10, 0, 0.35), (13, 12, 0.18), (14, 7, 0.25)):
            t = t0 + st * S16
            if near_hit(t, 0.5):
                continue
            put("bass", note("bass-electric", root - 12 + iv, ln, 0.9, 0.06), t, 0)
    if s == "end" and fade_end is False:
        put("bass", note("contrabass", root - 12, BAR, 0.8), t0, 0)
    # ---- drums: light Afro kit (wash on), bongos, shaker
    if s == "night" and t0 < TOTAL - 4:                       # night: only a soft heartbeat kick and a whisper of shaker
        for st in range(16):
            t = t0 + st * S16
            if near_hit(t, 1.0):
                continue
            if st in (0, 10):
                put("drums", KICK, t, 0, 0.45)
            if st % 2:
                put("perc", SHAKE, t, 0.35, 0.16)
    if s in ("wash", "lotion", "end") and t0 < TOTAL - 4:
        for st in range(16):
            t = t0 + st * S16
            if near_hit(t, 1.0):
                continue
            sw = 0.014 if st % 2 else 0
            if st in (0, 7, 10) or (s == "lotion" and st == 4):
                put("drums", KICK, t, 0, 0.8 if st == 0 else 0.6)
            if st == 8:
                put("drums", SNARE, t, 0.05, 0.45)
            put("perc", SHAKE, t + sw, 0.35, 0.42 if st % 2 else 0.26)
            if st in (3, 6, 11, 14):
                put("perc", BONGO_H if st in (3, 11) else BONGO_L, t + sw, -0.4, 0.5)
            if s != "wash" and st in (2, 6, 10, 14):
                put("perc", HAT, t + sw, 0.2, 0.18)

# ---------- hook: a bright "drop" accent on each of the three opening shots ----------
for k, t in enumerate((0.25, 2.25, 4.25)):
    for m in (86, 93):
        put("harp", note("harp", m - 2 * k, 1.5, 0.55, 1.2), t, (-0.4, 0.0, 0.4)[k])
    put("fx", note("piano", 38 + (0, 5, 7)[k], 2.0, 0.6, 1.5), t, 0)
    put("fx", KICK, t, 0, 0.55)

# ---------- reveals: harp glissando + tom swell into each hit, a deep piano/contrabass impact on it ----------
for h in HITS:
    scale = [62, 64, 66, 69, 71, 74, 76, 78, 81, 83, 86, 88]
    for k, m in enumerate(scale):
        put("harp", note("harp", m, 1.2, 0.35 + 0.04 * k, 1.0), h - 1.2 + k * 0.09, -0.3 + 0.05 * k)
    for k in range(12):
        put("perc", TOM, h - 1.5 + k * S16, 0, 0.15 + 0.03 * k)
    for m in (38, 50, 57, 62, 66, 69):
        put("fx", note("piano", m, 3.5, 0.75, 2.5), h, 0)
    put("fx", note("contrabass", 38, 3.0, 0.9), h, 0)
    put("fx", KICK, h, 0, 1.0)
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
mix = biquad(mix, "peak", 3200, 2.5, 0.9)                 # presence
mix = biquad(mix, "high", 7000, 6.0, 0.7)                 # air
env = filt(np.abs(mix).mean(1), 6, "low")
g = np.where(env > 0.22, (0.22 / np.maximum(env, 1e-6)) ** 0.4, 1.0)
mix *= g[:, None]
ft = int((TOTAL - 3.0) * SR)
mix[ft:] *= np.linspace(1, 0, N - ft)[:, None] ** 1.3
mix *= 0.89 / np.abs(mix).max()
sf.write("music_v6.wav", mix, SR, subtype="PCM_24")
print("ok", BARS, "bars", {k: len(v) for k, v in BANKS.items()})
