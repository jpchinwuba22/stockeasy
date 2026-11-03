"""Apply real-label replacement to a whole clip (1080x1920 output, same length, audio copied).
Usage: fixclip.py IN.mp4 OUT.mp4 SPEC  where SPEC is a python file defining ITEMS = [(label_name, roi_first, occlude,
t_from, t_to), ...] (roi in 1080x1920 coords of the first frame where the label is visible; times limit where the
label is patched)."""
import runpy
import subprocess
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, "labelfix")
import labelpatch as lp  # noqa: E402

LABELS = {
    "milky": ("straight/out/milky.png", (0.07, 1.04, 0.07, 3.07)),
    "cacao": ("straight/out/cacao.png", (0.07, 1.75, 0.07, 3.4)),
}
W, H, FPS = 1080, 1920, 24
EXP = 0.4


def read_frames(path):
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", path, "-vf", f"scale={W}:{H}:flags=lanczos", "-f", "rawvideo",
                          "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    frames = []
    while True:
        b = p.stdout.read(W * H * 3)
        if len(b) < W * H * 3:
            break
        frames.append(np.frombuffer(b, np.uint8).reshape(H, W, 3))
    return frames


def main(src, dst, spec):
    items = runpy.run_path(spec)["ITEMS"]
    frames = read_frames(src)
    n = len(frames)
    out = [f for f in frames]
    for it in items:
        name, roi0, occl, t_from, t_to = it[:5]
        min_fill = it[5] if len(it) > 5 else 0.72
        hclose = it[6] if len(it) > 6 else 0
        lbl = lp.Label(*LABELS[name])
        aspect = (lbl.banner[2] - lbl.banner[0]) / (lbl.banner[3] - lbl.banner[1])
        i0, i1 = int(round(t_from * FPS)), min(n, int(round(t_to * FPS)))
        tracks, roi = [], roi0
        for i in range(i0, i1):
            b = lp.find_banner(frames[i], roi, aspect=aspect * 0.9, close=6, min_fill=min_fill, hclose=hclose)
            if b is not None:
                # reject sudden jumps (a wrong blob): keep size within 25% of the previous good one
                prev = next((t for t in reversed(tracks) if t is not None), None)
                if prev is not None:
                    pw, w = prev[2] - prev[0], b[2] - b[0]
                    if abs(w / pw - 1) > 0.25:
                        b = None
            tracks.append(b)
            if b is not None:
                bw, bh = b[2] - b[0], b[3] - b[1]
                roi = (b[0] - EXP * bw, b[1] - EXP * bh, b[2] + EXP * bw, b[3] + EXP * bh)
        miss = sum(t is None for t in tracks)
        sm = lp.smooth_tracks(tracks, k=5)
        print(f"{name}: frames {i0}-{i1}, missed {miss}")
        if sm is None or miss > 0.3 * len(tracks):
            print(f"  SKIPPED {name}: banner not tracked reliably")
            continue
        for k, i in enumerate(range(i0, i1)):
            T = lp.similarity_from_banner(lbl.banner, tuple(sm[k]))
            rgb, al = lp.render_patch(lbl, T, (H, W))
            out[i] = lp.composite(out[i], rgb, al, occlude_skin=occl)
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                          "-i", "-", "-i", src, "-map", "0:v", "-map", "1:a?", "-c:v", "libx264", "-crf", "12", "-preset", "slow",
                          "-pix_fmt", "yuv420p", "-c:a", "copy", "-shortest", dst], stdin=subprocess.PIPE)
    for f in out:
        p.stdin.write(f.tobytes())
    p.stdin.close()
    p.wait()


if __name__ == "__main__":
    main(*sys.argv[1:4])
