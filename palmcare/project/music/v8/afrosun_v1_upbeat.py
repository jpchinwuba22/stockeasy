"""Video 5 (GlowShield) "Afro-sun" score. Based on the Afro-luxe engine: original premium "Afro-luxe" score for PalmCare Video 3, played with real recorded instruments (tonejs-instruments
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
BEAT = 0.6
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


# ---------- harmony: A major, sunlit and open (100 BPM, bar = 2.4 s) ----------
#            Amaj9                    F#m9                     Dmaj9                    Esus
CH = [(45, [61, 64, 68, 71, 76]), (42, [61, 64, 66, 69, 73]), (38, [57, 61, 64, 66, 69]), (40, [59, 64, 66, 69, 71])]
HOOK2, REVEAL, SHIELD, FIN, EC = HITS          # "meet your match" cut, pack reveal, shield, finale, end card
BARS = int(np.ceil(TOTAL / BAR))


def sect(t):
    if t < 8.0: return "hook"
    if t < REVEAL: return "problem"
    if t < SHIELD: return "groove"
    if t < FIN: return "lift"
    if t < EC: return "finale"
    return "end"


def near(t, pre=0.6):
    return any(h - pre <= t < h + 0.15 for h in HITS)


for bar in range(BARS):
    t0 = bar * BAR
    root, ch = CH[bar % 4]
    s = sect(t0 + 0.01)
    fade_end = t0 >= TOTAL - 4.0
    # strings: airy pads throughout (problem: lower and darker, cello only)
    sv = {"hook": 0.40, "problem": 0.42, "groove": 0.36, "lift": 0.42, "finale": 0.42, "end": 0.50}[s]
    for m in (root - 12 + 24, ch[1] - 12):
        put("strings", note("cello", m, BAR + 0.4, sv), t0, -0.35)
    if s != "problem" and (bar % 2 == 0 or s in ("lift", "end")):
        for m in (ch[2] + 12, ch[3] + 12):
            put("strings", note("violin", m, 2 * BAR + 0.4, sv * 0.5), t0, 0.35)
    # low end
    if s in ("problem",) and not fade_end:
        put("bass", note("contrabass", root - 12, BAR + 0.2, 0.45), t0, 0)
    if s in ("groove", "lift", "finale") and not fade_end:
        for st, m, v in ((0, root, 0.55), (6, root, 0.35), (10, root + 7, 0.4), (14, root + 12, 0.3)):
            put("bass", note("bass-electric", m, 0.5, v, 0.15), t0 + st * S16, 0)
    # nylon highlife guitar: soft off-beat double-stops (the sunny pulse), only in the groove sections
    if s in ("groove", "lift", "finale") and not fade_end:
        for k, st in enumerate((2, 6, 9, 10, 14)):
            t = t0 + st * S16
            if near(t):
                continue
            for m in (ch[2] + 12, ch[4] + 12) if k % 2 == 0 else (ch[1] + 12, ch[3] + 12):
                put("gtr", note("guitar-nylon", m, 0.35, 0.22, 0.2), t, 0.3 if k % 2 else -0.2)
    # percussion: shaker 8ths + sparse bongos (groove on)
    if s in ("groove", "lift", "finale") and not fade_end:
        for e in range(8):
            t = t0 + e * BEAT / 2
            if not near(t):
                put("perc", SHAKE * (0.22 if e % 2 else 0.12), t, 0.45)
        for st, b, v in ((3, BONGO_H, 0.16), (7, BONGO_H, 0.12), (11, BONGO_L, 0.16), (15, BONGO_H, 0.10)):
            put("perc", b * v, t0 + st * S16, -0.4)
        if s == "lift":
            put("drums", KICK * 0.30, t0, 0); put("drums", KICK * 0.22, t0 + 8 * S16, 0)
    # problem: a slow heartbeat pulse (tension, not drama)
    if s == "problem":
        for b in (0, 2):
            put("drums", filt(KICK, 900, "low") * 0.35, t0 + b * BEAT, 0)
    # piano: sparse warm notes
    if not fade_end and s != "hook":
        pat = {"problem": ((0, 1), (8, 3)), "groove": ((0, -1), (12, 3)), "lift": ((0, -1), (6, 2), (12, 3)),
               "finale": ((0, -1), (8, 2)), "end": ((0, -1), (8, 2))}[s]
        for k, (st, idx) in enumerate(pat):
            t = t0 + st * S16
            if not near(t, 0.4):
                put("piano", note("piano", ch[idx] + 12, 2.2, 0.30, 1.8), t, 0.25 * (-1) ** k)
    # harp sparkles (sun glints) in lift / finale / end
    if s in ("lift", "finale", "end") and bar % 2 == 1:
        arp = [ch[0] + 24, ch[2] + 12, ch[3] + 12, ch[4] + 12, ch[2] + 24]
        for k, m in enumerate(arp):
            put("harp", note("harp", m, 1.4, 0.20, 1.2), t0 + 1.2 + k * 0.11, -0.3 + 0.15 * k)

# ---------- hook: heat shimmer swell, sub impact on "Lagos sun", second impact on "meet your match" ----------
n = int(3.6 * SR)
noise = rng.standard_normal(n).astype(np.float32)
shim = filt(noise, [3000, 9000], "band") * np.linspace(0, 1, n) ** 2 * 0.05
shim *= (1 + 0.5 * np.sin(2 * np.pi * 7 * np.arange(n) / SR))
put("fx", shim, 0.0, -0.2); put("fx", shim[::-1] * 0.4, 0.4, 0.3)
for t, base in ((0.85, 33), (HOOK2, 33)):
    put("fx", note("contrabass", base + 12, 3.0, 0.9), t, 0)
    for m in (45, 57, 64, 69):
        put("fx", note("piano", m, 3.5, 0.45, 2.5), t, 0)
for k, m in enumerate((76, 81, 83, 88)):                         # flute: a bright four-note "sun" motif between the lines
    put("harp", note("flute", m, 0.5 if k < 3 else 1.6, 0.28, 0.4), 2.0 + k * 0.3, 0.2)

# ---------- reveal / shield / end card: harp glissando + reversed swell into the hit, warm impact on it ----------
for h in (REVEAL, SHIELD, EC):
    scale = [64, 66, 68, 69, 71, 73, 76, 78, 80, 81, 83, 85]
    for k, m in enumerate(scale):
        put("harp", note("harp", m, 1.2, 0.30 + 0.035 * k, 1.0), h - 1.15 + k * 0.09, -0.3 + 0.05 * k)
    for m in (33, 45, 57, 64, 69, 73):
        put("fx", note("piano", m, 3.5, 0.45, 2.5), h, 0)
    put("fx", note("contrabass", 45, 3.0, 0.8), h, 0)
    sw = note("piano", 76, 2.0, 0.5, 1.5)
    rv = fftconvolve(sw, rng.standard_normal(int(1.6 * SR)) * np.exp(-np.arange(int(1.6 * SR)) / SR / 0.5))[: int(2.0 * SR)]
    rv = (rv / (np.abs(rv).max() + 1e-9) * 0.3)[::-1].astype(np.float32)
    put("fx", rv, h - len(rv) / SR, 0)
for k, m in enumerate((76, 81, 83, 88)):                         # the sun motif returns on the end card
    put("harp", note("flute", m, 0.5 if k < 3 else 2.0, 0.24, 0.5), EC + 3.0 + k * 0.3, 0.2)

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
sf.write(sys.argv[0].replace("afrosun.py", "music_v8.wav"), mix, SR, subtype="PCM_24")
print("ok", BARS, "bars", {k: len(v) for k, v in BANKS.items()})
