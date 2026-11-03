"""Energy layer for the V2 score (same 80 BPM grid, bar = 3 s): amapiano-style drive (16th hats, open-hat
offbeats, backbeat claps, soft four-on-floor kick), a log-drum bass, and snare-roll builds into each reveal
(6 s, 24 s, 45 s), with a one-beat break right before each hit."""
import random
import mido
from compose import Track, CHORDS, BARS
random.seed(17)
KICK, CLAP, SNARE, HH, OH, RIDE = 36, 39, 38, 42, 46, 51
drive, logd = Track(0, 9, 30, 0), Track(38, 5, 25, 0)
BUILD = {1, 7, 14}            # bars that roll into a reveal (bar 2 = 6 s, bar 8 = 24 s, bar 15 = 45 s)
for bar in range(BARS - 1):
    root = CHORDS[bar % 4][0]
    full = bar >= 2
    brk = bar in BUILD
    for st in range(16):
        if brk and st >= 12:
            break                                         # one-beat break before the hit
        if bar >= 1 or st >= 8:
            drive.note(bar, st, HH, (70 if st % 4 == 2 else 52) + (6 if st % 2 == 0 else 0), 0.5, 3)
        if full and st in (2, 6, 10, 14):
            drive.note(bar, st, OH, 58, 1, 3)
        if full and st in (0, 4, 8, 12) and not (brk and st >= 12):
            drive.note(bar, st, KICK, 88 if st == 0 else 76, 1)
        if full and st in (4, 12):
            drive.note(bar, st, CLAP, 84, 1)
    if brk:                                               # snare roll build across beats 2-3, then silence
        for k, st in enumerate(range(4, 12)):
            for sub in (0, 0.5):
                drive.note(bar, st + sub, SNARE, 40 + k * 7, 0.4, 2)
    if full:                                              # log drum: syncopated, slides an octave
        for st, n, v in ((0, root, 96), (3, root, 80), (6, root + 12, 84), (10, root, 90), (11, root + 7, 74), (14, root + 12, 82)):
            if brk and st >= 12:
                continue
            logd.note(bar, st, n - 12 if n > 47 else n, v, 1.6, 2)
drive.save("drive.mid"); logd.save("logdrum.mid")
print("ok")
