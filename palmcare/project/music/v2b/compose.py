"""Original premium Afro-soul score for PalmCare Video 2 (80 BPM, Db major, 22 bars = 66 s).
Laid-back half-time groove: soft kick, gentle rim, swung shaker and congas (Afro feel), warm Rhodes, deep finger bass,
a nylon-guitar highlife arpeggio and a kalimba motif. Sections follow the edit:
intro (bars 1-4, cold open) -> groove (5-9, citrus) -> lift (10-15, molecular) -> glow (16-17) -> end card (18-22)."""
import random

import mido

BPM, TPB = 80, 480
STEP = TPB // 4
SWING = int(STEP * 0.18)
BARS = 20
random.seed(21)
CHORDS = [(49, [65, 68, 72, 75]),     # Dbmaj9 (F Ab C Eb)
          (46, [61, 65, 68, 72]),     # Bbm9  (Db F Ab C)
          (42, [58, 61, 65, 68]),     # Gbmaj9 (Bb Db F Ab)
          (44, [60, 63, 66, 70])]     # Ab13sus (C Eb Gb Bb)


def tick(bar, step):
    return bar * 16 * STEP + int(step * STEP) + (SWING if int(step) % 2 else 0)


class Track:
    def __init__(self, program, ch=0, rev=60, cho=20):
        self.ev, self.ch, self.program, self.rev, self.cho = [], ch, program, rev, cho

    def note(self, bar, step, n, vel, ln, jit=6):
        t = max(0, tick(bar, step) + random.randint(-jit, jit))
        v = max(1, min(127, vel + random.randint(-5, 5)))
        self.ev += [(t, 1, n, v), (t + max(10, int(ln * STEP) - 10), 0, n, 0)]

    def save(self, path):
        mid = mido.MidiFile(ticks_per_beat=TPB)
        tr = mido.MidiTrack()
        mid.tracks.append(tr)
        tr.append(mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(BPM), time=0))
        if self.ch != 9:
            tr.append(mido.Message("program_change", program=self.program, channel=self.ch, time=0))
        tr.append(mido.Message("control_change", control=91, value=self.rev, channel=self.ch, time=0))
        tr.append(mido.Message("control_change", control=93, value=self.cho, channel=self.ch, time=0))
        last = 0
        for t, k, a, b in sorted(self.ev, key=lambda e: (e[0], e[1])):
            tr.append(mido.Message("note_on" if k else "note_off", note=a, velocity=b, channel=self.ch, time=t - last))
            last = t
        tr.append(mido.MetaMessage("end_of_track", time=TPB * 8))
        mid.save(path)


def sec(bar):
    return "intro" if bar < 2 else "groove" if bar < 8 else "lift" if bar < 13 else "glow" if bar < 15 else "end"


drums, perc = Track(0, 9, 45, 0), Track(0, 9, 55, 0)
rhodes, bass, gtr, kal, pad = Track(4, 0, 70, 40), Track(33, 1, 30, 0), Track(24, 2, 65, 25), Track(108, 3, 85, 20), Track(89, 4, 90, 40)
KICK, RIM, SNAP, SHAKER, HAT, CONGA_M, CONGA_O, CONGA_L, CABASA, CHIMES = 36, 37, 39, 82, 42, 62, 63, 64, 69, 84

for bar in range(BARS):
    s = sec(bar)
    root, ch = CHORDS[bar % 4]
    last = bar == BARS - 1
    # ---- percussion: always gentle
    if not last:
        for st in range(16):
            if s == "intro" and bar < 1:
                break
            drums.note(bar, st, SHAKER, 46 if st % 2 else 58, 0.5, 4)
    if s in ("groove", "lift", "glow", "end") and not last:
        for st in (0, 7, 10):                      # half-time kick with an Afro push
            drums.note(bar, st, KICK, 82 if st == 0 else 66, 1)
        drums.note(bar, 8, RIM, 64, 0.5)
        drums.note(bar, 8, SNAP, 50, 0.5)
        for st, n, v in ((3, CONGA_M, 50), (6, CONGA_O, 62), (11, CONGA_M, 48), (14, CONGA_O, 60), (15, CONGA_L, 54)):
            perc.note(bar, st, n, v, 1)
        if s in ("lift", "glow"):
            for st in (2, 6, 10, 14):
                perc.note(bar, st, CABASA, 40, 0.5)
    if bar in (2, 8, 13, 15):
        perc.note(bar, 0, CHIMES, 58, 8)
    # ---- Rhodes: sustained chords in the intro, soft off-beat comping after
    if s == "intro" or s == "end":
        for n in ch:
            rhodes.note(bar, 0, n, 58 if s == "intro" else 62, 15.5, 3)
    else:
        for st, ln in ((0, 3), (6, 1.5), (10, 3)):
            for n in ch:
                rhodes.note(bar, st, n, 60 if st else 66, ln, 3)
    # ---- bass: deep, round, sparse
    if s != "intro" or bar >= 1:
        if s == "intro" or last:
            bass.note(bar, 0, root - 12 if root > 40 else root, 72, 15)
        else:
            for st, n, ln in ((0, root, 5), (7, root + 7, 1.5), (10, root + 12, 1), (12, root, 3)):
                bass.note(bar, st, n - 12 if n > 52 else n, 84 if st == 0 else 72, ln)
    # ---- nylon guitar highlife arpeggio (lift + glow)
    if s in ("lift", "glow"):
        arp = sorted(ch)[1:] + [sorted(ch)[0] + 12]
        for k, st in enumerate((0, 2, 3, 5, 8, 10, 11, 13)):
            gtr.note(bar, st, arp[k % 4] + 12, 56, 1.2, 3)
    # ---- kalimba motif: the hook (intro, every other bar of groove, end)
    if s in ("intro", "end") or (s in ("groove", "lift") and bar % 2 == 1):
        mot = [(0, 80), (3, 77), (6, 80), (8, 82), (11, 84), (14, 80)] if bar % 2 == 0 else [(0, 77), (4, 80), (8, 75), (12, 77)]
        for st, n in mot:
            if not (last and st > 0):
                kal.note(bar, st, n, 64, 3, 3)
    # ---- warm pad underneath everything
    for n in ch[:3]:
        pad.note(bar, 0, n - 12, 40 if s != "glow" else 50, 16, 0)

for name, tr in (("drums", drums), ("perc", perc), ("rhodes", rhodes), ("bass", bass), ("guitar", gtr), ("kalimba", kal), ("pad", pad)):
    tr.save(f"{name}.mid")
print("seconds", BARS * 4 * 60 / BPM)
