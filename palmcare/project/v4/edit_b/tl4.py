"""Video 3 — "Lagos sun, meet your match": PalmCare Advanced Tropical Glow Exfoliating Lightening Body Wash +
PalmCare Dermalight Body Lotion. Beat-cut to the 80 BPM score (impacts at 6 / 24 / 45 s). No AI-generated bottle:
the two reveals (PT, PD) and the end card are built from the straight product photos."""
import json

V = "4b"
BPM = 120
BEAT = 60 / BPM
VO = "vo4.wav"
VO_WORDS = "vo4_words.json"
MUSIC = "../../music/v4b/music_v4b.wav"
EC_FILE = "../EC4.mp4"
XF = 0.0

S0 = (1.0, 1.0, 0, 0, "s")
PUSH = (1.00, 1.05, 0, 0, "s")
SHOTS_B = [("K1", 3.5, 6, PUSH, set()),                       # Lagos sun: bridge, tilt into the blazing flare
           ("K2", 3.4, 6, (1.02, 1.08, 0, 0, "s"), set()),    # her eyes open in the palm shadows: "meet your match"
           ("PT", 0.0, 9, S0, {"nograde"}),                    # REVEAL 1 (6 s): body wash out of the gold vortex
           ("K3", 1.0, 6, PUSH, set()),                        # gold-leaf vortex (exfoliating formula)
           ("K4", 1.4, 6, S0, set()),                          # golden scrub on her shoulder
           ("K4", 4.6, 4, S0, set()),                          # water rinses it to a polished glow
           ("K4", 8.45, 3, S0, set()),                         # face in the water
           ("K2", 5.8, 8, (1.00, 1.05, 0, 0, "s"), set()),    # confident smile in the shadows (build)
           ("PD", 0.0, 9, S0, {"nograde"}),                    # REVEAL 2 (24 s): lotion in glass and light
           ("K5", 0.6, 8, PUSH, set()),                        # lotion pour, rainbow refraction (ingredients at work)
           ("K6", 1.6, 6, S0, set()),                          # smoothing it on
           ("K6", 6.0, 4, S0, set()),                          # glass skin, soft smile
           ("K7", 0.4, 8, S0, {"shield"}),                     # walks into the midday sun: UV shield
           ("K8", 2.5, 3, S0, {"shield"}),                     # face up to the sun
           ("K8", 6.8, 4, S0, set()),                          # powerful smile: Lighter. Even. Protected.
           ("EC", 0.0, 24, None, set())]                       # end card (45 s)


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
SHIELD = (38.95, STARTS[14])         # UV shield dome over her (appears as "UV defence" is spoken)

# narration (line, phrase, start). Line 0 is the original "Lagos sun... meet your match." read from the first Video 3.
VO_PLACE = [(0, 0, 0.80), (0, 1, 3.30),
            (1, 0, 6.50),
            (2, 0, 10.80), (2, 1, 13.90), (2, 2, 16.50),
            (3, 0, 22.40), (3, 1, 24.35),
            (4, 0, 27.75), (4, 1, 29.66), (4, 2, 31.95), (4, 3, 34.45), (4, 4, 36.60),
            (5, 0, 38.70), (5, 1, 41.10),
            (6, 0, 42.90), (6, 1, 43.75), (6, 2, 44.55),
            (7, 0, 46.60)]

TITLES = [("Advanced", "Tropical Glow", "PALMCARE  ·  LIGHTENING BODY WASH", STARTS[2] + 0.7, STARTS[3] - 0.1),
          ("Dermalight", "Body Lotion", "PALMCARE  ·  EVEN-TONE BODY LOTION", STARTS[8] + 0.7, STARTS[9] - 0.1)]
PILLS = []                              # filled from the word timings below (pop-ups on key words)
POPS = [("exfoliating", "Exfoliating formula"), ("dullness,", "Buffs away dullness"),
        ("lightening", "Intense lightening complex"), ("smoother,", "Smoother, radiant skin"),
        ("flawless,", "Flawless, glass-like finish"), ("UV", "UV defence shield")]
# ingredients at work: each active slides in with the job it does (word it is spoken on, name, job)
HEALTHY = ("Healthy ingredients", STARTS[9] + 0.05, 29.6)
INGREDIENTS = [("arbutin", "ALPHA ARBUTIN", "Targets dark spots"),
               ("tranexamic", "TRANEXAMIC ACID", "Clears stubborn patches"),
               ("vitamins", "VITAMINS B3 + E", "Nourish & refine")]
WORDS = [("Lagos sun", 0.8, 2.9), ("Meet your match", 3.3, STARTS[2] - 0.05),
         ("Lighter", 42.9, 43.7), ("Even", 43.75, 44.5), ("Protected", 44.55, EC_START - 0.02)]


def _pops():
    try:
        ws = json.load(open(VO_WORDS))["words"]
    except Exception:
        return []
    out, used = [], set()
    for key, text in POPS:
        w = next((w for w in ws if w["text"].strip(".,…").lower() == key.strip(".,").lower() and w["start"] not in used
                  and not any(a <= w["start"] < b for a, b in PRODUCT_SPANS)), None)
        if w:
            used.add(w["start"])
            out.append(["spark", text, w["start"], 0.0, 1360])
    for k in range(len(out)):                    # each pop stays until just before the next one (max 2.4 s), never past a reveal
        nxt = out[k + 1][2] - 0.08 if k + 1 < len(out) else out[k][2] + 2.0
        stop = min(nxt, out[k][2] + 2.4)
        for c in CUTS:
            if out[k][2] < c < stop and c in (STARTS[8], STARTS[14], EC_START):
                stop = c - 0.05
        out[k][3] = stop
    return [tuple(p) for p in out]


PILLS = _pops()


def ingredient_cards():
    """(name, job, start, end): each card lands on its spoken ingredient and they stack until the shot changes."""
    try:
        ws = json.load(open(VO_WORDS))["words"]
    except Exception:
        return []
    out = []
    for key, name, job in INGREDIENTS:
        w = next(w for w in ws if w["text"].strip(".,…").lower() == key)
        out.append((name, job, w["start"] - 0.1, STARTS[11] + 1.0))
    return out


CARDS = ingredient_cards()


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
