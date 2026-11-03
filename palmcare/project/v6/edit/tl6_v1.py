"""Video 4 — "Around the clock": the PalmCare serum family. PalmCare Vita C+ Serum (sunrise, gold), PalmCare N10
Niacinamide Serum (daylight, aqua), PalmCare DermaLuxe Pro Hydrating Night Repair Serum (midnight, violet).
Cut on the 120 BPM grid of the day-to-night score (bar = 2 s; impacts at 10 / 26 / 48 / 68 s). No AI-generated
bottle or box: the three unveils and the end card are built from the straight product photos and packs."""
import json

V = "6"
BPM = 120
BEAT = 60 / BPM
VO = "vo6.wav"
VO_WORDS = "vo6_words.json"
MUSIC = "../../music/v6/music_v6.wav"
EC_FILE = "../EC6.mp4"
XF = 0.0
HITS = (10.0, 26.0, 48.0, 68.0)

S0 = (1.0, 1.0, 0, 0, "s")
PUSH = (1.00, 1.05, 0, 0, "s")
SHOTS_B = [("S2", 2.4, 4, (1.00, 1.08, 0, 0, "s"), set()),    # HOOK: golden drop stretches and falls ("Three drops.")
           ("S4", 5.0, 4, (1.00, 1.08, 0, 0, "s"), set()),    # aqua crown splash ("Twenty-four hours.")
           ("S6", 4.2, 4, (1.00, 1.08, 0, 0, "s"), set()),    # violet drop ("One flawless glow.")
           ("S1", 4.0, 8, PUSH, set()),                        # sunrise: she wakes into gold
           ("PV", 0.0, 10, S0, {"nograde"}),                   # UNVEIL 1 (10 s): Vita C+ Serum
           ("S3", 2.2, 8, S0, set()),                          # pressing serum into her cheeks
           ("S2", 6.0, 5, S0, set()),                          # the golden drop lands and spreads on skin
           ("S3", 7.0, 5, S0, set()),                          # radiant, dewy
           ("S1", 7.8, 4, S0, set()),                          # her sunrise smile
           ("PN", 0.0, 10, S0, {"nograde"}),                   # UNVEIL 2 (26 s): N10 Niacinamide Serum
           ("S4", 0.3, 6, PUSH, set()),                        # crystal drop forming (healthy ingredients)
           ("S5", 1.2, 8, S0, set()),                          # daylight: she touches her even, fresh skin
           ("S4", 6.6, 6, S0, set()),                          # ripples
           ("S5", 5.4, 8, S0, set()),                          # confident smile in the light
           ("S6", 0.0, 6, PUSH, set()),                        # violet drop forming: night falls
           ("PD", 0.0, 10, S0, {"nograde"}),                   # UNVEIL 3 (48 s): DermaLuxe Pro
           ("S6", 7.2, 4, S0, set()),                          # the night serum lands on skin
           ("S7", 0.3, 8, S0, set()),                          # night ritual
           ("S7", 5.0, 8, S0, set()),                          # serene, eyes closed
           ("S8", 1.0, 6, S0, set()),                          # light shifts gold, aqua, violet: Bright. Even. Renewed.
           ("S8", 6.8, 4, S0, set()),                          # radiant smile to camera
           ("EC", 0.0, 20, None, set())]                       # end card (68 s)


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
REVEALS = [STARTS[4], STARTS[9], STARTS[15]]
PRODUCT_SPANS = [(STARTS[4], STARTS[5]), (STARTS[9], STARTS[10]), (STARTS[15], STARTS[16])]
PS_JSON = ["../PS_vitac.json", "../PS_n10.json", "../PS_derma.json"]
SHIELD = (999.0, 999.0)               # no UV shield in this film

VO_PLACE = [(0, 0, 0.30), (0, 1, 2.25), (0, 2, 4.25),
            (1, 0, 7.20), (1, 1, 10.50),
            (2, 0, 15.30), (2, 1, 19.90), (2, 2, 21.80),
            (3, 0, 25.00), (3, 1, 26.50),
            (4, 0, 31.20), (4, 1, 33.00), (4, 2, 36.80), (4, 3, 41.90),
            (5, 0, 47.00), (5, 1, 48.50),
            (6, 0, 53.30), (6, 1, 55.80), (6, 2, 58.80),
            (7, 0, 63.40), (7, 1, 64.20), (7, 2, 65.00),
            (8, 0, 69.40)]

TITLES = [("PalmCare", "Vita C+ Serum", "ULTRA-ACTIVE VITAMIN C FORMULA", STARTS[4] + 0.9, STARTS[5] - 0.1),
          ("PalmCare", "N10 Niacinamide", "SERUM  ·  ADVANCED EVENTONE CARE", STARTS[9] + 0.9, STARTS[10] - 0.1),
          ("PalmCare", "DermaLuxe Pro", "HYDRATING NIGHT REPAIR SERUM", STARTS[15] + 0.9, STARTS[16] - 0.1)]
CALLOUTS = []
PILLS = []                              # filled from the word timings below (pop-ups on key words)
POPS = [("dull", "Wakes up dull skin"), ("dark", "Fades dark spots"), ("radiance.", "Hydration + radiance"),
        ("balances,", "4% niacinamide balances"), ("congestion,", "Clears congestion"), ("drenches", "Overnight deep hydration")]
# N10, healthy ingredients at work: each pair of actives slides in with its job (word it is spoken on, occurrence, name, job)
HEALTHY = ("Healthy ingredients", 31.15, 33.0)
INGREDIENTS = [("niacinamide", 1, "NIACINAMIDE  ·  ALPHA ARBUTIN", "Target discolouration"),
               ("zinc", 0, "ZINC PCA  ·  LICORICE EXTRACT", "Refine pores, control shine"),
               ("hyaluronic", 0, "HYALURONIC ACID  ·  PANTHENOL  ·  ALOE", "Plump & soothe")]
WORDS = [("Three drops", 0.30, 1.95), ("Twenty-four hours", 2.25, 3.95), ("One flawless glow", 4.25, 5.95),
         ("Bright", 63.40, 64.15), ("Even", 64.20, 64.95), ("Renewed", 65.00, 66.9)]


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
            if out[k][2] < c < stop and c in (STARTS[4], STARTS[9], STARTS[15], EC_START):
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
