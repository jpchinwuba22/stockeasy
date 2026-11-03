"""Video 1 (client-correction remake): PalmCare Milky Hydro-Glow + PalmCare Cacao & Collagen, light-chocolate model.
New Flow clips (labels replaced with the real labels), free Kokoro narration laid out by ../v1n/edit/make_vo.py,
"PalmCare" before every product name, "Pamper your skin with PalmCare." on the end card."""
import json

V = "1n2"
TOTAL = 37.9
VO = "../v1n/edit/vo1n2.wav"            # already placed on the output timeline
VOSEG = [(0.0, TOTAL, 0.0)]
VO_WORDS = "../v1n/edit/vo1n2_words.json"
CAPTION_UNTIL = 31.2                    # the end-card slogan is shown by the card itself
MUSIC = "../v1n/edit/music1n.wav"
MUSVOL, MUSOFF = 0.9, 0.0
END_CARD = "../v1n/edit/ec1n2.mp4"
BADGE = "PALMCARE"
# her line in clip F: speech 1.8-3.3 s of the clip
LINE = None   # her on-camera clip was dropped (its Milky bottle had the wrong label layout)
LINE_WORDS = [("This", 1.82, 1.98), ("is", 1.98, 2.08), ("how", 2.08, 2.25), ("I", 2.25, 2.33), ("pamper", 2.33, 2.65),
              ("my", 2.65, 2.80), ("skin.", 2.80, 3.10)]
LINE_CHUNKS = []
# (clip, src start, duration, move (z0, z1, dx, dy, ease), transitions)
SHOTS = [("nA", 0.2, 2.7, (1.00, 1.08, 0, 20, "s"), {"dip_in"}),
         ("nC", 6.2, 1.9, (1.00, 1.06, 0, -10, "s"), {"wo:90"}),
         ("nA", 4.1, 2.8, (1.00, 1.03, -12, 0, "s"), {"wi:90"}),
         ("nB", 0.3, 1.5, (1.02, 1.06, 0, 0, "o"), set()),
         ("nB", 3.1, 3.6, (1.00, 1.08, 0, 10, "s"), set()),
         ("nB", 7.2, 1.6, (1.04, 1.10, -10, 0, "s"), {"wo:0"}),
         ("nC", 0.4, 1.8, (1.04, 1.10, 0, 0, "o"), {"wi:0"}),
         ("nC", 3.3, 1.8, (1.02, 1.08, 10, -10, "s"), {"flash_out"}),
         ("nE", 0.2, 2.7, (1.00, 1.04, 0, 0, "s"), {"flash_in"}),
         ("nE", 3.6, 3.3, (1.02, 1.08, -10, -10, "s"), set()),
         ("nE", 7.2, 2.7, (1.00, 1.03, 0, -10, "s"), {"wo:90"}),
         ("nD", 0.5, 4.5, (1.00, 1.04, 0, 0, "s"), {"wi:90", "flash_out"}),
         ("EC", 0, 7.0, None, set())]
SFX = [("reveal", 4.55), ("reveal", 17.65), ("reveal", 26.35), ("card", 30.85)]
CHIPS = [("GENTLY EXFOLIATES", 10.4, 12.4), ("ADVANCED HYDRATION COMPLEX", 15.6, 17.6),
         ("COLLAGEN PEPTIDES + VITAMIN E", 22.5, 25.3), ("24HR DEEP MOISTURE", 27.3, 29.6),
         ("NON-GREASY · FAST ABSORBING", 29.7, 30.85)]
# (name, sub, start, end, position)  "low" keeps the title off her face
TITLES = [("MILKY HYDRO-GLOW", "Moisturizing Body Wash", 4.8, 7.3, "low"), ("CACAO & COLLAGEN", "Body Lotion", 18.0, 20.4, "top")]
OPENER = (0.25, 2.5, "The Morning Glow")
OPENER_Y = 140


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
    ws = [w for w in json.load(open(VO_WORDS))["words"] if w["start"] < CAPTION_UNTIL]
    ch, cur, pid = [], [], None
    for w in ws:
        if pid is not None and (w["phrase"] != pid or len(cur) >= 6):
            ch.append(cur)
            cur = []
        cur.append((w["text"].replace("...", "…"), w["start"], w["end"]))
        pid = w["phrase"]
    if cur:
        ch.append(cur)
    off = LINE[3] - LINE[1] if LINE else 0
    lw = [(t, s + off, e + off) for t, s, e in LINE_WORDS] if LINE else []
    k = 0
    for n in LINE_CHUNKS:
        ch.append(lw[k:k + n])
        k += n
    return ch


if __name__ == "__main__":
    print("shots end", shot_times()[-1][1], "TOTAL", TOTAL)
    for c in caption_chunks():
        print(round(c[0][1], 2), round(c[-1][2], 2), " ".join(w[0] for w in c))
