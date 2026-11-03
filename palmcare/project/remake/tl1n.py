"""Video 1 (client-correction remake): PalmCare Milky Hydro-Glow + PalmCare Cacao & Collagen, light-chocolate model.
New Flow clips (labels replaced with the real labels), free Kokoro narration laid out by ../v1n/edit/make_vo.py,
"PalmCare" before every product name, "Pamper your skin with PalmCare." on the end card."""
import json

V = "1n"
TOTAL = 39.3
VO = "../v1n/edit/vo1n.wav"            # already placed on the output timeline
VOSEG = [(0.0, TOTAL, 0.0)]
VO_WORDS = "../v1n/edit/vo1n_words.json"
CAPTION_UNTIL = 32.5                    # the end-card slogan is shown by the card itself
MUSIC = "../v1n/edit/music1n.wav"
MUSVOL, MUSOFF = 0.9, 0.0
END_CARD = "../v1n/edit/ec1n.mp4"
BADGE = "PALMCARE"
# her line in clip F: speech 1.8-3.3 s of the clip
LINE = ("nF", 1.6, 3.5, 29.5)
LINE_WORDS = [("This", 1.82, 1.98), ("is", 1.98, 2.08), ("how", 2.08, 2.25), ("I", 2.25, 2.33), ("pamper", 2.33, 2.65),
              ("my", 2.65, 2.80), ("skin.", 2.80, 3.10)]
LINE_CHUNKS = [7]
# (clip, src start, duration, move (z0, z1, dx, dy, ease), transitions)
SHOTS = [("nA", 0.3, 2.4, (1.00, 1.10, 0, 20, "s"), {"dip_in"}),
         ("nA", 4.1, 2.6, (1.02, 1.08, 0, -10, "s"), {"wo:90"}),
         ("nB", 0.4, 2.0, (1.04, 1.10, 0, 0, "o"), {"wi:90"}),
         ("nB", 3.3, 3.0, (1.00, 1.08, 0, 10, "s"), set()),
         ("nB", 7.3, 1.6, (1.04, 1.10, -10, 0, "s"), {"wo:0"}),
         ("nC", 0.5, 1.8, (1.04, 1.12, 0, 0, "o"), {"wi:0"}),
         ("nC", 3.4, 1.4, (1.02, 1.08, 10, -10, "s"), set()),
         ("nC", 6.4, 2.0, (1.00, 1.06, 0, -10, "s"), {"flash_out"}),
         ("nE", 0.2, 2.8, (1.00, 1.06, 0, 0, "s"), {"flash_in"}),
         ("nE", 3.4, 3.0, (1.04, 1.10, -10, -10, "s"), set()),
         ("nE", 7.2, 2.6, (1.00, 1.05, 0, -10, "s"), {"wo:90"}),
         ("nD", 0.6, 3.7, (1.00, 1.05, 0, 0, "s"), {"wi:90"}),
         ("nF", 1.0, 3.4, (1.00, 1.05, 0, -10, "s"), {"flash_out"}),
         ("EC", 0, 7.0, None, set())]
SFX = [("reveal", 2.35), ("reveal", 16.75), ("reveal", 25.15), ("card", 32.25)]
CHIPS = [("GENTLY EXFOLIATES", 7.2, 9.4), ("ADVANCED HYDRATION COMPLEX", 10.0, 11.6),
         ("COLLAGEN PEPTIDES + VITAMIN E", 20.9, 23.6), ("24HR DEEP MOISTURE", 24.5, 26.2),
         ("NON-GREASY · FAST ABSORBING", 27.6, 28.9)]
TITLES = [("MILKY HYDRO-GLOW", "Moisturizing Body Wash", 2.5, 5.0), ("CACAO & COLLAGEN", "Body Lotion", 16.9, 19.6)]
OPENER = (0.25, 2.2, "The Morning Glow")


def shot_times():
    t, out = 0.0, []
    for s in SHOTS:
        out.append((t, t + s[2]))
        t += s[2]
    return out


def vo_words():
    return [(w["text"].replace("...", "…"), w["start"], w["end"]) for w in json.load(open(VO_WORDS))["words"]
            if w["start"] < CAPTION_UNTIL]


def chunk(words, maxn=4):
    out, cur = [], []
    for k, w in enumerate(words):
        cur.append(w)
        nxt = words[k + 1] if k + 1 < len(words) else None
        closes = nxt is not None and nxt[0][-1] in ".,…?!" and nxt[1] - w[2] <= 0.45
        brk = (w[0][-1] in ".,…?!" or (len(cur) >= maxn and not (len(cur) == maxn and closes)) or nxt is None
               or nxt[1] - w[2] > 0.45)
        if brk:
            out.append(cur)
            cur = []
    return out


def caption_chunks():
    ch = chunk(vo_words())
    off = LINE[3] - LINE[1]
    lw = [(t, s + off, e + off) for t, s, e in LINE_WORDS]
    k = 0
    for n in LINE_CHUNKS:
        ch.append(lw[k:k + n])
        k += n
    return ch


if __name__ == "__main__":
    print("shots end", shot_times()[-1][1], "TOTAL", TOTAL)
    for c in caption_chunks():
        print(round(c[0][1], 2), round(c[-1][2], 2), " ".join(w[0] for w in c))
