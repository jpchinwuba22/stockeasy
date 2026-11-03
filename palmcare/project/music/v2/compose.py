"""Original Afrobeats instrumental for PalmCare Video 2 (104 BPM, C major, 26 bars = 60 s).
Writes one MIDI file per stem (rendered separately with the GeneralUser GS sound bank, then mixed in mix.py).
Arrangement follows the edit: intro (bars 1-4) -> drop + groove A (5-12, Citrus) -> drop + groove B (13-19, Molecular)
-> lift (20-22, rooftop) -> end-card unveil (23-26) with a final hit."""
import random

import mido

BPM = 104
TPB = 480                      # ticks per beat
STEP = TPB // 4                # one 16th
SWING = int(STEP * 0.14)       # Afrobeats bounce: late off-16ths
BARS = 26
random.seed(7)

CHORDS = [  # (bass root, chord voicing) per bar, 4-bar loop
    (41, [57, 60, 64, 67]),    # Fmaj9
    (40, [55, 59, 62, 67]),    # Em7(add11 colour)
    (38, [53, 57, 60, 64]),    # Dm9
    (43, [53, 57, 62, 64]),    # G13sus4
]


def tick(bar, step):
    return bar * 16 * STEP + step * STEP + (SWING if step % 2 else 0)


class Track:
    def __init__(self, program, channel=0):
        self.ev, self.ch = [], channel
        self.program = program

    def note(self, bar, step, note, vel, length_steps, jitter=8):
        t = max(0, tick(bar, step) + random.randint(-jitter, jitter))
        v = max(1, min(127, vel + random.randint(-6, 6)))
        self.ev.append((t, 1, note, v))
        self.ev.append((t + max(10, int(length_steps * STEP) - 12), 0, note, 0))

    def cc(self, bar, step, ctrl, val):
        self.ev.append((tick(bar, step), 2, ctrl, val))

    def save(self, path):
        mid = mido.MidiFile(ticks_per_beat=TPB)
        tr = mido.MidiTrack()
        mid.tracks.append(tr)
        tr.append(mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(BPM), time=0))
        if self.ch != 9:
            tr.append(mido.Message("program_change", program=self.program, channel=self.ch, time=0))
        tr.append(mido.Message("control_change", control=91, value=40, channel=self.ch, time=0))   # reverb send
        tr.append(mido.Message("control_change", control=93, value=10, channel=self.ch, time=0))   # chorus send
        last = 0
        for t, kind, a, b in sorted(self.ev, key=lambda e: (e[0], e[1])):
            dt = t - last
            last = t
            if kind == 2:
                tr.append(mido.Message("control_change", control=a, value=b, channel=self.ch, time=dt))
            else:
                tr.append(mido.Message("note_on" if kind else "note_off", note=a, velocity=b, channel=self.ch, time=dt))
        tr.append(mido.MetaMessage("end_of_track", time=TPB * 8))
        mid.save(path)


def section(bar):
    if bar < 4:
        return "intro"
    if bar < 12:
        return "A"
    if bar < 19:
        return "B"
    if bar < 22:
        return "lift"
    return "end"


drums, perc, bass = Track(0, 9), Track(0, 9), Track(33)
keys, gtr, mar, pad = Track(4), Track(27), Track(12), Track(89)

KICK, RIM, CLAP, HAT, OHAT, SHAKER = 36, 37, 39, 42, 46, 82
CONGA_MUTE, CONGA_OPEN, CONGA_LOW, AGOGO_HI, AGOGO_LO, TAMB = 62, 63, 64, 67, 68, 54
LOWTOM, MIDTOM, HITOM, CRASH = 45, 47, 50, 49

