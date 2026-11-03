"""Video 6 — "Wake up your glow": PalmCare Vitamin C Face Moisturiser. Cinematic Afrobeats edit, cut on a 104 BPM grid
(beat = 0.577 s, bar = 2.31 s). Hook (orange burst -> her eyes open) -> the morning problem -> hero reveal of the REAL box and
jar -> stabilised vitamin C -> the tone trio (niacinamide, alpha arbutin, tranexamic acid) -> the hydration complex ->
results -> daily use with GlowShield -> finale -> end card. The product is only ever the real box/jar photos (PR, PP, PI)."""
import json

VO = "vo9.wav"
VO_WORDS = "vo9_words.json"
MUSIC = "../../music/v9/music_v9.wav"
EC_FILE = "../EC9b.mp4"
XF = 0.0
FPS = 24
BPM = 104
BEAT = 60 / BPM

S0 = (1.0, 1.0, 0, 0, "s")
PUSH = (1.00, 1.06, 0, 0, "s")
PULL = (1.07, 1.00, 0, 0, "s")
# (clip, source start, start beat, camera, flags)
SHOTS_B = [("C1", 2.3, 0, (1.00, 1.10, 0, 0, "s"), set()),       # HOOK: the orange bursts into light — "Dull, tired mornings?"
           ("C2", 0.9, 4, PUSH, set()),                          # match cut: her eyes open — "Wake up your glow."
           ("C2", 4.2, 8, S0, set()),                            # DROP: she sits up — overnight moisture loss
           ("C3", 3.0, 12, PUSH, set()),                         # mirror: looks flat, turns patchy
           ("PR", 0.0, 20, S0, {"nograde"}),                     # HERO REVEAL: real box + jar
           ("C4", 0.5, 32, PUSH, set()),                         # texture: stabilised vitamin C
           ("C5", 0.3, 40, S0, set()),                           # application: the tone trio
           ("PP", 0.0, 48, S0, {"nograde"}),                     # cutaway: box + jar while she applies
           ("C5", 6.9, 52, S0, set()),                           # neck strokes
           ("PI", 0.0, 56, S0, {"nograde"}),                     # the jar + hydration complex
           ("C6", 1.5, 66, S0, set()),                           # mirror "after": the glow wakes up
           ("C8", 3.0, 80, PUSH, set()),                         # window close-up: soft, smooth, radiant
           ("C7", 1.0, 88, S0, set()),                           # walks into the bright morning: daily use + GlowShield
           ("C8", 6.4, 98, PUSH, set()),                         # finale smile: luminous, supple, yours
           ("EC", 0.0, 104, None, set())]
END_BEAT = 122
REVEAL_B, DROP_B, EC_B = 20, 8, 104


def T(b):
    return round(b * BEAT * FPS) / FPS


SHOTS, STARTS = [], []
for k, (clip, st, b, mv, fl) in enumerate(SHOTS_B):
    nb = SHOTS_B[k + 1][2] if k + 1 < len(SHOTS_B) else END_BEAT
    STARTS.append(T(b))
    SHOTS.append((clip, st, T(nb) - T(b), mv if mv else S0, fl))
TOTAL = T(END_BEAT)
CUTS = STARTS[1:]
EC_START = STARTS[-1]
REVEAL, DROP = T(REVEAL_B), T(DROP_B)

# narration (line, phrase, start)
VO_PLACE = [(0, 0, 0.30), (0, 1, 2.62),
            (1, 0, 5.00), (1, 1, 7.75), (1, 2, 8.85),
            (2, 0, 12.15), (2, 1, 13.85),
            (3, 0, 18.85), (3, 1, 22.30),
            (4, 0, 25.55), (4, 1, 31.15),
            (5, 0, 32.80), (5, 1, 37.95), (5, 2, 40.45),
            (6, 0, 44.20), (6, 1, 45.75), (6, 2, 47.95),
            (7, 0, 51.00), (7, 1, 52.55),
            (8, 0, 56.90), (8, 1, 57.95), (8, 2, 58.90),
            (9, 0, 61.50)]


def words():
    try:
        return json.load(open(VO_WORDS))["words"]
    except Exception:
        return []


if __name__ == "__main__":
    print("TOTAL", TOTAL, "beat", round(BEAT, 4))
    for (c, st, d, *_), a in zip(SHOTS, STARTS):
        print(f"{a:6.2f}-{a + d:6.2f}  {c:3s} src {st:5.2f}-{st + d:5.2f}")
