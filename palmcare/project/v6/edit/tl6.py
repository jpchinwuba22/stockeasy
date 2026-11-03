"""Video 4 — "Around the clock": the PalmCare serum family. PalmCare Vita C+ Serum (sunrise, gold), PalmCare N10
Niacinamide Serum (daylight, aqua), PalmCare DermaLuxe Pro Hydrating Night Repair Serum (midnight, violet).
Cut on the 120 BPM grid of the day-to-night score (bar = 2 s; impacts at 10 / 26 / 48 / 68 s). No AI-generated
bottle or box: the three unveils and the end card are built from the straight product photos and packs."""
import json

V = "6b"
BPM = 120
BEAT = 60 / BPM
VO = "vo6.wav"
VO_WORDS = "vo6_words.json"
MUSIC = "../../music/v6/music_v6b.wav"
EC_FILE = "../EC6.mp4"
XF = 0.0
HITS = (10.0, 30.0, 60.0, 88.0)

S0 = (1.0, 1.0, 0, 0, "s")
PUSH = (1.00, 1.05, 0, 0, "s")
SHOTS_B = [("S2", 2.4, 4, (1.00, 1.08, 0, 0, "s"), set()),    # HOOK: golden drop ("Three drops.")
           ("S4", 5.0, 4, (1.00, 1.08, 0, 0, "s"), set()),    # aqua crown splash ("Twenty-four hours.")
           ("S6", 4.2, 4, (1.00, 1.08, 0, 0, "s"), set()),    # violet drop ("One flawless glow.")
           ("S1", 4.0, 8, PUSH, set()),                        # 06:00 she wakes into gold
           ("PV", 0.0, 10, S0, {"nograde"}),                   # UNVEIL 1 (10 s): Vita C+ Serum pack
           ("S3", 2.2, 8, S0, set()),                          # sun and pollution... she presses serum in
           ("S2", 6.0, 8, S0, set()),                          # the golden drop lands and spreads
           ("S3", 6.4, 6, S0, set()),                          # radiant, dewy
           ("S1", 7.8, 4, S0, set()),                          # sunrise smile
           ("S2", 0.4, 4, S0, set()),                          # golden drop forming: day moves on
           ("PN", 0.0, 10, S0, {"nograde"}),                   # UNVEIL 2 (30 s): N10 Niacinamide pack
           ("S4", 0.3, 6, PUSH, set()),                        # crystal drop (healthy ingredients)
           ("S5", 1.2, 8, S0, set()),                          # daylight: even, fresh skin
           ("S4", 7.0, 6, S0, set()),                          # ripples
           ("S5", 5.4, 8, S0, set()),                          # confident smile
           ("S4", 3.3, 7, S0, {"sp:0.5"}),                     # the drop meets the water, slow motion
           ("S8", 2.4, 4, S0, set()),                          # aqua light on her face
           ("PN", 1.5, 7, S0, {"nograde"}),                    # N10 pack reprise (barrier line)
           ("S6", 0.0, 4, PUSH, set()),                        # 00:00 violet drop forming: night falls
           ("PD", 0.0, 10, S0, {"nograde"}),                   # UNVEIL 3 (60 s): DermaLuxe Pro pack
           ("S6", 7.2, 5, S0, set()),                          # the night serum lands on skin
           ("S7", 0.3, 8, S0, set()),                          # night ritual
           ("S6", 2.0, 4, S0, set()),                          # violet drop falling
           ("S7", 4.5, 10, S0, set()),                         # serene, eyes closed
           ("S1", 1.5, 7, S0, set()),                          # asleep... she wakes up smoother, clearer
           ("S8", 4.1, 8, S0, set()),                          # Bright. Even. Renewed.
           ("S8", 8.1, 4, S0, set()),                          # radiant smile to camera
           ("EC", 0.0, 20, None, set())]                       # end card (88 s)


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
REVEALS = [STARTS[4], STARTS[10], STARTS[19]]
PRODUCT_SPANS = [(STARTS[4], STARTS[5]), (STARTS[10], STARTS[11]), (STARTS[19], STARTS[20]), (STARTS[17], STARTS[18])]
PS_JSON = ["../PS_vitac.json", "../PS_n10.json", "../PS_derma.json", "../PS_n10.json"]
SHIELD = (999.0, 999.0)

