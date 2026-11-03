"""Video 2: PalmCare Citrus Vitamin Glow Infusion Body Wash + PalmCare Molecular Glow Body Lotion (fair-skinned model).
Beat-locked edit at 104 BPM (every cut on a beat of the original Afrobeats score): sunny intro -> she picks the body
wash -> LIGHTNING UNVEIL -> citrus story -> LIGHTNING UNVEIL of the lotion -> molecular story -> rooftop result ->
LIGHTNING UNVEIL end card. Graphics: overlay2.py."""
import json

V = "2x"
BPM = 104
BEAT = 60 / BPM
VO = "../v2x/edit/vo.wav"
VO_WORDS = "../v2x/edit/vo_words.json"
MUSIC = "../music/v2/music_v2.wav"
MUSVOL, MUSOFF = 1.0, 0.0
END_CARD = "y7.mp4"
LINE, LINE_WORDS, LINE_CHUNKS = None, [], []
TITLES, CHIPS, SFX = [], [], []
OPENER, OPENER_Y, BADGE = (0, 0, ""), 0, ""

S0 = (1.0, 1.0, 0, 0, "s")
# (clip, src start, beats, move (z0, z1, dx, dy, ease), flags; "sp:x" = slow motion)
SHOTS_B = [("y1", 0.0, 4, (1.00, 1.05, 0, 14, "s"), {"dip_in"}),               # wakes up in the sun
           ("y1", 3.5, 5, (1.06, 1.00, 0, 0, "s"), set()),                      # walks into the bathroom
           ("y1bp", 1.05, 3, S0, set()),                                         # lifts the Citrus bottle (locked)
           ("y1b", 5.3, 4, (1.00, 1.04, 0, -8, "s"), set()),                    # holds it beside her face
           ("y2", 0.2, 8, S0, set()),                                            # UNVEIL 1: pool + falling fruit
           ("y2r", 6.55, 4, S0, set()),                                          # rack focus orange -> bottle
           ("y3", 0.63, 4, S0, set()),                                           # pump (locked)
           ("y3", 3.2, 6, (1.00, 1.06, 0, 0, "s"), {"sp:0.66"}),                 # thick slow pour on the loofah
           ("y3", 7.02, 8, (1.20, 1.27, 70, -120, "s"), {"sp:0.64"}),            # outdoor shower (towel cropped out)
           ("y2", 8.8, 2, (1.00, 1.03, 0, 0, "s"), set()),                       # bottle recap
           ("y4", 0.2, 8, S0, set()),                                            # UNVEIL 2: glass + prism
           ("y5", 0.6, 4, S0, set()),                                            # lotion pump (locked)
           ("y4", 5.0, 4, (1.00, 1.05, 0, 0, "s"), set()),                      # silky lotion swirl
           ("y1", 7.6, 4, S0, set()),                                            # holds Molecular beside her face
           ("y5", 3.0, 4, (1.02, 1.07, 0, -10, "s"), set()),                    # smooths it on
           ("y5", 7.2, 4, (1.00, 1.04, 0, 0, "s"), set()),                      # glowing shoulder
           ("y6", 0.4, 6, (1.00, 1.04, 0, 0, "s"), set()),                      # rooftop walk
           ("y6", 6.2, 6, (1.00, 1.05, 0, -10, "s"), set()),                    # sun close-up
           ("y7", 0.0, 16, S0, set())]                                           # UNVEIL 3: end card packshot (clean plate)


def _frames(k):
    return round(k * BEAT * 24)


SHOTS, _b = [], 0
for clip, st, nb, mv, fl in SHOTS_B:
    n = _frames(_b + nb) - _frames(_b)
    SHOTS.append((clip, st, round(n / 24 - 0.002, 4), mv, fl))
    _b += nb
TOTAL = _frames(_b) / 24
VOSEG = [(0.0, TOTAL, 0.0)]
AMB = 0.22
UNVEILS = [_frames(k) / 24 for k in (16, 48, 88)]
EC_START = UNVEILS[2]
CAPTION_UNTIL = EC_START - 0.05

