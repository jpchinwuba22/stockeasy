"""Video 6 score, take 2: "Amapiano Luxe" on the real-instrument sample engine (tonejs-instruments + Tone.js drum
samples, CC-BY 3.0): 113 BPM, Ab major / F minor. Real grand piano jazzy voicings, cello + violin swells, harp
glissandi, nylon guitar plucks, electric bass under a pitch-gliding log drum (the Amapiano signature), acoustic kit,
bongos and shaker. Intro (street dialogue): soft piano + shaker -> harp run + riser -> DROP on the jar shot -> groove
under the review (thinned under the voice) -> string swell + harp into the HERO -> END CARD (full, violin topline,
fades). Usage: amapiano_luxe.py TOTAL DROP HERO END OUT.wav"""
import glob
import os
import re
import sys

import numpy as np
import soundfile as sf
from scipy.signal import butter, fftconvolve, resample_poly, sosfilt

SR = 48000
TOTAL, HITS = float(sys.argv[1]), [float(x) for x in sys.argv[2:5]]
BEAT = 60 / 113
BAR = 4 * BEAT
S16 = BEAT / 4
N = int(TOTAL * SR)
SMP = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "samples")
rng = np.random.default_rng(23)
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



DROP, HERO, END = HITS
# Fm9 - Dbmaj9 - Abmaj9 - Eb6/9 (bass roots MIDI), voicings
CH = [(41, [56, 60, 63, 67, 68]), (37, [56, 60, 63, 65, 68]), (44, [55, 60, 63, 67, 70]), (39, [55, 58, 63, 65, 70])]
BARS = int(np.ceil(TOTAL / BAR)) + 1


def logdrum(midi, dur, vel):
    tt = np.arange(int(dur * SR)) / SR
    f0 = 440 * 2 ** ((midi - 69) / 12)
    f = f0 * (1 + 1.5 * np.exp(-tt / 0.03))
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt / (dur * 0.5))
    x += 0.3 * np.sin(2 * np.pi * np.cumsum(f * 2.0) / SR) * np.exp(-tt / 0.06)
    return (np.tanh(2.4 * x) * 0.5 * vel).astype(np.float32)


LOG = [(0, 0), (0.75, 0), (1.5, 7), (2.5, 3), (3.25, 5)]
for b in range(BARS):
    t0 = b * BAR
    if t0 >= TOTAL:
        break
    root, voic = CH[b % 4]
    intro = t0 + BAR <= DROP + 1e-6
    end = t0 >= END - 0.01
    under_voice = not intro and t0 < HERO - BAR and t0 >= DROP + 2 * BAR      # thinner bed under the review dialogue
    # real piano: jazzy off-beat stabs (intro: soft sustained voicings)
    if intro:
        for j, m in enumerate(voic):
            put("piano", note("piano", m, BAR * 0.95, 0.38, 0.5), t0 + j * 0.012, -0.3 + 0.15 * j)
    else:
        for off in (0.5, 1.75, 2.5, 3.5):
            for j, m in enumerate(voic):
                put("piano", note("piano", m, BEAT * 0.7, 0.42 if under_voice else 0.55, 0.15), t0 + off * BEAT + j * 0.008, -0.3 + 0.15 * j)
    # shaker 16ths, swung
    for s in range(16):
        put("perc", SHAKE * (0.55 if s % 2 else 0.3), t0 + s * BEAT / 4 + (0.014 if s % 2 else 0), 0.3 if s % 4 else -0.2)
    if not intro:
        for k in range(4):
            put("drums", KICK * (0.75 if under_voice else 0.95), t0 + k * BEAT)
        for k in (1, 3):
            put("drums", SNARE * (0.35 if under_voice else 0.5), t0 + k * BEAT, 0.1)
        for off, semi in LOG:
            put("bass", logdrum(root + semi - 12 + 12, 0.42 if semi == 0 else 0.3, 0.8 if under_voice else 1.0), t0 + off * BEAT)
        put("bass", note("bass-electric", root, BAR * 0.9, 0.5, 0.2), t0)
        if not under_voice:
            for k, off in enumerate((0.25, 1.25, 2.75)):
                put("perc", BONGO_H * 0.35 if k % 2 else BONGO_L * 0.4, t0 + off * BEAT, 0.4 - 0.3 * k)
        # nylon guitar pluck motif every other bar
        if b % 2 == 1:
            for k, (off, m) in enumerate(((0, 75), (0.5, 72), (1.0, 70), (1.5, 72), (2.5, 68))):
                put("gtr", note("guitar-nylon", m, BEAT * 0.6, 0.45, 0.2), t0 + off * BEAT, 0.35)
    # cello swell bed (sections around the hero and end)
    if not intro and (t0 >= HERO - BAR or b % 4 == 0):
        put("strings", note("cello", root + 12, BAR * 1.0, 0.35, 0.6), t0, -0.2)
    if end:
        for k, (off, m) in enumerate(((0, 80), (1, 79), (2, 75), (3, 77))):
            put("strings", note("violin", m, BEAT * 1.0, 0.28, 0.4), t0 + off * BEAT, 0.25)


