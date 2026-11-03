"""Video 1 lock-down cut: PalmCare Milky Hydro-Glow + PalmCare Cacao & Collagen, light-chocolate model.
Product-on-counter shots are camera-locked (labels glued to still bottles), the body-wash line no longer mentions
particles, bold captions, a spotlight pop-up card at each product reveal, ingredient call-outs pointing at the real
label, and benefit explainers. Graphics: overlay1r.py."""
import json

V = "1r"
TOTAL = 1017 / 24
VO = "../v1r/edit/vo1r.wav"             # already placed on the output timeline
VOSEG = [(0.0, TOTAL, 0.0)]
VO_WORDS = "../v1r/edit/vo1r_words.json"
CAPTION_UNTIL = 35.4                    # the end card shows the slogan itself
MUSIC = "../v1r/edit/music1r.wav"
MUSVOL, MUSOFF = 0.9, 0.0
END_CARD = "../v1n/edit/ec1n2.mp4"
BADGE = "PALMCARE"
LINE = None
LINE_WORDS, LINE_CHUNKS = [], []
STILL = (1.0, 1.0, 0, 0, "s")


def fr(n):
    """n frames at 24 fps (a hair under, so ffmpeg's trim keeps exactly n frames)."""
    return round(n / 24 - 0.002, 4)

# (clip, src start, duration, move (z0, z1, dx, dy, ease), transitions; "sp:x" = slow motion)
SHOTS = [("rA", 0.2, fr(65), (1.00, 1.08, 0, 20, "s"), {"dip_in"}),
         ("rC", 6.2, fr(46), (1.00, 1.06, 0, -10, "s"), {"wo:90"}),
         ("rA", 4.05, fr(70), (1.00, 1.03, -12, 0, "s"), {"wi:90"}),          # she shows Milky Hydro-Glow
         ("rB", 0.1, fr(68), STILL, set()),                                 # locked: Milky on the counter
         ("rB", 3.1, fr(86), (1.00, 1.06, 0, 10, "s"), set()),               # thick slow pour
         ("rB", 7.2, fr(38), (1.04, 1.10, -10, 0, "s"), {"wo:0"}),
         ("rC", 0.4, fr(43), (1.04, 1.10, 0, 0, "o"), {"wi:0"}),
         ("rC", 3.3, fr(48), (1.02, 1.08, 10, -10, "s"), {"flash_out"}),
         ("rE", 7.0, fr(71), (1.00, 1.03, 0, -10, "s"), {"flash_in"}),       # she shows Cacao & Collagen
         ("rE", 0.05, fr(91), STILL, {"sp:0.75"}),                            # locked: Cacao on the counter
         ("rE", 3.6, fr(79), (1.02, 1.07, -10, -10, "s"), set()),
         ("rD", 0.45, fr(144), (1.00, 1.03, 0, 0, "s"), {"sp:0.75", "flash_out"}),
         ("EC", 0, fr(168), None, set())]
SFX = [("reveal", 4.55), ("reveal", 19.3), ("card", 35.35)]
OPENER = (0.25, 2.5, "The Morning Glow")
OPENER_Y = 140
TITLES, CHIPS = [], []
# product spotlight pop-ups at the reveals: (cutout, line1, line2, category, bullets, t0, t1, y_centre)
SPOTLIGHT = [("../straight/out/milky.png", "Milky", "Hydro-Glow", "MOISTURIZING BODY WASH",
              ["Advanced Hydration Complex", "Rich, creamy lather", "Smooths & softens skin"], 4.7, 7.4, 1530),
             ("../straight/out/cacao.png", "Cacao &", "Collagen", "BODY LOTION",
              ["Collagen · Niacinamide · Vitamin E", "24hr deep moisture", "Non-greasy, fast absorbing"], 19.5, 22.2, 1530)]
# ingredient call-outs on the locked shots: (title, line, t0, t1, anchor xy on the label, tag centre xy)
TAGS = [("ADVANCED\nHYDRATION\nCOMPLEX", "Deep moisture\nas you cleanse", 9.1, 10.32, (372, 1078), (162, 1300)),
        ("COLLAGEN\nPEPTIDES", "Supple, bouncy-\nfeeling skin", 23.1, 26.03, (404, 1316), (175, 1110)),
        ("NIACINAMIDE", "Smooth, refined-\nlooking texture", 24.6, 26.03, (470, 1352), (175, 1480)),
        ("VITAMIN E", "Nourishes and\nprotects", 25.2, 26.03, (659, 1326), (912, 1470))]
# benefit explainers: (title, line, icon, t0, t1, y_centre)
POPS = [("RICH, CREAMY LATHER", "Cleanses gently, never stripping", "drop", 11.6, 13.85, 1330),
        ("SMOOTH · SOFT · HYDRATED", "Silky skin after every shower", "sparkle", 14.05, 17.25, 1330),
        ("24HR DEEP MOISTURE", "Long-lasting hydration, all day", "clock", 29.36, 30.7, 330),
        ("RADIANT GLOW", "Healthy-looking, luminous skin", "sparkle", 30.8, 32.4, 330),
        ("FAST ABSORBING", "Never greasy, never sticky", "leaf", 32.5, 35.3, 330)]


def shot_times():
    t, out = 0.0, []
    for s in SHOTS:
        d = round(s[2] * 24) / 24
        out.append((t, t + d))
        t += d
    return out


def caption_chunks():
    ws = [w for w in json.load(open(VO_WORDS))["words"] if w["start"] < CAPTION_UNTIL]
    ch, cur, pid = [], [], None
    for w in ws:
        if pid is not None and (w["phrase"] != pid or len(cur) >= 6):
            ch.append(cur)
            cur = []
        cur.append((w["text"].replace("...", "…").replace("twenty-four-hour", "24-hour"), w["start"], w["end"]))
        pid = w["phrase"]
    if cur:
        ch.append(cur)
    return ch


if __name__ == "__main__":
    print("shots end", shot_times()[-1][1], "TOTAL", TOTAL)
    for (s, *_), (a, b) in zip(SHOTS, shot_times()):
        print(f"{a:6.2f}-{b:6.2f} {s}")
    for c in caption_chunks():
        print(round(c[0][1], 2), round(c[-1][2], 2), " ".join(w[0] for w in c))
