"""Video 1, reverse-engineered from the client's reference ads: PalmCare Milky Hydro-Glow + PalmCare Cacao & Collagen.
Morning story -> she picks the body wash -> CGI hero reveal -> pump / thick pour / shower -> Cacao hero reveal ->
lotion -> Lagos balcony result -> live packshot end card. Editorial Luxe graphics: overlay1x.py."""
import json

V = "1x"
VO = "../v1x/edit/vo.wav"
VO_WORDS = "../v1x/edit/vo_words.json"
MUSIC = "../v1x/edit/music.wav"
MUSVOL, MUSOFF = 0.9, 0.0
END_CARD = "x7.mp4"   # unused input (the end card is drawn over the live packshot)
BADGE = "PALMCARE"
LINE, LINE_WORDS, LINE_CHUNKS = None, [], []
TITLES, CHIPS = [], []


def fr(n):
    """n frames at 24 fps (a hair under, so ffmpeg's trim keeps exactly n frames)."""
    return round(n / 24 - 0.002, 4)


S0 = (1.0, 1.0, 0, 0, "s")
# (clip, src start, duration, move (z0, z1, dx, dy, ease), flags; "sp:x" slow motion, "warm" golden grade)
SHOTS = [("x1", 0.0, fr(70), (1.00, 1.06, 0, 16, "s"), {"dip_in"}),            # wakes up
         ("x1", 3.0, fr(94), (1.05, 1.00, 0, 0, "s"), set()),                   # walks into the bathroom
         ("x1b", 0.3, fr(62), (1.00, 1.03, 0, 0, "s"), set()),                  # takes Milky from the shelf
         ("x1b", 7.0, fr(70), (1.00, 1.05, 0, -10, "s"), set()),                # holds it, smiles
         ("x2", 0.0, fr(115), (1.00, 1.06, 0, 0, "s"), set()),                  # Milky hero reveal
         ("x2", 5.0, fr(72), (1.06, 1.06, 0, 0, "s"), {"sp:0.6"}),              # milk crown, slow motion
         ("x3", 0.1, fr(67), S0, set()),                                        # pump (locked)
         ("x3", 3.0, fr(29), S0, set()),                                        # pour, real speed ...
         ("x3", 4.2, fr(72), (1.00, 1.08, 0, 0, "s"), {"sp:0.6"}),              # ... ramps into slow motion
         ("x3", 7.0, fr(72), (1.02, 1.08, 0, -10, "s"), set()),                 # shower lather
         ("x4", 0.0, fr(115), (1.00, 1.03, 0, 0, "s"), set()),                  # Cacao hero reveal
         ("x5", 0.1, fr(66), S0, set()),                                        # lotion pump (locked)
         ("x4", 5.0, fr(72), (1.08, 1.08, 0, 0, "s"), {"sp:0.6"}),              # lotion wave, slow motion
         ("x5", 3.0, fr(94), (1.02, 1.08, -10, -10, "s"), set()),               # smooths it on
         ("x5", 7.0, fr(71), (1.00, 1.04, 0, 0, "s"), set()),                   # holds Cacao, smiles
         ("x6", 0.2, fr(96), (1.00, 1.08, 0, 0, "s"), {"warm"}),                # Lagos balcony
         ("x6", 5.4, fr(84), (1.00, 1.05, 0, -10, "s"), {"warm"}),              # beauty close-up
         ("x7", 4.65, fr(144), (1.00, 1.03, 0, 0, "s"), {"sp:0.89"})]           # live packshot end card
VOSEG = None   # set below
SFX = []       # set below


def shot_times():
    t, out = 0.0, []
    for s in SHOTS:
        d = round(s[2] * 24) / 24
        out.append((t, t + d))
        t += d
    return out