# narration: (line, phrase, start time of its first word)
VO_PLACE = [(0, 0, 0.60), (0, 1, 1.95), (0, 2, 3.45),                  # Sunshine on your skin... and a fresh start, every single day.
            (1, 0, 7.30),                                               # Meet your new glow essential...
            (2, 0, 10.00),                                              # PalmCare Citrus Vitamin Glow Infusion Body Wash.
            (3, 0, 14.15),                                              # Infused with vitamin-rich citrus,
            (3, 1, 18.65),                                              # its thick, luxurious gel cleanses gently...
            (3, 2, 22.10), (3, 3, 23.85), (3, 4, 25.95),               # deep surge of moisture, brighter fresher-looking skin, soft... and radiant.
            (4, 0, 28.05), (4, 1, 29.55),                               # Then, lock it in... with PalmCare Molecular Glow Body Lotion.
            (5, 0, 32.65), (5, 1, 34.55), (5, 2, 36.00),               # alpha arbutin, tranexamic acid, vitamin C...
            (5, 3, 37.55), (5, 4, 39.45), (5, 5, 41.20),                # lightening complex, even skin tone, luminous glow.
            (6, 0, 77 * BEAT), (6, 1, 78 * BEAT), (6, 2, 79.3 * BEAT),    # Fresh. Radiant. Confident...  (on the beat)
            (6, 3, 82.5 * BEAT), (6, 4, 84.6 * BEAT),                   # from sunrise, to sunset.
            (7, 0, 53.30)]                                              # Pamper your skin with PalmCare.


def shot_times():
    t, out = 0.0, []
    for s in SHOTS:
        d = round(s[2] * 24) / 24
        out.append((t, t + d))
        t += d
    return out


CUTS = [a for a, _ in shot_times()[1:]]
_T = shot_times()
# transitions at cuts (index = shot that starts): flare (sun-flare wipe), whip, ripple, cut; unveils handled separately
TRANS = {1: "flare", 2: "whip", 3: "cut", 5: "ripple", 6: "whip", 7: "cut", 8: "flare", 9: "whip",
         11: "whip", 12: "ripple", 13: "flare", 14: "cut", 15: "whip", 16: "flare", 17: "ripple"}

# product title cards after each unveil: (lines, tag, t0, t1)
UNVEIL_TITLES = [(["CITRUS", "VITAMIN", "GLOW"], "PALMCARE  ·  INFUSION BODY WASH", UNVEILS[0] + 0.55, _T[4][1] - 0.1),
                 (["MOLECULAR", "GLOW"], "PALMCARE  ·  BODY LOTION", UNVEILS[1] + 0.55, _T[10][1] - 0.1)]
# citrus seal badge (rotating ring text) on the rack-focus shot
SEAL = ("BRIGHTENING COMPLEX", "VIT", "C", _T[5][0] + 0.25, _T[5][1] - 0.05, (820, 470))
# pill callouts: (icon, text, t0, t1, centre)
PILLS = [("drop", "DEEP MOISTURE SURGE", 22.05, 23.8, (540, 1290)),
         ("spark", "BRIGHTER, FRESHER SKIN", 23.85, _T[8][1] - 0.6, (540, 1290)),
         ("leaf", "GENTLE CLEANSE", _T[7][0] + 0.9, _T[7][1] - 0.05, (540, 1290)),
         ("spark", "LIGHTENING COMPLEX", 37.5, _T[13][1] - 0.05, (540, 1330)),
         ("spark", "EVENS OUT SKIN TONE", 39.4, _T[14][1] - 0.05, (540, 1330))]
# molecule diagram: nodes appear with the words (label, t_in, node xy)
MOLECULE = ([("ALPHA ARBUTIN", 32.60, (250, 520)), ("TRANEXAMIC ACID", 34.50, (800, 430)),
             ("VITAMIN C  (SAP)", 35.95, (560, 760))], _T[12][1] - 0.05)
# rooftop word slams on the beat
SLAMS = [("BRIGHT.", 77 * BEAT, 78 * BEAT), ("RADIANT.", 78 * BEAT, 79 * BEAT), ("CONFIDENT.", 79 * BEAT, _T[16][1] - 0.05)]
# end card bottle labels (text, sub, anchor on bottle, label position)
EC_TAGS = [("CITRUS VITAMIN GLOW", "Infusion Body Wash  ·  1000 mL", (380, 1497), (300, 1588)),
           ("MOLECULAR GLOW", "Body Lotion  ·  500 mL", (710, 1497), (800, 1588))]
EC_GLINTS = [(398, 640), (742, 762)]


def caption_chunks():
    ws = [w for w in json.load(open(VO_WORDS))["words"] if w["start"] < CAPTION_UNTIL]
    groups = {}
    for w in ws:
        groups.setdefault(w["phrase"], []).append((w["text"].replace("...", "…").replace("twenty-four-hour", "24-hour"),
                                                   w["start"], w["end"]))
    ch = []
    for g in groups.values():
        k = -(-len(g) // 4)
        n = -(-len(g) // k)
        ch += [g[i:i + n] for i in range(0, len(g), n)]
    return ch


if __name__ == "__main__":
    print("TOTAL", TOTAL, "unveils", [round(u, 3) for u in UNVEILS])
    for k, ((s, st, d, *_), (a, b)) in enumerate(zip(SHOTS, shot_times())):
        print(f"{k:2d} {a:6.2f}-{b:6.2f} {s:4s} src {st:5.2f}-{st + d:5.2f}  -> {TRANS.get(k + 1, '')}")
