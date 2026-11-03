"""Video 2 (redo): PalmCare Citrus Vitamin Glow Infusion Body Wash + PalmCare Molecular Glow Body Lotion.
Slow premium cut at 80 BPM (beat = 0.75 s): cold open on liquid gold and sunlight -> the body wash revealed in
falling citrus -> pick-up, pump, loofah, shower -> the lotion revealed in prism light -> pump, swirl, application ->
rooftop result -> bright studio end card. Only static / locked product shots (no hand-held bottles, so no label can
move). Soft dissolves only. Graphics: overlay2b.py, end card: endcard2b.py."""
import json

V = "2b"
BPM = 80
BEAT = 60 / BPM
VO = "../v2x/edit/vo2b.wav"
EC_FILE = "../v2x/fix/EC2b.mp4"
VO_WORDS = "../v2x/edit/vo2b_words.json"
MUSIC = "../music/v2b/music_e.wav"
XF = 0.0                     # hard cuts on the beat (energy pass)

S0 = (1.0, 1.0, 0, 0, "s")
# (clip, src start, beats, move (z0, z1, dx, dy, ease), flags)
SHOTS_B = [("y3", 3.6, 5, (1.45, 1.36, -120, 40, "s"), {"sp:0.7"}),              # cold open: liquid gold macro (bottle cropped out)
           ("y6", 5.0, 3, (1.00, 1.04, 0, 0, "s"), set()),                      # her face turning to the sun
           ("y2", 0.4, 6, S0, {"sp:0.88"}),                                      # REVEAL 1: citrus falls into the pool (ends before the in-clip cut)
           ("y2r", 6.55, 3, S0, set()),                                          # rack focus orange -> bottle
           ("y1bp", 0.0, 3, S0, set()),                                          # she reaches for it (locked, bottle static)
           ("y3", 0.63, 3, S0, {"cut"}),                                         # pump (locked) ...
           ("y3", 3.0, 3, S0, set()),                                            # macro: thick gel stacking on the loofah
           ("y3", 6.95, 6, (1.20, 1.27, 70, -120, "s"), {"sp:0.64", "cut"}),     # outdoor shower (strap cropped out)
           ("y4", 0.2, 6, S0, {"cut"}),                                          # REVEAL 2: lotion in prism light (locked)
           ("y5", 0.1, 3, S0, set()),                                            # lotion pump (locked)
           ("y4", 5.0, 5, (1.00, 1.05, 0, 0, "s"), set()),                      # silky swirl
           ("y5", 3.0, 4, (1.02, 1.06, 0, -10, "s"), set()),                    # smooths it on
           ("y5", 7.0, 3, (1.00, 1.04, 0, 0, "s"), set()),                      # glowing shoulder
           ("y6", 0.2, 5, (1.00, 1.05, 0, 0, "s"), set()),                      # rooftop walk
           ("y6", 7.8, 2, (1.00, 1.03, 0, -6, "s"), set()),                     # sun close-up smile
           ("EC", 0.0, 16, None, set())]                                         # end card (built, endcard2b.py)


def _frames(k):
    return round(k * BEAT * 24)


SHOTS, _b, STARTS = [], 0, []
for clip, st, nb, mv, fl in SHOTS_B:
    n = _frames(_b + nb) - _frames(_b)
    STARTS.append(_frames(_b) / 24)
    SHOTS.append((clip, st, n / 24, mv, fl))
    _b += nb
TOTAL = _frames(_b) / 24
CUTS = STARTS[1:]
EC_START = STARTS[-1]
CAPTION_UNTIL = EC_START - 0.05
REVEALS = [STARTS[2], STARTS[8]]

# narration: (line, phrase, start of first word)
VO_PLACE = [(0, 0, 0.90), (0, 1, 4.00),
            (1, 0, 6.90),
            (2, 0, 10.75), (2, 1, 15.25), (2, 2, 17.50), (2, 3, 19.70), (2, 4, 20.90),
            (3, 0, 24.30), (3, 1, 25.75),
            (4, 0, 28.80), (4, 1, 31.00), (4, 2, 32.80), (4, 3, 34.75), (4, 4, 37.60),
            (5, 0, 54 * BEAT), (5, 1, 56 * BEAT), (5, 2, 43.60),
            (6, 0, 46.50)]

TITLES = [("Citrus Vitamin", "Glow Infusion", "PALMCARE  ·  BODY WASH", STARTS[2] + 1.6, STARTS[3] - 0.1),
          ("Molecular", "Glow", "PALMCARE  ·  BODY LOTION", STARTS[8] + 1.2, STARTS[9] - 0.1)]
PILLS = [("spark", "Intense brightening complex", 10.8, STARTS[4] - 0.15, 1380),
         ("drop", "Rich, cleansing gel", 15.3, STARTS[6] - 0.05, 1380),
         ("spark", "Brighter, fresher-looking skin", 17.55, STARTS[8] - 0.6, 1380),
         ("spark", "Brightening complex", 34.8, STARTS[12] - 0.1, 1380),
         ("leaf", "Even brighter skin", 37.65, STARTS[13] - 0.15, 1380)]
MOLECULE = ([("ALPHA ARBUTIN", 28.85, (250, 470)), ("TRANEXAMIC ACID", 31.05, (800, 400)),
             ("VITAMIN C  (SAP)", 32.85, (560, 720))], STARTS[11] - 0.05)
WORDS = [("Bright.", 54 * BEAT, 56 * BEAT - 0.05), ("Even.", 56 * BEAT, STARTS[14] - 0.05),
         ("Beautifully you.", 43.6, STARTS[15] - 0.1)]


def shot_times():
    return [(a, a + s[2]) for a, s in zip(STARTS, SHOTS)]


def caption_chunks():
    ws = [w for w in json.load(open(VO_WORDS))["words"] if w["start"] < CAPTION_UNTIL]
    groups = {}
    for w in ws:
        groups.setdefault(w["phrase"], []).append((w["text"].replace("...", "…"), w["start"], w["end"]))
    ch = []
    for g in groups.values():
        k = -(-len(g) // 4)
        n = -(-len(g) // k)
        ch += [g[i:i + n] for i in range(0, len(g), n)]
    return ch


if __name__ == "__main__":
    print("TOTAL", TOTAL)
    for (c, st, d, *_), a in zip(SHOTS, STARTS):
        print(f"{a:6.2f}-{a + d:6.2f}  {c:5s} src {st}")
