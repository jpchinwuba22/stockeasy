"""Video 2 (v3, rebuilt from scratch): PalmCare Citrus Vitamin Glow Infusion Body Wash + Molecular Glow Body Lotion.
Beat-cut to the 80 BPM energy score (beat 0.75 s, impacts at 6 / 24 / 45 s). No AI-generated bottle anywhere: the
two reveals (PC, PM) and the end card are built from the straight product photos; Flow clips are model + texture only."""
import json

V = "3"
BPM = 80
BEAT = 60 / BPM
VO = "vo3.wav"
VO_WORDS = "vo3_words.json"
MUSIC = "../../music/v2b/music_e.wav"
EC_FILE = "../EC3.mp4"
XF = 0.0                      # hard cuts on the beat

S0 = (1.0, 1.0, 0, 0, "s")
PUSH = (1.00, 1.05, 0, 0, "s")
# (clip, src start, beats, move, flags)
SHOTS_B = [("N1", 0.5, 4, PUSH, set()),                  # hook: liquid gold pour
           ("N2", 4.5, 4, (1.02, 1.07, 0, 0, "s"), set()),  # her eyes open to the sun, smile
           ("PC", 0.0, 6, S0, {"nograde"}),                # REVEAL 1: body wash (built from the product photo)
           ("N3", 0.3, 3, S0, set()),                    # citrus slices crash into water
           ("N1", 4.6, 3, PUSH, set()),                  # gel + orange slice
           ("N4", 0.0, 4, (1.00, 1.04, 0, 0, "s"), set()),  # shower: fresh, smiling
           ("N3", 7.5, 3, S0, set()),                    # slice splash
           ("N4", 6.2, 5, (1.00, 1.04, 0, 0, "s"), set()),  # head back into the water
           ("PM", 0.0, 6, S0, {"nograde"}),                # REVEAL 2: body lotion (built from the product photo)
           ("N5", 1.5, 5, PUSH, set()),                  # lotion pours into a swirl (ingredients)
           ("N5", 6.0, 4, (1.04, 1.09, 0, 0, "s"), set()),  # rainbow light across the swirl
           ("N6", 0.5, 4, S0, set()),                    # smoothing it on
           ("N6", 6.6, 2, S0, set()),                    # her glowing face
           ("N7", 1.0, 3, S0, set()),                    # rooftop walk
           ("N7", 6.25, 4, S0, set()),                   # turn, look back, smile
           ("EC", 0.0, 16, None, set())]                 # end card (built from the product photos)


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
PRODUCT_SPANS = [(STARTS[2], STARTS[3]), (STARTS[8], STARTS[9])]   # no captions over the product hero shots

# narration: (line, phrase, start)
VO_PLACE = [(0, 0, 0.60), (0, 1, 2.40),
            (1, 0, 6.60),
            (2, 0, 10.60), (2, 1, 13.00), (2, 2, 15.30), (2, 3, 17.10), (2, 4, 18.20),
            (3, 0, 24.40), (3, 1, 25.90),
            (4, 0, 28.70), (4, 1, 30.75), (4, 2, 32.10), (4, 3, 33.65), (4, 4, 35.50), (4, 5, 37.00),
            (5, 0, 40.00), (5, 1, 41.20), (5, 2, 43.00),
            (6, 0, 46.50)]

TITLES = [("Citrus Vitamin", "Glow Infusion", "PALMCARE  ·  BODY WASH", STARTS[2] + 0.7, STARTS[3] - 0.1),
          ("Molecular", "Glow", "PALMCARE  ·  BODY LOTION", STARTS[8] + 0.7, STARTS[9] - 0.1)]
PILLS = [("spark", "Liquid sunshine", 0.62, 2.35, 1360),
         ("spark", "Intense brightening complex", 11.36, STARTS[4] - 0.05, 1360),
         ("drop", "Rich cleansing gel", 13.33, STARTS[5] - 0.05, 1360),
         ("leaf", "Fresher", 16.23, 17.05, 1520),
         ("leaf", "Clearer", 17.1, STARTS[6] - 0.05, 1520),
         ("spark", "Visibly renewed", 18.47, 20.15, 1360),
         ("leaf", "Healthy ingredients", 29.36, 30.65, 1360),
         ("spark", "Brightens your skin", 35.75, 36.95, 1360),
         ("drop", "Luminous, lasting finish", 37.45, STARTS[13] - 0.1, 1360)]
MOLECULE = ([("ALPHA ARBUTIN", 30.8, (250, 470)), ("TRANEXAMIC ACID", 32.15, (800, 400)),
             ("VITAMIN C", 33.7, (560, 720))], STARTS[11] - 0.05)
WORDS = [("Bright.", 40.0, 41.15), ("Radiant.", 41.2, 42.95), ("Beautifully you.", 43.0, EC_START - 0.1)]


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
        print(f"{a:6.2f}-{a + d:6.2f}  {c:3s} src {st:5.2f}-{st + d:5.2f}")