for bar in range(BARS):
    sec = section(bar)
    root, chord = CHORDS[bar % 4]
    pre_drop = bar in (3, 11, 21)          # the bar before each unveil
    # ---------------- drums ----------------
    full = sec in ("A", "B", "lift", "end")
    for s in range(16):
        acc = s % 4 == 2
        if sec != "end" or bar < 25:
            drums.note(bar, s, SHAKER, 78 if acc else (52 if s % 2 else 62), 0.5, 5)
    if sec == "intro":
        for s in (2, 6, 10, 14):
            drums.note(bar, s, HAT, 40, 0.5)
        if bar >= 2:
            perc.note(bar, 6, CONGA_OPEN, 62, 1)
            perc.note(bar, 14, CONGA_OPEN, 58, 1)
            perc.note(bar, 11, CONGA_MUTE, 50, 1)
    if full:
        kicks = [0, 6, 12] if bar % 2 == 0 else [0, 6, 10, 14]
        if sec == "end" and bar >= 24:
            kicks = [0, 6, 12] if bar == 24 else [0]
        for s in kicks:
            if pre_drop and s >= 12:
                continue
            drums.note(bar, s, KICK, 112 if s == 0 else 96, 1)
        for s in (4, 12):
            if not (pre_drop and s == 12) and not (bar == 25 and s == 12):
                drums.note(bar, s, CLAP, 96, 1)
        for s in (3, 7, 10, 15):
            if not (pre_drop and s >= 12) and bar < 25:
                drums.note(bar, s, RIM, 70 if s != 10 else 82, 0.5)
        for s in (2, 6, 10, 14):
            drums.note(bar, s, HAT, 58, 0.5)
        if bar % 4 == 3 and not pre_drop:
            drums.note(bar, 14, OHAT, 62, 2)
        # congas: tumbao-like, busier in B / lift
        pat = [(3, CONGA_MUTE, 66), (6, CONGA_OPEN, 82), (8, CONGA_LOW, 74), (11, CONGA_MUTE, 62), (14, CONGA_OPEN, 84)]
        if sec in ("B", "lift"):
            pat += [(13, CONGA_MUTE, 58), (15, CONGA_LOW, 70)]
        for s, n, v in pat:
            if not (pre_drop and s >= 12):
                perc.note(bar, s, n, v, 1)
        if sec in ("B", "lift"):
            for s in (0, 3, 6, 10, 12):                      # agogo bell pattern
                perc.note(bar, s, AGOGO_HI if s in (0, 6, 12) else AGOGO_LO, 54, 1)
        if sec == "lift":
            for s in (2, 6, 10, 14):
                perc.note(bar, s, TAMB, 48, 0.5)
    if bar in (4, 12, 22):                                    # crash on each unveil
        drums.note(bar, 0, CRASH, 100, 8)
    if pre_drop:                                              # tom fill into the drop, then a breath
        for s, n in ((8, HITOM), (9, HITOM), (10, MIDTOM), (11, MIDTOM), (12, LOWTOM), (13, LOWTOM)):
            perc.note(bar, s, n, 70 + (s - 8) * 6, 1)
    # ---------------- bass ----------------
    if full:
        line = [(0, root, 3), (3, root, 1), (6, root + 12, 1), (8, root, 2), (11, root + 7, 1), (14, root + 10, 1)]
        if bar == 25:
            line = [(0, 36, 12)]
        for s, n, l in line:
            if pre_drop and s >= 12:
                continue
            bass.note(bar, s, n, 104 if s == 0 else 90, l)
    elif bar >= 2:
        bass.note(bar, 0, root, 70, 8)
    # ---------------- keys (offbeat skank / intro pads) ----------------
    if sec == "intro":
        for n in chord:
            keys.note(bar, 0, n, 58, 15, 4)
    elif bar == 25:
        for n in [48] + chord + [72]:
            keys.note(bar, 0, n, 84, 16, 2)
    else:
        for s in (2, 6, 10, 14):
            if pre_drop and s >= 12:
                continue
            for n in chord:
                keys.note(bar, s, n, 70 if s != 10 else 78, 1.2, 3)
    # ---------------- highlife guitar (from groove A) ----------------
    if sec in ("A", "B", "lift") and not (pre_drop and False):
        hi = sorted(chord)[1:] + [sorted(chord)[1] + 12]
        cyc = [hi[3], hi[1], hi[2], hi[0]]
        for k, s in enumerate((0, 2, 3, 5, 6, 8, 10, 11, 13, 14)):
            if pre_drop and s >= 12:
                continue
            gtr.note(bar, s, cyc[k % 4] + 12, 64 if s % 4 else 74, 0.7, 4)
    # ---------------- marimba hook (groove B + lift + end) ----------------
    if sec in ("B", "lift") or (sec == "end" and bar < 25):
        motif = [(0, 76), (2, 79), (4, 81), (6, 79), (7, 76), (10, 74), (12, 76), (14, 72)] if bar % 2 == 0 else \
                [(0, 74), (3, 76), (6, 79), (8, 81), (10, 84), (12, 81), (14, 79)]
        for s, n in motif:
            if pre_drop and s >= 12:
                continue
            mar.note(bar, s, n, 76, 1.5, 4)
    # ---------------- pad ----------------
    if sec in ("intro", "B", "lift", "end"):
        for n in chord[:3]:
            pad.note(bar, 0, n - 12 if n > 60 else n, 46, 16, 0)

for name, tr in (("drums", drums), ("perc", perc), ("bass", bass), ("keys", keys), ("guitar", gtr),
                 ("marimba", mar), ("pad", pad)):
    tr.save(f"{name}.mid")
print("bars", BARS, "seconds", BARS * 4 * 60 / BPM)