TOTAL = shot_times()[-1][1]
VOSEG = [(0.0, TOTAL, 0.0)]
CUTS = [a for a, _ in shot_times()[1:]]
EC_START = shot_times()[-1][0]
CAPTION_UNTIL = EC_START
# transition at each cut: leak (golden light leak), zoom (blur zoom-through), cut
TRANS = dict(zip(range(1, len(SHOTS)), ["leak", "zoom", "cut", "leak2", "cut", "zoom", "cut", "cut", "leak", "leak2", "zoom",
                                         "cut", "zoom", "cut", "leak", "leak", "zoom"]))
SFX = [("reveal", shot_times()[4][0] - 0.05), ("reveal", shot_times()[10][0] - 0.05), ("card", EC_START - 0.05)]


def caption_chunks():
    ws = [w for w in json.load(open(VO_WORDS))["words"] if w["start"] < CAPTION_UNTIL]
    groups = {}
    for w in ws:
        groups.setdefault(w["phrase"], []).append((w["text"].replace("...", "…").replace("twenty-four-hour", "24-hour"),
                                                   w["start"], w["end"]))
    ch = []
    for g in groups.values():          # each spoken phrase in balanced pieces of at most 4 words
        words = [w[0] for w in g]
        if "Body" in words and len(g) > 4:     # keep product names whole: "... Collagen" / "Body Lotion."
            b = words.index("Body")
            ch += [g[:b], g[b:]]
            continue
        k = -(-len(g) // 4)
        n = -(-len(g) // k)
        ch += [g[i:i + n] for i in range(0, len(g), n)]
    return ch


if __name__ == "__main__":
    print("TOTAL", TOTAL)
    for k, ((s, *_), (a, b)) in enumerate(zip(SHOTS, shot_times())):
        print(f"{k:2d} {a:6.2f}-{b:6.2f} {s}  -> {TRANS.get(k + 1, '')}")
    for c in caption_chunks():
        print(round(c[0][1], 2), round(c[-1][2], 2), " ".join(w[0] for w in c))

# ---- graphics (positions in output pixels) ----
OPENER = (0.0, 0.0, "PalmCare")   # unused (overlay1x draws its own opener)
OPENER_Y = 140
_T = shot_times()
# editorial titles at the hero reveals: (pre, line1, line2, sub, t0, t1, x, y)
EDIT_TITLES = [("PALMCARE", "Milky", "Hydro-Glow", "MOISTURIZING BODY WASH", 14.15, _T[4][1] - 0.05, 80, 34),
               ("PALMCARE", "Cacao &", "Collagen", "BODY LOTION", 31.75, _T[10][1] - 0.05, 80, 30)]
# ingredient tags pinned to the still bottles: (title, line, t0, t1, anchor, tag centre)
TAGS = [("ADVANCED\nHYDRATION\nCOMPLEX", "Hydrates as\nit cleanses", 21.8, _T[6][1] - 0.04, (360, 1098), (160, 1330)),
        ("COLLAGEN\nPEPTIDES", "Supple, bouncy-\nfeeling skin", 35.2, _T[11][1] - 0.04, (342, 1229), (150, 1150)),
        ("NIACINAMIDE", "Smooth, refined-\nlooking texture", 36.95, _T[11][1] - 0.04, (430, 1262), (160, 1470))]
# the same three on the lotion-wave shot (filled in from the measured label position)
TAGS += [("COLLAGEN\nPEPTIDES", "Supple, bouncy-\nfeeling skin", _T[12][0] + 0.03, _T[12][1] - 0.04, (376, 1180), (150, 980)),
         ("NIACINAMIDE", "Smooth, refined-\nlooking texture", _T[12][0] + 0.03, _T[12][1] - 0.04, (470, 1216), (150, 1420)),
         ("VITAMIN E", "Nourishes and\nprotects", 38.55, _T[12][1] - 0.04, (650, 1195), (915, 1330))]
COUNT = (40.72, 42.65, 330, 1150)
BENEFITS = [("RADIANT GLOW", 42.75, _T[13][1] - 0.05, 330, 1180),
            ("FAST ABSORBING  ·  NEVER GREASY", _T[14][0] + 0.05, _T[14][1] - 0.05, 540, 1450)]
EC_TAGS = []
