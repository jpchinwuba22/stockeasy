"""Video 3 — "Lagos sun, meet your match": PalmCare Advanced Tropical Glow Exfoliating Lightening Body Wash +
PalmCare Dermalight Body Lotion. Cut on the 120 BPM grid of the Afro-luxe score (bar = 2 s; impacts at 6 / 26 / 54 s).
No AI-generated bottle: the two unveils (PT, PD) and the end card are built from the straight product photos."""
import json

V = "4c"
BPM = 120
BEAT = 60 / BPM
VO = "vo4.wav"
VO_WORDS = "vo4_words.json"
MUSIC = "../../music/v4c/music_v4d.wav"
EC_FILE = "../EC5.mp4"
XF = 0.0
HITS = (6.0, 26.0, 56.0)

S0 = (1.0, 1.0, 0, 0, "s")
PUSH = (1.00, 1.05, 0, 0, "s")
SHOTS_B = [("K2", 3.4, 6, (1.02, 1.08, 0, 0, "s"), set()),    # her eyes open in the palm shadows: "Step out of the shadows"
           ("K1", 3.5, 6, PUSH, set()),                        # into the blazing sun: "into your glow"
           ("PT", 0.0, 10, S0, {"nograde"}),                   # UNVEIL 1 (6 s): body wash
           ("K9", 0.2, 6, PUSH, set()),                        # the real gel: amber, fine dark micro-granules, gold flecks
           ("K4", 1.4, 6, S0, set()),                          # golden gel on her shoulder
           ("K4", 4.6, 5, S0, set()),                          # water rinses it to a polished glow
           ("K4", 8.45, 3, S0, set()),                         # face in the water
           ("K2", 6.4, 6, (1.00, 1.05, 0, 0, "s"), set()),    # confident smile in the shadows
           ("K4", 0.0, 4, (1.00, 1.06, 0, 0, "s"), {"sp:0.7"}),  # glowing shoulder, slow: builds into the second unveil
           ("PD", 0.0, 10, S0, {"nograde"}),                   # UNVEIL 2 (26 s): lotion
           ("K5", 0.6, 8, PUSH, set()),                        # lotion pour (ingredients at work)
           ("K6", 1.6, 8, S0, set()),                          # smoothing it on
           ("K5", 6.9, 6, S0, set()),                          # rainbow light through the lotion
           ("K6", 5.8, 8, S0, set()),                          # glass skin, soft smile
           ("K7", 0.4, 8, S0, set()),                          # walks into the midday sun: lightens + UV shield
           ("K8", 2.5, 6, S0, {"shield"}),                     # face up to the sun
           ("K8", 6.8, 6, S0, set()),                          # powerful smile: Lighter. Even. Protected.
           ("EC", 0.0, 24, None, set())]                       # end card (56 s)


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
REVEALS = [STARTS[2], STARTS[9]]
PRODUCT_SPANS = [(STARTS[2], STARTS[3]), (STARTS[9], STARTS[10])]
PS_JSON = ["../PS3_Tropical.json", "../PS2_Dermalight.json"]
SHIELD = (48.15, STARTS[16])         # UV shield dome over her (appears as "UV defence" is spoken)

# narration (line, phrase, start). Line 0 is the original "Lagos sun... meet your match." read from the first Video 3.
VO_PLACE = [(0, 0, 0.80), (0, 1, 3.30),
            (1, 0, 6.70),
            (2, 0, 11.20), (2, 1, 15.40), (2, 2, 20.60),
            (3, 0, 24.40), (3, 1, 26.50),
            (4, 0, 29.00), (4, 1, 31.60), (4, 2, 35.05), (4, 3, 38.75), (4, 4, 43.70),
            (5, 0, 46.30), (5, 1, 48.10), (5, 2, 50.50),
            (6, 0, 52.60), (6, 1, 53.40), (6, 2, 54.20),
            (7, 0, 57.40)]

TITLES = [("Advanced", "Tropical Glow", "PALMCARE  ·  LIGHTENING BODY WASH", STARTS[2] + 0.9, STARTS[3] - 0.1),
          ("Dermalight", "Body Lotion", "PALMCARE  ·  EVEN-TONE BODY LOTION", STARTS[9] + 0.9, STARTS[10] - 0.1)]
# label call-outs on the unveils: (product index, fraction down the bottle, side, line 1, line 2, start offset)
CALLOUTS = [(0, 0.535, -1, "INTENSE", "LIGHTENING COMPLEX", 2.0), (0, 0.72, 1, "EXFOLIATING", "FORMULA", 2.3),
            (0, 0.875, -1, "DEEP MOISTURE", "BOOST", 2.6),
            (1, 0.515, -1, "GLASS-SKIN", "TONE-UP CARE", 2.0), (1, 0.655, 1, "ALPHA ARBUTIN +", "TRANEXAMIC ACID", 2.3),
            (1, 0.80, -1, "UV DEFENCE", "SHIELD", 2.6)]
PILLS = []                              # filled from the word timings below (pop-ups on key words)
POPS = [("exfoliating", "Exfoliating formula"), ("dull", "Lifts away dull cells"),
        ("lightening", "Intense lightening complex"), ("moisture", "Deep moisture boost"),
        ("lightens", "Lightens your skin"), ("UV", "UV defence shield")]
# ingredients at work: each active slides in with the job it does (word it is spoken on, occurrence, name, job)
HEALTHY = ("Healthy ingredients", STARTS[10] + 0.05, 31.5)
INGREDIENTS = [("arbutin", 0, "ALPHA ARBUTIN", "Slows the melanin behind dark spots"),
               ("tranexamic", 0, "TRANEXAMIC ACID", "Calms stubborn patches"),
               ("niacinamide,", 0, "NIACINAMIDE · VITAMIN B3", "Refines tone, strengthens barrier"),
               ("vitamin", 1, "VITAMIN E", "Nourishes & defends")]
WORDS = [("Step out of the shadows", 0.8, 2.95), ("Into your glow", 3.3, STARTS[2] - 0.05),
         ("Lighter", 52.6, 53.35), ("Even", 53.4, 54.15), ("Protected", 54.2, EC_START - 0.02)]


def _words():
    try:
        return json.load(open(VO_WORDS))["words"]
    except Exception:
        return []


def _norm(w):
    return w["text"].strip(".,…").lower()


def _pops():
    ws = _words()
    out, used = [], set()
    for key, text in POPS:
        w = next((w for w in ws if _norm(w) == key.strip(".,").lower() and w["start"] not in used
                  and not any(a <= w["start"] < b for a, b in PRODUCT_SPANS)), None)
        if w:
            used.add(w["start"])
            out.append(["spark", text, w["start"], 0.0, 1360])
    for k in range(len(out)):                    # each pop stays until just before the next one (max 2.6 s), never past a reveal
        nxt = out[k + 1][2] - 0.08 if k + 1 < len(out) else out[k][2] + 2.2
        stop = min(nxt, out[k][2] + 2.6)
        for c in CUTS:
            if out[k][2] < c < stop and c in (STARTS[9], EC_START):
                stop = c - 0.05
        out[k][3] = stop
    return [tuple(p) for p in out]


PILLS = _pops()


def ingredient_cards():
    """(name, job, start, end): each card lands on its spoken ingredient and they stack until the UV section."""
    ws = _words()
    out = []
    for key, occ, name, job in INGREDIENTS:
        hits = [w for w in ws if _norm(w) == key.strip(".,")]
        if len(hits) > occ:
            out.append((name, job, hits[occ]["start"] - 0.1, STARTS[14] - 0.1))
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
    for c in CARDS:
        print(c)