def harp_gliss(t, up=True, n=14, span=1.2, vel=0.45):
    scale = [56, 58, 60, 63, 65, 68, 70, 72, 75, 77, 80, 82, 84, 87]
    seq = scale if up else scale[::-1]
    for k, m in enumerate(seq[:n]):
        put("harp", note("harp", m, 1.2, vel, 0.6), t + k * span / n, -0.4 + 0.8 * k / n)


def riser(dur, vel=0.3):
    tt = np.arange(int(dur * SR)) / SR
    x = filt(rng.standard_normal(len(tt)), 1500, "high") * (tt / dur) ** 3 * vel
    return x.astype(np.float32)


harp_gliss(0.2, True, 10, 1.0, 0.35)                 # opening sparkle
harp_gliss(DROP - 1.1, True, 14, 1.0, 0.45)
put("fx", riser(1.6), DROP - 1.6)
put("fx", boom(1.6, 0.8), DROP)
harp_gliss(HERO - 1.0, True, 14, 0.9, 0.45)
put("fx", riser(1.4, 0.25), HERO - 1.4)
put("fx", boom(1.4, 0.6), HERO)
for j, m in enumerate([56, 60, 63, 68, 72]):        # string swell into the hero
    put("strings", note("violin" if m > 62 else "cello", m, 2.5, 0.3, 0.8), HERO - 0.2, -0.3 + 0.15 * j)
harp_gliss(END + 0.4, True, 14, 1.1, 0.5)
put("fx", boom(1.8, 0.7, 44), END + 0.3)
for j, m in enumerate([44, 56, 60, 63, 68, 72]):
    put("piano", note("piano", m, 3.5, 0.5, 1.0), END + 0.3 + j * 0.02, -0.3 + 0.12 * j)

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



buses["strings"] = filt(buses["strings"], 170, "high")
buses["piano"] = biquad(filt(buses["piano"], 110, "high"), "peak", 300, -4.0, 0.9)
buses["gtr"] = filt(buses["gtr"], 160, "high")
buses["harp"] = filt(buses["harp"], 140, "high")
hall = sum(buses[k] * g for k, g in (("piano", 0.55), ("strings", 0.8), ("harp", 0.9), ("gtr", 0.35), ("fx", 0.4), ("perc", 0.15)))
mix = (buses["piano"] * 0.85 + buses["strings"] * 0.8 + buses["gtr"] * 0.75 + buses["bass"] * 0.75 + buses["harp"] * 0.8
       + buses["drums"] * 0.9 + buses["perc"] * 0.9 + buses["fx"] * 0.7 + filt(reverb(hall, 2.8), 200, "high") * 0.38)
i_drop = int(DROP * SR)
mix[:i_drop] = filt(mix[:i_drop], 2400, "low") * 0.85 + filt(mix[:i_drop], 2400, "high") * 0.5     # softer intro under the street dialogue
mix = filt(mix, 35, "high")
mix = biquad(mix, "peak", 280, -4.5, 0.7)
mix = biquad(mix, "peak", 2600, -4.5, 0.8)
mix = biquad(mix, "high", 8000, 2.5, 0.7)
env = filt(np.abs(mix).mean(1), 6, "low")
g = np.where(env > 0.22, (0.22 / np.maximum(env, 1e-6)) ** 0.4, 1.0)
mix *= g[:, None]
ft = int((TOTAL - 2.5) * SR)
mix[ft:] *= np.linspace(1, 0, N - ft)[:, None] ** 1.3
mix *= 0.89 / np.abs(mix).max()
sf.write(sys.argv[5], mix, SR, subtype="PCM_24")
print("ok", BARS)
