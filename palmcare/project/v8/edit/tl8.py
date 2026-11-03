"""Video 5 — "Lagos sun… meet your match": PalmCare GlowShield Broad-Spectrum Daily Defense Sunscreen SPF 50+ PA++++.
Story: hook (the sun) -> the problem explained (UVB / UVA, melanin, dark spots) -> pack reveal -> what SPF 50+ and PA++++
mean -> texture and application (no white cast) -> the shield (what it does for melanin-rich skin) -> daily use ->
sunrise-to-sunset payoff -> end card. Shots are placed in seconds (24 fps frames); the product appears only as its pack."""
import json

VO = "vo8.wav"
VO_WORDS = "vo8_words.json"
MUSIC = "../../music/v8/music_v8.wav"
EC_FILE = "../EC8.mp4"
XF = 0.0
FPS = 24
HOOK2, REVEAL, SHIELD, FIN = 4.0, 21.75, 52.8, 72.6

S0 = (1.0, 1.0, 0, 0, "s")
PUSH = (1.00, 1.05, 0, 0, "s")
# (clip, source start, start time on the timeline, camera, flags); each shot runs to the next one's start
SHOTS_T = [("K1", 1.0, 0.0, (1.00, 1.08, 0, 0, "s"), set()),     # Lagos sun over the bridge: "Lagos sun..."
           ("K2", 5.0, 4.0, S0, set()),                          # she steps into the light: "...meet your match."
           ("K3", 0.3, 8.0, PUSH, set()),                        # the street sun: two kinds of rays
           ("K1", 6.0, 13.0, PUSH, set()),                       # UVA goes deeper, through clouds and windows
           ("K3", 4.0, 16.0, S0, set()),                         # shading her eyes: melanin, dark spots, lines
           ("PG", 0.0, REVEAL, S0, {"nograde"}),               # PACK REVEAL
           ("TB", 4.4, 25.5, (1.00, 1.04, 0, 0, "s"), set()),   # client: she holds up the real GlowShield tube
           ("K4", 0.0, 29.75, S0, set()),                        # texture: SPF 50+ explained
           ("K2", 0.3, 34.5, PUSH, set()),                       # PA++++ explained
           ("K6", 1.8, 38.5, S0, set()),                         # rays reach her: guards the inner layers
           ("K5", 1.0, 41.5, S0, set()),                         # application: silky, healthy ingredients, melts in clear
           ("K4", 6.7, 47.5, S0, set()),                         # fingertip clear: no white cast, no grease
           ("K5", 7.9, 50.8, S0, set()),                         # invisible veil
           ("K6", 4.0, SHIELD, S0, set()),                       # THE SHIELD: what it does for her skin
           ("K7", 0.8, 58.3, S0, set()),                         # out in the heat
           ("TB", 6.2, 62.6, S0, set()),                         # client: the tube again - "wear it each morning"
           ("K8", 0.4, 64.0, S0, set()),                         # face up to the sun: reapply
           ("K9", 2.6, 67.6, S0, set()),                         # sunset, still flawless
           ("K8", 5.6, FIN, PUSH, set()),                        # powerful smile
           ("EC", 0.0, 75.6, None, set())]
TOTAL = 85.6

SHOTS, STARTS = [], []
for k, (clip, st, a, mv, fl) in enumerate(SHOTS_T):
    b = SHOTS_T[k + 1][2] if k + 1 < len(SHOTS_T) else TOTAL
    fa, fb = round(a * FPS), round(b * FPS)
    STARTS.append(fa / FPS)
    SHOTS.append((clip, st, (fb - fa) / FPS, mv, fl))
CUTS = STARTS[1:]
EC_START = STARTS[-1]
PRODUCT_SPANS = [(REVEAL, STARTS[7])]

# narration (line, phrase, start)
VO_PLACE = [(0, 0, 0.85), (0, 1, 4.45),
            (1, 0, 8.35), (1, 1, 11.2), (1, 2, 13.15), (1, 3, 14.75), (1, 4, 16.5), (1, 5, 19.15), (1, 6, 20.4),
            (2, 0, 22.3), (2, 1, 23.5), (2, 2, 27.1),
            (3, 0, 30.15), (3, 1, 34.75), (3, 2, 38.55),
            (4, 0, 41.75), (4, 1, 45.6), (4, 2, 48.35), (4, 3, 49.75), (4, 4, 51.0),
            (5, 0, 53.05), (5, 1, 54.85), (5, 2, 56.45), (5, 3, 58.4), (5, 4, 60.15),
            (6, 0, 62.6), (6, 1, 64.95),
            (7, 0, 68.0), (7, 1, 69.85),
            (8, 0, 77.0)]


def words():
    try:
        return json.load(open(VO_WORDS))["words"]
    except Exception:
        return []


if __name__ == "__main__":
    print("TOTAL", TOTAL)
    for (c, st, d, *_), a in zip(SHOTS, STARTS):
        print(f"{a:6.2f}-{a + d:6.2f}  {c:3s} src {st:5.2f}-{st + d:5.2f}")
