"""Timelines for the remade Videos 1-3 (output seconds), chosen with PCV: the cut list, voiceover placement (the
approved narration, unchanged, re-spaced around the new picture), her on-camera line, captions, chips, titles."""
import json
import os

V = int(os.environ.get("PCV", "1"))

# SHOTS: (source, src start, duration, camera move (z0, z1, dx, dy, ease), transitions)
#   source: clip name (vNx.mp4) or "HA"/"HB" (product reveals) or "EC" (end card)
#   transitions: set of "dip_in", "flash_in", "flash_out", "wo:<angle>", "wi:<angle>"
CFG = {
    1: dict(
        TOTAL=29.8, VO="../vo/vo1_take1.mp3", MUSIC="../music/v1_music_B.mp3", MUSVOL=0.9, MUSOFF=0.0,
        VOSEG=[(0.0, 3.76, 0.6), (3.8, 10.15, 4.9), (10.15, 16.9, 11.65), (17.0, 19.64, 23.4)],
        LINE=("v1e", 2.3, 4.9, 19.4), LINE_WORDS=[("My", 2.40, 2.60), ("skin", 2.75, 3.05), ("starts", 3.05, 3.30), ("the", 3.30, 3.42),
                                                ("day", 3.42, 3.62), ("before", 3.62, 3.95), ("I", 4.08, 4.20), ("do.", 4.30, 4.65)], LINE_CHUNKS=[3, 5],
        SHOTS=[("v1a", 0.5, 2.4, (1.00, 1.14, 0, 30, "s"), {"dip_in"}),
               ("v1a", 3.0, 2.2, (1.06, 1.16, -30, 0, "s"), {"flash_out"}),
               ("HA", 0, 2.8, None, {"flash_in", "wo:90"}),
               ("v1a", 6.0, 1.8, (1.04, 1.14, 0, -20, "o"), {"wi:90"}),
               ("v1b", 1.8, 2.2, (1.00, 1.08, 0, -20, "s"), {"flash_out"}),
               ("HB", 0, 2.8, None, {"flash_in", "wo:0"}),
               ("v1d", 0.3, 1.6, (1.04, 1.12, 0, 0, "o"), {"wi:0"}),
               ("v1c", 4.6, 1.6, (1.06, 1.12, -20, -20, "s"), set()),
               ("v1d", 7.2, 1.4, (1.00, 1.07, 0, -20, "s"), {"wo:90"}),
               ("v1e", 1.7, 4.0, (1.00, 1.06, 0, -20, "s"), {"wi:90", "flash_out"}),
               ("EC", 0, 7.0, None, set())],
        CHIPS=[("ADVANCED HYDRATION COMPLEX", 7.45, 8.95), ("SMOOTHS · GENTLY EXFOLIATES", 9.05, 10.5),
               ("COLLAGEN PEPTIDES + VITAMIN E", 14.3, 15.65), ("24HR DEEP MOISTURE", 15.75, 17.05),
               ("NON-GREASY · FAST ABSORBING", 17.15, 18.55)],
        TITLES=[("MILKY HYDRO-GLOW", "Moisturizing Body Wash", 4.65, 7.35), ("CACAO & COLLAGEN", "Body Lotion", 11.45, 14.15)],
        OPENER=(0.25, 2.3, "The Ritual After")),
    2: dict(
        TOTAL=34.4, VO="../v2/v2_vo.mp3", MUSIC="../v2/v2_music_scored.mp3", MUSVOL=1.0, MUSOFF=0.0,
        VOSEG=[(0.0, 1.48, 0.5), (1.48, 8.0, 4.32), (8.0, 17.3, 13.5), (17.3, 20.03, 28.0)],
        LINE=("v2d", 5.3, 8.0, 23.5), LINE_WORDS=[("Sun's", 5.50, 5.72), ("out…", 5.75, 6.10), ("so", 6.80, 6.95), ("is", 7.00, 7.10),
                                                ("my", 7.15, 7.30), ("glow.", 7.35, 7.75)], LINE_CHUNKS=[2, 4],
        SHOTS=[("v2a", 6.2, 2.2, (1.00, 1.14, 0, 30, "s"), {"dip_in"}),
               ("v2a", 0.2, 2.2, (1.04, 1.14, 0, -20, "s"), {"flash_out"}),
               ("HA", 0, 2.8, None, {"flash_in", "wo:90"}),
               ("v2a", 3.0, 1.8, (1.04, 1.14, 0, 10, "o"), {"wi:90"}),
               ("v2b", 0.2, 1.8, (1.06, 1.14, -20, -10, "s"), set()),
               ("v2b", 3.3, 1.6, (1.06, 1.12, 20, 0, "s"), set()),
               ("v2b", 7.2, 1.0, (1.00, 1.06, 0, -20, "s"), {"flash_out"}),
               ("HB", 0, 2.8, None, {"flash_in", "wo:0"}),
               ("v2c", 0.2, 1.8, (1.04, 1.12, 0, 0, "o"), {"wi:0"}),
               ("v2c", 3.2, 2.0, (1.06, 1.12, -20, -20, "s"), set()),
               ("v2c", 7.4, 1.6, (1.00, 1.08, 0, -20, "s"), {"wo:0"}),
               ("v2d", 1.0, 1.8, (1.00, 1.08, 0, -10, "s"), {"wi:0"}),
               ("v2d", 5.2, 4.0, (1.00, 1.06, 0, -20, "s"), {"flash_out"}),
               ("EC", 0, 7.0, None, set())],
        CHIPS=[("VITAMIN C + B3", 7.3, 8.75), ("SHIMMERING GOLDEN LATHER", 8.9, 10.5), ("LIGHT · SILKY", 16.4, 17.95),
               ("MELTS RIGHT IN", 18.1, 19.6), ("ULTRA DEEP MOISTURE", 20.9, 22.55)],
        TITLES=[("CITRUS VITAMIN GLOW", "Infusion Body Wash", 4.45, 7.15), ("MOLECULAR GLOW", "Body Lotion", 13.45, 16.15)],
        OPENER=(0.25, 2.15, "The Citrus Ritual")),
    3: dict(
        TOTAL=32.6, VO="../v3/v3_vo.mp3", MUSIC="../v3/v3_music.mp3", MUSVOL=0.95, MUSOFF=0.0,
        VOSEG=[(0.0, 2.58, 0.5), (2.58, 8.3, 3.64), (8.3, 13.5, 12.22), (13.5, 16.04, 26.2)],
        LINE=("v3d", 6.6, 8.3, 23.6), LINE_WORDS=[("Glow,", 6.78, 7.20), ("protected.", 7.45, 8.10)], LINE_CHUNKS=[2],
        SHOTS=[("v3a", 0.2, 1.9, (1.00, 1.12, 0, 20, "s"), {"dip_in"}),
               ("v3a", 3.2, 1.7, (1.04, 1.12, 0, -20, "s"), {"flash_out"}),
               ("HA", 0, 2.8, None, {"flash_in", "wo:90"}),
               ("v3b", 0.2, 1.8, (1.04, 1.12, 0, 0, "o"), {"wi:90"}),
               ("v3b", 3.2, 1.8, (1.00, 1.08, 0, -10, "s"), set()),
               ("v3b", 6.2, 2.0, (1.02, 1.10, 0, -20, "s"), {"flash_out"}),
               ("HB", 0, 2.8, None, {"flash_in", "wo:0"}),
               ("v3c", 0.2, 1.8, (1.04, 1.12, 0, 0, "o"), {"wi:0"}),
               ("v3c", 3.4, 1.8, (1.06, 1.12, -20, -20, "s"), set()),
               ("v3c", 7.4, 1.4, (1.00, 1.07, 0, -20, "s"), {"wo:90"}),
               ("v3d", 0.3, 1.6, (1.00, 1.08, 0, -10, "s"), {"wi:90"}),
               ("v3d", 3.2, 1.2, (1.04, 1.10, 0, -10, "o"), set()),
               ("v3d", 5.6, 3.0, (1.00, 1.06, 0, -20, "s"), {"flash_out"}),
               ("EC", 0, 7.0, None, set())],
        CHIPS=[("ULTRA-ACTIVE VITAMIN C", 6.5, 7.95), ("RADIANCE · EVEN TONE", 8.1, 9.6), ("SPF 50+ · PA++++", 13.5, 14.9),
               ("BROAD SPECTRUM", 15.0, 16.3), ("NO WHITE CAST", 16.4, 17.8)],
        TITLES=[("VITA C+ SERUM", "Ultra-Active Vitamin C", 3.65, 6.35), ("GLOWSHIELD", "SPF 50+ Daily Sunscreen", 12.05, 14.75)],
        OPENER=(0.25, 2.0, "Shadow & Light")),
}[V]
globals().update(CFG)
CAPTIONED = 3      # the last narration line (the sign-off) is shown by the end card itself


def shot_times():
    t, out = 0.0, []
    for s in SHOTS:
        out.append((t, t + s[2]))
        t += s[2]
    return out


def vo_words():
    words = json.load(open(f"v{V}_vo_words.json"))["words"]
    out = []
    for w in words:
        for s0, s1, at in VOSEG[:CAPTIONED]:
            if s0 <= w["start"] < s1:
                out.append((w["text"].replace("...", "…"), w["start"] - s0 + at, min(w["end"], s1) - s0 + at))
                break
    return out


def chunk(words, maxn=4):
    """Caption chunks: break after sentence/clause punctuation, a long pause, or maxn words."""
    out, cur = [], []
    for k, w in enumerate(words):
        cur.append(w)
        nxt = words[k + 1] if k + 1 < len(words) else None
        # at the word limit, still take one more word when it closes the clause (no orphan "wash…" / "tone.")
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
