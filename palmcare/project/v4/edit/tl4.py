"""Video 3 — "Lagos sun, meet your match": PalmCare Advanced Tropical Glow Exfoliating Lightening Body Wash +
PalmCare Dermalight Body Lotion. Beat-cut to the 80 BPM score (impacts at 6 / 24 / 45 s). No AI-generated bottle:
the two reveals (PT, PD) and the end card are built from the straight product photos."""
import json

V = "4"
BPM = 80
BEAT = 60 / BPM
VO = "vo4.wav"
VO_WORDS = "vo4_words.json"
MUSIC = "../../music/v4/music_v4.wav"
EC_FILE = "../EC4.mp4"
XF = 0.0

S0 = (1.0, 1.0, 0, 0, "s")
PUSH = (1.00, 1.05, 0, 0, "s")
SHOTS_B = [("K1", 3.5, 4, PUSH, set()),                       # Lagos sun: bridge, tilt into the blazing flare
           ("K2", 3.4, 4, (1.02, 1.08, 0, 0, "s"), set()),    # her eyes open in the palm shadows: "meet your match"
           ("PT", 0.0, 6, S0, {"nograde"}),                    # REVEAL 1: body wash out of the gold vortex
           ("K3", 1.0, 4, PUSH, set()),                        # gold-leaf vortex (exfoliating formula)
           ("K4", 1.5, 4, S0, set()),                          # golden scrub on her shoulder
           ("K4", 4.6, 3, S0, set()),                          # water rinses it to a polished glow
           ("K4", 8.45, 2, S0, set()),                         # face in the water
           ("K2", 6.0, 5, (1.00, 1.05, 0, 0, "s"), set()),    # confident smile in the shadows (build)
           ("PD", 0.0, 6, S0, {"nograde"}),                    # REVEAL 2: lotion in glass and light
           ("K5", 0.6, 5, PUSH, set()),                        # lotion pour, rainbow refraction (ingredients)
           ("K6", 1.6, 4, S0, set()),                          # smoothing it on: fades dark spots
           ("K6", 6.0, 3, S0, set()),                          # glass skin, soft smile
           ("K7", 0.4, 5, S0, {"shield"}),                     # walks into the midday sun: UV shield
           ("K8", 2.5, 2, S0, {"shield"}),                     # face up to the sun
           ("K8", 6.8, 3, S0, set()),                          # powerful smile: Lighter. Even. Protected.
           ("EC", 0.0, 16, None, set())]


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
PRODUCT_SPANS = [(STARTS[2], STARTS[3]), (STARTS[8], STARTS[9])]
SHIELD = (38.9, STARTS[14])          # UV shield dome over her (appears as "UV defence" is spoken)

VO_PLACE = [(0, 0, 0.60), (0, 1, 3.40),
            (1, 0, 6.60),
            (2, 0, 11.20), (2, 1, 14.40), (2, 2, 16.90),
            (3, 0, 24.30), (3, 1, 25.95),
            (4, 0, 28.60), (4, 1, 30.70), (4, 2, 31.95), (4, 3, 33.45), (4, 4, 35.35), (4, 5, 36.80),
            (5, 0, 38.90), (5, 1, 41.55),
            (6, 0, 43.10), (6, 1, 43.85), (6, 2, 44.55),
            (7, 0, 46.50)]

TITLES = [("Advanced", "Tropical Glow", "PALMCARE  ·  LIGHTENING BODY WASH", STARTS[2] + 0.7, STARTS[3] - 0.1),
          ("Dermalight", "Body Lotion", "PALMCARE  ·  GLASS SKIN TONE-UP", STARTS[8] + 0.7, STARTS[9] - 0.1)]
PILLS = []                              # filled from the word timings below (pop-ups on key words)
POPS = [("Exfoliating", "Exfoliates", 1360), ("dullness,", "Buffs away dullness", 1360),
        ("lightening", "Intense lightening complex", 1360), ("smoother,", "Smoother, radiant skin", 1360),
        ("healthy", "Healthy ingredients", 1360), ("fade", "Fades dark spots", 1360),
        ("even,", "Even, glass-like tone", 1360), ("UV", "UV defence shield", 1360)]
MOLECULE = ([("ALPHA ARBUTIN", 30.7, (250, 470)), ("TRANEXAMIC ACID", 31.95, (800, 400)),
             ("VITAMINS B3 + E", 33.45, (560, 720))], STARTS[11] - 0.05)
WORDS = [("Lagos sun,", 0.6, 3.0), ("Meet your match.", 3.4, STARTS[2] - 0.05),
         ("Lighter.", 43.1, 43.8), ("Even.", 43.85, 44.5), ("Protected.", 44.55, EC_START - 0.02)]


def _pops():
    try:
        ws = json.load(open(VO_WORDS))["words"]
    except Exception:
        return []
    out, used = [], set()
    for key, text, cy in POPS:
        w = next((w for w in ws if w["text"].strip(".,…").lower() == key.strip(".,").lower() and w["start"] not in used
                  and not any(a <= w["start"] < b for a, b in PRODUCT_SPANS)), None)
        if w:
            used.add(w["start"])
            out.append(["spark", text, w["start"], 0.0, cy])
    for k in range(len(out)):                    # each pop stays until just before the next one (max 2.4 s), never past a reveal
        nxt = out[k + 1][2] - 0.08 if k + 1 < len(out) else out[k][2] + 2.0
        stop = min(nxt, out[k][2] + 2.4)
        for c in CUTS:
            if out[k][2] < c < stop and c in (STARTS[8], STARTS[14], EC_START):
                stop = c - 0.05
        out[k][3] = stop
    return [tuple(p) for p in out]


PILLS = _pops()


def shot_times():
    return [(a, a + s[2]) for a, s in zip(STARTS, SHOTS)]


def caption_chunks():
    return []


if __name__ == "__main__":
    print("TOTAL", TOTAL)
    for (c, st, d, *_), a in zip(SHOTS, STARTS):
        print(f"{a:6.2f}-{a + d:6.2f}  {c:3s} src {st:5.2f}-{st + d:5.2f}")
    for p in PILLS:
        print(p)
