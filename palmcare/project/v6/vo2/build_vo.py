"""Lay the seven clean single-take narration lines for Video 6 onto the output timeline -> vo2/vo_new.wav,
level-matched, with word timings (output seconds) -> vo2/words_out.json. Run from v6/."""
import json
import subprocess

import numpy as np

# (file, output time, tempo, word timings from each line's transcript)
LINES = [
    ("L1b", 0.45, 1.00, None),
    ("L2", 4.95, 1.00, [("Advanced", 0, 0.65), ("Tropical", 0.708, 1.173), ("Glow.", 1.219, 1.95)]),
    ("L3", 7.45, 1.06, [("Lactic", 0, 0.673), ("and", 0.848, 0.975), ("mandelic", 1.033, 1.649), ("acids", 1.765, 2.194),
                        ("gently", 2.345, 2.879), ("buff", 2.995, 3.274), ("away", 3.367, 3.704), ("dullness,", 3.785, 4.54),
                        ("while", 4.923, 5.166), ("ceramides", 5.201, 5.968), ("lock", 6.084, 6.42), ("in", 6.513, 6.594),
                        ("moisture.", 6.687, 7.616)]),
    ("L4", 15.35, 1.00, [("Then,", 0, 0.662), ("Dermalight", 0.987, 1.625), ("Body", 1.695, 1.985), ("Lotion.", 2.055, 2.786)]),
    ("L5", 18.60, 1.06, [("Vitamins", 0, 0.569), ("B3", 0.639, 1.207), ("and", 1.231, 1.358), ("E,", 1.405, 1.66),
                         ("with", 2.043, 2.218), ("an", 2.264, 2.322), ("advanced", 2.368, 2.949), ("UV", 3.042, 3.529),
                         ("defence", 3.773, 4.226), ("shield.", 4.261, 5.016)]),
    ("L6", 23.85, 1.04, [("Smooth.", 0, 0.917), ("Radiant.", 1.358, 2.101), ("Ready", 2.543, 2.81), ("for", 2.879, 3.03),
                         ("the", 3.077, 3.158), ("sun.", 3.216, 3.947)]),
    ("L7", 32.30, 1.00, [("PalmCare.", 0, 0.824), ("The", 1.637, 1.753), ("Tropical", 1.811, 2.31), ("Glow", 2.334, 2.67),
                         ("ritual.", 2.694, 3.808)]),
]
# L1b's word timings were measured by transcribing it in the final mix
L1B_WORDS = [("Some", 0.11, 0.29), ("mornings", 0.37, 0.85), ("deserve", 0.93, 1.39), ("a", 1.43, 1.47),
             ("little", 1.51, 1.67), ("paradise.", 1.81, 2.51)]


def speech_rms(f):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", f, "-ac", "1", "-ar", "16000", "-f", "s16le", "-"], capture_output=True).stdout
    a = np.frombuffer(raw, np.int16).astype(np.float32) / 32768
    r = np.sqrt((a[:len(a) // 320 * 320].reshape(-1, 320) ** 2).mean(1))
    return 20 * np.log10(np.sqrt((r[r > 10 ** (-40 / 20)] ** 2).mean()))


ins, flt, words = [], [], []
for k, (n, at, tp, ws) in enumerate(LINES):
    ws = ws or L1B_WORDS
    g = -19.0 - speech_rms(f"vo2/{n}.mp3")
    ins += ["-i", f"vo2/{n}.mp3"]
    tf = f",atempo={tp}" if tp != 1 else ""
    flt.append(f"[{k}:a]aresample=44100,aformat=channel_layouts=mono{tf},volume={g:.2f}dB,afade=t=in:d=0.02,adelay={int(round(at * 1000))}[l{k}]")
    words += [{"text": t, "type": "word", "start": round(at + s / tp, 3), "end": round(at + e / tp, 3)} for t, s, e in ws]
flt.append("".join(f"[l{k}]" for k in range(len(LINES))) + f"amix=inputs={len(LINES)}:normalize=0:duration=longest,apad=whole_dur=37.6,atrim=0:37.6")
subprocess.run(["ffmpeg", "-v", "error", "-y", *ins, "-filter_complex", ";".join(flt), "-c:a", "pcm_s16le", "vo2/vo_new.wav"], check=True)
json.dump({"words": words}, open("vo2/words_out.json", "w"))
