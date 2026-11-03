"""Shared Video 6 timeline: voiceover placement, caption chunks, pop-up chips and product titles (output seconds)."""
import json

TOTAL = 37.6
# voiceover: vo2/vo_new.wav is the narration already laid out on the output timeline -- seven clean single-take
# lines (one per sentence), level-matched and spaced with natural breaths. Segments: (source start, end, output time)
VOSEG = [(0.0, 30.0, 0.0), (30.0, 37.6, 30.0)]
CAPTIONED = 1        # the end-card line is shown by the card itself
LINE_AT = 27.9 - 4.9          # her on-camera line: clip D source time + this offset
LINE_WORDS = [("Soft", 5.18, 5.5), ("skin,", 5.56, 5.9), ("all-day", 6.16, 6.5), ("glow.", 6.6, 6.9)]
# caption chunk sizes (words, in order); the end-card line is shown by the card itself
CHUNKS = [2, 4, 3, 4, 4, 2, 3, 4, 4, 3, 3, 2, 4]
CHIPS = [("GENTLE EXFOLIATION", 7.65, 9.35), ("DEEP MOISTURE BOOST", 11.95, 13.95),
         ("FAST ABSORBING", 18.4, 19.95), ("UV DEFENCE SHIELD", 21.3, 22.95), ("ACTIVE GLOW", 23.15, 24.6)]
TITLES = [("ADVANCED TROPICAL GLOW", "Exfoliating Body Wash", 4.75, 7.35),
          ("DERMALIGHT", "Body Lotion", 15.55, 18.15)]
OPENER = (0.25, 2.55)          # "Tropical Glow" title over the drone shot


def vo_words():
    """Captioned voiceover words in output time (a word starting inside a cut keeps its kept part)."""
    words = [w for w in json.load(open("vo2/words_out.json"))["words"] if w["type"] == "word"]
    out = []
    for w in words:
        for s0, s1, at in VOSEG[:CAPTIONED]:
            if s0 <= w["start"] < s1 or (w["start"] < s0 < w["end"] - 0.05 and w["end"] <= s1 + 0.05):
                st = max(w["start"], s0)
                out.append((w["text"].replace("U.V.", "UV"), st - s0 + at, min(w["end"], s1) - s0 + at))
                break
    return out


def caption_chunks():
    words = vo_words()
    out, k = [], 0
    for n in CHUNKS:
        out.append(words[k:k + n])
        k += n
    out.append([(t, s + LINE_AT, e + LINE_AT) for t, s, e in LINE_WORDS])
    return out


if __name__ == "__main__":
    for c in caption_chunks():
        print(round(c[0][1], 2), round(c[-1][2], 2), " ".join(w[0] for w in c))