VO_PLACE = [(0, 0, 0.30), (0, 1, 2.25), (0, 2, 4.25),
            (1, 0, 7.20), (1, 1, 10.50),
            (2, 0, 15.20), (2, 1, 18.20), (2, 2, 21.40), (2, 3, 24.20), (2, 4, 25.70),
            (3, 0, 29.30), (3, 1, 30.90),
            (4, 0, 35.20), (4, 1, 38.10), (4, 2, 43.40), (4, 3, 45.10), (4, 4, 48.75), (4, 5, 50.15), (4, 6, 51.40), (4, 7, 54.20),
            (5, 0, 58.20), (5, 1, 60.50),
            (6, 0, 65.20), (6, 1, 67.30), (6, 2, 69.30), (6, 3, 72.30), (6, 4, 75.20), (6, 5, 78.60),
            (7, 0, 82.40), (7, 1, 83.20), (7, 2, 84.00),
            (8, 0, 89.40)]

TITLES = [("PalmCare", "Vita C+ Serum", "ULTRA-ACTIVE VITAMIN C FORMULA", STARTS[4] + 0.9, STARTS[5] - 0.1),
          ("PalmCare", "N10 Niacinamide", "SERUM  ·  ADVANCED EVENTONE CARE", STARTS[10] + 0.9, STARTS[11] - 0.1),
          ("PalmCare", "DermaLuxe Pro", "HYDRATING NIGHT REPAIR SERUM", STARTS[19] + 0.9, STARTS[20] - 0.1)]
CALLOUTS = []
# kinetic benefit pop-ups: (spoken word, small label, big line, highlighted part)
POPS2 = [("free", "ANTIOXIDANT SHIELD", "Neutralises free radicals", "free radicals"),
         ("dark", "SPOT CORRECTOR", "Fades dark spots", "dark spots"),
         ("collagen", "COLLAGEN BOOST", "Firmer, luminous skin", "luminous"),
         ("healthy", "N10 FORMULA", "Healthy ingredients", "Healthy"),
         ("melanin", "NIACINAMIDE + ALPHA ARBUTIN", "Stops excess melanin", "excess melanin"),
         ("oil", "ZINC PCA + LICORICE", "Less oil, refined pores", "refined pores"),
         ("redness", "SOOTHING COMPLEX", "Calms redness", "redness"),
         ("moisture", "HYALURONIC ACID", "Draws moisture deep", "moisture"),
         ("barrier", "PANTHENOL + ALOE VERA", "Stronger skin barrier", "barrier"),
         ("repairs", "WHILE YOU SLEEP", "Night repair mode", "repair"),
         ("balance", "4% NIACINAMIDE", "Restores balance", "balance"),
         ("congestion", "SALICYLIC ACID", "Clears congestion", "congestion"),
         ("hydration", "MULTI-HUMECTANT COMPLEX", "Locks in hydration", "hydration"),
         ("refreshed", "WAKE UP", "Smoother. Clearer.", "Clearer.")]
POPS = []
PILLS = []
HEALTHY = ("", 999.0, 999.0)
INGREDIENTS = []
# big kinetic words: (bold part, italic part, start, end)
WORDS2 = [("THREE", "drops", 0.30, 1.95), ("TWENTY-FOUR", "hours", 2.25, 3.95), ("ONE", "flawless glow", 4.25, 5.95),
          ("BRIGHT", "", 82.40, 83.15), ("", "even", 83.20, 83.95), ("RENEWED", "", 84.00, 86.0)]
WORDS = []


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


def _pops2():
    ws = _words()
    out = []
    for key, lab, line, hl in POPS2:
        w = next((w for w in ws if _norm(w) == key and not any(a <= w['start'] < b for a, b in PRODUCT_SPANS[:3])), None)
        if w:
            out.append([lab, line, hl, w['start'] - 0.05, 0.0])
    for k in range(len(out)):
        nxt = out[k + 1][3] - 0.12 if k + 1 < len(out) else out[k][3] + 2.6
        stop = min(nxt, out[k][3] + 3.2)
        for c in (STARTS[10], STARTS[19], STARTS[25], EC_START):
            if out[k][3] < c < stop:
                stop = c - 0.05
        out[k][4] = stop
    return [tuple(p) for p in out]


POPS2_T = _pops2()


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
    for p in POPS2_T:
        print(p)
    for c in CARDS:
        print(c)
